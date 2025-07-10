# Voice Transcription Tool - Setup Guide

A powerful speech-to-text application with global hotkeys, voice training capabilities, and cross-platform support.

## 🚀 Quick Setup (Recommended)

**Interactive Setup Script** - Handles everything automatically:

```bash
# Download all files to a directory
# Run the interactive setup script
python setup.py
```

**Bash Script Alternative**:
```bash
# For users who prefer bash
chmod +x setup.sh
./setup.sh
```

The setup scripts will:
- ✅ Check your Python version
- ✅ Create virtual environment (venv or conda)
- ✅ Install system dependencies
- ✅ Let you choose installation type
- ✅ Install Python packages
- ✅ Test the installation
- ✅ Show you next steps

## 📦 Available Installation Types

### 1. 🚀 Full Installation (Recommended)
- **Includes**: Whisper + Google Speech + PyAudio + all features
- **Best for**: Users who want maximum functionality
- **Requirements**: ~2GB RAM, internet for setup

### 2. 🎯 Local High-Quality 
- **Includes**: Whisper + PyAudio
- **Best for**: Privacy-focused users, offline usage
- **Pros**: Highest accuracy, completely offline
- **Cons**: Slower processing, more memory usage

### 3. ⚡ Online Fast
- **Includes**: Google Speech + PyAudio  
- **Best for**: Users who want speed
- **Pros**: Fast processing, low memory
- **Cons**: Requires internet, less accurate

### 4. 💡 Minimal Installation
- **Includes**: Google Speech + system audio tools
- **Best for**: Lightweight setups, older systems
- **Uses**: arecord/ffmpeg instead of PyAudio

## 🎯 Features

- **One-Handed Hotkeys**: Default F9 key for easy single-handed operation
- **Multiple Speech Engines**: Whisper (local) and Google Speech Recognition (online)
- **Smart Text Insertion**: Automatically insert transcribed text at cursor position
- **Voice Training System**: Record sample phrases to improve personal recognition accuracy
- **Memory System**: Stores recent transcriptions with searchable history
- **Cross-Application**: Works in browsers, documents, chat apps, IDEs, everywhere
- **Configurable Window Size**: Resize and save your preferred window dimensions
- **Extended Recording**: Up to 30 seconds per recording with progress indicator
- **Comprehensive Debugging**: Real-time debug panel and detailed logging

## 📋 Requirements Files

The project includes modular requirements files for different installation scenarios:

- **`requirements-base.txt`** - Core dependencies (keyboard, pyperclip)
- **`requirements-audio.txt`** - PyAudio for audio recording
- **`requirements-whisper.txt`** - Whisper for local speech recognition
- **`requirements-google.txt`** - Google Speech Recognition for online processing
- **`requirements-full.txt`** - Complete installation with all features
- **`requirements-minimal.txt`** - Lightweight installation

## 🛠 Manual Installation (Advanced Users)

If you prefer manual control over the installation process:

### Create Virtual Environment

**Using Python venv**:
```bash
python3 -m venv voice_transcription
source voice_transcription/bin/activate  # Linux/macOS
# or
voice_transcription\Scripts\activate     # Windows
```

**Using Conda**:
```bash
conda create -n voice_transcription python=3.9
conda activate voice_transcription
```

### Install System Dependencies

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get update
sudo apt-get install portaudio19-dev python3-dev alsa-utils
```

**Linux (CentOS/RHEL)**:
```bash
sudo yum install portaudio-devel python3-devel alsa-utils
```

**macOS**:
```bash
brew install portaudio
```

### Install Python Packages

**Choose your installation type**:

```bash
# Full installation
pip install -r requirements-full.txt

# Local high-quality (Whisper only)
pip install -r requirements-base.txt
pip install -r requirements-audio.txt
pip install -r requirements-whisper.txt

# Online fast (Google Speech only)  
pip install -r requirements-base.txt
pip install -r requirements-audio.txt
pip install -r requirements-google.txt

# Minimal installation
pip install -r requirements-minimal.txt
```

## 🔧 Troubleshooting Installation Issues

### PyAudio Build Errors (Linux)

**Error**: `fatal error: portaudio.h: No such file or directory`

**Solution**:
```bash
# Install development headers
sudo apt-get install portaudio19-dev python3-dev

# Try alternative installation
sudo apt-get install python3-pyaudio
pip install keyboard pyperclip
```

### Alternative Audio Methods

If PyAudio fails completely, the tool supports these fallback methods:

- **arecord** (Linux): `sudo apt-get install alsa-utils`
- **ffmpeg** (Cross-platform): `sudo apt-get install ffmpeg`
- **System audio tools**: The app will detect and use available options

### **Recording Issues**

**"Recording stops after certain length"**:
- Check debug panel for timeout messages
- Recording auto-stops at 30 seconds (configurable)
- Look for "⏰ Maximum recording time reached" in debug log

**"Button doesn't change back to Start Recording"**:
- Fixed with new progress indicator
- Recording progress bar shows time remaining
- Button automatically resets when recording completes

**"Voice recognition not working"**:
1. Click "🧪 Test Microphone" in debug panel
2. Check "📋 Audio Devices" to see available mics
3. Try switching speech engines in Settings
4. Check debug log for transcription errors

### **Settings Not Saving**

**"Google Speech engine doesn't stick"**:
- Fixed with enhanced logging
- Check debug panel for "✅ Engine changed to: google"
- Settings now validate engine availability before switching
- Config file saves all preferences automatically

### **Hotkey Problems**

**"Hotkeys not working"**:
1. Enable hotkey mode: "🔥 Toggle Hotkey Mode"
2. Check debug panel for hotkey registration messages
3. Try one-handed options: F9, F10, F11, F12
4. Avoid Ctrl+Shift+V (conflicts with terminal paste)

**"Need one-handed operation"**:
- Use F9 (new default) - easy thumb reach
- F10, F11, F12 alternatives
- ` (backtick) for top-left access

### **Window Size Issues**

**"Window too small/large"**:
1. Settings → "Window Settings"
2. Choose preset: Compact, Standard, Large, Extra Large
3. Or set custom width x height
4. Size automatically saved for next startup

### Speech Recognition Issues

**Whisper Model Download**: On first run, Whisper downloads ~140MB model
```bash
# Pre-download models (optional)
python -c "import whisper; whisper.load_model('base')"
```

**Google Speech Recognition**: Requires internet connection
```bash
pip install SpeechRecognition
```

## 🔑 **Linux Hotkey Setup (Important)**

Global hotkeys on Linux require special permissions for security. Here are your options:

### **Option 1: Quick Test with Sudo**
```bash
# Find your virtual environment python path
which python
# Example output: /home/user/project/.venv/bin/python

# Run with sudo using full path
sudo /home/user/project/.venv/bin/python voice_transcription.py

# Or preserve environment
sudo -E env PATH=$PATH python voice_transcription.py
```

### **Option 2: Permanent Fix (Recommended)**
```bash
# Add your user to input group
sudo usermod -a -G input $USER

# Logout and login (or reboot) for changes to take effect
sudo reboot

# Then run normally with hotkeys
python voice_transcription.py
```

### **Option 3: Test Without Hotkeys First**
```bash
# All features work except global hotkeys
python voice_transcription.py
```

**Note**: Even without hotkeys, you can use all features through the GUI buttons!

### **🎯 New One-Handed Hotkeys (Default: F9)**

The app now defaults to **F9** for one-handed operation! Other one-handed options:
- **F9, F10, F11, F12** - Function keys (easy reach)
- **` (backtick)** - Top-left corner key
- **Tab** - Easy access (may conflict with some apps)

**Why one-handed?** Allows you to keep typing with one hand while activating recording with the other!

## 🎮 Usage Instructions

### 1. Starting the Application

```bash
# Save the tool as voice_transcription.py
python voice_transcription.py
```

### 2. First-Time Setup

1. **Launch the app** - GUI window opens
2. **Check status** - Green "Ready" means everything is working
3. **Test recording** - Click "🎤 Start Recording" button
4. **Verify engine** - Bottom right shows your speech engine

### 3. Enabling Global Hotkeys

1. **Click "🔥 Toggle Hotkey Mode"** - Button turns to "ON"
2. **Status shows** - "Hotkey mode active (Ctrl+Shift+V)"
3. **Test globally** - Press Ctrl+Shift+V from any application

### 4. Recording and Transcription

**Manual Recording**:
- Click "🎤 Start Recording"
- Speak clearly into microphone
- Click "🛑 Stop Recording"
- Transcription appears in text area

**Hotkey Recording**:
- Press `Ctrl+Shift+V` from anywhere
- Speak (recording indicator shows)
- Press `Ctrl+Shift+V` again to stop
- Text automatically transcribed

### 6. Voice Training (NEW!)

**Access Voice Training**:
1. Click "⚙️ Settings" → "Start Voice Training"
2. **Read provided phrases** clearly into microphone
3. **Complete all 5 sample phrases** for best results
4. **Training data automatically saved** to improve future recognition

**Training Benefits**:
- ✅ **Improved accuracy** for your specific voice
- ✅ **Better recognition** of your speech patterns
- ✅ **Stored samples** for continuous learning
- ✅ **Progress tracking** with real-time feedback

**Training Tips**:
- Record in a **quiet environment**
- Speak at **normal pace and volume**
- Use the **same microphone** you'll use regularly
- Complete **all phrases** for maximum benefit

### 8. **Using the Debug Panel (NEW!)**

**Real-time Debugging**:
- **Debug Log Panel** at bottom shows live system status
- **Green ✅** = Success, **Red ❌** = Error, **Orange ⚠️** = Warning
- **Timestamps** on all messages for troubleshooting

**Debug Controls**:
- **🧪 Test Microphone** - Verify recording functionality
- **📋 Audio Devices** - List all available microphones  
- **🗑️ Clear Debug** - Clear the debug log
- **💾 Save Log** - Export debug log to file

**Troubleshooting Workflow**:
1. **Problem occurs** → Check debug panel for error messages
2. **Test components** → Use microphone test and device list
3. **Try different settings** → Switch engines, change hotkeys
4. **Save logs** → Export debug info if issues persist

### 9. **Window Configuration (NEW!)**

**Resize Window**:
- Settings → "Window Settings"
- **Presets**: Compact (800x600), Standard (900x700), Large (1000x800), Extra Large (1200x900)
- **Custom Size**: Enter specific width and height
- **Auto-save**: Size preference saved for next startup

**Why Configure Size?**
- **Compact**: Minimal screen space usage
- **Large**: Better visibility of transcriptions and debug info
- **Custom**: Perfect fit for your workflow and screen resolution

### 10. Using Transcribed Text

**Copy to Clipboard**:
- Click "📋 Copy to Clipboard"
- Paste anywhere with Ctrl+V

**Insert at Cursor**:
- Position cursor where you want text
- Click "📝 Insert at Cursor"
- Text appears at cursor location

## ⚙️ Configuration

### Speech Engine Settings

**Access Settings**:
1. Click "⚙️ Settings" button
2. Choose between Whisper and Google Speech Recognition

**Whisper (Local)**:
- ✅ Works offline
- ✅ High accuracy
- ✅ Privacy (no data sent online)
- ❌ Slower processing
- ❌ Larger memory usage

**Google Speech Recognition (Online)**:
- ✅ Fast processing
- ✅ Low memory usage
- ❌ Requires internet
- ❌ Audio sent to Google

### Audio Settings

**Recording Parameters**:
- Sample Rate: 16000 Hz (optimized for speech)
- Channels: 1 (mono)
- Max Duration: 10 seconds per recording

**Custom Hotkey** (Advanced):
Edit the code to change from Ctrl+Shift+V:
```python
# In setup_hotkeys() method
keyboard.add_hotkey('ctrl+alt+r', self.hotkey_toggle_recording)  # Example
```

## 🎓 Advanced Features

### Voice Training (Framework Ready)

The database structure supports voice training:
- Personal voice profiles
- Custom vocabulary
- Accuracy improvements over time
- Sample audio storage

*Full implementation coming in next version*

### Memory System

**Automatic History**:
- Last 50 transcriptions stored
- Timestamped entries
- Searchable database
- Persistent across sessions

**Database Location**: `voice_transcriptions.db` in app directory

### Cross-Application Usage

**Tested Applications**:
- Web browsers (Chrome, Firefox, Edge)
- Text editors (VS Code, Sublime, Vim)
- Office apps (LibreOffice, Google Docs)
- Chat applications (Slack, Discord, Teams)
- Terminal and command line tools

## 🔍 Verification & Testing

### Test Speech Recognition

1. **Open the app**
2. **Start recording** (button or hotkey)
3. **Speak clearly**: "This is a test of speech recognition"
4. **Check transcription** accuracy in the text area

### Test Global Hotkeys

1. **Enable hotkey mode** in the app
2. **Open any text application** (notepad, browser, etc.)
3. **Position cursor** where you want text
4. **Press Ctrl+Shift+V** and speak
5. **Press Ctrl+Shift+V** again to stop
6. **Click "Insert at Cursor"** to place text

### Verify Audio Recording

```bash
# Test system audio (Linux)
arecord -d 3 -f cd test.wav && aplay test.wav

# Check microphone levels
alsamixer  # Use F4 to switch to capture, adjust input levels
```

## 🐛 Common Issues & Solutions

### "No speech recognition engine available"
- Install either Whisper or SpeechRecognition
- Check error messages in terminal

### "No audio recording method available"
- Install PyAudio, arecord, or ffmpeg
- Check microphone permissions

### Hotkeys not working
- Run as administrator/sudo (some systems)
- Check if other apps are capturing the same hotkey

### Poor transcription accuracy
- Speak clearly and slowly
- Check microphone levels
- Use Whisper for better accuracy
- Ensure quiet environment

### High memory usage
- Whisper loads large models (~1GB RAM)
- Use Google Speech Recognition for lower memory usage

## 📚 Dependencies Reference

### Required
```
keyboard>=0.13.5    # Global hotkey detection
pyperclip>=1.9.0    # Clipboard operations
```

### Audio (choose one)
```
pyaudio>=0.2.14     # Python audio library (preferred)
# OR system tools: arecord, ffmpeg
```

### Speech Recognition (choose one)
```
openai-whisper>=20231117    # Local speech recognition (recommended)
SpeechRecognition>=3.10.0   # Online speech recognition
```

### Additional
```
tkinter             # GUI (usually included with Python)
sqlite3             # Database (included with Python)
threading           # Background processing (included)
```

## 🎯 Performance Tips

**For Best Accuracy**:
- Use a good quality microphone
- Record in quiet environment
- Speak clearly at normal pace
- Use Whisper engine for better results

**For Best Performance**:
- Use Google Speech Recognition for speed
- Close other audio applications
- Ensure stable internet (for Google Speech)

**For Privacy**:
- Use Whisper (fully local processing)
- Audio never leaves your computer

## 🔄 Updates & Maintenance

**Database Cleanup**:
```python
# Optional: Clear old transcriptions
import sqlite3
conn = sqlite3.connect('voice_transcriptions.db')
conn.execute("DELETE FROM transcriptions WHERE timestamp < date('now', '-30 days')")
conn.commit()
```

**Model Updates**:
```bash
# Update Whisper models
pip install --upgrade openai-whisper
```

## 📞 Support & Troubleshooting

If you encounter issues:

1. **Check the terminal output** for error messages
2. **Verify all dependencies** are installed correctly
3. **Test microphone access** with system tools
4. **Try different speech engines** (Whisper vs Google)
5. **Check audio recording methods** (PyAudio vs system tools)

**Getting Help**:
- Run `python voice_transcription.py` and check error messages
- Test individual components (microphone, speech engines)
- Verify permissions and system dependencies

---

## 📁 Project Structure

Your project directory should contain:

```
voice-transcription-tool/
├── voice_transcription.py      # Main application
├── setup.py                    # Interactive setup script
├── setup.sh                    # Bash setup script
├── setup.md                    # This setup guide
├── requirements-base.txt       # Core dependencies
├── requirements-audio.txt      # Audio recording
├── requirements-whisper.txt    # Local speech recognition  
├── requirements-google.txt     # Online speech recognition
├── requirements-full.txt       # Complete installation
├── requirements-minimal.txt    # Lightweight installation
└── voice_transcriptions.db    # Created after first run
```

## 🚀 Getting Started

1. **Download all files** to a directory
2. **Run setup script**: `python setup.py` (or `./setup.sh`)
3. **Follow prompts** to choose your installation type
4. **Launch application**: `python voice_transcription.py`
5. **Test recording** and enable global hotkeys

**Ready to start transcribing?** The setup scripts handle everything automatically! 🎤✨