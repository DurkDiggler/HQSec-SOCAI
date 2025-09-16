# SOC Agent Full Stack Windows Setup Script
# This script sets up the complete SOC Agent with React frontend for presentation

param(
    [switch]$SkipDocker,
    [switch]$UseDocker,
    [string]$PythonPath = "",
    [switch]$SkipFrontend,
    [switch]$Help
)

if ($Help) {
    Write-Host "SOC Agent Full Stack Windows Setup Script" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage: .\setup-windows-full.ps1 [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -SkipDocker     Skip Docker installation check"
    Write-Host "  -UseDocker      Force Docker Compose setup"
    Write-Host "  -PythonPath     Specify custom Python path"
    Write-Host "  -SkipFrontend   Skip frontend setup (backend only)"
    Write-Host "  -Help           Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\setup-windows-full.ps1                    # Auto-detect best method"
    Write-Host "  .\setup-windows-full.ps1 -UseDocker         # Use Docker Compose"
    Write-Host "  .\setup-windows-full.ps1 -SkipDocker        # Use Python + Node.js"
    Write-Host "  .\setup-windows-full.ps1 -SkipFrontend      # Backend only"
    exit 0
}

# Set error action preference
$ErrorActionPreference = "Stop"

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

function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Test-Port {
    param([int]$Port)
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("localhost", $Port)
        $connection.Close()
        return $true
    }
    catch {
        return $false
    }
}

function Install-NodeDependencies {
    param([string]$NodeExe)
    
    Write-ColorOutput "📦 Installing Node.js dependencies for frontend..." $Colors.Info
    
    # Navigate to frontend directory
    Push-Location "frontend"
    
    try {
        # Install dependencies
        & $NodeExe -m npm install
        
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install npm dependencies"
        }
        
        Write-ColorOutput "✅ Node.js dependencies installed successfully" $Colors.Success
    }
    catch {
        Write-ColorOutput "❌ Failed to install Node.js dependencies: $($_.Exception.Message)" $Colors.Error
        throw
    }
    finally {
        Pop-Location
    }
}

function Start-Frontend {
    param([string]$NodeExe)
    
    Write-ColorOutput "🌐 Starting React frontend..." $Colors.Info
    
    # Check if port 3000 is already in use
    if (Test-Port 3000) {
        Write-ColorOutput "⚠️  Port 3000 is already in use. Please stop the service using that port first." $Colors.Warning
        Write-ColorOutput "   You can check what's using the port with: netstat -ano | findstr :3000" $Colors.Info
        return $false
    }
    
    # Start the frontend in background
    $job = Start-Job -ScriptBlock {
        param($NodePath)
        Set-Location $using:PWD
        Push-Location "frontend"
        & $NodePath -m npm start
    } -ArgumentList $NodeExe
    
    # Wait a moment for the frontend to start
    Start-Sleep -Seconds 5
    
    # Check if frontend is running
    $maxAttempts = 15
    $attempt = 0
    do {
        Start-Sleep -Seconds 2
        $attempt++
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-ColorOutput "✅ React frontend started successfully!" $Colors.Success
                Write-ColorOutput "   Frontend is running on http://localhost:3000" $Colors.Info
                return $true
            }
        }
        catch {
            # Frontend not ready yet
        }
    } while ($attempt -lt $maxAttempts)
    
    Write-ColorOutput "❌ Failed to start React frontend. Check the logs for errors." $Colors.Error
    Stop-Job $job -ErrorAction SilentlyContinue
    Remove-Job $job -ErrorAction SilentlyContinue
    return $false
}

function Install-PythonDependencies {
    param([string]$PythonExe)
    
    Write-ColorOutput "📦 Installing Python dependencies..." $Colors.Info
    
    # Install the package in development mode
    & $PythonExe -m pip install --upgrade pip
    & $PythonExe -m pip install -e .
    & $PythonExe -m pip install -e .[dev]
    
    # Install additional required packages
    & $PythonExe -m pip install sqlalchemy alembic cryptography python-multipart
    
    Write-ColorOutput "✅ Python dependencies installed successfully" $Colors.Success
}

function Start-SOCAgent {
    param([string]$PythonExe)
    
    Write-ColorOutput "🚀 Starting SOC Agent backend..." $Colors.Info
    
    # Check if port 8000 is already in use
    if (Test-Port 8000) {
        Write-ColorOutput "⚠️  Port 8000 is already in use. Please stop the service using that port first." $Colors.Warning
        Write-ColorOutput "   You can check what's using the port with: netstat -ano | findstr :8000" $Colors.Info
        return $false
    }
    
    # Start the service in background
    $job = Start-Job -ScriptBlock {
        param($PythonPath)
        Set-Location $using:PWD
        & $PythonPath -m uvicorn soc_agent.webapp:app --host 0.0.0.0 --port 8000
    } -ArgumentList $PythonExe
    
    # Wait a moment for the service to start
    Start-Sleep -Seconds 3
    
    # Check if service is running
    $maxAttempts = 10
    $attempt = 0
    do {
        Start-Sleep -Seconds 2
        $attempt++
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/healthz" -TimeoutSec 5 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-ColorOutput "✅ SOC Agent backend started successfully!" $Colors.Success
                Write-ColorOutput "   Backend is running on http://localhost:8000" $Colors.Info
                return $true
            }
        }
        catch {
            # Service not ready yet
        }
    } while ($attempt -lt $maxAttempts)
    
    Write-ColorOutput "❌ Failed to start SOC Agent backend. Check the logs for errors." $Colors.Error
    Stop-Job $job -ErrorAction SilentlyContinue
    Remove-Job $job -ErrorAction SilentlyContinue
    return $false
}

function Start-DockerComposeFull {
    Write-ColorOutput "🐳 Starting SOC Agent Full Stack with Docker Compose..." $Colors.Info
    
    # Check if ports are already in use
    if (Test-Port 8000) {
        Write-ColorOutput "⚠️  Port 8000 is already in use. Please stop the service using that port first." $Colors.Warning
        return $false
    }
    
    if (Test-Port 3000) {
        Write-ColorOutput "⚠️  Port 3000 is already in use. Please stop the service using that port first." $Colors.Warning
        return $false
    }
    
    try {
        # Start Docker Compose with full stack
        docker-compose -f docker-compose.full.yml up --build -d
        
        # Wait for services to start
        Start-Sleep -Seconds 15
        
        # Check if services are running
        $maxAttempts = 20
        $attempt = 0
        $backendReady = $false
        $frontendReady = $false
        
        do {
            Start-Sleep -Seconds 2
            $attempt++
            
            # Check backend
            if (-not $backendReady) {
                try {
                    $response = Invoke-WebRequest -Uri "http://localhost:8000/healthz" -TimeoutSec 5 -ErrorAction Stop
                    if ($response.StatusCode -eq 200) {
                        $backendReady = $true
                        Write-ColorOutput "✅ SOC Agent backend is running" $Colors.Success
                    }
                }
                catch {
                    # Backend not ready yet
                }
            }
            
            # Check frontend
            if (-not $frontendReady) {
                try {
                    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -ErrorAction Stop
                    if ($response.StatusCode -eq 200) {
                        $frontendReady = $true
                        Write-ColorOutput "✅ React frontend is running" $Colors.Success
                    }
                }
                catch {
                    # Frontend not ready yet
                }
            }
            
        } while ($attempt -lt $maxAttempts -and (-not $backendReady -or -not $frontendReady))
        
        if ($backendReady -and $frontendReady) {
            Write-ColorOutput "✅ SOC Agent Full Stack started successfully with Docker!" $Colors.Success
            Write-ColorOutput "   Frontend: http://localhost:3000" $Colors.Info
            Write-ColorOutput "   Backend API: http://localhost:8000" $Colors.Info
            Write-ColorOutput "   API Documentation: http://localhost:8000/docs" $Colors.Info
            Write-ColorOutput "   MailDev UI: http://localhost:1080" $Colors.Info
            return $true
        } else {
            Write-ColorOutput "❌ Failed to start SOC Agent Full Stack with Docker. Check the logs with: docker-compose -f docker-compose.full.yml logs" $Colors.Error
            return $false
        }
    }
    catch {
        Write-ColorOutput "❌ Error starting Docker Compose: $($_.Exception.Message)" $Colors.Error
        return $false
    }
}

function Show-PresentationInfo {
    Write-ColorOutput "`n🎤 SOC Agent Full Stack Presentation Ready!" $Colors.Header
    Write-ColorOutput "===========================================" $Colors.Header
    Write-ColorOutput ""
    Write-ColorOutput "📋 Quick Demo Commands:" $Colors.Info
    Write-ColorOutput ""
    Write-ColorOutput "1. Health Check:" $Colors.Info
    Write-ColorOutput "   curl http://localhost:8000/healthz" $Colors.White
    Write-ColorOutput ""
    Write-ColorOutput "2. Test Wazuh Webhook:" $Colors.Info
    Write-ColorOutput '   curl -X POST http://localhost:8000/webhook -H "Content-Type: application/json" -d "{\"source\": \"wazuh\", \"rule\": {\"id\": 5710, \"level\": 7, \"description\": \"sshd: authentication failed\"}, \"agent\": {\"name\": \"srv01\"}, \"data\": {\"srcip\": \"192.168.1.100\", \"srcuser\": \"admin\"}, \"full_log\": \"Failed password from 192.168.1.100 port 22 ssh2\"}""' $Colors.White
    Write-ColorOutput ""
    Write-ColorOutput "3. Test CrowdStrike Webhook:" $Colors.Info
    Write-ColorOutput '   curl -X POST http://localhost:8000/webhook -H "Content-Type: application/json" -d "{\"source\": \"crowdstrike\", \"eventType\": \"AuthActivityAuthFail\", \"Severity\": 8, \"LocalIP\": \"10.0.0.50\", \"UserName\": \"administrator\", \"Name\": \"Multiple failed login attempts\"}""' $Colors.White
    Write-ColorOutput ""
    Write-ColorOutput "4. View Web Interface:" $Colors.Info
    Write-ColorOutput "   Start-Process http://localhost:3000" $Colors.White
    Write-ColorOutput ""
    Write-ColorOutput "5. View API Documentation:" $Colors.Info
    Write-ColorOutput "   Start-Process http://localhost:8000/docs" $Colors.White
    Write-ColorOutput ""
    Write-ColorOutput "6. View MailDev (if using Docker):" $Colors.Info
    Write-ColorOutput "   Start-Process http://localhost:1080" $Colors.White
    Write-ColorOutput ""
    Write-ColorOutput "📖 For detailed presentation flow, see PRESENTATION_FLOW.md" $Colors.Info
    Write-ColorOutput "🛑 To stop the services: docker-compose -f docker-compose.full.yml down (Docker) or Ctrl+C (Python/Node)" $Colors.Warning
}

# Main script execution
Write-ColorOutput "🚀 SOC Agent Full Stack Windows Setup Script" $Colors.Header
Write-ColorOutput "=============================================" $Colors.Header
Write-ColorOutput ""

# Check if we're in the right directory
if (-not (Test-Path "src\soc_agent\__init__.py")) {
    Write-ColorOutput "❌ Error: Please run this script from the SOC Agent project root directory" $Colors.Error
    Write-ColorOutput "   The script should be run from the directory containing src\soc_agent\" $Colors.Info
    exit 1
}

# Check if frontend directory exists
if (-not $SkipFrontend -and -not (Test-Path "frontend\package.json")) {
    Write-ColorOutput "❌ Error: Frontend directory not found. Please ensure you're in the correct project directory." $Colors.Error
    Write-ColorOutput "   The script should be run from the directory containing frontend\package.json" $Colors.Info
    exit 1
}

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-ColorOutput "📝 Creating .env file from template..." $Colors.Info
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-ColorOutput "✅ .env file created from .env.example" $Colors.Success
        Write-ColorOutput "⚠️  Please edit .env file with your configuration before running the service" $Colors.Warning
    } elseif (Test-Path "env.example") {
        Copy-Item "env.example" ".env"
        Write-ColorOutput "✅ .env file created from env.example" $Colors.Success
        Write-ColorOutput "⚠️  Please edit .env file with your configuration before running the service" $Colors.Warning
    } else {
        Write-ColorOutput "⚠️  No .env template found. You may need to create .env manually" $Colors.Warning
    }
} else {
    Write-ColorOutput "✅ .env file already exists" $Colors.Success
}

# Determine setup method
$useDocker = $false
$usePython = $false

if ($UseDocker) {
    $useDocker = $true
} elseif ($SkipDocker) {
    $usePython = $true
} else {
    # Auto-detect best method
    if (Test-Command "docker") {
        if (Test-Command "docker-compose") {
            Write-ColorOutput "🐳 Docker and Docker Compose detected" $Colors.Success
            $useDocker = $true
        } else {
            Write-ColorOutput "⚠️  Docker detected but Docker Compose not found" $Colors.Warning
            $usePython = $true
        }
    } else {
        Write-ColorOutput "🐍 Docker not found, using Python + Node.js setup" $Colors.Info
        $usePython = $true
    }
}

# Docker setup
if ($useDocker) {
    # Start with Docker Compose Full Stack
    if (Start-DockerComposeFull) {
        Show-PresentationInfo
    } else {
        Write-ColorOutput "❌ Docker setup failed. Falling back to Python + Node.js setup..." $Colors.Warning
        
        # Fallback to Python + Node.js
        $pythonExe = ""
        $nodeExe = ""
        
        # Find Python
        $pythonCandidates = @("python", "python3", "py")
        foreach ($candidate in $pythonCandidates) {
            if (Test-Command $candidate) {
                try {
                    $version = & $candidate --version 2>&1
                    if ($version -match "Python (\d+)\.(\d+)") {
                        $major = [int]$matches[1]
                        $minor = [int]$matches[2]
                        if ($major -eq 3 -and $minor -ge 10) {
                            $pythonExe = $candidate
                            break
                        }
                    }
                }
                catch {
                    # Continue to next candidate
                }
            }
        }
        
        # Find Node.js
        $nodeCandidates = @("node", "nodejs")
        foreach ($candidate in $nodeCandidates) {
            if (Test-Command $candidate) {
                try {
                    $version = & $candidate --version 2>&1
                    if ($version -match "v(\d+)\.(\d+)") {
                        $major = [int]$matches[1]
                        if ($major -ge 16) {
                            $nodeExe = $candidate
                            break
                        }
                    }
                }
                catch {
                    # Continue to next candidate
                }
            }
        }
        
        if ($pythonExe -ne "" -and $nodeExe -ne "") {
            Install-PythonDependencies -PythonExe $pythonExe
            if (-not $SkipFrontend) {
                Install-NodeDependencies -NodeExe $nodeExe
            }
            
            if (Start-SOCAgent -PythonExe $pythonExe) {
                if (-not $SkipFrontend) {
                    Start-Frontend -NodeExe $nodeExe
                }
                Show-PresentationInfo
            } else {
                Write-ColorOutput "❌ Both Docker and Python setup failed." $Colors.Error
                exit 1
            }
        } else {
            Write-ColorOutput "❌ Both Docker and Python/Node.js setup failed." $Colors.Error
            exit 1
        }
    }
}

# Python + Node.js setup
if ($usePython) {
    # Find Python executable
    $pythonExe = ""
    if ($PythonPath -ne "") {
        if (Test-Path $PythonPath) {
            $pythonExe = $PythonPath
        } else {
            Write-ColorOutput "❌ Specified Python path not found: $PythonPath" $Colors.Error
            exit 1
        }
    } else {
        # Try to find Python 3.10+
        $pythonCandidates = @(
            "python",
            "python3",
            "py",
            "C:\Python310\python.exe",
            "C:\Python311\python.exe",
            "C:\Python312\python.exe"
        )
        
        foreach ($candidate in $pythonCandidates) {
            if (Test-Command $candidate) {
                try {
                    $version = & $candidate --version 2>&1
                    if ($version -match "Python (\d+)\.(\d+)") {
                        $major = [int]$matches[1]
                        $minor = [int]$matches[2]
                        if ($major -eq 3 -and $minor -ge 10) {
                            $pythonExe = $candidate
                            Write-ColorOutput "✅ Found Python $($matches[0]) at $candidate" $Colors.Success
                            break
                        }
                    }
                }
                catch {
                    # Continue to next candidate
                }
            }
        }
        
        if ($pythonExe -eq "") {
            Write-ColorOutput "❌ Python 3.10+ not found. Please install Python 3.10 or higher" $Colors.Error
            Write-ColorOutput "   Download from: https://www.python.org/downloads/" $Colors.Info
            exit 1
        }
    }
    
    # Find Node.js executable
    $nodeExe = ""
    if (-not $SkipFrontend) {
        $nodeCandidates = @("node", "nodejs")
        foreach ($candidate in $nodeCandidates) {
            if (Test-Command $candidate) {
                try {
                    $version = & $candidate --version 2>&1
                    if ($version -match "v(\d+)\.(\d+)") {
                        $major = [int]$matches[1]
                        if ($major -ge 16) {
                            $nodeExe = $candidate
                            Write-ColorOutput "✅ Found Node.js $version at $candidate" $Colors.Success
                            break
                        }
                    }
                }
                catch {
                    # Continue to next candidate
                }
            }
        }
        
        if ($nodeExe -eq "") {
            Write-ColorOutput "❌ Node.js 16+ not found. Please install Node.js 16 or higher" $Colors.Error
            Write-ColorOutput "   Download from: https://nodejs.org/" $Colors.Info
            Write-ColorOutput "   Or run with -SkipFrontend to skip frontend setup" $Colors.Info
            exit 1
        }
    }
    
    # Install dependencies
    Install-PythonDependencies -PythonExe $pythonExe
    if (-not $SkipFrontend) {
        Install-NodeDependencies -NodeExe $nodeExe
    }
    
    # Start the services
    if (Start-SOCAgent -PythonExe $pythonExe) {
        if (-not $SkipFrontend) {
            Start-Frontend -NodeExe $nodeExe
        }
        Show-PresentationInfo
    } else {
        Write-ColorOutput "❌ Setup failed. Please check the error messages above." $Colors.Error
        exit 1
    }
}

Write-ColorOutput "`n🎉 Full Stack Setup complete! SOC Agent with frontend is ready for presentation." $Colors.Success
