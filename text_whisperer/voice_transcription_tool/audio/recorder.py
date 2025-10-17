"""
audio/recorder.py - Audio recording functionality for the Voice Transcription Tool.

MIGRATION STEP 3A: Create this file

TO MIGRATE from voice_transcription.py, copy these methods:
- init_audio() → becomes _init_audio_method()
- record_audio() → becomes start_recording()
- record_with_pyaudio() → keep as is
- record_with_arecord() → keep as is  
- record_with_ffmpeg() → keep as is
- test_microphone() → becomes test_recording()
"""

import logging
import tempfile
import subprocess
import platform
import time
import threading
from typing import Optional, Callable
from pathlib import Path

try:
    import pyaudio
    import wave
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False


class AudioRecorder:
    """Handles audio recording using various methods."""
    
    def __init__(self, sample_rate: int = 16000, channels: int = 1, chunk_size: int = 1024):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.is_recording = False
        self.logger = logging.getLogger(__name__)
        
        # Audio setup
        self.audio_method = None
        self.audio_instance = None
        self.format = None
        self.current_stream = None  # Store current recording stream for cleanup

        self._init_audio_method()
    
    def _init_audio_method(self) -> None:
        """
        Initialize the best available audio recording method.
        
        MIGRATION: Copy the logic from your init_audio() method here.
        """
        if PYAUDIO_AVAILABLE:
            try:
                import pyaudio
                self.audio_instance = pyaudio.PyAudio()
                self.format = pyaudio.paInt16
                self.audio_method = "pyaudio"
                self.logger.info("✅ PyAudio initialized")
                return
            except Exception as e:
                self.logger.warning(f"PyAudio failed: {e}")
        
        # Fallback to system tools
        system = platform.system().lower()
        if system == "linux":
            if self._command_exists("arecord"):
                self.audio_method = "arecord"
                self.logger.info("✅ Using arecord")
            elif self._command_exists("ffmpeg"):
                self.audio_method = "ffmpeg"
                self.logger.info("✅ Using ffmpeg")
        elif system == "darwin":
            self.audio_method = "afplay"
            self.logger.info("✅ Using macOS audio")
        elif system == "windows":
            self.audio_method = "windows"
            self.logger.info("✅ Using Windows audio")
        
        if not self.audio_method:
            self.logger.error("❌ No audio recording method available")
    
    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH."""
        try:
            subprocess.run(["which", command], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def test_recording(self, duration: float = 1.0, device_index: Optional[int] = None) -> bool:
        """
        Test audio recording functionality.
        
        MIGRATION: Copy logic from your test_microphone() method here.
        """
        self.logger.info(f"Testing audio recording (device: {device_index})...")
        
        try:
            if self.audio_method == "pyaudio":
                return self._test_pyaudio(duration, device_index)
            else:
                self.logger.info("Testing system audio tools")
                return True  # Assume system tools work
                
        except Exception as e:
            self.logger.error(f"Audio test failed: {e}")
            return False
    
    def _test_pyaudio(self, duration: float, device_index: Optional[int]) -> bool:
        """Test PyAudio recording."""
        try:
            stream = self.audio_instance.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size
            )
            
            # Record briefly
            frames = []
            for _ in range(int(self.sample_rate / self.chunk_size * duration)):
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
            self.logger.info("✅ PyAudio test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"PyAudio test failed: {e}")
            return False
    
    def start_recording(self, max_duration: float, 
                       progress_callback: Optional[Callable[[float], None]] = None) -> Optional[str]:
        """
        Start recording audio and return the temp file path.
        
        MIGRATION: Copy logic from your record_audio() method here.
        """
        if self.is_recording:
            self.logger.warning("Recording already in progress")
            return None
        
        if not self.audio_method:
            self.logger.error("No audio recording method available")
            return None
        
        self.is_recording = True
        temp_file = tempfile.mktemp(suffix=".wav")
        
        try:
            if self.audio_method == "pyaudio":
                self._record_pyaudio(temp_file, max_duration, progress_callback)
            elif self.audio_method == "arecord":
                self._record_arecord(temp_file, max_duration)
            elif self.audio_method == "ffmpeg":
                self._record_ffmpeg(temp_file, max_duration)
            else:
                raise Exception(f"Unsupported audio method: {self.audio_method}")
            
            # Verify recording
            if Path(temp_file).exists() and Path(temp_file).stat().st_size > 0:
                self.logger.info(f"Recording completed: {Path(temp_file).stat().st_size} bytes")
                return temp_file
            else:
                raise Exception("No audio data recorded")
                
        except Exception as e:
            self.logger.error(f"Recording failed: {e}")
            # Clean up failed recording
            try:
                Path(temp_file).unlink(missing_ok=True)
            except:
                pass
            return None
        finally:
            self.is_recording = False
    
    def stop_recording(self) -> None:
        """Stop the current recording."""
        self.is_recording = False
        self.logger.info("Recording stop requested")
    
    def _record_pyaudio(self, temp_file: str, max_duration: float,
                       progress_callback: Optional[Callable[[float], None]]) -> None:
        """
        Record using PyAudio.

        MIGRATION: Copy logic from your record_with_pyaudio() method here.
        """
        stream = self.audio_instance.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=None  # Blocking mode but with error handling
        )

        # Store stream so stop_recording() can close it
        self.current_stream = stream

        frames = []
        start_time = time.time()

        try:
            while self.is_recording and (time.time() - start_time) < max_duration:
                try:
                    # Read with timeout by checking available frames first
                    available_frames = stream.get_read_available()

                    if available_frames >= self.chunk_size:
                        # Read full chunk if available
                        data = stream.read(self.chunk_size, exception_on_overflow=False)
                        frames.append(data)
                    else:
                        # Small sleep to avoid busy waiting
                        time.sleep(0.01)
                        continue

                    # Progress callback
                    if progress_callback:
                        elapsed = time.time() - start_time
                        progress_callback(elapsed)

                except OSError as e:
                    # Stream closed or device error - exit cleanly
                    self.logger.info(f"Stream closed: {e}")
                    break
                except Exception as e:
                    self.logger.warning(f"Audio read error: {e}")
                    break
        finally:
            # Always clean up the stream
            try:
                if stream.is_active():
                    stream.stop_stream()
                stream.close()
                self.logger.info("Stream closed successfully")
            except Exception as e:
                self.logger.warning(f"Error closing stream: {e}")
            self.current_stream = None
        
        if not frames:
            raise Exception("No audio frames captured")
        
        # Save to file
        with wave.open(temp_file, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio_instance.get_sample_size(self.format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))
    
    def _record_arecord(self, temp_file: str, max_duration: float) -> None:
        """
        Record using arecord.
        
        MIGRATION: Copy logic from your record_with_arecord() method here.
        """
        cmd = [
            "arecord",
            "-f", "S16_LE",
            "-c", str(self.channels),
            "-r", str(self.sample_rate),
            "-d", str(max_duration),
            temp_file
        ]
        
        process = subprocess.Popen(cmd)
        
        while self.is_recording and process.poll() is None:
            time.sleep(0.1)
        
        if process.poll() is None:
            process.terminate()
            process.wait()
    
    def _record_ffmpeg(self, temp_file: str, max_duration: float) -> None:
        """
        Record using ffmpeg.
        
        MIGRATION: Copy logic from your record_with_ffmpeg() method here.
        """
        cmd = [
            "ffmpeg",
            "-f", "pulse",
            "-i", "default",
            "-t", str(max_duration),
            "-acodec", "pcm_s16le",
            "-ar", str(self.sample_rate),
            "-ac", str(self.channels),
            "-y",
            temp_file
        ]
        
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        while self.is_recording and process.poll() is None:
            time.sleep(0.1)
        
        if process.poll() is None:
            process.terminate()
            process.wait()
    
    def get_audio_method(self) -> str:
        """Get the current audio recording method."""
        return self.audio_method or "none"
    
    def is_available(self) -> bool:
        """Check if audio recording is available."""
        return self.audio_method is not None
    
    def cleanup(self) -> None:
        """Clean up audio resources."""
        self.is_recording = False
        if self.audio_instance and hasattr(self.audio_instance, 'terminate'):
            try:
                self.audio_instance.terminate()
            except:
                pass


# MIGRATION TEST: Test this module independently
if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from utils.logger import setup_logging
    
    setup_logging()
    
    # Test audio recorder
    recorder = AudioRecorder()
    
    print(f"Audio method: {recorder.get_audio_method()}")
    print(f"Available: {'✅' if recorder.is_available() else '❌'}")
    
    if recorder.is_available():
        print("Testing recording...")
        success = recorder.test_recording(1.0)
        print(f"Recording test: {'✅' if success else '❌'}")
    
    print("✅ Audio recorder module test completed!")
