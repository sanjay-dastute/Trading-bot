"""
Web Application Package
"""
from flask import Flask
from src.web.routes.api_keys import api_keys

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)

    # Register blueprints
    app.register_blueprint(api_keys)

    return app
