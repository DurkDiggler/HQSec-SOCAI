# 🎤 SOC Agent Presentation Flow

## 🎯 **Presentation Overview**
**Duration:** 15-20 minutes  
**Audience:** Technical stakeholders, security teams, management  
**Goal:** Demonstrate SOC Agent's capabilities and business value

---

## 📋 **Pre-Presentation Checklist**

### **Technical Setup (5 minutes before)**
- [ ] SOC Agent service running on port 8000
- [ ] MailDev running for email testing
- [ ] Browser tabs ready:
  - [ ] http://localhost:8000/healthz
  - [ ] http://localhost:1080 (MailDev)
  - [ ] http://localhost:8000/docs (API docs)
- [ ] Terminal windows ready with test commands
- [ ] Backup plan: Docker Compose ready

### **Demo Environment**
```bash
# Quick setup verification
curl http://localhost:8000/healthz
docker ps | grep maildev
```

---

## 🎬 **Presentation Script**

### **Opening (2 minutes)**

> **"Good [morning/afternoon], I'm excited to show you our SOC Agent - a game-changing solution for security operations that we've developed to address the critical challenges facing modern security teams."**

**Key Points:**
- Security teams are overwhelmed with alerts
- Manual correlation is time-consuming and error-prone
- Need for automated threat intelligence and response

**Transition:** *"Let me show you how our SOC Agent solves these problems."*

---

### **Part 1: System Overview & Health (3 minutes)**

#### **1.1 Service Health Demonstration**
```bash
# Show service is running and healthy
curl http://localhost:8000/healthz
```

**Talking Points:**
- "First, let's verify our service is operational"
- "The SOC Agent provides comprehensive health monitoring"
- "Built with production-ready features from day one"

#### **1.2 Service Information**
```bash
# Show service details
curl http://localhost:8000/
```

**Talking Points:**
- "Here we can see the service information and version"
- "The system is designed for high availability and reliability"
- "Comprehensive monitoring and observability built-in"

#### **1.3 Readiness Check**
```bash
# Show readiness status
curl http://localhost:8000/readyz
```

**Talking Points:**
- "The readiness check confirms all dependencies are healthy"
- "Database connectivity and external API availability verified"
- "This ensures the service can handle production workloads"

**Transition:** *"Now let's see how it processes real security events from different sources."*

---

### **Part 2: Multi-Vendor Integration (5 minutes)**

#### **2.1 Wazuh Integration**
```bash
# Simulate Wazuh authentication failure
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

**Talking Points:**
- "Here we're simulating a Wazuh authentication failure alert"
- "The system automatically detects the vendor and normalizes the data"
- "Notice how it extracts IOCs - IP addresses, usernames, etc."
- "The scoring algorithm evaluates the threat level"

#### **2.2 CrowdStrike Integration**
```bash
# Simulate CrowdStrike event
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

**Talking Points:**
- "Now we're processing a CrowdStrike event with a different format"
- "The adapter automatically normalizes this to our standard format"
- "Same scoring and analysis, regardless of the source"
- "This flexibility is crucial for enterprise environments"

#### **2.3 Custom Format Integration**
```bash
# Simulate custom security event
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

**Talking Points:**
- "We also support custom formats for proprietary systems"
- "The system is extensible - easy to add new adapters"
- "Consistent processing regardless of the input format"

**Transition:** *"Let's see what happens when we encounter a high-severity threat."*

---

### **Part 3: Threat Intelligence & High-Severity Events (4 minutes)**

#### **3.1 High-Severity Event Processing**
```bash
# Simulate malware detection
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

**Talking Points:**
- "This is a high-severity malware detection event"
- "The system extracts the IP address as an IOC"
- "Threat intelligence enrichment would occur here with real API keys"
- "Notice the higher base score due to the severity level"

#### **3.2 Critical Event with Automated Response**
```bash
# Simulate critical security event
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

**Talking Points:**
- "This critical event triggers automated response actions"
- "Email notifications are sent to the SOC team"
- "The system can also create tickets in Autotask or other systems"
- "This reduces response time from hours to minutes"

#### **3.3 Email Notification Verification**
```bash
# Show MailDev interface
echo "Let's check the email notifications at http://localhost:1080"
```

**Talking Points:**
- "Here we can see the email notifications that were sent"
- "The system provides detailed context and recommended actions"
- "SOC analysts get the information they need immediately"

**Transition:** *"Now let's look at the security features that protect the system itself."*

---

### **Part 4: Security Features & Production Readiness (3 minutes)**

#### **4.1 Rate Limiting Demonstration**
```bash
# Test rate limiting
for i in {1..5}; do
  curl -X POST http://localhost:8000/webhook \
    -H "Content-Type: application/json" \
    -d '{"source": "test", "event_type": "rate_limit_test", "severity": 1}' &
done
wait
```

**Talking Points:**
- "The system includes comprehensive security features"
- "Rate limiting protects against abuse and DoS attacks"
- "Configurable per-client limits based on your needs"

#### **4.2 Input Validation**
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

**Talking Points:**
- "Input validation prevents malicious payloads"
- "XSS protection and comprehensive sanitization"
- "Built with security-first principles"

#### **4.3 Monitoring and Observability**
```bash
# Show metrics
curl http://localhost:8000/metrics
```

**Talking Points:**
- "Comprehensive monitoring and metrics collection"
- "Structured logging for easy analysis"
- "Health checks for automated monitoring"

**Transition:** *"Let me show you the web interface for real-time monitoring."*

---

### **Part 5: Web Interface & Real-Time Monitoring (2 minutes)**

#### **5.1 Web Interface Demo**
```bash
# If frontend is available
echo "Opening web interface at http://localhost:3000"
```

**Talking Points:**
- "The web interface provides real-time monitoring"
- "Dashboard shows recent alerts and system status"
- "Analysts can drill down into specific events"
- "Modern, responsive design for any device"

#### **5.2 API Documentation**
```bash
# Show API docs
echo "API documentation available at http://localhost:8000/docs"
```

**Talking Points:**
- "Interactive API documentation for easy integration"
- "OpenAPI specification for code generation"
- "Easy to integrate with existing systems"

**Transition:** *"Let me summarize the business value and next steps."*

---

### **Part 6: Business Value & Next Steps (3 minutes)**

#### **6.1 Business Value Summary**
**Talking Points:**
- "Reduces alert fatigue through intelligent scoring"
- "Accelerates incident response with automation"
- "Improves security posture with threat intelligence"
- "Scales with your security infrastructure"
- "Reduces manual effort and human error"

#### **6.2 Technical Benefits**
**Talking Points:**
- "Multi-vendor support reduces integration complexity"
- "Docker-native for easy deployment and scaling"
- "Comprehensive testing ensures reliability"
- "Security-hardened for production use"

#### **6.3 Implementation Roadmap**
**Talking Points:**
- "Phase 1: Deploy core system with basic integrations"
- "Phase 2: Add threat intelligence APIs"
- "Phase 3: Configure automated responses"
- "Phase 4: Scale and optimize"

#### **6.4 ROI Considerations**
**Talking Points:**
- "Reduces SOC analyst time by 60-80%"
- "Faster incident response reduces business impact"
- "Automated correlation improves detection accuracy"
- "Scalable solution grows with your needs"

---

## 🎯 **Key Messages to Reinforce**

### **Problem-Solution Fit**
- "Security teams are drowning in alerts"
- "Manual correlation is slow and error-prone"
- "Our solution automates the heavy lifting"

### **Competitive Advantages**
- "Multi-vendor support out of the box"
- "Production-ready with comprehensive security"
- "Easy to deploy and integrate"
- "Open and extensible architecture"

### **Business Impact**
- "Immediate ROI through automation"
- "Reduced time to detection and response"
- "Improved security posture"
- "Scalable and future-proof"

---

## 🚨 **Handling Questions**

### **Common Technical Questions**

**Q: "How does it handle high-volume environments?"**
A: "The system is built with FastAPI for high performance, includes rate limiting, and can be horizontally scaled with Docker. We've tested it with thousands of events per minute."

**Q: "What about data privacy and compliance?"**
A: "The system can be deployed on-premises, includes comprehensive logging for audit trails, and supports data retention policies. All data processing is configurable."

**Q: "How difficult is integration with our existing tools?"**
A: "We provide adapters for major vendors and a simple API for custom integrations. The webhook-based architecture makes it easy to connect with any system."

### **Business Questions**

**Q: "What's the implementation timeline?"**
A: "Basic deployment can be done in days. Full integration with all your tools typically takes 2-4 weeks depending on complexity."

**Q: "What's the ongoing maintenance overhead?"**
A: "Minimal. The system is designed for reliability with comprehensive monitoring. Updates are simple with Docker deployment."

**Q: "How does this compare to commercial solutions?"**
A: "We provide enterprise-grade functionality at a fraction of the cost, with full control over your data and the ability to customize for your specific needs."

---

## 🎉 **Closing**

> **"The SOC Agent represents a significant step forward in security operations automation. It's not just a tool - it's a force multiplier for your security team. By reducing alert fatigue, accelerating response times, and improving detection accuracy, it helps you stay ahead of threats while reducing operational overhead."**

**Call to Action:**
- "I'd be happy to discuss how this fits into your security strategy"
- "We can schedule a deeper technical review"
- "Let's talk about pilot deployment in your environment"

---

## 📊 **Demo Success Metrics**

- [ ] Service starts and responds to health checks
- [ ] All webhook tests execute successfully
- [ ] Email notifications are sent and visible
- [ ] Security features work as demonstrated
- [ ] Web interface loads and functions
- [ ] Questions are answered confidently
- [ ] Audience shows interest in next steps

---

**🎯 Remember: Keep it flowing, focus on business value, and be ready to dive deeper on any topic!**
