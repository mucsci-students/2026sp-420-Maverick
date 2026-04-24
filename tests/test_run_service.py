# Author: Antonio Corona
# Date: 2026-04-04
"""
test_run_service.py

Tests for app/web/services/run_service.py.

Purpose:
- Validate base scheduling execution service behavior
- Confirm generated schedules are stored in session correctly
- Ensure optimizer flag handling works as expected
- Verify service guards against invalid state and concurrent runs

These are base-case tests intended to:
- Improve code coverage in the active web service layer
- Protect the scheduling/session data flow
- Catch regressions in generator UI backend behavior
"""

from flask import Flask, session

from app.web.services.config_service import SESSION_CONFIG_KEY
from app.web.services.progress_store import generation_progress, is_running
from app.web.services.run_service import (
    KNOWN_OPTIMIZER_FLAGS,
    SESSION_SCHEDULES_KEY,
    SESSION_SELECTED_INDEX_KEY,
    SESSION_USER_SELECTED_KEY,
    _to_int,
    generate_schedules_into_session,
)


def _make_app():
    """
    Creates a lightweight Flask app for testing session-based service logic.
    """
    app = Flask(__name__)
    app.secret_key = "test-secret"
    return app


def test_to_int_returns_integer_for_valid_input():
    """
    Ensures _to_int converts valid numeric input correctly.
    """
    assert _to_int("5") == 5
    assert _to_int(12) == 12


def test_to_int_returns_default_for_invalid_input():
    """
    Ensures _to_int falls back to default value on invalid input.
    """
    assert _to_int("abc", default=99) == 99
    assert _to_int(None, default=7) == 7


def test_generate_schedules_into_session_raises_without_config():
    """
    Ensures service raises a clear error when no config is loaded in session.
    """
    app = _make_app()

    with app.test_request_context("/"):
        session["_test_sid"] = "test-session-missing-config"

        try:
            generate_schedules_into_session(limit=5)
            assert False, "Expected ValueError when no config is loaded"
        except ValueError as exc:
            assert "No config loaded" in str(exc)

        # Cleanup shared progress globals after test
        session_id = session["_test_sid"]
        generation_progress.pop(session_id, None)
        is_running.pop(session_id, None)


def test_generate_schedules_into_session_blocks_concurrent_generation():
    """
    Ensures service prevents a second generation while one is already running.
    """
    app = _make_app()

    with app.test_request_context("/"):
        session["_test_sid"] = "test-session-concurrent"
        is_running[session["_test_sid"]] = True

        try:
            generate_schedules_into_session(limit=5)
            assert False, "Expected RuntimeError when generation is already running"
        except RuntimeError as exc:
            assert "already in progress" in str(exc)

        # Cleanup shared progress globals after test
        session_id = session["_test_sid"]
        generation_progress.pop(session_id, None)
        is_running.pop(session_id, None)


def test_generate_schedules_into_session_stores_schedules(monkeypatch):
    """
    Ensures generated schedules are grouped and stored in session correctly.
    """
    app = _make_app()

    fake_cfg = {
        "config": {
            "rooms": ["Roddy 136"],
            "labs": ["Linux"],
            "courses": [],
            "faculty": [],
        },
        "optimizer_flags": ["faculty_course"],
        "time_slot_config": {
            "days": ["MON", "TUE", "WED", "THU", "FRI"],
            "time_slots": {
                "MON": [{"start_time": "08:00", "end_time": "09:00"}],
                "TUE": [],
                "WED": [],
                "THU": [],
                "FRI": [],
            },
        },
    }

    fake_generated_rows = [
        [
            {
                "schedule_id": 1,
                "course_id": "CMSC 161.01",
                "day": "MON",
                "start": "10:00",
                "room": "Roddy 136",
                "faculty": "Zoppetti",
                "lab": "",
                "duration": "50",
                "credits": "4",
                "meeting_index": 1,
            },
            {
                "schedule_id": 1,
                "course_id": "CMSC 161.01",
                "day": "WED",
                "start": "10:00",
                "room": "Roddy 136",
                "faculty": "Zoppetti",
                "lab": "Linux",
                "duration": "110",
                "credits": "4",
                "meeting_index": 2,
            },
        ]
    ]

    def fake_generate_schedules(cfg, limit, optimize):
        """
        Fake scheduler generator that mimics scheduler_core output.
        """
        yield from fake_generated_rows

    monkeypatch.setattr(
        "app.web.services.run_service.generate_schedules",
        fake_generate_schedules,
    )

    with app.test_request_context("/"):
        session["_test_sid"] = "test-session-store"
        session[SESSION_CONFIG_KEY] = fake_cfg

        count = generate_schedules_into_session(limit=1)

        assert count == 1
        assert SESSION_SCHEDULES_KEY in session
        assert SESSION_SELECTED_INDEX_KEY in session
        assert SESSION_USER_SELECTED_KEY in session

        schedules = session[SESSION_SCHEDULES_KEY]
        assert len(schedules) == 1
        assert schedules[0]["meta"]["schedule_id"] == 1
        assert schedules[0]["meta"]["row_count"] == 2
        assert schedules[0]["assignments"][0]["course_id"] == "CMSC 161.01"
        assert schedules[0]["assignments"][0]["time"] == "MON 10:00"

        assert session[SESSION_SELECTED_INDEX_KEY] == 0
        assert session[SESSION_USER_SELECTED_KEY] is False

        # Cleanup shared progress globals after test
        session_id = session["_test_sid"]
        generation_progress.pop(session_id, None)
        is_running.pop(session_id, None)


def test_generate_schedules_into_session_filters_unknown_optimizer_flags(monkeypatch):
    """
    Ensures only known optimizer flags are retained before schedules are stored.
    """
    app = _make_app()

    fake_cfg = {
        "config": {
            "rooms": ["Roddy 136"],
            "labs": [],
            "courses": [],
            "faculty": [],
        },
        "optimizer_flags": ["faculty_course", "bad_flag"],
    }

    def fake_generate_schedules(cfg, limit, optimize):
        """
        Fake generator returning one minimal schedule row.
        """
        yield [
            {
                "schedule_id": 1,
                "course_id": "CMSC 140.01",
                "day": "MON",
                "start": "09:00",
                "room": "Roddy 136",
                "faculty": "Hardy",
                "lab": "",
                "duration": "50",
                "credits": "4",
                "meeting_index": 1,
            }
        ]

    monkeypatch.setattr(
        "app.web.services.run_service.generate_schedules",
        fake_generate_schedules,
    )

    with app.test_request_context("/"):
        session["_test_sid"] = "test-session-flags"
        session[SESSION_CONFIG_KEY] = fake_cfg

        generate_schedules_into_session(
            limit=1,
            optimizer_flags=["faculty_course", "same_room", "not_real_flag"],
        )

        schedules = session[SESSION_SCHEDULES_KEY]
        used_flags = schedules[0]["meta"]["optimizer_flags"]

        assert "faculty_course" in used_flags
        assert "same_room" in used_flags
        assert "not_real_flag" not in used_flags
        assert all(flag in KNOWN_OPTIMIZER_FLAGS for flag in used_flags)

        # Cleanup shared progress globals after test
        session_id = session["_test_sid"]
        generation_progress.pop(session_id, None)
        is_running.pop(session_id, None)


def test_generate_schedules_into_session_uses_config_flags_when_none_passed(
    monkeypatch,
):
    """
    Ensures config-defined optimizer flags are used when UI does not override them.
    """
    app = _make_app()

    fake_cfg = {
        "config": {
            "rooms": ["Roddy 140"],
            "labs": [],
            "courses": [],
            "faculty": [],
        },
        "optimizer_flags": ["faculty_room", "pack_rooms"],
    }

    def fake_generate_schedules(cfg, limit, optimize):
        """
        Fake generator returning one minimal schedule row.
        """
        yield [
            {
                "schedule_id": 1,
                "course_id": "CMSC 330.01",
                "day": "THU",
                "start": "10:00",
                "room": "Roddy 140",
                "faculty": "Xie",
                "lab": "",
                "duration": "110",
                "credits": "4",
                "meeting_index": 1,
            }
        ]

    monkeypatch.setattr(
        "app.web.services.run_service.generate_schedules",
        fake_generate_schedules,
    )

    with app.test_request_context("/"):
        session["_test_sid"] = "test-session-default-flags"
        session[SESSION_CONFIG_KEY] = fake_cfg

        generate_schedules_into_session(limit=1, optimizer_flags=None)

        schedules = session[SESSION_SCHEDULES_KEY]
        used_flags = schedules[0]["meta"]["optimizer_flags"]

        assert used_flags == ["faculty_room", "pack_rooms"]

        # Cleanup shared progress globals after test
        session_id = session["_test_sid"]
        generation_progress.pop(session_id, None)
        is_running.pop(session_id, None)


def test_generate_schedules_into_session_handles_empty_flag_list(monkeypatch):
    """
    Ensures an explicit empty optimizer flag list is respected.
    """
    app = _make_app()

    fake_cfg = {
        "config": {
            "rooms": ["Roddy 147"],
            "labs": [],
            "courses": [],
            "faculty": [],
        },
        "optimizer_flags": ["faculty_course"],
    }

    def fake_generate_schedules(cfg, limit, optimize):
        """
        Fake generator returning one minimal schedule row.
        """
        yield [
            {
                "schedule_id": 1,
                "course_id": "CMSC 152.01",
                "day": "MON",
                "start": "14:00",
                "room": "Roddy 147",
                "faculty": "Hardy",
                "lab": "",
                "duration": "50",
                "credits": "4",
                "meeting_index": 1,
            }
        ]

    monkeypatch.setattr(
        "app.web.services.run_service.generate_schedules",
        fake_generate_schedules,
    )

    with app.test_request_context("/"):
        session["_test_sid"] = "test-session-empty-flags"
        session[SESSION_CONFIG_KEY] = fake_cfg

        generate_schedules_into_session(limit=1, optimizer_flags=[])

        schedules = session[SESSION_SCHEDULES_KEY]
        used_flags = schedules[0]["meta"]["optimizer_flags"]

        assert used_flags == []

        # Cleanup shared progress globals after test
        session_id = session["_test_sid"]
        generation_progress.pop(session_id, None)
        is_running.pop(session_id, None)


def test_generate_schedules_into_session_releases_running_flag_on_error(monkeypatch):
    """
    Ensures the generator lock is released even when scheduler generation fails.

    This protects the app from getting stuck in a permanent
    'Generation already in progress' state after an exception.
    """
    app = _make_app()

    fake_cfg = {
        "config": {
            "rooms": ["Room A"],
            "labs": [],
            "courses": [],
            "faculty": [],
        },
        "optimizer_flags": [],
    }

    def broken_generate_schedules(cfg, limit, optimize):
        raise RuntimeError("Scheduler failed")

    monkeypatch.setattr(
        "app.web.services.run_service.generate_schedules",
        broken_generate_schedules,
    )

    with app.test_request_context("/"):
        session["_test_sid"] = "test-session-error-cleanup"
        session[SESSION_CONFIG_KEY] = fake_cfg

        try:
            generate_schedules_into_session(limit=1)
            assert False, "Expected scheduler failure"
        except RuntimeError:
            pass

        assert is_running[session["_test_sid"]] is False

        session_id = session["_test_sid"]
        generation_progress.pop(session_id, None)
        is_running.pop(session_id, None)


def test_generate_schedules_into_session_rejects_zero_limit():
    """
    Ensures generation rejects invalid limits before invoking the scheduler.
    """
    app = _make_app()

    with app.test_request_context("/"):
        session["_test_sid"] = "test-session-zero-limit"
        session[SESSION_CONFIG_KEY] = {
            "config": {
                "rooms": [],
                "labs": [],
                "courses": [],
                "faculty": [],
            }
        }

        try:
            generate_schedules_into_session(limit=0)
            assert False, "Expected ValueError for zero limit"
        except ValueError as exc:
            assert "limit must be greater than 0" in str(exc)

        session_id = session["_test_sid"]
        generation_progress.pop(session_id, None)
        is_running.pop(session_id, None)