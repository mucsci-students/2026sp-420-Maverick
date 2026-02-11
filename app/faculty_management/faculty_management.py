# Author: Antonio Corona
# Date: 2026-2-10
"""
faculty_management.py

Service module for Faculty Management operations.

Implements business logic for adding, modifying, and deleting faculty members,
as well as managing faculty availability and course preferences.

Related User Stories:
    A1 — Faculty Management
"""

from typing import Any, Dict, List, Optional, Tuple

# -----------------------------
# Constants
# -----------------------------
DAYS = ["MON", "TUE", "WED", "THU", "FRI"]
DEFAULT_TIME_RANGE = "09:00-17:00"


# -----------------------------
# Appointment Defaults
# -----------------------------
def faculty_defaults(appointment_type: str) -> Tuple[int, int, int]:
    """
    Returns:
        (maximum_credits, minimum_credits, unique_course_limit)
    """

    t = appointment_type.lower()

    if t in {"full_time", "full-time", "fulltime"}:
        return (12, 6, 2)

    if t == "adjunct":
        return (4, 0, 1)

    raise ValueError(f"Unknown appointment type: {appointment_type}")


# -----------------------------
# Times Builder
# -----------------------------
def build_times(day: Optional[str], time_range: Optional[str]) -> Dict[str, List[str]]:
    """
    Builds times block like:
    {
      "MON": ["09:00-17:00"],
      ...
    }
    """

    times = {d: [DEFAULT_TIME_RANGE] for d in DAYS}

    if day is None and time_range is None:
        return times

    if day is None or time_range is None:
        raise ValueError("If specifying day, you must also specify time range")

    day = day.upper()

    if day not in DAYS:
        raise ValueError(f"Invalid day {day}. Must be one of {DAYS}")

    if "-" not in time_range:
        raise ValueError("Time range must be HH:MM-HH:MM")

    times[day] = [time_range]

    return times


# -----------------------------
# Preferences Parser
# -----------------------------
def parse_prefs(pref_args: Optional[List[str]]) -> List[Dict[str, Any]]:
    """
    Converts CLI pref args into config objects.

    Input example:
        ["CS101:8", "CS201:5"]

    Output:
        [
          {"course_id": "CS101", "weight": 8},
          {"course_id": "CS201", "weight": 5}
        ]
    """

    if not pref_args:
        return []

    prefs = []

    for raw in pref_args:
        if ":" not in raw:
            raise ValueError("Preference must be COURSE:WEIGHT")

        course_id, weight_str = raw.split(":", 1)

        prefs.append({
            "course_id": course_id.strip(),
            "weight": int(weight_str.strip())
        })

    return prefs


# -----------------------------
# Internal Helpers
# -----------------------------
def get_faculty_list(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    return cfg.setdefault("config", {}).setdefault("faculty", [])


def find_faculty_index(faculty_list: List[Dict[str, Any]], name: str) -> int:
    name_lower = name.lower()

    for i, f in enumerate(faculty_list):
        if str(f.get("name", "")).lower() == name_lower:
            return i

    return -1


# -----------------------------
# CRUD Operations
# -----------------------------
def add_faculty(
    cfg: Dict[str, Any],
    name: str,
    appointment_type: str,
    day: Optional[str],
    time_range: Optional[str],
    prefs: List[Dict[str, Any]],
) -> None:

    faculty_list = get_faculty_list(cfg)

    if find_faculty_index(faculty_list, name) != -1:
        raise ValueError(f"Faculty '{name}' already exists")

    max_c, min_c, unique_limit = faculty_defaults(appointment_type)
    times = build_times(day, time_range)

    entry = {
        "name": name,
        "maximum_credits": max_c,
        "minimum_credits": min_c,
        "unique_course_limit": unique_limit,
        "times": times,
    }

    if prefs:
        entry["preferences"] = prefs

    faculty_list.append(entry)