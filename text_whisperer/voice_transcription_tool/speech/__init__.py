"""
Speech module for the Voice Transcription Tool.

This module handles all speech recognition functionality.
"""

from .engines import SpeechEngineManager, WhisperEngine, GoogleSpeechEngine

__all__ = ['SpeechEngineManager', 'WhisperEngine', 'GoogleSpeechEngine']
