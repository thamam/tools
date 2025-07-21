import os
import threading
import time
import logging
from typing import Optional, Callable

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:  # pragma: no cover - psutil may be optional
    PSUTIL_AVAILABLE = False


class HealthMonitor:
    """Monitor process health and trigger emergency cleanup on limits."""

    def __init__(self,
                 pid: Optional[int] = None,
                 memory_limit_mb: int = 1024,
                 cpu_limit_percent: int = 95,
                 check_interval: int = 30,
                 emergency_callback: Optional[Callable] = None):
        self.pid = pid or os.getpid()
        self.memory_limit_mb = memory_limit_mb
        self.cpu_limit_percent = cpu_limit_percent
        self.check_interval = max(1, check_interval)
        self.emergency_callback = emergency_callback
        self.logger = logging.getLogger(__name__)
        self._stop_event = threading.Event()
        self._thread = None

    def start(self) -> None:
        """Start monitoring in background."""
        if not PSUTIL_AVAILABLE:
            self.logger.warning("psutil not available - health monitoring disabled")
            return
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop monitoring."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1)

    def _monitor_loop(self) -> None:
        try:
            process = psutil.Process(self.pid)
        except Exception as e:  # pragma: no cover - should not happen
            self.logger.error(f"Health monitor failed to access process: {e}")
            return

        while not self._stop_event.is_set():
            try:
                mem_mb = process.memory_info().rss / (1024 * 1024)
                cpu_percent = process.cpu_percent(interval=0.1)
                self.logger.debug(
                    f"HealthMonitor: memory={mem_mb:.1f}MB cpu={cpu_percent:.1f}%")

                if mem_mb > self.memory_limit_mb or cpu_percent > self.cpu_limit_percent:
                    self.logger.error(
                        f"Resource limit exceeded: {mem_mb:.1f}MB, {cpu_percent:.1f}% CPU")
                    if self.emergency_callback:
                        try:
                            self.emergency_callback()
                        finally:
                            pass
                    break
            except Exception as e:  # pragma: no cover - psutil errors
                self.logger.error(f"Health monitor error: {e}")
                break
            time.sleep(self.check_interval)
