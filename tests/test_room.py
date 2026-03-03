# Author(s): Antonio Corona, Tanner Ness, Ian Swartz, Jacob Karasow
# Date: 2026-03-02
"""
test_room.py

Purpose:
    This test module verifies the correctness of the Room Management functionality
    implemented in the application layer. It ensures that rooms can be added,
    modified (renamed), and deleted from the scheduler configuration according
    to the project user stories (Chunk A — A4 Room Management).

Scope:
    - Add Room:
        Confirms that new rooms are correctly inserted into the configuration
        and can be listed afterward.

    - Modify Room:
        Confirms that existing rooms can be renamed and that the configuration
        reflects the updated room name while removing the old one.

    - Delete Room:
        Confirms that rooms can be removed and no longer appear in the configuration.

Testing Strategy:
    - Uses a fresh deep-copied base configuration for each test (pytest fixture)
      to avoid modifying real data.
    - Validates both successful operations and expected failure cases.

Related User Stories:
    A4.1 — Add Room
    A4.2 — Modify Room
    A4.3 — Delete Room
"""
import pytest
from app.room_management import room_management


# ---------------------------
# Delete Room
# ---------------------------

def test_delete_room(example):
    """Removes an existing room from config."""
    room_to_delete = example["config"]["rooms"][0]

    room_management.remove_room(example, room_to_delete)

    assert room_to_delete not in example["config"]["rooms"]

def test_delete_room_nested(example):
    """
    Ensures that when a room is removed:
    - It is removed from the top-level rooms list
    - It is removed from any course that referenced it
    """

    # Pick an actual existing room
    room = example["config"]["rooms"][0]

    # Make sure at least one course references this room (if none do,
    # manually assign it to the first course to test nested behavior)
    if example["config"]["courses"]:
        example["config"]["courses"][0]["room"] = [room]

    # Perform deletion
    room_management.remove_room(example, room)

    # Assert room removed from main room list
    assert room not in example["config"]["rooms"]

    # Assert room removed from all courses
    for course in example["config"]["courses"]:
        assert room not in course.get("room", [])

def test_delete_room_nonexistent(example):
    """Ensures removing a room that doesn't exist raises ValueError."""
    with pytest.raises(ValueError):
        room_management.remove_room(example, "Room 999")

# ---------------------------
# Add Room
# ---------------------------

def test_add_room(example):
    """A4.1 — Confirms new rooms are correctly inserted."""
    room_name = "Roddy 300"
    
    # Ensure we don't collide with an existing room name.
    # If it already exists, tweak it slightly.
    if room_name in example["config"]["rooms"]:
        room_name = room_name + " (New)"

    room_management.add_room(example, room_name)

    assert room_name in example["config"]["rooms"], f"Room '{room_name}' was not added."

def test_add_room_duplicate(example):
    """Ensures adding an existing room raises a ValueError."""
    existing_room = example["config"]["rooms"][0]

    with pytest.raises(ValueError):
        room_management.add_room(example, existing_room)


# ---------------------------
# Modify Room
# ---------------------------

def test_modify_room(example):
    """Renames an existing room and updates the config list."""
    old_room = example["config"]["rooms"][0]
    new_room = "Room Z"

    # Avoid accidental collision if "Room Z" already exists.
    if new_room in example["config"]["rooms"]:
        new_room = "Room Z (Renamed)"

    room_management.modify_room(
        example, 
        old_room, 
        new_room
    )

    assert new_room in example["config"]["rooms"]
    assert old_room not in example["config"]["rooms"]

def test_modify_room_nonexistent(example):
    """Ensures renaming a room that doesn't exist raises ValueError."""
    with pytest.raises(ValueError):
        room_management.modify_room(example, "Room 999", "Room X")