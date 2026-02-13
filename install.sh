#!/bin/bash
set -e

# Heidi CLI One-Click Installer for Linux/macOS
# Clones repo and installs in editable mode with venv

echo "Heidi CLI Installer"
echo "===================="

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

# Create temp directory
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Clone repo
echo "Cloning heidi-cli..."
git clone https://github.com/heidi-dang/heidi-cli.git
cd heidi-cli/heidi_cli

# Create virtual environment
echo "Creating virtual environment..."
$PYTHON_CMD -m venv .venv
source .venv/bin/activate

# Upgrade pip
echo "Installing dependencies..."
pip install --upgrade pip -q

# Install in editable mode
pip install -e ".[dev]" -q

echo ""
echo "Heidi CLI installed successfully!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "Then run:"
echo "  heidi init"
echo "  heidi --help"
