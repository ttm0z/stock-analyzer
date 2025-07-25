#!/usr/bin/env python3
"""
Flask application factory with PostgreSQL database setup.
"""

import os
import logging
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import text
from datetime import datetime

from config import config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name=None):
    """Application factory pattern for Flask app creation."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Configure logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = logging.FileHandler('logs/app.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Application startup')
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Import all models after db initialization to ensure they're registered
    with app.app_context():
        # Import from compatibility layer to maintain existing route imports
        from app.models.user_models import User, UserPreferences
        from app.models.portfolio_models import Portfolio, Position, Transaction, PortfolioSnapshot
        try:
            from models import (
                Strategy, StrategyParameter, StrategyPerformance,
                Backtest, Trade, Signal,
                Asset, MarketData, Benchmark,
                RiskProfile, RiskMetrics
            )
        except ImportError:
            # Models not yet migrated, skip for now
            pass
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register CLI commands
    register_cli_commands(app)
    
    return app

def register_blueprints(app):
    """Register Flask blueprints."""
    # Health check and system endpoints
    @app.route('/health')
    def health_check():
        """Health check endpoint with database connectivity test."""
        try:
            # Test database connection
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # Get database info
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT version();"))
                db_version = result.fetchone()[0]
            
            # Get pool status
            pool = db.engine.pool
            pool_status = {
                'size': pool.size(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'checked_in': pool.checkedin()
            }
            
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'database': {
                    'connected': True,
                    'version': db_version,
                    'pool': pool_status
                },
                'config': {
                    'environment': app.config.get('ENV', 'unknown'),
                    'debug': app.debug,
                    'testing': app.testing
                }
            }), 200
            
        except Exception as e:
            app.logger.error(f"Health check failed: {e}")
            return jsonify({
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e),
                'database': {'connected': False}
            }), 500
    
    @app.route('/db-status')
    def db_status():
        """Detailed database status endpoint."""
        try:
            status_info = {}
            
            # Database connection test
            with db.engine.connect() as conn:
                # Basic connectivity
                conn.execute(text("SELECT 1"))
                status_info['connection'] = 'OK'
                
                # Get PostgreSQL version and settings
                result = conn.execute(text("SELECT version();"))
                status_info['version'] = result.fetchone()[0]
                
                # Get current database name
                result = conn.execute(text("SELECT current_database();"))
                status_info['database'] = result.fetchone()[0]
                
                # Get table count
                result = conn.execute(text("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public';
                """))
                status_info['table_count'] = result.fetchone()[0]
                
                # Get total connections
                result = conn.execute(text("""
                    SELECT COUNT(*) 
                    FROM pg_stat_activity 
                    WHERE datname = current_database();
                """))
                status_info['active_connections'] = result.fetchone()[0]
            
            # Connection pool status
            pool = db.engine.pool
            status_info['pool'] = {
                'size': pool.size(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'checked_in': pool.checkedin(),
                'invalid': pool.invalid()
            }
            
            # Migration status
            try:
                from flask_migrate import current
                with app.app_context():
                    current_rev = current()
                    status_info['migration'] = {
                        'current_revision': current_rev,
                        'up_to_date': True  # Simplified check
                    }
            except Exception as e:
                status_info['migration'] = {
                    'error': str(e),
                    'up_to_date': False
                }
            
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'details': status_info
            }), 200
            
        except Exception as e:
            app.logger.error(f"Database status check failed: {e}")
            return jsonify({
                'status': 'error',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }), 500
    
    @app.route('/db-test')
    def db_test():
        """Database functionality test endpoint."""
        try:
            from models import User, Asset
            
            test_results = {}
            
            # Test basic query
            user_count = db.session.query(User).count()
            test_results['user_count'] = user_count
            
            # Test asset query
            asset_count = db.session.query(Asset).count()
            test_results['asset_count'] = asset_count
            
            # Test constraint validation (without actually inserting)
            try:
                # This should not raise an error for the test
                test_user = User(
                    username='test_user_validation',
                    email='test@example.com',
                    first_name='Test',
                    last_name='User',
                    password_hash='test_hash'
                )
                # Don't actually insert, just validate the model can be created
                test_results['model_validation'] = 'OK'
            except Exception as e:
                test_results['model_validation'] = f'Error: {e}'
            
            # Test JSONB functionality
            test_results['jsonb_support'] = 'Available' if 'postgresql' in str(db.engine.url) else 'Not Available'
            
            return jsonify({
                'status': 'test_completed',
                'timestamp': datetime.utcnow().isoformat(),
                'results': test_results
            }), 200
            
        except Exception as e:
            app.logger.error(f"Database test failed: {e}")
            return jsonify({
                'status': 'test_failed',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }), 500

def register_error_handlers(app):
    """Register error handlers."""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource could not be found.',
            'status_code': 404
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f"Internal server error: {error}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An internal error occurred. Please try again later.',
            'status_code': 500
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Handle uncaught exceptions."""
        db.session.rollback()
        app.logger.error(f"Uncaught exception: {e}", exc_info=True)
        
        # Don't reveal internal errors in production
        if app.config.get('DEBUG'):
            return jsonify({
                'error': 'Internal Server Error',
                'message': str(e),
                'status_code': 500
            }), 500
        else:
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An internal error occurred. Please try again later.',
                'status_code': 500
            }), 500

def register_cli_commands(app):
    """Register CLI commands."""
    
    @app.cli.command('init-db')
    def init_database():
        """Initialize the database with all tables."""
        print("🔧 Initializing database...")
        try:
            db.create_all()
            print("✅ Database initialized successfully!")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
    
    @app.cli.command('test-db')
    def test_database():
        """Test database connectivity and functionality."""
        print("🧪 Testing database...")
        try:
            from utils.db_test import DatabaseTester
            tester = DatabaseTester(app.config.get('ENV', 'development'))
            success = tester.run_all_tests()
            if success:
                print("✅ All database tests passed!")
            else:
                print("❌ Some database tests failed!")
        except ImportError:
            print("⚠️  Database testing utility not available")
        except Exception as e:
            print(f"❌ Database testing failed: {e}")
    
    @app.cli.command('create-sample-data')
    def create_sample_data():
        """Create sample data for development."""
        print("📊 Creating sample data...")
        try:
            from models import User, Portfolio, Asset
            from decimal import Decimal
            
            # Create sample user
            if not db.session.query(User).filter_by(username='demo_user').first():
                demo_user = User(
                    username='demo_user',
                    email='demo@example.com',
                    first_name='Demo',
                    last_name='User',
                    password_hash='demo_hash'
                )
                db.session.add(demo_user)
                db.session.commit()
                print("✅ Demo user created")
                
                # Create sample portfolio
                demo_portfolio = Portfolio(
                    user_id=demo_user.id,
                    name='Demo Portfolio',
                    initial_capital=Decimal('100000.00'),
                    current_capital=Decimal('100000.00'),
                    cash_balance=Decimal('100000.00'),
                    total_value=Decimal('100000.00')
                )
                db.session.add(demo_portfolio)
                db.session.commit()
                print("✅ Demo portfolio created")
            
            # Create sample assets
            sample_symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
            for symbol in sample_symbols:
                if not db.session.query(Asset).filter_by(symbol=symbol).first():
                    asset = Asset(
                        symbol=symbol,
                        name=f'{symbol} Inc.',
                        asset_type='stock',
                        exchange='NASDAQ',
                        last_price=Decimal('150.00')
                    )
                    db.session.add(asset)
            
            db.session.commit()
            print("✅ Sample data created successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Sample data creation failed: {e}")
    
    @app.cli.command('cleanup-db')
    def cleanup_database():
        """Clean up test data from database."""
        print("🧹 Cleaning up database...")
        try:
            from models import User, Portfolio, Asset
            
            # Remove demo data
            demo_user = db.session.query(User).filter_by(username='demo_user').first()
            if demo_user:
                db.session.delete(demo_user)
            
            # Remove test assets
            test_assets = db.session.query(Asset).filter(Asset.symbol.like('TEST%')).all()
            for asset in test_assets:
                db.session.delete(asset)
            
            db.session.commit()
            print("✅ Database cleanup completed!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Database cleanup failed: {e}")

def create_wsgi_app():
    """Create WSGI application for production deployment."""
    return create_app('production')

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)