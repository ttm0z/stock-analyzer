import os
from flask import Flask
from flask_cors import CORS
from .db import db

from .routes.stock_routes import stock_bp
from .routes.test_routes import test_bp

def create_app():
    app = Flask(__name__)

    # Use environment variable or fallback to a local PostgreSQL URI
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL', 
        'postgresql://stockanalyzer:stockanalyzer@localhost:5432/stockdb'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    
    # Enable CORS for your React frontend (adjust origin as needed)
    CORS(app)

    # Import and register your API blueprint
    
    app.register_blueprint(test_bp, url_prefix='/test')
    app.register_blueprint(stock_bp, url_prefix='/api')

    with app.app_context():
        # Create tables if they don't exist
        db.create_all()

    return app

