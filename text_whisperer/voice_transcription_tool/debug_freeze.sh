#!/bin/bash
# Emergency debug script for system freezes
# Run this from TTY (Ctrl+Alt+F3) if system freezes

LOG_FILE="$HOME/freeze_debug.log"

echo "=== System Freeze Debug $(date) ===" | tee -a "$LOG_FILE"
echo ""

echo "=== Voice Transcription Processes ===" | tee -a "$LOG_FILE"
ps aux | grep -E "python.*main\.py|voice.*transcription|pynput" | grep -v grep | tee -a "$LOG_FILE"
echo ""

echo "=== Memory Usage ===" | tee -a "$LOG_FILE"
free -h | tee -a "$LOG_FILE"
echo ""

echo "=== System Load ===" | tee -a "$LOG_FILE"
uptime | tee -a "$LOG_FILE"
echo ""

echo "=== Input Device Grabs ===" | tee -a "$LOG_FILE"
sudo fuser -v /dev/input/event* 2>&1 | grep -v "kernel" | tee -a "$LOG_FILE"
echo ""

echo "=== Recent System Errors ===" | tee -a "$LOG_FILE"
journalctl -xe --since "10 minutes ago" | grep -iE "error|fail|crash|pynput|X11|input|kbd" | tail -20 | tee -a "$LOG_FILE"
echo ""

echo "=== Process Thread Stacks ===" | tee -a "$LOG_FILE"
for pid in $(pgrep -f "python.*main\.py"); do
    echo "--- PID $pid thread stack ---" | tee -a "$LOG_FILE"
    if [ -r "/proc/$pid/stack" ]; then
        sudo cat "/proc/$pid/stack" | tee -a "$LOG_FILE"
    fi
    echo "" | tee -a "$LOG_FILE"
done

echo "=== Killing Voice Transcription Processes ===" | tee -a "$LOG_FILE"
pkill -f "python.*main\.py" && echo "Killed main.py processes" | tee -a "$LOG_FILE"
pkill -f "voice.*transcription" && echo "Killed voice transcription processes" | tee -a "$LOG_FILE"

echo "=== Emergency cleanup complete ===" | tee -a "$LOG_FILE"
echo "Log saved to: $LOG_FILE"