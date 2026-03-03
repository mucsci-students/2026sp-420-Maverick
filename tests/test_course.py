# Author(s): Antonio Corona, Tanner Ness, Ian Swartz, Jacob Karasow
# Date: 2026-03-02
"""
test_course.py

Purpose:
    This test module verifies the correctness of the Course Management functionality
    implemented in the application layer. It ensures that courses can be added,
    modified, deleted, and that course conflicts can be managed within the scheduler
    configuration according to the project user stories (Chunk A — A2 Course Management).

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

import pytest
from app.course_management import course_management


# the conflict should be removed from 'courses'
def delete_conflict():

    example = copy.deepcopy(get_example())

    conflict = 'Room B'

    course_management.remove_conflict(conflict)

    assert conflict not in any(c['conflicts'] == conflict for c in example['config']['courses']), f"Conflict {conflict} has not been removed from 'conflicts'."

# should raise an error
def delete_conflict_nonexistent():

    example = copy.deepcopy(get_example())

    try:
        course_management.remove_conflict(example, 'Room 199')
    except ValueError:
        print(f"Removing a nonexistent conflict raises the correct error: {ValueError}")


# the course should be removed
def delete_course():

    example = copy.deepcopy(get_example())

    course = 'CS101'

    course_management.remove_course(example, course)
    
    assert course not in any(c['course_id'] for c in example['config']['courses']), f"Course {course} has not been removed from 'courses'."

# should raise an error
def delete_course_nonexistent():

    example = copy.deepcopy(get_example())
    
    try:
        course_management.remove_course(example, 'CS009')
    except ValueError:
        print(f"Removing a nonexistent course raises the correct error: {ValueError}")



# Add course test
def test_add_course_success():
    """A2.1 — Confirms new courses are correctly inserted with required fields."""
    example = get_example() # Get a fresh copy for this test
    
    # Test data - Ensure 'Roddy 145' exists in your config_base.json rooms list
    course_id = "CS420"
    credits = 3
    room = "Roddy 145" 

    course_management.add_course(example, course_id, credits, room)

    # Verify existence
    courses = example['config']['courses']
    new_course = next((c for c in courses if c['course_id'] == course_id), None)
    
    assert new_course is not None, f"Course {course_id} was not added."
    assert new_course['credits'] == credits, "Credits mismatch."
    assert isinstance(new_course['room'], list), "Room must be stored as a list."
    assert new_course['room'][0] == room
    print(f"PASSED: test_add_course_success")

def test_add_course_duplicate():
    """Verifies that adding a duplicate ID raises a ValueError."""
    example = get_example()
    course_id = "CS101" # Assuming CS101 is already in your base config
    
    try:
        # Attempt to add a course that likely already exists
        course_management.add_course(example, course_id, 3, "Roddy 145")
        assert False, "Should have raised ValueError for duplicate ID."
    except ValueError:
        print(f"PASSED: test_add_course_duplicate (Correctly blocked)")

# The course credits should change
def modify_course():
    course = 'CS101'
    new_credits = 5

    course_management.modify_course(
        Example, 
        course, 
        credits = new_credits
    )

# Should raise an error
def modify_course_nonexistent():
    try:
        course_management.modify_course(
            Example, 
            'CS009', 
            credits = 4
        )
    except ValueError:
        print("Modifying a nonexistent course raises the correct error.")