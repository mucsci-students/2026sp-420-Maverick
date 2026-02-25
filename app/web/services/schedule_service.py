# Author: Antonio Corona
# Date: 2026-02-24
"""
Schedule Viewing Service

Purpose:
    Provides business logic for the Schedule Viewer portion of the Flask GUI.
    This service is responsible for:
        - Navigating between generated schedules stored in session state
        - Preparing tabular/grouped views (by Room/Lab and by Faculty)
        - Importing/exporting schedule sets as JSON files

Architectural Role (MVC):
    - Acts as part of the Model layer.
    - Owns schedule viewer state (selected schedule index) via Flask session.
    - Prepares data structures that are easy for the View layer to render.

High-Level Responsibilities:
    1. Maintain navigation state (current schedule index).
    2. Provide access to session-backed schedule data.
    3. Transform assignment rows into grouped table structures.
    4. Support JSON import/export for portability.    

Design Notes:
    - Schedules are stored in session under SESSION_SCHEDULES_KEY as a list.
    - The currently selected schedule is tracked by index under
      SESSION_SELECTED_INDEX_KEY.
    - Import/export uses JSON for portability and simplicity.
    - All access to session state is funneled through helper functions
      to centralize logic.
"""

# app/web/services/schedule_service.py

# ------------------------------
# Imports
# ------------------------------

import json                    # Serialize/deserialize schedules to/from JSON
from flask import session      # Per-user session storage (viewer state + schedules)
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, ValidationError

# ------------------------------
# Session Keys (Viewer State)
# ------------------------------

# Stores the list of generated/imported schedules in the Flask session
# Each element is expected to follow the structure produced by run_service.
SESSION_SCHEDULES_KEY = "schedules"

# Stores the currently selected schedule index for navigation
SESSION_SELECTED_INDEX_KEY = "selected_schedule_index"


# ------------------------------
# Session Access Helpers
# ------------------------------

def _get_schedules():
    """
    Retrieves the list of schedules from session.

    Returns:
        list:
            A list of schedule objects (or an empty list if none exist).
    """
    return session.get(SESSION_SCHEDULES_KEY, [])


def _get_index():
    """
    Retrieves the current selected schedule index from session.

    Returns:
        int:
            The selected schedule index. Defaults to 0 if missing/invalid.
    """
    # The `or 0` guards against None/""
    return int(session.get(SESSION_SELECTED_INDEX_KEY, 0) or 0)


# ------------------------------
# Navigation Operations
# ------------------------------

def next_schedule():
    """
    Advances the selected schedule index forward by one.

    Behavior:
        - Clamped to the last schedule index.
        - No-op if no schedules are loaded.

    Side Effects:
        - Updates SESSION_SELECTED_INDEX_KEY in session.
    """
    schedules = _get_schedules()

    if not schedules:
        # Nothing to navigate - safely exit
        return

    # Clamp to valid range: 0..len(schedules)-1
    index = min(_get_index() + 1, len(schedules) - 1)
    session[SESSION_SELECTED_INDEX_KEY] = index


def prev_schedule():
    """
    Moves the selected schedule index backward by one.

    Behavior:
        - Clamped to zero.
        - No-op if no schedules are loaded.

    Side Effects:
        - Updates SESSION_SELECTED_INDEX_KEY in session.
    """
    schedules = _get_schedules()
    
    if not schedules:
        # Nothing to navigate - safely exit
        return

    # Clamp to valid range: 0..len(schedules)-1
    index = max(_get_index() - 1, 0)
    session[SESSION_SELECTED_INDEX_KEY] = index


# -------------------------------------------------------------------------
# Import / Export Operations (Just initial/temp/placeholder code for now )
# -------------------------------------------------------------------------

def export_schedules_to_file(path: str):
    """
    Exports the schedules currently stored in session to a JSON file.

    Parameters:
        path (str):

    Notes:
        - Produces human-readable JSON.
        - Intended for sharing, or debugging.
        - Does NOT modify session state.
    """
    schedules = _get_schedules()

    # Persist a human-readable JSON representation for easy sharing/debugging
    with open(path, "w", encoding="utf-8") as f:
        json.dump(schedules, f, indent=2)

# Disables the 'Export Schedules' button if there are no schedules to export.
def is_export_enabled() -> bool:
    count = len(_get_schedules())
    return count != 0



def import_schedules_from_file(path: str):
    """
    Imports schedules from a JSON file and loads them into session.

    Parameters:
        path (str):
            Source file path containing a JSON list of schedule objects.

    Raises:
        ValueError:
            If the loaded JSON is not a list (expected top-level structure).

    Side Effects:
        - Overwrites session schedules
        - Resets selected index to 0 (first schedule)
    """
    with open('./configs/config_base.json', "r", encoding="utf-8") as f:
        schedules = json.load(f)


    # Basic structural validation: the Viewer expects a list of schedules
    if not isinstance(schedules, list):
        raise ValueError("Imported schedules file must contain a JSON list.")
    
    # in-depth validation of each schedule's structure against the schema.
    scheduleschema = Schema()
    for s in schedules:
        is_valid_file(s, scheduleschema)

    is_export_enabled()

    session[SESSION_SCHEDULES_KEY] = schedules

    # Reset navigation to first schedule for consistency.
    session[SESSION_SELECTED_INDEX_KEY] = 0


# Checks the file being imported fits the general schema of the configuration file.
# TODO
def is_valid_file(schedule: Dict[str, Any], scheduleschema) -> None:
    try:
        # checks if schedules' schema matches 
        scheduleschema.model_validate(schedule)
        print("valid)")
    except ValidationError as e:
        raise ValueError(f"Invalid file: {e}")

# returns the schema of a properly configured json file
# TODO
def Schema():

    class Course(BaseModel):
        course_id: str
        credits: int
        room: List[str]
        lab: Optional[List[str]] = None
        conflicts: Optional[List[str]] = None
        faculty: List[str]

    class Faculty(BaseModel):
        name: str
        maximum_credits: int
        minimum_credits: int
        unique_course_limit: int
        maximum_days: Optional[int] = None
        mandatory_days: Optional[List[str]] = None
        times: Dict[str, List[str]]
        course_preferences: Optional[Dict[str, int]] = None
        room_preferences: Optional[Dict[str, int]] = None
        lab_preferences: Optional[Dict[str, int]] = None

    class Meeting(BaseModel):
        day: Literal["MON", "TUE", "WED", "THU", "FRI"]
        duration: int
        lab: Optional[bool] = None

    class Class(BaseModel):
        credits: int
        meetings: List[Meeting]
        start_time: Optional[str] = None
        disabled: Optional[bool] = None
    
    class TimeSlot(BaseModel):
        start: str
        spacing: int
        end: str

    class TimeSlotConfig(BaseModel):
        times: Dict[Literal["MON", "TUE", "WED", "THU", "FRI"], List[TimeSlot]]
        classes: List[Class]

    class Config(BaseModel):
        rooms: List[str]
        labs: List[str]
        courses: List[Course]
        faculty: List[Faculty]

    class ScheduleSchema(BaseModel):
        config: Config
        time_slot_config: TimeSlotConfig
        limit: int
        optimizer_flags: List[str]
        
    return ScheduleSchema

# ------------------------------
# Viewer Grouping Helpers
# ------------------------------

def _group_by(assignments, key):
    """
    Groups assignment rows by a specific field for tabular rendering.

    Parameters:
        assignments (list[dict]):
            Flat list of assignment dicts for the current schedule.
        key (str):
            Field name to group by (e.g., 'room', 'faculty').

    Returns:
        dict[str, list[dict]]:
            Mapping from group name -> list of assignments in that group.

    UI Purpose:
        Enables tabular rendering grouped by:
            - Room / Lab
            - Faculty

    Notes:
        - Missing keys are grouped under 'Unknown' to keep the UI stable & to prevent template errors.
    """
    grouped = {}
    for a in assignments:
        k = a.get(key, "Unknown")
        grouped.setdefault(k, []).append(a)
    return grouped


# ------------------------------
# Core Viewer Data Function
# ------------------------------

def get_view_data():
    """
    Builds the complete data bundle needed by the Schedule Viewer UI.

    Returns:
        dict:
            {
                "count": total number of schedules,
                "index": currently selected index,
                "current_meta": metadata for selected schedule,
                "assignments": flat assignment list,
                "by_room": grouped assignments by room,
                "by_faculty": grouped assignments by faculty,
                "has_schedules": bool,
                "is_first": bool,
                "is_last": bool
            }

    Architectural Intent:
        - This function acts as a View adapter.
        - It centralizes all session-derived state.
        - It computes navigation flags for template logic.
        - It ensures safe defaults when no schedules exist.

    Design Notes:
        - Index bounds are validated.
        - Missing schedules return empty-safe structures.
    """

    # ------------------------------
    # 1. Retrieve Session State
    # ------------------------------

    schedules = _get_schedules()
    index = _get_index()

    count = len(schedules)
    has_schedules = count > 0

    # ------------------------------
    # 2. Resolve Current Schedule
    # ------------------------------

    # Pick the current schedule only if the index is valid
    current = schedules[index] if schedules and 0 <= index < len(schedules) else None

    # Assignments are stored under the "assignments" key (same shape as run_service output)
    assignments = (current or {}).get("assignments", [])

    # ------------------------------
    # 3. Compute Navigation Flags
    # ------------------------------

    # Compute navigation state flags for the View layer
    is_first = has_schedules and index == 0
    is_last = has_schedules and index == (count - 1)

    # ------------------------------
    # 4. Build View Model
    # ------------------------------

    return {
        "count": len(schedules),
        "index": index,
        "current_meta": (current or {}).get("meta", {}),
        "assignments": assignments,

        # Tabular groupings for the Viewer: Rooms/Labs and Faculty
        "by_room": _group_by(assignments, "room"),
        "by_faculty": _group_by(assignments, "faculty"),

        # Navigation state for disabling Prev/Next in the template
        "has_schedules": has_schedules,
        "is_first": is_first,
        "is_last": is_last,
    }