# services/cache_service.py
import os
import redis
import json
import hashlib
import logging
from typing import Any, Optional, Dict
import pickle

logger = logging.getLogger(__name__)

class CacheService:
    """Redis cache service for the stock analyzer"""
    
    def __init__(self, redis_client=None, default_ttl=300, key_prefix='stock_app'):
        self.redis = redis_client
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'errors': 0
        }
    
    @classmethod
    def create_instance(cls):
        """Create cache service instance with Redis connection"""
        try:
            redis_config = {
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', 6379)),
                'db': int(os.getenv('REDIS_DB', 0)),
                'decode_responses': False,
                'socket_timeout': 5,
                'socket_connect_timeout': 5,
                'retry_on_timeout': True,
                'max_connections': int(os.getenv('REDIS_MAX_CONNECTIONS', 50))
            }
            
            redis_client = redis.Redis(**redis_config)
            
            # Test connection
            redis_client.ping()
            logger.info(f"✅ Redis connected: {redis_config['host']}:{redis_config['port']}")
            
            return cls(
                redis_client=redis_client,
                default_ttl=int(os.getenv('CACHE_DEFAULT_TTL', 300)),
                key_prefix=os.getenv('CACHE_KEY_PREFIX', 'stock_app')
            )
            
        except redis.ConnectionError as e:
            logger.error(f"❌ Redis connection failed: {e}")
            logger.warning("⚠️  Continuing without cache - performance will be degraded")
            return cls(redis_client=None)
        except Exception as e:
            logger.error(f"❌ Redis setup error: {e}")
            return cls(redis_client=None)
    
    def _generate_key(self, namespace: str, identifier: str, params: Dict = None) -> str:
        """Generate consistent cache key"""
        key_parts = [self.key_prefix, namespace, identifier]
        
        if params:
            param_str = json.dumps(params, sort_keys=True, default=str)
            param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
            key_parts.append(param_hash)
        
        return ':'.join(key_parts)
    
    def _serialize_data(self, data: Any) -> bytes:
        """Serialize data for Redis storage"""
        try:
            if isinstance(data, (dict, list, str, int, float, bool, type(None))):
                return json.dumps(data, default=str).encode('utf-8')
            else:
                return pickle.dumps(data)
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            raise
    
    def _deserialize_data(self, data: bytes) -> Any:
        """Deserialize data from Redis"""
        try:
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            try:
                return pickle.loads(data)
            except Exception as e:
                logger.error(f"Deserialization error: {e}")
                raise
    
    def get(self, namespace: str, identifier: str, params: Dict = None) -> Optional[Any]:
        """Get data from cache"""
        if not self.redis:
            return None
        
        cache_key = self._generate_key(namespace, identifier, params)
        
        try:
            cached_data = self.redis.get(cache_key)
            if cached_data:
                self.stats['hits'] += 1
                logger.debug(f"🎯 Cache HIT: {cache_key}")
                return self._deserialize_data(cached_data)
            else:
                self.stats['misses'] += 1
                logger.debug(f"❌ Cache MISS: {cache_key}")
                return None
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Cache GET error for {cache_key}: {e}")
            return None
    
    def set(self, namespace: str, identifier: str, data: Any, 
            ttl: Optional[int] = None, params: Dict = None) -> bool:
        """Set data in cache"""
        if not self.redis:
            return False
        
        cache_key = self._generate_key(namespace, identifier, params)
        ttl = ttl if ttl is not None else self.default_ttl
        
        try:
            serialized_data = self._serialize_data(data)
            result = self.redis.setex(cache_key, ttl, serialized_data)
            if result:
                self.stats['sets'] += 1
                logger.debug(f"💾 Cache SET: {cache_key} (TTL: {ttl}s)")
            return result
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Cache SET error for {cache_key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete multiple cache entries matching pattern"""
        if not self.redis:
            return 0
        
        try:
            keys = self.redis.keys(pattern)
            if keys:
                deleted = self.redis.delete(*keys)
                logger.info(f"🧹 Cache DELETE PATTERN: {pattern} - {deleted} keys deleted")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache DELETE PATTERN error for {pattern}: {e}")
            return 0
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_operations = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_operations * 100) if total_operations > 0 else 0
        
        stats = {
            **self.stats,
            'hit_rate': round(hit_rate, 2),
            'total_operations': total_operations
        }
        
        if self.redis:
            try:
                redis_info = self.redis.info('memory')
                stats.update({
                    'redis_memory_used': redis_info.get('used_memory_human', 'N/A'),
                    'redis_keys': self.redis.dbsize(),
                    'redis_connected': True
                })
            except Exception:
                stats.update({
                    'redis_connected': False
                })
        
        return stats
    
    def clear_stats(self):
        """Reset cache statistics"""
        self.stats = {'hits': 0, 'misses': 0, 'sets': 0, 'errors': 0}

# Cache TTL constants
class CacheTTL:
    """Cache TTL constants for different types of data"""
    REAL_TIME_QUOTES = 60           # 1 minute
    SEARCH_RESULTS = 300            # 5 minutes  
    COMPANY_PROFILES = 3600         # 1 hour
    FINANCIAL_STATEMENTS = 86400    # 24 hours
    HISTORICAL_DATA = 3600          # 1 hour
    MARKET_NEWS = 300               # 5 minutes