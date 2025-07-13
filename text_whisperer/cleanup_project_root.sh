#!/bin/bash
# Cleanup script for the ACTUAL project root (/text_whisperer/)
# This will properly organize the entire project structure

set -e  # Exit on any error

echo "=== Voice Transcription Tool - Root Level Cleanup ==="
echo "Current directory: $(pwd)"
echo "This will reorganize the ENTIRE project structure"
echo ""

# Confirm we're in the right place
if [[ ! -d "voice_transcription_tool" ]]; then
    echo "❌ Error: voice_transcription_tool directory not found!"
    echo "Please run this script from the text_whisperer root directory"
    exit 1
fi

# Confirm before proceeding
read -p "Are you sure you want to proceed with root-level cleanup? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

echo "Starting root-level cleanup..."

# Remove redundant files that are duplicated
echo "🗑️ Removing duplicate/redundant files..."
rm -f cleanup_and_reorganize.sh 2>/dev/null || true
rm -f voice_transcription_config.json 2>/dev/null || true  # Keep the one in voice_transcription_tool/
rm -f voice_transcriptions.db 2>/dev/null || true          # Keep the one in voice_transcription_tool/

# Remove old directories that are no longer needed
echo "🗑️ Removing obsolete directories..."
rm -rf TO_BE_DELETED 2>/dev/null || true
rm -rf install 2>/dev/null || true

# Remove migration artifacts
echo "🗑️ Removing migration artifacts..."
rm -f migration_script.py 2>/dev/null || true

# Move the dist and scripts from voice_transcription_tool/ to root level
echo "📦 Moving build artifacts to root level..."
if [[ -d "voice_transcription_tool/dist" ]]; then
    if [[ -d "dist" ]]; then
        # Merge the contents
        cp -r voice_transcription_tool/dist/* dist/ 2>/dev/null || true
        rm -rf voice_transcription_tool/dist
    else
        mv voice_transcription_tool/dist ./
    fi
fi

echo "🔧 Moving scripts to root level..."
if [[ -d "voice_transcription_tool/scripts" ]]; then
    if [[ -d "scripts" ]]; then
        # Merge the contents
        cp -r voice_transcription_tool/scripts/* scripts/ 2>/dev/null || true
        rm -rf voice_transcription_tool/scripts
    else
        mv voice_transcription_tool/scripts ./
    fi
fi

echo "📄 Moving docs to root level..."
if [[ -d "voice_transcription_tool/docs" ]]; then
    if [[ -d "docs" ]]; then
        # Merge the contents
        cp -r voice_transcription_tool/docs/* docs/ 2>/dev/null || true
        rm -rf voice_transcription_tool/docs
    else
        mv voice_transcription_tool/docs ./
    fi
fi

# Clean up the inner duplicated README
echo "📝 Cleaning up duplicate README..."
if [[ -f "voice_transcription_tool/README.md" ]]; then
    rm -f voice_transcription_tool/README.md
fi

# Create the final project structure
echo "📁 Final project structure:"
echo ""
echo "text_whisperer/"
echo "├── README.md                     # Main project documentation"
echo "├── requirements.txt              # → voice_transcription_tool/requirements.txt"  
echo "├── main.py                       # → voice_transcription_tool/main.py"
echo "├── voice_transcription_tool/     # Core application package"
echo "│   ├── main.py                   # Entry point"
echo "│   ├── requirements.txt          # Dependencies"
echo "│   ├── audio/                    # Audio recording"
echo "│   ├── config/                   # Configuration & DB"
echo "│   ├── gui/                      # User interface"
echo "│   ├── speech/                   # Speech recognition"
echo "│   ├── utils/                    # Utilities & hotkeys"
echo "│   └── tests/                    # Unit tests"
echo "├── docs/                         # All documentation"
echo "├── scripts/                      # Helper scripts"
echo "└── dist/                         # Build artifacts"

# Create convenience files at root level
echo "🔗 Creating convenience files at root level..."

# Create root-level requirements.txt that points to the real one
cat > requirements.txt << 'EOF'
# Install dependencies using:
# pip install -r voice_transcription_tool/requirements.txt

# Or run this file directly:
-r voice_transcription_tool/requirements.txt
EOF

# Create root-level main.py that delegates to the real one
cat > main.py << 'EOF'
#!/usr/bin/env python3
"""
Voice Transcription Tool - Root Entry Point
Delegates to the actual main.py in voice_transcription_tool/
"""

import sys
import os
from pathlib import Path

# Add voice_transcription_tool to path and run its main
sys.path.insert(0, str(Path(__file__).parent / "voice_transcription_tool"))

if __name__ == "__main__":
    from voice_transcription_tool.main import main
    sys.exit(main())
EOF

chmod +x main.py

# Update root README.md
cat > README.md << 'EOF'
# Voice Transcription Tool

Professional speech-to-text application with global hotkeys, system tray, and auto-paste functionality.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Linux users also need:
sudo apt install xdotool

# Run the application
python main.py
```

## Usage

- **Alt+D**: Start/stop recording
- **Alt+S**: Open settings  
- **Alt+W**: Toggle wake word detection

## Features

🎤 **Global Hotkeys** - Record from anywhere (no sudo required)  
🖥️ **System Tray** - Visual recording timer and status  
📋 **Auto-paste** - Automatically paste transcribed text  
🔊 **Audio Feedback** - Sound notifications  
🧠 **Multiple Engines** - Whisper (local) or Google Speech (cloud)  
🎯 **Wake Word** - Hands-free "Hey Computer" activation  
🎨 **Modern GUI** - Tabbed interface with advanced options  

## Command Line Options

```bash
python main.py --help           # Show all options
python main.py --minimized     # Start hidden in system tray
python main.py --debug         # Enable verbose logging
python main.py --no-tray       # Disable system tray
```

## Project Structure

- `voice_transcription_tool/` - Core application code
- `docs/` - Documentation and guides
- `scripts/` - Helper and setup scripts  
- `dist/` - Build artifacts and packages

## Troubleshooting

- **System freezes**: Run `voice_transcription_tool/debug_freeze.sh` from TTY
- **Monitor health**: Run `voice_transcription_tool/monitor_voice_tool.sh`
- See `docs/` for detailed guides

## Development

```bash
cd voice_transcription_tool/
python -m pytest tests/    # Run tests
python main.py --debug     # Debug mode
```
EOF

# Create final .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.env
.venv
env/
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

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
dist/
*.deb
EOF

echo ""
echo "✅ Root-level cleanup complete!"
echo ""
echo "🚀 You can now run from project root:"
echo "   python main.py"
echo ""
echo "📖 Or work directly in the package:"
echo "   cd voice_transcription_tool/"
echo "   python main.py"
echo ""
echo "📁 Project is now properly organized!"