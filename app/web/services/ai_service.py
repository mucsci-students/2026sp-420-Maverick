# Author: Antonio Corona
# Date: 2026-04-04
"""
AI Service

Implements the core orchestration logic for the Sprint 3 Chunk A AI Chat Tool.

Responsibilities:
    - Build the base/system prompt for the AI tool
    - Submit a single user command to the OpenAI API
    - Provide tool definitions (function-calling interface)
    - Detect and execute backend tools selected by the AI
    - Return structured results for the Flask route layer

Architectural Role:
    - Acts as the Service-layer coordinator for AI-assisted configuration
      interactions.
    - Bridges the Flask controller layer and:
        • OpenAI client (external API)
        • AI tool execution layer (internal backend logic)

High-Level Flow:
    1. Receive one natural language command from the route layer
    2. Build the system/base prompt
    3. Send a stateless request to the OpenAI Responses API
    4. Allow the model to select a tool (if applicable)
    5. Execute the selected tool via ai_tools.py
    6. Return a structured result (success, message, changes_applied)

Notes:
    - This implementation is stateless (no conversation history).
    - All configuration changes are executed through approved tools.
    - The AI never directly modifies configuration data.
"""

import json

from app.web.services.ai_tools import execute_tool, get_tool_definitions

# Existing config service import used for pulling high-level status
# about the current configuration. We do not mutate config yet in Phase 2.
from app.web.services.config_service import _get_working_config, get_config_status

# OpenAI client helper functions are isolated in their own module so that
# external API setup does not clutter the AI orchestration logic.
from app.web.services.openai_client import get_model_name, get_openai_client

# ------------------------------------------------------------------
# Base Prompt
# ------------------------------------------------------------------

BASE_PROMPT = """
You are the Maverick Scheduler AI Configuration Assistant.

You are part of a college course scheduling system.

Your job:
- Interpret exactly one scheduler configuration command at a time
- Help only with scheduler configuration tasks
- Stay within the scope of modifying or explaining scheduler configuration
- Do not assume any prior conversation history
- Treat each request as a standalone command
- If the request is unclear, unsupported, or outside scope, say so clearly
- Do not claim that changes were applied unless a backend tool executes successfully

Approved tool-based actions currently include:
- adding, removing, and modifying faculty
- adding, removing, and modifying rooms
- adding, removing, and modifying labs
- adding and removing courses
- renaming courses
- changing course credits
- changing course rooms
- changing course labs
- changing course faculty assignments
- changing course conflict lists
- adding, removing, and modifying course conflicts

When using tools:
- Only call a tool if the required arguments are known
- Do not invent values that were not provided
- Prefer exact names for course IDs, rooms, labs, and faculty
- If required information is missing, 
  respond with a clarification-style message instead of guessing
- Use the most specific available tool for the request
- Do not use a broad course modification pattern when a specific course tool exists

For faculty availability:
- use set_faculty_day_unavailable to mark a faculty member unavailable on a specific day

For course updates, use the most specific available tool:
- use rename_course for renaming a course
- use modify_course_credits for changing credits
- use modify_course_room for changing a room
- use modify_course_lab for assigning or changing a lab
- use remove_course_lab for removing a lab from a course
- use modify_course_faculty for changing faculty assignments
- use modify_course_conflicts for changing conflict lists
- use add_conflict or remove_conflict when the user wants to add 
  or remove a single conflict relationship

Examples:
- "Rename course CS163 to CS370" -> rename_course
- "Change the credits of CS199 to 4" -> modify_course_credits
- "Change the room for CS163 to Roddy 147" -> modify_course_room
- "Change the lab for CS163 to Linux" -> modify_course_lab
- "Set the faculty for CS163 to Hardy and Xie" -> modify_course_faculty
- "Set the conflicts for CS163 to CMSC 330 and CMSC 362" -> modify_course_conflicts
- "Add a conflict between CMSC 140 and CMSC 161" -> add_conflict
- "Remove the conflict between CMSC 140 and CMSC 161" -> remove_conflict

You must not:
- answer unrelated general-purpose questions
- rely on previous commands
- modify configuration directly
- pretend that a change succeeded when no tool executed
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

    cfg = _get_working_config()

    # Extract useful context (NOT entire config)
    courses = [c["course_id"] for c in cfg.get("config", {}).get("courses", [])]
    rooms = cfg.get("config", {}).get("rooms", [])

    # A small amount of app context helps the model respond more usefully
    # without introducing multi-turn memory. We only send current state.
    return f"""
Current application context:
- Config loaded: {status.get("loaded")}
- Courses: {courses[:10]}
- Rooms: {rooms[:10]}

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
    # The OpenAI Responses API exposes a convenience `output_text` field
    # when the model returns plain text (no tool call).
    # We use this as the fallback when no function execution occurs.
    text = getattr(response, "output_text", None)

    if text and str(text).strip():
        return str(text).strip()

    return "The AI request completed, but no text response was returned."


def process_ai_command(user_command: str) -> dict:
    """
    Process a single natural language command using the OpenAI API.

    Phase 3 Behavior:
        - Sends one stateless request to OpenAI
        - Provides tool definitions (function-calling interface)
        - Detects and executes backend tools when selected by the model
        - Returns either:
            • A tool execution result (changes applied)
            • Or a plain-text AI response (no changes applied)

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
        tools=get_tool_definitions(),
    )

    # ---------------------------------------------
    # TOOL HANDLING
    # ---------------------------------------------
    # The Responses API may return structured output items.
    # If the model selects one of our approved function tools:
    #   1. Extract the tool name and JSON arguments
    #   2. Parse the arguments safely
    #   3. Execute the tool via ai_tools.execute_tool()
    #   4. Return the backend result immediately
    #
    # This ensures:
    #   - AI does not directly modify configuration
    #   - All changes go through controlled service-layer logic
    #   - The system remains safe and deterministic

    for item in getattr(response, "output", []):
        item_type = getattr(item, "type", None)

        # Function tools are returned as "function_call" items.
        if item_type == "function_call":
            tool_name = getattr(item, "name", None)
            raw_arguments = getattr(item, "arguments", "{}")

            try:
                arguments = json.loads(raw_arguments)
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "message": (
                        f"AI returned invalid tool arguments for '{tool_name}'."
                    ),
                    "changes_applied": False,
                    "tool_calls": [tool_name] if tool_name else [],
                    "model": model_name,
                }

            result = execute_tool(tool_name, arguments)

            # Optional but useful: include tool name in the result payload
            result.setdefault("tool_calls", [tool_name] if tool_name else [])
            result.setdefault("model", model_name)

            return result

    ai_message = extract_text_from_response(response)

    return {
        "success": True,
        "message": ai_message,
        "changes_applied": False,
        "tool_calls": [],
        "model": model_name,
    }
