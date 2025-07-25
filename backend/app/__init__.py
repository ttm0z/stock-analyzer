import os
from flask import Flask
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models.base import Base
from .services import init_services
from .routes import register_blueprints
from .cli import register_cli_commands
from .database import init_db_session_handlers
# Import all models to register them with Base.metadata
from .models import *  # This imports all models
from .auth.models import User, APIKey


def create_app():
    app = Flask(__name__)

    # Core Configuration
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev')
    database_url = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost:5432/stockdb')
    app.config['DATABASE_URL'] = database_url

    # CORS
    allowed_origins = os.getenv('ALLOWED_ORIGINS', '').split(',')
    CORS(app, 
         origins=[origin.strip() for origin in allowed_origins if origin.strip()],
         supports_credentials=True)

    # Database setup with SQLAlchemy Core
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    
    # Store session factory in app config
    app.config['SESSION_FACTORY'] = Session

    # Database session handlers
    init_db_session_handlers(app)

    # Services
    init_services(app)

    # Blueprints
    register_blueprints(app)

    # CLI Commands
    register_cli_commands(app)

    return app