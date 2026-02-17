"""
NexusAI - Intelligent Code Assistant
Flask application factory with modular configuration.
"""

import logging
from flask import Flask


def create_app(config_class=None):
    """Create and configure the Flask application.

    Args:
        config_class: Optional configuration class override.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__, static_folder='assets')

    # Load configuration
    if config_class:
        app.config.from_object(config_class)
    else:
        from ai_smart_assistant.app.config import Config
        app.config.from_object(Config)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    app.logger.setLevel(logging.INFO)
    app.logger.info('NexusAI starting up...')

    # Register blueprints
    from ai_smart_assistant.app.routes import main
    app.register_blueprint(main)

    app.logger.info('NexusAI initialized successfully')
    return app
