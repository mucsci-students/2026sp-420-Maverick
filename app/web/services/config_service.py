# Author: Antonio Corona
# Date: 2026-02-20
"""
Configuration Service

Provides business logic for loading, saving, and modifying
the scheduler configuration.

This module wraps the existing Sprint 1 configuration
and management modules to integrate them into the Flask GUI.

Acts as part of the Model layer in MVC.
"""

# app/web/services/config_service.py
import json
from flask import session

SESSION_CONFIG_KEY = "config"
SESSION_CONFIG_PATH_KEY = "config_path"


def load_config_into_session(path: str):
    # Minimal working version: read JSON file and store it in session
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    session[SESSION_CONFIG_KEY] = cfg
    session[SESSION_CONFIG_PATH_KEY] = path


def save_config_from_session(path: str):
    cfg = session.get(SESSION_CONFIG_KEY)
    if cfg is None:
        raise ValueError("No config loaded. Load a config first.")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

    session[SESSION_CONFIG_PATH_KEY] = path


def get_config_status():
    cfg = session.get(SESSION_CONFIG_KEY)
    path = session.get(SESSION_CONFIG_PATH_KEY)

    if not cfg:
        return {"loaded": False, "path": None, "counts": {}}

    # Helpful summary counts (works regardless of exact schema, as long as lists exist)
    counts = {}
    for k in ("faculty", "courses", "rooms", "labs", "conflicts"):
        v = cfg.get(k)
        if isinstance(v, list):
            counts[k] = len(v)

    return {"loaded": True, "path": path, "counts": counts}
