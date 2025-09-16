# SOC Agent Windows Demo Script
# This script demonstrates the SOC Agent capabilities for presentation

param(
    [switch]$Help,
    [string]$BaseUrl = "http://localhost:8000"
)

if ($Help) {
    Write-Host "SOC Agent Windows Demo Script" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage: .\demo-windows.ps1 [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -BaseUrl        Base URL for the SOC Agent (default: http://localhost:8000)"
    Write-Host "  -Help           Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\demo-windows.ps1                           # Use default localhost:8000"
    Write-Host "  .\demo-windows.ps1 -BaseUrl http://192.168.1.100:8000"
    exit 0
}

# Colors for output
$Colors = @{
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "Cyan"
    Header = "Magenta"
    Data = "White"
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-Service {
    param([string]$Url)
    
    try {
        $response = Invoke-WebRequest -Uri "$Url/healthz" -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            return $true
        }
    }
    catch {
        return $false
    }
    return $false
}

function Invoke-Webhook {
    param(
        [string]$Url,
        [string]$Data,
        [string]$Description
    )
    
    Write-ColorOutput "`n📡 $Description" $Colors.Info
    Write-ColorOutput "POST $Url/webhook" $Colors.Data
    
    try {
        $response = Invoke-RestMethod -Uri "$Url/webhook" -Method Post -Body $Data -ContentType "application/json" -TimeoutSec 10
        Write-ColorOutput "✅ Response received:" $Colors.Success
        $response | ConvertTo-Json -Depth 10 | Write-ColorOutput -Color $Colors.Data
        return $true
    }
    catch {
        Write-ColorOutput "❌ Error: $($_.Exception.Message)" $Colors.Error
        if ($_.Exception.Response) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            Write-ColorOutput "Response: $responseBody" $Colors.Error
        }
        return $false
    }
}

function Show-HealthChecks {
    param([string]$Url)
    
    Write-ColorOutput "`n🏥 Health Checks" $Colors.Header
    Write-ColorOutput "================" $Colors.Header
    
    # Service info
    try {
        Write-ColorOutput "`n📊 Service Information:" $Colors.Info
        $response = Invoke-RestMethod -Uri $Url -TimeoutSec 5
        $response | ConvertTo-Json -Depth 3 | Write-ColorOutput -Color $Colors.Data
    }
    catch {
        Write-ColorOutput "❌ Failed to get service info: $($_.Exception.Message)" $Colors.Error
    }
    
    # Health check
    try {
        Write-ColorOutput "`n💚 Health Check:" $Colors.Info
        $response = Invoke-RestMethod -Uri "$Url/healthz" -TimeoutSec 5
        $response | ConvertTo-Json -Depth 3 | Write-ColorOutput -Color $Colors.Data
    }
    catch {
        Write-ColorOutput "❌ Health check failed: $($_.Exception.Message)" $Colors.Error
    }
    
    # Readiness check
    try {
        Write-ColorOutput "`n✅ Readiness Check:" $Colors.Info
        $response = Invoke-RestMethod -Uri "$Url/readyz" -TimeoutSec 5
        $response | ConvertTo-Json -Depth 3 | Write-ColorOutput -Color $Colors.Data
    }
    catch {
        Write-ColorOutput "❌ Readiness check failed: $($_.Exception.Message)" $Colors.Error
    }
}

function Show-DemoData {
    Write-ColorOutput "`n📋 Demo Data" $Colors.Header
    Write-ColorOutput "============" $Colors.Header
    
    Write-ColorOutput "`n1. Wazuh Authentication Failure:" $Colors.Info
    $wazuhData = @{
        source = "wazuh"
        rule = @{
            id = 5710
            level = 7
            description = "sshd: authentication failed"
        }
        agent = @{
            name = "srv01"
        }
        data = @{
            srcip = "192.168.1.100"
            srcuser = "admin"
        }
        full_log = "Failed password from 192.168.1.100 port 22 ssh2"
    } | ConvertTo-Json -Depth 10
    Write-ColorOutput $wazuhData $Colors.Data
    
    Write-ColorOutput "`n2. CrowdStrike Event:" $Colors.Info
    $crowdstrikeData = @{
        source = "crowdstrike"
        eventType = "AuthActivityAuthFail"
        Severity = 8
        LocalIP = "10.0.0.50"
        UserName = "administrator"
        Name = "Multiple failed login attempts"
    } | ConvertTo-Json -Depth 10
    Write-ColorOutput $crowdstrikeData $Colors.Data
    
    Write-ColorOutput "`n3. Custom Security Event:" $Colors.Info
    $customData = @{
        source = "custom"
        event_type = "suspicious_activity"
        severity = 7
        timestamp = "2025-01-15T17:59:00Z"
        message = "Suspicious activity detected"
        ip = "203.0.113.50"
        username = "admin"
    } | ConvertTo-Json -Depth 10
    Write-ColorOutput $customData $Colors.Data
    
    Write-ColorOutput "`n4. High-Severity Malware Detection:" $Colors.Info
    $malwareData = @{
        source = "wazuh"
        rule = @{
            id = 1002
            level = 12
            description = "Malware detected"
        }
        agent = @{
            name = "workstation01"
        }
        data = @{
            srcip = "1.2.3.4"
            srcuser = "user1"
        }
        full_log = "Malware detected: trojan.exe from 1.2.3.4"
    } | ConvertTo-Json -Depth 10
    Write-ColorOutput $malwareData $Colors.Data
    
    Write-ColorOutput "`n5. Critical Security Event:" $Colors.Info
    $criticalData = @{
        source = "wazuh"
        rule = @{
            id = 1001
            level = 15
            description = "Critical security event"
        }
        agent = @{
            name = "server01"
        }
        data = @{
            srcip = "10.0.0.100"
            srcuser = "root"
        }
        full_log = "Critical: Unauthorized access attempt to root account"
    } | ConvertTo-Json -Depth 10
    Write-ColorOutput $criticalData $Colors.Data
}

# Main script execution
Write-ColorOutput "🎤 SOC Agent Windows Demo Script" $Colors.Header
Write-ColorOutput "=================================" $Colors.Header
Write-ColorOutput "Base URL: $BaseUrl" $Colors.Info

# Check if service is running
Write-ColorOutput "`n🔍 Checking if SOC Agent is running..." $Colors.Info
if (-not (Test-Service -Url $BaseUrl)) {
    Write-ColorOutput "❌ SOC Agent is not running at $BaseUrl" $Colors.Error
    Write-ColorOutput "Please start the service first with:" $Colors.Info
    Write-ColorOutput "  .\setup-windows.ps1" $Colors.Data
    Write-ColorOutput "  or" $Colors.Info
    Write-ColorOutput "  .\setup-windows.bat" $Colors.Data
    exit 1
}

Write-ColorOutput "✅ SOC Agent is running!" $Colors.Success

# Show health checks
Show-HealthChecks -Url $BaseUrl

# Show demo data
Show-DemoData

# Interactive demo
Write-ColorOutput "`n🎯 Interactive Demo" $Colors.Header
Write-ColorOutput "==================" $Colors.Header
Write-ColorOutput "Press Enter to run each demo scenario..." $Colors.Info
Write-ColorOutput "Press Ctrl+C to exit" $Colors.Warning

# Demo 1: Wazuh Authentication Failure
Read-Host "`nPress Enter to test Wazuh authentication failure"
$wazuhData = @{
    source = "wazuh"
    rule = @{
        id = 5710
        level = 7
        description = "sshd: authentication failed"
    }
    agent = @{
        name = "srv01"
    }
    data = @{
        srcip = "192.168.1.100"
        srcuser = "admin"
    }
    full_log = "Failed password from 192.168.1.100 port 22 ssh2"
} | ConvertTo-Json -Depth 10

Invoke-Webhook -Url $BaseUrl -Data $wazuhData -Description "Wazuh Authentication Failure"

# Demo 2: CrowdStrike Event
Read-Host "`nPress Enter to test CrowdStrike event"
$crowdstrikeData = @{
    source = "crowdstrike"
    eventType = "AuthActivityAuthFail"
    Severity = 8
    LocalIP = "10.0.0.50"
    UserName = "administrator"
    Name = "Multiple failed login attempts"
} | ConvertTo-Json -Depth 10

Invoke-Webhook -Url $BaseUrl -Data $crowdstrikeData -Description "CrowdStrike Event"

# Demo 3: Custom Security Event
Read-Host "`nPress Enter to test custom security event"
$customData = @{
    source = "custom"
    event_type = "suspicious_activity"
    severity = 7
    timestamp = "2025-01-15T17:59:00Z"
    message = "Suspicious activity detected"
    ip = "203.0.113.50"
    username = "admin"
} | ConvertTo-Json -Depth 10

Invoke-Webhook -Url $BaseUrl -Data $customData -Description "Custom Security Event"

# Demo 4: High-Severity Malware Detection
Read-Host "`nPress Enter to test high-severity malware detection"
$malwareData = @{
    source = "wazuh"
    rule = @{
        id = 1002
        level = 12
        description = "Malware detected"
    }
    agent = @{
        name = "workstation01"
    }
    data = @{
        srcip = "1.2.3.4"
        srcuser = "user1"
    }
    full_log = "Malware detected: trojan.exe from 1.2.3.4"
} | ConvertTo-Json -Depth 10

Invoke-Webhook -Url $BaseUrl -Data $malwareData -Description "High-Severity Malware Detection"

# Demo 5: Critical Security Event
Read-Host "`nPress Enter to test critical security event"
$criticalData = @{
    source = "wazuh"
    rule = @{
        id = 1001
        level = 15
        description = "Critical security event"
    }
    agent = @{
        name = "server01"
    }
    data = @{
        srcip = "10.0.0.100"
        srcuser = "root"
    }
    full_log = "Critical: Unauthorized access attempt to root account"
} | ConvertTo-Json -Depth 10

Invoke-Webhook -Url $BaseUrl -Data $criticalData -Description "Critical Security Event"

# Demo 6: Rate Limiting Test
Read-Host "`nPress Enter to test rate limiting (sending 5 requests quickly)"
Write-ColorOutput "`n🚦 Testing Rate Limiting" $Colors.Info
$testData = @{
    source = "test"
    event_type = "rate_limit_test"
    severity = 1
    message = "Rate limit test"
} | ConvertTo-Json -Depth 10

for ($i = 1; $i -le 5; $i++) {
    Write-ColorOutput "Sending request $i/5..." $Colors.Info
    Invoke-Webhook -Url $BaseUrl -Data $testData -Description "Rate Limit Test $i" | Out-Null
    Start-Sleep -Milliseconds 100
}

# Demo 7: XSS Protection Test
Read-Host "`nPress Enter to test XSS protection"
$xssData = @{
    source = "test"
    event_type = "xss_test"
    severity = 1
    message = "<script>alert('xss')</script>"
} | ConvertTo-Json -Depth 10

Invoke-Webhook -Url $BaseUrl -Data $xssData -Description "XSS Protection Test"

# Show metrics
Read-Host "`nPress Enter to view metrics"
Write-ColorOutput "`n📊 Metrics" $Colors.Header
Write-ColorOutput "==========" $Colors.Header

try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/metrics" -TimeoutSec 5
    $response | ConvertTo-Json -Depth 3 | Write-ColorOutput -Color $Colors.Data
}
catch {
    Write-ColorOutput "❌ Failed to get metrics: $($_.Exception.Message)" $Colors.Error
}

# Final summary
Write-ColorOutput "`n🎉 Demo Complete!" $Colors.Success
Write-ColorOutput "================" $Colors.Success
Write-ColorOutput ""
Write-ColorOutput "📋 What we demonstrated:" $Colors.Info
Write-ColorOutput "• Multi-vendor webhook processing (Wazuh, CrowdStrike, Custom)" $Colors.Data
Write-ColorOutput "• Intelligent threat scoring and categorization" $Colors.Data
Write-ColorOutput "• Security features (rate limiting, XSS protection)" $Colors.Data
Write-ColorOutput "• Health monitoring and metrics" $Colors.Data
Write-ColorOutput "• Real-time event processing and analysis" $Colors.Data
Write-ColorOutput ""
Write-ColorOutput "🌐 Additional URLs to explore:" $Colors.Info
Write-ColorOutput "• API Documentation: $BaseUrl/docs" $Colors.Data
Write-ColorOutput "• Health Check: $BaseUrl/healthz" $Colors.Data
Write-ColorOutput "• Readiness Check: $BaseUrl/readyz" $Colors.Data
Write-ColorOutput "• Service Info: $BaseUrl" $Colors.Data
Write-ColorOutput ""
Write-ColorOutput "📖 For detailed presentation flow, see PRESENTATION_FLOW.md" $Colors.Info
