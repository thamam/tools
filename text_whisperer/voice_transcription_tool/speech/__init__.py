"""
Speech module for the Voice Transcription Tool.

This module handles all speech recognition and voice training functionality.
"""

from .engines import SpeechEngineManager, WhisperEngine, GoogleSpeechEngine
from .training import VoiceTrainer

__all__ = ['SpeechEngineManager', 'WhisperEngine', 'GoogleSpeechEngine', 'VoiceTrainer']
