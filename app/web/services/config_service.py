# Author: Antonio Corona, Jacob Karasow, Tanner Ness
# Date: 2026-04-05

"""
config_service.py

Purpose:
    Provides the business logic for loading, saving, exporting, validating,
    and modifying the scheduler configuration used by the web interface.

Architectural Role (MVC):
    - Acts as part of the Model / Service layer in MVC.
    - Stores and retrieves the active working configuration from Flask session state.
    - Coordinates edits made through the Config Editor before they are persisted.
    - Validates config data before save/export/generation actions.
    - Tracks unsaved changes, conflict state, and schedule freshness.

High-Level Responsibilities:
    - Maintain the in-session working configuration
    - Load configuration from a repo path or browser-uploaded JSON file
    - Save the current configuration to disk
    - Export the current configuration as downloadable JSON
    - Apply sane defaults for time slot configuration
    - Detect lightweight configuration conflicts for UI feedback
    - Validate scheduler data before saving/exporting/generating
    - Expose service wrappers for faculty, room, lab, course, and conflict edits

Notes:
    - This module does not render templates or handle HTTP responses directly.
    - Routes/controllers call into this service to perform config-related actions.
"""

# ------------------------------
# Imports
# ------------------------------

# Standard library imports used for JSON parsing, file path handling,
# and safe deep-copying of configuration dictionaries.
import json
import os
import copy

# Flask session stores the user's active working configuration,
# editor state, and related UI flags.
from flask import session

from os import PathLike

# Faculty management operations from the domain/application layer.
from app.faculty_management.faculty_management import (
    add_faculty,
    remove_faculty,
    modify_faculty,
)

# Course + conflict management operations from the domain/application layer.
from app.course_management.course_management import (
    add_course,
    remove_course,
    modify_course,
    add_conflict,
    remove_conflict,
    modify_conflict,
)

# Room management operations.
from app.room_management.room_management import (
    add_room,
    remove_room,
    modify_room,
)

# Lab management operations.
from app.lab_management.lab_management import (
    add_lab,
    remove_lab,
    modify_lab,
)

# ================================================================
# Paths
# ================================================================

# Resolve the absolute path to the project root so config files can be
# accessed consistently regardless of where the app is launched from.
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../")
)

# The configs directory contains baseline, dev, test, and working configs.
CONFIGS_DIR = os.path.join(PROJECT_ROOT, "configs")

# working_config.json is the internal file mirror of the in-session config.
# It serves as a safe current snapshot of the config being edited in the GUI.
WORKING_PATH = os.path.join(CONFIGS_DIR, "working_config.json")


# ================================================================
# Session Keys
# ================================================================

# Session key for the actively edited scheduler configuration.
SESSION_CONFIG_KEY = "working_config"

# Session key for the currently loaded config path or uploaded filename.
SESSION_CONFIG_PATH_KEY = "working_path"

# Session key indicating whether the config has unsaved edits.
SESSION_UNSAVED_KEY = "unsaved_changes"

# Session key indicating whether schedules reflect the latest config state.
SESSION_SCHEDULES_UPDATED_KEY = "schedules_updated"

# Session key storing detected config conflicts for UI display.
SESSION_CONFLICTS_KEY = "config_conflicts"


# ================================================================
# Helper Functions
# ================================================================

def _ensure_configs_folder():
    if not os.path.exists(CONFIGS_DIR):
        os.makedirs(CONFIGS_DIR)


def _empty_config():
    """
    Build a blank scheduler configuration with safe defaults.

    Returns:
        dict:
            A minimal valid configuration structure containing:
            - empty faculty/course/room/lab collections
            - default limit value
            - empty optimizer flags
            - default time slot configuration
    """
    cfg =  {
        "config": {
            "faculty": [],
            "courses": [],
            "rooms": [],
            "labs": [],
        },
        "limit": 3,
        "optimizer_flags": [],
    }

    return apply_timeslot_defaults(cfg)


def _write_working_file(cfg):
    """
    Persist the current working configuration to working_config.json.

    Purpose:
        Keeps a disk copy of the in-session configuration for debugging,
        consistency, and internal fallback behavior.

    Args:
        cfg (dict): The scheduler configuration to write.
    """
    _ensure_configs_folder()
    with open(WORKING_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4)


def _set_unsaved(value: bool):
    session[SESSION_UNSAVED_KEY] = value


def get_unsaved():
    return session.get(SESSION_UNSAVED_KEY, False)


def set_schedules_updated(value: bool):
    session[SESSION_SCHEDULES_UPDATED_KEY] = value


def get_schedules_updated():
    return session.get(SESSION_SCHEDULES_UPDATED_KEY, False)

def normalize_time_entry(entry):
    if isinstance(entry, str):
        start, end = entry.split("-")
        return {
            "start_time": start.strip(), 
            "end_time": end.strip()
        }
    
    return {
        "start_time": entry.get("start_time", "").strip(),
        "end_time": entry.get("end_time", "").strip()
    }

def clean_time(s: str) -> str:
    return s.strip()

def normalize_cfg(cfg):
    """
    Normalizes ALL time formats in config:
    - faculty times
    - time_slot_config slots
    """

    cfg = copy.deepcopy(cfg)

    # --------------------------
    # Normalize faculty times
    # --------------------------
    for faculty in cfg.get("config", {}).get("faculty", []):
        for day, slots in faculty.get("times", {}).items():
            faculty["times"][day] = [
                normalize_time_entry(s) for s in slots
            ]

    # --------------------------
    # Normalize time slots
    # --------------------------
    tsc = cfg.get("time_slot_config", {})
    for day, slots in tsc.get("time_slots", {}).items():
        tsc["time_slots"][day] = [
            normalize_time_entry(s) for s in slots
        ]

    return cfg

# ================================================================
# Conflict Helpers
# ================================================================

def set_conflicts(conflicts):
    session[SESSION_CONFLICTS_KEY] = conflicts


def get_conflicts():
    return session.get(SESSION_CONFLICTS_KEY, [])


def has_conflicts():
    return len(get_conflicts()) > 0


# ================================================================
# Conflict Detection
# ================================================================

def detect_conflicts(cfg):

    conflicts = []
    config = cfg.get("config", {})

    faculty_names = set()
    room_names = set()
    lab_names = set()

    for f in config.get("faculty", []):
        name = f if isinstance(f, str) else f.get("name") if isinstance(f, dict) else None

        if not name:
            conflicts.append("Faculty member with missing name.")
            continue

        if name in faculty_names:
            conflicts.append(f"Duplicate faculty name: {name}")

        faculty_names.add(name)

    for r in config.get("rooms", []):
        name = r if isinstance(r, str) else r.get("name")

        if not name:
            conflicts.append("Room with missing name.")
            continue

        if name in room_names:
            conflicts.append(f"Duplicate room name: {name}")

        room_names.add(name)

    for l in config.get("labs", []):
        name = l if isinstance(l, str) else l.get("name")

        if not name:
            conflicts.append("Lab with missing name.")
            continue

        if name in lab_names:
            conflicts.append(f"Duplicate lab name: {name}")

        lab_names.add(name)

    for c in config.get("courses", []):

        cid = c.get("course_id")

        if not cid:
            conflicts.append("Course with missing course_id.")
            continue

        # Duplicate course_id values are allowed because they represent
        # multiple sections of the same course in scheduler input JSON.
        
    return conflicts


# ================================================================
# Working Config
# ================================================================

def _get_working_config():
    """
    Retrieve the active working configuration from session.

    Behavior:
        - If no config is currently loaded, create a blank default config
        - Write the working config snapshot to disk
        - Reset unsaved/schedule flags for this initial session setup

    Returns:
        dict: The active working configuration.
    """
    cfg = session.get(SESSION_CONFIG_KEY)

    # If nothing has been loaded yet, do NOT auto-create one
    if cfg is None:
        cfg = _empty_config()
    
    session[SESSION_CONFIG_KEY] = cfg

    # Keep the disk mirror in sync with session state.
    _write_working_file(cfg)

    # Initial retrieval should not count as a user edit.
    _set_unsaved(False)
    set_schedules_updated(False)

    return cfg


def _get_cgf():
    return _get_working_config()


def _commit_change(cfg):

    cfg = normalize_cfg(cfg)

    session[SESSION_CONFIG_KEY] = cfg

    _write_working_file(cfg)

    conflicts = detect_conflicts(cfg)
    set_conflicts(conflicts)

    _set_unsaved(True)
    set_schedules_updated(False)


# ================================================================
# Timeslot Defaults
# ================================================================

def apply_timeslot_defaults(cfg):
    if "time_slot_config" not in cfg:
        cfg["time_slot_config"] = {
            "days": ["MON", "TUE", "WED", "THU", "FRI"],
            "start_time": "08:00",
            "end_time": "17:00",
            "slot_length": 60
        }
    return cfg

def _ensure_time_slot_defaults(cfg):
    cfg = apply_timeslot_defaults(cfg)
    tsc = cfg.setdefault("time_slot_config", {})

    if "time_slots" not in tsc:
        tsc["time_slots"] = {
            day: [] for day in tsc.get("days", ["MON", "TUE", "WED", "THU", "FRI"])
        }
    
    if "patterns" not in tsc:
        tsc["patterns"] = []

    return cfg

def has_time_blocks(cfg):
    tsc = cfg.get("time_slot_config", {})
    time_slots = tsc.get("time_slots", {})
    
    return any(len(slots) > 0 for slots in time_slots.values())

# ================================================================
# Load / Save
# ================================================================

def load_config_into_session(source):
    """
    Load a scheduler configuration into session.

    Supported Sources:
        - A filesystem path (str or Path-like object) pointing to a JSON config file
        - An uploaded browser file object from request.files

    Workflow:
        - Detect whether the source is a path or uploaded file
        - Read and parse JSON content
        - Apply missing time slot defaults
        - Store config + metadata in session
        - Refresh working_config.json
        - Reset unsaved and schedules_updated flags
        - Detect and store conflicts

    Args:
        source:
            Either:
                - A filesystem path (str or pathlib.Path)
                - An uploaded file object (from Flask request.files)

    Raises:
        json.JSONDecodeError:
            If the source content is not valid JSON.
        OSError:
            If a provided path cannot be opened.
        AttributeError:
            If the source is neither a valid path nor file-like object.
    """
    
    # -------------------------------------------------------------
    # Case 1: Source is a filesystem path (string or Path-like object)
    # -------------------------------------------------------------
    if isinstance(source, (str, PathLike)):
        with open(source, "r", encoding="utf-8") as f:
            loaded_config = json.load(f)
        loaded_path = str(source)

    # -------------------------------------------------------------
    # Case 2: Source is an uploaded file (Flask request.files)
    # -------------------------------------------------------------
    else:
        # Read raw bytes from uploaded file and decode (handle BOM if present)
        raw_data = source.read().decode("utf-8-sig")

        # Parse JSON content from uploaded file
        loaded_config = json.loads(raw_data)

        # Use filename for tracking instead of a filesystem path
        loaded_path = getattr(source, "filename", None)

    # ------------------------------------------------------------------------------------------------------
    # Continue with existing logic (Apply defaults, store in session, write working_config.json, etc.)
    # ------------------------------------------------------------------------------------------------------
    # Work on a copy so imported data can be normalized safely.
    working_copy = normalize_cfg(apply_timeslot_defaults(copy.deepcopy(loaded_config)))

    # Store the loaded config and its source identifier in session.
    session[SESSION_CONFIG_KEY] = working_copy
    session[SESSION_CONFIG_PATH_KEY] = loaded_path

    # Keep the internal working file synchronized with session state.
    _write_working_file(working_copy)

    # Freshly loaded configs should not be marked as unsaved yet.
    _set_unsaved(False)
    set_schedules_updated(False)

    # Immediately detect editor-level conflicts for display in the UI.
    conflicts = detect_conflicts(working_copy)
    session["config_conflicts"] = conflicts

def set_config(cfg):
    return normalize_cfg(cfg)

def save_config_from_session(path: str):
    """
    Save the current working configuration from session to a target JSON file.

    Workflow:
        - Retrieve the working config
        - Validate it before writing
        - Serialize it to the provided path
        - Update session path to the new save location
        - Mark unsaved edits as resolved

    Args:
        path (str): Destination JSON file path.

    Raises:
        ValueError:
            If the configuration fails validation.
        OSError:
            If the path cannot be written.
    """
    cfg = _get_working_config()

    validate_config(cfg)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4)

    session[SESSION_CONFIG_PATH_KEY] = path

    _set_unsaved(False)
    set_schedules_updated(True)


# ================================================================
# Clear / Reset
# ================================================================

def clear_config():
    """
    Clear the loaded configuration from session.

    Post-condition:
      - session has no loaded config/path (status.loaded becomes False)
      - working_config.json is reset to a blank config on disk (safe fallback)
      - unsaved + schedules_updated reset

    Notes:
        This does not delete real config files from the repo or user's system.
        It only clears the current web-session working state.
    """    
    blank = _empty_config()

    session.pop(SESSION_CONFIG_KEY, None)
    session.pop(SESSION_CONFIG_PATH_KEY, None)

    _write_working_file(blank)

    _set_unsaved(False)
    set_schedules_updated(False)


# ================================================================
# Export Config File (Input JSON)
# ================================================================

def get_default_export_filename() -> str:
    """
    Suggest a filename for exporting the working config.

    Rules:
      - If a real config was loaded, suggest its basename.
      - If nothing loaded (or only working_config.json exists), suggest new_config_file.json.
    """
    path = session.get(SESSION_CONFIG_PATH_KEY)
    if not path:
        return "new_config_file.json"

    base = os.path.basename(str(path))

    # If the "loaded path" is the internal working file, treat it like "no loaded config"
    if os.path.abspath(str(path)) == os.path.abspath(WORKING_PATH):
        return "new_config_file.json"

    return base if base else "new_config_file.json"


def sanitize_export_filename(name: str | None) -> str:
    """
    Prevent path traversal + ensure .json extension.

    Rules:
        - Strip whitespace
        - Reduce to basename only
        - Fall back to default name if empty
        - Append .json if the extension is missing
    
    Returns:
        str: Safe filename suitable for download.
    """
    if not name:
        return get_default_export_filename()

    safe = os.path.basename(name.strip())
    if not safe:
        safe = get_default_export_filename()

    if not safe.lower().endswith(".json"):
        safe += ".json"

    return safe

def export_config_bytes(filename: str | None = None):
    """
    Build the current working configuration as downloadable JSON bytes.

    Purpose:
        Prepares the in-session working configuration for export through
        the web interface.    
    
    Behavior:
        - Retrieves the current working configuration from session storage
        - Validates the configuration before export
        - Sanitizes the requested filename to ensure safe JSON output
        - Serializes the configuration into formatted JSON text
        - Encodes the JSON text into UTF-8 bytes for HTTP download

    Default Filename Rules:
        - If a filename is provided, it is sanitized and used
        - If no filename is provided, the service falls back to the
          currently loaded config filename
        - If no config has been loaded, the default filename becomes
          'new_config_file.json'

    Returns:
        tuple[bytes, str]:
            - JSON payload as UTF-8 encoded bytes
            - Safe export filename ending in '.json'
    """
    # Pull the current working config from the user session.
    # This is the live config being edited in the Config Editor.
    cfg = _get_working_config()

    # Validate before export so the user does not download
    # malformed or incomplete scheduler configuration data.
    validate_config(cfg)

    # Clean and normalize the export filename.
    # Ensures safe basename usage and appends .json if needed.
    safe_name = sanitize_export_filename(filename)

    # Convert the config dictionary into nicely formatted JSON text
    # so the saved file is readable when opened later.
    payload = json.dumps(cfg, indent=4)

    # Return bytes for the HTTP response body plus the final filename
    # that the browser should suggest to the user.
    return payload.encode("utf-8"), safe_name


# ================================================================
# Validation
# ================================================================

def validate_config(cfg):
    """
    Validate the scheduler configuration.

    Notes:
        - Duplicate course_id values are allowed.
        - Repeated course_id entries represent multiple sections
          of the same course in scheduler-library input.
    """
    if "config" not in cfg:
        raise ValueError("Invalid configuration format.")

    if not has_time_blocks(cfg):
        raise ValueError(
            "Time blocks are required in the configuration."
        )

    config = cfg["config"]

    courses = config.get("courses", [])
    rooms = config.get("rooms", [])
    labs = config.get("labs", [])
    faculty_list = config.get("faculty", [])

    faculty_names = {f.get("name") for f in faculty_list if isinstance(f, dict)}

    room_names = [
        r if isinstance(r, str) else r.get("name")
        for r in rooms
    ]

    lab_names = [
        l if isinstance(l, str) else l.get("name")
        for l in labs
    ]

    for course in courses:

        cid = course.get("course_id")

        if not cid:
            raise ValueError("Course with missing course_id.")

        credits = course.get("credits")

        if not isinstance(credits, int) or credits <= 0:
            raise ValueError(f"Invalid credits for course {cid}")

        for r in course.get("room", []):
            if r not in room_names:
                raise ValueError(f"Invalid room '{r}' in course {cid}")

        for l in course.get("lab", []):
            if l not in lab_names:
                raise ValueError(f"Invalid lab '{l}' in course {cid}")

        for f in course.get("faculty", []):
            if f not in faculty_names:
                raise ValueError(f"Invalid faculty '{f}' in course {cid}")

        for conflict in course.get("conflicts", []):
            if conflict not in [c.get("course_id") for c in courses]:
                raise ValueError(f"Invalid conflict '{conflict}' in course {cid}")


# ================================================================
# Status
# ================================================================
def get_config_status():
    """
    Build a summary of the current configuration/editor state for the UI.

    Returned data is typically used by routes/views to show:
        - whether a config is loaded
        - where it came from
        - how many faculty/courses/rooms/labs exist
        - whether unsaved edits exist
        - whether schedules are current
        - what filename should be suggested for export

    Returns:
        dict: Config editor status information.
    """
    cfg = session.get(SESSION_CONFIG_KEY)
    loaded = cfg is not None
    path = session.get(SESSION_CONFIG_PATH_KEY)

    if not cfg:
        return {
            "loaded": False,
            "path": None,
            "counts": {}
        }

    counts = {}
    time_slot_summary = {}

    if loaded and isinstance(cfg, dict):
        c = cfg.get("config", {}) if isinstance(cfg.get("config", {}), dict) else {}
        tsc = cfg.get("time_slot_config", {})

        time_slots = tsc.get("time_slots", {})
        patterns = tsc.get("patterns", []) or []

        counts = {
            "Faculty": len(c.get("faculty", []) or []),
            "Courses": len(c.get("courses", []) or []),
            "Rooms": len(c.get("rooms", []) or []),
            "Labs": len(c.get("labs", []) or []),
        }

        total_slots = sum(len(slots) for slots in time_slots.values())

        enabled_patterns = len([
            p for p in patterns if p.get("enabled", True)
        ])

        time_slot_summary = {
            "total_slots": total_slots,
            "patterns": len(patterns), 
            "Enabled Patterns": enabled_patterns
        }

    return {
        "loaded": loaded,
        "path": path,
        "counts": counts,
        "time_slot_summary": time_slot_summary,

        "time_slot_summary_raw": time_slots,
        "patterns_raw": patterns,

        "unsaved_changes": get_unsaved(),
        "schedules_updated": get_schedules_updated(),
        "default_filename": get_default_export_filename(),
        "conflicts": get_conflicts(),
    }



# ================================================================
# Faculty Management
# ================================================================

def add_faculty_service(**kwargs):
    cfg = _get_cgf()
    add_faculty(cfg, **kwargs)
    _commit_change(cfg)


def remove_faculty_service(**kwargs):
    cfg = _get_cgf()
    remove_faculty(cfg, **kwargs)
    _commit_change(cfg)


def modify_faculty_service(**kwargs):
    cfg = _get_cgf()
    modify_faculty(cfg, **kwargs)
    _commit_change(cfg)

def set_faculty_time_service(name: str, day: str, start_time: str, end_time: str):
    cfg = _get_cgf()

    faculty_list = cfg.get("config", {}).get("faculty", [])
    day = day.upper()

    for faculty in faculty_list:
        if faculty.get("name") == name:
            faculty.setdefault("times", {})
            faculty["times"].setdefault(day, [])

            faculty["times"][day].append({
                "start_time": start_time,
                "end_time": end_time
            })

            _commit_change(cfg)
            return

    raise ValueError(f"Faculty '{name}' does not exist")

def set_faculty_day_unavailable_service(name: str, day: str):
    """
    Mark a faculty member unavailable on a specific day by setting that
    day's time list to an empty list.
    """
    cfg = _get_cgf()
    faculty_list = cfg.get("config", {}).get("faculty", [])

    day = day.upper()

    for faculty in faculty_list:
        if faculty.get("name") == name:
            faculty.setdefault("times", {})
            faculty["times"][day] = []
            _commit_change(cfg)
            return

    raise ValueError(f"Faculty '{name}' does not exist")

def remove_faculty_time_service(name: str, day: str, start_time: str, end_time: str):
    cfg = _get_cgf()
    faculty_list = cfg.get("config", {}).get("faculty", [])

    for faculty in faculty_list:
        if faculty.get("name") == name:
            slots = faculty.get("times", {}).get(day, [])

            faculty["times"][day] = [
                s for s in slots
                if not (
                    s.get("start_time") == start_time and
                    s.get("end_time") == end_time
                )
            ]

            _commit_change(cfg)
            return

    raise ValueError(f"Faculty '{name}' not found")

# ================================================================
# Room Management
# ================================================================

def add_room_service(room):
    cfg = _get_cgf()
    add_room(cfg, room)
    _commit_change(cfg)


def remove_room_service(room):
    cfg = _get_cgf()
    remove_room(cfg, room)
    _commit_change(cfg)


def modify_room_service(room, new_name):
    cfg = _get_cgf()
    modify_room(cfg, room, new_name)
    _commit_change(cfg)


# ================================================================
# Lab Management
# ================================================================

def add_lab_service(**kwargs):
    cfg = _get_cgf()
    add_lab(cfg, **kwargs)
    _commit_change(cfg)


def remove_lab_service(**kwargs):
    cfg = _get_cgf()
    remove_lab(cfg, **kwargs)
    _commit_change(cfg)


def modify_lab_service(**kwargs):
    cfg = _get_cgf()
    modify_lab(cfg, **kwargs)
    _commit_change(cfg)


# ================================================================
# Course Management
# ================================================================

def add_course_service(**kwargs):
    cfg = _get_cgf()
    if "credits" in kwargs and kwargs["credits"]:
        kwargs["credits"] = int(kwargs["credits"])
    if"faculty" in kwargs and kwargs["faculty"]:
        kwargs["faculty"] = [
            f.strip() for f in kwargs["faculty"].split(",") if f.strip()
        ]
    else:
        kwargs["faculty"] = []
    
    add_course(cfg, **kwargs)
    _commit_change(cfg)


def remove_course_service(course_id):
    cfg = _get_cgf()
    remove_course(cfg, course_id)
    _commit_change(cfg)


def modify_course_service(**kwargs):
    cfg = _get_cgf()
    if "credits" in kwargs and kwargs["credits"]:
        kwargs["credits"] = int(kwargs["credits"])
    if "faculty" in kwargs and kwargs["faculty"]:
        kwargs["faculty"] = [
            f.strip() for f in kwargs["faculty"].split(",") if f.strip()
        ]
    else:
        kwargs["faculty"] = []
    modify_course(cfg, **kwargs)
    _commit_change(cfg)


# ================================================================
# Conflict Management
# ================================================================

def add_conflict_service(**kwargs):
    cfg = _get_cgf()
    add_conflict(cfg, **kwargs)
    _commit_change(cfg)


def remove_conflict_service(**kwargs):
    cfg = _get_cgf()
    remove_conflict(cfg, **kwargs)
    _commit_change(cfg)


def modify_conflict_service(**kwargs):
    cfg = _get_cgf()
    modify_conflict(cfg, **kwargs)
    _commit_change(cfg)

# ==============================================================
# Time Slot Management
# ==============================================================

def add_time_slot_service(day, start_time, end_time):
    cfg = _get_cgf()

    _ensure_time_slot_defaults(cfg)

    slots = cfg["time_slot_config"]["time_slots"].setdefault(day, [])

    slots.append({
        "start_time": start_time,
        "end_time": end_time
    })

    _commit_change(cfg)

def remove_time_slot_service(day, start_time, end_time):
    cfg = _get_cgf()
    _ensure_time_slot_defaults(cfg)

    slots = cfg["time_slot_config"]["time_slots"].get(day, [])

    cfg["time_slot_config"]["time_slots"][day] = [
        s for s in slots
        if not (
            s.get("start_time") == start_time and
            s.get("end_time") == end_time
        )
    ]

    _commit_change(cfg)

def modify_time_slot_service(day, index, start_time, end_time):
    cfg = _get_cgf()

    _ensure_time_slot_defaults(cfg)

    slots = cfg["time_slot_config"]["time_slots"].get(day, [])

    if 0 <= index < len(slots):
        slots[index] = {
            "start_time": start_time,
            "end_time": end_time
        }
    
    _commit_change(cfg)

# ================================================================
# Meeting Pattern Management
# ================================================================

def add_pattern_service(pattern_id, credits, days, duration,
                        is_lab=False, fixed_start_time=None, enabled=True):

    cfg = _get_cgf()
    _ensure_time_slot_defaults(cfg)

    is_lab = str(is_lab).lower() == "true"

    pattern = {
        "pattern_id": pattern_id,
        "credits": int(credits),
        "days": days,
        "duration": int(duration),
        "is_lab": is_lab,
        "fixed_start_time": fixed_start_time,
        "enabled": enabled
    }

    cfg["time_slot_config"]["patterns"].append(pattern)

    _commit_change(cfg)


def remove_pattern_service(pattern_id):
    cfg = _get_cgf()
    _ensure_time_slot_defaults(cfg)

    patterns = cfg["time_slot_config"]["patterns"]

    cfg["time_slot_config"]["patterns"] = [
        p for p in patterns if p.get("pattern_id") != pattern_id
    ]

    _commit_change(cfg)


def modify_pattern_service(pattern_id, **updates):
    cfg = _get_cgf()
    _ensure_time_slot_defaults(cfg)

    for p in cfg["time_slot_config"]["patterns"]:
        if p.get("pattern_id") == pattern_id:
            p.update(updates)

    _commit_change(cfg)


def toggle_pattern_service(pattern_id, enabled):
    cfg = _get_cgf()
    _ensure_time_slot_defaults(cfg)

    if isinstance(enabled, str):
        enabled = str(enabled).lower() in ["true", "on", "1"]

    for p in cfg["time_slot_config"]["patterns"]:
        if p.get("pattern_id") == pattern_id:
            p["enabled"] = enabled

    _commit_change(cfg)


# ================================================================
# Schedule Generation
# ================================================================

def update_schedules(cfg):

    from app.web.services.run_service import generate_schedules_into_session

    cfg = _ensure_time_slot_defaults(cfg)

    conflicts = get_conflicts()

    if conflicts:
        raise ValueError(
            "Schedules cannot be generated until configuration conflicts are resolved."
        )

    generate_schedules_into_session(
        cfg.get("limit", 3),
        cfg.get("optimizer_flags", []),
    )

    return session.get("schedules", [])