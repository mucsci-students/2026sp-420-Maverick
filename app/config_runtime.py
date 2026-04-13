# Author: Antonio Corona
# Date: 2026-04-13
"""
Runtime configuration helpers for Maverick Scheduler.

Configuration lookup order:
1. Environment variables
2. Safe defaults where appropriate
"""

import os

OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
FLASK_SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
MAVERICK_OPENAI_MODEL: str = os.getenv("MAVERICK_OPENAI_MODEL", "gpt-5-mini")


def get_openai_api_key() -> str | None:
    """
    Return the OpenAI API key from environment variables.
    """
    return OPENAI_API_KEY


def get_flask_secret_key() -> str:
    """
    Return the Flask secret key from environment variables.

    Falls back to a development key if nothing is provided.
    """
    return FLASK_SECRET_KEY


def get_openai_model() -> str:
    """
    Return the configured OpenAI model name.
    """
    return MAVERICK_OPENAI_MODEL
