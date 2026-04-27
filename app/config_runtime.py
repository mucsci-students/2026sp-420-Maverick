# Author: Antonio Corona
# Date: 2026-04-26
"""
Runtime configuration helpers for Maverick Scheduler.

Configuration lookup order:
1. app/local_settings.py
2. Environment variables
3. Safe defaults where appropriate
"""

import os


def _get_local_setting(name: str, default=None):
    """
    Safely read an optional value from app/local_settings.py.

    local_settings.py is intentionally optional so the app still works in
    GitHub Actions, production, and teammate environments.
    """
    try:
        from app import local_settings

        return getattr(local_settings, name, default)
    except ImportError:
        return default


def get_openai_api_key() -> str | None:
    """
    Return the OpenAI API key from local settings first, then environment.
    """
    return _get_local_setting("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")


def get_flask_secret_key() -> str:
    """
    Return the Flask secret key from local settings first, then environment.

    Falls back to a development key if nothing is provided.
    """
    return (
        _get_local_setting("FLASK_SECRET_KEY")
        or os.getenv("FLASK_SECRET_KEY")
        or "dev-secret-key"
    )


def get_openai_model() -> str:
    """
    Return the configured OpenAI model name.
    """
    return (
        _get_local_setting("MAVERICK_OPENAI_MODEL")
        or os.getenv("MAVERICK_OPENAI_MODEL")
        or "gpt-5-mini"
    )