#!/bin/bash

# SOC Agent - Linux One-Click Starter
# This script requires ONLY Docker and Docker Compose to be installed

set -e

# Color functions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${CYAN}========================================"
    echo -e "    SOC Agent - Linux Starter"
    echo -e "========================================${NC}"
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

print_header

# Check if Docker is running
print_info "Checking Docker..."
if ! docker version >/dev/null 2>&1; then
    print_error "Docker is not running or not installed"
    echo
    print_info "Please:"
    print_info "1. Install Docker and Docker Compose"
    print_info "2. Start Docker service: sudo systemctl start docker"
    print_info "3. Add your user to docker group: sudo usermod -aG docker \$USER"
    print_info "4. Log out and back in, then run this script again"
    echo
    print_warning "Alternative: Use the native setup (./setup-linux-native.sh)"
    echo
    exit 1
fi

print_success "Docker is running"

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the SOC Agent root directory"
    print_info "Make sure you've extracted all files first"
    exit 1
fi

print_success "SOC Agent files found"

echo
print_info "🚀 Starting SOC Agent..."
print_info "   This may take 2-3 minutes on first run"
echo

# Start the services
docker compose up --build

echo
print_success "🎉 SOC Agent is running!"
echo -e "${CYAN}=======================${NC}"
echo
print_info "Access URLs:"
print_info "  • Web Interface: http://localhost:3000"
print_info "  • Backend API: http://localhost:8000"
print_info "  • API Documentation: http://localhost:8000/docs"
echo
print_info "To stop: Press Ctrl+C"
print_info "To restart: Run this script again"
echo
