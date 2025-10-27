from flask import Flask

def create_app() -> Flask:
    """Application factory to create Flask app instances."""
    app = Flask(__name__)

    from .api.routes import api_bp

    app.register_blueprint(api_bp, url_prefix="/api")

    return app
