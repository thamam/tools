#!/usr/bin/env python3
"""
Voice Transcription Tool - Main Entry Point
A powerful speech-to-text application with global hotkeys and voice training.

MIGRATION STEP 6C: The final piece! This replaces your original voice_transcription.py

This is now a clean, modular entry point that uses all our separated modules.
"""

import sys
import logging
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.logger import setup_logging
from gui.main_window import VoiceTranscriptionApp


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Voice Transcription Tool - Speech-to-text with global hotkeys"
    )
    parser.add_argument(
        "--minimized", 
        action="store_true",
        help="Start minimized to system tray"
    )
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--no-tray", 
        action="store_true",
        help="Disable system tray"
    )
    return parser.parse_args()


def main():
    """Main entry point for the Voice Transcription Tool."""
    try:
        # Parse command line arguments
        args = parse_args()
        
        # Setup logging
        log_level = logging.DEBUG if args.debug else logging.INFO
        setup_logging(level=log_level)
        logger = logging.getLogger(__name__)
        logger.info("=== Voice Transcription Tool Starting ===")
        
        if args.debug:
            logger.info("Debug mode enabled")
        if args.minimized:
            logger.info("Starting minimized to system tray")
        if args.no_tray:
            logger.info("System tray disabled")
        
        # Check dependencies
        missing_deps = check_dependencies()
        if missing_deps:
            print("Missing required dependencies:")
            for dep, message in missing_deps.items():
                print(f"  • {dep}: {message}")
            print("\nPlease install missing dependencies:")
            print("  pip install keyboard pyperclip")
            print("  pip install openai-whisper  # OR")
            print("  pip install SpeechRecognition")
            return 1
        
        # Start the application
        logger.info("Starting modular voice transcription application")
        app = VoiceTranscriptionApp(
            start_minimized=args.minimized,
            enable_tray=not args.no_tray
        )
        app.run()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user")
        return 1
    except Exception as e:
        print(f"Fatal error: {e}")
        logging.exception("Fatal error occurred")
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


# MIGRATION COMPLETE! 🎉
# 
# This file replaces your original voice_transcription.py
# All functionality is now modular and organized:
#
# ✅ config/ - Configuration and database
# ✅ audio/ - Recording and device management  
# ✅ speech/ - Recognition engines and training
# ✅ gui/ - User interface components
# ✅ utils/ - Hotkeys and logging
# ✅ main.py - Clean entry point
#
# Benefits of the new structure:
# ✅ Easier to debug individual components
# ✅ Better testing capabilities
# ✅ Cleaner code organization
# ✅ Easier to add new features
# ✅ Better error handling
# ✅ Professional, maintainable architecture
