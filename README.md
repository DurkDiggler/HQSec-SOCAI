# SOC Agent - Enhanced Security Operations Center Webhook Analyzer

A robust FastAPI webhook service that ingests security events, enriches IOCs with threat intelligence (OTX, VirusTotal, AbuseIPDB), scores them using configurable algorithms, and triggers appropriate responses (email notifications or Autotask tickets). Built with security-first principles, comprehensive testing, and production-ready features.

## 🚀 Features

- **Multi-Vendor Support**: Auto-detects and normalizes Wazuh, CrowdStrike, and custom event formats
- **Threat Intelligence**: Enriches IOCs with OTX, VirusTotal, and AbuseIPDB APIs
- **Intelligent Scoring**: Configurable scoring algorithm with base and intelligence-based scoring
- **Multiple Actions**: Email notifications and Autotask ticket creation
- **Security Hardened**: Rate limiting, input validation, HMAC authentication, CORS support
- **Production Ready**: Comprehensive logging, metrics, health checks, caching, and retry logic
- **Docker Native**: Full Docker and Docker Compose support with multi-stage builds
- **Well Tested**: Comprehensive test suite with security, integration, and unit tests

## 🛡️ Security Features

- **Input Validation**: Comprehensive validation of all inputs with Pydantic models
- **Rate Limiting**: Configurable rate limiting per client IP
- **Authentication**: Optional shared secret and HMAC signature verification
- **Request Size Limits**: Protection against large payload attacks
- **XSS Protection**: Detection and blocking of malicious content
- **IP Validation**: Proper IPv4/IPv6 validation using ipaddress module
- **CORS Support**: Configurable Cross-Origin Resource Sharing
- **Security Headers**: Proper HTTP security headers
- **Logging**: Comprehensive security event logging

## 📋 Requirements

- Python 3.10+
- Docker & Docker Compose (recommended)
- Threat intelligence API keys (optional but recommended)

## 🚀 Quick Start

### Using Docker Compose (Recommended)

1. **Clone and configure**
   ```bash
   git clone https://github.com/DurkDiggler/HQSec-SOCAI.git
   cd HQSec-SOCAI
   cp .env.sample .env
   # Edit .env with your configuration
   ```

2. **Start the service**
   ```bash
   docker compose up --build
   ```

3. **Verify deployment**
   ```bash
   curl http://localhost:8000/healthz
   curl http://localhost:8000/readyz
   ```

### Manual Installation

1. **Install dependencies**
   ```bash
   pip install -e .[dev]
   ```

2. **Configure environment**
   ```bash
   cp .env.sample .env
   # Edit .env with your configuration
   ```

3. **Run the service**
   ```bash
   uvicorn soc_agent.webapp:app --host 0.0.0.0 --port 8000
   ```

## 🔧 Configuration

The service is configured via environment variables. See `.env.sample` for all available options:

### Essential Configuration

```bash
# Server
APP_HOST=0.0.0.0
APP_PORT=8000

# Security
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
MAX_REQUEST_SIZE=1048576

# Email (if using email notifications)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
EMAIL_FROM=soc-agent@example.com
EMAIL_TO=soc@example.com

# Autotask (if using ticket creation)
AT_BASE_URL=https://your-instance.autotask.net
AT_API_INTEGRATION_CODE=your-code
AT_USERNAME=your-username
AT_SECRET=your-secret
AT_ACCOUNT_ID=12345
AT_QUEUE_ID=67890

# Threat Intelligence (optional but recommended)
OTX_API_KEY=your-otx-key
VT_API_KEY=your-virustotal-key
ABUSEIPDB_API_KEY=your-abuseipdb-key
```

## 📡 API Endpoints

### Webhook Endpoint
- **POST** `/webhook` - Main webhook for security events
- **Authentication**: Optional shared secret or HMAC signature
- **Rate Limited**: Configurable per-client rate limiting
- **Content-Type**: `application/json`

### Health & Monitoring
- **GET** `/healthz` - Health check endpoint
- **GET** `/readyz` - Readiness check endpoint
- **GET** `/metrics` - Basic metrics (if enabled)
- **GET** `/` - Service information

## 🔌 Vendor Adapters

The service automatically detects and normalizes events from:

### Wazuh
```json
{
  "rule": {"id": 5710, "level": 7, "description": "sshd: authentication failed"},
  "agent": {"name": "srv01"},
  "data": {"srcip": "203.0.113.4", "srcuser": "bob"},
  "full_log": "Failed password from 203.0.113.4 port 22 ssh2"
}
```

### CrowdStrike
```json
{
  "eventType": "AuthActivityAuthFail",
  "Severity": 5,
  "LocalIP": "198.51.100.10",
  "UserName": "alice",
  "Name": "Authentication failed"
}
```

### Custom Format
```json
{
  "source": "custom",
  "event_type": "auth_failed",
  "severity": 5,
  "timestamp": "2023-01-01T00:00:00Z",
  "message": "Authentication failed",
  "ip": "1.2.3.4",
  "username": "admin"
}
```

## 🧪 Testing

### Run All Tests
```bash
make test
```

### Run Specific Test Categories
```bash
# Security tests
pytest tests/test_security.py -v

# Integration tests
pytest tests/test_integration.py -v

# Model validation tests
pytest tests/test_models.py -v
```

### Test Coverage
```bash
pytest --cov=soc_agent --cov-report=html
```

## 🔒 Security Best Practices

1. **Use HTTPS**: Always use TLS in production
2. **Enable Authentication**: Set `WEBHOOK_SHARED_SECRET` or `WEBHOOK_HMAC_SECRET`
3. **Configure CORS**: Set appropriate `CORS_ORIGINS`
4. **Rate Limiting**: Adjust `RATE_LIMIT_REQUESTS` based on your needs
5. **Monitor Logs**: Enable structured logging and monitor for security events
6. **Regular Updates**: Keep dependencies updated
7. **Network Security**: Use firewalls and network segmentation
8. **API Keys**: Rotate threat intelligence API keys regularly

## 🐳 Docker Deployment

### Production Docker Compose
```yaml
version: '3.8'
services:
  soc-agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
      - ENABLE_METRICS=true
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### TLS with Reverse Proxy
```yaml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
    depends_on:
      - soc-agent
  
  soc-agent:
    build: .
    expose:
      - "8000"
    environment:
      - LOG_LEVEL=INFO
```

## 📊 Monitoring & Observability

### Metrics
- Request count and rate limiting statistics
- Cache hit/miss ratios
- Active client count
- Error rates

### Logging
- Structured JSON logging
- Security event logging
- Performance metrics
- Error tracking

### Health Checks
- Service health (`/healthz`)
- Readiness checks (`/readyz`)
- Dependency health monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues**: Report bugs and request features via GitHub Issues
- **Documentation**: Check the `/docs` endpoint when running the service
- **Security**: Report security issues privately to security@example.com

## 🔄 Changelog

### v1.2.0 (Current)
- Enhanced security features
- Improved input validation
- Added comprehensive testing
- Better error handling and logging
- Caching and retry logic
- Rate limiting and CORS support
- Production-ready configuration

### v1.1.0
- Initial multi-vendor support
- Basic threat intelligence integration
- Docker support

### v1.0.0
- Initial release
- Basic webhook functionality
