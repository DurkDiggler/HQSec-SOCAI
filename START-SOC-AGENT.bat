@echo off
REM SOC Agent - Enterprise One-Click Starter
REM This script requires ONLY Docker Desktop to be installed

echo.
echo ========================================
echo    SOC Agent - Enterprise Starter
echo ========================================
echo.

REM Check if Docker is running
docker version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Docker Desktop is not running or not installed
    echo.
    echo Please:
    echo 1. Install Docker Desktop from https://docker.com
    echo 2. Start Docker Desktop
    echo 3. Run this script again
    echo.
    echo Alternative: Use the native setup (setup-windows-native.ps1)
    echo.
    pause
    exit /b 1
)

echo ✅ Docker Desktop is running

REM Check if we're in the right directory
if not exist "docker-compose.yml" (
    echo ❌ Please run this script from the SOC Agent root directory
    echo    Make sure you've extracted all files first
    pause
    exit /b 1
)

echo ✅ SOC Agent files found

echo.
echo 🚀 Starting SOC Agent...
echo    This may take 2-3 minutes on first run
echo.

REM Start the services
docker compose up --build

echo.
echo 🎉 SOC Agent is running!
echo ========================
echo.
echo Access URLs:
echo   • Web Interface: http://localhost:3000
echo   • Backend API: http://localhost:8000
echo   • API Documentation: http://localhost:8000/docs
echo.
echo To stop: Press Ctrl+C
echo To restart: Run this script again
echo.
pause
