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
import os
import fcntl
import signal
import atexit
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.logger import setup_logging
from gui.main_window import VoiceTranscriptionApp

# Global references for cleanup
lock_file = None
app_instance = None


def acquire_process_lock():
    """Prevent multiple instances from running simultaneously."""
    global lock_file
    lock_path = "/tmp/voice_transcription.lock"
    
    try:
        lock_file = open(lock_path, 'w')
        fcntl.lockf(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_file.write(str(os.getpid()))
        lock_file.flush()
        return True
    except IOError:
        if lock_file:
            lock_file.close()
        return False


def emergency_cleanup():
    """Emergency cleanup function."""
    global app_instance, lock_file
    
    try:
        if app_instance:
            # Try to gracefully stop the app
            if hasattr(app_instance, '_emergency_shutdown'):
                app_instance._emergency_shutdown()
    except:
        pass
    
    try:
        if lock_file:
            lock_file.close()
        os.unlink("/tmp/voice_transcription.lock")
    except:
        pass


def signal_handler(signum, frame):
    """Handle signals for graceful shutdown."""
    print(f"\nReceived signal {signum}, shutting down...")
    emergency_cleanup()
    sys.exit(0)


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
    global app_instance
    
    try:
        # Parse command line arguments
        args = parse_args()
        
        # Setup logging
        log_level = logging.DEBUG if args.debug else logging.INFO
        setup_logging(level=log_level)
        logger = logging.getLogger(__name__)
        logger.info("=== Voice Transcription Tool Starting ===")
        
        # Acquire process lock to prevent multiple instances
        if not acquire_process_lock():
            print("ERROR: Another instance of Voice Transcription Tool is already running!")
            print("If you're sure no other instance is running, delete: /tmp/voice_transcription.lock")
            return 1
            
        logger.info(f"Process lock acquired (PID: {os.getpid()})")
        
        # Register cleanup handlers
        atexit.register(emergency_cleanup)
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
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
            print("  pip install -r requirements.txt")
            return 1
        
        # Start the application
        logger.info("Starting modular voice transcription application")
        app_instance = VoiceTranscriptionApp(
            start_minimized=args.minimized,
            enable_tray=not args.no_tray
        )
        app_instance.run()
        
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
        import pynput
    except ImportError:
        missing['pynput'] = 'pip install pynput'
        
    try:
        import pyperclip
    except ImportError:
        missing['pyperclip'] = 'pip install pyperclip'
    
    try:
        import pyaudio
    except ImportError:
        missing['pyaudio'] = 'pip install pyaudio'
    
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
