# Author: Tanner Ness, Antonio Corona
# Date: 2026-04-24
"""
Shared generation state for schedule generation progress.

This module intentionally stores lightweight per-session runtime state outside
the Flask session so long-running scheduler jobs can update progress while the
browser polls /run/progress.
"""

from threading import Lock

# progress per session id
generation_progress = {}

# allows only one generation to occur at a time
is_running = {}

generation_errors = {}
generation_results = {}

# simple lock for thread safety
progress_lock = Lock()
