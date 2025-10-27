#!/bin/bash
#
# Launch BMAD Dashboard Helper
# Opens the dashboard in a new terminal window
#

DASHBOARD_PATH="$HOME/.config/claude-code/apps/bmad-dashboard.py"

# Check if dashboard exists
if [ ! -f "$DASHBOARD_PATH" ]; then
    echo "Error: Dashboard not found at $DASHBOARD_PATH"
    exit 1
elif [ ! -x "$DASHBOARD_PATH" ]; then
    echo "Error: Dashboard is not executable. Run: chmod +x $DASHBOARD_PATH"
    exit 1
fi

# Detect terminal emulator and launch
if command -v gnome-terminal &> /dev/null; then
    gnome-terminal -- bash -c "'$DASHBOARD_PATH'; read -p 'Press Enter to close...'"
elif command -v xterm &> /dev/null; then
    xterm -e "'$DASHBOARD_PATH'" &
elif command -v konsole &> /dev/null; then
    konsole -e "'$DASHBOARD_PATH'" &
elif command -v alacritty &> /dev/null; then
    alacritty -e "$DASHBOARD_PATH" &
elif command -v kitty &> /dev/null; then
    kitty "$DASHBOARD_PATH" &
else
    echo "No supported terminal emulator found."
    echo "Running dashboard in current terminal..."
    "$DASHBOARD_PATH"
fi
