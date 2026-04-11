# Author(s): Antonio Corona, Tanner Ness, Ian Swartz
# Date: 2026-03-03
"""
test_faculty.py

Purpose:
    This test module verifies the correctness of the Faculty Management functionality
    implemented in the application layer. It ensures that faculty members can be added,
    modified, deleted, and assigned preferences within the scheduler configuration
    according to the project user stories (Chunk A — A1 Faculty Management).

Scope:
    - Add Faculty:
        Confirms that new faculty members are correctly inserted into the configuration
        with default or custom availability and appropriate course limits.

    - Modify Faculty:
        Confirms that existing faculty availability 
        and configuration details can be updated.

    - Manage Faculty Preferences:
        Confirms that course preferences can be added and stored correctly.

    - Delete Faculty:
        Confirms that faculty members can be removed 
        and no longer appear in the configuration.

Testing Strategy:
    - Uses temporary or test configuration files to avoid modifying real data.
    - Validates both successful operations and expected failure cases.
    - Ensures service-layer functions properly update and persist configuration data.

Related User Stories:
    A1.1 — Add Full-Time Faculty (Default Availability)
    A1.2 — Add Adjunct Faculty with Preferences
    A1.3 — Modify Faculty Availability
    A1.4 — Delete Faculty
"""

from typing import List

import pytest

from app.faculty_management import faculty_management

# ---------------------------
# Delete Faculty
# ---------------------------


def test_delete_faculty_member(example):
    """
    Removes an existing faculty member from the config.
    Ensure that a when a faculty member is removed:
    - They are removed from the top-level faculty list.
    - They are also removed from any course that referenced them.
    """

    # Pick an existing faculty member.
    name_to_delete = example["config"]["faculty"][0]["name"]

    faculty_management.remove_faculty(example, name_to_delete)

    assert not any(f["name"] == name_to_delete for f in example["config"]["faculty"])

    assert not any(f["faculty"] == name_to_delete for f in example["config"]["courses"])


def test_delete_faculty_member_nonexistent(example):
    """Ensures removing a faculty member that doesn't exist raises a ValueError."""
    with pytest.raises(ValueError):
        faculty_management.remove_faculty(example, "MR CBO")


# ---------------------------
# Add Faculty
# ---------------------------


# Add faculty tests
def test_add_faculty_full_time(example):
    """A1.1 — Add Full-Time Faculty (Default Availability)"""
    name = "Dr. Alice"

    # Ensure we don't collide with an existing faculty member.
    # If they already exist, tweak it slightly.
    if any(f["name"] == name for f in example["config"]["faculty"]):
        name = name + "(New)"

    faculty_management.add_faculty(example, name, "full-time")

    faculty_list = example["config"]["faculty"]
    # Check if name exists in any faculty dict.
    found = any(f["name"] == name for f in faculty_list)

    assert found, f"Faculty {name} was not added to the configuration."

    # Check defaults for Full-Time (12 max credits).
    new_fac = next(f for f in faculty_list if f["name"] == name)
    assert new_fac["maximum_credits"] == 12, (
        "Full-time faculty should have 12 max credits."
    )


def test_add_faculty_adjunct_with_prefs(example):
    """A1.2 — Add Adjunct Faculty with Preferences"""

    name = "Prof. Bob"

    # Ensure we don't collide with an existing faculty member.
    # If they already exist, tweak it slightly.
    if any(f["name"] == name for f in example["config"]["faculty"]):
        name = name + "(New)"

    # Preferences format expected by add_faculty based on your management file.
    test_prefs = [{"course_id": "CS101", "weight": 5}]

    faculty_management.add_faculty(example, name, "adjunct", prefs=test_prefs)

    faculty_list = example["config"]["faculty"]
    new_fac = next(f for f in faculty_list if f["name"] == name)

    assert new_fac["maximum_credits"] == 4, "Adjunct should have 4 max credits."
    assert new_fac["preferences"] == test_prefs, (
        "Preferences were not stored correctly."
    )


def test_add_faculty_same_name(example):
    """Ensures adding a duplicate name raises a ValueError"""

    test_prefs = [{"course_id": "CS101", "weight": 5}]

    with pytest.raises(ValueError):
        faculty_management.add_faculty(
            example, "Dr. Smith", "adjunct", prefs=test_prefs
        )


# ---------------------------
# Modify Faculty
# ---------------------------


def test_modify_faculty_member(example):
    """Set a new maximum credit limit for an existing faculty member."""
    name = example["config"]["faculty"][0]["name"]
    new_max_credits = 15

    # Avoid accidental collision with existing max credits.
    if example["config"]["faculty"][0]["maximum_credits"] == new_max_credits:
        new_max_credits += 1

    faculty_management.modify_faculty(example, name, maximum_credits=new_max_credits)


def test_modify_faculty_member_nonexistent(example):
    """Ensures modifying a faculty member that doesn't exist raises a ValueError."""
    with pytest.raises(ValueError):
        faculty_management.modify_faculty(example, "MR BOBBY", maximum_credits=10)


def test_modify_faculty_update_appointment_type(example):
    """
    Ensures updating a faculty member's appointment type updates all related defaults.
    """
    name = example["config"]["faculty"][0]["name"]

    faculty_management.modify_faculty(example, name, appointment_type="adjunct")

    faculty = next(f for f in example["config"]["faculty"] if f["name"] == name)

    assert faculty["maximum_credits"] == 4
    assert faculty["minimum_credits"] == 0
    assert faculty["unique_course_limit"] == 1


def test_modify_faculty_manual_credit_overrides(example):
    """Ensures manually overriding minimum_credits and unique_course_limit."""
    name = example["config"]["faculty"][0]["name"]
    new_min_credits = 8
    new_unique_limit = 3

    faculty_management.modify_faculty(
        example,
        name,
        minimum_credits=new_min_credits,
        unique_course_limit=new_unique_limit,
    )

    faculty = next(f for f in example["config"]["faculty"] if f["name"] == name)

    assert faculty["minimum_credits"] == new_min_credits, "Minimum credits not updated."
    assert faculty["unique_course_limit"] == new_unique_limit, (
        "Unique course limit not updated."
    )


def test_modify_faculty_update_availability(example):
    """Test updating a faculty member's availability."""
    name = example["config"]["faculty"][0]["name"]
    test_day = "MON"
    test_time_range = "13:00-16:00"

    faculty_management.modify_faculty(
        example, name, day=test_day, time_range=test_time_range
    )

    faculty = next(f for f in example["config"]["faculty"] if f["name"] == name)

    assert faculty["times"][test_day] == [test_time_range], (
        "Availability not updated correctly."
    )
    assert faculty["times"]["TUE"] == ["09:00-17:00"], (
        "Other days should keep defaults."
    )


def test_modify_faculty_replace_preferences(example):
    """Ensures replacing a faculty member's preferences."""
    name = example["config"]["faculty"][0]["name"]
    new_prefs = [
        {"course_id": "CS101", "weight": 9},
        {"course_id": "CS201", "weight": 4},
    ]

    faculty_management.modify_faculty(example, name, prefs=new_prefs)

    faculty = next(f for f in example["config"]["faculty"] if f["name"] == name)

    assert faculty["preferences"] == new_prefs


# ---------------------------
# Faculty default
# ---------------------------
def test_faculty_defaults_raises_error():
    """
    Ensures faculty_defaults raises a ValueError when given an unknown appointment type
    """
    with pytest.raises(ValueError):
        faculty_management.faculty_defaults("something")


# ---------------------------
# Faculty Build Time
# ---------------------------


def test_faculty_build_times_partial_raises_error():
    with pytest.raises(ValueError):
        """Ensures build_times raises a ValueError because of ambigutiy."""
        faculty_management.build_times("", "")


def test_faculty_build_times_invalid_day_raises_error():
    with pytest.raises(ValueError):
        """Ensures build_times raises a ValueError of invalid day."""
        faculty_management.build_times("something", "12-7")


def test_faculty_build_times_invalid_time_range_raises_error():
    with pytest.raises(ValueError):
        """Ensures build_times raises a ValueError because of invalid time."""
        faculty_management.build_times("WED", "128")


def test_faculty_build():
    """Ensures build_times returns a dict."""

    times = faculty_management.build_times("WED", "9:00-17:00")

    assert isinstance(times, dict)


# ---------------------------
# preference parser
# ---------------------------


def test_parse_prefs_none():
    """Ensures parse_prefs returns [] if no value passed"""
    prefs = faculty_management.parse_prefs("")
    assert prefs == []


def test_parse_prefs_no_colon():
    "Ensures parse_prefs raises a ValueError when there is no colon"
    with pytest.raises(ValueError):
        faculty_management.parse_prefs(["CS1208", "CS9991"])


def test_parse_prefs():
    "Ensures parse_prefs returns a list"
    prefs = faculty_management.parse_prefs(["CS101:8", "CS201:5"])
    assert isinstance(prefs, List)
