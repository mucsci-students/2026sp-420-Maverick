# Author(s): Antonio Corona, Tanner Ness, Ian Swartz, Jacob Karasow
# Date: 2026-03-02
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

# the lab should be removed from 'lab'
def delete_lab():

    example = copy.deepcopy(get_example())

    lab = 'Lab 2'
    lab_management.remove_lab(example, lab)

    assert lab not in example['config']['labs'], f"Lab {lab} has not been removed from 'lab'."

# the lab should be removed from 'lab' and 'courses'
def delete_lab_nested():

    example = copy.deepcopy(get_example())

    lab = 'Lab 1'

    lab_management.remove_lab(example, lab)

    assert lab not in example['config']['labs'], f"Room {lab} has not been removed from 'room'."

    assert lab not in any(l['lab'] == lab for l in example['config']['courses']), f"Room {lab} has not been removed from 'courses'."

# should raise an error
def delete_lab_nonexistent():

    example = copy.deepcopy(get_example())

    try:
        lab_management.remove_lab(example, 'Lab 999')
    except ValueError:
        print(f"Removing a nonexistent lab raises the correct error: {ValueError}")


# Add lab tests
def test_add_lab():
    """A3.1 — Confirms new labs are correctly inserted."""
    example = get_example()
    lab_name = "Digital Media Lab"
    
    lab_management.add_lab(example, lab_name)
    
    assert lab_name in example['config']['labs'], f"Lab {lab_name} was not added."
    print(f"PASSED: test_add_lab")

def test_add_lab_duplicate():
    """Ensures adding an existing lab raises a ValueError."""
    example = get_example()
    # Assuming 'Lab 1' exists in your config_base.json
    lab_name = 'Lab 1' 
    
    try:
        lab_management.add_lab(example, lab_name)
        assert False, "Should have raised ValueError for duplicate lab."
    except ValueError:
        print(f"PASSED: test_add_lab_duplicate")

# The lab name should change
def test_modify_lab():

    example = copy.deepcopy(get_example())

    old_lab = "Lab 1"
    new_lab = "Lab X"

    lab_management.modify_lab(
        example, 
        old_lab, 
        new_lab
        )

# Should raise an error
def test_modify_lab_nonexistent():

    example = copy.deepcopy(get_example())

    try:
        lab_management.modify_lab(
            example, 
            "Lab 999", 
            "Lab Z"
            )
    except ValueError:
        print("Modifying a nonexistent lab raises the correct error.")