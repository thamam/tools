# Voice Transcription Tool - Global Hotkey Setup Guide

## The Issue
Global hotkeys on Linux require special permissions to capture keyboard input system-wide. The `keyboard` library needs either:
1. Root access (sudo)
2. User in the 'input' group
3. Or use application-specific hotkeys only

## Solutions

### Option 1: Add User to Input Group (Recommended)
This allows global hotkeys without needing sudo every time:

```bash
./setup_input_group.sh
# Then log out and log back in
```

After this, hotkeys will work with the normal startup:
```bash
./start_on_login.sh
```

### Option 2: Use GUI Buttons (No Setup Required)
If you prefer not to use global hotkeys:
- Use the **Record** button in the GUI
- Use the **Settings** button in the GUI  
- Use the **Wake Word** toggle in settings
- Or use the system tray menu

### Option 3: Use Window-Specific Hotkeys
When the Voice Transcription Tool window is focused:
- The configured hotkeys will work within the application
- No special permissions needed

## Current Hotkey Configuration
- **Alt+D**: Start/Stop Recording
- **Alt+S**: Open Settings
- **Alt+W**: Toggle Wake Word Detection

## Troubleshooting

### "You must be root to use this library on linux"
This means the keyboard library can't access global input. Use Option 1 above.

### Hotkeys work in GUI but not globally
This is normal without proper permissions. The application falls back to window-specific hotkeys.

### Still having issues?
1. Check if you're in the input group: `groups | grep input`
2. Try logging out and back in after group changes
3. Use the GUI buttons as a fallback