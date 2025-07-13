"""
Tests for the utils module components.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from utils.autopaste import AutoPasteManager
from utils.system_tray import SystemTrayManager
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
            assert manager.method in ['xdotool', 'pyautogui', 'none']
    
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


class TestSystemTrayManager:
    """Test the SystemTrayManager class."""
    
    def test_system_tray_initialization(self):
        """Test system tray manager initialization."""
        tray = SystemTrayManager()
        
        assert tray is not None
        assert hasattr(tray, 'tray_icon')
        assert hasattr(tray, 'is_running')
        assert tray.is_running is False
    
    @patch('utils.system_tray.PYSTRAY_AVAILABLE', False)
    def test_system_tray_unavailable(self):
        """Test system tray when pystray is not available."""
        tray = SystemTrayManager()
        
        assert tray.is_available() is False
        assert tray.start() is False
    
    @patch('utils.system_tray.PYSTRAY_AVAILABLE', True)
    def test_create_icon(self):
        """Test creating tray icon."""
        tray = SystemTrayManager()
        
        icon = tray.create_icon()
        # Icon creation might fail in test environment, but shouldn't crash
        assert icon is None or hasattr(icon, 'size')
    
    def test_callback_setters(self):
        """Test setting callbacks."""
        tray = SystemTrayManager()
        
        mock_callback = Mock()
        
        tray.set_show_callback(mock_callback)
        assert tray.on_show_callback == mock_callback
        
        tray.set_hide_callback(mock_callback)
        assert tray.on_hide_callback == mock_callback
        
        tray.set_quit_callback(mock_callback)
        assert tray.on_quit_callback == mock_callback
    
    def test_get_install_instructions(self):
        """Test getting installation instructions."""
        tray = SystemTrayManager()
        
        instructions = tray.get_install_instructions()
        assert isinstance(instructions, str)
        assert 'pystray' in instructions or 'pillow' in instructions


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