@echo off
REM SOC Agent Full Stack Windows Setup Script (Batch Version)
REM This script sets up the complete SOC Agent with React frontend for presentation

setlocal enabledelayedexpansion

echo.
echo ===============================================
echo    SOC Agent Full Stack Windows Setup
echo ===============================================
echo.

REM Check if we're in the right directory
if not exist "src\soc_agent\__init__.py" (
    echo ERROR: Please run this script from the SOC Agent project root directory
    echo The script should be run from the directory containing src\soc_agent\
    pause
    exit /b 1
)

REM Check if frontend directory exists
if not exist "frontend\package.json" (
    echo ERROR: Frontend directory not found. Please ensure you're in the correct project directory.
    echo The script should be run from the directory containing frontend\package.json
    pause
    exit /b 1
)

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file from template...
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo .env file created from .env.example
    ) else if exist "env.example" (
        copy "env.example" ".env" >nul
        echo .env file created from env.example
    ) else (
        echo WARNING: No .env template found. You may need to create .env manually
    )
    echo WARNING: Please edit .env file with your configuration before running the service
) else (
    echo .env file already exists
)

REM Check for Python
echo Checking for Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.10 or higher
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%

REM Check for Node.js
echo Checking for Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found. Please install Node.js 16 or higher
    echo Download from: https://nodejs.org/
    pause
    exit /b 1
)

REM Check Node.js version
for /f %%i in ('node --version 2^>^&1') do set NODE_VERSION=%%i
echo Found Node.js %NODE_VERSION%

REM Install Python dependencies
echo.
echo Installing Python dependencies...
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install -e .[dev]
python -m pip install sqlalchemy alembic cryptography python-multipart

if %errorlevel% neq 0 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

echo Python dependencies installed successfully!

REM Install Node.js dependencies
echo.
echo Installing Node.js dependencies for frontend...
cd frontend
npm install
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Node.js dependencies
    cd ..
    pause
    exit /b 1
)
cd ..

echo Node.js dependencies installed successfully!

REM Check if ports are in use
echo.
echo Checking if ports 8000 and 3000 are available...
netstat -an | findstr ":8000" >nul
if %errorlevel% equ 0 (
    echo WARNING: Port 8000 is already in use
    echo Please stop the service using that port first
    echo You can check what's using the port with: netstat -ano ^| findstr :8000
    echo.
    set /p choice="Do you want to continue anyway? (y/N): "
    if /i not "!choice!"=="y" (
        echo Setup cancelled
        pause
        exit /b 1
    )
)

netstat -an | findstr ":3000" >nul
if %errorlevel% equ 0 (
    echo WARNING: Port 3000 is already in use
    echo Please stop the service using that port first
    echo You can check what's using the port with: netstat -ano ^| findstr :3000
    echo.
    set /p choice="Do you want to continue anyway? (y/N): "
    if /i not "!choice!"=="y" (
        echo Setup cancelled
        pause
        exit /b 1
    )
)

REM Start the services
echo.
echo Starting SOC Agent Full Stack...
echo Backend will be available at http://localhost:8000
echo Frontend will be available at http://localhost:3000
echo Press Ctrl+C to stop the services
echo.

REM Start backend in background
start "SOC Agent Backend" cmd /k "python -m uvicorn soc_agent.webapp:app --host 0.0.0.0 --port 8000"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in background
start "SOC Agent Frontend" cmd /k "cd frontend && npm start"

REM Wait a moment for frontend to start
timeout /t 5 /nobreak >nul

REM Check if services are running
echo Checking if services are running...
timeout /t 5 /nobreak >nul

REM Test backend
curl -s http://localhost:8000/healthz >nul 2>&1
if %errorlevel% equ 0 (
    echo Backend is running at http://localhost:8000
) else (
    echo WARNING: Backend may not be running properly
)

REM Test frontend
curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo Frontend is running at http://localhost:3000
) else (
    echo WARNING: Frontend may not be running properly
)

echo.
echo ===============================================
echo SOC Agent Full Stack is now running!
echo ===============================================
echo.
echo Access URLs:
echo   - Web Interface: http://localhost:3000
echo   - Backend API: http://localhost:8000
echo   - API Documentation: http://localhost:8000/docs
echo   - Health Check: http://localhost:8000/healthz
echo.
echo Demo Commands:
echo   1. Health Check: curl http://localhost:8000/healthz
echo   2. Test Wazuh: curl -X POST http://localhost:8000/webhook -H "Content-Type: application/json" -d "{\"source\": \"wazuh\", \"rule\": {\"id\": 5710, \"level\": 7, \"description\": \"sshd: authentication failed\"}, \"agent\": {\"name\": \"srv01\"}, \"data\": {\"srcip\": \"192.168.1.100\", \"srcuser\": \"admin\"}, \"full_log\": \"Failed password from 192.168.1.100 port 22 ssh2\"}"
echo   3. Test CrowdStrike: curl -X POST http://localhost:8000/webhook -H "Content-Type: application/json" -d "{\"source\": \"crowdstrike\", \"eventType\": \"AuthActivityAuthFail\", \"Severity\": 8, \"LocalIP\": \"10.0.0.50\", \"UserName\": \"administrator\", \"Name\": \"Multiple failed login attempts\"}"
echo.
echo To stop the services, close the command windows or press Ctrl+C
echo.
pause
