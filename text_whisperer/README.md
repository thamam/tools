# Voice Transcription Tool v2.0

A powerful speech-to-text application with global hotkeys, voice training, and modular architecture.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r voice_transcription_tool/requirements.txt

# Run with global hotkeys (recommended)
./voice_transcription_tool/launch.sh

# Run with GUI password prompt
./voice_transcription_tool/launch-gui.sh

# Run without hotkeys (for testing)
./voice_transcription_tool/run.sh

# Or install as package
pip install -e .
voice-transcription
```

### Launch Options

1. **`launch.sh`** - Terminal launcher with sudo (hotkeys work)
2. **`launch-gui.sh`** - GUI password prompt (hotkeys work)
3. **`run.sh`** - No sudo required (hotkeys disabled)
4. **`voice-transcription.desktop`** - Desktop entry for app menu

## 🏗️ Architecture

This is a refactored version with modular architecture:

- **config/**: Configuration and database management
- **audio/**: Audio recording and device management  
- **speech/**: Speech recognition engines and training
- **gui/**: User interface components
- **utils/**: Utilities (hotkeys, logging)

## 📦 Features

- ✅ Multiple speech engines (Whisper, Google Speech)
- ✅ Global hotkeys (F9 default, one-handed)
- ✅ Voice training for improved accuracy
- ✅ Cross-platform audio recording
- ✅ Configurable window size and settings
- ✅ Comprehensive debug logging
- ✅ Modular, maintainable codebase

## 🔧 Development

```bash
# Run tests (when implemented)
python -m pytest tests/

# Run specific module
python -c "from audio.recorder import AudioRecorder; print('Audio OK')"

# Debug mode
python voice_transcription_tool/main.py --debug
```

## 📋 Migration from v1.0

If you're upgrading from the monolithic version:

1. Your settings will be preserved (voice_transcription_config.json)
2. Your voice training data will be preserved (voice_transcriptions.db) 
3. All features remain the same, just better organized

## 🎤 Usage

1. **Start the app**: `python voice_transcription_tool/main.py`
2. **Test recording**: Click "🎤 Start Recording"
3. **Enable hotkeys**: Click "🔥 Toggle Hotkey Mode"
4. **Use F9 globally**: Press F9 from any application to record
5. **Train your voice**: Settings → "Start Voice Training"
