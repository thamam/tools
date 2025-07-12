# Linux Global Hotkey Solution - Definitive Guide

## The Problem

The Python `keyboard` library requires root/sudo privileges on Linux, causing the error:
```
ImportError: You must be root to use this library on linux.
```

This occurs even when the user is in the `input` group because the `keyboard` library bypasses X11 and directly reads from `/dev/input/` devices, which requires elevated privileges for security reasons.

## Why the Input Group Solution Doesn't Work

Adding users to the `input` group provides read/write access to `/dev/input/event*` devices, but the `keyboard` library's implementation still requires root privileges because it:

1. **Bypasses X11**: Reads directly from raw input devices
2. **Uses uinput**: Requires kernel-level access for key injection
3. **Security Model**: Linux kernel intentionally restricts raw input access

Even with proper permissions (`660` on `/dev/input/event*` and membership in `input` group), the library's architecture requires root access.

## The Solution: Switch to pynput

### Why pynput Works Without Sudo

- **X11 Integration**: Uses X11 for hotkey detection instead of raw device access
- **Cross-Platform**: Same API works on Windows, macOS, and Linux
- **Mature Library**: Well-maintained with good documentation
- **Security Compliant**: Works within user-space permissions

### Implementation

We've created `utils/hotkeys_pynput.py` which provides a drop-in replacement for the original hotkey manager with the same API but using pynput internally.

#### Key Features:
- ✅ No sudo required on Linux X11 systems
- ✅ Automatic fallback to original `keyboard` library if needed
- ✅ Same API as original HotkeyManager
- ✅ Better error handling and diagnostics
- ✅ Support for both X11 and Wayland (limited)

## Installation and Setup

### 1. Install pynput
```bash
pip install pynput>=1.8.0
```

### 2. Update Your Application
Replace imports in your code:
```python
# Old way (requires sudo)
from utils.hotkeys import HotkeyManager

# New way (no sudo required)
from utils.hotkeys_pynput import HotkeyManager
```

The API remains the same, so existing code continues to work unchanged.

### 3. Test the Solution
```bash
python3 test_hotkey_alternatives.py
```

This will test all available hotkey solutions and provide recommendations.

## Compatibility Matrix

| Environment | pynput | keyboard | evdev | Recommendation |
|-------------|--------|----------|-------|---------------|
| X11 | ✅ Works | ❌ Needs sudo | ✅ Works* | **Use pynput** |
| Wayland | ⚠️ Limited | ❌ Needs sudo | ✅ Works* | **Use compositor hotkeys** |
| Headless | ❌ No display | ❌ Needs sudo | ✅ Works* | **Use evdev + input group** |

*Requires user in `input` group

## How Other Applications Handle This

### Discord
- **X11**: Uses X11 global hotkeys
- **Wayland**: Falls back to compositor-specific configurations
- **Workaround**: Uses XWayland compatibility layer

### VS Code
- **Global hotkeys**: Uses electron's native hotkey system
- **Linux**: Leverages X11 or compositor integration
- **Extensions**: Some use external tools for global shortcuts

### Spotify/Media Players
- **MPRIS**: Uses D-Bus media keys protocol on Linux
- **Desktop Integration**: Relies on desktop environment hotkey management
- **Global shortcuts**: Configured at compositor/DE level

## Technical Details

### X11 vs Raw Device Access

| Approach | Pros | Cons | Sudo Required |
|----------|------|------|---------------|
| **X11 (pynput)** | Simple, secure, user-space | X11 only, requires display | ❌ No |
| **Raw devices (keyboard)** | Low-level, works headless | Security risk, complex | ✅ Yes |
| **evdev + udev** | Low-level, configurable | Requires setup, Linux-only | ❌ No (with setup) |

### Why X11 Approach is Better

1. **Security**: Operates in user-space, no kernel access needed
2. **Compatibility**: Works with existing desktop environments
3. **Maintenance**: Less likely to break with system updates
4. **Cross-platform**: Same code works on multiple operating systems

## Migration Guide

### For Existing Applications

1. **Update requirements.txt**:
   ```diff
   - keyboard>=0.13.5
   + pynput>=1.8.0
   ```

2. **Update imports**:
   ```diff
   - from utils.hotkeys import HotkeyManager
   + from utils.hotkeys_pynput import HotkeyManager
   ```

3. **No code changes needed** - API is identical

### For New Applications

Use pynput from the start:
```python
from pynput import keyboard

def on_hotkey():
    print("Hotkey pressed!")

hotkeys = keyboard.GlobalHotKeys({
    '<f9>': on_hotkey,
    '<ctrl>+<alt>+r': on_hotkey
})

hotkeys.start()
# Keep program running
try:
    hotkeys.join()
except KeyboardInterrupt:
    hotkeys.stop()
```

## Troubleshooting

### "Could not determine a listener backend"
- **Cause**: No X11 display available
- **Solution**: Set DISPLAY environment variable or use GUI session

### "This operation is only possible for X11"
- **Cause**: Running under Wayland
- **Solution**: Use XWayland or configure compositor hotkeys

### "Permission denied accessing /dev/input"
- **Cause**: Using evdev backend without proper permissions
- **Solution**: Add user to input group and use pynput instead

### Hotkeys work only when app is focused
- **Cause**: X11 window manager restrictions or Wayland security
- **Solution**: Check desktop environment hotkey settings

## Best Practices

### 1. Graceful Degradation
```python
def setup_hotkeys():
    try:
        hotkey_manager = HotkeyManager()
        if hotkey_manager.register_hotkey('f9', on_toggle_recording):
            print("✅ Global hotkeys enabled")
        else:
            print("⚠️ Using GUI buttons only")
    except Exception as e:
        print(f"❌ Hotkeys failed: {e}")
        # Fall back to GUI-only mode
```

### 2. User Choice
```python
# Let users choose their preferred hotkey method
HOTKEY_METHODS = {
    'auto': 'Automatic (recommended)',
    'pynput': 'pynput (X11, no sudo)',
    'evdev': 'evdev (low-level, requires input group)',
    'gui': 'GUI buttons only'
}
```

### 3. Clear Error Messages
```python
if not hotkey_manager.is_hotkey_active():
    self.show_status("⚠️ Global hotkeys unavailable - using GUI buttons")
```

## Alternative Solutions

### 1. Desktop Environment Integration
Configure hotkeys in system settings to run commands:
```bash
# Example: Configure F9 to send signal to your app
pkill -USR1 voice-transcription-tool
```

### 2. Named Pipes/FIFO
```python
# Create a named pipe for external hotkey programs
import os
FIFO_PATH = '/tmp/voice_transcription_hotkey'
os.mkfifo(FIFO_PATH)

# External hotkey program writes to pipe
# Your app reads from pipe
```

### 3. D-Bus Integration
```python
# Use D-Bus for inter-process communication
# Configure system hotkeys to send D-Bus messages
# Your app listens for D-Bus signals
```

## Conclusion

The **pynput** library provides the most reliable, secure, and user-friendly solution for global hotkeys on Linux without requiring sudo privileges. It integrates well with existing X11 desktop environments and provides a consistent cross-platform API.

For applications requiring global hotkeys on Linux:
1. **Primary choice**: pynput (this solution)
2. **Fallback**: GUI buttons and application-focused hotkeys
3. **Advanced**: Desktop environment integration or D-Bus

This solution eliminates the need for users to run applications with sudo privileges while maintaining full global hotkey functionality.