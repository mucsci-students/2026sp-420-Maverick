# app/web/services/run_service.py
from flask import session
from copy import deepcopy
from datetime import datetime

from app.web.services.config_service import SESSION_CONFIG_KEY

SESSION_SCHEDULES_KEY = "schedules"
SESSION_SELECTED_INDEX_KEY = "selected_schedule_index"


def generate_schedules_into_session(limit: int, optimize: bool) -> int:
    """
    Minimal working placeholder:
    - Requires a config be loaded (so flow matches your real app)
    - Generates fake schedules so Viewer can be demo'd today
    Replace the placeholder section with SchedulerExecution when ready.
    """
    cfg = session.get(SESSION_CONFIG_KEY)
    if not cfg:
        raise ValueError("No config loaded. Load a config first in Config Editor.")

    run_cfg = deepcopy(cfg)  # so you can apply overrides without mutating saved config

    # --- PLACEHOLDER SCHEDULE GENERATION ---
    # TODO: Replace with your real scheduler call, e.g.
    # from app.scheduler_execution.scheduler_execution import SchedulerExecution
    # executor = SchedulerExecution()
    # schedules = executor.run_scheduler(...)

    schedules = []
    for i in range(max(0, limit)):
        schedules.append({
            "meta": {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "optimize": optimize,
                "index": i,
            },
            "assignments": [
                # fake rows; replace with real schedule output
                {"course": "CS101", "room": "R101", "faculty": "Dr. Smith", "time": "MWF 09:00"},
                {"course": "CS102", "room": "R102", "faculty": "Dr. Smith", "time": "MWF 10:00"},
            ],
        })

    session[SESSION_SCHEDULES_KEY] = schedules
    session[SESSION_SELECTED_INDEX_KEY] = 0
    return len(schedules)
