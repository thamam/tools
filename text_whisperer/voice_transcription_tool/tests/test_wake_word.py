"""
Tests for the wake word detection module.
"""

import pytest
import time
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from utils.wake_word import WakeWordDetector, SimpleWakeWordDetector


class TestWakeWordDetector:
    """Test the WakeWordDetector class."""
    
    def test_wake_word_initialization(self):
        """Test wake word detector initialization."""
        detector = WakeWordDetector(
            wake_words=["test wake word"],
            threshold=0.6
        )
        
        assert detector is not None
        assert detector.wake_words == ["test wake word"]
        assert detector.threshold == 0.6
        assert detector.is_listening is False
    
    @patch('utils.wake_word.OPENWAKEWORD_AVAILABLE', False)
    def test_unavailable_without_openwakeword(self):
        """Test detector when openWakeWord is not available."""
        detector = WakeWordDetector()
        assert detector.is_available() is False
    
    @patch('utils.wake_word.PYAUDIO_AVAILABLE', False)
    def test_unavailable_without_pyaudio(self):
        """Test detector when PyAudio is not available."""
        detector = WakeWordDetector()
        assert detector.is_available() is False
    
    def test_set_wake_words(self):
        """Test setting custom wake words."""
        detector = WakeWordDetector()
        
        new_words = ["alexa", "hey siri"]
        success = detector.set_wake_words(new_words)
        
        assert success is True
        assert detector.wake_words == new_words
    
    def test_set_threshold(self):
        """Test setting detection threshold."""
        detector = WakeWordDetector()
        
        # Test valid threshold
        detector.set_threshold(0.7)
        assert detector.threshold == 0.7
        
        # Test boundary values
        detector.set_threshold(1.5)  # Should clamp to 1.0
        assert detector.threshold == 1.0
        
        detector.set_threshold(-0.5)  # Should clamp to 0.0
        assert detector.threshold == 0.0
    
    def test_callback_invocation(self):
        """Test that callback is invoked on detection."""
        mock_callback = Mock()
        detector = WakeWordDetector(callback=mock_callback)
        
        # Simulate wake word detection
        detector._on_wake_word_detected("test word", 0.85)
        
        mock_callback.assert_called_once_with("test word", 0.85)
    
    def test_get_status(self):
        """Test getting detector status."""
        detector = WakeWordDetector()
        
        status = detector.get_status()
        assert isinstance(status, dict)
        assert 'is_available' in status
        assert 'is_listening' in status
        assert 'wake_words' in status
        assert 'threshold' in status
        assert 'model_loaded' in status
        assert 'last_activation' in status
    
    @patch('utils.wake_word.PYAUDIO_AVAILABLE', True)
    @patch('utils.wake_word.pyaudio.PyAudio')
    def test_start_stop_listening(self, mock_pyaudio):
        """Test starting and stopping listening."""
        # Mock PyAudio
        mock_audio = Mock()
        mock_stream = Mock()
        mock_audio.open.return_value = mock_stream
        mock_pyaudio.return_value = mock_audio
        
        detector = WakeWordDetector()
        
        # Assume model is available for this test
        with patch.object(detector, 'is_available', return_value=True):
            with patch.object(detector, '_initialize_model', return_value=True):
                # Start listening
                success = detector.start_listening()
                assert success is True
                assert detector.is_listening is True
                
                # Stop listening
                detector.stop_listening()
                assert detector.is_listening is False
    
    def test_cooldown_period(self):
        """Test activation cooldown period."""
        mock_callback = Mock()
        detector = WakeWordDetector(
            callback=mock_callback,
            wake_words=["hey jarvis"]  # Ensure wake word is in list
        )
        detector.activation_cooldown = 2.0  # 2 second cooldown
        
        # The cooldown happens in _process_audio_chunk, not _on_wake_word_detected
        # So we test the cooldown logic directly
        
        # Set initial activation time
        detector.last_activation = time.time()
        
        # Create mock audio data
        audio_data = np.ones(512, dtype=np.float32) * 0.5
        
        # Mock the model prediction to return high score for our wake word
        with patch.object(detector, 'model', Mock()):
            detector.model.predict.return_value = {"hey jarvis": 0.9}
            
            # Process audio immediately after activation (should be ignored due to cooldown)
            detector._process_audio_chunk(audio_data)
            assert mock_callback.call_count == 0
            
            # Simulate time passing beyond cooldown
            detector.last_activation = time.time() - 3
            
            # Process audio again (should trigger)
            detector._process_audio_chunk(audio_data)
            assert mock_callback.call_count == 1


class TestSimpleWakeWordDetector:
    """Test the SimpleWakeWordDetector class."""
    
    def test_simple_detector_initialization(self):
        """Test simple detector initialization."""
        detector = SimpleWakeWordDetector(wake_phrase="hey assistant")
        
        assert detector is not None
        assert detector.wake_phrase == "hey assistant"
        assert detector.energy_threshold == 1000
    
    def test_simple_detector_energy_detection(self):
        """Test energy-based detection."""
        mock_callback = Mock()
        detector = SimpleWakeWordDetector(callback=mock_callback)
        
        # Create audio data with low energy (should not trigger)
        quiet_audio = np.zeros(1024, dtype=np.float32)
        detector._process_audio_chunk(quiet_audio)
        assert mock_callback.call_count == 0
        
        # Create audio data with high energy (should trigger)
        loud_audio = np.ones(1024, dtype=np.float32) * 0.5
        detector.last_activation = 0  # Reset cooldown
        detector._process_audio_chunk(loud_audio)
        assert mock_callback.call_count == 1
    
    def test_simple_detector_always_available(self):
        """Test that simple detector is always available."""
        detector = SimpleWakeWordDetector()
        
        # Should return True for _initialize_model
        assert detector._initialize_model() is True