#!/usr/bin/env python3
"""
Database table creation script
Run this to create database tables manually if the app can't create them automatically.
"""
import os
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app, db

def create_tables():
    """Create database tables"""
    print("🗄️  Creating database tables...")
    
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Create Flask app
        app = create_app()
        
        with app.app_context():
            # Try to create tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # List created tables
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if tables:
                print(f"📋 Created tables: {', '.join(tables)}")
            else:
                print("⚠️  No tables were created - they may already exist")
                
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        print("\n💡 Possible solutions:")
        print("1. Check database connection settings in .env file")
        print("2. Ensure PostgreSQL is running")
        print("3. Verify database user has CREATE privileges")
        print("4. Run: psql -d stockdb -c 'GRANT CREATE ON SCHEMA public TO stockuser;'")
        return False
    
    return True

if __name__ == '__main__':
    success = create_tables()
    sys.exit(0 if success else 1)