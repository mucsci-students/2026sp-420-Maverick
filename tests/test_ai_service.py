# Author: Antonio Corona
# Date: 2026-04-04
"""
test_ai_service.py

Tests for app/web/services/ai_service.py.

Purpose:
- Validate prompt and user-input construction
- Confirm response-text extraction behavior
- Ensure AI command processing returns structured results
- Verify function-tool execution behavior for the current AI tool system

These tests are designed to:
- Improve coverage for AI orchestration logic
- Confirm stateless request construction
- Catch regressions in response formatting behavior
- Verify tool calls are dispatched correctly
"""

from types import SimpleNamespace

from app.web.services.ai_service import (
    BASE_PROMPT,
    build_base_prompt,
    build_user_input,
    extract_text_from_response,
    process_ai_command,
)


def _mock_status():
    """
    Shared fake config status used across AI service tests.
    """
    return {
        "loaded": True,
        "path": "configs/config_dev.json",
        "counts": {"courses": 3},
        "unsaved_changes": False,
        "schedules_updated": False,
    }


def _mock_working_config():
    """
    Shared fake working config used to avoid Flask session access.
    """
    return {
        "config": {
            "courses": [
                {"course_id": "CMSC 161"},
                {"course_id": "CMSC 162"},
                {"course_id": "CMSC 330"},
            ],
            "rooms": ["Roddy 140", "Roddy 147"],
        }
    }


def test_build_base_prompt_returns_expected_prompt():
    """
    Ensures the base prompt function returns the static AI system prompt.
    """
    assert build_base_prompt() == BASE_PROMPT
    assert "Maverick Scheduler AI Configuration Assistant" in build_base_prompt()


def test_build_user_input_includes_status_context(monkeypatch):
    """
    Ensures user input payload includes current config status and user command.
    """
    monkeypatch.setattr(
        "app.web.services.ai_service.get_config_status",
        _mock_status,
    )
    monkeypatch.setattr(
        "app.web.services.ai_service._get_working_config",
        _mock_working_config,
    )

    result = build_user_input("Add CMSC 161")

    assert "Config loaded: True" in result
    assert "Courses:" in result
    assert "Rooms:" in result
    assert "CMSC 161" in result
    assert "Roddy 140" in result
    assert "User command:" in result
    assert "Add CMSC 161" in result


def test_extract_text_from_response_uses_output_text():
    """
    Ensures helper extracts output_text when present.
    """
    response = SimpleNamespace(output_text="Hello from AI")

    result = extract_text_from_response(response)

    assert result == "Hello from AI"


def test_extract_text_from_response_returns_fallback_for_blank_text():
    """
    Ensures helper returns fallback text when no usable text is present.
    """
    response = SimpleNamespace(output_text="   ")

    result = extract_text_from_response(response)

    assert result == "The AI request completed, but no text response was returned."


def test_process_ai_command_rejects_blank_input():
    """
    Ensures blank commands return a structured failure response.
    """
    result = process_ai_command("   ")

    assert result["success"] is False
    assert result["changes_applied"] is False
    assert result["tool_calls"] == []
    assert "No command was provided." in result["message"]


def test_process_ai_command_success_without_tool_call(monkeypatch):
    """
    Ensures AI command processing builds a successful structured response
    when the model returns plain text and no tool call.
    """
    fake_response = SimpleNamespace(
        output_text="Add course interpreted successfully.",
        output=[],
    )

    class FakeResponses:
        def create(self, model, instructions, input, tools=None):
            return fake_response

    class FakeClient:
        def __init__(self):
            self.responses = FakeResponses()

    monkeypatch.setattr(
        "app.web.services.ai_service.get_openai_client",
        lambda: FakeClient(),
    )
    monkeypatch.setattr(
        "app.web.services.ai_service.get_model_name",
        lambda: "gpt-5-mini",
    )
    monkeypatch.setattr(
        "app.web.services.ai_service.get_config_status",
        _mock_status,
    )
    monkeypatch.setattr(
        "app.web.services.ai_service._get_working_config",
        _mock_working_config,
    )
    monkeypatch.setattr(
        "app.web.services.ai_service.get_tool_definitions",
        lambda: [{"type": "function", "name": "add_course"}],
    )

    result = process_ai_command("Add CMSC 161")

    assert result["success"] is True
    assert result["changes_applied"] is False
    assert result["tool_calls"] == []
    assert result["model"] == "gpt-5-mini"
    assert result["message"] == "Add course interpreted successfully."


def test_process_ai_command_executes_add_course_tool_call(monkeypatch):
    """
    Ensures a returned function_call item is parsed and executed through
    the tool dispatcher for add_course.
    """
    fake_response = SimpleNamespace(
        output_text="",
        output=[
            SimpleNamespace(
                type="function_call",
                name="add_course",
                arguments='{"course_id": "CS102", "credits": 3, "room": "Roddy 140"}',
            )
        ],
    )

    class FakeResponses:
        def create(self, model, instructions, input, tools=None):
            return fake_response

    class FakeClient:
        def __init__(self):
            self.responses = FakeResponses()

    monkeypatch.setattr(
        "app.web.services.ai_service.get_openai_client",
        lambda: FakeClient(),
    )
    monkeypatch.setattr(
        "app.web.services.ai_service.get_model_name",
        lambda: "gpt-5-mini",
    )
    monkeypatch.setattr(
        "app.web.services.ai_service.get_config_status",
        _mock_status,
    )
    monkeypatch.setattr(
        "app.web.services.ai_service._get_working_config",
        _mock_working_config,
    )
    monkeypatch.setattr(
        "app.web.services.ai_service.get_tool_definitions",
        lambda: [{"type": "function", "name": "add_course"}],
    )
    monkeypatch.setattr(
        "app.web.services.ai_service.execute_tool",
        lambda tool_name, args: {
            "success": True,
            "message": f"Executed {tool_name} for {args['course_id']}",
            "changes_applied": True,
        },
    )

    result = process_ai_command("Add course CS102 with 3 credits in Roddy 140")

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["tool_calls"] == ["add_course"]
    assert result["model"] == "gpt-5-mini"
    assert result["message"] == "Executed add_course for CS102"


def test_process_ai_command_executes_rename_course_tool_call(monkeypatch):
    """
    Ensures a rename_course function_call is executed correctly.
    """
    fake_response = SimpleNamespace(
        output_text="",
        output=[
            SimpleNamespace(
                type="function_call",
                name="rename_course",
                arguments='{"course_id": "CS163", "new_course_id": "CS370"}',
            )
        ],
    )

    class FakeResponses:
        def create(self, model, instructions, input, tools=None):
            return fake_response

    class FakeClient:
        def __init__(self):
            self.responses = FakeResponses()

    monkeypatch.setattr(
        "app.web.services.ai_service.get_openai_client",
        lambda: FakeClient(),
    )
    monkeypatch.setattr(
        "app.web.services.ai_service.get_model_name",
        lambda: "gpt-5-mini",
    )
    monkeypatch.setattr(
        "app.web.services.ai_service.get_config_status",
        _mock_status,
    )
    monkeypatch.setattr(
        "app.web.services.ai_service._get_working_config",
        _mock_working_config,
    )
    monkeypatch.setattr(
        "app.web.services.ai_service.get_tool_definitions",
        lambda: [{"type": "function", "name": "rename_course"}],
    )
    monkeypatch.setattr(
        "app.web.services.ai_service.execute_tool",
        lambda tool_name, args: {
            "success": True,
            "message": f"Renamed {args['course_id']} to {args['new_course_id']}",
            "changes_applied": True,
        },
    )

    result = process_ai_command("Rename course CS163 to CS370")

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["tool_calls"] == ["rename_course"]
    assert result["model"] == "gpt-5-mini"
    assert result["message"] == "Renamed CS163 to CS370"


def test_process_ai_command_executes_remove_course_lab_tool_call(monkeypatch):
    """
    Ensures a remove_course_lab function_call is executed correctly.
    """
    fake_response = SimpleNamespace(
        output_text="",
        output=[
            SimpleNamespace(
                type="function_call",
                name="remove_course_lab",
                arguments='{"course_id": "CS199"}',
            )
        ],
    )

    class FakeResponses:
        def create(self, model, instructions, input, tools=None):
            return fake_response

    class FakeClient:
        def __init__(self):
            self.responses = FakeResponses()

    monkeypatch.setattr(
        "app.web.services.ai_service.get_openai_client",
        lambda: FakeClient(),
    )
    monkeypatch.setattr(
        "app.web.services.ai_service.get_model_name",
        lambda: "gpt-5-mini",
    )
    monkeypatch.setattr(
        "app.web.services.ai_service.get_config_status",
        _mock_status,
    )
    monkeypatch.setattr(
        "app.web.services.ai_service._get_working_config",
        _mock_working_config,
    )
    monkeypatch.setattr(
        "app.web.services.ai_service.get_tool_definitions",
        lambda: [{"type": "function", "name": "remove_course_lab"}],
    )
    monkeypatch.setattr(
        "app.web.services.ai_service.execute_tool",
        lambda tool_name, args: {
            "success": True,
            "message": f"Removed lab from {args['course_id']}",
            "changes_applied": True,
        },
    )

    result = process_ai_command("Remove the lab from CS199")

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["tool_calls"] == ["remove_course_lab"]
    assert result["model"] == "gpt-5-mini"
    assert result["message"] == "Removed lab from CS199"


def test_process_ai_command_executes_modify_course_credits_tool_call(monkeypatch):
    """
    Ensures a modify_course_credits function_call is executed correctly.
    """
    fake_response = SimpleNamespace(
        output_text="",
        output=[
            SimpleNamespace(
                type="function_call",
                name="modify_course_credits",
                arguments='{"course_id": "CS199", "credits": 4}',
            )
        ],
    )

    class FakeResponses:
        def create(self, model, instructions, input, tools=None):
            return fake_response

    class FakeClient:
        def __init__(self):
            self.responses = FakeResponses()

    monkeypatch.setattr(
        "app.web.services.ai_service.get_openai_client",
        lambda: FakeClient(),
    )
    monkeypatch.setattr(
        "app.web.services.ai_service.get_model_name",
        lambda: "gpt-5-mini",
    )
    monkeypatch.setattr(
        "app.web.services.ai_service.get_config_status",
        _mock_status,
    )
    monkeypatch.setattr(
        "app.web.services.ai_service._get_working_config",
        _mock_working_config,
    )
    monkeypatch.setattr(
        "app.web.services.ai_service.get_tool_definitions",
        lambda: [{"type": "function", "name": "modify_course_credits"}],
    )
    monkeypatch.setattr(
        "app.web.services.ai_service.execute_tool",
        lambda tool_name, args: {
            "success": True,
            "message": f"Changed credits for {args['course_id']} to {args['credits']}",
            "changes_applied": True,
        },
    )

    result = process_ai_command("Change the credits of CS199 to 4")

    assert result["success"] is True
    assert result["changes_applied"] is True
    assert result["tool_calls"] == ["modify_course_credits"]
    assert result["model"] == "gpt-5-mini"
    assert result["message"] == "Changed credits for CS199 to 4"


def test_process_ai_command_returns_error_for_invalid_tool_arguments(monkeypatch):
    """
    Ensures invalid JSON arguments from the AI tool call are handled safely.
    """
    fake_response = SimpleNamespace(
        output_text="",
        output=[
            SimpleNamespace(
                type="function_call",
                name="add_course",
                arguments='{"course_id": "CS102", "credits": 3, ',
            )
        ],
    )

    class FakeResponses:
        def create(self, model, instructions, input, tools=None):
            return fake_response

    class FakeClient:
        def __init__(self):
            self.responses = FakeResponses()

    monkeypatch.setattr(
        "app.web.services.ai_service.get_openai_client",
        lambda: FakeClient(),
    )
    monkeypatch.setattr(
        "app.web.services.ai_service.get_model_name",
        lambda: "gpt-5-mini",
    )
    monkeypatch.setattr(
        "app.web.services.ai_service.get_config_status",
        _mock_status,
    )
    monkeypatch.setattr(
        "app.web.services.ai_service._get_working_config",
        _mock_working_config,
    )
    monkeypatch.setattr(
        "app.web.services.ai_service.get_tool_definitions",
        lambda: [{"type": "function", "name": "add_course"}],
    )

    result = process_ai_command("Add course CS102 with 3 credits in Roddy 140")

    assert result["success"] is False
    assert result["changes_applied"] is False
    assert result["tool_calls"] == ["add_course"]
    assert result["model"] == "gpt-5-mini"
    assert "invalid tool arguments" in result["message"].lower()
