# Author: Antonio Corona, Ian Swartz, Tanner Ness
# Date: 2026-02-20
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
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, Response
from app.web.services.config_service import update_schedules, _get_cgf, get_schedules_updated, set_schedules_updated
from app.web.services.schedule_service import (
    get_view_data,
    next_schedule,
    prev_schedule,
    select_schedule,              
    export_schedules_to_file,
    import_schedules_from_file,
    SESSION_SCHEDULES_KEY,
    SESSION_SELECTED_INDEX_KEY,
    is_export_enabled,
    get_schedules_for_export
)

bp = Blueprint("viewer", __name__, url_prefix="/viewer")


@bp.get("/")
def viewer():
    """
    Main Viewer page.
    Retrieves fully prepared view data from the service layer.
    """
    
    if get_schedules_updated():
        
        cfg = _get_cgf()
        update_schedules(cfg)

        set_schedules_updated(False)

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


# Added an import for temporary file handling if need be
import os

# import file route made for importing/uploading a file from user's local system
@bp.post("/import_file")
def import_file():
    """Handles uploading multiple files from the user's local system and appending them."""
    
    # Use getlist to capture all files from the 'multiple' input
    uploaded_files = request.files.getlist("schedule_file")
    
    if not uploaded_files or uploaded_files[0].filename == '':
        flash("No files selected.", "error")
        return redirect(url_for("viewer.viewer"))

    total_added = 0
    final_count = 0
    files_count = 0

    try:
        for file in uploaded_files:
            if file and file.filename.endswith('.json'):
                # Your existing service function handles individual file objects perfectly
                added, total = import_schedules_from_file(file)
                total_added += added
                final_count = total
                files_count += 1
        
        flash(f"Successfully imported {files_count} file(s)! Added {total_added} new schedule(s).", "success")
        
    except Exception as e:
        flash(f"Upload failed: {e}", "error")
        
    return redirect(url_for("viewer.viewer"))


# route for exporting schedule(s) to a file
import json

@bp.post("/export_file")
def export_file():
    # Get the list of indices from the checkboxes (e.g., ['0', '2'])
    selected_indices = request.form.getlist("schedule_indices")
    
    if not selected_indices:
        flash("Please select at least one schedule to export.", "error")
        return redirect(url_for("viewer.viewer"))

    # Get all schedules from the session
    all_schedules = get_schedules_for_export()
    
    # Filter the list based on what the user checked
    export_data = []
    for idx_str in selected_indices:
        idx = int(idx_str)
        if 0 <= idx < len(all_schedules):
            export_data.append(all_schedules[idx])

    # Convert to JSON string
    json_data = json.dumps(export_data, indent=2)
    
    # Determine filename (mention 'partial' if not all were selected)
    filename = "schedules_export.json" if len(export_data) == len(all_schedules) else "selected_schedules.json"

    return Response(
        json_data,
        mimetype="application/json",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )


# Added a route for allowing the user to reset (clear) the scheulde viewer
@bp.post("/reset")
def reset_viewer():
    session.pop(SESSION_SCHEDULES_KEY, None)
    session.pop(SESSION_SELECTED_INDEX_KEY, None)
    session.modified = True
    
    flash("Schedule viewer has been reset.", "success")
    return redirect(url_for("viewer.viewer"))