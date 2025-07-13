# Voice Transcription Tool

Professional speech-to-text application with global hotkeys, system tray, and auto-paste functionality.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Linux users also need:
sudo apt install xdotool

# Run the application
python main.py
```

## Usage

- **Alt+D**: Start/stop recording
- **Alt+S**: Open settings  
- **Alt+W**: Toggle wake word detection

## Features

🎤 **Global Hotkeys** - Record from anywhere (no sudo required)  
🖥️ **System Tray** - Visual recording timer and status  
📋 **Auto-paste** - Automatically paste transcribed text  
🔊 **Audio Feedback** - Sound notifications  
🧠 **Multiple Engines** - Whisper (local) or Google Speech (cloud)  
🎯 **Wake Word** - Hands-free "Hey Computer" activation  
🎨 **Modern GUI** - Tabbed interface with advanced options  

## Command Line Options

```bash
python main.py --help           # Show all options
python main.py --minimized     # Start hidden in system tray
python main.py --debug         # Enable verbose logging
python main.py --no-tray       # Disable system tray
```

## Project Structure

- `voice_transcription_tool/` - Core application code
- `docs/` - Documentation and guides
- `scripts/` - Helper and setup scripts  
- `dist/` - Build artifacts and packages

## Troubleshooting

- **System freezes**: Run `voice_transcription_tool/debug_freeze.sh` from TTY
- **Monitor health**: Run `voice_transcription_tool/monitor_voice_tool.sh`
- See `docs/` for detailed guides

## Development

```bash
cd voice_transcription_tool/
python -m pytest tests/    # Run tests
python main.py --debug     # Debug mode
```
