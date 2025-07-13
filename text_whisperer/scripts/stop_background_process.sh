#!/bin/bash

# Voice Transcription Tool - Stop Background Process

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDFILE="$SCRIPT_DIR/.voice_transcription.pid"

if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Stopping Voice Transcription Tool (PID: $PID)..."
        kill "$PID"
        rm "$PIDFILE"
        echo "Voice Transcription Tool stopped."
    else
        echo "Process not running (stale PID file)."
        rm "$PIDFILE"
    fi
else
    echo "Voice Transcription Tool is not running."
fi

# Also kill any other instances that might be running
pkill -f "voice_transcription_tool/run.py" && echo "Killed any other running instances."