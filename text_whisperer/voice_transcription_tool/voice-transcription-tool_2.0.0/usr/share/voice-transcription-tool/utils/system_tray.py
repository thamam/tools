"""
utils/system_tray.py - System tray functionality for the Voice Transcription Tool.

Provides system tray icon with context menu for background operation.
"""

import logging
import threading
from typing import Optional, Callable
from pathlib import Path

try:
    import pystray
    from PIL import Image, ImageDraw
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False


class SystemTrayManager:
    """Manages system tray icon and menu."""
    
    def __init__(self, app_instance=None):
        """
        Initialize system tray manager.
        
        Args:
            app_instance: Reference to main application instance
        """
        self.logger = logging.getLogger(__name__)
        self.app = app_instance
        self.tray_icon = None
        self.tray_thread = None
        self.is_running = False
        
        # Callbacks
        self.on_show_callback = None
        self.on_hide_callback = None
        self.on_quit_callback = None
        self.on_record_callback = None
        
        if not PYSTRAY_AVAILABLE:
            self.logger.warning("pystray not available - system tray disabled")
    
    def create_icon(self) -> Optional[Image.Image]:
        """Create a simple tray icon."""
        try:
            # Create a simple microphone icon
            size = 64
            image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Draw microphone shape
            # Base circle
            center = size // 2
            radius = size // 4
            draw.ellipse([center - radius, center - radius, 
                         center + radius, center + radius], 
                        fill=(70, 130, 180, 255))  # Steel blue
            
            # Microphone body
            body_width = radius // 2
            body_height = radius
            draw.rectangle([center - body_width, center - body_height//2,
                          center + body_width, center + body_height*1.5],
                         fill=(70, 130, 180, 255))
            
            # Stand base
            base_width = radius * 1.5
            draw.line([center - base_width, size - 8, 
                      center + base_width, size - 8], 
                     fill=(70, 130, 180, 255), width=4)
            
            # Center pole
            draw.line([center, center + body_height*1.5, 
                      center, size - 8], 
                     fill=(70, 130, 180, 255), width=3)
            
            return image
        except Exception as e:
            self.logger.error(f"Failed to create tray icon: {e}")
            return None
    
    def create_menu(self) -> Optional:
        """Create the system tray context menu."""
        if not PYSTRAY_AVAILABLE:
            return None
        
        try:
            menu_items = [
                pystray.MenuItem(
                    "🎤 Quick Record", 
                    self._on_quick_record,
                    enabled=True
                ),
                pystray.MenuItem(
                    "📋 Show Transcriptions", 
                    self._on_show_transcriptions,
                    enabled=True
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "⚙️ Settings", 
                    self._on_show_settings,
                    enabled=True
                ),
                pystray.MenuItem(
                    "📊 Show Main Window", 
                    self._on_show_window,
                    enabled=True
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "❌ Quit", 
                    self._on_quit,
                    enabled=True
                )
            ]
            
            return pystray.Menu(*menu_items)
        except Exception as e:
            self.logger.error(f"Failed to create tray menu: {e}")
            return None
    
    def start(self) -> bool:
        """Start the system tray icon."""
        if not PYSTRAY_AVAILABLE:
            self.logger.warning("Cannot start system tray - pystray not available")
            return False
        
        if self.is_running:
            self.logger.warning("System tray already running")
            return True
        
        try:
            icon_image = self.create_icon()
            if not icon_image:
                return False
            
            menu = self.create_menu()
            if not menu:
                return False
            
            self.tray_icon = pystray.Icon(
                "VoiceTranscription",
                icon_image,
                "Voice Transcription Tool",
                menu
            )
            
            # Start tray icon in background thread
            self.tray_thread = threading.Thread(
                target=self._run_tray, 
                daemon=True
            )
            self.tray_thread.start()
            
            self.is_running = True
            self.logger.info("System tray started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start system tray: {e}")
            return False
    
    def stop(self):
        """Stop the system tray icon."""
        if self.tray_icon and self.is_running:
            try:
                self.tray_icon.stop()
                self.is_running = False
                self.logger.info("System tray stopped")
            except Exception as e:
                self.logger.error(f"Error stopping system tray: {e}")
    
    def _run_tray(self):
        """Run the tray icon (called in background thread)."""
        try:
            self.tray_icon.run()
        except Exception as e:
            self.logger.error(f"System tray error: {e}")
            self.is_running = False
    
    def update_icon_state(self, is_recording: bool):
        """Update tray icon to show recording state."""
        if not self.tray_icon:
            return
        
        try:
            # Create different icon for recording state
            if is_recording:
                # Red icon for recording
                size = 64
                image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
                draw = ImageDraw.Draw(image)
                
                center = size // 2
                radius = size // 4
                draw.ellipse([center - radius, center - radius, 
                             center + radius, center + radius], 
                            fill=(220, 20, 60, 255))  # Crimson red
                
                # Add recording indicator
                draw.text((center - 8, center + radius + 5), "REC", 
                         fill=(220, 20, 60, 255))
            else:
                image = self.create_icon()
            
            if image:
                self.tray_icon.icon = image
                
        except Exception as e:
            self.logger.error(f"Failed to update tray icon: {e}")
    
    def show_notification(self, title: str, message: str):
        """Show a system notification."""
        if self.tray_icon:
            try:
                self.tray_icon.notify(message, title)
            except Exception as e:
                self.logger.error(f"Failed to show notification: {e}")
    
    # Menu callbacks
    def _on_quick_record(self, icon, item):
        """Handle quick record menu item."""
        if self.on_record_callback:
            self.on_record_callback()
        elif self.app:
            self.app._toggle_recording()
    
    def _on_show_transcriptions(self, icon, item):
        """Handle show transcriptions menu item."""
        if self.app:
            self.app._show_recent_transcriptions()
    
    def _on_show_settings(self, icon, item):
        """Handle settings menu item."""
        if self.app:
            self.app._open_settings()
    
    def _on_show_window(self, icon, item):
        """Handle show main window menu item."""
        if self.on_show_callback:
            self.on_show_callback()
        elif self.app:
            self.app.root.deiconify()
            self.app.root.lift()
            self.app.root.focus_force()
    
    def _on_quit(self, icon, item):
        """Handle quit menu item."""
        if self.on_quit_callback:
            self.on_quit_callback()
        elif self.app:
            self.app._on_closing()
    
    # Callback setters
    def set_show_callback(self, callback: Callable):
        """Set callback for showing main window."""
        self.on_show_callback = callback
    
    def set_hide_callback(self, callback: Callable):
        """Set callback for hiding main window."""
        self.on_hide_callback = callback
    
    def set_quit_callback(self, callback: Callable):
        """Set callback for quitting application."""
        self.on_quit_callback = callback
    
    def set_record_callback(self, callback: Callable):
        """Set callback for quick record action."""
        self.on_record_callback = callback
    
    def is_available(self) -> bool:
        """Check if system tray is available."""
        return PYSTRAY_AVAILABLE
    
    def get_install_instructions(self) -> str:
        """Get installation instructions for system tray dependencies."""
        return """To enable system tray functionality:
pip install pystray pillow

Note: System tray requires a desktop environment with tray support."""


# Test the system tray functionality
if __name__ == "__main__":
    import time
    
    print("🖥️ Testing System Tray")
    print("=" * 30)
    
    if not PYSTRAY_AVAILABLE:
        print("❌ pystray not available")
        print("Install with: pip install pystray pillow")
        exit(1)
    
    tray = SystemTrayManager()
    
    if tray.start():
        print("✅ System tray started")
        print("Right-click the tray icon to test menu")
        print("Press Ctrl+C to stop")
        
        try:
            # Test notification
            time.sleep(2)
            tray.show_notification("Test", "System tray is working!")
            
            # Test icon state change
            time.sleep(3)
            tray.update_icon_state(True)  # Recording
            time.sleep(2)
            tray.update_icon_state(False)  # Not recording
            
            # Keep running
            while tray.is_running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping system tray...")
            tray.stop()
    else:
        print("❌ Failed to start system tray")