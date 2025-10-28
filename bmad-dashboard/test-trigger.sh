#!/bin/bash
#
# BMAD Dashboard Trigger Test Utility
# Tests the dashboard refresh mechanism by manually triggering an update
#

# Use cross-platform temporary directory
TMPDIR="${TMPDIR:-/tmp}"
TRIGGER_FILE="${TMPDIR}/bmad-dashboard-trigger"

echo "=========================================="
echo "BMAD Dashboard Trigger Test"
echo "=========================================="
echo ""
echo "Trigger file: $TRIGGER_FILE"
echo "Current time: $(date)"
echo ""

# Check if trigger file exists
if [ -f "$TRIGGER_FILE" ]; then
    OLD_TIME=$(stat -c %y "$TRIGGER_FILE" 2>/dev/null || stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$TRIGGER_FILE")
    echo "Trigger file exists"
    echo "Last modified: $OLD_TIME"
else
    echo "Trigger file does not exist (will be created)"
fi

echo ""
echo "Touching trigger file..."
touch "$TRIGGER_FILE"

if [ $? -eq 0 ]; then
    NEW_TIME=$(stat -c %y "$TRIGGER_FILE" 2>/dev/null || stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$TRIGGER_FILE")
    echo "✅ SUCCESS: Trigger file touched"
    echo "New modified time: $NEW_TIME"
    echo ""
    echo "If the dashboard is running, it should refresh within 1-2 seconds."
else
    echo "❌ ERROR: Failed to touch trigger file"
    exit 1
fi

echo ""
echo "=========================================="
echo "Checking hook log..."
echo "=========================================="

LOG_FILE="${TMPDIR}/bmad-dashboard.log"
if [ -f "$LOG_FILE" ]; then
    echo ""
    echo "Last 5 hook triggers:"
    tail -5 "$LOG_FILE"
else
    echo ""
    echo "No hook log found at: $LOG_FILE"
    echo "(Hook logs only appear when BMAD commands are run via Claude Code)"
fi

echo ""
echo "=========================================="
echo "Test complete!"
echo "=========================================="
