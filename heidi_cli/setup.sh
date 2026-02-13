#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "========================================"
echo "Heidi CLI Setup Script"
echo "========================================"

# Detect OS
OS="$(uname -s)"
if [[ "$OS" == "Darwin" ]]; then
    PYTHON_CMD="python3"
elif [[ "$OS" == "Linux" ]]; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

# Check Python version
echo "[1/5] Checking Python..."
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "Error: Python not found. Please install Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "  Found Python $PYTHON_VERSION"

# Create virtual environment
echo "[2/5] Creating virtual environment..."
if [ -d "$VENV_DIR" ]; then
    echo "  Virtual environment already exists, skipping..."
else
    $PYTHON_CMD -m venv "$VENV_DIR"
    echo "  Created .venv/"
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "[3/5] Installing dependencies..."
pip install --upgrade pip -q

# Install heidi-cli in editable mode
pip install -e ".[dev]" -q

# Check if heidi is available
if ! command -v heidi &> /dev/null; then
    echo "Error: heidi command not found after installation"
    exit 1
fi

echo "  Installed heidi-cli"

# Initialize heidi
echo "[4/5] Initializing Heidi CLI..."
heidi init

# Show version and help
echo "[5/5] Setup complete!"
echo ""
echo "========================================"
echo "Heidi CLI Ready!"
echo "========================================"
echo ""
echo "Available commands:"
echo ""
heidi --help | sed 's/^/  /'
echo ""
echo "Quick start:"
echo "  heidi doctor              # Check system health"
echo "  heidi auth gh            # Authenticate with GitHub"
echo "  heidi agents list        # List available agents"
echo "  heidi loop 'your task'   # Run agent loop"
echo "  heidi serve              # Start HTTP server (port 7777)"
echo ""
echo "For more info: heidi --help"
echo ""

# Ask to start server
read -p "Start Heidi server now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting Heidi server on http://localhost:7777"
    echo "Press Ctrl+C to stop"
    heidi serve
fi
