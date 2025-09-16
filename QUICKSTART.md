# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Option 1: Using the Setup Script (Recommended)

```bash
# Clone the repository
git clone https://github.com/DurkDiggler/HQSec-SOCAI.git
cd HQSec-SOCAI

# Run the setup script
./setup.sh

# Edit configuration
nano .env

# Start the service
source venv/bin/activate
uvicorn soc_agent.webapp:app --host 0.0.0.0 --port 8000 --reload
```

### Option 2: Manual Setup

```bash
# Clone the repository
git clone https://github.com/DurkDiggler/HQSec-SOCAI.git
cd HQSec-SOCAI

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start the service
uvicorn soc_agent.webapp:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Using Docker

```bash
# Clone the repository
git clone https://github.com/DurkDiggler/HQSec-SOCAI.git
cd HQSec-SOCAI

# Create environment file
cp .env.example .env
# Edit .env with your settings

# Start with Docker Compose
docker compose up --build
```

## 🔧 Basic Configuration

Edit `.env` file with minimal required settings:

```bash
# Email notifications (required for email actions)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=soc-agent@yourcompany.com
EMAIL_TO=soc@yourcompany.com

# Optional: Threat intelligence APIs
OTX_API_KEY=your-otx-key
VT_API_KEY=your-virustotal-key
ABUSEIPDB_API_KEY=your-abuseipdb-key
```

## 🧪 Test the Installation

```bash
# Test webhook endpoint
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "source": "test",
    "event_type": "auth_failed",
    "severity": 5,
    "message": "Failed login attempt",
    "ip": "1.2.3.4"
  }'

# Check health
curl http://localhost:8000/healthz

# View API documentation
open http://localhost:8000/docs
```

## 📡 Webhook Integration

### Wazuh Integration
Configure Wazuh to send alerts to your SOC Agent:

```xml
<!-- In /var/ossec/etc/ossec.conf -->
<integration>
  <name>webhook</name>
  <hook_url>http://your-soc-agent:8000/webhook</hook_url>
  <level>3</level>
  <group>authentication_failed,authentication_success</group>
</integration>
```

### CrowdStrike Integration
Configure CrowdStrike to send events via webhook to your SOC Agent endpoint.

### Custom Integration
Send events in the standard format:

```json
{
  "source": "your-system",
  "event_type": "suspicious_activity",
  "severity": 7,
  "timestamp": "2023-01-01T00:00:00Z",
  "message": "Suspicious activity detected",
  "ip": "1.2.3.4",
  "username": "admin"
}
```

## 🔒 Security Features

- **Rate Limiting**: 100 requests per hour per IP (configurable)
- **Input Validation**: Comprehensive validation of all inputs
- **Authentication**: Optional HMAC or shared secret authentication
- **XSS Protection**: Automatic detection and blocking of malicious content
- **CORS Support**: Configurable Cross-Origin Resource Sharing

## 📊 Monitoring

- **Health Check**: `GET /healthz`
- **Readiness Check**: `GET /readyz`
- **Metrics**: `GET /metrics` (if enabled)
- **API Documentation**: `GET /docs`

## 🆘 Troubleshooting

### Common Issues

1. **Import Errors**: Make sure virtual environment is activated
2. **Configuration Errors**: Check `.env` file syntax
3. **Port Already in Use**: Change `APP_PORT` in `.env` file
4. **Permission Denied**: Run `chmod +x setup.sh` for setup script

### Getting Help

- Check the logs for error messages
- Review the comprehensive README.md
- See DEVELOPMENT.md for development workflow
- Open an issue on GitHub for bugs or questions

## 🎯 Next Steps

1. **Configure Threat Intelligence**: Add API keys for OTX, VirusTotal, AbuseIPDB
2. **Set Up Monitoring**: Configure log aggregation and metrics collection
3. **Customize Scoring**: Adjust scoring thresholds in configuration
4. **Add More Adapters**: Extend support for additional security tools
5. **Scale Deployment**: Use Docker Swarm or Kubernetes for production

---

**Need more help?** Check out the full [README.md](README.md) and [DEVELOPMENT.md](DEVELOPMENT.md) for comprehensive documentation.
