# Author: Antonio Corona
# Date: 2026-04-04
"""
test_ai_tools.py

Tests for app/web/services/ai_tools.py.

Purpose:
- Verify supported tool schemas are defined correctly
- Verify tool dispatch maps to the correct backend action
- Verify unsupported tools are rejected safely
- Verify backend wrapper calls produce structured results

Notes:
- These tests validate deterministic backend dispatch behavior.
- OpenAI API behavior is tested separately in test_ai_service.py.
"""

from app.web.services.ai_tools import (
    get_tool_definitions,
    execute_tool,
    add_course_tool,
    rename_course_tool,
    modify_course_credits_tool,
    modify_course_room_tool,
    modify_course_lab_tool,
    remove_course_lab_tool,
    modify_course_faculty_tool,
    modify_course_conflicts_tool,
    remove_room_tool,
)


def test_get_tool_definitions_contains_expected_tools():
    """
    Ensures the AI tool registry exposes the expected current tools.
    """
    tools = get_tool_definitions()
    names = {tool["name"] for tool in tools}

    assert "add_course" in names
    assert "rename_course" in names
    assert "modify_course_credits" in names
    assert "modify_course_room" in names
    assert "modify_course_lab" in names
    assert "remove_course_lab" in names
    assert "modify_course_faculty" in names
    assert "modify_course_conflicts" in names
    assert "remove_room" in names


def test_add_course_tool_definition_requires_expected_fields():
    """
    Ensures add_course requires the fields needed by the backend.
    """
    tools = get_tool_definitions()
    add_course_def = next(tool for tool in tools if tool["name"] == "add_course")

    required = add_course_def["parameters"]["required"]

    assert "course_id" in required
    assert "credits" in required
    assert "room" in required


def test_rename_course_tool_definition_requires_expected_fields():
    """
    Ensures rename_course requires the correct fields.
    """
    tools = get_tool_definitions()
    rename_def = next(tool for tool in tools if tool["name"] == "rename_course")

    required = rename_def["parameters"]["required"]

    assert required == ["course_id", "new_course_id"]


def test_modify_course_credits_definition_requires_expected_fields():
    """
    Ensures modify_course_credits requires course_id and credits.
    """
    tools = get_tool_definitions()
    credits_def = next(
        tool for tool in tools if tool["name"] == "modify_course_credits"
    )

    required = credits_def["parameters"]["required"]

    assert required == ["course_id", "credits"]


def test_execute_tool_dispatches_add_course(monkeypatch):
    """
    Ensures execute_tool routes add_course requests correctly.
    """
    monkeypatch.setattr(
        "app.web.services.ai_tools.add_course_tool",
        lambda args: {
            "success": True,
            "message": f"Added {args['course_id']}",
            "changes_applied": True,
        },
    )

    result = execute_tool(
        "add_course",
        {"course_id": "CS102", "credits": 3, "room": "Roddy 140"},
    )

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["message"] == "Added CS102"


def test_execute_tool_dispatches_remove_course_lab(monkeypatch):
    """
    Ensures execute_tool routes remove_course_lab requests correctly.
    """
    monkeypatch.setattr(
        "app.web.services.ai_tools.remove_course_lab_tool",
        lambda args: {
            "success": True,
            "message": f"Removed lab from {args['course_id']}",
            "changes_applied": True,
        },
    )

    result = execute_tool(
        "remove_course_lab",
        {"course_id": "CS199"},
    )

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["message"] == "Removed lab from CS199"


def test_execute_tool_dispatches_rename_course(monkeypatch):
    """
    Ensures execute_tool routes rename_course requests correctly.
    """
    monkeypatch.setattr(
        "app.web.services.ai_tools.rename_course_tool",
        lambda args: {
            "success": True,
            "message": f"Renamed {args['course_id']} to {args['new_course_id']}",
            "changes_applied": True,
        },
    )

    result = execute_tool(
        "rename_course",
        {"course_id": "CS163", "new_course_id": "CS370"},
    )

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["message"] == "Renamed CS163 to CS370"


def test_execute_tool_dispatches_modify_course_credits(monkeypatch):
    """
    Ensures execute_tool routes modify_course_credits requests correctly.
    """
    monkeypatch.setattr(
        "app.web.services.ai_tools.modify_course_credits_tool",
        lambda args: {
            "success": True,
            "message": f"Updated {args['course_id']}",
            "changes_applied": True,
        },
    )

    result = execute_tool(
        "modify_course_credits",
        {"course_id": "CS102", "credits": 4},
    )

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["message"] == "Updated CS102"


def test_execute_tool_dispatches_modify_course_room(monkeypatch):
    """
    Ensures execute_tool routes modify_course_room requests correctly.
    """
    monkeypatch.setattr(
        "app.web.services.ai_tools.modify_course_room_tool",
        lambda args: {
            "success": True,
            "message": f"Room changed to {args['room']}",
            "changes_applied": True,
        },
    )

    result = execute_tool(
        "modify_course_room",
        {"course_id": "CS102", "room": "Roddy 147"},
    )

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["message"] == "Room changed to Roddy 147"


def test_execute_tool_dispatches_modify_course_lab(monkeypatch):
    """
    Ensures execute_tool routes modify_course_lab requests correctly.
    """
    monkeypatch.setattr(
        "app.web.services.ai_tools.modify_course_lab_tool",
        lambda args: {
            "success": True,
            "message": f"Lab changed to {args['lab']}",
            "changes_applied": True,
        },
    )

    result = execute_tool(
        "modify_course_lab",
        {"course_id": "CS102", "lab": "Linux"},
    )

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["message"] == "Lab changed to Linux"


def test_execute_tool_dispatches_modify_course_faculty(monkeypatch):
    """
    Ensures execute_tool routes modify_course_faculty requests correctly.
    """
    monkeypatch.setattr(
        "app.web.services.ai_tools.modify_course_faculty_tool",
        lambda args: {
            "success": True,
            "message": "Faculty updated",
            "changes_applied": True,
        },
    )

    result = execute_tool(
        "modify_course_faculty",
        {"course_id": "CS102", "faculty": ["Hardy", "Xie"]},
    )

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["message"] == "Faculty updated"


def test_execute_tool_dispatches_modify_course_conflicts(monkeypatch):
    """
    Ensures execute_tool routes modify_course_conflicts requests correctly.
    """
    monkeypatch.setattr(
        "app.web.services.ai_tools.modify_course_conflicts_tool",
        lambda args: {
            "success": True,
            "message": "Conflicts updated",
            "changes_applied": True,
        },
    )

    result = execute_tool(
        "modify_course_conflicts",
        {"course_id": "CS102", "conflicts": ["CMSC 330", "CMSC 362"]},
    )

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["message"] == "Conflicts updated"


def test_execute_tool_dispatches_remove_room(monkeypatch):
    """
    Ensures execute_tool routes remove_room requests correctly.
    """
    monkeypatch.setattr(
        "app.web.services.ai_tools.remove_room_tool",
        lambda args: {
            "success": True,
            "message": f"Removed {args['room']}",
            "changes_applied": True,
        },
    )

    result = execute_tool("remove_room", {"room": "Roddy 147"})

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["message"] == "Removed Roddy 147"


def test_execute_tool_rejects_unsupported_tool():
    """
    Ensures unsupported tools return a safe structured failure.
    """
    result = execute_tool("delete_everything", {})

    assert result["success"] is False
    assert result["changes_applied"] is False
    assert "Unsupported tool" in result["message"]


def test_execute_tool_catches_tool_exception(monkeypatch):
    """
    Ensures execute_tool safely catches tool-layer exceptions.
    """
    def boom(args):
        raise RuntimeError("tool exploded")

    monkeypatch.setattr("app.web.services.ai_tools.remove_room_tool", boom)

    result = execute_tool("remove_room", {"room": "Roddy 147"})

    assert result["success"] is False
    assert result["changes_applied"] is False
    assert "tool exploded" in result["message"]


def test_add_course_tool_calls_service_wrapper(monkeypatch):
    """
    Ensures add_course_tool delegates to add_course_service with the
    expected arguments.
    """
    captured = {}

    def fake_add_course_service(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        "app.web.services.ai_tools.add_course_service",
        fake_add_course_service,
    )

    result = add_course_tool(
        {"course_id": "CS102", "credits": 3, "room": "Roddy 140"}
    )

    assert captured == {
        "course_id": "CS102",
        "credits": 3,
        "room": "Roddy 140",
        "lab": None,
        "faculty": None,
    }
    assert result["success"] is True
    assert result["changes_applied"] is True
    assert "Added course CS102" in result["message"]


def test_remove_course_lab_tool_calls_service_wrapper(monkeypatch):
    """
    Ensures remove_course_lab_tool delegates to modify_course_service
    with an empty lab string so the backend clears the lab list.
    """
    captured = {}

    def fake_modify_course_service(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        "app.web.services.ai_tools.modify_course_service",
        fake_modify_course_service,
    )

    result = remove_course_lab_tool({"course_id": "CS199"})

    assert captured == {
        "course_id": "CS199",
        "lab": "",
    }
    assert result["success"] is True
    assert result["changes_applied"] is True
    assert "Removed lab from course CS199" in result["message"]
    

def test_rename_course_tool_calls_service_wrapper(monkeypatch):
    """
    Ensures rename_course_tool delegates to modify_course_service with the
    expected rename arguments.
    """
    captured = {}

    def fake_modify_course_service(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        "app.web.services.ai_tools.modify_course_service",
        fake_modify_course_service,
    )

    result = rename_course_tool(
        {"course_id": "CS163", "new_course_id": "CS370"}
    )

    assert captured == {
        "course_id": "CS163",
        "new_course_id": "CS370",
    }
    assert result["success"] is True
    assert result["changes_applied"] is True
    assert "Renamed course CS163 to CS370" in result["message"]


def test_modify_course_credits_tool_calls_service_wrapper(monkeypatch):
    """
    Ensures modify_course_credits_tool delegates to modify_course_service.
    """
    captured = {}

    def fake_modify_course_service(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        "app.web.services.ai_tools.modify_course_service",
        fake_modify_course_service,
    )

    result = modify_course_credits_tool(
        {"course_id": "CS102", "credits": 4}
    )

    assert captured == {
        "course_id": "CS102",
        "credits": 4,
    }
    assert result["success"] is True
    assert result["changes_applied"] is True
    assert "Changed credits for course CS102 to 4" in result["message"]


def test_modify_course_room_tool_calls_service_wrapper(monkeypatch):
    """
    Ensures modify_course_room_tool delegates to modify_course_service.
    """
    captured = {}

    def fake_modify_course_service(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        "app.web.services.ai_tools.modify_course_service",
        fake_modify_course_service,
    )

    result = modify_course_room_tool(
        {"course_id": "CS102", "room": "Roddy 147"}
    )

    assert captured == {
        "course_id": "CS102",
        "room": "Roddy 147",
    }
    assert result["success"] is True
    assert result["changes_applied"] is True
    assert "Changed room for course CS102 to Roddy 147" in result["message"]


def test_modify_course_lab_tool_calls_service_wrapper(monkeypatch):
    """
    Ensures modify_course_lab_tool delegates to modify_course_service.
    """
    captured = {}

    def fake_modify_course_service(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        "app.web.services.ai_tools.modify_course_service",
        fake_modify_course_service,
    )

    result = modify_course_lab_tool(
        {"course_id": "CS102", "lab": "Linux"}
    )

    assert captured == {
        "course_id": "CS102",
        "lab": "Linux",
    }
    assert result["success"] is True
    assert result["changes_applied"] is True
    assert "Changed lab for course CS102 to Linux" in result["message"]


def test_modify_course_faculty_tool_calls_service_wrapper(monkeypatch):
    """
    Ensures modify_course_faculty_tool delegates to modify_course_service
    with cleaned faculty names.
    """
    captured = {}

    def fake_modify_course_service(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        "app.web.services.ai_tools.modify_course_service",
        fake_modify_course_service,
    )

    result = modify_course_faculty_tool(
        {"course_id": "CS102", "faculty": ["Hardy", "  Xie  ", ""]}
    )

    assert captured == {
        "course_id": "CS102",
        "faculty": ["Hardy", "Xie"],
    }
    assert result["success"] is True
    assert result["changes_applied"] is True
    assert "Updated faculty for course CS102" in result["message"]


def test_modify_course_conflicts_tool_calls_service_wrapper(monkeypatch):
    """
    Ensures modify_course_conflicts_tool delegates to modify_course_service
    with cleaned conflict IDs.
    """
    captured = {}

    def fake_modify_course_service(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        "app.web.services.ai_tools.modify_course_service",
        fake_modify_course_service,
    )

    result = modify_course_conflicts_tool(
        {"course_id": "CS102", "conflicts": ["CMSC 330", " CMSC 362 ", ""]}
    )

    assert captured == {
        "course_id": "CS102",
        "conflicts": ["CMSC 330", "CMSC 362"],
    }
    assert result["success"] is True
    assert result["changes_applied"] is True
    assert "Updated conflicts for course CS102" in result["message"]


def test_remove_room_tool_calls_service_wrapper(monkeypatch):
    """
    Ensures remove_room_tool delegates to remove_room_service.
    """
    captured = {"room": None}

    def fake_remove_room_service(room):
        captured["room"] = room

    monkeypatch.setattr(
        "app.web.services.ai_tools.remove_room_service",
        fake_remove_room_service,
    )

    result = remove_room_tool({"room": "Roddy 147"})

    assert captured["room"] == "Roddy 147"
    assert result["success"] is True
    assert result["changes_applied"] is True
    assert "Removed room Roddy 147" in result["message"]