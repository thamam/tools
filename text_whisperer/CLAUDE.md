# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Voice Transcription Tool (v2.0) - A modular speech-to-text application with global hotkeys, system tray integration, wake word detection, and auto-paste functionality. The project underwent a major refactoring from a monolithic architecture to a clean, modular design.

## Key Commands

### Running the Application
```bash
# Primary method - run from project root
python main.py

# With command line options
python main.py --debug      # Enable verbose logging
python main.py --minimized  # Start hidden in system tray
python main.py --no-tray    # Disable system tray

# Using the manager script (background service)
./voice_transcription_manager.sh --start   # Start in background
./voice_transcription_manager.sh --stop    # Stop background process
./voice_transcription_manager.sh --restart # Restart service
./voice_transcription_manager.sh --status  # Check status and logs
```

### Development Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests (must be in voice_transcription_tool directory)
cd voice_transcription_tool/
python -m pytest tests/              # All tests (73 total)
python -m pytest tests/ -v           # Verbose output
python -m pytest tests/ --cov        # With coverage report
python -m pytest tests/test_audio.py # Specific test file
python -m pytest -m unit             # Only unit tests
python -m pytest -m integration      # Only integration tests

# Test markers available:
# -m unit              Unit tests for individual components
# -m integration       Integration tests for component interaction
# -m slow              Tests that take longer to run
# -m requires_audio    Tests requiring audio hardware
# -m requires_internet Tests requiring internet connection
```

### Monitoring & Debugging
```bash
# Monitor resource usage
./voice_transcription_tool/monitor_voice_tool.sh

# Debug system freezes (run from TTY)
./voice_transcription_tool/debug_freeze.sh

# Check logs
tail -f logs/voice_transcription_*.log
```

## Architecture Overview

### Modular Design Pattern

The codebase follows a **Manager Pattern** architecture where each subsystem is encapsulated in a dedicated manager class. The main GUI (VoiceTranscriptionApp) coordinates all managers but doesn't implement their functionality.

**Key Integration Point**: `voice_transcription_tool/gui/main_window.py:53` - VoiceTranscriptionApp class that orchestrates all managers.

### Core Module Structure

```
voice_transcription_tool/
├── main.py                 # Entry point with process locking
├── config/                 # Configuration & persistence
│   ├── settings.py         # ConfigManager - JSON config
│   └── database.py         # DatabaseManager - SQLite for voice training
├── audio/                  # Audio capture & feedback
│   ├── recorder.py         # AudioRecorder - PyAudio wrapper
│   ├── devices.py          # AudioDeviceManager - device selection
│   └── feedback.py         # AudioFeedback - recording sounds
├── speech/                 # Speech recognition
│   ├── engines.py          # SpeechEngineManager (Whisper/Google)
│   └── training.py         # VoiceTrainer - accuracy improvement
├── gui/                    # User interface
│   └── main_window.py      # VoiceTranscriptionApp - main coordinator
└── utils/                  # Utilities
    ├── hotkeys.py          # HotkeyManager - pynput global shortcuts
    ├── autopaste.py        # AutoPasteManager - xdotool integration
    ├── system_tray.py      # SystemTrayManager - pystray integration
    ├── wake_word.py        # WakeWordDetector - voice activation
    ├── health_monitor.py   # HealthMonitor - resource monitoring
    └── logger.py           # Logging setup and debug handling
```

### Critical Design Patterns

1. **Manager Classes**: Each subsystem has a manager (AudioRecorder, SpeechEngineManager, etc.) with clear responsibility boundaries
2. **Abstract Base Classes**: Speech engines inherit from SpeechEngine ABC (`speech/engines.py:15`)
3. **Queue-based Threading**: Audio processing uses queues for thread-safe communication between recorder → speech engine → GUI
4. **Callback Pattern**: Debug messages and events use callbacks to update GUI from background threads
5. **Singleton Process Lock**: `/tmp/voice_transcription.lock` prevents multiple instances (`voice_transcription_tool/main.py:32`)

### Data Flow Architecture

**Recording Flow**:
```
User Hotkey → HotkeyManager → VoiceTranscriptionApp.toggle_recording()
→ AudioRecorder.start_recording() → audio_queue
→ SpeechEngineManager.transcribe() → transcription_queue
→ GUI update + AutoPasteManager → clipboard/paste
```

**Configuration Flow**:
```
ConfigManager.load() → voice_transcription_config.json
→ Distributed to managers on init
→ ConfigManager.save() on settings change
```

**Voice Training Flow**:
```
User correction → VoiceTrainer.add_correction()
→ DatabaseManager → voice_transcriptions.db (SQLite)
→ VoiceTrainer.get_suggestions() for future transcriptions
```

### Thread Safety Considerations

- **Main Thread**: GUI (Tkinter), system tray updates, hotkey callbacks
- **Background Threads**: Audio recording, transcription processing, wake word detection, health monitoring
- **Synchronization**: queues (thread-safe), Tkinter.after() for GUI updates from background threads
- **Critical Section**: Recording state changes protected by flag checks before queue operations

### Global State & Configuration

**Persistent Files**:
- Configuration: `voice_transcription_config.json` (root and module directory)
- Database: `voice_transcriptions.db` (SQLite for voice training data)
- Logs: `logs/voice_transcription_*.log`
- Process Lock: `/tmp/voice_transcription.lock`

**Default Settings**:
- Hotkeys: Alt+D (record), Alt+S (settings), Alt+W (wake word)
- Audio: 16kHz, mono, 30s max recording
- Engine: Whisper (local) preferred, Google Speech (cloud) fallback
- Health Limits: 1024MB memory, 95% CPU, 30s check interval

## System Dependencies

**Required**:
- FFmpeg - Audio processing for Whisper (critical dependency)
- xdotool (Linux) - Auto-paste functionality
- Python 3.7+ with tkinter

**Speech Engines** (at least one required):
- Whisper (openai-whisper) - Local processing, more accurate, GPU-accelerated
- Google Speech (SpeechRecognition) - Cloud-based, faster, requires internet

**Key Python Packages**:
- pynput - Cross-platform global hotkeys **without sudo requirement**
- pyaudio - Audio recording interface
- pygame - Audio feedback sounds
- pystray + pillow - System tray functionality
- torch - Required for Whisper engine
- psutil - Resource monitoring (optional but recommended)

## Testing Philosophy

The project has 73 comprehensive tests with ~45% code coverage. Tests are organized by:

- **Unit tests**: Individual manager components in isolation with mocked dependencies
- **Integration tests**: Component interaction (e.g., AudioRecorder → SpeechEngineManager)
- **Mock strategy**: External dependencies (PyAudio, Whisper API, file I/O) are mocked to enable CI/CD

**Test Configuration**: `voice_transcription_tool/pytest.ini` - markers, test discovery, output formatting

## Important Implementation Notes

### Process Lock Mechanism
The application uses fcntl file locking (`voice_transcription_tool/main.py:32`) to prevent multiple instances. If the application crashes, the lock file may persist and must be manually removed.

### Hotkey Implementation on Linux
Uses pynput instead of keyboard library to avoid sudo requirements. See `docs/LINUX_HOTKEY_SOLUTION.md` for migration details.

### Auto-Paste Focus Management
Captures active window before recording (`utils/autopaste.py:45`), then restores focus before pasting to prevent GUI from stealing focus. Terminal applications use Ctrl+Shift+V instead of Ctrl+V.

### Wake Word Detection
Dual implementation with graceful fallback:
- Primary: openWakeWord library (more accurate, optional dependency)
- Fallback: SimpleWakeWordDetector (energy-based, always available)

### Health Monitor Emergency Cleanup
Monitors CPU/memory usage every 30s. On limit breach, triggers emergency callback to prevent system freeze (`utils/health_monitor.py:14`).

## Migration Context

This is a v2.0 refactored codebase. Previous version was monolithic (`voice_transcription.py`). Comments in code reference "MIGRATION STEP X" showing the refactoring process. These can be ignored for new development.

## Common Development Patterns

### Adding a New Manager Component
1. Create manager class in appropriate module (audio/, speech/, utils/)
2. Initialize in `VoiceTranscriptionApp.__init__()` (`gui/main_window.py:61`)
3. Add configuration fields to ConfigManager if needed
4. Create unit tests in `tests/test_*.py`
5. Add integration test if it interacts with other managers

### Adding a New Speech Engine
1. Inherit from `SpeechEngine` ABC (`speech/engines.py:15`)
2. Implement `transcribe()`, `is_available()`, `get_name()` methods
3. Register in `SpeechEngineManager._init_engines()` (`speech/engines.py:38`)
4. Add dependency check in `main.py:check_dependencies()`

### Adding a New Hotkey
1. Register in `HotkeyManager` (`utils/hotkeys.py`)
2. Add callback in `VoiceTranscriptionApp._setup_hotkeys()` (`gui/main_window.py`)
3. Add to default config in `ConfigManager`
4. Update GUI settings tab for configuration

## Known Limitations

- Tkinter GUI (planned migration to CustomTkinter for modern look)
- No CI/CD pipeline (GitHub Actions planned)
- System tray icons require X11 (no Wayland support yet)
- Wake word detection not production-ready (experimental feature)
- Test coverage at 45% (target: 70%+)

## Future Enhancements

See `docs/IMPROVEMENT_PLAN.md` for detailed roadmap. Key pending items:
- Modern GUI redesign (CustomTkinter/ttkbootstrap)
- Ubuntu desktop integration (.deb package)
- CI/CD with GitHub Actions
- Improved test coverage
