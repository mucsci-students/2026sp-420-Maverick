# app/web/routes/run_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.web.services.run_service import generate_schedules_into_session

bp = Blueprint("run", __name__, url_prefix="/run")


@bp.get("/")
def generator():
    return render_template("generator.html")


@bp.post("/generate")
def generate():
    try:
        limit = int(request.form.get("limit", "5"))
        optimize = request.form.get("optimize") == "on"
    except ValueError:
        flash("Limit must be an integer.", "error")
        return redirect(url_for("run.generator"))

    try:
        count = generate_schedules_into_session(limit=limit, optimize=optimize)
        flash(f"Generated {count} schedule(s).", "success")
        return redirect(url_for("viewer.viewer"))
    except Exception as e:
        flash(f"Generate failed: {e}", "error")
        return redirect(url_for("run.generator"))
