# Voice Transcription Tool

**Production-ready** speech-to-text application with global hotkeys and auto-paste functionality.

[![Tests](https://img.shields.io/badge/tests-114%20passing-brightgreen)](voice_transcription_tool/tests/)
[![Coverage](https://img.shields.io/badge/coverage-74%25-green)](voice_transcription_tool/tests/)
[![Python](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/)

## Quick Start

```bash
# Install system dependencies (Linux)
sudo apt install ffmpeg xdotool

# Install Python dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Core Features

✅ **Keyboard Shortcut Recording** - Press Alt+D to record, release to transcribe
✅ **Auto-paste at Cursor** - Transcribed text automatically inserted where you're typing
✅ **Real-time Feedback** - Audio cues and visual status during recording
✅ **Standby Mode** - Lightweight background process, instant activation
✅ **Production Stability** - No memory leaks, crash-resistant, resource-monitored

### Speech Recognition Engines

- **Whisper** (default) - Local processing, high accuracy, GPU-accelerated
- **Google Speech** - Cloud-based fallback, requires internet

## Usage

### Basic Controls

- **Alt+D**: Start/stop recording
- **Alt+S**: Open settings dialog

### Command Line Options

```bash
python main.py --debug         # Enable verbose logging
python main.py --minimized     # Start hidden (background mode)
```

## Production Readiness

This application has been hardened for production use through comprehensive testing:

- ✅ **114 passing tests** across unit, integration, and stress categories
- ✅ **74% code coverage** with critical paths fully tested
- ✅ **Memory leak detection** - Validated with 1000-cycle stress tests
- ✅ **Resource monitoring** - Automatic health checks prevent system freezes
- ✅ **Error recovery** - Graceful handling of audio device failures
- ✅ **Thread safety** - Concurrent operation validation

### Testing Infrastructure

```bash
# Run all tests (must be in voice_transcription_tool directory)
cd voice_transcription_tool/
python -m pytest tests/                    # All 114 tests
python -m pytest tests/ -v --cov          # With coverage report
python -m pytest -m stress                # Stress tests only

# Memory leak detection
python scripts/memory_leak_test.py --cycles 1000
python scripts/memory_leak_test.py --duration 3600  # 1 hour

# Multi-hour stability testing
./scripts/stability_test.sh --duration 8  # 8-hour background test
```

## System Requirements

### Required Dependencies

- **Python 3.7+** with tkinter
- **FFmpeg** - Audio processing for Whisper engine (critical)
- **xdotool** (Linux) - Auto-paste functionality
- **At least one speech engine**:
  - Whisper (`openai-whisper`) - Recommended for accuracy
  - Google Speech (`SpeechRecognition`) - Requires internet

### Optional Components

- **psutil** - Resource monitoring (highly recommended)
- **GPU with CUDA** - For accelerated Whisper processing

See [INSTALLATION.md](docs/INSTALLATION.md) for detailed setup instructions.

## Project Structure

```
voice_transcription_tool/    # Core application code
├── audio/                   # Audio capture and feedback
├── speech/                  # Speech recognition engines
├── gui/                     # User interface
├── utils/                   # Hotkeys, auto-paste, health monitoring
├── config/                  # Configuration management
├── tests/                   # Test suite (114 tests)
└── scripts/                 # Stability and memory leak testing

docs/                        # Documentation
scripts/                     # Helper scripts
```

## Troubleshooting

Common issues and solutions:

- **"FFmpeg not found"** - Install: `sudo apt install ffmpeg`
- **Auto-paste not working** - Install: `sudo apt install xdotool`
- **System freezes** - Run `voice_transcription_tool/debug_freeze.sh` from TTY
- **Resource monitoring** - Run `voice_transcription_tool/monitor_voice_tool.sh`

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for comprehensive debugging guide.

## Development

```bash
cd voice_transcription_tool/

# Run test suite
python -m pytest tests/ -v                    # Verbose output
python -m pytest tests/ --cov                 # With coverage
python -m pytest -m "not slow"                # Skip slow tests

# Stress testing for production validation
python -m pytest -m stress                    # Resource leak detection
python scripts/memory_leak_test.py --cycles 500

# Debug mode
python main.py --debug
```

## Version

**v2.0** - Production-ready release with comprehensive testing and stability hardening.
