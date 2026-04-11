# Author: Antonio Corona, Tanner Ness
# Date: 2026-03-03
"""
Pytest Fixtures for Configuration-Based Tests

Purpose:
    Provides reusable pytest fixtures for loading and isolating
    configuration data used in unit tests.

Primary Responsibilities:
    - Resolve repository root dynamically.
    - Load test configuration JSON from disk.
    - Provide a fresh deep-copied config per test.

Design Principles:
    - Tests must not mutate shared state.
    - Each test receives an isolated configuration instance.
    - File paths are computed dynamically to avoid hardcoding.

Architectural Context:
    - Supports Model-layer unit tests (faculty, room, lab, course, etc.).
    - Ensures deterministic test behavior.
    - Prevents cross-test side effects.
"""

# --------------------------------------------------
# Imports
# --------------------------------------------------

import copy  # Deep copy to isolate test state
import json  # JSON file parsing
from pathlib import Path  # Filesystem path resolution (cross-platform safe)

import pytest  # Pytest framework for fixtures
from flask import Flask

# ==================================================
# Fixture: Repository Root
# ==================================================


@pytest.fixture
def repo_root() -> Path:
    """
    Resolves the repository root directory dynamically.

    Returns:
        Path:
            Absolute path to the project root directory.

    Implementation Detail:
        __file__ → current test file
        .resolve() → absolute path
        .parents[1] → move up two levels to repo root

    Rationale:
        Avoids hardcoding paths so tests remain portable.
    """
    return Path(__file__).resolve().parents[1]


# ==================================================
# Fixture: Test Configuration Loader
# ==================================================


@pytest.fixture
def config_test(repo_root):
    """
    Loads configs/config_base.json into memory.

    Parameters:
        repo_root (Path):
            Injected fixture providing repository root directory.

    Returns:
        dict:
            Parsed JSON configuration as a Python dictionary.

    Design Rationale:
        - Provides a canonical test config for all tests.
        - Ensures tests start from known, stable data.
    """

    path = repo_root / "configs" / "config_test.json"

    # Open file safely with explicit UTF-8 encoding
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


# ==================================================
# Fixture: Isolated Example Config
# ==================================================


@pytest.fixture
def example(config_test):
    """
    Provides a deep-copied configuration instance per test.

    Parameters:
        config_test(dict):
            test configuration loaded from disk.

    Returns:
        dict:
            Fresh deep copy of configuration.

    Critical Design Note:
        Tests frequently mutate the configuration (add/remove entities).
        Using deepcopy ensures:
            - No shared state between tests.
            - No mutation of config_test.
            - Deterministic, isolated test behavior.
    """

    return copy.deepcopy(config_test)


# ==================================================
# Fixture: Create flask application
# ==================================================
@pytest.fixture
def app():
    """
    creates and configures a flask application for testing
    """
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    return app


# ==================================================
# Fixture: Create flask application context
# ==================================================


@pytest.fixture
def app_context(app):
    """
    Create a request context for testing.
    """
    with app.test_request_context():
        yield app
