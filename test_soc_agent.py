#!/usr/bin/env python3
"""
Comprehensive test script for SOC Agent
Tests core functionality without requiring external dependencies
"""

import json
import sys
import time
from datetime import datetime

def test_imports():
    """Test that all modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        from soc_agent import __version__
        print(f"✅ SOC Agent version: {__version__}")
        
        from soc_agent.webapp import app
        print("✅ Webapp imported")
        
        from soc_agent.config import SETTINGS
        print("✅ Configuration loaded")
        
        from soc_agent.models import EventIn
        print("✅ Models imported")
        
        from soc_agent.analyzer import enrich_and_score, extract_iocs
        print("✅ Analyzer imported")
        
        from soc_agent.database import create_tables, get_db
        print("✅ Database imported")
        
        from soc_agent.intel.client import intel_client
        print("✅ Intel client imported")
        
        from soc_agent.notifiers import send_email
        print("✅ Notifiers imported")
        
        from soc_agent.autotask import create_autotask_ticket
        print("✅ Autotask imported")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_models():
    """Test Pydantic models."""
    print("\n🔍 Testing models...")
    
    try:
        from soc_agent.models import EventIn
        
        # Test valid event
        event_data = {
            "source": "test",
            "event_type": "auth_failed",
            "severity": 5,
            "timestamp": "2024-01-01T00:00:00Z",
            "message": "Test message",
            "ip": "192.168.1.1",
            "username": "testuser"
        }
        
        event = EventIn.model_validate(event_data)
        print("✅ Valid event created")
        
        # Test IP validation
        event_data["ip"] = "invalid-ip"
        try:
            EventIn.model_validate(event_data)
            print("❌ Invalid IP should have been rejected")
            return False
        except ValueError:
            print("✅ Invalid IP correctly rejected")
        
        return True
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

def test_analyzer():
    """Test the analyzer functionality."""
    print("\n🔍 Testing analyzer...")
    
    try:
        from soc_agent.analyzer import extract_iocs, base_score, enrich_and_score
        
        # Test IOC extraction
        event = {
            "message": "Failed login from 192.168.1.100 to admin@example.com",
            "ip": "192.168.1.100",
            "src_ip": "10.0.0.1"
        }
        
        iocs = extract_iocs(event)
        print(f"✅ IOCs extracted: {iocs}")
        
        # Test base scoring
        event["event_type"] = "auth_failed"
        event["severity"] = 5
        score = base_score(event)
        print(f"✅ Base score calculated: {score}")
        
        # Test full analysis (without external APIs)
        result = enrich_and_score(event)
        print(f"✅ Analysis result: {result['category']} - {result['recommended_action']}")
        
        return True
    except Exception as e:
        print(f"❌ Analyzer test failed: {e}")
        return False

def test_database():
    """Test database functionality."""
    print("\n🔍 Testing database...")
    
    try:
        from soc_agent.database import create_tables, get_db, save_alert, get_alerts
        
        # Create tables
        create_tables()
        print("✅ Database tables created")
        
        # Test database session
        db = next(get_db())
        print("✅ Database session created")
        
        # Test alert creation
        event_data = {
            "source": "test",
            "event_type": "test_event",
            "severity": 5,
            "message": "Test alert",
            "ip": "192.168.1.1"
        }
        
        analysis_result = {
            "category": "LOW",
            "recommended_action": "none",
            "scores": {"base": 30, "intel": 0, "final": 18},
            "iocs": {"ips": ["192.168.1.1"], "domains": []},
            "intel": {"ips": [], "domains": []}
        }
        
        alert = save_alert(db, event_data, analysis_result, {})
        print(f"✅ Alert saved with ID: {alert.id}")
        
        # Test alert retrieval
        alerts = get_alerts(db, limit=1)
        print(f"✅ Retrieved {len(alerts)} alerts")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_webhook():
    """Test webhook endpoint."""
    print("\n🔍 Testing webhook endpoint...")
    
    try:
        from fastapi.testclient import TestClient
        from soc_agent.webapp import app
        
        client = TestClient(app)
        
        # Test health endpoints
        response = client.get("/")
        assert response.status_code == 200
        print("✅ Root endpoint working")
        
        response = client.get("/healthz")
        assert response.status_code == 200
        print("✅ Health check working")
        
        response = client.get("/readyz")
        assert response.status_code == 200
        print("✅ Readiness check working")
        
        # Test webhook with valid payload
        payload = {
            "source": "test",
            "event_type": "auth_failed",
            "severity": 5,
            "message": "Test webhook message",
            "ip": "192.168.1.1"
        }
        
        response = client.post("/webhook", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "analysis" in data
        assert "actions" in data
        print("✅ Webhook endpoint working")
        
        return True
    except Exception as e:
        print(f"❌ Webhook test failed: {e}")
        return False

def test_configuration():
    """Test configuration loading."""
    print("\n🔍 Testing configuration...")
    
    try:
        from soc_agent.config import SETTINGS
        
        print(f"✅ App host: {SETTINGS.app_host}")
        print(f"✅ App port: {SETTINGS.app_port}")
        print(f"✅ Log level: {SETTINGS.log_level}")
        print(f"✅ Database URL: {SETTINGS.database_url}")
        print(f"✅ Rate limit: {SETTINGS.rate_limit_requests} requests per {SETTINGS.rate_limit_window}s")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting SOC Agent comprehensive test suite...\n")
    
    tests = [
        test_imports,
        test_configuration,
        test_models,
        test_analyzer,
        test_database,
        test_webhook,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! SOC Agent is ready for use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
