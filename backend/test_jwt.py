#!/usr/bin/env python3
"""
Quick JWT token generation test
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from auth.models import User
from datetime import datetime, timedelta
import jwt

def test_jwt_generation():
    print("Testing JWT token generation...")
    
    # Check if JWT_SECRET_KEY is available
    secret_key = os.getenv('JWT_SECRET_KEY')
    print(f"JWT_SECRET_KEY exists: {bool(secret_key)}")
    print(f"JWT_SECRET_KEY length: {len(secret_key) if secret_key else 0}")
    
    if not secret_key:
        print("❌ JWT_SECRET_KEY is not set!")
        return
    
    # Test direct JWT encoding
    try:
        test_payload = {
            'user_id': 123,
            'username': 'testuser',
            'email': 'test@example.com',
            'exp': datetime.utcnow() + timedelta(seconds=3600),
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(test_payload, secret_key, algorithm='HS256')
        print(f"✅ Direct JWT encoding successful")
        print(f"Token type: {type(token)}")
        print(f"Token (first 50 chars): {str(token)[:50]}...")
        
        # Test decoding
        decoded = jwt.decode(token, secret_key, algorithms=['HS256'])
        print(f"✅ JWT decoding successful: {decoded['username']}")
        
    except Exception as e:
        print(f"❌ Direct JWT encoding failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_jwt_generation()