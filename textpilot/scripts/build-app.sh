#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="TextPilot"
BUNDLE_ID="com.textpilot.dev"
SIGNING_IDENTITY="TextPilot Local Signing"   # must exactly match the Keychain Access cert name
APP_PATH="/Applications/${APP_NAME}.app"
LSREGISTER="/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister"

VERSION="$(grep -o 'current = "[^"]*"' "$PROJECT_DIR/Sources/TextPilotCore/TextPilotCore.swift" | sed -E 's/current = "(.*)"/\1/')"
echo "Building TextPilot ${VERSION}..."

cd "$PROJECT_DIR"
swift build -c release --product TextPilot

BUILT_BINARY="$PROJECT_DIR/.build/release/TextPilot"
[ -x "$BUILT_BINARY" ] || { echo "error: $BUILT_BINARY not found" >&2; exit 1; }

if ! security find-identity -v -p codesigning | grep -q "$SIGNING_IDENTITY"; then
    echo "error: no code signing identity named '$SIGNING_IDENTITY' found in the keychain." >&2
    echo "Create it once via Keychain Access -> Certificate Assistant -> Create a Certificate..." >&2
    echo "(Identity Type: Self Signed Root, Certificate Type: Code Signing), then trust it for" >&2
    echo "Code Signing (Always Trust). See the plan's manual-steps section for details." >&2
    exit 1
fi

echo "Assembling ${APP_PATH}..."
rm -rf "$APP_PATH"
mkdir -p "$APP_PATH/Contents/MacOS" "$APP_PATH/Contents/Resources"
cp "$BUILT_BINARY" "$APP_PATH/Contents/MacOS/${APP_NAME}"
sed "s/__VERSION__/${VERSION}/g" "$PROJECT_DIR/Packaging/Info.plist.template" > "$APP_PATH/Contents/Info.plist"

xattr -cr "$APP_PATH"   # defensive; local builds are never quarantined, this is a no-op safety net

echo "Signing with identity: ${SIGNING_IDENTITY}"
codesign --force --timestamp=none --sign "$SIGNING_IDENTITY" "$APP_PATH"
codesign --verify --strict --verbose=2 "$APP_PATH"
codesign -dvvv "$APP_PATH" 2>&1 | grep -E 'Identifier|TeamIdentifier|Signature'

echo "Re-registering with Launch Services..."
"$LSREGISTER" -f "$APP_PATH"

if launchctl print "gui/$(id -u)/${BUNDLE_ID}" >/dev/null 2>&1; then
    echo "Restarting running instance..."
    launchctl kickstart -k "gui/$(id -u)/${BUNDLE_ID}"
else
    echo "LaunchAgent not loaded — run scripts/install-launch-agent.sh"
fi

echo "Done: ${APP_PATH}"
