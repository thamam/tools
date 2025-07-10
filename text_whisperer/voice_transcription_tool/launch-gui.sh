#!/bin/bash
# GUI launcher for Voice Transcription Tool with PolicyKit

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create a temporary script that pkexec will run
cat > /tmp/voice_transcription_launcher.sh << 'EOF'
#!/bin/bash
# This script runs with elevated privileges

# Get the original user info
ORIGINAL_USER="${PKEXEC_UID:-$(id -u)}"
ORIGINAL_HOME=$(getent passwd $(id -un $ORIGINAL_USER) | cut -d: -f6)

# Set up environment
export HOME="$ORIGINAL_HOME"
export USER=$(id -un $ORIGINAL_USER)
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$ORIGINAL_HOME/.Xauthority}"

# Change to script directory (passed as argument)
cd "$1"

# Activate virtual environment if it exists
if [ -f "../.venv/bin/activate" ]; then
    source "../.venv/bin/activate"
elif [ -f ".venv/bin/activate" ]; then
    source ".venv/bin/activate"
fi

# Run the application
exec python main.py
EOF

chmod +x /tmp/voice_transcription_launcher.sh

# Use pkexec with the temporary script
pkexec env DISPLAY="$DISPLAY" XAUTHORITY="$XAUTHORITY" /tmp/voice_transcription_launcher.sh "$SCRIPT_DIR"

# Clean up
rm -f /tmp/voice_transcription_launcher.sh