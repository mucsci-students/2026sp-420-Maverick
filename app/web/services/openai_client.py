# Author: Antonio Corona
# Date: 2026-03-26
"""
OpenAI Client Utilities

Provides helper functions for creating and configuring the OpenAI client
used by the Maverick Scheduler AI Chat Tool.

Responsibilities:
    - Load OpenAI configuration from environment variables
    - Provide a central place for model selection
    - Isolate third-party client setup from service/controller logic

Architectural Role:
    - Supports the Service layer by encapsulating external API setup.
    - Prevents route/controller code from depending directly on SDK details.

Notes:
    - In Phase 1, this file exists as a scaffold.
    - The real client setup is added in Phase 2.
"""


def get_model_name() -> str:
    """
    Return the configured model name for the AI feature.

    Phase 1:
        This is a placeholder function so the file exists and the
        project structure is ready for Phase 2.

    Returns:
        str: Default placeholder model name.
    """
    return "gpt-5-mini"