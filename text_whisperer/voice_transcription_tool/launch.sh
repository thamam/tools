#!/bin/bash
# Launch script for Voice Transcription Tool with proper permissions

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${GREEN}🎤 Voice Transcription Tool Launcher${NC}"
echo "===================================="

# Check if running with sudo
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Already running as root${NC}"
else
    echo -e "${YELLOW}ℹ️  Global hotkeys require administrator privileges${NC}"
    echo -e "${YELLOW}   You'll be prompted for your password${NC}"
    echo ""
fi

# Preserve user's display and home directory
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"

# Function to run the app
run_app() {
    cd "$SCRIPT_DIR"
    
    # Activate virtual environment if it exists
    if [ -f "../.venv/bin/activate" ]; then
        echo -e "${GREEN}✅ Activating virtual environment${NC}"
        source "../.venv/bin/activate"
    elif [ -f ".venv/bin/activate" ]; then
        echo -e "${GREEN}✅ Activating virtual environment${NC}"
        source ".venv/bin/activate"
    fi
    
    # Run the application
    echo -e "${GREEN}🚀 Starting Voice Transcription Tool...${NC}"
    echo ""
    
    # Get the full path to python
    PYTHON_PATH=$(which python)
    
    if [ "$EUID" -eq 0 ]; then
        # If already root, preserve the original user's home
        "$PYTHON_PATH" main.py
    else
        # Use sudo but preserve environment and use full python path
        sudo -E "$PYTHON_PATH" main.py
    fi
}

# Handle errors
trap 'echo -e "\n${RED}❌ Application terminated${NC}"' EXIT

# Run the application
run_app