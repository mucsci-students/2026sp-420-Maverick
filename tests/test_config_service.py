# Author: Tanner Ness,

import pytest
from flask import Flask

from app.web.services.config_service import (
    load_config_into_session,
    get_config_status,
)


@pytest.fixture
def app():
    """
    creates and configures a flask application for testing
    """
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    return app


@pytest.fixture
def app_context(app):
    """
    Create a request context for testing.
    """
    with app.test_request_context():
        yield app


def test_load_existing_configuration(app_context):

    load_config_into_session('configs/config_base.json')
     
    status = get_config_status()
    assert status['loaded'] is True