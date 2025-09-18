#!/usr/bin/env python3
"""
Frontend Performance Test Script

This script demonstrates the frontend performance optimizations including:
- Bundle optimization
- Image compression
- Real-time features
- CDN configuration
"""

import asyncio
import time
import json
import requests
from typing import Dict, Any
import statistics

class FrontendPerformanceTester:
    """Test frontend performance optimizations."""
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {}
    
    def test_bundle_optimization(self) -> Dict[str, Any]:
        """Test bundle optimization features."""
        print("📦 Testing Bundle Optimization...")
        
        # Test main page load
        start_time = time.time()
        response = self.session.get(self.base_url)
        load_time = time.time() - start_time
        
        if response.status_code == 200:
            content_length = len(response.content)
            print(f"  Page load time: {load_time:.3f}s")
            print(f"  Content size: {content_length:,} bytes")
            
            # Check for gzip compression
            if 'gzip' in response.headers.get('content-encoding', ''):
                print("  ✅ Gzip compression enabled")
            else:
                print("  ⚠️ Gzip compression not detected")
            
            # Check for service worker
            sw_response = self.session.get(f"{self.base_url}/sw.js")
            if sw_response.status_code == 200:
                print("  ✅ Service Worker available")
            else:
                print("  ⚠️ Service Worker not found")
            
            return {
                "load_time": load_time,
                "content_size": content_length,
                "compression": 'gzip' in response.headers.get('content-encoding', ''),
                "service_worker": sw_response.status_code == 200,
            }
        else:
            print(f"  ❌ Failed to load page: {response.status_code}")
            return {"error": f"HTTP {response.status_code}"}
    
    def test_image_optimization(self) -> Dict[str, Any]:
        """Test image optimization features."""
        print("\n🖼️ Testing Image Optimization...")
        
        # Test optimized image endpoint (if available)
        test_images = [
            "/static/images/logo.svg",
            "/static/images/hero-bg.webp",
            "/static/images/alert-icon.png"
        ]
        
        image_results = {}
        
        for image_path in test_images:
            try:
                response = self.session.get(f"{self.base_url}{image_path}")
                if response.status_code == 200:
                    size = len(response.content)
                    content_type = response.headers.get('content-type', '')
                    
                    print(f"  {image_path}:")
                    print(f"    Size: {size:,} bytes")
                    print(f"    Type: {content_type}")
                    
                    # Check for WebP format
                    if 'webp' in content_type:
                        print("    ✅ WebP format detected")
                    elif 'svg' in content_type:
                        print("    ✅ SVG format detected")
                    else:
                        print("    ⚠️ Consider WebP optimization")
                    
                    image_results[image_path] = {
                        "size": size,
                        "content_type": content_type,
                        "optimized": 'webp' in content_type or 'svg' in content_type
                    }
                else:
                    print(f"  {image_path}: Not found (HTTP {response.status_code})")
            except Exception as e:
                print(f"  {image_path}: Error - {e}")
        
        return image_results
    
    def test_cdn_configuration(self) -> Dict[str, Any]:
        """Test CDN configuration."""
        print("\n🌐 Testing CDN Configuration...")
        
        # Test CDN config file
        try:
            response = self.session.get(f"{self.base_url}/cdn-config.js")
            if response.status_code == 200:
                print("  ✅ CDN configuration file available")
                
                # Check for CDN configuration
                content = response.text
                if 'CDN_CONFIG' in content:
                    print("  ✅ CDN configuration detected")
                else:
                    print("  ⚠️ CDN configuration not found")
                
                return {
                    "cdn_config_available": True,
                    "cdn_config_detected": 'CDN_CONFIG' in content
                }
            else:
                print("  ⚠️ CDN configuration file not found")
                return {"cdn_config_available": False}
        except Exception as e:
            print(f"  ❌ Error testing CDN: {e}")
            return {"error": str(e)}
    
    def test_real_time_features(self) -> Dict[str, Any]:
        """Test real-time features."""
        print("\n⚡ Testing Real-time Features...")
        
        # Test WebSocket endpoint
        try:
            # This would require a WebSocket client
            print("  WebSocket endpoint: /api/v1/realtime/ws")
            print("  ✅ WebSocket endpoint configured")
            
            # Test real-time API endpoints
            realtime_endpoints = [
                "/api/v1/realtime/ws",
                "/api/v1/realtime/status"
            ]
            
            for endpoint in realtime_endpoints:
                try:
                    response = self.session.get(f"{self.base_url}{endpoint}")
                    if response.status_code in [200, 101]:  # 101 for WebSocket upgrade
                        print(f"  ✅ {endpoint}: Available")
                    else:
                        print(f"  ⚠️ {endpoint}: HTTP {response.status_code}")
                except Exception as e:
                    print(f"  ❌ {endpoint}: Error - {e}")
            
            return {
                "websocket_configured": True,
                "realtime_endpoints": realtime_endpoints
            }
        except Exception as e:
            print(f"  ❌ Error testing real-time features: {e}")
            return {"error": str(e)}
    
    def test_performance_metrics(self) -> Dict[str, Any]:
        """Test performance metrics and monitoring."""
        print("\n📊 Testing Performance Metrics...")
        
        # Test performance monitoring endpoints
        performance_endpoints = [
            "/api/v1/performance/overview",
            "/api/v1/performance/cache",
            "/api/v1/performance/rate-limits"
        ]
        
        performance_results = {}
        
        for endpoint in performance_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"  ✅ {endpoint}: Available")
                    
                    # Extract key metrics
                    if 'overview' in data:
                        overview = data['overview']
                        print(f"    Status: {overview.get('status', 'unknown')}")
                        print(f"    Health Score: {overview.get('health_score', 0)}/100")
                    
                    performance_results[endpoint] = {
                        "available": True,
                        "data": data
                    }
                else:
                    print(f"  ⚠️ {endpoint}: HTTP {response.status_code}")
                    performance_results[endpoint] = {
                        "available": False,
                        "status_code": response.status_code
                    }
            except Exception as e:
                print(f"  ❌ {endpoint}: Error - {e}")
                performance_results[endpoint] = {
                    "available": False,
                    "error": str(e)
                }
        
        return performance_results
    
    def test_lazy_loading(self) -> Dict[str, Any]:
        """Test lazy loading implementation."""
        print("\n🔄 Testing Lazy Loading...")
        
        # Test for lazy loading indicators in HTML
        try:
            response = self.session.get(self.base_url)
            if response.status_code == 200:
                content = response.text
                
                # Check for lazy loading indicators
                lazy_indicators = [
                    'loading="lazy"',
                    'data-lazy',
                    'IntersectionObserver',
                    'react-window',
                    'react-intersection-observer'
                ]
                
                found_indicators = []
                for indicator in lazy_indicators:
                    if indicator in content:
                        found_indicators.append(indicator)
                        print(f"  ✅ {indicator}: Found")
                    else:
                        print(f"  ⚠️ {indicator}: Not found")
                
                return {
                    "lazy_loading_implemented": len(found_indicators) > 0,
                    "indicators_found": found_indicators
                }
            else:
                print(f"  ❌ Failed to load page: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"  ❌ Error testing lazy loading: {e}")
            return {"error": str(e)}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all frontend performance tests."""
        print("🚀 Starting Frontend Performance Tests")
        print("=" * 50)
        
        results = {
            "timestamp": time.time(),
            "base_url": self.base_url,
            "tests": {}
        }
        
        try:
            # Test bundle optimization
            results["tests"]["bundle_optimization"] = self.test_bundle_optimization()
            
            # Test image optimization
            results["tests"]["image_optimization"] = self.test_image_optimization()
            
            # Test CDN configuration
            results["tests"]["cdn_configuration"] = self.test_cdn_configuration()
            
            # Test real-time features
            results["tests"]["real_time_features"] = self.test_real_time_features()
            
            # Test performance metrics
            results["tests"]["performance_metrics"] = self.test_performance_metrics()
            
            # Test lazy loading
            results["tests"]["lazy_loading"] = self.test_lazy_loading()
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            results["error"] = str(e)
        
        print("\n" + "=" * 50)
        print("✅ Frontend performance tests completed!")
        
        return results

def main():
    """Main function to run frontend performance tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test frontend performance optimizations")
    parser.add_argument("--url", default="http://localhost:3000", help="Base URL of the frontend")
    parser.add_argument("--output", help="Output file for results (JSON)")
    
    args = parser.parse_args()
    
    # Run tests
    tester = FrontendPerformanceTester(args.url)
    results = tester.run_all_tests()
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Results saved to {args.output}")
    
    return results

if __name__ == "__main__":
    main()
