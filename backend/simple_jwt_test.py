#!/usr/bin/env python3
"""
Simple JWT token generation test
"""
import os
import jwt
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

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
        print(f"Token length: {len(str(token))}")
        print(f"Token (first 50 chars): {str(token)[:50]}...")
        
        # Handle bytes vs string
        if isinstance(token, bytes):
            token_str = token.decode('utf-8')
            print(f"Converted bytes to string: {token_str[:50]}...")
        else:
            token_str = token
            print(f"Token is already string: {token_str[:50]}...")
        
        # Test decoding
        decoded = jwt.decode(token_str, secret_key, algorithms=['HS256'])
        print(f"✅ JWT decoding successful: {decoded['username']}")
        
        return token_str
        
    except Exception as e:
        print(f"❌ Direct JWT encoding failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    token = test_jwt_generation()
    if token:
        print(f"\n🎉 JWT generation works! Token: {token}")
    else:
        print(f"\n💥 JWT generation failed!")