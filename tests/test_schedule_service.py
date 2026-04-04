# Author: Antonio Corona
# Date: 2026-04-04
"""
test_schedule_service.py

Tests for schedule_service.py.

Purpose:
- Validate grouping logic used for viewer filtering
- Ensure view data structure is correctly constructed
- Confirm conflict detection runs without error

These are base-case tests designed to:
- Increase coverage
- Validate core data flow
- Catch regressions in grouping/filter behavior
"""

from app.web.app import create_app
from app.web.services.schedule_service import (
    _group_by,
    get_view_data,
    SESSION_SCHEDULES_KEY,
    SESSION_SELECTED_INDEX_KEY,
    SESSION_USER_SELECTED_KEY,
)


def test_group_by_basic():
    """
    Tests that grouping correctly organizes assignments by key.
    """
    assignments = [
        {"room": "A", "course_id": "C1"},
        {"room": "A", "course_id": "C2"},
        {"room": "B", "course_id": "C3"},
    ]

    grouped = _group_by(assignments, "room")

    assert "A" in grouped
    assert "B" in grouped
    assert len(grouped["A"]) == 2
    assert len(grouped["B"]) == 1


def test_group_by_lab_ignores_empty():
    """
    Ensures lab grouping ignores empty and placeholder values.
    """
    assignments = [
        {"lab": ""},
        {"lab": "None"},
        {"lab": "Mac"},
    ]

    grouped = _group_by(assignments, "lab")

    assert "Mac" in grouped
    assert "" not in grouped
    assert "None" not in grouped


def test_get_view_data_structure():
    """
    Validates that get_view_data returns expected keys used by the UI.

    Since get_view_data reads from Flask session, this test must run
    inside a request context and seed session state first.
    """
    app = create_app()

    fake_schedule = {
        "meta": {},
        "assignments": [
            {
                "course_id": "C1",
                "room": "A",
                "lab": "",
                "faculty": "Smith",
                "day": "MON",
                "start": "10:00",
                "duration": "50",
                "time": "MON 10:00",
                "credits": "3",
                "meeting_index": 1,
                "schedule_id": 1,
            }
        ],
    }

    with app.test_request_context("/viewer/"):
        from flask import session

        session[SESSION_SCHEDULES_KEY] = [fake_schedule]
        session[SESSION_SELECTED_INDEX_KEY] = 0
        session[SESSION_USER_SELECTED_KEY] = False

        result = get_view_data()

        assert "by_room" in result
        assert "by_lab" in result
        assert "by_faculty" in result
        assert "assignments" in result
        assert result["count"] == 1
        assert result["index"] == 0


def test_get_view_data_conflicts_flag():
    """
    Ensures conflict detection runs and returns a flag.

    This test seeds two overlapping assignments in the same room/day/time
    so the service has a chance to detect a conflict.
    """
    app = create_app()

    fake_schedule = {
        "meta": {},
        "assignments": [
            {
                "course_id": "C1",
                "room": "A",
                "faculty": "Smith",
                "lab": "",
                "day": "MON",
                "start": "10:00",
                "duration": "50",
                "time": "MON 10:00",
                "credits": "3",
                "meeting_index": 1,
                "schedule_id": 1,
            },
            {
                "course_id": "C2",
                "room": "A",
                "faculty": "Jones",
                "lab": "",
                "day": "MON",
                "start": "10:00",
                "duration": "50",
                "time": "MON 10:00",
                "credits": "3",
                "meeting_index": 1,
                "schedule_id": 1,
            },
        ],
    }

    with app.test_request_context("/viewer/"):
        from flask import session

        session[SESSION_SCHEDULES_KEY] = [fake_schedule]
        session[SESSION_SELECTED_INDEX_KEY] = 0
        session[SESSION_USER_SELECTED_KEY] = False

        result = get_view_data()

        assert "has_conflicts" in result
        assert result["has_conflicts"] is True