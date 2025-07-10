"""
utils/hotkeys.py - Global hotkey management for the Voice Transcription Tool.

MIGRATION STEP 5A: Create this file

TO MIGRATE from voice_transcription.py, copy these methods:
- setup_hotkeys() → becomes HotkeyManager.register_hotkey()
- update_hotkey() → becomes HotkeyManager.register_hotkey()
- hotkey_toggle_recording() → becomes the callback
- All hotkey validation logic
"""

import logging
from typing import Callable, Optional, List, Dict, Any

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False


class HotkeyManager:
    """Manages global hotkeys."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.registered_hotkey = None
        self.current_combination = None
        self.callback = None
        self.is_active = False
    
    def register_hotkey(self, combination: str, callback: Callable[[], None]) -> bool:
        """
        Register a global hotkey.
        
        MIGRATION: Copy logic from your setup_hotkeys() method here.
        """
        if not KEYBOARD_AVAILABLE:
            self.logger.error("Keyboard library not available")
            return False
        
        try:
            # Remove existing hotkey
            self.unregister_hotkey()
            
            # Validate combination
            if not self.validate_combination(combination):
                self.logger.error(f"Invalid hotkey combination: {combination}")
                return False
            
            # Register new hotkey
            self.registered_hotkey = keyboard.add_hotkey(
                combination,
                callback,
                suppress=False
            )
            
            self.current_combination = combination
            self.callback = callback
            self.logger.info(f"✅ Hotkey registered: {combination}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register hotkey '{combination}': {e}")
            
            # Provide helpful error messages
            if "root" in str(e).lower():
                self.logger.info("💡 Tip: Run with sudo for global hotkeys, or use manual recording")
            elif "already" in str(e).lower():
                self.logger.info("💡 Tip: This hotkey might be in use by another application")
            
            return False
    
    def unregister_hotkey(self) -> None:
        """Unregister the current hotkey."""
        if self.registered_hotkey and KEYBOARD_AVAILABLE:
            try:
                keyboard.remove_hotkey(self.registered_hotkey)
                self.logger.info(f"Hotkey unregistered: {self.current_combination}")
            except Exception as e:
                self.logger.warning(f"Failed to unregister hotkey: {e}")
        
        self.registered_hotkey = None
        self.current_combination = None
        self.callback = None
    
    def set_active(self, active: bool) -> None:
        """Set hotkey activation state."""
        self.is_active = active
        status = "activated" if active else "deactivated"
        self.logger.info(f"Hotkey {status}")
    
    def is_hotkey_active(self) -> bool:
        """Check if hotkeys are active."""
        return self.is_active and self.registered_hotkey is not None
    
    def get_current_combination(self) -> Optional[str]:
        """Get the current hotkey combination."""
        return self.current_combination
    
    def validate_combination(self, combination: str) -> bool:
        """
        Validate a hotkey combination.
        
        MIGRATION: Copy any validation logic from your hotkey updates.
        """
        if not combination:
            return False
        
        # Basic validation - could be expanded
        valid_modifiers = ['ctrl', 'alt', 'shift', 'cmd', 'win']
        valid_keys = ['f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
                     'space', 'tab', 'enter', 'esc', '`', 'capslock']
        
        parts = combination.lower().split('+')
        
        # Single key
        if len(parts) == 1:
            key = parts[0]
            return (key in valid_keys or 
                   (len(key) == 1 and key.isalpha()) or
                   key.isdigit())
        
        # Modifier + key combinations
        modifiers = parts[:-1]
        key = parts[-1]
        
        for modifier in modifiers:
            if modifier not in valid_modifiers:
                return False
        
        return (key in valid_keys or 
               (len(key) == 1 and key.isalpha()) or
               key.isdigit())
    
    def get_recommended_combinations(self) -> List[tuple]:
        """Get a list of recommended hotkey combinations."""
        return [
            ("f9", "F9 - Easy one-handed (recommended)"),
            ("f10", "F10 - One-handed alternative"),
            ("f11", "F11 - One-handed"),
            ("f12", "F12 - One-handed"),
            ("`", "` (backtick) - One-handed, top-left"),
            ("tab", "Tab key - One-handed (may conflict)"),
            ("capslock", "Caps Lock - One-handed (Linux only)"),
            ("ctrl+`", "Ctrl+` - Easy two-handed"),
            ("alt+space", "Alt+Space - Easy two-handed"),
            ("ctrl+alt+v", "Ctrl+Alt+V - Two-handed (gaming safe)"),
            ("ctrl+shift+m", "Ctrl+Shift+M - Two-handed (M for mic)")
        ]
    
    def get_one_handed_combinations(self) -> List[tuple]:
        """Get one-handed hotkey combinations."""
        return [
            ("f9", "F9 - Easy one-handed (recommended)"),
            ("f10", "F10 - One-handed alternative"),
            ("f11", "F11 - One-handed"),
            ("f12", "F12 - One-handed"),
            ("`", "` (backtick) - One-handed, top-left"),
            ("tab", "Tab key - One-handed (may conflict)"),
            ("capslock", "Caps Lock - One-handed (Linux only)")
        ]
    
    def get_two_handed_combinations(self) -> List[tuple]:
        """Get two-handed hotkey combinations."""
        return [
            ("ctrl+`", "Ctrl+` - Easy two-handed"),
            ("alt+space", "Alt+Space - Easy two-handed"),
            ("ctrl+alt+v", "Ctrl+Alt+V - Two-handed (gaming safe)"),
            ("ctrl+shift+m", "Ctrl+Shift+M - Two-handed (M for mic)")
        ]
    
    def is_combination_one_handed(self, combination: str) -> bool:
        """Check if a combination is one-handed."""
        one_handed = [combo[0] for combo in self.get_one_handed_combinations()]
        return combination.lower() in one_handed
    
    def get_status_info(self) -> Dict[str, Any]:
        """Get comprehensive status information."""
        return {
            'available': KEYBOARD_AVAILABLE,
            'registered': self.registered_hotkey is not None,
            'active': self.is_active,
            'current_combination': self.current_combination,
            'one_handed': self.is_combination_one_handed(self.current_combination or ''),
            'callback_set': self.callback is not None
        }
    
    def test_combination(self, combination: str) -> Dict[str, Any]:
        """Test a hotkey combination without registering it."""
        return {
            'valid': self.validate_combination(combination),
            'one_handed': self.is_combination_one_handed(combination),
            'available': KEYBOARD_AVAILABLE,
            'recommended': combination in [c[0] for c in self.get_recommended_combinations()]
        }


# MIGRATION TEST: Test this module independently  
if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from utils.logger import setup_logging
    
    setup_logging()
    
    # Test hotkey manager
    hotkey_manager = HotkeyManager()
    
    print(f"Keyboard available: {'✅' if KEYBOARD_AVAILABLE else '❌'}")
    
    # Test validation
    test_combinations = ['f9', 'ctrl+shift+v', 'invalid+key', '`', 'alt+space']
    print("\nTesting combinations:")
    for combo in test_combinations:
        result = hotkey_manager.test_combination(combo)
        status = "✅" if result['valid'] else "❌"
        one_handed = " (one-handed)" if result['one_handed'] else ""
        print(f"  {status} {combo}{one_handed}")
    
    # Test recommendations
    one_handed = hotkey_manager.get_one_handed_combinations()
    print(f"\nOne-handed options: {len(one_handed)}")
    for combo, desc in one_handed[:3]:  # Show first 3
        print(f"  • {combo}: {desc}")
    
    # Test status
    status = hotkey_manager.get_status_info()
    print(f"\nStatus: {status}")
    
    print("✅ Hotkeys module test completed!")
