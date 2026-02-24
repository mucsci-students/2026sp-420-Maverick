# Author: Antonio Corona
# Date: 2026-02-23
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
from typing import Any, Dict, List, Optional  # Type hints for clarity

from app.web.services.config_service import SESSION_CONFIG_KEY
from scheduler_core.main import generate_schedules  # Core solver engine


# ----------------------------------
# Session Keys (Key Sources of Date)
# ----------------------------------

# Stores generated schedules in the Flask session
SESSION_SCHEDULES_KEY = "schedules"

# Stores currently selected schedule index for navigation
SESSION_SELECTED_INDEX_KEY = "selected_schedule_index"


# -------------------------------------------------
# Optimization Flag Constants (UI & Config Bridge)
# -------------------------------------------------
# These represent all valid optimizer flags supported
# by the scheduling engine. The UI may select any subset
# of these, and per-run overrides are validated against
# this list.

KNOWN_OPTIMIZER_FLAGS = [
    "faculty_course",
    "faculty_room",
    "faculty_lab",
    "same_room",
    "same_lab",
    "pack_rooms",
]


# ------------------------------
# Utility Functions
# ------------------------------

def _to_int(x: Any, default: int = 0) -> int:
    """
    Safely convert a value to int.

    Used primarily when grouping solver rows by schedule_id,
    since solver output may return numeric values as strings.
    """
    try:
        return int(x)
    except Exception:
        return default


# ------------------------------
# Core Service Function
# ------------------------------

def generate_schedules_into_session(limit: int, optimizer_flags: Optional[List[str]] = None) -> int:
    """
    Executes the scheduling engine and stores results in session state.

    Parameters:
        limit (int):
            Maximum number of schedules to generate (override value).

        optimizer_flags (Optional[List[str]]):
            List of optimizer flags selected in the UI.
            - If None, defaults to flags defined in loaded JSON config.
            - If empty list, runs without optimization preferences.

    Returns:
        int:
            Number of schedules successfully generated.

    Raises:
        ValueError:
            If no configuration is currently loaded in session.

    Design Notes:
        - This function does NOT mutate the original config.
        - Per-run overrides affect only the in-memory copy.
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
    # the saved configuration stored in session.

    run_cfg = deepcopy(cfg)


    # ----------------------------------------
    # 3. Apply Per-Run Overrides (Generator UI)
    # ----------------------------------------

    # Override schedule generation limit
    # (Ensures consistency between config and solver call)
    run_cfg["limit"] = limit

    # ----------------------------------------------------
    # Optimization Flag Override Logic
    # ----------------------------------------------------
    # Behavior:
    #   - If UI did not submit flags (None), default to
    #     JSON configuration values.
    #   - If UI submitted flags (including empty list),
    #     use exactly what user selected.
    #   - Validate against KNOWN_OPTIMIZER_FLAGS for safety.
    # ----------------------------------------------------
    if optimizer_flags is None:
        # No UI override → use JSON defaults
        optimizer_flags = run_cfg.get("optimizer_flags", []) or []

    # Filter out any unknown flags (defensive validation)
    optimizer_flags = [
        flag for flag in optimizer_flags
        if flag in KNOWN_OPTIMIZER_FLAGS
    ]

    # Apply override to in-memory config
    run_cfg["optimizer_flags"] = optimizer_flags

    # Core currently doesn't use optimize bool, but kept it for future compatibility
    optimize = len(optimizer_flags) > 0


    # --------------------------------
    # 4. Invoke Core Scheduler Engine
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
    # 5. Transform Flat Rows -> Grouped Schedules
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
    # 6. Build Final Schedule Objects
    # --------------------------------
    
    schedules: List[Dict[str, Any]] = []

    for sid in sorted(grouped.keys()):
        schedules.append({
            "meta": {
                "schedule_id": sid,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "optimizer_flags": optimizer_flags,   # Store actual flags used
                "row_count": len(grouped[sid]),
            },
            "assignments": grouped[sid],
        })


    # ----------------------------------------
    # 7. Persist in Session for Viewer Layer
    # ----------------------------------------
    # Store for Viewer navigation
    
    session[SESSION_SCHEDULES_KEY] = schedules
    session[SESSION_SELECTED_INDEX_KEY] = 0     # Reset navigation to first schedule

    return len(schedules)
