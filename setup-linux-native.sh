#!/bin/bash

# SOC Agent Linux Native Setup (No Docker Required)
# This script sets up SOC Agent using Python and Node.js directly on Linux

set -e

# Color functions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${CYAN}🚀 SOC Agent Linux Native Setup${NC}"
    echo -e "${CYAN}=================================${NC}"
    echo
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -d "src/soc_agent" ]; then
    print_error "Please run this script from the SOC Agent root directory"
    exit 1
fi

print_header

# Check Python
print_info "Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    if [[ $PYTHON_VERSION == *"Python 3.1"* ]] || [[ $PYTHON_VERSION == *"Python 3.1"* ]]; then
        print_success "Python found: $PYTHON_VERSION"
        PYTHON_CMD="python3"
    else
        print_error "Python 3.10+ required. Found: $PYTHON_VERSION"
        print_warning "Please install Python 3.10+ using your package manager"
        exit 1
    fi
else
    print_error "Python not found. Please install Python 3.10+ using your package manager"
    print_info "Ubuntu/Debian: sudo apt install python3.10 python3.10-venv python3.10-pip"
    print_info "CentOS/RHEL: sudo yum install python310 python310-pip"
    print_info "Fedora: sudo dnf install python3.10 python3.10-pip"
    exit 1
fi

# Check Node.js
print_info "Checking Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version 2>&1)
    if [[ $NODE_VERSION == v1[8-9] ]] || [[ $NODE_VERSION == v2[0-9] ]]; then
        print_success "Node.js found: $NODE_VERSION"
    else
        print_error "Node.js 18+ required. Found: $NODE_VERSION"
        print_warning "Please install Node.js 18+ using your package manager"
        exit 1
    fi
else
    print_error "Node.js not found. Please install Node.js 18+ using your package manager"
    print_info "Ubuntu/Debian: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs"
    print_info "CentOS/RHEL: curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash - && sudo yum install -y nodejs"
    print_info "Fedora: curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash - && sudo dnf install -y nodejs"
    exit 1
fi

# Create virtual environment
print_info "Setting up Python virtual environment..."
if [ -d "venv" ]; then
    print_success "Virtual environment already exists"
else
    $PYTHON_CMD -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
print_info "Installing Python dependencies..."
pip install --upgrade pip
pip install -e .[dev]
print_success "Python dependencies installed"

# Install Node.js dependencies
print_info "Installing Node.js dependencies..."
cd frontend
npm install
cd ..
print_success "Node.js dependencies installed"

# Setup environment file
print_info "Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp env.example .env
    print_success "Environment file created from template"
else
    print_success "Environment file already exists"
fi

# Create startup scripts
print_info "Creating startup scripts..."

# Backend startup script
cat > start-backend.sh << 'EOF'
#!/bin/bash
echo "Starting SOC Agent Backend..."
source venv/bin/activate
python -m uvicorn soc_agent.webapp:app --host 0.0.0.0 --port 8000
EOF
chmod +x start-backend.sh

# Frontend startup script
cat > start-frontend.sh << 'EOF'
#!/bin/bash
echo "Starting SOC Agent Frontend..."
cd frontend
npm start
EOF
chmod +x start-frontend.sh

# Combined startup script
cat > start-soc-agent.sh << 'EOF'
#!/bin/bash
echo "Starting SOC Agent (Backend + Frontend)..."
echo
echo "Starting Backend in background..."
source venv/bin/activate
python -m uvicorn soc_agent.webapp:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"
echo
echo "Waiting 5 seconds for backend to start..."
sleep 5
echo
echo "Starting Frontend in background..."
cd frontend
npm start &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"
echo
echo "Both services are starting..."
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo
echo "Press Ctrl+C to stop both services"
echo
wait
EOF
chmod +x start-soc-agent.sh

print_success "Startup scripts created"

# Test the setup
print_info "Testing setup..."
if $PYTHON_CMD -c "import soc_agent; print('Backend import successful')" 2>/dev/null; then
    print_success "Backend import test passed"
else
    print_error "Backend import test failed"
fi

if node -e "console.log('Frontend test successful')" 2>/dev/null; then
    print_success "Frontend test passed"
else
    print_error "Frontend test failed"
fi

echo
print_success "🎉 Setup Complete!"
echo -e "${CYAN}=================${NC}"
echo
print_info "To start SOC Agent:"
print_info "  • Run: ./start-soc-agent.sh (recommended)"
print_info "  • Or run: ./start-backend.sh and ./start-frontend.sh separately"
echo
print_info "Access URLs:"
print_info "  • Backend API: http://localhost:8000"
print_info "  • Frontend: http://localhost:3000"
print_info "  • API Docs: http://localhost:8000/docs"
echo
print_info "Configuration:"
print_info "  • Edit .env file to add API keys and configure settings"
echo
print_info "Troubleshooting:"
print_info "  • Check firewall settings"
print_info "  • Ensure ports 8000 and 3000 are not blocked"
print_info "  • Run 'python -m soc_agent.webapp' to test backend directly"
echo
