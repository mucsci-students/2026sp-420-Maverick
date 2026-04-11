# Author: Antonio Corona
# Date: 2026-04-05
"""
Runtime configuration helpers for Maverick Scheduler.

Configuration lookup order:
1. app/local_settings.py
2. Environment variables
3. Safe defaults where appropriate
"""

import os

try:
    from app.local_settings import (
        FLASK_SECRET_KEY,
        MAVERICK_OPENAI_MODEL,
        OPENAI_API_KEY,
    )
except ImportError:
    OPENAI_API_KEY = None
    FLASK_SECRET_KEY = None
    MAVERICK_OPENAI_MODEL = None


def get_openai_api_key() -> str | None:
    """
    Return the OpenAI API key from local settings or environment.
    """
    return OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")


def get_flask_secret_key() -> str:
    """
    Return the Flask secret key from local settings or environment.

    Falls back to a development key if nothing is provided.
    """
    return FLASK_SECRET_KEY or os.environ.get("FLASK_SECRET_KEY") or "dev-secret-key"


def get_openai_model() -> str:
    """
    Return the configured OpenAI model name.
    """
    return (
        MAVERICK_OPENAI_MODEL or os.environ.get("MAVERICK_OPENAI_MODEL") or "gpt-5-mini"
    )
