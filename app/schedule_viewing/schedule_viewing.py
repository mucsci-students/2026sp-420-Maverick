# Author: Ian Swartz
# Date: 2026-02-13
"""
schedule_viewing.py

Schedule viewing and output formatting module for the scheduler application.

Handles displaying generated schedules in user-friendly formats,
including CSV and terminal-readable output.

Related User Stories:
    D1 — Display Schedules in CSV Format
"""

from typing import Dict, Any


# A function used to display a scheulde.
# Takes the output dictionary from the scheduler and prints it.
def display_schedule(schedule_data: Dict[str, Any]) -> None:
    print("\n" + "="*50)
    print("        FINAL SCHEDULE OUTPUT")
    print("="*50)

    # Structured the same as the scheduler
    if not schedule_data or "schedule" not in schedule_data:
        print("No schedule data found or generation failed.")
        return
    
    # Prints each item that is needed.
    for item in schedule_data["schedule"]:
        course = item.get("course_id", "Unknown")
        room = item.get("room", "No Room")
        time = item.get("time_range", "No Time")

        print(f"Course: {course} | Room: {room} | Time: {time}")
    
    print("="*50 + "\n")


# A function that exports the schedule to a text file.
def export_schedule_to_text(schedule_data: Dict[str, Any], filename: str = "final_schedule.txt") -> None:
    try:
        with open(filename, 'w') as f:
            f.write("Generated Schedule\n")
            f.write("="*20 + "\n")

            for item in schedule_data.get("schedule", []):
                f.write(f"{item}\n")

        print(f"Schedule exported successfully to {filename}")
    
    except Exception as e:
        print(f"Failed to export schedule: {e}")

