"""
audio/feedback.py - Audio feedback system for recording events.

Provides configurable sound effects for recording start/stop events.
"""

import logging
import threading
import os
from typing import Optional, Dict, Any
from pathlib import Path

# Try multiple audio playback methods for cross-platform support
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    import pyaudio
    import wave
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False


class AudioFeedback:
    """Manages audio feedback for recording events."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize audio feedback system.
        
        Args:
            config: Configuration dict with keys:
                - enabled: bool (default True)
                - volume: float 0.0-1.0 (default 0.5)
                - feedback_type: 'beep', 'sound', 'tts' (default 'beep')
                - start_sound: path to sound file
                - stop_sound: path to sound file
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Default configuration
        self.enabled = self.config.get('audio_feedback_enabled', True)
        self.volume = self.config.get('audio_feedback_volume', 0.5)
        self.feedback_type = self.config.get('audio_feedback_type', 'beep')
        
        # Sound file paths
        self.start_sound = self.config.get('audio_feedback_start_sound', None)
        self.stop_sound = self.config.get('audio_feedback_stop_sound', None)
        
        # Initialize audio backend
        self._init_audio_backend()
        
        # TTS engine for voice feedback
        self.tts_engine = None
        if TTS_AVAILABLE and self.feedback_type == 'tts':
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 150)
                self.tts_engine.setProperty('volume', self.volume)
            except Exception as e:
                self.logger.error(f"Failed to initialize TTS: {e}")
    
    def _init_audio_backend(self):
        """Initialize the audio playback backend."""
        self.audio_backend = None
        
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                pygame.mixer.set_num_channels(2)  # Allow overlapping sounds
                self.audio_backend = 'pygame'
                self.logger.info("Audio feedback using pygame")
            except Exception as e:
                self.logger.warning(f"Failed to initialize pygame: {e}")
        
        if not self.audio_backend and PYAUDIO_AVAILABLE:
            self.audio_backend = 'pyaudio'
            self.logger.info("Audio feedback using pyaudio")
        
        if not self.audio_backend:
            self.logger.warning("No audio backend available for feedback")
            self.enabled = False
    
    def play_start(self):
        """Play recording start feedback."""
        if not self.enabled:
            return
        
        # Run in thread to avoid blocking
        threading.Thread(target=self._play_start_internal, daemon=True).start()
    
    def play_stop(self):
        """Play recording stop feedback."""
        if not self.enabled:
            return
        
        # Run in thread to avoid blocking
        threading.Thread(target=self._play_stop_internal, daemon=True).start()
    
    def _play_start_internal(self):
        """Internal method to play start sound."""
        try:
            if self.feedback_type == 'beep':
                self._play_beep(frequency=800, duration=100)
            elif self.feedback_type == 'sound' and self.start_sound:
                self._play_sound_file(self.start_sound)
            elif self.feedback_type == 'tts' and self.tts_engine:
                self._speak("Recording started")
        except Exception as e:
            self.logger.error(f"Error playing start feedback: {e}")
    
    def _play_stop_internal(self):
        """Internal method to play stop sound."""
        try:
            if self.feedback_type == 'beep':
                self._play_beep(frequency=400, duration=200)
            elif self.feedback_type == 'sound' and self.stop_sound:
                self._play_sound_file(self.stop_sound)
            elif self.feedback_type == 'tts' and self.tts_engine:
                self._speak("Recording stopped")
        except Exception as e:
            self.logger.error(f"Error playing stop feedback: {e}")
    
    def _play_beep(self, frequency: int, duration: int):
        """
        Play a simple beep sound.
        
        Args:
            frequency: Frequency in Hz
            duration: Duration in milliseconds
        """
        if self.audio_backend == 'pygame':
            try:
                # Generate beep using pygame
                import numpy as np
                sample_rate = 22050
                samples = int(sample_rate * duration / 1000.0)
                waves = np.sin(2 * np.pi * frequency * np.arange(samples) / sample_rate)
                
                # Apply volume
                waves = (waves * self.volume * 32767).astype(np.int16)
                
                # Convert to stereo
                stereo_waves = np.zeros((samples, 2), dtype=np.int16)
                stereo_waves[:, 0] = waves
                stereo_waves[:, 1] = waves
                
                # Play
                sound = pygame.sndarray.make_sound(stereo_waves)
                sound.play()
            except Exception as e:
                self.logger.error(f"Pygame beep failed: {e}")
                self._fallback_beep()
        
        elif self.audio_backend == 'pyaudio':
            self._pyaudio_beep(frequency, duration)
        else:
            self._fallback_beep()
    
    def _pyaudio_beep(self, frequency: int, duration: int):
        """Generate beep using PyAudio."""
        try:
            p = pyaudio.PyAudio()
            
            # Generate samples
            sample_rate = 44100
            samples = int(sample_rate * duration / 1000.0)
            
            # Generate sine wave
            import numpy as np
            t = np.linspace(0, duration / 1000.0, samples, False)
            wave = np.sin(frequency * t * 2 * np.pi) * self.volume
            
            # Convert to bytes
            wave_bytes = (wave * 32767).astype(np.int16).tobytes()
            
            # Play
            stream = p.open(format=pyaudio.paInt16,
                          channels=1,
                          rate=sample_rate,
                          output=True)
            stream.write(wave_bytes)
            stream.stop_stream()
            stream.close()
            p.terminate()
        except Exception as e:
            self.logger.error(f"PyAudio beep failed: {e}")
            self._fallback_beep()
    
    def _fallback_beep(self):
        """Fallback beep using system bell."""
        try:
            # Try system bell
            print('\a', end='', flush=True)
        except:
            pass
    
    def _play_sound_file(self, file_path: str):
        """Play a sound file."""
        if not os.path.exists(file_path):
            self.logger.error(f"Sound file not found: {file_path}")
            return
        
        if self.audio_backend == 'pygame':
            try:
                sound = pygame.mixer.Sound(file_path)
                sound.set_volume(self.volume)
                sound.play()
            except Exception as e:
                self.logger.error(f"Failed to play sound file: {e}")
        elif self.audio_backend == 'pyaudio':
            self._play_wav_pyaudio(file_path)
    
    def _play_wav_pyaudio(self, file_path: str):
        """Play WAV file using PyAudio."""
        try:
            wf = wave.open(file_path, 'rb')
            p = pyaudio.PyAudio()
            
            stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                          channels=wf.getnchannels(),
                          rate=wf.getframerate(),
                          output=True)
            
            # Read and play chunks
            chunk_size = 1024
            data = wf.readframes(chunk_size)
            
            while data:
                # Apply volume
                if self.volume < 1.0:
                    import numpy as np
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    audio_data = (audio_data * self.volume).astype(np.int16)
                    data = audio_data.tobytes()
                
                stream.write(data)
                data = wf.readframes(chunk_size)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            wf.close()
        except Exception as e:
            self.logger.error(f"Failed to play WAV file: {e}")
    
    def _speak(self, text: str):
        """Use text-to-speech for feedback."""
        if self.tts_engine:
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                self.logger.error(f"TTS failed: {e}")
    
    def set_enabled(self, enabled: bool):
        """Enable or disable audio feedback."""
        self.enabled = enabled
        self.logger.info(f"Audio feedback {'enabled' if enabled else 'disabled'}")
    
    def set_volume(self, volume: float):
        """Set feedback volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
        if self.tts_engine:
            self.tts_engine.setProperty('volume', self.volume)
    
    def set_feedback_type(self, feedback_type: str):
        """Set feedback type: 'beep', 'sound', or 'tts'."""
        if feedback_type in ['beep', 'sound', 'tts']:
            self.feedback_type = feedback_type
            if feedback_type == 'tts' and not self.tts_engine and TTS_AVAILABLE:
                try:
                    self.tts_engine = pyttsx3.init()
                    self.tts_engine.setProperty('rate', 150)
                    self.tts_engine.setProperty('volume', self.volume)
                except Exception as e:
                    self.logger.error(f"Failed to initialize TTS: {e}")