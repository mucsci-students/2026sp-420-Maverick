# Author: Antonio Corona
# Date: 2026-04-04
"""
test_ai_service.py

Tests for app/web/services/ai_service.py.

Purpose:
- Validate prompt and user-input construction
- Confirm response-text extraction behavior
- Ensure AI command processing returns structured results
- Verify function-tool execution behavior for Phase 3

These are base-case service tests designed to:
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
        lambda: {
            "loaded": True,
            "path": "configs/config_dev.json",
            "counts": {"courses": 5},
            "unsaved_changes": False,
            "schedules_updated": True,
        },
    )

    result = build_user_input("Add CMSC 161")

    assert "Config loaded: True" in result
    assert "Config path: configs/config_dev.json" in result
    assert "Counts: {'courses': 5}" in result
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
        """
        Fake nested responses API with a create() method.
        """
        def create(self, model, instructions, input, tools=None):
            return fake_response

    class FakeClient:
        """
        Fake OpenAI client wrapper used by the service.
        """
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
        lambda: {
            "loaded": True,
            "path": "configs/config_dev.json",
            "counts": {"courses": 3},
            "unsaved_changes": False,
            "schedules_updated": False,
        },
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


def test_process_ai_command_executes_function_tool_call(monkeypatch):
    """
    Ensures a returned function_call item is parsed and executed through
    the tool dispatcher.
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
        lambda: {
            "loaded": True,
            "path": "configs/config_dev.json",
            "counts": {"courses": 3},
            "unsaved_changes": False,
            "schedules_updated": False,
        },
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
        lambda: {
            "loaded": True,
            "path": "configs/config_dev.json",
            "counts": {"courses": 3},
            "unsaved_changes": False,
            "schedules_updated": False,
        },
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