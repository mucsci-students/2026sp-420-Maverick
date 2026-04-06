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

# Flask helpers for routing, form handling, flashing messages,
# redirecting the user, and rendering HTML templates.
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

# Import the service-layer function that will process a single AI command.
from app.web.services.ai_service import process_ai_command

# Import the existing session key used by the config editor so that
# the AI feature can verify that a configuration is currently loaded.
from app.web.services.config_service import SESSION_CONFIG_KEY


# Create a dedicated Blueprint for AI chat functionality.
# This keeps the Chunk A feature isolated from the existing config,
# generator, and viewer blueprints.
bp = Blueprint("ai", __name__, url_prefix="/ai")


@bp.get("/")
def ai_chat():
    """
    Route: GET /ai

    Purpose:
        Render the AI Chat page.

    Behavior:
        - Checks whether a working configuration is loaded in session
        - Passes that status to the template
        - Renders the AI chat interface

    Why this exists:
        The user needs a dedicated screen for entering natural language
        commands like "Add course CS102 with 3 credits".
    """
    config_loaded = SESSION_CONFIG_KEY in session

    return render_template(
        "ai_chat.html",
        title="AI Chat",
        config_loaded=config_loaded,
    )


@bp.post("/command")
def ai_command():
    """
    Route: POST /ai/command

    Purpose:
        Accept a single natural language command from the AI Chat page
        and send it to the AI service layer for processing.

    Behavior:
        - Validates that a config is loaded
        - Validates that the user entered a command
        - Calls the AI service
        - Re-renders the AI page with the result

    Why this exists:
        This is the controller entry point for one-off, stateless AI
        command execution.
    """
    # Read the submitted command from the HTML form.
    user_command = request.form.get("command", "").strip()

    # The AI tool should only operate when a config is already loaded,
    # since its purpose is to modify the current working configuration.
    config_loaded = SESSION_CONFIG_KEY in session

    if not config_loaded:
        flash("Load a configuration before using AI Chat.", "error")
        return redirect(url_for("ai.ai_chat"))

    if not user_command:
        flash("Please enter a command.", "error")
        return redirect(url_for("ai.ai_chat"))

    try:
        # Call the AI service with the single current command only.
        # This is intentionally stateless.
        result = process_ai_command(user_command)

    except Exception as e:
        # If the AI layer raises an unexpected error, display it safely.
        result = {
            "success": False,
            "message": f"AI processing failed: {e}",
            "changes_applied": False,
            "tool_calls": [],
        }

    return render_template(
        "ai_chat.html",
        title="AI Chat",
        config_loaded=True,
        user_command=user_command,
        ai_result=result,
    )
