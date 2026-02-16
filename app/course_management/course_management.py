# Author: Antonio Coroan, Tanner Ness, Jacob Karasow
# Date: 2026-2-15
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
Description: remove_course removes a given course from the config file. 
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
Description: remove_course_helper removes the course from faculty -> 'course_preferences'.
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

        prefs = cse.get("preferences") or []
        cse["preferences"] = [p for p in prefs if str(p.get("course_id","")).lower() != course_lower]

        for r in list(course_prefs):
            if r.lower() == course_lower:
                course_prefs.pop(r, None)
                break


"""
Description: find_conflict_index checks if a course exists in a conflict list or not.
Parameters :
           conflict_list -> the list of conflicts.
           conflict_name -> the name of the conflict to find.
Returns    :
           If the conflict exists in the list, returns the index
           Otherwise, returns -1.
"""
def find_conflict_index(conflict_list: List[str], conflict_name: str) -> int:
    name_lower = conflict_name.lower()

    for index, conflict in enumerate(conflict_list):
        # case insensitive
        if conflict.lower() == name_lower:
            return index

    return -1

def _norm_course_id(course_id: str) -> str:
    return str(course_id or "").strip()


def _norm_course_id_lower(course_id: str) -> str:
    return _norm_course_id(course_id).lower()


def _get_course(cfg: Dict[str, Any], course_id: str) -> Dict[str, Any]:
    """Return the course dict for course_id or raise."""
    courses = get_course_list(cfg)
    idx = find_course_index(courses, course_id)
    if idx == -1:
        raise ValueError(f"Course '{course_id}' does not exist.")
    return courses[idx]


def _ensure_conflicts_list(course: Dict[str, Any]) -> List[str]:
    """Ensures the conflicts key exists and is a list. Returns the list."""
    conflicts = course.get("conflicts")
    if conflicts is None:
        course["conflicts"] = []
        return course["conflicts"]
    if not isinstance(conflicts, list):
        raise ValueError("Course 'conflicts' must be a list in config.")
    return conflicts


"""
Decription: Adds a confict to a given course.
Parameters:
          cfg -> the config file.
          course -> the course to add the conflict to.
          conflict -> the conflict to add
Returns   :
          Nothing.
"""
def add_conflict(
    cfg: Dict[str, Any],
    course_id: str,
    conflict_course_id: str,
    symmetric: bool = True,
) -> None:
    """
    Add a conflict to a course.

    - Prevents duplicates (case-insensitive)
    - Prevents self-conflict
    - If symmetric=True and conflict course exists, also adds the reverse conflict
    """
    course_id = _norm_course_id(course_id)
    conflict_course_id = _norm_course_id(conflict_course_id)

    if not course_id or not conflict_course_id:
        raise ValueError("course_id and conflict_course_id cannot be empty")

    if _norm_course_id_lower(course_id) == _norm_course_id_lower(conflict_course_id):
        raise ValueError("A course cannot conflict with itself")

    course = _get_course(cfg, course_id)
    conflicts = _ensure_conflicts_list(course)

    # already present?
    if find_conflict_index(conflicts, conflict_course_id) != -1:
        raise ValueError(f"Conflict '{conflict_course_id}' already exists in course '{course_id}'.")

    conflicts.append(conflict_course_id)

    # Optional: enforce symmetry only if the other course exists
    if symmetric:
        other_idx = find_course_index(get_course_list(cfg), conflict_course_id)
        if other_idx != -1:
            other = get_course_list(cfg)[other_idx]
            other_conflicts = _ensure_conflicts_list(other)
            if find_conflict_index(other_conflicts, course_id) == -1:
                other_conflicts.append(course_id)


def remove_conflict(
    cfg: Dict[str, Any],
    course_id: str,
    conflict_course_id: str,
    symmetric: bool = True,
) -> None:
    """
    Remove a conflict from a course.

    - Requires conflict exists (case-insensitive)
    - If symmetric=True and conflict course exists, also removes reverse conflict
    """
    course_id = _norm_course_id(course_id)
    conflict_course_id = _norm_course_id(conflict_course_id)

    if not course_id or not conflict_course_id:
        raise ValueError("course_id and conflict_course_id cannot be empty")

    course = _get_course(cfg, course_id)
    conflicts = _ensure_conflicts_list(course)

    idx = find_conflict_index(conflicts, conflict_course_id)
    if idx == -1:
        raise ValueError(f"Conflict '{conflict_course_id}' does not exist in course '{course_id}'.")

    conflicts.pop(idx)

    if symmetric:
        other_idx = find_course_index(get_course_list(cfg), conflict_course_id)
        if other_idx != -1:
            other = get_course_list(cfg)[other_idx]
            other_conflicts = _ensure_conflicts_list(other)

            rev_idx = find_conflict_index(other_conflicts, course_id)
            if rev_idx != -1:
                other_conflicts.pop(rev_idx)


def modify_conflict(
    cfg: Dict[str, Any],
    course_id: str,
    old_conflict_course_id: str,
    new_conflict_course_id: str,
    symmetric: bool = True,
) -> None:
    """
    Modify a conflict on a course: replace old -> new.

    Equivalent to:
      remove_conflict(course_id, old)
      add_conflict(course_id, new)

    but done in a single operation with proper validation.
    """
    course_id = _norm_course_id(course_id)
    old_conflict_course_id = _norm_course_id(old_conflict_course_id)
    new_conflict_course_id = _norm_course_id(new_conflict_course_id)

    if not course_id or not old_conflict_course_id or not new_conflict_course_id:
        raise ValueError("course_id, old_conflict_course_id, new_conflict_course_id cannot be empty")

    if _norm_course_id_lower(course_id) == _norm_course_id_lower(new_conflict_course_id):
        raise ValueError("A course cannot conflict with itself")

    course = _get_course(cfg, course_id)
    conflicts = _ensure_conflicts_list(course)

    old_idx = find_conflict_index(conflicts, old_conflict_course_id)
    if old_idx == -1:
        raise ValueError(
            f"Conflict '{old_conflict_course_id}' does not exist in course '{course_id}'."
        )

    # prevent duplicates
    if find_conflict_index(conflicts, new_conflict_course_id) != -1:
        raise ValueError(
            f"Conflict '{new_conflict_course_id}' already exists in course '{course_id}'."
        )

    # replace in place (keeps list order stable)
    conflicts[old_idx] = new_conflict_course_id

    if symmetric:
        # Remove reverse old conflict if other course exists
        old_other_idx = find_course_index(get_course_list(cfg), old_conflict_course_id)
        if old_other_idx != -1:
            old_other = get_course_list(cfg)[old_other_idx]
            old_other_conflicts = _ensure_conflicts_list(old_other)
            rev_idx = find_conflict_index(old_other_conflicts, course_id)
            if rev_idx != -1:
                old_other_conflicts.pop(rev_idx)

        # Add reverse new conflict if other course exists
        new_other_idx = find_course_index(get_course_list(cfg), new_conflict_course_id)
        if new_other_idx != -1:
            new_other = get_course_list(cfg)[new_other_idx]
            new_other_conflicts = _ensure_conflicts_list(new_other)
            if find_conflict_index(new_other_conflicts, course_id) == -1:
                new_other_conflicts.append(course_id)  

def modify_course (
        cfg: Dict[str, Any], 
        course_id: str, 
        new_course_id: Optional[str] = None, 
        credits: Optional[int] = None, 
        room: Optional[str] = None, 
        lab: Optional[str] = None, 
        faculty: Optional[List[str]] = None, 
        conflicts: Optional[list[str]] = None, 
) -> None: 
    
    courses = get_course_list(cfg)
    index = find_course_index(courses, course_id)

    if index == -1:
        raise ValueError(f"Course '{course_id}' does not exist.")

    course = courses[index]

# ========== Rename Course ==========
    if new_course_id is not None:
        new_course_id = new_course_id.strip()
        if not new_course_id:
            raise ValueError("new_course_id cannot be empty")

        if find_course_index(courses, new_course_id) != -1:
            raise ValueError(f"Course '{new_course_id}' already exists")

        old_lower = course["course_id"].lower()
        course["course_id"] = new_course_id

    # update references...

    # Prevent duplicate IDs
    if find_course_index(courses, new_course_id) != -1:
        raise ValueError(f"Course '{new_course_id}' already exists")

    old_lower = course["course_id"].lower()

    # Update course_id
    course["course_id"] = new_course_id

    config = cfg.get("config", {})
    faculty_list = config.get("faculty", [])
    course_list = config.get("courses", [])

    # Update conflicts in other courses
    for c in course_list:
        conflict_list = c.get("conflicts", [])
        for i in range(len(conflict_list)):
            if conflict_list[i].lower() == old_lower:
                conflict_list[i] = new_course_id

    # Update faculty course_preferences
    for fac in faculty_list:
        prefs = fac.get("preferences") or []
        for p in prefs:
            if str(p.get("course_id","")).lower() == old_lower:
                p["course_id"] = new_course_id


    # ========== Update Credits ==========
    if credits is not None:
        if credits <= 0:
            raise ValueError("credits must be a positive integer")
        course["credits"] = int(credits)

    # ========== Update Room ==========
    if room is not None:
        room = room.strip()
        if not room:
            raise ValueError("room cannot be empty")

        rooms = _get_rooms(cfg)
        if room not in rooms:
            raise ValueError(f"Room '{room}' does not exist in config.rooms")

        course["room"] = [room]

    # ========== Update Lab ==========
    if lab is not None:
        labs = _get_labs(cfg)

        lab = lab.strip()
        if lab:
            if lab not in labs:
                raise ValueError(f"Lab '{lab}' does not exist in config.labs")
            course["lab"] = [lab]
        else:
            # empty string clears lab
            course["lab"] = []

    # ========== Replace Faculty List ==========
    if faculty is not None:
        existing_faculty = set(_get_faculty_names(cfg))
        cleaned = [f.strip() for f in faculty if f.strip()]
        missing = [f for f in cleaned if f not in existing_faculty]

        if missing:
            raise ValueError(f"Faculty not found in config.faculty: {missing}")

        course["faculty"] = cleaned

    # ========== Replace Conflicts List ==========
    if conflicts is not None:
        cleaned_conflicts = [c.strip() for c in conflicts if c.strip()]
        course["conflicts"] = cleaned_conflicts