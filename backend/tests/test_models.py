#!/usr/bin/env python3
"""
Model tests for PostgreSQL schema validation.
"""

import pytest
import sys
import os
from decimal import Decimal
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from models import *

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
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

class TestUserModel:
    """Test User model functionality."""
    
    def test_user_creation(self, app_context):
        """Test basic user creation."""
        user = User(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password_hash='hash123'
        )
        
        db.session.add(user)
        db.session.commit()
        
        assert user.id is not None
        assert user.full_name == 'Test User'
        assert user.created_at is not None
    
    def test_user_constraints(self, app_context):
        """Test user model constraints."""
        # Test unique username constraint
        user1 = User(
            username='duplicate',
            email='user1@example.com',
            first_name='User',
            last_name='One',
            password_hash='hash1'
        )
        user2 = User(
            username='duplicate',
            email='user2@example.com',
            first_name='User',
            last_name='Two',
            password_hash='hash2'
        )
        
        db.session.add(user1)
        db.session.commit()
        
        db.session.add(user2)
        with pytest.raises(Exception):  # Should violate unique constraint
            db.session.commit()

class TestPortfolioModel:
    """Test Portfolio model functionality."""
    
    def test_portfolio_creation(self, app_context):
        """Test basic portfolio creation."""
        user = User(
            username='portfoliouser',
            email='portfolio@example.com',
            first_name='Portfolio',
            last_name='User',
            password_hash='hash123'
        )
        db.session.add(user)
        db.session.commit()
        
        portfolio = Portfolio(
            user_id=user.id,
            name='Test Portfolio',
            initial_capital=Decimal('10000.00'),
            current_capital=Decimal('10000.00'),
            cash_balance=Decimal('10000.00'),
            total_value=Decimal('10000.00')
        )
        
        db.session.add(portfolio)
        db.session.commit()
        
        assert portfolio.id is not None
        assert portfolio.user_id == user.id
        assert portfolio.initial_capital == Decimal('10000.00')
        assert portfolio.total_return == Decimal('0.00')
    
    def test_portfolio_constraints(self, app_context):
        """Test portfolio constraints."""
        user = User(
            username='constraintuser',
            email='constraint@example.com',
            first_name='Constraint',
            last_name='User',
            password_hash='hash123'
        )
        db.session.add(user)
        db.session.commit()
        
        # Test negative initial capital constraint
        portfolio = Portfolio(
            user_id=user.id,
            name='Invalid Portfolio',
            initial_capital=Decimal('-1000.00'),  # Should violate constraint
            current_capital=Decimal('10000.00'),
            cash_balance=Decimal('10000.00'),
            total_value=Decimal('10000.00')
        )
        
        db.session.add(portfolio)
        with pytest.raises(Exception):  # Should violate positive constraint
            db.session.commit()
    
    def test_portfolio_calculations(self, app_context):
        """Test portfolio calculation methods."""
        user = User(
            username='calcuser',
            email='calc@example.com',
            first_name='Calc',
            last_name='User',
            password_hash='hash123'
        )
        db.session.add(user)
        db.session.commit()
        
        portfolio = Portfolio(
            user_id=user.id,
            name='Calc Portfolio',
            initial_capital=Decimal('10000.00'),
            current_capital=Decimal('12000.00'),
            cash_balance=Decimal('5000.00'),
            total_value=Decimal('12000.00')
        )
        
        db.session.add(portfolio)
        db.session.commit()
        
        # Test calculate_portfolio_value method
        portfolio.calculate_portfolio_value()
        assert portfolio.total_return == Decimal('2000.00')
        assert portfolio.total_return_pct == Decimal('20.0000')

class TestAssetModel:
    """Test Asset model functionality."""
    
    def test_asset_creation(self, app_context):
        """Test basic asset creation."""
        asset = Asset(
            symbol='AAPL',
            name='Apple Inc.',
            asset_type='stock',
            exchange='NASDAQ',
            last_price=Decimal('150.25')
        )
        
        db.session.add(asset)
        db.session.commit()
        
        assert asset.id is not None
        assert asset.symbol == 'AAPL'
        assert asset.last_price == Decimal('150.25')
    
    def test_asset_constraints(self, app_context):
        """Test asset constraints."""
        # Test unique symbol constraint
        asset1 = Asset(
            symbol='DUPLICATE',
            name='Asset One',
            asset_type='stock',
            exchange='NYSE'
        )
        asset2 = Asset(
            symbol='DUPLICATE',
            name='Asset Two',
            asset_type='stock',
            exchange='NASDAQ'
        )
        
        db.session.add(asset1)
        db.session.commit()
        
        db.session.add(asset2)
        with pytest.raises(Exception):  # Should violate unique constraint
            db.session.commit()

class TestMarketDataModel:
    """Test MarketData model functionality."""
    
    def test_market_data_creation(self, app_context):
        """Test basic market data creation."""
        asset = Asset(
            symbol='TESTMD',
            name='Test Market Data',
            asset_type='stock',
            exchange='NYSE'
        )
        db.session.add(asset)
        db.session.commit()
        
        market_data = MarketData(
            asset_id=asset.id,
            symbol='TESTMD',
            timestamp=datetime.utcnow(),
            timeframe='1d',
            open_price=Decimal('100.00'),
            high_price=Decimal('105.00'),
            low_price=Decimal('99.00'),
            close_price=Decimal('102.50'),
            volume=Decimal('1000000')
        )
        
        db.session.add(market_data)
        db.session.commit()
        
        assert market_data.id is not None
        assert market_data.typical_price == Decimal('102.1666666666666667')
        assert market_data.price_change == Decimal('2.50')
        assert market_data.price_change_pct == 2.5
    
    def test_market_data_constraints(self, app_context):
        """Test market data constraints."""
        asset = Asset(
            symbol='CONSTMD',
            name='Constraint Market Data',
            asset_type='stock',
            exchange='NYSE'
        )
        db.session.add(asset)
        db.session.commit()
        
        # Test OHLC validation (high < low should fail)
        invalid_data = MarketData(
            asset_id=asset.id,
            symbol='CONSTMD',
            timestamp=datetime.utcnow(),
            timeframe='1d',
            open_price=Decimal('100.00'),
            high_price=Decimal('95.00'),  # High less than low
            low_price=Decimal('98.00'),
            close_price=Decimal('99.00'),
            volume=Decimal('1000000')
        )
        
        db.session.add(invalid_data)
        with pytest.raises(Exception):  # Should violate OHLC constraint
            db.session.commit()

class TestTransactionModel:
    """Test Transaction model functionality."""
    
    def test_transaction_creation(self, app_context):
        """Test basic transaction creation."""
        user = User(
            username='txnuser',
            email='txn@example.com',
            first_name='Transaction',
            last_name='User',
            password_hash='hash123'
        )
        db.session.add(user)
        db.session.commit()
        
        portfolio = Portfolio(
            user_id=user.id,
            name='Transaction Portfolio',
            initial_capital=Decimal('10000.00'),
            current_capital=Decimal('10000.00'),
            cash_balance=Decimal('10000.00'),
            total_value=Decimal('10000.00')
        )
        db.session.add(portfolio)
        db.session.commit()
        
        transaction = Transaction(
            portfolio_id=portfolio.id,
            symbol='AAPL',
            transaction_type='BUY',
            quantity=Decimal('10.000000'),
            price=Decimal('150.00'),
            total_value=Decimal('1500.00'),
            transaction_date=datetime.utcnow(),
            cash_impact=Decimal('-1500.00')
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        assert transaction.id is not None
        assert transaction.quantity == Decimal('10.000000')
        assert transaction.total_value == Decimal('1500.00')

class TestRiskModel:
    """Test Risk model functionality."""
    
    def test_risk_profile_creation(self, app_context):
        """Test basic risk profile creation."""
        user = User(
            username='riskuser',
            email='risk@example.com',
            first_name='Risk',
            last_name='User',
            password_hash='hash123'
        )
        db.session.add(user)
        db.session.commit()
        
        risk_profile = RiskProfile(
            user_id=user.id,
            name='Conservative Profile',
            risk_tolerance='conservative',
            time_horizon='long',
            investment_experience='beginner',
            allowed_asset_classes=['stocks', 'bonds']
        )
        
        db.session.add(risk_profile)
        db.session.commit()
        
        assert risk_profile.id is not None
        assert risk_profile.risk_tolerance == 'conservative'
        assert risk_profile.max_position_size_pct == Decimal('10.00')

class TestRelationships:
    """Test model relationships."""
    
    def test_user_portfolio_relationship(self, app_context):
        """Test User-Portfolio relationship."""
        user = User(
            username='reluser',
            email='rel@example.com',
            first_name='Relationship',
            last_name='User',
            password_hash='hash123'
        )
        db.session.add(user)
        db.session.commit()
        
        portfolio1 = Portfolio(
            user_id=user.id,
            name='Portfolio 1',
            initial_capital=Decimal('10000.00'),
            current_capital=Decimal('10000.00'),
            cash_balance=Decimal('10000.00'),
            total_value=Decimal('10000.00')
        )
        portfolio2 = Portfolio(
            user_id=user.id,
            name='Portfolio 2',
            initial_capital=Decimal('20000.00'),
            current_capital=Decimal('20000.00'),
            cash_balance=Decimal('20000.00'),
            total_value=Decimal('20000.00')
        )
        
        db.session.add_all([portfolio1, portfolio2])
        db.session.commit()
        
        # Test relationship loading
        user_with_portfolios = db.session.query(User).filter_by(id=user.id).first()
        assert len(user_with_portfolios.portfolios) == 2
        assert portfolio1 in user_with_portfolios.portfolios
        assert portfolio2 in user_with_portfolios.portfolios
    
    def test_asset_market_data_relationship(self, app_context):
        """Test Asset-MarketData relationship."""
        asset = Asset(
            symbol='RELTEST',
            name='Relationship Test',
            asset_type='stock',
            exchange='NYSE'
        )
        db.session.add(asset)
        db.session.commit()
        
        # Create multiple market data points
        for i in range(5):
            market_data = MarketData(
                asset_id=asset.id,
                symbol='RELTEST',
                timestamp=datetime.utcnow() - timedelta(days=i),
                timeframe='1d',
                open_price=Decimal(f'{100 + i}.00'),
                high_price=Decimal(f'{105 + i}.00'),
                low_price=Decimal(f'{99 + i}.00'),
                close_price=Decimal(f'{102 + i}.00'),
                volume=Decimal('1000000')
            )
            db.session.add(market_data)
        
        db.session.commit()
        
        # Test relationship loading
        asset_with_data = db.session.query(Asset).filter_by(id=asset.id).first()
        assert len(asset_with_data.market_data) == 5

if __name__ == '__main__':
    pytest.main([__file__])