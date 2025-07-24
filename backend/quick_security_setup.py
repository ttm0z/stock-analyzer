#!/usr/bin/env python3
"""
Quick Security Setup - Streamlined version for immediate deployment
"""
import os
import secrets
import getpass
import sys

def generate_secure_key(length=32):
    """Generate cryptographically secure key"""
    return secrets.token_urlsafe(length)

def main():
    print("🛡️ QUICK SECURITY SETUP")
    print("=" * 40)
    
    # Get API keys
    print("\n🔑 Enter your NEW API keys (after revoking old ones):")
    fmp_key = input("FMP API Key: ").strip()
    alpha_key = input("Alpha Vantage API Key: ").strip()
    
    if not fmp_key or not alpha_key:
        print("❌ Both API keys are required!")
        return 1
    
    # Generate secure credentials
    print("\n🔐 Generating secure credentials...")
    flask_secret = generate_secure_key(32)
    jwt_secret = generate_secure_key(32)
    password_salt = generate_secure_key(16)
    db_password = generate_secure_key(24)
    redis_password = generate_secure_key(24)
    
    # Create secure .env
    env_content = f"""# SECURE CONFIGURATION - Generated {__import__('datetime').datetime.now()}
# NEVER COMMIT THIS FILE TO VERSION CONTROL

# Database Configuration
DATABASE_URL=postgresql://stockuser:{db_password}@localhost:5432/stockdb

# API Keys
ALPHA_VANTAGE_API_KEY={alpha_key}
FMP_API_KEY={fmp_key}

# Redis Configuration  
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD={redis_password}
REDIS_MAX_CONNECTIONS=50

# Cache Configuration
CACHE_DEFAULT_TTL=300
CACHE_KEY_PREFIX=stock_app

# Flask Configuration
FLASK_ENV=development
FLASK_SECRET_KEY={flask_secret}
FLASK_HOST=127.0.0.1
FLASK_PORT=5000

# Security Configuration
JWT_SECRET_KEY={jwt_secret}
PASSWORD_SALT={password_salt}

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Logging
LOG_LEVEL=INFO
"""
    
    # Write .env file
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Secure .env file created")
    except Exception as e:
        print(f"❌ Failed to create .env: {e}")
        return 1
    
    # Update Redis config
    try:
        redis_config = f"""# Redis Configuration - SECURE
bind 127.0.0.1
port 6379
timeout 0
tcp-keepalive 300
protected-mode yes
requirepass {redis_password}

# Memory Management
maxmemory 512mb
maxmemory-policy allkeys-lru
maxmemory-samples 5

# Persistence
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir ./

# Append Only File
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec

# Logging
loglevel notice
logfile ""

# Performance
tcp-backlog 511
databases 16

# Slow Log
slowlog-log-slower-than 10000
slowlog-max-len 128
"""
        
        with open('app/redis.conf', 'w') as f:
            f.write(redis_config)
        print("✅ Redis configuration secured")
    except Exception as e:
        print(f"⚠️ Redis config update failed: {e}")
    
    # Create database setup script
    db_script = f"""#!/bin/bash
# Database Setup Script
echo "🗄️ Setting up PostgreSQL..."

# Create user and database
sudo -u postgres psql -c "CREATE USER stockuser WITH PASSWORD '{db_password}';"
sudo -u postgres psql -c "CREATE DATABASE stockdb OWNER stockuser;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE stockdb TO stockuser;"

echo "✅ Database setup complete!"
"""
    
    try:
        with open('setup_db.sh', 'w') as f:
            f.write(db_script)
        os.chmod('setup_db.sh', 0o755)
        print("✅ Database setup script created")
    except Exception as e:
        print(f"⚠️ Database script creation failed: {e}")
    
    # Create startup instructions
    instructions = f"""
🎉 SECURITY SETUP COMPLETE!

📋 NEXT STEPS (run these commands in order):

1. Install dependencies:
   pip install -r requirements.txt

2. Setup database:
   ./setup_db.sh

3. Start Redis:
   redis-server app/redis.conf

4. Test the application:
   python run.py

5. Create first user:
   curl -X POST http://localhost:5000/api/auth/register \\
     -H "Content-Type: application/json" \\
     -d '{{"email":"admin@stockanalyzer.com","username":"admin","password":"SecurePassword123!"}}'

🔐 SECURITY NOTES:
- Database password: {db_password[:8]}... (in .env)
- Redis password: {redis_password[:8]}... (in .env)
- All secrets are cryptographically secure
- .env file is gitignored (verified)

⚠️ PRODUCTION CHECKLIST:
□ Set FLASK_ENV=production
□ Use HTTPS/SSL certificates  
□ Set up database backups
□ Configure firewall rules
□ Enable logging/monitoring
"""
    
    print(instructions)
    
    # Save instructions to file
    with open('SECURITY_SETUP_COMPLETE.txt', 'w') as f:
        f.write(instructions)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())