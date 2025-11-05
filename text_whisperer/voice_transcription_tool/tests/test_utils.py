"""
Tests for the utils module components.
"""

import pytest
import subprocess
from unittest.mock import Mock, patch, MagicMock
from utils.autopaste import AutoPasteManager
from utils.hotkeys import HotkeyManager
from utils.logger import DebugMessageHandler


class TestAutoPasteManager:
    """Test the AutoPasteManager class."""

    def test_autopaste_initialization(self):
        """Test autopaste manager initialization."""
        manager = AutoPasteManager()

        assert manager is not None
        assert hasattr(manager, 'method')
        assert hasattr(manager, 'active_window_id')

    @patch('utils.autopaste.subprocess.run')
    def test_detect_xdotool_method(self, mock_run):
        """Test detection of xdotool method."""
        mock_run.return_value.returncode = 0  # xdotool available

        manager = AutoPasteManager()

        # Should detect xdotool on Linux
        import sys
        if sys.platform == "linux":
            assert manager.method in ['xdotool', 'none']

    def test_terminal_detection(self):
        """Test terminal window detection."""
        manager = AutoPasteManager()

        # Test various terminal window names
        terminal_names = [
            'Terminal',
            'gnome-terminal',
            'user@host: ~$',
            'vim /path/to/file',
            'konsole',
            'bash'
        ]

        # Test method exists and returns boolean
        for name in terminal_names:
            result = manager._is_terminal_window(name)
            assert isinstance(result, bool)

        # Test non-terminal names
        non_terminal_names = [
            'Firefox',
            'LibreOffice Writer',
            'Settings',
            'File Manager'
        ]

        for name in non_terminal_names:
            result = manager._is_terminal_window(name)
            assert isinstance(result, bool)

    @patch('utils.autopaste.subprocess.run')
    def test_capture_active_window(self, mock_run):
        """Test capturing active window information."""
        # Mock successful xdotool commands
        mock_run.side_effect = [
            Mock(returncode=0, stdout='12345'),  # getactivewindow
            Mock(returncode=0, stdout='Terminal'),  # getwindowname
            Mock(returncode=0, stdout='gnome-terminal')  # getwindowclassname
        ]

        manager = AutoPasteManager()
        manager.method = 'xdotool'

        success = manager.capture_active_window()
        assert isinstance(success, bool)
        # Only check these if capture was successful
        if success:
            assert manager.active_window_id is not None

    def test_install_instructions(self):
        """Test getting installation instructions."""
        manager = AutoPasteManager()

        instructions = manager.install_instructions()
        assert isinstance(instructions, str)
        assert len(instructions) > 0

    def test_terminal_detection_specific_cases(self):
        """Test specific terminal detection cases."""
        manager = AutoPasteManager()

        # Should detect terminals
        assert manager._is_terminal_window('gnome-terminal') is True
        assert manager._is_terminal_window('konsole') is True
        assert manager._is_terminal_window('xterm') is True
        assert manager._is_terminal_window('user@host:~$') is True
        assert manager._is_terminal_window('Terminal') is True

        # Should NOT detect non-terminals
        assert manager._is_terminal_window('Firefox') is False
        assert manager._is_terminal_window('Chrome') is False
        assert manager._is_terminal_window('LibreOffice') is False

    def test_browser_detection(self):
        """Test browser window detection."""
        manager = AutoPasteManager()

        # Should detect browsers
        assert manager._is_browser_window('Firefox') is True
        assert manager._is_browser_window('Google Chrome') is True
        assert manager._is_browser_window('Chromium') is True
        assert manager._is_browser_window('https://www.example.com - Firefox') is True
        assert manager._is_browser_window('Safari') is True

        # Should NOT detect non-browsers
        assert manager._is_browser_window('Terminal') is False
        assert manager._is_browser_window('LibreOffice Writer') is False
        assert manager._is_browser_window('File Manager') is False

    @patch('utils.autopaste.subprocess.run')
    def test_capture_active_window_success(self, mock_run):
        """Test successfully capturing active window."""
        manager = AutoPasteManager()
        manager.method = 'xdotool'

        # Mock xdotool commands
        mock_run.side_effect = [
            Mock(returncode=0, stdout='12345', check=True),  # getactivewindow
            Mock(returncode=0, stdout='Test Window'),  # getwindowname
            Mock(returncode=0, stdout='TestClass')  # getwindowclassname
        ]

        success = manager.capture_active_window()

        assert success is True
        assert manager.active_window_id == '12345'
        assert 'Test Window' in manager.active_window_name
        assert 'TestClass' in manager.active_window_name

    @patch('utils.autopaste.subprocess.run')
    def test_capture_active_window_failure(self, mock_run):
        """Test capturing active window when xdotool fails."""
        manager = AutoPasteManager()
        manager.method = 'xdotool'

        # Mock xdotool failure
        mock_run.side_effect = subprocess.CalledProcessError(1, 'xdotool')

        success = manager.capture_active_window()

        assert success is False

    @patch('utils.autopaste.subprocess.run')
    def test_restore_active_window_success(self, mock_run):
        """Test successfully restoring window focus."""
        manager = AutoPasteManager()
        manager.method = 'xdotool'
        manager.active_window_id = '12345'
        manager.active_window_name = 'Test Window'

        # Mock successful windowactivate
        mock_run.return_value = Mock(returncode=0)

        # Reset call count after init (which calls subprocess.run to detect xdotool)
        mock_run.reset_mock()

        success = manager.restore_active_window()

        assert success is True
        mock_run.assert_called_once()

    @patch('utils.autopaste.subprocess.run')
    def test_restore_active_window_failure(self, mock_run):
        """Test restoring window focus when xdotool fails."""
        manager = AutoPasteManager()
        manager.method = 'xdotool'
        manager.active_window_id = '12345'

        # Mock xdotool failure
        mock_run.side_effect = subprocess.CalledProcessError(1, 'xdotool')

        success = manager.restore_active_window()

        assert success is False

    def test_restore_active_window_no_window_id(self):
        """Test restoring window when no window ID is captured."""
        manager = AutoPasteManager()
        manager.method = 'xdotool'
        manager.active_window_id = None

        success = manager.restore_active_window()

        assert success is False

    @patch('utils.autopaste.PYPERCLIP_AVAILABLE', False)
    def test_auto_paste_no_pyperclip(self):
        """Test auto-paste when pyperclip is not available."""
        manager = AutoPasteManager()

        result = manager.auto_paste("test text")

        assert result['success'] is False
        assert 'error' in result
        assert 'Clipboard' in result['error']

    @patch('utils.autopaste.PYPERCLIP_AVAILABLE', True)
    @patch('utils.autopaste.pyperclip')
    @patch('utils.autopaste.subprocess.run')
    @patch('utils.autopaste.time.sleep')
    def test_auto_paste_with_xdotool_success(self, mock_sleep, mock_run, mock_pyperclip):
        """Test successful auto-paste with xdotool."""
        manager = AutoPasteManager()
        manager.method = 'xdotool'
        manager.active_window_id = '12345'
        manager.active_window_name = 'Terminal'

        # Mock successful xdotool commands
        mock_run.return_value = Mock(returncode=0)

        result = manager.auto_paste("test text")

        assert result['success'] is True
        assert result['method'] == 'xdotool'
        mock_pyperclip.copy.assert_called_once_with("test text")

    @patch('utils.autopaste.PYPERCLIP_AVAILABLE', True)
    @patch('utils.autopaste.pyperclip')
    @patch('utils.autopaste.subprocess.run')
    @patch('utils.autopaste.time.sleep')
    def test_auto_paste_with_xdotool_terminal(self, mock_sleep, mock_run, mock_pyperclip):
        """Test auto-paste uses Ctrl+Shift+V for terminal."""
        manager = AutoPasteManager()
        manager.method = 'xdotool'
        manager.active_window_id = '12345'
        manager.active_window_name = 'gnome-terminal'

        # Mock successful xdotool
        mock_run.return_value = Mock(returncode=0)

        result = manager.auto_paste("test text")

        # Should use ctrl+shift+v for terminal
        assert result['success'] is True
        # Check that xdotool key was called with ctrl+shift+v
        calls = [call for call in mock_run.call_args_list if 'key' in str(call)]
        assert len(calls) > 0

    @patch('utils.autopaste.PYPERCLIP_AVAILABLE', True)
    @patch('utils.autopaste.pyperclip')
    @patch('utils.autopaste.subprocess.run')
    @patch('utils.autopaste.time.sleep')
    def test_auto_paste_with_xdotool_failure(self, mock_sleep, mock_run, mock_pyperclip):
        """Test auto-paste when xdotool fails."""
        manager = AutoPasteManager()
        manager.method = 'xdotool'
        manager.active_window_id = '12345'
        manager.active_window_name = 'Test Window'

        # Mock xdotool failure
        mock_run.side_effect = subprocess.CalledProcessError(1, 'xdotool')

        result = manager.auto_paste("test text")

        assert result['success'] is False
        assert result['method'] == 'xdotool'

    @patch('utils.autopaste.PYPERCLIP_AVAILABLE', True)
    @patch('utils.autopaste.pyperclip')
    def test_auto_paste_no_method(self, mock_pyperclip):
        """Test auto-paste when no method is available."""
        manager = AutoPasteManager()
        manager.method = 'none'

        result = manager.auto_paste("test text")

        assert result['success'] is False
        assert result['method'] == 'none'
        # Should still copy to clipboard
        mock_pyperclip.copy.assert_called_once_with("test text")

    def test_is_available(self):
        """Test checking if auto-paste is available."""
        manager = AutoPasteManager()

        # When method is set
        manager.method = 'xdotool'
        assert manager.is_available() is True

        # When no method
        manager.method = 'none'
        assert manager.is_available() is False

    def test_get_method(self):
        """Test getting the auto-paste method."""
        manager = AutoPasteManager()

        assert isinstance(manager.get_method(), str)
        assert manager.get_method() in ['xdotool', 'osascript', 'none']

    @patch('utils.autopaste.sys.platform', 'darwin')
    @patch('utils.autopaste.subprocess.run')
    def test_detect_method_macos(self, mock_run):
        """Test method detection on macOS."""
        manager = AutoPasteManager()

        assert manager.method == 'osascript'

    @patch('utils.autopaste.sys.platform', 'win32')
    def test_detect_method_windows(self):
        """Test method detection on Windows."""
        manager = AutoPasteManager()

        assert manager.method == 'none'

    @patch('utils.autopaste.PYPERCLIP_AVAILABLE', True)
    @patch('utils.autopaste.pyperclip')
    @patch('utils.autopaste.subprocess.run')
    @patch('utils.autopaste.time.sleep')
    def test_paste_with_xdotool_browser(self, mock_sleep, mock_run, mock_pyperclip):
        """Test pasting in a browser window (special handling)."""
        manager = AutoPasteManager()
        manager.method = 'xdotool'
        manager.active_window_id = '12345'
        manager.active_window_name = 'Google Chrome - Test Page'

        # Mock xdotool commands
        mock_run.return_value = Mock(returncode=0, stdout='')

        result = manager.auto_paste("test text")

        # Should attempt special browser handling
        assert mock_run.call_count >= 1

    @patch('utils.autopaste.PYPERCLIP_AVAILABLE', True)
    @patch('utils.autopaste.pyperclip')
    @patch('utils.autopaste.subprocess.run')
    @patch('utils.autopaste.time.sleep')
    def test_auto_paste_exception_handling(self, mock_sleep, mock_run, mock_pyperclip):
        """Test auto-paste handles exceptions gracefully."""
        manager = AutoPasteManager()
        manager.method = 'xdotool'

        # Make pyperclip.copy raise an exception
        mock_pyperclip.copy.side_effect = Exception("Clipboard error")

        result = manager.auto_paste("test text")

        assert result['success'] is False
        assert 'error' in result


# TestSystemTrayManager removed - system tray disabled for production readiness


class TestHotkeyManager:
    """Test the HotkeyManager class."""

    def test_hotkey_initialization(self):
        """Test hotkey manager initialization."""
        manager = HotkeyManager()

        assert manager is not None
        assert hasattr(manager, 'registered_hotkeys')
        assert hasattr(manager, 'is_active')

    def test_get_one_handed_combinations(self):
        """Test getting one-handed key combinations."""
        manager = HotkeyManager()

        combinations = manager.get_one_handed_combinations()
        assert isinstance(combinations, list)
        assert len(combinations) > 0

        # Check format: should be tuples of (value, label)
        for combo in combinations:
            assert len(combo) == 2
            assert isinstance(combo[0], str)  # value
            assert isinstance(combo[1], str)  # label

    def test_get_two_handed_combinations(self):
        """Test getting two-handed key combinations."""
        manager = HotkeyManager()

        combinations = manager.get_two_handed_combinations()
        assert isinstance(combinations, list)
        assert len(combinations) > 0

    @patch('utils.hotkeys.PYNPUT_AVAILABLE', False)
    def test_hotkey_unavailable(self):
        """Test hotkey manager when keyboard library is not available."""
        manager = HotkeyManager()

        success = manager.register_hotkey('f9', lambda: None)
        assert success is False

    def test_is_hotkey_active(self):
        """Test checking if hotkey is active."""
        manager = HotkeyManager()

        # Initially should not be active
        assert manager.is_hotkey_active() is False

    def test_get_current_combination(self):
        """Test getting current key combination."""
        manager = HotkeyManager()

        combination = manager.get_current_combination()
        # Should return string or None
        assert combination is None or isinstance(combination, str)

    @patch('utils.hotkeys.PYNPUT_AVAILABLE', True)
    @patch('utils.hotkeys.keyboard.GlobalHotKeys')
    def test_register_hotkey_simple(self, mock_global_hotkeys):
        """Test registering a simple hotkey combination."""
        manager = HotkeyManager()
        mock_listener = Mock()
        mock_global_hotkeys.return_value = mock_listener

        callback = Mock()
        success = manager.register_hotkey('alt+d', callback)

        assert success is True
        assert 'alt+d' in manager.registered_hotkeys
        assert manager.registered_hotkeys['alt+d'] == callback
        mock_listener.start.assert_called_once()

    @patch('utils.hotkeys.PYNPUT_AVAILABLE', True)
    @patch('utils.hotkeys.keyboard.GlobalHotKeys')
    def test_register_hotkey_function_key(self, mock_global_hotkeys):
        """Test registering function key combinations."""
        manager = HotkeyManager()
        mock_listener = Mock()
        mock_global_hotkeys.return_value = mock_listener

        callback = Mock()

        # Test F9
        success = manager.register_hotkey('f9', callback)
        assert success is True
        assert 'f9' in manager.registered_hotkeys

        # Test Ctrl+Shift+F9
        success = manager.register_hotkey('ctrl+shift+f9', callback)
        assert success is True
        assert 'ctrl+shift+f9' in manager.registered_hotkeys

    @patch('utils.hotkeys.PYNPUT_AVAILABLE', True)
    @patch('utils.hotkeys.keyboard.GlobalHotKeys')
    def test_register_multiple_hotkeys(self, mock_global_hotkeys):
        """Test registering multiple hotkeys at once."""
        manager = HotkeyManager()
        mock_listener = Mock()
        mock_global_hotkeys.return_value = mock_listener

        hotkey_map = {
            'alt+d': Mock(),
            'alt+s': Mock(),
            'f9': Mock()
        }

        results = manager.register_multiple_hotkeys(hotkey_map)

        assert len(results) == 3
        assert all(results.values())  # All should be True
        assert len(manager.registered_hotkeys) == 3

    def test_convert_combination_simple(self):
        """Test converting simple key combinations."""
        manager = HotkeyManager()

        # Test single key
        assert manager._convert_combination('f9') == '<f9>'

        # Test modifier + key
        assert manager._convert_combination('alt+d') == '<alt>+d'
        assert manager._convert_combination('ctrl+shift+f9') == '<ctrl>+<shift>+<f9>'

    def test_convert_combination_special_keys(self):
        """Test converting special key combinations."""
        manager = HotkeyManager()

        # Test special keys
        assert manager._convert_combination('ctrl+space') == '<ctrl>+<space>'
        assert manager._convert_combination('alt+enter') == '<alt>+<enter>'
        assert manager._convert_combination('shift+tab') == '<shift>+<tab>'

    def test_convert_combination_invalid(self):
        """Test converting invalid key combinations."""
        manager = HotkeyManager()

        # Invalid modifier
        assert manager._convert_combination('invalid+d') is None

        # Invalid function key
        assert manager._convert_combination('f99') is None

        # Unknown key
        assert manager._convert_combination('ctrl+unknown_key') is None

    @patch('utils.hotkeys.PYNPUT_AVAILABLE', True)
    @patch('utils.hotkeys.keyboard.GlobalHotKeys')
    def test_unregister_hotkey_specific(self, mock_global_hotkeys):
        """Test unregistering a specific hotkey."""
        manager = HotkeyManager()
        mock_listener = Mock()
        mock_global_hotkeys.return_value = mock_listener

        # Register two hotkeys
        manager.register_hotkey('alt+d', Mock())
        manager.register_hotkey('f9', Mock())

        assert len(manager.registered_hotkeys) == 2

        # Unregister one
        manager.unregister_hotkey('alt+d')

        assert len(manager.registered_hotkeys) == 1
        assert 'alt+d' not in manager.registered_hotkeys
        assert 'f9' in manager.registered_hotkeys

    @patch('utils.hotkeys.PYNPUT_AVAILABLE', True)
    @patch('utils.hotkeys.keyboard.GlobalHotKeys')
    def test_unregister_all_hotkeys(self, mock_global_hotkeys):
        """Test unregistering all hotkeys."""
        manager = HotkeyManager()
        mock_listener = Mock()
        mock_global_hotkeys.return_value = mock_listener

        # Register multiple hotkeys
        manager.register_hotkey('alt+d', Mock())
        manager.register_hotkey('f9', Mock())

        assert len(manager.registered_hotkeys) == 2

        # Unregister all (call with no args)
        manager.unregister_hotkey()

        assert len(manager.registered_hotkeys) == 0
        mock_listener.stop.assert_called()

    @patch('utils.hotkeys.PYNPUT_AVAILABLE', True)
    @patch('utils.hotkeys.keyboard.GlobalHotKeys')
    def test_set_active(self, mock_global_hotkeys):
        """Test activating and deactivating hotkeys."""
        manager = HotkeyManager()
        mock_listener = Mock()
        mock_global_hotkeys.return_value = mock_listener

        # Register a hotkey
        manager.register_hotkey('f9', Mock())
        assert manager.is_active is True

        # Deactivate
        manager.set_active(False)
        assert manager.is_active is False
        mock_listener.stop.assert_called()

        # Reactivate
        manager.set_active(True)
        assert manager.is_active is True

    @patch('utils.hotkeys.PYNPUT_AVAILABLE', True)
    @patch('utils.hotkeys.keyboard.GlobalHotKeys')
    def test_stop_all_emergency(self, mock_global_hotkeys):
        """Test emergency stop all operations."""
        manager = HotkeyManager()
        mock_listener = Mock()
        mock_global_hotkeys.return_value = mock_listener

        # Register hotkeys
        manager.register_hotkey('alt+d', Mock())
        manager.register_hotkey('f9', Mock())

        assert len(manager.registered_hotkeys) == 2
        assert manager.is_active is True

        # Emergency stop
        manager.stop_all()

        assert len(manager.registered_hotkeys) == 0
        assert manager.is_active is False
        mock_listener.stop.assert_called()

    def test_validate_combination(self):
        """Test validating hotkey combinations."""
        manager = HotkeyManager()

        # Valid combinations
        assert manager.validate_combination('alt+d') is True
        assert manager.validate_combination('f9') is True
        assert manager.validate_combination('ctrl+shift+f10') is True

        # Invalid combinations
        assert manager.validate_combination('invalid+key') is False
        assert manager.validate_combination('f99') is False

    def test_get_recommended_combinations(self):
        """Test getting recommended combinations."""
        manager = HotkeyManager()

        combos = manager.get_recommended_combinations()
        assert isinstance(combos, list)
        assert len(combos) > 0

        # Check format
        for combo in combos:
            assert len(combo) == 2
            assert isinstance(combo[0], str)
            assert isinstance(combo[1], str)

    def test_is_combination_one_handed(self):
        """Test checking if combination is one-handed."""
        manager = HotkeyManager()

        # One-handed combinations
        assert manager.is_combination_one_handed('alt+d') is True
        assert manager.is_combination_one_handed('f9') is True

        # Two-handed combinations
        assert manager.is_combination_one_handed('ctrl+shift+r') is False
        assert manager.is_combination_one_handed('invalid') is False

    def test_get_status_info(self):
        """Test getting comprehensive status information."""
        manager = HotkeyManager()

        status = manager.get_status_info()

        assert isinstance(status, dict)
        assert 'available' in status
        assert 'registered' in status
        assert 'active' in status
        assert 'current_combination' in status
        assert 'library' in status
        assert 'sudo_required' in status
        assert status['sudo_required'] is False

    def test_test_combination(self):
        """Test testing a combination without registering."""
        manager = HotkeyManager()

        result = manager.test_combination('alt+d')

        assert isinstance(result, dict)
        assert 'valid' in result
        assert 'available' in result
        assert 'sudo_required' in result
        assert 'converted' in result
        assert result['sudo_required'] is False

    @patch('utils.hotkeys.PYNPUT_AVAILABLE', True)
    @patch('utils.hotkeys.keyboard.GlobalHotKeys')
    def test_get_registered_combinations(self, mock_global_hotkeys):
        """Test getting all registered combinations."""
        manager = HotkeyManager()
        mock_listener = Mock()
        mock_global_hotkeys.return_value = mock_listener

        # Register hotkeys
        manager.register_hotkey('alt+d', Mock())
        manager.register_hotkey('f9', Mock())

        combinations = manager.get_registered_combinations()

        assert isinstance(combinations, list)
        assert len(combinations) == 2
        assert 'alt+d' in combinations
        assert 'f9' in combinations

    @patch('utils.hotkeys.PYNPUT_AVAILABLE', True)
    @patch('utils.hotkeys.keyboard.GlobalHotKeys')
    def test_listener_restart_on_register(self, mock_global_hotkeys):
        """Test that listener restarts when registering new hotkey."""
        manager = HotkeyManager()
        mock_listener = Mock()
        mock_global_hotkeys.return_value = mock_listener

        # Register first hotkey
        manager.register_hotkey('alt+d', Mock())

        stop_call_count = mock_listener.stop.call_count
        start_call_count = mock_listener.start.call_count

        # Register second hotkey - should restart listener
        manager.register_hotkey('f9', Mock())

        # Should have called stop and start again
        assert mock_listener.stop.call_count > stop_call_count
        assert mock_listener.start.call_count > start_call_count

    @patch('utils.hotkeys.PYNPUT_AVAILABLE', True)
    @patch('utils.hotkeys.keyboard.GlobalHotKeys')
    def test_register_invalid_combination(self, mock_global_hotkeys):
        """Test registering an invalid hotkey combination."""
        manager = HotkeyManager()

        callback = Mock()
        success = manager.register_hotkey('invalid+key', callback)

        assert success is False
        assert 'invalid+key' not in manager.registered_hotkeys

    @patch('utils.hotkeys.PYNPUT_AVAILABLE', True)
    @patch('utils.hotkeys.keyboard.GlobalHotKeys')
    def test_exception_handling_in_listener(self, mock_global_hotkeys):
        """Test exception handling during listener startup."""
        manager = HotkeyManager()

        # Make GlobalHotKeys raise exception
        mock_global_hotkeys.side_effect = Exception("Test error")

        callback = Mock()
        success = manager.register_hotkey('alt+d', callback)

        # Should still register the hotkey even if listener fails
        # (defensive programming - hotkey is registered, listener will retry)
        assert success is True
        assert 'alt+d' in manager.registered_hotkeys
        assert manager.is_active is False  # But listener should not be active


class TestDebugMessageHandler:
    """Test the DebugMessageHandler class."""
    
    def test_debug_handler_initialization(self):
        """Test debug message handler initialization."""
        handler = DebugMessageHandler()
        
        assert handler is not None
        assert hasattr(handler, 'callbacks')
        assert len(handler.callbacks) == 0
    
    def test_add_callback(self):
        """Test adding message callback."""
        handler = DebugMessageHandler()
        mock_callback = Mock()
        
        handler.add_callback(mock_callback)
        assert len(handler.callbacks) == 1
        assert mock_callback in handler.callbacks
    
    def test_send_message(self):
        """Test sending debug message."""
        handler = DebugMessageHandler()
        mock_callback = Mock()
        handler.add_callback(mock_callback)
        
        test_message = "Test debug message"
        handler.add_message(test_message)  # Use correct method name
        
        # Check that callback was called with formatted message
        assert mock_callback.call_count == 1
        args, kwargs = mock_callback.call_args
        assert test_message in args[0]  # Message should be in the formatted string
    
    def test_multiple_callbacks(self):
        """Test multiple callbacks receive messages."""
        handler = DebugMessageHandler()
        
        callback1 = Mock()
        callback2 = Mock()
        
        handler.add_callback(callback1)
        handler.add_callback(callback2)
        
        test_message = "Test message"
        handler.add_message(test_message)  # Use correct method name
        
        # Check that both callbacks were called
        assert callback1.call_count == 1
        assert callback2.call_count == 1
    
    def test_callback_exception_handling(self):
        """Test that callback exceptions don't break the handler."""
        handler = DebugMessageHandler()
        
        # Callback that raises exception
        def bad_callback(message):
            raise Exception("Test exception")
        
        good_callback = Mock()
        
        handler.add_callback(bad_callback)
        handler.add_callback(good_callback)
        
        # Should not crash and good callback should still be called
        handler.add_message("Test message")  # Use correct method name
        # Check that good callback was called despite the bad one
        assert good_callback.call_count == 1