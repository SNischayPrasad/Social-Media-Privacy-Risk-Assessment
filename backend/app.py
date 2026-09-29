"""
Flask application factory - Social Media Privacy Risk Assessment Framework.

Run from the project root:
    python run.py

The same Flask server serves:
    * the REST API under /api/...
    * the static frontend (frontend/ folder) at http://127.0.0.1:5000/
Serving both from one origin avoids CORS configuration entirely.
"""

import logging
import os

from flask import Flask, jsonify, send_from_directory
from werkzeug.exceptions import HTTPException

from backend.config import Config
from backend.models.database import Database
from backend.routes.assessment_routes import assessment_bp
from backend.routes.dashboard_routes import dashboard_bp
from backend.utils.security import apply_security_headers
from backend.utils.validators import ValidationError


def create_app(config_class=Config, overrides=None):
    """Create and configure the Flask app."""
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config_class)
    if overrides:
        app.config.update(overrides)
    app.json.sort_keys = False  # keep category order A-J in JSON responses

    # ---------------------------------------------------------------- database
    db_path = app.config["DATABASE_PATH"]
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    database = Database(db_path)
    database.init_schema()
    purged = database.purge_older_than(app.config["RETENTION_DAYS"])
    if purged:
        app.logger.info("Retention policy removed %s expired assessment(s).", purged)
    app.config["DB"] = database

    # ---------------------------------------------------------------- routes
    app.register_blueprint(assessment_bp)
    app.register_blueprint(dashboard_bp)
    app.after_request(apply_security_headers)

    frontend_dir = app.config["FRONTEND_DIR"]

    @app.get("/")
    def index():
        return send_from_directory(frontend_dir, "index.html")

    @app.get("/<path:filename>")
    def frontend_files(filename):
        # send_from_directory blocks path traversal such as ../../secret
        return send_from_directory(frontend_dir, filename)

    # ---------------------------------------------------------------- errors
    @app.errorhandler(ValidationError)
    def handle_validation(error):
        return jsonify(error="Validation failed.", details=error.errors), 400

    @app.errorhandler(HTTPException)
    def handle_http(error):
        return jsonify(error=error.description or error.name), error.code

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        # Log details server-side; never send stack traces to the client.
        app.logger.exception("Unhandled error: %s", error)
        return jsonify(error="An internal error occurred."), 500

    return app


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    application = create_app()
    application.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
