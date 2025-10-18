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
        help="Start minimized (hidden window)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
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
            logger.info("Starting minimized")
        
        # Check dependencies
        critical_missing, optional_missing, warnings_list = check_dependencies()

        # Show warnings (non-blocking)
        if warnings_list:
            print("\n⚠️  Warnings:")
            for warning in warnings_list:
                print(f"  • {warning}")
            logger.warning(f"Dependency warnings: {', '.join(warnings_list)}")

        # Show optional dependencies (non-blocking)
        if optional_missing:
            print("\n⚠️  Optional dependencies missing (reduced functionality):")
            for dep, info in optional_missing.items():
                print(f"\n  {dep}:")
                print(f"    Reason: {info['reason']}")
                print(f"    Install: {info['install']}")
                print(f"    Impact: {info['impact']}")
            logger.warning(f"Optional dependencies missing: {', '.join(optional_missing.keys())}")
            print("\n  The application will continue with reduced functionality.")
            print("  Press Enter to continue...")
            input()

        # Check critical dependencies (blocking)
        if critical_missing:
            print("\n❌ Missing required dependencies:\n")
            for dep, info in critical_missing.items():
                print(f"  {dep}:")
                print(f"    Reason: {info['reason']}")
                print(f"    Install: {info['install']}")
                print()

            print("Please install missing dependencies:")
            print("  Quick install: pip install -r requirements.txt")
            print("\nOr install individually:")
            for dep, info in critical_missing.items():
                print(f"  {info['install']}")

            return 1
        
        # Start the application
        logger.info("Starting modular voice transcription application")
        app_instance = VoiceTranscriptionApp(
            start_minimized=args.minimized
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
    """
    Check for required dependencies with clear installation instructions.

    Returns:
        Tuple of (critical_missing, optional_missing, warnings)
    """
    critical_missing = {}  # Must have to run
    optional_missing = {}  # Can run without, but with reduced functionality
    warnings = []  # Non-blocking warnings

    # Critical: Tkinter (GUI)
    try:
        import tkinter
    except ImportError:
        critical_missing['tkinter'] = {
            'reason': 'GUI library required',
            'install': 'Usually included with Python. Try: sudo apt install python3-tk'
        }

    # Critical: pynput (hotkeys)
    try:
        import pynput
    except ImportError:
        critical_missing['pynput'] = {
            'reason': 'Required for global hotkeys',
            'install': 'pip install pynput'
        }

    # Critical: pyperclip (clipboard)
    try:
        import pyperclip
    except ImportError:
        critical_missing['pyperclip'] = {
            'reason': 'Required for clipboard operations',
            'install': 'pip install pyperclip'
        }

    # Critical: pyaudio (recording)
    try:
        import pyaudio
    except ImportError:
        critical_missing['pyaudio'] = {
            'reason': 'Required for audio recording',
            'install': 'pip install pyaudio'
        }

    # Critical: At least one speech engine
    has_whisper = False
    has_google = False

    try:
        import whisper
        has_whisper = True
    except ImportError:
        pass

    try:
        import speech_recognition
        has_google = True
    except ImportError:
        pass

    if not has_whisper and not has_google:
        critical_missing['speech_engine'] = {
            'reason': 'At least one speech recognition engine required',
            'install': 'pip install openai-whisper  OR  pip install SpeechRecognition'
        }
    elif not has_whisper:
        warnings.append("Whisper not available - using Google Speech only (requires internet)")
    elif not has_google:
        warnings.append("Google Speech not available - using Whisper only (slower)")

    # Optional: FFmpeg (for Whisper)
    if has_whisper:
        try:
            import subprocess
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            optional_missing['ffmpeg'] = {
                'reason': 'Required for Whisper speech engine',
                'install': 'sudo apt install ffmpeg',
                'impact': 'Whisper will not work without FFmpeg'
            }

    # Optional: xdotool (for auto-paste on Linux)
    if sys.platform == 'linux':
        try:
            import subprocess
            subprocess.run(['which', 'xdotool'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            optional_missing['xdotool'] = {
                'reason': 'Required for auto-paste functionality',
                'install': 'sudo apt install xdotool',
                'impact': 'Auto-paste will be disabled (text still copied to clipboard)'
            }

    return critical_missing, optional_missing, warnings


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
