"""Advanced rate limiting system with Redis backend."""

from __future__ import annotations

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

from .caching import cache_manager
from .config import SETTINGS

logger = logging.getLogger(__name__)

class RateLimitType(Enum):
    """Types of rate limiting."""
    GLOBAL = "global"
    PER_IP = "per_ip"
    PER_USER = "per_user"
    PER_ENDPOINT = "per_endpoint"

class RateLimitConfig:
    """Rate limiting configuration."""
    
    def __init__(
        self,
        requests: int = 100,
        window: int = 3600,  # seconds
        burst: int = 10,  # burst allowance
        rate_limit_type: RateLimitType = RateLimitType.PER_IP
    ):
        self.requests = requests
        self.window = window
        self.burst = burst
        self.rate_limit_type = rate_limit_type

class RateLimiter:
    """Advanced rate limiter with Redis backend."""
    
    def __init__(self):
        self.cache = cache_manager
        self.default_config = RateLimitConfig(
            requests=SETTINGS.rate_limit_requests,
            window=SETTINGS.rate_limit_window
        )
        
        # Rate limit configurations for different endpoints
        self.endpoint_configs = {
            "/api/v1/alerts": RateLimitConfig(requests=200, window=3600),
            "/api/v1/ai/analyze": RateLimitConfig(requests=50, window=3600),
            "/api/v1/mcp/scan": RateLimitConfig(requests=10, window=3600),
            "/api/v1/database/optimize": RateLimitConfig(requests=5, window=3600),
            "/api/v1/settings/test-email": RateLimitConfig(requests=3, window=300),
            "/api/v1/settings/test-intel": RateLimitConfig(requests=10, window=300),
        }
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get client identifier based on rate limit type."""
        # Get real IP (considering proxies)
        client_ip = request.headers.get("x-forwarded-for")
        if not client_ip:
            client_ip = request.headers.get("x-real-ip")
        if not client_ip:
            client_ip = request.client.host
        
        # Get user identifier if available
        user_id = request.headers.get("x-user-id")
        
        return {
            RateLimitType.GLOBAL: "global",
            RateLimitType.PER_IP: f"ip:{client_ip}",
            RateLimitType.PER_USER: f"user:{user_id}" if user_id else f"ip:{client_ip}",
            RateLimitType.PER_ENDPOINT: f"endpoint:{request.url.path}"
        }
    
    def _get_rate_limit_key(
        self, 
        request: Request, 
        config: RateLimitConfig,
        identifier: str
    ) -> str:
        """Generate rate limit key."""
        base_key = f"rate_limit:{config.rate_limit_type.value}:{identifier}"
        
        if config.rate_limit_type == RateLimitType.PER_ENDPOINT:
            base_key += f":{request.url.path}"
        
        # Add time window
        current_window = int(time.time() // config.window)
        return f"{base_key}:{current_window}"
    
    def _get_burst_key(self, base_key: str) -> str:
        """Generate burst allowance key."""
        return f"{base_key}:burst"
    
    def _is_rate_limited(
        self, 
        request: Request, 
        config: RateLimitConfig
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is rate limited."""
        if not self.cache.is_available():
            # If Redis is down, allow request but log warning
            logger.warning("Rate limiting disabled: Redis unavailable")
            return False, {}
        
        identifier = self._get_client_identifier(request)[config.rate_limit_type]
        rate_limit_key = self._get_rate_limit_key(request, config, identifier)
        burst_key = self._get_burst_key(rate_limit_key)
        
        try:
            # Use Redis pipeline for atomic operations
            pipe = self.cache.redis_client.pipeline()
            
            # Get current count
            pipe.get(rate_limit_key)
            pipe.get(burst_key)
            pipe.expire(rate_limit_key, config.window)
            pipe.expire(burst_key, config.window)
            
            results = pipe.execute()
            current_count = int(results[0] or 0)
            burst_count = int(results[1] or 0)
            
            # Check if we're within limits
            if current_count >= config.requests:
                # Check burst allowance
                if burst_count >= config.burst:
                    # Rate limited
                    remaining_time = self.cache.redis_client.ttl(rate_limit_key)
                    return True, {
                        "limit": config.requests,
                        "remaining": 0,
                        "reset_time": int(time.time()) + remaining_time,
                        "retry_after": remaining_time,
                        "burst_remaining": 0
                    }
                else:
                    # Use burst allowance
                    pipe.incr(burst_key)
                    pipe.expire(burst_key, config.window)
                    pipe.execute()
            
            # Increment counter
            pipe.incr(rate_limit_key)
            pipe.expire(rate_limit_key, config.window)
            pipe.execute()
            
            # Calculate remaining requests
            remaining = max(0, config.requests - current_count - 1)
            burst_remaining = max(0, config.burst - burst_count)
            
            return False, {
                "limit": config.requests,
                "remaining": remaining,
                "reset_time": int(time.time()) + config.window,
                "burst_remaining": burst_remaining
            }
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # On error, allow request but log
            return False, {}
    
    def check_rate_limit(self, request: Request) -> Optional[Dict[str, Any]]:
        """Check rate limit for request."""
        # Get endpoint-specific config or use default
        endpoint_config = self.endpoint_configs.get(
            request.url.path, 
            self.default_config
        )
        
        is_limited, rate_info = self._is_rate_limited(request, endpoint_config)
        
        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "rate_limit": rate_info
                },
                headers={
                    "X-RateLimit-Limit": str(rate_info["limit"]),
                    "X-RateLimit-Remaining": str(rate_info["remaining"]),
                    "X-RateLimit-Reset": str(rate_info["reset_time"]),
                    "Retry-After": str(rate_info["retry_after"])
                }
            )
        
        return rate_info
    
    def get_rate_limit_info(self, request: Request) -> Dict[str, Any]:
        """Get rate limit information without enforcing."""
        endpoint_config = self.endpoint_configs.get(
            request.url.path, 
            self.default_config
        )
        
        identifier = self._get_client_identifier(request)[endpoint_config.rate_limit_type]
        rate_limit_key = self._get_rate_limit_key(request, endpoint_config, identifier)
        
        try:
            current_count = int(self.cache.redis_client.get(rate_limit_key) or 0)
            remaining = max(0, endpoint_config.requests - current_count)
            ttl = self.cache.redis_client.ttl(rate_limit_key)
            
            return {
                "limit": endpoint_config.requests,
                "remaining": remaining,
                "reset_time": int(time.time()) + ttl if ttl > 0 else int(time.time()) + endpoint_config.window,
                "window": endpoint_config.window
            }
        except Exception as e:
            logger.error(f"Rate limit info error: {e}")
            return {
                "limit": endpoint_config.requests,
                "remaining": endpoint_config.requests,
                "reset_time": int(time.time()) + endpoint_config.window,
                "window": endpoint_config.window
            }

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware."""
    try:
        # Check rate limit
        rate_info = rate_limiter.check_rate_limit(request)
        
        # Process request
        response = call_next(request)
        
        # Add rate limit headers
        if rate_info:
            response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(rate_info["reset_time"])
            if "burst_remaining" in rate_info:
                response.headers["X-RateLimit-Burst-Remaining"] = str(rate_info["burst_remaining"])
        
        return response
        
    except HTTPException as e:
        if e.status_code == 429:
            return JSONResponse(
                status_code=429,
                content=e.detail,
                headers=e.headers
            )
        raise e
    except Exception as e:
        logger.error(f"Rate limiting middleware error: {e}")
        # On error, allow request
        return call_next(request)

def get_rate_limit_stats() -> Dict[str, Any]:
    """Get rate limiting statistics."""
    if not cache_manager.is_available():
        return {"status": "unavailable"}
    
    try:
        # Get all rate limit keys
        pattern = "rate_limit:*"
        keys = cache_manager.redis_client.keys(pattern)
        
        stats = {
            "status": "available",
            "total_keys": len(keys),
            "endpoints": {},
            "global_stats": {
                "total_requests": 0,
                "rate_limited_requests": 0
            }
        }
        
        # Analyze keys
        for key in keys:
            key_parts = key.decode().split(":")
            if len(key_parts) >= 3:
                endpoint = key_parts[2] if len(key_parts) > 2 else "unknown"
                if endpoint not in stats["endpoints"]:
                    stats["endpoints"][endpoint] = {
                        "keys": 0,
                        "total_requests": 0
                    }
                
                stats["endpoints"][endpoint]["keys"] += 1
                count = int(cache_manager.redis_client.get(key) or 0)
                stats["endpoints"][endpoint]["total_requests"] += count
                stats["global_stats"]["total_requests"] += count
        
        return stats
        
    except Exception as e:
        logger.error(f"Rate limit stats error: {e}")
        return {"status": "error", "error": str(e)}
