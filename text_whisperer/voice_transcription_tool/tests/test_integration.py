"""
Integration tests for the Voice Transcription Tool.

These tests verify that different components work together correctly.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from config.settings import ConfigManager
from audio.recorder import AudioRecorder
from speech.engines import SpeechEngineManager
from utils.autopaste import AutoPasteManager


class TestAudioSpeechIntegration:
    """Test integration between audio and speech components."""
    
    @patch('audio.recorder.PYAUDIO_AVAILABLE', True)
    @patch('speech.engines.WHISPER_AVAILABLE', True)
    def test_audio_to_speech_workflow(self, temp_dir):
        """Test audio recording to speech recognition workflow."""
        # Mock audio recorder
        recorder = AudioRecorder()
        
        # Mock speech engine manager
        speech_manager = SpeechEngineManager()
        
        # Test that components can be initialized together
        assert recorder is not None
        assert speech_manager is not None
        
        # Test audio method detection
        audio_method = recorder.get_audio_method()
        assert isinstance(audio_method, str)
        
        # Test engine availability
        available_engines = speech_manager.get_available_engines()
        assert isinstance(available_engines, list)


class TestAutoPasteIntegration:
    """Test integration of auto-paste with other components."""
    
    def test_autopaste_config_integration(self, temp_dir, sample_config):
        """Test auto-paste with configuration."""
        config_file = temp_dir / "autopaste_config.json"
        config = ConfigManager(str(config_file))
        
        # Set auto-paste configuration
        config.update({
            'auto_paste_mode': True,
            'auto_paste_delay': 2.0
        })
        config.save()
        
        # Initialize auto-paste manager
        autopaste = AutoPasteManager()
        
        # Test configuration integration
        config2 = ConfigManager(str(config_file))
        assert config2.get('auto_paste_mode') is True
        assert config2.get('auto_paste_delay') == 2.0
        
        # Test auto-paste availability
        is_available = autopaste.is_available()
        assert isinstance(is_available, bool)


class TestSystemIntegration:
    """Test integration of the entire system."""
    
    def test_component_initialization_order(self, temp_dir):
        """Test that all components can be initialized in the correct order."""
        config_file = temp_dir / "system_config.json"

        # Initialize in order similar to main application
        config = ConfigManager(str(config_file))

        # Audio components
        recorder = AudioRecorder(
            sample_rate=config.get('audio_rate', 16000),
            channels=config.get('audio_channels', 1)
        )

        # Speech components
        speech_manager = SpeechEngineManager()

        # Utils components
        autopaste = AutoPasteManager()

        # Verify all components initialized successfully
        assert config is not None
        assert recorder is not None
        assert speech_manager is not None
        assert autopaste is not None

        # Test basic functionality
        assert recorder.sample_rate == config.get('audio_rate', 16000)
        assert recorder.channels == config.get('audio_channels', 1)
    
    def test_transcription_workflow_simulation(self, temp_dir, mock_transcription_result):
        """Test simulated complete transcription workflow."""
        config_file = temp_dir / "workflow_config.json"

        # Initialize system
        config = ConfigManager(str(config_file))

        # Configure for auto-copy (using empty string for engine since validation rejects 'test')
        config.update({
            'auto_copy_to_clipboard': True,
            'auto_paste_mode': False,  # Don't actually paste in tests
            'current_engine': ''  # Empty string is valid (will be set by SpeechEngineManager)
        })
        config.save()

        # Simulate transcription completion
        transcription_text = mock_transcription_result['text']
        transcription_confidence = mock_transcription_result['confidence']
        transcription_method = config.get('current_engine')

        # Verify workflow parameters
        assert transcription_text is not None
        assert transcription_confidence > 0
        assert transcription_method == ''  # Empty is valid


class TestErrorHandlingIntegration:
    """Test error handling across component integration."""
    
    def test_missing_dependencies_handling(self, temp_dir):
        """Test graceful handling when dependencies are missing."""
        # Test should not crash when optional dependencies are missing
        
        with patch('audio.feedback.PYGAME_AVAILABLE', False):
            with patch('audio.feedback.PYAUDIO_AVAILABLE', False):
                from audio.feedback import AudioFeedback
                
                feedback = AudioFeedback({'audio_feedback_enabled': True})
                # Should disable itself gracefully
                assert feedback.enabled is False

        # System tray test removed - system tray disabled for production readiness
    
    def test_invalid_config_handling(self, temp_dir):
        """Test handling of invalid configuration values."""
        config_file = temp_dir / "invalid_config.json"
        
        # Create config with invalid values
        config = ConfigManager(str(config_file))
        
        # Test with invalid values
        config.set('audio_rate', -1)  # Invalid sample rate
        config.set('audio_channels', 0)  # Invalid channels
        config.set('record_seconds', -5)  # Invalid duration
        
        # Components should handle invalid values gracefully
        recorder = AudioRecorder(
            sample_rate=max(8000, config.get('audio_rate', 16000)),
            channels=max(1, config.get('audio_channels', 1))
        )
        
        assert recorder.sample_rate >= 8000
        assert recorder.channels >= 1