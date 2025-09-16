# 🎤 SOC Agent Windows Presentation Guide

## 🚀 Quick Start for Windows

This guide provides everything you need to run the SOC Agent presentation on a Windows machine.

### 📋 Prerequisites

- **Windows 10/11** (tested on Windows 10 build 22631)
- **Python 3.10+** or **Docker Desktop**
- **Node.js 16+** (for frontend development)
- **PowerShell 5.1+** (comes with Windows)
- **curl** (for demo scripts, usually pre-installed)

### 🎯 Setup Options

#### Option 1: Full Stack Setup (Recommended)
```powershell
# Run as Administrator (recommended)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup-windows-full.ps1
```

#### Option 2: Backend Only Setup
```powershell
# Backend only (no frontend)
.\setup-windows.ps1
```

#### Option 3: Batch File Setup
```cmd
# Double-click or run from command prompt
setup-windows-full.bat
```

#### Option 4: Docker Setup
```powershell
# If you have Docker Desktop installed
.\setup-windows-full.ps1 -UseDocker
```

---

## 🎬 Presentation Script

### **Pre-Presentation Setup (5 minutes before)**

1. **Open Command Prompt or PowerShell as Administrator**
2. **Navigate to the project directory:**
   ```cmd
   cd C:\Users\DJDurko\SOCAI\HQSec-SOCAI
   ```

3. **Run the setup script:**
   ```powershell
   .\setup-windows-full.ps1
   ```
   or
   ```cmd
   setup-windows-full.bat
   ```

4. **Verify the services are running:**
   - Backend: http://localhost:8000/healthz
   - Frontend: http://localhost:3000
   - Should show: `{"status": "ok", "timestamp": ...}` for backend

5. **Prepare demo windows:**
   - Browser tab: http://localhost:3000 (Web Interface)
   - Browser tab: http://localhost:8000/docs (API documentation)
   - Browser tab: http://localhost:1080 (MailDev, if using Docker)
   - Command prompt ready for demo commands

### **Presentation Flow (15-20 minutes)**

#### **Opening (2 minutes)**
> "Good [morning/afternoon], I'm excited to show you our SOC Agent - a game-changing solution for security operations that we've developed to address the critical challenges facing modern security teams."

**Key Points:**
- Security teams are overwhelmed with alerts
- Manual correlation is time-consuming and error-prone
- Need for automated threat intelligence and response

#### **Part 1: System Overview & Health (3 minutes)**

**1.1 Service Health Demonstration**
```powershell
# In PowerShell or Command Prompt
curl http://localhost:8000/healthz
```

**Talking Points:**
- "First, let's verify our service is operational"
- "The SOC Agent provides comprehensive health monitoring"
- "Built with production-ready features from day one"

**1.2 Service Information**
```powershell
curl http://localhost:8000/
```

**1.3 Readiness Check**
```powershell
curl http://localhost:8000/readyz
```

**Transition:** *"Now let's see how it processes real security events from different sources."*

#### **Part 2: Multi-Vendor Integration (5 minutes)**

**2.1 Wazuh Integration**
```powershell
curl -X POST http://localhost:8000/webhook -H "Content-Type: application/json" -d '{
  "source": "wazuh",
  "rule": {"id": 5710, "level": 7, "description": "sshd: authentication failed"},
  "agent": {"name": "srv01"},
  "data": {"srcip": "192.168.1.100", "srcuser": "admin"},
  "full_log": "Failed password from 192.168.1.100 port 22 ssh2"
}'
```

**2.2 CrowdStrike Integration**
```powershell
curl -X POST http://localhost:8000/webhook -H "Content-Type: application/json" -d '{
  "source": "crowdstrike",
  "eventType": "AuthActivityAuthFail",
  "Severity": 8,
  "LocalIP": "10.0.0.50",
  "UserName": "administrator",
  "Name": "Multiple failed login attempts"
}'
```

**2.3 Custom Format Integration**
```powershell
curl -X POST http://localhost:8000/webhook -H "Content-Type: application/json" -d '{
  "source": "custom",
  "event_type": "suspicious_activity",
  "severity": 7,
  "timestamp": "2025-01-15T17:59:00Z",
  "message": "Suspicious activity detected",
  "ip": "203.0.113.50",
  "username": "admin"
}'
```

#### **Part 3: Threat Intelligence & High-Severity Events (4 minutes)**

**3.1 High-Severity Event Processing**
```powershell
curl -X POST http://localhost:8000/webhook -H "Content-Type: application/json" -d '{
  "source": "wazuh",
  "rule": {"id": 1002, "level": 12, "description": "Malware detected"},
  "agent": {"name": "workstation01"},
  "data": {"srcip": "1.2.3.4", "srcuser": "user1"},
  "full_log": "Malware detected: trojan.exe from 1.2.3.4"
}'
```

**3.2 Critical Event with Automated Response**
```powershell
curl -X POST http://localhost:8000/webhook -H "Content-Type: application/json" -d '{
  "source": "wazuh",
  "rule": {"id": 1001, "level": 15, "description": "Critical security event"},
  "agent": {"name": "server01"},
  "data": {"srcip": "10.0.0.100", "srcuser": "root"},
  "full_log": "Critical: Unauthorized access attempt to root account"
}'
```

#### **Part 4: Security Features & Production Readiness (3 minutes)**

**4.1 Rate Limiting Demonstration**
```powershell
# Send multiple requests quickly
for ($i = 1; $i -le 5; $i++) {
  curl -X POST http://localhost:8000/webhook -H "Content-Type: application/json" -d "{\"source\": \"test\", \"event_type\": \"rate_limit_test\", \"severity\": 1}"
}
```

**4.2 Input Validation**
```powershell
curl -X POST http://localhost:8000/webhook -H "Content-Type: application/json" -d '{
  "source": "test",
  "event_type": "xss_test",
  "severity": 1,
  "message": "<script>alert(\"xss\")</script>"
}'
```

**4.3 Monitoring and Observability**
```powershell
curl http://localhost:8000/metrics
```

#### **Part 5: Web Interface & Real-Time Monitoring (2 minutes)**

**5.1 Web Interface Demo**
- Open browser to http://localhost:3000
- Show modern React dashboard with real-time alerts
- Demonstrate interactive charts and statistics
- Show alert details and filtering capabilities

**5.2 API Documentation**
- Open browser to http://localhost:8000/docs
- Show interactive API documentation
- Demonstrate webhook testing interface

**5.3 MailDev Interface (if using Docker)**
- Open browser to http://localhost:1080
- Show email notifications that were sent

#### **Part 6: Business Value & Next Steps (3 minutes)**

**Key Messages:**
- Reduces alert fatigue through intelligent scoring
- Accelerates incident response with automation
- Improves security posture with threat intelligence
- Scales with your security infrastructure
- Reduces manual effort and human error

---

## 🛠️ Demo Scripts

### **Automated Demo (PowerShell)**
```powershell
# Full stack demo (with frontend)
.\demo-windows-full.ps1

# Backend only demo
.\demo-windows.ps1
```

### **Automated Demo (Batch)**
```cmd
# Full stack demo (with frontend)
demo-windows-full.bat

# Backend only demo
demo-windows.bat
```

### **Manual Demo Commands**

**Health Checks:**
```powershell
# Service info
curl http://localhost:8000/

# Health check
curl http://localhost:8000/healthz

# Readiness check
curl http://localhost:8000/readyz
```

**Webhook Tests:**
```powershell
# Wazuh test
curl -X POST http://localhost:8000/webhook -H "Content-Type: application/json" -d '{"source": "wazuh", "rule": {"id": 5710, "level": 7, "description": "sshd: authentication failed"}, "agent": {"name": "srv01"}, "data": {"srcip": "192.168.1.100", "srcuser": "admin"}, "full_log": "Failed password from 192.168.1.100 port 22 ssh2"}'

# CrowdStrike test
curl -X POST http://localhost:8000/webhook -H "Content-Type: application/json" -d '{"source": "crowdstrike", "eventType": "AuthActivityAuthFail", "Severity": 8, "LocalIP": "10.0.0.50", "UserName": "administrator", "Name": "Multiple failed login attempts"}'

# Custom test
curl -X POST http://localhost:8000/webhook -H "Content-Type: application/json" -d '{"source": "custom", "event_type": "suspicious_activity", "severity": 7, "timestamp": "2025-01-15T17:59:00Z", "message": "Suspicious activity detected", "ip": "203.0.113.50", "username": "admin"}'
```

---

## 🔧 Troubleshooting

### **Common Issues**

**1. PowerShell Execution Policy Error**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**2. Port 8000 Already in Use**
```cmd
# Check what's using the port
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

**3. Python Not Found**
- Download Python 3.10+ from https://www.python.org/downloads/
- Make sure to check "Add Python to PATH" during installation
- Or specify path: `.\setup-windows-full.ps1 -PythonPath "C:\Python310\python.exe"`

**4. Node.js Not Found**
- Download Node.js 16+ from https://nodejs.org/
- Make sure to check "Add to PATH" during installation
- Or use backend-only setup: `.\setup-windows.ps1`

**5. Docker Not Working**
- Install Docker Desktop from https://www.docker.com/products/docker-desktop/
- Make sure Docker Desktop is running
- Or use Python + Node.js setup: `.\setup-windows-full.ps1 -SkipDocker`

**6. curl Not Found**
- Download curl from https://curl.se/download.html
- Or use PowerShell version: `.\demo-windows-full.ps1`

### **Service Management**

**Start Service:**
```powershell
# Full stack (backend + frontend)
.\setup-windows-full.ps1

# Backend only
.\setup-windows.ps1
```

**Stop Service:**
- **Python + Node.js**: Press `Ctrl+C` in the terminal windows
- **Docker**: `docker-compose -f docker-compose.full.yml down`

**Restart Service:**
```powershell
# Stop first, then start
.\setup-windows-full.ps1
```

**View Logs:**
- **Python**: Check terminal output
- **Docker**: `docker-compose logs -f`

---

## 📊 Expected Results

### **Health Endpoints:**
- **Root**: `{"ok": true, "service": "SOC Agent – Webhook Analyzer", "version": "1.2.0", "status": "operational"}`
- **Health**: `{"status": "ok", "timestamp": 1757959119.8685493}`
- **Ready**: `{"status": "ready", "checks": {"database": true, "external_apis": true}}`

### **Webhook Response Example:**
```json
{
  "analysis": {
    "iocs": {"ips": ["192.168.1.100"], "domains": []},
    "intel": {},
    "scores": {"base": 57, "intel": 0, "final": 34},
    "category": "LOW",
    "recommended_action": "none"
  },
  "actions": {},
  "processed_at": 1757959137.957173
}
```

---

## 🎯 Key Presentation Points

### **Problem-Solution Fit**
- Security teams are drowning in alerts
- Manual correlation is slow and error-prone
- Our solution automates the heavy lifting

### **Competitive Advantages**
- Multi-vendor support out of the box
- Production-ready with comprehensive security
- Easy to deploy and integrate
- Open and extensible architecture

### **Business Impact**
- Immediate ROI through automation
- Reduced time to detection and response
- Improved security posture
- Scalable and future-proof

---

## 📞 Support

- **Web Interface**: http://localhost:3000
- **Health Check**: http://localhost:8000/healthz
- **Service Info**: http://localhost:8000/
- **API Documentation**: http://localhost:8000/docs
- **MailDev UI**: http://localhost:1080 (if using Docker)

---

**🎉 The SOC Agent is ready for your Windows presentation!**
