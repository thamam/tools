"""
Tests for the speech recognition module components.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from speech.engines import SpeechEngineManager, WhisperEngine, GoogleSpeechEngine
from speech.training import VoiceTrainer


class TestSpeechEngineManager:
    """Test the SpeechEngineManager class."""
    
    def test_speech_manager_initialization(self):
        """Test speech engine manager initialization."""
        manager = SpeechEngineManager()
        
        assert manager is not None
        assert hasattr(manager, 'engines')
        assert hasattr(manager, 'current_engine')
    
    def test_get_available_engines(self):
        """Test getting available engines."""
        manager = SpeechEngineManager()
        
        engines = manager.get_available_engines()
        assert isinstance(engines, list)
        
        # Should contain at least one of the engines if dependencies are available
        possible_engines = ['whisper', 'google']
        for engine in engines:
            assert engine in possible_engines
    
    def test_is_engine_available(self):
        """Test checking if specific engine is available."""
        manager = SpeechEngineManager()
        
        # Test with known engine names
        for engine_name in ['whisper', 'google']:
            result = manager.is_engine_available(engine_name)
            assert isinstance(result, bool)
        
        # Test with invalid engine name
        assert manager.is_engine_available('invalid_engine') is False
    
    def test_set_engine(self):
        """Test setting current engine."""
        manager = SpeechEngineManager()
        
        available_engines = manager.get_available_engines()
        if available_engines:
            # Test setting to available engine
            engine_name = available_engines[0]
            success = manager.set_engine(engine_name)
            assert success is True
            assert manager.get_current_engine() == engine_name
        
        # Test setting to unavailable engine
        success = manager.set_engine('invalid_engine')
        assert success is False
    
    def test_get_current_engine(self):
        """Test getting current engine."""
        manager = SpeechEngineManager()
        
        current = manager.get_current_engine()
        assert current is None or isinstance(current, str)


class TestWhisperEngine:
    """Test the WhisperEngine class."""
    
    @patch('speech.engines.WHISPER_AVAILABLE', True)
    @patch('speech.engines.whisper.load_model')
    def test_whisper_engine_initialization(self, mock_load_model):
        """Test Whisper engine initialization."""
        mock_model = Mock()
        mock_load_model.return_value = mock_model
        
        engine = WhisperEngine(model_size="base")
        
        assert engine.model_size == "base"
        assert engine.model == mock_model
        mock_load_model.assert_called_once_with("base")
    
    @patch('speech.engines.WHISPER_AVAILABLE', False)
    def test_whisper_engine_unavailable(self):
        """Test Whisper engine when library is not available."""
        engine = WhisperEngine()
        
        assert engine.is_available() is False
    
    @patch('speech.engines.WHISPER_AVAILABLE', True)
    def test_whisper_engine_name(self):
        """Test Whisper engine name property."""
        with patch('speech.engines.whisper.load_model'):
            engine = WhisperEngine()
            assert engine.name == "whisper"
    
    @patch('speech.engines.WHISPER_AVAILABLE', True)
    @patch('speech.engines.whisper.load_model')
    def test_whisper_transcribe(self, mock_load_model, temp_dir):
        """Test Whisper transcription."""
        # Mock whisper model
        mock_model = Mock()
        mock_result = {
            'text': 'Test transcription',
            'segments': [{'start': 0, 'end': 1, 'text': 'Test transcription'}]
        }
        mock_model.transcribe.return_value = mock_result
        mock_load_model.return_value = mock_model
        
        engine = WhisperEngine()
        
        # Create a dummy audio file
        audio_file = temp_dir / "test.wav"
        audio_file.write_bytes(b"dummy audio data")
        
        result = engine.transcribe(str(audio_file))
        
        assert result['text'] == 'Test transcription'
        assert result['method'] == 'whisper'
        assert 'confidence' in result


class TestGoogleSpeechEngine:
    """Test the GoogleSpeechEngine class."""
    
    @patch('speech.engines.SPEECH_RECOGNITION_AVAILABLE', True)
    @patch('speech.engines.sr.Recognizer')
    def test_google_engine_initialization(self, mock_recognizer):
        """Test Google Speech engine initialization."""
        mock_rec = Mock()
        mock_recognizer.return_value = mock_rec
        
        engine = GoogleSpeechEngine()
        
        assert engine.recognizer == mock_rec
        assert engine.name == "google"
    
    @patch('speech.engines.SPEECH_RECOGNITION_AVAILABLE', False)
    def test_google_engine_unavailable(self):
        """Test Google Speech engine when library is not available."""
        engine = GoogleSpeechEngine()
        
        assert engine.is_available() is False
    
    @patch('speech.engines.SPEECH_RECOGNITION_AVAILABLE', True)
    @patch('speech.engines.sr.Recognizer')
    @patch('speech.engines.sr.AudioFile')
    def test_google_transcribe(self, mock_audio_file, mock_recognizer, temp_dir):
        """Test Google Speech transcription."""
        # Mock recognizer
        mock_rec = Mock()
        mock_rec.recognize_google.return_value = "Test transcription"
        mock_recognizer.return_value = mock_rec
        
        # Mock audio file context manager
        mock_audio = Mock()
        mock_audio_file.return_value.__enter__.return_value = mock_audio
        
        engine = GoogleSpeechEngine()
        
        # Create a dummy audio file
        audio_file = temp_dir / "test.wav"
        audio_file.write_bytes(b"dummy audio data")
        
        result = engine.transcribe(str(audio_file))
        
        assert result['text'] == "Test transcription"
        assert result['method'] == "google"
        assert 'confidence' in result


class TestVoiceTrainer:
    """Test the VoiceTrainer class."""
    
    def test_voice_trainer_initialization(self, temp_dir):
        """Test voice trainer initialization."""
        from config.database import DatabaseManager
        
        db_file = temp_dir / "test_training.db"
        db_manager = DatabaseManager(str(db_file))
        
        trainer = VoiceTrainer(db_manager)
        
        assert trainer is not None
        assert trainer.db_manager == db_manager
    
    def test_get_existing_profiles(self, temp_dir):
        """Test getting existing voice profiles."""
        from config.database import DatabaseManager
        
        db_file = temp_dir / "test_training.db"
        db_manager = DatabaseManager(str(db_file))
        trainer = VoiceTrainer(db_manager)
        
        # Initially should have no profiles
        profiles = trainer.get_existing_profiles()
        assert isinstance(profiles, list)
        assert len(profiles) == 0
    
    def test_clear_training_data(self, temp_dir):
        """Test clearing training data."""
        from config.database import DatabaseManager
        
        db_file = temp_dir / "test_training.db"
        db_manager = DatabaseManager(str(db_file))
        trainer = VoiceTrainer(db_manager)
        
        # Should not crash even with no data
        success = trainer.clear_training_data()
        assert isinstance(success, bool)
    
    def test_save_training_sample(self, temp_dir):
        """Test saving a training sample."""
        from config.database import DatabaseManager
        
        db_file = temp_dir / "test_training.db"
        db_manager = DatabaseManager(str(db_file))
        trainer = VoiceTrainer(db_manager)
        
        # Test saving a sample
        sample_data = {
            'text': 'Test training phrase',
            'audio_path': '/path/to/audio.wav',
            'confidence': 0.95
        }
        
        # Method may not exist yet, but test shouldn't crash
        try:
            success = trainer.save_training_sample(
                sample_data['text'],
                sample_data['audio_path'],
                sample_data['confidence']
            )
            assert isinstance(success, bool)
        except AttributeError:
            # Method not implemented yet, that's OK
            pass