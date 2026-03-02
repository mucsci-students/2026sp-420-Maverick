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

SESSION_CONFIG_KEY = "config"
SESSION_CONFIG_PATH_KEY = "config_path"

# Global flag to track if update_schedules has been run
_schedules_updated = False

def set_schedules_updated(is_updated: bool):
    global _schedules_updated
    _schedules_updated = is_updated

def get_schedules_updated() -> bool:
    return _schedules_updated

# Load / Save
def load_config_into_session(path: str):
    # Minimal working version: read JSON file and store it in session
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    session[SESSION_CONFIG_KEY] = cfg
    session[SESSION_CONFIG_PATH_KEY] = path


def save_config_from_session(path: str):
    cfg = session.get(SESSION_CONFIG_KEY)
    if cfg is None:
        raise ValueError("No config loaded. Load a config first.")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4)

    session[SESSION_CONFIG_PATH_KEY] = path


def get_config_status():
    cfg = session.get(SESSION_CONFIG_KEY)
    path = session.get(SESSION_CONFIG_PATH_KEY)

    if not cfg:
        return {"loaded": False, "path": None, "counts": {}}

    # Helpful summary counts (works regardless of exact schema, as long as lists exist)
    counts = {}
    for k in ("faculty", "courses", "rooms", "labs", "conflicts"):
        v = cfg.get(k)
        if isinstance(v, list):
            counts[k] = len(v)

    return {"loaded": True, "path": path, "counts": counts}

# Helper
def _get_cgf():
    cfg = session.get(SESSION_CONFIG_KEY)
    if cfg is None:
        raise ValueError("No config loaded. Load a config first.")
    return cfg

# Helper 
def _write_session_to_file():
    cfg = session.get(SESSION_CONFIG_KEY)
    path = session.get(SESSION_CONFIG_PATH_KEY)

    if cfg is None or path is None:
        raise ValueError("No config loaded. Load a config first.")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent = 2)

# Config Validation 
def validate_config(cfg: dict) -> None:
    config = cfg.get("config", {})

    courses = config.get("courses", [])
    rooms = config.get("rooms", [])
    labs = config.get("labs", [])
    faculty_list = config.get("faculty", [])

    faculty_names = {f["name"] for f in faculty_list}

    seen_ids = set()

    for course in courses:

        cid = course.get("course_id")
        if not cid:
            raise ValueError(f"Course with empty course_id found.")
        
        # Prevent duplicate IDs
        if cid in seen_ids:
            raise ValueError(f"Duplicate course_id detected: {cid}")
        seen_ids.add(cid)

        # Credits should be a positive integer
        credits = course.get("credits")
        if not isinstance(credits, int) or credits <= 0:
            raise ValueError(f"Invalid credits for course {cid}")
        
        # Room Validation
        for r in course.get("room", []):
            if r not in rooms:
                raise ValueError(f"Course {cid} references unknown room: {r}")

        # Lab Validation
        for l in course.get("lab", []):
            if l not in labs:
                raise ValueError(f"Course {cid} references invalid lab: {l}")

        # Faculty Validation
        for f in course.get("faculty", []):
            if f not in faculty_names:
                raise ValueError(f"Course {cid} references unknown faculty: {f}")
        
        # Conflict Validation 
        for conflict in course.get("conflicts", []):
            if conflict not in [c.get("course_id") for c in courses]:
                raise ValueError(f"Course {cid} has conflict with unknown course: {conflict}")


# Faculty Management
def add_faculty_service(**kwargs):
    cfg = _get_cgf()
    add_faculty(cfg, **kwargs)
    session[SESSION_CONFIG_KEY] = cfg
    _write_session_to_file()
    set_schedules_updated(True)

def remove_faculty_service(**kwargs):
    cfg = _get_cgf()
    remove_faculty(cfg, **kwargs)
    session[SESSION_CONFIG_KEY] = cfg
    _write_session_to_file()
    set_schedules_updated(True)

def modify_faculty_service(**kwargs):
    cfg = _get_cgf()
    modify_faculty(cfg, **kwargs)
    session[SESSION_CONFIG_KEY] = cfg
    _write_session_to_file()
    set_schedules_updated(True)


# Room Management
def add_room_service(room: str):
    cfg = _get_cgf()
    add_room(cfg, room)
    session[SESSION_CONFIG_KEY] = cfg
    _write_session_to_file()
    set_schedules_updated(True)

def remove_room_service(room: str):
    cfg = _get_cgf()
    remove_room(cfg, room)
    session[SESSION_CONFIG_KEY] = cfg
    _write_session_to_file()
    set_schedules_updated(True)

def modify_room_service(room: str, new_name: str):
    cfg = _get_cgf()
    modify_room(cfg, room, new_name)
    session[SESSION_CONFIG_KEY] = cfg
    _write_session_to_file()
    set_schedules_updated(True)


# Lab Management
def add_lab_service(**kwargs):
    cfg = _get_cgf()
    add_lab(cfg, **kwargs)
    session[SESSION_CONFIG_KEY] = cfg
    _write_session_to_file()
    set_schedules_updated(True)

def remove_lab_service(**kwargs):
    cfg = _get_cgf()
    remove_lab(cfg, **kwargs)
    session[SESSION_CONFIG_KEY] = cfg
    _write_session_to_file()
    set_schedules_updated(True)

def modify_lab_service(**kwargs):
    cfg = _get_cgf()
    modify_lab(cfg, **kwargs)
    session[SESSION_CONFIG_KEY] = cfg
    _write_session_to_file()
    set_schedules_updated(True)


# Course Management
def add_course_service(**kwargs):
    cfg = _get_cgf()

    # Convert credits to int if provided and not empty
    if "credits" in kwargs and kwargs["credits"]:
        kwargs["credits"] = int(kwargs["credits"])

    add_course(cfg, **kwargs)
    session[SESSION_CONFIG_KEY] = cfg
    _write_session_to_file()
    set_schedules_updated(True)

def remove_course_service(course_id: str):
    cfg = _get_cgf()
    remove_course(cfg, course_id)
    session[SESSION_CONFIG_KEY] = cfg
    _write_session_to_file()
    set_schedules_updated(True)

def modify_course_service(**kwargs):
    cfg = _get_cgf()

    # Convert credits to int if provided and not empty
    if "credits" in kwargs and kwargs["credits"]:
        kwargs["credits"] = int(kwargs["credits"])

    modify_course(cfg, **kwargs)
    session[SESSION_CONFIG_KEY] = cfg
    _write_session_to_file()
    set_schedules_updated(True)


# Conflict Management
def add_conflict_service(**kwargs):
    cfg = _get_cgf()
    add_conflict(cfg, **kwargs)
    session[SESSION_CONFIG_KEY] = cfg
    _write_session_to_file()
    set_schedules_updated(True)

def remove_conflict_service(**kwargs):
    cfg = _get_cgf()
    remove_conflict(cfg, **kwargs)
    session[SESSION_CONFIG_KEY] = cfg
    _write_session_to_file()
    set_schedules_updated(True)
    set_schedules_updated(True)

def modify_conflict_service(**kwargs):
    cfg = _get_cgf()
    modify_conflict(cfg, **kwargs)
    session[SESSION_CONFIG_KEY] = cfg
    _write_session_to_file()
    set_schedules_updated(True) 


# only called when user modifies the config
def update_schedules(cfg):

    from app.web.services.run_service import generate_schedules_into_session

    limit = cfg.get("limit", 0)
    optimizer_flags = cfg.get("optimizer_flags", None)

    generate_schedules_into_session(limit, optimizer_flags)

    return session.get('schedules', [])