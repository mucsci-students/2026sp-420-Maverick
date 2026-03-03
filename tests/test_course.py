# Author(s): Antonio Corona, Tanner Ness, Ian Swartz, Jacob Karasow
# Date: 2026-03-03
"""
test_course.py

Purpose:
    This test module verifies the correctness of the Course Management functionality
    implemented in the application layer. It ensures that courses can be added,
    modified, deleted, and that course conflicts can be managed within the scheduler
    configuration according to the project user stories (Chunk A — A2 Course Management).

Scope:
    - Add Course:
        Confirms that new courses are correctly inserted into the configuration
        with credits and room assignments and can be listed afterward.

    - Modify Course:
        Confirms that existing course attributes (such as credits) can be updated
        and reflected in the configuration.

    - Manage Course Conflicts:
        Confirms that conflicts can be added, modified, and deleted between courses
        and that conflict relationships are stored correctly.

    - Delete Course:
        Confirms that courses can be removed and no longer appear in the configuration.

Testing Strategy:
    - Uses temporary or test configuration files to avoid modifying real data.
    - Validates both successful operations and expected failure cases.
    - Ensures service-layer functions properly update and persist configuration data.

Related User Stories:
    A2.1 — Add Course
    A2.2 — Modify Course
    A2.3 — Add Conflict
    A2.4 — Delete Course
    A2.5 — Modify Conflict
    A2.6 — Delete Conflict
"""

import pytest
from app.course_management import course_management


def test_delete_conflict(example):
    """Removes an existing conflict from the config."""

    course_to_remove_from = None
    conflict_to_remove = None

    # Picks an actual existing course and conflict.
    for course in example["config"]["courses"]:
        for conflict in course["conflicts"]:
            if conflict:
                course_to_remove_from = course["course_id"]
                conflict_to_remove = course["conflicts"][0]
                break
    
    course_management.remove_conflict(example, course_to_remove_from, conflict_to_remove)

    assert not any(c["conflicts"] == conflict_to_remove for c in example["config"]["courses"]), f"Conflict {conflict_to_remove} has not been removed from 'conflicts'."

def test_delete_conflict_nonexistent(example):
    """Ensures conflict that doesn't exist raises a ValueError."""
    
    # Pick an acutal existing course
    course = example["config"]["courses"][0]["course_id"]
    
    with pytest.raises(ValueError):
        course_management.remove_conflict(example, course, "ROOM 000")


def test_delete_course(example):
    """
    Ensures that when a course is removed:
    - It is removed from the top-level course_list.
    - It is removed from any course that referenced it.
    - It is removed from any faculty that referenced it.
    """

    # Pick an actual existing course.
    course = example["config"]["courses"][0]["course_id"]

    course_management.remove_course(example, course)
    
    assert not any(c["course_id"] == course for c in example["config"]["courses"]), f"Course {course} has not been removed from 'courses'."

    assert not any(course in c["course_preferences"] for c in example["config"]["faculty"]), f"Course {course} has not been removed from 'course_preferences'."

    assert not any(c["conflicts"] == course for c in example["config"]["courses"]), f"Conflict {course} has not been removed from 'conflicts'."


def test_delete_course_nonexistent(example):
    """Ensures removing a course that doesn't exist raises ValueError."""
    with pytest.raises(ValueError):
        course_management.remove_course(example, "Roddy 888")



def test_add_course_success(example):
    """A2.1 — Confirms new courses are correctly inserted with required fields."""
    
    # Test data.
    course_id = "CS420"
    credits = 3
    room = example["config"]["rooms"][0]

    # Ensure we don't collide with an existing course name.
    # If it already exists, tweak it slightly.
    for course in example["config"]["courses"]:
        for id in course["course_id"]:
            if id == course_id:
                course_id == course_id + "(New)"
                break

    course_management.add_course(example, course_id, credits, room)

    # Verify existence
    courses = example["config"]["courses"]
    new_course = next((c for c in courses if c["course_id"] == course_id), None)
    
    assert new_course is not None, f"Course {course_id} was not added."
    assert new_course['credits'] == credits, "Credits mismatch."
    assert isinstance(new_course['room'], list), "Room must be stored as a list."
    assert new_course['room'][0] == room

def test_add_course_duplicate(example):
    """Verifies that adding a duplicate ID raises a ValueError."""

    # Pick an actual existing course
    course_id = example["config"]["courses"][0]["course_id"]

    room = example["config"]["rooms"][0]

    with pytest.raises(ValueError):
        course_management.add_course(example, course_id, 3, room)

# The course credits should change
def test_modify_course(example):
    """changes the credits of an existing course and updates the config list."""

    # Pick an acutal existing course
    course = example["config"]["courses"][0]["course_id"]
    new_credits = 20

    course_management.modify_course(
        example, 
        course, 
        credits = new_credits
    )

    assert new_credits == example["config"]["courses"][0]["credits"]

def test_modify_course_nonexistent(example):
    """Ensures modifying a course that doesn't exist raises ValueError."""

    with pytest.raises(ValueError):
        course_management.modify_course(
            example, 
            'CS009', 
            credits = 4
        )
   