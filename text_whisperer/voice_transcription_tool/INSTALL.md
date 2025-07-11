# Voice Transcription Tool - Ubuntu Installation Guide

## Quick Installation

### Option 1: Install the .deb Package (Recommended)

```bash
# Install the package
sudo dpkg -i voice-transcription-tool_2.0.0.deb

# Fix any dependency issues (if needed)
sudo apt-get install -f
```

### Option 2: Manual Installation
If you prefer not to use the .deb package, you can still use the desktop installer:
```bash
python3 install_package.py
```

## Usage

### Starting the Application

**From Terminal:**
```bash
# Regular mode (no global hotkeys)
voice-transcription-tool

# With global hotkeys (requires sudo)
sudo voice-transcription-tool
```

**From GUI:**
- Open Applications menu
- Search for "Voice Transcription Tool"
- Click to launch

### Global Hotkeys (when running with sudo)
- **Alt+D**: Start/Stop recording
- **Alt+S**: Open Settings
- **Alt+W**: Toggle Wake Word detection

## Features

✅ **Speech Recognition Engines**
- Whisper (local, high quality)
- Google Speech Recognition (online)

✅ **Wake Word Detection**
- Hands-free activation
- Customizable wake words
- Voice training for accuracy

✅ **Modern GUI**
- Tabbed interface
- Advanced mode toggle
- Real-time audio visualization

✅ **System Integration**
- Auto-paste transcriptions
- Clipboard integration
- System tray operation

✅ **Audio Features**
- Multiple input device support
- Audio feedback
- Device testing tools

## System Requirements

- Ubuntu 18.04+ (or compatible Debian-based system)
- Python 3.8+
- Audio input device (microphone)
- Internet connection (for Google Speech engine)

## Troubleshooting

### Dependencies
The package automatically installs Python dependencies during installation. If you encounter issues:

```bash
# Reinstall the package
sudo dpkg -r voice-transcription-tool
sudo dpkg -i voice-transcription-tool_2.0.0.deb
sudo apt-get install -f
```

### Audio Issues
- Check microphone permissions
- Test audio devices in settings
- Ensure PulseAudio is running

### Global Hotkeys
- Global hotkeys require sudo privileges
- Run with: `sudo voice-transcription-tool`
- Alternative: Use GUI buttons for recording

## Uninstallation

```bash
sudo dpkg -r voice-transcription-tool
```

## Support

For issues and feature requests, please refer to the documentation or create an issue in the project repository.