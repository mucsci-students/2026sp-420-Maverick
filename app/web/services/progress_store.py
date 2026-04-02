# Author: Tanner Ness
# Date: 2026-03-08

from threading import Lock

# progress per session id
generation_progress = {}

# allows only one generation to occur at a time
is_running = {}

# simple lock for thread safety
progress_lock = Lock()


