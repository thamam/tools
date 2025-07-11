#!/bin/bash
# Voice Transcription Tool GUI Launcher
# This script launches with a GUI password prompt for hotkeys

cd "/home/thh3/personal/tools/text_whisperer/voice_transcription_tool"

# Try to get sudo with GUI prompt
if command -v pkexec >/dev/null 2>&1; then
    # Use PolicyKit for GUI password prompt
    pkexec env DISPLAY=$DISPLAY XAUTHORITY=$XAUTHORITY python3 "/home/thh3/personal/tools/text_whisperer/voice_transcription_tool/main.py" "$@"
elif command -v gksudo >/dev/null 2>&1; then
    # Fallback to gksudo
    gksudo python3 "/home/thh3/personal/tools/text_whisperer/voice_transcription_tool/main.py" "$@"
else
    # No GUI sudo available, run normally
    python3 "/home/thh3/personal/tools/text_whisperer/voice_transcription_tool/main.py" "$@"
fi
