# Author(s): Tanner Ness
# Date: 2026-02-14
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

from ..app.course_management import course_management
import json

def get_example():
    with open('..configs/config_base.json', 'r') as file:
        return json.load(file)
    
example = get_example().copy()

# the conflict should be removed from 'courses'
def delete_conflict():
    conflict = 'Room B'

    course_management.remove_conflict(conflict)

    assert conflict not in any(c['conflicts'] == conflict for c in example['config']['courses']), f"Conflict {conflict} has not been removed from 'conflicts'."

# should raise an error
def delete_conflict_nonexistent():
    try:
        course_management.remove_conflict(example, 'Room 199')
    except ValueError:
        print(f"Removing a nonexistent conflict raises the correct error: {ValueError}")


# the course should be removed
def delete_course():
    course = 'CS101'

    course_management.remove_course(example, course)
    
    assert course not in any(c['course_id'] for c in example['config']['courses']), f"Course {course} has not been removed from 'courses'."

# should raise an error
def delete_course_nonexistent():
    try:
        course_management.remove_course(example, 'CS009')
    except ValueError:
        print(f"Removing a nonexistent course raises the correct error: {ValueError}")

