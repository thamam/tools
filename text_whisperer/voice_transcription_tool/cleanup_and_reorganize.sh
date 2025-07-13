#!/bin/bash
# Cleanup and Reorganization Script for Voice Transcription Tool
# This will move files to proper locations and remove clutter

set -e  # Exit on any error

echo "=== Voice Transcription Tool Cleanup & Reorganization ==="
echo "This will reorganize the project structure and remove clutter"
echo ""

# Confirm before proceeding
read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

echo "Starting cleanup..."

# Create new directory structure
echo "📁 Creating new directory structure..."
mkdir -p docs
mkdir -p scripts
mkdir -p dist

# Move documentation files to docs/
echo "📄 Moving documentation files..."
mv CLAUDE.md docs/ 2>/dev/null || true
mv HOTKEY_SETUP.md docs/ 2>/dev/null || true
mv IMPROVEMENT_PLAN.md docs/ 2>/dev/null || true
mv INSTALL.md docs/ 2>/dev/null || true
mv LINUX_HOTKEY_SOLUTION.md docs/ 2>/dev/null || true

# Move script files to scripts/
echo "🔧 Moving script files..."
mv launch.sh scripts/ 2>/dev/null || true
mv launch-gui.sh scripts/ 2>/dev/null || true
mv launch-user.sh scripts/ 2>/dev/null || true
mv run.py scripts/ 2>/dev/null || true
mv setup_background_service.sh scripts/ 2>/dev/null || true
mv setup_input_group.sh scripts/ 2>/dev/null || true
mv start_background.sh scripts/ 2>/dev/null || true
mv start_on_login.sh scripts/ 2>/dev/null || true
mv start_with_hotkeys.sh scripts/ 2>/dev/null || true
mv status_and_control.sh scripts/ 2>/dev/null || true
mv stop_background.sh scripts/ 2>/dev/null || true
mv stop_background_process.sh scripts/ 2>/dev/null || true
mv install_package.py scripts/ 2>/dev/null || true

# Move build artifacts to dist/
echo "📦 Moving build artifacts..."
mv voice-transcription-tool_*.deb dist/ 2>/dev/null || true
mv voice-transcription-tool_*/ dist/ 2>/dev/null || true
mv voice-transcription.desktop dist/ 2>/dev/null || true
mv voice-transcription.svg dist/ 2>/dev/null || true

# Remove old/obsolete files
echo "🗑️  Removing obsolete files..."
rm -f compare_hotkey_libraries.py 2>/dev/null || true
rm -f migrate_to_pynput.py 2>/dev/null || true
rm -f test_hotkey_alternatives.py 2>/dev/null || true
rm -f test_pynput_simple.py 2>/dev/null || true
rm -f utils/hotkeys_old.py 2>/dev/null || true
rm -f utils/hotkeys_pynput.py 2>/dev/null || true

# Clean up any temporary files
echo "🧹 Cleaning temporary files..."
rm -f .voice_transcription.pid 2>/dev/null || true
rm -rf __pycache__ 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Keep essential files in root
echo "✅ Keeping essential files in root:"
echo "   - README.md"
echo "   - requirements.txt" 
echo "   - main.py"
echo "   - pytest.ini"
echo "   - voice_transcription_config.json"
echo "   - voice_transcriptions.db"
echo "   - debug_freeze.sh"
echo "   - monitor_voice_tool.sh"

# Create new simplified README.md
echo "📝 Creating simplified README..."
cat > README.md << 'EOF'
# Voice Transcription Tool

Speech-to-text application with global hotkeys, system tray, and auto-paste functionality.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   
   # Linux users also need:
   sudo apt install xdotool
   ```

2. **Run the application:**
   ```bash
   python main.py
   ```

## Usage

- **Alt+D**: Start/stop recording
- **Alt+S**: Open settings  
- **Alt+W**: Toggle wake word detection

The app starts with a system tray icon (blue microphone) that turns red with a countdown timer during recording.

## Command Line Options

```bash
python main.py --help           # Show all options
python main.py --minimized     # Start hidden in system tray
python main.py --debug         # Enable verbose logging
python main.py --no-tray       # Disable system tray
```

## Features

- 🎤 **Global Hotkeys**: Record from anywhere (no sudo required)
- 🖥️ **System Tray**: Visual recording timer and status
- 📋 **Auto-paste**: Automatically paste transcribed text
- 🔊 **Audio Feedback**: Sound notifications for start/stop
- 🧠 **Multiple Engines**: Whisper (local) or Google Speech (cloud)
- 🎯 **Wake Word**: Hands-free "Hey Computer" activation
- 🎨 **Modern GUI**: Tabbed interface with advanced options

## Troubleshooting

- **System freezes**: Run `./debug_freeze.sh` from TTY (Ctrl+Alt+F3)
- **Monitor health**: Run `./monitor_voice_tool.sh`
- **Multiple instances**: Only one can run at a time (prevents conflicts)

## Documentation

See `docs/` folder for:
- Development setup
- Linux hotkey configuration  
- Troubleshooting guides
- Architecture documentation

## Scripts

See `scripts/` folder for:
- Installation helpers
- Auto-start configuration
- Background service setup
EOF

# Update .gitignore
echo "🚫 Updating .gitignore..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Application specific
*.log
logs/
htmlcov/
.coverage
.pytest_cache/
voice_transcriptions.db
voice_transcription_config.json
.voice_transcription.pid
/tmp/voice_transcription.lock

# Build artifacts  
*.deb
dist/
build/
EOF

echo ""
echo "✅ Cleanup and reorganization complete!"
echo ""
echo "📁 New structure:"
echo "   ├── README.md                 # Simple getting started guide"
echo "   ├── requirements.txt          # All dependencies"
echo "   ├── main.py                   # Single entry point"
echo "   ├── voice_transcription_tool/ # Core application code"
echo "   ├── tests/                    # Unit tests"
echo "   ├── docs/                     # All documentation"
echo "   ├── scripts/                  # Helper scripts"
echo "   └── dist/                     # Build artifacts (git-ignored)"
echo ""
echo "🚀 You can now run: python main.py"
echo "📖 See README.md for usage instructions"