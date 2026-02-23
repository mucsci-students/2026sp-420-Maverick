# Author: Antonio Corona
# Date: 2026-02-22
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

Design Notes:
    - Schedules are stored in session under SESSION_SCHEDULES_KEY as a list.
    - The currently selected schedule is tracked by index under
      SESSION_SELECTED_INDEX_KEY.
    - Import/export uses JSON for portability and simplicity.
"""

# app/web/services/schedule_service.py

# ------------------------------
# Imports
# ------------------------------

import json                    # Serialize/deserialize schedules to/from JSON
from flask import session      # Per-user session storage (viewer state + schedules)


# ------------------------------
# Session Keys (Viewer State)
# ------------------------------

# Stores the list of generated/imported schedules in the Flask session
SESSION_SCHEDULES_KEY = "schedules"

# Stores the currently selected schedule index for navigation
SESSION_SELECTED_INDEX_KEY = "selected_schedule_index"


# ------------------------------
# Session Access Helpers
# ------------------------------

def _get_schedules():
    """
    Fetches the schedules list from session.

    Returns:
        list:
            A list of schedule objects (or an empty list if none exist).
    """
    return session.get(SESSION_SCHEDULES_KEY, [])


def _get_index():
    """
    Fetches the current schedule index from session (safely coerced to int).

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
    Advances the selected schedule index by one, clamped to the last schedule.

    No-op if no schedules are loaded.
    """
    schedules = _get_schedules()
    if not schedules:
        # Nothing to navigate
        return

    # Clamp to valid range: 0..len(schedules)-1
    i = min(_get_index() + 1, len(schedules) - 1)
    session[SESSION_SELECTED_INDEX_KEY] = i


def prev_schedule():
    """
    Moves the selected schedule index back by one, clamped to zero.

    No-op if no schedules are loaded.
    """
    schedules = _get_schedules()
    if not schedules:
        # Nothing to navigate
        return

    # Clamp to valid range: 0..len(schedules)-1
    i = max(_get_index() - 1, 0)
    session[SESSION_SELECTED_INDEX_KEY] = i


# -------------------------------------------------------------------------
# Import / Export Operations (Just initial/temp/placeholder code for now )
# -------------------------------------------------------------------------

def export_schedules_to_file(path: str):
    """
    Exports the schedules currently stored in session to a JSON file.

    Parameters:
        path (str):
            Destination file path (written as UTF-8).
    """
    schedules = _get_schedules()

    # Persist a human-readable JSON representation for easy sharing/debugging
    with open(path, "w", encoding="utf-8") as f:
        json.dump(schedules, f, indent=2)


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
    with open(path, "r", encoding="utf-8") as f:
        schedules = json.load(f)

    # Basic validation: the Viewer expects a list of schedules
    if not isinstance(schedules, list):
        raise ValueError("Imported schedules file must contain a JSON list.")

    session[SESSION_SCHEDULES_KEY] = schedules
    session[SESSION_SELECTED_INDEX_KEY] = 0


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

    Notes:
        - Missing keys are grouped under 'Unknown' to keep the UI stable.
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
            A dictionary containing:
                - count: total number of schedules in session
                - index: currently selected schedule index
                - current_meta: metadata dict for the selected schedule
                - assignments: flat assignment list for the selected schedule
                - by_room: assignments grouped by room
                - by_faculty: assignments grouped by faculty

    Design Notes:
        - This function is coded defensively:
          if index is out of range or no schedules exist, it returns safe defaults.
        - The View layer can render "no schedules" state using count/current_meta.
    """
    schedules = _get_schedules()
    i = _get_index()

    # Pick the current schedule only if the index is valid
    current = schedules[i] if schedules and 0 <= i < len(schedules) else None

    # Assignments are stored under the "assignments" key (same shape as run_service output)
    assignments = (current or {}).get("assignments", [])

    return {
        "count": len(schedules),
        "index": i,
        "current_meta": (current or {}).get("meta", {}),
        "assignments": assignments,

        # Tabular groupings for the Viewer: Rooms/Labs and Faculty
        "by_room": _group_by(assignments, "room"),
        "by_faculty": _group_by(assignments, "faculty"),
    }