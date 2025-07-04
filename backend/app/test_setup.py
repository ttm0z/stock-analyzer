import redis
import os
from dotenv import load_dotenv

load_dotenv()

# Test Redis connection
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=0
    )
    
    # Test connection
    redis_client.ping()
    print("✅ Redis connection successful!")
    
    # Test set/get
    redis_client.set('test_key', 'Hello from Fedora!')
    value = redis_client.get('test_key').decode('utf-8')
    print(f"✅ Redis test value: {value}")
    
    # Cleanup
    redis_client.delete('test_key')
    print("✅ Setup test completed successfully!")
    
except Exception as e:
    print(f"❌ Setup test failed: {e}")
