# Author: Antonio Corona
# Date: 2026-04-26
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

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

from app.web.services.config_service import (
    add_conflict_service,
    add_course_service,
    add_faculty_service,
    add_lab_service,
    add_room_service,
    modify_conflict_service,
    modify_course_service,
    modify_faculty_service,
    modify_lab_service,
    modify_room_service,
    remove_conflict_service,
    remove_course_service,
    remove_faculty_service,
    remove_lab_service,
    remove_room_service,
    set_faculty_day_unavailable_service,
)


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

    if tool_name == "set_faculty_day_unavailable":
        if not args.get("name"):
            return False, "Missing required field: name"
        if not args.get("day"):
            return False, "Missing required field: day"

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

    if tool_name == "rename_course":
        if not args.get("course_id"):
            return False, "Missing required field: course_id"
        if not args.get("new_course_id"):
            return False, "Missing required field: new_course_id"

    if tool_name == "modify_course_credits":
        if not args.get("course_id"):
            return False, "Missing required field: course_id"
        if args.get("credits") is None or not isinstance(args.get("credits"), int):
            return False, "credits must be an integer"
        if args["credits"] <= 0:
            return False, "credits must be a positive integer"

    if tool_name == "modify_course_room":
        if not args.get("course_id"):
            return False, "Missing required field: course_id"
        if not args.get("room"):
            return False, "Missing required field: room"

    if tool_name == "modify_course_lab":
        if not args.get("course_id"):
            return False, "Missing required field: course_id"
        if not args.get("lab"):
            return False, "Missing required field: lab"

    if tool_name == "remove_course_lab":
        if not args.get("course_id"):
            return False, "Missing required field: course_id"

    if tool_name == "modify_course_faculty":
        if not args.get("course_id"):
            return False, "Missing required field: course_id"
        if "faculty" not in args or not isinstance(args.get("faculty"), list):
            return False, "faculty must be a list"

    if tool_name == "modify_course_conflicts":
        if not args.get("course_id"):
            return False, "Missing required field: course_id"
        if "conflicts" not in args or not isinstance(args.get("conflicts"), list):
            return False, "conflicts must be a list"

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
    Execute a validated AI tool request using the Command pattern.

    Instead of directly dispatching through a long if/elif chain, this creates
    a command object and executes it through the shared ToolCommand interface.
    """
    is_valid, error = validate_tool_args(tool_name, args)

    if not is_valid:
        return {
            "success": False,
            "message": f"Validation failed: {error}",
            "changes_applied": False,
        }

    try:
        command = ToolCommandFactory.create(tool_name, args)
        return command.execute()

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


def set_faculty_day_unavailable_tool(args: dict) -> dict:
    """
    Mark a faculty member unavailable on a specific day by clearing
    the time ranges for that day.
    """
    set_faculty_day_unavailable_service(
        name=args["name"],
        day=args["day"],
    )

    return {
        "success": True,
        "message": f"Set faculty {args['name']} as unavailable on {args['day']}.",
        "changes_applied": True,
        "details": {
            "action": "set_faculty_day_unavailable",
            "name": args["name"],
            "day": args["day"],
        },
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


def rename_course_tool(args: dict) -> dict:
    modify_course_service(
        course_id=args["course_id"],
        new_course_id=args["new_course_id"],
    )
    return {
        "success": True,
        "message": f"Renamed course {args['course_id']} to {args['new_course_id']}.",
        "changes_applied": True,
        "details": {"action": "rename_course", **args},
    }


def modify_course_credits_tool(args: dict) -> dict:
    modify_course_service(
        course_id=args["course_id"],
        credits=args["credits"],
    )
    return {
        "success": True,
        "message": (
            f"Changed credits for course {args['course_id']} to {args['credits']}."
        ),
        "changes_applied": True,
        "details": {"action": "modify_course_credits", **args},
    }


def modify_course_room_tool(args: dict) -> dict:
    modify_course_service(
        course_id=args["course_id"],
        room=args["room"],
    )
    return {
        "success": True,
        "message": f"Changed room for course {args['course_id']} to {args['room']}.",
        "changes_applied": True,
        "details": {"action": "modify_course_room", **args},
    }


def modify_course_lab_tool(args: dict) -> dict:
    modify_course_service(
        course_id=args["course_id"],
        lab=args["lab"],
    )
    return {
        "success": True,
        "message": f"Changed lab for course {args['course_id']} to {args['lab']}.",
        "changes_applied": True,
        "details": {"action": "modify_course_lab", **args},
    }


def remove_course_lab_tool(args: dict) -> dict:
    """
    Remove the lab assigned to an existing course.

    The backend modify_course() clears the lab only when it receives
    an empty string, not None.
    """
    modify_course_service(
        course_id=args["course_id"],
        lab="",
    )
    return {
        "success": True,
        "message": f"Removed lab from course {args['course_id']}.",
        "changes_applied": True,
        "details": {"action": "remove_course_lab", **args},
    }


def modify_course_faculty_tool(args: dict) -> dict:
    cleaned_faculty = [
        f.strip() for f in args["faculty"] if isinstance(f, str) and f.strip()
    ]

    modify_course_service(
        course_id=args["course_id"],
        faculty=cleaned_faculty,
    )
    return {
        "success": True,
        "message": f"Updated faculty for course {args['course_id']}.",
        "changes_applied": True,
        "details": {
            "action": "modify_course_faculty",
            "course_id": args["course_id"],
            "faculty": cleaned_faculty,
        },
    }


def modify_course_conflicts_tool(args: dict) -> dict:
    cleaned_conflicts = [
        c.strip() for c in args["conflicts"] if isinstance(c, str) and c.strip()
    ]

    modify_course_service(
        course_id=args["course_id"],
        conflicts=cleaned_conflicts,
    )
    return {
        "success": True,
        "message": f"Updated conflicts for course {args['course_id']}.",
        "changes_applied": True,
        "details": {
            "action": "modify_course_conflicts",
            "course_id": args["course_id"],
            "conflicts": cleaned_conflicts,
        },
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


# ================================================================
# Command Design Pattern
# ================================================================


class ToolCommand(ABC):
    """
    Abstract command interface for AI tool execution.

    Command Pattern Role:
        - Declares a shared execute() interface.
        - Encapsulates one AI tool request as an object.
        - Allows callers to execute commands without knowing which service
          function performs the work.
    """

    @abstractmethod
    def execute(self) -> dict:
        """
        Execute the command and return a standardized result payload.
        """
        raise NotImplementedError


@dataclass
class ConfigToolCommand(ToolCommand):
    """
    Concrete command for scheduler configuration tool requests.

    Each instance stores:
        - command name
        - parsed argument dictionary
        - callable implementation that performs the action

    This turns the previous function-dispatch approach into real command
    objects with a common execute() interface.
    """

    name: str
    args: dict
    handler: Callable[[dict], dict]

    def execute(self) -> dict:
        """
        Execute the assigned handler using this command's arguments.
        """
        return self.handler(self.args)


class UnsupportedToolCommand(ToolCommand):
    """
    Null/safe command used when the AI requests an unsupported tool.

    This prevents callers from needing special-case None checks and returns a
    consistent response shape.
    """

    def __init__(self, tool_name: str):
        self.tool_name = tool_name

    def execute(self) -> dict:
        return {
            "success": False,
            "message": f"Unsupported tool: {self.tool_name}",
            "changes_applied": False,
        }


class ToolCommandFactory:
    """
    Factory for creating concrete command objects from AI tool requests.

    The factory keeps command selection centralized while execute_tool()
    depends only on the ToolCommand interface.
    """

    _handlers: dict[str, Callable[[dict], dict]] = {
        "add_faculty": add_faculty_tool,
        "remove_faculty": remove_faculty_tool,
        "modify_faculty": modify_faculty_tool,
        "set_faculty_day_unavailable": set_faculty_day_unavailable_tool,
        "add_room": add_room_tool,
        "remove_room": remove_room_tool,
        "modify_room": modify_room_tool,
        "add_lab": add_lab_tool,
        "remove_lab": remove_lab_tool,
        "modify_lab": modify_lab_tool,
        "add_course": add_course_tool,
        "remove_course": remove_course_tool,
        "rename_course": rename_course_tool,
        "modify_course_credits": modify_course_credits_tool,
        "modify_course_room": modify_course_room_tool,
        "modify_course_lab": modify_course_lab_tool,
        "remove_course_lab": remove_course_lab_tool,
        "modify_course_faculty": modify_course_faculty_tool,
        "modify_course_conflicts": modify_course_conflicts_tool,
        "add_conflict": add_conflict_tool,
        "remove_conflict": remove_conflict_tool,
        "modify_conflict": modify_conflict_tool,
    }

    @classmethod
    def create(cls, tool_name: str, args: dict) -> ToolCommand:
        """
        Create a command object for a supported tool name.
        """
        handler = cls._handlers.get(tool_name)

        if handler is None:
            return UnsupportedToolCommand(tool_name)

        return ConfigToolCommand(
            name=tool_name,
            args=args,
            handler=handler,
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
        {
            "type": "function",
            "name": "set_faculty_day_unavailable",
            "description": "Mark a faculty member as unavailable on a specific day "
            "by setting that day's times to an empty list.",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "day": {"type": "string"}},
                "required": ["name", "day"],
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
            "name": "rename_course",
            "description": "Rename an existing course by changing its course ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_id": {"type": "string"},
                    "new_course_id": {"type": "string"},
                },
                "required": ["course_id", "new_course_id"],
            },
        },
        {
            "type": "function",
            "name": "modify_course_credits",
            "description": "Change the credits of an existing course.",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_id": {"type": "string"},
                    "credits": {"type": "integer"},
                },
                "required": ["course_id", "credits"],
            },
        },
        {
            "type": "function",
            "name": "modify_course_room",
            "description": "Change the room assigned to an existing course.",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_id": {"type": "string"},
                    "room": {"type": "string"},
                },
                "required": ["course_id", "room"],
            },
        },
        {
            "type": "function",
            "name": "modify_course_lab",
            "description": "Change the lab assigned to an existing course.",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_id": {"type": "string"},
                    "lab": {"type": "string"},
                },
                "required": ["course_id", "lab"],
            },
        },
        {
            "type": "function",
            "name": "remove_course_lab",
            "description": "Remove the lab assigned to an existing course.",
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
            "name": "modify_course_faculty",
            "description": "Change the faculty list assigned to an existing course.",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_id": {"type": "string"},
                    "faculty": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["course_id", "faculty"],
            },
        },
        {
            "type": "function",
            "name": "modify_course_conflicts",
            "description": "Change the conflicts list assigned to an existing course.",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_id": {"type": "string"},
                    "conflicts": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["course_id", "conflicts"],
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