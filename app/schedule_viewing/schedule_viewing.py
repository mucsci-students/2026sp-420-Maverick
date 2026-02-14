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

import csv
import sys
from typing import List, Dict, Any

# A function that displays the schedule as a csv file.
# Takes a list of schedule entruies and prints them in a CSV format.
def display_schedule_as_csv(schedule_data: List[Dict[str, Any]]) -> None:
    if not schedule_data:
        print("No schedule data available to display.")
        return
    
    headers = schedule_data[0].keys()

    # Use csv.DictWriter function so that it's formatted correctly, and prints to terminal.
    writer = csv.DictWriter(sys.stdout, fieldnames=headers)
    
    # Print the header row (e.g., course_id, room, time).
    writer.writeheader()
    
    for row in schedule_data:
        writer.writerow(row)


# A function that exports the schedule to a csv file.
def export_schedule_to_csv_file(schedule_data: List[Dict[str, Any]], filename: str = "schedule_output.csv") -> None:
    try:
        if not schedule_data:
            raise ValueError("No data to save.")
            
        headers = schedule_data[0].keys()

        with open(filename, mode='w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(schedule_data)
        print(f"\nSuccessfully exported schedule to {filename}")

    except Exception as e:
        print(f"Error exporting to CSV: {e}")




# Commented out cause we want a CSV not a text file.
"""
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
"""

