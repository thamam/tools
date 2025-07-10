"""
utils/logger.py - Logging utilities for the Voice Transcription Tool.

MIGRATION STEP 2: Create this file first (no dependencies)
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logging():
    """Setup comprehensive logging system."""
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Setup file logging
    log_filename = logs_dir / f"voice_transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific log levels for noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


class DebugMessageHandler:
    """Handler for debug messages in the GUI."""
    
    def __init__(self):
        self.messages = []
        self.callbacks = []
    
    def add_message(self, message):
        """Add a debug message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        debug_msg = f"[{timestamp}] {message}"
        self.messages.append(debug_msg)
        
        # Notify callbacks
        for callback in self.callbacks:
            callback(debug_msg)
    
    def add_callback(self, callback):
        """Add a callback for new messages."""
        self.callbacks.append(callback)
    
    def clear_messages(self):
        """Clear all messages."""
        self.messages.clear()
    
    def get_messages(self):
        """Get all messages."""
        return self.messages.copy()
