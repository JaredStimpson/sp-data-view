from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from .db import init_db


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=False)
    root = Path(__file__).resolve().parent.parent
    app.config.from_mapping(
        DATABASE=str(root / "data" / "listening_history.sqlite3"),
        LOG_FILE=str(root / "logs" / "app.log"),
        MAX_CONTENT_LENGTH=2 * 1024 * 1024 * 1024,
        JSON_SORT_KEYS=False,
    )
    if test_config:
        app.config.update(test_config)

    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    Path(app.config["LOG_FILE"]).parent.mkdir(parents=True, exist_ok=True)
    _configure_logging(app)
    init_db(app.config["DATABASE"])

    from .routes import api, pages

    app.register_blueprint(pages)
    app.register_blueprint(api, url_prefix="/api")

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify(error="Upload is larger than the configured 2 GB limit."), 413

    @app.errorhandler(Exception)
    def unhandled(error):
        if isinstance(error, HTTPException):
            return error
        app.logger.exception("Unhandled request error")
        if app.config.get("TESTING"):
            raise error
        return jsonify(error="Unexpected server error. Check the diagnostics log."), 500

    return app


def _configure_logging(app: Flask) -> None:
    for existing in app.logger.handlers[:]:
        if getattr(existing, "_resonance_handler", False):
            app.logger.removeHandler(existing)
            existing.close()
    handler = RotatingFileHandler(
        app.config["LOG_FILE"], maxBytes=2_000_000, backupCount=3, encoding="utf-8"
    )
    handler._resonance_handler = True  # type: ignore[attr-defined]
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(module)s: %(message)s")
    )
    handler.setLevel(logging.DEBUG if app.debug else logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG if app.debug else logging.INFO)
