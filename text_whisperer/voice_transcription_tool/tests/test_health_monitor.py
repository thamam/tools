from utils.health_monitor import HealthMonitor
from unittest.mock import MagicMock, patch
import time

@patch('utils.health_monitor.psutil.Process')
def test_health_monitor_start_stop(mock_process):
    fake_proc = MagicMock()
    fake_proc.memory_info.return_value = MagicMock(rss=10 * 1024 * 1024)
    fake_proc.cpu_percent.return_value = 1.0
    mock_process.return_value = fake_proc

    monitor = HealthMonitor(memory_limit_mb=100, cpu_limit_percent=50, check_interval=0.1)
    monitor.start()
    time.sleep(0.2)
    monitor.stop()

    assert not monitor._thread.is_alive()
