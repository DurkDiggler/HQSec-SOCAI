@echo off
REM SOC Agent Windows Setup Script (Batch Version)
REM This script sets up the SOC Agent for presentation on Windows

setlocal enabledelayedexpansion

echo.
echo ===============================================
echo    SOC Agent Windows Setup Script
echo ===============================================
echo.

REM Check if we're in the right directory
if not exist "src\soc_agent\__init__.py" (
    echo ERROR: Please run this script from the SOC Agent project root directory
    echo The script should be run from the directory containing src\soc_agent\
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

REM Install dependencies
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

echo Dependencies installed successfully!

REM Check if port 8000 is in use
echo.
echo Checking if port 8000 is available...
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

REM Start the service
echo.
echo Starting SOC Agent...
echo Service will be available at http://localhost:8000
echo Press Ctrl+C to stop the service
echo.

REM Start the service in the foreground
python -m uvicorn soc_agent.webapp:app --host 0.0.0.0 --port 8000

REM If we get here, the service was stopped
echo.
echo SOC Agent stopped.
pause
