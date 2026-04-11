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
    add_conflict_tool,
    add_course_tool,
    add_faculty_tool,
    add_lab_tool,
    add_room_tool,
    execute_tool,
    get_tool_definitions,
    modify_conflict_tool,
    modify_course_conflicts_tool,
    modify_course_credits_tool,
    modify_course_faculty_tool,
    modify_course_lab_tool,
    modify_course_room_tool,
    modify_faculty_tool,
    modify_lab_tool,
    modify_room_tool,
    remove_conflict_tool,
    remove_course_lab_tool,
    remove_course_tool,
    remove_faculty_tool,
    remove_lab_tool,
    remove_room_tool,
    rename_course_tool,
    set_faculty_day_unavailable_tool,
    validate_tool_args,
)


def test_get_tool_definitions_contains_expected_tools():
    """
    Ensures the AI tool registry exposes the expected current tools.
    """
    tools = get_tool_definitions()
    names = {tool["name"] for tool in tools}

    assert "add_faculty" in names
    assert "remove_faculty" in names
    assert "modify_faculty" in names
    assert "set_faculty_day_unavailable" in names
    assert "add_room" in names
    assert "remove_room" in names
    assert "modify_room" in names
    assert "add_lab" in names
    assert "remove_lab" in names
    assert "modify_lab" in names
    assert "add_course" in names
    assert "remove_course" in names
    assert "rename_course" in names
    assert "modify_course_credits" in names
    assert "modify_course_room" in names
    assert "modify_course_lab" in names
    assert "remove_course_lab" in names
    assert "modify_course_faculty" in names
    assert "modify_course_conflicts" in names
    assert "add_conflict" in names
    assert "remove_conflict" in names
    assert "modify_conflict" in names


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

    result = add_course_tool({"course_id": "CS102", "credits": 3, "room": "Roddy 140"})

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

    result = rename_course_tool({"course_id": "CS163", "new_course_id": "CS370"})

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

    result = modify_course_credits_tool({"course_id": "CS102", "credits": 4})

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

    result = modify_course_room_tool({"course_id": "CS102", "room": "Roddy 147"})

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

    result = modify_course_lab_tool({"course_id": "CS102", "lab": "Linux"})

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


def test_room_tool_add(monkeypatch):
    """
    Ensures add_room_tool delegates to add_room_service.
    """
    captured = {"room": None}

    def fake_add_room_service(room):
        captured["room"] = room

    monkeypatch.setattr(
        "app.web.services.ai_tools.add_room_service",
        fake_add_room_service,
    )

    result = add_room_tool({"room": "Roddy 080"})

    assert captured["room"] == "Roddy 080"
    assert result["success"] is True
    assert result["changes_applied"] is True
    assert "Added room Roddy 080" in result["message"]


def test_room_tool_modify(monkeypatch):
    """
    Ensures modify_room_tool delegates to modify_room_service.
    """
    captured = {}

    def fake_modify_room_service(room, new_name):
        captured["room"] = room
        captured["new_name"] = new_name

    monkeypatch.setattr(
        "app.web.services.ai_tools.modify_room_service",
        fake_modify_room_service,
    )

    result = modify_room_tool({"room": "Roddy 147", "new_name": "Roddy 001"})

    assert captured["room"] == "Roddy 147"
    assert captured["new_name"] == "Roddy 001"
    assert result["success"] is True
    assert result["changes_applied"] is True
    assert "Renamed room Roddy 147 to Roddy 001" in result["message"]


def test_lab_tool_remove(monkeypatch):
    """
    Ensures remove_lab_tool delegates to remove_lab_service.
    """
    captured = {"lab": None}

    def fake_remove_lab_service(lab):
        captured["lab"] = lab

    monkeypatch.setattr(
        "app.web.services.ai_tools.remove_lab_service",
        fake_remove_lab_service,
    )

    result = remove_lab_tool({"lab": "Linux"})

    assert captured["lab"] == "Linux"
    assert result["success"] is True
    assert result["changes_applied"] is True
    assert "Removed lab Linux" in result["message"]


def test_lab_tool_add(monkeypatch):
    """
    Ensures add_lab_tool delegates to add_lab_service.
    """
    captured = {"lab": None}

    def fake_add_lab_service(lab):
        captured["lab"] = lab

    monkeypatch.setattr(
        "app.web.services.ai_tools.add_lab_service",
        fake_add_lab_service,
    )

    result = add_lab_tool({"lab": "Window"})

    assert captured["lab"] == "Window"
    assert result["success"] is True
    assert result["changes_applied"] is True
    assert "Added lab Window" in result["message"]


def test_lab_tool_modify(monkeypatch):
    """
    Ensures modify_lab_tool delegates to modify_lab_service.
    """
    captured = {}

    def fake_modify_lab_service(lab, new_name):
        captured["lab"] = lab
        captured["new_name"] = new_name

    monkeypatch.setattr(
        "app.web.services.ai_tools.modify_lab_service",
        fake_modify_lab_service,
    )

    result = modify_lab_tool({"lab": "Linux", "new_name": "Glerp"})

    assert captured["lab"] == "Linux"
    assert captured["new_name"] == "Glerp"
    assert result["success"] is True
    assert result["changes_applied"] is True
    assert "Renamed lab Linux to Glerp" in result["message"]


def test_course_tool_remove(monkeypatch):
    """
    Ensures remove_course_tool delegates to remove_course_service.
    """
    captured = {"course_id": None}

    def fake_remove_course_service(course_id):
        captured["course_id"] = course_id

    monkeypatch.setattr(
        "app.web.services.ai_tools.remove_course_service",
        fake_remove_course_service,
    )

    result = remove_course_tool({"course_id": "CS102"})

    assert captured["course_id"] == "CS102"
    assert result["success"] is True
    assert result["changes_applied"] is True
    assert "Removed course CS102" in result["message"]


def test_conflict_tool_add(monkeypatch):
    """
    Ensures add_conflict_tool delegates to add_conflict_service.
    """
    captured = {}

    def fake_add_conflict_service(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        "app.web.services.ai_tools.add_conflict_service",
        fake_add_conflict_service,
    )

    result = add_conflict_tool({"course_id": "CS102", "conflict_course_id": "CS771"})

    assert captured["course_id"] == "CS102"
    assert captured["conflict_course_id"] == "CS771"
    assert captured["symmetric"] is True
    assert result["success"] is True
    assert result["changes_applied"] is True
    assert "Added conflict between CS102 and CS771" in result["message"]


def test_conflict_too_remove(monkeypatch):
    """
    Ensures remove_conflict_tool delegates to remove_conflict_service.
    """
    captured = {}

    def fake_remove_conflict_service(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        "app.web.services.ai_tools.remove_conflict_service",
        fake_remove_conflict_service,
    )

    result = remove_conflict_tool({"course_id": "CS102", "conflict_course_id": "CS888"})

    assert captured["course_id"] == "CS102"
    assert captured["conflict_course_id"] == "CS888"
    assert captured["symmetric"] is True
    assert result["success"] is True
    assert result["changes_applied"] is True
    assert "Removed conflict between CS102 and CS888" in result["message"]


def test_modify_conflict_tool(monkeypatch):
    """
    Ensures modify_conflict_tool delegates to modify_conflict_service.
    """
    captured = {}

    def fake_modify_conflict_service(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        "app.web.services.ai_tools.modify_conflict_service",
        fake_modify_conflict_service,
    )

    result = modify_conflict_tool(
        {
            "course_id": "CS102",
            "old_conflict_course_id": "CS103",
            "new_conflict_course_id": "CS911",
        }
    )

    assert captured["course_id"] == "CS102"
    assert captured["old_conflict_course_id"] == "CS103"
    assert captured["new_conflict_course_id"] == "CS911"
    assert captured["symmetric"] is True
    assert result["success"] is True
    assert result["changes_applied"] is True
    assert "Modified conflict for CS102" in result["message"]


def test_faculty_tool_add(monkeypatch):
    """
    Ensures add_faculty_tool delegates to add_faculty_service.
    """
    captured = {}

    def fake_add_faculty_service(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        "app.web.services.ai_tools.add_faculty_service",
        fake_add_faculty_service,
    )

    result = add_faculty_tool({"name": "MR BIGG", "appointment_type": "Full-time"})

    assert captured["name"] == "MR BIGG"
    assert captured["appointment_type"] == "Full-time"
    assert result["success"] is True
    assert result["changes_applied"] is True
    assert "Added faculty MR BIGG" in result["message"]


def test_faculty_tool_remove(monkeypatch):
    """
    Ensures remove_faculty_tool delegates to remove_faculty_service.
    """
    captured = {"name": None}

    def fake_remove_faculty_service(name):
        captured["name"] = name

    monkeypatch.setattr(
        "app.web.services.ai_tools.remove_faculty_service",
        fake_remove_faculty_service,
    )

    result = remove_faculty_tool({"name": "HEAVY"})

    assert captured["name"] == "HEAVY"
    assert result["success"] is True
    assert result["changes_applied"] is True
    assert "Removed faculty HEAVY" in result["message"]


def test_faculty_tool_modify(monkeypatch):
    """
    Ensures modify_faculty_tool delegates to modify_faculty_service.
    """
    captured = {}

    def fake_modify_faculty_service(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        "app.web.services.ai_tools.modify_faculty_service",
        fake_modify_faculty_service,
    )

    result = modify_faculty_tool({"name": "France", "appointment_type": "Full-time"})

    assert captured["name"] == "France"
    assert captured["appointment_type"] == "Full-time"
    assert result["success"] is True
    assert result["changes_applied"] is True
    assert "Modified faculty France" in result["message"]


def test_validate_tool_args_rejects_missing_name_for_faculty_tools():
    """
    Ensures faculty tools that require a name fail validation when the
    name field is missing.
    """
    is_valid, error = validate_tool_args(
        "add_faculty", {"appointment_type": "Full-time"}
        )
    assert is_valid is False
    assert error == "Missing required field: name"

    is_valid, error = validate_tool_args("remove_faculty", {})
    assert is_valid is False
    assert error == "Missing required field: name"

    is_valid, error = validate_tool_args("modify_faculty", {})
    assert is_valid is False
    assert error == "Missing required field: name"


def test_validate_tool_args_rejects_missing_appointment_type_for_add_faculty():
    """
    Ensures add_faculty fails validation when appointment_type is missing.
    """
    is_valid, error = validate_tool_args("add_faculty", {"name": "Smith"})

    assert is_valid is False
    assert error == "Missing required field: appointment_type"


def test_validate_tool_args_rejects_missing_fields_for_set_faculty_day_unavailable():
    """
    Ensures set_faculty_day_unavailable validates both required fields.
    """
    is_valid, error = validate_tool_args("set_faculty_day_unavailable", {"day": "MON"})
    assert is_valid is False
    assert error == "Missing required field: name"

    is_valid, error = validate_tool_args(
        "set_faculty_day_unavailable",
        {"name": "Smith"},
    )
    assert is_valid is False
    assert error == "Missing required field: day"


def test_validate_tool_args_rejects_missing_room_fields():
    """
    Ensures room tools fail validation when required room fields are missing.
    """
    is_valid, error = validate_tool_args("add_room", {})
    assert is_valid is False
    assert error == "Missing required field: room"

    is_valid, error = validate_tool_args("remove_room", {})
    assert is_valid is False
    assert error == "Missing required field: room"

    is_valid, error = validate_tool_args("modify_room", {"room": "Roddy 140"})
    assert is_valid is False
    assert error == "Missing required field: new_name"


def test_validate_tool_args_rejects_missing_lab_fields():
    """
    Ensures lab tools fail validation when required lab fields are missing.
    """
    is_valid, error = validate_tool_args("add_lab", {})
    assert is_valid is False
    assert error == "Missing required field: lab"

    is_valid, error = validate_tool_args("remove_lab", {})
    assert is_valid is False
    assert error == "Missing required field: lab"

    is_valid, error = validate_tool_args("modify_lab", {"lab": "Linux"})
    assert is_valid is False
    assert error == "Missing required field: new_name"


def test_validate_tool_args_rejects_add_course_missing_course_id():
    """
    Ensures add_course requires a course_id.
    """
    is_valid, error = validate_tool_args(
        "add_course",
        {"credits": 3, "room": "Roddy 140"},
    )

    assert is_valid is False
    assert error == "Missing required field: course_id"


def test_validate_tool_args_rejects_add_course_non_integer_credits():
    """
    Ensures add_course rejects credits when they are not an integer.
    """
    is_valid, error = validate_tool_args(
        "add_course",
        {"course_id": "CS101", "credits": "3", "room": "Roddy 140"},
    )

    assert is_valid is False
    assert error == "credits must be an integer"


def test_validate_tool_args_rejects_add_course_missing_room():
    """
    Ensures add_course requires a room value.
    """
    is_valid, error = validate_tool_args(
        "add_course",
        {"course_id": "CS101", "credits": 3},
    )

    assert is_valid is False
    assert error == "Missing required field: room"


def test_validate_tool_args_rejects_remove_course_missing_course_id():
    """
    Ensures remove_course requires a course_id.
    """
    is_valid, error = validate_tool_args("remove_course", {})

    assert is_valid is False
    assert error == "Missing required field: course_id"


def test_validate_tool_args_rejects_modify_course_credits_missing_course_id():
    """
    Ensures modify_course_credits requires course_id.
    """
    is_valid, error = validate_tool_args("modify_course_credits", {"credits": 4})

    assert is_valid is False
    assert error == "Missing required field: course_id"


def test_validate_tool_args_rejects_modify_course_credits_non_integer():
    """
    Ensures modify_course_credits rejects non-integer credits.
    """
    is_valid, error = validate_tool_args(
        "modify_course_credits",
        {"course_id": "CS101", "credits": "4"},
    )

    assert is_valid is False
    assert error == "credits must be an integer"


def test_validate_tool_args_rejects_modify_course_credits_non_positive():
    """
    Ensures modify_course_credits rejects zero or negative credits.
    """
    is_valid, error = validate_tool_args(
        "modify_course_credits",
        {"course_id": "CS101", "credits": 0},
    )

    assert is_valid is False
    assert error == "credits must be a positive integer"


def test_validate_tool_args_rejects_modify_course_room_missing_fields():
    """
    Ensures modify_course_room validates both course_id and room.
    """
    is_valid, error = validate_tool_args("modify_course_room", {"room": "Roddy 140"})
    assert is_valid is False
    assert error == "Missing required field: course_id"

    is_valid, error = validate_tool_args("modify_course_room", {"course_id": "CS101"})
    assert is_valid is False
    assert error == "Missing required field: room"


def test_validate_tool_args_rejects_modify_course_lab_missing_fields():
    """
    Ensures modify_course_lab validates both course_id and lab.
    """
    is_valid, error = validate_tool_args("modify_course_lab", {"lab": "Linux"})
    assert is_valid is False
    assert error == "Missing required field: course_id"

    is_valid, error = validate_tool_args("modify_course_lab", {"course_id": "CS101"})
    assert is_valid is False
    assert error == "Missing required field: lab"


def test_validate_tool_args_rejects_remove_course_lab_missing_course_id():
    """
    Ensures remove_course_lab requires course_id.
    """
    is_valid, error = validate_tool_args("remove_course_lab", {})

    assert is_valid is False
    assert error == "Missing required field: course_id"


def test_validate_tool_args_rejects_modify_course_faculty_invalid_faculty_type():
    """
    Ensures modify_course_faculty requires faculty to be a list.
    """
    is_valid, error = validate_tool_args(
        "modify_course_faculty",
        {"course_id": "CS101", "faculty": "Smith"},
    )

    assert is_valid is False
    assert error == "faculty must be a list"


def test_validate_tool_args_rejects_modify_course_conflicts_invalid_conflicts_type():
    """
    Ensures modify_course_conflicts requires conflicts to be a list.
    """
    is_valid, error = validate_tool_args(
        "modify_course_conflicts",
        {"course_id": "CS101", "conflicts": "CS102"},
    )

    assert is_valid is False
    assert error == "conflicts must be a list"


def test_validate_tool_args_rejects_conflict_tools_missing_fields():
    """
    Ensures add/remove conflict tools validate both required IDs.
    """
    is_valid, error = validate_tool_args(
        "add_conflict", {"conflict_course_id": "CS102"}
        )
    assert is_valid is False
    assert error == "Missing required field: course_id"

    is_valid, error = validate_tool_args("remove_conflict", {"course_id": "CS101"})
    assert is_valid is False
    assert error == "Missing required field: conflict_course_id"


def test_validate_tool_args_rejects_modify_conflict_missing_fields():
    """
    Ensures modify_conflict validates all required IDs.
    """
    is_valid, error = validate_tool_args(
        "modify_conflict", {"old_conflict_course_id": "CS102"}
        )
    assert is_valid is False
    assert error == "Missing required field: course_id"

    is_valid, error = validate_tool_args(
        "modify_conflict",
        {"course_id": "CS101", "new_conflict_course_id": "CS103"},
    )
    assert is_valid is False
    assert error == "Missing required field: old_conflict_course_id"

    is_valid, error = validate_tool_args(
        "modify_conflict",
        {"course_id": "CS101", "old_conflict_course_id": "CS102"},
    )
    assert is_valid is False
    assert error == "Missing required field: new_conflict_course_id"


def test_execute_tool_rejects_failed_validation_before_dispatch(monkeypatch):
    """
    Ensures execute_tool returns the validation failure payload without
    attempting dispatch when validation fails.
    """
    monkeypatch.setattr(
        "app.web.services.ai_tools.validate_tool_args",
        lambda tool_name, args: (False, "Missing required field: name"),
    )

    result = execute_tool("add_faculty", {})

    assert result == {
        "success": False,
        "message": "Validation failed: Missing required field: name",
        "changes_applied": False,
    }


def test_execute_tool_dispatches_add_faculty(monkeypatch):
    """
    Ensures execute_tool routes add_faculty requests correctly.
    """
    monkeypatch.setattr(
        "app.web.services.ai_tools.add_faculty_tool",
        lambda args: {
            "success": True,
            "message": f"Added faculty {args['name']}",
            "changes_applied": True,
        },
    )

    result = execute_tool(
        "add_faculty",
        {"name": "Smith", "appointment_type": "Full-time"},
    )

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["message"] == "Added faculty Smith"


def test_execute_tool_dispatches_remove_faculty(monkeypatch):
    """
    Ensures execute_tool routes remove_faculty requests correctly.
    """
    monkeypatch.setattr(
        "app.web.services.ai_tools.remove_faculty_tool",
        lambda args: {
            "success": True,
            "message": f"Removed faculty {args['name']}",
            "changes_applied": True,
        },
    )

    result = execute_tool("remove_faculty", {"name": "Smith"})

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["message"] == "Removed faculty Smith"


def test_execute_tool_dispatches_modify_faculty(monkeypatch):
    """
    Ensures execute_tool routes modify_faculty requests correctly.
    """
    monkeypatch.setattr(
        "app.web.services.ai_tools.modify_faculty_tool",
        lambda args: {
            "success": True,
            "message": f"Modified faculty {args['name']}",
            "changes_applied": True,
        },
    )

    result = execute_tool(
        "modify_faculty",
        {"name": "Smith", "appointment_type": "Adjunct"},
    )

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["message"] == "Modified faculty Smith"


def test_execute_tool_dispatches_set_faculty_day_unavailable(monkeypatch):
    """
    Ensures execute_tool routes set_faculty_day_unavailable requests correctly.
    """
    monkeypatch.setattr(
        "app.web.services.ai_tools.set_faculty_day_unavailable_tool",
        lambda args: {
            "success": True,
            "message": f"{args['name']} unavailable on {args['day']}",
            "changes_applied": True,
        },
    )

    result = execute_tool(
        "set_faculty_day_unavailable",
        {"name": "Smith", "day": "MON"},
    )

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["message"] == "Smith unavailable on MON"


def test_execute_tool_dispatches_add_room(monkeypatch):
    """
    Ensures execute_tool routes add_room requests correctly.
    """
    monkeypatch.setattr(
        "app.web.services.ai_tools.add_room_tool",
        lambda args: {
            "success": True,
            "message": f"Added room {args['room']}",
            "changes_applied": True,
        },
    )

    result = execute_tool("add_room", {"room": "Roddy 080"})

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["message"] == "Added room Roddy 080"


def test_execute_tool_dispatches_modify_room(monkeypatch):
    """
    Ensures execute_tool routes modify_room requests correctly.
    """
    monkeypatch.setattr(
        "app.web.services.ai_tools.modify_room_tool",
        lambda args: {
            "success": True,
            "message": f"Renamed room {args['room']}",
            "changes_applied": True,
        },
    )

    result = execute_tool(
        "modify_room",
        {"room": "Roddy 140", "new_name": "Roddy 141"},
    )

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["message"] == "Renamed room Roddy 140"


def test_execute_tool_dispatches_add_lab(monkeypatch):
    """
    Ensures execute_tool routes add_lab requests correctly.
    """
    monkeypatch.setattr(
        "app.web.services.ai_tools.add_lab_tool",
        lambda args: {
            "success": True,
            "message": f"Added lab {args['lab']}",
            "changes_applied": True,
        },
    )

    result = execute_tool("add_lab", {"lab": "Linux"})

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["message"] == "Added lab Linux"


def test_execute_tool_dispatches_remove_lab(monkeypatch):
    """
    Ensures execute_tool routes remove_lab requests correctly.
    """
    monkeypatch.setattr(
        "app.web.services.ai_tools.remove_lab_tool",
        lambda args: {
            "success": True,
            "message": f"Removed lab {args['lab']}",
            "changes_applied": True,
        },
    )

    result = execute_tool("remove_lab", {"lab": "Linux"})

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["message"] == "Removed lab Linux"


def test_execute_tool_dispatches_modify_lab(monkeypatch):
    """
    Ensures execute_tool routes modify_lab requests correctly.
    """
    monkeypatch.setattr(
        "app.web.services.ai_tools.modify_lab_tool",
        lambda args: {
            "success": True,
            "message": f"Renamed lab {args['lab']}",
            "changes_applied": True,
        },
    )

    result = execute_tool(
        "modify_lab",
        {"lab": "Linux", "new_name": "Mac"},
    )

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["message"] == "Renamed lab Linux"


def test_execute_tool_dispatches_remove_course(monkeypatch):
    """
    Ensures execute_tool routes remove_course requests correctly.
    """
    monkeypatch.setattr(
        "app.web.services.ai_tools.remove_course_tool",
        lambda args: {
            "success": True,
            "message": f"Removed course {args['course_id']}",
            "changes_applied": True,
        },
    )

    result = execute_tool("remove_course", {"course_id": "CS101"})

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["message"] == "Removed course CS101"


def test_execute_tool_dispatches_add_conflict(monkeypatch):
    """
    Ensures execute_tool routes add_conflict requests correctly.
    """
    monkeypatch.setattr(
        "app.web.services.ai_tools.add_conflict_tool",
        lambda args: {
            "success": True,
            "message": f"Added conflict for {args['course_id']}",
            "changes_applied": True,
        },
    )

    result = execute_tool(
        "add_conflict",
        {"course_id": "CS101", "conflict_course_id": "CS102"},
    )

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["message"] == "Added conflict for CS101"


def test_execute_tool_dispatches_remove_conflict(monkeypatch):
    """
    Ensures execute_tool routes remove_conflict requests correctly.
    """
    monkeypatch.setattr(
        "app.web.services.ai_tools.remove_conflict_tool",
        lambda args: {
            "success": True,
            "message": f"Removed conflict for {args['course_id']}",
            "changes_applied": True,
        },
    )

    result = execute_tool(
        "remove_conflict",
        {"course_id": "CS101", "conflict_course_id": "CS102"},
    )

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["message"] == "Removed conflict for CS101"


def test_execute_tool_dispatches_modify_conflict(monkeypatch):
    """
    Ensures execute_tool routes modify_conflict requests correctly.
    """
    monkeypatch.setattr(
        "app.web.services.ai_tools.modify_conflict_tool",
        lambda args: {
            "success": True,
            "message": f"Modified conflict for {args['course_id']}",
            "changes_applied": True,
        },
    )

    result = execute_tool(
        "modify_conflict",
        {
            "course_id": "CS101",
            "old_conflict_course_id": "CS102",
            "new_conflict_course_id": "CS103",
        },
    )

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["message"] == "Modified conflict for CS101"


def test_set_faculty_day_unavailable_tool_calls_service_wrapper(monkeypatch):
    """
    Ensures set_faculty_day_unavailable_tool delegates to the service wrapper.
    """
    captured = {}

    def fake_set_faculty_day_unavailable_service(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        "app.web.services.ai_tools.set_faculty_day_unavailable_service",
        fake_set_faculty_day_unavailable_service,
    )

    result = set_faculty_day_unavailable_tool({"name": "Smith", "day": "FRI"})

    assert captured == {"name": "Smith", "day": "FRI"}
    assert result["success"] is True
    assert result["changes_applied"] is True
    assert "Set faculty Smith as unavailable on FRI" in result["message"]