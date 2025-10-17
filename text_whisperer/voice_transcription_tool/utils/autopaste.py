"""
utils/autopaste.py - Auto-paste functionality for the Voice Transcription Tool.

Provides alternative methods for auto-pasting that work without root access.
"""

import logging
import subprocess
import sys
import time
from typing import Optional

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

# pyautogui removed due to Qt threading conflicts with OpenCV
# Use xdotool on Linux instead (no sudo required, no Qt conflicts)


class AutoPasteManager:
    """Manages auto-paste functionality with fallback methods."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.method = self._detect_best_method()
        self.active_window_id = None
        self.active_window_name = None
        
    def _detect_best_method(self) -> str:
        """Detect the best auto-paste method for the current platform."""
        if sys.platform == "linux":
            # Check if xdotool is available
            try:
                subprocess.run(["which", "xdotool"],
                             capture_output=True, check=True)
                self.logger.info("Auto-paste using xdotool (Linux)")
                return "xdotool"
            except:
                self.logger.warning("xdotool not found - install with: sudo apt install xdotool")

        elif sys.platform == "darwin":  # macOS
            self.logger.info("Auto-paste using osascript (macOS)")
            return "osascript"

        elif sys.platform == "win32":  # Windows
            self.logger.warning("Auto-paste not implemented for Windows yet")
            return "none"

        self.logger.warning("No auto-paste method available")
        return "none"
    
    def capture_active_window(self) -> bool:
        """Capture information about the currently active window."""
        if self.method == "xdotool":
            try:
                # Get active window ID
                result = subprocess.run(["xdotool", "getactivewindow"], 
                                      capture_output=True, text=True, check=True)
                self.active_window_id = result.stdout.strip()
                
                # Get window name
                result = subprocess.run(["xdotool", "getwindowname", self.active_window_id], 
                                      capture_output=True, text=True)
                window_name = result.stdout.strip() if result.returncode == 0 else ""
                
                # Get window class for better detection
                result = subprocess.run(["xdotool", "getwindowclassname", self.active_window_id], 
                                      capture_output=True, text=True)
                window_class = result.stdout.strip() if result.returncode == 0 else ""
                
                # Combine name and class for better terminal detection
                self.active_window_name = f"{window_name} [{window_class}]" if window_class else window_name
                
                is_terminal = self._is_terminal_window(self.active_window_name)
                terminal_info = " (Terminal detected)" if is_terminal else ""
                
                self.logger.info(f"Captured active window: {self.active_window_name} (ID: {self.active_window_id}){terminal_info}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to capture active window: {e}")
                return False
        return False
    
    def restore_active_window(self) -> bool:
        """Restore focus to the previously captured window."""
        if self.method == "xdotool" and self.active_window_id:
            try:
                subprocess.run(["xdotool", "windowactivate", self.active_window_id], 
                             check=True)
                self.logger.info(f"Restored focus to: {self.active_window_name}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to restore window focus: {e}")
                return False
        return False
    
    def _is_terminal_window(self, window_name: str) -> bool:
        """Check if the window appears to be a terminal."""
        terminal_indicators = [
            'terminal', 'gnome-terminal', 'konsole', 'xterm', 'urxvt', 
            'alacritty', 'kitty', 'tilix', 'terminator', 'guake',
            'yakuake', 'tilda', 'terminology', 'st', 'rxvt',
            'bash', 'zsh', 'fish', 'shell', 'command', 'cmd',
            # Common terminal window titles
            'Terminal', 'Console', '@', '~', '$', '#'
        ]
        
        window_name_lower = window_name.lower()
        
        # Check if any terminal indicator is in the window name
        for indicator in terminal_indicators:
            if indicator.lower() in window_name_lower:
                return True
        
        # Additional check for common terminal patterns
        if any(char in window_name for char in ['@', '~$', '#']):
            return True
            
        return False
    
    def _is_browser_window(self, window_name: str) -> bool:
        """Check if the window appears to be a web browser."""
        browser_indicators = [
            'firefox', 'chrome', 'chromium', 'safari', 'opera', 'edge',
            'brave', 'vivaldi', 'webkit', 'mozilla', 'browser',
            # Common browser window class names
            'Firefox', 'Chrome', 'Chromium', 'Safari', 'Opera', 'Edge',
            'Brave-browser', 'Vivaldi', 'WebKit', 'Navigator',
            # Browser-specific indicators
            'www.', 'http', '.com', '.org', '.net'
        ]
        window_name_lower = window_name.lower()
        return any(indicator.lower() in window_name_lower for indicator in browser_indicators)

    def auto_paste(self, text: str, delay: float = 0.1) -> dict:
        """
        Attempt to auto-paste text at cursor position.

        Args:
            text: Text to paste
            delay: Delay before pasting (seconds)

        Returns:
            Dict with keys:
                - success: bool - Whether paste succeeded
                - method: str - Method used or 'none'
                - error: str - Error message if failed (optional)
        """
        if not PYPERCLIP_AVAILABLE:
            self.logger.error("pyperclip not available for auto-paste")
            return {
                'success': False,
                'method': 'none',
                'error': 'Clipboard library not available'
            }

        try:
            # First, copy to clipboard
            pyperclip.copy(text)

            # Small delay to ensure clipboard is updated
            time.sleep(delay)

            # Try to paste based on detected method
            if self.method == "xdotool":
                success = self._paste_with_xdotool()
                if success:
                    return {
                        'success': True,
                        'method': 'xdotool',
                        'window': self.active_window_name
                    }
                else:
                    return {
                        'success': False,
                        'method': 'xdotool',
                        'error': 'Failed to paste with xdotool - text is in clipboard'
                    }
            elif self.method == "osascript":
                success = self._paste_with_osascript()
                if success:
                    return {
                        'success': True,
                        'method': 'osascript'
                    }
                else:
                    return {
                        'success': False,
                        'method': 'osascript',
                        'error': 'Failed to paste - text is in clipboard'
                    }
            else:
                self.logger.warning("No auto-paste method available - text copied to clipboard only")
                return {
                    'success': False,
                    'method': 'none',
                    'error': 'Auto-paste not available - install xdotool (Linux) or use manual paste'
                }

        except Exception as e:
            self.logger.error(f"Auto-paste failed: {e}")
            return {
                'success': False,
                'method': self.method,
                'error': f'Auto-paste error: {str(e)}'
            }
    
    def _paste_with_xdotool(self) -> bool:
        """Use xdotool to paste (Linux)."""
        try:
            # Restore focus to the original window first
            if self.active_window_id:
                subprocess.run(["xdotool", "windowactivate", self.active_window_id], check=True)
                # Small delay to ensure window is focused
                time.sleep(0.1)
            
            # Check if this is a browser and handle focus issues
            is_browser = self._is_browser_window(self.active_window_name or "")
            if is_browser:
                self.logger.info("Detected browser - applying browser-specific focus handling")
                # Click in the center of the window to ensure proper focus
                # but first get window geometry
                try:
                    result = subprocess.run(["xdotool", "getwindowgeometry", self.active_window_id], 
                                          capture_output=True, text=True, check=True)
                    # Parse geometry to get center coordinates
                    # Format: "Window 123: Geometry: 1920x1080+0+0  Screen: 0"
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if 'Geometry:' in line:
                            # Extract dimensions and position
                            geom_part = line.split('Geometry:')[1].strip().split()[0]
                            # Format: 1920x1080+0+0
                            dims, pos = geom_part.split('+', 1)
                            width, height = dims.split('x')
                            x_offset, y_offset = pos.split('+')
                            
                            # Click in center of window (avoiding address bar area)
                            center_x = int(x_offset) + int(width) // 2
                            center_y = int(y_offset) + int(height) // 2 + 100  # Offset down from address bar
                            
                            subprocess.run(["xdotool", "mousemove", str(center_x), str(center_y)], check=True)
                            subprocess.run(["xdotool", "click", "1"], check=True)
                            time.sleep(0.2)  # Extra delay for browser focus
                            break
                except Exception as e:
                    self.logger.warning(f"Could not get window geometry for browser focus: {e}")
                    # Fallback: use Escape + Tab to get out of address bar
                    try:
                        subprocess.run(["xdotool", "key", "Escape"], check=True)
                        time.sleep(0.1)
                        subprocess.run(["xdotool", "key", "Tab"], check=True)
                        time.sleep(0.2)
                    except:
                        time.sleep(0.3)
            
            # Detect if target window is a terminal
            paste_key = "ctrl+v"  # Default for most applications
            
            if self.active_window_name and self._is_terminal_window(self.active_window_name):
                paste_key = "ctrl+shift+v"  # Terminal paste shortcut
                self.logger.info("Detected terminal - using Ctrl+Shift+V")
            
            # Send appropriate paste command
            subprocess.run(["xdotool", "key", "--clearmodifiers", paste_key], 
                         check=True)
            self.logger.info(f"Auto-pasted with xdotool using {paste_key}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"xdotool paste failed: {e}")
            return False
    
    def _paste_with_osascript(self) -> bool:
        """Use osascript to paste (macOS)."""
        try:
            # AppleScript to paste
            script = 'tell application "System Events" to keystroke "v" using command down'
            subprocess.run(["osascript", "-e", script], check=True)
            self.logger.info("Auto-pasted with osascript")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"osascript paste failed: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if auto-paste is available."""
        return self.method != "none"
    
    def get_method(self) -> str:
        """Get the current auto-paste method."""
        return self.method
    
    def install_instructions(self) -> str:
        """Get installation instructions for auto-paste dependencies."""
        if sys.platform == "linux":
            return """To enable auto-paste on Linux:
sudo apt-get install xdotool

Note: xdotool provides reliable auto-paste without Qt threading conflicts."""

        elif sys.platform == "win32":
            return "Auto-paste not yet implemented for Windows."

        elif sys.platform == "darwin":
            return "Auto-paste should work on macOS without additional dependencies."

        return "Auto-paste not supported on this platform."