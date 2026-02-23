# Author: Antonio Corona
# Date: 2026-02-22
"""
Schedule Generator Routes

Defines Flask endpoints for generating schedules.

Responsibilities:
- Accept limit override input
- Accept optimization override selection
- Trigger schedule generation
- Redirect to the Schedule Viewer upon completion

These routes serve as Controllers in the MVC structure.
"""

# app/web/routes/run_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.web.services.run_service import generate_schedules_into_session, KNOWN_OPTIMIZER_FLAGS
from app.web.services.config_service import SESSION_CONFIG_KEY
from flask import session

bp = Blueprint("run", __name__, url_prefix="/run")


@bp.get("/")
def generator():
    cfg = session.get(SESSION_CONFIG_KEY)

    config_loaded = bool(cfg)
    default_limit = 5
    selected_flags = []
    available_flags = KNOWN_OPTIMIZER_FLAGS

    if cfg:
        default_limit = int(cfg.get("limit", 5))
        selected_flags = cfg.get("optimizer_flags", []) or []

        # (Optional) If you ever add new flags to configs, include them automatically:
        extra = [f for f in selected_flags if f not in available_flags]
        available_flags = available_flags + extra

    return render_template(
        "generator.html",
        config_loaded=config_loaded,
        default_limit=default_limit,
        selected_flags=selected_flags,
        available_flags=available_flags,
    )


@bp.post("/generate")
def generate():
    try:
        limit = int(request.form.get("limit", "5"))
        if limit < 1:
            flash("Limit must be at least 1.", "error")
            return redirect(url_for("run.generator"))

        # Multi-select flags (can be empty list if user unchecked all)
        optimizer_flags = request.form.getlist("optimizer_flags")

    except ValueError:
        flash("Limit must be an integer.", "error")
        return redirect(url_for("run.generator"))

    try:
        count = generate_schedules_into_session(limit=limit, optimizer_flags=optimizer_flags)
        flash(f"Generated {count} schedule(s).", "success")
        return redirect(url_for("viewer.viewer"))
    except Exception as e:
        flash(f"Generate failed: {e}", "error")
        return redirect(url_for("run.generator"))
