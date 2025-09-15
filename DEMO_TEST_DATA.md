# 🧪 Demo Test Data & Webhook Examples

## 📋 **Quick Test Commands**

### **1. Health Check Tests**
```bash
# Basic health check
curl http://localhost:8000/healthz

# Service information
curl http://localhost:8000/

# Readiness check
curl http://localhost:8000/readyz

# Metrics (if enabled)
curl http://localhost:8000/metrics
```

---

## 🔥 **Wazuh Integration Tests**

### **Authentication Failure (Low Severity)**
```bash
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

### **Multiple Failed Logins (Medium Severity)**
```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "source": "wazuh",
    "rule": {"id": 5711, "level": 10, "description": "Multiple failed logins"},
    "agent": {"name": "workstation01"},
    "data": {"srcip": "10.0.0.50", "srcuser": "user1"},
    "full_log": "Multiple failed login attempts from 10.0.0.50 for user user1"
  }'
```

### **Malware Detection (High Severity)**
```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "source": "wazuh",
    "rule": {"id": 1002, "level": 12, "description": "Malware detected"},
    "agent": {"name": "workstation02"},
    "data": {"srcip": "1.2.3.4", "srcuser": "user2"},
    "full_log": "Malware detected: trojan.exe from 1.2.3.4"
  }'
```

### **Critical Security Event (Critical Severity)**
```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "source": "wazuh",
    "rule": {"id": 1001, "level": 15, "description": "Critical security event"},
    "agent": {"name": "server01"},
    "data": {"srcip": "10.0.0.100", "srcuser": "root"},
    "full_log": "Critical: Unauthorized access attempt to root account from 10.0.0.100"
  }'
```

---

## 🛡️ **CrowdStrike Integration Tests**

### **Authentication Failure**
```bash
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

### **Malware Detection**
```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "source": "crowdstrike",
    "eventType": "ProcessRollup2",
    "Severity": 10,
    "LocalIP": "192.168.1.200",
    "UserName": "user3",
    "Name": "Malware execution detected",
    "ProcessName": "suspicious.exe"
  }'
```

### **Suspicious Network Activity**
```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "source": "crowdstrike",
    "eventType": "NetworkConnect",
    "Severity": 7,
    "LocalIP": "10.0.0.75",
    "RemoteIP": "203.0.113.50",
    "UserName": "user4",
    "Name": "Suspicious network connection"
  }'
```

---

## 🔧 **Custom Format Tests**

### **Basic Security Event**
```bash
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

### **High-Severity Custom Event**
```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "source": "custom",
    "event_type": "data_exfiltration",
    "severity": 12,
    "timestamp": "2025-09-15T18:00:00Z",
    "message": "Potential data exfiltration detected",
    "ip": "198.51.100.25",
    "username": "service_account",
    "data_size": "500MB"
  }'
```

### **Critical Custom Event**
```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "source": "custom",
    "event_type": "privilege_escalation",
    "severity": 15,
    "timestamp": "2025-09-15T18:01:00Z",
    "message": "Privilege escalation attempt detected",
    "ip": "10.0.0.200",
    "username": "regular_user",
    "target_user": "admin"
  }'
```

---

## 🧪 **Security Testing**

### **Rate Limiting Test**
```bash
# Send multiple requests quickly to test rate limiting
for i in {1..10}; do
  curl -X POST http://localhost:8000/webhook \
    -H "Content-Type: application/json" \
    -d '{"source": "test", "event_type": "rate_limit_test", "severity": 1}' &
done
wait
```

### **Input Validation Test**
```bash
# Test XSS protection
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "source": "test",
    "event_type": "xss_test",
    "severity": 1,
    "message": "<script>alert(\"xss\")</script>"
  }'
```

### **Malformed JSON Test**
```bash
# Test malformed JSON handling
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"source": "test", "event_type": "malformed", "severity": 1, "message": "test'
```

### **Large Payload Test**
```bash
# Test large payload handling
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d "{\"source\": \"test\", \"event_type\": \"large_payload\", \"severity\": 1, \"message\": \"$(printf 'A%.0s' {1..10000})\"}"
```

---

## 📊 **Expected Response Examples**

### **Low Severity Response**
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

### **High Severity Response**
```json
{
  "analysis": {
    "iocs": {"ips": ["1.2.3.4"], "domains": []},
    "intel": {
      "otx": {"reputation": "malicious", "confidence": 0.85},
      "virustotal": {"positives": 45, "total": 67}
    },
    "scores": {"base": 85, "intel": 25, "final": 95},
    "category": "HIGH",
    "recommended_action": "email_notification"
  },
  "actions": {
    "email_sent": true,
    "email_to": "soc@demo.local"
  },
  "processed_at": 1757959137.957173
}
```

### **Critical Severity Response**
```json
{
  "analysis": {
    "iocs": {"ips": ["10.0.0.100"], "domains": []},
    "intel": {
      "otx": {"reputation": "malicious", "confidence": 0.95},
      "abuseipdb": {"abuse_confidence": 100}
    },
    "scores": {"base": 95, "intel": 30, "final": 100},
    "category": "CRITICAL",
    "recommended_action": "immediate_response"
  },
  "actions": {
    "email_sent": true,
    "email_to": "soc@demo.local",
    "autotask_ticket": "TICKET-12345"
  },
  "processed_at": 1757959137.957173
}
```

---

## 🎯 **Demo Sequence Recommendations**

### **Quick Demo (5 minutes)**
1. Health check
2. Wazuh authentication failure
3. CrowdStrike malware detection
4. Custom high-severity event
5. Check email notifications

### **Full Demo (15 minutes)**
1. All health checks
2. Wazuh: Low → Medium → High → Critical
3. CrowdStrike: Various event types
4. Custom: Different severity levels
5. Security testing (rate limiting, validation)
6. Email notification verification
7. Web interface (if available)

### **Technical Demo (20 minutes)**
1. All above tests
2. Threat intelligence integration
3. Database inspection
4. Log analysis
5. Configuration explanation
6. Architecture overview
7. Security features deep dive

---

## 🚨 **Troubleshooting Commands**

### **Check Service Status**
```bash
# Check if service is running
ps aux | grep uvicorn

# Check port usage
lsof -i :8000

# Check logs
tail -f logs/soc_agent.log
```

### **Reset Demo Environment**
```bash
# Stop service
pkill -f uvicorn

# Clear database
rm -f soc_agent.db

# Restart service
uvicorn soc_agent.webapp:app --host 0.0.0.0 --port 8000 --reload
```

### **Check Email Notifications**
```bash
# Open MailDev interface
echo "Open http://localhost:1080 in your browser"

# Check if MailDev is running
docker ps | grep maildev
```

---

**🎯 Pro Tip: Keep these commands handy during your demo for quick reference!**
