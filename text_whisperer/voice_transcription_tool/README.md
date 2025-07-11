# Voice Transcription Tool v2.0

A modern, AI-powered voice transcription application with wake word detection, voice training, and seamless desktop integration.

![Voice Transcription Tool](voice-transcription.svg)

## 🚀 Features

### Core Functionality
- **🎤 Voice Transcription**: Convert speech to text using Whisper or Google Speech Recognition
- **🎯 Wake Word Detection**: Hands-free activation with customizable wake words
- **🎓 Voice Training**: Improve accuracy by training the system with your voice
- **📋 Auto-Paste**: Automatic clipboard copy and paste to any application
- **🔥 Global Hotkeys**: Quick recording with configurable keyboard shortcuts
- **🖥️ System Tray**: Background operation with minimal UI

### Modern Interface
- **📱 Tabbed Interface**: Clean, organized layout with main/history/advanced tabs
- **🔧 Advanced Mode**: Hide complex features for simple user experience
- **📜 History Management**: View and reuse previous transcriptions
- **⚙️ Comprehensive Settings**: Customize all aspects of the application

### Desktop Integration
- **🖱️ Applications Menu**: Launch from your desktop applications menu
- **💻 Command Line**: Multiple launch options with and without privileges
- **🎨 Custom Icon**: Professional application icon and branding
- **🔔 Notifications**: System notifications for transcription completion

## 📦 Installation

### Quick Install
```bash
# Clone or download the project
cd voice_transcription_tool

# Install dependencies
pip install -r requirements.txt

# Install as desktop application
python install_package.py
```

### Manual Setup
```bash
# Install Python dependencies
pip install torch whisper pyaudio speech_recognition pyperclip keyboard pystray pygame

# Optional: Wake word detection
pip install openwakeword onnxruntime

# Run directly
python main.py
```

## 🎮 Usage

### Desktop Application
1. **Applications Menu**: Look for "Voice Transcription Tool" in your applications
2. **Command Line**: 
   - `voice-transcription` - Launch with GUI password prompt for hotkeys
   - `voice-transcription-user` - Launch without hotkeys (GUI only)

### Basic Operation
1. **Start Recording**: Click the 🎤 button or use your configured hotkey
2. **Stop Recording**: Click again or press hotkey to stop
3. **View Results**: Transcription appears in the main text area
4. **Copy/Paste**: Text is automatically copied to clipboard and optionally pasted

### Advanced Features
1. **Enable Advanced Mode**: Toggle "Advanced Mode" in the toolbar
2. **Wake Word Setup**: 
   - Configure wake words in Settings
   - Train with "Train Wake Word" for better accuracy
   - Test with "Test Live" to verify detection
3. **Voice Training**: Use "Start Voice Training" to improve recognition

## ⚙️ Configuration

### Settings Categories
- **🎤 Audio**: Input device, feedback options, recording duration
- **🧠 Speech Recognition**: Engine selection (Whisper/Google), confidence thresholds
- **⌨️ Hotkeys**: Customize recording shortcuts
- **📋 Clipboard & Auto-Paste**: Automatic copying and pasting behavior
- **🎯 Wake Word**: Detection settings, threshold tuning
- **🎓 Voice Training**: Manage training data and profiles

### Configuration File
Settings are automatically saved to `voice_transcription_config.json`:
```json
{
  "hotkey_combination": "capslock",
  "current_engine": "whisper",
  "audio_rate": 16000,
  "auto_copy_to_clipboard": true,
  "auto_paste_mode": true,
  "wake_word_enabled": true,
  "wake_words": ["hey computer"],
  "wake_word_threshold": 0.5
}
```

## 🛠️ Technical Details

### Architecture
- **Modular Design**: Separated concerns with dedicated modules
- **Thread-Safe**: Background audio processing with queue communication
- **Cross-Platform**: Works on Linux, Windows, and macOS
- **Extensible**: Plugin-ready architecture for new speech engines

### Dependencies
- **Core**: Python 3.8+, tkinter (GUI), threading, queue
- **Audio**: PyAudio (recording), pygame (feedback)
- **Speech**: Whisper (local AI), SpeechRecognition (Google API)
- **System**: pyperclip (clipboard), keyboard (hotkeys), pystray (tray)
- **Optional**: openWakeWord (wake word detection), onnxruntime (AI inference)

### Performance
- **Memory Usage**: ~100-200MB (depending on loaded models)
- **CPU Usage**: Minimal when idle, moderate during transcription
- **Startup Time**: 2-5 seconds (model loading)
- **Transcription Speed**: Real-time to 2x real-time (depending on engine)

## 🧪 Testing

### Automated Tests
```bash
# Run functionality tests
python test_gui_functionality.py

# Run unit tests
python -m pytest tests/ -v

# Check coverage
python run_tests.py
```

### Manual Testing
1. **Basic Recording**: Test record/stop functionality
2. **Engine Switching**: Try both Whisper and Google engines
3. **Auto-Paste**: Test in different applications
4. **Wake Word**: Configure and test wake word detection
5. **Voice Training**: Complete training session
6. **System Tray**: Test minimize/restore
7. **Hotkeys**: Test with different key combinations

## 🔧 Troubleshooting

### Common Issues

**Hotkeys not working**
- Run with sudo: `sudo voice-transcription-launch`
- Or use GUI-only mode: `voice-transcription-user`

**Audio not recording**
- Check microphone permissions
- Select correct input device in Settings
- Test with `python -c "import pyaudio; print('PyAudio OK')"`

**Wake word not detecting**
- Increase microphone volume
- Lower threshold in Settings (0.3-0.5)
- Complete wake word training
- Ensure clear pronunciation

**Transcription quality poor**
- Use Whisper engine for better accuracy
- Complete voice training
- Ensure quiet environment
- Speak clearly and at normal pace

### Log Files
- **Debug Log**: Check latest file in `logs/` directory
- **Live Debug**: Enable in Advanced tab debug panel
- **System Log**: Use `journalctl -f` to see system messages

## 🤝 Contributing

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-cov

# Run tests
python -m pytest

# Code style
python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

### Architecture Overview
```
voice_transcription_tool/
├── main.py                 # Application entry point
├── gui/
│   └── main_window.py      # Main GUI implementation
├── config/
│   ├── settings.py         # Configuration management
│   └── database.py         # SQLite database operations
├── audio/
│   ├── recorder.py         # Audio capture
│   ├── devices.py          # Device management
│   └── feedback.py         # Audio feedback
├── speech/
│   ├── engines.py          # Speech recognition engines
│   └── training.py         # Voice training
└── utils/
    ├── hotkeys.py          # Global hotkey management
    ├── autopaste.py        # Auto-paste functionality
    ├── system_tray.py      # System tray integration
    ├── wake_word.py        # Wake word detection
    └── logger.py           # Logging utilities
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI Whisper**: State-of-the-art speech recognition
- **SpeechRecognition**: Google Speech API integration
- **openWakeWord**: Wake word detection library
- **PyAudio**: Cross-platform audio I/O
- **Contributors**: Thanks to all who contributed to this project

## 📞 Support

- **Issues**: Report bugs on the GitHub Issues page
- **Documentation**: This README and inline code documentation
- **Community**: Join discussions on GitHub Discussions

---

**Voice Transcription Tool v2.0** - Making voice-to-text accessible and powerful for everyone.