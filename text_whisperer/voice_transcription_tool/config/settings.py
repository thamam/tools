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
            'hotkey_combination': 'alt+d',
            'current_engine': '',
            'audio_rate': 16000,
            'audio_channels': 1,
            'audio_method': '',
            'window_width': 900,
            'window_height': 800,
            'record_seconds': 30,
            # Health monitor defaults
            'health_memory_limit': 1024,  # MB
            'health_cpu_limit': 95,       # Percent
            'health_check_interval': 30,  # Seconds
            'last_updated': datetime.now().isoformat()
        }
    
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate configuration values and reset invalid ones to defaults.

        Args:
            config: Configuration dict to validate

        Returns:
            Validated configuration dict
        """
        defaults = self._load_defaults()
        validated = config.copy()
        warnings = []

        # Validate numeric ranges
        numeric_validations = {
            'audio_rate': (8000, 48000, 'Sample rate'),
            'audio_channels': (1, 2, 'Audio channels'),
            'record_seconds': (1, 300, 'Recording duration'),
            'health_memory_limit': (256, 16384, 'Memory limit (MB)'),
            'health_cpu_limit': (50, 100, 'CPU limit (%)'),
            'health_check_interval': (5, 300, 'Health check interval (seconds)'),
            'window_width': (400, 4000, 'Window width'),
            'window_height': (300, 3000, 'Window height'),
        }

        for key, (min_val, max_val, description) in numeric_validations.items():
            if key in validated:
                value = validated[key]
                try:
                    num_val = float(value)
                    if not (min_val <= num_val <= max_val):
                        warnings.append(
                            f"{description} ({value}) out of range [{min_val}-{max_val}], using default: {defaults[key]}"
                        )
                        validated[key] = defaults[key]
                except (TypeError, ValueError):
                    warnings.append(
                        f"Invalid {description} value: {value}, using default: {defaults[key]}"
                    )
                    validated[key] = defaults[key]

        # Validate string options
        valid_engines = ['whisper', 'google', '']
        if validated.get('current_engine') not in valid_engines:
            warnings.append(
                f"Invalid engine '{validated.get('current_engine')}', using default"
            )
            validated['current_engine'] = defaults['current_engine']

        # Validate hotkey format (basic check)
        hotkey = validated.get('hotkey_combination', '')
        if hotkey and not isinstance(hotkey, str):
            warnings.append(f"Invalid hotkey format, using default: {defaults['hotkey_combination']}")
            validated['hotkey_combination'] = defaults['hotkey_combination']

        # Validate boolean values
        bool_keys = ['auto_paste_mode', 'auto_copy_to_clipboard', 'audio_feedback_enabled']
        for key in bool_keys:
            if key in validated and not isinstance(validated[key], bool):
                warnings.append(f"Invalid boolean value for {key}, using default: {defaults.get(key, False)}")
                validated[key] = defaults.get(key, False)

        # Log all warnings
        for warning in warnings:
            self.logger.warning(f"Config validation: {warning}")

        return validated

    def load(self) -> bool:
        """Load configuration from file with validation."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)

                # Validate loaded config
                saved_config = self._validate_config(saved_config)

                # Merge with defaults (in case new settings were added)
                self._config.update(saved_config)
                self.logger.info(f"Configuration loaded from {self.config_file}")
                return True
            else:
                self.logger.info("No config file found, using defaults")
                return False

        except json.JSONDecodeError as e:
            self.logger.error(f"Config file corrupted: {e}, using defaults")
            # Reset to defaults on corruption
            self._config = self._load_defaults()
            return False
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}, using defaults")
            self._config = self._load_defaults()
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
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set a configuration value with validation.

        Args:
            key: Configuration key
            value: Value to set

        Returns:
            True if value was set, False if validation failed
        """
        # Create temp config with new value
        temp_config = self._config.copy()
        temp_config[key] = value

        # Validate
        validated = self._validate_config({key: value})

        # Check if value was changed by validation
        if validated.get(key) != value:
            self.logger.warning(f"Value for '{key}' was rejected by validation")
            return False

        self._config[key] = value
        return True
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple configuration values with validation."""
        # Validate all updates
        validated_updates = self._validate_config(updates)
        self._config.update(validated_updates)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return self._config.copy()
