# TextPilot

TextPilot v0.2.2 is a native SwiftUI macOS menu-bar utility for rewriting selected text with an LLM.

## MVP Flow

1. Select text in any app.
2. Press `Control + Option + R`, or use an action shortcut: `G` grammar, `C` clear, `S` shorten, `P` professional, `L` casual, `K` custom with `Control + Option`.
3. TextPilot copies the selected text, restores your previous clipboard, and opens a floating panel.
4. Pick a rewrite action. Press `Return` to run from an editor, or `Shift + Return` to insert a newline.
5. The generated alternative is copied automatically.
6. Press `Command + Return` to copy and close, or `Option + Return` to replace the original selection and close.
7. Replacement first tries a direct Accessibility edit of the still-selected text, then falls back to `Cmd+V` paste if the app does not expose a compatible text selection.
8. Paste manually, use `Replace`, or use History to recover the last 20 generated responses.

## Run

```sh
swift run --build-path /private/tmp/textpilot-build TextPilot
```

## Test

```sh
swift run --build-path /private/tmp/textpilot-build TextPilotCoreSpec
./scripts/e2e-textpilot-v2.sh
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
