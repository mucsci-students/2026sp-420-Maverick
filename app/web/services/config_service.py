# Author: Antonio Corona, Jacob Karasow, Tanner Ness
# Date: 2026-03-07

"""
Configuration Service

Provides business logic for loading, saving, and modifying
the scheduler configuration.

Acts as part of the Model layer in MVC.
"""

# ------------------------------
# Imports
# ------------------------------

import json
import os
import copy
from flask import session

from app.faculty_management.faculty_management import (
    add_faculty,
    remove_faculty,
    modify_faculty,
)

from app.course_management.course_management import (
    add_course,
    remove_course,
    modify_course,
    add_conflict,
    remove_conflict,
    modify_conflict,
)

from app.room_management.room_management import (
    add_room,
    remove_room,
    modify_room,
)

from app.lab_management.lab_management import (
    add_lab,
    remove_lab,
    modify_lab,
)

# ================================================================
# Paths
# ================================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../")
)

CONFIGS_DIR = os.path.join(PROJECT_ROOT, "configs")
WORKING_PATH = os.path.join(CONFIGS_DIR, "working_config.json")


# ================================================================
# Session Keys
# ================================================================

SESSION_CONFIG_KEY = "working_config"
SESSION_CONFIG_PATH_KEY = "working_path"
SESSION_UNSAVED_KEY = "unsaved_changes"
SESSION_SCHEDULES_UPDATED_KEY = "schedules_updated"
SESSION_CONFLICTS_KEY = "config_conflicts"


# ================================================================
# Helper Functions
# ================================================================

def _ensure_configs_folder():
    if not os.path.exists(CONFIGS_DIR):
        os.makedirs(CONFIGS_DIR)


def _empty_config():
    cfg =  {
        "config": {
            "faculty": [],
            "courses": [],
            "rooms": [],
            "labs": [],
            "conflicts": [],
        },
        "limit": 3,
        "optimizer_flags": [],
    }

    return apply_timeslot_defaults(cfg)


def _write_working_file(cfg):
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
        name = f if isinstance(f, str) else f.get("name")

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
    cfg = session.get(SESSION_CONFIG_KEY)

    # If nothing has been loaded yet, do NOT auto-create one
    if cfg is None:
        cfg = _empty_config()
    
    session[SESSION_CONFIG_KEY] = cfg

    _write_working_file(cfg)
    _set_unsaved(False)
    set_schedules_updated(False)

    return cfg


def _get_cgf():
    return _get_working_config()


def _commit_change(cfg):

    session[SESSION_CONFIG_KEY] = cfg

    _write_working_file(cfg)

    conflicts = detect_conflicts(cfg)
    set_conflicts(conflicts)

    _set_unsaved(True)
    set_schedules_updated(False)


# ================================================================
# Timeslot Defaults
# ================================================================

DEFAULT_TIMESLOT_CONFIG = {
    "days": ["MON", "TUE", "WED", "THU", "FRI"],
    "start_time": "08:00",
    "end_time": "17:00",
    "slot_length": 60
}

def apply_timeslot_defaults(cfg):

    if "time_slot_config" not in cfg:
        cfg["time_slot_config"] = copy.deepcopy(DEFAULT_TIMESLOT_CONFIG)
    else:
        for k, v in DEFAULT_TIMESLOT_CONFIG.items():
            cfg["time_slot_config"].setdefault(k, copy.deepcopy(v))

    return cfg


# ================================================================
# Load / Save
# ================================================================

def load_config_into_session(path: str):

    with open(path, "r", encoding = "utf-8") as f:
        loaded_config = json.load(f)

    working_copy = apply_timeslot_defaults(copy.deepcopy(loaded_config))

    # store config
    session[SESSION_CONFIG_KEY] = working_copy
    session[SESSION_CONFIG_PATH_KEY] = path

    _write_working_file(working_copy)

    _set_unsaved(False)
    set_schedules_updated(False)

    # detect conflicts but DO NOT stop loading
    conflicts = detect_conflicts(working_copy)

    session["config_conflicts"] = conflicts


def save_config_from_session(path: str):

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
    if loaded and isinstance(cfg, dict):
        c = cfg.get("config", {}) if isinstance(cfg.get("config", {}), dict) else {}
        counts = {
            "Faculty": len(c.get("faculty", []) or []),
            "Courses": len(c.get("courses", []) or []),
            "Rooms": len(c.get("rooms", []) or []),
            "Labs": len(c.get("labs", []) or []),
            "Conflicts": len(c.get("conflicts", []) or []),
        }

    return {
        "loaded": loaded,
        "path": path,
        "counts": counts,
        "unsaved_changes": get_unsaved(),
        "schedules_updated": get_schedules_updated(),
        "default_filename": get_default_export_filename(),
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


# ================================================================
# Schedule Generation
# ================================================================

def update_schedules(cfg):

    from app.web.services.run_service import generate_schedules_into_session

    conflicts = get_conflicts()

    if conflicts:
        raise ValueError(
            "Schedules cannot be generated until configuration conflicts are resolved."
        )

    limit = cfg.get("limit", 0)
    optimizer_flags = cfg.get("optimizer_flags")

    generate_schedules_into_session(limit, optimizer_flags)

    return session.get("schedules", [])