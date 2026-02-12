# Author: Antonio Coroan, Tanner Ness
# Date: 2026-2-11
"""
course_management.py

Service module for Course Management operations.

Implements business logic for adding, modifying, and deleting courses,
as well as managing course conflicts within the scheduler configuration.

Related User Stories:
    A2 — Course Management and Conflict Handling
"""

# Use typing so funcitons are self-documenting and test are easier ot write.
from typing import Any, Dict, List, Optional


# JSON config gets loaded in a Python dict via (cfg).
# The courses are found at/live at: cfg["config"]["courses"]
#
# This helper function ensures that the path exists and returns the list of course dicts. 
def get_course_list(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    # .setdefault ensures it exists or creates it
    return cfg.setdefault("config", {}).setdefault("courses", [])

# The config indentifies courses by "course_id" (ex. "CS101").
# Prevent duplicates and supports modify/delete
def find_course_index(courses: List[Dict[str, Any]], course_id: str) -> int:
    # Normalizes the course id so matching is case_insensitive and whitespace-safe.
    cid = course_id.strip().lower()

    # Scans the list and looks for a matching "course_id"
    for i, c in enumerate(courses):
        # Obtains "course_id" or defaults, normalizes and compares.
        if str(c.get("course_id", "")).strip().lower() == cid:
            return i

    # -1 means "not found"
    return -1

# Ensures rooms list exists and returns it.
def _get_rooms(cfg: Dict[str, Any]) -> List[str]:
    return cfg.setdefault("config", {}).setdefault("rooms", [])

# Ensures labs list exists and returns it.
def _get_labs(cfg: Dict[str, Any]) -> List[str]:
    return cfg.setdefault("config", {}).setdefault("labs", [])

# Faculty list is a list of dicts. This extracts the "name" values.
def _get_faculty_names(cfg: Dict[str, Any]) -> List[str]:
    fac = cfg.setdefault("config", {}).setdefault("faculty", [])
    return [str(f.get("name", "")).strip() for f in fac]


# -----------------------------
# Course Add 
# -----------------------------
# Current schema expects these keys on every course:
#
#   course_id: string
#   credits: int
#   room: list[str]        <-- note: list, even if only one room
#   lab: list[str]         <-- list, can be empty
#   conflicts: list        <-- default []
#   faculty: list[str]     <-- can be empty
#
# This function adds a new course dict into cfg["config"]["courses"].

def add_course(
    cfg: Dict[str, Any],
    course_id: str,
    credits: int,
    room: str,
    lab: Optional[str] = None,
    faculty: Optional[List[str]] = None,
) -> None:
    """
    Adds a new course to cfg["config"]["courses"] with required fields + defaults.

    Stored schema:
      {
        "course_id": "...",
        "credits": int,
        "room": ["Room A"],
        "lab": ["Lab 1"] or [],
        "conflicts": [],
        "faculty": ["Dr. Smith"] or []
      }
    """
    # -----------------------------
    # Input Validations (fail fast)
    # -----------------------------
    # Strip whitespace so " CS101 " becomes "CS101"
    course_id = course_id.strip()

    # No empty course IDs allowed.
    if not course_id:
        raise ValueError("course_id cannot be empty")

    # credits must be positive.
    if credits <= 0:
        raise ValueError("credits must be a positive integer")

    # room is required and must not be empty.
    room = room.strip()
    if not room:
        raise ValueError("room cannot be empty")
        
    # -----------------------------
    # Duplicate prevention
    # -----------------------------
    # Get the existing course list.
    courses = get_course_list(cfg)

    # If this course_id already exists, reject.
    if find_course_index(courses, course_id) != -1:
        raise ValueError(f"Course '{course_id}' already exists")

    # -----------------------------
    # Validate the room exists
    # -----------------------------
    # Config has a master room list: cfg["config"]["rooms"]
    rooms = _get_rooms(cfg)

    # If the provided room isn't in that list, reject.
    if room not in rooms:
        raise ValueError(f"Room '{room}' does not exist in config.rooms")

    # -----------------------------
    # Validate lab (optional)
    # -----------------------------
    labs = _get_labs(cfg)

    # This will become the stored "lab": [...]
    labs_list: List[str] = []

    # If lab was passed, validate it exists in cfg["config"]["labs"]
    if lab is not None:
        lab = lab.strip()

        # If they passed an empty string, treat as "no lab"
        if lab:
            if lab not in labs:
                raise ValueError(f"Lab '{lab}' does not exist in config.labs")

            # Schema expects list, so wrap it.
            labs_list = [lab]

    # --------------------------------------
    # Validate faculty references (optional)
    # --------------------------------------
    faculty_list: List[str] = []

    # If faculty was provided, it should be a list of names.
    if faculty:
        # Build a set of known faculty names from cfg["config"]["faculty"]
        existing_faculty = set(_get_faculty_names(cfg))

        # Clean input: strip whitespace and drop empties
        cleaned = [f.strip() for f in faculty if f.strip()]

        # Find any names not present in existing faculty set
        missing = [f for f in cleaned if f not in existing_faculty]

        # If any are missing, reject.
        if missing:
            raise ValueError(f"Faculty not found in config.faculty: {missing}")

        # Store cleaned list in course entry.
        faculty_list = cleaned

    # -------------------------------------
    # Create the course entry with defaults
    # -------------------------------------
    # This matches the dev config schema exactly.
    entry: Dict[str, Any] = {
        "course_id": course_id,
        "credits": int(credits),

        # IMPORTANT: schema expects list[str] for room and lab
        "room": [room],
        "lab": labs_list,

        # Defaults expected by scheduler configs
        "conflicts": [],
        "faculty": faculty_list,
    }

    # Append the new course to the config list.
    courses.append(entry)


"""
Description: Removes a given course from the config file. 
Parameters : 
           cfg -> the config file.
           course -> the course to remove.
Returns    :
           Nothing.
"""
def remove_course(cfg: Dict[str, Any], course: str) -> None:
    course_list = get_course_list(cfg)

    index = find_course_index(course_list, course)

    match index:
        case -1:
            raise ValueError(f"Course {course} does not exist or list is empty.")
        case _:
            course_list.pop(index)
            remove_course_helper(cfg, course)

"""
Description: Removes the course from faculty -> 'course_preferences'.
Parameters :
           cfg -> the config file.
           course -> the course to remove
Returns    :
           Nothing
"""
def remove_course_helper(cfg: Dict[str, Any], course: str) -> None:
    
    config = cfg.get('config', {})

    course_list = config.get('courses',[])

    faculty_list = config.get('faculty',[])

    course_lower = course.lower()

    # removes any instances of the course in courses -> 'conflicts' if it exists.
    for course in course_list:

        conflicts = course.get('conflicts', [])

        for c in range(len(conflicts)):
            if conflicts[c].lower() == course_lower:
                conflicts.pop(c)
                break

    # Removes the instance of room in faculty -> 'course_preferences' if it exists.
    for cse in faculty_list:

        course_prefs = cse.get('course_preferences', {})

        for r in list(course_prefs):
            if r.lower() == course_lower:
                course_prefs.pop(r, None)
                break