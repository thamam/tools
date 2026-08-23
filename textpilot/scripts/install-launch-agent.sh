#!/usr/bin/env bash
set -euo pipefail

PLIST_PATH="$HOME/Library/LaunchAgents/com.textpilot.dev.plist"
BINARY_PATH="/Applications/TextPilot.app/Contents/MacOS/TextPilot"

[ -x "$BINARY_PATH" ] || { echo "error: $BINARY_PATH not found — run scripts/build-app.sh first" >&2; exit 1; }

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
        <string>$BINARY_PATH</string>
    </array>
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

echo "Installed TextPilot LaunchAgent: $PLIST_PATH -> $BINARY_PATH"
echo "Logs: /tmp/textpilot.out.log and /tmp/textpilot.err.log"
