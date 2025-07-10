# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Voice Transcription Tool - A modular speech-to-text application with global hotkeys, voice training, and multiple speech recognition engines. This is a refactored version (v2.0) with a clean, modular architecture.

## Key Commands

### Running the Application
```bash
# Run the main application
python voice_transcription_tool/main.py

# Or with debug mode
python voice_transcription_tool/main.py --debug

# Run as installed package (if installed with pip install -e .)
voice-transcription
```

### Development Commands
```bash
# Install dependencies
pip install -r voice_transcription_tool/requirements.txt

# Check if a specific module loads correctly
python -c "from audio.recorder import AudioRecorder; print('Audio OK')"

# No test suite exists yet - tests would go in tests/ directory
# No linting/formatting configuration exists yet
```

## Architecture Overview

The codebase follows a modular architecture with clear separation of concerns:

### Core Modules

- **main.py**: Entry point that checks dependencies and starts the GUI application
- **config/**: Configuration and persistence
  - `settings.py`: ConfigManager for JSON config file management
  - `database.py`: DatabaseManager for SQLite voice training data
- **audio/**: Audio capture and management
  - `recorder.py`: AudioRecorder handles cross-platform recording
  - `devices.py`: AudioDeviceManager for input device selection
- **speech/**: Speech recognition
  - `engines.py`: SpeechEngineManager with Whisper and Google Speech support
  - `training.py`: VoiceTrainer for improving recognition accuracy
- **gui/**: User interface
  - `main_window.py`: VoiceTranscriptionApp - main Tkinter window
- **utils/**: Utilities
  - `hotkeys.py`: HotkeyManager for global keyboard shortcuts
  - `logger.py`: Logging setup and debug message handling

### Key Design Patterns

1. **Manager Classes**: Each subsystem has a manager (AudioRecorder, SpeechEngineManager, etc.) that encapsulates functionality
2. **Abstract Base Classes**: Speech engines inherit from SpeechEngine ABC for consistent interface
3. **Queue-based Threading**: Audio processing and transcription use queues for thread communication
4. **Callback Pattern**: Debug messages use callbacks to update GUI from other modules

### Critical Integration Points

- GUI main_window.py coordinates all managers and handles user interaction
- Audio data flows: AudioRecorder → Queue → SpeechEngineManager → GUI display
- Configuration is loaded by ConfigManager and used throughout the application
- Voice training data is stored in SQLite via DatabaseManager

### Global State

- Configuration file: `voice_transcription_config.json`
- Database file: `voice_transcriptions.db`
- Log files: `logs/voice_transcription_*.log`
- Default hotkey: F9 (configurable)

### Dependencies

The application supports two speech engines:
- **Whisper**: Local processing, more accurate, requires more resources
- **Google Speech**: Cloud-based, faster, requires internet

At least one must be installed for the app to function.