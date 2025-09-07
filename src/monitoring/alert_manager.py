"""告警管理器模块.

提供告警规则管理、告警触发和通知功能。"""

import logging
import threading
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from .types import (
    HealthStatus, HealthCheckResult, AlertSeverity, AlertStatus, Alert, AlertRule
)


class AlertManager:
    """告警管理器.
    
    负责管理告警规则、生成告警和发送通知。
    """
    
    def __init__(self):
        """初始化告警管理器."""
        self._rules: Dict[str, AlertRule] = {}
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_history: List[Alert] = []
        self._notification_handlers: List[Callable[[Alert], None]] = []
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        self._last_alert_time: Dict[str, float] = {}
        
    def add_rule(self, rule: AlertRule) -> None:
        """添加告警规则.
        
        Args:
            rule: 告警规则
        """
        with self._lock:
            self._rules[rule.name] = rule
        
        self._logger.info(f"Alert rule added: {rule.name}")
    
    def remove_rule(self, name: str) -> bool:
        """移除告警规则.
        
        Args:
            name: 规则名称
            
        Returns:
            是否成功移除
        """
        with self._lock:
            if name in self._rules:
                del self._rules[name]
                self._logger.info(f"Alert rule removed: {name}")
                return True
        
        return False
    
    def add_notification_handler(self, handler: Callable[[Alert], None]) -> None:
        """添加通知处理器.
        
        Args:
            handler: 通知处理函数
        """
        with self._lock:
            self._notification_handlers.append(handler)
        
        self._logger.info("Notification handler added")
    
    def create_alert(self, rule_id: str, title: str, source: str, data: Dict[str, Any]) -> Alert:
        """创建告警.
        
        Args:
            rule_id: 规则ID
            title: 告警标题
            source: 告警源
            data: 告警数据
            
        Returns:
            创建的告警对象
        """
        alert = Alert(
            name=rule_id,
            severity=AlertSeverity.WARNING,
            status=AlertStatus.ACTIVE,
            message=title,
            component=source,
            timestamp=datetime.now(),
            details=data
        )
        
        with self._lock:
            self._active_alerts[rule_id] = alert
            self._alert_history.append(alert)
        
        self._send_notification(alert)
        self._logger.info(f"Alert created: {rule_id}")
        
        return alert
    
    def evaluate_health_check(self, result: HealthCheckResult) -> None:
        """评估健康检查结果并生成告警.
        
        Args:
            result: 健康检查结果
        """
        # 检查健康状态告警规则
        if result.status == HealthStatus.UNHEALTHY:
            self._trigger_alert(
                name=f"health_check_{result.component}",
                severity=AlertSeverity.CRITICAL,
                message=f"Health check failed for {result.component}: {result.message}",
                component=result.component,
                details={
                    'health_status': result.status.value,
                    'duration': result.duration,
                    'details': result.details
                }
            )
        elif result.status == HealthStatus.DEGRADED:
            self._trigger_alert(
                name=f"health_check_{result.component}",
                severity=AlertSeverity.WARNING,
                message=f"Health check degraded for {result.component}: {result.message}",
                component=result.component,
                details={
                    'health_status': result.status.value,
                    'duration': result.duration,
                    'details': result.details
                }
            )
        elif result.status == HealthStatus.HEALTHY:
            # 解决相关告警
            self._resolve_alert(f"health_check_{result.component}")
    
    def evaluate_metrics(self, metrics: Dict[str, Any]) -> None:
        """评估指标并生成告警.
        
        Args:
            metrics: 指标数据
        """
        # 检查系统资源告警
        gauges = metrics.get('gauges', {})
        
        # CPU使用率告警
        cpu_usage = gauges.get('system_health.system_cpu_usage')
        if cpu_usage is not None:
            if cpu_usage > 90:
                self._trigger_alert(
                    name="high_cpu_usage",
                    severity=AlertSeverity.CRITICAL,
                    message=f"High CPU usage: {cpu_usage:.1f}%",
                    component="system",
                    details={'cpu_usage': cpu_usage}
                )
            elif cpu_usage > 80:
                self._trigger_alert(
                    name="high_cpu_usage",
                    severity=AlertSeverity.WARNING,
                    message=f"Elevated CPU usage: {cpu_usage:.1f}%",
                    component="system",
                    details={'cpu_usage': cpu_usage}
                )
            else:
                self._resolve_alert("high_cpu_usage")
        
        # 内存使用率告警
        memory_usage = gauges.get('system_health.system_memory_usage')
        if memory_usage is not None:
            if memory_usage > 90:
                self._trigger_alert(
                    name="high_memory_usage",
                    severity=AlertSeverity.CRITICAL,
                    message=f"High memory usage: {memory_usage:.1f}%",
                    component="system",
                    details={'memory_usage': memory_usage}
                )
            elif memory_usage > 80:
                self._trigger_alert(
                    name="high_memory_usage",
                    severity=AlertSeverity.WARNING,
                    message=f"Elevated memory usage: {memory_usage:.1f}%",
                    component="system",
                    details={'memory_usage': memory_usage}
                )
            else:
                self._resolve_alert("high_memory_usage")
        
        # 磁盘使用率告警
        disk_usage = gauges.get('system_health.system_disk_usage')
        if disk_usage is not None:
            if disk_usage > 95:
                self._trigger_alert(
                    name="high_disk_usage",
                    severity=AlertSeverity.CRITICAL,
                    message=f"High disk usage: {disk_usage:.1f}%",
                    component="system",
                    details={'disk_usage': disk_usage}
                )
            elif disk_usage > 85:
                self._trigger_alert(
                    name="high_disk_usage",
                    severity=AlertSeverity.WARNING,
                    message=f"Elevated disk usage: {disk_usage:.1f}%",
                    component="system",
                    details={'disk_usage': disk_usage}
                )
            else:
                self._resolve_alert("high_disk_usage")
        
        # 游戏进程告警
        game_process_count = gauges.get('game_performance.game_process_count')
        if game_process_count is not None:
            if game_process_count == 0:
                self._trigger_alert(
                    name="no_game_process",
                    severity=AlertSeverity.WARNING,
                    message="No game processes detected",
                    component="game",
                    details={'process_count': game_process_count}
                )
            else:
                self._resolve_alert("no_game_process")
    
    def _trigger_alert(self, name: str, severity: AlertSeverity, message: str, 
                      component: str, details: Optional[Dict[str, Any]] = None) -> None:
        """触发告警.
        
        Args:
            name: 告警名称
            severity: 严重程度
            message: 告警消息
            component: 组件名称
            details: 详细信息
        """
        current_time = time.time()
        
        # 检查冷却时间
        last_time = self._last_alert_time.get(name, 0)
        if current_time - last_time < 300:  # 5分钟冷却
            return
        
        with self._lock:
            # 检查是否已有活跃告警
            if name in self._active_alerts:
                # 更新现有告警
                alert = self._active_alerts[name]
                alert.severity = severity
                alert.message = message
                alert.details = details or {}
                alert.timestamp = current_time
                
                # 发送通知（因为超过了冷却时间）
                self._send_notification(alert)
                
                self._logger.warning(f"Alert updated: {name} - {message}")
            else:
                # 创建新告警
                alert = Alert(
                    name=name,
                    severity=severity,
                    status=AlertStatus.ACTIVE,
                    message=message,
                    component=component,
                    timestamp=current_time,
                    details=details or {}
                )
                
                self._active_alerts[name] = alert
                self._alert_history.append(alert)
                
                # 发送通知
                self._send_notification(alert)
                
                self._logger.warning(f"Alert triggered: {name} - {message}")
        
        self._last_alert_time[name] = current_time
    
    def _resolve_alert(self, name: str) -> None:
        """解决告警.
        
        Args:
            name: 告警名称
        """
        with self._lock:
            if name in self._active_alerts:
                alert = self._active_alerts[name]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = time.time()
                
                del self._active_alerts[name]
                
                self._logger.info(f"Alert resolved: {name} (duration: {alert.duration:.1f}s)")
    
    def _send_notification(self, alert: Alert) -> None:
        """发送告警通知.
        
        Args:
            alert: 告警对象
        """
        for handler in self._notification_handlers:
            try:
                handler(alert)
            except Exception as e:
                self._logger.error(f"Notification handler failed: {e}", exc_info=True)
    
    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警列表.
        
        Returns:
            活跃告警列表
        """
        with self._lock:
            return list(self._active_alerts.values())
    
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """获取告警历史.
        
        Args:
            hours: 查询小时数
            
        Returns:
            告警历史列表
        """
        cutoff_time = time.time() - (hours * 3600)
        
        with self._lock:
            return [alert for alert in self._alert_history if alert.timestamp >= cutoff_time]
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """获取告警统计信息.
        
        Returns:
            告警统计信息
        """
        with self._lock:
            active_count = len(self._active_alerts)
            
            # 按严重程度统计活跃告警
            severity_counts = {
                AlertSeverity.CRITICAL.value: 0,
                AlertSeverity.WARNING.value: 0,
                AlertSeverity.INFO.value: 0
            }
            
            for alert in self._active_alerts.values():
                severity_counts[alert.severity.value] += 1
            
            # 24小时内告警统计
            recent_alerts = self.get_alert_history(24)
            recent_count = len(recent_alerts)
            
            return {
                'active_alerts': active_count,
                'recent_alerts_24h': recent_count,
                'severity_breakdown': severity_counts,
                'total_rules': len(self._rules)
            }


def create_console_notification_handler() -> Callable[[Alert], None]:
    """创建控制台通知处理器.
    
    Returns:
        控制台通知处理函数
    """
    logger = logging.getLogger('alert_notifications')
    
    def handler(alert: Alert) -> None:
        """控制台通知处理器.
        
        Args:
            alert: 告警对象
        """
        timestamp = datetime.fromtimestamp(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S')
        message = f"[{alert.severity.value.upper()}] {timestamp} - {alert.component}: {alert.message}"
        
        if alert.severity == AlertSeverity.CRITICAL:
            logger.error(message)
        elif alert.severity == AlertSeverity.WARNING:
            logger.warning(message)
        else:
            logger.info(message)
    
    return handler