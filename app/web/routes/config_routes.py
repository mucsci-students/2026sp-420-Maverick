

# app/web/routes/config_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.web.services.config_service import (
    load_config_into_session,
    save_config_from_session,
    get_config_status,
)

bp = Blueprint("config", __name__, url_prefix="/config")


@bp.get("/")
def editor():
    status = get_config_status()
    return render_template("config_editor.html", status=status)


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
