# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Voice Transcription Tool v2.1 - Production-ready, GPU-accelerated speech-to-text application with global hotkeys, auto-paste functionality, and system tray mode. The project follows a modular Manager Pattern architecture where each subsystem is encapsulated in dedicated manager classes coordinated by the main GUI.

**Production Status**: 121 tests, 71% coverage, stress-tested for 8+ hours, zero memory leaks.

**v2.1 Highlights**: GPU acceleration (4x faster), Faster-Whisper engine, model size selector, system tray with notifications, visual recording feedback, enhanced error messages.

## Essential Commands

### Running the Application

```bash
# Primary method - run from project root
python main.py

# With options
python main.py --debug      # Enable verbose logging
python main.py --minimized  # Start hidden (background mode)

# Using background service manager
./voice_transcription_manager.sh --start   # Start as background service
./voice_transcription_manager.sh --stop    # Stop service
./voice_transcription_manager.sh --status  # Check status and logs
```

### Testing

**IMPORTANT**: All test commands must be run from the `voice_transcription_tool/` directory.

```bash
# Navigate to test directory
cd voice_transcription_tool/

# Run all tests (121 total)
python -m pytest tests/

# With coverage report (71% achieved)
python -m pytest tests/ --cov

# Specific test categories
python -m pytest -m unit              # Unit tests only
python -m pytest -m integration       # Integration tests only
python -m pytest -m stress            # Stress tests (resource leak detection)
python -m pytest -m "not slow"        # Skip slow tests

# Specific test files
python -m pytest tests/test_audio.py -v
python -m pytest tests/test_speech.py -v

# When adding new tests, verify they run
python -m pytest tests/test_<new_feature>.py -v
```

### Stress Testing & Validation

```bash
# Stress tests (run from voice_transcription_tool/)
cd voice_transcription_tool/
python -m pytest -m stress -v

# Memory leak detection (run from project root)
python scripts/memory_leak_test.py --cycles 1000 --log-interval 100
python scripts/memory_leak_test.py --duration 3600  # 1-hour test

# Multi-hour stability testing (run from project root)
./scripts/stability_test.sh --duration 8  # 8-hour overnight test
```

### Development & Debugging

```bash
# Install dependencies
pip install -r requirements.txt

# Monitor resource usage
./voice_transcription_tool/monitor_voice_tool.sh

# Debug system freezes (run from TTY)
./voice_transcription_tool/debug_freeze.sh

# View logs
tail -f logs/voice_transcription_*.log
```

## Architecture Overview

### Manager Pattern Design

The codebase uses a **Manager Pattern** where the main GUI (`VoiceTranscriptionApp`) orchestrates specialized manager classes. Each manager has clear responsibility boundaries and is initialized in `voice_transcription_tool/gui/main_window.py:41-70`.

**Key Managers**:
- `ConfigManager` - JSON config with validation and auto-save
- `AudioRecorder` - PyAudio wrapper for audio capture
- `AudioDeviceManager` - Device selection and management
- `SpeechEngineManager` - Multi-engine transcription (Whisper/Google with fallback)
- `HotkeyManager` - Global hotkeys via pynput (no sudo required)
- `AutoPasteManager` - xdotool integration for auto-paste
- `AudioFeedback` - Recording sound feedback
- `HealthMonitor` - Resource monitoring (CPU/memory)

### Recording Flow

```
User Hotkey (Alt+D) 
  → HotkeyManager 
  → VoiceTranscriptionApp.toggle_recording()
  → AudioRecorder.start_recording() 
  → audio_queue
  → SpeechEngineManager.transcribe() 
  → transcription_queue
  → GUI update + AutoPasteManager 
  → clipboard/paste
```

### Module Structure

```
voice_transcription_tool/
├── main.py                 # Entry point with process locking
├── config/settings.py      # ConfigManager - JSON config
├── audio/
│   ├── recorder.py         # AudioRecorder - PyAudio wrapper
│   ├── devices.py          # AudioDeviceManager
│   └── feedback.py         # AudioFeedback - recording sounds
├── speech/engines.py       # SpeechEngineManager (Whisper/Google)
├── gui/main_window.py      # VoiceTranscriptionApp - main coordinator
└── utils/
    ├── hotkeys.py          # HotkeyManager - pynput global shortcuts
    ├── autopaste.py        # AutoPasteManager - xdotool integration
    ├── health_monitor.py   # HealthMonitor - resource monitoring
    └── logger.py           # Logging setup
```

### Thread Architecture

- **Main Thread**: Tkinter GUI, hotkey callbacks
- **Background Threads**: Audio recording, transcription processing, health monitoring
- **Synchronization**: Thread-safe queues, `Tkinter.after()` for GUI updates from background threads
- **Process Lock**: `/tmp/voice_transcription.lock` prevents multiple instances

## Configuration

### Persistent Files

- Configuration: `voice_transcription_config.json` (root and module directory)
- Logs: `logs/voice_transcription_*.log`
- Process Lock: `/tmp/voice_transcription.lock` (remove manually if app crashes)

### Default Settings

- Hotkey: `Alt+D` (record toggle)
- Audio: 16kHz, mono, 30s max recording
- Engine: Whisper (local) preferred, Google Speech (cloud) fallback
- Health Limits: 2048MB memory, 98% CPU, 30s check interval
- Auto-paste: Enabled by default

## Critical System Dependencies

**Must Have**:
- **FFmpeg** - Critical for Whisper audio processing: `sudo apt install ffmpeg`
- **xdotool** - Auto-paste functionality (Linux): `sudo apt install xdotool`
- **Python 3.7+** with tkinter: `sudo apt install python3-tk`
- **At least one speech engine**:
  - Whisper (`openai-whisper`) - Recommended, local, GPU-accelerated
  - Google Speech (`SpeechRecognition`) - Cloud-based, requires internet

**Key Python Packages**:
- `pynput` - Global hotkeys without sudo (replaced `keyboard` library)
- `pyaudio` - Audio recording
- `pygame` - Audio feedback
- `torch` - Required for Whisper
- `psutil` - Resource monitoring (optional but recommended)

## Common Development Tasks

### Adding a New Manager Component

1. Create manager class in appropriate module (`audio/`, `speech/`, `utils/`)
2. Initialize in `VoiceTranscriptionApp.__init__()` (`gui/main_window.py:41-70`)
3. Add configuration fields to `ConfigManager` if needed
4. Create unit tests in `tests/test_<module>.py`
5. Add integration test if it interacts with other managers

### Adding a New Speech Engine

1. Inherit from `SpeechEngine` ABC (`speech/engines.py:15`)
2. Implement `transcribe()`, `is_available()`, `get_name()` methods
3. Register in `SpeechEngineManager._init_engines()` (`speech/engines.py:38`)
4. Add dependency check in `main.py:check_dependencies()`
5. Add tests in `tests/test_speech.py`

### Adding a New Hotkey

1. Register in `HotkeyManager` (`utils/hotkeys.py`)
2. Add callback in `VoiceTranscriptionApp._setup_hotkeys()` (`gui/main_window.py:176`)
3. Add to default config in `ConfigManager`
4. Update GUI settings dialog

## Testing Philosophy

The project has comprehensive testing with 114 tests achieving 74% coverage:

- **Unit tests**: Individual manager components with mocked dependencies
- **Integration tests**: Component interaction (e.g., AudioRecorder → SpeechEngineManager)
- **Stress tests**: 1000-cycle resource leak detection, memory monitoring, crash resilience

**Test Organization**:
- Test files: `voice_transcription_tool/tests/test_<module>.py`
- Configuration: `voice_transcription_tool/pytest.ini`
- Fixtures: `voice_transcription_tool/tests/conftest.py`

**Available Test Markers** (from pytest.ini):
- `unit` - Unit tests for individual components
- `integration` - Integration tests for component interaction
- `slow` - Tests that take longer to run
- `stress` - Stress tests for production validation
- `requires_audio` - Tests requiring audio hardware
- `requires_internet` - Tests requiring internet connection

**Coverage Breakdown**:
- Audio module: 100%
- Speech module: 85%
- Config module: 92%
- Utils module: 68%
- GUI module: 51%

## Important Implementation Notes

### Process Lock Mechanism

The application uses `fcntl` file locking (`voice_transcription_tool/main.py:30`) to prevent multiple instances. **If the app crashes, manually remove** `/tmp/voice_transcription.lock` before restarting.

### Hotkey Implementation (Linux)

Uses `pynput` instead of `keyboard` library to avoid sudo requirements. See `docs/LINUX_HOTKEY_SOLUTION.md` for migration details.

### Auto-Paste Focus Management

Captures active window before recording (`utils/autopaste.py:55`), then restores focus before pasting to prevent GUI stealing focus. Terminal apps use `Ctrl+Shift+V` instead of `Ctrl+V`. Browser detection prevents address bar focus issues.

### Secure Temporary Files

Uses `tempfile.NamedTemporaryFile(delete=False)` instead of deprecated `mktemp()` to avoid race condition vulnerabilities (`audio/recorder.py:232`).

### Health Monitor Warning System

Monitors CPU/memory every 30s. Logs warnings on limit breach (2048MB memory, 98% CPU). Emergency callback is optional (`utils/health_monitor.py:14`).

## Troubleshooting

### Common Issues

- **"FFmpeg not found"**: `sudo apt install ffmpeg`
- **Auto-paste not working**: `sudo apt install xdotool`
- **"Another instance running"**: `rm /tmp/voice_transcription.lock`
- **System freezes**: Run `voice_transcription_tool/debug_freeze.sh` from TTY

See `docs/TROUBLESHOOTING.md` for comprehensive debugging guide.

## Known Limitations

- Tkinter GUI (simple by design for stability)
- xdotool auto-paste is Linux-only (Windows/macOS support planned)
- No CI/CD pipeline (GitHub Actions planned)

## Version History

### v2.1 (Current) - Performance & UX Enhancements

**Release Date**: 2025-10

**Major Features**:
- **GPU Acceleration**: Automatic CUDA/cuDNN detection with CPU fallback
- **Faster-Whisper Integration**: CTranslate2 optimization for 4x transcription speedup
- **Model Size Selector**: Choose tiny/base/small/medium/large models
- **System Tray Mode**: Background operation with desktop notifications
- **Visual Feedback**: Audio level meter, pulsing recording banner, live RMS display
- **Enhanced Error Messages**: User-friendly error dialogs with recovery guidance
- **Keyboard Shortcuts**: Ctrl+R (record), Ctrl+C (copy), Ctrl+Q (quit), Esc (stop)

**Technical Improvements**:
- RMS throttling (90% CPU reduction during recording)
- GPU device detection with FP16/FP32 automatic selection
- TrayManager with programmatic icon generation
- Error message system with actionable recovery steps
- 121 tests (up from 114), 71% coverage

**Files Added**:
- `utils/error_messages.py` - Centralized error handling
- `utils/tray_manager.py` - System tray with notifications

**Compatibility**: All v2.0 configurations forward-compatible. GPU features optional (auto-fallback to CPU).

---

### v2.0 - Production-Ready Refactor

**Release Date**: 2024

**Major Changes**:
- Modular Manager Pattern architecture (49% LOC reduction)
- 114 tests with 74% coverage
- 8-hour stability validation, zero memory leaks
- Comprehensive error handling and logging

**Removed Features** (Simplification):
- Wake word detection (experimental)
- Voice training database (experimental)
- `pyautogui` dependency (replaced with xdotool)

## Migration Notes

This is a v2.1 codebase with modular architecture. Previous versions (v1.0) were monolithic. Code comments may reference "MIGRATION STEP X" - these document the v1.0 → v2.0 refactoring and can be ignored for new development.
