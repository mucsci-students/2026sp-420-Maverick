# Author: Ian Swartz
# Date: 2026-02-13
"""
NOTE:
This module is used for CLI-based schedule output (Sprint 1).

It is NOT currently used by the Flask web application.

Web-based schedule rendering uses:
- schedule_service.py (data prep)
- viewer_routes.py (routing)
- viewer.html (UI)
- app.js (filtering)

Safe to refactor or remove if CLI support is deprecated.
"""

"""
schedule_viewing.py

Schedule viewing and output formatting module for the scheduler application.

Handles displaying generated schedules in user-friendly formats,
including CSV and terminal-readable output.

Related User Stories:
    D1 — Display Schedules in CSV Format
"""

# import csv
# import sys
# from typing import List, Dict, Any

# # A function that displays the schedule as a csv file.
# # Takes a list of schedule entruies and prints them in a CSV format.
# def display_schedule_as_csv(schedule_data: List[Dict[str, Any]]) -> None:
#     if not schedule_data:
#         print("No schedule data available to display.")
#         return

#     headers = schedule_data[0].keys()

#     # Use csv.DictWriter function so that it's formatted correctly, 
#     # and prints to terminal.
#     writer = csv.DictWriter(sys.stdout, fieldnames=headers)

#     # Print the header row (e.g., course_id, room, time).
#     writer.writeheader()

#     for row in schedule_data:
#         writer.writerow(row)


# # A function that exports the schedule to a csv file.
# def export_schedule_to_csv_file(
#     schedule_data: List[Dict[str, Any]],
#     filename: str = "schedule_output.csv",
# ) -> None:
#     try:
#         if not schedule_data:
#             raise ValueError("No data to save.")

#         headers = schedule_data[0].keys()

#         with open(filename, mode='w', newline='') as f:
#             writer = csv.DictWriter(f, fieldnames=headers)
#             writer.writeheader()
#             writer.writerows(schedule_data)
#         print(f"\nSuccessfully exported schedule to {filename}")

#     except Exception as e:
#         print(f"Error exporting to CSV: {e}")
