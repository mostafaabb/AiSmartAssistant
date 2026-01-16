from flask import Flask

def create_app():
    app = Flask(__name__, static_folder='assets')
    from ai_smart_assistant.app.config import Config
    app.config.from_object(Config)

    from ai_smart_assistant.app.routes import main
    app.register_blueprint(main)

    return app
