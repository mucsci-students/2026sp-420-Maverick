# Author: Antonio Corona, Jacob Karasow, Tanner Ness
# Date: 2026-02-25
"""
Configuration Service

Provides business logic for loading, saving, and modifying
the scheduler configuration.

This module wraps the existing Sprint 1 configuration
and management modules to integrate them into the Flask GUI.

Acts as part of the Model layer in MVC.
"""

# app/web/services/config_service.py
import json
import os 
import copy
from flask import session

# Import management functions
from app.faculty_management.faculty_management import ( 
    add_faculty,
    remove_faculty, 
    modify_faculty,     
)

# Import course management functions 
from app.course_management.course_management import (
    add_course, 
    remove_course, 
    modify_course, 
    add_conflict, 
    remove_conflict, 
    modify_conflict,
)

# Import room management functions
from app.room_management.room_management import (
    add_room, 
    remove_room, 
    modify_room, 
)

# Import lab management functions
from app.lab_management.lab_management import (
    add_lab, 
    remove_lab, 
    modify_lab,
)

#================================================================
# Absolute Paths
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../")
)
CONFIGS_DIR = os.path.join(PROJECT_ROOT, "configs")
WORKING_PATH = os.path.join(CONFIGS_DIR, "working_config.json")

#================================================================
# Session Keys
SESSION_CONFIG_KEY = "working_config"
SESSION_CONFIG_PATH_KEY = "working_path"
SESSION_UNSAVED_KEY = "unsaved_changes"
SESSION_SCHEDULES_UPDATED_KEY = "schedules_updated"

#================================================================
# Helpful Functions 
def _ensure_configs_folder():
    if not os.path.exists(CONFIGS_DIR):
        os.makedirs(CONFIGS_DIR)

def _empty_config():
    return {
        "config": {
            "faculty": [],
            "courses": [],
            "rooms": [],
            "labs": [],
            "conflicts": [],
        },
        "limit": 1,
        "optimizer_flags": None,
    }

def _write_working_file(cfg):
    _ensure_configs_folder()
    with open(WORKING_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent = 4)

def _set_unsaved(value: bool):
    session[SESSION_UNSAVED_KEY] = value

def get_unsaved() -> bool:
    return session.get(SESSION_UNSAVED_KEY, False)

def set_schedules_updated(value: bool):
    session[SESSION_SCHEDULES_UPDATED_KEY] = value

def get_schedules_updated() -> bool:
    return session.get(SESSION_SCHEDULES_UPDATED_KEY, False)

def _get_working_config():
    cfg = session.get(SESSION_CONFIG_KEY)

    if cfg is None:
        cfg = _empty_config()
        session[SESSION_CONFIG_KEY] = cfg
        session[SESSION_CONFIG_PATH_KEY] = WORKING_PATH
        _write_working_file(cfg)
        _set_unsaved(False)
        set_schedules_updated(False)

    return cfg

def _get_cgf():
    return _get_working_config()

def _commit_change(cfg):
    session[SESSION_CONFIG_KEY] = cfg
    _write_working_file(cfg)
    _set_unsaved(True)
    set_schedules_updated(False)

#================================================================
# Load / Save
def load_config_into_session(path: str):

    # Minimal working version: read JSON file and store it in session
    with open(path, "r", encoding="utf-8") as f:
        loaded_config = json.load(f)

    working_copy = copy.deepcopy(loaded_config)

    session[SESSION_CONFIG_KEY] = working_copy
    session[SESSION_CONFIG_PATH_KEY] = path

    _write_working_file(working_copy)

    _set_unsaved(False)
    set_schedules_updated(False)

#================================================================
# Save
def save_config_from_session(path: str):
    cfg = _get_working_config()
    validate_config(cfg)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent = 4)

    session[SESSION_CONFIG_PATH_KEY] = path
    _set_unsaved(False)

#================================================================
# Clear / Reset
def clear_config():
    blank = _empty_config()

    session[SESSION_CONFIG_KEY] = blank
    session[SESSION_CONFIG_PATH_KEY] = WORKING_PATH

    _write_working_file(blank)

    _set_unsaved(False)
    set_schedules_updated(False)

#================================================================
# Config Validation 
def validate_config(cfg: dict):
    if "config" not in cfg:
        raise ValueError("Invalid configuation format.")

    config = cfg["config"]

    courses = config.get("courses", [])
    rooms = config.get("rooms", [])
    labs = config.get("labs", [])
    faculty_list = config.get("faculty", [])

    faculty_names = {f.get("name") for f in faculty_list}

    course_ids = set()

    for course in courses:

        course_id = course.get("course_id")

        if not course_id:
            raise ValueError("Course with missing course_id.")
        
        # Prevent duplicate IDs
        if course_id in course_ids:
            raise ValueError(f"Duplicate course_id found: {course_id}")
        course_ids.add(course_id)

        # Credits should be a positive integer
        credits = course.get("credits")
        if not isinstance(credits, int) or credits <= 0:
            raise ValueError(f"Invalid credits for course {course_id}")
        
        # Room Validation
        for r in course.get("room", []):
            if r not in rooms:
                raise ValueError(f"Invalid room '{r}' in course {course_id}")

        # Lab Validation
        for l in course.get("lab", []):
            if l not in labs:
                raise ValueError(f"Invalid lab '{l}' in course {course_id}")

        # Faculty Validation
        for f in course.get("faculty", []):
            if f not in faculty_names:
                raise ValueError(f"Invalid faculty '{f}' in course {course_id}")
        
        # Conflict Validation 
        for conflict in course.get("conflicts", []):
            if conflict not in [c.get("course_id") for c in courses]:
                raise ValueError(f"Invalid conflict '{conflict}' in course {course_id}")

#================================================================
# Status
def get_config_status():
    cfg = session.get(SESSION_CONFIG_KEY)

    return {
        "loaded_config": cfg is not None,
        "unsaved_changes": get_unsaved(),
        "schedules_updated": get_schedules_updated(),
        "current_path": session.get(SESSION_CONFIG_PATH_KEY, None),
    }

#================================================================
# Faculty Management
def add_faculty_service(**kwargs):
    cfg = _get_cgf()
    add_faculty(cfg, **kwargs)
    _commit_change(cfg)

def remove_faculty_service(**kwargs):
    cfg = _get_cgf()
    remove_faculty(cfg, **kwargs)
    session[SESSION_CONFIG_KEY] = cfg
    _commit_change(cfg)

def modify_faculty_service(**kwargs):
    cfg = _get_cgf()
    modify_faculty(cfg, **kwargs)
    _commit_change(cfg)


# Room Management
def add_room_service(room: str):
    cfg = _get_cgf()
    add_room(cfg, room)
    _commit_change(cfg)

def remove_room_service(room: str):
    cfg = _get_cgf()
    remove_room(cfg, room)
    _commit_change(cfg)

def modify_room_service(room: str, new_name: str):
    cfg = _get_cgf()
    modify_room(cfg, room, new_name)
    _commit_change(cfg)


# Lab Management
def add_lab_service(**kwargs):
    cfg = _get_cgf()
    add_lab(cfg, **kwargs)
    _commit_change(cfg)

def remove_lab_service(**kwargs):
    cfg = _get_cgf()
    remove_lab(cfg, **kwargs)
    _commit_change(cfg)
    set_schedules_updated(True)

def modify_lab_service(**kwargs):
    cfg = _get_cgf()
    modify_lab(cfg, **kwargs)
    _commit_change(cfg)


# Course Management
def add_course_service(**kwargs):
    cfg = _get_cgf()

    # Convert credits to int if provided and not empty
    if "credits" in kwargs and kwargs["credits"]:
        kwargs["credits"] = int(kwargs["credits"])

    add_course(cfg, **kwargs)
    _commit_change(cfg)

def remove_course_service(course_id: str):
    cfg = _get_cgf()
    remove_course(cfg, course_id)
    _commit_change(cfg)

def modify_course_service(**kwargs):
    cfg = _get_cgf()

    # Convert credits to int if provided and not empty
    if "credits" in kwargs and kwargs["credits"]:
        kwargs["credits"] = int(kwargs["credits"])

    modify_course(cfg, **kwargs)
    _commit_change(cfg)


# Conflict Management
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


# only called when user modifies the config
def update_schedules(cfg):

    from app.web.services.run_service import generate_schedules_into_session

    limit = cfg.get("limit", 0)
    optimizer_flags = cfg.get("optimizer_flags", None)

    generate_schedules_into_session(limit, optimizer_flags)

    return session.get('schedules', []);