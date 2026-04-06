# Author: Antonio Corona
# Date: 2026-04-04
"""
test_viewer_routes.py

Tests for app/web/routes/viewer_routes.py.

Purpose:
- Ensure schedule viewer page loads successfully
- Validate routing behavior for the viewer endpoint
- Validate schedule viewer route behavior
- Confirm navigation, export, import, and reset endpoints behave correctly
- Improve branch coverage for the active Viewer controller layer

These are base-case route tests designed to:
- Verify Flask endpoint wiring
- Confirm redirects and flash-driven flows do not crash
- Cover both success and fallback/error branches where practical

Notes:
- The real route is /viewer/ (with trailing slash).
"""

from io import BytesIO

from flask import Flask, session

from app.web.app import create_app
from app.web.routes.viewer_routes import bp


def test_viewer_route_loads():
    """
    Tests that the viewer page loads successfully.
    """
    app = create_app()
    client = app.test_client()

    response = client.get("/viewer/")

    assert response.status_code == 200


def test_viewer_route_with_query_string():
    """
    Tests that the viewer route still loads when given a query string.
    """
    app = create_app()
    client = app.test_client()

    response = client.get("/viewer/?index=0")

    assert response.status_code == 200


def _make_app():
    """
    Creates a lightweight Flask app with the viewer blueprint registered.

    A minimal inline template is used so route tests can render successfully
    without depending on the full production template stack.
    """
    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.register_blueprint(bp)

    @app.route("/")
    def home():
        return "home"

    return app


def test_viewer_route_loads(monkeypatch):
    """
    Ensures the main viewer page loads successfully with normal service data.
    """
    app = _make_app()

    monkeypatch.setattr(
        "app.web.routes.viewer_routes.get_schedules_updated",
        lambda: False,
    )
    monkeypatch.setattr(
        "app.web.routes.viewer_routes.is_export_enabled",
        lambda: True,
    )
    monkeypatch.setattr(
        "app.web.routes.viewer_routes.get_view_data",
        lambda: {
            "has_schedules": True,
            "assignments": [],
            "by_room": {},
            "by_lab": {},
            "by_faculty": {},
        },
    )
    monkeypatch.setattr(
        "app.web.routes.viewer_routes._get_cgf",
        lambda: {
            "config": {
                "rooms": ["Roddy 136", "Roddy 140"],
                "labs": ["Linux", "Mac"],
                "faculty": [{"name": "Hardy"}, {"name": "Xie"}],
            }
        },
    )
    monkeypatch.setattr(
        "app.web.routes.viewer_routes.render_template",
        lambda template, **kwargs: f"rendered:{template}",
    )

    client = app.test_client()
    response = client.get("/viewer/")

    assert response.status_code == 200
    assert b"rendered:viewer.html" in response.data


def test_viewer_route_updates_schedules_when_flagged_from_config(monkeypatch):
    """
    Ensures viewer triggers schedule updates when returning from the config page
    and the schedules-updated flag is set.
    """
    app = _make_app()
    calls = {"updated": False, "reset_flag": False}

    monkeypatch.setattr(
        "app.web.routes.viewer_routes.get_schedules_updated",
        lambda: True,
    )
    monkeypatch.setattr(
        "app.web.routes.viewer_routes._get_cgf",
        lambda: {"config": {"rooms": [], "labs": [], "faculty": []}},
    )

    def fake_update_schedules(cfg):
        calls["updated"] = True

    def fake_set_schedules_updated(value):
        calls["reset_flag"] = value is False

    monkeypatch.setattr(
        "app.web.routes.viewer_routes.update_schedules",
        fake_update_schedules,
    )
    monkeypatch.setattr(
        "app.web.routes.viewer_routes.set_schedules_updated",
        fake_set_schedules_updated,
    )
    monkeypatch.setattr(
        "app.web.routes.viewer_routes.get_view_data",
        lambda: {
            "has_schedules": True,
            "assignments": [],
            "by_room": {},
            "by_lab": {},
            "by_faculty": {},
        },
    )
    monkeypatch.setattr(
        "app.web.routes.viewer_routes.is_export_enabled",
        lambda: False,
    )
    monkeypatch.setattr(
        "app.web.routes.viewer_routes.render_template",
        lambda template, **kwargs: "ok",
    )

    client = app.test_client()
    response = client.get("/viewer/", headers={"Referer": "/config"})

    assert response.status_code == 200
    assert calls["updated"] is True
    assert calls["reset_flag"] is True


def test_go_next_redirects(monkeypatch):
    """
    Ensures the next-schedule route calls the service and redirects back to viewer.
    """
    app = _make_app()
    called = {"next": False}

    monkeypatch.setattr(
        "app.web.routes.viewer_routes.next_schedule",
        lambda: called.__setitem__("next", True),
    )

    client = app.test_client()
    response = client.post("/viewer/next")

    assert response.status_code == 302
    assert called["next"] is True


def test_go_prev_redirects(monkeypatch):
    """
    Ensures the previous-schedule route calls the service and redirects back to viewer.
    """
    app = _make_app()
    called = {"prev": False}

    monkeypatch.setattr(
        "app.web.routes.viewer_routes.prev_schedule",
        lambda: called.__setitem__("prev", True),
    )

    client = app.test_client()
    response = client.post("/viewer/prev")

    assert response.status_code == 302
    assert called["prev"] is True


def test_select_route_with_valid_index(monkeypatch):
    """
    Ensures direct schedule selection parses a valid integer index.
    """
    app = _make_app()
    called = {"index": None}

    monkeypatch.setattr(
        "app.web.routes.viewer_routes.select_schedule",
        lambda idx: called.__setitem__("index", idx),
    )

    client = app.test_client()
    response = client.post("/viewer/select", data={"index": "2"})

    assert response.status_code == 302
    assert called["index"] == 2


def test_select_route_with_invalid_index_is_ignored(monkeypatch):
    """
    Ensures invalid selection input is ignored instead of crashing.
    """
    app = _make_app()
    called = {"count": 0}

    def fake_select_schedule(idx):
        called["count"] += 1
        raise ValueError("bad index")

    monkeypatch.setattr(
        "app.web.routes.viewer_routes.select_schedule",
        fake_select_schedule,
    )

    client = app.test_client()
    response = client.post("/viewer/select", data={"index": "bad"})

    assert response.status_code == 302
    assert called["count"] == 0


def test_export_route_success(monkeypatch):
    """
    Ensures export route handles successful JSON export.
    """
    app = _make_app()
    called = {"path": None}

    monkeypatch.setattr(
        "app.web.routes.viewer_routes.export_schedules_to_file",
        lambda path: called.__setitem__("path", path),
    )

    client = app.test_client()
    response = client.post("/viewer/export", data={"path": "out.json"})

    assert response.status_code == 302
    assert called["path"] == "out.json"


def test_export_route_failure(monkeypatch):
    """
    Ensures export route handles service-layer exceptions gracefully.
    """
    app = _make_app()

    def fake_export(path):
        raise RuntimeError("export broke")

    monkeypatch.setattr(
        "app.web.routes.viewer_routes.export_schedules_to_file",
        fake_export,
    )

    client = app.test_client()
    response = client.post("/viewer/export", data={"path": "out.json"})

    assert response.status_code == 302


def test_import_route_success(monkeypatch):
    """
    Ensures import route handles successful file import.
    """
    app = _make_app()
    called = {"path": None}

    monkeypatch.setattr(
        "app.web.routes.viewer_routes.import_schedules_from_file",
        lambda path: called.__setitem__("path", path),
    )

    client = app.test_client()
    response = client.post("/viewer/import", data={"path": "in.json"})

    assert response.status_code == 302
    assert called["path"] == "in.json"


def test_import_route_failure(monkeypatch):
    """
    Ensures import route handles service-layer import failure gracefully.
    """
    app = _make_app()

    def fake_import(path):
        raise RuntimeError("import broke")

    monkeypatch.setattr(
        "app.web.routes.viewer_routes.import_schedules_from_file",
        fake_import,
    )

    client = app.test_client()
    response = client.post("/viewer/import", data={"path": "in.json"})

    assert response.status_code == 302


def test_import_file_with_no_selected_files():
    """
    Ensures upload route handles missing file selection gracefully.
    """
    app = _make_app()
    client = app.test_client()

    response = client.post(
        "/viewer/import_file",
        data={"schedule_file": (BytesIO(b""), "")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 302


def test_import_file_success(monkeypatch):
    """
    Ensures upload route processes JSON files and appends imported schedules.
    """
    app = _make_app()

    monkeypatch.setattr(
        "app.web.routes.viewer_routes.import_schedules_from_file",
        lambda file_obj: (2, 5),
    )

    client = app.test_client()
    response = client.post(
        "/viewer/import_file",
        data={"schedule_file": (BytesIO(b"[]"), "sched.json")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 302


def test_export_file_requires_selection(monkeypatch):
    """
    Ensures export_file route redirects when no schedules are selected.
    """
    app = _make_app()

    monkeypatch.setattr(
        "app.web.routes.viewer_routes.get_schedules_for_export",
        lambda: [],
    )

    client = app.test_client()
    response = client.post("/viewer/export_file", data={})

    assert response.status_code == 302


def test_export_file_returns_json_attachment(monkeypatch):
    """
    Ensures export_file returns a downloadable JSON response for selected schedules.
    """
    app = _make_app()

    monkeypatch.setattr(
        "app.web.routes.viewer_routes.get_schedules_for_export",
        lambda: [
            {"meta": {"schedule_id": 1}, "assignments": []},
            {"meta": {"schedule_id": 2}, "assignments": []},
        ],
    )

    client = app.test_client()
    response = client.post(
        "/viewer/export_file",
        data={"schedule_indices": ["0"]},
    )

    assert response.status_code == 200
    assert response.mimetype == "application/json"
    assert "attachment;" in response.headers["Content-disposition"]


def test_export_csv_requires_selection():
    """
    Ensures export_csv redirects when no schedules are selected.
    """
    app = _make_app()
    client = app.test_client()

    response = client.post("/viewer/export_csv", data={})

    assert response.status_code == 302


def test_export_csv_success(monkeypatch):
    """
    Ensures export_csv returns a downloadable CSV response on success.
    """
    app = _make_app()

    monkeypatch.setattr(
        "app.web.routes.viewer_routes.export_schedules_to_csv",
        lambda indices: "course_id,room\nCMSC 161.01,Roddy 136\n",
    )

    client = app.test_client()
    response = client.post(
        "/viewer/export_csv",
        data={"schedule_indices": ["0", "1"]},
    )

    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert b"course_id,room" in response.data


def test_export_csv_failure(monkeypatch):
    """
    Ensures export_csv handles CSV export exceptions gracefully.
    """
    app = _make_app()

    def fake_export(indices):
        raise RuntimeError("csv broke")

    monkeypatch.setattr(
        "app.web.routes.viewer_routes.export_schedules_to_csv",
        fake_export,
    )

    client = app.test_client()
    response = client.post(
        "/viewer/export_csv",
        data={"schedule_indices": ["0"]},
    )

    assert response.status_code == 302


def test_visual_view_redirects_without_schedules(monkeypatch):
    """
    Ensures visual calendar route redirects when no schedules exist.
    """
    app = _make_app()

    monkeypatch.setattr(
        "app.web.routes.viewer_routes.get_view_data",
        lambda: {"has_schedules": False},
    )

    client = app.test_client()
    response = client.get("/viewer/visual_view")

    assert response.status_code == 302


def test_visual_view_renders_with_schedules(monkeypatch):
    """
    Ensures visual calendar route renders when schedules exist.
    """
    app = _make_app()

    monkeypatch.setattr(
        "app.web.routes.viewer_routes.get_view_data",
        lambda: {"has_schedules": True, "assignments": []},
    )
    monkeypatch.setattr(
        "app.web.routes.viewer_routes.render_template",
        lambda template, **kwargs: f"rendered:{template}",
    )

    client = app.test_client()
    response = client.get("/viewer/visual_view")

    assert response.status_code == 200
    assert b"rendered:visual_schedule.html" in response.data


def test_grid_view_redirects_without_schedules(monkeypatch):
    """
    Ensures grid view route redirects when no schedules exist.
    """
    app = _make_app()

    monkeypatch.setattr(
        "app.web.routes.viewer_routes.get_view_data",
        lambda: {"has_schedules": False},
    )

    client = app.test_client()
    response = client.get("/viewer/grid_view")

    assert response.status_code == 302


def test_grid_view_renders_with_schedules(monkeypatch):
    """
    Ensures grid view route renders when schedules exist.
    """
    app = _make_app()

    monkeypatch.setattr(
        "app.web.routes.viewer_routes.get_view_data",
        lambda: {"has_schedules": True, "assignments": []},
    )
    monkeypatch.setattr(
        "app.web.routes.viewer_routes.render_template",
        lambda template, **kwargs: f"rendered:{template}",
    )

    client = app.test_client()
    response = client.get("/viewer/grid_view")

    assert response.status_code == 200
    assert b"rendered:grid_schedule.html" in response.data


def test_reset_viewer_clears_session_keys():
    """
    Ensures reset_viewer removes schedule-related session state.
    """
    app = _make_app()
    client = app.test_client()

    with client.session_transaction() as sess:
        sess["schedules"] = [{"meta": {}, "assignments": []}]
        sess["selected_schedule_index"] = 2

    response = client.post("/viewer/reset")

    assert response.status_code == 302

    with client.session_transaction() as sess:
        assert "schedules" not in sess
        assert "selected_schedule_index" not in sess
