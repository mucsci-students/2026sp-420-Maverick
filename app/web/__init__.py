# Author: Antonio Corona
# Date: 2026-02-20
"""
Flask Web Package Initialization

This package contains the Sprint 2 Flask web application for the
Scheduler project. It provides the GUI layer built on top of the
existing Sprint 1 CLI and core scheduling logic.

The create_app() function is exposed here for Flask to discover
the application factory.
"""

# app/web/__init__.py
from app.web.app import create_app as create_app