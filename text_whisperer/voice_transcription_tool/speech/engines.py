"""
speech/engines.py - Speech recognition engines for the Voice Transcription Tool.

Provides abstract base class and concrete implementations for Whisper (local)
and Google Speech (cloud) recognition engines with automatic fallback.
"""

import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False


class SpeechEngine(ABC):
    """Abstract base class for speech recognition engines."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @abstractmethod
    def transcribe(self, audio_file: str) -> Dict[str, Any]:
        """Transcribe audio file and return result."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the engine is available."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Engine name."""
        pass


class WhisperEngine(SpeechEngine):
    """OpenAI Whisper speech recognition engine."""
    
    def __init__(self, model_size: str = "tiny"):
        super().__init__()
        self.model_size = model_size
        self.model = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the Whisper model."""
        if not WHISPER_AVAILABLE:
            self.logger.error("Whisper not available")
            return
        
        try:
            self.logger.info(f"Loading Whisper model: {self.model_size}")
            self.model = whisper.load_model(self.model_size)
            self.logger.info("✅ Whisper model loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load Whisper model: {e}")
    
    def transcribe(self, audio_file: str) -> Dict[str, Any]:
        """Transcribe audio using Whisper with optimizations for short clips."""
        if not self.model:
            return {
                'text': '',
                'confidence': 0.0,
                'method': 'whisper',
                'error': 'Whisper model not loaded',
                'success': False
            }

        try:
            self.logger.info(f"Transcribing with Whisper {self.model_size} model...")

            # Optimize for short clips - use faster settings
            result = self.model.transcribe(
                audio_file,
                fp16=False,  # Use FP32 for better CPU performance
                condition_on_previous_text=False,  # Don't condition on previous text for short clips
                temperature=0.0,  # Use deterministic decoding for consistency
                best_of=1,  # Use single beam for speed
                beam_size=1,  # Single beam search for speed
                no_speech_threshold=0.6,  # Higher threshold to avoid false positives
                logprob_threshold=-1.0,  # Standard threshold
                compression_ratio_threshold=2.4,  # Standard threshold
                word_timestamps=False  # Don't generate word timestamps for speed
            )

            text = result.get('text', '').strip()
            if not text:
                return {
                    'text': '',
                    'confidence': 0.0,
                    'method': 'whisper',
                    'error': 'No speech detected in audio. The recording may be too noisy or unclear.',
                    'success': False
                }

            return {
                'text': text,
                'confidence': 0.95,  # Whisper doesn't provide confidence scores
                'method': 'whisper',
                'language': result.get('language', 'unknown'),
                'success': True
            }

        except Exception as e:
            self.logger.error(f"Whisper transcription failed: {e}")
            error_msg = 'Transcription failed. The audio may be too noisy, unclear, or in an unsupported format.'
            return {
                'text': '',
                'confidence': 0.0,
                'method': 'whisper',
                'error': error_msg,
                'error_detail': str(e),
                'success': False
            }
    
    def is_available(self) -> bool:
        """Check if Whisper is available."""
        return WHISPER_AVAILABLE and self.model is not None
    
    @property
    def name(self) -> str:
        """Engine name."""
        return "whisper"


class GoogleSpeechEngine(SpeechEngine):
    """Google Speech Recognition engine."""
    
    def __init__(self):
        super().__init__()
        self.recognizer = None
        self._init_recognizer()
    
    def _init_recognizer(self) -> None:
        """Initialize the speech recognizer."""
        if not SPEECH_RECOGNITION_AVAILABLE:
            self.logger.error("SpeechRecognition library not available")
            return
        
        try:
            self.recognizer = sr.Recognizer()
            self.logger.info("✅ Google Speech Recognition initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Google Speech Recognition: {e}")
    
    def transcribe(self, audio_file: str) -> Dict[str, Any]:
        """Transcribe audio using Google Speech Recognition."""
        if not self.recognizer:
            return {
                'text': '',
                'confidence': 0.0,
                'method': 'google',
                'error': 'Google Speech Recognition not initialized',
                'success': False
            }

        try:
            self.logger.info("Transcribing with Google Speech Recognition...")

            with sr.AudioFile(audio_file) as source:
                audio_data = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio_data)

            return {
                'text': text,
                'confidence': 0.9,  # Google API doesn't provide confidence in free tier
                'method': 'google',
                'success': True
            }

        except sr.UnknownValueError:
            return {
                'text': '',
                'confidence': 0.0,
                'method': 'google',
                'error': 'Could not understand audio. Please speak more clearly.',
                'success': False
            }
        except sr.RequestError as e:
            self.logger.error(f"Google Speech Recognition request failed: {e}")
            # Check for network-related errors
            error_msg = 'Google Speech API request failed.'
            if 'connection' in str(e).lower() or 'network' in str(e).lower():
                error_msg = 'Cannot reach Google Speech API. Please check your internet connection.'
            return {
                'text': '',
                'confidence': 0.0,
                'method': 'google',
                'error': error_msg,
                'error_detail': str(e),
                'success': False
            }
        except Exception as e:
            self.logger.error(f"Google Speech Recognition failed: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'method': 'google',
                'error': f'Recognition error: {str(e)}',
                'success': False
            }
    
    def is_available(self) -> bool:
        """Check if Google Speech Recognition is available."""
        return SPEECH_RECOGNITION_AVAILABLE and self.recognizer is not None
    
    @property
    def name(self) -> str:
        """Engine name."""
        return "google"


class SpeechEngineManager:
    """Manages multiple speech recognition engines with automatic fallback."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.engines = {}
        self.current_engine = None
        self._init_engines()
    
    def _init_engines(self) -> None:
        """Initialize all available speech recognition engines."""
        # Initialize Whisper
        whisper_engine = WhisperEngine()
        if whisper_engine.is_available():
            self.engines['whisper'] = whisper_engine
            self.logger.info("Whisper engine registered")
        
        # Initialize Google Speech Recognition
        google_engine = GoogleSpeechEngine()
        if google_engine.is_available():
            self.engines['google'] = google_engine
            self.logger.info("Google Speech engine registered")
        
        self.logger.info(f"Available engines: {list(self.engines.keys())}")
        
        # Set default engine (prefer Whisper, fallback to Google)
        if 'whisper' in self.engines:
            self.current_engine = 'whisper'
        elif 'google' in self.engines:
            self.current_engine = 'google'
        else:
            self.logger.warning("No speech engines available!")
    
    def get_available_engines(self) -> list[str]:
        """Get list of available engine names."""
        return list(self.engines.keys())
    
    def set_engine(self, engine_name: str) -> bool:
        """Set the current speech engine."""
        if engine_name in self.engines:
            self.current_engine = engine_name
            self.logger.info(f"Speech engine set to: {engine_name}")
            return True
        else:
            self.logger.error(f"Engine '{engine_name}' not available")
            return False
    
    def get_current_engine(self) -> Optional[str]:
        """Get the current engine name."""
        return self.current_engine
    
    def transcribe(self, audio_file: str, enable_fallback: bool = True) -> Dict[str, Any]:
        """
        Transcribe audio using the current engine with automatic fallback.

        Args:
            audio_file: Path to audio file
            enable_fallback: If True, try alternative engine on failure

        Returns:
            Dict with transcription result or error
        """
        if not self.current_engine or self.current_engine not in self.engines:
            return {
                'text': '',
                'confidence': 0.0,
                'method': 'no_engine',
                'error': 'No speech engine available',
                'success': False
            }

        # Try primary engine
        engine = self.engines[self.current_engine]
        result = engine.transcribe(audio_file)

        # If primary engine failed and fallback is enabled, try alternative engine
        if not result.get('success', False) and enable_fallback:
            alternative_engine = self._get_alternative_engine()

            if alternative_engine:
                self.logger.info(f"Primary engine ({self.current_engine}) failed, trying {alternative_engine}...")
                result['fallback_attempted'] = True
                result['primary_engine'] = self.current_engine

                # Try alternative engine
                alt_engine = self.engines[alternative_engine]
                alt_result = alt_engine.transcribe(audio_file)

                # If alternative succeeded, use its result
                if alt_result.get('success', False):
                    self.logger.info(f"Fallback to {alternative_engine} succeeded")
                    alt_result['fallback_from'] = self.current_engine
                    alt_result['fallback_success'] = True
                    return alt_result
                else:
                    # Both engines failed
                    self.logger.error(f"Both engines failed: {self.current_engine} and {alternative_engine}")
                    result['fallback_failed'] = True
                    result['fallback_engine'] = alternative_engine
                    result['fallback_error'] = alt_result.get('error', 'Unknown error')

        return result

    def _get_alternative_engine(self) -> Optional[str]:
        """Get an alternative engine for fallback."""
        # Prefer Whisper over Google for fallback (more accurate)
        if self.current_engine == 'google' and 'whisper' in self.engines:
            return 'whisper'
        elif self.current_engine == 'whisper' and 'google' in self.engines:
            return 'google'
        return None
    
    def transcribe_for_training(self, audio_file: str) -> Dict[str, Any]:
        """
        Transcribe audio optimized for training - uses Google Speech for speed.
        
        For voice training, we prioritize speed over accuracy, so use Google Speech
        which is much faster for short clips than Whisper.
        """
        # For training, prefer Google Speech (faster) over Whisper (slower)
        if 'google' in self.engines and self.engines['google'].is_available():
            self.logger.info("Using Google Speech for training transcription (faster)")
            return self.engines['google'].transcribe(audio_file)
        elif 'whisper' in self.engines and self.engines['whisper'].is_available():
            self.logger.info("Using Whisper for training transcription (slower but still works)")
            return self.engines['whisper'].transcribe(audio_file)
        else:
            return {
                'text': '[No speech engine available for training]',
                'confidence': 0.0,
                'method': 'no_engine'
            }
    
    def is_engine_available(self, engine_name: str) -> bool:
        """Check if a specific engine is available."""
        return engine_name in self.engines and self.engines[engine_name].is_available()
    
    def get_engine_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all engines."""
        info = {}
        for name, engine in self.engines.items():
            info[name] = {
                'name': engine.name,
                'available': engine.is_available(),
                'current': name == self.current_engine
            }
        return info


if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from utils.logger import setup_logging
    
    setup_logging()
    
    # Test speech engine manager
    speech_manager = SpeechEngineManager()
    
    available_engines = speech_manager.get_available_engines()
    print(f"Available engines: {available_engines}")
    
    current_engine = speech_manager.get_current_engine()
    print(f"Current engine: {current_engine}")
    
    engine_info = speech_manager.get_engine_info()
    print("Engine info:")
    for name, info in engine_info.items():
        status = "✅" if info['available'] else "❌"
        current = " (current)" if info['current'] else ""
        print(f"  {status} {name}{current}")
    
    print("✅ Speech engines module test completed!")
