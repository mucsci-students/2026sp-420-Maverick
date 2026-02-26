# Author: Antonio Corona, Tanner Ness
# Date: 2026-02-25
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
    is_export_enabled,
)

bp = Blueprint("viewer", __name__, url_prefix="/viewer")


@bp.get("/")
def viewer():
    """
    Main Viewer page.
    Retrieves fully prepared view data from the service layer.
    """
    data = get_view_data()
    export_enabled = is_export_enabled()
    return render_template("viewer.html", data=data, is_export_enabled = export_enabled)


@bp.post("/next")
def go_next():
    """
    Advances to the next schedule.
    """
    next_schedule()
    return redirect(url_for("viewer.viewer"))


@bp.post("/prev")
def go_prev():
    """
    Moves to the previous schedule.
    """
    prev_schedule()
    return redirect(url_for("viewer.viewer"))

@bp.post("/select")  
def select():
    """
    Handles direct schedule selection from the dropdown.

    Expects:
        form field 'index' (0-based integer)

    Controller Responsibility:
        - Parse raw form value
        - Call service layer to clamp & set index
        - Redirect back to viewer page

    Any invalid input is ignored.
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
    """
    Exports schedules currently stored in session to a JSON file.
    """
    path = request.form.get("path", "schedules.json").strip()
    try:
        export_schedules_to_file(path)
        flash(f"Exported schedules to {path}", "success")
    except Exception as e:
        flash(f"Export failed: {e}", "error")
    return redirect(url_for("viewer.viewer"))


@bp.post("/import")
def import_():
    """
    Imports schedules from a JSON file and loads them into session.
    Resets selected index to 0 inside the service layer.
    """
    path = request.form.get("path", "schedules.json").strip()
    try:
        import_schedules_from_file(path)
        flash(f"Imported schedules from {path}", "success")
    except Exception as e:
        flash(f"Import failed: {e}", "error")
    return redirect(url_for("viewer.viewer"))
