# TextPilot

TextPilot is a native SwiftUI macOS menu-bar utility for rewriting selected text with an LLM.

## MVP Flow

1. Select text in any app.
2. Press `Control + Option + R`, or use the menu-bar item and choose `Rewrite Selection`.
3. TextPilot copies the selected text, restores your previous clipboard, and opens a floating panel.
4. Pick a rewrite action.
5. Copy the generated alternative text.
6. Paste it manually wherever you want.

## Run

```sh
swift run --build-path /private/tmp/textpilot-build TextPilot
```

## Test

```sh
swift run --build-path /private/tmp/textpilot-build TextPilotCoreSpec
```

## Prompt Profiles

Open `Settings` from the menu-bar item.

- `Default` is built in and read-only.
- Use `New Profile` to create a local editable profile.
- Rename or delete custom profiles from Settings.
- Edit the prompt text for each action in the selected custom profile.
- Rewrites use the active profile selected in Settings.

## Launch At Login

For the SwiftPM MVP, install a user LaunchAgent:

```sh
./scripts/install-launch-agent.sh
```

Remove it with:

```sh
./scripts/uninstall-launch-agent.sh
```

Logs are written to `/tmp/textpilot.out.log` and `/tmp/textpilot.err.log`.

## First-Time Setup

Open `Settings` from the menu-bar item and add an OpenAI API key.

macOS may require Accessibility permission before TextPilot can simulate `Cmd+C` or use the global hotkey fallback from another app:

`System Settings` -> `Privacy & Security` -> `Accessibility`

Add or enable the running `TextPilot` executable if prompted.
