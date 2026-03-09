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
        Confirms that existing faculty availability and configuration details can be updated.

    - Manage Faculty Preferences:
        Confirms that course preferences can be added and stored correctly.

    - Delete Faculty:
        Confirms that faculty members can be removed and no longer appear in the configuration.

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

    assert not any(f["name"] == name_to_delete for f in example["config"]["faculty"] )

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
    assert new_fac["maximum_credits"] == 12, "Full-time faculty should have 12 max credits."

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
    assert new_fac["preferences"] == test_prefs, "Preferences were not stored correctly."

# ---------------------------
# Modify Faculty
# ---------------------------

def test_modify_faculty_member(example):
    """Set a new maximum credit limit for an existing faculty member."""
    name = example["config"]["faculty"][0]['name']
    new_max_credits = 15

    # Avoid accidental collision with existing max credits.
    if example["config"]["faculty"][0]["maximum_credits"] == new_max_credits:
        new_max_credits += 1

    faculty_management.modify_faculty(
        example,
        name,
        maximum_credits=new_max_credits
    )

def test_modify_faculty_member_nonexistent(example):
    """Ensures modifying a faculty member that doesn't exist raises a ValueError."""
    with pytest.raises(ValueError):
        faculty_management.modify_faculty(
            example,
            "MR BOBBY",
            maximum_credits=10
        )