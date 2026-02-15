# scheduler_core/main.py
# scheduler_core/main.py
from typing import Any, Dict, List
from scheduler import Scheduler
from scheduler.config import CombinedConfig

def _rows_from_course_as_csv(schedule_id: int, course_obj: Any) -> List[Dict[str, Any]]:
    """
    Turns one course model into 1+ CSV rows.
    We rely on course.as_csv() (documented by the library) and then parse it.
    """
    line = course_obj.as_csv()  # documented usage
    parts = [p.strip() for p in line.split(",")]

    # We don't know exact column order across versions, so we store it safely.
    # Also: many schedulers return one row per meeting already.
    row = {
        "schedule_id": schedule_id,
        "raw": line,
    }

    # If the library's as_csv format is stable in your team, map indexes:
    # Example guess: course_id, day, start, room, faculty, lab
    if len(parts) >= 6:
        row.update({
            "course_id": parts[0],
            "day": parts[1],
            "start": parts[2],
            "room": parts[3],
            "faculty": parts[4],
            "lab": parts[5],
        })
    return [row]

def generate_schedules(cfg: Dict[str, Any], limit: int, optimize: bool) -> List[Dict[str, Any]]:
    combined = CombinedConfig(**cfg)
    s = Scheduler(combined)

    rows: List[Dict[str, Any]] = []
    for schedule_id, schedule in enumerate(s.get_models(), start=1):
        for course in schedule:
            rows.extend(_rows_from_course_as_csv(schedule_id, course))
        if schedule_id >= limit:
            break
    return rows
