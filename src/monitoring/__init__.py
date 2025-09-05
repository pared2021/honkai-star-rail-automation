"""监控系统模块。

提供系统监控、日志记录和性能分析功能。
"""

from .alert_manager import AlertLevel, AlertManager
from .health_checker import HealthChecker
from .metrics_collector import MetricsCollector


class MonitoringSystem:
    """监控系统主类"""

    def __init__(self):
        self.alert_manager = AlertManager()
        self.health_checker = HealthChecker()
        self.metrics_collector = MetricsCollector()

    def start(self):
        """启动监控系统"""
        self.health_checker.start()
        self.metrics_collector.start()

    def stop(self):
        """停止监控系统"""
        self.health_checker.stop()
        self.metrics_collector.stop()


# 全局监控系统实例
_monitoring_system = None


def get_monitoring_system():
    """获取监控系统实例"""
    global _monitoring_system
    return _monitoring_system


def initialize_monitoring_system():
    """初始化监控系统"""
    global _monitoring_system
    if _monitoring_system is None:
        _monitoring_system = MonitoringSystem()
    return _monitoring_system


def set_monitoring_system(system):
    """设置监控系统实例"""
    global _monitoring_system
    _monitoring_system = system


__all__ = [
    "AlertManager",
    "AlertLevel",
    "HealthChecker",
    "MetricsCollector",
    "MonitoringSystem",
    "get_monitoring_system",
    "set_monitoring_system",
    "initialize_monitoring_system",
]
