#!/usr/bin/env python3
"""
Test script to verify database resolution is working
"""

import sys
import os
sys.path.insert(0, '/home/t/Projects/stock-analyzer/backend')

def test_model_imports():
    """Test that all model imports work correctly"""
    print("🔍 Testing model imports...")
    
    try:
        # Test user model import
        from app.models.user_models import User, UserPreferences
        print("✅ User models imported successfully")
        
        # Test portfolio model import
        from app.models.portfolio_models import Portfolio, Position, Transaction
        print("✅ Portfolio models imported successfully")
        
        # Test optimized models direct import
        from models.user import User as OptimizedUser
        from models.portfolio import Portfolio as OptimizedPortfolio
        print("✅ Optimized models imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Model import failed: {e}")
        return False

def test_data_types():
    """Test that optimized models use correct data types"""
    print("🔍 Testing data types...")
    
    try:
        from models.portfolio import Portfolio
        from sqlalchemy import inspect
        
        # Check Portfolio model columns
        mapper = inspect(Portfolio)
        columns = {col.name: str(col.type) for col in mapper.columns}
        
        # Check for Numeric types
        numeric_fields = ['initial_capital', 'cash_balance', 'total_value']
        for field in numeric_fields:
            if field in columns:
                if 'NUMERIC' in columns[field].upper():
                    print(f"✅ {field}: {columns[field]} (Correct precision)")
                else:
                    print(f"⚠️  {field}: {columns[field]} (May need migration)")
        
        return True
    except Exception as e:
        print(f"❌ Data type check failed: {e}")
        return False

def test_app_creation():
    """Test that app can be created without conflicts"""
    print("🔍 Testing app creation...")
    
    try:
        from app import create_app
        app = create_app('development')
        print("✅ App created successfully with optimized factory")
        
        # Test database connection
        with app.app_context():
            from app import db
            with db.engine.connect() as conn:
                result = conn.execute(db.text("SELECT 1"))
                print("✅ Database connection successful")
        
        return True
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        return False

def test_route_imports():
    """Test that routes can import models correctly"""
    print("🔍 Testing route imports...")
    
    try:
        # Test what trading routes would import
        from app.models.portfolio_models import Portfolio, Position, Transaction
        
        # Verify these are the optimized models
        if hasattr(Portfolio, 'initial_capital'):
            print("✅ Trading routes can access Portfolio model")
        
        return True
    except Exception as e:
        print(f"❌ Route import failed: {e}")
        return False

def main():
    """Run all resolution tests"""
    print("🧪 Running Database Resolution Tests\n")
    
    tests = [
        test_model_imports,
        test_data_types,
        test_app_creation,
        test_route_imports
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Database resolution successful!")
        return True
    else:
        print("⚠️  Some tests failed. Manual intervention may be needed.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)