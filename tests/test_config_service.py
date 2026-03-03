# Author: Tanner Ness
# Date: 2026-03-03

from app.web.services.config_service import (
    load_config_into_session,
    get_config_status,
)

Path = "configs/config_base.json"

def test_load_existing_configuration(app_context):
    """Ensures a config can be loaded."""
    load_config_into_session(Path)
     
    status = get_config_status()
    assert status["loaded"] is True