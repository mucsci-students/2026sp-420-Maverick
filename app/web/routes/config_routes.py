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
from flask import Blueprint, render_template, request, redirect, url_for, flash
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
def add_faculty():
    add_faculty_service(request.form.get("name").strip())
    flash("Faculty added.", "success")
    return redirect(url_for("config.editor"))

@bp.post("/faculty/remove")
def remove_faculty():
    remove_faculty_service(request.form.get("name").strip())
    flash("Faculty removed.", "success")
    return redirect(url_for("config.editor"))

@bp.post("/faculty/modify")
def modify_faculty():
    modify_faculty_service(
        old_name=request.form.get("old_name").strip(),
        new_name=request.form.get("new_name").strip(),
    )
    flash("Faculty modified.", "success")
    return redirect(url_for("config.editor"))

# Room
@bp.post("/room/add")
def add_room():
    add_room_service(request.form.get("name").strip())
    flash("Room added.", "success")
    return redirect(url_for("config.editor"))

@bp.post("/room/remove")
def remove_room():
    remove_room_service(request.form.get("name").strip())
    flash("Room removed.", "success")
    return redirect(url_for("config.editor"))

@bp.post("/room/modify")
def modify_room():
    modify_room_service(
        old_name=request.form.get("old_name").strip(),
        new_name=request.form.get("new_name").strip(),
    )
    flash("Room modified.", "success")
    return redirect(url_for("config.editor"))

# Lab
@bp.post("/lab/add")
def add_lab():
    add_lab_service(request.form.get("name").strip())
    flash("Lab added.", "success")
    return redirect(url_for("config.editor"))

@bp.post("/lab/remove")
def remove_lab():
    remove_lab_service(request.form.get("name").strip())
    flash("Lab removed.", "success")
    return redirect(url_for("config.editor"))

@bp.post("/lab/modify")
def modify_lab():
    modify_lab_service(
        old_name=request.form.get("old_name").strip(),
        new_name=request.form.get("new_name").strip(),
    )
    flash("Lab modified.", "success")
    return redirect(url_for("config.editor"))

# Course
@bp.post("/course/add")
def course_add():
    add_course_service(
        request.form.get("course_id").strip(),
        int(request.form.get("credits")),
        request.form.get("room").strip(),
        request.form.get("lab") or None,
        faculty=request.form.get("faculty"),
    )
    flash("Course added.", "success")
    return redirect(url_for("config.editor"))

@bp.post("/course/remove")
def course_remove():
    remove_course_service(request.form.get("course_id").strip())
    flash("Course removed.", "success")
    return redirect(url_for("config.editor"))

@bp.post("/course/modify")
def course_modify():
    modify_course_service(
        old_name=request.form.get("course_id").strip(),
        new_name=request.form.get("new_course_id") or None,
        credits=int(request.form.get("credits")) if request.form.get("credits") else None,
        room=request.form.get("room") or None,
        lab=request.form.get("lab") or None,
        faculty=request.form.getlist("faculty") or None,
    )
    flash("Course modified.", "success")
    return redirect(url_for("config.editor"))

# Conflict

@bp.post("/conflict/add")
def conflict_add():
    add_conflict_service(
        request.form.get("course_id").strip(),
        request.form.get("conflict_course_id").strip(),
    )
    flash("Conflict added.", "success")
    return redirect(url_for("config.editor"))


@bp.post("/conflict/remove")
def conflict_remove():
    remove_conflict_service(
        request.form.get("course_id").strip(),
        request.form.get("conflict_course_id").strip(),
    )
    flash("Conflict removed.", "success")
    return redirect(url_for("config.editor"))

@bp.post("/conflict/modify")
def conflict_modify():
    modify_conflict_service(
        request.form.get("course_id").strip(),
        request.form.get("old_conflict_course_id").strip(),
        request.form.get("new_conflict_course_id").strip(),
    )
    flash("Conflict modified.", "success")
    return redirect(url_for("config.editor"))
