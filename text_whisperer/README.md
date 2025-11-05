# Voice Transcription Tool

**Production-ready, GPU-accelerated** speech-to-text application with global hotkeys, auto-paste functionality, and system tray mode.

[![Tests](https://img.shields.io/badge/tests-121%20passing-brightgreen)](voice_transcription_tool/tests/)
[![Coverage](https://img.shields.io/badge/coverage-71%25-green)](voice_transcription_tool/tests/)
[![Python](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-2.1-blue)](WARP.md#version-history)

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

✅ **GPU Acceleration** (v2.1) - Automatic CUDA/cuDNN detection, 4x faster transcription
✅ **Faster-Whisper Engine** (v2.1) - CTranslate2 optimization with Voice Activity Detection
✅ **Model Size Selector** (v2.1) - Choose tiny/base/small/medium/large models
✅ **System Tray Mode** (v2.1) - Background operation with desktop notifications
✅ **Keyboard Shortcuts** (v2.1) - Ctrl+R (record), Ctrl+C (copy), Ctrl+Q (quit), Esc (stop)
✅ **Visual Feedback** (v2.1) - Audio level meter, pulsing recording banner, live RMS display
✅ **Keyboard Shortcut Recording** - Press Alt+D to record, release to transcribe
✅ **Auto-paste at Cursor** - Transcribed text automatically inserted where you're typing
✅ **Real-time Feedback** - Audio cues and visual status during recording
✅ **Standby Mode** - Lightweight background process, instant activation
✅ **Production Stability** - No memory leaks, crash-resistant, resource-monitored

### Speech Recognition Engines

- **Faster-Whisper** (preferred) - CTranslate2 optimization, 4x faster, GPU/CPU, local processing
- **Whisper** (fallback) - High accuracy, GPU-accelerated, local processing
- **Google Speech** (cloud fallback) - Cloud-based, requires internet

## Usage

### Basic Controls

- **Alt+D**: Start/stop recording
- **Alt+S**: Open settings dialog

### Command Line Options

```bash
python main.py --debug         # Enable verbose logging
python main.py --minimized     # Start hidden (background mode)
```

## GPU Acceleration (v2.1)

The application automatically detects and utilizes GPU acceleration for faster transcription:

### Automatic GPU Detection

- **CUDA Detection**: Checks for NVIDIA GPU with CUDA support
- **cuDNN Validation**: Verifies cuDNN libraries are installed
- **Automatic Fallback**: Seamlessly switches to CPU if GPU unavailable
- **Device Selection**: Automatically selects FP16 on GPU, FP32/INT8 on CPU

### Performance Comparison

| Configuration | Speed | Model | Notes |
|--------------|-------|-------|-------|
| **Faster-Whisper + GPU** | 4x faster | CTranslate2 + FP16 | Recommended |
| **Faster-Whisper + CPU** | 2x faster | CTranslate2 + INT8 | Good performance |
| **Whisper + GPU** | 1x (baseline) | PyTorch + FP16 | High quality |
| **Whisper + CPU** | Slower | PyTorch + FP32 | CPU fallback |

### GPU Setup (Optional)

For optimal performance with NVIDIA GPUs:

```bash
# Install CUDA Toolkit (if not already installed)
# Ubuntu/Debian:
sudo apt install nvidia-cuda-toolkit

# Install cuDNN libraries
sudo apt install libcudnn9-cuda-12

# Verify GPU detection
python main.py --debug  # Check logs for "GPU detected" message
```

**Force CPU Mode**: Enable "Force CPU Mode" in Settings if GPU causes issues.

## Model Selection (v2.1)

Choose the Whisper model size that balances speed and accuracy for your needs:

| Model | Speed | RAM | Accuracy | Use Case |
|-------|-------|-----|----------|----------|
| **tiny** | Fastest | ~1GB | Lower | Quick notes, simple commands |
| **base** | Fast | ~1GB | Good | **Default** - balanced performance |
| **small** | Moderate | ~2GB | Better | Detailed transcription |
| **medium** | Slower | ~5GB | High | Professional transcription |
| **large** | Slowest | ~10GB | Highest | Maximum accuracy needed |

**How to Change**: Open Settings dialog (Alt+S) → Select model size → Apply (will download model if needed)

**Model Download**: First use of each model size downloads it (~100MB-5GB depending on size). Subsequent uses are instant.

## Production Readiness

This application has been hardened for production use through comprehensive testing:

- ✅ **121 passing tests** across unit, integration, and stress categories (v2.1)
- ✅ **71% code coverage** with critical paths fully tested
- ✅ **GPU acceleration tests** - Validates CUDA detection and CPU fallback (v2.1)
- ✅ **Memory leak detection** - Validated with 1000-cycle stress tests
- ✅ **Resource monitoring** - Automatic health checks prevent system freezes
- ✅ **Error recovery** - Graceful handling of audio device failures
- ✅ **Thread safety** - Concurrent operation validation

### Testing Infrastructure

```bash
# Run all tests (from voice_transcription_tool directory)
cd voice_transcription_tool/
python -m pytest tests/                    # All 121 tests
python -m pytest tests/ -v --cov          # With coverage report (71%)
python -m pytest -m stress                # Stress tests only

# Memory leak detection (scripts are at repo root)
python ../scripts/memory_leak_test.py --cycles 1000
python ../scripts/memory_leak_test.py --duration 3600  # 1 hour

# Multi-hour stability testing
../scripts/stability_test.sh --duration 8  # 8-hour background test
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
├── tests/                   # Test suite (121 tests, 74% coverage)
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
