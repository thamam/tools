"""
Tests for the configuration management module.
"""

import pytest
import json
from pathlib import Path
from config.settings import ConfigManager


class TestConfigManager:
    """Test the ConfigManager class."""
    
    def test_config_initialization(self, temp_dir):
        """Test config manager initialization."""
        config_file = temp_dir / "test_config.json"
        config = ConfigManager(str(config_file))
        
        assert config is not None
        assert config.config_file == config_file
    
    def test_default_values(self, temp_dir):
        """Test that default values are set correctly."""
        config_file = temp_dir / "test_config.json"
        config = ConfigManager(str(config_file))
        
        # Test some default values
        assert config.get('hotkey_combination') == 'alt+d'
        assert config.get('audio_rate') == 16000
        assert config.get('audio_channels') == 1
        assert config.get('record_seconds') == 30
    
    def test_save_and_load(self, temp_dir):
        """Test saving and loading configuration."""
        config_file = temp_dir / "test_config.json"
        
        # Create and save config
        config1 = ConfigManager(str(config_file))
        config1.set('test_key', 'test_value')
        config1.set('hotkey_combination', 'f12')
        assert config1.save()
        
        # Load config in new instance
        config2 = ConfigManager(str(config_file))
        assert config2.get('test_key') == 'test_value'
        assert config2.get('hotkey_combination') == 'f12'
    
    def test_update_multiple_values(self, temp_dir):
        """Test updating multiple configuration values."""
        config_file = temp_dir / "test_config.json"
        config = ConfigManager(str(config_file))
        
        updates = {
            'window_width': 1200,
            'window_height': 800,
            'auto_copy_to_clipboard': False
        }
        
        config.update(updates)
        
        assert config.get('window_width') == 1200
        assert config.get('window_height') == 800
        assert config.get('auto_copy_to_clipboard') is False
    
    def test_get_all_config(self, temp_dir):
        """Test getting all configuration values."""
        config_file = temp_dir / "test_config.json"
        config = ConfigManager(str(config_file))
        
        all_config = config.get_all()
        
        assert isinstance(all_config, dict)
        assert 'hotkey_combination' in all_config
        assert 'audio_rate' in all_config
        assert 'last_updated' in all_config
    
    def test_corrupted_config_file(self, temp_dir):
        """Test handling of corrupted config file."""
        config_file = temp_dir / "corrupted_config.json"
        
        # Create corrupted JSON file
        with open(config_file, 'w') as f:
            f.write('{ invalid json }')
        
        # Should handle corruption gracefully
        config = ConfigManager(str(config_file))
        assert config.get('hotkey_combination') == 'alt+d'  # Should have defaults