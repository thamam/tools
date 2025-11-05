"""
utils/tray_manager.py - System tray icon manager for Voice Transcription Tool.

Provides system tray icon with menu, recording state animation, and desktop notifications.
"""

import logging
import threading
import time
from typing import Callable, Optional
from PIL import Image, ImageDraw


class TrayManager:
    """System tray icon manager with recording state animation and live feedback."""

    def __init__(self, app):
        """
        Initialize tray manager.

        Args:
            app: VoiceTranscriptionApp instance
        """
        self.app = app
        self.logger = logging.getLogger(__name__)
        self.icon = None
        self.is_recording = False
        self._icon_thread = None
        self._last_notification_time = 0
        self._notification_interval = 5.0  # Show updates every 5 seconds
        self._recording_start_time = None
        self._last_audio_level = 0
        
    def create_icon(self, color="black") -> Image.Image:
        """
        Generate microphone icon programmatically.
        
        Args:
            color: Icon color ("black" or "red" for recording state)
            
        Returns:
            PIL Image object
        """
        # Create 64x64 image with transparent background
        img = Image.new('RGBA', (64, 64), color=(255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # Set fill color
        if color == "red":
            fill = (220, 53, 69)  # Red for recording
        else:
            fill = (51, 51, 51)  # Dark gray for idle
        
        # Draw microphone shape
        # Mic capsule (rounded rectangle)
        draw.ellipse([22, 12, 42, 32], fill=fill)  # Top circle
        draw.rectangle([22, 22, 42, 38], fill=fill)  # Middle rectangle
        draw.ellipse([22, 32, 42, 42], fill=fill)  # Bottom circle
        
        # Mic stand
        draw.rectangle([30, 42, 34, 52], fill=fill)  # Vertical stand
        
        # Mic base (ellipse)
        draw.ellipse([24, 48, 40, 54], fill=fill)
        
        return img
    
    def _is_window_visible(self):
        """Check if main window is currently visible (not withdrawn)."""
        try:
            # Window is visible if its state is not 'withdrawn'
            return self.app.root.state() != 'withdrawn'
        except:
            return False

    def create_menu(self):
        """
        Create dynamic system tray menu.

        Menu items change based on window visibility and recording state.
        Like Dropbox/NoMachine, provides Show/Hide toggle.

        Returns:
            pystray.Menu object
        """
        try:
            from pystray import Menu, MenuItem

            return Menu(
                MenuItem(
                    'Show Window',
                    lambda: self._safe_call(self.app.restore_window),
                    default=True,
                    visible=lambda item: not self._is_window_visible()
                ),
                MenuItem(
                    'Hide Window',
                    lambda: self._safe_call(self.app.hide_to_tray),
                    visible=lambda item: self._is_window_visible()
                ),
                Menu.SEPARATOR,
                MenuItem(
                    'Start Recording',
                    lambda: self._safe_call(self.app._toggle_recording),
                    enabled=lambda item: not self.is_recording,
                    visible=lambda item: not self.is_recording
                ),
                MenuItem(
                    'Stop Recording',
                    lambda: self._safe_call(self.app._toggle_recording),
                    enabled=lambda item: self.is_recording,
                    visible=lambda item: self.is_recording
                ),
                Menu.SEPARATOR,
                MenuItem('Quit', lambda: self._safe_call(self.app._on_closing))
            )
        except ImportError as e:
            self.logger.error(f"Failed to import pystray: {e}")
            return None
    
    def _safe_call(self, func: Callable):
        """
        Safely call a function with error handling.
        
        Args:
            func: Function to call
        """
        try:
            func()
        except Exception as e:
            self.logger.error(f"Tray action error: {e}")
    
    def start(self):
        """Start the system tray icon."""
        try:
            from pystray import Icon
            
            self.icon = Icon(
                "Voice Transcription",
                self.create_icon(),
                "Voice Transcription Tool",
                self.create_menu()
            )
            
            # Run icon in separate thread
            self._icon_thread = threading.Thread(target=self.icon.run, daemon=True)
            self._icon_thread.start()
            
            self.logger.info("System tray icon started")
        except ImportError:
            self.logger.warning("pystray not available - tray icon disabled")
        except Exception as e:
            self.logger.error(f"Failed to start tray icon: {e}")
    
    def stop(self):
        """Stop the system tray icon."""
        if self.icon:
            try:
                self.icon.stop()
                self.logger.info("System tray icon stopped")
            except Exception as e:
                self.logger.error(f"Error stopping tray icon: {e}")
    
    def set_recording_state(self, is_recording: bool):
        """
        Update icon when recording state changes.
        
        Args:
            is_recording: True if recording is active
        """
        self.is_recording = is_recording
        
        if self.icon:
            try:
                # Change icon color
                color = "red" if is_recording else "black"
                self.icon.icon = self.create_icon(color)
                
                # Update menu
                self.icon.menu = self.create_menu()
                
                self.logger.debug(f"Tray icon updated: recording={is_recording}")
            except Exception as e:
                self.logger.error(f"Failed to update tray icon: {e}")
    
    def show_notification(self, title: str, message: str):
        """
        Show desktop notification.
        
        Args:
            title: Notification title
            message: Notification message
        """
        if self.icon:
            try:
                # Truncate long messages
                if len(message) > 100:
                    message = message[:97] + "..."
                
                self.icon.notify(message, title)
                self.logger.debug(f"Notification shown: {title}")
            except Exception as e:
                self.logger.error(f"Failed to show notification: {e}")
    
    def is_available(self) -> bool:
        """
        Check if tray icon is available.

        Returns:
            True if tray icon is running
        """
        return self.icon is not None

    def notify_recording_started(self):
        """Show notification when recording starts."""
        self._recording_start_time = time.time()
        self._last_notification_time = time.time()
        self.show_notification(
            "🔴 Recording Started",
            "Speak clearly into your microphone..."
        )

    def notify_recording_stopped(self):
        """Show notification when recording stops."""
        self._recording_start_time = None
        self.show_notification(
            "⏹️ Recording Stopped",
            "Processing audio..."
        )

    def update_recording_progress(self, elapsed: float, audio_level: float):
        """
        Update recording progress with audio level feedback.

        Args:
            elapsed: Seconds elapsed since recording started
            audio_level: RMS audio level (0-10000 range)
        """
        self._last_audio_level = audio_level

        # Only show notifications every N seconds
        current_time = time.time()
        if current_time - self._last_notification_time < self._notification_interval:
            return

        self._last_notification_time = current_time

        # Determine audio level status (consistent with main_window.py thresholds)
        if audio_level < 500:
            level_emoji = "🟡"
            level_text = "Too quiet"
        elif audio_level > 5000:
            level_emoji = "🔴"
            level_text = "Too loud"
        else:
            level_emoji = "🟢"
            level_text = "Good"

        # Calculate remaining time (30s max)
        remaining = max(0, 30 - int(elapsed))

        self.show_notification(
            f"🎙️ Recording... {int(elapsed)}s / 30s",
            f"Audio Level: {level_emoji} {level_text}"
        )

    def notify_transcription_complete(self, text: str, success: bool = True):
        """
        Show notification when transcription completes.

        Args:
            text: Transcribed text
            success: Whether transcription was successful
        """
        if success:
            # Show preview of transcribed text
            preview = text[:80] + "..." if len(text) > 80 else text
            self.show_notification(
                "✅ Transcription Complete",
                preview
            )
        else:
            self.show_notification(
                "❌ Transcription Failed",
                "Could not transcribe audio. Please try again."
            )
