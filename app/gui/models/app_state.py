# Author: 
# Date: 2026-02-18
"""
AppState — Central Application Model (MVC)

This module defines the in-memory state container used by the GUI.

Responsibilities:
    - Store loaded configuration data
    - Store generated schedules
    - Track selected schedule index
    - Track configuration and schedule file paths
    - Store temporary override values (limit, optimization flags)

AppState acts as the single source of truth for the GUI layer.
Views should read from AppState, and Controllers should modify it.
"""
