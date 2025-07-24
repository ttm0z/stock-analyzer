#!/usr/bin/env python3
"""
Quick Redis connectivity test
"""
import redis
import os

def test_redis_connection():
    """Test Redis connection with your configuration"""
    
    # Load password from environment
    redis_password = "7nU4pIfCGUyqb08dyd55VF3z5QAZmPOG"  # From your .env
    
    print("🔍 Testing Redis Connection...")
    print(f"Host: 127.0.0.1")
    print(f"Port: 6379")
    print(f"Password: {'*' * len(redis_password)}")
    
    try:
        # Create Redis connection
        r = redis.Redis(
            host='127.0.0.1',
            port=6389,
            password=redis_password,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        
        # Test connection
        print("\n📡 Testing connection...")
        response = r.ping()
        
        if response:
            print("✅ Redis connection successful!")
            
            # Test basic operations
            print("\n🧪 Testing operations...")
            r.set('test_key', 'test_value')
            retrieved = r.get('test_key')
            
            if retrieved == 'test_value':
                print("✅ Redis read/write working!")
                r.delete('test_key')  # Clean up
            else:
                print("❌ Redis read/write failed!")
            
            # Get Redis info
            info = r.info()
            print(f"\n📊 Redis Info:")
            print(f"   Version: {info.get('redis_version', 'Unknown')}")
            print(f"   Memory used: {info.get('used_memory_human', 'Unknown')}")
            print(f"   Connected clients: {info.get('connected_clients', 'Unknown')}")
            
            return True
            
    except redis.ConnectionError as e:
        print(f"❌ Redis connection failed: {e}")
        print("\n💡 Try starting Redis:")
        print("   redis-server /home/t/Projects/stock-analyzer/backend/app/redis.conf")
        return False
        
    except redis.AuthenticationError as e:
        print(f"❌ Redis authentication failed: {e}")
        print("💡 Check password in redis.conf matches .env")
        return False
        
    except Exception as e:
        print(f"❌ Redis test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_redis_connection()
    exit(0 if success else 1)