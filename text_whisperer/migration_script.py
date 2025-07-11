#!/usr/bin/env python3
"""
migrate_to_modular.py - Automated migration script for Voice Transcription Tool

This script helps migrate from the monolithic voice_transcription.py to a modular structure.
"""

import os
import shutil
from pathlib import Path
import re


def create_directory_structure():
    """Create the new modular directory structure."""
    print("📁 Creating directory structure...")
    
    # Define the structure
    dirs = [
        "voice_transcription_tool",
        "voice_transcription_tool/config", 
        "voice_transcription_tool/audio",
        "voice_transcription_tool/speech",
        "voice_transcription_tool/gui",
        "voice_transcription_tool/utils"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(exist_ok=True)
        print(f"  ✅ Created {dir_path}")
    
    # Create __init__.py files
    init_files = [
        "voice_transcription_tool/__init__.py",
        "voice_transcription_tool/config/__init__.py",
        "voice_transcription_tool/audio/__init__.py", 
        "voice_transcription_tool/speech/__init__.py",
        "voice_transcription_tool/gui/__init__.py",
        "voice_transcription_tool/utils/__init__.py"
    ]
    
    for init_file in init_files:
        Path(init_file).touch()
        print(f"  ✅ Created {init_file}")


def backup_original():
    """Backup the original monolithic file."""
    original_file = "voice_transcription.py"
    
    if Path(original_file).exists():
        backup_file = f"{original_file}.backup"
        shutil.copy2(original_file, backup_file)
        print(f"📦 Backed up original file to {backup_file}")
        return True
    else:
        print(f"⚠️  Original file {original_file} not found")
        return False


def create_requirements_txt():
    """Create requirements.txt file."""
    requirements = """# Core dependencies
keyboard>=0.13.5
pyperclip>=1.9.0

# Audio recording
pyaudio>=0.2.14

# Speech recognition engines (choose one or both)
openai-whisper>=20231117
SpeechRecognition>=3.10.0

# Additional dependencies
torch>=1.9.0
numpy>=1.21.0
requests>=2.25.0
"""
    
    with open("voice_transcription_tool/requirements.txt", "w") as f:
        f.write(requirements)
    
    print("✅ Created requirements.txt")


def create_main_entry_point():
    """Create the main entry point."""
    main_py_content = '''#!/usr/bin/env python3
"""
Voice Transcription Tool - Main Entry Point
A powerful speech-to-text application with global hotkeys and voice training.
"""

import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.logger import setup_logging
from gui.main_window import VoiceTranscriptionApp


def main():
    """Main entry point for the Voice Transcription Tool."""
    try:
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("=== Voice Transcription Tool Starting ===")
        
        # Check dependencies
        missing_deps = check_dependencies()
        if missing_deps:
            print("Missing required dependencies:")
            for dep, message in missing_deps.items():
                print(f"  • {dep}: {message}")
            print("\\nPlease run: pip install -r requirements.txt")
            return 1
        
        # Start the application
        app = VoiceTranscriptionApp()
        app.run()
        
        return 0
        
    except KeyboardInterrupt:
        print("\\n\\nApplication interrupted by user")
        return 1
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1


def check_dependencies():
    """Check for required dependencies."""
    missing = {}
    
    try:
        import tkinter
    except ImportError:
        missing['tkinter'] = 'GUI library (usually included with Python)'
    
    try:
        import keyboard
    except ImportError:
        missing['keyboard'] = 'pip install keyboard'
        
    try:
        import pyperclip
    except ImportError:
        missing['pyperclip'] = 'pip install pyperclip'
    
    # Check for at least one speech engine
    has_speech_engine = False
    try:
        import whisper
        has_speech_engine = True
    except ImportError:
        pass
        
    try:
        import speech_recognition
        has_speech_engine = True
    except ImportError:
        pass
        
    if not has_speech_engine:
        missing['speech_engine'] = 'pip install openai-whisper OR pip install SpeechRecognition'
    
    return missing


if __name__ == "__main__":
    sys.exit(main())
'''
    
    with open("voice_transcription_tool/main.py", "w") as f:
        f.write(main_py_content)
    
    print("✅ Created main.py entry point")


def create_setup_script():
    """Create setup.py for installation."""
    setup_py_content = '''from setuptools import setup, find_packages

setup(
    name="voice-transcription-tool",
    version="2.0.0",
    description="A powerful speech-to-text application with global hotkeys and voice training",
    packages=find_packages(),
    install_requires=[
        "keyboard>=0.13.5",
        "pyperclip>=1.9.0",
        "pyaudio>=0.2.14",
        "openai-whisper>=20231117",
        "SpeechRecognition>=3.10.0",
        "torch>=1.9.0",
        "numpy>=1.21.0",
        "requests>=2.25.0"
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "voice-transcription=voice_transcription_tool.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
'''
    
    with open("setup.py", "w") as f:
        f.write(setup_py_content)
    
    print("✅ Created setup.py for installation")


def create_readme():
    """Create README.md for the new structure."""
    readme_content = '''# Voice Transcription Tool v2.0

A powerful speech-to-text application with global hotkeys, voice training, and modular architecture.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r voice_transcription_tool/requirements.txt

# Run the application
python voice_transcription_tool/main.py

# Or install as package
pip install -e .
voice-transcription
```

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
'''
    
    with open("README.md", "w") as f:
        f.write(readme_content)
    
    print("✅ Created README.md")


def create_migration_checklist():
    """Create a checklist for manual migration steps."""
    checklist = '''# Migration Checklist

## ✅ Automated Steps (Completed)
- [x] Created directory structure
- [x] Created main.py entry point  
- [x] Created requirements.txt
- [x] Created setup.py
- [x] Created README.md
- [x] Backed up original file

## 📋 Manual Steps (TODO)

### 1. Move Code Sections
- [ ] Move database operations to `config/database.py`
- [ ] Move audio recording to `audio/recorder.py` 
- [ ] Move device management to `audio/devices.py`
- [ ] Move speech engines to `speech/engines.py`
- [ ] Move voice training to `speech/training.py`
- [ ] Move GUI components to `gui/main_window.py`
- [ ] Move settings dialog to `gui/settings_dialog.py`
- [ ] Move training dialog to `gui/training_dialog.py`
- [ ] Move configuration to `config/settings.py`
- [ ] Move hotkey handling to `utils/hotkeys.py`
- [ ] Move logging utilities to `utils/logger.py`

### 2. Fix Imports
- [ ] Add imports between modules
- [ ] Update relative imports
- [ ] Test each module independently

### 3. Testing
- [ ] Test audio recording: `python -c "from audio.recorder import AudioRecorder; r=AudioRecorder(); print(r.test_recording())"`
- [ ] Test speech engines: `python -c "from speech.engines import SpeechEngineManager; print('OK')"`
- [ ] Test full application: `python voice_transcription_tool/main.py`

### 4. Final Steps
- [ ] Update documentation
- [ ] Test installation: `pip install -e .`
- [ ] Verify all features work
- [ ] Remove old monolithic file (optional)

## 🎯 Benefits After Migration

- ✅ **Easier debugging** - isolate issues to specific modules
- ✅ **Better testing** - test components independently
- ✅ **Cleaner code** - single responsibility per module
- ✅ **Easier features** - add new engines/UI components
- ✅ **Better reusability** - use modules in other projects
- ✅ **Team development** - multiple developers can work together
- ✅ **Professional structure** - industry-standard organization

## 🚀 Next Steps

1. Copy code sections from `voice_transcription.py.backup` to appropriate modules
2. Add proper imports and test each module
3. Run the new modular version
4. Enjoy the improved maintainability!
'''
    
    with open("MIGRATION_CHECKLIST.md", "w") as f:
        f.write(checklist)
    
    print("✅ Created MIGRATION_CHECKLIST.md")


def main():
    """Run the automated migration steps."""
    print("🎯 Voice Transcription Tool - Automated Migration")
    print("=" * 50)
    
    # Check if original file exists
    if not Path("voice_transcription.py").exists():
        print("❌ voice_transcription.py not found in current directory")
        print("Please run this script in the same directory as your voice_transcription.py file")
        return
    
    # Run migration steps
    try:
        create_directory_structure()
        backup_original()
        create_requirements_txt()
        create_main_entry_point()
        create_setup_script()
        create_readme()
        create_migration_checklist()
        
        print("\n🎉 Automated migration completed successfully!")
        print("\n📋 Next steps:")
        print("1. Review MIGRATION_CHECKLIST.md for manual steps")
        print("2. Copy code sections from voice_transcription.py.backup to appropriate modules")
        print("3. Test the new modular structure")
        print("4. Run: python voice_transcription_tool/main.py")
        
        print("\n💡 Benefits of the new structure:")
        print("  ✅ Easier to maintain and debug")
        print("  ✅ Better code organization")
        print("  ✅ Easier to add new features")
        print("  ✅ Better testing capabilities")
        print("  ✅ Professional, scalable architecture")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("Please check the error and try again")


if __name__ == "__main__":
    main()
