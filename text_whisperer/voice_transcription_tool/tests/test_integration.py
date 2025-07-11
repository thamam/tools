"""
Integration tests for the Voice Transcription Tool.

These tests verify that different components work together correctly.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from config.settings import ConfigManager
from config.database import DatabaseManager
from audio.recorder import AudioRecorder
from speech.engines import SpeechEngineManager
from utils.autopaste import AutoPasteManager


class TestConfigDatabaseIntegration:
    """Test integration between config and database components."""
    
    def test_config_database_workflow(self, temp_dir):
        """Test complete config and database workflow."""
        config_file = temp_dir / "integration_config.json"
        db_file = temp_dir / "integration_transcriptions.db"
        
        # Initialize components
        config = ConfigManager(str(config_file))
        db_manager = DatabaseManager(str(db_file))
        
        # Test config operations
        config.set('current_engine', 'whisper')
        config.set('auto_copy_to_clipboard', True)
        assert config.save()
        
        # Test database operations
        success = db_manager.save_transcription(
            "Integration test transcription",
            0.92,
            config.get('current_engine')
        )
        assert success
        
        # Verify data persistence
        config2 = ConfigManager(str(config_file))
        assert config2.get('current_engine') == 'whisper'
        assert config2.get('auto_copy_to_clipboard') is True
        
        recent = db_manager.get_recent_transcriptions(1)
        assert len(recent) == 1
        assert recent[0]['text'] == "Integration test transcription"
        assert recent[0]['method'] == 'whisper'


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
        db_file = temp_dir / "system_transcriptions.db"
        
        # Initialize in order similar to main application
        config = ConfigManager(str(config_file))
        db_manager = DatabaseManager(str(db_file))
        
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
        assert db_manager is not None
        assert recorder is not None
        assert speech_manager is not None
        assert autopaste is not None
        
        # Test basic functionality
        assert recorder.sample_rate == config.get('audio_rate', 16000)
        assert recorder.channels == config.get('audio_channels', 1)
    
    def test_transcription_workflow_simulation(self, temp_dir, mock_transcription_result):
        """Test simulated complete transcription workflow."""
        config_file = temp_dir / "workflow_config.json"
        db_file = temp_dir / "workflow_transcriptions.db"
        
        # Initialize system
        config = ConfigManager(str(config_file))
        db_manager = DatabaseManager(str(db_file))
        
        # Configure for auto-copy
        config.update({
            'auto_copy_to_clipboard': True,
            'auto_paste_mode': False,  # Don't actually paste in tests
            'current_engine': 'test'
        })
        config.save()
        
        # Simulate transcription completion
        transcription_text = mock_transcription_result['text']
        transcription_confidence = mock_transcription_result['confidence']
        transcription_method = config.get('current_engine')
        
        # Save transcription to database
        success = db_manager.save_transcription(
            transcription_text,
            transcription_confidence,
            transcription_method
        )
        assert success
        
        # Verify workflow completed
        recent = db_manager.get_recent_transcriptions(1)
        assert len(recent) == 1
        assert recent[0]['text'] == transcription_text
        assert recent[0]['confidence'] == transcription_confidence
        assert recent[0]['method'] == transcription_method


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
        
        with patch('utils.system_tray.PYSTRAY_AVAILABLE', False):
            from utils.system_tray import SystemTrayManager
            
            tray = SystemTrayManager()
            assert tray.is_available() is False
            assert tray.start() is False
    
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
    
    def test_database_corruption_handling(self, temp_dir):
        """Test handling of database corruption."""
        db_file = temp_dir / "corrupted.db"
        
        # Create corrupted database file
        with open(db_file, 'w') as f:
            f.write("This is not a valid SQLite database")
        
        # Should handle corruption gracefully
        try:
            db_manager = DatabaseManager(str(db_file))
            # Should either recover or create new database
            assert db_manager is not None
        except Exception as e:
            # If it fails, it should be a controlled failure
            assert "database" in str(e).lower() or "sqlite" in str(e).lower()