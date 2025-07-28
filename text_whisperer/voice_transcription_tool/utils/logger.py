"""
utils/logger.py - Logging utilities for the Voice Transcription Tool.

MIGRATION STEP 2: Create this file first (no dependencies)
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(level=logging.INFO):
    """Setup comprehensive logging system."""
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Setup file logging
    log_filename = logs_dir / f"voice_transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=level,
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

    MAX_MESSAGES = 100

    def __init__(self, max_messages: int | None = None):
        self.messages: list[str] = []
        self.callbacks: list = []
        if isinstance(max_messages, int) and max_messages > 0:
            self.MAX_MESSAGES = max_messages
    
    def add_message(self, message):
        """Add a debug message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        debug_msg = f"[{timestamp}] {message}"
        self.messages.append(debug_msg)
        if len(self.messages) > self.MAX_MESSAGES:
            excess = len(self.messages) - self.MAX_MESSAGES
            del self.messages[:excess]
        
        # Notify callbacks
        for callback in self.callbacks:
            try:
                callback(debug_msg)
            except Exception as e:
                # Log exception but don't stop other callbacks
                import logging
                logging.getLogger(__name__).warning(f"Callback exception: {e}")
    
    def add_callback(self, callback):
        """Add a callback for new messages."""
        self.callbacks.append(callback)
    
    def clear_messages(self):
        """Clear all messages."""
        self.messages.clear()
    
    def get_messages(self):
        """Get all messages."""
        return self.messages.copy()
