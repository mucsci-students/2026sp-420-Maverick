# Author: Antonio Corona, Jacob Karasow
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

# Import management functions from existing modules
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

# Faculty Management
def add_faculty_service(name: str): 
    cfg = session[SESSION_CONFIG_KEY]
    add_faculty(cfg, name)
    session[SESSION_CONFIG_KEY] = cfg

def remove_faculty_service(name: str):
    cfg = session[SESSION_CONFIG_KEY]
    remove_faculty(cfg, name)
    session[SESSION_CONFIG_KEY] = cfg

def modify_faculty_service(old_name: str, new_name: str):
    cfg = session[SESSION_CONFIG_KEY]
    modify_faculty(cfg, old_name, new_name)
    session[SESSION_CONFIG_KEY] = cfg

# Room Management
def add_room_service(name: str):
    cfg = session[SESSION_CONFIG_KEY]
    add_room(cfg, name)
    session[SESSION_CONFIG_KEY] = cfg

def remove_room_service(name: str):
    cfg = session[SESSION_CONFIG_KEY]
    remove_room(cfg, name)
    session[SESSION_CONFIG_KEY] = cfg

def modify_room_service(old_name: str, new_name: str):
    cfg = session[SESSION_CONFIG_KEY]
    modify_room(cfg, old_name, new_name)
    session[SESSION_CONFIG_KEY] = cfg

# Lab Management
def add_lab_service(name: str):
    cfg = session[SESSION_CONFIG_KEY]
    add_lab(cfg, name)
    session[SESSION_CONFIG_KEY] = cfg

def remove_lab_service(name: str):
    cfg = session[SESSION_CONFIG_KEY]
    remove_lab(cfg, name)
    session[SESSION_CONFIG_KEY] = cfg

def modify_lab_service(old_name: str, new_name: str):    
    cfg = session[SESSION_CONFIG_KEY]
    modify_lab(cfg, old_name, new_name)
    session[SESSION_CONFIG_KEY] = cfg

# Course Management
def add_course_service(name: str, faculty: str, room: str, lab: str):
    cfg = session[SESSION_CONFIG_KEY]
    add_course(cfg, name, faculty, room, lab)
    session[SESSION_CONFIG_KEY] = cfg

def remove_course_service(name: str):
    cfg = session[SESSION_CONFIG_KEY]
    remove_course(cfg, name)
    session[SESSION_CONFIG_KEY] = cfg

def modify_course_service(old_name: str, new_name: str, faculty: str, room: str, lab: str):
    cfg = session[SESSION_CONFIG_KEY]
    modify_course(cfg, old_name, new_name, faculty, room, lab)
    session[SESSION_CONFIG_KEY] = cfg

# Conflict Management
def add_conflict_service(course1: str, course2: str):
    cfg = session[SESSION_CONFIG_KEY]
    add_conflict(cfg, course1, course2)
    session[SESSION_CONFIG_KEY] = cfg

def remove_conflict_service(course1: str, course2: str):
    cfg = session[SESSION_CONFIG_KEY]
    remove_conflict(cfg, course1, course2)
    session[SESSION_CONFIG_KEY] = cfg   

def modify_conflict_service(old_course1: str, old_course2: str, new_course1: str, new_course2: str):
    cfg = session[SESSION_CONFIG_KEY]
    modify_conflict(cfg, old_course1, old_course2, new_course1, new_course2)
    session[SESSION_CONFIG_KEY] = cfg