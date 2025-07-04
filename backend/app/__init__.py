import os
from flask import Flask
from flask_cors import CORS
from .db import db
from .routes.stock_routes import stock_bp
from .routes.test_routes import test_bp
from .services.cache_service import CacheService
from .services.stock_service import StockService

def create_app():
    app = Flask(__name__)
    
    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql://stockanalyzer:stockanalyzer@localhost:5432/stockdb'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    # Initialize Redis cache service
    cache_service = CacheService.create_instance()
    app.cache_service = cache_service
    
    # Initialize enhanced stock service with caching
    fmp_api_key = os.getenv('FMP_API_KEY')
    if not fmp_api_key:
        raise ValueError("FMP_API_KEY environment variable is required")
    
    app.stock_service = StockService(fmp_api_key, cache_service)
    
    # Enable CORS for your React frontend
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(test_bp, url_prefix='/test')
    app.register_blueprint(stock_bp, url_prefix='/api')
    
    # Add admin routes for cache management
    from .routes.admin_routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
    
    return app

