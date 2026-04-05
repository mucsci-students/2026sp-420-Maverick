# Author: Antonio Corona
# Date: 2026-04-05
"""
Flask Application Factory

This module defines the create_app() function, which initializes
and configures the Flask application.

Responsibilities:
- Create the Flask app instance
- Configure Flask settings
- Configure server-side sessions
- Register blueprints (routes)
- Support local/runtime configuration for secret key loading

This serves as the main entry point for the web-based GUI.
"""

# app/web/app.py

from flask import Flask
from flask_session import Session

from app.config_runtime import get_flask_secret_key

def create_app():
    """
    Application factory for the Maverick Scheduler Flask app.
    """
    app = Flask(__name__)

    # ---------------------------------------------------------
    # Core Flask configuration
    # ---------------------------------------------------------
    # Load the secret key from app/local_settings.py first,
    # then environment variables, then a development fallback.
    app.config["SECRET_KEY"] = get_flask_secret_key()

    # ---------------------------------------------------------
    # Flask-Session configuration
    # ---------------------------------------------------------
    # Store session data on the filesystem so config editing and
    # working state persist across requests during local use.
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_FILE_DIR"] = "/tmp/flask_sessions"

    # Initializes server-side sessions
    Session(app)

    # ---------------------------------------------------------
    # Optional startup warning for missing OpenAI key
    # ---------------------------------------------------------
    # This does not stop the app from starting, because non-AI routes
    # should still work even if AI is not configured.
    if not get_openai_api_key():
        print(
            "Warning: OpenAI API key not found. "
            "Set OPENAI_API_KEY in app/local_settings.py or your environment "
            "to use the AI Chat Tool."
        )

    # ---------------------------------------------------------
    # Register blueprints
    # ---------------------------------------------------------
    from app.web.routes.config_routes import bp as config_bp
    from app.web.routes.run_routes import bp as run_bp
    from app.web.routes.viewer_routes import bp as viewer_bp
    from app.web.routes.ai_routes import bp as ai_bp

    app.register_blueprint(config_bp)
    app.register_blueprint(run_bp)
    app.register_blueprint(viewer_bp)
    app.register_blueprint(ai_bp)

    # ---------------------------------------------------------
    # Simple home redirect
    # ---------------------------------------------------------
    @app.get("/")
    def home():
        return '<meta http-equiv="refresh" content="0; url=/config">'

    return app
