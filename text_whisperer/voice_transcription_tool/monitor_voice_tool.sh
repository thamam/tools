#!/bin/bash
# Monitor Voice Transcription Tool for issues
# Run this to check if the tool is behaving properly

echo "=== Voice Transcription Tool Monitor ==="
echo "Current time: $(date)"
echo ""

# Check if running
PIDS=$(pgrep -f "python.*main\.py")
if [ -n "$PIDS" ]; then
    echo "✅ Voice Transcription Tool is running (PIDs: $PIDS)"
    
    # Check resource usage
    echo ""
    echo "=== Resource Usage ==="
    for pid in $PIDS; do
        echo "PID $pid:"
        ps -p "$pid" -o pid,ppid,pcpu,pmem,time,cmd --no-headers
    done
    
    # Check threads
    echo ""
    echo "=== Thread Count ==="
    for pid in $PIDS; do
        thread_count=$(ps -eLf | grep "^[^[:space:]]*[[:space:]]*$pid" | wc -l)
        echo "PID $pid: $thread_count threads"
    done
    
    # Check input device grabs
    echo ""
    echo "=== Input Device Grabs ==="
    if command -v fuser >/dev/null 2>&1; then
        sudo fuser -v /dev/input/event* 2>&1 | grep -v "kernel" | grep "$PIDS" || echo "No input grabs by voice tool"
    else
        echo "fuser not available"
    fi
    
else
    echo "❌ Voice Transcription Tool is not running"
fi

# Check lock file
echo ""
echo "=== Process Lock ==="
if [ -f "/tmp/voice_transcription.lock" ]; then
    LOCK_PID=$(cat /tmp/voice_transcription.lock)
    echo "Lock file exists with PID: $LOCK_PID"
    
    if ps -p "$LOCK_PID" > /dev/null 2>&1; then
        echo "✅ Lock PID is still running"
    else
        echo "⚠️ Lock PID is dead - stale lock file"
        echo "To clean up: rm /tmp/voice_transcription.lock"
    fi
else
    echo "No lock file found"
fi

# Recent errors
echo ""
echo "=== Recent Errors (last 5 minutes) ==="
journalctl --since "5 minutes ago" | grep -iE "voice|transcription|pynput|hotkey" | tail -5 || echo "No recent errors"

echo ""
echo "=== Monitor complete ==="