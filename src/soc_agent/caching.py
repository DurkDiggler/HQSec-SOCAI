"""Redis-based caching system for API performance optimization."""

from __future__ import annotations

import json
import logging
import pickle
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps

import redis
from redis.exceptions import RedisError

from .config import SETTINGS

logger = logging.getLogger(__name__)

class CacheManager:
    """Redis-based cache manager with advanced features."""
    
    def __init__(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.Redis(
                host=SETTINGS.redis_host,
                port=SETTINGS.redis_port,
                password=SETTINGS.redis_password,
                db=SETTINGS.redis_db,
                decode_responses=False,  # Keep binary for pickle
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache connection established")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def is_available(self) -> bool:
        """Check if Redis is available."""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except RedisError:
            return False
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage."""
        try:
            # Try JSON first for simple types
            if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                return json.dumps(value, default=str).encode('utf-8')
            else:
                # Use pickle for complex objects
                return pickle.dumps(value)
        except (TypeError, ValueError):
            # Fallback to pickle
            return pickle.dumps(value)
    
    def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize value from storage."""
        try:
            # Try JSON first
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fallback to pickle
            return pickle.loads(data)
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        # Create hash of arguments
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"soc_agent:{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.is_available():
            return None
        
        try:
            data = self.redis_client.get(key)
            if data is None:
                return None
            return self._deserialize_value(data)
        except RedisError as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL."""
        if not self.is_available():
            return False
        
        try:
            serialized_value = self._serialize_value(value)
            return self.redis_client.setex(key, ttl, serialized_value)
        except RedisError as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.is_available():
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except RedisError as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern."""
        if not self.is_available():
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except RedisError as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.is_available():
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except RedisError as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    def get_ttl(self, key: str) -> int:
        """Get TTL for key."""
        if not self.is_available():
            return -1
        
        try:
            return self.redis_client.ttl(key)
        except RedisError as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return -1
    
    def increment(self, key: str, amount: int = 1, ttl: int = 3600) -> int:
        """Increment counter in cache."""
        if not self.is_available():
            return 0
        
        try:
            pipe = self.redis_client.pipeline()
            pipe.incr(key, amount)
            pipe.expire(key, ttl)
            results = pipe.execute()
            return results[0]
        except RedisError as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.is_available():
            return {"status": "unavailable"}
        
        try:
            info = self.redis_client.info()
            return {
                "status": "available",
                "used_memory": info.get("used_memory_human", "0B"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info),
                "uptime_seconds": info.get("uptime_in_seconds", 0)
            }
        except RedisError as e:
            logger.error(f"Cache stats error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _calculate_hit_rate(self, info: Dict[str, Any]) -> float:
        """Calculate cache hit rate."""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0

# Global cache manager instance
cache_manager = CacheManager()

def cached(ttl: int = 3600, key_prefix: str = "api", vary_by: List[str] = None):
    """Decorator for caching function results."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_manager._generate_key(
                f"{key_prefix}:{func.__name__}",
                *args,
                **{k: v for k, v in kwargs.items() if not vary_by or k in vary_by}
            )
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            logger.debug(f"Cached result for {func.__name__}")
            
            return result
        
        return wrapper
    return decorator

def cache_invalidate(pattern: str = None, keys: List[str] = None):
    """Invalidate cache entries."""
    if pattern:
        return cache_manager.delete_pattern(pattern)
    elif keys:
        deleted = 0
        for key in keys:
            if cache_manager.delete(key):
                deleted += 1
        return deleted
    return 0

def cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    return cache_manager.get_stats()

# Cache key generators for common patterns
class CacheKeys:
    """Standard cache key patterns."""
    
    @staticmethod
    def alerts(skip: int = 0, limit: int = 100, **filters) -> str:
        """Generate cache key for alerts query."""
        return cache_manager._generate_key(
            "alerts",
            skip, limit,
            **filters
        )
    
    @staticmethod
    def alert_stats(days: int = 7) -> str:
        """Generate cache key for alert statistics."""
        return cache_manager._generate_key("alert_stats", days)
    
    @staticmethod
    def dashboard_data(days: int = 7) -> str:
        """Generate cache key for dashboard data."""
        return cache_manager._generate_key("dashboard", days)
    
    @staticmethod
    def ai_analysis(alert_id: int) -> str:
        """Generate cache key for AI analysis."""
        return cache_manager._generate_key("ai_analysis", alert_id)
    
    @staticmethod
    def top_sources(limit: int = 10) -> str:
        """Generate cache key for top sources."""
        return cache_manager._generate_key("top_sources", limit)
    
    @staticmethod
    def top_event_types(limit: int = 10) -> str:
        """Generate cache key for top event types."""
        return cache_manager._generate_key("top_event_types", limit)
    
    @staticmethod
    def top_ips(limit: int = 10) -> str:
        """Generate cache key for top IPs."""
        return cache_manager._generate_key("top_ips", limit)
    
    @staticmethod
    def database_metrics() -> str:
        """Generate cache key for database metrics."""
        return cache_manager._generate_key("database_metrics")
    
    @staticmethod
    def table_statistics() -> str:
        """Generate cache key for table statistics."""
        return cache_manager._generate_key("table_statistics")
