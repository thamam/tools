"""
Audio module for the Voice Transcription Tool.

This module handles all audio recording and device management functionality.
"""

from .recorder import AudioRecorder
from .devices import AudioDeviceManager

__all__ = ['AudioRecorder', 'AudioDeviceManager']
