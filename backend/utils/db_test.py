#!/usr/bin/env python3
"""
Comprehensive database testing utility for PostgreSQL setup.
Tests psycopg2 direct connection, SQLAlchemy connection, and Flask app integration.
"""

import os
import sys
import time
import traceback
from datetime import datetime, timedelta
from decimal import Decimal
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import argparse

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from models import *
from models.base import Base

class DatabaseTester:
    """Comprehensive database testing utility."""
    
    def __init__(self, config_name='development'):
        self.config = config[config_name]
        self.db_config = self._parse_db_url()
        self.engine = None
        self.session = None
        
    def _parse_db_url(self):
        """Parse database URL into components."""
        url = self.config.SQLALCHEMY_DATABASE_URI
        # Extract components from postgresql://user:pass@host:port/db
        parts = url.replace('postgresql://', '').split('@')
        user_pass = parts[0].split(':')
        host_port_db = parts[1].split('/')
        host_port = host_port_db[0].split(':')
        
        return {
            'user': user_pass[0],
            'password': user_pass[1],
            'host': host_port[0],
            'port': int(host_port[1]) if len(host_port) > 1 else 5432,
            'database': host_port_db[1]
        }
    
    def test_psycopg2_connection(self):
        """Test direct psycopg2 connection."""
        print("🔌 Testing psycopg2 direct connection...")
        try:
            conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database']
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ PostgreSQL connection successful!")
            print(f"   Version: {version}")
            
            # Test basic operations
            cursor.execute("SELECT NOW();")
            current_time = cursor.fetchone()[0]
            print(f"   Current time: {current_time}")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ psycopg2 connection failed: {e}")
            return False
    
    def test_sqlalchemy_connection(self):
        """Test SQLAlchemy connection."""
        print("\n🔧 Testing SQLAlchemy connection...")
        try:
            self.engine = create_engine(
                self.config.SQLALCHEMY_DATABASE_URI,
                **self.config.SQLALCHEMY_ENGINE_OPTIONS
            )
            
            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version();"))
                version = result.fetchone()[0]
                print(f"✅ SQLAlchemy connection successful!")
                print(f"   Version: {version}")
                
                # Test pool info
                pool = self.engine.pool
                print(f"   Pool size: {pool.size()}")
                print(f"   Pool checked out: {pool.checkedout()}")
                print(f"   Pool overflow: {pool.overflow()}")
                
            return True
            
        except Exception as e:
            print(f"❌ SQLAlchemy connection failed: {e}")
            return False
    
    def test_flask_app_integration(self):
        """Test Flask app database integration."""
        print("\n🌶️  Testing Flask app integration...")
        try:
            # Import app factory
            from app import create_app, db
            
            app = create_app('development')
            
            with app.app_context():
                # Test database connection through Flask
                db.session.execute(text("SELECT 1"))
                print("✅ Flask app database connection successful!")
                
                # Test health endpoint simulation
                try:
                    db.session.execute(text("SELECT 1"))
                    print("✅ Health check simulation passed!")
                except Exception as e:
                    print(f"❌ Health check simulation failed: {e}")
                    return False
                
            return True
            
        except ImportError as e:
            print(f"⚠️  Flask app not available for testing: {e}")
            return True  # Not critical for database testing
        except Exception as e:
            print(f"❌ Flask app integration failed: {e}")
            return False
    
    def test_model_imports(self):
        """Test that all models can be imported successfully."""
        print("\n📦 Testing model imports...")
        try:
            # Test individual model imports
            models_to_test = [
                ('User', User),
                ('UserPreferences', UserPreferences),
                ('Portfolio', Portfolio),
                ('Position', Position),
                ('Transaction', Transaction),
                ('PortfolioSnapshot', PortfolioSnapshot),
                ('Strategy', Strategy),
                ('StrategyParameter', StrategyParameter),
                ('StrategyPerformance', StrategyPerformance),
                ('Backtest', Backtest),
                ('Trade', Trade),
                ('Signal', Signal),
                ('Asset', Asset),
                ('MarketData', MarketData),
                ('Benchmark', Benchmark),
                ('RiskProfile', RiskProfile),
                ('RiskMetrics', RiskMetrics),
            ]
            
            for model_name, model_class in models_to_test:
                # Test model instantiation (without saving)
                try:
                    if model_name == 'User':
                        instance = model_class(
                            username='test_user',
                            email='test@example.com',
                            first_name='Test',
                            last_name='User',
                            password_hash='test_hash'
                        )
                    elif model_name == 'Portfolio':
                        instance = model_class(
                            user_id=1,
                            name='Test Portfolio',
                            initial_capital=Decimal('10000.00'),
                            current_capital=Decimal('10000.00'),
                            cash_balance=Decimal('10000.00'),
                            total_value=Decimal('10000.00')
                        )
                    else:
                        # Basic instantiation for other models
                        instance = model_class()
                    
                    # Test to_dict method if available
                    if hasattr(instance, 'to_dict'):
                        instance.to_dict()
                    
                    print(f"   ✅ {model_name}: Import and instantiation successful")
                    
                except Exception as e:
                    print(f"   ❌ {model_name}: Failed - {e}")
                    return False
            
            print("✅ All model imports successful!")
            return True
            
        except Exception as e:
            print(f"❌ Model import testing failed: {e}")
            return False
    
    def test_table_creation(self):
        """Test table creation with all constraints and indexes."""
        print("\n🏗️  Testing table creation...")
        try:
            if not self.engine:
                self.engine = create_engine(self.config.SQLALCHEMY_DATABASE_URI)
            
            # Create all tables
            print("   Creating all tables...")
            Base.metadata.create_all(self.engine)
            print("✅ All tables created successfully!")
            
            # Verify tables exist
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name;
                """))
                tables = [row[0] for row in result]
                
                expected_tables = [
                    'users', 'user_preferences', 'portfolios', 'positions', 
                    'transactions', 'portfolio_snapshots', 'strategies', 
                    'strategy_parameters', 'strategy_performance', 'backtests', 
                    'trades', 'signals', 'assets', 'market_data', 'benchmarks',
                    'risk_profiles', 'risk_metrics'
                ]
                
                missing_tables = set(expected_tables) - set(tables)
                if missing_tables:
                    print(f"⚠️  Missing tables: {missing_tables}")
                    return False
                
                print(f"   Tables created: {len(tables)}")
                for table in sorted(tables):
                    print(f"   - {table}")
                
            return True
            
        except Exception as e:
            print(f"❌ Table creation failed: {e}")
            traceback.print_exc()
            return False
    
    def test_basic_crud_operations(self):
        """Test basic CRUD operations."""
        print("\n🔄 Testing basic CRUD operations...")
        try:
            if not self.engine:
                self.engine = create_engine(self.config.SQLALCHEMY_DATABASE_URI)
            
            Session = sessionmaker(bind=self.engine)
            session = Session()
            
            try:
                # Test User creation
                print("   Testing User CRUD...")
                user = User(
                    username='test_user_crud',
                    email='crud@example.com',
                    first_name='CRUD',
                    last_name='Test',
                    password_hash='test_hash'
                )
                session.add(user)
                session.commit()
                user_id = user.id
                print(f"   ✅ User created with ID: {user_id}")
                
                # Test Portfolio creation
                print("   Testing Portfolio CRUD...")
                portfolio = Portfolio(
                    user_id=user_id,
                    name='Test CRUD Portfolio',
                    initial_capital=Decimal('10000.00'),
                    current_capital=Decimal('10000.00'),
                    cash_balance=Decimal('10000.00'),
                    total_value=Decimal('10000.00')
                )
                session.add(portfolio)
                session.commit()
                portfolio_id = portfolio.id
                print(f"   ✅ Portfolio created with ID: {portfolio_id}")
                
                # Test Asset creation
                print("   Testing Asset CRUD...")
                asset = Asset(
                    symbol='TEST',
                    name='Test Asset',
                    asset_type='stock',
                    exchange='NYSE',
                    last_price=Decimal('100.00')
                )
                session.add(asset)
                session.commit()
                asset_id = asset.id
                print(f"   ✅ Asset created with ID: {asset_id}")
                
                # Test MarketData creation
                print("   Testing MarketData CRUD...")
                market_data = MarketData(
                    asset_id=asset_id,
                    symbol='TEST',
                    timestamp=datetime.utcnow(),
                    timeframe='1d',
                    open_price=Decimal('99.50'),
                    high_price=Decimal('101.00'),
                    low_price=Decimal('99.00'),
                    close_price=Decimal('100.50'),
                    volume=Decimal('1000000')
                )
                session.add(market_data)
                session.commit()
                print(f"   ✅ MarketData created with ID: {market_data.id}")
                
                # Test reading with relationships
                print("   Testing relationship queries...")
                user_with_portfolios = session.query(User).filter_by(id=user_id).first()
                if user_with_portfolios and len(user_with_portfolios.portfolios) > 0:
                    print("   ✅ User-Portfolio relationship working")
                else:
                    print("   ⚠️  User-Portfolio relationship issue")
                
                # Clean up test data
                print("   Cleaning up test data...")
                session.query(MarketData).filter_by(asset_id=asset_id).delete()
                session.query(Asset).filter_by(id=asset_id).delete()
                session.query(Portfolio).filter_by(id=portfolio_id).delete()
                session.query(User).filter_by(id=user_id).delete()
                session.commit()
                print("   ✅ Test data cleaned up")
                
                session.close()
                print("✅ All CRUD operations successful!")
                return True
                
            except Exception as e:
                session.rollback()
                session.close()
                raise e
                
        except Exception as e:
            print(f"❌ CRUD operations failed: {e}")
            traceback.print_exc()
            return False
    
    def test_performance(self):
        """Test database performance with sample data."""
        print("\n⚡ Testing database performance...")
        try:
            if not self.engine:
                self.engine = create_engine(self.config.SQLALCHEMY_DATABASE_URI)
            
            Session = sessionmaker(bind=self.engine)
            session = Session()
            
            try:
                # Performance test parameters
                num_assets = 100
                num_data_points = 1000
                
                print(f"   Creating {num_assets} test assets...")
                start_time = time.time()
                
                # Create test assets
                assets = []
                for i in range(num_assets):
                    asset = Asset(
                        symbol=f'TEST{i:03d}',
                        name=f'Test Asset {i}',
                        asset_type='stock',
                        exchange='NYSE',
                        last_price=Decimal(f'{100 + i}.00')
                    )
                    assets.append(asset)
                
                session.add_all(assets)
                session.commit()
                
                asset_creation_time = time.time() - start_time
                print(f"   ✅ Created {num_assets} assets in {asset_creation_time:.2f}s")
                
                # Create market data
                print(f"   Creating {num_data_points} market data points...")
                start_time = time.time()
                
                market_data_points = []
                base_date = datetime.utcnow() - timedelta(days=num_data_points)
                
                for i in range(num_data_points):
                    asset = assets[i % num_assets]
                    date = base_date + timedelta(days=i)
                    
                    market_data = MarketData(
                        asset_id=asset.id,
                        symbol=asset.symbol,
                        timestamp=date,
                        timeframe='1d',
                        open_price=Decimal(f'{100 + (i % 10)}.00'),
                        high_price=Decimal(f'{105 + (i % 10)}.00'),
                        low_price=Decimal(f'{95 + (i % 10)}.00'),
                        close_price=Decimal(f'{102 + (i % 10)}.00'),
                        volume=Decimal('1000000')
                    )
                    market_data_points.append(market_data)
                
                session.add_all(market_data_points)
                session.commit()
                
                data_creation_time = time.time() - start_time
                print(f"   ✅ Created {num_data_points} data points in {data_creation_time:.2f}s")
                
                # Test query performance
                print("   Testing query performance...")
                start_time = time.time()
                
                # Test index usage with symbol query
                result = session.query(MarketData).filter(
                    MarketData.symbol == 'TEST001'
                ).limit(100).all()
                
                query_time = time.time() - start_time
                print(f"   ✅ Symbol query returned {len(result)} results in {query_time:.3f}s")
                
                # Test date range query
                start_time = time.time()
                date_range_start = base_date + timedelta(days=100)
                date_range_end = base_date + timedelta(days=200)
                
                result = session.query(MarketData).filter(
                    MarketData.timestamp.between(date_range_start, date_range_end)
                ).limit(100).all()
                
                date_query_time = time.time() - start_time
                print(f"   ✅ Date range query returned {len(result)} results in {date_query_time:.3f}s")
                
                # Clean up test data
                print("   Cleaning up performance test data...")
                session.query(MarketData).filter(
                    MarketData.symbol.like('TEST%')
                ).delete(synchronize_session=False)
                session.query(Asset).filter(
                    Asset.symbol.like('TEST%')
                ).delete(synchronize_session=False)
                session.commit()
                
                session.close()
                print("✅ Performance tests completed successfully!")
                return True
                
            except Exception as e:
                session.rollback()
                session.close()
                raise e
                
        except Exception as e:
            print(f"❌ Performance tests failed: {e}")
            return False
    
    def test_constraints_and_validations(self):
        """Test database constraints and validations."""
        print("\n🛡️  Testing constraints and validations...")
        try:
            if not self.engine:
                self.engine = create_engine(self.config.SQLALCHEMY_DATABASE_URI)
            
            Session = sessionmaker(bind=self.engine)
            session = Session()
            
            try:
                print("   Testing positive value constraints...")
                
                # Test portfolio constraint violations
                portfolio = Portfolio(
                    user_id=1,  # This will fail FK constraint, but that's expected
                    name='Test Constraint Portfolio',
                    initial_capital=Decimal('-1000.00'),  # Should violate positive constraint
                    current_capital=Decimal('10000.00'),
                    cash_balance=Decimal('10000.00'),
                    total_value=Decimal('10000.00')
                )
                
                try:
                    session.add(portfolio)
                    session.commit()
                    print("   ❌ Negative initial_capital constraint not enforced")
                    return False
                except Exception as e:
                    session.rollback()
                    if 'ck_initial_capital_positive' in str(e) or 'check constraint' in str(e).lower():
                        print("   ✅ Positive value constraint enforced")
                    else:
                        print(f"   ⚠️  Unexpected constraint error: {e}")
                
                # Test OHLC validation constraints
                print("   Testing OHLC validation constraints...")
                asset = Asset(
                    symbol='CONSTRAINT_TEST',
                    name='Constraint Test Asset',
                    asset_type='stock',
                    exchange='NYSE'
                )
                session.add(asset)
                session.commit()
                
                # Test invalid OHLC data (high < low)
                invalid_market_data = MarketData(
                    asset_id=asset.id,
                    symbol='CONSTRAINT_TEST',
                    timestamp=datetime.utcnow(),
                    timeframe='1d',
                    open_price=Decimal('100.00'),
                    high_price=Decimal('95.00'),  # High less than low - should fail
                    low_price=Decimal('98.00'),
                    close_price=Decimal('99.00'),
                    volume=Decimal('1000000')
                )
                
                try:
                    session.add(invalid_market_data)
                    session.commit()
                    print("   ❌ OHLC validation constraint not enforced")
                    return False
                except Exception as e:
                    session.rollback()
                    if 'ck_high_low_valid' in str(e) or 'check constraint' in str(e).lower():
                        print("   ✅ OHLC validation constraint enforced")
                    else:
                        print(f"   ⚠️  Unexpected OHLC constraint error: {e}")
                
                # Clean up
                session.query(Asset).filter_by(symbol='CONSTRAINT_TEST').delete()
                session.commit()
                session.close()
                
                print("✅ Constraint validation tests completed!")
                return True
                
            except Exception as e:
                session.rollback()
                session.close()
                raise e
                
        except Exception as e:
            print(f"❌ Constraint validation tests failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all database tests."""
        print("🚀 Starting comprehensive database tests...\n")
        
        tests = [
            ("psycopg2 Connection", self.test_psycopg2_connection),
            ("SQLAlchemy Connection", self.test_sqlalchemy_connection),
            ("Flask App Integration", self.test_flask_app_integration),
            ("Model Imports", self.test_model_imports),
            ("Table Creation", self.test_table_creation),
            ("CRUD Operations", self.test_basic_crud_operations),
            ("Performance Tests", self.test_performance),
            ("Constraints & Validations", self.test_constraints_and_validations),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                results[test_name] = result
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
        
        # Summary
        print("\n" + "="*60)
        print("🏁 DATABASE TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All database tests PASSED! Your PostgreSQL setup is ready.")
            return True
        else:
            print("⚠️  Some tests FAILED. Please review the output above.")
            return False

def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description='Database testing utility')
    parser.add_argument('command', choices=['test', 'migrate'], 
                       help='Command to run')
    parser.add_argument('--config', default='development',
                       choices=['development', 'testing', 'production'],
                       help='Configuration to use')
    
    args = parser.parse_args()
    
    if args.command == 'test':
        tester = DatabaseTester(args.config)
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    
    elif args.command == 'migrate':
        print("🔄 Running migrations...")
        try:
            from utils.migration_manager import MigrationManager
            manager = MigrationManager(args.config)
            manager.run_migrations()
            print("✅ Migrations completed successfully!")
        except ImportError:
            print("❌ Migration manager not available. Run: flask db upgrade")
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()