# SOC Agent - Security Operations Center

**Choose Your Setup Method - All Options Available**

## 🎯 **Quick Start (Choose One)**

### **🚀 Option 1: Docker (One-Click) - RECOMMENDED**
**Perfect for:** Stakeholders, demos, production

**Windows:**
```bash
# 1. Install Docker Desktop from https://docker.com
# 2. Double-click START-SOC-AGENT.bat
# 3. Open http://localhost:3000
```

**Linux:**
```bash
# 1. Install Docker and Docker Compose
# 2. Run: ./start-soc-agent.sh
# 3. Open http://localhost:3000
```

### **🚀 Option 2: Native Installation (No Docker)**
**Perfect for:** Developers, lightweight deployment

**Windows:**
```powershell
# 1. Install Python 3.10+ and Node.js 18+
# 2. Run setup-windows-native.ps1
# 3. Double-click start-soc-agent.bat
# 4. Open http://localhost:3000
```

**Linux:**
```bash
# 1. Install Python 3.10+ and Node.js 18+
# 2. Run: ./setup-linux-native.sh
# 3. Run: ./start-soc-agent.sh
# 4. Open http://localhost:3000
```

### **🚀 Option 3: Docker Compose (Production)**
**Perfect for:** Production servers, advanced users

**Windows & Linux:**
```bash
# 1. Install Docker and Docker Compose
# 2. Run: docker compose up --build
# 3. Open http://localhost:3000
```

### **🚀 Option 4: Manual Installation (Advanced)**
**Perfect for:** Custom deployments, development
```bash
# See ADVANCED_SETUP.md for full manual setup
```

---

## 📋 **What You Get (All Methods)**

- ✅ **Modern Web Dashboard** - Professional SOC interface
- ✅ **Threat Intelligence** - OTX, VirusTotal, AbuseIPDB integration
- ✅ **Multi-Vendor Support** - Wazuh, CrowdStrike, custom formats
- ✅ **Real-time Alerts** - Live security event processing
- ✅ **Email Notifications** - Automated incident response
- ✅ **API Integration** - Connect to any SIEM or security tool

---

## 🎯 **Which Method Should I Choose?**

| Your Situation | Recommended Method | Time to Running |
|----------------|-------------------|-----------------|
| **Stakeholder/Demo** | Option 1 (Docker) | 5 minutes |
| **Developer/Testing** | Option 2 (Native) | 3 minutes |
| **Production/Server** | Option 3 (Docker Compose) | 5 minutes |
| **Custom Setup** | Option 4 (Manual) | 10+ minutes |

**Not sure?** Start with **Option 1 (Docker)** - it's the easiest!

---

## 🚀 **Quick Decision Guide**

### **Choose Option 1 (Docker) if:**
- ✅ You want the easiest setup
- ✅ You're demonstrating to stakeholders
- ✅ You want consistent results
- ✅ You don't want to manage dependencies

### **Choose Option 2 (Native) if:**
- ✅ You don't want to install Docker
- ✅ You're a developer
- ✅ You want faster startup
- ✅ You prefer lightweight deployment

### **Choose Option 3 (Docker Compose) if:**
- ✅ You're deploying to production
- ✅ You want full control
- ✅ You need advanced features
- ✅ You're comfortable with command line

### **Choose Option 4 (Manual) if:**
- ✅ You need custom configuration
- ✅ You're developing new features
- ✅ You want to understand every detail
- ✅ You have specific requirements

---

## 📚 **Documentation**

- **`GET-STARTED.md`** - Detailed setup guide for all methods
- **`QUICKSTART.md`** - 3-step setup for each method
- **`ADVANCED_SETUP.md`** - Advanced options and troubleshooting
- **`ENTERPRISE-SETUP.md`** - Enterprise-grade setup guide

---

## 🆘 **Need Help?**

### **Setup Issues:**
- **Docker not working?** → Try Option 2 (Native)
- **Python/Node issues?** → Try Option 1 (Docker)
- **Still stuck?** → See `ENTERPRISE-SETUP.md`

### **All Methods Available:**
- **Option 1:** `START-SOC-AGENT.bat` (Docker)
- **Option 2:** `setup-windows-native.ps1` (Native)
- **Option 3:** `docker compose up --build` (Docker Compose)
- **Option 4:** Manual setup (Advanced)

---

## 🎉 **Ready to Start?**

**For most users:** Double-click `START-SOC-AGENT.bat` and open http://localhost:3000

**For developers:** Run `setup-windows-native.ps1` and double-click `start-soc-agent.bat`

**For production:** Run `docker compose up --build` and open http://localhost:3000

**All methods work!** Choose what's best for your situation.

---

## 🔧 **Features**

- **Multi-Vendor Support**: Auto-detects and normalizes Wazuh, CrowdStrike, and custom event formats
- **Threat Intelligence**: Enriches IOCs with OTX, VirusTotal, and AbuseIPDB APIs
- **Intelligent Scoring**: Configurable scoring algorithm with base and intelligence-based scoring
- **Multiple Actions**: Email notifications and Autotask ticket creation
- **Security Hardened**: Rate limiting, input validation, HMAC authentication, CORS support
- **Production Ready**: Comprehensive logging, metrics, health checks, caching, and retry logic
- **Web Interface**: Modern React dashboard for alert management and visualization
- **Well Tested**: Comprehensive test suite with security, integration, and unit tests

---

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

---

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🆘 **Support**

- **Issues**: Report bugs and request features via GitHub Issues
- **Documentation**: Check the `/docs` endpoint when running the service
- **Advanced Setup**: See `ADVANCED_SETUP.md` for manual installation and advanced options
- **Security**: Report security issues privately to security@example.com