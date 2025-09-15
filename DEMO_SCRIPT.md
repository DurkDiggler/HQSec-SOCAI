# 🎯 SOC Agent Live Demo Script

## 🚀 **Demo Overview**
This is a comprehensive walkthrough of the SOC Agent - a Security Operations Center webhook analyzer that processes security events, enriches them with threat intelligence, and triggers automated responses.

---

## 📋 **Pre-Demo Setup**

### 1. **Environment Preparation**
```bash
# Navigate to project directory
cd "/home/durkdiggler/HQSec - SOCAI"

# Create .env file (copy this content)
cat > .env << 'EOF'
# SOC Agent Configuration for Demo
DATABASE_URL=sqlite:///./soc_agent.db
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001","http://localhost:8000"]
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=3600
MAX_REQUEST_SIZE=1048576
SMTP_HOST=maildev
SMTP_PORT=1025
EMAIL_FROM=soc-agent@demo.local
EMAIL_TO=["soc@demo.local"]
EOF

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
pip install -e .
pip install sqlalchemy alembic cryptography python-multipart
```

### 2. **Start the Services**
```bash
# Terminal 1: Start SOC Agent
uvicorn soc_agent.webapp:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start MailDev (for email testing)
docker run -d --name maildev -p 1080:1080 -p 1025:1025 maildev/maildev:latest
```

---

## 🎬 **Live Demo Flow**

### **Phase 1: System Health & Overview (2 minutes)**

#### 1.1 **Service Health Check**
```bash
# Check if service is running
curl http://localhost:8000/healthz
```
**Expected Response:**
```json
{
  "status": "ok",
  "timestamp": 1757959119.8685493
}
```

#### 1.2 **Service Information**
```bash
# Get service details
curl http://localhost:8000/
```
**Expected Response:**
```json
{
  "ok": true,
  "service": "SOC Agent – Webhook Analyzer",
  "version": "1.2.0",
  "status": "operational"
}
```

#### 1.3 **Readiness Check**
```bash
# Check if service is ready to process requests
curl http://localhost:8000/readyz
```
**Expected Response:**
```json
{
  "status": "ready",
  "checks": {
    "database": true,
    "external_apis": true
  }
}
```

**🎯 Demo Points:**
- Show the service is operational and healthy
- Highlight the comprehensive health monitoring
- Explain the microservice architecture

---

### **Phase 2: Multi-Vendor Webhook Processing (5 minutes)**

#### 2.1 **Wazuh Integration Demo**
```bash
# Simulate a Wazuh authentication failure alert
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "source": "wazuh",
    "rule": {"id": 5710, "level": 7, "description": "sshd: authentication failed"},
    "agent": {"name": "srv01"},
    "data": {"srcip": "192.168.1.100", "srcuser": "admin"},
    "full_log": "Failed password from 192.168.1.100 port 22 ssh2"
  }'
```

**Expected Response:**
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

#### 2.2 **CrowdStrike Integration Demo**
```bash
# Simulate a CrowdStrike authentication failure
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
```

#### 2.3 **Custom Format Demo**
```bash
# Simulate a custom security event
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "source": "custom",
    "event_type": "suspicious_activity",
    "severity": 7,
    "timestamp": "2025-09-15T17:59:00Z",
    "message": "Suspicious activity detected",
    "ip": "203.0.113.50",
    "username": "admin"
  }'
```

**🎯 Demo Points:**
- Show automatic vendor detection and normalization
- Explain the scoring algorithm
- Highlight the flexible adapter architecture

---

### **Phase 3: Threat Intelligence Integration (3 minutes)**

#### 3.1 **High-Severity Event with IOC Enrichment**
```bash
# Simulate a high-severity event that would trigger threat intelligence lookup
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

**🎯 Demo Points:**
- Show IOC extraction (IPs, domains, hashes)
- Explain threat intelligence enrichment process
- Highlight the scoring enhancement with intel data

---

### **Phase 4: Automated Response Actions (3 minutes)**

#### 4.1 **Email Notification Demo**
```bash
# Check MailDev interface
echo "Open http://localhost:1080 in browser to see email notifications"
```

#### 4.2 **High-Priority Alert Simulation**
```bash
# Simulate a critical alert that triggers email notification
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "source": "wazuh",
    "rule": {"id": 1001, "level": 15, "description": "Critical security event"},
    "agent": {"name": "server01"},
    "data": {"srcip": "10.0.0.100", "srcuser": "root"},
    "full_log": "Critical: Unauthorized access attempt to root account"
  }'
```

**🎯 Demo Points:**
- Show automated email notifications
- Explain the action triggering logic
- Highlight the configurable response system

---

### **Phase 5: Security Features & Monitoring (2 minutes)**

#### 5.1 **Rate Limiting Demo**
```bash
# Test rate limiting by sending multiple requests quickly
for i in {1..5}; do
  curl -X POST http://localhost:8000/webhook \
    -H "Content-Type: application/json" \
    -d '{"source": "test", "event_type": "rate_limit_test", "severity": 1}' &
done
wait
```

#### 5.2 **Input Validation Demo**
```bash
# Test input validation with malicious payload
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "source": "test",
    "event_type": "xss_test",
    "severity": 1,
    "message": "<script>alert(\"xss\")</script>"
  }'
```

#### 5.3 **Metrics and Monitoring**
```bash
# Check service metrics
curl http://localhost:8000/metrics
```

**🎯 Demo Points:**
- Show security hardening features
- Explain rate limiting and input validation
- Highlight monitoring and observability

---

### **Phase 6: Web Interface Demo (2 minutes)**

#### 6.1 **Start Frontend (if available)**
```bash
# If frontend is available, start it
cd frontend
npm install
npm start
```

#### 6.2 **Show Web Interface**
- Navigate to http://localhost:3000
- Show dashboard with recent alerts
- Demonstrate real-time updates

**🎯 Demo Points:**
- Show the modern web interface
- Highlight real-time monitoring capabilities
- Explain the user experience

---

## 🎯 **Key Demo Talking Points**

### **1. Problem Statement**
- "Security teams are overwhelmed with alerts from multiple sources"
- "Manual correlation and response is time-consuming and error-prone"
- "Need for automated threat intelligence enrichment and response"

### **2. Solution Architecture**
- "Multi-vendor webhook processing with automatic normalization"
- "Threat intelligence integration with multiple providers"
- "Configurable scoring and automated response actions"
- "Security-hardened with rate limiting and input validation"

### **3. Business Value**
- "Reduces alert fatigue through intelligent scoring"
- "Accelerates incident response with automation"
- "Improves security posture with threat intelligence"
- "Scales with your security infrastructure"

### **4. Technical Highlights**
- "Built with FastAPI for high performance"
- "Docker-native for easy deployment"
- "Comprehensive testing and security validation"
- "Production-ready with monitoring and logging"

---

## 🚨 **Troubleshooting Quick Reference**

### **Service Won't Start**
```bash
# Check if port is in use
lsof -i :8000

# Check logs
tail -f logs/soc_agent.log

# Restart service
pkill -f uvicorn
uvicorn soc_agent.webapp:app --host 0.0.0.0 --port 8000 --reload
```

### **Webhook Not Responding**
```bash
# Check service health
curl http://localhost:8000/healthz

# Check service logs
tail -f logs/soc_agent.log

# Test with simple request
curl http://localhost:8000/
```

### **Database Issues**
```bash
# Remove database and restart
rm soc_agent.db
# Restart service
```

---

## 📊 **Demo Success Metrics**

- ✅ Service starts successfully
- ✅ Health checks pass
- ✅ Webhook processing works for all vendors
- ✅ Threat intelligence integration functions
- ✅ Email notifications are sent
- ✅ Security features work as expected
- ✅ Web interface loads and updates

---

## 🎉 **Demo Conclusion**

"This SOC Agent demonstrates how we can automate security operations, reduce alert fatigue, and improve incident response times. The system is production-ready and can be easily integrated with your existing security infrastructure."

**Next Steps:**
1. Configure threat intelligence API keys
2. Set up production email notifications
3. Integrate with your security tools
4. Deploy to production environment

---

**🎯 Remember: Keep the demo flowing, explain the business value, and be ready to answer technical questions!**
