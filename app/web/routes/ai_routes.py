# Author: Antonio Corona
# Date: 2026-03-26
"""
AI Chat Routes

Defines Flask endpoints for the Sprint 3 Chunk A AI Chat Tool.

Responsibilities:
    - Render the AI chat interface page
    - Accept one-off natural language configuration commands
    - Pass user input to the AI service layer
    - Return AI results, errors, and status messages to the view

Architectural Role (MVC):
    - Acts as the Controller layer for AI chat interactions.
    - Receives HTTP requests from the AI Chat View.
    - Delegates processing to the AI service layer.
    - Returns rendered templates with result data.

Notes:
    - This feature is intentionally stateless.
    - Each command is processed independently.
    - No prior conversation history is required or assumed.
"""

from flask import Blueprint, render_template, request, flash, session
from app.web.services.ai_service import process_ai_command
from app.web.services.config_service import SESSION_CONFIG_KEY

bp = Blueprint("ai", __name__, url_prefix="/ai")

@bp.get("/")
def ai_chat():
    config_loaded = SESSION_CONFIG_KEY in session
    return render_template("ai_chat.html", config_loaded=config_loaded)

@bp.post("/command")
def ai_command():
    user_command = request.form.get("command", "").strip()
    config_loaded = SESSION_CONFIG_KEY in session

    if not config_loaded:
        flash("Load a configuration before using AI Chat.", "error")
        return render_template("ai_chat.html", config_loaded=False)

    if not user_command:
        flash("Please enter a command.", "error")
        return render_template("ai_chat.html", config_loaded=True)

    result = process_ai_command(user_command)

    return render_template(
        "ai_chat.html",
        config_loaded=True,
        user_command=user_command,
        ai_result=result,
    )