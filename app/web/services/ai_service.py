# Author: Antonio Corona
# Date: 2026-03-26
"""
AI Service

Implements the core orchestration logic for the Sprint 3 Chunk A AI Chat Tool.

Responsibilities:
    - Build the base/system prompt for the AI tool
    - Receive a single natural language command
    - Return a structured response to the Flask route layer
    - Serve as the main orchestration layer for later OpenAI integration

Architectural Role:
    - Acts as the Service-layer coordinator for AI-assisted configuration
      interactions.
    - Bridges the Flask controller layer and future backend tool execution.

High-Level Flow:
    1. Receive one command from the route/controller
    2. Build the prompt context for that command
    3. Process the command
    4. Return a structured result dictionary for rendering

Notes:
    - This Phase 1 version is a scaffold only.
    - It does not yet call the OpenAI API.
    - It exists to get the route/template/UI path working first.
"""

# ------------------------------------------------------------------
# Base Prompt
# ------------------------------------------------------------------

# This prompt will later be sent to the OpenAI model.
# For now, its defined early so the structure of the feature
# is already in place before the real API call is added.
BASE_PROMPT = """
You are the Maverick Scheduler AI Configuration Assistant.

Your role:
- Help interpret one natural language configuration command at a time
- Work only within scheduler configuration tasks
- Do not answer unrelated questions
- Do not assume prior conversation context
- Treat every request as a standalone command
- Only perform allowed configuration-related operations

If a command is unsupported, unclear, or outside scope, explain that clearly.
""".strip()


def build_base_prompt() -> str:
    """
    Return the fixed system/base prompt for the AI tool.

    Why this exists:
        Keeping prompt construction in its own function makes the service
        easier to test and easier to evolve later when tools are added.

    Returns:
        str: The base prompt used to constrain AI behavior.
    """
    return BASE_PROMPT


def process_ai_command(user_command: str) -> dict:
    """
    Process a single natural language command.

    Phase 1 Behavior:
        - Does NOT yet call OpenAI
        - Returns a placeholder result so the route/template flow can be
          tested end-to-end before API integration begins

    Args:
        user_command (str): The current one-off command entered by the user.

    Returns:
        dict: Structured response for the route/template layer.
    """
    # Defensive cleanup to keep behavior predictable.
    cleaned_command = (user_command or "").strip()

    # In Phase 1, this is only a scaffold response.
    # This lets you verify the AI page, form submission, and controller/service
    # connection before layering in the OpenAI SDK.
    return {
        "success": True,
        "message": (
            "Phase 1 scaffold is working. "
            f"Received command: '{cleaned_command}'. "
            "OpenAI integration has not been enabled yet."
        ),
        "changes_applied": False,
        "tool_calls": [],
        "base_prompt_used": build_base_prompt(),
    }