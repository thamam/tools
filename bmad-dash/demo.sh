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
echo "1. Health Check - Analyzing test repository..."
echo ""
python3 bmad_dash.py check --repos /home/ubuntu/test-bmad-repo
echo ""
echo "2. To launch interactive dashboard, run:"
echo "   ./run.sh --repos /home/ubuntu/test-bmad-repo"
echo ""
echo "   Or manually:"
echo "   source venv/bin/activate"
echo "   python3 bmad_dash.py --repos /home/ubuntu/test-bmad-repo"
echo ""
echo "   Keyboard shortcuts:"
echo "   - Arrow keys: Navigate stories"
echo "   - Enter: View story details"
echo "   - s: Show valid state transitions"
echo "   - o: Show command to open PRD"
echo "   - l: Show command to tail logs"
echo "   - r: Refresh dashboard"
echo "   - q: Quit"
