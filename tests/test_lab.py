# Author: 
# Date: <yyyy-mm-dd>
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
