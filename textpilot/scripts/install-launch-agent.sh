#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST_PATH="$HOME/Library/LaunchAgents/com.textpilot.dev.plist"
SWIFT_PATH="$(command -v swift)"

mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.textpilot.dev</string>
    <key>ProgramArguments</key>
    <array>
        <string>$SWIFT_PATH</string>
        <string>run</string>
        <string>--build-path</string>
        <string>/private/tmp/textpilot-build</string>
        <string>TextPilot</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/textpilot.out.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/textpilot.err.log</string>
</dict>
</plist>
PLIST

launchctl bootout gui/"$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl bootstrap gui/"$(id -u)" "$PLIST_PATH"
launchctl enable gui/"$(id -u)"/com.textpilot.dev

echo "Installed TextPilot LaunchAgent: $PLIST_PATH"
echo "Logs: /tmp/textpilot.out.log and /tmp/textpilot.err.log"
