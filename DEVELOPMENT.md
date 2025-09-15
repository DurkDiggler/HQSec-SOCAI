# Development Guide

## Prerequisites

- Python 3.10 or higher
- pip (Python package installer)
- Git

## Quick Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/SOCAI.git
cd SOCAI
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### 3. Install Dependencies
```bash
# Install the package in development mode
pip install -e .

# Or install with development dependencies
pip install -e .[dev]
```

### 4. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit the configuration
nano .env  # or use your preferred editor
```

### 5. Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=soc_agent --cov-report=html

# Run specific test categories
pytest tests/test_security.py -v
pytest tests/test_integration.py -v
pytest tests/test_models.py -v
```

### 6. Start Development Server
```bash
# Start the FastAPI development server
uvicorn soc_agent.webapp:app --host 0.0.0.0 --port 8000 --reload

# Or use the make command
make run
```

## Development Workflow

### 1. Code Quality
```bash
# Format code
ruff format

# Check code quality
ruff check

# Fix auto-fixable issues
ruff check --fix

# Or use the make command
make fmt
```

### 2. Testing
```bash
# Run tests before committing
pytest

# Run tests with coverage
pytest --cov=soc_agent --cov-report=term-missing

# Run specific tests
pytest tests/test_security.py::test_rate_limiting -v
```

### 3. Docker Development
```bash
# Build and run with Docker Compose
docker compose up --build

# Run tests in Docker
make test docker=1

# Stop services
docker compose down
```

## Project Structure

```
SOCAI/
├── src/
│   └── soc_agent/
│       ├── __init__.py
│       ├── adapters/          # Vendor-specific adapters
│       ├── intel/             # Threat intelligence providers
│       ├── config.py          # Configuration management
│       ├── models.py          # Pydantic data models
│       ├── webapp.py          # FastAPI application
│       ├── analyzer.py        # Event analysis and scoring
│       ├── security.py        # Security utilities
│       ├── logging.py         # Logging configuration
│       ├── notifiers.py       # Email notifications
│       └── autotask.py        # Autotask integration
├── tests/                     # Test suite
├── scripts/                   # Utility scripts
├── docker-compose.yml         # Docker Compose configuration
├── Dockerfile                 # Docker image definition
├── pyproject.toml            # Project configuration
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore               # Git ignore rules
├── Makefile                 # Development commands
└── README.md                # Project documentation
```

## Environment Variables

### Required for Production
- `SMTP_HOST`: SMTP server for email notifications
- `EMAIL_FROM`: Sender email address
- `EMAIL_TO`: Comma-separated recipient emails

### Optional but Recommended
- `OTX_API_KEY`: AlienVault OTX API key
- `VT_API_KEY`: VirusTotal API key
- `ABUSEIPDB_API_KEY`: AbuseIPDB API key
- `AT_BASE_URL`: Autotask base URL
- `AT_API_INTEGRATION_CODE`: Autotask integration code
- `AT_USERNAME`: Autotask username
- `AT_SECRET`: Autotask secret
- `AT_ACCOUNT_ID`: Autotask account ID
- `AT_QUEUE_ID`: Autotask queue ID

### Security
- `WEBHOOK_SHARED_SECRET`: Webhook authentication secret
- `WEBHOOK_HMAC_SECRET`: HMAC signature secret
- `RATE_LIMIT_REQUESTS`: Rate limit per window (default: 100)
- `RATE_LIMIT_WINDOW`: Rate limit window in seconds (default: 3600)

## Testing

### Test Categories
- **Security Tests**: Input validation, authentication, rate limiting
- **Integration Tests**: End-to-end webhook processing
- **Model Tests**: Data validation and constraints
- **Adapter Tests**: Vendor-specific event normalization
- **Analyzer Tests**: IOC extraction and scoring

### Running Tests
```bash
# All tests
pytest

# Specific category
pytest tests/test_security.py

# With coverage
pytest --cov=soc_agent --cov-report=html

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

## Code Style

### Formatting
- Use `ruff` for code formatting and linting
- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write comprehensive docstrings

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## Debugging

### Enable Debug Logging
```bash
# Set debug level
export LOG_LEVEL=DEBUG

# Start server
uvicorn soc_agent.webapp:app --host 0.0.0.0 --port 8000 --reload
```

### Common Issues

1. **Import Errors**: Make sure you're in the virtual environment
2. **Configuration Errors**: Check your `.env` file
3. **Test Failures**: Ensure all dependencies are installed
4. **Docker Issues**: Check Docker daemon is running

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `pytest`
6. Format code: `ruff format`
7. Commit changes: `git commit -m "Add your feature"`
8. Push to branch: `git push origin feature/your-feature`
9. Create a Pull Request

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release tag: `git tag v1.2.0`
4. Push tags: `git push --tags`
5. Create GitHub release

## Troubleshooting

### Virtual Environment Issues
```bash
# Recreate virtual environment
rm -rf venv/
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### Docker Issues
```bash
# Clean Docker cache
docker system prune -a

# Rebuild from scratch
docker compose build --no-cache
```

### Test Issues
```bash
# Clear pytest cache
rm -rf .pytest_cache/

# Run tests with verbose output
pytest -v --tb=short
```

## Performance Testing

### Load Testing
```bash
# Install locust
pip install locust

# Run load tests
locust -f tests/load_test.py --host=http://localhost:8000
```

### Memory Profiling
```bash
# Install memory profiler
pip install memory-profiler

# Profile memory usage
python -m memory_profiler src/soc_agent/webapp.py
```

## Security Testing

### Security Scan
```bash
# Install safety
pip install safety

# Check for known vulnerabilities
safety check

# Install bandit
pip install bandit

# Run security linter
bandit -r src/
```

## Monitoring

### Health Checks
```bash
# Check service health
curl http://localhost:8000/healthz

# Check readiness
curl http://localhost:8000/readyz

# Get metrics
curl http://localhost:8000/metrics
```

### Logs
```bash
# View logs in real-time
tail -f logs/soc-agent.log

# Filter security events
grep "SECURITY" logs/soc-agent.log
```
