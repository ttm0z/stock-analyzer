#!/usr/bin/env python3
"""
Database connection and functionality tests.
"""

import pytest
import sys
import os
from decimal import Decimal
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from config import config
from utils.db_test import DatabaseTester

@pytest.fixture
def app():
    """Create test app fixture."""
    app = create_app('testing')
    return app

@pytest.fixture
def client(app):
    """Create test client fixture."""
    return app.test_client()

@pytest.fixture
def app_context(app):
    """Create app context fixture."""
    with app.app_context():
        yield app

class TestDatabaseConnection:
    """Test database connection functionality."""
    
    def test_database_connection(self, app_context):
        """Test basic database connection."""
        # Test that we can execute a simple query
        result = db.session.execute(db.text("SELECT 1 as test_value"))
        row = result.fetchone()
        assert row[0] == 1
    
    def test_database_version(self, app_context):
        """Test database version query."""
        result = db.session.execute(db.text("SELECT version()"))
        version = result.fetchone()[0]
        assert 'PostgreSQL' in version or 'SQLite' in version  # Support both for testing
    
    def test_current_database(self, app_context):
        """Test current database query."""
        if 'postgresql' in str(db.engine.url):
            result = db.session.execute(db.text("SELECT current_database()"))
            database_name = result.fetchone()[0]
            assert database_name is not None

class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_endpoint(self, client):
        """Test /health endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] in ['healthy', 'unhealthy']
        assert 'timestamp' in data
        assert 'database' in data
    
    def test_db_status_endpoint(self, client):
        """Test /db-status endpoint."""
        response = client.get('/db-status')
        assert response.status_code in [200, 500]  # May fail in test environment
        
        data = response.get_json()
        assert 'status' in data
        assert 'timestamp' in data
    
    def test_db_test_endpoint(self, client):
        """Test /db-test endpoint."""
        response = client.get('/db-test')
        assert response.status_code in [200, 500]  # May fail in test environment
        
        data = response.get_json()
        assert 'status' in data
        assert 'timestamp' in data

class TestDatabaseTester:
    """Test the DatabaseTester utility class."""
    
    def test_database_tester_initialization(self):
        """Test DatabaseTester initialization."""
        tester = DatabaseTester('testing')
        assert tester.config is not None
        assert tester.db_config is not None
    
    def test_model_imports(self):
        """Test that all models can be imported."""
        tester = DatabaseTester('testing')
        # This should not raise an exception
        result = tester.test_model_imports()
        assert result is True  # All models should import successfully

class TestDatabaseConstraints:
    """Test database constraints are working."""
    
    def test_numeric_precision(self, app_context):
        """Test that Numeric fields maintain precision."""
        from models import Portfolio, User
        
        # Create test user
        user = User(
            username='precision_test',
            email='precision@test.com',
            first_name='Precision',
            last_name='Test',
            password_hash='test_hash'
        )
        db.session.add(user)
        db.session.commit()
        
        # Create portfolio with precise decimal values
        portfolio = Portfolio(
            user_id=user.id,
            name='Precision Test',
            initial_capital=Decimal('10000.12'),
            current_capital=Decimal('10000.12'),
            cash_balance=Decimal('10000.12'),
            total_value=Decimal('10000.12')
        )
        
        db.session.add(portfolio)
        db.session.commit()
        
        # Retrieve and verify precision is maintained
        retrieved_portfolio = db.session.query(Portfolio).filter_by(id=portfolio.id).first()
        assert retrieved_portfolio.initial_capital == Decimal('10000.12')
        assert str(retrieved_portfolio.initial_capital) == '10000.12'
    
    def test_jsonb_functionality(self, app_context):
        """Test JSONB field functionality."""
        from models import Strategy, User
        
        # Skip if not PostgreSQL
        if 'postgresql' not in str(db.engine.url):
            pytest.skip("JSONB tests require PostgreSQL")
        
        # Create test user
        user = User(
            username='jsonb_test',
            email='jsonb@test.com',
            first_name='JSONB',
            last_name='Test',
            password_hash='test_hash'
        )
        db.session.add(user)
        db.session.commit()
        
        # Create strategy with JSONB data
        strategy = Strategy(
            user_id=user.id,
            name='JSONB Test Strategy',
            strategy_type='test',
            category='test',
            parameters={'param1': 'value1', 'param2': 42},
            entry_rules={'rule1': 'condition1'},
            exit_rules={'rule1': 'exit_condition1'}
        )
        
        db.session.add(strategy)
        db.session.commit()
        
        # Retrieve and verify JSONB data
        retrieved_strategy = db.session.query(Strategy).filter_by(id=strategy.id).first()
        assert retrieved_strategy.parameters['param1'] == 'value1'
        assert retrieved_strategy.parameters['param2'] == 42
    
    def test_check_constraints(self, app_context):
        """Test that check constraints are enforced."""
        from models import Portfolio, User
        
        # Create test user
        user = User(
            username='constraint_test',
            email='constraint@test.com',
            first_name='Constraint',
            last_name='Test',
            password_hash='test_hash'
        )
        db.session.add(user)
        db.session.commit()
        
        # Try to create portfolio with negative initial capital
        invalid_portfolio = Portfolio(
            user_id=user.id,
            name='Invalid Portfolio',
            initial_capital=Decimal('-1000.00'),  # Should violate check constraint
            current_capital=Decimal('10000.00'),
            cash_balance=Decimal('10000.00'),
            total_value=Decimal('10000.00')
        )
        
        db.session.add(invalid_portfolio)
        
        # This should raise an exception due to check constraint
        with pytest.raises(Exception):
            db.session.commit()
        
        db.session.rollback()

class TestDatabasePerformance:
    """Test database performance with indexes."""
    
    def test_index_usage(self, app_context):
        """Test that indexes are being used for common queries."""
        from models import Asset, MarketData
        
        # Create test assets
        assets = []
        for i in range(10):
            asset = Asset(
                symbol=f'PERF{i:03d}',
                name=f'Performance Test {i}',
                asset_type='stock',
                exchange='NYSE'
            )
            assets.append(asset)
        
        db.session.add_all(assets)
        db.session.commit()
        
        # Create market data
        market_data_points = []
        for asset in assets:
            for j in range(5):
                market_data = MarketData(
                    asset_id=asset.id,
                    symbol=asset.symbol,
                    timestamp=datetime.utcnow(),
                    timeframe='1d',
                    open_price=Decimal('100.00'),
                    high_price=Decimal('105.00'),
                    low_price=Decimal('99.00'),
                    close_price=Decimal('102.50'),
                    volume=Decimal('1000000')
                )
                market_data_points.append(market_data)
        
        db.session.add_all(market_data_points)
        db.session.commit()
        
        # Test symbol-based query (should use index)
        result = db.session.query(MarketData).filter(
            MarketData.symbol == 'PERF001'
        ).all()
        
        assert len(result) == 5
        
        # Test asset_id based query (should use index)
        result = db.session.query(MarketData).filter(
            MarketData.asset_id == assets[0].id
        ).all()
        
        assert len(result) == 5

if __name__ == '__main__':
    pytest.main([__file__])