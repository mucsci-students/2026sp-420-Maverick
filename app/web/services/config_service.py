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
        json.dump(cfg, f, indent=2)

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

# Faculty Management
def add_faculty_service(**kwargs):
    cfg = _get_cgf()
    add_faculty(cfg, **kwargs)
    session[SESSION_CONFIG_KEY] = cfg

    update_schedules(cfg)

def remove_faculty_service(**kwargs):
    cfg = _get_cgf()
    remove_faculty(cfg, **kwargs)
    session[SESSION_CONFIG_KEY] = cfg

    update_schedules(cfg)

def modify_faculty_service(**kwargs):
    cfg = _get_cgf()
    modify_faculty(cfg, **kwargs)
    session[SESSION_CONFIG_KEY] = cfg

    update_schedules(cfg)


# Room Management
def add_room_service(room: str):
    cfg = _get_cgf()
    add_room(cfg, room)
    session[SESSION_CONFIG_KEY] = cfg

    update_schedules(cfg)

def remove_room_service(**kwargs):
    cfg = _get_cgf()
    remove_room(cfg, **kwargs)
    session[SESSION_CONFIG_KEY] = cfg

    update_schedules(cfg)

def modify_room_service(room: str, new_name: str):
    cfg = _get_cgf()
    modify_room(cfg, room, new_name)
    session[SESSION_CONFIG_KEY] = cfg

    update_schedules(cfg)


# Lab Management
def add_lab_service(**kwargs):
    cfg = _get_cgf()
    add_lab(cfg, **kwargs)
    session[SESSION_CONFIG_KEY] = cfg

    update_schedules(cfg)

def remove_lab_service(**kwargs):
    cfg = _get_cgf()
    remove_lab(cfg, **kwargs)
    session[SESSION_CONFIG_KEY] = cfg

    update_schedules(cfg)

def modify_lab_service(**kwargs):
    cfg = _get_cgf()
    modify_lab(cfg, **kwargs)
    session[SESSION_CONFIG_KEY] = cfg

    update_schedules(cfg)


# Course Management
def add_course_service(**kwargs):
    cfg = _get_cgf()
    add_course(cfg, **kwargs)
    session[SESSION_CONFIG_KEY] = cfg

    update_schedules(cfg)

def remove_course_service(**kwargs):
    cfg = _get_cgf()
    remove_course(cfg, **kwargs)
    session[SESSION_CONFIG_KEY] = cfg

    update_schedules(cfg)

def modify_course_service(**kwargs):
    cfg = _get_cgf()
    modify_course(cfg, **kwargs)
    session[SESSION_CONFIG_KEY] = cfg

    update_schedules(cfg)


# Conflict Management
def add_conflict_service(**kwargs):
    cfg = _get_cgf()
    add_conflict(cfg, **kwargs)
    session[SESSION_CONFIG_KEY] = cfg

    update_schedules(cfg)

def remove_conflict_service(**kwargs):
    cfg = _get_cgf()
    remove_conflict(cfg, **kwargs)
    session[SESSION_CONFIG_KEY] = cfg

    update_schedules(cfg)

def modify_conflict_service(**kwargs):
    cfg = _get_cgf()
    modify_conflict(cfg, **kwargs)
    session[SESSION_CONFIG_KEY] = cfg

    update_schedules(cfg)


def update_schedules(cfg):

    from app.web.services.run_service import generate_schedules_into_session

    limit = cfg.get("limit", 0)
    optimizer_flags = cfg.get("optimizer_flags", None)
    generate_schedules_into_session(limit, optimizer_flags)

    return session.get('schedules', [])
