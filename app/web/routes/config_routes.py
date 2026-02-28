# Author: Antonio Corona, Jacob Karasow
# Date: 2026-02-25
"""
Configuration Routes

Defines Flask endpoints for the Scheduler Config Editor.

Responsibilities:
- Load configuration file
- Save configuration file
- Display configuration summary
- Handle add/edit/remove operations for faculty, courses, rooms, and labs

These routes act as Controllers in the MVC architecture.
"""

# app/web/routes/config_routes.py
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from app.web.services.config_service import (
    load_config_into_session,
    save_config_from_session,
    get_config_status,

    # Faculty 
    add_faculty_service,
    remove_faculty_service,
    modify_faculty_service,

    # Rooms
    add_room_service,
    remove_room_service,
    modify_room_service,

    # Labs
    add_lab_service,
    remove_lab_service,
    modify_lab_service,

    # Courses
    add_course_service,
    remove_course_service,
    modify_course_service,

    # Conflicts
    add_conflict_service,
    remove_conflict_service,
    modify_conflict_service,
)

bp = Blueprint("config", __name__, url_prefix="/config")

# Editor 
@bp.get("/")
def editor():
    status = get_config_status()
    return render_template("config_editor.html", status=status)

# Load / Save
@bp.post("/load")
def load():
    path = request.form.get("path", "configs/config_dev.json").strip()
    try:
        load_config_into_session(path)
        flash(f"Loaded config: {path}", "success")
    except Exception as e:
        flash(f"Load failed: {e}", "error")
    return redirect(url_for("config.editor"))


@bp.post("/save")
def save():
    path = request.form.get("path", "configs/config_dev.json").strip()
    try:
        save_config_from_session(path)
        flash(f"Saved config: {path}", "success")
    except Exception as e:
        flash(f"Save failed: {e}", "error")
    return redirect(url_for("config.editor"))


# Faculty 
@bp.post("/faculty/add")
def faculty_add():
    try:
        add_faculty_service(**request.form.to_dict())
        flash("Faculty added successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))

@bp.post("/faculty/remove")
def faculty_remove():
    try: 
        remove_faculty_service(**request.form.to_dict())
        flash("Faculty removed successfully.", "success")
    except Exception as e:
        flash(str(e), "error")  
    return redirect(url_for("config.editor"))

@bp.post("/faculty/modify")
def modify_faculty():
    try:
        modify_faculty_service(**request.form.to_dict())
        flash("Faculty modified successfully.", "success")
    except Exception as e:
        flash(str(e), "error")  
    return redirect(url_for("config.editor"))


# Room 
@bp.post("/room/add")
def room_add():
    try:
        add_room_service(request.form.get("room"))
        flash("Room added successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))

@bp.post("/room/remove")
def room_remove():
    try:
        remove_room_service(request.form.get("room"))
        flash("Room removed successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))

@bp.post("/room/modify")
def modify_room():
    try:
        modify_room_service(
            request.form.get("room"), 
            request.form.get("new_name"),
        )
        flash("Room modified successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))


# Lab
@bp.post("/lab/add")
def lab_add():
    try:
        add_lab_service(**request.form.to_dict())
        flash("Lab added successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))

@bp.post("/lab/remove")
def lab_remove():
    try:
        remove_lab_service(**request.form.to_dict())
        flash("Lab removed successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))

@bp.post("/lab/modify")
def modify_lab():
    try:   
        modify_lab_service(**request.form.to_dict())
        flash("Lab modified successfully.", "success")
    except Exception as e:
        flash(str(e), "error") 
    return redirect(url_for("config.editor"))


# Course
@bp.post("/course/add")
def course_add():
    try: 
        add_course_service(**request.form.to_dict())
        flash("Course added successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))

@bp.post("/course/remove")
def course_remove():
    try:
        remove_course_service(**request.form.to_dict())
        flash("Course removed successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))

@bp.post("/course/modify")
def course_modify():
    try:
        modify_course_service(**request.form.to_dict())
        flash("Course modified successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))


# Conflict
@bp.post("/conflict/add")
def conflict_add():
    try:
        add_conflict_service(**request.form.to_dict())
        flash("Conflict added successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))

@bp.post("/conflict/remove")
def conflict_remove():
    try:
        remove_conflict_service(**request.form.to_dict())
        flash("Conflict removed successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))

@bp.post("/conflict/modify")
def conflict_modify():
    try:
        modify_conflict_service(**request.form.to_dict())
        flash("Conflict modified successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))