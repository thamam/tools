#!/bin/bash
# Simple run script without sudo (hotkeys won't work)

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "🎤 Voice Transcription Tool (No Hotkeys Mode)"
echo "==========================================="
echo "ℹ️  Running without sudo - global hotkeys disabled"
echo "   Use the GUI buttons to start/stop recording"
echo ""

cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -f "../.venv/bin/activate" ]; then
    source "../.venv/bin/activate"
elif [ -f ".venv/bin/activate" ]; then
    source ".venv/bin/activate"
fi

# Run the application
python main.py