# 🎤 SOC Agent Full Stack Presentation Checklist

## ✅ **Pre-Presentation Setup (15 minutes before)**

### **Windows Machine**
- [ ] **PowerShell Execution Policy**: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- [ ] **Python 3.10+**: Verify with `python --version`
- [ ] **Node.js 16+**: Verify with `node --version`
- [ ] **Docker Desktop**: Running and accessible (if using Docker)
- [ ] **Ports Available**: 8000, 3000, 5432, 6379, 1080

### **Linux Machine**
- [ ] **Python 3.10+**: Verify with `python3 --version`
- [ ] **Node.js 16+**: Verify with `node --version`
- [ ] **Docker & Docker Compose**: Running and accessible (if using Docker)
- [ ] **Ports Available**: 8000, 3000, 5432, 6379, 1080

### **Both Platforms**
- [ ] **Project Directory**: Navigate to HQSec-SOCAI root
- [ ] **Environment File**: `.env` exists and configured
- [ ] **Dependencies**: All packages installed
- [ ] **Services Running**: Backend and frontend accessible

---

## 🚀 **Setup Commands**

### **Windows (PowerShell)**
```powershell
# Full stack setup
.\setup-windows-full.ps1

# Test everything
.\test-full-stack.ps1
```

### **Windows (Batch)**
```cmd
# Full stack setup
setup-windows-full.bat

# Test everything
.\test-full-stack.ps1
```

### **Linux**
```bash
# Full stack setup
./setup-full.sh

# Test everything
./test-full-stack.sh
```

### **Docker (Both Platforms)**
```bash
# Full stack with Docker
docker-compose -f docker-compose.full.yml up --build -d

# Test everything
./test-full-stack.sh
```

---

## 🌐 **URL Verification**

### **Required URLs (All Must Work)**
- [ ] **Frontend**: http://localhost:3000
- [ ] **Backend API**: http://localhost:8000
- [ ] **Health Check**: http://localhost:8000/healthz
- [ ] **API Documentation**: http://localhost:8000/docs
- [ ] **Readiness Check**: http://localhost:8000/readyz

### **Optional URLs (Docker Only)**
- [ ] **MailDev UI**: http://localhost:1080
- [ ] **PostgreSQL**: localhost:5432
- [ ] **Redis**: localhost:6379

---

## 🧪 **Pre-Presentation Tests**

### **1. Backend Health Tests**
```bash
# Windows
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz
curl http://localhost:8000/

# Linux
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz
curl http://localhost:8000/
```

### **2. Frontend Tests**
```bash
# Windows
Start-Process http://localhost:3000

# Linux
xdg-open http://localhost:3000
```

### **3. API Integration Tests**
```bash
# Test alerts API
curl http://localhost:8000/api/v1/alerts

# Test statistics
curl http://localhost:8000/api/v1/alerts/stats

# Test dashboard
curl http://localhost:8000/api/v1/dashboard
```

### **4. Webhook Tests**
```bash
# Test webhook endpoint
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "source": "test",
    "event_type": "presentation_test",
    "severity": 5,
    "message": "Pre-presentation test",
    "ip": "192.168.1.100",
    "username": "presenter"
  }'
```

---

## 🎯 **Presentation Flow Verification**

### **Part 1: System Overview (3 minutes)**
- [ ] Service health check works
- [ ] Service information displays correctly
- [ ] Readiness check shows all green

### **Part 2: Multi-Vendor Integration (5 minutes)**
- [ ] Wazuh webhook test ready
- [ ] CrowdStrike webhook test ready
- [ ] Custom format webhook test ready
- [ ] All responses show proper analysis

### **Part 3: Threat Intelligence (4 minutes)**
- [ ] High-severity event test ready
- [ ] Critical event test ready
- [ ] Email notifications working (if configured)
- [ ] Scoring algorithm working

### **Part 4: Security Features (3 minutes)**
- [ ] Rate limiting test ready
- [ ] XSS protection test ready
- [ ] Input validation working
- [ ] Metrics endpoint accessible

### **Part 5: Web Interface (5 minutes)**
- [ ] Frontend loads correctly
- [ ] Dashboard shows data
- [ ] Alerts display properly
- [ ] Charts and statistics working
- [ ] API integration functional

### **Part 6: Business Value (3 minutes)**
- [ ] Key talking points ready
- [ ] ROI calculations prepared
- [ ] Next steps outlined

---

## 🔧 **Troubleshooting Quick Fixes**

### **Common Issues**

**Port Already in Use**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux
lsof -i :8000
kill -9 <PID>
```

**Services Not Starting**
```bash
# Check logs
docker-compose -f docker-compose.full.yml logs

# Restart services
docker-compose -f docker-compose.full.yml restart
```

**Frontend Not Loading**
```bash
# Check if backend is running
curl http://localhost:8000/healthz

# Check CORS configuration
curl -H "Origin: http://localhost:3000" http://localhost:8000/api/v1/alerts
```

**Database Issues**
```bash
# Reset database
rm soc_agent.db
# Restart services
```

---

## 📋 **Backup Plans**

### **Plan A: Full Stack (Preferred)**
- Frontend + Backend + Database
- Complete web interface
- All features available

### **Plan B: Backend Only**
- Backend API only
- Command line demos
- API documentation

### **Plan C: Docker Fallback**
- Use Docker Compose
- All services containerized
- More reliable deployment

---

## 🎉 **Success Criteria**

### **Must Have**
- [ ] Backend API responding
- [ ] Frontend loading
- [ ] Webhook processing working
- [ ] Health checks passing

### **Nice to Have**
- [ ] Email notifications working
- [ ] Database persistence
- [ ] Real-time updates
- [ ] All security features

### **Presentation Ready**
- [ ] All URLs accessible
- [ ] Demo data prepared
- [ ] Backup plans ready
- [ ] Troubleshooting guide handy

---

## 📞 **Emergency Contacts**

- **Technical Issues**: Check logs first
- **Service Problems**: Restart services
- **Network Issues**: Check firewall/ports
- **Configuration**: Verify .env file

---

**🎯 Remember: Test everything 15 minutes before the presentation!**
