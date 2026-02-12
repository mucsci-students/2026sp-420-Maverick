# Author: Jacob Karasow
# Date: 2026-02-11
"""
scheduler_execution.py

Scheduler execution module for generating course schedules.

Handles running the scheduler with user-defined options, managing
generation limits, selecting output formats, applying optimization
settings, and saving generated schedules to files.

Related User Stories:
    C1 — Run Scheduler with Options
"""

from typing import Dict, Any, List, Optional

from faculty_management import add_faculty, remove_faculty, parse_prefs
from lab_management import add_lab, remove_lab
from room_management import add_room, remove_room
from course_management import add_course

class Scheduler: 

    def __init__(self) -> None:
        self.cfg: Dict[str, Any] = {
            "config": {
                "faculty": [],
                "courses": [],
                "rooms": [],
                "labs": []
            }
        }

    def add_faculty(
        self, 
        name: str, 
        appointment_type: str,
        day: Optional[str] = None,
        time_range: Optional[str] = None,
        prefs: Optional[List[Dict[str, Any]]] = None
    )  -> None:
        add_faculty(self.cfg, name, appointment_type, day, time_range, prefs)

    def remove_faculty(self, name: str) -> None:
        remove_faculty(self.cfg, name)

    def parse_preferences(self, pref_list: List[str]) -> List[Dict[str, Any]]:
        return parse_prefs(pref_list)

    # =========================
    # Lab Operations
    # =========================

    def add_lab(self, lab: str) -> None:
        add_lab(self.cfg, lab)

    def remove_lab(self, lab: str) -> None:
        remove_lab(self.cfg, lab)

    # =========================
    # Room Operations
    # =========================

    def add_room(self, room: str) -> None:
        add_room(self.cfg, room)

    def remove_room(self, room: str) -> None:
        remove_room(self.cfg, room)

    # =========================
    # Course Operations
    # =========================

    def add_course(
        self,
        course_id: str,
        credits: int,
        room: str,
        lab: Optional[str] = None,
        faculty_list: Optional[List[str]] = None
    ) -> None:
        add_course(self.cfg, course_id, credits, room, lab, faculty_list)

    # =========================
    # Accessor
    # =========================

    def get_config(self) -> Dict[str, Any]:
        return self.cfg