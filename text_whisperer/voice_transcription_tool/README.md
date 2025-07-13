# Voice Transcription Tool

Speech-to-text application with global hotkeys, system tray, and auto-paste functionality.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   
   # Linux users also need:
   sudo apt install xdotool
   ```

2. **Run the application:**
   ```bash
   python main.py
   ```

## Usage

- **Alt+D**: Start/stop recording
- **Alt+S**: Open settings  
- **Alt+W**: Toggle wake word detection

The app starts with a system tray icon (blue microphone) that turns red with a countdown timer during recording.

## Command Line Options

```bash
python main.py --help           # Show all options
python main.py --minimized     # Start hidden in system tray
python main.py --debug         # Enable verbose logging
python main.py --no-tray       # Disable system tray
```

## Features

- 🎤 **Global Hotkeys**: Record from anywhere (no sudo required)
- 🖥️ **System Tray**: Visual recording timer and status
- 📋 **Auto-paste**: Automatically paste transcribed text
- 🔊 **Audio Feedback**: Sound notifications for start/stop
- 🧠 **Multiple Engines**: Whisper (local) or Google Speech (cloud)
- 🎯 **Wake Word**: Hands-free "Hey Computer" activation
- 🎨 **Modern GUI**: Tabbed interface with advanced options

## Troubleshooting

- **System freezes**: Run `./debug_freeze.sh` from TTY (Ctrl+Alt+F3)
- **Monitor health**: Run `./monitor_voice_tool.sh`
- **Multiple instances**: Only one can run at a time (prevents conflicts)

## Documentation

See `docs/` folder for:
- Development setup
- Linux hotkey configuration  
- Troubleshooting guides
- Architecture documentation

## Scripts

See `scripts/` folder for:
- Installation helpers
- Auto-start configuration
- Background service setup
