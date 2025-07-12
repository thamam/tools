"""
utils/hotkeys_pynput.py - Global hotkey management using pynput for the Voice Transcription Tool.

This is an improved version that uses pynput instead of the 'keyboard' library to avoid
the "must be root" error on Linux. Works without sudo on X11 systems.

Key improvements:
- Uses pynput.keyboard.GlobalHotKeys for cross-platform compatibility
- No sudo/root required on Linux X11 systems
- Better error handling and fallback mechanisms
- Maintains same API as original HotkeyManager for easy replacement
"""

import logging
import threading
import time
from typing import Callable, Optional, List, Dict, Any

try:
    from pynput import keyboard as pynput_keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

# Fallback to original keyboard library if pynput not available
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False


class HotkeyManagerPynput:
    """
    Manages global hotkeys using pynput library.
    
    This class provides the same interface as the original HotkeyManager
    but uses pynput instead of the keyboard library to avoid sudo requirements.
    """
    
    def __init__(self, prefer_pynput: bool = True):
        self.logger = logging.getLogger(__name__)
        self.prefer_pynput = prefer_pynput
        self.registered_hotkeys = {}  # Dict of combination -> callback
        self.is_active = False
        self._global_hotkeys = None
        self._hotkey_thread = None
        
        # Determine which backend to use
        self.backend = self._select_backend()
        self.logger.info(f"HotkeyManager using backend: {self.backend}")
    
    def _select_backend(self) -> str:
        """Select the best available backend."""
        if self.prefer_pynput and PYNPUT_AVAILABLE:
            return "pynput"
        elif KEYBOARD_AVAILABLE:
            return "keyboard"
        elif PYNPUT_AVAILABLE:
            return "pynput"
        else:
            return "none"
    
    def register_hotkey(self, combination: str, callback: Callable[[], None]) -> bool:
        """
        Register a global hotkey.
        
        Args:
            combination: Hotkey combination (e.g., 'f9', 'ctrl+alt+r')
            callback: Function to call when hotkey is pressed
            
        Returns:
            True if hotkey was registered successfully, False otherwise
        """
        if self.backend == "none":
            self.logger.error("No hotkey backend available")
            return False
        
        # Validate combination
        if not self.validate_combination(combination):
            self.logger.error(f"Invalid hotkey combination: {combination}")
            return False
        
        try:
            # Remove existing hotkey for this combination if any
            if combination in self.registered_hotkeys:
                self.unregister_hotkey(combination)
            
            if self.backend == "pynput":
                return self._register_pynput_hotkey(combination, callback)
            elif self.backend == "keyboard":
                return self._register_keyboard_hotkey(combination, callback)
            
        except Exception as e:
            self.logger.error(f"Failed to register hotkey '{combination}': {e}")
            
            # Provide helpful error messages
            if "root" in str(e).lower():
                self.logger.info("💡 Tip: Try installing pynput: pip install pynput")
            elif "display" in str(e).lower():
                self.logger.info("💡 Tip: Make sure DISPLAY environment variable is set")
            
            return False
    
    def _register_pynput_hotkey(self, combination: str, callback: Callable[[], None]) -> bool:
        """Register hotkey using pynput backend."""
        try:
            # Convert combination to pynput format
            pynput_combination = self._convert_to_pynput_format(combination)
            
            # Store the callback
            self.registered_hotkeys[combination] = callback
            
            # Create new GlobalHotKeys instance with all registered hotkeys
            hotkey_map = {}
            for combo, cb in self.registered_hotkeys.items():
                pynput_combo = self._convert_to_pynput_format(combo)
                hotkey_map[pynput_combo] = cb
            
            # Stop existing hotkeys if any
            if self._global_hotkeys:
                self._global_hotkeys.stop()
            
            # Create and start new hotkeys
            self._global_hotkeys = pynput_keyboard.GlobalHotKeys(hotkey_map)
            self._global_hotkeys.start()
            
            self.logger.info(f"✅ Hotkey registered (pynput): {combination}")
            return True
            
        except Exception as e:
            self.logger.error(f"Pynput hotkey registration failed: {e}")
            return False
    
    def _register_keyboard_hotkey(self, combination: str, callback: Callable[[], None]) -> bool:
        """Register hotkey using keyboard backend (fallback)."""
        try:
            # Register using keyboard library
            hotkey_id = keyboard.add_hotkey(combination, callback, suppress=False)
            self.registered_hotkeys[combination] = callback
            
            self.logger.info(f"✅ Hotkey registered (keyboard): {combination}")
            return True
            
        except Exception as e:
            self.logger.error(f"Keyboard hotkey registration failed: {e}")
            return False
    
    def _convert_to_pynput_format(self, combination: str) -> str:
        """
        Convert standard hotkey format to pynput format.
        
        Examples:
            'f9' -> '<f9>'
            'ctrl+alt+r' -> '<ctrl>+<alt>+r'
            'alt+space' -> '<alt>+<space>'
        """
        parts = combination.lower().split('+')
        pynput_parts = []
        
        for part in parts:
            part = part.strip()
            
            # Map common key names
            key_mapping = {
                'ctrl': 'ctrl',
                'control': 'ctrl',
                'alt': 'alt',
                'shift': 'shift',
                'cmd': 'cmd',
                'win': 'cmd',
                'windows': 'cmd',
                'space': 'space',
                'tab': 'tab',
                'enter': 'enter',
                'return': 'enter',
                'esc': 'esc',
                'escape': 'esc',
                'backspace': 'backspace',
                'delete': 'delete',
                'capslock': 'caps_lock',
                'caps': 'caps_lock',
            }
            
            # Function keys
            if part.startswith('f') and part[1:].isdigit():
                pynput_parts.append(f'<{part}>')
            # Mapped keys
            elif part in key_mapping:
                pynput_parts.append(f'<{key_mapping[part]}>')
            # Single character keys
            elif len(part) == 1 and part.isalpha():
                pynput_parts.append(part)
            # Number keys
            elif part.isdigit():
                pynput_parts.append(part)
            # Special characters
            else:
                pynput_parts.append(f'<{part}>')
        
        return '+'.join(pynput_parts)
    
    def unregister_hotkey(self, combination: Optional[str] = None) -> None:
        """Unregister hotkey(s)."""
        if self.backend == "none":
            return
        
        if combination:
            # Unregister specific hotkey
            if combination in self.registered_hotkeys:
                if self.backend == "pynput":
                    # Remove from dict and recreate GlobalHotKeys
                    del self.registered_hotkeys[combination]
                    if self.registered_hotkeys:
                        # Recreate with remaining hotkeys
                        self._recreate_pynput_hotkeys()
                    else:
                        # No more hotkeys, stop the listener
                        if self._global_hotkeys:
                            self._global_hotkeys.stop()
                            self._global_hotkeys = None
                elif self.backend == "keyboard":
                    # For keyboard backend, we can't easily remove individual hotkeys
                    # so we'll need to clear all and re-register the rest
                    keyboard.unhook_all_hotkeys()
                    del self.registered_hotkeys[combination]
                    # Re-register remaining hotkeys
                    for combo, callback in self.registered_hotkeys.items():
                        keyboard.add_hotkey(combo, callback, suppress=False)
                
                self.logger.info(f"Hotkey unregistered: {combination}")
        else:
            # Unregister all hotkeys
            if self.backend == "pynput" and self._global_hotkeys:
                self._global_hotkeys.stop()
                self._global_hotkeys = None
            elif self.backend == "keyboard":
                keyboard.unhook_all_hotkeys()
            
            self.registered_hotkeys.clear()
            self.logger.info("All hotkeys unregistered")
    
    def _recreate_pynput_hotkeys(self):
        """Recreate pynput GlobalHotKeys with current registered hotkeys."""
        if not self.registered_hotkeys:
            return
        
        try:
            # Stop existing
            if self._global_hotkeys:
                self._global_hotkeys.stop()
            
            # Create new hotkey map
            hotkey_map = {}
            for combo, callback in self.registered_hotkeys.items():
                pynput_combo = self._convert_to_pynput_format(combo)
                hotkey_map[pynput_combo] = callback
            
            # Start new GlobalHotKeys
            self._global_hotkeys = pynput_keyboard.GlobalHotKeys(hotkey_map)
            self._global_hotkeys.start()
            
        except Exception as e:
            self.logger.error(f"Failed to recreate pynput hotkeys: {e}")
    
    def register_multiple_hotkeys(self, hotkey_map: Dict[str, Callable[[], None]]) -> Dict[str, bool]:
        """Register multiple hotkeys at once."""
        results = {}
        for combination, callback in hotkey_map.items():
            results[combination] = self.register_hotkey(combination, callback)
        return results
    
    def set_active(self, active: bool) -> None:
        """Set hotkey activation state."""
        self.is_active = active
        status = "activated" if active else "deactivated"
        self.logger.info(f"Hotkey {status}")
    
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
        """Validate a hotkey combination."""
        if not combination:
            return False
        
        # Basic validation - could be expanded
        valid_modifiers = ['ctrl', 'control', 'alt', 'shift', 'cmd', 'win', 'windows']
        valid_keys = ['f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
                     'space', 'tab', 'enter', 'return', 'esc', 'escape', 'backspace', 'delete',
                     '`', 'capslock', 'caps']
        
        parts = combination.lower().split('+')
        
        # Single key
        if len(parts) == 1:
            key = parts[0].strip()
            return (key in valid_keys or 
                   (len(key) == 1 and key.isalpha()) or
                   key.isdigit())
        
        # Modifier + key combinations
        modifiers = [p.strip() for p in parts[:-1]]
        key = parts[-1].strip()
        
        for modifier in modifiers:
            if modifier not in valid_modifiers:
                return False
        
        return (key in valid_keys or 
               (len(key) == 1 and key.isalpha()) or
               key.isdigit())
    
    def get_recommended_combinations(self) -> List[tuple]:
        """Get a list of recommended hotkey combinations."""
        return [
            ("f9", "F9 - Easy one-handed (recommended for pynput)"),
            ("f10", "F10 - One-handed alternative"),
            ("f11", "F11 - One-handed"),
            ("f12", "F12 - One-handed"),
            ("ctrl+alt+r", "Ctrl+Alt+R - Record toggle"),
            ("ctrl+alt+s", "Ctrl+Alt+S - Settings"),
            ("ctrl+alt+w", "Ctrl+Alt+W - Wake word toggle"),
            ("alt+space", "Alt+Space - Easy two-handed"),
            ("ctrl+shift+m", "Ctrl+Shift+M - Two-handed (M for mic)"),
            ("`", "` (backtick) - One-handed, top-left"),
        ]
    
    def get_one_handed_combinations(self) -> List[tuple]:
        """Get one-handed hotkey combinations."""
        return [
            ("f9", "F9 - Easy one-handed (recommended)"),
            ("f10", "F10 - One-handed alternative"),
            ("f11", "F11 - One-handed"),
            ("f12", "F12 - One-handed"),
            ("`", "` (backtick) - One-handed, top-left"),
        ]
    
    def get_two_handed_combinations(self) -> List[tuple]:
        """Get two-handed hotkey combinations."""
        return [
            ("ctrl+alt+r", "Ctrl+Alt+R - Record toggle"),
            ("ctrl+alt+s", "Ctrl+Alt+S - Settings"),
            ("alt+space", "Alt+Space - Easy two-handed"),
            ("ctrl+shift+m", "Ctrl+Shift+M - Two-handed (M for mic)")
        ]
    
    def is_combination_one_handed(self, combination: str) -> bool:
        """Check if a combination is one-handed."""
        one_handed = [combo[0] for combo in self.get_one_handed_combinations()]
        return combination.lower() in one_handed
    
    def get_status_info(self) -> Dict[str, Any]:
        """Get comprehensive status information."""
        current_combo = self.get_current_combination()
        return {
            'backend': self.backend,
            'available': self.backend != "none",
            'registered': len(self.registered_hotkeys) > 0,
            'active': self.is_active,
            'current_combination': current_combo,
            'one_handed': self.is_combination_one_handed(current_combo or ''),
            'callback_set': len(self.registered_hotkeys) > 0,
            'pynput_available': PYNPUT_AVAILABLE,
            'keyboard_available': KEYBOARD_AVAILABLE
        }
    
    def test_combination(self, combination: str) -> Dict[str, Any]:
        """Test a hotkey combination without registering it."""
        return {
            'valid': self.validate_combination(combination),
            'one_handed': self.is_combination_one_handed(combination),
            'available': self.backend != "none",
            'recommended': combination in [c[0] for c in self.get_recommended_combinations()],
            'pynput_format': self._convert_to_pynput_format(combination) if PYNPUT_AVAILABLE else None
        }
    
    def cleanup(self):
        """Clean up resources when shutting down."""
        self.unregister_hotkey()  # Unregister all hotkeys
        if self._global_hotkeys:
            try:
                self._global_hotkeys.stop()
            except:
                pass
            self._global_hotkeys = None


# Backward compatibility - use the new implementation by default
HotkeyManager = HotkeyManagerPynput


# Test and demonstration
if __name__ == "__main__":
    import sys
    import os
    sys.path.append('..')
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    print("🔍 Testing HotkeyManagerPynput")
    print("=" * 50)
    
    # Create manager
    hotkey_manager = HotkeyManagerPynput()
    
    # Print status
    status = hotkey_manager.get_status_info()
    print(f"Backend: {status['backend']}")
    print(f"Available: {status['available']}")
    print(f"Pynput available: {status['pynput_available']}")
    print(f"Keyboard available: {status['keyboard_available']}")
    
    if not status['available']:
        print("❌ No hotkey backend available!")
        print("💡 Install pynput: pip install pynput")
        sys.exit(1)
    
    # Test validation
    print(f"\n📝 Testing combinations:")
    test_combinations = ['f9', 'ctrl+alt+r', 'invalid+key', '`', 'alt+space']
    for combo in test_combinations:
        result = hotkey_manager.test_combination(combo)
        status_icon = "✅" if result['valid'] else "❌"
        one_handed = " (one-handed)" if result['one_handed'] else ""
        pynput_format = f" -> {result['pynput_format']}" if result['pynput_format'] else ""
        print(f"  {status_icon} {combo}{one_handed}{pynput_format}")
    
    # Test recommendations
    print(f"\n💡 Recommended combinations:")
    for combo, desc in hotkey_manager.get_recommended_combinations()[:5]:  # Show first 5
        print(f"  • {combo}: {desc}")
    
    # Interactive test if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        print(f"\n🎯 Interactive test - Press F9 or Ctrl+Alt+Q to test hotkeys")
        print("   Press Ctrl+C to exit")
        
        def test_f9():
            print("🎉 F9 hotkey triggered!")
        
        def test_exit():
            print("🛑 Exit hotkey triggered!")
            hotkey_manager.cleanup()
            sys.exit(0)
        
        # Register test hotkeys
        success = hotkey_manager.register_multiple_hotkeys({
            'f9': test_f9,
            'ctrl+alt+q': test_exit
        })
        
        print(f"Registration results: {success}")
        
        if any(success.values()):
            print("✅ At least one hotkey registered successfully!")
            try:
                # Keep program running
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print(f"\n🛑 Exiting...")
                hotkey_manager.cleanup()
        else:
            print("❌ No hotkeys could be registered!")
    
    else:
        print(f"\n💡 Run with --interactive to test hotkeys interactively")
    
    print("✅ Testing completed!")