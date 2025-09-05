"""告警管理器模块。.

提供系统告警的管理和处理功能。
"""

import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class AlertLevel(Enum):
    """告警级别枚举。"""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """告警状态枚举。"""

    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    ACKNOWLEDGED = "acknowledged"


@dataclass
class Alert:
    """告警数据类。"""

    id: str
    title: str
    message: str
    level: AlertLevel
    source: str
    timestamp: float = field(default_factory=time.time)
    status: AlertStatus = AlertStatus.ACTIVE
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    resolved_at: Optional[float] = None
    acknowledged_at: Optional[float] = None
    acknowledged_by: Optional[str] = None


@dataclass
class AlertRule:
    """告警规则数据类。"""

    id: str
    name: str
    condition: Callable[[Any], bool]
    level: AlertLevel
    message_template: str
    enabled: bool = True
    cooldown: float = 300.0  # 5分钟冷却时间
    last_triggered: Optional[float] = None
    labels: Dict[str, str] = field(default_factory=dict)


class AlertManager:
    """告警管理器。

    负责管理系统告警的创建、处理、通知和存储。
    """

    def __init__(self, max_alerts: int = 1000):
        """初始化告警管理器。

        Args:
            max_alerts: 最大告警数量
        """
        self._alerts: Dict[str, Alert] = {}
        self._rules: Dict[str, AlertRule] = {}
        self._handlers: Dict[AlertLevel, List[Callable]] = defaultdict(list)
        self._alert_history: deque = deque(maxlen=max_alerts)
        self._max_alerts = max_alerts
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        self._stats = {
            "total_alerts": 0,
            "active_alerts": 0,
            "resolved_alerts": 0,
            "suppressed_alerts": 0,
        }

    def create_alert(
        self,
        title: str,
        message: str,
        level: AlertLevel,
        source: str,
        rule_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        labels: Optional[Dict[str, str]] = None,
        annotations: Optional[Dict[str, str]] = None,
        alert_id: Optional[str] = None,
    ) -> str:
        """创建告警。

        Args:
            title: 告警标题
            message: 告警消息
            level: 告警级别
            source: 告警源
            rule_id: 关联的规则ID
            data: 告警数据
            labels: 标签
            annotations: 注释
            alert_id: 自定义告警ID

        Returns:
            告警ID
        """
        import uuid

        if alert_id is None:
            alert_id = str(uuid.uuid4())

        alert = Alert(
            id=alert_id,
            title=title,
            message=message,
            level=level,
            source=source,
            labels=labels or {},
            annotations=annotations or {},
        )

        with self._lock:
            self._alerts[alert_id] = alert
            self._alert_history.append(alert)
            self._stats["total_alerts"] += 1
            self._stats["active_alerts"] += 1

        # 触发处理器
        self._trigger_handlers(alert)

        self._logger.info(f"Alert created: {alert_id} - {title}")
        return alert_id

    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警。

        Args:
            alert_id: 告警ID

        Returns:
            是否成功解决
        """
        with self._lock:
            if alert_id not in self._alerts:
                return False

            alert = self._alerts[alert_id]
            if alert.status == AlertStatus.ACTIVE:
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = time.time()
                self._stats["active_alerts"] -= 1
                self._stats["resolved_alerts"] += 1

                self._logger.info(f"Alert resolved: {alert_id}")
                return True

        return False

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """确认告警。

        Args:
            alert_id: 告警ID
            acknowledged_by: 确认人

        Returns:
            是否成功确认
        """
        with self._lock:
            if alert_id not in self._alerts:
                return False

            alert = self._alerts[alert_id]
            if alert.status == AlertStatus.ACTIVE:
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = time.time()
                alert.acknowledged_by = acknowledged_by

                self._logger.info(
                    f"Alert acknowledged: {alert_id} by {acknowledged_by}"
                )
                return True

        return False

    def suppress_alert(self, alert_id: str) -> bool:
        """抑制告警。

        Args:
            alert_id: 告警ID

        Returns:
            是否成功抑制
        """
        with self._lock:
            if alert_id not in self._alerts:
                return False

            alert = self._alerts[alert_id]
            if alert.status == AlertStatus.ACTIVE:
                alert.status = AlertStatus.SUPPRESSED
                self._stats["active_alerts"] -= 1
                self._stats["suppressed_alerts"] += 1

                self._logger.info(f"Alert suppressed: {alert_id}")
                return True

        return False

    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """获取告警。

        Args:
            alert_id: 告警ID

        Returns:
            告警对象
        """
        with self._lock:
            return self._alerts.get(alert_id)

    def get_alerts(
        self,
        status: Optional[AlertStatus] = None,
        level: Optional[AlertLevel] = None,
        source: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Alert]:
        """获取告警列表。

        Args:
            status: 过滤状态
            level: 过滤级别
            source: 过滤源
            limit: 限制数量

        Returns:
            告警列表
        """
        with self._lock:
            alerts = list(self._alerts.values())

        # 应用过滤器
        if status is not None:
            alerts = [a for a in alerts if a.status == status]
        if level is not None:
            alerts = [a for a in alerts if a.level == level]
        if source is not None:
            alerts = [a for a in alerts if a.source == source]

        # 按时间戳排序（最新的在前）
        alerts.sort(key=lambda x: x.timestamp, reverse=True)

        # 应用限制
        if limit is not None:
            alerts = alerts[:limit]

        return alerts

    def add_rule(self, rule: AlertRule) -> None:
        """添加告警规则。

        Args:
            rule: 告警规则
        """
        with self._lock:
            self._rules[rule.id] = rule

        self._logger.info(f"Alert rule added: {rule.id} - {rule.name}")

    def remove_rule(self, rule_id: str) -> bool:
        """移除告警规则。

        Args:
            rule_id: 规则ID

        Returns:
            是否成功移除
        """
        with self._lock:
            if rule_id in self._rules:
                del self._rules[rule_id]
                self._logger.info(f"Alert rule removed: {rule_id}")
                return True

        return False

    def evaluate_rules(self, data: Any) -> List[str]:
        """评估告警规则。

        Args:
            data: 评估数据

        Returns:
            触发的告警ID列表
        """
        triggered_alerts = []
        current_time = time.time()

        with self._lock:
            for rule in self._rules.values():
                if not rule.enabled:
                    continue

                # 检查冷却时间
                if (
                    rule.last_triggered is not None
                    and current_time - rule.last_triggered < rule.cooldown
                ):
                    continue

                try:
                    if rule.condition(data):
                        # 创建告警
                        alert_id = self.create_alert(
                            title=rule.name,
                            message=rule.message_template,
                            level=rule.level,
                            source="rule_engine",
                            labels=rule.labels.copy(),
                        )

                        rule.last_triggered = current_time
                        triggered_alerts.append(alert_id)

                except Exception as e:
                    self._logger.error(f"Error evaluating rule {rule.id}: {e}")

        return triggered_alerts

    def add_handler(self, level: AlertLevel, handler: Callable[[Alert], None]) -> None:
        """添加告警处理器。

        Args:
            level: 告警级别
            handler: 处理器函数
        """
        with self._lock:
            self._handlers[level].append(handler)

    def remove_handler(
        self, level: AlertLevel, handler: Callable[[Alert], None]
    ) -> bool:
        """移除告警处理器。

        Args:
            level: 告警级别
            handler: 处理器函数

        Returns:
            是否成功移除
        """
        with self._lock:
            if handler in self._handlers[level]:
                self._handlers[level].remove(handler)
                return True

        return False

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息。

        Returns:
            统计信息字典
        """
        with self._lock:
            stats = self._stats.copy()
            stats["total_rules"] = len(self._rules)
            stats["enabled_rules"] = len([r for r in self._rules.values() if r.enabled])
            stats["total_handlers"] = sum(
                len(handlers) for handlers in self._handlers.values()
            )

        return stats

    def clear_resolved_alerts(self, older_than: Optional[float] = None) -> int:
        """清理已解决的告警。

        Args:
            older_than: 清理早于指定时间的告警（秒）

        Returns:
            清理的告警数量
        """
        if older_than is None:
            older_than = 24 * 3600  # 默认24小时

        current_time = time.time()
        cutoff_time = current_time - older_than

        cleared_count = 0

        with self._lock:
            alerts_to_remove = []

            for alert_id, alert in self._alerts.items():
                if (
                    alert.status == AlertStatus.RESOLVED
                    and alert.resolved_at is not None
                    and alert.resolved_at < cutoff_time
                ):
                    alerts_to_remove.append(alert_id)

            for alert_id in alerts_to_remove:
                del self._alerts[alert_id]
                cleared_count += 1
                self._stats["resolved_alerts"] -= 1

        if cleared_count > 0:
            self._logger.info(f"Cleared {cleared_count} resolved alerts")

        return cleared_count

    def _trigger_handlers(self, alert: Alert) -> None:
        """触发告警处理器。

        Args:
            alert: 告警对象
        """
        handlers = self._handlers.get(alert.level, [])

        for handler in handlers:
            try:
                handler(alert)
            except Exception as e:
                self._logger.error(f"Error in alert handler: {e}")
