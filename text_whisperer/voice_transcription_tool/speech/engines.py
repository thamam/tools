"""
speech/engines.py - Speech recognition engines for the Voice Transcription Tool.

Provides abstract base class and concrete implementations for Whisper (local)
and Google Speech (cloud) recognition engines with automatic fallback.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from abc import ABC, abstractmethod

from utils.error_messages import format_engine_error

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

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False


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
    
    def __init__(self, model_size: str = "tiny", config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.model_size = model_size
        self.model = None
        self.config = config or {}
        
        # GPU detection
        self.has_gpu, self.device_name = self._detect_gpu()
        self.force_cpu = self.config.get('force_cpu', False)
        
        # Check cuDNN availability before attempting GPU usage
        if self.has_gpu and not self.force_cpu:
            if not self._check_cudnn_available():
                self.logger.warning("cuDNN libraries not found - forcing CPU mode for Whisper")
                self.logger.warning("Install libcudnn9 for GPU support: sudo apt install libcudnn9-cuda-12")
                self.force_cpu = True
        
        self.use_gpu = self.has_gpu and not self.force_cpu
        
        # Log GPU status
        if self.use_gpu:
            self.logger.info(f"🚀 GPU detected: {self.device_name} - Acceleration enabled")
        elif self.has_gpu and self.force_cpu:
            self.logger.info(f"GPU detected: {self.device_name} - Disabled by force_cpu config")
        else:
            self.logger.info("Running on CPU (GPU not available)")
        
        self._load_model()
    
    def _detect_gpu(self) -> tuple:
        """Detect GPU availability and return (has_gpu, device_name)."""
        try:
            import torch
            if torch.cuda.is_available():
                device_name = torch.cuda.get_device_name(0)
                memory_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
                return (True, f"{device_name} ({memory_gb:.1f}GB)")
        except Exception as e:
            self.logger.debug(f"GPU detection failed: {e}")
        return (False, "CPU")
    
    def _check_cudnn_available(self) -> bool:
        """Check if cuDNN libraries are available."""
        try:
            import ctypes
            import ctypes.util
            
            # Try to find cuDNN library
            cudnn_libs = [
                'libcudnn.so.9',
                'libcudnn.so.8', 
                'libcudnn.so'
            ]
            
            for lib_name in cudnn_libs:
                lib_path = ctypes.util.find_library(lib_name.replace('.so', '').replace('lib', ''))
                if lib_path:
                    try:
                        ctypes.CDLL(lib_path)
                        self.logger.debug(f"Found cuDNN library: {lib_path}")
                        return True
                    except OSError:
                        continue
            
            self.logger.debug("cuDNN library not found in system")
            return False
        except Exception as e:
            self.logger.debug(f"cuDNN check failed: {e}")
            return False
    
    def _load_model(self) -> None:
        """Load the Whisper model."""
        if not WHISPER_AVAILABLE:
            self.logger.error("Whisper not available")
            return
        
        try:
            device = "cuda" if self.use_gpu else "cpu"
            self.logger.info(f"Loading Whisper model: {self.model_size} on {device}")
            self.model = whisper.load_model(self.model_size, device=device)
            self.logger.info("✅ Whisper model loaded successfully")
        except Exception as e:
            error_str = str(e).lower()
            # Check for cuDNN/CUDA-related errors
            if self.use_gpu and ('cudnn' in error_str or 'cuda' in error_str or 'libcudnn' in error_str):
                self.logger.warning(f"CUDA/cuDNN library issue: {e}")
                self.logger.warning("Falling back to CPU mode (install libcudnn9 for GPU support)")
            else:
                self.logger.error(f"Failed to load Whisper model: {e}")
            
            # Try fallback to CPU if GPU load failed
            if self.use_gpu:
                self.logger.warning("Attempting to load on CPU as fallback...")
                try:
                    self.model = whisper.load_model(self.model_size, device="cpu")
                    self.use_gpu = False
                    self.logger.info("✅ Whisper model loaded on CPU (fallback)")
                except Exception as e2:
                    self.logger.error(f"CPU fallback also failed: {e2}")
    
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
            device_info = "GPU" if self.use_gpu else "CPU"
            self.logger.info(f"Transcribing with Whisper {self.model_size} model on {device_info}...")

            # Use quality settings for accurate transcription
            result = self.model.transcribe(
                audio_file,
                fp16=self.use_gpu,  # Use FP16 on GPU for speed, FP32 on CPU for compatibility
                language='en',  # Force English for better accuracy
                task='transcribe',  # Transcription task
                condition_on_previous_text=False,  # Don't condition on previous text for short clips
                temperature=0.0,  # Deterministic decoding
                best_of=5,  # Sample 5 candidates for better quality
                beam_size=5,  # Use 5 beams for better accuracy
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
            error_str = str(e).lower()
            # Check for runtime CUDA/cuDNN errors and retry on CPU
            if self.use_gpu and ('cudnn' in error_str or 'cuda' in error_str or 'out of memory' in error_str):
                self.logger.warning(f"GPU runtime error: {e}")
                self.logger.warning("Retrying on CPU...")
                try:
                    # Reload model on CPU
                    self.model = whisper.load_model(self.model_size, device="cpu")
                    self.use_gpu = False
                    # Retry transcription on CPU with quality settings
                    result = self.model.transcribe(
                        audio_file,
                        fp16=False,
                        language='en',
                        task='transcribe',
                        condition_on_previous_text=False,
                        temperature=0.0,
                        best_of=5,
                        beam_size=5,
                        no_speech_threshold=0.6,
                        logprob_threshold=-1.0,
                        compression_ratio_threshold=2.4,
                        word_timestamps=False
                    )
                    text = result.get('text', '').strip()
                    self.logger.info("✅ CPU fallback transcription successful")
                    return {
                        'text': text,
                        'confidence': 0.95,
                        'method': 'whisper',
                        'language': result.get('language', 'unknown'),
                        'success': True
                    }
                except Exception as e2:
                    self.logger.error(f"CPU fallback transcription also failed: {e2}")
                    error_msg = 'Transcription failed on both GPU and CPU.'
                    return {
                        'text': '',
                        'confidence': 0.0,
                        'method': 'whisper',
                        'error': error_msg,
                        'error_detail': str(e2),
                        'success': False
                    }
            
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


class FasterWhisperEngine(SpeechEngine):
    """CTranslate2-optimized Whisper engine (4x faster than openai-whisper)."""
    
    def __init__(self, model_size: str = "base", config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.model_size = model_size
        self.model = None
        self.config = config or {}
        
        # GPU detection
        self.has_gpu, self.device_name = self._detect_gpu()
        self.force_cpu = self.config.get('force_cpu', False)
        
        # Check cuDNN availability before attempting GPU usage
        if self.has_gpu and not self.force_cpu:
            if not self._check_cudnn_available():
                self.logger.warning("cuDNN libraries not found - forcing CPU mode")
                self.logger.warning("Install libcudnn9 for GPU support: sudo apt install libcudnn9-cuda-12")
                self.force_cpu = True
        
        self.use_gpu = self.has_gpu and not self.force_cpu
        
        # Log GPU status
        if self.use_gpu:
            self.logger.info(f"⚡ Faster-Whisper GPU: {self.device_name} - Turbo mode enabled")
        elif self.has_gpu and self.force_cpu:
            self.logger.info(f"Faster-Whisper GPU detected: {self.device_name} - Disabled by config")
        else:
            self.logger.info("Faster-Whisper running on CPU")
        
        self._load_model()
    
    def _detect_gpu(self) -> tuple:
        """Detect GPU availability and return (has_gpu, device_name)."""
        try:
            import torch
            if torch.cuda.is_available():
                device_name = torch.cuda.get_device_name(0)
                memory_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
                return (True, f"{device_name} ({memory_gb:.1f}GB)")
        except Exception as e:
            self.logger.debug(f"GPU detection failed: {e}")
        return (False, "CPU")
    
    def _check_cudnn_available(self) -> bool:
        """Check if cuDNN libraries are available."""
        try:
            import ctypes
            import ctypes.util
            
            # Try to find cuDNN library
            cudnn_libs = [
                'libcudnn.so.9',
                'libcudnn.so.8', 
                'libcudnn.so'
            ]
            
            for lib_name in cudnn_libs:
                lib_path = ctypes.util.find_library(lib_name.replace('.so', '').replace('lib', ''))
                if lib_path:
                    try:
                        ctypes.CDLL(lib_path)
                        self.logger.debug(f"Found cuDNN library: {lib_path}")
                        return True
                    except OSError:
                        continue
            
            self.logger.debug("cuDNN library not found in system")
            return False
        except Exception as e:
            self.logger.debug(f"cuDNN check failed: {e}")
            return False
    
    def _load_model(self) -> None:
        """Load the Faster-Whisper model."""
        if not FASTER_WHISPER_AVAILABLE:
            self.logger.error("faster-whisper not available")
            return
        
        try:
            # Determine device and compute type
            device = "cuda" if self.use_gpu else "cpu"
            compute_type = "float16" if self.use_gpu else "int8"
            
            self.logger.info(f"Loading Faster-Whisper model: {self.model_size} on {device} ({compute_type})")
            
            self.model = WhisperModel(
                self.model_size,
                device=device,
                compute_type=compute_type,
                cpu_threads=4  # Optimize CPU performance
            )
            
            self.logger.info("✅ Faster-Whisper model loaded successfully (4x speedup)")
        except Exception as e:
            error_str = str(e).lower()
            # Check for cuDNN-related errors
            if self.use_gpu and ('cudnn' in error_str or 'libcudnn' in error_str):
                self.logger.warning(f"cuDNN library missing or incompatible: {e}")
                self.logger.warning("Falling back to CPU mode (install libcudnn9 for GPU support)")
            else:
                self.logger.error(f"Failed to load Faster-Whisper model: {e}")
            
            # Try fallback to CPU if GPU load failed
            if self.use_gpu:
                self.logger.warning("Attempting to load on CPU as fallback...")
                try:
                    self.model = WhisperModel(
                        self.model_size,
                        device="cpu",
                        compute_type="int8",
                        cpu_threads=4
                    )
                    self.use_gpu = False
                    self.logger.info("✅ Faster-Whisper loaded on CPU (fallback)")
                except Exception as e2:
                    self.logger.error(f"CPU fallback also failed: {e2}")
    
    def transcribe(self, audio_file: str) -> Dict[str, Any]:
        """Transcribe audio using Faster-Whisper with optimizations."""
        if not self.model:
            return {
                'text': '',
                'confidence': 0.0,
                'method': 'faster-whisper',
                'error': 'Faster-Whisper model not loaded',
                'success': False
            }
        
        try:
            device_info = "GPU" if self.use_gpu else "CPU"
            self.logger.info(f"Transcribing with Faster-Whisper {self.model_size} on {device_info}...")
            
            # Transcribe with optimizations
            segments, info = self.model.transcribe(
                audio_file,
                beam_size=1,  # Single beam for speed
                best_of=1,
                temperature=0.0,
                vad_filter=True,  # Voice activity detection (filters silence)
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    threshold=0.5
                ),
                condition_on_previous_text=False,
                compression_ratio_threshold=2.4,
                log_prob_threshold=-1.0,
                no_speech_threshold=0.6
            )
            
            # Combine segments into single text
            text = " ".join([seg.text for seg in segments]).strip()
            
            if not text:
                return {
                    'text': '',
                    'confidence': 0.0,
                    'method': 'faster-whisper',
                    'error': 'No speech detected in audio. The recording may be too noisy or unclear.',
                    'success': False
                }
            
            return {
                'text': text,
                'confidence': 0.95,
                'method': 'faster-whisper',
                'language': info.language,
                'language_probability': info.language_probability,
                'duration': info.duration,
                'success': True
            }
        
        except Exception as e:
            self.logger.error(f"Faster-Whisper transcription failed: {e}")
            error_msg = 'Transcription failed. The audio may be too noisy, unclear, or in an unsupported format.'
            return {
                'text': '',
                'confidence': 0.0,
                'method': 'faster-whisper',
                'error': error_msg,
                'error_detail': str(e),
                'success': False
            }
    
    def is_available(self) -> bool:
        """Check if Faster-Whisper is available."""
        return FASTER_WHISPER_AVAILABLE and self.model is not None
    
    @property
    def name(self) -> str:
        """Engine name."""
        return "faster-whisper"


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
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(__name__)
        self.engines = {}
        self.current_engine = None
        self.config = config or {}
        self._init_engines()
    
    def _init_engines(self) -> None:
        """Initialize all available speech recognition engines."""
        # Get model size from config (default to 'base' for better quality)
        model_size = self.config.get('whisper_model_size', 'base')
        
        # Priority 1: Try Faster-Whisper (4x faster)
        faster_whisper_engine = FasterWhisperEngine(model_size=model_size, config=self.config)
        if faster_whisper_engine.is_available():
            self.engines['faster-whisper'] = faster_whisper_engine
            self.logger.info("⚡ Faster-Whisper engine registered (primary)")
        
        # Priority 2: Initialize standard Whisper as fallback
        whisper_engine = WhisperEngine(model_size=model_size, config=self.config)
        if whisper_engine.is_available():
            self.engines['whisper'] = whisper_engine
            self.logger.info("Whisper engine registered (fallback)")
        
        # Priority 3: Initialize Google Speech Recognition
        google_engine = GoogleSpeechEngine()
        if google_engine.is_available():
            self.engines['google'] = google_engine
            self.logger.info("Google Speech engine registered (fallback)")
        
        self.logger.info(f"Available engines: {list(self.engines.keys())}")
        
        # Set default engine (prefer Faster-Whisper > Whisper > Google)
        if 'faster-whisper' in self.engines:
            self.current_engine = 'faster-whisper'
            self.logger.info("🚀 Using Faster-Whisper as primary engine (4x speedup)")
        elif 'whisper' in self.engines:
            self.current_engine = 'whisper'
            self.logger.info("Using standard Whisper engine")
        elif 'google' in self.engines:
            self.current_engine = 'google'
            self.logger.info("Using Google Speech engine")
        else:
            self.logger.warning("No speech engines available!")
    
    def get_available_engines(self) -> List[str]:
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

    def format_transcription_error(self, result: Dict[str, Any]) -> Tuple[str, str]:
        """
        Format transcription error into user-friendly message for GUI.

        Args:
            result: Transcription result dictionary with error information

        Returns:
            Tuple of (error_title, error_message) for display
        """
        if result.get('success', False):
            return "", ""  # No error

        error = result.get('error', 'Unknown error')
        method = result.get('method', 'unknown')

        # Determine error type based on error message content
        if 'not available' in error.lower() or method == 'no_engine':
            return format_engine_error('not_available', engine_name=self.current_engine)

        elif 'model' in error.lower() and 'load' in error.lower():
            return format_engine_error('model_load', engine_name=method)

        elif 'gpu' in error.lower() or 'cuda' in error.lower():
            return format_engine_error('gpu_failed', engine_name=method)

        elif result.get('fallback_failed', False):
            # Both engines failed
            primary = result.get('primary_engine', self.current_engine)
            fallback = result.get('fallback_engine', 'unknown')
            title, message = format_engine_error('all_failed')
            # Add engine details
            message += f"\n\nAttempted engines:\n  • {primary}\n  • {fallback}"
            return title, message

        else:
            # General transcription failure
            return format_engine_error('transcription', engine_name=method)

    def _get_alternative_engine(self) -> Optional[str]:
        """Get an alternative engine for fallback with priority order."""
        # Fallback priority: faster-whisper > whisper > google
        
        if self.current_engine == 'faster-whisper':
            # Faster-whisper failed, try standard whisper, then google
            if 'whisper' in self.engines:
                return 'whisper'
            elif 'google' in self.engines:
                return 'google'
        
        elif self.current_engine == 'whisper':
            # Standard whisper failed, try faster-whisper or google
            if 'faster-whisper' in self.engines:
                return 'faster-whisper'
            elif 'google' in self.engines:
                return 'google'
        
        elif self.current_engine == 'google':
            # Google failed, try faster-whisper or whisper
            if 'faster-whisper' in self.engines:
                return 'faster-whisper'
            elif 'whisper' in self.engines:
                return 'whisper'
        
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
