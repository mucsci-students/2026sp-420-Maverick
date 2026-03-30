# Author: Antonio Corona
# Date: 2026-03-27
"""
AI Service

Implements the core orchestration logic for the Sprint 3 Chunk A AI Chat Tool.

Responsibilities:
    - Build the base/system prompt for the AI tool
    - Submit a single user command to the OpenAI API
    - Keep each request stateless
    - Return a structured response for the Flask route layer

Architectural Role:
    - Acts as the Service-layer coordinator for AI-assisted configuration
      interactions.
    - Bridges the Flask controller layer and the OpenAI client utility layer.

High-Level Flow:
    1. Receive one natural language command from the route layer
    2. Build the system/base prompt
    3. Send one stateless request to the OpenAI Responses API
    4. Return the model's response in a UI-friendly structure

Notes:
    - This Phase 2 version does not yet execute backend tools/functions.
    - It focuses only on getting a real stateless AI response working.
"""

# Existing config service import used for pulling high-level status
# about the current configuration. We do not mutate config yet in Phase 2.
from app.web.services.config_service import get_config_status

# OpenAI client helper functions are isolated in their own module so that
# external API setup does not clutter the AI orchestration logic.
from app.web.services.openai_client import get_openai_client, get_model_name


# ------------------------------------------------------------------
# Base Prompt
# ------------------------------------------------------------------

BASE_PROMPT = """
You are the Maverick Scheduler AI Configuration Assistant.

You are part of a college course scheduling system.

Your job:
- Interpret exactly one scheduler configuration command at a time
- Help with scheduler configuration tasks only
- Stay within the scope of modifying or explaining scheduler configuration
- Do not assume any prior conversation history
- Treat each request as a standalone command
- If the request is unclear, unsupported, or outside scope, say so clearly
- For now, do not claim to have made changes unless the system explicitly confirms it

You may help with commands involving:
- courses
- faculty
- rooms
- labs
- conflicts
- configuration summaries

You must not:
- answer unrelated general-purpose questions
- rely on previous commands
- pretend that changes were applied when no backend tool executed
""".strip()


def build_base_prompt() -> str:
    """
    Return the fixed system/base prompt for the AI tool.

    Why this exists:
        Keeping the prompt isolated makes the service easier to test and
        easier to refine without changing route logic.

    Returns:
        str: The system prompt text.
    """
    return BASE_PROMPT


def build_user_input(user_command: str) -> str:
    """
    Build the user-facing request payload that will be sent to the model.

    Why this exists:
        We want the model to receive the current command plus a small amount
        of current application context, while still remaining stateless.

    Args:
        user_command (str): The one-off command entered by the user.

    Returns:
        str: A formatted user input string for the model.
    """
    status = get_config_status()

    # A small amount of app context helps the model respond more usefully
    # without introducing multi-turn memory. We only send current state.
    return f"""
Current application context:
- Config loaded: {status.get("loaded")}
- Config path: {status.get("path")}
- Counts: {status.get("counts")}
- Unsaved changes: {status.get("unsaved_changes", False)}
- Schedules updated: {status.get("schedules_updated", False)}

User command:
{user_command}
""".strip()


def extract_text_from_response(response) -> str:
    """
    Extract a readable text answer from an OpenAI response object.

    Why this exists:
        The SDK response object can contain structured content, so this helper
        gives us one predictable place to extract the final text shown in the UI.

    Args:
        response: The SDK response object returned by the API.

    Returns:
        str: The extracted text, or a fallback message if none is found.
    """
    # The official SDK exposes a convenience output_text field on Responses
    # objects when text output is available.
    text = getattr(response, "output_text", None)

    if text and str(text).strip():
        return str(text).strip()

    return "The AI request completed, but no text response was returned."


def process_ai_command(user_command: str) -> dict:
    """
    Process a single natural language command using the OpenAI API.

    Phase 2 Behavior:
        - Sends one stateless request to OpenAI
        - Does not yet execute backend tools/functions
        - Returns interpretation/help text only

    Args:
        user_command (str): The current one-off AI command from the user.

    Returns:
        dict: Structured result for the Flask route/template layer.
    """
    cleaned_command = (user_command or "").strip()

    if not cleaned_command:
        return {
            "success": False,
            "message": "No command was provided.",
            "changes_applied": False,
            "tool_calls": [],
        }

    # Create the SDK client and resolve the configured model.
    client = get_openai_client()
    model_name = get_model_name()

    # Send a single request to the OpenAI Responses API.
    # This is intentionally stateless:
    # - no conversation memory
    # - no prior messages
    # - only the current base prompt and current command/context
    response = client.responses.create(
        model=model_name,
        instructions=build_base_prompt(),
        input=build_user_input(cleaned_command),
    )

    ai_message = extract_text_from_response(response)

    return {
        "success": True,
        "message": ai_message,
        "changes_applied": False,
        "tool_calls": [],
        "model": model_name,
    }