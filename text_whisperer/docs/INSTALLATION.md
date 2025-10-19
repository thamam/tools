# Installation Guide

Complete installation guide for Voice Transcription Tool v2.0 (Production Release).

## Table of Contents

- [System Requirements](#system-requirements)
- [Quick Installation](#quick-installation)
- [Detailed Installation Steps](#detailed-installation-steps)
- [Speech Engine Setup](#speech-engine-setup)
- [Verification](#verification)
- [Optional: GPU Acceleration](#optional-gpu-acceleration)
- [Common Installation Issues](#common-installation-issues)

## System Requirements

### Operating System
- **Linux**: Ubuntu 18.04+, Debian 10+, or compatible distributions
- **Python**: 3.7 or higher with tkinter support
- **Hardware**: Microphone for audio input

### Disk Space
- Minimal installation: ~500MB (Google Speech only)
- Full installation with Whisper: ~3GB (includes Whisper model weights)
- With GPU CUDA support: ~5GB

## Quick Installation

For experienced users, the minimal command sequence:

```bash
# Install system dependencies
sudo apt update
sudo apt install -y ffmpeg xdotool python3-tk

# Clone repository (or navigate to existing installation)
cd /path/to/text_whisperer

# Install Python dependencies
pip install -r requirements.txt

# Run application
python main.py
```

## Detailed Installation Steps

### Step 1: Install System Dependencies

#### FFmpeg (Critical - Required for Whisper)

FFmpeg is essential for audio processing with the Whisper speech engine.

```bash
# Check if already installed
ffmpeg -version

# Install if missing
sudo apt update
sudo apt install -y ffmpeg
```

**Verification**:
```bash
ffmpeg -version
# Should output: ffmpeg version 4.x.x or higher
```

#### xdotool (Required for Auto-paste)

xdotool enables automatic text insertion at cursor position.

```bash
# Install xdotool
sudo apt install -y xdotool

# Verify installation
xdotool --version
# Should output: xdotool version 3.x.x
```

#### Python Tkinter (Usually Pre-installed)

```bash
# Check if tkinter is available
python3 -c "import tkinter; print('Tkinter available')"

# If missing, install:
sudo apt install -y python3-tk
```

### Step 2: Set Up Python Environment

#### Option A: System Python (Simplest)

```bash
# Navigate to project directory
cd /path/to/text_whisperer

# Install Python dependencies
pip install -r requirements.txt
```

#### Option B: Virtual Environment (Recommended for Development)

```bash
# Create virtual environment
python3 -m venv venv

# Activate environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Install Python Dependencies

The `requirements.txt` includes all necessary packages:

**Core Dependencies**:
- `pyaudio` - Audio recording interface
- `pynput` - Global hotkeys (no sudo required)
- `pygame` - Audio feedback sounds
- `psutil` - Resource monitoring

**Speech Engine Dependencies**:
- `openai-whisper` - Local speech recognition (recommended)
- `SpeechRecognition` - Google Speech fallback
- `torch` - Required for Whisper processing

**Optional Dependencies**:
- `openwake` - Advanced wake word detection (experimental)

```bash
# Install all dependencies
pip install -r requirements.txt

# This will take 5-10 minutes on first installation
# Whisper models will download on first use (~1.5GB)
```

### Step 4: Verify Installation

```bash
# Run application with debug mode
python main.py --debug

# You should see:
# ✓ FFmpeg found
# ✓ Audio device initialized
# ✓ Whisper engine loaded (or Google Speech if Whisper unavailable)
# ✓ Hotkey manager initialized
```

## Speech Engine Setup

Voice Transcription Tool supports two speech recognition engines. **At least one is required**.

### Whisper Engine (Recommended)

**Advantages**:
- High accuracy (industry-leading)
- Works offline (no internet required)
- GPU-accelerated (with CUDA)
- Supports multiple languages

**Installation**:
```bash
pip install openai-whisper
```

**First Run**:
On first use, Whisper will automatically download model weights (~1.5GB for the base model):

```bash
python main.py
# Press Alt+D to record
# First transcription will trigger model download
# Subsequent uses will be faster
```

**Model Selection** (Advanced):
Edit `voice_transcription_config.json` to change model size:

```json
{
  "whisper_model": "base"
}
```

**Available Options**: tiny, base, small, medium, large

Model size vs. accuracy tradeoff:
- **tiny** (39M params): Fast, lower accuracy
- **base** (74M params): **Default**, good balance
- **small** (244M params): Better accuracy, slower
- **medium** (769M params): High accuracy, requires GPU
- **large** (1550M params): Best accuracy, requires powerful GPU

### Google Speech Engine (Fallback)

**Advantages**:
- Fast setup (no model downloads)
- Low resource usage
- Good accuracy for English

**Disadvantages**:
- Requires internet connection
- Usage limits may apply
- Cloud-based (privacy considerations)

**Installation**:
```bash
pip install SpeechRecognition
```

**No additional setup required** - works immediately.

### Engine Priority

The application automatically selects the best available engine:

1. **Whisper** (if installed and models available)
2. **Google Speech** (if internet available)

You can override this in settings (Alt+S) or in the config file.

## Verification

### Test 1: Application Startup

```bash
python main.py --debug
```

**Expected Output**:
```
[INFO] Voice Transcription Tool v2.0 starting...
[INFO] Config loaded from voice_transcription_config.json
[INFO] FFmpeg found: /usr/bin/ffmpeg
[INFO] Audio device: Default (index 0)
[INFO] Speech engine: Whisper (base model)
[INFO] Hotkey registered: Alt+D
[INFO] Health monitor started
```

### Test 2: Recording Test

1. Launch application: `python main.py`
2. Press **Alt+D** to start recording
3. Speak: "This is a test"
4. Release **Alt+D** to stop
5. Verify transcription appears in the text box

### Test 3: Auto-paste Test

1. Open any text editor (gedit, kate, etc.)
2. Click inside the text field
3. Press **Alt+D** and speak
4. Transcribed text should automatically appear in the editor

**If auto-paste doesn't work**, verify xdotool is installed:
```bash
xdotool --version
```

### Test 4: Resource Monitoring

```bash
# Monitor resource usage
./voice_transcription_tool/monitor_voice_tool.sh
```

**Expected behavior**: Memory should stay below 1GB, CPU spikes during transcription are normal.

## Optional: GPU Acceleration

For significantly faster Whisper transcription, enable GPU acceleration with CUDA.

### Prerequisites

- NVIDIA GPU with CUDA support
- CUDA Toolkit 11.0+ installed
- cuDNN installed

### Installation

```bash
# Install CUDA-enabled PyTorch
pip uninstall torch  # Remove CPU-only version
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Verify CUDA is available
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
# Should output: CUDA available: True
```

### Performance Comparison

| Model Size | CPU (base model) | GPU (base model) |
|------------|------------------|------------------|
| Tiny       | ~3s              | ~0.5s            |
| Base       | ~8s              | ~1.5s            |
| Small      | ~25s             | ~4s              |
| Medium     | ~90s             | ~12s             |

**Note**: GPU acceleration provides 5-8x speedup for transcription.

## Common Installation Issues

### Issue 1: "FFmpeg not found"

**Symptom**:
```
ERROR: FFmpeg not found. Please install FFmpeg to use Whisper engine.
```

**Solution**:
```bash
sudo apt update
sudo apt install -y ffmpeg
```

Verify: `ffmpeg -version`

### Issue 2: "No module named 'tkinter'"

**Symptom**:
```
ModuleNotFoundError: No module named 'tkinter'
```

**Solution**:
```bash
sudo apt install python3-tk
```

### Issue 3: "Could not open audio device"

**Symptom**:
```
ERROR: Failed to initialize audio device
```

**Solutions**:

1. Check if microphone is connected:
   ```bash
   arecord -l  # List recording devices
   ```

2. Test recording:
   ```bash
   arecord -d 3 test.wav  # Record 3 seconds
   aplay test.wav         # Play back
   ```

3. Check PulseAudio:
   ```bash
   pulseaudio --check
   pulseaudio --start
   ```

### Issue 4: Auto-paste Not Working

**Symptom**: Transcription completes but text doesn't paste

**Solutions**:

1. Verify xdotool is installed:
   ```bash
   sudo apt install xdotool
   ```

2. Check clipboard access:
   ```bash
   echo "test" | xclip -selection clipboard
   xclip -selection clipboard -o  # Should output: test
   ```

3. Test xdotool manually:
   ```bash
   sleep 3 && xdotool type "test"  # Switch to text editor within 3s
   ```

### Issue 5: Whisper Model Download Fails

**Symptom**:
```
ERROR: Failed to download Whisper model
```

**Solutions**:

1. Check internet connection
2. Manually download model:
   ```bash
   python -c "import whisper; whisper.load_model('base')"
   ```

3. Use Google Speech as fallback (edit settings)

### Issue 6: High Memory Usage

**Symptom**: Application uses >2GB RAM

**Solutions**:

1. Use smaller Whisper model:
   - Edit config: `"whisper_model": "tiny"`

2. Switch to Google Speech:
   - Open settings (Alt+S)
   - Select "Google Speech" engine

3. Enable resource monitoring:
   ```bash
   ./voice_transcription_tool/monitor_voice_tool.sh
   ```

### Issue 7: Permission Denied on First Run

**Symptom**:
```
PermissionError: [Errno 13] Permission denied: '/tmp/voice_transcription.lock'
```

**Solution**:
```bash
# Remove stale lock file
rm /tmp/voice_transcription.lock

# Run again
python main.py
```

## Advanced Configuration

### Custom Installation Directory

```bash
# Install to custom location
git clone <repo-url> ~/my-apps/voice-transcription
cd ~/my-apps/voice-transcription
pip install -r requirements.txt

# Create desktop shortcut
cat > ~/.local/share/applications/voice-transcription.desktop <<EOF
[Desktop Entry]
Name=Voice Transcription Tool
Exec=python ~/my-apps/voice-transcription/main.py
Type=Application
Categories=Utility;Audio;
EOF
```

### System-wide Installation (Development Mode)

```bash
cd /path/to/text_whisperer
pip install -e .  # Editable installation

# Now you can run from anywhere:
voice-transcription
```

## Next Steps

After successful installation:

1. **Configure hotkeys**: Press Alt+S to open settings
2. **Test recording**: Press Alt+D to record your first transcription
3. **Review logs**: Check `logs/voice_transcription_*.log` for any warnings
4. **Read TROUBLESHOOTING.md**: For common usage issues

## Getting Help

- **Documentation**: See `docs/` directory
- **Logs**: `logs/voice_transcription_*.log`
- **Debug mode**: Run with `python main.py --debug`
- **Health monitoring**: `./voice_transcription_tool/monitor_voice_tool.sh`
