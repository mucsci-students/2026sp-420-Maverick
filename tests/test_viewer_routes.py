# Author: Antonio Corona
# Date: 2026-04-04
"""
test_viewer_routes.py

Tests for viewer_routes.py.

Purpose:
- Ensure schedule viewer page loads successfully
- Validate routing behavior for the viewer endpoint

Notes:
- The real route is /viewer/ (with trailing slash).
"""

from app.web.app import create_app


def test_viewer_route_loads():
    """
    Tests that the viewer page loads successfully.
    """
    app = create_app()
    client = app.test_client()

    response = client.get("/viewer/")

    assert response.status_code == 200


def test_viewer_route_with_query_string():
    """
    Tests that the viewer route still loads when given a query string.
    """
    app = create_app()
    client = app.test_client()

    response = client.get("/viewer/?index=0")

    assert response.status_code == 200