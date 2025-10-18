# Troubleshooting Guide

Comprehensive troubleshooting guide for Voice Transcription Tool v2.0 based on production testing and stress validation.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Audio Issues](#audio-issues)
- [Transcription Problems](#transcription-problems)
- [Hotkey Issues](#hotkey-issues)
- [Auto-paste Problems](#auto-paste-problems)
- [Performance Issues](#performance-issues)
- [Application Crashes](#application-crashes)
- [Advanced Debugging](#advanced-debugging)
- [Filing Bug Reports](#filing-bug-reports)

## Quick Diagnostics

Before diving into specific issues, run these quick diagnostic checks:

### 1. Check Application Logs

```bash
# View recent logs
tail -f logs/voice_transcription_*.log

# Search for errors
grep ERROR logs/voice_transcription_*.log

# View full log with timestamps
cat logs/voice_transcription_$(date +%Y%m%d).log
```

### 2. Run Debug Mode

```bash
python main.py --debug
```

Debug mode provides detailed output about:
- Configuration loading
- Audio device initialization
- Speech engine selection
- Hotkey registration
- Recording state changes

### 3. Verify System Dependencies

```bash
# Check FFmpeg (critical for Whisper)
ffmpeg -version

# Check xdotool (for auto-paste)
xdotool --version

# Check Python version
python3 --version  # Should be 3.7+

# Check tkinter
python3 -c "import tkinter; print('Tkinter OK')"
```

### 4. Test Audio Hardware

```bash
# List audio input devices
arecord -l

# Record 3-second test
arecord -d 3 test.wav

# Play back
aplay test.wav

# Clean up
rm test.wav
```

## Audio Issues

### Issue: "Could not open audio device"

**Symptoms**:
- Application fails to start
- Error message: "Failed to initialize audio device"
- Red error in debug log

**Diagnosis**:
```bash
# Check if any application is using microphone
lsof /dev/snd/*

# List available input devices
python3 -c "import pyaudio; p = pyaudio.PyAudio(); [print(f'{i}: {p.get_device_info_by_index(i)[\"name\"]}') for i in range(p.get_device_count()) if p.get_device_info_by_index(i)['maxInputChannels'] > 0]"
```

**Solutions**:

1. **Close other applications** using microphone (Zoom, Discord, etc.)

2. **Restart PulseAudio**:
   ```bash
   pulseaudio --kill
   pulseaudio --start
   ```

3. **Select different input device**:
   - Press Alt+S (Settings)
   - Go to "Audio" tab
   - Click "Refresh Devices"
   - Select working device from dropdown

4. **Check microphone permissions**:
   ```bash
   # Test microphone access
   arecord -d 1 -f cd test.wav
   ```

### Issue: "No speech detected" (Silence Detection)

**Symptoms**:
- Recording completes but shows "No speech detected"
- Audio feedback sounds play but no transcription
- Works sometimes but not consistently

**Diagnosis**:
```bash
# Check microphone volume
alsamixer  # Press F4 for Capture, ensure not muted and volume is high

# Test with debug mode to see RMS values
python main.py --debug
# Press Alt+D and speak - look for "RMS: X.XX" in output
```

**Solutions**:

1. **Increase microphone volume**:
   ```bash
   alsamixer
   # F4 for Capture
   # Use arrow keys to increase volume
   # Press M to unmute if needed
   ```

2. **Speak closer to microphone** - Silence threshold is RMS < 500.0

3. **Adjust silence threshold** (Advanced):
   Edit `voice_transcription_config.json`:
   ```json
   {
     "silence_threshold": 300.0,  // Lower = more sensitive (default: 500.0)
     ...
   }
   ```

4. **Test in Settings**:
   - Press Alt+S
   - Go to "Audio" tab
   - Click "Test Recording"
   - Verify you see audio visualization

### Issue: Distorted or Choppy Audio

**Symptoms**:
- Transcriptions are inaccurate
- Audio sounds choppy in recordings
- Intermittent audio dropouts

**Solutions**:

1. **Reduce CPU load** - Close resource-heavy applications

2. **Increase buffer size** (reduces dropouts):
   Edit `voice_transcription_tool/audio/recorder.py` (line 39):
   ```python
   self.chunk_size = 2048  # Increase from 1024
   ```

3. **Check system resources**:
   ```bash
   # Monitor during recording
   ./voice_transcription_tool/monitor_voice_tool.sh
   ```

4. **Disable other audio applications** - Some apps interfere with PyAudio

## Transcription Problems

### Issue: Low Transcription Accuracy

**Symptoms**:
- Transcriptions contain many errors
- Wrong words or missing words
- Inconsistent accuracy

**Solutions**:

1. **Use Whisper engine instead of Google Speech**:
   - Press Alt+S (Settings)
   - Select "Whisper" from Engine dropdown
   - Whisper is significantly more accurate

2. **Upgrade Whisper model**:
   Edit `voice_transcription_config.json`:
   ```json
   {
     "whisper_model": "small",  // Upgrade from "base" (default)
     ...
   }
   ```
   Models by accuracy (higher = better but slower):
   - tiny < base < **small** < medium < large

3. **Improve recording quality**:
   - Use better microphone
   - Record in quiet environment
   - Speak clearly and at normal pace
   - Position microphone 6-12 inches from mouth

4. **Check for background noise**:
   ```bash
   # Record silence and check RMS
   python main.py --debug
   # Press Alt+D without speaking
   # Look for RMS values in log - should be < 100.0
   ```

### Issue: Whisper Engine Not Loading

**Symptoms**:
- Application falls back to Google Speech
- Log shows: "Whisper engine not available"
- First transcription attempt hangs

**Diagnosis**:
```bash
# Test Whisper installation
python3 -c "import whisper; print('Whisper OK')"

# Check if FFmpeg is available
ffmpeg -version

# Test model loading
python3 -c "import whisper; model = whisper.load_model('base'); print('Model loaded')"
```

**Solutions**:

1. **Install Whisper**:
   ```bash
   pip install openai-whisper
   ```

2. **Install FFmpeg** (required for Whisper):
   ```bash
   sudo apt install ffmpeg
   ```

3. **Download model manually**:
   ```bash
   python3 -c "import whisper; whisper.load_model('base')"
   # This downloads ~1.5GB model weights
   ```

4. **Check disk space** - Whisper models require 1-3GB:
   ```bash
   df -h ~  # Check home directory space
   ```

### Issue: Transcription Takes Too Long

**Symptoms**:
- Transcription takes >30 seconds
- Application appears frozen after recording
- High CPU usage during transcription

**Solutions**:

1. **Use smaller Whisper model**:
   ```json
   {
     "whisper_model": "tiny",  // Fastest, lower accuracy
     ...
   }
   ```

2. **Enable GPU acceleration** (if you have NVIDIA GPU):
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

   # Verify CUDA is available
   python3 -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
   ```

3. **Switch to Google Speech** (faster but requires internet):
   - Press Alt+S
   - Select "Google Speech" from dropdown

4. **Record shorter clips** - Transcription time scales with audio length

## Hotkey Issues

### Issue: Hotkeys Not Working

**Symptoms**:
- Alt+D doesn't start recording
- No response when pressing hotkeys
- Hotkeys work in GUI but not globally

**Diagnosis**:
```bash
# Check if pynput is installed
python3 -c "import pynput; print('pynput OK')"

# Run debug mode and watch for hotkey registration
python main.py --debug | grep -i hotkey
```

**Solutions**:

1. **Verify pynput is installed**:
   ```bash
   pip install pynput
   ```

2. **Check for hotkey conflicts**:
   - Try different key combination in Settings (Alt+S)
   - Some desktop environments reserve Alt+D

3. **No sudo required** - Unlike keyboard library, pynput works without root:
   ```bash
   python main.py  # No sudo needed
   ```

4. **Test in debug mode**:
   ```bash
   python main.py --debug
   # Press Alt+D - you should see "Hotkey pressed: Alt+D"
   ```

### Issue: Hotkey Triggers Multiple Times

**Symptoms**:
- Single press starts/stops multiple recordings
- Rapid toggles when holding hotkey
- Inconsistent behavior

**Solution**:
This is expected behavior - release the hotkey to stop recording. The application uses press/release model:
- **Press Alt+D**: Start recording
- **Release Alt+D**: Stop recording and transcribe

If you need click-to-toggle instead, this requires code modification (see CLAUDE.md).

## Auto-paste Problems

### Issue: Auto-paste Not Working

**Symptoms**:
- Transcription completes but text doesn't paste
- Text appears in application but not in other apps
- Clipboard copy works but paste doesn't

**Diagnosis**:
```bash
# Check if xdotool is installed
xdotool version

# Test xdotool manually
sleep 3 && xdotool type "test"
# Switch to a text editor within 3 seconds
# "test" should appear
```

**Solutions**:

1. **Install xdotool** (Linux):
   ```bash
   sudo apt install xdotool
   ```

2. **Enable auto-paste in settings**:
   - Press Alt+S
   - Check "Auto-paste after transcription"

3. **Check window focus** - Auto-paste requires focus return:
   - Click in target application before recording
   - Ensure no modal dialogs are blocking focus

4. **Test with simple application**:
   - Open gedit or kate
   - Click in text area
   - Press Alt+D, speak, release
   - Text should appear automatically

5. **Terminal applications** - Use Ctrl+Shift+V:
   The application detects terminal windows and uses Ctrl+Shift+V instead of Ctrl+V

### Issue: Auto-paste Pastes in Wrong Application

**Symptoms**:
- Text appears in application that wasn't focused
- Text pastes into Voice Transcription window itself

**Cause**: Focus changes between recording start and completion.

**Solution**:
- Keep focus in target application while recording
- Don't click on Voice Transcription window during recording
- Use minimized mode: `python main.py --minimized`

## Performance Issues

### Issue: High Memory Usage

**Symptoms**:
- Application uses >2GB RAM
- System becomes slow during use
- Resource limit warnings in logs

**Diagnosis**:
```bash
# Monitor memory usage
./voice_transcription_tool/monitor_voice_tool.sh

# Or check manually
ps aux | grep python | grep main.py
```

**Expected Memory Usage**:
- **With Whisper (base model)**: 800MB - 1.5GB
- **With Google Speech**: 200MB - 400MB
- **Baseline (no transcription)**: 150MB - 250MB

**Solutions**:

1. **Use smaller Whisper model**:
   ```json
   {
     "whisper_model": "tiny",  // ~600MB instead of ~1.2GB
     ...
   }
   ```

2. **Switch to Google Speech**:
   - Press Alt+S
   - Select "Google Speech" engine
   - Much lower memory footprint

3. **Restart application periodically** if memory grows over time:
   ```bash
   # If memory exceeds 2GB, restart
   pkill -f "python.*main.py"
   python main.py
   ```

4. **Check for memory leaks** (unlikely after Phase 5 testing):
   ```bash
   python scripts/memory_leak_test.py --cycles 1000
   # Should show < 20% growth over 1000 cycles
   ```

### Issue: High CPU Usage

**Symptoms**:
- CPU at 100% during transcription (normal)
- CPU high even when idle (problem)
- System becomes unresponsive

**Diagnosis**:
```bash
# Check CPU usage
top -p $(pgrep -f "python.*main.py")

# Monitor during idle and active states
./voice_transcription_tool/monitor_voice_tool.sh
```

**Expected CPU Usage**:
- **Idle (standby)**: 0-5% CPU
- **Recording**: 5-15% CPU (audio capture)
- **Transcribing**: 80-100% CPU (normal for Whisper)

**Solutions**:

1. **High CPU during transcription is normal** - Whisper is CPU-intensive:
   - Use GPU acceleration for faster processing
   - Or use Google Speech for lower CPU usage

2. **High CPU when idle** (problem):
   - Check logs for stuck threads
   - Kill and restart application
   - File bug report if persistent

3. **Enable GPU for Whisper**:
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```
   This reduces CPU usage from 100% to 10-20% during transcription

### Issue: Application Freezes System

**Symptoms**:
- Entire system becomes unresponsive
- Mouse/keyboard lag during transcription
- Desktop environment freezes

**Emergency Recovery** (from TTY):
```bash
# Switch to TTY: Ctrl+Alt+F2
# Login and run:
./voice_transcription_tool/debug_freeze.sh

# This will:
# - Kill the application
# - Capture system state
# - Free resources
```

**Solutions**:

1. **Reduce resource limits**:
   Edit `voice_transcription_config.json`:
   ```json
   {
     "health_monitor": {
       "memory_limit_mb": 1024,  // Lower from 2048
       "cpu_limit_percent": 90,  // Lower from 98
       "check_interval": 15       // Check more frequently
     },
     ...
   }
   ```

2. **Use lighter speech engine**:
   - Switch to Google Speech (cloud-based, much lighter)
   - Or use Whisper "tiny" model

3. **Close other applications** during transcription

4. **Upgrade hardware** if consistently freezing:
   - Minimum recommended: 8GB RAM, quad-core CPU
   - For comfortable Whisper use: 16GB RAM, 8+ cores

## Application Crashes

### Issue: Application Won't Start

**Symptoms**:
- Python error on startup
- "Another instance is already running"
- ImportError or ModuleNotFoundError

**Solutions**:

1. **Check for stale lock file**:
   ```bash
   rm /tmp/voice_transcription.lock
   python main.py
   ```

2. **Verify dependencies**:
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

3. **Check for import errors**:
   ```bash
   python main.py --debug 2>&1 | grep -i "error\|exception"
   ```

4. **Test Python version**:
   ```bash
   python3 --version  # Must be 3.7+
   ```

### Issue: Crashes During Transcription

**Symptoms**:
- Application closes unexpectedly
- Segmentation fault
- "Process terminated" error

**Diagnosis**:
```bash
# Check crash logs
grep -i "crash\|segfault\|killed" logs/voice_transcription_*.log

# Check system logs
journalctl -u python --since "1 hour ago" | grep -i error

# Run with increased verbosity
python main.py --debug 2>&1 | tee crash_log.txt
```

**Solutions**:

1. **Update dependencies** (especially PyAudio, which can segfault):
   ```bash
   pip install --upgrade pyaudio pynput pygame
   ```

2. **Check for out-of-memory kills**:
   ```bash
   dmesg | grep -i "killed process"
   # If you see python process, you're out of memory
   ```

3. **Run stability test** to reproduce:
   ```bash
   ./scripts/stability_test.sh --duration 4
   # Let run for 4 hours to catch intermittent crashes
   ```

4. **File bug report** with crash log (see below)

### Issue: Crashes on Exit

**Symptoms**:
- Error when closing application
- "Exception in thread" messages
- Cleanup warnings

**Cause**: Background threads not properly stopped (rare after Phase 4 fixes)

**Solution**:
This is usually harmless - background threads terminate after cleanup. If persistent:

```bash
# Force kill all instances
pkill -9 -f "python.*main.py"

# Remove lock file
rm /tmp/voice_transcription.lock

# Restart cleanly
python main.py
```

## Advanced Debugging

### Health Monitor

Monitor resource usage in real-time:

```bash
./voice_transcription_tool/monitor_voice_tool.sh
```

**What it shows**:
- Current memory usage vs. limit
- CPU percentage
- Recording state
- Process uptime
- Resource limit warnings

**When to use**:
- Diagnosing high resource usage
- Monitoring during long recording sessions
- Identifying memory leaks

### Debug Freeze Script

For system freezes, use from TTY:

```bash
# Switch to TTY: Ctrl+Alt+F2
./voice_transcription_tool/debug_freeze.sh
```

**What it does**:
- Captures process state before killing
- Logs CPU and memory usage
- Shows all running threads
- Saves debug snapshot to logs/

### Memory Leak Testing

Test for memory leaks with sustained load:

```bash
# Cycle-based test (1000 recordings)
python scripts/memory_leak_test.py --cycles 1000 --log-interval 100

# Duration-based test (1 hour)
python scripts/memory_leak_test.py --duration 3600 --check-interval 60
```

**Expected results**:
- Memory growth < 20% over 1000 cycles
- No "leak detected" warnings
- JSON report generated in logs/

**If leak detected**:
- File bug report with generated JSON report
- Use Google Speech as temporary workaround

### Stability Testing

Multi-hour background testing:

```bash
# Run 8-hour stability test
./scripts/stability_test.sh --duration 8 --interval 300

# Check results
cat logs/stability_test_*.log
```

**Expected behavior**:
- 0 crashes over test duration
- Success rate > 95%
- Memory growth < 30%

## Filing Bug Reports

If you encounter a persistent issue not resolved by this guide, please file a bug report with:

### Required Information

1. **System details**:
   ```bash
   uname -a
   python3 --version
   pip list | grep -E "pyaudio|pynput|whisper|torch"
   ```

2. **Log file**:
   ```bash
   # Attach the most recent log
   cat logs/voice_transcription_$(date +%Y%m%d).log
   ```

3. **Steps to reproduce**:
   - Exact sequence of actions
   - Expected vs. actual behavior
   - Frequency (always, sometimes, once)

4. **Configuration**:
   ```bash
   # Sanitize personal info, then attach
   cat voice_transcription_config.json
   ```

### Optional But Helpful

- Memory leak test results (if performance issue)
- Crash dump (if segfault)
- Audio device info: `arecord -l`
- Debug log: `python main.py --debug 2>&1 | tee debug.log`

## Additional Resources

- **Installation Guide**: See `docs/INSTALLATION.md`
- **User Documentation**: See `docs/` directory
- **Development Guide**: See `CLAUDE.md` in project root
- **Test Suite**: Run `cd voice_transcription_tool && pytest tests/ -v`

## Getting Further Help

If this guide doesn't resolve your issue:

1. Check logs: `logs/voice_transcription_*.log`
2. Run debug mode: `python main.py --debug`
3. Search closed issues in repository
4. File detailed bug report with required information above
