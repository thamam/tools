#!/bin/bash
# Install desktop entry for Voice Transcription Tool

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "📦 Installing Voice Transcription Tool desktop entry..."

# Copy desktop file to user's applications
mkdir -p ~/.local/share/applications
cp "$SCRIPT_DIR/voice-transcription.desktop" ~/.local/share/applications/

# Make it executable
chmod +x ~/.local/share/applications/voice-transcription.desktop

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database ~/.local/share/applications
fi

echo "✅ Desktop entry installed!"
echo ""
echo "You can now find 'Voice Transcription Tool' in your applications menu."
echo "Or run it from terminal with: ./launch.sh"