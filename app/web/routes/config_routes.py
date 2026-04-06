# Author: Antonio Corona, Jacob Karasow
# Date: 2026-04-05
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

# Flask utilities for routing, request handling, flashing messages,
# session access, redirects, template rendering, and downloadable responses.
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    Response,
)

from app.web.services.run_service import (
    SESSION_SCHEDULES_KEY,
    SESSION_SELECTED_INDEX_KEY,
    SESSION_USER_SELECTED_KEY,
)

# Config service helpers used by the Config Editor routes.
from app.web.services.config_service import (
    load_config_into_session,
    save_config_from_session,
    get_config_status,
    set_schedules_updated,
    export_config_bytes,
    # Faculty
    add_faculty_service,
    remove_faculty_service,
    modify_faculty_service,
    set_faculty_time_service,
    remove_faculty_time_service,
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

    # Time Slots
    add_time_slot_service,
    remove_time_slot_service,
    modify_time_slot_service,

    # Meeting Patterns
    add_pattern_service,
    remove_pattern_service,
    modify_pattern_service,
    toggle_pattern_service,
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


@bp.post("/load_file")
def load_file():
    """
    Route: POST /config/load_file

    Purpose:
        Loads a configuration JSON file uploaded from the user's system
        into the active working session.

    Behavior:
        - Reads the uploaded file from the submitted form
        - Validates that a file was selected and that it is a JSON file
        - Passes the uploaded file object to the service layer
        - The service parses the JSON and stores it in the session
        - Redirects back to the Config Editor page after completion
    """

    # Retrieve the uploaded file object from the form submission.
    # The name "config_file" must match the HTML file input name.
    uploaded_file = request.files.get("config_file")

    # Validate that the user actually selected a file.
    if not uploaded_file or uploaded_file.filename == "":
        flash("No config file selected.", "error")
        return redirect(url_for("config.editor"))

    # Ensure the uploaded file appears to be a JSON configuration file.
    # This is a basic safety check before attempting to parse it.
    if not uploaded_file.filename.lower().endswith(".json"):
        flash("Please upload a valid JSON config file.", "error")
        return redirect(url_for("config.editor"))

    try:
        # Pass the uploaded file object to the service layer.
        # The service reads the JSON contents and loads the config
        # into the session as the current working configuration.
        load_config_into_session(uploaded_file)

        # Inform the user that the configuration was loaded successfully.
        flash(f"Loaded config from system: {uploaded_file.filename}", "success")

    except Exception as e:
        # If parsing or loading fails, display the error message.
        flash(f"Load failed: {e}", "error")

    # Redirect back to the Config Editor so the user can view or edit
    # the newly loaded configuration.
    return redirect(url_for("config.editor"))


@bp.post("/export")
def export():
    """
    Route: POST /config/export

    Purpose:
        Exports the current working configuration as a downloadable JSON file.

    Behavior:
        - Reads the optional requested filename from the submitted form
        - Builds the export payload from the current in-session config
        - Returns the config as a file download response
        - Suggests a default filename to the browser for saving
    """
    # Read the filename the user typed into the Save field.
    # If blank, the service layer will choose the default filename.
    requested_name = request.form.get("filename", "").strip()

    try:
        # Ask the service layer to package the current working config
        # as JSON bytes and determine the final safe filename.
        payload, filename = export_config_bytes(requested_name)

        # Return a downloadable file response.
        # Content-Disposition tells the browser this is an attachment
        # and suggests the filename to use in the save dialog.
        return Response(
            payload,
            mimetype="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Export-Filename": filename,
            },
        )
    except Exception as e:
        # Return a simple error response if export fails.
        # The front end will display this message to the user.
        return Response(str(e), status=400, mimetype="text/plain")


# Clear Input JSON
@bp.post("/clear")
def clear():
    """
    Route: POST /config/clear

    Purpose:
        Clears the currently loaded configuration and all related
        schedule/viewer session state.

    Responsibilities:
        - Resets the application to a "no configuration loaded" state.
        - Redirects back to the Config Editor view

    Side Effects:
        - Removes loaded configuration path.
        - Removes in-memory configuration object.
        - Clears any generated schedules.
        - Resets schedule navigation state.
        - Resets any user-selected schedule state.
        - Marks schedules as not updated.

    Post-Condition:
        The system behaves as if no configuration has been loaded.
        The user must load a config again before generating schedules.
    """
    # ----------------------------------------
    # 1. Remove Loaded Configuration State
    # ----------------------------------------

    # Remove stored config file path
    session.pop("working_config", None)

    # Remove the in-session configuration objectS
    session.pop("working_path", None)

    session.pop("unsaved_changes", None)

    # ----------------------------------------
    # 2. Remove Schedule Data (If Present)
    # ----------------------------------------

    # fallback schedule key
    session.pop("schedules", None)

    # Remove generated schedules used in Viewer
    session.pop(SESSION_SCHEDULES_KEY, None)

    # Remove current selected schedule index
    session.pop(SESSION_SELECTED_INDEX_KEY, None)

    # Remove any per-user schedule selection state
    session.pop(SESSION_USER_SELECTED_KEY, None)

    # ----------------------------------------
    # 3. Reset Application Flags
    # ----------------------------------------

    # Mark schedules as not updated so UI reflects cleared state
    set_schedules_updated(False)

    # ----------------------------------------
    # 4. Notify User + Redirect
    # ----------------------------------------

    # Flash confirmation message for UI feedback
    flash("Cleared loaded configuration.", "success")

    # Redirect back to Config Editor page
    return redirect(url_for("config.editor"))


# Tells user that a new faculty was added
@bp.post("/faculty/add")
def faculty_add():
    try:
        add_faculty_service(**request.form.to_dict())
        flash("Faculty added successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))


# Tells user that a faculty was removed
@bp.post("/faculty/remove")
def faculty_remove():
    try:
        remove_faculty_service(**request.form.to_dict())
        flash("Faculty removed successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))


# Tells user that a faculty was modified
@bp.post("/faculty/modify")
def modify_faculty():
    try:
        modify_faculty_service(**request.form.to_dict())
        flash("Faculty modified successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))


@bp.post("/faculty/set_time")
def faculty_set_time():
    try:
        set_faculty_time_service(**request.form.to_dict())
        flash("Faculty availability updated.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))


@bp.post("/faculty/remove_time")
def faculty_remove_time():
    try:
        remove_faculty_time_service(**request.form.to_dict())
        flash("Faculty availability removed.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))


# Tells user that a new room was added
@bp.post("/room/add")
def room_add():
    try:
        add_room_service(request.form.get("room"))
        flash("Room added successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))


# Tells user that a room was removed
@bp.post("/room/remove")
def room_remove():
    try:
        remove_room_service(request.form.get("room"))
        flash("Room removed successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))


# Tells user that a room was modified
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


# Tells user that a new lab was added
@bp.post("/lab/add")
def lab_add():
    try:
        add_lab_service(**request.form.to_dict())
        flash("Lab added successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))


# Tells user that a lab was removed
@bp.post("/lab/remove")
def lab_remove():
    try:
        remove_lab_service(**request.form.to_dict())
        flash("Lab removed successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))


# Tells user that a lab was modified
@bp.post("/lab/modify")
def modify_lab():
    try:
        modify_lab_service(**request.form.to_dict())
        flash("Lab modified successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))


# Tells user that a new course was added
@bp.post("/course/add")
def course_add():
    try:
        add_course_service(**request.form.to_dict())
        flash("Course added successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))


# Tells user that a course was removed
@bp.post("/course/remove")
def course_remove():
    try:
        remove_course_service(**request.form.to_dict())
        flash("Course removed successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))


# Tells user that a course was modified
@bp.post("/course/modify")
def course_modify():
    try:
        modify_course_service(**request.form.to_dict())
        flash("Course modified successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))


# Tells user that a new conflict was added
@bp.post("/conflict/add")
def conflict_add():
    try:
        add_conflict_service(**request.form.to_dict())
        flash("Conflict added successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))


# Tells user that a conflict was removed
@bp.post("/conflict/remove")
def conflict_remove():
    try:
        remove_conflict_service(**request.form.to_dict())
        flash("Conflict removed successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))


# Tells user that a conflict was modified
@bp.post("/conflict/modify")
def conflict_modify():
    try:
        modify_conflict_service(**request.form.to_dict())
        flash("Conflict modified successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))

# -------------------------
# Time Slot Routes
# -------------------------
@bp.post("/timeslot/add")
def timeslot_add():
    try:
        add_time_slot_service(**request.form.to_dict())
        flash("Time slot added successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))

@bp.post("/timeslot/remove")
def timeslot_remove():
    try:
        remove_time_slot_service(**request.form.to_dict())
        flash("Time slot removed successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))

@bp.post("/timeslot/modify")
def timeslot_modify():
    try:
        modify_time_slot_service(**request.form.to_dict())
        flash("Time slot modified successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))

# -------------------------
# Meeting Pattern Routes
# -------------------------
@bp.post("/pattern/add")
def pattern_add():
    try:
        add_pattern_service(**request.form.to_dict())
        flash("Pattern added successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))

@bp.post("/pattern/remove")
def pattern_remove():
    try:
        remove_pattern_service(**request.form.to_dict())
        flash("Meeting pattern removed successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))

@bp.post("/pattern/modify")
def pattern_modify():
    try:
        modify_pattern_service(**request.form.to_dict())
        flash("Meeting pattern modified successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))

@bp.post("/pattern/toggle")
def pattern_toggle():
    try:
        toggle_pattern_service(**request.form.to_dict())
        flash("Meeting pattern toggled successfully.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("config.editor"))
