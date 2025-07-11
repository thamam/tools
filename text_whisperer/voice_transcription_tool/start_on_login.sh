#!/bin/bash

# Voice Transcription Tool - Startup Script
# This script starts the application in the background when you log in

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="/home/thh3/personal/tools/text_whisperer/.venv/bin/python"
PIDFILE="$SCRIPT_DIR/.voice_transcription.pid"

# Check if already running
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "Voice Transcription Tool is already running (PID: $(cat "$PIDFILE"))"
    exit 0
fi

# Wait a bit for the desktop environment to be ready
sleep 5

# Start the application in the background
cd "$SCRIPT_DIR"
nohup "$VENV_PYTHON" run.py > /tmp/voice_transcription.log 2>&1 &
echo $! > "$PIDFILE"

echo "Voice Transcription Tool started in background (PID: $!)"
echo "Log file: /tmp/voice_transcription.log"