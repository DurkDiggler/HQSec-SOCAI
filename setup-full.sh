#!/bin/bash

# SOC Agent Full Stack Setup Script
# This script sets up the complete SOC Agent with web interface

set -e

echo "🚀 Setting up SOC Agent Full Stack..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if Node.js is installed (for frontend development)
if ! command -v node &> /dev/null; then
    echo "⚠️  Node.js is not installed. Frontend development will not be available."
    echo "   Install Node.js 18+ for frontend development."
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data certs logs

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    
    # Generate random passwords
    POSTGRES_PASSWORD=$(openssl rand -base64 32)
    REDIS_PASSWORD=$(openssl rand -base64 32)
    
    # Update .env file with generated passwords
    sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" .env
    sed -i "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=$REDIS_PASSWORD/" .env
    
    echo "✅ .env file created with generated passwords"
    echo "⚠️  Please review and update the .env file with your configuration"
else
    echo "✅ .env file already exists"
fi

# Create database initialization script
echo "📝 Creating database initialization script..."
cat > init.sql << 'EOF'
-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS soc_agent;

-- Create user if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'soc_agent') THEN
        CREATE ROLE soc_agent LOGIN PASSWORD 'soc_agent_password';
    END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE soc_agent TO soc_agent;
EOF

# Create nginx configuration
echo "📝 Creating nginx configuration..."
cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream soc-agent {
        server soc-agent:8000;
    }
    
    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        server_name localhost;

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # API
        location /api/ {
            proxy_pass http://soc-agent;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket support (if needed)
        location /ws/ {
            proxy_pass http://soc-agent;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF

# Build and start services
echo "🔨 Building and starting services..."
docker-compose -f docker-compose.full.yml up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

# Check SOC Agent
if curl -f http://localhost:8000/healthz > /dev/null 2>&1; then
    echo "✅ SOC Agent backend is running"
else
    echo "❌ SOC Agent backend is not responding"
fi

# Check Frontend
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is running"
else
    echo "❌ Frontend is not responding"
fi

# Check Database
if docker-compose -f docker-compose.full.yml exec postgres pg_isready -U soc_agent > /dev/null 2>&1; then
    echo "✅ PostgreSQL database is running"
else
    echo "❌ PostgreSQL database is not responding"
fi

echo ""
echo "🎉 SOC Agent Full Stack is now running!"
echo ""
echo "📊 Access URLs:"
echo "   - Web Interface: http://localhost:3000"
echo "   - API Documentation: http://localhost:8000/docs"
echo "   - Health Check: http://localhost:8000/healthz"
echo "   - Mail Dev (if enabled): http://localhost:1080"
echo ""
echo "🔧 Management Commands:"
echo "   - View logs: docker-compose -f docker-compose.full.yml logs -f"
echo "   - Stop services: docker-compose -f docker-compose.full.yml down"
echo "   - Restart services: docker-compose -f docker-compose.full.yml restart"
echo "   - Update services: docker-compose -f docker-compose.full.yml up --build -d"
echo ""
echo "📝 Next Steps:"
echo "   1. Open http://localhost:3000 in your browser"
echo "   2. Configure your threat intelligence API keys in .env"
echo "   3. Set up your email and Autotask credentials"
echo "   4. Start sending webhook events to http://localhost:8000/webhook"
echo ""
echo "🆘 Troubleshooting:"
echo "   - Check logs: docker-compose -f docker-compose.full.yml logs [service-name]"
echo "   - Restart a service: docker-compose -f docker-compose.full.yml restart [service-name]"
echo "   - Rebuild: docker-compose -f docker-compose.full.yml up --build -d"
