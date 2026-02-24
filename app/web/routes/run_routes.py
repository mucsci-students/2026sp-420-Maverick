# Author: Antonio Corona
# Date: 2026-02-23
"""
Schedule Generator Routes

Defines Flask endpoints for generating schedules.

Responsibilities:
    - Accept limit override input
    - Accept optimization override selection (multi-flag)
    - Trigger schedule generation
    - Redirect to the Schedule Viewer upon completion

Architectural Role (MVC):
    - Acts as the Controller layer for schedule generation.
    - Receives user input from the Generator View (HTML form).
    - Delegates scheduling work to the Model/Service layer.

High-Level Flow:
    1. GET /run/
        - Render Generator page
        - Default UI fields to JSON config values (limit + optimizer_flags)
    2. POST /run/generate
        - Validate form inputs
        - Apply per-run overrides
        - Generate schedules and store results in session
        - Redirect to Viewer
"""

# app/web/routes/run_routes.py

# ------------------------------
# Imports
# ------------------------------

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask import session  # Session access for checking loaded config defaults

from app.web.services.run_service import (
    generate_schedules_into_session,
    KNOWN_OPTIMIZER_FLAGS  # Shared list of valid optimizer flags for UI + validation
)
from app.web.services.config_service import SESSION_CONFIG_KEY  # Where the loaded config is stored


# ------------------------------
# Blueprint Setup
# ------------------------------

bp = Blueprint("run", __name__, url_prefix="/run")


# ------------------------------
# Route: Generator Page (GET)
# ------------------------------

@bp.get("/")
def generator():
    """
    Renders the schedule generator page.

    Behavior:
        - If a config is loaded, defaults the form fields to:
            * limit from JSON (cfg["limit"])
            * selected optimizer flags from JSON (cfg["optimizer_flags"])
        - If no config is loaded, the UI should display a "no config loaded"
          state (handled in the template).
    """

    # ----------------------------------------
    # 1. Retrieve Configuration from Session
    # ----------------------------------------

    cfg = session.get(SESSION_CONFIG_KEY)

    # ----------------------------------------
    # 2. Compute Default UI Values
    # ----------------------------------------
    # These values drive the Generator template defaults.

    config_loaded = bool(cfg)                 # Used to disable/enable Generate UI
    default_limit = 5                         # Fallback if config does not specify limit
    selected_flags = []                       # Flags to pre-check in UI
    available_flags = KNOWN_OPTIMIZER_FLAGS   # Full supported list for checkbox rendering

    if cfg:
        # Default limit comes from config when available
        default_limit = int(cfg.get("limit", 5))

        # Default selected optimizer flags come from config when available
        selected_flags = cfg.get("optimizer_flags", []) or []

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


# ------------------------------
# Route: Generate Schedules (POST)
# ------------------------------

@bp.post("/generate")
def generate():
    """
    Handles schedule generation requests from the Generator UI.

    Validates per-run overrides:
        - limit: integer >= 1
        - optimizer_flags: multi-select list (can be empty)

    Delegates actual scheduling work to the Service layer and redirects
    to the Viewer on success.
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

    try:
        count = generate_schedules_into_session(
            limit=limit,
            optimizer_flags=optimizer_flags
        )

        flash(f"Generated {count} schedule(s).", "success")
        return redirect(url_for("viewer.viewer"))

    except Exception as e:
        # Catch-all so UI doesn’t crash on user-facing errors
        flash(f"Generate failed: {e}", "error")
        return redirect(url_for("run.generator"))
