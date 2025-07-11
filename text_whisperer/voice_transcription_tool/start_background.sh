#!/bin/bash

# Voice Transcription Tool Background Launcher
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting Voice Transcription Tool in background..."

# Start as systemd user service
systemctl --user start voice-transcription-tool.service

echo "Service started. Check status with:"
echo "  systemctl --user status voice-transcription-tool.service"
echo ""
echo "To stop: systemctl --user stop voice-transcription-tool.service"
echo "To view logs: journalctl --user -u voice-transcription-tool.service -f"
