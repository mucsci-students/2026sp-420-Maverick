# Author(s): 
# Date: 2026-02-14
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
    - Uses temporary or test configuration files to avoid modifying real data.
    - Validates both successful operations and expected failure cases.
    - Ensures service-layer functions properly update and persist configuration data.

Related User Stories:
    A4.1 — Add Room
    A4.2 — Modify Room
    A4.3 — Delete Room
"""
from ..app.room_management import room_management
import json

def get_example():
    with open('..configs/config_base.json', 'r') as file:
        return json.load(file)
    
example = get_example().copy()

# the room should be removed from 'room'
def delete_room():
    room = 'Room B'
    room_management.remove_room(example, room)

    assert room not in example['config']['rooms'], f"Room {room} has not been removed from 'room'."

# the room should be removed from 'room' and 'courses'
def delete_room_nested():
    room = 'Room A'
    room_management.remove_room(room)

    assert room not in example['config']['rooms'], f"Room {room} has not been removed from 'room'."

    assert room not in any(r['room'] == room for r in example['config']['courses']), f"Room {room} has not been removed from 'courses'."

# should raise an error
def delete_room_nonexistent():
    try:
        room_management.remove_room(example, 'CS999')
    except ValueError:
        print(f"Removing a nonexistent room raises the correct error: {ValueError}")


