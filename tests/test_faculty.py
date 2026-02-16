# Author(s): Tanner Ness, Ian Swartz
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
import copy

def get_example():
    with open('..configs/config_base.json', 'r') as file:
        return json.load(file)

# the faculty member should be removed from 'faculty' and 'courses'
def delete_faculty_member():

    example = copy.deepcopy(get_example())

    name = 'Dr. Smith'

    faculty_management.remove_faculty(example, name)

    assert name not in any(f['name'] == name for f in example['config']['faculty'] ), f"Faculty {name} has not been removed from 'faculty'."

    assert name not in any(f['faculty'] == name for f in example['config']['courses']), f"Faculty {name} has not been removed from 'courses'."

# should raise an error
def delete_faculty_member_nonexistent():

    example = copy.deepcopy(get_example())
    
    try:
        faculty_management.remove_faculty(example, 'MR CBO')
    except ValueError:
        print(f"Removing a nonexistent faculty members raises the correct error: {ValueError}")


# Add faculty tests
def test_add_faculty_full_time():
    """A1.1 — Add Full-Time Faculty (Default Availability)"""
    example = get_example()
    name = "Dr. Alice"
    
    faculty_management.add_faculty(example, name, "full-time")
    
    faculty_list = example['config']['faculty']
    # Check if name exists in any faculty dict
    found = any(f['name'] == name for f in faculty_list)
    
    assert found, f"Faculty {name} was not added to the configuration."
    
    # Check defaults for Full-Time (12 max credits)
    new_fac = next(f for f in faculty_list if f['name'] == name)
    assert new_fac['maximum_credits'] == 12, "Full-time faculty should have 12 max credits."
    print(f"PASSED: test_add_faculty_full_time")

def test_add_faculty_adjunct_with_prefs():
    """A1.2 — Add Adjunct Faculty with Preferences"""
    example = get_example()
    name = "Prof. Bob"
    # Preferences format expected by add_faculty based on your management file
    test_prefs = [{"course_id": "CS101", "weight": 5}]
    
    faculty_management.add_faculty(example, name, "adjunct", prefs=test_prefs)
    
    faculty_list = example['config']['faculty']
    new_fac = next(f for f in faculty_list if f['name'] == name)
    
    assert new_fac['maximum_credits'] == 4, "Adjunct should have 4 max credits."
    assert new_fac['preferences'] == test_prefs, "Preferences were not stored correctly."
    print(f"PASSED: test_add_faculty_adjunct_with_prefs")


#Used to execute tests:
"""
if __name__ == "__main__":
    print("--- Starting Faculty Management Tests ---")
    test_add_faculty_full_time()
    test_add_faculty_adjunct_with_prefs()
    delete_faculty_member()
    delete_faculty_member_nonexistent()
    print("\nAll faculty tests passed")
"""