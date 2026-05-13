"""
NexusAI - Intelligent Code Assistant
Flask application factory with modular configuration.
"""

import logging
import os

from flask import Flask, jsonify, request
from werkzeug.middleware.proxy_fix import ProxyFix

from ai_smart_assistant.app.config import enforce_production_secrets, select_config


def create_app(config_class=None):
    """Create and configure the Flask application.

    Args:
        config_class: Optional configuration class override.

    Returns:
        Configured Flask application instance.
    """
    enforce_production_secrets()

    app = Flask(__name__, static_folder="assets")

    if config_class:
        app.config.from_object(config_class)
    else:
        app.config.from_object(select_config())

    if app.config.get("TRUST_PROXY"):
        app.wsgi_app = ProxyFix(
            app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
        )

    # Logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    app.logger.setLevel(logging.INFO)
    app.logger.info("NexusAI starting up (env=%s)", app.config.get("ENV"))

    _register_security_headers(app)
    _register_error_handlers(app)

    from ai_smart_assistant.app.extensions import limiter

    # Flask-Limiter 4.x: configure via app.config, then init_app(app)
    if app.config.get("RATELIMIT_ENABLED"):
        app.config.setdefault(
            "RATELIMIT_DEFAULT", "400 per hour; 120 per minute"
        )
    else:
        app.config["RATELIMIT_ENABLED"] = False

    limiter.init_app(app)

    from ai_smart_assistant.app.routes import main

    app.register_blueprint(main)

    app.logger.info("NexusAI initialized successfully")
    return app


def _register_security_headers(app: Flask) -> None:
    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()",
        )
        if (
            app.config.get("ENV") == "production"
            and app.config.get("PREFERRED_URL_SCHEME") == "https"
        ):
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        return response


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(_e):
        if (
            request.path.startswith("/api/")
            or request.accept_mimetypes.best == "application/json"
        ):
            return jsonify({"error": "Not found"}), 404
        return (
            "<h1>Not found</h1><p>The page you requested does not exist.</p>",
            404,
        )

    @app.errorhandler(500)
    def internal_error(_e):
        app.logger.exception("Unhandled server error")
        if (
            request.path.startswith("/api/")
            or request.accept_mimetypes.best == "application/json"
        ):
            return jsonify({"error": "Internal server error"}), 500
        return (
            "<h1>Something went wrong</h1><p>Please try again later.</p>",
            500,
        )

    @app.errorhandler(413)
    def too_large(_e):
        return jsonify({"error": "Payload too large"}), 413

    @app.errorhandler(429)
    def ratelimited(_e):
        return jsonify({"error": "Too many requests. Please slow down."}), 429
