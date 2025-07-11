"""
Pytest configuration and fixtures for the Voice Transcription Tool tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_config():
    """Provide a sample configuration dict for testing."""
    return {
        'hotkey_combination': 'f9',
        'current_engine': 'whisper',
        'audio_rate': 16000,
        'audio_channels': 1,
        'window_width': 800,
        'window_height': 600,
        'record_seconds': 30,
        'auto_copy_to_clipboard': True,
        'auto_paste_mode': False,
        'auto_paste_delay': 1.0,
        'audio_feedback_enabled': True,
        'audio_feedback_type': 'beep',
        'audio_feedback_volume': 0.5
    }


@pytest.fixture
def mock_transcription_result():
    """Provide a mock transcription result for testing."""
    return {
        'text': 'This is a test transcription',
        'confidence': 0.95,
        'method': 'whisper'
    }


@pytest.fixture
def sample_audio_data():
    """Provide sample audio data for testing."""
    # Generate simple sine wave data
    import numpy as np
    sample_rate = 16000
    duration = 1.0  # 1 second
    frequency = 440  # A4 note
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = np.sin(frequency * t * 2 * np.pi) * 0.5
    
    # Convert to 16-bit integers
    audio_int16 = (audio_data * 32767).astype(np.int16)
    return audio_int16.tobytes()


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment before each test."""
    # Ensure we're not using real config files during tests
    os.environ['VOICE_TRANSCRIPTION_TEST_MODE'] = '1'
    yield
    # Cleanup
    if 'VOICE_TRANSCRIPTION_TEST_MODE' in os.environ:
        del os.environ['VOICE_TRANSCRIPTION_TEST_MODE']