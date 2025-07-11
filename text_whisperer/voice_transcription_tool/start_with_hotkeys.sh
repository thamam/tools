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

# Set environment variables for GUI access when using sudo
export DISPLAY="${DISPLAY:-:0}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u $USER)}"
export PULSE_RUNTIME_PATH="${PULSE_RUNTIME_PATH:-/run/user/$(id -u $USER)/pulse}"

# Get the real user (in case we're already running under sudo)
REAL_USER="${SUDO_USER:-$USER}"
export XAUTHORITY="/home/$REAL_USER/.Xauthority"

echo "🚀 Starting application with global hotkeys..."
cd "$SCRIPT_DIR"

# Run with sudo, preserving environment variables
sudo -E "$VENV_PYTHON" run.py

echo ""
echo "Application stopped."