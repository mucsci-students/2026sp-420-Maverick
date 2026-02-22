# Author: Antonio Corona
# Date: 2026-02-21
"""
Schedule Execution Service

Purpose:
    Provides business logic for running the scheduler from the Flask web interface.

Architectural Role (MVC):
    - Acts as part of the Model layer.
    - Responsible for invoking the scheduling engine.
    - Transforms scheduler output into a structure suitable for the View layer.
    - Persists generated schedules in session state for navigation.

High-Level Flow:
    1. Retrieve configuration from session.
    2. Apply per-run overrides (limit, optimize).
    3. Invoke scheduler_core.generate_schedules().
    4. Group flat solver rows into schedule objects.
    5. Store schedules in session for the Viewer.
"""

# ------------------------------
# Imports
# ------------------------------

from flask import session                     # Session storage for per-user state
from copy import deepcopy                     # Prevent mutation of loaded config
from datetime import datetime                 # Timestamp metadata for schedules
from typing import Any, Dict, List            # Type hints for clarity

from app.web.services.config_service import SESSION_CONFIG_KEY
from scheduler_core.main import generate_schedules  # Core solver engine


# ----------------------------------
# Session Keys (Key Sources of Date)
# ----------------------------------

# Stores generated schedules in the Flask session
SESSION_SCHEDULES_KEY = "schedules"

# Stores currently selected schedule index for navigation
SESSION_SELECTED_INDEX_KEY = "selected_schedule_index"


# ------------------------------
# Utility Functions
# ------------------------------

def _to_int(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return default


# ------------------------------
# Core Service Function
# ------------------------------

def generate_schedules_into_session(limit: int, optimize: bool) -> int:
    """
    Executes the scheduling engine and stores results in session state.

    Parameters:
        limit (int):
            Maximum number of schedules to generate (override value).

        optimize (bool):
            Whether to apply optimization flags in the solver.

    Returns:
        int:
            Number of schedules successfully generated.

    Raises:
        ValueError:
            If no configuration is currently loaded in session.

    Design Notes:
        - This function does NOT mutate the original config.
        - It transforms solver output (flat rows) into grouped schedules.
        - It prepares data in a format optimized for the Viewer layer.
    """

    # ----------------------------------------
    # 1. Retrieve Configuration
    # ----------------------------------------
    # Get loaded config 

    cfg = session.get(SESSION_CONFIG_KEY)

    if not cfg:
        # Explicit error instead of silent failure
        raise ValueError("No config loaded. Load a config first in Config Editor.")


    # ----------------------------------
    # 2. Protect Original Configuration
    # ----------------------------------
    # Copy so we don't mutate saved config 

    # Use deepcopy to ensure overrides do not modify the saved configuration.
    run_cfg = deepcopy(cfg)


    # --------------------------------
    # 3. Invoke Core Scheduler Engine
    # --------------------------------

    # --- REAL SCHEDULER CALL ---
    # The scheduler returns a flat list of assignment rows.
    # Each row corresponds to one meeting instance.
    flat_rows: List[Dict[str, Any]] = generate_schedules(
        run_cfg,
        limit=limit,
        optimize=optimize
    )


    # --------------------------------------------
    # 4. Transform Flat Rows -> Grouped Schedules
    # --------------------------------------------

    # Group rows by schedule_id for Viewer to navigate
    grouped: Dict[int, List[Dict[str, Any]]] = {}

    for row in flat_rows:
        sid = _to_int(row.get("schedule_id"), default=1)

        grouped.setdefault(sid, []).append({
            # fields returned by scheduler_core
            "schedule_id": sid,
            "course_id": row.get("course_id", ""),
            "day": row.get("day", ""),
            "start": row.get("start", ""),
            "room": row.get("room", ""),
            "faculty": row.get("faculty", ""),
            "lab": row.get("lab", ""),
            "duration": row.get("duration", ""),
            "credits": row.get("credits", ""),
            "meeting_index": row.get("meeting_index", ""),

            # Convenience field for UI display
            "time": f"{row.get('day','')} {row.get('start','')}".strip()
        })


    # --------------------------------
    # 5. Build Final Schedule Objects
    # --------------------------------
    
    schedules: List[Dict[str, Any]] = []

    for sid in sorted(grouped.keys()):
        schedules.append({
            "meta": {
                "schedule_id": sid,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "optimize": optimize,
                "row_count": len(grouped[sid]),
            },
            "assignments": grouped[sid],
        })


    # ----------------------------------------
    # 6. Persist in Session for Viewer Layer
    # ----------------------------------------
    # Store for Viewer navigation
    
    session[SESSION_SCHEDULES_KEY] = schedules
    session[SESSION_SELECTED_INDEX_KEY] = 0     # Reset navigation to first schedule

    return len(schedules)
