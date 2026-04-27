# Author: Antonio Corona, Ian Swartz
# Date: 2026-04-05
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

import pytest
from flask import session

from app.web.app import create_app
from app.web.services.schedule_service import (
    SESSION_SCHEDULES_KEY,
    SESSION_SELECTED_INDEX_KEY,
    SESSION_USER_SELECTED_KEY,
    _check_for_conflicts,
    _group_by,
    export_schedules_to_csv,
    get_view_data,
    is_export_enabled,
    is_valid_file,
    next_schedule,
    prev_schedule,
    select_schedule,
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


def test_navigation_clamping(app):
    with app.test_request_context():
        session[SESSION_SCHEDULES_KEY] = [{"meta": {}}, {"meta": {}}]
        session[SESSION_SELECTED_INDEX_KEY] = 0

        next_schedule()
        assert session[SESSION_SELECTED_INDEX_KEY] == 1

        next_schedule()
        assert session[SESSION_SELECTED_INDEX_KEY] == 1

        prev_schedule()
        assert session[SESSION_SELECTED_INDEX_KEY] == 0

        prev_schedule()
        assert session[SESSION_SELECTED_INDEX_KEY] == 0


def test_select_schedule_bounds(app):
    with app.test_request_context():
        session[SESSION_SCHEDULES_KEY] = [{"meta": {}}, {"meta": {}}]

        select_schedule(10)
        assert session[SESSION_SELECTED_INDEX_KEY] == 1


def test_csv_export_format(app):
    with app.test_request_context():
        session[SESSION_SCHEDULES_KEY] = [
            {"assignments": [{"course_id": "CS101", "room": "101", "time": "10:00"}]}
        ]

        csv_out = export_schedules_to_csv([0])
        assert "Schedule #,Course ID,Faculty,Room,Lab,Time" in csv_out
        assert "CS101" in csv_out


def test_validation_error(app):
    bad_data = [
        {
            "meta": {"generated_at": "now", "row_count": 1, "schedule_id": 1},
            "assignments": [{"room": "101"}],
        }
    ]

    with pytest.raises(ValueError) as excinfo:
        is_valid_file(bad_data)
    assert "Invalid file" in str(excinfo.value)


def test_group_by_handles_none_and_missing_keys():
    assignments = [
        {"room": None},
        {},
        {"room": " A "},
    ]

    grouped = _group_by(assignments, "room")

    assert "A" in grouped
    assert len(grouped["A"]) == 1


def test_group_by_skips_blank_strings():
    assignments = [
        {"faculty": ""},
        {"faculty": "   "},
        {"faculty": "Smith"},
    ]

    grouped = _group_by(assignments, "faculty")

    assert "Smith" in grouped
    assert len(grouped) == 1


def test_no_conflict_different_days():
    assignments = [
        {"day": "MON", "start": "10:00", "duration": "60"},
        {"day": "TUE", "start": "10:00", "duration": "60"},
    ]

    assert _check_for_conflicts(assignments) is False


def test_conflict_partial_overlap():
    assignments = [
        {"day": "MON", "start": "10:00", "duration": "60"},
        {"day": "MON", "start": "10:30", "duration": "60"},
    ]

    assert _check_for_conflicts(assignments) is True


def test_conflict_invalid_time_data_graceful():
    assignments = [
        {"day": "MON", "start": "bad", "duration": "60"},
        {"day": "MON", "start": "10:00", "duration": "60"},
    ]

    # Should not crash
    result = _check_for_conflicts(assignments)
    assert result in [True, False]


def test_select_schedule_sets_user_selected(app):
    with app.test_request_context():
        session[SESSION_SCHEDULES_KEY] = [{}, {}]

        select_schedule(0)

        assert session[SESSION_USER_SELECTED_KEY] is True


def test_export_enabled_flag(app):
    with app.test_request_context():
        session[SESSION_SCHEDULES_KEY] = []
        assert is_export_enabled() is False

        session[SESSION_SCHEDULES_KEY] = [{}]
        assert is_export_enabled() is True
