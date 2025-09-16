#!/bin/bash

# SOC Agent Full Stack Test Script (Linux)
# This script tests the complete full stack setup

set -e

BACKEND_URL=${1:-"http://localhost:8000"}
FRONTEND_URL=${2:-"http://localhost:3000"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

function print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

function test_service() {
    local url=$1
    local service_name=$2
    
    if curl -f -s "$url" > /dev/null 2>&1; then
        print_color $GREEN "✅ $service_name is running at $url"
        return 0
    else
        print_color $RED "❌ $service_name is not running at $url"
        return 1
    fi
}

function test_api_endpoint() {
    local url=$1
    local endpoint=$2
    local description=$3
    
    if curl -f -s "$url$endpoint" > /dev/null 2>&1; then
        print_color $GREEN "✅ $description - $endpoint"
        return 0
    else
        print_color $RED "❌ $description - $endpoint"
        return 1
    fi
}

function test_webhook() {
    local url=$1
    
    local test_data='{
        "source": "test",
        "event_type": "full_stack_test",
        "severity": 5,
        "message": "Full stack integration test",
        "ip": "192.168.1.100",
        "username": "testuser",
        "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
    }'
    
    if curl -f -s -X POST "$url/webhook" \
        -H "Content-Type: application/json" \
        -d "$test_data" > /dev/null 2>&1; then
        print_color $GREEN "✅ Webhook endpoint working"
        return 0
    else
        print_color $RED "❌ Webhook endpoint failed"
        return 1
    fi
}

# Main test execution
print_color $PURPLE "🧪 SOC Agent Full Stack Test"
print_color $PURPLE "============================"
print_color $CYAN "Backend URL: $BACKEND_URL"
print_color $CYAN "Frontend URL: $FRONTEND_URL"
echo ""

all_tests_passed=true

# Test 1: Backend Health
print_color $BLUE "1. Testing Backend Health..."
if ! test_service "$BACKEND_URL/healthz" "Backend Health Check"; then
    all_tests_passed=false
fi

# Test 2: Backend Service Info
print_color $BLUE "2. Testing Backend Service Info..."
if ! test_api_endpoint "$BACKEND_URL" "/" "Service Information"; then
    all_tests_passed=false
fi

# Test 3: Backend Readiness
print_color $BLUE "3. Testing Backend Readiness..."
if ! test_api_endpoint "$BACKEND_URL" "/readyz" "Readiness Check"; then
    all_tests_passed=false
fi

# Test 4: Backend API Endpoints
print_color $BLUE "4. Testing Backend API Endpoints..."
if ! test_api_endpoint "$BACKEND_URL" "/api/v1/alerts" "Alerts API"; then
    all_tests_passed=false
fi
if ! test_api_endpoint "$BACKEND_URL" "/api/v1/alerts/stats" "Statistics API"; then
    all_tests_passed=false
fi
if ! test_api_endpoint "$BACKEND_URL" "/api/v1/dashboard" "Dashboard API"; then
    all_tests_passed=false
fi

# Test 5: Webhook Functionality
print_color $BLUE "5. Testing Webhook Functionality..."
if ! test_webhook "$BACKEND_URL"; then
    all_tests_passed=false
fi

# Test 6: Frontend Accessibility
print_color $BLUE "6. Testing Frontend Accessibility..."
if ! test_service "$FRONTEND_URL" "Frontend"; then
    all_tests_passed=false
fi

# Test 7: CORS Configuration
print_color $BLUE "7. Testing CORS Configuration..."
if curl -f -s -X OPTIONS "$BACKEND_URL/api/v1/alerts" \
    -H "Origin: $FRONTEND_URL" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: Content-Type" > /dev/null 2>&1; then
    print_color $GREEN "✅ CORS is properly configured"
else
    print_color $RED "❌ CORS test failed"
    all_tests_passed=false
fi

# Test 8: Database Connectivity
print_color $BLUE "8. Testing Database Connectivity..."
if curl -f -s "$BACKEND_URL/api/v1/alerts?limit=1" > /dev/null 2>&1; then
    print_color $GREEN "✅ Database connectivity working"
else
    print_color $RED "❌ Database connectivity failed"
    all_tests_passed=false
fi

# Test 9: Metrics Endpoint
print_color $BLUE "9. Testing Metrics Endpoint..."
if ! test_api_endpoint "$BACKEND_URL" "/metrics" "Metrics"; then
    all_tests_passed=false
fi

# Test 10: API Documentation
print_color $BLUE "10. Testing API Documentation..."
if ! test_service "$BACKEND_URL/docs" "API Documentation"; then
    all_tests_passed=false
fi

# Final Results
print_color $PURPLE "📊 Test Results Summary"
print_color $PURPLE "========================"

if [ "$all_tests_passed" = true ]; then
    print_color $GREEN "🎉 ALL TESTS PASSED! Full stack is working perfectly!"
    echo ""
    print_color $GREEN "✅ Backend API: $BACKEND_URL"
    print_color $GREEN "✅ Frontend UI: $FRONTEND_URL"
    print_color $GREEN "✅ API Documentation: $BACKEND_URL/docs"
    print_color $GREEN "✅ Webhook Endpoint: $BACKEND_URL/webhook"
    echo ""
    print_color $GREEN "🚀 Ready for presentation!"
else
    print_color $RED "❌ SOME TESTS FAILED! Please check the errors above."
    echo ""
    print_color $CYAN "🔧 Troubleshooting:"
    print_color $CYAN "1. Ensure all services are running"
    print_color $CYAN "2. Check port availability (8000, 3000)"
    print_color $CYAN "3. Verify .env configuration"
    print_color $CYAN "4. Check Docker containers if using Docker"
    print_color $CYAN "5. Review service logs for errors"
fi

echo ""
print_color $CYAN "📋 Next Steps:"
print_color $CYAN "1. Open the frontend: xdg-open $FRONTEND_URL"
print_color $CYAN "2. View API docs: xdg-open $BACKEND_URL/docs"
print_color $CYAN "3. Run demo: ./demo-windows-full.ps1 (or equivalent)"
