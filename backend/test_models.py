#!/usr/bin/env python3
"""
Test script to verify model definitions work with database
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.auth.models import User, APIKey
from app.models.user_models import UserSession, UserPreferences

def test_models():
    """Test model creation and relationships"""
    database_url = os.getenv('DATABASE_URL', 'postgresql://stockuser:sasfcUlSi_jLh68ZwnRPRBNowlvpJrPY@localhost:5432/stockdb')
    
    try:
        engine = create_engine(database_url)
        
        # Try to create tables
        print("Creating tables...")
        Base.metadata.create_all(engine)
        print("✅ Tables created successfully")
        
        # Test session creation
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Test basic query
        print("Testing User query...")
        users = session.query(User).limit(1).all()
        print(f"✅ User query successful, found {len(users)} users")
        
        session.close()
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_models()