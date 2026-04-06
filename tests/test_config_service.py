# Author: Tanner Ness, Ian Swartz
# Date: 2026-04-05

import pytest
import json
from flask import session
from app.web.services.config_service import (
    load_config_into_session,
    get_config_status,
    sanitize_export_filename,
    detect_conflicts,
    validate_config,
    add_faculty_service,
    get_unsaved,
    clear_config,
    SESSION_CONFIG_KEY,
    export_config_bytes,
    set_faculty_day_unavailable_service,
    add_room_service,
    add_lab_service,
    add_course_service,
    save_config_from_session,
    update_schedules,
    remove_faculty_service,
    remove_room_service,
    remove_course_service,
    modify_room_service,
    modify_faculty_service,
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


def test_sanitize_filename_edge_cases(app_context):
    assert sanitize_export_filename("../../../") == "new_config_file.json"
    assert sanitize_export_filename("...") == "....json"


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
            "faculty": [{"name": ""}],
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
                "room": ["Room Z"],
                "faculty": ["Smith"]
            }]
        },
        "time_slot_config": {
            "days": ["MON", "TUE", "WED", "THU", "FRI"],
            "time_slots": {
                "MON": [{"start_time": "08:00", "end_time": "09:00"}],
                "TUE": [], "WED": [], "THU": [], "FRI": []
            }
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


def test_clear_config(app_context):
    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {"some": "data"}
        
        clear_config()
        
        assert SESSION_CONFIG_KEY not in session
        status = get_config_status()
        assert status["loaded"] is False


def test_export_config_bytes(app_context):
    with app_context.test_request_context():
        cfg = {
            "config": {
                "faculty": []}, 
                "limit": 3, 
                "time_slot_config": {
                    "days": ["MON", "TUE", "WED", "THU", "FRI"],
                    "time_slots": {
                        "MON": [{"start_time": "08:00", "end_time": "09:00"}],
                        "TUE": [], "WED": [], "THU": [], "FRI": []
                    }
                }
            }
        session[SESSION_CONFIG_KEY] = cfg

        payload, filename = export_config_bytes("my_export")

        assert filename == "my_export.json"
        assert isinstance(payload, bytes)
        exported_data = json.loads(payload.decode("utf-8"))
        assert exported_data["limit"] == 3


def test_detect_room_lab_conflicts():
    cfg = {
        "config": {
            "faculty": [],
            "rooms": [{"name": "101"}, {"name": "101"}],
            "labs": [{"name": "Lab A"}, {"name": ""}],
        }
    }
    conflicts = detect_conflicts(cfg)
    assert "Duplicate room name: 101" in conflicts
    assert "Lab with missing name." in conflicts


def test_validate_config_invalid_credits():
    cfg = {
        "config": {
            "faculty": [], "rooms": [], "labs": [],
            "courses": [{"course_id": "CS101", "credits": 0}]
        }, 
        "time_slot_config": {
            "days": ["MON", "TUE", "WED", "THU", "FRI"],
            "time_slots": {
                "MON": [{"start_time": "08:00", "end_time": "09:00"}],
                "TUE": [], "WED": [], "THU": [], "FRI": []
            }
        }
    }
    with pytest.raises(ValueError, match="Invalid credits for course CS101"):
        validate_config(cfg)


def test_validate_config_missing_id():
    cfg = {
        "config": {
            "faculty": [], "rooms": [], "labs": [],
            "courses": [{"credits": 3}]
        }, 
        "time_slot_config": {
            "days": ["MON", "TUE", "WED", "THU", "FRI"],
            "time_slots": {
                "MON": [{"start_time": "08:00", "end_time": "09:00"}],
                "TUE": [], "WED": [], "THU": [], "FRI": []
            }
        }
    }
    with pytest.raises(ValueError, match="Course with missing course_id."):
        validate_config(cfg)


def test_set_faculty_unavailable(app_context):
    with app_context.test_request_context():
        cfg = {"config": {"faculty": [{"name": "Smith"}]}}
        session[SESSION_CONFIG_KEY] = cfg

        set_faculty_day_unavailable_service("Smith", "mon")

        faculty = session[SESSION_CONFIG_KEY]["config"]["faculty"][0]
        assert faculty["times"]["MON"] == []


def test_room_service_updates(app_context):
    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {"config": {"rooms": []}}
        add_room_service("Room 101")
        assert len(session[SESSION_CONFIG_KEY]["config"]["rooms"]) == 1
        assert session[SESSION_CONFIG_KEY]["config"]["rooms"][0] == "Room 101"


def test_lab_service_updates(app_context):
    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {"config": {"labs": []}}
        add_lab_service(lab="Biology Lab")
        assert len(session[SESSION_CONFIG_KEY]["config"]["labs"]) == 1
        assert session[SESSION_CONFIG_KEY]["config"]["labs"][0] == "Biology Lab"


def test_course_service_casts_credits(app_context):
    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {
            "config": {
                "courses": [],
                "rooms": ["Room A"]
            }
        }

        add_course_service(
            course_id="CS102", 
            credits="4", 
            room="Room A", 
            faculty=[]
        )

        course = session[SESSION_CONFIG_KEY]["config"]["courses"][0]
        assert course["credits"] == 4
        assert isinstance(course["credits"], int)


def test_save_config_fails_validation(app_context, tmp_path):
    with app_context.test_request_context():
        # Invalid config (missing couse_id)
        session[SESSION_CONFIG_KEY] = {
            "config": {"courses": [{"credits": 3}]},
            "time_slot_config": {
                "days": ["MON", "TUE", "WED", "THU", "FRI"],
                "time_slots": {
                    "MON": [{"start_time": "08:00", "end_time": "09:00"}],
                    "TUE": [], "WED": [], "THU": [], "FRI": []
                }
            }
        }
        save_path = tmp_path / "fail.json"
        
        with pytest.raises(ValueError, match="Course with missing course_id."):
            save_config_from_session(str(save_path))


def test_update_schedules_fails_on_conflicts(app_context):
    with app_context.test_request_context():
        cfg = {"config": {"faculty": [{"name": "Smith"}, {"name": "Smith"}]}}
        session[SESSION_CONFIG_KEY] = cfg
        session["config_conflicts"] = ["Duplicate faculty name: Smith"]
        
        with pytest.raises(ValueError, match="Schedules cannot be generated until configuration conflicts are resolved."):
            update_schedules(cfg)


def test_get_config_status_empty_session(app_context):
    with app_context.test_request_context():
        session.clear()
        status = get_config_status()
        assert status["loaded"] is False
        assert status["counts"] == {}


def test_remove_services(app_context):
    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {
            "config": {
                "faculty": [{"name": "Smith"}],
                "rooms": ["101"],
                "courses": [{"course_id": "CS101"}]
            }
        }
        
        remove_faculty_service(name="Smith")
        remove_room_service(room="101")
        remove_course_service(course_id="CS101")
        
        cfg = session[SESSION_CONFIG_KEY]["config"]
        assert len(cfg["faculty"]) == 0
        assert len(cfg["rooms"]) == 0
        assert len(cfg["courses"]) == 0


def test_modify_room_service(app_context):
    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {"config": {"rooms": ["Old Room"]}}
        modify_room_service(room="Old Room", new_name="New Room")
        assert session[SESSION_CONFIG_KEY]["config"]["rooms"][0] == "New Room"


def test_get_config_status_no_config(app_context):
    with app_context.test_request_context():
        if SESSION_CONFIG_KEY in session:
            del session[SESSION_CONFIG_KEY]
            
        status = get_config_status()
        assert status["loaded"] is False
        assert status["counts"] == {}


def test_remove_course_and_modify_room(app_context):
    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {
            "config": {
                "courses": [{"course_id": "CS101", "room": "101"}],
                "rooms": ["101"]
            }
        }

        modify_room_service(room="101", new_name="202")
        assert session[SESSION_CONFIG_KEY]["config"]["rooms"][0] == "202"

        remove_course_service(course_id="CS101")
        assert len(session[SESSION_CONFIG_KEY]["config"]["courses"]) == 0


def test_config_service_error_branches(app_context):
    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {
            "config": {
                "faculty": [],
                "rooms": [],
                "courses": [],
                "labs": []
            }
        }
        session.modified = True

        with pytest.raises(ValueError, match="Faculty Ghost does not exist."):
            remove_faculty_service(name="Ghost")

        with pytest.raises(ValueError, match="Room 'Void' does not exist."):
            remove_room_service(room="Void")

        with pytest.raises(ValueError, match="Course None does not exist."):
            remove_course_service(course_id="None")

        add_room_service("101")
        with pytest.raises(ValueError, match="Room '101' already exists."):
            add_room_service("101")
            
        add_faculty_service(name="Jones", appointment_type="Adjunct")
        with pytest.raises(ValueError, match="Faculty 'Jones' already exists"):
            add_faculty_service(name="Jones", appointment_type="Adjunct")

        session.clear()
        status = get_config_status()
        assert status["loaded"] is False
        assert status["counts"] == {}
        