"""监控系统主模块.

提供统一的监控系统管理功能。"""

import time
import threading
import logging
from typing import Dict, List, Optional, Any
from .health_checker import HealthChecker
from .metrics_collector import MetricsCollector
from .alert_manager import AlertManager, create_console_notification_handler
from .types import HealthCheckResult, Alert


class MonitoringSystem:
    """监控系统主类.
    
    整合健康检查、指标收集和告警管理功能。
    """
    
    def __init__(self, 
                 health_check_interval: float = 30.0,
                 metrics_collection_interval: float = 60.0):
        """初始化监控系统.
        
        Args:
            health_check_interval: 健康检查间隔（秒）
            metrics_collection_interval: 指标收集间隔（秒）
        """
        self._logger = logging.getLogger(__name__)
        
        # 创建告警管理器
        self._alert_manager = AlertManager()
        
        # 添加控制台通知处理器
        console_handler = create_console_notification_handler()
        self._alert_manager.add_notification_handler(console_handler)
        
        # 创建健康检查器和指标收集器
        self._health_checker = HealthChecker(
            check_interval=health_check_interval,
            alert_manager=self._alert_manager
        )
        
        self._metrics_collector = MetricsCollector(
            max_metrics=10000,
            alert_manager=self._alert_manager
        )
        
        self._running = False
        self._lock = threading.RLock()
        
        self._logger.info("Monitoring system initialized")
    
    @property
    def health_checker(self) -> HealthChecker:
        """获取健康检查器.
        
        Returns:
            健康检查器实例
        """
        return self._health_checker
    
    @property
    def metrics_collector(self) -> MetricsCollector:
        """获取指标收集器.
        
        Returns:
            指标收集器实例
        """
        return self._metrics_collector
    
    @property
    def alert_manager(self) -> AlertManager:
        """获取告警管理器.
        
        Returns:
            告警管理器实例
        """
        return self._alert_manager
    
    def start(self) -> None:
        """启动监控系统."""
        with self._lock:
            if self._running:
                self._logger.warning("Monitoring system is already running")
                return
            
            try:
                # 启动健康检查器
                self._health_checker.start_monitoring()
                
                # 启动指标收集器
                self._metrics_collector.start()
                
                self._running = True
                self._logger.info("Monitoring system started")
                
            except Exception as e:
                self._logger.error(f"Failed to start monitoring system: {e}", exc_info=True)
                self.stop()
                raise
    
    def stop(self) -> None:
        """停止监控系统."""
        with self._lock:
            if not self._running:
                self._logger.warning("Monitoring system is not running")
                return
            
            try:
                # 停止健康检查器
                self._health_checker.stop_monitoring()
                
                # 停止指标收集器
                self._metrics_collector.stop()
                
                self._running = False
                self._logger.info("Monitoring system stopped")
                
            except Exception as e:
                self._logger.error(f"Error stopping monitoring system: {e}", exc_info=True)
    
    def is_running(self) -> bool:
        """检查监控系统是否运行中.
        
        Returns:
            是否运行中
        """
        return self._running
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态概览.
        
        Returns:
            系统状态信息
        """
        # 获取健康检查状态
        health_status = self._health_checker.get_overall_status()
        health_results = self._health_checker.get_results()
        
        # 获取最新指标
        latest_metrics = self._metrics_collector.get_all_metrics()
        
        # 获取告警统计
        alert_stats = self._alert_manager.get_alert_stats()
        active_alerts = self._alert_manager.get_active_alerts()
        
        return {
            'timestamp': time.time(),
            'running': self._running,
            'health': {
                'overall_status': health_status.value if health_status else 'unknown',
                'component_count': len(health_results),
                'healthy_components': sum(1 for r in health_results.values() 
                                        if r.status.value == 'healthy'),
                'unhealthy_components': sum(1 for r in health_results.values() 
                                          if r.status.value == 'unhealthy')
            },
            'metrics': {
                'total_metrics': len(latest_metrics.get('gauges', {})) + 
                               len(latest_metrics.get('counters', {})),
                'last_collection': latest_metrics.get('timestamp'),
                'collectors_count': len(self._metrics_collector._collectors)
            },
            'alerts': {
                'active_count': alert_stats['active_alerts'],
                'recent_24h': alert_stats['recent_alerts_24h'],
                'critical_count': alert_stats['severity_breakdown']['critical'],
                'warning_count': alert_stats['severity_breakdown']['warning'],
                'active_alerts': [{
                    'name': alert.name,
                    'severity': alert.severity.value,
                    'component': alert.component,
                    'message': alert.message,
                    'duration': alert.duration
                } for alert in active_alerts[:5]]  # 只显示前5个
            }
        }
    
    def get_health_report(self) -> Dict[str, Any]:
        """获取详细健康报告.
        
        Returns:
            健康检查详细报告
        """
        results = self._health_checker.get_results()
        overall_status = self._health_checker.get_overall_status()
        
        return {
            'timestamp': time.time(),
            'overall_status': overall_status.value if overall_status else 'unknown',
            'components': {
                name: {
                    'status': result.status.value,
                    'message': result.message,
                    'duration': result.duration,
                    'details': result.details
                }
                for name, result in results.items()
            }
        }
    
    def get_metrics_report(self) -> Dict[str, Any]:
        """获取详细指标报告.
        
        Returns:
            指标收集详细报告
        """
        return self._metrics_collector.get_all_metrics()
    
    def get_alerts_report(self) -> Dict[str, Any]:
        """获取详细告警报告.
        
        Returns:
            告警详细报告
        """
        active_alerts = self._alert_manager.get_active_alerts()
        recent_alerts = self._alert_manager.get_alert_history(24)
        stats = self._alert_manager.get_alert_stats()
        
        return {
            'timestamp': time.time(),
            'statistics': stats,
            'active_alerts': [{
                'name': alert.name,
                'severity': alert.severity.value,
                'status': alert.status.value,
                'component': alert.component,
                'message': alert.message,
                'timestamp': alert.timestamp,
                'duration': alert.duration,
                'details': alert.details
            } for alert in active_alerts],
            'recent_alerts': [{
                'name': alert.name,
                'severity': alert.severity.value,
                'status': alert.status.value,
                'component': alert.component,
                'message': alert.message,
                'timestamp': alert.timestamp,
                'resolved_at': alert.resolved_at,
                'duration': alert.duration
            } for alert in recent_alerts]
        }
    
    def add_custom_health_check(self, name: str, check_func) -> None:
        """添加自定义健康检查.
        
        Args:
            name: 检查名称
            check_func: 检查函数
        """
        self._health_checker.add_check(name, check_func)
        self._logger.info(f"Custom health check added: {name}")
    
    def add_custom_metrics_collector(self, name: str, collector_func) -> None:
        """添加自定义指标收集器.
        
        Args:
            name: 收集器名称
            collector_func: 收集器函数
        """
        self._metrics_collector.register_collector(name, collector_func)
        self._logger.info(f"Custom metrics collector added: {name}")
    
    def add_notification_handler(self, handler) -> None:
        """添加通知处理器.
        
        Args:
            handler: 通知处理函数
        """
        self._alert_manager.add_notification_handler(handler)
        self._logger.info("Notification handler added")


# 全局监控系统实例
_monitoring_system: Optional[MonitoringSystem] = None
_system_lock = threading.Lock()


def get_monitoring_system() -> Optional[MonitoringSystem]:
    """获取全局监控系统实例.
    
    Returns:
        监控系统实例，如果未初始化则返回None
    """
    global _monitoring_system
    return _monitoring_system


def start_monitoring() -> None:
    """启动全局监控系统."""
    system = get_monitoring_system()
    if system is None:
        system = initialize_monitoring_system()
    system.start()


def stop_monitoring() -> None:
    """停止全局监控系统."""
    global _monitoring_system
    
    if _monitoring_system:
        _monitoring_system.stop()


def set_monitoring_system(system: MonitoringSystem) -> None:
    """设置全局监控系统实例.
    
    Args:
        system: 监控系统实例
    """
    global _monitoring_system
    
    with _system_lock:
        _monitoring_system = system


def initialize_monitoring_system() -> MonitoringSystem:
    """初始化监控系统.
    
    Returns:
        监控系统实例
    """
    global _monitoring_system
    
    with _system_lock:
        if _monitoring_system is None:
            _monitoring_system = MonitoringSystem()
    
    return _monitoring_system


def get_system_status() -> Dict[str, Any]:
    """获取系统状态.
    
    Returns:
        系统状态信息
    """
    system = get_monitoring_system()
    if system is None:
        system = initialize_monitoring_system()
    return system.get_system_status()