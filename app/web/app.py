# Author: Antonio Corona
# Date: 2026-04-26
"""
File: app/web/app.py
Purpose: Define the Flask application factory for the Maverick Scheduler web GUI.

Responsibilities:
- Create and configure the Flask app instance
- Configure server-side sessions and runtime settings
- Register route blueprints for core web features
- Inject global template state for Viewer / Editor mode
- Enforce read-only request behavior while in Viewer Mode

Notes:
- This module serves as the main entry point for the web-based GUI.
- Secret key and OpenAI API key values are loaded through runtime configuration helpers.
"""

from flask import Flask
from flask_session import Session

from app.config_runtime import get_flask_secret_key, get_openai_api_key


def create_app():
    """
    Create, configure, and return the Maverick Scheduler Flask application.

    The factory pattern keeps app setup centralized while supporting test and
    local runtime initialization.
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
    # Store session data on the filesystem so configuration state and UI mode
    # persist across requests during local development and testing.
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_FILE_DIR"] = "/tmp/flask_sessions"

    # Initialize server-side session management.
    Session(app)

    # ---------------------------------------------------------
    # Optional startup warning for missing OpenAI key
    # ---------------------------------------------------------
    # The application remains fully usable without AI functionality;
    # only AI-powered features depend on this configuration.
    if not get_openai_api_key():
        print(
            "Warning: OpenAI API key not found. "
            "Set OPENAI_API_KEY in app/local_settings.py or your environment "
            "to use the AI Chat Tool. "
            "Missing OpenAI API key. Set it in app/local_settings.py "
            "or as an environment variable."
        )

    # ---------------------------------------------------------
    # Register blueprints
    # ---------------------------------------------------------
    # Blueprints separate concerns across configuration, execution,
    # AI interaction, and schedule viewing functionality.
    from app.web.routes.ai_routes import bp as ai_bp
    from app.web.routes.config_routes import bp as config_bp
    from app.web.routes.run_routes import bp as run_bp
    from app.web.routes.viewer_routes import bp as viewer_bp

    app.register_blueprint(config_bp)
    app.register_blueprint(run_bp)
    app.register_blueprint(viewer_bp)
    app.register_blueprint(ai_bp)

    # ---------------------------------------------------------
    # Simple home redirect
    # ---------------------------------------------------------
    @app.get("/")
    def home():
        """Redirect the root route to the configuration UI."""
        return '<meta http-equiv="refresh" content="0; url=/config">'

    # ---------------------------------------------------------
    # Template context injection
    # ---------------------------------------------------------
    @app.context_processor
    def inject_mode():
        """
        Inject Viewer / Editor mode state into all Jinja templates.

        This allows templates to conditionally show, hide, or disable editing
        controls without each route manually passing the same context values.
        """
        from app.web.services.mode_service import get_mode, is_editor, is_viewer

        return {
            "app_mode": get_mode(),
            "is_viewer_mode": is_viewer(),
            "is_editor_mode": is_editor(),
        }

    return app
