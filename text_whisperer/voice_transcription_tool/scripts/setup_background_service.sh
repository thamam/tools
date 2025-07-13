#!/bin/bash

# Voice Transcription Tool - Background Service Setup Script
# This script sets up the application to run continuously in the background and auto-start on boot

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the absolute path of the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$SCRIPT_DIR"
USER_NAME="$(whoami)"
USER_HOME="$(eval echo ~$USER_NAME)"

echo -e "${BLUE}=== Voice Transcription Tool Background Service Setup ===${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Don't run this script as root. Run as your regular user."
    echo "The script will ask for sudo when needed."
    exit 1
fi

# Step 1: Install Python dependencies
echo -e "${BLUE}Step 1: Installing Python dependencies...${NC}"
cd "$APP_DIR"

if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found in $APP_DIR"
    exit 1
fi

# Install dependencies in the current environment
pip install -r requirements.txt
print_status "Python dependencies installed"

# Step 2: Test the application
echo -e "${BLUE}Step 2: Testing application...${NC}"
echo "Testing if the application starts correctly..."

# Test run for 3 seconds
timeout 3s python run.py --debug > /tmp/voice_test.log 2>&1 || true

if grep -q "Voice Transcription Tool initialized" /tmp/voice_test.log 2>/dev/null; then
    print_status "Application test successful"
else
    print_warning "Application test may have issues. Check /tmp/voice_test.log"
    echo "Continuing with setup..."
fi

# Step 3: Create systemd user service
echo -e "${BLUE}Step 3: Creating systemd user service...${NC}"

# Create user systemd directory if it doesn't exist
mkdir -p "$USER_HOME/.config/systemd/user"

# Create the service file
cat > "$USER_HOME/.config/systemd/user/voice-transcription-tool.service" << EOF
[Unit]
Description=Voice Transcription Tool
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
Environment=DISPLAY=:0
Environment=XDG_RUNTIME_DIR=/run/user/%i
Environment=PULSE_RUNTIME_PATH=/run/user/%i/pulse
WorkingDirectory=$APP_DIR
ExecStart=$USER_HOME/.local/share/virtualenvs/$(basename $(dirname $APP_DIR))-*/bin/python $APP_DIR/run.py
# Fallback if virtualenv not found
ExecStart=/usr/bin/python3 $APP_DIR/run.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

print_status "Systemd service file created"

# Step 4: Create a launcher script for manual execution
echo -e "${BLUE}Step 4: Creating launcher script...${NC}"

cat > "$APP_DIR/start_background.sh" << 'EOF'
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
EOF

chmod +x "$APP_DIR/start_background.sh"
print_status "Launcher script created"

# Step 5: Create stop script
cat > "$APP_DIR/stop_background.sh" << 'EOF'
#!/bin/bash

echo "Stopping Voice Transcription Tool background service..."
systemctl --user stop voice-transcription-tool.service
systemctl --user disable voice-transcription-tool.service
echo "Service stopped and disabled from auto-start."
EOF

chmod +x "$APP_DIR/stop_background.sh"
print_status "Stop script created"

# Step 6: Enable the service
echo -e "${BLUE}Step 5: Enabling auto-start on boot...${NC}"

# Reload systemd user configuration
systemctl --user daemon-reload

# Enable the service to start on boot
systemctl --user enable voice-transcription-tool.service

# Enable user services to start without login (lingering)
sudo loginctl enable-linger "$USER_NAME"

print_status "Auto-start enabled"

# Step 7: Create desktop entry for manual control
echo -e "${BLUE}Step 6: Creating desktop shortcuts...${NC}"

mkdir -p "$USER_HOME/.local/share/applications"

# Desktop entry to start the service
cat > "$USER_HOME/.local/share/applications/voice-transcription-start.desktop" << EOF
[Desktop Entry]
Name=Start Voice Transcription (Background)
Comment=Start Voice Transcription Tool as background service
Exec=$APP_DIR/start_background.sh
Icon=$APP_DIR/voice-transcription.svg
Terminal=true
Type=Application
Categories=AudioVideo;Audio;Utility;
EOF

# Desktop entry to stop the service
cat > "$USER_HOME/.local/share/applications/voice-transcription-stop.desktop" << EOF
[Desktop Entry]
Name=Stop Voice Transcription (Background)
Comment=Stop Voice Transcription Tool background service
Exec=$APP_DIR/stop_background.sh
Icon=$APP_DIR/voice-transcription.svg
Terminal=true
Type=Application
Categories=AudioVideo;Audio;Utility;
EOF

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$USER_HOME/.local/share/applications"
fi

print_status "Desktop shortcuts created"

# Step 8: Start the service immediately
echo -e "${BLUE}Step 7: Starting the service...${NC}"
systemctl --user start voice-transcription-tool.service

# Wait a moment for it to start
sleep 2

# Check if it's running
if systemctl --user is-active --quiet voice-transcription-tool.service; then
    print_status "Service is running successfully!"
else
    print_warning "Service may not have started correctly"
fi

# Step 9: Summary and instructions
echo ""
echo -e "${GREEN}=== Setup Complete! ===${NC}"
echo ""
echo -e "${BLUE}What was set up:${NC}"
echo "• Python dependencies installed"
echo "• Systemd user service created and enabled"
echo "• Auto-start on boot configured"
echo "• Desktop shortcuts created"
echo "• Service started immediately"
echo ""
echo -e "${BLUE}How to control the service:${NC}"
echo "• Start:  ./start_background.sh"
echo "• Stop:   ./stop_background.sh"
echo "• Status: systemctl --user status voice-transcription-tool.service"
echo "• Logs:   journalctl --user -u voice-transcription-tool.service -f"
echo ""
echo -e "${BLUE}Desktop shortcuts created:${NC}"
echo "• 'Start Voice Transcription (Background)' - in applications menu"
echo "• 'Stop Voice Transcription (Background)' - in applications menu"
echo ""
echo -e "${BLUE}Global Hotkeys:${NC}"
echo "• Alt+D: Record/Stop (requires sudo for global hotkeys)"
echo "• Alt+S: Open Settings"
echo "• Alt+W: Toggle Wake Word"
echo ""
if systemctl --user is-active --quiet voice-transcription-tool.service; then
    echo -e "${GREEN}✓ Voice Transcription Tool is now running in the background!${NC}"
    echo -e "${GREEN}✓ It will automatically start when you boot your computer.${NC}"
else
    echo -e "${YELLOW}⚠ Check the service status and logs if you encounter issues.${NC}"
fi
echo ""
echo "To view real-time logs: journalctl --user -u voice-transcription-tool.service -f"