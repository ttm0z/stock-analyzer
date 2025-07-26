import os
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .db import db
from .services import init_services
from .routes import register_blueprints
from .cli import register_cli_commands
# Import models to register them with SQLAlchemy
from .models import *  # This imports all models
from .auth.models import User, APIKey


def create_app():
    app = Flask(__name__)

    # Core Configuration
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev')
    database_url = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost:5432/stockdb')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # CORS
    allowed_origins = os.getenv('ALLOWED_ORIGINS', '').split(',')
    CORS(app, 
         origins=[origin.strip() for origin in allowed_origins if origin.strip()],
         supports_credentials=True)

    # Initialize Flask-SQLAlchemy
    db.init_app(app)
    
    # Initialize Flask-Migrate
    migrate = Migrate(app, db)

    # Create tables
    with app.app_context():
        db.create_all()

    # Services
    init_services(app)

    # Blueprints
    register_blueprints(app)

    # CLI Commands
    register_cli_commands(app)

    return app