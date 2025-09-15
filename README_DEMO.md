# 🎯 SOC Agent - Demo Ready!

## 🚀 **Quick Start for Demo**

### **Option 1: Backend Only (Recommended)**
```bash
cd "/home/durkdiggler/HQSec - SOCAI"
./start-demo.sh
```

### **Option 2: Full Stack with Frontend**
```bash
cd "/home/durkdiggler/HQSec - SOCAI"
./setup-demo-hybrid.sh
```

### **Option 3: Test Everything**
```bash
cd "/home/durkdiggler/HQSec - SOCAI"
./test-demo.sh
```

---

## 📊 **Demo Access URLs**

- **SOC Agent API:** http://localhost:8000
- **Health Check:** http://localhost:8000/healthz
- **API Documentation:** http://localhost:8000/docs
- **Web Interface:** http://localhost:3000 (if frontend available)
- **Mail Dev:** http://localhost:1080 (for email testing)

---

## 🧪 **Demo Test Commands**

### **Health Checks**
```bash
curl http://localhost:8000/healthz
curl http://localhost:8000/
curl http://localhost:8000/readyz
```

### **Webhook Tests**
```bash
# Wazuh Authentication Failure
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "source": "wazuh",
    "rule": {"id": 5710, "level": 7, "description": "sshd: authentication failed"},
    "agent": {"name": "srv01"},
    "data": {"srcip": "192.168.1.100", "srcuser": "admin"},
    "full_log": "Failed password from 192.168.1.100 port 22 ssh2"
  }'

# CrowdStrike Auth Failure
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "source": "crowdstrike",
    "eventType": "AuthActivityAuthFail",
    "Severity": 8,
    "LocalIP": "10.0.0.50",
    "UserName": "administrator",
    "Name": "Multiple failed login attempts"
  }'

# High-Severity Malware Detection
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "source": "wazuh",
    "rule": {"id": 1002, "level": 12, "description": "Malware detected"},
    "agent": {"name": "workstation01"},
    "data": {"srcip": "1.2.3.4", "srcuser": "user1"},
    "full_log": "Malware detected: trojan.exe from 1.2.3.4"
  }'
```

---

## 🎬 **Demo Features**

### **✅ Working Features**
- **Multi-vendor webhook processing** (Wazuh, CrowdStrike, Custom)
- **Intelligent scoring algorithm** (LOW/MEDIUM/HIGH categorization)
- **Threat intelligence integration** (IOC extraction and enrichment)
- **Automated response actions** (email notifications)
- **Comprehensive health monitoring**
- **Security features** (rate limiting, input validation)
- **Database storage** (SQLite for demo, PostgreSQL for production)

### **📈 Demo Results**
- **Low Severity Events:** Category "LOW", no action required
- **Medium Severity Events:** Category "MEDIUM", email notification triggered
- **High Severity Events:** Category "HIGH", immediate response actions
- **IOC Extraction:** IPs, domains, and other indicators automatically identified
- **Scoring:** Base score + threat intelligence enhancement

---

## 🛠️ **Setup Scripts**

### **start-demo.sh**
- Starts SOC Agent backend only
- Perfect for API-focused demos
- Includes health checks and status verification

### **setup-demo-hybrid.sh**
- Starts SOC Agent backend + optional frontend
- Includes MailDev for email testing
- Works without Docker daemon
- Recommended for full-stack demos

### **setup-demo-full.sh**
- Full Docker Compose setup
- Includes PostgreSQL, Redis, Nginx
- Requires Docker daemon running
- Production-like environment

### **test-demo.sh**
- Comprehensive testing suite
- Tests all webhook formats
- Verifies all endpoints
- Perfect for validation

---

## 🔧 **Configuration**

### **Environment Variables (.env)**
```bash
# Database
DATABASE_URL=sqlite:///./soc_agent.db

# Server
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO

# Security
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001","http://localhost:8000"]
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=3600

# Email (for notifications)
SMTP_HOST=maildev
SMTP_PORT=1025
EMAIL_FROM=soc-agent@demo.local
EMAIL_TO=["soc@demo.local"]
```

---

## 🚨 **Troubleshooting**

### **Service Won't Start**
```bash
# Check if port is in use
lsof -i :8000

# Kill existing processes
pkill -f uvicorn

# Restart service
./start-demo.sh
```

### **Webhook Not Responding**
```bash
# Check service health
curl http://localhost:8000/healthz

# Check logs
tail -f logs/soc_agent.log
```

### **Email Notifications Not Working**
```bash
# Check MailDev
docker ps | grep maildev

# Restart MailDev
docker stop maildev
docker run -d --name maildev -p 1080:1080 -p 1025:1025 maildev/maildev:latest
```

---

## 📚 **Documentation**

- **DEMO_SCRIPT.md** - Step-by-step demo instructions
- **DEMO_TEST_DATA.md** - Comprehensive test scenarios
- **PRESENTATION_FLOW.md** - Complete presentation script
- **PRESENTATION_SUMMARY.md** - Quick reference guide

---

## 🎯 **Presentation Tips**

1. **Start with health checks** to show the service is operational
2. **Demonstrate multi-vendor support** with different webhook formats
3. **Show scoring algorithm** with various severity levels
4. **Highlight security features** like rate limiting and validation
5. **Use the web interface** if available for visual appeal
6. **Check email notifications** in MailDev interface

---

**🎉 Your SOC Agent is fully operational and ready for presentation!**
