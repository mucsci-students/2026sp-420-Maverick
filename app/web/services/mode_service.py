# Author: Antonio Corona
# Date: 2026-04-26
"""
File: mode_service.py
Purpose:
    Manage Viewer / Editor mode state for the application using Flask session storage.

Responsibilities:
- Store and retrieve the current application mode from the session
- Enforce valid mode values (viewer/editor)
- Provide helper checks for conditional behavior in routes and views

Notes:
- Defaults to EDITOR_MODE if no session value is set or an invalid mode is provided.
- Relies on Flask session, so this requires a properly configured secret key.
- Setting session.modified ensures the session is persisted
    even if the value is unchanged.
"""

from flask import session

# Session key used to persist the current application mode
SESSION_APP_MODE_KEY = "app_mode"

# Supported application modes
VIEWER_MODE = "viewer"
EDITOR_MODE = "editor"


def get_mode():
    """
    Retrieve the current application mode from the session.

    Defaults to EDITOR_MODE if no mode has been set yet.
    """
    return session.get(SESSION_APP_MODE_KEY, EDITOR_MODE)


def set_mode(mode: str):
    """
    Set the application mode in the session.

    If an invalid mode is provided, falls back to EDITOR_MODE to maintain
    predictable behavior and avoid unsupported states.

    Side Effects:
    - Updates Flask session storage
    - Marks session as modified to ensure persistence
    """
    if mode not in {VIEWER_MODE, EDITOR_MODE}:
        mode = EDITOR_MODE

    session[SESSION_APP_MODE_KEY] = mode
    # Explicitly mark session as modified to ensure Flask saves the change
    session.modified = True
    return mode


def is_viewer():
    """
    Check if the application is currently in Viewer Mode.

    Used to disable editing functionality in routes or templates.
    """
    return get_mode() == VIEWER_MODE


def is_editor():
    """
    Check if the application is currently in Editor Mode.

    Used to allow full editing functionality when enabled.
    """
    return get_mode() == EDITOR_MODE
