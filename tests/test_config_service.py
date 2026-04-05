# Author: Tanner Ness, Ian Swartz
# Date: 2026-04-05

import pytest
from flask import session
from app.web.services.config_service import (
    load_config_into_session,
    get_config_status,
    sanitize_export_filename,
    detect_conflicts,
    validate_config,
    add_faculty_service,
    get_unsaved,
)

def test_load_existing_configuration(app_context, repo_root):
    """Ensures a config can be loaded."""

    path = repo_root / "configs" /"config_test.json"

    load_config_into_session(path)
     
    status = get_config_status()
    assert status["loaded"] is True


def test_sanitize_filename(app_context):
    assert sanitize_export_filename("my_config") == "my_config.json"
    assert sanitize_export_filename("  spacey  ") == "spacey.json"
    assert sanitize_export_filename("/etc/passwd") == "passwd.json"
    assert sanitize_export_filename("") == "new_config_file.json"


def test_detect_duplicate_faculty():
    cfg = {
        "config": {
            "faculty": [{"name": "Dr. Smith"}, {"name": "Dr. Smith"}],
            "rooms": [],
            "labs": []
        }
    }
    conflicts = detect_conflicts(cfg)
    assert len(conflicts) == 1
    assert "Duplicate faculty name: Dr. Smith" in conflicts[0]


def test_detect_missing_names():
    cfg = {
        "config": {
            "faculty": [{"name": ""}], # Missing name
            "rooms": [],
            "labs": []
        }
    }
    conflicts = detect_conflicts(cfg)
    assert "Faculty member with missing name." in conflicts


def test_validate_config_invalid_room():
    cfg = {
        "config": {
            "faculty": [{"name": "Smith"}],
            "rooms": [{"name": "Room A"}],
            "labs": [],
            "courses": [{
                "course_id": "CS101",
                "credits": 3,
                "room": ["Room Z"], # Room Z doesn't exist in 'rooms'
                "faculty": ["Smith"]
            }]
        }
    }
    with pytest.raises(ValueError, match="Invalid room 'Room Z'"):
        validate_config(cfg)


def test_faculty_service_updates_session(app_context):
    with app_context.test_request_context():
        session["working_config"] = {"config": {"faculty": []}, "limit": 3}
        
        add_faculty_service(name="New Faculty", appointment_type="Full-Time")
        
        assert get_unsaved() is True
        assert len(session["working_config"]["config"]["faculty"]) == 1
        assert session["working_config"]["config"]["faculty"][0]["name"] == "New Faculty"
        