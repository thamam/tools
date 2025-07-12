"""
utils/hotkeys_new.py - New hotkey manager using pynput (no sudo required)

This replaces the keyboard library which requires root access on Linux.
Pynput uses X11 integration and works without sudo.
"""

import logging
from typing import Optional, Callable, Dict, List, Any
import threading

try:
    from pynput import keyboard
    from pynput.keyboard import Key, KeyCode
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False


class HotkeyManager:
    """Manages global hotkeys using pynput (no sudo required)."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.hotkey_listener = None
        self.registered_hotkeys = {}  # Dict of combination -> callback
        self.is_active = False
        
        if not PYNPUT_AVAILABLE:
            self.logger.warning("pynput not available - hotkeys disabled")
            self.logger.info("💡 Install with: pip install pynput")
    
    def register_hotkey(self, combination: str, callback: Callable[[], None]) -> bool:
        """
        Register a single hotkey.
        
        Args:
            combination: Hotkey combination (e.g., 'alt+d', 'ctrl+shift+f')
            callback: Function to call when hotkey is pressed
            
        Returns:
            bool: True if registration successful
        """
        if not PYNPUT_AVAILABLE:
            self.logger.error("pynput not available for hotkey registration")
            return False
        
        try:
            # Convert combination to pynput format
            pynput_combo = self._convert_combination(combination)
            if not pynput_combo:
                self.logger.error(f"Invalid hotkey combination: {combination}")
                return False
            
            # Store the callback
            self.registered_hotkeys[combination] = callback
            
            # Restart listener with new hotkeys
            self._restart_listener()
            
            self.logger.info(f"✅ Hotkey registered: {combination}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register hotkey {combination}: {e}")
            return False
    
    def register_multiple_hotkeys(self, hotkey_map: Dict[str, Callable[[], None]]) -> Dict[str, bool]:
        """Register multiple hotkeys at once."""
        results = {}
        for combination, callback in hotkey_map.items():
            results[combination] = self.register_hotkey(combination, callback)
        return results
    
    def unregister_hotkey(self, combination: Optional[str] = None) -> None:
        """Unregister hotkey(s)."""
        if combination:
            if combination in self.registered_hotkeys:
                del self.registered_hotkeys[combination]
                self._restart_listener()
                self.logger.info(f"Hotkey unregistered: {combination}")
        else:
            # Unregister all
            self.registered_hotkeys.clear()
            self._stop_listener()
            self.logger.info("All hotkeys unregistered")
    
    def _convert_combination(self, combination: str) -> Optional[str]:
        """Convert string combination to pynput string format."""
        try:
            # Parse combination like 'alt+d', 'ctrl+shift+f9', or 'f9'
            parts = combination.lower().split('+')
            if len(parts) < 1:
                return None
            
            # Build pynput string format like '<alt>+d' or '<ctrl>+<shift>+f9'
            pynput_parts = []
            
            # Handle single key (no modifiers) vs key with modifiers
            if len(parts) == 1:
                # Single key like 'f9'
                key_part = parts[0]
            else:
                # Process modifiers
                for modifier in parts[:-1]:
                    if modifier in ['ctrl', 'alt', 'shift', 'cmd']:
                        pynput_parts.append(f'<{modifier}>')
                    else:
                        self.logger.warning(f"Unknown modifier: {modifier}")
                        return None
                
                # Process key
                key_part = parts[-1]
            
            # Special key mappings for pynput format
            special_keys = {
                'space': '<space>',
                'enter': '<enter>',
                'tab': '<tab>',
                'esc': '<esc>',
                'escape': '<esc>',
                'backspace': '<backspace>',
                'delete': '<delete>',
                'up': '<up>',
                'down': '<down>', 
                'left': '<left>',
                'right': '<right>',
                'home': '<home>',
                'end': '<end>',
                'page_up': '<page_up>',
                'page_down': '<page_down>',
            }
            
            if key_part in special_keys:
                pynput_parts.append(special_keys[key_part])
            elif key_part.startswith('f') and key_part[1:].isdigit():
                # Function keys
                fn_num = int(key_part[1:])
                if 1 <= fn_num <= 12:
                    pynput_parts.append(f'<{key_part}>')
                else:
                    return None
            elif len(key_part) == 1:
                # Single character - no brackets needed
                pynput_parts.append(key_part)
            else:
                self.logger.error(f"Unknown key: {key_part}")
                return None
            
            return '+'.join(pynput_parts)
            
        except Exception as e:
            self.logger.error(f"Error converting combination {combination}: {e}")
            return None
    
    def _restart_listener(self):
        """Restart the hotkey listener with current hotkeys."""
        self._stop_listener()
        
        if not self.registered_hotkeys:
            return
        
        try:
            # Build hotkey dict for pynput
            hotkey_dict = {}
            for combination, callback in self.registered_hotkeys.items():
                pynput_combo = self._convert_combination(combination)
                if pynput_combo:
                    # pynput_combo is a string like '<alt>+d'
                    hotkey_dict[pynput_combo] = callback
            
            if hotkey_dict:
                self.hotkey_listener = keyboard.GlobalHotKeys(hotkey_dict)
                self.hotkey_listener.start()
                self.is_active = True
                self.logger.debug(f"Hotkey listener started with {len(hotkey_dict)} hotkeys")
            
        except Exception as e:
            self.logger.error(f"Failed to start hotkey listener: {e}")
            self.is_active = False
    
    def _stop_listener(self):
        """Stop the hotkey listener."""
        if self.hotkey_listener:
            try:
                self.hotkey_listener.stop()
                self.hotkey_listener = None
                self.is_active = False
                self.logger.debug("Hotkey listener stopped")
            except Exception as e:
                self.logger.error(f"Error stopping hotkey listener: {e}")
    
    def set_active(self, active: bool) -> None:
        """Set hotkey activation state."""
        if active and not self.is_active:
            self._restart_listener()
        elif not active and self.is_active:
            self._stop_listener()
    
    def is_hotkey_active(self) -> bool:
        """Check if hotkeys are active."""
        return self.is_active and len(self.registered_hotkeys) > 0
    
    def get_registered_combinations(self) -> List[str]:
        """Get all registered hotkey combinations."""
        return list(self.registered_hotkeys.keys())
    
    def get_current_combination(self) -> Optional[str]:
        """Get the primary hotkey combination (for backward compatibility)."""
        combinations = self.get_registered_combinations()
        return combinations[0] if combinations else None
    
    def validate_combination(self, combination: str) -> bool:
        """Validate a hotkey combination format."""
        return self._convert_combination(combination) is not None
    
    def get_one_handed_combinations(self) -> List[tuple]:
        """Get one-handed hotkey combinations."""
        return [
            ("alt+d", "Alt+D - Record/Stop (recommended)"),
            ("alt+s", "Alt+S - Settings"),
            ("alt+w", "Alt+W - Wake word toggle"),
            ("f9", "F9 - Easy one-handed"),
            ("f10", "F10 - One-handed alternative"),
            ("f11", "F11 - One-handed"),
            ("f12", "F12 - One-handed"),
            ("ctrl+space", "Ctrl+Space - Easy reach"),
        ]
    
    def get_two_handed_combinations(self) -> List[tuple]:
        """Get two-handed hotkey combinations."""
        return [
            ("ctrl+shift+r", "Ctrl+Shift+R - Record"),
            ("ctrl+shift+s", "Ctrl+Shift+S - Settings"),
            ("ctrl+alt+v", "Ctrl+Alt+V - Voice"),
            ("ctrl+alt+r", "Ctrl+Alt+R - Record"),
        ]
    
    def get_recommended_combinations(self) -> List[tuple]:
        """Get recommended hotkey combinations."""
        return [
            ("alt+d", "Alt+D - Record/Stop (recommended)"),
            ("alt+s", "Alt+S - Settings"),
            ("alt+w", "Alt+W - Wake word toggle"),
            ("f9", "F9 - Easy one-handed"),
            ("ctrl+space", "Ctrl+Space - Easy reach"),
        ]
    
    def is_combination_one_handed(self, combination: str) -> bool:
        """Check if a combination is one-handed."""
        one_handed = [combo[0] for combo in self.get_one_handed_combinations()]
        return combination.lower() in one_handed
    
    def get_status_info(self) -> Dict[str, Any]:
        """Get comprehensive status information."""
        current_combo = self.get_current_combination()
        return {
            'available': PYNPUT_AVAILABLE,
            'registered': len(self.registered_hotkeys) > 0,
            'active': self.is_active,
            'current_combination': current_combo,
            'one_handed': self.is_combination_one_handed(current_combo or ''),
            'callback_set': len(self.registered_hotkeys) > 0,
            'library': 'pynput' if PYNPUT_AVAILABLE else 'none',
            'sudo_required': False  # pynput doesn't need sudo!
        }
    
    def test_combination(self, combination: str) -> Dict[str, Any]:
        """Test a hotkey combination without registering it."""
        return {
            'valid': self.validate_combination(combination),
            'available': PYNPUT_AVAILABLE,
            'sudo_required': False,
            'converted': self._convert_combination(combination) is not None
        }