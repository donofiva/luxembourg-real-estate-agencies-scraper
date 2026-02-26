#!/bin/bash

# Setup script for Luxembourg Real Estate Agencies Scraper

echo "🏠 Luxembourg Real Estate Agencies Scraper - Setup"
echo "=================================================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv .venv

if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi
echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo "✓ Dependencies installed"
echo ""

# Install Playwright browsers
echo "🌐 Installing Playwright browser..."
playwright install chromium

if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Playwright browser installation failed. You may need to install manually."
else
    echo "✓ Playwright browser installed"
fi
echo ""

echo "✅ Setup complete!"
echo ""
echo "To start using the scraper:"
echo "  1. Activate the virtual environment:"
echo "     source .venv/bin/activate"
echo "  2. Run the scraper:"
echo "     python main.py"
echo ""
echo "Happy scraping! 🚀"
