#!/usr/bin/env python3
"""
Secure startup script with pre-flight checks
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def check_prerequisites():
    """Check all prerequisites before starting"""
    print("🔍 Pre-flight Security Checks...")
    
    issues = []
    
    # Check .env exists
    if not Path('.env').exists():
        issues.append("❌ .env file not found - run quick_security_setup.py first")
    
    # Check Redis config
    if not Path('app/redis.conf').exists():
        issues.append("❌ Redis config not found")
    
    # Check database setup script
    if not Path('setup_db.sh').exists():
        issues.append("⚠️ Database setup script missing")
    
    # Load and check environment variables
    if Path('.env').exists():
        with open('.env', 'r') as f:
            env_vars = {}
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
        
        required_vars = ['FLASK_SECRET_KEY', 'JWT_SECRET_KEY', 'FMP_API_KEY']
        for var in required_vars:
            if var not in env_vars or len(env_vars[var]) < 10:
                issues.append(f"❌ {var} not properly configured")
    
    if issues:
        print("\n🚨 SECURITY ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
        print("\n💡 Run: python quick_security_setup.py")
        return False
    
    print("✅ All security checks passed!")
    return True

def start_services():
    """Start required services"""
    print("\n🚀 Starting services...")
    
    # Check if Redis is running
    try:
        result = subprocess.run(['redis-cli', 'ping'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            print("📡 Starting Redis server...")
            subprocess.Popen(['redis-server', 'app/redis.conf'])
            time.sleep(2)
    except FileNotFoundError:
        print("⚠️ Redis not installed - install with: sudo apt install redis-server")
    except Exception as e:
        print(f"⚠️ Redis startup issue: {e}")
    
    # Check PostgreSQL
    try:
        result = subprocess.run(['pg_isready'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            print("⚠️ PostgreSQL not running - start with: sudo systemctl start postgresql")
    except FileNotFoundError:
        print("⚠️ PostgreSQL not installed")
    except Exception as e:
        print(f"⚠️ PostgreSQL check failed: {e}")

def start_application():
    """Start the Flask application"""
    print("\n🌟 Starting Stock Analyzer (Secure Mode)...")
    
    # Load environment variables
    if Path('.env').exists():
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    # Import and start Flask app
    try:
        from app import create_app
        app = create_app()
        
        print("✅ Application initialized successfully")
        print("🌐 Server starting at: http://127.0.0.1:5000")
        print("🔐 Security: ENABLED")
        print("📊 Debug mode: " + ("ON" if os.getenv('FLASK_ENV') == 'development' else "OFF"))
        print("\n💡 Create first user:")
        print('curl -X POST http://localhost:5000/api/auth/register \\')
        print('  -H "Content-Type: application/json" \\')
        print('  -d \'{"email":"admin@example.com","username":"admin","password":"SecurePass123!"}\'')
        print("\n🛑 Press Ctrl+C to stop")
        
        # Start the app
        app.run(
            host=os.getenv('FLASK_HOST', '127.0.0.1'),
            port=int(os.getenv('FLASK_PORT', 5000)),
            debug=os.getenv('FLASK_ENV') == 'development'
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        return 1
    
    return 0

def main():
    print("🛡️ SECURE STARTUP - Stock Analyzer")
    print("=" * 40)
    
    if not check_prerequisites():
        return 1
    
    start_services()
    return start_application()

if __name__ == "__main__":
    sys.exit(main())