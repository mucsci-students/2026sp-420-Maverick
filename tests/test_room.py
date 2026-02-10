# Author: 
# Date: <yyyy-mm-dd>
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