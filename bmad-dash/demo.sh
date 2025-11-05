#!/bin/bash
# Demo script for BMAD Dashboard

echo "=== BMAD Dashboard Demo ==="
echo ""
echo "1. Health Check - Analyzing test repository..."
echo ""
python3 bmad_dash.py check --repos /home/ubuntu/test-bmad-repo
echo ""
echo "2. To launch interactive dashboard, run:"
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
