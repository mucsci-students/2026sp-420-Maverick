# Author: Antonio Corona
# Date: 2026-04-05
"""
OpenAI Client Utilities

Provides helper functions for creating and configuring the OpenAI client
used by the Maverick Scheduler AI Chat Tool.
"""

from openai import OpenAI

from app.config_runtime import get_openai_api_key, get_openai_model


def get_openai_client() -> OpenAI:
    """
    Create and return an OpenAI client instance.

    Raises:
        ValueError: If no OpenAI API key is configured.
    """
    api_key = get_openai_api_key()

    if not api_key:
        raise ValueError(
            "Missing OpenAI API key. Set it in app/local_settings.py "
            "or in the OPENAI_API_KEY environment variable."
        )

    return OpenAI(api_key=api_key)


def get_model_name() -> str:
    """
    Return the configured model name for the AI tool.
    """
    return get_openai_model()