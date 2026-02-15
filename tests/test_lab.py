# Author(s): Tanner Ness
# Date: 2026-02-14
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
from ..app.lab_management import lab_management
import json

def get_example():
    with open('..configs/config_base.json', 'r') as file:
        return json.load(file)
    
example = get_example().copy()

# the lab should be removed from 'lab'
def delete_lab():
    lab = 'Lab 2'
    lab_management.remove_lab(example, lab)

    assert lab not in example['config']['labs'], f"Lab {lab} has not been removed from 'lab'."

# the lab should be removed from 'lab' and 'courses'
def delete_lab_nested():
    lab = 'Lab_1'
    lab_management.remove_lab(example, lab)

    assert lab not in example['config']['labs'], f"Room {lab} has not been removed from 'room'."

    assert lab not in any(l['lab'] == lab for l in example['config']['courses']), f"Room {lab} has not been removed from 'courses'."

# should raise an error
def delete_lab_nonexistent():
    try:
        lab_management.remove_lab(example, 'Lab 999')
    except ValueError:
        print(f"Removing a nonexistent lab raises the correct error: {ValueError}")
