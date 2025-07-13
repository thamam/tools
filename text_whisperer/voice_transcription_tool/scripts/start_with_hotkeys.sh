#!/bin/bash

# Voice Transcription Tool - Start with Global Hotkeys
# This script starts the application with sudo for global hotkey support

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="/home/thh3/personal/tools/text_whisperer/.venv/bin/python"

echo "🔥 Starting Voice Transcription Tool with Global Hotkeys..."
echo ""
echo "ℹ️  This requires sudo permissions for global hotkey registration"
echo "   Global hotkeys: Alt+D (record), Alt+S (settings), Alt+W (wake word)"
echo ""

# Check if already running
if pgrep -f "voice_transcription_tool/run.py" > /dev/null; then
    echo "⚠️  Voice Transcription Tool is already running!"
    echo "   Stop it first with: ./stop_background_process.sh"
    exit 1
fi

# Get current user info
CURRENT_USER="$(whoami)"
USER_ID="$(id -u)"

# Copy X11 authentication to a temporary location accessible by root
TEMP_XAUTH="/tmp/.voice_transcription_xauth"
rm -f "$TEMP_XAUTH"
touch "$TEMP_XAUTH"
xauth nlist "$DISPLAY" | xauth -f "$TEMP_XAUTH" nmerge -

echo "🚀 Starting application with global hotkeys..."
cd "$SCRIPT_DIR"

# Run with sudo, setting proper environment
sudo -E \
    DISPLAY="$DISPLAY" \
    XAUTHORITY="$TEMP_XAUTH" \
    XDG_RUNTIME_DIR="/run/user/$USER_ID" \
    PULSE_RUNTIME_PATH="/run/user/$USER_ID/pulse" \
    HOME="/home/$CURRENT_USER" \
    USER="$CURRENT_USER" \
    "$VENV_PYTHON" run.py

# Clean up
rm -f "$TEMP_XAUTH"

echo ""
echo "Application stopped."