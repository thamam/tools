#!/usr/bin/env bash
set -euo pipefail

BUILD_PATH="${BUILD_PATH:-/private/tmp/textpilot-v2-e2e-build}"
MOCK_OUTPUT="${TEXTPILOT_MOCK_OUTPUT:-E2E rewritten output}"
HOST_OUTPUT="${HOST_OUTPUT:-/tmp/textpilot-e2e-host.txt}"
REPLACEMENT_LOG="${REPLACEMENT_LOG:-/tmp/textpilot-v2-replacement.log}"
EXPECTED_REPLACEMENT_METHOD="${TEXTPILOT_EXPECT_REPLACEMENT_METHOD:-accessibilityDirect}"
DEFAULTS_SUITE="dev.textpilot.e2e.$$"
APP_PID=""
HOST_PID=""

cleanup() {
  if [[ -n "$APP_PID" ]]; then kill "$APP_PID" >/dev/null 2>&1 || true; fi
  if [[ -n "$HOST_PID" ]]; then kill "$HOST_PID" >/dev/null 2>&1 || true; fi
  defaults delete "$DEFAULTS_SUITE" >/dev/null 2>&1 || true
}
trap cleanup EXIT

activate_host() {
  osascript <<'OSA'
tell application "System Events"
  tell process "TextPilotE2EHost"
    set frontmost to true
  end tell
end tell
OSA
  sleep 0.5
}

window_contents() {
  osascript -e 'tell application "System Events" to tell process "TextPilot" to get entire contents of window 1' 2>/dev/null || true
}

window_count() {
  osascript -e 'tell application "System Events" to tell process "TextPilot" to count windows' 2>/dev/null || echo 0
}

rm -f "$HOST_OUTPUT" "$REPLACEMENT_LOG" /tmp/textpilot-v2-e2e-app.log /tmp/textpilot-v2-e2e-host.log
swift build --build-path "$BUILD_PATH" --product TextPilot --product TextPilotE2EHost >/dev/null

TEXTPILOT_E2E_HOST_OUTPUT="$HOST_OUTPUT" swift run --build-path "$BUILD_PATH" TextPilotE2EHost >/tmp/textpilot-v2-e2e-host.log 2>&1 &
HOST_PID=$!
sleep 3

APP_ENV=(
  "TEXTPILOT_MOCK_OUTPUT=$MOCK_OUTPUT"
  "TEXTPILOT_USER_DEFAULTS_SUITE=$DEFAULTS_SUITE"
  "TEXTPILOT_REPLACEMENT_LOG=$REPLACEMENT_LOG"
)
if [[ "${TEXTPILOT_DISABLE_DIRECT_REPLACE:-}" == "1" ]]; then
  APP_ENV+=("TEXTPILOT_DISABLE_DIRECT_REPLACE=1")
fi
if [[ "${TEXTPILOT_REQUIRE_DIRECT_REPLACE:-}" == "1" ]]; then
  APP_ENV+=("TEXTPILOT_REQUIRE_DIRECT_REPLACE=1")
fi

env "${APP_ENV[@]}" swift run --build-path "$BUILD_PATH" TextPilot >/tmp/textpilot-v2-e2e-app.log 2>&1 &
APP_PID=$!
sleep 7

activate_host
printf "BEFORE_RETURN_RUN" | pbcopy
osascript -e 'tell application "System Events" to key code 15 using {control down, option down}'
sleep 2
osascript <<'OSA' >/dev/null
tell application "System Events"
  tell process "TextPilot"
    set frontmost to true
    delay 0.3
    click text area 1 of scroll area 1 of group 1 of window 1
  end tell
end tell
OSA
sleep 0.3
osascript -e 'tell application "System Events" to key code 36'
sleep 3

CLIPBOARD_VALUE="$(pbpaste)"
if [[ "$CLIPBOARD_VALUE" != "$MOCK_OUTPUT" ]]; then
  echo "FAIL return-run: expected clipboard '$MOCK_OUTPUT' but got '$CLIPBOARD_VALUE'" >&2
  exit 1
fi

WINDOW_TEXT="$(window_contents)"
if [[ "$WINDOW_TEXT" != *"Fix Grammar"* || "$WINDOW_TEXT" != *"$MOCK_OUTPUT"* ]]; then
  echo "FAIL copy-close UI: expected Fix Grammar history and output, got '$WINDOW_TEXT'" >&2
  exit 1
fi

osascript -e 'tell application "System Events" to key code 36 using {command down}'
sleep 1
if [[ "$(window_count)" != "0" ]]; then
  echo "FAIL copy-close: expected TextPilot panel to close" >&2
  exit 1
fi

activate_host
printf "BEFORE_SHORTCUT" | pbcopy
osascript -e 'tell application "System Events" to key code 1 using {control down, option down}'
sleep 4

CLIPBOARD_VALUE="$(pbpaste)"
if [[ "$CLIPBOARD_VALUE" != "$MOCK_OUTPUT" ]]; then
  echo "FAIL auto-copy: expected clipboard '$MOCK_OUTPUT' but got '$CLIPBOARD_VALUE'" >&2
  exit 1
fi

WINDOW_TEXT="$(window_contents)"
if [[ "$WINDOW_TEXT" != *"Shorten"* || "$WINDOW_TEXT" != *"$MOCK_OUTPUT"* ]]; then
  echo "FAIL replace-close UI: expected Shorten history and output, got '$WINDOW_TEXT'" >&2
  exit 1
fi

osascript -e 'tell application "System Events" to key code 36 using {option down}'
sleep 1.5
HOST_TEXT="$(cat "$HOST_OUTPUT")"
if [[ "$HOST_TEXT" != "$MOCK_OUTPUT" ]]; then
  echo "FAIL replace-close: expected host text '$MOCK_OUTPUT' but got '$HOST_TEXT'" >&2
  echo "Replacement log:" >&2
  cat "$REPLACEMENT_LOG" >&2 2>/dev/null || true
  exit 1
fi
if [[ "$(window_count)" != "0" ]]; then
  echo "FAIL replace-close: expected TextPilot panel to close" >&2
  exit 1
fi

REPLACEMENT_TEXT="$(cat "$REPLACEMENT_LOG" 2>/dev/null || true)"
if [[ "$REPLACEMENT_TEXT" != *"method=$EXPECTED_REPLACEMENT_METHOD"* ]]; then
  echo "FAIL replacement-method: expected '$EXPECTED_REPLACEMENT_METHOD' in replacement log, got '$REPLACEMENT_TEXT'" >&2
  exit 1
fi

echo "PASS e2e return-run-copy-close-shortcut-replace-close-history method=$EXPECTED_REPLACEMENT_METHOD"
