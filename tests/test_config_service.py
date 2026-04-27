# Author: Tanner Ness, Ian Swartz
# Date: 2026-04-05

import json

import pytest
from flask import session

import app.web.services.config_service as config_service
from app.web.app import create_app
from app.web.services.config_service import (
    SESSION_CONFIG_KEY,
    add_course_service,
    add_faculty_service,
    add_lab_service,
    add_pattern_service,
    add_room_service,
    add_time_slot_service,
    clear_config,
    detect_conflicts,
    export_config_bytes,
    get_config_status,
    get_conflicts,
    get_unsaved,
    has_conflicts,
    load_config_into_session,
    modify_faculty_service,
    modify_pattern_service,
    modify_room_service,
    modify_time_slot_service,
    redo,
    remove_course_service,
    remove_faculty_service,
    remove_pattern_service,
    remove_room_service,
    remove_time_slot_service,
    sanitize_export_filename,
    save_config_from_session,
    set_conflicts,
    set_faculty_day_unavailable_service,
    toggle_pattern_service,
    undo,
    update_schedules,
    validate_config,
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
            match=(
                "Schedules cannot be generated until configuration conflicts "
                "are resolved."
            ),
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


def test_add_time_slot_service_writes_canonical_slot(app_context):
    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {
            "config": {"faculty": [], "courses": [], "rooms": [], "labs": []},
            "limit": 3,
            "optimizer_flags": [],
            "time_slot_config": {
                "times": {
                    "MON": [],
                    "TUE": [],
                    "WED": [],
                    "THU": [],
                    "FRI": [],
                },
                "classes": [],
            },
        }

        add_time_slot_service(day="MON", start="08:00", spacing="60", end="17:00")

        slots = session[SESSION_CONFIG_KEY]["time_slot_config"]["times"]["MON"]
        assert len(slots) == 1
        assert slots[0] == {"start": "08:00", "spacing": 60, "end": "17:00"}
        assert get_unsaved() is True


def test_modify_and_remove_time_slot_service_use_index(app_context):
    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {
            "config": {"faculty": [], "courses": [], "rooms": [], "labs": []},
            "time_slot_config": {
                "times": {
                    "MON": [{"start": "08:00", "spacing": 60, "end": "12:00"}],
                    "TUE": [],
                    "WED": [],
                    "THU": [],
                    "FRI": [],
                },
                "classes": [],
            },
        }

        modify_time_slot_service(
            day="MON",
            index="0",
            start="09:00",
            spacing="50",
            end="13:00",
        )

        slots = session[SESSION_CONFIG_KEY]["time_slot_config"]["times"]["MON"]
        assert slots[0] == {"start": "09:00", "spacing": 50, "end": "13:00"}

        remove_time_slot_service(day="MON", index="0")
        assert session[SESSION_CONFIG_KEY]["time_slot_config"]["times"]["MON"] == []


def test_add_pattern_service_creates_canonical_class_pattern(app_context):
    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {
            "config": {"faculty": [], "courses": [], "rooms": [], "labs": []},
            "time_slot_config": {
                "times": {
                    "MON": [{"start": "08:00", "spacing": 60, "end": "17:00"}],
                    "TUE": [],
                    "WED": [{"start": "08:00", "spacing": 60, "end": "17:00"}],
                    "THU": [],
                    "FRI": [{"start": "08:00", "spacing": 60, "end": "17:00"}],
                },
                "classes": [],
            },
        }

        add_pattern_service(
            credits="3",
            days="MON,WED,FRI",
            duration="50",
            is_lab=False,
            fixed_start_time="09:00",
            enabled=True,
        )

        classes = session[SESSION_CONFIG_KEY]["time_slot_config"]["classes"]
        assert len(classes) == 1
        assert classes[0]["credits"] == 3
        assert classes[0]["meetings"] == [
            {"days": ["MON"], "duration": "50"},
            {"days": ["WED"], "duration": "50"},
            {"days": ["FRI"], "duration": "50"},
        ]
        assert classes[0]["start_time"] == "09:00"
        assert "disabled" not in classes[0]


def test_modify_toggle_and_remove_pattern_service_by_index(app_context):
    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {
            "config": {"faculty": [], "courses": [], "rooms": [], "labs": []},
            "time_slot_config": {
                "times": {
                    "MON": [{"start": "08:00", "spacing": 60, "end": "17:00"}],
                    "TUE": [{"start": "08:00", "spacing": 60, "end": "17:00"}],
                    "WED": [],
                    "THU": [],
                    "FRI": [],
                },
                "classes": [
                    {
                        "credits": 4,
                        "meetings": [{"day": "MON", "duration": "50", "lab": False}],
                    }
                ],
            },
        }

        modify_pattern_service(
            index="0",
            credits="4",
            days="MON,TUE",
            duration="110",
            is_lab="on",
            fixed_start_time="10:00",
        )

        pattern = session[SESSION_CONFIG_KEY]["time_slot_config"]["classes"][0]
        assert pattern["credits"] == 4
        assert pattern["meetings"] == [
            {"days": ["MON"], "duration": "110", "lab": True},
            {"days": ["TUE"], "duration": "110", "lab": True},
        ]
        assert pattern["start_time"] == "10:00"

        toggle_pattern_service(index="0", enabled="false")
        assert pattern["disabled"] is True

        toggle_pattern_service(index="0", enabled="true")
        assert "disabled" not in pattern

        remove_pattern_service(index="0")
        assert session[SESSION_CONFIG_KEY]["time_slot_config"]["classes"] == []


def test_validate_config_rejects_time_slot_with_bad_time_format():
    cfg = {
        "config": {"faculty": [], "rooms": [], "labs": [], "courses": []},
        "time_slot_config": {
            "times": {
                "MON": [{"start": "8:00", "spacing": 60, "end": "17:00"}],
                "TUE": [],
                "WED": [],
                "THU": [],
                "FRI": [],
            },
            "classes": [],
        },
    }

    with pytest.raises(ValueError, match="Invalid time format"):
        validate_config(cfg)


def test_validate_config_rejects_pattern_day_without_time_slots():
    cfg = {
        "config": {"faculty": [], "rooms": [], "labs": [], "courses": []},
        "time_slot_config": {
            "times": {
                "MON": [],
                "TUE": [],
                "WED": [],
                "THU": [],
                "FRI": [],
            },
            "classes": [
                {
                    "credits": 3,
                    "meetings": [{"day": "MON", "duration": "50", "lab": False}],
                }
            ],
        },
    }

    with pytest.raises(ValueError, match="no time slots are configured for MON"):
        validate_config(cfg)


def test_undo_button_restores_previous_state(app_context):
    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {"config": {"faculty": []}}
        config_service.undo_stack = []
        config_service.redo_stack = []

        add_faculty_service(name="Horatio Nelson", appointment_type="Full-Time")

        undo()

        assert len(session[SESSION_CONFIG_KEY]["config"]["faculty"]) == 0


def test_redo_button_restores_undone_state(app_context):
    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {"config": {"faculty": []}}
        config_service.undo_stack = []
        config_service.redo_stack = []

        add_faculty_service(name="John Darktide", appointment_type="Adjunct")

        undo()
        redo()

        assert len(session[SESSION_CONFIG_KEY]["config"]["faculty"]) == 1
        assert (
            session[SESSION_CONFIG_KEY]["config"]["faculty"][0]["name"]
            == "John Darktide"
        )


def test_undo_multiple(app_context):

    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {"config": {"faculty": [], "rooms": []}}
        config_service.undo_stack = []
        config_service.redo_stack = []

        add_faculty_service(name="Belisarius", appointment_type="Full-Time")

        add_room_service("Amber Room")

        add_faculty_service(name="Villanova", appointment_type="Adjunct")

        # Undo last addition (Villanova)
        undo()
        assert len(session[SESSION_CONFIG_KEY]["config"]["faculty"]) == 1

        # Undo room
        undo()
        assert len(session[SESSION_CONFIG_KEY]["config"]["rooms"]) == 0

        # Undo first faculty (Belisarius)
        undo()
        assert len(session[SESSION_CONFIG_KEY]["config"]["faculty"]) == 0


def test_redo_clears_on_new_action(app_context):

    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {"config": {"faculty": [], "rooms": []}}
        config_service.undo_stack = []
        config_service.redo_stack = []

        add_faculty_service(name="Neumann", appointment_type="Full-Time")

        undo()

        add_room_service("Room 740")

        with pytest.raises(ValueError, match="Nothing to redo"):
            redo()


def test_undo_raises_when_stack_empty(app_context):

    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {"config": {"faculty": []}}
        config_service.undo_stack = []
        config_service.redo_stack = []

        with pytest.raises(ValueError, match="Nothing to undo"):
            undo()


def test_redo_raises_when_stack_empty(app_context):

    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {"config": {"faculty": []}}
        config_service.undo_stack = []
        config_service.redo_stack = []

        with pytest.raises(ValueError, match="Nothing to redo"):
            redo()


def test_get_working_config_initializes(app_context):
    from app.web.services.config_service import _get_working_config

    with app_context.test_request_context():
        session.clear()

        cfg = _get_working_config()

        assert "config" in cfg
        assert get_unsaved() is False


def test_undo_deep_copy_integrity(app_context):
    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {"config": {"faculty": []}}
        config_service.undo_stack = []
        config_service.redo_stack = []

        add_faculty_service(name="A", appointment_type="Full-Time")

        undo()

        # mutate current state
        session[SESSION_CONFIG_KEY]["config"]["faculty"].append({"name": "Injected"})

        redo()

        # ensure redo didn't include mutation
        faculty = session[SESSION_CONFIG_KEY]["config"]["faculty"]
        assert all(f["name"] != "Injected" for f in faculty)


def test_add_time_slot_invalid_day(app_context):
    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {"config": {}}

        with pytest.raises(ValueError, match="Invalid day"):
            add_time_slot_service("SUN", "08:00", 60, "17:00")


def test_remove_time_slot_invalid_index(app_context):
    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {
            "config": {},
            "time_slot_config": {"times": {"MON": []}, "classes": []},
        }

        with pytest.raises(ValueError, match="Invalid slot index"):
            remove_time_slot_service("MON", 0)


def test_detect_conflicts_mixed_formats():
    cfg = {
        "config": {
            "faculty": ["Smith", {"name": "Smith"}],
            "rooms": ["101", {"name": "101"}],
            "labs": [],
        }
    }

    conflicts = detect_conflicts(cfg)

    assert any("Duplicate faculty name: Smith" in c for c in conflicts)
    assert any("Duplicate room name: 101" in c for c in conflicts)


def test_clear_config_resets_flags(app_context):
    with app_context.test_request_context():
        session[SESSION_CONFIG_KEY] = {"config": {}}
        session["unsaved_changes"] = True
        session["schedules_updated"] = True

        clear_config()

        assert session.get("unsaved_changes") is False
        assert session.get("schedules_updated") is False


def test_empty_config_structure():
    from app.web.services.config_service import _empty_config

    cfg = _empty_config()

    assert "config" in cfg
    assert "time_slot_config" in cfg
    assert "times" in cfg["time_slot_config"]
    assert "classes" in cfg["time_slot_config"]


def _base_valid_config():
    """
    Builds a minimal valid config using the current supported time-slot format.
    """
    return {
        "config": {
            "faculty": [],
            "rooms": [],
            "labs": [],
            "courses": [],
        },
        "time_slot_config": {
            "times": {
                "MON": [{"start": "09:00", "spacing": 60, "end": "17:00"}],
                "TUE": [{"start": "09:00", "spacing": 60, "end": "17:00"}],
                "WED": [{"start": "09:00", "spacing": 60, "end": "17:00"}],
                "THU": [{"start": "09:00", "spacing": 60, "end": "17:00"}],
                "FRI": [{"start": "09:00", "spacing": 60, "end": "17:00"}],
            },
            "classes": [
                {
                    "credits": 3,
                    "meetings": [
                        {"day": "MON", "duration": 50, "lab": False},
                        {"day": "WED", "duration": 50, "lab": False},
                    ],
                }
            ],
        },
    }


def test_validate_config_rejects_invalid_time_format():
    """
    Covers invalid HH:MM format validation for time-slot start/end values.
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["times"]["MON"][0]["start"] = "9AM"

    with pytest.raises(ValueError, match="Invalid time format"):
        validate_config(cfg)


def test_validate_config_rejects_invalid_time_value():
    """
    Covers invalid time values such as impossible hours/minutes.
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["times"]["MON"][0]["start"] = "25:00"

    with pytest.raises(ValueError, match="Invalid time value"):
        validate_config(cfg)


def test_validate_config_rejects_non_dictionary_time_slots():
    """
    Covers validation branch where time_slot_config.times is not a dictionary.
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["times"] = []

    with pytest.raises(ValueError, match="time_slot_config.times must be a dictionary"):
        validate_config(cfg)


def test_validate_config_rejects_non_list_classes():
    """
    Covers validation branch where time_slot_config.classes is not a list.
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["classes"] = {}

    with pytest.raises(ValueError, match="time_slot_config.classes must be a list"):
        validate_config(cfg)


def test_validate_config_rejects_invalid_time_slot_day():
    """
    Covers invalid day names in time_slot_config.times.
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["times"]["SAT"] = [
        {"start": "09:00", "spacing": 60, "end": "12:00"}
    ]

    with pytest.raises(ValueError, match="Invalid time-slot day 'SAT'"):
        validate_config(cfg)


def test_validate_config_rejects_non_list_day_slots():
    """
    Covers validation branch where a day's time slots are not a list.
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["times"]["MON"] = {"start": "09:00"}

    with pytest.raises(
        ValueError, match=r"time_slot_config.times\['MON'\] must be a list"
    ):
        validate_config(cfg)


def test_validate_config_rejects_non_object_slot():
    """
    Covers validation branch where an individual time slot is not an object.
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["times"]["MON"] = ["09:00-17:00"]

    with pytest.raises(ValueError, match="Invalid slot in MON; expected an object"):
        validate_config(cfg)


def test_validate_config_rejects_missing_slot_fields():
    """
    Covers missing start/spacing/end validation.
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["times"]["MON"] = [{"start": "09:00", "end": "17:00"}]

    with pytest.raises(ValueError, match="must include start, spacing, and end"):
        validate_config(cfg)


def test_validate_config_rejects_end_before_start():
    """
    Covers branch where time-slot end is not after start.
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["times"]["MON"][0]["start"] = "17:00"
    cfg["time_slot_config"]["times"]["MON"][0]["end"] = "09:00"

    with pytest.raises(ValueError, match="Time slot end must be after start"):
        validate_config(cfg)


def test_validate_config_rejects_invalid_spacing():
    """
    Covers invalid spacing branch.
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["times"]["MON"][0]["spacing"] = 0

    with pytest.raises(ValueError, match="Invalid spacing in MON"):
        validate_config(cfg)


def test_validate_config_rejects_non_object_pattern():
    """
    Covers validation branch where class pattern is not an object.
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["classes"] = ["bad-pattern"]

    with pytest.raises(ValueError, match="Pattern at index 0 must be an object"):
        validate_config(cfg)


def test_validate_config_rejects_invalid_pattern_credits():
    """
    Covers invalid class pattern credits.
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["classes"][0]["credits"] = 0

    with pytest.raises(ValueError, match="Pattern 0 has invalid credits"):
        validate_config(cfg)


def test_validate_config_rejects_missing_pattern_meetings():
    """
    Covers missing/empty meetings list validation.
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["classes"][0]["meetings"] = []

    with pytest.raises(ValueError, match="Pattern 0 must have at least one meeting"):
        validate_config(cfg)


def test_validate_config_rejects_non_object_meeting():
    """
    Covers validation branch where meeting entry is not an object.
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["classes"][0]["meetings"] = ["MON 09:00"]

    with pytest.raises(ValueError, match="Pattern 0, meeting 0 must be an object"):
        validate_config(cfg)


def test_validate_config_rejects_missing_meeting_day():
    """
    Covers validation branch where meeting day is missing.
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["classes"][0]["meetings"] = [{"duration": 50}]

    with pytest.raises(ValueError, match="must include a valid 'day'"):
        validate_config(cfg)


def test_validate_config_rejects_invalid_meeting_day():
    """
    Covers validation branch where meeting day is outside VALID_DAYS.
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["classes"][0]["meetings"] = [{"day": "SAT", "duration": 50}]

    with pytest.raises(ValueError, match="contains invalid day"):
        validate_config(cfg)


def test_validate_config_rejects_meeting_day_without_slots():
    """
    Covers branch where a meeting references a valid day with no configured slots.
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["times"]["MON"] = []

    with pytest.raises(ValueError, match="no time slots are configured for MON"):
        validate_config(cfg)


def test_validate_config_rejects_missing_duration():
    """
    Covers validation branch where meeting duration is missing.
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["classes"][0]["meetings"] = [{"day": "MON"}]

    with pytest.raises(ValueError, match="must include a duration"):
        validate_config(cfg)


def test_validate_config_rejects_non_numeric_duration():
    """
    Covers invalid duration conversion branch.
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["classes"][0]["meetings"] = [
        {"day": "MON", "duration": "abc"}
    ]

    with pytest.raises(ValueError, match="has invalid duration"):
        validate_config(cfg)


def test_validate_config_rejects_non_positive_duration():
    """
    Covers duration <= 0 branch.
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["classes"][0]["meetings"] = [{"day": "MON", "duration": 0}]

    with pytest.raises(ValueError, match="has invalid duration"):
        validate_config(cfg)


def test_validate_config_rejects_non_boolean_lab_flag():
    """
    Covers validation branch where meeting lab flag is not boolean.
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["classes"][0]["meetings"] = [
        {"day": "MON", "duration": 50, "lab": "yes"}
    ]

    with pytest.raises(ValueError, match="field 'lab' must be true or false"):
        validate_config(cfg)


def test_validate_config_rejects_invalid_fixed_start_time():
    """
    Covers fixed_start validation branch.
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["classes"][0]["meetings"] = [
        {"day": "MON", "duration": 50, "fixed_start": "bad"}
    ]

    with pytest.raises(ValueError, match="Invalid time format"):
        validate_config(cfg)


def test_validate_config_rejects_invalid_pattern_start_time():
    """
    Covers pattern-level start_time validation branch.
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["classes"][0]["start_time"] = "bad"

    with pytest.raises(ValueError, match="Invalid time format"):
        validate_config(cfg)


def test_conflict_helpers_store_and_report_session_conflicts():
    """
    Covers set_conflicts, get_conflicts, and has_conflicts session helpers.
    """
    app = create_app()

    with app.test_request_context("/config"):
        set_conflicts(["Duplicate room: Roddy 140"])

        assert get_conflicts() == ["Duplicate room: Roddy 140"]
        assert has_conflicts() is True


def test_conflict_helpers_default_to_empty_list():
    """
    Covers default conflict helper behavior when no conflicts are stored.
    """
    app = create_app()

    with app.test_request_context("/config"):
        assert get_conflicts() == []
        assert has_conflicts() is False


def test_detect_conflicts_reports_missing_and_duplicate_entities():
    """
    Covers conflict detection branches for missing and duplicate names.
    """
    cfg = {
        "config": {
            "faculty": [
                {"name": "Smith"},
                {"name": "Smith"},
                {},
            ],
            "rooms": [
                "Roddy 140",
                "Roddy 140",
                {},
            ],
            "labs": [
                "Linux",
                "Linux",
                {},
            ],
            "courses": [
                {"course_id": "CS101"},
                {"course_id": "CS101"},
                {},
            ],
        }
    }

    conflicts = detect_conflicts(cfg)

    assert "Duplicate faculty name: Smith" in conflicts
    assert "Faculty member with missing name." in conflicts
    assert "Duplicate room name: Roddy 140" in conflicts
    assert "Room with missing name." in conflicts
    assert "Duplicate lab name: Linux" in conflicts
    assert "Lab with missing name." in conflicts
    assert "Course with missing course_id." in conflicts


# =========================================================
# Additional targeted config_service coverage
# =========================================================


def test_validate_config_accepts_valid_current_time_slot_config():
    """
    Covers the successful validation path for the current supported
    time_slot_config format.
    """
    cfg = _base_valid_config()

    validate_config(cfg)


def test_validate_config_accepts_meeting_with_lab_true_fixed_start_and_pattern_time():
    """
    Covers successful branches for:
    - lab=True
    - meeting-level fixed_start
    - pattern-level start_time
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["classes"][0] = {
        "credits": 4,
        "start_time": "09:00",
        "meetings": [
            {
                "day": "MON",
                "duration": 110,
                "lab": True,
                "fixed_start": "10:00",
            }
        ],
    }

    validate_config(cfg)


def test_validate_config_rejects_invalid_fixed_start_value():
    """
    Covers invalid HH:MM value for meeting-level fixed_start.
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["classes"][0]["meetings"] = [
        {
            "day": "MON",
            "duration": 50,
            "fixed_start": "99:99",
        }
    ]

    with pytest.raises(ValueError, match="Invalid time value"):
        validate_config(cfg)


def test_validate_config_rejects_invalid_start_time_value():
    """
    Covers invalid HH:MM value for pattern-level start_time.
    """
    cfg = _base_valid_config()
    cfg["time_slot_config"]["classes"][0]["start_time"] = "99:99"

    with pytest.raises(ValueError, match="Invalid time value"):
        validate_config(cfg)


def test_detect_conflicts_accepts_string_and_object_entities_without_conflicts():
    """
    Covers normal paths where faculty, rooms, and labs can be represented
    as strings or objects without producing conflict messages.
    """
    cfg = {
        "config": {
            "faculty": [
                "Smith",
                {"name": "Jones"},
            ],
            "rooms": [
                "Roddy 136",
                {"name": "Roddy 140"},
            ],
            "labs": [
                "Linux",
                {"name": "Mac"},
            ],
            "courses": [
                {"course_id": "CMSC 140"},
                {"course_id": "CMSC 161"},
            ],
        }
    }

    conflicts = detect_conflicts(cfg)

    assert conflicts == []


def test_detect_conflicts_handles_missing_config_section():
    """
    Covers detect_conflicts fallback behavior when cfg does not include
    a config section.
    """
    conflicts = detect_conflicts({})

    assert conflicts == []


def test_has_conflicts_returns_false_after_clearing_conflicts():
    """
    Covers has_conflicts after explicitly storing an empty conflict list.
    """
    app = create_app()

    with app.test_request_context("/config"):
        set_conflicts([])
        assert get_conflicts() == []
        assert has_conflicts() is False
