# Author: Antonio Corona
# Date: 2026-04-04
"""
test_ai_routes.py

Tests for app/web/routes/ai_routes.py.

Purpose:
- Validate AI chat page routing behavior
- Confirm AI command controller validation logic
- Ensure successful and failure AI command flows are handled correctly

These are base-case route tests designed to:
- Verify Flask endpoint wiring
- Cover config-loaded and missing-config branches
- Confirm command submission behavior remains stateless
"""

from flask import Flask

from app.web.routes.ai_routes import bp
from app.web.services.config_service import SESSION_CONFIG_KEY


def _make_app():
    """
    Creates a lightweight Flask app with the AI blueprint registered.
    """
    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.register_blueprint(bp)
    return app


def test_ai_chat_route_renders_without_config(monkeypatch):
    """
    Ensures the AI chat page renders correctly when no config is loaded.
    """
    app = _make_app()

    monkeypatch.setattr(
        "app.web.routes.ai_routes.render_template",
        lambda template, **kwargs: f"rendered:{template}:{kwargs['config_loaded']}",
    )

    client = app.test_client()
    response = client.get("/ai/")

    assert response.status_code == 200
    assert b"rendered:ai_chat.html:False" in response.data


def test_ai_chat_route_renders_with_config(monkeypatch):
    """
    Ensures the AI chat page renders correctly when a config is loaded.
    """
    app = _make_app()

    monkeypatch.setattr(
        "app.web.routes.ai_routes.render_template",
        lambda template, **kwargs: f"rendered:{template}:{kwargs['config_loaded']}",
    )

    client = app.test_client()

    with client.session_transaction() as sess:
        sess[SESSION_CONFIG_KEY] = {"config": {}}

    response = client.get("/ai/")

    assert response.status_code == 200
    assert b"rendered:ai_chat.html:True" in response.data


def test_ai_command_redirects_when_no_config_loaded():
    """
    Ensures command submission is rejected if no config is loaded.
    """
    app = _make_app()
    client = app.test_client()

    response = client.post("/ai/command", data={"command": "Add CMSC 161"})

    assert response.status_code == 302
    assert "/ai/" in response.headers["Location"]


def test_ai_command_redirects_when_command_is_blank():
    """
    Ensures blank AI commands are rejected even when config is loaded.
    """
    app = _make_app()
    client = app.test_client()

    with client.session_transaction() as sess:
        sess[SESSION_CONFIG_KEY] = {"config": {}}

    response = client.post("/ai/command", data={"command": "   "})

    assert response.status_code == 302
    assert "/ai/" in response.headers["Location"]


def test_ai_command_renders_success_result(monkeypatch):
    """
    Ensures a valid AI command renders the AI response successfully.
    """
    app = _make_app()

    monkeypatch.setattr(
        "app.web.routes.ai_routes.process_ai_command",
        lambda command: {
            "success": True,
            "message": f"Processed: {command}",
            "changes_applied": False,
            "tool_calls": [],
        },
    )
    monkeypatch.setattr(
        "app.web.routes.ai_routes.render_template",
        lambda template, **kwargs: f"rendered:{kwargs['ai_result']['message']}",
    )

    client = app.test_client()

    with client.session_transaction() as sess:
        sess[SESSION_CONFIG_KEY] = {"config": {}}

    response = client.post("/ai/command", data={"command": "Add CMSC 161"})

    assert response.status_code == 200
    assert b"rendered:Processed: Add CMSC 161" in response.data


def test_ai_command_handles_service_exception(monkeypatch):
    """
    Ensures route catches AI service exceptions and renders a safe fallback result.
    """
    app = _make_app()

    def fake_process(command):
        raise RuntimeError("service exploded")

    monkeypatch.setattr(
        "app.web.routes.ai_routes.process_ai_command",
        fake_process,
    )
    monkeypatch.setattr(
        "app.web.routes.ai_routes.render_template",
        lambda template, **kwargs: kwargs["ai_result"]["message"],
    )

    client = app.test_client()

    with client.session_transaction() as sess:
        sess[SESSION_CONFIG_KEY] = {"config": {}}

    response = client.post("/ai/command", data={"command": "Do something"})

    assert response.status_code == 200
    assert b"AI processing failed: service exploded" in response.data


def test_ai_command_renders_tool_applied_result(monkeypatch):
    """
    Ensures the route renders a successful tool-execution result.
    """
    app = _make_app()

    monkeypatch.setattr(
        "app.web.routes.ai_routes.process_ai_command",
        lambda command: {
            "success": True,
            "message": "Added course CS102 with 3 credits in room Roddy 140.",
            "changes_applied": True,
            "tool_calls": ["add_course"],
            "model": "gpt-5-mini",
        },
    )
    monkeypatch.setattr(
        "app.web.routes.ai_routes.render_template",
        lambda template, **kwargs: (
            f"rendered:{kwargs['ai_result']['message']}:"
            f"{kwargs['ai_result']['changes_applied']}"
        ),
    )

    client = app.test_client()

    with client.session_transaction() as sess:
        sess[SESSION_CONFIG_KEY] = {"config": {}}

    response = client.post(
        "/ai/command",
        data={"command": "Add course CS102 with 3 credits in Roddy 140"},
    )

    assert response.status_code == 200
    assert (
        b"rendered:Added course CS102 with 3 credits in room Roddy 140.:True"
        in response.data
    )
