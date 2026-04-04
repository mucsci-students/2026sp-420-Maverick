# Author: Antonio Corona
# Date: 2026-04-04
"""
test_config_routes.py

Tests for config_routes.py.

Purpose:
- Ensure configuration page loads successfully
- Validate routing for config editor UI

Notes:
- The real route is /config/ (with trailing slash).
"""

from app.web.app import create_app


def test_config_route_loads():
    """
    Tests that the config page loads successfully.
    """
    app = create_app()
    client = app.test_client()

    response = client.get("/config/")

    assert response.status_code == 200