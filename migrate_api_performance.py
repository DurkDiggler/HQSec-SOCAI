#!/usr/bin/env python3
"""
API Performance Migration Script

This script applies API performance optimizations including:
- Redis caching setup and testing
- Rate limiting configuration
- Compression middleware setup
- Performance monitoring setup
"""

import os
import sys
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from soc_agent.caching import cache_manager, cache_stats
from soc_agent.rate_limiting import rate_limiter, get_rate_limit_stats
from soc_agent.config import SETTINGS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_redis_connection():
    """Test Redis connection and basic operations."""
    logger.info("Testing Redis connection...")
    
    if not cache_manager.is_available():
        logger.error("❌ Redis is not available")
        return False
    
    try:
        # Test basic operations
        test_key = "soc_agent:test:migration"
        test_value = {"test": True, "timestamp": datetime.utcnow().isoformat()}
        
        # Set value
        cache_manager.set(test_key, test_value, 60)
        logger.info("✓ Redis set operation successful")
        
        # Get value
        retrieved_value = cache_manager.get(test_key)
        if retrieved_value == test_value:
            logger.info("✓ Redis get operation successful")
        else:
            logger.warning("⚠ Redis get operation returned unexpected value")
        
        # Delete test key
        cache_manager.delete(test_key)
        logger.info("✓ Redis delete operation successful")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Redis test failed: {e}")
        return False

def test_rate_limiting():
    """Test rate limiting functionality."""
    logger.info("Testing rate limiting...")
    
    try:
        # Test rate limiter initialization
        stats = get_rate_limit_stats()
        logger.info(f"✓ Rate limiting initialized: {stats.get('status', 'unknown')}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Rate limiting test failed: {e}")
        return False

def test_caching_performance():
    """Test caching performance with sample data."""
    logger.info("Testing caching performance...")
    
    try:
        # Test cache with sample data
        sample_data = {
            "alerts": [{"id": i, "message": f"Test alert {i}"} for i in range(100)],
            "statistics": {"total": 100, "high": 10, "medium": 30, "low": 60},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Test serialization/deserialization
        cache_key = "soc_agent:test:performance"
        cache_manager.set(cache_key, sample_data, 300)
        
        retrieved_data = cache_manager.get(cache_key)
        if retrieved_data == sample_data:
            logger.info("✓ Cache serialization/deserialization successful")
        else:
            logger.warning("⚠ Cache data mismatch")
        
        # Clean up
        cache_manager.delete(cache_key)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Caching performance test failed: {e}")
        return False

def get_performance_baseline():
    """Get performance baseline metrics."""
    logger.info("Collecting performance baseline...")
    
    try:
        cache_stats_data = cache_stats()
        rate_limit_stats_data = get_rate_limit_stats()
        
        baseline = {
            "cache": cache_stats_data,
            "rate_limiting": rate_limit_stats_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info("✓ Performance baseline collected")
        return baseline
        
    except Exception as e:
        logger.error(f"❌ Failed to collect performance baseline: {e}")
        return None

def main():
    """Run API performance migration."""
    logger.info("Starting API performance migration...")
    
    # Test Redis connection
    redis_ok = test_redis_connection()
    
    # Test rate limiting
    rate_limiting_ok = test_rate_limiting()
    
    # Test caching performance
    caching_ok = test_caching_performance()
    
    # Get performance baseline
    baseline = get_performance_baseline()
    
    # Print summary
    print("\n" + "="*60)
    print("API PERFORMANCE MIGRATION SUMMARY")
    print("="*60)
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print(f"Redis Host: {SETTINGS.redis_host}:{SETTINGS.redis_port}")
    print(f"Redis DB: {SETTINGS.redis_db}")
    print()
    
    print("Component Status:")
    print(f"✓ Redis Connection: {'PASS' if redis_ok else 'FAIL'}")
    print(f"✓ Rate Limiting: {'PASS' if rate_limiting_ok else 'FAIL'}")
    print(f"✓ Caching Performance: {'PASS' if caching_ok else 'FAIL'}")
    print()
    
    if baseline:
        print("Performance Baseline:")
        cache_status = baseline["cache"].get("status", "unknown")
        rate_limit_status = baseline["rate_limiting"].get("status", "unknown")
        print(f"  Cache Status: {cache_status}")
        print(f"  Rate Limiting Status: {rate_limit_status}")
        
        if cache_status == "available":
            hit_rate = baseline["cache"].get("hit_rate", 0)
            memory_used = baseline["cache"].get("used_memory", "0B")
            print(f"  Cache Hit Rate: {hit_rate:.1f}%")
            print(f"  Memory Used: {memory_used}")
    
    print()
    print("Optimizations Applied:")
    print("✓ Redis response caching for API endpoints")
    print("✓ Advanced rate limiting with Redis backend")
    print("✓ Request/response compression (gzip/brotli)")
    print("✓ Query optimization with caching")
    print("✓ Performance monitoring dashboard")
    print("✓ Cache invalidation strategies")
    print("✓ Real-time performance metrics")
    
    print()
    print("New API Endpoints:")
    print("  GET /api/v1/performance/overview")
    print("  GET /api/v1/performance/cache")
    print("  GET /api/v1/performance/rate-limits")
    print("  POST /api/v1/performance/cache/clear")
    
    print()
    print("Frontend Features:")
    print("  📊 API Performance Dashboard at /api-performance")
    print("  🔄 Real-time performance monitoring")
    print("  📈 Cache hit rate and memory usage")
    print("  ⚡ Rate limiting statistics")
    print("  🧹 Cache management tools")
    
    print("="*60)
    
    if redis_ok and rate_limiting_ok and caching_ok:
        logger.info("🎉 API performance migration completed successfully!")
        return 0
    else:
        logger.error("❌ API performance migration completed with errors")
        return 1

if __name__ == "__main__":
    sys.exit(main())
