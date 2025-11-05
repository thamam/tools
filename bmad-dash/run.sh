#!/bin/bash
# BMAD Dashboard Runner Script
# Automatically activates virtual environment and runs the dashboard

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found. Please run ./install.sh first"
    exit 1
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Run the dashboard with all arguments passed through
python "$SCRIPT_DIR/bmad_dash.py" "$@"
