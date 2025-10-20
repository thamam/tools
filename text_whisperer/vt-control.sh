#!/bin/bash
# Voice Transcription Tool Control Script
# Easy management of the Voice Transcription Tool process

PYTHON_BIN="/home/thh3/anaconda3/bin/python3"
APP_DIR="/home/thh3/personal/tools/text_whisperer"
APP_MAIN="${APP_DIR}/main.py"
LOG_DIR="${APP_DIR}/logs"
LOCK_FILE="/tmp/voice_transcription.lock"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to get PID of running process
get_pid() {
    pgrep -f "text_whisperer/main.py" 2>/dev/null
}

# Function to check if process is running
is_running() {
    local pid=$(get_pid)
    [ -n "$pid" ]
}

# Function to start the app
start() {
    if is_running; then
        echo -e "${YELLOW}Voice Transcription Tool is already running (PID: $(get_pid))${NC}"
        return 1
    fi

    # Remove stale lock file if process is not running
    if [ -f "$LOCK_FILE" ]; then
        echo -e "${YELLOW}Removing stale lock file...${NC}"
        rm -f "$LOCK_FILE"
    fi

    echo -e "${BLUE}Starting Voice Transcription Tool...${NC}"
    nohup "$PYTHON_BIN" "$APP_MAIN" --minimized > /dev/null 2>&1 &
    sleep 1
    
    if is_running; then
        echo -e "${GREEN}✅ Started successfully (PID: $(get_pid))${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to start. Check logs: $LOG_DIR${NC}"
        return 1
    fi
}

# Function to stop the app
stop() {
    if ! is_running; then
        echo -e "${YELLOW}Voice Transcription Tool is not running${NC}"
        return 1
    fi
    
    local pid=$(get_pid)
    echo -e "${BLUE}Stopping Voice Transcription Tool (PID: $pid)...${NC}"
    
    # Try graceful shutdown first
    kill "$pid" 2>/dev/null
    sleep 1
    
    # Check if still running, force kill if necessary
    if is_running; then
        echo -e "${YELLOW}Process still running, forcing shutdown...${NC}"
        kill -9 "$pid" 2>/dev/null
        sleep 0.5
    fi
    
    if is_running; then
        echo -e "${RED}❌ Failed to stop process${NC}"
        return 1
    else
        # Remove lock file after successful kill
        rm -f "$LOCK_FILE" 2>/dev/null
        echo -e "${GREEN}✅ Stopped successfully${NC}"
        return 0
    fi
}

# Function to restart the app
restart() {
    echo -e "${BLUE}Restarting Voice Transcription Tool...${NC}"
    stop
    sleep 1
    start
}

# Function to show status
status() {
    if is_running; then
        local pid=$(get_pid)
        echo -e "${GREEN}✅ Voice Transcription Tool is running${NC}"
        echo -e "   PID: ${BLUE}$pid${NC}"
        
        # Show memory and CPU usage
        if command -v ps &> /dev/null; then
            local mem_cpu=$(ps -p "$pid" -o %cpu,%mem,etime --no-headers 2>/dev/null)
            if [ -n "$mem_cpu" ]; then
                echo -e "   CPU/MEM/TIME: ${BLUE}$mem_cpu${NC}"
            fi
        fi
        
        # Show latest log file
        if [ -d "$LOG_DIR" ]; then
            local latest_log=$(ls -t "$LOG_DIR"/voice_transcription_*.log 2>/dev/null | head -1)
            if [ -n "$latest_log" ]; then
                echo -e "   Latest log: ${BLUE}$latest_log${NC}"
            fi
        fi
        
        return 0
    else
        echo -e "${RED}❌ Voice Transcription Tool is not running${NC}"
        return 1
    fi
}

# Function to show logs
logs() {
    if [ -d "$LOG_DIR" ]; then
        local latest_log=$(ls -t "$LOG_DIR"/voice_transcription_*.log 2>/dev/null | head -1)
        if [ -n "$latest_log" ]; then
            echo -e "${BLUE}Showing latest log: $latest_log${NC}"
            tail -f "$latest_log"
        else
            echo -e "${YELLOW}No log files found in $LOG_DIR${NC}"
        fi
    else
        echo -e "${YELLOW}Log directory not found: $LOG_DIR${NC}"
    fi
}

# Function to show help
show_help() {
    cat << HELP
${BLUE}Voice Transcription Tool Control Script${NC}

Usage: $(basename "$0") {start|stop|restart|status|logs|help}

Commands:
  ${GREEN}start${NC}       Start the Voice Transcription Tool in minimized mode
  ${GREEN}stop${NC}        Stop the Voice Transcription Tool
  ${GREEN}restart${NC}     Restart the Voice Transcription Tool
  ${GREEN}status${NC}      Show current status and process info
  ${GREEN}logs${NC}        Show and follow the latest log file (Ctrl+C to exit)
  ${GREEN}help${NC}        Show this help message

Examples:
  $(basename "$0") start      # Start in system tray
  $(basename "$0") status     # Check if running
  $(basename "$0") logs       # View logs in real-time

Keyboard Shortcuts (when running):
  Alt+D   Start/stop recording
  Alt+S   Open settings dialog
  Alt+W   Toggle wake word detection

Configuration:
  Config: $APP_DIR/voice_transcription_config.json
  Logs:   $LOG_DIR/

HELP
}

# Main command handler
case "${1:-}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        echo -e "${YELLOW}No command specified. Use 'help' for usage information.${NC}"
        show_help
        exit 1
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_help
        exit 1
        ;;
esac
