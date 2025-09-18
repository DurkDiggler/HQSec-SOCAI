#!/usr/bin/env python3
"""
API Performance Test Script

This script demonstrates the API performance optimizations including:
- Response caching
- Rate limiting
- Database query optimization
- Request/response compression
"""

import asyncio
import time
import json
import requests
from typing import Dict, Any
import statistics

class APIPerformanceTester:
    """Test API performance optimizations."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {}
    
    def test_cache_performance(self) -> Dict[str, Any]:
        """Test response caching performance."""
        print("🧪 Testing Response Caching...")
        
        # Test cached endpoint multiple times
        endpoint = f"{self.base_url}/api/v1/alerts"
        times = []
        
        for i in range(5):
            start_time = time.time()
            response = self.session.get(endpoint)
            end_time = time.time()
            
            if response.status_code == 200:
                times.append(end_time - start_time)
                cached = response.json().get('cached', False)
                print(f"  Request {i+1}: {end_time - start_time:.3f}s (cached: {cached})")
        
        avg_time = statistics.mean(times) if times else 0
        print(f"  Average response time: {avg_time:.3f}s")
        
        return {
            "endpoint": endpoint,
            "average_time": avg_time,
            "times": times,
            "cached_responses": sum(1 for t in times if t < 0.1)  # Assume <0.1s is cached
        }
    
    def test_rate_limiting(self) -> Dict[str, Any]:
        """Test rate limiting functionality."""
        print("\n🚦 Testing Rate Limiting...")
        
        # Test rate limit endpoint
        endpoint = f"{self.base_url}/api/v1/performance/rate-limits"
        response = self.session.get(endpoint)
        
        if response.status_code == 200:
            rate_limit_stats = response.json()
            print(f"  Rate limiting status: {rate_limit_stats.get('rate_limit_stats', {}).get('status', 'unknown')}")
            print(f"  Total rate limit keys: {rate_limit_stats.get('rate_limit_stats', {}).get('total_keys', 0)}")
            return rate_limit_stats
        else:
            print(f"  Failed to get rate limit stats: {response.status_code}")
            return {"error": f"HTTP {response.status_code}"}
    
    def test_compression(self) -> Dict[str, Any]:
        """Test response compression."""
        print("\n🗜️ Testing Response Compression...")
        
        # Test with different Accept-Encoding headers
        endpoints = [
            f"{self.base_url}/api/v1/dashboard",
            f"{self.base_url}/api/v1/statistics"
        ]
        
        compression_results = {}
        
        for endpoint in endpoints:
            # Test without compression
            response_no_compression = self.session.get(endpoint)
            size_no_compression = len(response_no_compression.content)
            
            # Test with gzip compression
            headers_gzip = {"Accept-Encoding": "gzip"}
            response_gzip = self.session.get(endpoint, headers=headers_gzip)
            size_gzip = len(response_gzip.content)
            
            # Test with brotli compression
            headers_brotli = {"Accept-Encoding": "br"}
            response_brotli = self.session.get(endpoint, headers=headers_brotli)
            size_brotli = len(response_brotli.content)
            
            compression_ratio_gzip = (1 - size_gzip / size_no_compression) * 100 if size_no_compression > 0 else 0
            compression_ratio_brotli = (1 - size_brotli / size_no_compression) * 100 if size_no_compression > 0 else 0
            
            print(f"  {endpoint.split('/')[-1]}:")
            print(f"    Original: {size_no_compression} bytes")
            print(f"    Gzip: {size_gzip} bytes ({compression_ratio_gzip:.1f}% reduction)")
            print(f"    Brotli: {size_brotli} bytes ({compression_ratio_brotli:.1f}% reduction)")
            
            compression_results[endpoint] = {
                "original_size": size_no_compression,
                "gzip_size": size_gzip,
                "brotli_size": size_brotli,
                "gzip_ratio": compression_ratio_gzip,
                "brotli_ratio": compression_ratio_brotli
            }
        
        return compression_results
    
    def test_database_performance(self) -> Dict[str, Any]:
        """Test database performance metrics."""
        print("\n🗄️ Testing Database Performance...")
        
        # Get database metrics
        endpoint = f"{self.base_url}/api/v1/database/metrics"
        response = self.session.get(endpoint)
        
        if response.status_code == 200:
            db_metrics = response.json()
            metrics = db_metrics.get('database_metrics', {})
            
            print(f"  Query count: {metrics.get('query_count', 0)}")
            print(f"  Average query time: {metrics.get('avg_query_time', 0):.3f}s")
            print(f"  Slow queries: {len(metrics.get('slow_queries', []))}")
            
            # Connection pool stats
            pool_stats = metrics.get('connection_pool_stats', {})
            print(f"  Pool size: {pool_stats.get('pool_size', 0)}")
            print(f"  Checked out: {pool_stats.get('checked_out', 0)}")
            print(f"  Overflow: {pool_stats.get('overflow', 0)}")
            
            return db_metrics
        else:
            print(f"  Failed to get database metrics: {response.status_code}")
            return {"error": f"HTTP {response.status_code}"}
    
    def test_performance_overview(self) -> Dict[str, Any]:
        """Test overall performance overview."""
        print("\n📊 Testing Performance Overview...")
        
        endpoint = f"{self.base_url}/api/v1/performance/overview"
        response = self.session.get(endpoint)
        
        if response.status_code == 200:
            overview = response.json()
            overview_data = overview.get('overview', {})
            
            print(f"  Overall status: {overview_data.get('status', 'unknown')}")
            print(f"  Health score: {overview_data.get('health_score', 0)}/100")
            print(f"  Issues: {len(overview_data.get('issues', []))}")
            
            if overview_data.get('issues'):
                print("  Issues found:")
                for issue in overview_data.get('issues', []):
                    print(f"    - {issue}")
            
            return overview
        else:
            print(f"  Failed to get performance overview: {response.status_code}")
            return {"error": f"HTTP {response.status_code}"}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all performance tests."""
        print("🚀 Starting API Performance Tests")
        print("=" * 50)
        
        results = {
            "timestamp": time.time(),
            "base_url": self.base_url,
            "tests": {}
        }
        
        try:
            # Test caching
            results["tests"]["caching"] = self.test_cache_performance()
            
            # Test rate limiting
            results["tests"]["rate_limiting"] = self.test_rate_limiting()
            
            # Test compression
            results["tests"]["compression"] = self.test_compression()
            
            # Test database performance
            results["tests"]["database"] = self.test_database_performance()
            
            # Test performance overview
            results["tests"]["overview"] = self.test_performance_overview()
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            results["error"] = str(e)
        
        print("\n" + "=" * 50)
        print("✅ Performance tests completed!")
        
        return results

def main():
    """Main function to run performance tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test API performance optimizations")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--output", help="Output file for results (JSON)")
    
    args = parser.parse_args()
    
    # Run tests
    tester = APIPerformanceTester(args.url)
    results = tester.run_all_tests()
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Results saved to {args.output}")
    
    return results

if __name__ == "__main__":
    main()
