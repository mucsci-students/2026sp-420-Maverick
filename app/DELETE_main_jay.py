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

# Takes functions from management files, imports into this file 
from faculty_management import add_faculty, remove_faculty, parse_prefs
from lab_management import add_lab, remove_lab
from room_management import add_room, remove_room
from course_management import add_course, remove_course

class Scheduler: 

    # Initializes a new Scheduler 
    def __init__(self) -> None:
        self.cfg: Dict[str, Any] = {
            "config": {
                "faculty": [],
                "courses": [],
                "rooms": [],
                "labs": []
            }
        }

    # ========== Faculty Operations ==========

    # Adds new faculty member to the configuration 
    #
    # Parameters:
    #   name             -> Faculty member name 
    #   appointment_type -> Type of appointment (full-time, adjunct)
    #   day              -> (Optional) days available
    #   time_range       -> (Optional) times available 
    #   prefs            -> (Optional) room/course preferences 
    def add_faculty(
        self, 
        name: str, 
        appointment_type: str,
        day: Optional[str] = None,
        time_range: Optional[str] = None,
        prefs: Optional[List[Dict[str, Any]]] = None
    )  -> None:
        add_faculty(self.cfg, name, appointment_type, day, time_range, prefs)

    # Removes a faculty member from the configuration
    #
    # Parameters:
    #   name    -> Faculty member name 
    def remove_faculty(self, name: str) -> None:
        remove_faculty(self.cfg, name)

    # Parses a list of preference strings into a structured
    #   preference dictionaries
    # 
    # Parameters:
    #   pref_list   -> List of preferences strings 
    # 
    # Returns:
    #   A list of structured preferecne dictionaries
    def parse_preferences(self, pref_list: List[str]) -> List[Dict[str, Any]]:
        return parse_prefs(pref_list)

    # ========== Lab Operations ==========

    # Adds a lab to the configuration
    #
    # Parameters:
    #   lab -> Name of the lab
    def add_lab(self, lab: str) -> None:
        add_lab(self.cfg, lab)

    # Removes a lab from the configuration
    #
    # Parameters:
    #   lab -> Name of the lab
    def remove_lab(self, lab: str) -> None:
        remove_lab(self.cfg, lab)

    # ========== Room Operations ==========

    # Adds a room to the configuration
    #
    # Parameters:
    #   room -> Name of the room
    def add_room(self, room: str) -> None:
        add_room(self.cfg, room)

    # Removes a room from the configuration
    #
    # Parameters:
    #   room -> Name of the room
    def remove_room(self, room: str) -> None:
        remove_room(self.cfg, room)

    # ========== Course Operations ==========

    # Adds a course to the configuration 
    #
    # Parameters:
    #   course_id   -> Course identifier (e.g., CMSC330)
    #   credits     -> Number of credit hours
    #   room        -> Assigned room
    #   lab         -> Optional associated lab
    #   faculty_list-> Optional list of assigned faculty members
    def add_course(
        self,
        course_id: str,
        credits: int,
        room: str,
        lab: Optional[str] = None,
        faculty_list: Optional[List[str]] = None
    ) -> None:
        add_course(self.cfg, course_id, credits, room, lab, faculty_list)

    # Removes a course from the configuration
    #
    # Parameters:
    #   course -> Course identifier 
    def remove_course (self, course: str) -> None:
        remove_course(self.cfg, course)
    
    # ========== Accessor ==========

    # Returns the current configuration dictionary
    def get_config(self) -> Dict[str, Any]:
        return self.cfg