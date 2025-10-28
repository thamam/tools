#!/bin/bash
#
# Tool Result Hook
# Triggers after any tool execution in Claude Code
# This hook detects BMAD command execution and signals the dashboard to refresh.
#
# Environment variables available:
#   $TOOL_NAME - Name of the tool that was executed
#   $TOOL_STATUS - Status of the tool execution (success/error)
#

# Use cross-platform temporary directory
# Fall back to /tmp if TMPDIR is not set
TMPDIR="${TMPDIR:-/tmp}"
TRIGGER_FILE="${TMPDIR}/bmad-dashboard-trigger"

# Check if this was a BMAD-related command
# Look for "/bmad:" in tool name or other BMAD indicators
if [[ "$TOOL_NAME" == *"/bmad:"* || \
      "$TOOL_NAME" == *"bmad"* || \
      ( "$TOOL_NAME" == *"SlashCommand"* && "$CLAUDE_LAST_OUTPUT" == *"/bmad:"* ) ]]; then

    # Touch the trigger file to signal dashboard
    touch "$TRIGGER_FILE" 2>/dev/null

    # Log the trigger for debugging
    echo "[$(date)] BMAD command detected: $TOOL_NAME" >> "${TMPDIR}/bmad-dashboard.log"
fi

# Exit successfully (hooks should not block tool execution)
exit 0
