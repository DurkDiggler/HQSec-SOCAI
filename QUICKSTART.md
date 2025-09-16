# Quick Start Guide

Get SOC Agent running in 3 simple steps!

## 📋 Prerequisites

### Option 1: Docker (Recommended - All Platforms)
- **Docker & Docker Compose** (all platforms)
- **Git** (all platforms)
- **Windows**: Docker Desktop for Windows
- **Linux/macOS**: Docker and Docker Compose installed

### Option 2: Native Installation (Windows Only)
- **Python 3.10+** (from python.org)
- **Node.js 18+** (from nodejs.org)
- **Git** (from git-scm.com)
- **No Docker required!**

## 🚀 3-Step Setup

### Option 1: Docker (All Platforms)

#### 1. Clone and Configure
```bash
git clone https://github.com/DurkDiggler/HQSec-SOCAI.git
cd HQSec-SOCAI
cp env.example .env
```

#### 2. Start Everything
```bash
docker compose up --build
```

#### 3. Access Your SOC Agent
- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/healthz

### Option 2: Native Windows (No Docker)

#### 1. Clone and Setup
```powershell
git clone https://github.com/DurkDiggler/HQSec-SOCAI.git
cd HQSec-SOCAI
.\setup-windows-native.ps1
```

#### 2. Start Everything
```powershell
# Double-click this file or run:
.\start-soc-agent.bat
```

#### 3. Access Your SOC Agent
- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/healthz

## ✅ That's It!

Your SOC Agent is now running with:
- ✅ Backend API with threat intelligence
- ✅ Modern web dashboard
- ✅ PostgreSQL database
- ✅ Redis caching
- ✅ Email testing interface
- ✅ Nginx reverse proxy

## 🔧 Optional Configuration

Edit `.env` to add your API keys:
```bash
# Threat Intelligence (optional)
OTX_API_KEY=your-otx-key
VT_API_KEY=your-virustotal-key
ABUSEIPDB_API_KEY=your-abuseipdb-key

# Email Notifications (optional)
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=soc-agent@yourcompany.com
```

## 📡 Test Your Setup

Send a test webhook:

**Linux/macOS:**
```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "source": "test",
    "event_type": "auth_failed",
    "severity": 5,
    "timestamp": "2023-01-01T00:00:00Z",
    "message": "Test authentication failure",
    "ip": "1.2.3.4",
    "username": "admin"
  }'
```

**Windows PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/webhook" -Method POST -ContentType "application/json" -Body '{
  "source": "test",
  "event_type": "auth_failed",
  "severity": 5,
  "timestamp": "2023-01-01T00:00:00Z",
  "message": "Test authentication failure",
  "ip": "1.2.3.4",
  "username": "admin"
}'
```

## 🆘 Need Help?

- **Full Documentation**: See `README.md`
- **Advanced Setup**: See `ADVANCED_SETUP.md`
- **Issues**: Report bugs on GitHub

## 🎯 Next Steps

1. **Configure Threat Intelligence**: Add API keys for OTX, VirusTotal, AbuseIPDB
2. **Set Up Monitoring**: Configure log aggregation and metrics
3. **Integrate with SIEM**: Connect Wazuh, CrowdStrike, or custom systems
4. **Customize Scoring**: Adjust threat scoring algorithms
5. **Set Up Notifications**: Configure email and Autotask integration