@echo off
REM SOC Agent Windows Demo Script (Batch Version)
REM This script demonstrates the SOC Agent capabilities for presentation

setlocal enabledelayedexpansion

set BASE_URL=http://localhost:8000

echo.
echo ===============================================
echo    SOC Agent Windows Demo Script
echo ===============================================
echo Base URL: %BASE_URL%
echo.

REM Check if curl is available
curl --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: curl is not available. Please install curl or use PowerShell version
    echo Download curl from: https://curl.se/download.html
    echo Or run: .\demo-windows.ps1
    pause
    exit /b 1
)

REM Check if service is running
echo Checking if SOC Agent is running...
curl -s %BASE_URL%/healthz >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: SOC Agent is not running at %BASE_URL%
    echo Please start the service first with:
    echo   .\setup-windows.ps1
    echo   or
    echo   .\setup-windows.bat
    pause
    exit /b 1
)

echo SOC Agent is running!
echo.

REM Health checks
echo ===============================================
echo Health Checks
echo ===============================================
echo.

echo Service Information:
curl -s %BASE_URL% | python -m json.tool
echo.

echo Health Check:
curl -s %BASE_URL%/healthz | python -m json.tool
echo.

echo Readiness Check:
curl -s %BASE_URL%/readyz | python -m json.tool
echo.

REM Demo scenarios
echo ===============================================
echo Demo Scenarios
echo ===============================================
echo.

echo Press any key to test Wazuh authentication failure...
pause >nul
echo.
echo Testing Wazuh Authentication Failure:
curl -X POST %BASE_URL%/webhook -H "Content-Type: application/json" -d "{\"source\": \"wazuh\", \"rule\": {\"id\": 5710, \"level\": 7, \"description\": \"sshd: authentication failed\"}, \"agent\": {\"name\": \"srv01\"}, \"data\": {\"srcip\": \"192.168.1.100\", \"srcuser\": \"admin\"}, \"full_log\": \"Failed password from 192.168.1.100 port 22 ssh2\"}" | python -m json.tool
echo.

echo Press any key to test CrowdStrike event...
pause >nul
echo.
echo Testing CrowdStrike Event:
curl -X POST %BASE_URL%/webhook -H "Content-Type: application/json" -d "{\"source\": \"crowdstrike\", \"eventType\": \"AuthActivityAuthFail\", \"Severity\": 8, \"LocalIP\": \"10.0.0.50\", \"UserName\": \"administrator\", \"Name\": \"Multiple failed login attempts\"}" | python -m json.tool
echo.

echo Press any key to test custom security event...
pause >nul
echo.
echo Testing Custom Security Event:
curl -X POST %BASE_URL%/webhook -H "Content-Type: application/json" -d "{\"source\": \"custom\", \"event_type\": \"suspicious_activity\", \"severity\": 7, \"timestamp\": \"2025-01-15T17:59:00Z\", \"message\": \"Suspicious activity detected\", \"ip\": \"203.0.113.50\", \"username\": \"admin\"}" | python -m json.tool
echo.

echo Press any key to test high-severity malware detection...
pause >nul
echo.
echo Testing High-Severity Malware Detection:
curl -X POST %BASE_URL%/webhook -H "Content-Type: application/json" -d "{\"source\": \"wazuh\", \"rule\": {\"id\": 1002, \"level\": 12, \"description\": \"Malware detected\"}, \"agent\": {\"name\": \"workstation01\"}, \"data\": {\"srcip\": \"1.2.3.4\", \"srcuser\": \"user1\"}, \"full_log\": \"Malware detected: trojan.exe from 1.2.3.4\"}" | python -m json.tool
echo.

echo Press any key to test critical security event...
pause >nul
echo.
echo Testing Critical Security Event:
curl -X POST %BASE_URL%/webhook -H "Content-Type: application/json" -d "{\"source\": \"wazuh\", \"rule\": {\"id\": 1001, \"level\": 15, \"description\": \"Critical security event\"}, \"agent\": {\"name\": \"server01\"}, \"data\": {\"srcip\": \"10.0.0.100\", \"srcuser\": \"root\"}, \"full_log\": \"Critical: Unauthorized access attempt to root account\"}" | python -m json.tool
echo.

echo Press any key to test rate limiting...
pause >nul
echo.
echo Testing Rate Limiting (sending 5 requests quickly):
for /l %%i in (1,1,5) do (
    echo Sending request %%i/5...
    curl -X POST %BASE_URL%/webhook -H "Content-Type: application/json" -d "{\"source\": \"test\", \"event_type\": \"rate_limit_test\", \"severity\": 1, \"message\": \"Rate limit test %%i\"}" >nul 2>&1
    timeout /t 1 >nul
)
echo Rate limiting test complete.
echo.

echo Press any key to test XSS protection...
pause >nul
echo.
echo Testing XSS Protection:
curl -X POST %BASE_URL%/webhook -H "Content-Type: application/json" -d "{\"source\": \"test\", \"event_type\": \"xss_test\", \"severity\": 1, \"message\": \"<script>alert('xss')</script>\"}" | python -m json.tool
echo.

echo Press any key to view metrics...
pause >nul
echo.
echo Metrics:
curl -s %BASE_URL%/metrics | python -m json.tool
echo.

REM Final summary
echo ===============================================
echo Demo Complete!
echo ===============================================
echo.
echo What we demonstrated:
echo • Multi-vendor webhook processing (Wazuh, CrowdStrike, Custom)
echo • Intelligent threat scoring and categorization
echo • Security features (rate limiting, XSS protection)
echo • Health monitoring and metrics
echo • Real-time event processing and analysis
echo.
echo Additional URLs to explore:
echo • API Documentation: %BASE_URL%/docs
echo • Health Check: %BASE_URL%/healthz
echo • Readiness Check: %BASE_URL%/readyz
echo • Service Info: %BASE_URL%
echo.
echo For detailed presentation flow, see PRESENTATION_FLOW.md
echo.

pause
