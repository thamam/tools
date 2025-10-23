# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Voice Transcription Tool (v2.0) - A production-ready, modular speech-to-text application with global hotkeys and auto-paste functionality. The project underwent a major refactoring from a monolithic architecture to a clean, modular design focused on core functionality.

**Production Readiness**: This codebase has been streamlined by removing experimental features (wake word detection, voice training, system tray) to focus on bulletproof core functionality with 74% test coverage.

## Key Commands

### Running the Application
```bash
# Primary method - run from project root
python main.py

# With command line options
python main.py --debug      # Enable verbose logging

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
python -m pytest tests/              # All tests (114 total)
python -m pytest tests/ -v           # Verbose output
python -m pytest tests/ --cov        # With coverage report (74%)
python -m pytest tests/test_audio.py # Specific test file
python -m pytest -m unit             # Only unit tests
python -m pytest -m integration      # Only integration tests

# Test markers available:
# -m unit              Unit tests for individual components
# -m integration       Integration tests for component interaction
# -m slow              Tests that take longer to run
# -m stress            Stress tests for production readiness validation
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

### Phase 5 Stability Testing (Production Validation)
```bash
# Stress tests - resource leak detection
cd voice_transcription_tool/
python -m pytest -m stress              # Run all stress tests
python -m pytest tests/test_stress.py -v  # Verbose stress test output

# Memory leak detection
python scripts/memory_leak_test.py --cycles 1000 --log-interval 100
python scripts/memory_leak_test.py --duration 3600  # 1-hour test

# Multi-hour stability testing
./scripts/stability_test.sh --duration 8 --interval 300  # 8-hour test
./scripts/stability_test.sh --duration 4                 # 4-hour test

# Review stability reports
cat logs/stability_test_*.log
cat logs/memory_leak_report_*.json
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
│   └── settings.py         # ConfigManager - JSON config with validation
├── audio/                  # Audio capture & feedback
│   ├── recorder.py         # AudioRecorder - PyAudio wrapper
│   ├── devices.py          # AudioDeviceManager - device selection
│   └── feedback.py         # AudioFeedback - recording sounds
├── speech/                 # Speech recognition
│   └── engines.py          # SpeechEngineManager (Whisper/Google with fallback)
├── gui/                    # User interface
│   └── main_window.py      # VoiceTranscriptionApp - main coordinator
└── utils/                  # Utilities
    ├── hotkeys.py          # HotkeyManager - pynput global shortcuts
    ├── autopaste.py        # AutoPasteManager - xdotool integration
    ├── health_monitor.py   # HealthMonitor - resource monitoring
    └── logger.py           # Logging setup and debug handling
```

**Removed Modules** (Phase 1 Simplification):
- `config/database.py` - DatabaseManager removed (SQLite voice training)
- `speech/training.py` - VoiceTrainer removed (experimental feature)
- `utils/system_tray.py` - SystemTrayManager stubbed (Qt threading conflicts)
- `utils/wake_word.py` - WakeWordDetector removed (experimental feature)

### Critical Design Patterns

1. **Manager Classes**: Each subsystem has a manager (AudioRecorder, SpeechEngineManager, etc.) with clear responsibility boundaries
2. **Abstract Base Classes**: Speech engines inherit from SpeechEngine ABC (`speech/engines.py:15`)
3. **Queue-based Threading**: Audio processing uses queues for thread-safe communication between recorder → speech engine → GUI
4. **Callback Pattern**: Debug messages and events use callbacks to update GUI from background threads
5. **Singleton Process Lock**: `/tmp/voice_transcription.lock` prevents multiple instances (`voice_transcription_tool/main.py:32`)

### Data Flow Architecture

**Recording Flow**:
```
User Hotkey (Alt+D) → HotkeyManager → VoiceTranscriptionApp.toggle_recording()
→ AudioRecorder.start_recording() → audio_queue
→ SpeechEngineManager.transcribe() → transcription_queue
→ GUI update + AutoPasteManager → clipboard/paste
```

**Configuration Flow**:
```
ConfigManager.load() → voice_transcription_config.json (with validation)
→ Distributed to managers on init
→ ConfigManager.save() on settings change (auto-save)
```

### Thread Safety Considerations

- **Main Thread**: GUI (Tkinter), hotkey callbacks
- **Background Threads**: Audio recording, transcription processing, health monitoring
- **Synchronization**: queues (thread-safe), Tkinter.after() for GUI updates from background threads
- **Critical Section**: Recording state changes protected by flag checks before queue operations

### Global State & Configuration

**Persistent Files**:
- Configuration: `voice_transcription_config.json` (root and module directory)
- Logs: `logs/voice_transcription_*.log`
- Process Lock: `/tmp/voice_transcription.lock`

**Default Settings**:
- Hotkey: Alt+D (record toggle)
- Audio: 16kHz, mono, 30s max recording
- Engine: Whisper (local) preferred, Google Speech (cloud) fallback
- Health Limits: 2048MB memory, 98% CPU, 30s check interval
- Auto-paste: Enabled by default (can be disabled in settings)

## System Dependencies

**Required**:
- FFmpeg - Audio processing for Whisper (critical dependency)
- xclip (Linux) - Clipboard functionality
- xdotool (Linux) - Auto-paste functionality
- Python 3.7+ with tkinter

**Speech Engines** (at least one required):
- Whisper (openai-whisper) - Local processing, more accurate, GPU-accelerated
- Google Speech (SpeechRecognition) - Cloud-based, faster, requires internet

**Key Python Packages**:
- pynput - Cross-platform global hotkeys **without sudo requirement**
- pyaudio - Audio recording interface
- pygame - Audio feedback sounds
- torch - Required for Whisper engine
- psutil - Resource monitoring (optional but recommended)

**Removed Dependencies** (Phase 1 Simplification):
- ~~pystray + pillow~~ - System tray removed (Qt threading conflicts)
- ~~pyautogui~~ - Replaced with xdotool (no Qt conflicts)
- ~~openwakeword + onnxruntime~~ - Wake word detection removed

## Testing Philosophy

The project has 114 comprehensive tests with 74% code coverage (exceeded 70% target). Tests are organized by:

- **Unit tests**: Individual manager components in isolation with mocked dependencies
- **Integration tests**: Component interaction (e.g., AudioRecorder → SpeechEngineManager)
- **Stress tests** (Phase 5): 1000-cycle resource leak detection, memory monitoring, crash resilience
- **Mock strategy**: External dependencies (PyAudio, Whisper API, file I/O) are mocked to enable CI/CD

**Test Configuration**: `voice_transcription_tool/pytest.ini` - markers, test discovery, output formatting

**Coverage Breakdown**:
- Audio module: 100% coverage
- Speech module: 85% coverage
- Config module: 92% coverage
- GUI module: 51% coverage
- Utils module: 68% coverage

### Phase 5 Stress Testing Infrastructure

**Stress Test Suite** (`tests/test_stress.py`):
- `test_1000_recording_cycles` - Memory leak detection over 1000 start/stop cycles
- `test_rapid_hotkey_presses` - Race condition validation with rapid toggles
- `test_long_recording_cycles` - Large audio buffer handling (30s recordings)
- `test_concurrent_start_attempts` - Thread safety under concurrent load
- `test_transcription_memory_leak` - Garbage collection validation for transcription results
- `test_config_save_memory_leak` - File handle cleanup validation
- `test_recovery_from_intermittent_failures` - Error resilience and recovery

**Memory Leak Detector** (`scripts/memory_leak_test.py`):
- Baseline memory establishment with forced garbage collection
- Cycle-based testing: 1000+ recording cycles with periodic sampling
- Duration-based testing: Multi-hour monitoring with configurable intervals
- JSON report generation with memory growth metrics
- 20% growth threshold validation (detects slow accumulation)

**Stability Test Script** (`scripts/stability_test.sh`):
- Multi-hour background testing (default 8 hours)
- Crash detection and automatic restart
- Resource monitoring (memory/CPU) every 5 minutes
- Comprehensive reporting with success rates
- Log aggregation for post-mortem analysis

**Validation Criteria**:
- Zero crashes over 8-hour stability test
- Memory growth < 20% over 1000 cycles
- Error count < 5 per 100 log lines
- Successful recovery from intermittent failures

**Test Execution**:
```bash
# Quick stress validation (3-5 minutes)
python -m pytest -m stress

# Extended memory leak detection (1 hour)
python scripts/memory_leak_test.py --duration 3600

# Production stability validation (8 hours, run overnight)
./scripts/stability_test.sh --duration 8
```

## Important Implementation Notes

### Process Lock Mechanism
The application uses fcntl file locking (`voice_transcription_tool/main.py:32`) to prevent multiple instances. If the application crashes, the lock file may persist and must be manually removed.

### Hotkey Implementation on Linux
Uses pynput instead of keyboard library to avoid sudo requirements. See `docs/LINUX_HOTKEY_SOLUTION.md` for migration details.

### Auto-Paste Focus Management
Captures active window before recording (`utils/autopaste.py:55`), then restores focus before pasting to prevent GUI from stealing focus. Terminal applications use Ctrl+Shift+V instead of Ctrl+V. Browser detection prevents address bar focus issues.

### Health Monitor Warning System
Monitors CPU/memory usage every 30s. On limit breach (2048MB memory, 98% CPU), logs warnings and provides optional emergency callback (`utils/health_monitor.py:14`).

### Secure Temporary Files
Uses `tempfile.NamedTemporaryFile(delete=False)` instead of deprecated `mktemp()` to avoid race condition vulnerabilities (`audio/recorder.py:232`).

## Migration Context

This is a v2.0 refactored codebase. Previous version was monolithic (`voice_transcription.py`). Comments in code reference "MIGRATION STEP X" showing the refactoring process. These can be ignored for new development.

**Phase 1 Simplification** removed 3,759 LOC (49% reduction) by removing experimental features to focus on production-ready core functionality.

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
4. Update GUI settings dialog for configuration

## Known Limitations

- Tkinter GUI (simple by design for production stability)
- No CI/CD pipeline (GitHub Actions planned for Phase 6)
- xdotool auto-paste Linux-only (Windows/macOS support planned)

## Production Readiness Status

**Completed Phases**:
- ✅ Phase 1: Feature removal & simplification (removed 3,759 LOC)
- ✅ Phase 2: Resource management fixes (clean shutdown, thread lifecycle)
- ✅ Phase 3: Error handling improvements (zero silent failures)
- ✅ Phase 4: Test coverage to 74% (exceeded 70% target, 114 tests)
- ✅ Phase 5: Stability & stress testing (7 stress tests, memory leak detection, 8-hour stability validation)

**Current Phase**:
- ⏳ Phase 6: Documentation & polish (in progress)
  - ✅ README.md updated with production-ready features
  - ✅ INSTALLATION.md comprehensive guide created
  - ✅ TROUBLESHOOTING.md diagnostic guide created
  - ⏳ Migration comment cleanup pending
  - ⏳ Final production release pending

**Phase 5 Achievements**:
- 7 comprehensive stress tests covering memory leaks, race conditions, thread safety
- Standalone memory leak detector with JSON reporting
- Multi-hour stability testing script with crash detection
- Validation: 0 crashes, <20% memory growth, error recovery confirmed

## Future Enhancements

Post-v2.0 roadmap:
- Installation packaging (.deb for Ubuntu)
- CI/CD with GitHub Actions
- Windows/macOS auto-paste support (currently Linux-only via xdotool)
- Additional speech engine support (Azure, AWS Transcribe)
