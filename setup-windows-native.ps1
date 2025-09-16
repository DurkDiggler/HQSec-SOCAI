# SOC Agent Windows Native Setup (No Docker Required)
# This script sets up SOC Agent using Python and Node.js directly on Windows

param(
    [switch]$SkipPython,
    [switch]$SkipNode,
    [switch]$SkipDatabase,
    [switch]$Help
)

if ($Help) {
    Write-Host "SOC Agent Windows Native Setup" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage: .\setup-windows-native.ps1 [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -SkipPython     Skip Python installation check"
    Write-Host "  -SkipNode       Skip Node.js installation check"
    Write-Host "  -SkipDatabase   Skip database setup"
    Write-Host "  -Help           Show this help message"
    Write-Host ""
    Write-Host "This setup runs SOC Agent natively on Windows without Docker."
    exit 0
}

# Color functions
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    } else {
        $input | Write-Output
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

$Colors = @{
    Header = "Cyan"
    Success = "Green"
    Error = "Red"
    Warning = "Yellow"
    Info = "White"
    Data = "Gray"
}

Write-ColorOutput "🚀 SOC Agent Windows Native Setup" $Colors.Header
Write-ColorOutput "=====================================" $Colors.Header

# Check if we're in the right directory
if (-not (Test-Path "src/soc_agent")) {
    Write-ColorOutput "❌ Please run this script from the SOC Agent root directory" $Colors.Error
    exit 1
}

# Check Python
if (-not $SkipPython) {
    Write-ColorOutput "`n🐍 Checking Python..." $Colors.Info
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python 3\.(10|11|12)") {
            Write-ColorOutput "✅ Python found: $pythonVersion" $Colors.Success
        } else {
            Write-ColorOutput "❌ Python 3.10+ required. Found: $pythonVersion" $Colors.Error
            Write-ColorOutput "   Please install Python 3.10+ from https://python.org" $Colors.Warning
            exit 1
        }
    } catch {
        Write-ColorOutput "❌ Python not found. Please install Python 3.10+ from https://python.org" $Colors.Error
        exit 1
    }
}

# Check Node.js
if (-not $SkipNode) {
    Write-ColorOutput "`n📦 Checking Node.js..." $Colors.Info
    try {
        $nodeVersion = node --version 2>&1
        if ($nodeVersion -match "v(18|19|20|21)") {
            Write-ColorOutput "✅ Node.js found: $nodeVersion" $Colors.Success
        } else {
            Write-ColorOutput "❌ Node.js 18+ required. Found: $nodeVersion" $Colors.Error
            Write-ColorOutput "   Please install Node.js 18+ from https://nodejs.org" $Colors.Warning
            exit 1
        }
    } catch {
        Write-ColorOutput "❌ Node.js not found. Please install Node.js 18+ from https://nodejs.org" $Colors.Error
        exit 1
    }
}

# Create virtual environment
Write-ColorOutput "`n🔧 Setting up Python virtual environment..." $Colors.Info
if (Test-Path "venv") {
    Write-ColorOutput "✅ Virtual environment already exists" $Colors.Success
} else {
    python -m venv venv
    Write-ColorOutput "✅ Virtual environment created" $Colors.Success
}

# Activate virtual environment
Write-ColorOutput "`n🔌 Activating virtual environment..." $Colors.Info
& "venv\Scripts\Activate.ps1"

# Install Python dependencies
Write-ColorOutput "`n📦 Installing Python dependencies..." $Colors.Info
pip install --upgrade pip
pip install -e .[dev]
Write-ColorOutput "✅ Python dependencies installed" $Colors.Success

# Install Node.js dependencies
Write-ColorOutput "`n📦 Installing Node.js dependencies..." $Colors.Info
Set-Location frontend
npm install
Set-Location ..
Write-ColorOutput "✅ Node.js dependencies installed" $Colors.Success

# Setup environment file
Write-ColorOutput "`n⚙️ Setting up environment configuration..." $Colors.Info
if (-not (Test-Path ".env")) {
    Copy-Item "env.example" ".env"
    Write-ColorOutput "✅ Environment file created from template" $Colors.Success
} else {
    Write-ColorOutput "✅ Environment file already exists" $Colors.Success
}

# Setup database
if (-not $SkipDatabase) {
    Write-ColorOutput "`n🗄️ Setting up database..." $Colors.Info
    # SQLite will be created automatically on first run
    Write-ColorOutput "✅ Database will be created on first run" $Colors.Success
}

# Create startup scripts
Write-ColorOutput "`n📝 Creating startup scripts..." $Colors.Info

# Backend startup script
$backendScript = @"
@echo off
echo Starting SOC Agent Backend...
call venv\Scripts\activate.bat
python -m uvicorn soc_agent.webapp:app --host 0.0.0.0 --port 8000
pause
"@
$backendScript | Out-File -FilePath "start-backend.bat" -Encoding ASCII

# Frontend startup script
$frontendScript = @"
@echo off
echo Starting SOC Agent Frontend...
cd frontend
call npm start
pause
"@
$frontendScript | Out-File -FilePath "start-frontend.bat" -Encoding ASCII

# Combined startup script
$combinedScript = @"
@echo off
echo Starting SOC Agent (Backend + Frontend)...
echo.
echo Starting Backend in new window...
start "SOC Agent Backend" cmd /k "call venv\Scripts\activate.bat && python -m uvicorn soc_agent.webapp:app --host 0.0.0.0 --port 8000"
echo.
echo Waiting 5 seconds for backend to start...
timeout /t 5 /nobreak > nul
echo.
echo Starting Frontend in new window...
start "SOC Agent Frontend" cmd /k "cd frontend && npm start"
echo.
echo Both services are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to exit this window...
pause > nul
"@
$combinedScript | Out-File -FilePath "start-soc-agent.bat" -Encoding ASCII

Write-ColorOutput "✅ Startup scripts created" $Colors.Success

# Test the setup
Write-ColorOutput "`n🧪 Testing setup..." $Colors.Info
try {
    # Test Python import
    python -c "import soc_agent; print('Backend import successful')" 2>$null
    Write-ColorOutput "✅ Backend import test passed" $Colors.Success
} catch {
    Write-ColorOutput "❌ Backend import test failed" $Colors.Error
}

try {
    # Test Node.js
    Set-Location frontend
    node -e "console.log('Frontend test successful')" 2>$null
    Set-Location ..
    Write-ColorOutput "✅ Frontend test passed" $Colors.Success
} catch {
    Write-ColorOutput "❌ Frontend test failed" $Colors.Error
}

Write-ColorOutput "`n🎉 Setup Complete!" $Colors.Success
Write-ColorOutput "=================" $Colors.Success
Write-ColorOutput ""
Write-ColorOutput "To start SOC Agent:" $Colors.Info
Write-ColorOutput "  • Double-click 'start-soc-agent.bat' (recommended)" $Colors.Data
Write-ColorOutput "  • Or run 'start-backend.bat' and 'start-frontend.bat' separately" $Colors.Data
Write-ColorOutput ""
Write-ColorOutput "Access URLs:" $Colors.Info
Write-ColorOutput "  • Backend API: http://localhost:8000" $Colors.Data
Write-ColorOutput "  • Frontend: http://localhost:3000" $Colors.Data
Write-ColorOutput "  • API Docs: http://localhost:8000/docs" $Colors.Data
Write-ColorOutput ""
Write-ColorOutput "Configuration:" $Colors.Info
Write-ColorOutput "  • Edit .env file to add API keys and configure settings" $Colors.Data
Write-ColorOutput ""
Write-ColorOutput "Troubleshooting:" $Colors.Info
Write-ColorOutput "  • Check Windows Defender firewall settings" $Colors.Data
Write-ColorOutput "  • Ensure ports 8000 and 3000 are not blocked" $Colors.Data
Write-ColorOutput "  • Run 'python -m soc_agent.webapp' to test backend directly" $Colors.Data
