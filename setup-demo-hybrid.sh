y
#!/bin/bash

# SOC Agent Demo Hybrid Setup Script
# This script sets up the SOC Agent backend + optional frontend for demo

set -e

echo "🚀 Setting up SOC Agent Demo (Hybrid Approach)..."

# Stop any existing services
echo "🛑 Stopping existing services..."
pkill -f uvicorn 2>/dev/null || true
docker stop maildev 2>/dev/null || true

# Wait a moment
sleep 2

# Start MailDev for email testing
echo "📧 Starting MailDev for email testing..."
docker run -d --name maildev -p 1080:1080 -p 1025:1025 maildev/maildev:latest 2>/dev/null || true

# Start SOC Agent backend
echo "🔧 Starting SOC Agent backend..."
cd "/home/durkdiggler/HQSec - SOCAI"
source venv/bin/activate

# Start the service in background
uvicorn soc_agent.webapp:app --host 0.0.0.0 --port 8000 &
SERVICE_PID=$!

# Wait for service to start
echo "⏳ Waiting for SOC Agent to start..."
sleep 5

# Test the service
echo "🔍 Testing SOC Agent..."
if curl -s http://localhost:8000/healthz >/dev/null; then
    echo "✅ SOC Agent backend is running successfully!"
else
    echo "❌ SOC Agent backend failed to start"
    echo "📋 Checking logs..."
    ps aux | grep uvicorn
    exit 1
fi

# Check MailDev
if curl -s http://localhost:1080 >/dev/null; then
    echo "✅ MailDev is running"
else
    echo "❌ MailDev is not responding"
fi

# Optional: Start frontend if available
if [ -d "frontend" ] && command -v node &> /dev/null; then
    echo "🌐 Starting frontend..."
    cd frontend
    if [ ! -d "node_modules" ]; then
        echo "📦 Installing frontend dependencies..."
        npm install
    fi
    npm start &
    FRONTEND_PID=$!
    cd ..
    
    # Wait for frontend
    sleep 10
    if curl -s http://localhost:3000 >/dev/null; then
        echo "✅ Frontend is running"
    else
        echo "❌ Frontend is not responding"
    fi
else
    echo "⚠️  Frontend not available (Node.js not installed or frontend directory missing)"
fi

echo ""
echo "🎉 SOC Agent Demo is now running!"
echo ""
echo "📊 Access URLs:"
echo "   - SOC Agent API: http://localhost:8000"
echo "   - Health Check: http://localhost:8000/healthz"
echo "   - API Documentation: http://localhost:8000/docs"
echo "   - Mail Dev: http://localhost:1080"
if [ -d "frontend" ] && command -v node &> /dev/null; then
    echo "   - Web Interface: http://localhost:3000"
fi
echo ""
echo "🧪 Test Commands:"
echo "   - Test everything: ./test-demo.sh"
echo "   - Test webhook: curl -X POST http://localhost:8000/webhook -H 'Content-Type: application/json' -d '{\"source\": \"test\", \"event_type\": \"test_event\", \"severity\": 5}'"
echo ""
echo "🛑 To stop services:"
echo "   - Backend: kill $SERVICE_PID"
echo "   - MailDev: docker stop maildev"
if [ -d "frontend" ] && command -v node &> /dev/null; then
    echo "   - Frontend: kill $FRONTEND_PID"
fi
echo "   - Or run: pkill -f uvicorn && docker stop maildev"
echo ""
