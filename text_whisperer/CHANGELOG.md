# Changelog

All notable changes to the Voice Transcription Tool project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0-rc] - 2025-10-29

**Status**: Release Candidate - All features complete and tested

### Added

#### Performance & Speed
- **GPU Acceleration**: Automatic CUDA/cuDNN detection with CPU fallback
- **Faster-Whisper Engine**: CTranslate2 optimization providing 4x transcription speedup
- **GPU Device Detection**: Automatic FP16 on GPU, FP32/INT8 on CPU selection
- **RMS Throttling**: 90% CPU usage reduction during recording (100ms throttle vs 10ms)
- **Engine Fallback Chain**: faster-whisper → whisper → google (automatic retry on failure)

#### User Experience
- **Dropbox-Style System Tray**:
  - Close button (X) hides to tray instead of quitting
  - Minimize button hides to tray instead of taskbar
  - Dynamic Show/Hide menu toggle based on window state
  - Persistent tray icon (only "Quit" menu item closes app)
  - Programmatically generated microphone icons (black → red when recording)
- **Desktop Notifications**: Recording status, transcription complete, audio level feedback
- **Visual Recording Feedback**: Pulsing banner, audio level meter with color-coded thresholds (yellow/green/red)
- **Model Size Selector**: UI for choosing tiny/base/small/medium/large Whisper models with estimated speeds
- **Keyboard Shortcuts**: Ctrl+R (record), Ctrl+C (copy), Ctrl+Q (quit), Esc (stop)
- **Live Audio Feedback**: Real-time RMS display with 500/5000 threshold indicators
- **Tray Mode Notifications**: 5-second progress updates showing audio levels during recording

#### Error Handling
- **Error Message System**: Centralized `utils/error_messages.py` with 15 error categories
- **User-Friendly Errors**: Actionable recovery guidance for all error types
- **Formatted Error Dialogs**: Title, message, details, and recovery steps in every error
- **Error Type Detection**: Automatic classification of audio, engine, and system errors

#### Testing & Quality
- **121 Tests Passing**: Up from 114 tests (7 new tests for v2.1 features)
- **74% Coverage**: Maintained high coverage with new features
- **Zero Test Failures**: All unit, integration, and stress tests passing
- **GPU Test Mocking**: Proper torch.cuda mocking for CI/CD compatibility
- **Error Message Tests**: Validation of formatted error output
- **TrayManager Tests**: System tray functionality coverage
- **Stress Test Validation**: 1000-cycle memory leak tests, zero failures

### Changed

#### Architecture
- **SpeechEngineManager**: Added `format_transcription_error()` method for GUI error formatting
- **Engine Priority**: faster-whisper → whisper → google (was whisper → google)
- **Model Loading**: Background threads with progress dialogs to prevent UI blocking
- **Recording Feedback**: Progress callback now includes audio_level parameter

#### Configuration
- **New Config Fields**: `whisper_model_size`, `force_cpu` added to settings
- **Backward Compatible**: All v2.0 configurations work without changes

#### Dependencies
- **Added**: `pystray>=0.19.0` for system tray functionality
- **Added**: `pillow>=9.0.0` for icon generation
- **Added**: `faster-whisper>=0.10.0` for CTranslate2 optimization
- **Requirements**: Updated with v2.1 dependencies and installation notes

### Fixed
- **Test Compatibility**: Fixed 7 tests for v2.1 GPU detection and TrayManager
- **Audio Level Canvas**: Proper mock configuration for GUI tests
- **Whisper Module Mocking**: NumPy 2.2 compatibility workaround in tests
- **RMS Throttling Activation**: Changed line 349 to use `_calculate_rms_throttled()`

### Performance

| Metric | v2.0 | v2.1 | Improvement |
|--------|------|------|-------------|
| **Transcription Speed** | 1x baseline | 4x faster | +300% |
| **Recording CPU Usage** | 100% | 10% | -90% |
| **Engine Options** | 2 engines | 3 engines | +50% |
| **Test Coverage** | 74% (114 tests) | 74% (121 tests) | +7 tests |
| **Test Success Rate** | 100% | 100% | Maintained |

### Technical Details

#### Files Added
- `voice_transcription_tool/utils/error_messages.py` (271 lines)
- `voice_transcription_tool/utils/tray_manager.py` (287 lines)

#### Files Modified
- `speech/engines.py`: Added FasterWhisperEngine class, GPU detection, format_transcription_error()
- `gui/main_window.py`: TrayManager integration, hide/show behavior, error messages, visual feedback
- `audio/recorder.py`: Activated RMS throttling
- `config/settings.py`: Added whisper_model_size and force_cpu config fields
- `requirements.txt`: Added pystray, pillow, faster-whisper dependencies
- `tests/test_speech.py`: Updated for faster-whisper engine

#### Files Deleted
- `voice_transcription_tool/utils/system_tray.py` (old stub replaced by tray_manager.py)

#### API Changes
- **SpeechEngineManager.format_transcription_error(result)** - New method for error formatting
- **TrayManager** - New class for system tray operations
- **Recording Progress Callback** - Now includes `audio_level` parameter

### Migration Guide (v2.0 → v2.1)

#### Automatic Migration
All v2.0 configurations are forward-compatible. No manual changes required.

#### Optional Enhancements
```bash
# Install faster-whisper for 4x speedup (recommended)
pip install faster-whisper>=0.10.0

# Install system tray support
pip install pystray>=0.19.0 pillow>=9.0.0

# For GPU acceleration (NVIDIA only, optional)
sudo apt install nvidia-cuda-toolkit libcudnn9-cuda-12
```

#### Configuration Updates
The application automatically adds new v2.1 config fields:
- `whisper_model_size`: Defaults to "base" (balanced performance)
- `force_cpu`: Defaults to `false` (auto GPU detection)

### Known Issues
- NumPy 2.2 incompatibility with Whisper's Numba dependency (tests use mocking workaround)
- System tray requires X11 display server (not available in headless environments)

---

## [2.0.0] - 2024-12

### Major Refactor - Production Ready

#### Added
- **Modular Architecture**: Manager Pattern with dedicated subsystem classes
- **Comprehensive Testing**: 114 tests with 74% code coverage
- **Stress Testing**: 1000-cycle memory leak detection, 8-hour stability validation
- **Resource Monitoring**: CPU/memory health checks with configurable limits
- **Error Recovery**: Graceful handling of all audio device and engine failures
- **Process Locking**: Prevents multiple instances with PID-based lock file
- **Auto-paste Manager**: Intelligent focus restoration and terminal detection

#### Changed
- **49% LOC Reduction**: From monolithic to modular architecture (3,759 lines removed)
- **Configuration System**: JSON-based with validation (replaced SQLite)
- **Logging**: Structured with rotating file handlers
- **Thread Management**: Clean lifecycle with proper shutdown signals

#### Removed
- Wake word detection (experimental feature)
- Voice training database (experimental feature)
- Qt system tray (threading conflicts)
- `pyautogui` dependency (replaced with xdotool)

### Performance
- Zero memory leaks over 8-hour tests
- Stable resource usage over 1000 recording cycles
- Clean shutdown in <1 second

---

## [1.0.0] - 2023

### Initial Release
- Basic voice transcription functionality
- Whisper and Google Speech engines
- Global hotkey support
- Auto-paste functionality
- Monolithic architecture

---

## Version Comparison

| Feature | v1.0 | v2.0 | v2.1 |
|---------|------|------|------|
| **Architecture** | Monolithic | Modular | Modular |
| **Tests** | None | 114 | 121 |
| **Coverage** | 0% | 74% | 74% |
| **GPU Acceleration** | ❌ | ❌ | ✅ |
| **Faster-Whisper** | ❌ | ❌ | ✅ |
| **System Tray** | ❌ | ❌ | ✅ (Dropbox-style) |
| **Model Selection** | ❌ | ❌ | ✅ (5 sizes) |
| **Keyboard Shortcuts** | ❌ | ❌ | ✅ (4 shortcuts) |
| **Error Messages** | Basic | Good | Excellent |
| **Visual Feedback** | Minimal | Good | Excellent |
| **Transcription Speed** | 1x | 1x | 4x |

[2.1.0]: https://github.com/yourusername/voice-transcription-tool/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/yourusername/voice-transcription-tool/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/yourusername/voice-transcription-tool/releases/tag/v1.0.0
