# Author: Antonio Corona
# Date: 2026-04-05
"""
test_run_routes.py

Tests for run_routes.py.

Purpose:
- Expand controller coverage for the Schedule Generator routes
- Cover both success and failure branches in run_routes.py
- Verify session-based override behavior for generator defaults
- Confirm reset and progress endpoints behave safely

Notes:
- These tests mock the service layer so no real scheduler work is performed.
- Focus remains on controller logic, not UI rendering.
"""

from app.web.app import create_app
from app.web.services.config_service import SESSION_CONFIG_KEY
from app.web.services.progress_store import generation_progress, is_running
from app.web.services.run_service import (
    SESSION_GENERATOR_LIMIT_OVERRIDE_KEY,
    SESSION_GENERATOR_FLAGS_OVERRIDE_KEY,
)


def _get_flashes(client):
    """
    Helper to read flashed messages from the current session.
    """
    with client.session_transaction() as sess:
        return list(sess.get("_flashes", []))


def test_run_route_loads():
    """
    Tests that the run page loads successfully.
    """
    app = create_app()
    client = app.test_client()

    response = client.get("/run/")

    assert response.status_code == 200


def test_generator_uses_fallback_defaults_when_no_config(monkeypatch):
    """
    Ensures the generator page uses fallback values when no config is loaded.
    Covers the default branch before cfg is present.
    """
    captured = {}

    def fake_render_template(template_name, **context):
        captured["template_name"] = template_name
        captured["context"] = context
        return "rendered-generator"

    monkeypatch.setattr(
        "app.web.routes.run_routes.render_template", fake_render_template
    )

    app = create_app()
    client = app.test_client()

    response = client.get("/run/")

    assert response.status_code == 200
    assert response.data == b"rendered-generator"
    assert captured["template_name"] == "generator.html"
    assert captured["context"]["config_loaded"] is False
    assert captured["context"]["default_limit"] == 5
    assert captured["context"]["selected_flags"] == []
    assert captured["context"]["available_flags"] == [
        "faculty_course",
        "faculty_room",
        "faculty_lab",
        "same_room",
        "same_lab",
        "pack_rooms",
    ]


def test_generator_uses_config_defaults_and_session_overrides(monkeypatch):
    """
    Ensures generator UI values come from config first and then session overrides.
    Also covers the branch that appends unknown selected flags into available_flags.
    """
    captured = {}

    def fake_render_template(template_name, **context):
        captured["template_name"] = template_name
        captured["context"] = context
        return "rendered-generator"

    monkeypatch.setattr(
        "app.web.routes.run_routes.render_template", fake_render_template
    )

    app = create_app()
    client = app.test_client()

    with client.session_transaction() as sess:
        sess[SESSION_CONFIG_KEY] = {
            "limit": 7,
            "optimizer_flags": ["faculty_course"],
        }
        sess[SESSION_GENERATOR_LIMIT_OVERRIDE_KEY] = 12
        sess[SESSION_GENERATOR_FLAGS_OVERRIDE_KEY] = ["faculty_room", "mystery_flag"]

    response = client.get("/run/")

    assert response.status_code == 200
    assert response.data == b"rendered-generator"
    assert captured["template_name"] == "generator.html"
    assert captured["context"]["config_loaded"] is True
    assert captured["context"]["default_limit"] == 12
    assert captured["context"]["selected_flags"] == ["faculty_room", "mystery_flag"]
    assert "faculty_room" in captured["context"]["available_flags"]
    assert "mystery_flag" in captured["context"]["available_flags"]


def test_generate_rejects_limit_below_one(monkeypatch):
    """
    Ensures generation rejects limit values below 1 and does not call the service.
    Covers the early validation failure branch.
    """
    service_called = {"called": False}

    def fake_generate_schedules_into_session(*args, **kwargs):
        service_called["called"] = True
        return 99

    monkeypatch.setattr(
        "app.web.routes.run_routes.generate_schedules_into_session",
        fake_generate_schedules_into_session,
    )

    app = create_app()
    client = app.test_client()

    response = client.post("/run/generate", data={"limit": "0"})

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/run/")
    assert service_called["called"] is False
    assert ("error", "Limit must be at least 1.") in _get_flashes(client)


def test_generate_rejects_non_integer_limit(monkeypatch):
    """
    Ensures generation rejects non-integer limit values.
    Covers the ValueError branch.
    """
    service_called = {"called": False}

    def fake_generate_schedules_into_session(*args, **kwargs):
        service_called["called"] = True
        return 99

    monkeypatch.setattr(
        "app.web.routes.run_routes.generate_schedules_into_session",
        fake_generate_schedules_into_session,
    )

    app = create_app()
    client = app.test_client()

    response = client.post("/run/generate", data={"limit": "abc"})

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/run/")
    assert service_called["called"] is False
    assert ("error", "Limit must be an integer.") in _get_flashes(client)


def test_generate_success_persists_overrides_and_returns_204(monkeypatch):
    """
    Ensures a successful generation:
    - parses submitted values
    - stores override values in session
    - calls the service layer
    - flashes success
    - returns HTTP 204 for JS-driven redirect handling
    """
    observed = {}

    def fake_generate_schedules_into_session(limit, optimizer_flags):
        observed["limit"] = limit
        observed["optimizer_flags"] = optimizer_flags
        return 3

    monkeypatch.setattr(
        "app.web.routes.run_routes.generate_schedules_into_session",
        fake_generate_schedules_into_session,
    )

    app = create_app()
    client = app.test_client()

    response = client.post(
        "/run/generate",
        data={
            "limit": "9",
            "optimizer_flags": ["faculty_course", "pack_rooms"],
        },
    )

    assert response.status_code == 204
    assert response.data == b""
    assert observed == {
        "limit": 9,
        "optimizer_flags": ["faculty_course", "pack_rooms"],
    }

    with client.session_transaction() as sess:
        assert sess[SESSION_GENERATOR_LIMIT_OVERRIDE_KEY] == 9
        assert sess[SESSION_GENERATOR_FLAGS_OVERRIDE_KEY] == [
            "faculty_course",
            "pack_rooms",
        ]

    assert ("success", "Generated 3 schedule(s).") in _get_flashes(client)


def test_generate_allows_empty_optimizer_flags(monkeypatch):
    """
    Ensures generation still succeeds when no optimizer flags are selected.
    Covers the branch where request.form.getlist(...) returns an empty list.
    """
    observed = {}

    def fake_generate_schedules_into_session(limit, optimizer_flags):
        observed["limit"] = limit
        observed["optimizer_flags"] = optimizer_flags
        return 1

    monkeypatch.setattr(
        "app.web.routes.run_routes.generate_schedules_into_session",
        fake_generate_schedules_into_session,
    )

    app = create_app()
    client = app.test_client()

    response = client.post("/run/generate", data={"limit": "5"})

    assert response.status_code == 204
    assert observed == {"limit": 5, "optimizer_flags": []}

    with client.session_transaction() as sess:
        assert sess[SESSION_GENERATOR_FLAGS_OVERRIDE_KEY] == []

    assert ("success", "Generated 1 schedule(s).") in _get_flashes(client)


def test_generate_exception_resets_progress_and_redirects(monkeypatch):
    """
    Ensures an exception during generation:
    - resets progress state
    - clears running state
    - flashes an error
    - redirects back to the generator

    This test avoids depending on the exact Flask-Session sid value by
    monkeypatching the route module's progress dictionaries.
    """
    observed_progress = {}
    observed_running = {}

    def fake_generate_schedules_into_session(*args, **kwargs):
        raise RuntimeError("scheduler exploded")

    monkeypatch.setattr(
        "app.web.routes.run_routes.generate_schedules_into_session",
        fake_generate_schedules_into_session,
    )
    monkeypatch.setattr(
        "app.web.routes.run_routes.generation_progress", observed_progress
    )
    monkeypatch.setattr("app.web.routes.run_routes.is_running", observed_running)

    app = create_app()
    client = app.test_client()

    response = client.post("/run/generate", data={"limit": "5"})

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/run/")
    assert len(observed_progress) == 1
    assert len(observed_running) == 1
    assert list(observed_progress.values()) == [0]
    assert list(observed_running.values()) == [False]
    assert ("error", "Generate failed: scheduler exploded") in _get_flashes(client)


def test_reset_clears_overrides_and_progress_state():
    """
    Ensures reset:
    - removes stored generator overrides
    - clears progress state
    - clears running state
    - flashes success
    """
    app = create_app()
    client = app.test_client()

    client.get("/run/")

    with client.session_transaction() as sess:
        sess[SESSION_GENERATOR_LIMIT_OVERRIDE_KEY] = 14
        sess[SESSION_GENERATOR_FLAGS_OVERRIDE_KEY] = ["faculty_course"]
        session_id = sess.sid

    generation_progress[session_id] = 88
    is_running[session_id] = True

    response = client.post("/run/reset")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/run/")

    with client.session_transaction() as sess:
        assert SESSION_GENERATOR_LIMIT_OVERRIDE_KEY not in sess
        assert SESSION_GENERATOR_FLAGS_OVERRIDE_KEY not in sess

    assert generation_progress[session_id] == 0
    assert is_running[session_id] is False
    assert ("success", "Reset Generator settings to config defaults.") in _get_flashes(
        client
    )


def test_get_progress_returns_current_session_progress(monkeypatch):
    """
    Ensures the progress endpoint returns the stored progress value.

    This test avoids depending on a specific persisted session sid by
    monkeypatching the route module's generation_progress mapping.
    """

    class FakeProgressStore(dict):
        def get(self, key, default=None):
            return 42

    monkeypatch.setattr(
        "app.web.routes.run_routes.generation_progress",
        FakeProgressStore(),
    )

    app = create_app()
    client = app.test_client()

    response = client.get("/run/progress")

    assert response.status_code == 200
    assert response.get_json() == {"progress": 42}


def test_get_progress_defaults_to_zero_for_new_session():
    """
    Ensures the progress endpoint defaults to zero when the session
    has no stored progress value.
    """
    app = create_app()
    client = app.test_client()

    response = client.get("/run/progress")

    assert response.status_code == 200
    assert response.get_json() == {"progress": 0}
