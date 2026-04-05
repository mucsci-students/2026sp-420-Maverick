# Author: Antonio Corona
# Date: 2026-04-04
"""
AI Tool Definitions and Dispatching

Defines the approved AI tool schemas and maps them to the existing
scheduler configuration service-layer wrappers.

Design Rules:
- AI never edits JSON directly
- All configuration mutations go through config_service.py
- Tools are explicit, validated, and deterministic
- Unsupported tools are rejected safely
"""

from app.web.services.config_service import (
    add_faculty_service,
    remove_faculty_service,
    modify_faculty_service,
    add_room_service,
    remove_room_service,
    modify_room_service,
    add_lab_service,
    remove_lab_service,
    modify_lab_service,
    add_course_service,
    remove_course_service,
    modify_course_service,
    add_conflict_service,
    remove_conflict_service,
    modify_conflict_service,
)


# ---------------------------------------------------
# TOOL DEFINITIONS (WHAT AI CAN DO)
# ---------------------------------------------------

def get_tool_definitions():
    """
    Return the list of approved tools the AI is allowed to call.

    These schemas define:
    - the tool name
    - what the tool does
    - the allowed JSON arguments
    - which arguments are required
    """
    return [
        # --------------------------------------------------------
        # Faculty Tools
        # --------------------------------------------------------
        {
            "type": "function",
            "name": "add_faculty",
            "description": "Add a faculty member to the scheduler configuration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "appointment_type": {"type": "string"},
                    "day": {"type": "string"},
                    "time_range": {"type": "string"},
                    "prefs": {
                        "type": "array",
                        "items": {"type": "object"},
                    },
                },
                "required": ["name", "appointment_type"],
            },
        },
        {
            "type": "function",
            "name": "remove_faculty",
            "description": "Remove a faculty member from the scheduler configuration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                },
                "required": ["name"],
            },
        },
        {
            "type": "function",
            "name": "modify_faculty",
            "description": "Modify an existing faculty member.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "appointment_type": {"type": "string"},
                    "day": {"type": "string"},
                    "time_range": {"type": "string"},
                    "prefs": {
                        "type": "array",
                        "items": {"type": "object"},
                    },
                    "maximum_credits": {"type": "integer"},
                    "minimum_credits": {"type": "integer"},
                    "unique_course_limit": {"type": "integer"},
                },
                "required": ["name"],
            },
        },

        # --------------------------------------------------------
        # Room Tools
        # --------------------------------------------------------
        {
            "type": "function",
            "name": "add_room",
            "description": "Add a room to the scheduler configuration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "room": {"type": "string"},
                },
                "required": ["room"],
            },
        },
        {
            "type": "function",
            "name": "remove_room",
            "description": "Remove a room from the scheduler configuration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "room": {"type": "string"},
                },
                "required": ["room"],
            },
        },
        {
            "type": "function",
            "name": "modify_room",
            "description": "Rename an existing room.",
            "parameters": {
                "type": "object",
                "properties": {
                    "room": {"type": "string"},
                    "new_name": {"type": "string"},
                },
                "required": ["room", "new_name"],
            },
        },

        # --------------------------------------------------------
        # Lab Tools
        # --------------------------------------------------------
        {
            "type": "function",
            "name": "add_lab",
            "description": "Add a lab to the scheduler configuration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string"},
                },
                "required": ["lab"],
            },
        },
        {
            "type": "function",
            "name": "remove_lab",
            "description": "Remove a lab from the scheduler configuration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string"},
                },
                "required": ["lab"],
            },
        },
        {
            "type": "function",
            "name": "modify_lab",
            "description": "Rename an existing lab.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string"},
                    "new_name": {"type": "string"},
                },
                "required": ["lab", "new_name"],
            },
        },

        # --------------------------------------------------------
        # Course Tools
        # --------------------------------------------------------
        {
            "type": "function",
            "name": "add_course",
            "description": "Add a course to the scheduler configuration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_id": {"type": "string"},
                    "credits": {"type": "integer"},
                    "room": {"type": "string"},
                    "lab": {"type": "string"},
                    "faculty": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["course_id", "credits", "room"],
            },
        },
        {
            "type": "function",
            "name": "remove_course",
            "description": "Remove a course from the scheduler configuration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_id": {"type": "string"},
                },
                "required": ["course_id"],
            },
        },
        {
            "type": "function",
            "name": "modify_course",
            "description": "Modify an existing course. Supports renaming, credits, room, lab, faculty, and conflicts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_id": {"type": "string"},
                    "new_course_id": {"type": "string"},
                    "credits": {"type": "integer"},
                    "room": {"type": "string"},
                    "lab": {"type": "string"},
                    "faculty": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "conflicts": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["course_id"],
            },
        },

        # --------------------------------------------------------
        # Conflict Tools
        # --------------------------------------------------------
        {
            "type": "function",
            "name": "add_conflict",
            "description": "Add a conflict relationship between two courses.",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_id": {"type": "string"},
                    "conflict_course_id": {"type": "string"},
                    "symmetric": {"type": "boolean"},
                },
                "required": ["course_id", "conflict_course_id"],
            },
        },
        {
            "type": "function",
            "name": "remove_conflict",
            "description": "Remove a conflict relationship between two courses.",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_id": {"type": "string"},
                    "conflict_course_id": {"type": "string"},
                    "symmetric": {"type": "boolean"},
                },
                "required": ["course_id", "conflict_course_id"],
            },
        },
        {
            "type": "function",
            "name": "modify_conflict",
            "description": "Replace one course conflict with another.",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_id": {"type": "string"},
                    "old_conflict_course_id": {"type": "string"},
                    "new_conflict_course_id": {"type": "string"},
                    "symmetric": {"type": "boolean"},
                },
                "required": [
                    "course_id",
                    "old_conflict_course_id",
                    "new_conflict_course_id",
                ],
            },
        },
    ]


# ================================================================
# Validation
# ================================================================

def validate_tool_args(tool_name: str, args: dict) -> tuple[bool, str]:
    """
    Perform lightweight validation before dispatching a tool.

    Returns:
        tuple[bool, str]:
            (True, "") if valid
            (False, error_message) if invalid
    """
    if tool_name in {
        "add_faculty",
        "remove_faculty",
        "modify_faculty",
    } and not args.get("name"):
        return False, "Missing required field: name"

    if tool_name == "add_faculty" and not args.get("appointment_type"):
        return False, "Missing required field: appointment_type"

    if tool_name in {"add_room", "remove_room"} and not args.get("room"):
        return False, "Missing required field: room"

    if tool_name == "modify_room":
        if not args.get("room"):
            return False, "Missing required field: room"
        if not args.get("new_name"):
            return False, "Missing required field: new_name"

    if tool_name in {"add_lab", "remove_lab"} and not args.get("lab"):
        return False, "Missing required field: lab"

    if tool_name == "modify_lab":
        if not args.get("lab"):
            return False, "Missing required field: lab"
        if not args.get("new_name"):
            return False, "Missing required field: new_name"

    if tool_name == "add_course":
        if not args.get("course_id"):
            return False, "Missing required field: course_id"
        if args.get("credits") is None or not isinstance(args.get("credits"), int):
            return False, "credits must be an integer"
        if not args.get("room"):
            return False, "Missing required field: room"

    if tool_name == "remove_course" and not args.get("course_id"):
        return False, "Missing required field: course_id"

    if tool_name == "modify_course" and not args.get("course_id"):
        return False, "Missing required field: course_id"

    if tool_name in {"add_conflict", "remove_conflict"}:
        if not args.get("course_id"):
            return False, "Missing required field: course_id"
        if not args.get("conflict_course_id"):
            return False, "Missing required field: conflict_course_id"

    if tool_name == "modify_conflict":
        if not args.get("course_id"):
            return False, "Missing required field: course_id"
        if not args.get("old_conflict_course_id"):
            return False, "Missing required field: old_conflict_course_id"
        if not args.get("new_conflict_course_id"):
            return False, "Missing required field: new_conflict_course_id"

    return True, ""


# ================================================================
# TOOL DISPATCHER (HOW PYTHON EXECUTES THEM)
# ================================================================

def execute_tool(tool_name: str, args: dict) -> dict:
    """
    Execute a validated AI tool request.

    Args:
        tool_name (str): Approved tool name selected by the AI.
        args (dict): Parsed JSON arguments from the AI function call.

    Returns:
        dict: Standardized result payload for the route/UI layer.
    """
    is_valid, error = validate_tool_args(tool_name, args)
    if not is_valid:
        return {
            "success": False,
            "message": f"Validation failed: {error}",
            "changes_applied": False,
        }

    try:
        if tool_name == "add_faculty":
            return add_faculty_tool(args)

        if tool_name == "remove_faculty":
            return remove_faculty_tool(args)

        if tool_name == "modify_faculty":
            return modify_faculty_tool(args)

        if tool_name == "add_room":
            return add_room_tool(args)

        if tool_name == "remove_room":
            return remove_room_tool(args)

        if tool_name == "modify_room":
            return modify_room_tool(args)

        if tool_name == "add_lab":
            return add_lab_tool(args)

        if tool_name == "remove_lab":
            return remove_lab_tool(args)

        if tool_name == "modify_lab":
            return modify_lab_tool(args)

        if tool_name == "add_course":
            return add_course_tool(args)

        if tool_name == "remove_course":
            return remove_course_tool(args)

        if tool_name == "modify_course":
            return modify_course_tool(args)

        if tool_name == "add_conflict":
            return add_conflict_tool(args)

        if tool_name == "remove_conflict":
            return remove_conflict_tool(args)

        if tool_name == "modify_conflict":
            return modify_conflict_tool(args)

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


# ================================================================
# Tool Implementations
# ================================================================

def add_faculty_tool(args: dict) -> dict:
    add_faculty_service(
        name=args["name"],
        appointment_type=args["appointment_type"],
        day=args.get("day"),
        time_range=args.get("time_range"),
        prefs=args.get("prefs"),
    )
    return {
        "success": True,
        "message": f"Added faculty {args['name']}.",
        "changes_applied": True,
        "details": {"action": "add_faculty", **args},
    }


def remove_faculty_tool(args: dict) -> dict:
    remove_faculty_service(name=args["name"])
    return {
        "success": True,
        "message": f"Removed faculty {args['name']}.",
        "changes_applied": True,
        "details": {"action": "remove_faculty", **args},
    }


def modify_faculty_tool(args: dict) -> dict:
    modify_faculty_service(**args)
    return {
        "success": True,
        "message": f"Modified faculty {args['name']}.",
        "changes_applied": True,
        "details": {"action": "modify_faculty", **args},
    }


def add_room_tool(args: dict) -> dict:
    add_room_service(args["room"])
    return {
        "success": True,
        "message": f"Added room {args['room']}.",
        "changes_applied": True,
        "details": {"action": "add_room", **args},
    }


def remove_room_tool(args: dict) -> dict:
    remove_room_service(args["room"])
    return {
        "success": True,
        "message": f"Removed room {args['room']}.",
        "changes_applied": True,
        "details": {"action": "remove_room", **args},
    }


def modify_room_tool(args: dict) -> dict:
    modify_room_service(args["room"], args["new_name"])
    return {
        "success": True,
        "message": f"Renamed room {args['room']} to {args['new_name']}.",
        "changes_applied": True,
        "details": {"action": "modify_room", **args},
    }


def add_lab_tool(args: dict) -> dict:
    add_lab_service(lab=args["lab"])
    return {
        "success": True,
        "message": f"Added lab {args['lab']}.",
        "changes_applied": True,
        "details": {"action": "add_lab", **args},
    }


def remove_lab_tool(args: dict) -> dict:
    remove_lab_service(lab=args["lab"])
    return {
        "success": True,
        "message": f"Removed lab {args['lab']}.",
        "changes_applied": True,
        "details": {"action": "remove_lab", **args},
    }


def modify_lab_tool(args: dict) -> dict:
    modify_lab_service(lab=args["lab"], new_name=args["new_name"])
    return {
        "success": True,
        "message": f"Renamed lab {args['lab']} to {args['new_name']}.",
        "changes_applied": True,
        "details": {"action": "modify_lab", **args},
    }


def add_course_tool(args: dict) -> dict:
    add_course_service(
        course_id=args["course_id"],
        credits=args["credits"],
        room=args["room"],
        lab=args.get("lab"),
        faculty=args.get("faculty"),
    )
    return {
        "success": True,
        "message": f"Added course {args['course_id']}.",
        "changes_applied": True,
        "details": {"action": "add_course", **args},
    }


def remove_course_tool(args: dict) -> dict:
    remove_course_service(args["course_id"])
    return {
        "success": True,
        "message": f"Removed course {args['course_id']}.",
        "changes_applied": True,
        "details": {"action": "remove_course", **args},
    }


def modify_course_tool(args: dict) -> dict:
    """
    Modify an existing course.

    Important:
        The AI may include optional fields as empty strings, zero values,
        or empty lists even when the user did not intend to change them.
        This function cleans the payload before passing it to the backend
        so only meaningful changes are applied.
    """
    cleaned_args = {
        "course_id": args["course_id"]
    }

    # Only pass a rename if it is a non-empty string.
    new_course_id = args.get("new_course_id")
    if isinstance(new_course_id, str) and new_course_id.strip():
        cleaned_args["new_course_id"] = new_course_id.strip()

    # Only pass credits if they are a valid positive integer.
    credits = args.get("credits")
    if isinstance(credits, int) and credits > 0:
        cleaned_args["credits"] = credits

    # Only pass room if it is a non-empty string.
    room = args.get("room")
    if isinstance(room, str) and room.strip():
        cleaned_args["room"] = room.strip()

    # Only pass lab if it is a string.
    # Empty string is allowed here only if you intentionally want to clear lab,
    # but for now we avoid passing blank lab values from the AI automatically.
    lab = args.get("lab")
    if isinstance(lab, str) and lab.strip():
        cleaned_args["lab"] = lab.strip()

    # Only pass faculty if it is a non-empty list of non-empty strings.
    faculty = args.get("faculty")
    if isinstance(faculty, list):
        cleaned_faculty = [f.strip() for f in faculty if isinstance(f, str) and f.strip()]
        if cleaned_faculty:
            cleaned_args["faculty"] = cleaned_faculty

    # Only pass conflicts if it is a non-empty list of non-empty strings.
    conflicts = args.get("conflicts")
    if isinstance(conflicts, list):
        cleaned_conflicts = [c.strip() for c in conflicts if isinstance(c, str) and c.strip()]
        if cleaned_conflicts:
            cleaned_args["conflicts"] = cleaned_conflicts

    # Make sure at least one actual modification is being requested.
    if len(cleaned_args) == 1:
        return {
            "success": False,
            "message": (
                "No valid course modifications were provided. "
                "Please specify at least one field to change."
            ),
            "changes_applied": False,
        }

    modify_course_service(**cleaned_args)

    return {
        "success": True,
        "message": f"Modified course {args['course_id']}.",
        "changes_applied": True,
        "details": {"action": "modify_course", **cleaned_args},
    }


def add_conflict_tool(args: dict) -> dict:
    add_conflict_service(
        course_id=args["course_id"],
        conflict_course_id=args["conflict_course_id"],
        symmetric=args.get("symmetric", True),
    )
    return {
        "success": True,
        "message": (
            f"Added conflict between {args['course_id']} "
            f"and {args['conflict_course_id']}."
        ),
        "changes_applied": True,
        "details": {"action": "add_conflict", **args},
    }


def remove_conflict_tool(args: dict) -> dict:
    remove_conflict_service(
        course_id=args["course_id"],
        conflict_course_id=args["conflict_course_id"],
        symmetric=args.get("symmetric", True),
    )
    return {
        "success": True,
        "message": (
            f"Removed conflict between {args['course_id']} "
            f"and {args['conflict_course_id']}."
        ),
        "changes_applied": True,
        "details": {"action": "remove_conflict", **args},
    }


def modify_conflict_tool(args: dict) -> dict:
    modify_conflict_service(
        course_id=args["course_id"],
        old_conflict_course_id=args["old_conflict_course_id"],
        new_conflict_course_id=args["new_conflict_course_id"],
        symmetric=args.get("symmetric", True),
    )
    return {
        "success": True,
        "message": (
            f"Modified conflict for {args['course_id']} from "
            f"{args['old_conflict_course_id']} to {args['new_conflict_course_id']}."
        ),
        "changes_applied": True,
        "details": {"action": "modify_conflict", **args},
    }