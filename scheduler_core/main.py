# Author: Antonio Corona
# Date: 2026-03-30
"""
scheduler_core/main.py

Core scheduling engine wrapper.

Responsibilities:
- Build a CombinedConfig from the loaded config dict
- Run the scheduler library
- Convert solver output into CANONICAL "flat rows" (meeting-level rows)
  ready for CSV/JSON export.

Flat row schema (required + optional):
  schedule_id, course_id, day, start, room, faculty, lab, duration, credits, meeting_index
"""

from __future__ import annotations

import csv
import re
from io import StringIO
from typing import Any, Dict, List, Tuple, Iterator

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
_MEETING_RE = re.compile(
    r"^(MON|TUE|WED|THU|FRI)\s+(\d{2}:\d{2})-(\d{2}:\d{2})\^?$"
)

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


def _explode_meetings(meetings_field: str) -> List[Tuple[str, str, str, str]]:
    """
    Turns:
      'MON 10:40-11:30,WED 10:40-11:30,FRI 10:40-11:30'
    into:
      [('MON', '10:40', '11:30', '50'), ...]
    """
    out: List[Tuple[str, str, str, str]] = []
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
            out.append((day, start, end, duration))
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


# def _parse_course_line_to_flat_rows(schedule_id: int, course_obj: Any) -> List[Dict[str, Any]]:
#     """
#     Converts one solver course/model object into meeting-level flat rows.

#     Your observed scheduler output behaves like:
#       parts[0] = course_id     (e.g., CS101.01)
#       parts[1] = faculty       (e.g., Dr. Smith)
#       parts[2] = meetings      (quoted; contains commas)
#                  e.g. "MON 10:40-11:30,WED 10:40-11:30,FRI 10:40-11:30"
#       parts[3] = room          (e.g., Room A)

#     We parse that reliably using csv.reader (NOT string.split).
#     Then we explode meetings into one row per day.
#     """
#     line = _safe_as_csv(course_obj)

#     try:
#         parts = [p.strip() for p in _csv_split(line)]
#     except Exception:
#         # If parsing fails, fall back to a very conservative split
#         parts = [p.strip() for p in line.split(",")]

#     course_id = parts[0] if len(parts) > 0 else ""
#     faculty = parts[1] if len(parts) > 1 else ""
#     meetings_field = parts[2] if len(parts) > 2 else ""
#     room = parts[3] if len(parts) > 3 else ""

#     meetings = _explode_meetings(meetings_field)

#     # Lab: your current configs may include lab requirements, but this
#     # particular scheduler output doesn't provide a clean lab field.
#     lab = ""

#     rows: List[Dict[str, Any]] = []

#     # Meeting-level rows (MWF -> 3 rows)
#     for idx, (day, start) in enumerate(meetings, start=1):
#         rows.append(
#             {
#                 "schedule_id": schedule_id,
#                 "course_id": course_id,
#                 "day": day,
#                 "start": start,
#                 "room": room,
#                 "faculty": faculty,
#                 "lab": lab,
#                 "duration": "",
#                 "credits": "",
#                 "meeting_index": idx,
#             }
#         )

#     # If no meetings were parsed, still emit a single fallback row
#     if not rows:
#         rows.append(
#             {
#                 "schedule_id": schedule_id,
#                 "course_id": course_id,
#                 "day": "",
#                 "start": "",
#                 "room": room,
#                 "faculty": faculty,
#                 "lab": lab,
#                 "duration": "",
#                 "credits": "",
#                 "meeting_index": 1,
#             }
#         )

#     return rows

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

def _parse_course_line_to_flat_rows(schedule_id: int, course_obj: Any, cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
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
    lab = parts[3] if len(parts) > 3 else ""

    # Collect all meeting chunks (some outputs split them)
    meeting_chunks = parts[4:]
    meetings_field = ",".join(meeting_chunks)
    meetings = _explode_meetings(meetings_field)

    rows: List[Dict[str, Any]] = []

    for idx, (day, start, end, duration) in enumerate(meetings, start=1):
        rows.append({
            "schedule_id": schedule_id,
            "course_id": course_id,
            "day": day,
            "start": start,
            "room": room,
            "faculty": faculty,
            "lab": lab,
            "duration": duration,
            "credits": credits,
            "meeting_index": idx,
        })

    if not rows:
        rows.append({
            "schedule_id": schedule_id,
            "course_id": course_id,
            "day": "",
            "start": "",
            "room": room,
            "faculty": faculty,
            "lab": lab,
            "duration": "",
            "credits": credits,
            "meeting_index": 1,
        })

    return rows

def generate_schedules(cfg: Dict[str, Any], limit: int, optimize: bool) -> Iterator[List[Dict[str, Any]]]:
    """
    Runs the scheduler and returns flat meeting-level rows.

    IMPORTANT:
    - limit is the number of SCHEDULES (models) to produce, not number of rows.
    - optimize flag is passed through for future use (core optimization can be added later).
    """
    combined = CombinedConfig(**cfg)
    s = Scheduler(combined)


    # for schedule_id, schedule in enumerate(s.get_models(), start=1):
    #     schedule_rows: List[Dict[str, Any]]= []
    #     for course in schedule:
    #        schedule_rows.extend(_parse_course_line_to_flat_rows(schedule_id, course, cfg))

    #     yield schedule_rows

    #     if schedule_id >= limit:
    #         break

    for schedule_id, schedule in enumerate(s.get_models(), start=1):
        course_models = list(schedule)

        print(f"\n=== RAW SCHEDULER OUTPUT: schedule {schedule_id} ===")
        for course in course_models:
            print(_safe_as_csv(course))

        schedule_rows: List[Dict[str, Any]] = []
        for course in course_models:
            schedule_rows.extend(_parse_course_line_to_flat_rows(schedule_id, course, cfg))

        print(f"\n================ PROCESSED OUTPUT (Schedule {schedule_id}) ================")
        for row in schedule_rows:
            print(f"{row['course_id']} | {row['day']} {row['start']} | room={row['room']}")

        yield schedule_rows

        if schedule_id >= limit:
            break
