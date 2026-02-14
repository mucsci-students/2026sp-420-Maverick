# Author: Jacob Karasow
# Date: 2026-02-13
"""
scheduler_execution.py

Scheduler execution module for generating course schedules.

Handles running the scheduler with user-defined options, managing
generation limits, selecting output formats, applying optimization
settings, and saving generated schedules to files.

Related User Stories:
    C1 — Run Scheduler with Options
"""  

import json
import csv
from typing import List, Dict, Any

# Coordinates the full scheduling pipeline.
class SchedulerExecution:

    # Initializes execution parameters.
    #
    # Parameters:
    #   config_file     -> Path to configuration JSON file
    #   limit           -> Maximum number of schedules to generate
    #   output_format   -> csv' or 'json'
    #   output_file     -> Output file path
    #   optimize        -> Whether or not to optimize generated schedules
    def __init__(
        self,
        config_file: str,
        limit: int,
        output_format: str,
        output_file: str,
        optimize: bool = False
    ) -> None:
        self.config_file = config_file
        self.limit = limit
        self.output_format = output_format.lower()
        self.output_file = output_file
        self.optimize = optimize

        self.cfg: Dict[str, Any] = {}

    # ========== Public Execution Method ==========

    # Executes the full scheduling pipeline
    def run(self) -> None:
    
        self._load_config()

        schedules = self._generate_schedules()

        def _optimize_schedules(self, schedules):
            return schedules
        # Added the temporary stub above until the below code is implemented
        # This was throwing an error -AC
        # if self.optimize:
        #     schedules = self._optimize_schedules(schedules)

        schedules = schedules[:self.limit]

        self._write_output(schedules)

    # ========== Internal Methods ==========
 
    # Loads configuration from JSON file
    def _load_config(self) -> None:

        with open(self.config_file, "r") as file:
            self.cfg = json.load(file)

    # Generates Schedules 
    def _generate_schedules(self) -> List[Dict[str, Any]]:
        config = self.cfg.get("config", {})
        courses = config.get("courses", [])
        faculty_list = config.get("faculty", [])
        rooms = config.get("rooms", [])

        schedules: List[Dict[str, Any]] = []

        schedule_id = 1

        for course in courses:
            for faculty in faculty_list:
                for room in rooms:

                    schedule = {
                        "schedule_id": schedule_id,
                        "course": course.get("course_id"),
                        "faculty": faculty.get("name"),
                        "room": room,
                        "credits": course.get("credits")
                    }

                    schedules.append(schedule)
                    schedule_id += 1

        return schedules

    # Writes schedules to file in selected format.
    def _write_output(
        self,
        schedules: List[Dict[str, Any]]
    ) -> None:
        
        if self.output_format == "json":
            self._write_json(schedules)

        elif self.output_format == "csv":
            self._write_csv(schedules)

        else:
            raise ValueError("Unsupported format. Use 'csv' or 'json'.")

    # Writes schedules in JSON format
    def _write_json(
        self,
        schedules: List[Dict[str, Any]]
    ) -> None:
        with open(self.output_file, "w") as file:
            json.dump(schedules, file, indent=4)

    # Writes schedules in CSV format.
    def _write_csv(
        self,
        schedules: List[Dict[str, Any]]
    ) -> None:

        if not schedules:
            return

        with open(self.output_file, "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=schedules[0].keys())
            writer.writeheader()
            writer.writerows(schedules)
