# Author: Antonio Corona
# Date: 2026-04-02
"""
scheduler_core/main.py

Core scheduling engine wrapper.

Responsibilities:
- Build a CombinedConfig from the loaded config dict
- Run the scheduler library
- Convert solver output into CANONICAL "flat rows" (meeting-level rows)
  ready for CSV/JSON export.

Flat row schema (required + optional):
  schedule_id, course_id, day, start,
  room, faculty, lab, duration, credits, meeting_index
"""

from __future__ import annotations

import csv
import re
from io import StringIO
from typing import Any, Dict, Iterator, List, Tuple

from scheduler import Scheduler
from scheduler.config import CombinedConfig

# Canonical flat-row schema (order matters for CSV output)
FIELDNAMES = [
    "schedule_id",
    "course_id",
    "day",
    "start",
    "room",
    "faculty",
    "lab",
    "duration",
    "credits",
    "meeting_index",
]

# Matches: "MON 10:40-11:30"
_MEETING_RE = re.compile(r"^(MON|TUE|WED|THU|FRI)\s+(\d{2}:\d{2})-(\d{2}:\d{2})(\^?)$")


def _csv_split(line: str) -> List[str]:
    """
    Correctly split a CSV line while respecting quotes.
    This is critical because the 'meetings' field contains commas and is quoted.
    """
    return next(csv.reader(StringIO(line)))


def _minutes_between(start: str, end: str) -> int:
    sh, sm = map(int, start.split(":"))
    eh, em = map(int, end.split(":"))
    return (eh * 60 + em) - (sh * 60 + sm)


def _explode_meetings(meetings_field: str) -> List[Tuple[str, str, str, str, bool]]:
    """
    Turns:
      'MON 10:40-11:30,WED 10:40-11:30^,FRI 10:40-11:30'
    into:
      [('MON', '10:40', '11:30', '50', False),
       ('WED', '10:40', '11:30', '50', True),
       ('FRI', '10:40', '11:30', '50', False)]
    """
    out: List[Tuple[str, str, str, str, bool]] = []
    if not meetings_field:
        return out

    meetings_field = meetings_field.strip().strip('"').strip("'")
    for chunk in meetings_field.split(","):
        chunk = chunk.strip().strip('"').strip("'")
        m = _MEETING_RE.match(chunk)
        if m:
            day = m.group(1)
            start = m.group(2)
            end = m.group(3)
            duration = str(_minutes_between(start, end))
            is_lab_meeting = m.group(4) == "^"
            out.append((day, start, end, duration, is_lab_meeting))
    return out


def _safe_as_csv(course_obj: Any) -> str:
    """
    Best-effort conversion to a CSV-ish line from the scheduler course model.
    Prefer course.as_csv() (documented by the scheduler library).
    """
    if hasattr(course_obj, "as_csv") and callable(getattr(course_obj, "as_csv")):
        try:
            return str(course_obj.as_csv())
        except Exception:
            pass
    return repr(course_obj)


def _room_for_course(course_id: str, cfg: Dict[str, Any]) -> str:
    base = course_id.split(".")[0]  # CS101.01 -> CS101
    for c in cfg.get("config", {}).get("courses", []):
        if c.get("course_id") == base:
            rooms = c.get("room") or []
            if isinstance(rooms, list) and rooms:
                return str(rooms[0])
            if isinstance(rooms, str):
                return rooms
    return ""


def _lab_for_course(course_id: str, cfg: Dict[str, Any]) -> str:
    """
    Returns first lab assigned to a course from config.
    Example config:
        "lab": ["Lab 1"]
    """
    base = course_id.split(".")[0]

    for c in cfg.get("config", {}).get("courses", []):
        if c.get("course_id") == base:
            labs = c.get("lab") or []
            if isinstance(labs, list) and labs:
                return str(labs[0])
            if isinstance(labs, str):
                return labs

    return ""


def _base_course_id(course_id: str) -> str:
    # Solver gives CS101.01; config stores CS101
    return course_id.split(".")[0] if course_id else ""


def _credits_for_course(course_id: str, cfg: Dict[str, Any]) -> str:
    base = _base_course_id(course_id)
    for c in cfg.get("config", {}).get("courses", []):
        if str(c.get("course_id", "")) == base:
            credits = c.get("credits", "")
            return str(credits) if credits is not None else ""
    return ""


def _duration_for_course(course_id: str, cfg: Dict[str, Any]) -> str:
    """
    Gets meeting duration (minutes) based on the time_slot_config.classes mapping.
    Your config maps credits -> meetings list -> duration.
    We'll return the NON-lab duration if present, else blank.
    """
    base = _base_course_id(course_id)

    # Find course credits first
    credits_str = _credits_for_course(base, cfg)
    try:
        credits = int(credits_str) if credits_str != "" else None
    except ValueError:
        credits = None

    if credits is None:
        return ""

    for klass in cfg.get("time_slot_config", {}).get("classes", []):
        if klass.get("credits") == credits:
            meetings = klass.get("meetings") or []
            # Prefer non-lab meeting duration
            for m in meetings:
                if not m.get("lab", False) and "duration" in m:
                    return str(m["duration"])
            # Otherwise, fall back to any duration
            for m in meetings:
                if "duration" in m:
                    return str(m["duration"])
    return ""


def _parse_course_line_to_flat_rows(
    schedule_id: int, course_obj: Any, cfg: Dict[str, Any]
) -> List[Dict[str, Any]]:
    line = _safe_as_csv(course_obj)

    try:
        parts = [p.strip() for p in _csv_split(line)]
    except Exception:
        parts = [p.strip() for p in line.split(",")]

    course_id = parts[0] if len(parts) > 0 else ""
    faculty = parts[1] if len(parts) > 1 else ""

    # Reliable variables from config (not from solver string formatting)
    room = parts[2] if len(parts) > 2 else ""
    credits = _credits_for_course(course_id, cfg)

    """
    LAB ASSIGNMENT LOGIC

    Lab is assigned ONLY to meetings marked with '^' in scheduler output.

    - parts[3] = lab name (course-level)
    - '^' indicates which meeting is the actual lab

    This ensures:
    - only true lab sessions appear in lab filters/tables
    - lecture meetings are not incorrectly labeled as labs

    If lab filtering looks wrong, verify this mapping first.
    """
    course_lab = parts[3] if len(parts) > 3 else ""
    if course_lab in {"None", "none", "null", "NULL"}:
        course_lab = ""

    # Collect all meeting chunks (some outputs split them)
    meeting_chunks = parts[4:]
    meetings_field = ",".join(meeting_chunks)
    meetings = _explode_meetings(meetings_field)

    rows: List[Dict[str, Any]] = []

    for idx, (day, start, end, duration, is_lab_meeting) in enumerate(
        meetings, start=1
    ):
        rows.append(
            {
                "schedule_id": schedule_id,
                "course_id": course_id,
                "day": day,
                "start": start,
                "room": room,
                "faculty": faculty,
                "lab": course_lab if is_lab_meeting else "",
                "duration": duration,
                "credits": credits,
                "meeting_index": idx,
            }
        )

    if not rows:
        rows.append(
            {
                "schedule_id": schedule_id,
                "course_id": course_id,
                "day": "",
                "start": "",
                "room": room,
                "faculty": faculty,
                "lab": "",
                "duration": "",
                "credits": credits,
                "meeting_index": 1,
            }
        )

    return rows


def generate_schedules(
    cfg: Dict[str, Any], limit: int, optimize: bool
) -> Iterator[List[Dict[str, Any]]]:
    """
    Runs the scheduler and yields flat meeting-level schedule rows.

    Defensive behavior:
    - Validates limit before invoking the solver.
    - Stops exactly at the requested schedule limit.
    - Avoids storing all solver models in memory.
    - Keeps the optimize argument for API compatibility, even though
      optimization is currently handled by the scheduler configuration.
    """

    if limit <= 0:
        raise ValueError("Schedule generation limit must be greater than 0.")

    combined = CombinedConfig(**cfg)
    scheduler = Scheduler(combined)

    schedule_count = 0

    for schedule in scheduler.get_models():
        schedule_count += 1

        course_models = list(schedule)
        schedule_rows: List[Dict[str, Any]] = []

        for course in course_models:
            schedule_rows.extend(
                _parse_course_line_to_flat_rows(schedule_count, course, cfg)
            )

        yield schedule_rows

        if schedule_count >= limit:
            break