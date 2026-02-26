# Author: Antonio Corona, Tanner Ness
# Date: 2026-02-20
"""
Schedule Viewer Routes

Defines Flask endpoints for viewing and managing generated schedules.

Responsibilities:
- Navigate between schedules
- Display schedules by Room and Faculty
- Export schedules to file
- Import schedules from file

Acts as the Controller layer for schedule viewing functionality.
"""

# app/web/routes/viewer_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.web.services.schedule_service import (
    get_view_data,
    next_schedule,
    prev_schedule,
    export_schedules_to_file,
    import_schedules_from_file,
    is_export_enabled,
)

bp = Blueprint("viewer", __name__, url_prefix="/viewer")


@bp.get("/")
def viewer():
    data = get_view_data()
    export_enabled = is_export_enabled()
    return render_template("viewer.html", data=data, is_export_enabled = export_enabled)


@bp.post("/next")
def go_next():
    next_schedule()
    return redirect(url_for("viewer.viewer"))


@bp.post("/prev")
def go_prev():
    prev_schedule()
    return redirect(url_for("viewer.viewer"))

@bp.post("/export")
def export():
    path = request.form.get("path", "schedules.json").strip()
    try:
        export_schedules_to_file(path)
        flash(f"Exported schedules to {path}", "success")
    except Exception as e:
        flash(f"Export failed: {e}", "error")
    return redirect(url_for("viewer.viewer"))


@bp.post("/import")
def import_():
    path = request.form.get("path", "schedules.json").strip()
    try:
        import_schedules_from_file(path)
        flash(f"Imported schedules from {path}", "success")
    except Exception as e:
        flash(f"Import failed: {e}", "error")
    return redirect(url_for("viewer.viewer"))
