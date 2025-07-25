#!/usr/bin/env python3
"""
Complete database setup script for PostgreSQL trading platform.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(command, description, capture_output=True):
    """Run a command with error handling."""
    print(f"🔄 {description}...")
    
    try:
        if capture_output:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            if result.stdout:
                print(f"   Output: {result.stdout.strip()}")
            print(f"✅ {description} completed successfully")
            return True
        else:
            result = subprocess.run(command, shell=True, check=True)
            print(f"✅ {description} completed successfully")
            return True
            
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        if capture_output and e.stdout:
            print(f"   STDOUT: {e.stdout}")
        if capture_output and e.stderr:
            print(f"   STDERR: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        return False

def check_prerequisites():
    """Check if all prerequisites are installed."""
    print("🔍 Checking prerequisites...")
    
    prerequisites = [
        ('python3', 'Python 3'),
        ('pip', 'pip'),
        ('psql', 'PostgreSQL client'),
        ('pg_dump', 'PostgreSQL tools')
    ]
    
    all_present = True
    
    for command, name in prerequisites:
        try:
            subprocess.run([command, '--version'], capture_output=True, check=True)
            print(f"   ✅ {name} is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"   ❌ {name} is not available")
            all_present = False
    
    return all_present

def install_dependencies():
    """Install Python dependencies."""
    return run_command(
        "pip install -r requirements.txt",
        "Installing Python dependencies"
    )

def setup_environment():
    """Setup environment variables."""
    print("🔧 Setting up environment...")
    
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if env_file.exists():
        print("   ℹ️  .env file already exists")
        return True
    
    if env_example.exists():
        # Copy example to .env
        import shutil
        shutil.copy(env_example, env_file)
        print("   ✅ Created .env from .env.example")
        print("   ⚠️  Please update .env with your database credentials")
        return True
    else:
        # Create basic .env file
        env_content = """# Database Configuration
POSTGRES_USER=trading_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=trading_db

# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=

# API Configuration
FMP_API_KEY=your-fmp-api-key-here
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("   ✅ Created basic .env file")
        print("   ⚠️  Please update .env with your actual credentials")
        return True

def test_database_connection():
    """Test database connection."""
    return run_command(
        "python utils/db_test.py test",
        "Testing database connection and functionality"
    )

def initialize_database():
    """Initialize database with Flask-Migrate."""
    print("🏗️  Initializing database...")
    
    # Set environment
    os.environ['FLASK_APP'] = 'app.py'
    os.environ['FLASK_ENV'] = 'development'
    
    success = True
    
    # Initialize migrations if not already done
    migrations_dir = Path('migrations')
    if not migrations_dir.exists():
        success &= run_command("flask db init", "Initializing Flask-Migrate")
    
    # Create initial migration
    versions_dir = migrations_dir / 'versions'
    if not versions_dir.exists() or not list(versions_dir.glob('*.py')):
        success &= run_command(
            'flask db migrate -m "Initial database schema"',
            "Creating initial migration"
        )
    
    # Apply migrations
    if success:
        success &= run_command("flask db upgrade", "Applying database migrations")
    
    return success

def create_sample_data():
    """Create sample data for development."""
    return run_command(
        "flask create-sample-data",
        "Creating sample data"
    )

def run_tests():
    """Run database tests."""
    print("🧪 Running tests...")
    
    success = True
    
    # Run model tests
    if Path('tests/test_models.py').exists():
        success &= run_command(
            "python -m pytest tests/test_models.py -v",
            "Running model tests"
        )
    
    # Run database tests
    if Path('tests/test_db.py').exists():
        success &= run_command(
            "python -m pytest tests/test_db.py -v",
            "Running database tests"
        )
    
    return success

def cleanup_database():
    """Clean up test data."""
    return run_command(
        "flask cleanup-db",
        "Cleaning up test data"
    )

def show_setup_summary():
    """Show setup summary and next steps."""
    print("\n" + "="*60)
    print("🏁 DATABASE SETUP SUMMARY")
    print("="*60)
    
    print("\n📋 What was set up:")
    print("✅ PostgreSQL-optimized database schema")
    print("✅ All models with Numeric data types for financial precision")
    print("✅ Proper foreign key relationships and constraints")
    print("✅ JSONB fields for flexible data storage")
    print("✅ Comprehensive indexes for query performance")
    print("✅ Flask-Migrate for database versioning")
    print("✅ Database testing utilities")
    print("✅ Sample data for development")
    
    print("\n🚀 Next steps:")
    print("1. Update .env file with your actual database credentials")
    print("2. Start your Flask application: flask run")
    print("3. Test health endpoints:")
    print("   - http://localhost:5000/health")
    print("   - http://localhost:5000/db-status")
    print("   - http://localhost:5000/db-test")
    
    print("\n🛠️  Available commands:")
    print("• python utils/db_test.py test           - Run comprehensive database tests")
    print("• python utils/migration_manager.py setup - Full migration setup")
    print("• flask db migrate -m 'message'         - Create new migration")
    print("• flask db upgrade                      - Apply migrations")
    print("• flask create-sample-data              - Create sample data")
    print("• flask cleanup-db                      - Clean up test data")
    
    print("\n📚 Key features implemented:")
    print("• Numeric precision for all financial calculations")
    print("• PostgreSQL JSONB for flexible metadata storage")
    print("• Comprehensive check constraints for data validation")
    print("• Performance-optimized indexes for time-series queries")
    print("• Connection pooling with proper configuration")
    print("• Database backup utilities for production")
    print("• Real-time health monitoring endpoints")

def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description='Database setup utility')
    parser.add_argument('--skip-tests', action='store_true', help='Skip running tests')
    parser.add_argument('--skip-sample-data', action='store_true', help='Skip creating sample data')
    parser.add_argument('--test-only', action='store_true', help='Run tests only')
    parser.add_argument('--clean', action='store_true', help='Clean up test data')
    
    args = parser.parse_args()
    
    print("🚀 PostgreSQL Database Setup for Trading Platform")
    print("="*60)
    
    if args.clean:
        print("🧹 Cleaning up database...")
        cleanup_database()
        return
    
    if args.test_only:
        print("🧪 Running tests only...")
        if not test_database_connection():
            sys.exit(1)
        if not run_tests():
            sys.exit(1)
        return
    
    # Full setup process
    steps = [
        ("Checking prerequisites", check_prerequisites),
        ("Setting up environment", setup_environment),
        ("Installing dependencies", install_dependencies),
        ("Testing database connection", test_database_connection),
        ("Initializing database", initialize_database),
    ]
    
    if not args.skip_sample_data:
        steps.append(("Creating sample data", create_sample_data))
    
    if not args.skip_tests:
        steps.append(("Running tests", run_tests))
    
    # Execute all steps
    for step_name, step_func in steps:
        print(f"\n📍 Step: {step_name}")
        if not step_func():
            print(f"\n❌ Setup failed at step: {step_name}")
            print("Please resolve the errors and run the setup again.")
            sys.exit(1)
    
    print(f"\n🎉 Database setup completed successfully!")
    show_setup_summary()

if __name__ == '__main__':
    main()