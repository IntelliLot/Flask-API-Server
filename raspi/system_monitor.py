"""
System Monitor - Monitor Raspberry Pi system resources
"""

import psutil
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class SystemMonitor:
    """Monitor system resources and health"""

    def __init__(self, config: dict):
        self.config = config
        self.enable_monitoring = config.get('enable_system_stats', True)

    def get_cpu_usage(self) -> float:
        """Get CPU usage percentage"""
        try:
            return psutil.cpu_percent(interval=1)
        except Exception as e:
            logger.error(f"Failed to get CPU usage: {e}")
            return 0.0

    def get_memory_usage(self) -> Dict[str, float]:
        """Get memory usage statistics"""
        try:
            mem = psutil.virtual_memory()
            return {
                'total': mem.total / (1024 ** 3),  # GB
                'available': mem.available / (1024 ** 3),  # GB
                'used': mem.used / (1024 ** 3),  # GB
                'percent': mem.percent
            }
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return {'total': 0, 'available': 0, 'used': 0, 'percent': 0}

    def get_disk_usage(self) -> Dict[str, float]:
        """Get disk usage statistics"""
        try:
            disk = psutil.disk_usage('/')
            return {
                'total': disk.total / (1024 ** 3),  # GB
                'used': disk.used / (1024 ** 3),  # GB
                'free': disk.free / (1024 ** 3),  # GB
                'percent': disk.percent
            }
        except Exception as e:
            logger.error(f"Failed to get disk usage: {e}")
            return {'total': 0, 'used': 0, 'free': 0, 'percent': 0}

    def get_temperature(self) -> Optional[float]:
        """Get CPU temperature (Raspberry Pi specific)"""
        try:
            # Try reading from thermal zone (Raspberry Pi)
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read().strip()) / 1000.0
                return temp
        except FileNotFoundError:
            # Thermal zone not available (not on Raspberry Pi or not accessible)
            try:
                # Try using psutil sensors_temperatures
                temps = psutil.sensors_temperatures()
                if temps:
                    # Get first available temperature sensor
                    for name, entries in temps.items():
                        if entries:
                            return entries[0].current
            except Exception:
                pass
        except Exception as e:
            logger.debug(f"Temperature monitoring not available: {e}")

        return None

    def get_network_stats(self) -> Dict[str, int]:
        """Get network statistics"""
        try:
            net = psutil.net_io_counters()
            return {
                'bytes_sent': net.bytes_sent,
                'bytes_recv': net.bytes_recv,
                'packets_sent': net.packets_sent,
                'packets_recv': net.packets_recv
            }
        except Exception as e:
            logger.error(f"Failed to get network stats: {e}")
            return {'bytes_sent': 0, 'bytes_recv': 0, 'packets_sent': 0, 'packets_recv': 0}

    def get_stats(self) -> Dict:
        """Get all system statistics"""
        if not self.enable_monitoring:
            return {}

        stats = {
            'cpu_percent': self.get_cpu_usage(),
            'memory': self.get_memory_usage(),
            'disk': self.get_disk_usage(),
            'network': self.get_network_stats()
        }

        # Add memory and disk percentage to top level for easy access
        stats['memory_percent'] = stats['memory']['percent']
        stats['disk_percent'] = stats['disk']['percent']

        # Add temperature if available
        temp = self.get_temperature()
        if temp is not None:
            stats['temperature'] = temp

        return stats

    def check_health(self) -> bool:
        """Check if system is healthy based on thresholds"""
        if not self.enable_monitoring:
            return True

        stats = self.get_stats()

        # Check CPU
        cpu_threshold = self.config.get('cpu_threshold', 80)
        if stats['cpu_percent'] > cpu_threshold:
            logger.warning(
                f"CPU usage high: {stats['cpu_percent']:.1f}% > {cpu_threshold}%")
            return False

        # Check Memory
        memory_threshold = self.config.get('memory_threshold', 85)
        if stats['memory_percent'] > memory_threshold:
            logger.warning(
                f"Memory usage high: {stats['memory_percent']:.1f}% > {memory_threshold}%")
            return False

        # Check Disk
        disk_threshold = self.config.get('disk_threshold', 90)
        if stats['disk_percent'] > disk_threshold:
            logger.warning(
                f"Disk usage high: {stats['disk_percent']:.1f}% > {disk_threshold}%")
            return False

        # Check Temperature
        if 'temperature' in stats:
            temp_threshold = self.config.get('temperature_threshold', 70)
            if stats['temperature'] > temp_threshold:
                logger.warning(
                    f"Temperature high: {stats['temperature']:.1f}°C > {temp_threshold}°C")
                return False

        return True
