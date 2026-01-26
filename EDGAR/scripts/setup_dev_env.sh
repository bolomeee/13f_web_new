#!/bin/bash

# EDGAR Cleaner Development Environment Setup Script
# This script sets up the development environment for the EDGAR Cleaner project

set -e  # Exit on any error

echo "🚀 Setting up EDGAR Cleaner development environment..."

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

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
echo "⬆️ Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -e ".[dev,performance]"

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p output/{processed,logs,reports}
mkdir -p tests/test_data
mkdir -p config
mkdir -p temp

# Create default configuration files if they don't exist
echo "⚙️ Setting up configuration files..."
if [ ! -f "config/default.yaml" ]; then
    python -c "
import sys
sys.path.insert(0, 'src')
from edgar_cleaner.config import create_default_config
from pathlib import Path
create_default_config(Path('config'))
"
    echo "✅ Created default configuration files"
fi

# Copy environment template
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ Created .env file from template"
fi

# Set up pre-commit hooks
if command -v pre-commit &> /dev/null; then
    echo "🔗 Setting up pre-commit hooks..."
    pre-commit install
    echo "✅ Pre-commit hooks installed"
else
    echo "⚠️ pre-commit not found, skipping hook setup"
fi

# Run initial code quality checks
echo "🔍 Running initial code quality checks..."
echo "Running black..."
black --check src/ tests/ || echo "⚠️ Code formatting issues found. Run 'black src/ tests/' to fix."

echo "Running flake8..."
flake8 src/ tests/ || echo "⚠️ Code style issues found."

# Create sample test data symlink if original files exist
if [ -d "SEC_Filings" ] && [ ! -L "tests/test_data/sample_filings" ]; then
    echo "🔗 Creating test data symlink..."
    ln -s ../../SEC_Filings tests/test_data/sample_filings
    echo "✅ Test data symlink created"
fi

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run tests: pytest"
echo "3. Start development: edgar-cleaner --help"
echo "4. Edit configuration: config/default.yaml"
echo ""
echo "Happy coding! 🐍" 