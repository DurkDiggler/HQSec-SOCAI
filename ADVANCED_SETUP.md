# Advanced Setup Guide

This guide covers advanced deployment options, manual installation, and platform-specific configurations.

## 🐳 Docker Compose Profiles

### Backend Only
```bash
# Run only backend services
docker compose up --build soc-agent postgres redis maildev
```

### Frontend Only
```bash
# Run only frontend (requires backend running)
docker compose up --build frontend nginx
```

### Development Mode
```bash
# Run with development overrides
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

## 🪟 Windows Advanced Setup

### PowerShell Scripts
```powershell
# Backend only setup
.\setup-windows.ps1

# Full stack setup
.\setup-windows-full.ps1

# Test deployment
.\demo-windows-full.ps1
```

### Batch Files
```cmd
# Backend only
setup-windows.bat

# Full stack
setup-windows-full.bat
```

### Windows Prerequisites
- **Docker Desktop** for Windows
- **PowerShell 5.1+** or **PowerShell Core 7+**
- **Node.js 18+** (for full-stack)
- **Git** for cloning

## 🐧 Linux Advanced Setup

### Bash Scripts
```bash
# Full stack setup
./setup-full.sh

# Test deployment
./test-full-stack.sh
```

### Manual Installation
```bash
# Install dependencies
pip install -e .[dev]

# Configure environment
cp env.example .env
# Edit .env with your configuration

# Run the service
uvicorn soc_agent.webapp:app --host 0.0.0.0 --port 8000
```

## 🍎 macOS Advanced Setup

### Homebrew Installation
```bash
# Install dependencies
brew install python@3.10 node@18 docker

# Clone and setup
git clone https://github.com/DurkDiggler/HQSec-SOCAI.git
cd HQSec-SOCAI
cp env.example .env

# Run with Docker
docker compose up --build
```

## 🔧 Environment Configuration

### Database Options
```bash
# SQLite (default)
DATABASE_URL=sqlite:///./soc_agent.db

# PostgreSQL (recommended for production)
DATABASE_URL=postgresql://soc_agent:soc_agent_password@postgres:5432/soc_agent
```

### Caching Options
```bash
# Redis (default)
REDIS_URL=redis://redis:6379

# Disable caching
ENABLE_CACHING=false
```

### Logging Options
```bash
# JSON logging (default)
LOG_FORMAT=json

# Text logging
LOG_FORMAT=text

# Log level
LOG_LEVEL=INFO
```

## 🚀 Production Deployment

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: soc-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: soc-agent
  template:
    metadata:
      labels:
        app: soc-agent
    spec:
      containers:
      - name: soc-agent
        image: soc-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://soc_agent:password@postgres:5432/soc_agent"
```

### Docker Swarm
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml soc-agent
```

### AWS ECS
```json
{
  "family": "soc-agent",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "soc-agent",
      "image": "soc-agent:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ]
    }
  ]
}
```

## 🔒 Security Hardening

### TLS Configuration
```bash
# Generate certificates
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Configure nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;
}
```

### Authentication
```bash
# Enable webhook authentication
WEBHOOK_SHARED_SECRET=your-secure-secret
WEBHOOK_HMAC_SECRET=your-hmac-secret
WEBHOOK_HMAC_HEADER=X-Signature
```

### Network Security
```bash
# Restrict CORS origins
CORS_ORIGINS=["https://yourdomain.com"]

# Enable rate limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
```

## 📊 Monitoring & Observability

### Prometheus Metrics
```bash
# Enable metrics
ENABLE_METRICS=true
METRICS_PORT=9090
```

### Log Aggregation
```bash
# Structured logging
LOG_FORMAT=json
LOG_LEVEL=INFO
```

### Health Checks
```bash
# Custom health check timeout
HEALTH_CHECK_TIMEOUT=5.0
```

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=soc_agent --cov-report=html

# Run specific test file
pytest tests/test_security.py -v
```

### Integration Tests
```bash
# Test with Docker
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Test API endpoints
pytest tests/test_integration.py -v
```

### Load Testing
```bash
# Install locust
pip install locust

# Run load tests
locust -f tests/load_test.py --host=http://localhost:8000
```

## 🔧 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   lsof -i :8000
   
   # Kill the process
   kill -9 <PID>
   ```

2. **Docker Build Fails**
   ```bash
   # Clean Docker cache
   docker system prune -a
   
   # Rebuild without cache
   docker compose build --no-cache
   ```

3. **Database Connection Issues**
   ```bash
   # Check database logs
   docker compose logs postgres
   
   # Test connection
   docker compose exec postgres psql -U soc_agent -d soc_agent
   ```

4. **Frontend Not Loading**
   ```bash
   # Check frontend logs
   docker compose logs frontend
   
   # Rebuild frontend
   docker compose build frontend
   ```

### Debug Mode
```bash
# Enable debug logging
LOG_LEVEL=DEBUG

# Run with debugger
python -m pdb -m uvicorn soc_agent.webapp:app --host 0.0.0.0 --port 8000
```

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Health Check**: http://localhost:8000/healthz
- **Metrics**: http://localhost:8000/metrics
- **Email Testing**: http://localhost:1080
