# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Voice Transcription Tool (v2.1) - A production-ready, GPU-accelerated speech-to-text application with global hotkeys and auto-paste functionality. The project underwent a major refactoring from monolithic to modular architecture, with ongoing v2.1 enhancements adding GPU acceleration and UX improvements.

**Production Readiness**: Streamlined codebase with 74% test coverage (114 tests), comprehensive stress testing, and zero memory leaks over 8-hour stability validation.

## Key Commands

### Running the Application
```bash
# Primary method - run from project root (text_whisperer/)
cd text_whisperer/
python main.py

# From voice_transcription_tool/ subdirectory
cd voice_transcription_tool/
python main.py

# With command line options
python main.py --debug      # Enable verbose logging
python main.py --minimized  # Start hidden (background mode)

# Using the manager script (background service)
./voice_transcription_manager.sh --start   # Start in background
./voice_transcription_manager.sh --stop    # Stop background process
./voice_transcription_manager.sh --restart # Restart service
./voice_transcription_manager.sh --status  # Check status and logs
```

### Development Commands
```bash
# Install dependencies (from voice_transcription_tool/)
cd voice_transcription_tool/
pip install -r requirements.txt

# Run tests (MUST be in voice_transcription_tool directory)
cd voice_transcription_tool/
python -m pytest tests/              # All tests (114 total)
python -m pytest tests/ -v           # Verbose output
python -m pytest tests/ --cov        # With coverage report (74%)
python -m pytest tests/test_audio.py # Specific test file
python -m pytest -m unit             # Only unit tests
python -m pytest -m integration      # Only integration tests
python -m pytest -m stress           # Stress tests (Phase 5)

# Test markers available:
# -m unit              Unit tests for individual components
# -m integration       Integration tests for component interaction
# -m slow              Tests that take longer to run
# -m stress            Stress tests for production readiness
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

### Stress Testing & Validation
```bash
# Stress tests - resource leak detection
cd voice_transcription_tool/
python -m pytest -m stress -v

# Memory leak detection (run from repo root)
cd ../
python scripts/memory_leak_test.py --cycles 1000 --log-interval 100
python scripts/memory_leak_test.py --duration 3600  # 1-hour test

# Multi-hour stability testing
./scripts/stability_test.sh --duration 8 --interval 300  # 8-hour test

# Review stability reports
cat logs/stability_test_*.log
cat logs/memory_leak_report_*.json
```

## Architecture Overview

### Modular Design Pattern

The codebase follows a **Manager Pattern** where each subsystem is encapsulated in a dedicated manager class. The main GUI (`VoiceTranscriptionApp`) acts as a coordinator but doesn't implement subsystem functionality.

**Key Integration Point**: `voice_transcription_tool/gui/main_window.py:53` - VoiceTranscriptionApp class orchestrating all managers.

### Core Module Structure

```
voice_transcription_tool/
├── main.py                 # Entry point with process locking & cleanup
├── config/                 # Configuration & persistence
│   └── settings.py         # ConfigManager - JSON config with validation
├── audio/                  # Audio capture & feedback
│   ├── recorder.py         # AudioRecorder - PyAudio wrapper
│   ├── devices.py          # AudioDeviceManager - device selection
│   └── feedback.py         # AudioFeedback - recording sounds
├── speech/                 # Speech recognition engines
│   └── engines.py          # SpeechEngineManager with fallback chain:
│                           #   FasterWhisperEngine (GPU, 4x faster)
│                           #   WhisperEngine (GPU/CPU, HQ mode)
│                           #   GoogleSpeechEngine (cloud fallback)
├── gui/                    # User interface
│   └── main_window.py      # VoiceTranscriptionApp - main coordinator
│                           # Tkinter GUI with visual feedback
└── utils/                  # Utilities
    ├── hotkeys.py          # HotkeyManager - pynput global shortcuts
    ├── autopaste.py        # AutoPasteManager - xdotool integration
    ├── tray_manager.py     # TrayManager - system tray with notifications
    ├── health_monitor.py   # HealthMonitor - resource monitoring
    └── logger.py           # Logging setup and debug handling
```

**Removed Modules** (Phase 1 Simplification):
- `config/database.py` - SQLite voice training removed
- `speech/training.py` - Voice training removed (experimental)
- `utils/system_tray.py` - Old stub deleted, replaced by `tray_manager.py`
- `utils/wake_word.py` - Wake word detection removed (experimental)

### v2.1 Architecture Changes (In Progress)

**GPU Acceleration** (P1.1 Complete):
- GPU detection with CUDA availability checks (`speech/engines.py:86-96`)
- Automatic FP16 on GPU, FP32 on CPU
- cuDNN availability validation before GPU usage
- Graceful CPU fallback if GPU initialization fails
- Configuration: `force_cpu` option to disable GPU

**Faster-Whisper Integration** (P1.2 Complete):
- `FasterWhisperEngine` class using CTranslate2 optimization
- 4x transcription speedup with Voice Activity Detection (VAD)
- Engine priority chain: faster-whisper → whisper → google
- GPU detection reused from WhisperEngine
- Located at: `speech/engines.py:269-461`

**UI Enhancements** (P1.3, P2.x Complete):
- Model size selector (tiny/base/small/medium/large) with estimated speeds
- System tray icon with recording state indicator (black → red)
- Desktop notifications on transcription complete
- Keyboard shortcuts: Ctrl+R (record), Ctrl+C (copy), Ctrl+Q (quit), Esc (stop)
- Visual recording feedback: pulsing banner, audio level meter

### Critical Design Patterns

1. **Manager Classes**: Each subsystem has clear responsibility boundaries with a manager (AudioRecorder, SpeechEngineManager, HotkeyManager, TrayManager, etc.)
2. **Abstract Base Classes**: Speech engines inherit from `SpeechEngine` ABC (`speech/engines.py:31`)
3. **Queue-based Threading**: Audio processing uses thread-safe queues for communication (recorder → speech engine → GUI)
4. **Callback Pattern**: Debug messages and events use callbacks to update GUI from background threads
5. **Singleton Process Lock**: `/tmp/voice_transcription.lock` prevents multiple instances (`main.py:32`)
6. **Graceful Degradation**: Each feature (GPU, faster-whisper, system tray) has fallback paths

### Data Flow Architecture

**Recording Flow**:
```
User Hotkey (Alt+D) → HotkeyManager → VoiceTranscriptionApp.toggle_recording()
→ AudioRecorder.start_recording() → audio_queue
→ SpeechEngineManager.transcribe() → transcription_queue
→ GUI update + AutoPasteManager → clipboard/paste
→ TrayManager.show_notification() (optional)
```

**GPU-Accelerated Transcription Flow** (v2.1):
```
Audio File → FasterWhisperEngine.transcribe()
  ↓ (if available)
  ├─ GPU detected? → CTranslate2 with FP16
  ├─ CPU only? → CTranslate2 with INT8
  └─ Not available? → WhisperEngine (standard)
      ↓
      ├─ GPU detected? → torch.cuda with FP16
      └─ CPU only? → torch with FP32
```

**Configuration Flow**:
```
ConfigManager.load() → voice_transcription_config.json (with validation)
→ Distributed to managers on init
→ ConfigManager.save() on settings change (auto-save)
→ Persists: hotkeys, audio settings, engine preferences, GPU settings, model size
```

### Thread Safety Considerations

- **Main Thread**: GUI (Tkinter), hotkey callbacks, tray icon menu
- **Background Threads**: Audio recording, transcription processing, health monitoring, model loading
- **Synchronization**: Python queues (thread-safe), `Tkinter.after()` for GUI updates from background threads
- **Critical Sections**: Recording state changes protected by flag checks before queue operations
- **Model Loading**: Non-blocking UI with progress dialogs and background threads

### Global State & Configuration

**Persistent Files**:
- Configuration: `voice_transcription_config.json` (root and module directory)
- Logs: `logs/voice_transcription_*.log` (timestamped)
- Process Lock: `/tmp/voice_transcription.lock` (PID-based)

**Default Settings** (v2.1):
- Hotkey: Alt+D (record toggle)
- Audio: 16kHz, mono, 30s max recording
- Engine Priority: faster-whisper > whisper > google
- Model Size: base (configurable: tiny/base/small/medium/large)
- GPU: Auto-detect with cuDNN validation, CPU fallback
- Health Limits: 2048MB memory, 98% CPU, 30s check interval
- Auto-paste: Enabled by default
- System Tray: Enabled with desktop notifications

## System Dependencies

**Required**:
- FFmpeg - Audio processing for Whisper (critical dependency)
- xclip (Linux) - Clipboard functionality
- xdotool (Linux) - Auto-paste functionality
- Python 3.7+ with tkinter

**Speech Engines** (at least one required):
- faster-whisper (>=0.10.0) - CTranslate2 optimization, 4x speedup, GPU-accelerated
- Whisper (openai-whisper) - Local processing, accurate, GPU-accelerated
- Google Speech (SpeechRecognition) - Cloud-based, requires internet

**GPU Acceleration** (optional but recommended):
- CUDA Toolkit (for NVIDIA GPUs)
- cuDNN libraries (libcudnn9-cuda-12)
- PyTorch with CUDA support

**Key Python Packages**:
- pynput - Cross-platform global hotkeys **without sudo requirement**
- pyaudio - Audio recording interface
- pygame - Audio feedback sounds
- torch - Required for Whisper engines (GPU support optional)
- psutil - Resource monitoring (highly recommended)
- pystray - System tray icon (v2.1)
- pillow - Icon generation for system tray (v2.1)
- faster-whisper (>=0.10.0) - CTranslate2 optimization (v2.1)

**Removed Dependencies** (Phase 1):
- ~~pystray + pillow~~ - Old system tray stub removed, new implementation in v2.1
- ~~pyautogui~~ - Replaced with xdotool (no Qt conflicts)
- ~~openwakeword + onnxruntime~~ - Wake word detection removed

## Testing Philosophy

The project has 114 comprehensive tests with 74% code coverage (exceeded 70% target). Tests are organized by:

- **Unit tests** (`-m unit`): Individual manager components with mocked dependencies
- **Integration tests** (`-m integration`): Component interaction (AudioRecorder → SpeechEngineManager)
- **Stress tests** (`-m stress`, Phase 5): 1000-cycle resource leak detection, memory monitoring, crash resilience
- **Mock strategy**: External dependencies (PyAudio, Whisper API, file I/O) are mocked for CI/CD

**Test Configuration**: `voice_transcription_tool/pytest.ini` - markers, test discovery, output formatting

**Coverage Breakdown**:
- Audio module: 100%
- Speech module: 85%
- Config module: 92%
- GUI module: 51%
- Utils module: 68%

### Stress Testing Infrastructure (Phase 5)

**Stress Test Suite** (`tests/test_stress.py`):
- `test_1000_recording_cycles` - Memory leak detection over 1000 start/stop cycles
- `test_rapid_hotkey_presses` - Race condition validation
- `test_long_recording_cycles` - Large audio buffer handling (30s recordings)
- `test_concurrent_start_attempts` - Thread safety under concurrent load
- `test_transcription_memory_leak` - Garbage collection validation
- `test_config_save_memory_leak` - File handle cleanup validation
- `test_recovery_from_intermittent_failures` - Error resilience

**Memory Leak Detector** (`scripts/memory_leak_test.py`):
- Baseline memory establishment with forced garbage collection
- Cycle-based testing: 1000+ recording cycles with periodic sampling
- Duration-based testing: Multi-hour monitoring with configurable intervals
- JSON report generation with memory growth metrics
- 20% growth threshold validation

**Stability Test Script** (`scripts/stability_test.sh`):
- Multi-hour background testing (default 8 hours)
- Crash detection and automatic restart
- Resource monitoring every 5 minutes
- Comprehensive reporting with success rates

## Important Implementation Notes

### GPU Detection & Acceleration (v2.1)

The application automatically detects GPU availability using `torch.cuda.is_available()` and validates cuDNN libraries before enabling GPU mode. Key locations:

- GPU detection: `speech/engines.py:86-96` (WhisperEngine and FasterWhisperEngine)
- cuDNN validation: `speech/engines.py:98-113`
- Device selection: Automatic FP16 on GPU, FP32/INT8 on CPU
- Graceful fallback: If GPU initialization fails (e.g., CUDA errors), automatically retries on CPU
- Configuration override: Set `force_cpu: true` in config to disable GPU usage

**Common GPU Issues**:
- Missing cuDNN: Install `libcudnn9-cuda-12` package
- CUDA version mismatch: Ensure PyTorch CUDA version matches system CUDA
- Memory errors: GPU memory insufficient for large models (medium/large)

### Faster-Whisper Engine Priority (v2.1)

The `SpeechEngineManager` tries engines in this order:
1. FasterWhisperEngine (if faster-whisper installed)
2. WhisperEngine (if whisper installed)
3. GoogleSpeechEngine (fallback, requires internet)

Engine initialization location: `speech/engines.py:565-596`

### Process Lock Mechanism

The application uses fcntl file locking (`main.py:32`) to prevent multiple instances. If the application crashes, the lock file may persist at `/tmp/voice_transcription.lock` and must be manually removed or cleaned by checking PID validity.

### Hotkey Implementation on Linux

Uses pynput instead of keyboard library to avoid sudo requirements. See `docs/LINUX_HOTKEY_SOLUTION.md` for migration details from older implementations.

### Auto-Paste Focus Management

Captures active window before recording (`utils/autopaste.py:55`), then restores focus before pasting to prevent GUI from stealing focus. Terminal applications use Ctrl+Shift+V instead of Ctrl+V. Browser detection prevents address bar focus issues.

### Health Monitor Warning System

Monitors CPU/memory usage every 30s. On limit breach (2048MB memory, 98% CPU), logs warnings and provides optional emergency callback (`utils/health_monitor.py:14`).

### System Tray Implementation (v2.1)

The `TrayManager` (`utils/tray_manager.py`) generates icons programmatically using PIL:
- Icon changes from black to red during recording
- Menu options: Show/Hide, Start/Stop Recording, Quit
- Desktop notifications on transcription complete
- Runs in separate thread to avoid blocking main GUI

### Secure Temporary Files

Uses `tempfile.NamedTemporaryFile(delete=False)` instead of deprecated `mktemp()` to avoid race condition vulnerabilities (`audio/recorder.py:232`).

### Model Size Selection (v2.1)

Users can select Whisper model size in settings dialog:
- tiny: Fastest, lowest accuracy (~1GB RAM)
- base: Default, balanced (~1GB RAM)
- small: Better accuracy (~2GB RAM)
- medium: High accuracy (~5GB RAM)
- large: Best accuracy (~10GB RAM)

Model loading happens in background thread with progress dialog. Configuration persists across restarts.

## Migration Context

This is v2.1, currently in development. Version history:
- **v1.0**: Original monolithic implementation
- **v2.0**: Major refactor to modular architecture (Phase 1-6 completed)
  - Removed 3,759 LOC (49% reduction)
  - 74% test coverage, zero memory leaks
  - Production stability validated
- **v2.1**: Performance & UX improvements (in progress)
  - GPU acceleration (P1.1 ✅)
  - Faster-Whisper integration (P1.2 ✅)
  - Model size selector (P1.3 ✅)
  - Visual feedback improvements (P2.1 ✅)
  - System tray icon (P2.2 ✅)
  - Keyboard shortcuts (P2.3 ✅)

Comments referencing "MIGRATION STEP X" can be ignored for new development - they document the v1.0 → v2.0 refactoring process.

## Common Development Patterns

### Adding a New Manager Component
1. Create manager class in appropriate module (audio/, speech/, utils/)
2. Initialize in `VoiceTranscriptionApp.__init__()` (`gui/main_window.py:61`)
3. Add configuration fields to ConfigManager if needed (`config/settings.py`)
4. Create unit tests in `tests/test_*.py`
5. Add integration test if it interacts with other managers

### Adding a New Speech Engine
1. Inherit from `SpeechEngine` ABC (`speech/engines.py:31`)
2. Implement `transcribe()`, `is_available()`, `name` property
3. Register in `SpeechEngineManager._init_engines()` (`speech/engines.py:565`)
4. Add dependency check in `main.py:check_dependencies()`
5. Update engine priority order if needed
6. Add unit tests in `tests/test_speech.py`

### Adding a New Hotkey
1. Register in `HotkeyManager` (`utils/hotkeys.py`)
2. Add callback in `VoiceTranscriptionApp._setup_hotkeys()` (`gui/main_window.py`)
3. Add to default config in `ConfigManager` (`config/settings.py`)
4. Update GUI settings dialog for configuration
5. Document in keyboard shortcuts hint label

### GPU/Performance Debugging
1. Run with `--debug` flag to see GPU detection logs
2. Check logs for GPU device name and memory
3. Verify cuDNN detection messages
4. Monitor GPU usage: `nvidia-smi` (if NVIDIA) or `rocm-smi` (if AMD)
5. Test CPU fallback by setting `force_cpu: true` in config
6. Compare transcription times: `--debug` logs show timing for each transcription

## Known Limitations

- Tkinter GUI (simple by design for production stability, not feature-rich)
- xdotool auto-paste is Linux-only (Windows/macOS support planned for future)
- No CI/CD pipeline yet (GitHub Actions planned)
- GPU support requires CUDA/cuDNN installation (not auto-installed with pip)

## Production Readiness Status

**Completed Phases**:
- ✅ Phase 1: Feature removal & simplification (removed 3,759 LOC, 49% reduction)
- ✅ Phase 2: Resource management fixes (clean shutdown, thread lifecycle)
- ✅ Phase 3: Error handling improvements (zero silent failures)
- ✅ Phase 4: Test coverage to 74% (exceeded 70% target, 114 tests)
- ✅ Phase 5: Stability & stress testing (7 stress tests, 8-hour validation)
- ✅ Phase 6: Documentation & polish (README, INSTALLATION, TROUBLESHOOTING)

**v2.1 Progress** (Current):
- ✅ P1.1: GPU detection & acceleration (GPU/CPU auto-detect, cuDNN validation)
- ✅ P1.2: Faster-Whisper integration (4x speedup, VAD filtering)
- ✅ P1.3: Model size selector UI (tiny/base/small/medium/large)
- ✅ P2.1: Visual recording feedback (pulsing banner, audio level meter)
- ✅ P2.2: System tray icon (background mode, notifications)
- ✅ P2.3: Keyboard shortcuts (Ctrl+R, Ctrl+C, Ctrl+Q, Esc)
- ⏳ P3.x: Cleanup & optimization (error messages, dead code, RMS throttling)

**Validation Results**:
- ✅ 0 crashes over 8-hour stability test
- ✅ Memory growth < 20% over 1000 cycles
- ✅ Error recovery confirmed for intermittent failures
- ✅ GPU acceleration working (NVIDIA GTX 1650 SUPER tested)
- ✅ 4x transcription speedup with faster-whisper confirmed

## File Organization & Navigation

**Key Files by Function**:

- **Entry Point**: `voice_transcription_tool/main.py` - Process lock, emergency cleanup, startup
- **Main Orchestrator**: `gui/main_window.py` - VoiceTranscriptionApp coordinates all managers
- **Speech Engines**: `speech/engines.py` - All 3 engines (FasterWhisper, Whisper, Google)
- **Audio Capture**: `audio/recorder.py` - AudioRecorder with RMS calculation
- **Configuration**: `config/settings.py` - ConfigManager with JSON persistence
- **Global Hotkeys**: `utils/hotkeys.py` - HotkeyManager using pynput
- **Auto-paste**: `utils/autopaste.py` - AutoPasteManager using xdotool
- **System Tray**: `utils/tray_manager.py` - TrayManager with icon generation
- **Health Monitoring**: `utils/health_monitor.py` - HealthMonitor for resource limits

**Test Files**:
- `tests/test_audio.py` - AudioRecorder, AudioDeviceManager, AudioFeedback
- `tests/test_speech.py` - All speech engines
- `tests/test_config.py` - ConfigManager
- `tests/test_gui.py` - VoiceTranscriptionApp
- `tests/test_utils.py` - Hotkeys, AutoPaste, HealthMonitor
- `tests/test_integration.py` - Cross-component workflows
- `tests/test_stress.py` - Memory leaks, race conditions, stability

**Documentation**:
- `README.md` - User-facing overview and quick start
- `CLAUDE.md` (this file) - Developer guidance for Claude Code
- `V2.1_IMPLEMENTATION_PLAN.md` - Detailed v2.1 feature roadmap
- `V2.1_PROGRESS.md` - Session-by-session progress tracking
- `P1.1_GPU_ACCELERATION_COMPLETE.md` - GPU feature completion report
- `WARP.md` - Project history and major decisions
- `docs/INSTALLATION.md` - Comprehensive installation guide
- `docs/TROUBLESHOOTING.md` - Diagnostic guide

## Future Enhancements

Post-v2.1 roadmap:
- Installation packaging (.deb for Ubuntu)
- CI/CD with GitHub Actions
- Windows/macOS auto-paste support (currently Linux-only)
- Additional speech engine support (Azure, AWS Transcribe)
- Hotkey customization UI (currently config-file only)
- Recording history and playback
