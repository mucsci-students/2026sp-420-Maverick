# Author: Antonio Corona
# Date: 2026-04-13
"""
Runtime configuration helpers for Maverick Scheduler.

Configuration lookup order:
1. Environment variables
2. Safe defaults where appropriate
"""

import os

OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
FLASK_SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
MAVERICK_OPENAI_MODEL: str = os.getenv("MAVERICK_OPENAI_MODEL", "gpt-5-mini")