# Author: Antonio Corona
# Date: 2026-04-04
"""
test_run_routes.py

Tests for run_routes.py.

Purpose:
- Validate that the run route is accessible
- Ensure no crashes when accessing scheduling execution endpoint

Notes:
- The real route is /run/ (with trailing slash).
"""

from app.web.app import create_app


def test_run_route_loads():
    """
    Tests that the run page loads successfully.
    """
    app = create_app()
    client = app.test_client()

    response = client.get("/run/")

    assert response.status_code == 200