#!/bin/bash

# Voice Transcription Tool - Setup Input Group for Global Hotkeys
# This script adds the user to the 'input' group to allow global hotkey access without sudo

echo "=== Voice Transcription Tool - Global Hotkey Setup ==="
echo ""
echo "This script will add your user to the 'input' group to enable"
echo "global hotkeys without requiring sudo."
echo ""

CURRENT_USER="$(whoami)"

# Check if user is already in input group
if groups "$CURRENT_USER" | grep -q '\binput\b'; then
    echo "✅ You are already in the 'input' group!"
    echo ""
    echo "If hotkeys still don't work, try:"
    echo "1. Log out and log back in"
    echo "2. Or run: newgrp input"
    exit 0
fi

echo "Adding $CURRENT_USER to the 'input' group..."
echo "This requires sudo permission:"
echo ""

# Add user to input group
sudo usermod -a -G input "$CURRENT_USER"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully added $CURRENT_USER to the 'input' group!"
    echo ""
    echo "⚠️  IMPORTANT: You need to log out and log back in for this to take effect!"
    echo ""
    echo "Alternatively, you can start a new shell with the group active:"
    echo "  newgrp input"
    echo "  ./start_on_login.sh"
    echo ""
    echo "After logging back in, global hotkeys will work without sudo!"
else
    echo ""
    echo "❌ Failed to add user to input group"
    echo "Please run manually: sudo usermod -a -G input $CURRENT_USER"
fi