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

OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
FLASK_SECRET_KEY: str | None = os.getenv("FLASK_SECRET_KEY")
MAVERICK_OPENAI_MODEL: str | None = os.getenv("MAVERICK_OPENAI_MODEL")

try:
    from app.local_settings import (
        FLASK_SECRET_KEY as LOCAL_FLASK_SECRET_KEY,
    )
    from app.local_settings import (
        MAVERICK_OPENAI_MODEL as LOCAL_MAVERICK_OPENAI_MODEL,
    )
    from app.local_settings import (
        OPENAI_API_KEY as LOCAL_OPENAI_API_KEY,
    )

    OPENAI_API_KEY = LOCAL_OPENAI_API_KEY
    FLASK_SECRET_KEY = LOCAL_FLASK_SECRET_KEY
    MAVERICK_OPENAI_MODEL = LOCAL_MAVERICK_OPENAI_MODEL
except ImportError:
    pass


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
