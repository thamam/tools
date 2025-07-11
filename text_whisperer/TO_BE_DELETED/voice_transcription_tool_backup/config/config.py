"""
config/settings.py - Configuration management for the Voice Transcription Tool.

MIGRATION STEP 2B: Create this file second (only depends on basic Python)
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_file: str = "voice_transcription_config.json"):
        self.config_file = Path(config_file)
        self.logger = logging.getLogger(__name__)
        self._config = self._load_defaults()
        self.load()
    
    def _load_defaults(self) -> Dict[str, Any]:
        """Load default configuration."""
        return {
            'hotkey_combination': 'f9',
            'current_engine': '',
            'audio_rate': 16000,
            'audio_channels': 1,
            'audio_method': '',
            'window_width': 900,
            'window_height': 800,
            'record_seconds': 30,
            'last_updated': datetime.now().isoformat()
        }
    
    def load(self) -> bool:
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                
                # Merge with defaults (in case new settings were added)
                self._config.update(saved_config)
                self.logger.info(f"Configuration loaded from {self.config_file}")
                return True
            else:
                self.logger.info("No config file found, using defaults")
                return False
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Config file corrupted: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return False
    
    def save(self) -> bool:
        """Save configuration to file."""
        try:
            self._config['last_updated'] = datetime.now().isoformat()
            
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
            
            self.logger.info(f"Configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config[key] = value
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple configuration values."""
        self._config.update(updates)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return self._config.copy()
