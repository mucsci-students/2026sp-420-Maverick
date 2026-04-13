# Author: Antonio Corona
# Date: 2026-03-02
"""
Schedule Generator Routes

Purpose:
    Defines Flask endpoints for generating schedules.

Responsibilities:
    - Render the Schedule Generator UI.
    - Accept per-run limit overrides.
    - Accept per-run optimizer flag overrides (multi-select).
    - Persist override state in session.
    - Trigger schedule generation
    - Redirect to the Schedule Viewer upon completion

Architectural Role (MVC):
    - Acts as the Controller layer for schedule generation.
    - Receives user input from the Generator View (HTML form).
    - Delegates scheduling work to the Model/Service layer.
    - Manages session-based UI override state.

High-Level Flow:
    1. GET  /run/
       - Render Generator page.
       - Default UI fields to JSON config values.
       - Apply session overrides if previously set.

    2. POST /run/generate
       - Validate form inputs.
       - Persist per-run overrides in session.
       - Call Service layer to generate schedules.
       - Redirect to Viewer on success.

    3. POST /run/reset
       - Clear per-run overrides from session.
       - Restore UI defaults to JSON config values.
"""

# app/web/routes/run_routes.py

# ==================================================
# Imports
# ==================================================

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,  # Session access for checking loaded config defaults
    url_for,
)

from app.web.services.config_service import (
    SESSION_CONFIG_KEY,
)  # Where the loaded config is stored
from app.web.services.progress_store import (
    generation_progress,
    is_running,
    progress_lock,
)
from app.web.services.run_service import (
    KNOWN_OPTIMIZER_FLAGS,  # Shared list of valid optimizer flags for UI + validation
    SESSION_GENERATOR_FLAGS_OVERRIDE_KEY,
    SESSION_GENERATOR_LIMIT_OVERRIDE_KEY,
    generate_schedules_into_session,
)

# ==================================================
# Blueprint Setup
# ==================================================

# Blueprint:
#   - Name: "run"
#   - URL Prefix: /run
#   - All generator-related routes are grouped under this namespace.
bp = Blueprint("run", __name__, url_prefix="/run")


# ==================================================
# Helper function
# ==================================================
def _get_session_id() -> str:
    sid = getattr(session, "sid", None)
    if isinstance(sid, str) and sid:
        return sid

    test_sid = session.get("_test_sid")
    if isinstance(test_sid, str) and test_sid:
        return test_sid

    return "default-session"


# ==================================================
# Route: Generator Page (GET)
# ==================================================


@bp.get("/")
def generator():
    """
    Purpose:
        Renders the schedule generator page.

    Behavior:
        - If a configuration is loaded:
            * Default limit comes from JSON config.
            * Default optimizer flags come from JSON config.
            * Session overrides (if present) take precedence.
        - If no configuration is loaded:
            * UI will render in disabled state (handled in template).

    Returns:
        Rendered generator.html with UI state context.
    """

    # ----------------------------------------
    # 1. Retrieve Configuration from Session
    # ----------------------------------------

    cfg = session.get(SESSION_CONFIG_KEY)

    # ----------------------------------------
    # 2. Compute Default UI Values
    # ----------------------------------------
    # These values drive the Generator template defaults.

    config_loaded = bool(cfg)  # Used to disable/enable Generate UI

    # Fallback defaults (used if config missing limit)
    default_limit = 5
    selected_flags = []

    available_flags = (
        KNOWN_OPTIMIZER_FLAGS  # Full supported list for checkbox rendering
    )

    if cfg:
        # JSON defaults
        json_default_limit = int(cfg.get("limit", 5))
        json_selected_flags = cfg.get("optimizer_flags", []) or []

        # Apply session overrides if present
        default_limit = int(
            session.get(SESSION_GENERATOR_LIMIT_OVERRIDE_KEY, json_default_limit)
        )
        selected_flags = (
            session.get(SESSION_GENERATOR_FLAGS_OVERRIDE_KEY, json_selected_flags) or []
        )

        # Optional: If config contains a flag not listed in KNOWN_OPTIMIZER_FLAGS,
        # include it to avoid hiding/losing that config state in the UI.
        extra = [f for f in selected_flags if f not in available_flags]
        available_flags = available_flags + extra

    # ----------------------------------------
    # 3. Render the View
    # ----------------------------------------

    return render_template(
        "generator.html",
        config_loaded=config_loaded,
        default_limit=default_limit,
        selected_flags=selected_flags,
        available_flags=available_flags,
    )


# ==================================================
# Route: Generate Schedules (POST)
# ==================================================
@bp.post("/generate")
def generate():
    """
    Purpose:
        Handles schedule generation requests from the Generator UI.

    Validations:
        - limit must be an integer >= 1
        - optimizer_flags may be empty (valid case)

    Flow:
        1. Parse + validate user input.
        2. Persist overrides in session.
        3. Delegate generation to Service layer.
        4. Redirect to Viewer on success.
        5. Flash user-facing error messages on failure.
    """

    # ----------------------------------------
    # 1. Parse + Validate User Overrides
    # ----------------------------------------

    try:
        # Limit override: required to be a positive integer
        limit = int(request.form.get("limit", "5"))

        if limit < 1:
            flash("Limit must be at least 1.", "error")
            return redirect(url_for("run.generator"))

        # Optimization override: multi-select checkbox list
        # NOTE: This can be empty if user unchecks all flags.
        optimizer_flags = request.form.getlist("optimizer_flags")

    except ValueError:
        flash("Limit must be an integer.", "error")
        return redirect(url_for("run.generator"))

    # ----------------------------------------
    # 2. Generate Schedules via Service Layer
    # ----------------------------------------

    session_id = _get_session_id()

    try:
        # Persist Generator overrides so the UI stays consistent after generating
        session[SESSION_GENERATOR_LIMIT_OVERRIDE_KEY] = limit
        session[SESSION_GENERATOR_FLAGS_OVERRIDE_KEY] = optimizer_flags

        count = generate_schedules_into_session(
            limit=limit, optimizer_flags=optimizer_flags
        )

        flash(f"Generated {count} schedule(s).", "success")

        # lets the js handle the redirect
        return ("", 204)

    except Exception as e:
        # Catch-all so UI doesn't crash on user-facing errors
        with progress_lock:
            generation_progress[session_id] = 0
            is_running[session_id] = False

        flash(f"Generate failed: {e}", "error")
        return redirect(url_for("run.generator"))


# ==================================================
# Route: POST /run/reset
# ==================================================


@bp.post("/reset")
def reset():
    """
    Purpose:
        Clears per-run Generator override state from session.

    Behavior:
        - Removes stored limit override.
        - Removes stored optimizer flag override.
        - Restores Generator UI to JSON config defaults.

    Does NOT:
        - Modify the underlying configuration.
        - Delete generated schedules.
    """
    session.pop(SESSION_GENERATOR_LIMIT_OVERRIDE_KEY, None)
    session.pop(SESSION_GENERATOR_FLAGS_OVERRIDE_KEY, None)

    session_id = _get_session_id()

    # clears the session progress
    with progress_lock:
        generation_progress[session_id] = 0
        is_running[session_id] = False

    flash("Reset Generator settings to config defaults.", "success")
    return redirect(url_for("run.generator"))


# ==================================================
# Route: Generation Progress (GET)
# ==================================================
@bp.get("/progress")
def get_progress():
    """
    Returns the current generation progress (from 0 -> 100)
    """
    session_id = _get_session_id()

    with progress_lock:
        progress = generation_progress.get(session_id, 0)

    return {"progress": progress}
