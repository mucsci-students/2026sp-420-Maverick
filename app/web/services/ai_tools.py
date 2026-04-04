# Author: Antonio Corona
# Date: 2026-04-04
"""
AI Tool Definitions and Dispatching

This file defines:
1. Tool schemas (what AI is allowed to call)
2. Tool dispatcher (how Python executes them)

IMPORTANT:
- AI never edits config directly
- All mutations go through controlled backend service functions
"""

from app.web.services.config_service import (
    add_course_service,
    modify_course_service,
    remove_room_service,
)


# ---------------------------------------------------
# TOOL DEFINITIONS (WHAT AI CAN DO)
# ---------------------------------------------------

def get_tool_definitions():
    """
    Returns tool schemas that OpenAI can call.
    """

    return [
        {
            "type": "function",
            "name": "add_course",
            "description": "Add a new course to the loaded scheduler configuration",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_id": {"type": "string"},
                    "credits": {"type": "integer"},
                    "room": {"type": "string"}
                },
                "required": ["course_id", "credits", "room"]
            }
        },
        {
            "type": "function",
            "name": "modify_course_credits",
            "description": "Modify the credits of an existing course",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_id": {"type": "string"},
                    "credits": {"type": "integer"}
                },
                "required": ["course_id", "credits"]
            }
        },
        {
            "type": "function",
            "name": "remove_room",
            "description": "Remove a room from the configuration",
            "parameters": {
                "type": "object",
                "properties": {
                    "room": {"type": "string"}
                },
                "required": ["room"]
            }
        },
    ]


# ---------------------------------------------------
# TOOL DISPATCHER (HOW PYTHON EXECUTES THEM)
# ---------------------------------------------------

def execute_tool(tool_name: str, args: dict) -> dict:
    """
    Executes a tool chosen by the AI.

    Args:
        tool_name: Name of the function
        args: Arguments from AI

    Returns:
        dict: Standardized result payload
    """
    try:
        if tool_name == "add_course":
            return add_course_tool(args)

        if tool_name == "modify_course_credits":
            return modify_course_credits_tool(args)

        if tool_name == "remove_room":
            return remove_room_tool(args)

        return {
            "success": False,
            "message": f"Unsupported tool: {tool_name}",
            "changes_applied": False,
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "changes_applied": False,
        }


# ---------------------------------------------------
# TOOL IMPLEMENTATIONS
# ---------------------------------------------------

def add_course_tool(args: dict) -> dict:
    """
    Add a course using the existing config service wrapper.

    Why:
        This ensures the session config, working file, unsaved changes,
        schedule freshness, and conflict detection are all updated
        through the normal app workflow.
    """
    add_course_service(
        course_id=args["course_id"],
        credits=args["credits"],
        room=args["room"],
    )

    return {
        "success": True,
        "message": (
            f"Added course {args['course_id']} with "
            f"{args['credits']} credits in room {args['room']}."
        ),
        "changes_applied": True,
    }


def modify_course_credits_tool(args: dict) -> dict:
    """
    Modify an existing course's credits using the service wrapper.
    """
    modify_course_service(
        course_id=args["course_id"],
        credits=args["credits"],
    )

    return {
        "success": True,
        "message": (
            f"Updated course {args['course_id']} "
            f"to {args['credits']} credits."
        ),
        "changes_applied": True,
    }


def remove_room_tool(args: dict) -> dict:
    """
    Remove a room using the existing room service wrapper.

    Why:
        The repo's room removal logic also cleans up related references
        in courses and faculty preferences.
    """
    remove_room_service(args["room"])

    return {
        "success": True,
        "message": f"Removed room {args['room']}.",
        "changes_applied": True,
    }