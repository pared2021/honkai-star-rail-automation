# -*- coding: utf-8 -*-
"""
告警管理系统 - 处理和管理各种系统告警
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
import json
from queue import Empty, Queue
import smtplib
from threading import Lock, Thread
import time
from typing import Any, Callable, Dict, List, Optional, Set

from PyQt6.QtCore import QObject, pyqtSignal

from src.core.logger import get_logger

logger = get_logger(__name__)

from src.monitoring.logging_monitoring_service import LogLevel, MonitoringEventType
from src.services.event_bus import EventBus


class AlertSeverity(Enum):
    """告警严重程度"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """告警状态"""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class AlertChannel(Enum):
    """告警通道"""

    EMAIL = "email"
    DESKTOP = "desktop"
    LOG = "log"
    WEBHOOK = "webhook"
    SMS = "sms"


@dataclass
class AlertRule:
    """告警规则"""

    id: str
    name: str
    description: str
    condition: str  # 条件表达式
    severity: AlertSeverity
    channels: List[AlertChannel]
    enabled: bool = True
    cooldown_minutes: int = 5  # 冷却时间（分钟）
    max_alerts_per_hour: int = 10  # 每小时最大告警数
    tags: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Alert:
    """告警实例"""

    id: str
    rule_id: str
    title: str
    message: str
    severity: AlertSeverity
    status: AlertStatus
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    notification_count: int = 0
    last_notification_at: Optional[datetime] = None


@dataclass
class NotificationConfig:
    """通知配置"""

    email_enabled: bool = False
    email_smtp_server: str = ""
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_from: str = ""
    email_to: List[str] = field(default_factory=list)

    desktop_enabled: bool = True

    webhook_enabled: bool = False
    webhook_url: str = ""
    webhook_headers: Dict[str, str] = field(default_factory=dict)

    sms_enabled: bool = False
    sms_api_key: str = ""
    sms_numbers: List[str] = field(default_factory=list)


class AlertEvaluator:
    """告警条件评估器"""

    def __init__(self):
        self.functions = {
            "cpu_usage": self._get_cpu_usage,
            "memory_usage": self._get_memory_usage,
            "disk_usage": self._get_disk_usage,
            "error_count": self._get_error_count,
            "task_failure_rate": self._get_task_failure_rate,
            "response_time": self._get_response_time,
            "cache_hit_rate": self._get_cache_hit_rate,
        }

        # 缓存的指标数据
        self.metrics_cache = {}
        self.cache_lock = Lock()

    def evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """评估告警条件"""
        try:
            # 更新上下文
            eval_context = {
                **self.functions,
                **context,
                "datetime": datetime,
                "timedelta": timedelta,
            }

            # 安全评估条件
            result = eval(condition, {"__builtins__": {}}, eval_context)
            return bool(result)

        except Exception as e:
            logger.error(f"评估告警条件失败: {condition}, 错误: {e}")
            return False

    def update_metrics(self, metrics: Dict[str, Any]):
        """更新指标缓存"""
        with self.cache_lock:
            self.metrics_cache.update(metrics)
            self.metrics_cache["last_update"] = datetime.now()

    def _get_cpu_usage(self) -> float:
        """获取CPU使用率"""
        with self.cache_lock:
            return self.metrics_cache.get("cpu_percent", 0.0)

    def _get_memory_usage(self) -> float:
        """获取内存使用率"""
        with self.cache_lock:
            return self.metrics_cache.get("memory_percent", 0.0)

    def _get_disk_usage(self) -> float:
        """获取磁盘使用率"""
        with self.cache_lock:
            return self.metrics_cache.get("disk_percent", 0.0)

    def _get_error_count(self, minutes: int = 5) -> int:
        """获取指定时间内的错误数量"""
        with self.cache_lock:
            return self.metrics_cache.get(f"error_count_{minutes}m", 0)

    def _get_task_failure_rate(self, minutes: int = 10) -> float:
        """获取任务失败率"""
        with self.cache_lock:
            total = self.metrics_cache.get(f"total_tasks_{minutes}m", 0)
            failed = self.metrics_cache.get(f"failed_tasks_{minutes}m", 0)
            return (failed / total * 100) if total > 0 else 0.0

    def _get_response_time(self) -> float:
        """获取平均响应时间"""
        with self.cache_lock:
            return self.metrics_cache.get("avg_response_time", 0.0)

    def _get_cache_hit_rate(self) -> float:
        """获取缓存命中率"""
        with self.cache_lock:
            return self.metrics_cache.get("cache_hit_rate", 0.0)


class NotificationSender:
    """通知发送器"""

    def __init__(self, config: NotificationConfig):
        self.config = config
        self.send_queue = Queue()
        self.sender_thread = None
        self.running = False

    def start(self):
        """启动通知发送器"""
        if not self.running:
            self.running = True
            self.sender_thread = Thread(target=self._sender_loop, daemon=True)
            self.sender_thread.start()
            logger.info("通知发送器已启动")

    def stop(self):
        """停止通知发送器"""
        self.running = False
        if self.sender_thread:
            self.sender_thread.join(timeout=5)
        logger.info("通知发送器已停止")

    def send_notification(self, alert: Alert, channels: List[AlertChannel]):
        """发送通知"""
        for channel in channels:
            self.send_queue.put((alert, channel))

    def _sender_loop(self):
        """发送器主循环"""
        while self.running:
            try:
                alert, channel = self.send_queue.get(timeout=1)
                self._send_single_notification(alert, channel)
                self.send_queue.task_done()
            except Empty:
                continue
            except Exception as e:
                logger.error(f"发送通知失败: {e}")

    def _send_single_notification(self, alert: Alert, channel: AlertChannel):
        """发送单个通知"""
        try:
            if channel == AlertChannel.EMAIL and self.config.email_enabled:
                self._send_email(alert)
            elif channel == AlertChannel.DESKTOP and self.config.desktop_enabled:
                self._send_desktop_notification(alert)
            elif channel == AlertChannel.LOG:
                self._send_log_notification(alert)
            elif channel == AlertChannel.WEBHOOK and self.config.webhook_enabled:
                self._send_webhook(alert)
            elif channel == AlertChannel.SMS and self.config.sms_enabled:
                self._send_sms(alert)

            logger.debug(f"通知已发送: {channel.value} - {alert.title}")

        except Exception as e:
            logger.error(f"发送{channel.value}通知失败: {e}")

    def _send_email(self, alert: Alert):
        """发送邮件通知"""
        if not self.config.email_to:
            return

        msg = MIMEMultipart()
        msg["From"] = self.config.email_from
        msg["To"] = ", ".join(self.config.email_to)
        msg["Subject"] = f"[{alert.severity.value.upper()}] {alert.title}"

        # 邮件内容
        body = f"""
告警详情:

标题: {alert.title}
严重程度: {alert.severity.value.upper()}
来源: {alert.source}
时间: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}
状态: {alert.status.value}

消息:
{alert.message}

数据:
{json.dumps(alert.data, indent=2, ensure_ascii=False)}

标签:
{json.dumps(alert.tags, indent=2, ensure_ascii=False)}
        """

        msg.attach(MIMEText(body, "plain", "utf-8"))

        # 发送邮件
        with smtplib.SMTP(
            self.config.email_smtp_server, self.config.email_smtp_port
        ) as server:
            server.starttls()
            server.login(self.config.email_username, self.config.email_password)
            server.send_message(msg)

    def _send_desktop_notification(self, alert: Alert):
        """发送桌面通知"""
        try:
            import plyer

            plyer.notification.notify(
                title=f"[{alert.severity.value.upper()}] {alert.title}",
                message=alert.message[:200],  # 限制长度
                timeout=10,
            )
        except ImportError:
            logger.warning("plyer库未安装，无法发送桌面通知")
        except Exception as e:
            logger.error(f"发送桌面通知失败: {e}")

    def _send_log_notification(self, alert: Alert):
        """发送日志通知"""
        level_map = {
            AlertSeverity.LOW: logger.info,
            AlertSeverity.MEDIUM: logger.warning,
            AlertSeverity.HIGH: logger.error,
            AlertSeverity.CRITICAL: logger.critical,
        }

        log_func = level_map.get(alert.severity, logger.info)
        log_func(f"告警: {alert.title} - {alert.message}")

    def _send_webhook(self, alert: Alert):
        """发送Webhook通知"""
        try:
            import requests

            payload = {
                "id": alert.id,
                "title": alert.title,
                "message": alert.message,
                "severity": alert.severity.value,
                "status": alert.status.value,
                "source": alert.source,
                "created_at": alert.created_at.isoformat(),
                "data": alert.data,
                "tags": alert.tags,
            }

            response = requests.post(
                self.config.webhook_url,
                json=payload,
                headers=self.config.webhook_headers,
                timeout=10,
            )
            response.raise_for_status()

        except ImportError:
            logger.warning("requests库未安装，无法发送Webhook通知")
        except Exception as e:
            logger.error(f"发送Webhook通知失败: {e}")

    def _send_sms(self, alert: Alert):
        """发送短信通知"""
        # 这里可以集成短信服务API
        logger.info(f"短信通知: {alert.title} - {alert.message}")


class AlertManager(QObject):
    """告警管理器"""

    # 信号定义
    alert_created = pyqtSignal(dict)  # 告警创建
    alert_updated = pyqtSignal(dict)  # 告警更新
    alert_resolved = pyqtSignal(dict)  # 告警解决

    def __init__(
        self, event_bus: EventBus, notification_config: NotificationConfig = None
    ):
        super().__init__()

        self.event_bus = event_bus
        self.notification_config = notification_config or NotificationConfig()

        # 组件
        self.evaluator = AlertEvaluator()
        self.notification_sender = NotificationSender(self.notification_config)

        # 数据存储
        self.rules: Dict[str, AlertRule] = {}
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []

        # 状态管理
        self.running = False
        self.evaluation_thread = None
        self.data_lock = Lock()

        # 统计信息
        self.stats = {
            "total_alerts": 0,
            "active_alerts": 0,
            "resolved_alerts": 0,
            "notifications_sent": 0,
            "rules_evaluated": 0,
        }

        # 设置默认规则
        self._setup_default_rules()

        # 连接事件
        self._setup_event_handlers()

        logger.info("告警管理器初始化完成")

    def start(self):
        """启动告警管理器"""
        if not self.running:
            self.running = True
            self.notification_sender.start()

            # 启动评估线程
            self.evaluation_thread = Thread(target=self._evaluation_loop, daemon=True)
            self.evaluation_thread.start()

            logger.info("告警管理器已启动")

    def stop(self):
        """停止告警管理器"""
        self.running = False
        self.notification_sender.stop()

        if self.evaluation_thread:
            self.evaluation_thread.join(timeout=5)

        logger.info("告警管理器已停止")

    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        with self.data_lock:
            self.rules[rule.id] = rule

        logger.info(f"添加告警规则: {rule.name}")

    def remove_rule(self, rule_id: str):
        """移除告警规则"""
        with self.data_lock:
            if rule_id in self.rules:
                del self.rules[rule_id]
                logger.info(f"移除告警规则: {rule_id}")

    def update_rule(self, rule: AlertRule):
        """更新告警规则"""
        with self.data_lock:
            if rule.id in self.rules:
                rule.updated_at = datetime.now()
                self.rules[rule.id] = rule
                logger.info(f"更新告警规则: {rule.name}")

    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """获取告警规则"""
        with self.data_lock:
            return self.rules.get(rule_id)

    def get_all_rules(self) -> List[AlertRule]:
        """获取所有告警规则"""
        with self.data_lock:
            return list(self.rules.values())

    def create_alert(
        self,
        rule_id: str,
        title: str,
        message: str,
        source: str,
        data: Dict[str, Any] = None,
        tags: Dict[str, str] = None,
    ) -> Optional[Alert]:
        """创建告警"""
        rule = self.get_rule(rule_id)
        if not rule or not rule.enabled:
            return None

        # 检查冷却时间
        if not self._check_cooldown(rule_id):
            return None

        # 检查频率限制
        if not self._check_rate_limit(rule_id):
            return None

        # 创建告警
        alert_id = f"{rule_id}_{int(datetime.now().timestamp())}"
        alert = Alert(
            id=alert_id,
            rule_id=rule_id,
            title=title,
            message=message,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            source=source,
            data=data or {},
            tags={**(tags or {}), **rule.tags},
        )

        with self.data_lock:
            self.alerts[alert_id] = alert
            self.alert_history.append(alert)
            self.stats["total_alerts"] += 1
            self.stats["active_alerts"] += 1

        # 发送通知
        self.notification_sender.send_notification(alert, rule.channels)
        self.stats["notifications_sent"] += 1

        # 发射信号
        self.alert_created.emit(self._alert_to_dict(alert))

        # 发送事件
        self.event_bus.emit(
            "alert_created",
            {
                "alert_id": alert_id,
                "rule_id": rule_id,
                "severity": rule.severity.value,
                "title": title,
                "message": message,
            },
        )

        logger.warning(f"创建告警: {title} (严重程度: {rule.severity.value})")
        return alert

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "system"):
        """确认告警"""
        with self.data_lock:
            alert = self.alerts.get(alert_id)
            if alert and alert.status == AlertStatus.ACTIVE:
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.now()
                alert.acknowledged_by = acknowledged_by
                alert.updated_at = datetime.now()

                # 发射信号
                self.alert_updated.emit(self._alert_to_dict(alert))

                logger.info(f"告警已确认: {alert_id} by {acknowledged_by}")

    def resolve_alert(self, alert_id: str, resolved_by: str = "system"):
        """解决告警"""
        with self.data_lock:
            alert = self.alerts.get(alert_id)
            if alert and alert.status in [AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED]:
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.now()
                alert.resolved_by = resolved_by
                alert.updated_at = datetime.now()

                self.stats["active_alerts"] -= 1
                self.stats["resolved_alerts"] += 1

                # 发射信号
                self.alert_resolved.emit(self._alert_to_dict(alert))

                # 发送事件
                self.event_bus.emit(
                    "alert_resolved", {"alert_id": alert_id, "resolved_by": resolved_by}
                )

                logger.info(f"告警已解决: {alert_id} by {resolved_by}")

    def suppress_alert(self, alert_id: str):
        """抑制告警"""
        with self.data_lock:
            alert = self.alerts.get(alert_id)
            if alert:
                alert.status = AlertStatus.SUPPRESSED
                alert.updated_at = datetime.now()

                if alert.status == AlertStatus.ACTIVE:
                    self.stats["active_alerts"] -= 1

                # 发射信号
                self.alert_updated.emit(self._alert_to_dict(alert))

                logger.info(f"告警已抑制: {alert_id}")

    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """获取告警"""
        with self.data_lock:
            return self.alerts.get(alert_id)

    def get_active_alerts(self) -> List[Alert]:
        """获取活动告警"""
        with self.data_lock:
            return [
                alert
                for alert in self.alerts.values()
                if alert.status == AlertStatus.ACTIVE
            ]

    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """按严重程度获取告警"""
        with self.data_lock:
            return [
                alert for alert in self.alerts.values() if alert.severity == severity
            ]

    def get_alerts_by_source(self, source: str) -> List[Alert]:
        """按来源获取告警"""
        with self.data_lock:
            return [alert for alert in self.alerts.values() if alert.source == source]

    def get_alerts(
        self, limit: Optional[int] = None, status: Optional[AlertStatus] = None
    ) -> List[Alert]:
        """获取告警列表"""
        with self.data_lock:
            alerts = list(self.alerts.values())

            # 按状态过滤
            if status:
                alerts = [alert for alert in alerts if alert.status == status]

            # 按创建时间排序（最新的在前）
            alerts.sort(key=lambda x: x.created_at, reverse=True)

            # 限制数量
            if limit:
                alerts = alerts[:limit]

            return alerts

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.data_lock:
            return {
                **self.stats,
                "rules_count": len(self.rules),
                "alerts_count": len(self.alerts),
                "history_count": len(self.alert_history),
            }

    def update_metrics(self, metrics: Dict[str, Any]):
        """更新指标数据"""
        self.evaluator.update_metrics(metrics)

    def _evaluation_loop(self):
        """评估循环"""
        while self.running:
            try:
                self._evaluate_rules()
                self.stats["rules_evaluated"] += 1
                time.sleep(30)  # 30秒评估一次
            except Exception as e:
                logger.error(f"规则评估失败: {e}")
                time.sleep(5)

    def _evaluate_rules(self):
        """评估所有规则"""
        with self.data_lock:
            rules = list(self.rules.values())

        for rule in rules:
            if not rule.enabled:
                continue

            try:
                # 评估条件
                context = {"rule": rule, "now": datetime.now()}

                if self.evaluator.evaluate_condition(rule.condition, context):
                    # 条件满足，创建告警
                    self.create_alert(
                        rule_id=rule.id,
                        title=rule.name,
                        message=rule.description,
                        source="rule_evaluation",
                        data={"condition": rule.condition},
                    )

            except Exception as e:
                logger.error(f"评估规则失败: {rule.name}, 错误: {e}")

    def _check_cooldown(self, rule_id: str) -> bool:
        """检查冷却时间"""
        rule = self.get_rule(rule_id)
        if not rule:
            return False

        # 查找最近的告警
        cutoff_time = datetime.now() - timedelta(minutes=rule.cooldown_minutes)

        with self.data_lock:
            recent_alerts = [
                alert
                for alert in self.alerts.values()
                if alert.rule_id == rule_id and alert.created_at > cutoff_time
            ]

        return len(recent_alerts) == 0

    def _check_rate_limit(self, rule_id: str) -> bool:
        """检查频率限制"""
        rule = self.get_rule(rule_id)
        if not rule:
            return False

        # 查找最近一小时的告警
        cutoff_time = datetime.now() - timedelta(hours=1)

        with self.data_lock:
            recent_alerts = [
                alert
                for alert in self.alerts.values()
                if alert.rule_id == rule_id and alert.created_at > cutoff_time
            ]

        return len(recent_alerts) < rule.max_alerts_per_hour

    def _alert_to_dict(self, alert: Alert) -> Dict[str, Any]:
        """将告警转换为字典"""
        return {
            "id": alert.id,
            "rule_id": alert.rule_id,
            "title": alert.title,
            "message": alert.message,
            "severity": alert.severity.value,
            "status": alert.status.value,
            "source": alert.source,
            "data": alert.data,
            "tags": alert.tags,
            "created_at": alert.created_at.isoformat(),
            "updated_at": alert.updated_at.isoformat(),
            "acknowledged_at": (
                alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
            ),
            "acknowledged_by": alert.acknowledged_by,
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
            "resolved_by": alert.resolved_by,
            "notification_count": alert.notification_count,
        }

    def _setup_default_rules(self):
        """设置默认告警规则"""
        default_rules = [
            AlertRule(
                id="high_cpu_usage",
                name="CPU使用率过高",
                description="CPU使用率超过80%",
                condition="cpu_usage() > 80",
                severity=AlertSeverity.HIGH,
                channels=[AlertChannel.DESKTOP, AlertChannel.LOG],
            ),
            AlertRule(
                id="high_memory_usage",
                name="内存使用率过高",
                description="内存使用率超过85%",
                condition="memory_usage() > 85",
                severity=AlertSeverity.HIGH,
                channels=[AlertChannel.DESKTOP, AlertChannel.LOG],
            ),
            AlertRule(
                id="critical_cpu_usage",
                name="CPU使用率严重过高",
                description="CPU使用率超过95%",
                condition="cpu_usage() > 95",
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.EMAIL, AlertChannel.DESKTOP, AlertChannel.LOG],
            ),
            AlertRule(
                id="high_error_rate",
                name="错误率过高",
                description="5分钟内错误数量超过10个",
                condition="error_count(5) > 10",
                severity=AlertSeverity.MEDIUM,
                channels=[AlertChannel.DESKTOP, AlertChannel.LOG],
            ),
            AlertRule(
                id="task_failure_rate",
                name="任务失败率过高",
                description="10分钟内任务失败率超过20%",
                condition="task_failure_rate(10) > 20",
                severity=AlertSeverity.HIGH,
                channels=[AlertChannel.DESKTOP, AlertChannel.LOG],
            ),
        ]

        for rule in default_rules:
            self.add_rule(rule)

    def _setup_event_handlers(self):
        """设置事件处理器"""
        # 监听系统事件
        self.event_bus.subscribe("system_error", self._handle_system_error)
        self.event_bus.subscribe("task_failed", self._handle_task_failed)
        self.event_bus.subscribe(
            "performance_warning", self._handle_performance_warning
        )
        self.event_bus.subscribe("automation_error", self._handle_automation_error)

    def _handle_system_error(self, event_data: Dict[str, Any]):
        """处理系统错误事件"""
        self.create_alert(
            rule_id="system_error",
            title="系统错误",
            message=event_data.get("message", "未知系统错误"),
            source="system",
            data=event_data,
        )

    def _handle_task_failed(self, event_data: Dict[str, Any]):
        """处理任务失败事件"""
        self.create_alert(
            rule_id="task_failure",
            title="任务执行失败",
            message=f"任务 {event_data.get('task_id', 'unknown')} 执行失败",
            source="task_manager",
            data=event_data,
        )

    def _handle_performance_warning(self, event_data: Dict[str, Any]):
        """处理性能警告事件"""
        self.create_alert(
            rule_id="performance_warning",
            title="性能警告",
            message=event_data.get("message", "性能指标异常"),
            source="performance_monitor",
            data=event_data,
        )

    def _handle_automation_error(self, event_data: Dict[str, Any]):
        """处理自动化错误事件"""
        self.create_alert(
            rule_id="automation_error",
            title="自动化操作错误",
            message=event_data.get("message", "自动化操作失败"),
            source="automation_controller",
            data=event_data,
        )


# 全局告警管理器实例
_alert_manager_instance: Optional[AlertManager] = None


def get_alert_manager() -> Optional[AlertManager]:
    """获取全局告警管理器实例"""
    return _alert_manager_instance


def set_alert_manager(alert_manager: AlertManager):
    """设置全局告警管理器实例"""
    global _alert_manager_instance
    _alert_manager_instance = alert_manager
