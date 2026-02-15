# Author(s): Tanner Ness
# Date: 2026-02-14
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
from ..app.faculty_management import faculty_management
import json

def get_example():
    with open('..configs/config_base.json', 'r') as file:
        return json.load(file)
    
example = get_example().copy()

# the faculty member should be removed from 'faculty' and 'courses'
def delete_faculty_member():
    name = 'Dr. Smith'
    faculty_management.remove_faculty(example, name)

    assert name not in any(f['name'] == name for f in example['config']['faculty'] ), f"Faculty {name} has not been removed from 'faculty'."

    assert name not in any(f['faculty'] == name for f in example['config']['courses']), f"Faculty {name} has not been removed from 'courses'."

# should raise an error
def delete_faculty_member_nonexistent():
    try:
        faculty_management.remove_faculty(example, 'MR CBO')
    except ValueError:
        print(f"Removing a nonexistent faculty members raises the correct error: {ValueError}")
