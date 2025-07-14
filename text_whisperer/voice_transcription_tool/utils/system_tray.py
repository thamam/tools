"""
utils/system_tray.py - System tray functionality for the Voice Transcription Tool.

Provides system tray icon with context menu for background operation.
"""

import logging
import threading
from typing import Optional, Callable, TYPE_CHECKING
from pathlib import Path

try:
    import pystray
    from PIL import Image, ImageDraw
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False
    if TYPE_CHECKING:
        from PIL import Image


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
    
    def create_icon(self, recording: bool = False, timer_text: str = "") -> Optional['Image.Image']:
        """Create a tray icon with optional recording indicator and timer."""
        try:
            # Create a simple microphone icon
            size = 64
            image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Choose color based on recording state
            color = (220, 20, 60, 255) if recording else (70, 130, 180, 255)  # Red when recording, steel blue when idle
            
            # Draw microphone shape
            # Base circle
            center = size // 2
            radius = size // 4
            draw.ellipse([center - radius, center - radius, 
                         center + radius, center + radius], 
                        fill=color)
            
            # Microphone body
            body_width = radius // 2
            body_height = radius
            draw.rectangle([center - body_width, center - body_height//2,
                          center + body_width, center + body_height*1.5],
                         fill=color)
            
            # Stand base
            base_width = radius * 1.5
            draw.line([center - base_width, size - 8, 
                      center + base_width, size - 8], 
                     fill=color, width=4)
            
            # Center pole
            draw.line([center, center + body_height*1.5, 
                      center, size - 8], 
                     fill=color, width=3)
            
            # Add recording indicator (red dot)
            if recording:
                dot_radius = 6
                draw.ellipse([size - dot_radius*2, 2, size - 2, dot_radius*2], 
                           fill=(255, 0, 0, 255))  # Bright red recording dot
            
            # Add timer text if provided
            if timer_text and recording:
                try:
                    # Use default font for timer text
                    text_color = (255, 255, 255, 255)  # White text
                    # Position timer text at bottom
                    bbox = draw.textbbox((0, 0), timer_text)
                    text_width = bbox[2] - bbox[0]
                    text_x = (size - text_width) // 2
                    text_y = size - 16
                    
                    # Add background for better readability
                    draw.rectangle([text_x - 2, text_y - 2, text_x + text_width + 2, text_y + 12], 
                                 fill=(0, 0, 0, 180))  # Semi-transparent black background
                    draw.text((text_x, text_y), timer_text, fill=text_color)
                except Exception as e:
                    self.logger.warning(f"Could not add timer text to icon: {e}")
            
            return image
        except Exception as e:
            self.logger.error(f"Failed to create tray icon: {e}")
            return None
    
    def create_menu(self) -> Optional['pystray.Menu']:
        """Create the system tray context menu."""
        if not PYSTRAY_AVAILABLE:
            return None
        
        try:
            menu_items = [
                pystray.MenuItem(
                    "🎤 Quick Record (or Left Click)", 
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
                    "📊 Show Main Window (or Double Click)", 
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
                menu,
                on_click=self._on_left_click,
                on_double_click=self._on_double_click
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
    
    def update_recording_status(self, recording: bool, timer_text: str = ""):
        """Update the tray icon to show recording status and timer."""
        if not self.tray_icon or not self.is_running:
            return
        
        try:
            # Create new icon with recording status
            new_icon = self.create_icon(recording=recording, timer_text=timer_text)
            if new_icon:
                self.tray_icon.icon = new_icon
                
                # Update tooltip with recording status
                if recording:
                    tooltip = f"Voice Transcription - Recording ({timer_text})" if timer_text else "Voice Transcription - Recording"
                else:
                    tooltip = "Voice Transcription Tool"
                self.tray_icon.title = tooltip
                
        except Exception as e:
            self.logger.error(f"Failed to update tray icon: {e}")
    
    def start_recording_animation(self):
        """Start the recording indicator on the tray icon."""
        self.update_recording_status(recording=True)
    
    def stop_recording_animation(self):
        """Stop the recording indicator on the tray icon."""
        self.update_recording_status(recording=False)
    
    def update_timer(self, seconds: int):
        """Update the timer display on the tray icon."""
        if seconds > 0:
            mins, secs = divmod(seconds, 60)
            timer_text = f"{mins:02d}:{secs:02d}"
            self.update_recording_status(recording=True, timer_text=timer_text)
    
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
        if not self.tray_icon:
            self.logger.error("Cannot run tray - tray_icon is None")
            return
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
    
    # Click handlers
    def _on_left_click(self, icon):
        """Handle left click on tray icon - trigger recording."""
        try:
            self.logger.info("🖱️ Left click on tray icon - triggering recording")
            if self.on_record_callback:
                self.on_record_callback()
            elif self.app:
                self.app._toggle_recording()
        except Exception as e:
            self.logger.error(f"Error handling left click: {e}")
    
    def _on_double_click(self, icon):
        """Handle double click on tray icon - show main window."""
        try:
            self.logger.info("🖱️ Double click on tray icon - showing main window")
            if self.on_show_callback:
                self.on_show_callback()
            elif self.app:
                self.app.root.deiconify()
                self.app.root.lift()
                self.app.root.focus_force()
        except Exception as e:
            self.logger.error(f"Error handling double click: {e}")
    
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