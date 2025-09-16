# SOC Agent Windows Setup Script
# This script sets up the SOC Agent for presentation on Windows

param(
    [switch]$SkipDocker,
    [switch]$UseDocker,
    [string]$PythonPath = "",
    [switch]$Help
)

if ($Help) {
    Write-Host "SOC Agent Windows Setup Script" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage: .\setup-windows.ps1 [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -SkipDocker     Skip Docker installation check"
    Write-Host "  -UseDocker      Force Docker Compose setup"
    Write-Host "  -PythonPath     Specify custom Python path"
    Write-Host "  -Help           Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\setup-windows.ps1                    # Auto-detect best method"
    Write-Host "  .\setup-windows.ps1 -UseDocker         # Use Docker Compose"
    Write-Host "  .\setup-windows.ps1 -SkipDocker        # Use Python only"
    Write-Host "  .\setup-windows.ps1 -PythonPath 'C:\Python310\python.exe'"
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
    
    Write-ColorOutput "🚀 Starting SOC Agent..." $Colors.Info
    
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
                Write-ColorOutput "✅ SOC Agent started successfully!" $Colors.Success
                Write-ColorOutput "   Service is running on http://localhost:8000" $Colors.Info
                Write-ColorOutput "   Health check: http://localhost:8000/healthz" $Colors.Info
                Write-ColorOutput "   API docs: http://localhost:8000/docs" $Colors.Info
                return $true
            }
        }
        catch {
            # Service not ready yet
        }
    } while ($attempt -lt $maxAttempts)
    
    Write-ColorOutput "❌ Failed to start SOC Agent. Check the logs for errors." $Colors.Error
    Stop-Job $job -ErrorAction SilentlyContinue
    Remove-Job $job -ErrorAction SilentlyContinue
    return $false
}

function Start-DockerCompose {
    Write-ColorOutput "🐳 Starting SOC Agent with Docker Compose..." $Colors.Info
    
    # Check if port 8000 is already in use
    if (Test-Port 8000) {
        Write-ColorOutput "⚠️  Port 8000 is already in use. Please stop the service using that port first." $Colors.Warning
        return $false
    }
    
    try {
        # Start Docker Compose
        docker-compose up --build -d
        
        # Wait for services to start
        Start-Sleep -Seconds 10
        
        # Check if service is running
        $maxAttempts = 15
        $attempt = 0
        do {
            Start-Sleep -Seconds 2
            $attempt++
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:8000/healthz" -TimeoutSec 5 -ErrorAction Stop
                if ($response.StatusCode -eq 200) {
                    Write-ColorOutput "✅ SOC Agent started successfully with Docker!" $Colors.Success
                    Write-ColorOutput "   Service is running on http://localhost:8000" $Colors.Info
                    Write-ColorOutput "   Health check: http://localhost:8000/healthz" $Colors.Info
                    Write-ColorOutput "   API docs: http://localhost:8000/docs" $Colors.Info
                    Write-ColorOutput "   MailDev UI: http://localhost:1080" $Colors.Info
                    return $true
                }
            }
            catch {
                # Service not ready yet
            }
        } while ($attempt -lt $maxAttempts)
        
        Write-ColorOutput "❌ Failed to start SOC Agent with Docker. Check the logs with: docker-compose logs" $Colors.Error
        return $false
    }
    catch {
        Write-ColorOutput "❌ Error starting Docker Compose: $($_.Exception.Message)" $Colors.Error
        return $false
    }
}

function Show-PresentationInfo {
    Write-ColorOutput "`n🎤 SOC Agent Presentation Ready!" $Colors.Header
    Write-ColorOutput "=================================" $Colors.Header
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
    Write-ColorOutput "4. View API Documentation:" $Colors.Info
    Write-ColorOutput "   Start-Process http://localhost:8000/docs" $Colors.White
    Write-ColorOutput ""
    Write-ColorOutput "5. View MailDev (if using Docker):" $Colors.Info
    Write-ColorOutput "   Start-Process http://localhost:1080" $Colors.White
    Write-ColorOutput ""
    Write-ColorOutput "📖 For detailed presentation flow, see PRESENTATION_FLOW.md" $Colors.Info
    Write-ColorOutput "🛑 To stop the service: docker-compose down (Docker) or Ctrl+C (Python)" $Colors.Warning
}

# Main script execution
Write-ColorOutput "🚀 SOC Agent Windows Setup Script" $Colors.Header
Write-ColorOutput "===================================" $Colors.Header
Write-ColorOutput ""

# Check if we're in the right directory
if (-not (Test-Path "src\soc_agent\__init__.py")) {
    Write-ColorOutput "❌ Error: Please run this script from the SOC Agent project root directory" $Colors.Error
    Write-ColorOutput "   The script should be run from the directory containing src\soc_agent\" $Colors.Info
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
        Write-ColorOutput "🐍 Docker not found, using Python setup" $Colors.Info
        $usePython = $true
    }
}

# Python setup
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
            Write-ColorOutput "   Or specify path with: .\setup-windows.ps1 -PythonPath 'C:\Python310\python.exe'" $Colors.Info
            exit 1
        }
    }
    
    # Install dependencies
    Install-PythonDependencies -PythonExe $pythonExe
    
    # Start the service
    if (Start-SOCAgent -PythonExe $pythonExe) {
        Show-PresentationInfo
    } else {
        Write-ColorOutput "❌ Setup failed. Please check the error messages above." $Colors.Error
        exit 1
    }
}

# Docker setup
if ($useDocker) {
    # Start with Docker Compose
    if (Start-DockerCompose) {
        Show-PresentationInfo
    } else {
        Write-ColorOutput "❌ Docker setup failed. Falling back to Python setup..." $Colors.Warning
        
        # Fallback to Python
        $pythonExe = ""
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
        
        if ($pythonExe -ne "") {
            Install-PythonDependencies -PythonExe $pythonExe
            if (Start-SOCAgent -PythonExe $pythonExe) {
                Show-PresentationInfo
            } else {
                Write-ColorOutput "❌ Both Docker and Python setup failed." $Colors.Error
                exit 1
            }
        } else {
            Write-ColorOutput "❌ Both Docker and Python setup failed." $Colors.Error
            exit 1
        }
    }
}

Write-ColorOutput "`n🎉 Setup complete! SOC Agent is ready for presentation." $Colors.Success
