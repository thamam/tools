#!/bin/bash

# Voice Transcription Tool Manager Script
# Manages the voice transcription tool with start, stop, and restart functionality

# Exit early if no arguments provided (prevents execution during alias definition)
[ $# -eq 0 ] && {
    echo "Usage: $0 {--start|--stop|--restart|--status}"
    exit 1
}

# Prevent execution if being sourced or parsed by bash during alias definition
if [ "${BASH_SOURCE[0]}" != "${0}" ]; then
    return 0 2>/dev/null || exit 0
fi

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Configuration
LOCK_FILE="/tmp/voice_transcription.lock"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/voice_transcription_$(date +%Y%m%d_%H%M%S).log"
VENV_PATH="$PROJECT_ROOT/venv"
PYTHON_SCRIPT="$PROJECT_ROOT/main.py"

# Ensure log directory exists
mkdir -p "$LOG_DIR" 2>/dev/null

# Set verbose mode for user feedback (suppress during alias definition)
VERBOSE="true"

# Function to activate virtual environment if it exists
activate_venv() {
    if [ -d "$VENV_PATH" ] && [ -f "$VENV_PATH/bin/activate" ]; then
        [ "$VERBOSE" = "true" ] && echo "Activating virtual environment..."
        source "$VENV_PATH/bin/activate" 2>/dev/null
    else
        [ "$VERBOSE" = "true" ] && echo "No virtual environment found at $VENV_PATH, using system Python"
    fi
}

# Function to check if the tool is running
is_running() {
    if [ -f "$LOCK_FILE" ]; then
        PID=$(cat "$LOCK_FILE" 2>/dev/null)
        if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
            return 0
        else
            # Stale lock file, remove it
            rm -f "$LOCK_FILE"
            return 1
        fi
    fi
    return 1
}

# Function to start the voice transcription tool
start_tool() {
    if is_running; then
        PID=$(cat "$LOCK_FILE")
        echo "Voice transcription tool is already running (PID: $PID)"
        return 1
    fi

    echo "Starting voice transcription tool..."
    
    # Activate virtual environment
    activate_venv
    
    # Check if Python script exists
    if [ ! -f "$PYTHON_SCRIPT" ]; then
        echo "Error: Python script not found at $PYTHON_SCRIPT"
        return 1
    fi
    
    # Start the tool in background (from project root to ensure config is found)
    cd "$PROJECT_ROOT" || { echo "Error: Cannot change to project directory"; return 1; }
    nohup python "$PYTHON_SCRIPT" --minimized > "$LOG_FILE" 2>&1 &
    PID=$!
    
    # Wait a moment to check if it started successfully
    sleep 2
    
    if kill -0 "$PID" 2>/dev/null; then
        # Write PID to lock file
        echo "$PID" > "$LOCK_FILE"
        echo "Voice transcription tool started successfully (PID: $PID)"
        echo "Log file: $LOG_FILE"
        return 0
    else
        echo "Failed to start voice transcription tool"
        echo "Check log file for details: $LOG_FILE"
        return 1
    fi
}

# Function to stop the voice transcription tool
stop_tool() {
    if ! is_running; then
        echo "Voice transcription tool is not running"
        return 1
    fi
    
    PID=$(cat "$LOCK_FILE")
    echo "Stopping voice transcription tool (PID: $PID)..."
    
    # Try graceful shutdown first
    kill "$PID" 2>/dev/null
    
    # Wait up to 5 seconds for graceful shutdown
    for i in {1..5}; do
        if ! kill -0 "$PID" 2>/dev/null; then
            echo "Voice transcription tool stopped successfully"
            rm -f "$LOCK_FILE"
            return 0
        fi
        sleep 1
    done
    
    # Force kill if still running
    echo "Force stopping voice transcription tool..."
    kill -9 "$PID" 2>/dev/null
    rm -f "$LOCK_FILE"
    echo "Voice transcription tool force stopped"
    return 0
}

# Function to restart the voice transcription tool
restart_tool() {
    echo "Restarting voice transcription tool..."
    stop_tool
    sleep 1
    start_tool
}

# Function to show status
show_status() {
    if is_running; then
        PID=$(cat "$LOCK_FILE")
        echo "Voice transcription tool is running (PID: $PID)"
        
        # Show process details
        ps -p "$PID" -o pid,vsz,rss,pcpu,comm 2>/dev/null
        
        # Show recent log entries
        if [ -f "$LOG_FILE" ]; then
            echo -e "\nRecent log entries:"
            tail -n 5 "$LOG_FILE"
        fi
    else
        echo "Voice transcription tool is not running"
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 {--start|--stop|--restart|--status}"
    echo ""
    echo "Options:"
    echo "  --start    Start the voice transcription tool"
    echo "  --stop     Stop the voice transcription tool"
    echo "  --restart  Restart the voice transcription tool"
    echo "  --status   Show the status of the voice transcription tool"
    echo ""
    echo "The tool will run in the background with output logged to:"
    echo "  $LOG_DIR/voice_transcription_*.log"
}

# Main script logic
case "$1" in
    --start)
        start_tool
        exit $?
        ;;
    --stop)
        stop_tool
        exit $?
        ;;
    --restart)
        restart_tool
        exit $?
        ;;
    --status)
        show_status
        exit 0
        ;;
    *)
        show_usage
        exit 1
        ;;
esac