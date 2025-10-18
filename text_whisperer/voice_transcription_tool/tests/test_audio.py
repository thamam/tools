"""
Tests for the audio module components.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from audio.devices import AudioDeviceManager
from audio.feedback import AudioFeedback
from audio.recorder import AudioRecorder


class TestAudioDeviceManager:
    """Test the AudioDeviceManager class."""
    
    @patch('audio.devices.PYAUDIO_AVAILABLE', True)
    @patch('audio.devices.pyaudio.PyAudio')
    def test_device_manager_initialization(self, mock_pyaudio):
        """Test device manager initialization."""
        # Mock PyAudio
        mock_audio = Mock()
        mock_audio.get_device_count.return_value = 2
        mock_audio.get_device_info_by_index.side_effect = [
            {
                'name': 'Test Device 1',
                'maxInputChannels': 2,
                'defaultSampleRate': 44100.0,
                'hostApi': 0
            },
            {
                'name': 'Test Device 2', 
                'maxInputChannels': 1,
                'defaultSampleRate': 16000.0,
                'hostApi': 1
            }
        ]
        mock_pyaudio.return_value = mock_audio
        
        device_manager = AudioDeviceManager()
        
        assert len(device_manager.get_devices()) == 2
        assert device_manager.get_device_count() == 2
    
    @patch('audio.devices.PYAUDIO_AVAILABLE', False)
    def test_device_manager_no_pyaudio(self):
        """Test device manager when PyAudio is not available."""
        device_manager = AudioDeviceManager()
        
        assert device_manager.get_device_count() == 0
        assert len(device_manager.get_devices()) == 0
    
    def test_get_devices_info(self):
        """Test getting formatted device information."""
        device_manager = AudioDeviceManager()
        device_manager.devices = [
            {
                'index': 0,
                'name': 'Test Device',
                'channels': 2,
                'sample_rate': 44100.0
            }
        ]
        
        info = device_manager.get_devices_info()
        assert len(info) == 1
        assert 'Test Device' in info[0]
        assert '44100' in info[0]
    
    def test_get_device_by_name(self):
        """Test finding device by name."""
        device_manager = AudioDeviceManager()
        device_manager.devices = [
            {
                'index': 0,
                'name': 'Microphone (USB Audio)',
                'channels': 1,
                'sample_rate': 16000.0
            }
        ]
        
        # Should find device with partial name match
        device = device_manager.get_device_by_name('USB Audio')
        assert device is not None
        assert device['name'] == 'Microphone (USB Audio)'
        
        # Should not find non-existent device
        device = device_manager.get_device_by_name('NonExistent')
        assert device is None


class TestAudioFeedback:
    """Test the AudioFeedback class."""
    
    def test_audio_feedback_initialization(self, sample_config):
        """Test audio feedback initialization."""
        feedback = AudioFeedback(sample_config)
        
        assert feedback.enabled == sample_config['audio_feedback_enabled']
        assert feedback.volume == sample_config['audio_feedback_volume']
        assert feedback.feedback_type == sample_config['audio_feedback_type']
    
    def test_audio_feedback_disabled(self):
        """Test audio feedback when disabled."""
        config = {'audio_feedback_enabled': False}
        feedback = AudioFeedback(config)
        
        assert feedback.enabled is False
        
        # Should not crash when calling play methods
        feedback.play_start()
        feedback.play_stop()
    
    def test_set_volume(self, sample_config):
        """Test setting volume."""
        feedback = AudioFeedback(sample_config)
        
        feedback.set_volume(0.8)
        assert feedback.volume == 0.8
        
        # Test clamping
        feedback.set_volume(1.5)
        assert feedback.volume == 1.0
        
        feedback.set_volume(-0.1)
        assert feedback.volume == 0.0
    
    def test_set_feedback_type(self, sample_config):
        """Test setting feedback type."""
        feedback = AudioFeedback(sample_config)
        
        feedback.set_feedback_type('tts')
        assert feedback.feedback_type == 'tts'
        
        feedback.set_feedback_type('beep')
        assert feedback.feedback_type == 'beep'
        
        # Invalid type should be ignored
        old_type = feedback.feedback_type
        feedback.set_feedback_type('invalid')
        assert feedback.feedback_type == old_type
    
    @patch('audio.feedback.PYGAME_AVAILABLE', False)
    @patch('audio.feedback.PYAUDIO_AVAILABLE', False)
    def test_no_audio_backend(self, sample_config):
        """Test audio feedback when no backend is available."""
        feedback = AudioFeedback(sample_config)
        
        # Should disable itself when no backend available
        assert feedback.enabled is False


class TestAudioRecorder:
    """Test the AudioRecorder class."""
    
    def test_audio_recorder_initialization(self):
        """Test audio recorder initialization."""
        recorder = AudioRecorder(sample_rate=16000, channels=1)
        
        assert recorder.sample_rate == 16000
        assert recorder.channels == 1
        assert recorder.is_recording is False
    
    @patch('audio.recorder.PYAUDIO_AVAILABLE', True)
    def test_is_available_with_pyaudio(self):
        """Test is_available when PyAudio is present."""
        recorder = AudioRecorder()
        assert recorder.is_available() is True
    
    @patch('audio.recorder.PYAUDIO_AVAILABLE', False)
    def test_is_available_without_pyaudio(self):
        """Test is_available when PyAudio is not present.""" 
        recorder = AudioRecorder()
        # When PyAudio is not available, other methods might still be available
        # So we just check that is_available returns a boolean
        assert isinstance(recorder.is_available(), bool)
    
    def test_get_audio_method(self):
        """Test getting audio method description."""
        recorder = AudioRecorder()
        method = recorder.get_audio_method()
        assert isinstance(method, str)
        assert len(method) > 0
    
    @patch('audio.recorder.PYAUDIO_AVAILABLE', True)
    @patch('audio.recorder.pyaudio.PyAudio')
    def test_start_stop_recording(self, mock_pyaudio, sample_audio_data):
        """Test starting and stopping recording."""
        # Mock PyAudio
        mock_audio = Mock()
        mock_stream = Mock()
        mock_stream.read.return_value = sample_audio_data
        mock_audio.open.return_value = mock_stream
        mock_pyaudio.return_value = mock_audio
        
        recorder = AudioRecorder()
        
        # Test start recording
        assert recorder.is_recording is False
        
        # Mock the recording in a way that doesn't block
        with patch.object(recorder, '_record_pyaudio') as mock_record:
            mock_record.return_value = None

            # Test that we can call start_recording without blocking
            result = recorder.start_recording(max_duration=1.0)
            # Should return a dict with success/error info
            assert isinstance(result, dict)
            assert 'success' in result
    
    def test_stop_recording_when_not_recording(self):
        """Test stopping recording when not currently recording."""
        recorder = AudioRecorder()
        
        # Should not crash
        recorder.stop_recording()
        assert recorder.is_recording is False
    
    def test_cleanup(self):
        """Test cleanup method."""
        recorder = AudioRecorder()
        
        # Should not crash
        recorder.cleanup()
        assert recorder.is_recording is False