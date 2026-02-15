# Author(s): Antonio Corona, Tanner Ness, Jacob Karasow
# Date: 2026-2-15
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
# DAYS The days supported by the project.
DAYS = ["MON", "TUE", "WED", "THU", "FRI"]
# DEFAUILT_TIME_RANGE baseline availibilty when no custon time given.
DEFAULT_TIME_RANGE = "09:00-17:00"


# -----------------------------
# Appointment Defaults
# -----------------------------
def faculty_defaults(appointment_type: str) -> Tuple[int, int, int]:
    """
    Returns:
        (maximum_credits, minimum_credits, unique_course_limit)
    """

    # Normalizes input to avoid case issues
    t = appointment_type.lower()

    # Full-time defaults
    if t in {"full_time", "full-time", "fulltime"}:
        return (12, 6, 2)
    
    # Adjunct defaults
    if t == "adjunct":
        return (4, 0, 1)

    # If the type isn't recognized, fail fast that so CLI/tests catch it immediately
    raise ValueError(f"Unknown appointment type: {appointment_type}")


# -----------------------------
# Times Builder
# -----------------------------
def build_times(day: Optional[str], time_range: Optional[str]) -> Dict[str, List[str]]:
    """
    Build the "times" dictionary for a faculty member.

    Faculty schema expects:
      "times": {
        "MON": ["09:00-17:00"],
        "TUE": ["09:00-17:00"],
        ...
      }

        Parameters
    ----------
    day : Optional[str]
        A single day code like "TUE" if the user wants to override only one day.
        If None, no single-day override is applied.
    time_range : Optional[str]
        A time string like "13:00-16:00". Required if day is provided.

    Returns
    -------
    Dict[str, List[str]]
        A mapping from each weekday to a list of availability ranges.

    Behavior
    --------
    - If day and time_range are both None: return default 9–5 for all weekdays.
    - If only one of day/time_range is provided: error (incomplete specification).
    - If day/time_range provided: override that day only, keep defaults for other days.
    """

    # Starts with default times for all weekdays
    times = {d: [DEFAULT_TIME_RANGE] for d in DAYS}

    # No override requested → return defaults
    if day is None and time_range is None:
        return times

    # Partial override is invalid because it’s ambiguous
    if day is None or time_range is None:
        raise ValueError("If specifying day, you must also specify time range")
    
    # Normalize day and validate it
    day = day.upper()
    if day not in DAYS:
        raise ValueError(f"Invalid day {day}. Must be one of {DAYS}")

    # Minimal validation of "HH:MM-HH:MM" format
    if "-" not in time_range:
        raise ValueError("Time range must be HH:MM-HH:MM")

    # Apply override for the chosen day
    times[day] = [time_range]

    return times


# -----------------------------
# Preferences Parser
# -----------------------------
def parse_prefs(pref_args: Optional[List[str]]) -> List[Dict[str, Any]]:
    """
    Converts CLI pref args into config objects.

    CLI Input example:
        ["CS101:8", "CS201:5"]

    Stored Output Format:
        [
          {"course_id": "CS101", "weight": 8},
          {"course_id": "CS201", "weight": 5}
        ]
    
    Notes:
    - Preferences do not require the course to exist yet.
    - Weight is stored as an integer.
    - Invalid formats raise ValueError so CLI can show a clean error.
    """

    # If No preferences pass then -> store nothing
    if not pref_args:
        return []

    prefs = []  # Check this line (prefs: List[Dict[str, Any]] = [])

    for raw in pref_args:
        # Must contain ":" separating course_id and weight
        if ":" not in raw:
            raise ValueError("Preference must be COURSE:WEIGHT")

        course_id, weight_str = raw.split(":", 1)

        # Store standardized keys expected by config design
        prefs.append({
            "course_id": course_id.strip(),
            "weight": int(weight_str.strip())
        })

    return prefs


# -----------------------------
# Internal Helpers
# -----------------------------
def get_faculty_list(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Return the list cfg["config"]["faculty"], creating empty containers if missing.
    This keeps the rest of the code simple and avoids KeyError.
    """
    return cfg.setdefault("config", {}).setdefault("faculty", [])


def find_faculty_index(faculty_list: List[Dict[str, Any]], name: str) -> int:
    """
    Find a faculty member by name in a case-insensitive way.

    Returns;
    int
        Index of the faculty member if found, else -1.
    """
    name_lower = name.lower()

    for i, f in enumerate(faculty_list):
        # Normalize then compare the stored faculty "name"
        if str(f.get("name", "")).lower() == name_lower:
            return i

    return -1

# -----------------------------
# Course cleanup helper(s)
# -----------------------------
"""
Description: remove_faculty_helper remove all instances of the faculty member from courses.
Parameters:
    cfg -> the configuration file.
    name -> the name to remove.
Returns:
    Nothing.
"""
def remove_faculty_helper(cfg: Dict[str, Any], name: str) -> None:
    
    config = cfg.get('config', {})

    # Get courses list (default to empty list if missing)
    course_list = config.get('courses',[])

    # Normalizes the faculty name for case-insensitive comparison
    faculty_lower = name.lower()    
    
    # For each course, remove the deleted faculty from its faculty list
    for course in course_list:
        # IMPORTANT: this should default to [] not None, otherwise len(faculty) can crash
        faculty = course.get('faculty',)

        # Iterate by index and remove the first match
        for r in range(len(faculty)):
            if faculty[r].lower() == faculty_lower:
                faculty.pop(r)
                break


# -----------------------------
# CRUD Operations
# -----------------------------
def add_faculty(
    cfg: Dict[str, Any],
    name: str,
    appointment_type: str,
    day: Optional[str] = None,
    time_range: Optional[str] = None,
    prefs: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """
    Add a faculty member to cfg["config"]["faculty"].

    Enforces:
    - no duplicate faculty names
    - default credits/limits based on appointment_type
    - default times 9–5 unless overridden
    - optional preferences list
    """

    faculty_list = get_faculty_list(cfg)

    # Prevent duplicates by name
    if find_faculty_index(faculty_list, name) != -1:
        raise ValueError(f"Faculty '{name}' already exists")

    # Determine limits based on faculty type
    max_c, min_c, unique_limit = faculty_defaults(appointment_type)
    
    # Build times dictionary (defaults or day override)
    times = build_times(day, time_range)

    # Normalizes prefs
    if prefs is None:
        prefs = []

    # Faculty record stored in the config
    entry = {
        "name": name,
        "maximum_credits": max_c,
        "minimum_credits": min_c,
        "unique_course_limit": unique_limit,
        "times": times,
    }

    # Only store preferences if provided
    if prefs:
        entry["preferences"] = prefs

    # Add record to config list
    faculty_list.append(entry)


"""
Description: remove_faculty removes a faculty member from the config file.
Parameters : 
           cfg -> the config file.
           name -> the name of the faculty member to remove.
Returns    :
           Nothing
           If name does not exist in config file, returns ValueError.
"""
def remove_faculty(cfg: Dict[str, Any], name: str) -> None:
    
    faculty_list = get_faculty_list(cfg)

    index = find_faculty_index(faculty_list, name)


    match index:
        case -1:
            raise ValueError(f"Faculty {name} does not exist.")
        case _:
            faculty_list.pop(index)
            remove_faculty_helper(cfg, name)


def modify_faculty(
        cfg: Dict[str, Any],
        name: str, 
        appointment_type: Optional[str] = None,
        day: Optional[str] = None,             
        time_range: Optional[str] = None, 
        prefs: Optional[List[Dict[str, Any]]] = None, 
        maximum_credits: Optional[int] = None, 
        minimum_credits: Optional[int] = None,
        unique_course_limit: Optional[int] = None,
) -> None: 
    # Modify an existinf faculty member
    #
    # Only fields explicitly provided will be updated.
    # All others will remain unchanged.
    #
    # Raises: 
    #   ValueError if faculty does not exist
    faculty_list = get_faculty_list(cfg)
    index = find_faculty_index (faculty_list, name)

    if index == -1:
        raise ValueError(f"Faculty '{name}' does not exist")

    faculty = faculty_list[index]

    # ========== Update Appointment Type ==========
    if appointment_type:
        maximum_credits, minimum_credits, unique_course_limit = faculty_defaults(appointment_type)
        faculty["maximum_credits"] = maximum_credits
        faculty["minimum_credits"] = minimum_credits
        faculty["unique_course_limit"] = unique_course_limit

    # ========== Manual Credit overrides ==========
    if maximum_credits is not None:
        faculty["maximum_credits"] = maximum_credits

    if minimum_credits is not None:
        faculty["minimum_credits"] = minimum_credits

    if unique_course_limit is not None:
        faculty["unique_course_limit"] = unique_course_limit

    # ========== Update Availability ===========
    if day is not None or time_range is not None:
        faculty["times"] = build_times(day, time_range)

    # ========== Replace Preferences ==========
    if prefs is not None:
        faculty["preferences"] = prefs