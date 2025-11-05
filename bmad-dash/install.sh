#!/bin/bash
# BMAD Dashboard Installation Script
# Creates a virtual environment and installs dependencies

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

echo "=== BMAD Dashboard Installation ==="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Found Python $PYTHON_VERSION"

# Check if Python version is >= 3.10
if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "✓ Python version is compatible (>= 3.10)"
else
    echo "Warning: Python 3.10+ recommended, but will try to install anyway"
fi

# Create virtual environment
if [ -d "$VENV_DIR" ]; then
    echo "✓ Virtual environment already exists"
else
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --quiet --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install --quiet -r "$SCRIPT_DIR/requirements.txt"

echo ""
echo "✅ Installation complete!"
echo ""
echo "To use BMAD Dashboard:"
echo "  1. Activate the virtual environment:"
echo "     source $VENV_DIR/bin/activate"
echo ""
echo "  2. Run the dashboard:"
echo "     python bmad_dash.py --repos /path/to/repo"
echo ""
echo "  Or use the convenience script:"
echo "     ./run.sh --repos /path/to/repo"
echo ""
