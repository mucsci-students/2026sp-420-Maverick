# Author: Antonio Corona, Ian Swartz, Tanner Ness
# Date: 2026-03-05
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

# Tracks whether the user has explicitly selected a schedule via the dropdown
SESSION_USER_SELECTED_KEY = "viewer_user_selected"


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

def _get_user_selected() -> bool:
    """Returns True if user has made an explicit dropdown selection."""
    return bool(session.get(SESSION_USER_SELECTED_KEY, False))


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


# ------------------------------
# Direct Selection Operation
# ------------------------------

def select_schedule(index: int) -> None:
    """
    Directly sets the selected schedule index from the Viewer dropdown.

    Parameters:
        index (int):
            0-based schedule index submitted from the UI.

    Behavior:
        - If no schedules exist, this is a no-op.
        - The index is clamped to the valid range (0..len(schedules)-1)
          to prevent out-of-bounds access.
        - Updates the session-selected schedule index.
    """
    schedules = _get_schedules()

    # If no schedules exist, nothing to select
    if not schedules:
        return

    # Clamp index safely within valid bounds
    clamped = max(0, min(int(index), len(schedules) - 1))

    # Store new selected index in session
    session[SESSION_SELECTED_INDEX_KEY] = clamped

    # lock dropdown to selection in viewer
    session[SESSION_USER_SELECTED_KEY] = True


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

# Old import_schedules_from_file commented out
# def import_schedules_from_file(path: str):
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
    """
    with open(path, "r", encoding="utf-8") as f:
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
    """

# New import_schedules_from_file:
# app/web/services/schedule_service.py

def import_schedules_from_file(source):
    """
    Imports schedules from a JSON source and APPENDS them to the existing 
    session list. Returns a tuple of (number_added, new_total_count).
    """
    try:
        # 1. Parse the incoming data (Repo Path vs System Upload)
        if isinstance(source, str):
            with open(source, "r", encoding="utf-8") as f:
                new_data = json.load(f)
        else:
            # Handle files from System Upload with potential Notepad BOM
            raw_data = source.read().decode('utf-8-sig')
            new_data = json.loads(raw_data)

        # 2. Structural Validation: Ensure we have a list
        if not isinstance(new_data, list):
            # If the user uploaded a single schedule (dict), wrap it in a list
            new_data = [new_data]
        
        # Checks if the schedules are correctly formatted
        is_valid_file(new_data)


        added_count = len(new_data)

        # 3. Retrieve existing schedules from session (default to empty list)
        current_list = session.get(SESSION_SCHEDULES_KEY, [])

        # 4. APPEND: Add the new schedules to the end of the current list
        current_list.extend(new_data)

        # 5. Save and Update Navigation
        session[SESSION_SCHEDULES_KEY] = current_list
        new_total = len(current_list)
        
        # Set the viewer index to the last schedule added
        session[SESSION_SELECTED_INDEX_KEY] = new_total - 1
        
        # Mark session as modified so Flask saves the cookie
        session.modified = True

        return added_count, new_total

    except json.JSONDecodeError:
        raise ValueError("The selected file is not a valid JSON document.")
    except Exception as e:
        raise e

    # show placeholder initially
    session[SESSION_USER_SELECTED_KEY] = False 

# function for exporting a schedule(s) to a file
def get_schedules_for_export():
    """
    Returns the raw list of schedules from the session for browser download.
    """
    return _get_schedules()

# function for exporting the schedule(s) to a csv file
import csv
import io

def export_schedules_to_csv(indices: List[int]) -> str:
    """
    Converts selected schedules into a single CSV string.
    """
    schedules = _get_schedules()
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow(["Schedule #", "Course ID", "Faculty", "Room", "Lab", "Time"])
    
    for idx in indices:
        if 0 <= idx < len(schedules):
            assignments = schedules[idx].get("assignments", [])
            for a in assignments:
                writer.writerow([
                    idx + 1,
                    a.get("course_id", ""),
                    a.get("faculty", ""),
                    a.get("room", ""),
                    a.get("lab", ""),
                    a.get("time", "")
                ])
    
    return output.getvalue()


# Checks the file being imported fits the general schema of the configuration file.
def is_valid_file(data: List) -> None:
    Scheduleschema = Schema()
    try:
        # checks if data's schema matches 
        for d in data:
            Scheduleschema.model_validate(d)
        
    except ValidationError as e:
        raise ValueError(f"Invalid file: {json.dumps(e.errors(), indent = 2)}")

# returns the schema of a configured json file
def Schema():

    class Assignments(BaseModel):
        course_id: str
        credits: str
        day: Literal["MON", "TUE", "WED", "THU", "FRI"]
        duration: str
        faculty: str
        lab: Optional[str] = None
        meeting_index: int
        room: str
        schedule_id: int
        start: str
        time: str
    
    class Meta(BaseModel):
        generated_at: str
        optimizer_flags:  Optional[List[str]] = None
        row_count: int
        schedule_id: int

    class ScheduleSchema(BaseModel):
        assignments: List[Assignments]
        meta: Meta
        
    return ScheduleSchema


# Helper function that makes it so that only schedules without time conflicts 
# can be made into visual schedules
def _check_for_conflicts(assignments: List[Dict]) -> bool:
    """Checks if any assignments in the list overlap in time."""
    for i, a in enumerate(assignments):
        # Convert start time "HH:MM" to minutes from midnight
        try:
            h, m = map(int, a['start'].split(':'))
            a_start = h * 60 + m
            a_end = a_start + int(a['duration'])
        except (ValueError, KeyError):
            continue

        for j, other in enumerate(assignments):
            if i == j: continue
            if a['day'].strip().upper() != other['day'].strip().upper():
                continue
            
            try:
                oh, om = map(int, other['start'].split(':'))
                o_start = oh * 60 + om
                o_end = o_start + int(other['duration'])
                
                # Standard overlap formula: (StartA < EndB) and (EndA > StartB)
                if a_start < o_end and a_end > o_start:
                    return True
            except (ValueError, KeyError):
                continue
    return False

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
                "by_lab": grouped assignments by lab,
                "by_faculty": grouped assignments by faculty,
                "has_schedules": bool,
                "is_first": bool,
                "is_last": bool
                "user_selected": user_selected,
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
    user_selected = _get_user_selected()

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
        "by_lab": _group_by(assignments, "lab"),
        "by_faculty": _group_by(assignments, "faculty"),

        # Navigation state for disabling Prev/Next in the template
        "has_schedules": has_schedules,
        "is_first": is_first,
        "is_last": is_last,

        # Created for the visual view export
        "has_conflicts": _check_for_conflicts(assignments)
    }