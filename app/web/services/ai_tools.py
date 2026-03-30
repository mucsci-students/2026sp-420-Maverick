# Author: Antonio Corona
# Date: 2026-03-26
"""
AI Tool Definitions and Dispatching

Defines the backend tool layer for the Sprint 3 Chunk A AI Chat Tool.

Responsibilities:
    - Hold future tool schemas for allowed AI operations
    - Serve as the controlled bridge between AI output and backend logic
    - Keep tool execution isolated from prompt/orchestration logic

Architectural Role:
    - Will act as the execution layer between the AI service and the
      existing scheduler configuration services.

Notes:
    - In Phase 1 and Phase 2, this file is still a scaffold.
    - Real tool definitions are added in the next implementation phase.
"""


def get_tool_definitions() -> list:
    """
    Return the list of tool definitions available to the AI model.

    Phase 1 / Phase 2:
        This returns an empty list because tool calling is not yet wired in.

    Returns:
        list: Empty tool list placeholder.
    """
    return []