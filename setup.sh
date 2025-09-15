#!/bin/bash

# SOC Agent Setup Script
# This script sets up the development environment for SOC Agent

set -e

echo "🚀 Setting up SOC Agent development environment..."

# Check if Python 3.10+ is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $PYTHON_VERSION is installed, but Python $REQUIRED_VERSION or higher is required."
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install the package in development mode
echo "📥 Installing SOC Agent in development mode..."
pip install -e .

# Install development dependencies
echo "📥 Installing development dependencies..."
pip install -e .[dev]

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration"
else
    echo "✅ .env file already exists"
fi

# Run tests to verify installation
echo "🧪 Running tests to verify installation..."
python -m pytest tests/ -v --tb=short

echo ""
echo "🎉 Setup complete! SOC Agent is ready for development."
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Start development server: uvicorn soc_agent.webapp:app --reload"
echo "4. Or use Docker: docker compose up --build"
echo ""
echo "For more information, see:"
echo "- README.md for general usage"
echo "- DEVELOPMENT.md for development workflow"
echo "- IMPROVEMENTS.md for detailed changes"
