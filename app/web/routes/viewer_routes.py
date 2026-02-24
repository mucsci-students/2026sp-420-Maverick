# Author: Antonio Corona
# Date: 2026-02-24
"""
Schedule Viewer Routes

Defines Flask endpoints for viewing and managing generated schedules.

Responsibilities:
- Navigate between schedules
- Display schedules by Room and Faculty
- Export schedules to file
- Import schedules from file
- Select a schedule directly by index (dropdown)

Acts as the Controller layer for schedule viewing functionality.
"""

# app/web/routes/viewer_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.web.services.schedule_service import (
    get_view_data,
    next_schedule,
    prev_schedule,
    select_schedule,              
    export_schedules_to_file,
    import_schedules_from_file,
)

bp = Blueprint("viewer", __name__, url_prefix="/viewer")


@bp.get("/")
def viewer():
    data = get_view_data()
    return render_template("viewer.html", data=data)


@bp.post("/next")
def go_next():
    next_schedule()
    return redirect(url_for("viewer.viewer"))


@bp.post("/prev")
def go_prev():
    prev_schedule()
    return redirect(url_for("viewer.viewer"))

@bp.post("/select")  
def select():
    """
    Directly selects a schedule index from the Viewer dropdown.
    Expects a 0-based integer index in form field 'index'.
    """
    raw = request.form.get("index", "0")
    try:
        select_schedule(int(raw))
    except Exception:
        # Ignore invalid input; keep current schedule selection
        pass
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
