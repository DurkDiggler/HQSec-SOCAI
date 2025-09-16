# SOC Agent Full Stack Test Script
# This script tests the complete full stack setup

param(
    [string]$BackendUrl = "http://localhost:8000",
    [string]$FrontendUrl = "http://localhost:3000",
    [switch]$Help
)

if ($Help) {
    Write-Host "SOC Agent Full Stack Test Script" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage: .\test-full-stack.ps1 [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -BackendUrl     Backend URL (default: http://localhost:8000)"
    Write-Host "  -FrontendUrl    Frontend URL (default: http://localhost:3000)"
    Write-Host "  -Help           Show this help message"
    exit 0
}

# Colors for output
$Colors = @{
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "Cyan"
    Header = "Magenta"
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-Service {
    param([string]$Url, [string]$ServiceName)
    
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec 10 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-ColorOutput "✅ $ServiceName is running at $Url" $Colors.Success
            return $true
        }
    }
    catch {
        Write-ColorOutput "❌ $ServiceName is not running at $Url" $Colors.Error
        Write-ColorOutput "   Error: $($_.Exception.Message)" $Colors.Error
        return $false
    }
    return $false
}

function Test-APIEndpoint {
    param([string]$Url, [string]$Endpoint, [string]$Description)
    
    try {
        $response = Invoke-RestMethod -Uri "$Url$Endpoint" -TimeoutSec 10 -ErrorAction Stop
        Write-ColorOutput "✅ $Description - $Endpoint" $Colors.Success
        return $true
    }
    catch {
        Write-ColorOutput "❌ $Description - $Endpoint" $Colors.Error
        Write-ColorOutput "   Error: $($_.Exception.Message)" $Colors.Error
        return $false
    }
}

function Test-Webhook {
    param([string]$Url)
    
    $testData = @{
        source = "test"
        event_type = "full_stack_test"
        severity = 5
        message = "Full stack integration test"
        ip = "192.168.1.100"
        username = "testuser"
        timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
    } | ConvertTo-Json -Depth 10
    
    try {
        $response = Invoke-RestMethod -Uri "$Url/webhook" -Method Post -Body $testData -ContentType "application/json" -TimeoutSec 10 -ErrorAction Stop
        Write-ColorOutput "✅ Webhook endpoint working" $Colors.Success
        return $true
    }
    catch {
        Write-ColorOutput "❌ Webhook endpoint failed" $Colors.Error
        Write-ColorOutput "   Error: $($_.Exception.Message)" $Colors.Error
        return $false
    }
}

# Main test execution
Write-ColorOutput "🧪 SOC Agent Full Stack Test" $Colors.Header
Write-ColorOutput "============================" $Colors.Header
Write-ColorOutput "Backend URL: $BackendUrl" $Colors.Info
Write-ColorOutput "Frontend URL: $FrontendUrl" $Colors.Info
Write-ColorOutput ""

$allTestsPassed = $true

# Test 1: Backend Health
Write-ColorOutput "`n1. Testing Backend Health..." $Colors.Info
$backendHealthy = Test-Service -Url "$BackendUrl/healthz" -ServiceName "Backend Health Check"
if (-not $backendHealthy) { $allTestsPassed = $false }

# Test 2: Backend Service Info
Write-ColorOutput "`n2. Testing Backend Service Info..." $Colors.Info
$serviceInfo = Test-APIEndpoint -Url $BackendUrl -Endpoint "/" -Description "Service Information"
if (-not $serviceInfo) { $allTestsPassed = $false }

# Test 3: Backend Readiness
Write-ColorOutput "`n3. Testing Backend Readiness..." $Colors.Info
$readiness = Test-APIEndpoint -Url $BackendUrl -Endpoint "/readyz" -Description "Readiness Check"
if (-not $readiness) { $allTestsPassed = $false }

# Test 4: Backend API Endpoints
Write-ColorOutput "`n4. Testing Backend API Endpoints..." $Colors.Info
$alerts = Test-APIEndpoint -Url $BackendUrl -Endpoint "/api/v1/alerts" -Description "Alerts API"
$stats = Test-APIEndpoint -Url $BackendUrl -Endpoint "/api/v1/alerts/stats" -Description "Statistics API"
$dashboard = Test-APIEndpoint -Url $BackendUrl -Endpoint "/api/v1/dashboard" -Description "Dashboard API"
if (-not ($alerts -and $stats -and $dashboard)) { $allTestsPassed = $false }

# Test 5: Webhook Functionality
Write-ColorOutput "`n5. Testing Webhook Functionality..." $Colors.Info
$webhook = Test-Webhook -Url $BackendUrl
if (-not $webhook) { $allTestsPassed = $false }

# Test 6: Frontend Accessibility
Write-ColorOutput "`n6. Testing Frontend Accessibility..." $Colors.Info
$frontendAccessible = Test-Service -Url $FrontendUrl -ServiceName "Frontend"
if (-not $frontendAccessible) { $allTestsPassed = $false }

# Test 7: CORS Configuration
Write-ColorOutput "`n7. Testing CORS Configuration..." $Colors.Info
try {
    $headers = @{
        "Origin" = $FrontendUrl
        "Access-Control-Request-Method" = "GET"
        "Access-Control-Request-Headers" = "Content-Type"
    }
    $corsResponse = Invoke-WebRequest -Uri "$BackendUrl/api/v1/alerts" -Method Options -Headers $headers -TimeoutSec 10 -ErrorAction Stop
    if ($corsResponse.Headers["Access-Control-Allow-Origin"]) {
        Write-ColorOutput "✅ CORS is properly configured" $Colors.Success
    } else {
        Write-ColorOutput "❌ CORS headers missing" $Colors.Error
        $allTestsPassed = $false
    }
}
catch {
    Write-ColorOutput "❌ CORS test failed" $Colors.Error
    Write-ColorOutput "   Error: $($_.Exception.Message)" $Colors.Error
    $allTestsPassed = $false
}

# Test 8: Database Connectivity
Write-ColorOutput "`n8. Testing Database Connectivity..." $Colors.Info
try {
    $dbResponse = Invoke-RestMethod -Uri "$BackendUrl/api/v1/alerts?limit=1" -TimeoutSec 10 -ErrorAction Stop
    Write-ColorOutput "✅ Database connectivity working" $Colors.Success
}
catch {
    Write-ColorOutput "❌ Database connectivity failed" $Colors.Error
    Write-ColorOutput "   Error: $($_.Exception.Message)" $Colors.Error
    $allTestsPassed = $false
}

# Test 9: Metrics Endpoint
Write-ColorOutput "`n9. Testing Metrics Endpoint..." $Colors.Info
$metrics = Test-APIEndpoint -Url $BackendUrl -Endpoint "/metrics" -Description "Metrics"
if (-not $metrics) { $allTestsPassed = $false }

# Test 10: API Documentation
Write-ColorOutput "`n10. Testing API Documentation..." $Colors.Info
$docs = Test-Service -Url "$BackendUrl/docs" -ServiceName "API Documentation"
if (-not $docs) { $allTestsPassed = $false }

# Final Results
Write-ColorOutput "`n📊 Test Results Summary" $Colors.Header
Write-ColorOutput "========================" $Colors.Header

if ($allTestsPassed) {
    Write-ColorOutput "`n🎉 ALL TESTS PASSED! Full stack is working perfectly!" $Colors.Success
    Write-ColorOutput ""
    Write-ColorOutput "✅ Backend API: $BackendUrl" $Colors.Success
    Write-ColorOutput "✅ Frontend UI: $FrontendUrl" $Colors.Success
    Write-ColorOutput "✅ API Documentation: $BackendUrl/docs" $Colors.Success
    Write-ColorOutput "✅ Webhook Endpoint: $BackendUrl/webhook" $Colors.Success
    Write-ColorOutput ""
    Write-ColorOutput "🚀 Ready for presentation!" $Colors.Success
} else {
    Write-ColorOutput "`n❌ SOME TESTS FAILED! Please check the errors above." $Colors.Error
    Write-ColorOutput ""
    Write-ColorOutput "🔧 Troubleshooting:" $Colors.Info
    Write-ColorOutput "1. Ensure all services are running" $Colors.Info
    Write-ColorOutput "2. Check port availability (8000, 3000)" $Colors.Info
    Write-ColorOutput "3. Verify .env configuration" $Colors.Info
    Write-ColorOutput "4. Check Docker containers if using Docker" $Colors.Info
    Write-ColorOutput "5. Review service logs for errors" $Colors.Info
}

Write-ColorOutput "`n📋 Next Steps:" $Colors.Info
Write-ColorOutput "1. Open the frontend: Start-Process $FrontendUrl" $Colors.Info
Write-ColorOutput "2. View API docs: Start-Process $BackendUrl/docs" $Colors.Info
Write-ColorOutput "3. Run demo: .\demo-windows-full.ps1" $Colors.Info
