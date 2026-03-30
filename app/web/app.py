# Author: Antonio Corona
# Date: 2026-02-20
"""
Flask Application Factory

This module defines the create_app() function, which initializes
and configures the Flask application for Sprint 2.

Responsibilities:
- Create the Flask app instance
- Register blueprints (routes)
- Configure basic settings (secret key, etc.)

This serves as the main entry point for the web-based GUI.
"""

# app/web/app.py
import os
from flask import Flask
from flask_session import Session

def create_app():
    app = Flask(__name__)

    # Needed for session + flash messages
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")


    # Flask Session configuration
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_FILE_DIR"] = "/tmp/flask_sessions"

    # Initializes server-side sessions
    Session(app)

    # Blueprints (routes)
    from app.web.routes.config_routes import bp as config_bp
    from app.web.routes.run_routes import bp as run_bp
    from app.web.routes.viewer_routes import bp as viewer_bp

    app.register_blueprint(config_bp)
    app.register_blueprint(run_bp)
    app.register_blueprint(viewer_bp)

    # Simple home redirect
    @app.get("/")
    def home():
        return '<meta http-equiv="refresh" content="0; url=/config">'

    return app
