# Author: Tanner Ness
# Date: 2026-03-03

from app.web.services.config_service import (
    load_config_into_session,
    get_config_status,
)

def test_load_existing_configuration(app_context, repo_root):
    """Ensures a config can be loaded."""

    path = repo_root / "configs" /"config_base.json"

    load_config_into_session(path)
     
    status = get_config_status()
    assert status["loaded"] is True