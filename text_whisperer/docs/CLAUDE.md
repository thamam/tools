# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Voice Transcription Tool - A modular speech-to-text application with global hotkeys, voice training, and multiple speech recognition engines. This is a refactored version (v2.0) with a clean, modular architecture.

## Key Commands

### Running the Application
```bash
# Run from project root
python main.py  # Uses delegation to voice_transcription_tool/main.py

# Or directly from the module
python voice_transcription_tool/main.py

# With command line options
python main.py --debug      # Enable verbose logging
python main.py --minimized  # Start hidden in system tray
python main.py --no-tray    # Disable system tray

# Run from anywhere (if installed with pip install -e .)
voice-transcription
```

### Development Commands
```bash
# Install dependencies (from project root)
pip install -r requirements.txt  # This installs voice_transcription_tool/requirements.txt

# Run tests
cd voice_transcription_tool/
python -m pytest tests/           # Run all tests
python -m pytest tests/ -v       # Verbose output
python -m pytest tests/test_audio.py  # Run specific test file

# No linting/formatting configuration exists yet
```

## Architecture Overview

The codebase follows a modular architecture with clear separation of concerns:

### Core Modules

- **main.py**: Root entry point that delegates to voice_transcription_tool/main.py
- **voice_transcription_tool/main.py**: Application entry point with process locking and dependency checks
- **config/**: Configuration and persistence
  - `settings.py`: ConfigManager for JSON config file management
  - `database.py`: DatabaseManager for SQLite voice training data
- **audio/**: Audio capture and management
  - `recorder.py`: AudioRecorder handles cross-platform recording with PyAudio
  - `devices.py`: AudioDeviceManager for input device selection
  - `feedback.py`: AudioFeedback for recording start/stop sounds
- **speech/**: Speech recognition
  - `engines.py`: SpeechEngineManager with Whisper (local) and Google Speech (cloud) support
  - `training.py`: VoiceTrainer for improving recognition accuracy
- **gui/**: User interface
  - `main_window.py`: VoiceTranscriptionApp - main Tkinter window with tabbed interface
- **utils/**: Utilities
  - `hotkeys.py`: HotkeyManager using pynput for cross-platform global shortcuts
  - `autopaste.py`: AutoPasteManager for automatic text insertion
  - `system_tray.py`: SystemTrayManager with pystray for tray functionality
  - `wake_word.py`: Wake word detection (optional feature)
  - `health_monitor.py`: Resource usage monitoring
  - `logger.py`: Logging setup and debug message handling

### Key Design Patterns

1. **Manager Classes**: Each subsystem has a manager (AudioRecorder, SpeechEngineManager, etc.) that encapsulates functionality
2. **Abstract Base Classes**: Speech engines inherit from SpeechEngine ABC for consistent interface
3. **Queue-based Threading**: Audio processing and transcription use queues for thread communication
4. **Callback Pattern**: Debug messages use callbacks to update GUI from other modules
5. **Singleton Lock**: Process lock in main.py prevents multiple instances

### Critical Integration Points

- GUI main_window.py coordinates all managers and handles user interaction
- Audio data flows: AudioRecorder → Queue → SpeechEngineManager → GUI display
- Configuration is loaded by ConfigManager and used throughout the application
- Voice training data is stored in SQLite via DatabaseManager
- Global hotkeys are managed by pynput without requiring sudo on Linux

### Global State

- Configuration file: `voice_transcription_config.json`
- Database file: `voice_transcriptions.db`
- Log files: `logs/voice_transcription_*.log`
- Default hotkeys:
  - Alt+D: Start/stop recording
  - Alt+S: Open settings
  - Alt+W: Toggle wake word
- Process lock: `/tmp/voice_transcription.lock`

### Dependencies

**System Requirements**:
- FFmpeg: Required for Whisper audio processing
- xdotool (Linux): Required for auto-paste functionality

**Speech Engines** (at least one required):
- **Whisper**: Local processing, more accurate, requires more resources
- **Google Speech**: Cloud-based, faster, requires internet

**Key Python Dependencies**:
- pynput: Cross-platform hotkeys without sudo
- pyaudio: Audio recording
- pygame: Audio feedback sounds
- pystray + pillow: System tray functionality
- torch: Required for Whisper
- pyperclip: Clipboard operations
- tkinter: GUI (usually pre-installed with Python)