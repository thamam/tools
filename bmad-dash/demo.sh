#!/bin/bash
# Demo script for BMAD Dashboard

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# Check if virtual environment exists and activate it
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
fi

echo "=== BMAD Dashboard Demo ==="
echo ""
echo "This demo requires a BMAD project repository."
echo ""
echo "Usage:"
echo "  ./demo.sh /path/to/your/bmad/project"
echo ""

if [ -z "$1" ]; then
    echo "Error: Please provide a path to a BMAD project repository."
    echo ""
    echo "Example:"
    echo "  ./demo.sh ~/projects/my-bmad-project"
    exit 1
fi

REPO_PATH="$1"

if [ ! -d "$REPO_PATH" ]; then
    echo "Error: Directory '$REPO_PATH' does not exist."
    exit 1
fi

echo "1. Health Check - Analyzing repository..."
echo ""
python3 bmad_dash_v2.py check --repos "$REPO_PATH"

echo ""
echo "2. To launch interactive dashboard, run:"
echo "   ./dashboard.sh --repos $REPO_PATH"
echo ""
echo "   Keyboard shortcuts:"
echo "   - 0: Product Vision (strategic goals)"
echo "   - 1: Overview (roadmap + summary)"
echo "   - 2: Summary (metrics)"
echo "   - 3: Distribution (story states)"
echo "   - 4: Epics (epic breakdown)"
echo "   - 5: Risks (attention items)"
echo "   - 6: Tree (full structure with 'you are here')"
echo "   - r: Refresh dashboard"
echo "   - q: Quit"
echo ""
