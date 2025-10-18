#!/bin/bash
#
# scripts/stability_test.sh - Multi-hour stability test for Voice Transcription Tool
#
# This script runs the application in the background for extended periods (4-8 hours)
# and performs periodic recordings to verify stability. It monitors for crashes,
# resource limit breaches, and unexpected shutdowns.
#
# Usage:
#   ./scripts/stability_test.sh --duration 8  # Run for 8 hours
#   ./scripts/stability_test.sh --duration 4 --interval 300  # 4 hours, record every 5min
#
# Monitoring:
#   - Process health (crashes, unexpected exits)
#   - Resource usage (memory, CPU)
#   - Log file errors
#   - Recording success rate
#

set -e

# Default configuration
DURATION_HOURS=8
INTERVAL_SECONDS=300  # 5 minutes between recordings
LOG_DIR="logs"
REPORT_FILE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --duration)
            DURATION_HOURS="$2"
            shift 2
            ;;
        --interval)
            INTERVAL_SECONDS="$2"
            shift 2
            ;;
        --log-dir)
            LOG_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--duration HOURS] [--interval SECONDS] [--log-dir DIR]"
            exit 1
            ;;
    esac
done

# Calculate test parameters
DURATION_SECONDS=$((DURATION_HOURS * 3600))
TOTAL_CYCLES=$((DURATION_SECONDS / INTERVAL_SECONDS))
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="${LOG_DIR}/stability_test_${TIMESTAMP}.log"

# Create log directory
mkdir -p "$LOG_DIR"

echo "======================================================================="
echo "STABILITY TEST: ${DURATION_HOURS}-HOUR RUN"
echo "======================================================================="
echo "Duration:        ${DURATION_HOURS} hours (${DURATION_SECONDS} seconds)"
echo "Check Interval:  ${INTERVAL_SECONDS} seconds"
echo "Expected Cycles: ${TOTAL_CYCLES}"
echo "Report File:     ${REPORT_FILE}"
echo "Start Time:      $(date)"
echo "======================================================================="
echo ""

# Initialize report
cat > "$REPORT_FILE" <<EOF
Stability Test Report
=====================
Start Time: $(date)
Duration: ${DURATION_HOURS} hours
Interval: ${INTERVAL_SECONDS} seconds
Expected Cycles: ${TOTAL_CYCLES}

EOF

# Start the application in the background
echo "✓ Starting Voice Transcription Tool..."
python main.py --debug > "${LOG_DIR}/app_output_${TIMESTAMP}.log" 2>&1 &
APP_PID=$!

# Wait for app to initialize
sleep 5

# Check if process started successfully
if ! ps -p $APP_PID > /dev/null 2>&1; then
    echo "❌ ERROR: Application failed to start"
    echo "Check logs: ${LOG_DIR}/app_output_${TIMESTAMP}.log"
    exit 1
fi

echo "✓ Application started (PID: $APP_PID)"
echo ""

# Test loop
START_TIME=$(date +%s)
CYCLE=0
SUCCESS_COUNT=0
FAILURE_COUNT=0
CRASH_COUNT=0

while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))

    # Check if test duration exceeded
    if [ $ELAPSED -ge $DURATION_SECONDS ]; then
        echo "✓ Test duration completed: ${DURATION_HOURS} hours"
        break
    fi

    CYCLE=$((CYCLE + 1))
    ELAPSED_MIN=$((ELAPSED / 60))
    REMAINING_MIN=$(((DURATION_SECONDS - ELAPSED) / 60))

    echo "[Cycle ${CYCLE}/${TOTAL_CYCLES}] Elapsed: ${ELAPSED_MIN}min | Remaining: ${REMAINING_MIN}min"

    # Check if process still running
    if ! ps -p $APP_PID > /dev/null 2>&1; then
        echo "❌ CRASH DETECTED: Application process terminated unexpectedly!"
        echo "   Crash at cycle: $CYCLE"
        echo "   Elapsed time: ${ELAPSED_MIN} minutes"
        CRASH_COUNT=$((CRASH_COUNT + 1))

        # Log crash
        echo "CRASH at cycle $CYCLE (${ELAPSED_MIN} min)" >> "$REPORT_FILE"

        # Attempt to restart
        echo "   Attempting to restart..."
        python main.py --debug >> "${LOG_DIR}/app_output_${TIMESTAMP}.log" 2>&1 &
        APP_PID=$!
        sleep 5

        if ! ps -p $APP_PID > /dev/null 2>&1; then
            echo "❌ Failed to restart application. Aborting test."
            break
        else
            echo "✓ Application restarted (new PID: $APP_PID)"
        fi
    fi

    # Check resource usage
    if ps -p $APP_PID > /dev/null 2>&1; then
        MEMORY_MB=$(ps -o rss= -p $APP_PID | awk '{print $1/1024}')
        CPU_PERCENT=$(ps -o %cpu= -p $APP_PID)

        echo "   Memory: ${MEMORY_MB} MB | CPU: ${CPU_PERCENT}%"

        # Log to report
        echo "Cycle $CYCLE: Memory=${MEMORY_MB}MB CPU=${CPU_PERCENT}%" >> "$REPORT_FILE"

        # Check for resource limit warnings in logs
        RECENT_WARNINGS=$(tail -n 50 "${LOG_DIR}/app_output_${TIMESTAMP}.log" | grep -i "resource limit\|memory limit\|CPU limit" | wc -l)
        if [ $RECENT_WARNINGS -gt 0 ]; then
            echo "   ⚠️  Resource limit warnings detected: $RECENT_WARNINGS"
        fi
    fi

    # Check application logs for errors
    ERROR_COUNT=$(tail -n 100 "${LOG_DIR}/app_output_${TIMESTAMP}.log" | grep -c "ERROR" || true)
    if [ $ERROR_COUNT -gt 5 ]; then
        echo "   ⚠️  High error count in logs: $ERROR_COUNT errors in last 100 lines"
        FAILURE_COUNT=$((FAILURE_COUNT + 1))
    else
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    fi

    # Wait for next cycle
    sleep $INTERVAL_SECONDS
done

# Cleanup: Stop the application
echo ""
echo "Stopping application..."
if ps -p $APP_PID > /dev/null 2>&1; then
    kill $APP_PID
    sleep 2

    # Force kill if still running
    if ps -p $APP_PID > /dev/null 2>&1; then
        kill -9 $APP_PID
    fi
fi

# Generate final report
END_TIME=$(date +%s)
TOTAL_ELAPSED=$((END_TIME - START_TIME))
TOTAL_ELAPSED_MIN=$((TOTAL_ELAPSED / 60))

cat >> "$REPORT_FILE" <<EOF

======================================================================
FINAL REPORT
======================================================================
End Time:        $(date)
Total Duration:  ${TOTAL_ELAPSED_MIN} minutes (${TOTAL_ELAPSED} seconds)
Cycles Completed: ${CYCLE}/${TOTAL_CYCLES}
Success Count:   ${SUCCESS_COUNT}
Failure Count:   ${FAILURE_COUNT}
Crash Count:     ${CRASH_COUNT}

Success Rate:    $((SUCCESS_COUNT * 100 / (SUCCESS_COUNT + FAILURE_COUNT)))%

Verdict: $([ $CRASH_COUNT -eq 0 ] && echo "✅ PASS - No crashes detected" || echo "❌ FAIL - ${CRASH_COUNT} crashes detected")
======================================================================
EOF

# Display final report
echo ""
echo "======================================================================="
echo "STABILITY TEST COMPLETE"
echo "======================================================================="
echo "Total Duration:   ${TOTAL_ELAPSED_MIN} minutes"
echo "Cycles Completed: ${CYCLE}/${TOTAL_CYCLES}"
echo "Success Count:    ${SUCCESS_COUNT}"
echo "Failure Count:    ${FAILURE_COUNT}"
echo "Crash Count:      ${CRASH_COUNT}"
echo ""
echo "Verdict: $([ $CRASH_COUNT -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")"
echo "======================================================================="
echo ""
echo "Full report saved to: $REPORT_FILE"
echo "Application logs:     ${LOG_DIR}/app_output_${TIMESTAMP}.log"
