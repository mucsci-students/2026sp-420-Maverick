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
    SESSION_GENERATOR_FLAGS_OVERRIDE_KEY,
    SESSION_GENERATOR_LIMIT_OVERRIDE_KEY,
)


class ImmediateThread:
    """
    Test replacement for threading.Thread.

    Runs the background target immediately so async route behavior can be
    tested deterministically without starting a real thread.
    """

    def __init__(self, target, args=(), daemon=False):
        self.target = target
        self.args = args
        self.daemon = daemon

    def start(self):
        self.target(*self.args)


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


def test_generate_rejects_limit_below_one():
    """
    Ensures generation rejects limit values below 1 before starting async work.
    """
    app = create_app()
    client = app.test_client()

    response = client.post("/run/generate", data={"limit": "0"})

    assert response.status_code == 400
    assert response.get_json() == {"error": "Limit must be at least 1."}


def test_generate_rejects_non_integer_limit():
    """
    Ensures generation rejects non-integer limit values before starting async work.
    """
    app = create_app()
    client = app.test_client()

    response = client.post("/run/generate", data={"limit": "abc"})

    assert response.status_code == 400
    assert response.get_json() == {"error": "Limit must be an integer."}


def test_generate_success_persists_overrides_and_returns_202(monkeypatch):
    """
    Ensures successful generation:
    - parses submitted override values
    - stores override values in session
    - starts the async generation job
    - returns HTTP 202 for progress polling
    """
    observed = {}

    def fake_run_generation_job(session_id, cfg, limit, optimizer_flags):
        observed["session_id"] = session_id
        observed["cfg"] = cfg
        observed["limit"] = limit
        observed["optimizer_flags"] = optimizer_flags

    monkeypatch.setattr("app.web.routes.run_routes.Thread", ImmediateThread)
    monkeypatch.setattr(
        "app.web.routes.run_routes._run_generation_job",
        fake_run_generation_job,
    )

    app = create_app()
    client = app.test_client()

    with client.session_transaction() as sess:
        sess[SESSION_CONFIG_KEY] = {
            "limit": 100,
            "optimizer_flags": ["same_room"],
            "config": {"faculty": [], "rooms": [], "labs": [], "courses": []},
        }

    response = client.post(
        "/run/generate",
        data={
            "limit": "9",
            "optimizer_flags": ["faculty_course", "pack_rooms"],
        },
    )

    assert response.status_code == 202
    assert response.get_json() == {"status": "started"}

    assert observed["limit"] == 9
    assert observed["optimizer_flags"] == ["faculty_course", "pack_rooms"]
    assert observed["cfg"]["limit"] == 9
    assert observed["cfg"]["optimizer_flags"] == ["faculty_course", "pack_rooms"]

    with client.session_transaction() as sess:
        assert sess[SESSION_GENERATOR_LIMIT_OVERRIDE_KEY] == 9
        assert sess[SESSION_GENERATOR_FLAGS_OVERRIDE_KEY] == [
            "faculty_course",
            "pack_rooms",
        ]


def test_generate_allows_empty_optimizer_flags(monkeypatch):
    """
    Ensures async generation starts when no optimizer flags are selected.
    """
    observed = {}

    def fake_run_generation_job(session_id, cfg, limit, optimizer_flags):
        observed["limit"] = limit
        observed["optimizer_flags"] = optimizer_flags
        observed["cfg"] = cfg

    monkeypatch.setattr("app.web.routes.run_routes.Thread", ImmediateThread)
    monkeypatch.setattr(
        "app.web.routes.run_routes._run_generation_job",
        fake_run_generation_job,
    )

    app = create_app()
    client = app.test_client()

    with client.session_transaction() as sess:
        sess[SESSION_CONFIG_KEY] = {
            "limit": 100,
            "optimizer_flags": ["same_room"],
            "config": {"faculty": [], "rooms": [], "labs": [], "courses": []},
        }

    response = client.post("/run/generate", data={"limit": "5"})

    assert response.status_code == 202
    assert observed["limit"] == 5
    assert observed["optimizer_flags"] == []
    assert observed["cfg"]["optimizer_flags"] == []

    with client.session_transaction() as sess:
        assert sess[SESSION_GENERATOR_FLAGS_OVERRIDE_KEY] == []


def test_generation_job_exception_records_error_and_clears_running(monkeypatch):
    """
    Ensures background generation exceptions are stored for /run/progress
    and running state is cleared.
    """

    def fake_build_schedules_from_config(*args, **kwargs):
        raise RuntimeError("scheduler exploded")

    monkeypatch.setattr(
        "app.web.services.run_service.build_schedules_from_config",
        fake_build_schedules_from_config,
    )

    from app.web.routes.run_routes import _run_generation_job
    from app.web.services.progress_store import generation_errors

    session_id = "test-session-error"

    is_running[session_id] = True
    generation_progress[session_id] = 1

    _run_generation_job(
        session_id=session_id,
        cfg={"config": {"faculty": [], "rooms": [], "labs": [], "courses": []}},
        limit=5,
        optimizer_flags=[],
    )

    assert is_running[session_id] is False
    assert generation_errors[session_id] == "scheduler exploded"


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
    assert response.get_json() == {
        "progress": 42,
        "running": False,
        "error": None,
    }


def test_get_progress_defaults_to_zero_for_new_session():
    """
    Ensures the progress endpoint defaults to zero when the session
    has no stored progress value.
    """
    app = create_app()
    client = app.test_client()

    response = client.get("/run/progress")

    assert response.status_code == 200
    assert response.get_json() == {
        "progress": 0,
        "running": False,
        "error": None,
    }


def test_generate_fails_without_config():
    app = create_app()
    client = app.test_client()

    response = client.post("/run/generate", data={"limit": "5"})

    assert response.status_code == 400
    assert "No config loaded" in response.get_json()["error"]


def test_complete_generation_no_schedules():
    app = create_app()
    client = app.test_client()

    response = client.post("/run/complete")

    assert response.status_code == 409
    assert "not completed" in response.get_json()["error"]


def test_generator_handles_missing_optimizer_flags(monkeypatch):
    captured = {}

    def fake_render(template, **ctx):
        captured["ctx"] = ctx
        return "ok"

    monkeypatch.setattr("app.web.routes.run_routes.render_template", fake_render)

    app = create_app()
    client = app.test_client()

    with client.session_transaction() as sess:
        sess[SESSION_CONFIG_KEY] = {
            "limit": 5
            # optimizer_flags missing
        }

    client.get("/run/")

    assert captured["ctx"]["selected_flags"] == []


def test_generate_persists_session_overrides(monkeypatch):
    app = create_app()
    client = app.test_client()

    monkeypatch.setattr("app.web.routes.run_routes.Thread", ImmediateThread)

    with client.session_transaction() as sess:
        sess[SESSION_CONFIG_KEY] = {"limit": 10}

    client.post("/run/generate", data={"limit": "6", "optimizer_flags": ["A"]})

    with client.session_transaction() as sess:
        assert sess[SESSION_GENERATOR_LIMIT_OVERRIDE_KEY] == 6
        assert sess[SESSION_GENERATOR_FLAGS_OVERRIDE_KEY] == ["A"]


def test_progress_returns_error_field():
    app = create_app()
    client = app.test_client()

    from app.web.services.progress_store import generation_errors

    generation_errors["default-session"] = "failure happened"

    resp = client.get("/run/progress")

    data = resp.get_json()

    assert data["error"] == "failure happened"
