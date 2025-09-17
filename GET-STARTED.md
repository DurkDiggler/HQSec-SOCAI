# Get Started with SOC Agent

**Choose Your Setup Method - All Options Available**

## 🎯 **Quick Decision Guide**

| Your Situation | Recommended Method | Time to Running |
|----------------|-------------------|-----------------|
| **Stakeholder/Demo** | Docker (One-Click) | 5 minutes |
| **Developer/Testing** | Native Installation | 3 minutes |
| **Production/Server** | Docker Compose | 5 minutes |
| **Custom Setup** | Manual Installation | 10+ minutes |

---

## 🚀 **Method 1: Docker (One-Click) - RECOMMENDED**

### **Perfect For:** Stakeholders, demos, production, consistency

### **Windows:**
**What You Need:** Docker Desktop
**Setup Steps:**
1. **Install Docker Desktop** from https://docker.com
2. **Start Docker Desktop**
3. **Double-click** `START-SOC-AGENT.bat`
4. **Wait 2-3 minutes**
5. **Open** http://localhost:3000

### **Linux:**
**What You Need:** Docker and Docker Compose
**Setup Steps:**
1. **Install Docker and Docker Compose**
2. **Run:** `./start-soc-agent.sh`
3. **Wait 2-3 minutes**
4. **Open** http://localhost:3000

### **That's It!** ✅
- Zero configuration required
- Works identically on every machine
- Professional error handling
- All services included (database, cache, email testing)

---

## 🚀 **Method 2: Native Installation (No Docker)**

### **Perfect For:** Developers, lightweight deployment, testing

### **Windows:**
**What You Need:** Python 3.10+ and Node.js 18+
**Setup Steps:**
1. **Install Python 3.10+** from https://python.org
2. **Install Node.js 18+** from https://nodejs.org
3. **Right-click** `setup-windows-native.ps1` → "Run with PowerShell"
4. **Wait 2-3 minutes**
5. **Double-click** `start-soc-agent.bat`
6. **Open** http://localhost:3000

### **Linux:**
**What You Need:** Python 3.10+ and Node.js 18+
**Setup Steps:**
1. **Install Python 3.10+** and **Node.js 18+** using your package manager
2. **Run:** `./setup-linux-native.sh`
3. **Wait 2-3 minutes**
4. **Run:** `./start-soc-agent.sh`
5. **Open** http://localhost:3000

### **That's It!** ✅
- No Docker required
- Faster startup
- Full control over environment
- Same functionality as Docker version

---

## 🚀 **Method 3: Docker Compose (Production)**

### **Perfect For:** Production servers, advanced users, full control

### **Windows & Linux:**
**What You Need:** Docker and Docker Compose
**Setup Steps:**
1. **Install Docker and Docker Compose**
2. **Open Terminal/Command Prompt** in SOC Agent folder
3. **Run:** `docker compose up --build`
4. **Wait 3-5 minutes**
5. **Open** http://localhost:3000

### **That's It!** ✅
- Full production environment
- All services included
- Easy to customize
- Professional deployment

---

## 🚀 **Method 4: Manual Installation (Advanced)**

### **Perfect For:** Custom deployments, development, full control

### **What You Need:**
- Python 3.10+
- Node.js 18+
- PostgreSQL (optional)
- Redis (optional)

### **Setup Steps:**
1. **Install dependencies** (see `ADVANCED_SETUP.md`)
2. **Configure environment** (edit `.env` file)
3. **Start services** manually
4. **Customize** as needed

### **Full Control!** ✅
- Complete customization
- Advanced configurations
- Development workflow
- Production optimization

---

## 🆘 **Which Method Should I Choose?**

### **Choose Docker (Method 1) if:**
- ✅ You want the easiest setup
- ✅ You're demonstrating to stakeholders
- ✅ You want consistent results
- ✅ You don't want to manage dependencies

### **Choose Native Windows (Method 2) if:**
- ✅ You don't want to install Docker
- ✅ You're a developer
- ✅ You want faster startup
- ✅ You prefer lightweight deployment

### **Choose Docker Compose (Method 3) if:**
- ✅ You're deploying to production
- ✅ You want full control
- ✅ You need advanced features
- ✅ You're comfortable with command line

### **Choose Manual (Method 4) if:**
- ✅ You need custom configuration
- ✅ You're developing new features
- ✅ You want to understand every detail
- ✅ You have specific requirements

---

## 🔧 **All Methods Give You:**

- ✅ **Web Dashboard** - http://localhost:3000
- ✅ **Backend API** - http://localhost:8000
- ✅ **API Documentation** - http://localhost:8000/docs
- ✅ **Threat Intelligence** - OTX, VirusTotal, AbuseIPDB
- ✅ **Multi-Vendor Support** - Wazuh, CrowdStrike, custom
- ✅ **Real-time Alerts** - Live security event processing
- ✅ **Email Notifications** - Automated incident response

---

## 🆘 **Need Help?**

### **Setup Issues:**
- **Docker not working?** → Try Method 2 (Native)
- **Python/Node issues?** → Try Method 1 (Docker)
- **Still stuck?** → See `ENTERPRISE-SETUP.md`

### **Advanced Options:**
- **Custom configuration?** → See `ADVANCED_SETUP.md`
- **Production deployment?** → See `ADVANCED_SETUP.md`
- **Development setup?** → See `ADVANCED_SETUP.md`

### **All Methods Available:**
- **Method 1:** `START-SOC-AGENT.bat` (Docker)
- **Method 2:** `setup-windows-native.ps1` (Native)
- **Method 3:** `docker compose up --build` (Docker Compose)
- **Method 4:** Manual setup (Advanced)

---

## 🎉 **Ready to Start?**

### **Windows Users:**
**For most users:** Double-click `START-SOC-AGENT.bat` and open http://localhost:3000
**For developers:** Run `setup-windows-native.ps1` and double-click `start-soc-agent.bat`
**For production:** Run `docker compose up --build` and open http://localhost:3000

### **Linux Users:**
**For most users:** Run `./start-soc-agent.sh` and open http://localhost:3000
**For developers:** Run `./setup-linux-native.sh` and `./start-soc-agent.sh`
**For production:** Run `docker compose up --build` and open http://localhost:3000

**All methods work!** Choose what's best for your situation.
