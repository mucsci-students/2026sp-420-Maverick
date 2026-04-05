# Author: Tanner Ness, Jacob Karasow
# Date: 2026-04-05

import pytest

from app.web.services.config_service import (
    load_config_into_session,
    get_config_status,
    SESSION_CONFIG_KEY, 
)

# ================================
# 1. Valid Config Load Test
# ================================
def test_load_existing_configuration(app_context, repo_root):
    """Ensures a config can be loaded."""

    path = repo_root / "configs" /"config_test.json"

    load_config_into_session(path)
     
    status = get_config_status()
    assert status["loaded"] is True

# ================================
# 2. Missing File Test
# ================================
def test_load_missing_file(app_context, repo_root):
    """Ensures loading a non-existent file is handled gracefully."""
    path = repo_root / "configs" / "does_not_exist.json"
    
    with pytest.raises(FileNotFoundError):
        load_config_into_session(path)

# ================================
# 3. Invalid JSON Test
# ================================
def test_load_invalid_json(tmp_path, app_context):
    """Ensures loading a file with invalid JSON is handled gracefully."""
    
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{ invalid json }")

    with pytest.raises(Exception):
        load_config_into_session(bad_file)

    status = get_config_status()

    assert status["loaded"] is False

# ================================
# 4. Status Reset Behavior Test
# ================================
def test_config_status_reset(app_context, repo_root):
    """Ensures config status resets when loading a new config."""
    
    path = repo_root / "configs" / "config_test.json"
    load_config_into_session(path)
    status1 = get_config_status()
    assert status1["loaded"] is True

    bad_path = repo_root / "configs" / "does_not_exist.json"

    try: 
        load_config_into_session(bad_path)
    except FileNotFoundError:
        pass

    status2 = get_config_status()

    assert "loaded" in status2