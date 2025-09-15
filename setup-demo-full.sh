#!/bin/bash

# SOC Agent Demo Full Stack Setup Script
# This script sets up the complete SOC Agent with web interface for demo

set -e

echo "🚀 Setting up SOC Agent Demo Full Stack..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data certs logs

# Stop any existing services
echo "🛑 Stopping existing services..."
docker-compose -f docker-compose.full.yml down 2>/dev/null || true
pkill -f uvicorn 2>/dev/null || true

# Wait a moment
sleep 2

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
    echo "📋 Checking logs..."
    docker-compose -f docker-compose.full.yml logs soc-agent
fi

# Check Frontend
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is running"
else
    echo "❌ Frontend is not responding"
    echo "📋 Checking logs..."
    docker-compose -f docker-compose.full.yml logs frontend
fi

# Check MailDev
if curl -f http://localhost:1080 > /dev/null 2>&1; then
    echo "✅ MailDev is running"
else
    echo "❌ MailDev is not responding"
fi

echo ""
echo "🎉 SOC Agent Demo Full Stack setup complete!"
echo ""
echo "📊 Access URLs:"
echo "   - Web Interface: http://localhost:3000"
echo "   - API Documentation: http://localhost:8000/docs"
echo "   - Health Check: http://localhost:8000/healthz"
echo "   - Mail Dev: http://localhost:1080"
echo ""
echo "🔧 Management Commands:"
echo "   - View logs: docker-compose -f docker-compose.full.yml logs -f"
echo "   - Stop services: docker-compose -f docker-compose.full.yml down"
echo "   - Restart services: docker-compose -f docker-compose.full.yml restart"
echo ""
echo "🧪 Test Commands:"
echo "   - Test backend: ./test-demo.sh"
echo "   - Start backend only: ./start-demo.sh"
echo ""
