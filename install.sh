#!/bin/bash
set -e

# Heidi CLI One-Click Installer for Linux/macOS
# Uses pipx for global installation so heidi is available from any directory

echo "Heidi CLI Installer (pipx mode)"
echo "================================"

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "Python is not installed. Please install Python 3.10+ first."
    exit 1
fi

# Determine Python command
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "Found Python: $PYTHON_CMD"

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "Python $PYTHON_VERSION is too old. Please install Python 3.10 or later."
    exit 1
fi

echo "Python version: $PYTHON_VERSION"

# Check if pipx is installed
if ! command -v pipx &> /dev/null; then
    echo ""
    echo "Installing pipx..."
    $PYTHON_CMD -m pip install --user pipx
    pipx ensurepath
    export PATH="$HOME/.local/bin:$PATH"
fi

echo ""
echo "Installing Heidi CLI globally via pipx..."
pipx install git+https://github.com/heidi-dang/heidi-cli.git

echo ""
echo "Building UI into cache..."
heidi ui build

echo ""
echo "================================"
echo "Heidi CLI installed successfully!"
echo ""
echo "Usage from any directory:"
echo "  heidi --help"
echo "  heidi serve --ui"
echo ""
