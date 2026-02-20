# Author: Antonio Corona
# Date: 2026-02-20
"""
Schedule Viewing Service

Provides logic for:
- Navigating between schedules
- Transforming schedules into tabular formats
- Importing schedules from file
- Exporting schedules to file

Supports the Schedule Viewer functionality in the Flask GUI.

Acts as part of the Model layer in MVC.
"""

# app/web/services/schedule_service.py
import json
from flask import session

SESSION_SCHEDULES_KEY = "schedules"
SESSION_SELECTED_INDEX_KEY = "selected_schedule_index"


def _get_schedules():
    return session.get(SESSION_SCHEDULES_KEY, [])


def _get_index():
    return int(session.get(SESSION_SELECTED_INDEX_KEY, 0) or 0)


def next_schedule():
    schedules = _get_schedules()
    if not schedules:
        return
    i = min(_get_index() + 1, len(schedules) - 1)
    session[SESSION_SELECTED_INDEX_KEY] = i


def prev_schedule():
    schedules = _get_schedules()
    if not schedules:
        return
    i = max(_get_index() - 1, 0)
    session[SESSION_SELECTED_INDEX_KEY] = i


def export_schedules_to_file(path: str):
    schedules = _get_schedules()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(schedules, f, indent=2)


def import_schedules_from_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        schedules = json.load(f)

    if not isinstance(schedules, list):
        raise ValueError("Imported schedules file must contain a JSON list.")

    session[SESSION_SCHEDULES_KEY] = schedules
    session[SESSION_SELECTED_INDEX_KEY] = 0


def _group_by(assignments, key):
    grouped = {}
    for a in assignments:
        k = a.get(key, "Unknown")
        grouped.setdefault(k, []).append(a)
    return grouped


def get_view_data():
    schedules = _get_schedules()
    i = _get_index()

    current = schedules[i] if schedules and 0 <= i < len(schedules) else None
    assignments = (current or {}).get("assignments", [])

    return {
        "count": len(schedules),
        "index": i,
        "current_meta": (current or {}).get("meta", {}),
        "assignments": assignments,
        "by_room": _group_by(assignments, "room"),
        "by_faculty": _group_by(assignments, "faculty"),
    }
