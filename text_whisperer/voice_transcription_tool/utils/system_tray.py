"""
utils/system_tray.py - Stub system tray (disabled for production readiness).

This is a no-op stub to maintain compatibility while system tray is being phased out.
"""

import logging


class SystemTrayManager:
    """Stub system tray manager (non-functional)."""

    def __init__(self, app_instance=None):
        """Initialize stub system tray manager."""
        self.logger = logging.getLogger(__name__)
        self.app = app_instance
        self.logger.info("System tray disabled (using stub)")

    def is_available(self) -> bool:
        """System tray is not available."""
        return False

    def start(self) -> bool:
        """No-op start."""
        return False

    def stop(self):
        """No-op stop."""
        pass

    def set_show_callback(self, callback):
        """No-op callback setter."""
        pass

    def set_hide_callback(self, callback):
        """No-op callback setter."""
        pass

    def set_quit_callback(self, callback):
        """No-op callback setter."""
        pass

    def set_record_callback(self, callback):
        """No-op callback setter."""
        pass

    def show_notification(self, title: str, message: str):
        """No-op notification."""
        pass

    def start_recording_animation(self):
        """No-op recording animation."""
        pass

    def stop_recording_animation(self):
        """No-op stop recording animation."""
        pass

    def update_timer(self, seconds: int):
        """No-op timer update."""
        pass
