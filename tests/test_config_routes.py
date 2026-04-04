# Author: Antonio Corona
# Date: 2026-04-04
"""
test_config_routes.py

Tests for app/web/routes/config_routes.py.

Purpose:
- Validate configuration editor route behavior
- Confirm config load/save/export/clear flows work correctly
- Improve branch coverage for controller endpoints handling
  faculty, rooms, labs, courses, and conflicts

These are base-case route tests designed to:
- Verify Flask endpoint wiring
- Cover both success and failure controller branches
- Confirm session cleanup and response behavior
"""

from io import BytesIO

from flask import Flask

from app.web.routes.config_routes import bp


def _make_app():
    """
    Creates a lightweight Flask app with the config blueprint registered.

    A simple inline render_template monkeypatch is used in tests so route
    handlers can return successfully without depending on full templates.
    """
    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.register_blueprint(bp)
    return app


def test_editor_route_loads(monkeypatch):
    """
    Ensures the config editor page renders successfully.
    """
    app = _make_app()

    monkeypatch.setattr(
        "app.web.routes.config_routes.get_config_status",
        lambda: {"loaded": True, "path": "configs/config_dev.json"},
    )
    monkeypatch.setattr(
        "app.web.routes.config_routes.render_template",
        lambda template, **kwargs: f"rendered:{template}",
    )

    client = app.test_client()
    response = client.get("/config/")

    assert response.status_code == 200
    assert b"rendered:config_editor.html" in response.data


def test_load_route_success(monkeypatch):
    """
    Ensures config load route calls the service and redirects on success.
    """
    app = _make_app()
    called = {"path": None}

    monkeypatch.setattr(
        "app.web.routes.config_routes.load_config_into_session",
        lambda path: called.__setitem__("path", path),
    )

    client = app.test_client()
    response = client.post("/config/load", data={"path": "configs/config_dev.json"})

    assert response.status_code == 302
    assert called["path"] == "configs/config_dev.json"


def test_load_route_failure(monkeypatch):
    """
    Ensures config load route handles service-layer exceptions gracefully.
    """
    app = _make_app()

    def fake_load(path):
        raise RuntimeError("load failed")

    monkeypatch.setattr(
        "app.web.routes.config_routes.load_config_into_session",
        fake_load,
    )

    client = app.test_client()
    response = client.post("/config/load", data={"path": "bad.json"})

    assert response.status_code == 302


def test_save_route_success(monkeypatch):
    """
    Ensures config save route calls the service and redirects on success.
    """
    app = _make_app()
    called = {"path": None}

    monkeypatch.setattr(
        "app.web.routes.config_routes.save_config_from_session",
        lambda path: called.__setitem__("path", path),
    )

    client = app.test_client()
    response = client.post("/config/save", data={"path": "configs/config_dev.json"})

    assert response.status_code == 302
    assert called["path"] == "configs/config_dev.json"


def test_save_route_failure(monkeypatch):
    """
    Ensures config save route handles service-layer exceptions gracefully.
    """
    app = _make_app()

    def fake_save(path):
        raise RuntimeError("save failed")

    monkeypatch.setattr(
        "app.web.routes.config_routes.save_config_from_session",
        fake_save,
    )

    client = app.test_client()
    response = client.post("/config/save", data={"path": "bad.json"})

    assert response.status_code == 302


def test_load_file_route_with_no_file_selected():
    """
    Ensures file-upload load route rejects empty file selection.
    """
    app = _make_app()
    client = app.test_client()

    response = client.post(
        "/config/load_file",
        data={"config_file": (BytesIO(b""), "")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 302


def test_load_file_route_with_wrong_extension():
    """
    Ensures file-upload load route rejects non-JSON files.
    """
    app = _make_app()
    client = app.test_client()

    response = client.post(
        "/config/load_file",
        data={"config_file": (BytesIO(b"abc"), "config.txt")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 302


def test_load_file_route_success(monkeypatch):
    """
    Ensures JSON config upload is passed to the service layer successfully.
    """
    app = _make_app()
    called = {"filename": None}

    def fake_load(file_obj):
        called["filename"] = file_obj.filename

    monkeypatch.setattr(
        "app.web.routes.config_routes.load_config_into_session",
        fake_load,
    )

    client = app.test_client()
    response = client.post(
        "/config/load_file",
        data={"config_file": (BytesIO(b"{}"), "config.json")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 302
    assert called["filename"] == "config.json"


def test_load_file_route_failure(monkeypatch):
    """
    Ensures JSON config upload handles parsing/service failure gracefully.
    """
    app = _make_app()

    def fake_load(file_obj):
        raise RuntimeError("upload load failed")

    monkeypatch.setattr(
        "app.web.routes.config_routes.load_config_into_session",
        fake_load,
    )

    client = app.test_client()
    response = client.post(
        "/config/load_file",
        data={"config_file": (BytesIO(b"{}"), "config.json")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 302


def test_export_route_success(monkeypatch):
    """
    Ensures config export route returns a downloadable JSON response.
    """
    app = _make_app()

    monkeypatch.setattr(
        "app.web.routes.config_routes.export_config_bytes",
        lambda requested_name: (b'{"config":{}}', "my_config.json"),
    )

    client = app.test_client()
    response = client.post("/config/export", data={"filename": "my_config.json"})

    assert response.status_code == 200
    assert response.mimetype == "application/json"
    assert "attachment;" in response.headers["Content-Disposition"]
    assert response.headers["X-Export-Filename"] == "my_config.json"


def test_export_route_failure(monkeypatch):
    """
    Ensures config export route returns a 400 response on export failure.
    """
    app = _make_app()

    def fake_export(requested_name):
        raise RuntimeError("export failed")

    monkeypatch.setattr(
        "app.web.routes.config_routes.export_config_bytes",
        fake_export,
    )

    client = app.test_client()
    response = client.post("/config/export", data={"filename": "bad.json"})

    assert response.status_code == 400
    assert response.mimetype == "text/plain"


def test_clear_route_removes_session_state(monkeypatch):
    """
    Ensures clear route wipes config and viewer-related session state.
    """
    app = _make_app()
    called = {"updated": None}

    monkeypatch.setattr(
        "app.web.routes.config_routes.set_schedules_updated",
        lambda value: called.__setitem__("updated", value),
    )

    client = app.test_client()

    with client.session_transaction() as sess:
        sess["working_config"] = {"config": {}}
        sess["working_path"] = "configs/config_dev.json"
        sess["unsaved_changes"] = True
        sess["schedules"] = [{"meta": {}, "assignments": []}]
        sess["selected_schedule_index"] = 2
        sess["viewer_user_selected"] = True

    response = client.post("/config/clear")

    assert response.status_code == 302
    assert called["updated"] is False

    with client.session_transaction() as sess:
        assert "working_config" not in sess
        assert "working_path" not in sess
        assert "unsaved_changes" not in sess
        assert "schedules" not in sess
        assert "selected_schedule_index" not in sess
        assert "viewer_user_selected" not in sess


def test_faculty_add_success(monkeypatch):
    """
    Ensures faculty add route calls the service successfully.
    """
    app = _make_app()
    called = {"data": None}

    def fake_add_faculty_service(**kwargs):
        called["data"] = kwargs

    monkeypatch.setattr(
        "app.web.routes.config_routes.add_faculty_service",
        fake_add_faculty_service,
    )

    client = app.test_client()
    response = client.post("/config/faculty/add", data={"name": "Hardy"})

    assert response.status_code == 302
    assert called["data"]["name"] == "Hardy"


def test_faculty_add_failure(monkeypatch):
    """
    Ensures faculty add route handles service failure gracefully.
    """
    app = _make_app()

    def fake_add_faculty_service(**kwargs):
        raise RuntimeError("faculty add failed")

    monkeypatch.setattr(
        "app.web.routes.config_routes.add_faculty_service",
        fake_add_faculty_service,
    )

    client = app.test_client()
    response = client.post("/config/faculty/add", data={"name": "Hardy"})

    assert response.status_code == 302


def test_room_add_success(monkeypatch):
    """
    Ensures room add route passes the room value to the service.
    """
    app = _make_app()
    called = {"room": None}

    monkeypatch.setattr(
        "app.web.routes.config_routes.add_room_service",
        lambda room: called.__setitem__("room", room),
    )

    client = app.test_client()
    response = client.post("/config/room/add", data={"room": "Roddy 136"})

    assert response.status_code == 302
    assert called["room"] == "Roddy 136"


def test_room_modify_success(monkeypatch):
    """
    Ensures room modify route passes both current and new names.
    """
    app = _make_app()
    called = {"old": None, "new": None}

    def fake_modify_room_service(old_name, new_name):
        called["old"] = old_name
        called["new"] = new_name

    monkeypatch.setattr(
        "app.web.routes.config_routes.modify_room_service",
        fake_modify_room_service,
    )

    client = app.test_client()
    response = client.post(
        "/config/room/modify",
        data={"room": "Roddy 136", "new_name": "Roddy 140"},
    )

    assert response.status_code == 302
    assert called["old"] == "Roddy 136"
    assert called["new"] == "Roddy 140"


def test_lab_add_success(monkeypatch):
    """
    Ensures lab add route calls the service successfully.
    """
    app = _make_app()
    called = {"data": None}

    def fake_add_lab_service(**kwargs):
        called["data"] = kwargs

    monkeypatch.setattr(
        "app.web.routes.config_routes.add_lab_service",
        fake_add_lab_service,
    )

    client = app.test_client()
    response = client.post("/config/lab/add", data={"lab": "Linux"})

    assert response.status_code == 302
    assert called["data"]["lab"] == "Linux"


def test_course_add_success(monkeypatch):
    """
    Ensures course add route calls the service successfully.
    """
    app = _make_app()
    called = {"data": None}

    def fake_add_course_service(**kwargs):
        called["data"] = kwargs

    monkeypatch.setattr(
        "app.web.routes.config_routes.add_course_service",
        fake_add_course_service,
    )

    client = app.test_client()
    response = client.post("/config/course/add", data={"course_id": "CMSC 161"})

    assert response.status_code == 302
    assert called["data"]["course_id"] == "CMSC 161"


def test_conflict_add_success(monkeypatch):
    """
    Ensures conflict add route calls the service successfully.
    """
    app = _make_app()
    called = {"data": None}

    def fake_add_conflict_service(**kwargs):
        called["data"] = kwargs

    monkeypatch.setattr(
        "app.web.routes.config_routes.add_conflict_service",
        fake_add_conflict_service,
    )

    client = app.test_client()
    response = client.post(
        "/config/conflict/add",
        data={"course_id": "CMSC 161", "conflict": "CMSC 162"},
    )

    assert response.status_code == 302
    assert called["data"]["course_id"] == "CMSC 161"


def test_conflict_modify_failure(monkeypatch):
    """
    Ensures conflict modify route handles service failure gracefully.
    """
    app = _make_app()

    def fake_modify_conflict_service(**kwargs):
        raise RuntimeError("conflict modify failed")

    monkeypatch.setattr(
        "app.web.routes.config_routes.modify_conflict_service",
        fake_modify_conflict_service,
    )

    client = app.test_client()
    response = client.post(
        "/config/conflict/modify",
        data={"course_id": "CMSC 161", "conflict": "CMSC 162"},
    )

    assert response.status_code == 302