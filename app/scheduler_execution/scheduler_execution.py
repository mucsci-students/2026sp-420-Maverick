# Author: Jacob Karasow & Antonio Corona
# Date: 2026-02-14
"""
NOTE:
This module is currently NOT used by the Flask web application.

The web app directly calls scheduler_core via run_service.py.

This class may be used for CLI or future refactoring.
"""

"""
scheduler_execution.py

Scheduler execution module for generating course schedules.

Handles running the scheduler with user-defined options, managing
generation limits, selecting output formats, applying optimization
settings, and saving generated schedules to files.

Related User Stories:
    C1 — Run Scheduler with Options
"""

# import json
# import csv
# from typing import List, Dict, Any

# from scheduler_core.main import generate_schedules

# # Coordinates the full scheduling pipeline.
# class SchedulerExecution:

#     # Initializes execution parameters.
#     #
#     # Parameters:
#     #   config_file     -> Path to configuration JSON file
#     #   limit           -> Maximum number of schedules to generate
#     #   output_format   -> csv' or 'json'
#     #   output_file     -> Output file path
#     #   optimize        -> Whether or not to optimize generated schedules
#     def __init__(
#         self,
#         config_file: str,
#         limit: int,
#         output_format: str,
#         output_file: str,
#         optimize: bool = False
#     ) -> None:
#         self.config_file = config_file
#         self.limit = limit
#         self.output_format = output_format.lower()
#         self.output_file = output_file
#         self.optimize = optimize

#         self.cfg: Dict[str, Any] = {}

#     # ========== Public Execution Method ==========

#     # Executes the full scheduling pipeline
#     def run(self) -> None:

#         self._load_config()

#         schedules = self._generate_schedules(self.limit, self.optimize)

#         # def _optimize_schedules(self, schedules):
#         #     return schedules
#         # # Added the temporary stub above until the below code is implemented
#         # This was throwing an error -AC
#         if self.optimize:
#             schedules = self._optimize_schedules(schedules)

#         self._write_output(schedules)

#     # ========== Internal Methods ==========

#     # Loads configuration from JSON file
#     def _load_config(self) -> None:

#         with open(self.config_file, "r") as file:
#             self.cfg = json.load(file)

#     def _generate_schedules(self, limit: int, optimize: bool) -> List[Dict[str, Any]]:
#         """
#         Thin wrapper around scheduler_core.main.generate_schedules.

#         SchedulerExecution is responsible for:
#         - loading config JSON into self.cfg
#         - calling core scheduling
#         - writing output (csv/json)

#         scheduler_core is responsible for:
#         - running the solver
#         - converting solver output into flat meeting-level rows
#         """
#         return generate_schedules(self.cfg, limit=limit, optimize=optimize)


#     # Writes schedules to file in selected format.
#     def _write_output(
#         self,
#         schedules: List[Dict[str, Any]]
#     ) -> None:

#         if self.output_format == "json":
#             self._write_json(schedules)

#         elif self.output_format == "csv":
#             self._write_csv(schedules)

#         else:
#             raise ValueError("Unsupported format. Use 'csv' or 'json'.")

#     # Writes schedules in JSON format
#     def _write_json(
#         self,
#         schedules: List[Dict[str, Any]]
#     ) -> None:
#         with open(self.output_file, "w") as file:
#             json.dump(schedules, file, indent=4)

#     def _write_csv(self, schedules):
#         # schedules is a flat List[Dict[str, Any]]
#         if not schedules:
#             print("No schedules generated (solver returned 0 models).")
#             return

#         fieldnames = [
#             "schedule_id",
#             "course_id",
#             "day",
#             "start",
#             "room",
#             "faculty",
#             "lab",
#             "duration",
#             "credits",
#             "meeting_index",
#         ]

#         with open(self.output_file, "w", newline="") as file:
#             writer = csv.DictWriter(file, fieldnames=fieldnames)
#             writer.writeheader()
#             writer.writerows(schedules)


#     def _optimize_schedules(self, schedules: List[Dict[str, Any]]) ->
#       List[Dict[str, Any]]:
#         """
#         Sprint 1 optimization (simple heuristic):
#             (May Change in the future mainly for testing)

#         - If faculty preferences exist in the loaded config,
#           score schedules higher when
#           the schedule's course matches a preferred course for that faculty.
#         - Tie-breakers so output is deterministic.
#         - Returns schedules sorted best -> worst.
#         """
#         if not schedules:
#             print("No schedules generated (solver returned 0 models).")
#             return schedules

#         config = self.cfg.get("config", {})
#         faculty_list = config.get("faculty", [])

#         # faculty_name -> {course_id: weight}
#         pref_map: Dict[str, Dict[str, int]] = {}
#         for f in faculty_list:
#             name = f.get("name")
#             if not name:
#                 continue

#             weights: Dict[str, int] = {}
#             for p in (f.get("preferences") or []):
#                 course_id = p.get("course_id")
#                 weight = p.get("weight")
#                 if course_id is None or weight is None:
#                     continue
#                 try:
#                     weights[str(course_id)] = int(weight)
#                 except (TypeError, ValueError):
#                     continue

#             pref_map[str(name)] = weights

#         def score(schedule: Dict[str, Any]) -> int:
#             faculty_name = str(schedule.get("faculty", ""))
#             course_id = str(schedule.get("course_id", ""))

#             pref_score = pref_map.get(faculty_name, {}).get(course_id, 0)
#             room_bonus = 1 if schedule.get("room") else 0

#             credits_val = schedule.get("credits")
#             try:
#                 credits_bonus = int(credits_val) if credits_val is not None else 0
#             except (TypeError, ValueError):
#                 credits_bonus = 0

#             return (pref_score * 100) + (credits_bonus * 2) + room_bonus

#         return sorted(
#             schedules,
#             key=lambda s: (
#                 score(s),
#                 str(s.get("course_id", "")),
#                 str(s.get("faculty", "")),
#                 str(s.get("room", "")),
#                 int(s.get("schedule_id", 0))
#                   if str(s.get("schedule_id", "0")).isdigit() else 0,
#             ),
#             reverse=True,
#         )
