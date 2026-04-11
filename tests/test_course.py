# Author(s): Antonio Corona, Tanner Ness, Ian Swartz, Jacob Karasow
# Date: 2026-03-03
"""
test_course.py

Purpose:
    This test module verifies the correctness of the Course Management functionality
    implemented in the application layer. It ensures that courses can be added,
    modified, deleted, and that course conflicts can be managed within the scheduler
    configuration according to the project user stories 
    (Chunk A — A2 Course Management).

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

from typing import List

import pytest

from app.course_management import course_management

# ---------------------------
# Delete Conflict
# ---------------------------


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

    course_management.remove_conflict(
        example, course_to_remove_from, conflict_to_remove
    )

    assert not any(
        c["conflicts"] == conflict_to_remove for c in example["config"]["courses"]
    ), f"Conflict {conflict_to_remove} has not been removed from 'conflicts'."


def test_delete_conflict_nonexistent(example):
    """Ensures conflict that doesn't exist raises a ValueError."""

    # Pick an acutal existing course
    course = example["config"]["courses"][0]["course_id"]

    with pytest.raises(ValueError):
        course_management.remove_conflict(example, course, "ROOM 000")


def test_remove_conflict_success(example):
    """Ensures a conflict can be successfully removed."""

    conflict_id = "CS102"

    course_management.remove_conflict(example, "CS101", conflict_id, symmetric=False)

    course = example["config"]["courses"][0]

    assert conflict_id not in course["conflicts"]


def test_remove_conflict_nonexistent(example):
    """Ensures removing a non-existent conflict raises ValueError."""

    with pytest.raises(ValueError):
        course_management.remove_conflict(example, "CS101", "CS999", symmetric=False)


# ---------------------------
# Modify Conflict
# ---------------------------


def test_modify_conflict_success(example):
    """Ensures a conflict can be successfully modified."""

    course_id = "CS101"
    old_conflict_id = "CS102"
    new_conflict_id = "CS103"

    course_management.add_course(example, new_conflict_id, 4, "Room A")

    course = example["config"]["courses"][0]

    course_management.modify_conflict(
        example, course_id, old_conflict_id, new_conflict_id, symmetric=False
    )

    assert old_conflict_id not in course["conflicts"]
    assert new_conflict_id in course["conflicts"]


def test_modify_conflict_symmetric(example):
    """Ensures modify_conflict updates symmetric conflicts."""

    course_id = "CS101"
    old_conflict_id = "CS102"
    new_conflict_id = "CS103"

    course_management.add_course(example, new_conflict_id, 3, "Room A")

    course_management.modify_conflict(
        example, course_id, old_conflict_id, new_conflict_id, symmetric=True
    )

    old_course = example["config"]["courses"][0]
    new_course = example["config"]["courses"][3]

    assert course_id not in old_course["conflicts"]
    assert course_id in new_course["conflicts"]


def test_modify_conflict_self(example):
    """Ensures modifying to a self-conflict raises ValueError."""

    course_id = "CS101"

    with pytest.raises(ValueError):
        course_management.modify_conflict(
            example, course_id, "CS102", course_id, symmetric=False
        )


def test_modify_conflict_nonexistent_course(example):
    """Ensures modifying to nonexistent course raises ValueError."""

    with pytest.raises(ValueError):
        course_management.modify_conflict(
            example, "CS101", "CS102", "CS909", symmetric=False
        )


# ---------------------------
# Add Conflict
# ---------------------------


def test_add_conflict_success(example):
    """Ensures a conflict can be successfully added."""

    conflict_id = "CS102"

    course = example["config"]["courses"][0]
    course["conflicts"] = []

    course_management.add_conflict(example, "CS101", conflict_id, symmetric=False)

    assert conflict_id in course["conflicts"]


def test_add_conflict_symmetric(example):
    """Ensures add_conflict creates symmetric conflicts when symmetric=True."""

    course_id = "CS101"
    conflict_id = "CS102"

    course1 = example["config"]["courses"][0]
    course2 = example["config"]["courses"][2]

    course1["conflicts"] = []
    course2["conflicts"] = []

    course_management.add_conflict(example, course_id, conflict_id, symmetric=True)

    assert conflict_id in course1["conflicts"]
    assert course_id in course2["conflicts"]


def test_add_conflict_duplicate(example):
    """Ensures adding duplicate conflict raises ValueError."""

    with pytest.raises(ValueError):
        course_management.add_conflict(example, "CS101", "CS102", symmetric=False)


def test_add_conflict_self_conflict(example):
    """Ensures a course cannot conflict with itself."""

    course_id = "CS101"

    with pytest.raises(ValueError):
        course_management.add_conflict(example, course_id, course_id)


def test_add_conflict_nonexistent(example):
    """Ensures adding a conflict with nonexistent course raises ValueError."""

    course_id = "CS101"

    with pytest.raises(ValueError):
        course_management.add_conflict(example, course_id, "Bruh999")


# ---------------------------
# Delete Course
# ---------------------------


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

    assert not any(c["course_id"] == course for c in example["config"]["courses"]), (
        f"Course {course} has not been removed from 'courses'."
    )

    assert not any(
        course in c["course_preferences"] for c in example["config"]["faculty"]
    ), f"Course {course} has not been removed from 'course_preferences'."

    assert not any(c["conflicts"] == course for c in example["config"]["courses"]), (
        f"Conflict {course} has not been removed from 'conflicts'."
    )


def test_delete_course_nonexistent(example):
    """Ensures removing a course that doesn't exist raises ValueError."""
    with pytest.raises(ValueError):
        course_management.remove_course(example, "Roddy 888")


# ---------------------------
# Add Course
# ---------------------------


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
    new_course = None
    for c in courses:
        if c["course_id"] == course_id:
            new_course = c
            break

    assert new_course is not None, f"Course {course_id} was not added."
    assert new_course["credits"] == credits, "Credits mismatch."
    assert isinstance(new_course["room"], list), "Room must be stored as a list."
    assert new_course["room"][0] == room


def test_add_course_duplicate(example):
    """Verifies that adding a duplicate ID raises a ValueError."""

    # Pick an actual existing course
    course_id = example["config"]["courses"][0]["course_id"]

    room = example["config"]["rooms"][0]

    with pytest.raises(ValueError):
        course_management.add_course(example, course_id, 3, room)


def test_add_course_no_id(example):
    with pytest.raises(ValueError):
        course_management.add_course(example, "", 4, "Room A", "Lab 1", ["Dr. Smith"])


def test_add_course_negative_credits(example):
    with pytest.raises(ValueError):
        course_management.add_course(
            example, "CS999", -4, "Room A", "Lab 1", ["Dr. Smith"]
        )


def test_add_course_empty_room(example):
    with pytest.raises(ValueError):
        course_management.add_course(example, "CS777", 4, "", "Lab 1", ["Dr. Smith"])


def test_add_course_invalid_room(example):
    with pytest.raises(ValueError):
        course_management.add_course(
            example, "CS767", 4, "Room Z", "Lab 1", ["Dr. Smith"]
        )


def test_add_course_invalid_lab(example):
    with pytest.raises(ValueError):
        course_management.add_course(
            example, "CS901", 4, "Room A", "Lab 420", ["Dr. Smith"]
        )


def test_add_course_lab_wrapped(example):
    course_management.add_course(example, "CS901", 4, "Room A", "lab 2", ["Dr. Smith"])

    course = example["config"]["courses"][3]
    lab = course.get("lab")
    assert isinstance(lab, List)


def test_add_course_faculty_missing(example):
    with pytest.raises(ValueError):
        course_management.add_course(
            example, "CS901", 4, "Room A", "Lab 420", ["Dr. Argon"]
        )


def test_add_course_faculty_list_cleaned(example):
    """Ensures faculty list is cleaned of whitespace."""

    faculty = "Dr. Smith"
    course_management.add_course(
        example, "CS901", 4, "Room A", "lab 2", [" Dr. Smith  "]
    )

    course_faculty = example["config"]["courses"][3].get("faculty")
    assert faculty == course_faculty[0]


# ---------------------------
# Modify Course
# ---------------------------


# The course credits should change
def test_modify_course(example):
    """changes the credits of an existing course and updates the config list."""

    # Pick an acutal existing course
    course = example["config"]["courses"][0]["course_id"]
    new_credits = 20

    course_management.modify_course(example, course, credits=new_credits)

    assert new_credits == example["config"]["courses"][0]["credits"]


def test_modify_course_nonexistent(example):
    """Ensures modifying a course that doesn't exist raises ValueError."""

    with pytest.raises(ValueError):
        course_management.modify_course(example, "CS009", credits=4)


def test_modify_course_rename(example):
    """Ensures course can be renamed."""

    original_id = "CS101"
    new_id = "WEI"

    course_management.modify_course(example, original_id, new_course_id=new_id)

    found = None
    for c in example["config"]["courses"]:
        if c["course_id"] == new_id:
            found = c
            break
    assert found is not None


def test_modify_course_rename_duplicate(example):
    """Ensures renaming to already-existing course raises ValueError."""

    with pytest.raises(ValueError):
        course_management.modify_course(example, "CS102", "CS101")


def test_modify_course_update_credits(example):
    """Ensures credits can be updated."""

    new_credits = 5

    course_management.modify_course(example, "CS101", credits=new_credits)

    course = example["config"]["courses"][0]

    assert course["credits"] == new_credits


def test_modify_course_update_credits_invalid(example):
    """Ensures invalid credits raise ValueError."""

    with pytest.raises(ValueError):
        course_management.modify_course(example, "CS101", credits=-1)


def test_modify_course_update_room(example):
    """Ensures room can be updated."""

    new_room = "Room B"

    course_management.modify_course(example, "CS101", room=new_room)

    course = example["config"]["courses"][0]

    assert course["room"] == [new_room]


def test_modify_course_update_room_invalid(example):
    """Ensures invalid room raises ValueError."""

    with pytest.raises(ValueError):
        course_management.modify_course(example, "CS101", room="UMA")


def test_modify_course_replace_faculty_list_invalid(example):
    """Ensures invalid faculty names raise ValueError."""

    with pytest.raises(ValueError):
        course_management.modify_course(example, "CS101", faculty=["Dr. ROSEN"])


def test_modify_course_replace_conflict_list(example):
    """Ensures conflict list can be replaced."""

    course_management.add_course(example, "CS103", 3, example["config"]["rooms"][0])

    new_conflicts = ["CS102", "CS103"]

    course_management.modify_course(example, "CS101", conflicts=new_conflicts)

    course = example["config"]["courses"][0]
    assert course["conflicts"] == new_conflicts


def test_modify_course_replace_conflict_list_invalid(example):
    """Ensures invalid conflict courses raise ValueError."""

    with pytest.raises(ValueError):
        course_management.modify_course(example, "CS101", conflicts=["Chunkers"])


# ---------------------------
# Get faculty names
# ---------------------------


def test_get_faculty_names(example):
    """Ensures _get_faculty_names returns a list of names."""
    faculty_names = course_management._get_faculty_names(example)

    assert isinstance(faculty_names, list)

    for name in faculty_names:
        assert isinstance(name, str)


# ---------------------------
# Norm course id lower
# ---------------------------


def test_norm_course_id_lower():
    """Ensures _norm_course_id normalizes course IDs by stripping whitespace."""
    assert course_management._norm_course_id_lower("CS101") == "cs101"


# ---------------------------
# Get course
# ---------------------------


def test_get_course_raises_error(example):
    """Ensures _get_course raises ValueError for a nonexistent course."""
    with pytest.raises(ValueError):
        course_management._get_course(example, "CS999")


# ---------------------------
# Ensure conflicts list
# ---------------------------


def test_ensure_conflicts_list_none(example):
    """
    Ensures _ensure_conflicts_list creates empty conflicts list if missing 
    and returns it.
    """
    course = {"course_id": "CS101"}

    conflicts = course_management._ensure_conflicts_list(course)

    assert conflicts == []


def test_ensure_conflicts_list_raises_error():
    """Ensures _ensure_conflicts_list raises value error if not a list"""
    course = {
        "course_id": "TEST101",
        "conflicts": {"CS102": "something", "CS103": "something2"},
    }

    with pytest.raises(ValueError):
        course_management._ensure_conflicts_list(course)


# ---------------------------
# Remove Course Helper
# ---------------------------


def test_remove_course_helper_removes_from_conflicts(example):
    """Ensures remove_course_helper removes course from conflict lists."""

    course_to_remove = "CS102"

    course_management.remove_course_helper(example, course_to_remove)

    for course in example["config"]["courses"]:
        assert course_to_remove not in course["conflicts"]


def test_remove_course_helper_removes_from_faculty_preferences(example):
    """Ensures remove_course_helper removes course from faculty preferences."""

    course_to_remove = "CS101"
    faculty = example["config"]["faculty"][0]

    course_management.remove_course_helper(example, course_to_remove)

    prefs = faculty.get("course_preferences")

    assert course_to_remove not in prefs
