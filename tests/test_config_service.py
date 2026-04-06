# Author: Tanner Ness, Ian Swartz
# Date: 2026-04-05

import pytest
import json

import app.web.services.config_service as config_service

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

    path = repo_root / "configs" / "config_test.json"

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
            "labs": [],
        }
    }
    conflicts = detect_conflicts(cfg)
    assert len(conflicts) == 1
    assert "Duplicate faculty name: Dr. Smith" in conflicts[0]


def test_detect_missing_names():
    cfg = {"config": {"faculty": [{"name": ""}], "rooms": [], "labs": []}}
    conflicts = detect_conflicts(cfg)
    assert "Faculty member with missing name." in conflicts


def test_validate_config_invalid_room():
    cfg = {
        "config": {
            "faculty": [{"name": "Smith"}],
            "rooms": [{"name": "Room A"}],
            "labs": [],
            "courses": [
                {
                    "course_id": "CS101",
                    "credits": 3,
                    "room": ["Room Z"],
                    "faculty": ["Smith"],
                }
            ],
        },
        "time_slot_config": {
            "days": ["MON", "TUE", "WED", "THU", "FRI"],
            "time_slots": {
                "MON": [{"start_time": "08:00", "end_time": "09:00"}],
                "TUE": [],
                "WED": [],
                "THU": [],
                "FRI": [],
            },
        },
    }
    with pytest.raises(ValueError, match="Invalid room 'Room Z'"):
        validate_config(cfg)


def test_faculty_service_updates_session(app_context):
    with app_context.test_request_context():
        session["working_config"] = {"config": {"faculty": []}, "limit": 3}

        add_faculty_service(name="New Faculty", appointment_type="Full-Time")

        assert get_unsaved() is True
        assert len(session["working_config"]["config"]["faculty"]) == 1
        assert (
            session["working_config"]["config"]["faculty"][0]["name"] == "New Faculty"
        )


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
            "config": {"faculty": []},
            "limit": 3,
            "time_slot_config": {
                "days": ["MON", "TUE", "WED", "THU", "FRI"],
                "time_slots": {
                    "MON": [{"start_time": "08:00", "end_time": "09:00"}],
                    "TUE": [],
                    "WED": [],
                    "THU": [],
                    "FRI": [],
                },
            },
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
            "faculty": [],
            "rooms": [],
            "labs": [],
            "courses": [{"course_id": "CS101", "credits": 0}],
        },
        "time_slot_config": {
            "days": ["MON", "TUE", "WED", "THU", "FRI"],
            "time_slots": {
                "MON": [{"start_time": "08:00", "end_time": "09:00"}],
                "TUE": [],
                "WED": [],
                "THU": [],
                "FRI": [],
            },
        },
    }
    with pytest.raises(ValueError, match="Invalid credits for course CS101"):
        validate_config(cfg)


def test_validate_config_missing_id():
    cfg = {
        "config": {"faculty": [], "rooms": [], "labs": [], "courses": [{"credits": 3}]},
        "time_slot_config": {
            "days": ["MON", "TUE", "WED", "THU", "FRI"],
            "time_slots": {
                "MON": [{"start_time": "08:00", "end_time": "09:00"}],
                "TUE": [],
                "WED": [],
                "THU": [],
                "FRI": [],
            },
        },
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
        session[SESSION_CONFIG_KEY] = {"config": {"courses": [], "rooms": ["Room A"]}}

        add_course_service(course_id="CS102", credits="4", room="Room A", faculty=[])

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
                    "TUE": [],
                    "WED": [],
                    "THU": [],
                    "FRI": [],
                },
            },
        }
        save_path = tmp_path / "fail.json"

        with pytest.raises(ValueError, match="Course with missing course_id."):
            save_config_from_session(str(save_path))


def test_update_schedules_fails_on_conflicts(app_context):
    with app_context.test_request_context():
        cfg = {"config": {"faculty": [{"name": "Smith"}, {"name": "Smith"}]}}
        session[SESSION_CONFIG_KEY] = cfg
        session["config_conflicts"] = ["Duplicate faculty name: Smith"]

        with pytest.raises(
            ValueError,
            match="Schedules cannot be generated until configuration conflicts are resolved.",
        ):
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
                "courses": [{"course_id": "CS101"}],
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
                "rooms": ["101"],
            }
        }

        modify_room_service(room="101", new_name="202")
        assert session[SESSION_CONFIG_KEY]["config"]["rooms"][0] == "202"

        remove_course_service(course_id="CS101")
        assert len(session[SESSION_CONFIG_KEY]["config"]["courses"]) == 0


def test_config_service_error_branches(app_context):
    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {
            "config": {"faculty": [], "rooms": [], "courses": [], "labs": []}
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


def test_load_config_into_session_from_uploaded_file(app_context, monkeypatch):
    """
    Ensures load_config_into_session supports uploaded browser files
    instead of only filesystem paths.
    """

    class FakeUpload:
        filename = "uploaded_config.json"

        def read(self):
            return b'{"config": {"faculty": []}}'

    written = {}

    monkeypatch.setattr(
        config_service,
        "_write_working_file",
        lambda cfg: written.setdefault("cfg", cfg),
    )
    monkeypatch.setattr(
        config_service,
        "detect_conflicts",
        lambda cfg: ["demo-conflict"],
    )

    with app_context.test_request_context():
        config_service.load_config_into_session(FakeUpload())

        assert session[SESSION_CONFIG_KEY]["config"]["faculty"] == []
        assert session[config_service.SESSION_CONFIG_PATH_KEY] == "uploaded_config.json"
        assert session["config_conflicts"] == ["demo-conflict"]
        assert session[config_service.SESSION_UNSAVED_KEY] is False
        assert session[config_service.SESSION_SCHEDULES_UPDATED_KEY] is False
        assert written["cfg"]["config"]["faculty"] == []


def test_save_config_from_session_updates_path_and_flags(
    app_context, tmp_path, monkeypatch
):
    """
    Ensures save_config_from_session writes the config, updates the stored
    save path, and marks schedules as updated.
    """
    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {
            "config": {
                "faculty": [],
                "courses": [],
                "rooms": [],
                "labs": [],
            },
            "time_slot_config": {
                "days": ["MON"],
                "time_slots": {"MON": []},
            },
        }

        monkeypatch.setattr(config_service, "validate_config", lambda cfg: None)

        save_path = tmp_path / "saved_config.json"
        config_service.save_config_from_session(str(save_path))

        assert save_path.exists()
        assert session[config_service.SESSION_CONFIG_PATH_KEY] == str(save_path)
        assert session[config_service.SESSION_UNSAVED_KEY] is False
        assert session[config_service.SESSION_SCHEDULES_UPDATED_KEY] is True

        saved = json.loads(save_path.read_text(encoding="utf-8"))
        assert saved["config"]["faculty"] == []


def test_validate_config_rejects_missing_config_key():
    """
    Ensures validate_config rejects dictionaries that do not contain the
    required top-level config key.
    """
    with pytest.raises(ValueError, match="Invalid configuration format."):
        validate_config({})


def test_validate_config_invalid_lab_reference():
    """
    Ensures validate_config rejects courses that reference a lab not present
    in the configuration.
    """
    cfg = {
        "config": {
            "faculty": [{"name": "Smith"}],
            "rooms": ["Room A"],
            "labs": ["Lab A"],
            "courses": [
                {
                    "course_id": "CS101",
                    "credits": 3,
                    "room": ["Room A"],
                    "lab": ["Missing Lab"],
                    "faculty": ["Smith"],
                }
            ],
        }
    }

    with pytest.raises(ValueError, match="Invalid lab 'Missing Lab' in course CS101"):
        validate_config(cfg)


def test_validate_config_invalid_faculty_reference():
    """
    Ensures validate_config rejects courses that reference a faculty member
    not present in the configuration.
    """
    cfg = {
        "config": {
            "faculty": [{"name": "Smith"}],
            "rooms": ["Room A"],
            "labs": [],
            "courses": [
                {
                    "course_id": "CS101",
                    "credits": 3,
                    "room": ["Room A"],
                    "faculty": ["Jones"],
                }
            ],
        }
    }

    with pytest.raises(ValueError, match="Invalid faculty 'Jones' in course CS101"):
        validate_config(cfg)


def test_validate_config_invalid_conflict_reference():
    """
    Ensures validate_config rejects conflicts that point to a course_id
    that does not exist in the config.
    """
    cfg = {
        "config": {
            "faculty": [],
            "rooms": [],
            "labs": [],
            "courses": [
                {
                    "course_id": "CS101",
                    "credits": 3,
                    "conflicts": ["CS999"],
                }
            ],
        }
    }

    with pytest.raises(ValueError, match="Invalid conflict 'CS999' in course CS101"):
        validate_config(cfg)


def test_modify_faculty_service_calls_domain_and_commit(app_context, monkeypatch):
    """
    Ensures modify_faculty_service delegates to the faculty domain logic
    and then commits the change.
    """
    observed = {}

    monkeypatch.setattr(
        config_service,
        "modify_faculty",
        lambda cfg, **kwargs: observed.setdefault("kwargs", kwargs),
    )
    monkeypatch.setattr(
        config_service,
        "_commit_change",
        lambda cfg: observed.setdefault("committed", cfg),
    )

    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {"config": {"faculty": []}}

        modify_faculty_service(name="Smith", new_name="Jones")

        assert observed["kwargs"] == {"name": "Smith", "new_name": "Jones"}
        assert observed["committed"] == session[SESSION_CONFIG_KEY]


def test_set_faculty_time_service_adds_time_slot(app_context):
    """
    Ensures set_faculty_time_service creates the faculty times structure,
    uppercases the day, and appends the new availability slot.
    """
    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {"config": {"faculty": [{"name": "Smith"}]}}

        config_service.set_faculty_time_service("Smith", "mon", "09:00", "10:00")

        faculty = session[SESSION_CONFIG_KEY]["config"]["faculty"][0]
        assert faculty["times"]["MON"] == [{"start_time": "09:00", "end_time": "10:00"}]
        assert session[config_service.SESSION_UNSAVED_KEY] is True


def test_set_faculty_time_service_raises_when_missing(app_context):
    """
    Ensures set_faculty_time_service raises a clear error when the faculty
    member does not exist.
    """
    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {"config": {"faculty": []}}

        with pytest.raises(ValueError, match="Faculty 'Smith' does not exist"):
            config_service.set_faculty_time_service("Smith", "MON", "09:00", "10:00")


def test_remove_faculty_time_service_removes_matching_slot(app_context):
    """
    Ensures remove_faculty_time_service removes only the matching faculty
    time slot and leaves the others intact.
    """
    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {
            "config": {
                "faculty": [
                    {
                        "name": "Smith",
                        "times": {
                            "MON": [
                                {"start_time": "09:00", "end_time": "10:00"},
                                {"start_time": "10:00", "end_time": "11:00"},
                            ]
                        },
                    }
                ]
            }
        }

        config_service.remove_faculty_time_service("Smith", "MON", "09:00", "10:00")

        slots = session[SESSION_CONFIG_KEY]["config"]["faculty"][0]["times"]["MON"]
        assert slots == [{"start_time": "10:00", "end_time": "11:00"}]


def test_remove_faculty_time_service_raises_when_missing(app_context):
    """
    Ensures remove_faculty_time_service raises a clear error when the
    faculty member is not found.
    """
    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {"config": {"faculty": []}}

        with pytest.raises(ValueError, match="Faculty 'Smith' not found"):
            config_service.remove_faculty_time_service("Smith", "MON", "09:00", "10:00")


def test_remove_and_modify_lab_services_call_dependencies(app_context, monkeypatch):
    """
    Ensures remove_lab_service and modify_lab_service both delegate to
    the lab domain functions and then commit.
    """
    calls = []

    monkeypatch.setattr(
        config_service,
        "remove_lab",
        lambda cfg, **kwargs: calls.append(("remove", kwargs)),
    )
    monkeypatch.setattr(
        config_service,
        "modify_lab",
        lambda cfg, **kwargs: calls.append(("modify", kwargs)),
    )
    monkeypatch.setattr(
        config_service,
        "_commit_change",
        lambda cfg: calls.append(("commit", True)),
    )

    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {"config": {"labs": []}}

        config_service.remove_lab_service(lab="Old Lab")
        config_service.modify_lab_service(lab="Old Lab", new_name="New Lab")

    assert calls[0] == ("remove", {"lab": "Old Lab"})
    assert calls[1] == ("commit", True)
    assert calls[2] == ("modify", {"lab": "Old Lab", "new_name": "New Lab"})
    assert calls[3] == ("commit", True)


def test_modify_course_service_casts_credits_to_int(app_context, monkeypatch):
    """
    Ensures modify_course_service converts credits from string to int
    before delegating to the domain function.
    """
    observed = {}

    monkeypatch.setattr(
        config_service,
        "modify_course",
        lambda cfg, **kwargs: observed.setdefault("kwargs", kwargs),
    )
    monkeypatch.setattr(
        config_service,
        "_commit_change",
        lambda cfg: observed.setdefault("committed", True),
    )

    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {"config": {"courses": []}}

        config_service.modify_course_service(course_id="CS101", credits="4")

    assert observed["kwargs"]["credits"] == 4
    assert isinstance(observed["kwargs"]["credits"], int)
    assert observed["committed"] is True


def test_conflict_services_call_dependencies(app_context, monkeypatch):
    """
    Ensures add/remove/modify conflict services delegate correctly and commit.
    """
    calls = []

    monkeypatch.setattr(
        config_service,
        "add_conflict",
        lambda cfg, **kwargs: calls.append(("add", kwargs)),
    )
    monkeypatch.setattr(
        config_service,
        "remove_conflict",
        lambda cfg, **kwargs: calls.append(("remove", kwargs)),
    )
    monkeypatch.setattr(
        config_service,
        "modify_conflict",
        lambda cfg, **kwargs: calls.append(("modify", kwargs)),
    )
    monkeypatch.setattr(
        config_service,
        "_commit_change",
        lambda cfg: calls.append(("commit", True)),
    )

    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {"config": {"courses": []}}

        config_service.add_conflict_service(
            course_id="CS101", conflict_course_id="CS102"
        )
        config_service.remove_conflict_service(
            course_id="CS101", conflict_course_id="CS102"
        )
        config_service.modify_conflict_service(
            course_id="CS101",
            old_conflict="CS102",
            new_conflict="CS103",
        )

    assert calls[0] == ("add", {"course_id": "CS101", "conflict_course_id": "CS102"})
    assert calls[1] == ("commit", True)
    assert calls[2] == ("remove", {"course_id": "CS101", "conflict_course_id": "CS102"})
    assert calls[3] == ("commit", True)
    assert calls[4] == (
        "modify",
        {"course_id": "CS101", "old_conflict": "CS102", "new_conflict": "CS103"},
    )
    assert calls[5] == ("commit", True)

