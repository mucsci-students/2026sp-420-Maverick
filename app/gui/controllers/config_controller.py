# Author: 
# Date: 2026-02-18
"""
ConfigController — Configuration Editing Logic

Handles:
    - Loading configuration files
    - Saving configuration files
    - Faculty CRUD operations
    - Course CRUD operations
    - Room CRUD operations
    - Lab CRUD operations
    - Conflict management

This controller acts as a GUI wrapper around the
existing Sprint 1 configuration and management modules.

All changes modify AppState and then notify Views to refresh.
"""
