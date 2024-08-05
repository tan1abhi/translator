from flask import Flask
from .config import load_configurations, configure_logging
from .view1 import webhook_blueprint
from .model import db

def create_app():
    app = Flask(__name__)

    # Configure the app
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user_states.db'  # or your preferred database
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the database
    db.init_app(app)

    with app.app_context():
        db.create_all()
    
    # Load configurations and logging settings
    load_configurations(app)
    configure_logging()

    # Register blueprints
    app.register_blueprint(webhook_blueprint)

    return app
