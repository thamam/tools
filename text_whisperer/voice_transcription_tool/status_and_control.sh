#!/bin/bash

# Voice Transcription Tool - Status and Control Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDFILE="$SCRIPT_DIR/.voice_transcription.pid"

echo "=== Voice Transcription Tool - Status and Control ==="
echo ""

# Check if running
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    PID=$(cat "$PIDFILE")
    echo "✅ Status: RUNNING (PID: $PID)"
    echo "   Memory usage: $(ps -p $PID -o pid,vsz,rss,pcpu --no-headers 2>/dev/null || echo 'N/A')"
    echo "   Log file: /tmp/voice_transcription.log"
else
    echo "❌ Status: NOT RUNNING"
fi

echo ""
echo "🎮 Control Commands:"
echo "   Start (normal):     ./start_on_login.sh"
echo "   Start (w/hotkeys):  ./start_with_hotkeys.sh"
echo "   Stop:               ./stop_background_process.sh"
echo "   Status:             ./status_and_control.sh"
echo ""
echo "📋 Auto-start:"
if [ -f "$HOME/.config/autostart/voice-transcription-tool.desktop" ]; then
    echo "   ✅ Enabled - Will start automatically when you log in"
else
    echo "   ❌ Disabled"
fi

echo ""
echo "🔥 Features Available:"
echo "   • Voice Transcription (Whisper + Google Speech)"
echo "   • Wake Word Detection ('hey computer' or similar)"
echo "   • System Tray Integration"
echo "   • Auto-paste to applications"
echo "   • Manual recording with GUI buttons"
echo "   • Global hotkeys (requires sudo: sudo ./start_on_login.sh)"
echo ""
echo "📖 View Logs:"
echo "   tail -f /tmp/voice_transcription.log"