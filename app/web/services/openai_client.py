# Author: Antonio Corona
# Date: 2026-03-27
"""
OpenAI Client Utilities

Provides helper functions for creating and configuring the OpenAI client
used by the Maverick Scheduler AI Chat Tool.

Responsibilities:
    - Load OpenAI configuration from environment variables
    - Create the OpenAI client instance
    - Provide a central location for model selection
    - Isolate third-party API setup from service/controller logic

Architectural Role:
    - Supports the Service layer by encapsulating external API setup.
    - Prevents route/controller code from depending directly on SDK details.

Notes:
    - The API key must be provided through environment variables.
    - The default model for Chunk A is gpt-5-mini unless overridden.
"""

# Standard library access for reading environment variables.
import os

# Official OpenAI Python SDK client class.
from openai import OpenAI


def get_openai_client() -> OpenAI:
    """
    Create and return an OpenAI client instance.

    Why this exists:
        Keeping client creation in one place makes the codebase easier
        to maintain, test, and update later.

    Returns:
        OpenAI: Configured client instance.

    Raises:
        ValueError: If the OPENAI_API_KEY environment variable is missing.
    """
    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "Missing OPENAI_API_KEY environment variable. "
            "Add it to your environment or .env file before using AI Chat."
        )

    return OpenAI(api_key=api_key)


def get_model_name() -> str:
    """
    Return the model name used for the AI Chat Tool.

    Why this exists:
        Centralizing model selection makes it easy to switch models later
        without changing route or service logic.

    Returns:
        str: The configured model name.
    """
    return os.environ.get("MAVERICK_OPENAI_MODEL", "gpt-5-mini")