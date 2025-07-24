import os
from flask import Flask
from flask_cors import CORS
from .db import db
from .routes.stock_routes import stock_bp
from .routes.test_routes import test_bp
from .routes.auth_routes import auth_bp
from .routes.portfolio_routes import portfolio_bp
from .routes.strategy_routes import strategy_bp
from .routes.backtest_routes import backtest_bp
from .services.cache_service import CacheService
from .services.stock_service import StockService

def create_app():
    app = Flask(__name__)
    
    # Security Configuration
    app.secret_key = os.getenv('FLASK_SECRET_KEY')
    if not app.secret_key:
        raise ValueError("FLASK_SECRET_KEY environment variable is required")
    
    app.config['SECRET_KEY'] = app.secret_key
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') != 'development'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql://stockuser:change_this_password@localhost:5432/stockdb'
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
    
    # Enable CORS with restricted origins
    allowed_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
    CORS(app, origins=[origin.strip() for origin in allowed_origins], 
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization', 'X-CSRF-Token', 'X-Request-Timestamp'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # Register blueprints
    app.register_blueprint(test_bp, url_prefix='/test')
    app.register_blueprint(stock_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(portfolio_bp, url_prefix='/api/portfolios')
    app.register_blueprint(strategy_bp, url_prefix='/api/strategies')
    app.register_blueprint(backtest_bp, url_prefix='/api/backtests')
    
    # Add admin routes for cache management
    from .routes.admin_routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    with app.app_context():
        # Create tables if they don't exist
        try:
            db.create_all()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not create database tables: {e}")
            logger.info("Database tables may need to be created manually")
    
    return app

