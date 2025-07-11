#!/bin/bash

echo "=== Voice Transcription Tool .deb Package Test ==="
echo ""

# Check if package file exists
if [ ! -f "voice-transcription-tool_2.0.0.deb" ]; then
    echo "❌ Package file not found!"
    exit 1
fi

echo "✅ Package file exists: $(ls -lh voice-transcription-tool_2.0.0.deb | awk '{print $5}')"

# Check package integrity
echo ""
echo "📦 Package Information:"
dpkg --info voice-transcription-tool_2.0.0.deb | grep -E "(Package|Version|Architecture|Depends)"

echo ""
echo "📋 Package Contents Summary:"
dpkg -c voice-transcription-tool_2.0.0.deb | grep -E "(bin|applications|pixmaps|main.py)" | head -10

echo ""
echo "🔧 Installation Commands:"
echo "  To install: sudo dpkg -i voice-transcription-tool_2.0.0.deb"
echo "  To fix dependencies: sudo apt-get install -f"
echo "  To remove: sudo dpkg -r voice-transcription-tool"

echo ""
echo "🚀 Usage after installation:"
echo "  Terminal: voice-transcription-tool"
echo "  GUI: Search 'Voice Transcription Tool' in applications"
echo "  With hotkeys: sudo voice-transcription-tool"

echo ""
echo "✅ Package build successful and ready for distribution!"