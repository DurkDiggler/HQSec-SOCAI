#!/bin/bash

# SOC Agent Demo Startup Script
echo "🚀 Starting SOC Agent Demo..."

# Kill any existing processes
echo "Cleaning up existing processes..."
pkill -f uvicorn 2>/dev/null || true

# Wait a moment
sleep 2

# Check if port 8000 is free
if lsof -i :8000 >/dev/null 2>&1; then
    echo "❌ Port 8000 is still in use. Please check what's using it:"
    lsof -i :8000
    exit 1
fi

# Activate virtual environment and start service
echo "Starting SOC Agent service..."
cd "/home/durkdiggler/HQSec - SOCAI"
source venv/bin/activate

# Start the service in background
uvicorn soc_agent.webapp:app --host 0.0.0.0 --port 8000 &
SERVICE_PID=$!

# Wait for service to start
echo "Waiting for service to start..."
sleep 5

# Test the service
echo "Testing service health..."
if curl -s http://localhost:8000/healthz >/dev/null; then
    echo "✅ SOC Agent is running successfully!"
    echo "🌐 Service URL: http://localhost:8000"
    echo "🔍 Health Check: http://localhost:8000/healthz"
    echo "📚 API Docs: http://localhost:8000/docs"
    echo ""
    echo "📋 Demo Commands:"
    echo "curl http://localhost:8000/healthz"
    echo "curl http://localhost:8000/"
    echo "curl http://localhost:8000/readyz"
    echo ""
    echo "🛑 To stop the service: kill $SERVICE_PID"
    echo "   Or run: pkill -f uvicorn"
else
    echo "❌ Service failed to start. Check the logs above."
    kill $SERVICE_PID 2>/dev/null || true
    exit 1
fi
