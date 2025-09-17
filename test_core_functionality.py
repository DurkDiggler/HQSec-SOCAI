#!/usr/bin/env python3
"""
Test script to validate core functionality of the AI/MCP integration.
This tests the components that don't require external dependencies.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variables for testing
os.environ["DATABASE_URL"] = "sqlite:///./test_soc_agent.db"
os.environ["POSTGRES_HOST"] = ""  # Disable PostgreSQL
os.environ["ENABLE_AI_ANALYSIS"] = "false"  # Disable AI for this test
os.environ["ENABLE_OFFENSIVE_TESTING"] = "false"  # Disable MCP for this test

def test_database_models():
    """Test database model creation and basic operations."""
    print("🧪 Testing database models...")
    
    try:
        from soc_agent.database import (
            AIAnalysis, OffensiveTest, ThreatCorrelation,
            create_tables, get_db, save_ai_analysis,
            save_offensive_test, save_threat_correlation
        )
        
        # Create tables
        create_tables()
        print("✅ Database tables created successfully")
        
        # Test model instantiation
        ai_analysis = AIAnalysis(
            alert_id=1,
            threat_classification="Test Threat",
            risk_level="HIGH",
            confidence_score=85.5
        )
        print("✅ AIAnalysis model instantiated successfully")
        
        offensive_test = OffensiveTest(
            target="192.168.1.1",
            test_type="port_scan",
            status="pending"
        )
        print("✅ OffensiveTest model instantiated successfully")
        
        threat_correlation = ThreatCorrelation(
            correlation_id="test-001",
            correlation_name="Test Campaign",
            correlation_type="campaign",
            alert_ids=[1, 2, 3]
        )
        print("✅ ThreatCorrelation model instantiated successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Database models test failed: {e}")
        return False

def test_api_structure():
    """Test API structure and endpoints."""
    print("\n🧪 Testing API structure...")
    
    try:
        # Test by reading the API file instead of importing
        api_file = Path("src/soc_agent/api.py").read_text()
        
        expected_endpoints = [
            "/ai/analyze/{alert_id}",
            "/ai/risk-assessment", 
            "/ai/correlate-threats",
            "/mcp/scan",
            "/mcp/test-exploit",
            "/mcp/offensive-test",
            "/mcp/status",
            "/mcp/capabilities",
            "/ai/analyses",
            "/mcp/tests",
            "/ai/correlations"
        ]
        
        missing_endpoints = []
        for endpoint in expected_endpoints:
            if endpoint not in api_file:
                missing_endpoints.append(endpoint)
        
        if missing_endpoints:
            print(f"❌ Missing API endpoints: {missing_endpoints}")
            return False
        
        print("✅ All expected API endpoints are present in the code")
        
        # Check for key functions
        expected_functions = [
            "ai_analyze_alert_endpoint",
            "mcp_scan_endpoint", 
            "mcp_status_endpoint",
            "get_ai_analyses_endpoint",
            "get_offensive_tests_endpoint"
        ]
        
        missing_functions = []
        for func in expected_functions:
            if func not in api_file:
                missing_functions.append(func)
        
        if missing_functions:
            print(f"❌ Missing API functions: {missing_functions}")
            return False
        
        print("✅ All expected API functions are present")
        
        return True
        
    except Exception as e:
        print(f"❌ API structure test failed: {e}")
        return False

def test_configuration():
    """Test configuration loading."""
    print("\n🧪 Testing configuration...")
    
    try:
        from soc_agent.config import SETTINGS
        
        # Check if new config fields exist
        config_fields = [
            'openai_api_key', 'openai_model', 'openai_max_tokens',
            'openai_temperature', 'enable_ai_analysis',
            'kali_mcp_url', 'vuln_scanner_url', 'mcp_timeout',
            'enable_offensive_testing'
        ]
        
        missing_fields = []
        for field in config_fields:
            if not hasattr(SETTINGS, field):
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing configuration fields: {missing_fields}")
            return False
        
        print("✅ All configuration fields are present")
        print(f"✅ AI Analysis enabled: {SETTINGS.enable_ai_analysis}")
        print(f"✅ Offensive Testing enabled: {SETTINGS.enable_offensive_testing}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_frontend_components():
    """Test frontend component files exist and are valid."""
    print("\n🧪 Testing frontend components...")
    
    try:
        frontend_files = [
            "frontend/src/components/AIInsights.js",
            "frontend/src/components/MCPTools.js", 
            "frontend/src/components/AIDashboard.js",
            "frontend/src/services/api.js"
        ]
        
        missing_files = []
        for file_path in frontend_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            print(f"❌ Missing frontend files: {missing_files}")
            return False
        
        print("✅ All frontend component files exist")
        
        # Check if API service has new endpoints
        api_service = Path("frontend/src/services/api.js").read_text()
        expected_api_calls = [
            "aiAPI", "mcpAPI", "analyzeAlert", "scanTarget", 
            "runOffensiveTest", "getStatus", "getCapabilities"
        ]
        
        missing_api_calls = []
        for api_call in expected_api_calls:
            if api_call not in api_service:
                missing_api_calls.append(api_call)
        
        if missing_api_calls:
            print(f"❌ Missing API calls in frontend: {missing_api_calls}")
            return False
        
        print("✅ Frontend API service has all expected calls")
        
        return True
        
    except Exception as e:
        print(f"❌ Frontend components test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 SOC Agent AI/MCP Integration Test Suite")
    print("=" * 50)
    
    tests = [
        test_database_models,
        test_api_structure,
        test_configuration,
        test_frontend_components
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All core functionality tests passed!")
        print("\n✅ Ready for full stack testing with Docker!")
        print("\nNext steps:")
        print("1. Fix the .env file (remove \\n characters)")
        print("2. Run: docker-compose up --build")
        print("3. Test the web interface at http://localhost:3000")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
