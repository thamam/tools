"""
utils/wake_word.py - Wake word detection for hands-free activation.

Implements continuous listening for wake words using openWakeWord.
"""

import logging
import threading
import queue
import time
import numpy as np
from typing import Optional, Callable, List, Dict, Any
from pathlib import Path

try:
    import openwakeword
    from openwakeword.model import Model
    OPENWAKEWORD_AVAILABLE = True
except ImportError:
    OPENWAKEWORD_AVAILABLE = False
    
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False


class WakeWordDetector:
    """Handles wake word detection for hands-free activation."""
    
    def __init__(self, callback: Optional[Callable] = None, 
                 wake_words: Optional[List[str]] = None,
                 threshold: float = 0.5):
        """
        Initialize wake word detector.
        
        Args:
            callback: Function to call when wake word is detected
            wake_words: List of wake words to detect (default: ["hey jarvis"])
            threshold: Detection threshold (0.0-1.0)
        """
        self.logger = logging.getLogger(__name__)
        self.callback = callback
        self.threshold = threshold
        self.wake_words = wake_words or ["hey jarvis"]
        
        # Audio parameters
        self.sample_rate = 16000
        self.chunk_size = 512  # ~32ms chunks at 16kHz
        self.format = pyaudio.paInt16 if PYAUDIO_AVAILABLE else None
        
        # State management
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.listen_thread = None
        self.process_thread = None
        
        # Wake word model
        self.model = None
        self.audio_instance = None
        self.stream = None
        
        # Performance tracking
        self.last_activation = 0
        self.activation_cooldown = 3.0  # Seconds between activations (increased from 2.0)
        
        # Initialize if available
        if self.is_available():
            self._initialize_model()
    
    def is_available(self) -> bool:
        """Check if wake word detection is available."""
        if not OPENWAKEWORD_AVAILABLE:
            self.logger.warning("openWakeWord not available - install with: pip install openwakeword")
            return False
            
        if not PYAUDIO_AVAILABLE:
            self.logger.warning("PyAudio not available for wake word detection")
            return False
            
        return True
    
    def _initialize_model(self) -> bool:
        """Initialize the wake word model."""
        try:
            # Initialize openWakeWord with pre-trained models
            self.model = Model(
                wakeword_models=["hey_jarvis"],  # Use pre-trained model
                inference_framework="onnx"  # or "tflite" 
            )
            
            self.logger.info("✅ Wake word model initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize wake word model: {e}")
            # Try fallback to basic model
            try:
                self.model = Model()  # Use default models
                self.logger.info("✅ Using default wake word models")
                return True
            except Exception as e2:
                self.logger.error(f"Failed to initialize default model: {e2}")
                return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available pre-trained wake word models."""
        if not OPENWAKEWORD_AVAILABLE:
            return []
            
        try:
            # List available pre-trained models
            import openwakeword.utils as oww_utils
            models = oww_utils.list_models()
            return models
        except:
            # Return common models if listing fails
            return ["hey_jarvis", "alexa", "hey_mycroft", "hey_rhasspy"]
    
    def set_wake_words(self, wake_words: List[str]) -> bool:
        """Set custom wake words."""
        self.wake_words = wake_words
        
        # Re-initialize model with new wake words if needed
        if self.model and self.is_listening:
            self.stop_listening()
            self._initialize_model()
            self.start_listening()
            
        return True
    
    def set_threshold(self, threshold: float) -> None:
        """Set detection threshold (0.0-1.0)."""
        self.threshold = max(0.0, min(1.0, threshold))
        self.logger.info(f"Wake word threshold set to {self.threshold}")
    
    def start_listening(self) -> bool:
        """Start continuous wake word listening."""
        if not self.is_available():
            return False
            
        if self.is_listening:
            self.logger.warning("Already listening for wake words")
            return True
            
        try:
            # Initialize PyAudio
            self.audio_instance = pyaudio.PyAudio()
            
            # Open audio stream
            self.stream = self.audio_instance.open(
                format=self.format,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            # Start threads
            self.is_listening = True
            self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
            
            self.listen_thread.start()
            self.process_thread.start()
            
            self.stream.start_stream()
            
            self.logger.info("🎤 Wake word detection started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start wake word detection: {e}")
            self.stop_listening()
            return False
    
    def stop_listening(self) -> None:
        """Stop wake word listening."""
        self.is_listening = False
        
        # Stop stream
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
            self.stream = None
            
        # Close PyAudio
        if self.audio_instance:
            try:
                self.audio_instance.terminate()
            except:
                pass
            self.audio_instance = None
            
        # Clear queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except:
                pass
                
        self.logger.info("🛑 Wake word detection stopped")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback to capture audio chunks."""
        if self.is_listening:
            self.audio_queue.put(in_data)
        return (in_data, pyaudio.paContinue)
    
    def _listen_loop(self) -> None:
        """Main listening loop (runs in thread)."""
        # This is handled by PyAudio callback
        while self.is_listening:
            time.sleep(0.1)
    
    def _process_loop(self) -> None:
        """Process audio chunks for wake word detection."""
        audio_buffer = b""
        
        while self.is_listening:
            try:
                # Get audio chunk with timeout
                chunk = self.audio_queue.get(timeout=0.5)
                audio_buffer += chunk
                
                # Process when we have enough audio (80ms worth)
                if len(audio_buffer) >= self.chunk_size * 4:
                    # Convert to numpy array
                    audio_data = np.frombuffer(audio_buffer[:self.chunk_size * 4], 
                                               dtype=np.int16)
                    
                    # Normalize to [-1, 1]
                    audio_data = audio_data.astype(np.float32) / 32768.0
                    
                    # Predict wake word
                    self._process_audio_chunk(audio_data)
                    
                    # Keep remaining audio
                    audio_buffer = audio_buffer[self.chunk_size * 4:]
                    
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing audio: {e}")
    
    def _process_audio_chunk(self, audio_data: np.ndarray) -> None:
        """Process a single audio chunk for wake word detection."""
        if not self.model:
            return
            
        try:
            # Get predictions from model
            prediction = self.model.predict(audio_data)
            
            # Check each wake word
            for wake_word in self.wake_words:
                # Get score for this wake word
                if isinstance(prediction, dict):
                    score = prediction.get(wake_word, 0.0)
                else:
                    # Handle different prediction formats
                    score = float(prediction) if prediction > 0 else 0.0
                
                # Check if detected
                if score >= self.threshold:
                    current_time = time.time()
                    
                    # Check cooldown to avoid multiple activations
                    if current_time - self.last_activation >= self.activation_cooldown:
                        self.last_activation = current_time
                        self._on_wake_word_detected(wake_word, score)
                        
        except Exception as e:
            self.logger.debug(f"Wake word processing error: {e}")
    
    def _on_wake_word_detected(self, wake_word: str, score: float) -> None:
        """Handle wake word detection."""
        self.logger.info(f"🎯 Wake word detected: '{wake_word}' (score: {score:.2f})")
        
        # Call callback if provided
        if self.callback:
            try:
                self.callback(wake_word, score)
            except Exception as e:
                self.logger.error(f"Wake word callback error: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current detector status."""
        return {
            "is_available": self.is_available(),
            "is_listening": self.is_listening,
            "wake_words": self.wake_words,
            "threshold": self.threshold,
            "model_loaded": self.model is not None,
            "last_activation": self.last_activation
        }
    
    def test_microphone(self, duration: float = 3.0) -> bool:
        """Test microphone for wake word detection."""
        if not self.is_available():
            return False
            
        try:
            self.logger.info("Testing microphone for wake word detection...")
            
            # Temporarily start listening
            was_listening = self.is_listening
            if not was_listening:
                self.start_listening()
                
            # Record for duration
            time.sleep(duration)
            
            # Stop if we started it
            if not was_listening:
                self.stop_listening()
                
            self.logger.info("✅ Microphone test complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Microphone test failed: {e}")
            return False
    
    def start_live_test(self, test_callback: Optional[Callable] = None) -> bool:
        """Start live testing mode for wake word detection."""
        if not self.is_available():
            return False
            
        # Store original callback and replace with test callback
        self.original_callback = self.callback
        if test_callback:
            self.callback = test_callback
        
        # Start listening if not already
        if not self.is_listening:
            return self.start_listening()
        return True
    
    def stop_live_test(self) -> None:
        """Stop live testing mode and restore original callback."""
        # Restore original callback
        if hasattr(self, 'original_callback'):
            self.callback = self.original_callback
            delattr(self, 'original_callback')
        
        # Keep listening state as it was
        # (don't auto-stop listening)
    
    def collect_training_sample(self, duration: float = 3.0) -> Optional[Dict[str, Any]]:
        """Collect a training sample for the wake word."""
        if not self.is_available():
            return None
            
        try:
            import numpy as np
            
            self.logger.info(f"Collecting training sample for {duration} seconds...")
            
            # Store audio data during recording
            self.training_audio_buffer = []
            self.is_collecting_training = True
            
            # Start listening if not already
            was_listening = self.is_listening
            if not was_listening:
                self.start_listening()
            
            # Collect for specified duration
            time.sleep(duration)
            
            # Stop collecting
            self.is_collecting_training = False
            
            # Stop listening if we started it
            if not was_listening:
                self.stop_listening()
            
            # Process collected audio
            if self.training_audio_buffer:
                # Concatenate all audio chunks
                audio_data = np.concatenate(self.training_audio_buffer)
                
                # Create training sample
                training_sample = {
                    'audio_data': audio_data,
                    'duration': duration,
                    'sample_rate': self.sample_rate,
                    'wake_word': self.wake_words[0] if self.wake_words else 'unknown',
                    'timestamp': time.time()
                }
                
                self.logger.info("✅ Training sample collected")
                return training_sample
            else:
                self.logger.warning("No audio data collected")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to collect training sample: {e}")
            return None
        finally:
            # Clean up
            self.is_collecting_training = False
            if hasattr(self, 'training_audio_buffer'):
                delattr(self, 'training_audio_buffer')
    
    def _process_audio_chunk(self, audio_data: np.ndarray) -> None:
        """Process a single audio chunk for wake word detection."""
        # Store audio for training if collecting
        if hasattr(self, 'is_collecting_training') and self.is_collecting_training:
            if hasattr(self, 'training_audio_buffer'):
                self.training_audio_buffer.append(audio_data.copy())
        
        if not self.model:
            return
            
        try:
            # Get predictions from model
            prediction = self.model.predict(audio_data)
            
            # Check each wake word
            for wake_word in self.wake_words:
                # Get score for this wake word
                if isinstance(prediction, dict):
                    score = prediction.get(wake_word, 0.0)
                else:
                    # Handle different prediction formats
                    score = float(prediction) if prediction > 0 else 0.0
                
                # Check if detected
                if score >= self.threshold:
                    current_time = time.time()
                    
                    # Check cooldown to avoid multiple activations
                    if current_time - self.last_activation >= self.activation_cooldown:
                        self.last_activation = current_time
                        self._on_wake_word_detected(wake_word, score)
                        
        except Exception as e:
            self.logger.debug(f"Wake word processing error: {e}")


class SimpleWakeWordDetector(WakeWordDetector):
    """Simplified wake word detector using basic audio pattern matching."""
    
    def __init__(self, callback: Optional[Callable] = None,
                 wake_phrase: str = "hey computer", threshold: float = 0.5):
        """Initialize simple detector (fallback when openWakeWord unavailable)."""
        super().__init__(callback, threshold=threshold)
        self.wake_phrase = wake_phrase.lower()
        # Higher default threshold to reduce false positives
        self.energy_threshold = 3000  # Audio energy threshold (increased from 1000)
        self.training_samples = []  # Store training samples to adjust threshold
        # Map the 0-1 threshold to energy multiplier (0.5 = 1x, 0.8 = 2x, etc)
        self.threshold_multiplier = 1.0 + (threshold - 0.5) * 2
        
    def is_available(self) -> bool:
        """Simple detector only needs PyAudio."""
        if not PYAUDIO_AVAILABLE:
            self.logger.warning("PyAudio not available for wake word detection")
            return False
        return True
    
    def _initialize_model(self) -> bool:
        """No model needed for simple detector."""
        self.logger.info("Using simple wake word detector (energy-based)")
        return True
    
    def collect_training_sample(self, duration: float = 3.0) -> Optional[Dict[str, Any]]:
        """Collect training sample to improve energy threshold."""
        sample = super().collect_training_sample(duration)
        if sample:
            # Calculate energy statistics from the sample
            audio_data = sample['audio_data']
            energy = np.sqrt(np.mean(audio_data ** 2)) * 32768
            
            # Store sample with energy info
            training_sample = {
                'energy': energy,
                'wake_word': sample['wake_word'],
                'timestamp': sample['timestamp']
            }
            
            self.training_samples.append(training_sample)
            
            # Adjust threshold based on collected samples
            if len(self.training_samples) >= 3:
                energies = [s['energy'] for s in self.training_samples[-5:]]  # Use last 5 samples
                avg_energy = np.mean(energies)
                # Set threshold slightly below average training energy
                self.energy_threshold = max(500, avg_energy * 0.8)
                self.logger.info(f"Adjusted energy threshold to {self.energy_threshold:.0f} based on training")
            
            return sample
        return None
        
    def _process_audio_chunk(self, audio_data: np.ndarray) -> None:
        """Simple energy-based detection with training support."""
        # Store audio for training if collecting
        if hasattr(self, 'is_collecting_training') and self.is_collecting_training:
            if hasattr(self, 'training_audio_buffer'):
                self.training_audio_buffer.append(audio_data.copy())
        
        # Calculate RMS energy
        energy = np.sqrt(np.mean(audio_data ** 2))
        
        # Convert to 16-bit scale
        energy_16bit = energy * 32768
        
        # Check if above threshold (indicates speech)
        # Apply threshold multiplier based on user setting
        effective_threshold = self.energy_threshold * self.threshold_multiplier
        if energy_16bit > effective_threshold:
            current_time = time.time()
            if current_time - self.last_activation >= self.activation_cooldown:
                self.last_activation = current_time
                # Lower confidence scores to prevent continuous triggering
                confidence = min(0.7, energy_16bit / (effective_threshold * 3))
                self._on_wake_word_detected("speech detected", confidence)