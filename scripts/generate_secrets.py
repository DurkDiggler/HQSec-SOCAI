#!/usr/bin/env python3
"""Generate secure secrets for SOC Agent configuration."""

import secrets
import string
import os
from pathlib import Path

def generate_jwt_secret(length: int = 64) -> str:
    """Generate a secure JWT secret key."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_webhook_secret(length: int = 32) -> str:
    """Generate a webhook secret."""
    return secrets.token_urlsafe(length)

def generate_database_password(length: int = 24) -> str:
    """Generate a database password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_redis_password(length: int = 16) -> str:
    """Generate a Redis password."""
    return secrets.token_urlsafe(length)

def main():
    """Generate secure configuration values."""
    print("🔐 Generating secure configuration values...")
    
    # Generate secrets
    jwt_secret = generate_jwt_secret()
    webhook_shared_secret = generate_webhook_secret()
    webhook_hmac_secret = generate_webhook_secret()
    postgres_password = generate_database_password()
    redis_password = generate_redis_password()
    
    # Create .env file with secure values
    from datetime import datetime
    env_content = f"""# SOC Agent Configuration - Generated with secure values
# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Server Configuration
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
LOG_FORMAT=json

# Security Settings
MAX_REQUEST_SIZE=1048576
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=3600
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001","http://localhost:80","http://localhost"]

# Webhook Authentication (SECURE VALUES GENERATED)
WEBHOOK_SHARED_SECRET={webhook_shared_secret}
WEBHOOK_HMAC_SECRET={webhook_hmac_secret}
WEBHOOK_HMAC_HEADER=X-Signature
WEBHOOK_HMAC_PREFIX=sha256=

# Database Configuration
DATABASE_URL=sqlite:///./soc_agent.db

# PostgreSQL Configuration (SECURE VALUES GENERATED)
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=soc_agent
POSTGRES_PASSWORD={postgres_password}
POSTGRES_DB=soc_agent

# Redis Configuration (SECURE VALUES GENERATED)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD={redis_password}
REDIS_DB=0

# JWT Configuration (SECURE VALUES GENERATED)
JWT_SECRET_KEY={jwt_secret}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# OAuth 2.0 / OpenID Connect Configuration
OAUTH_ENABLED=true
OAUTH_PROVIDER=google
OAUTH_CLIENT_ID=your-oauth-client-id
OAUTH_CLIENT_SECRET=your-oauth-client-secret
OAUTH_REDIRECT_URI=http://localhost:3000/auth/callback
OAUTH_SCOPE=openid email profile

# MFA Configuration
MFA_ENABLED=true
MFA_ISSUER_NAME=SOC Agent
MFA_BACKUP_CODES_COUNT=10

# RBAC Configuration
RBAC_ENABLED=true
DEFAULT_USER_ROLE=analyst

# Email Configuration
ENABLE_EMAIL=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=soc-agent@yourcompany.com
EMAIL_TO=["soc@yourcompany.com"]

# Threat Intelligence APIs
OTX_API_KEY=your-otx-api-key
VT_API_KEY=your-virustotal-api-key
ABUSEIPDB_API_KEY=your-abuseipdb-api-key

# AI Integration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.1
ENABLE_AI_ANALYSIS=true

# Performance Settings
ENABLE_CACHING=true
ENABLE_METRICS=true
HTTP_TIMEOUT=8.0
IOC_CACHE_TTL=1800
MAX_RETRIES=3
RETRY_DELAY=1.0

# Real-time Capabilities
ENABLE_REALTIME=true
WEBSOCKET_PING_INTERVAL=30
WEBSOCKET_PING_TIMEOUT=10
MAX_WEBSOCKET_CONNECTIONS=100
SSE_KEEPALIVE_INTERVAL=30
ALERT_STREAM_BUFFER_SIZE=1000

# MCP Servers
KALI_MCP_URL=http://localhost:5000
VULN_SCANNER_URL=http://localhost:5001
MCP_TIMEOUT=30
ENABLE_OFFENSIVE_TESTING=true
"""
    
    # Write to .env file
    env_file = Path(".env")
    with open(env_file, "w") as f:
        f.write(env_content)
    
    print(f"✅ Generated secure .env file with:")
    print(f"   - JWT Secret: {jwt_secret[:8]}...")
    print(f"   - Webhook Shared Secret: {webhook_shared_secret[:8]}...")
    print(f"   - Webhook HMAC Secret: {webhook_hmac_secret[:8]}...")
    print(f"   - PostgreSQL Password: {postgres_password[:8]}...")
    print(f"   - Redis Password: {redis_password[:8]}...")
    print(f"\n🔒 IMPORTANT: Keep these secrets secure and never commit them to version control!")

if __name__ == "__main__":
    main()
