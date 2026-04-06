# Author(s): Antonio Corona, Tanner Ness, Ian Swartz, Jacob Karasow
# Date: 2026-03-03
"""
test_lab.py

Purpose:
    This test module verifies the correctness of the Lab Management functionality
    implemented in the application layer. It ensures that labs can be added,
    modified (renamed), and deleted from the scheduler configuration according
    to the project user stories (Chunk A — A3 Lab Management).

Scope:
    - Add Lab:
        Confirms that new labs are correctly inserted into the configuration
        and can be listed afterward.

    - Modify Lab:
        Confirms that existing labs can be renamed and that the configuration
        reflects the updated lab name while removing the old one.

    - Delete Lab:
        Confirms that labs can be removed and no longer appear in the configuration.

Testing Strategy:
    - Uses temporary or test configuration files to avoid modifying real data.
    - Validates both successful operations and expected failure cases.
    - Ensures service-layer functions properly update and persist configuration data.

Related User Stories:
    A3.1 — Add Lab
    A3.2 — Modify Lab
    A3.3 — Delete Lab
"""

import pytest
from app.lab_management import lab_management


# ---------------------------
# Delete Lab
# ---------------------------


def test_delete_lab(example):
    """Removes an existing lab from the config."""
    lab_to_delete = example["config"]["labs"][0]

    lab_management.remove_lab(example, lab_to_delete)

    assert lab_to_delete not in example["config"]["labs"]


def test_delete_lab_nested(example):
    """
    Ensures that when a lab is removed:
    - It is removed from the top-level 'labs' list.
    - It is also removed from any course taht references it.
    """

    # Pick an actual existing lab.
    lab = example["config"]["labs"][0]

    # Make sure at least one course references this lab (if none do,
    # Manually assign it to the first course to test nested behavior).
    if example["config"]["courses"][0]:
        example["config"]["courses"][0]["lab"] = [lab]

    # Perform deletion.
    lab_management.remove_lab(example, lab)

    # Assert lab removed from main lab list.
    assert lab not in example["config"]["labs"]

    # Assert lab removed from all courses.
    for course in example["config"]["courses"]:
        assert lab not in course.get("lab", [])


def test_delete_lab_nonexistent(example):
    """Ensures removing a lab that doesn't exist raises a ValueError."""
    with pytest.raises(ValueError):
        lab_management.remove_lab(example, "Lab 121")


# ---------------------------
# Add Lab
# ---------------------------


def test_add_lab(example):
    """A3.1 — Confirms new labs are correctly inserted."""
    lab_name = "Digital Media Lab"

    # Ensure we don't collide with an exisiting lab name.
    # If it already exists, tweak it slightly.]
    if lab_name in example["config"]["labs"]:
        lab_name = lab_name + "(New)"

    lab_management.add_lab(example, lab_name)

    assert lab_name in example["config"]["labs"], f"Lab {lab_name} was not added."


def test_add_lab_duplicate(example):
    """Ensures adding an existing lab raises a ValueError."""

    existing_lab = example["config"]["labs"][0]

    with pytest.raises(ValueError):
        lab_management.add_lab(example, existing_lab)


# ---------------------------
# Modify Lab
# ---------------------------


def test_modify_lab(example):
    """Renames an existing lab and updates the config list."""

    old_lab = example["config"]["labs"][0]
    new_lab = "Lab X"

    lab_management.modify_lab(example, old_lab, new_lab)

    assert new_lab in example["config"]["labs"]
    assert old_lab not in example["config"]["labs"]


def test_modify_lab_nonexistent(example):
    """Ensures renaming lab that does not exist raises a ValueError."""
    with pytest.raises(ValueError):
        lab_management.modify_lab(example, "Lab 121", "Lab XYZ")


def test_modify_lab_same_name(example):
    """Ensures renaming a lab to the same name raises a ValueError"""
    with pytest.raises(ValueError):
        lab_management.modify_lab(example, "Lab 1", "Lab 1")
