# -*- coding: utf-8 -*-
"""
日志和监控服务 - 统一管理日志记录和系统监控
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
import json
import os
from pathlib import Path
import threading
from typing import Any, Callable, Dict, List, Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from loguru import logger

from src.core.enums import TaskStatus
from src.core.logger import get_logger, log_error_with_context
from src.core.performance_monitor import PerformanceLevel, PerformanceMonitor
from src.monitoring.task_monitor import TaskMonitor, TaskStatusUpdate


class LogLevel(Enum):
    """日志级别"""

    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class MonitoringEventType(Enum):
    """监控事件类型"""

    PERFORMANCE_WARNING = "performance_warning"
    PERFORMANCE_CRITICAL = "performance_critical"
    TASK_STATUS_CHANGE = "task_status_change"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    SYSTEM_ERROR = "system_error"
    AUTOMATION_ACTION = "automation_action"
    GAME_STATE_CHANGE = "game_state_change"
    RESOURCE_USAGE = "resource_usage"
    CACHE_OPERATION = "cache_operation"


@dataclass
class LogEntry:
    """日志条目"""

    timestamp: datetime
    level: LogLevel
    message: str
    module: str
    function: str
    line: int
    thread_id: str
    task_id: Optional[str] = None
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    exception: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["level"] = self.level.value
        return data


@dataclass
class MonitoringEvent:
    """监控事件"""

    timestamp: datetime
    event_type: MonitoringEventType
    source: str
    data: Dict[str, Any]
    severity: str = "info"
    task_id: Optional[str] = None
    user_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["event_type"] = self.event_type.value
        return data


@dataclass
class SystemMetrics:
    """系统指标"""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    performance_level: str
    cache_hit_rate: float
    automation_actions_per_minute: float

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


class LoggingMonitoringService(QObject):
    """日志和监控服务"""

    # 信号定义
    log_entry_added = pyqtSignal(dict)  # 新日志条目
    monitoring_event_triggered = pyqtSignal(dict)  # 监控事件
    system_metrics_updated = pyqtSignal(dict)  # 系统指标更新
    alert_triggered = pyqtSignal(str, str, dict)  # 告警触发 (level, message, data)

    def __init__(
        self,
        performance_monitor: PerformanceMonitor,
        task_monitor: TaskMonitor,
        log_directory: str = "logs",
        config_manager=None,
    ):
        """初始化日志和监控服务

        Args:
            performance_monitor: 性能监控器
            task_monitor: 任务监控器
            log_directory: 日志目录
            config_manager: 配置管理器
        """
        super().__init__()

        self.performance_monitor = performance_monitor
        self.task_monitor = task_monitor
        self.log_directory = Path(log_directory)
        self.config_manager = config_manager

        # 确保日志目录存在
        self.log_directory.mkdir(exist_ok=True)

        # 日志和事件存储
        self.log_entries: List[LogEntry] = []
        self.monitoring_events: List[MonitoringEvent] = []
        self.system_metrics_history: List[SystemMetrics] = []

        # 配置
        self.max_log_entries = self._get_config_value('monitoring.max_log_entries', 10000)
        self.max_events = self._get_config_value('monitoring.max_events', 5000)
        self.max_metrics_history = self._get_config_value('monitoring.max_metrics_history', 1440)  # 24小时的分钟数
        self.metrics_collection_interval = self._get_config_value('monitoring.metrics_collection_interval', 60)  # 秒

        # 告警配置
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.alert_callbacks: Dict[str, Callable] = {}

        # 运行状态
        self.is_running = False
        self.metrics_timer = QTimer()
        self.metrics_timer.timeout.connect(self._collect_system_metrics)

        # 文件输出配置
        self.enable_file_output = self._get_config_value('monitoring.enable_file_output', True)
        self.log_rotation_size = self._get_config_value('monitoring.log_rotation_size', 10 * 1024 * 1024)  # 10MB
        self.log_retention_days = self._get_config_value('monitoring.log_retention_days', 30)

        # 初始化
        self._setup_performance_callbacks()
        self._setup_task_callbacks()
        self._setup_default_alert_rules()

        logger.info("日志和监控服务初始化完成")

    def _get_config_value(self, key: str, default_value):
        """从配置管理器获取配置值
        
        Args:
            key: 配置键
            default_value: 默认值
            
        Returns:
            配置值或默认值
        """
        if self.config_manager:
            return self.config_manager.get(key, default_value)
        return default_value

    def start(self):
        """启动服务"""
        if self.is_running:
            logger.warning("日志和监控服务已在运行")
            return

        self.is_running = True

        # 启动性能监控
        self.performance_monitor.start_monitoring()

        # 启动任务监控
        self.task_monitor.start_monitoring()

        # 启动指标收集
        self.metrics_timer.start(self.metrics_collection_interval * 1000)

        logger.info("日志和监控服务已启动")

    def stop(self):
        """停止服务"""
        if not self.is_running:
            return

        self.is_running = False

        # 停止定时器
        self.metrics_timer.stop()

        # 停止监控器
        self.performance_monitor.stop_monitoring()
        self.task_monitor.stop_monitoring()

        # 保存数据
        self._save_logs_to_file()
        self._save_events_to_file()
        self._save_metrics_to_file()

        logger.info("日志和监控服务已停止")

    def add_log_entry(
        self,
        level: LogLevel,
        message: str,
        module: str = "",
        function: str = "",
        line: int = 0,
        task_id: Optional[str] = None,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[str] = None,
    ):
        """添加日志条目

        Args:
            level: 日志级别
            message: 日志消息
            module: 模块名
            function: 函数名
            line: 行号
            task_id: 任务ID
            user_id: 用户ID
            context: 上下文信息
            exception: 异常信息
        """
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=message,
            module=module,
            function=function,
            line=line,
            thread_id=str(threading.get_ident()),
            task_id=task_id,
            user_id=user_id,
            context=context,
            exception=exception,
        )

        # 添加到内存存储
        self.log_entries.append(entry)

        # 限制内存中的日志数量
        if len(self.log_entries) > self.max_log_entries:
            self.log_entries = self.log_entries[-self.max_log_entries :]

        # 发射信号
        self.log_entry_added.emit(entry.to_dict())

        # 检查告警规则
        self._check_log_alerts(entry)

        # 写入文件（如果启用）
        if self.enable_file_output:
            self._write_log_to_file(entry)

    def add_monitoring_event(
        self,
        event_type: MonitoringEventType,
        source: str,
        data: Dict[str, Any],
        severity: str = "info",
        task_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """添加监控事件

        Args:
            event_type: 事件类型
            source: 事件源
            data: 事件数据
            severity: 严重程度
            task_id: 任务ID
            user_id: 用户ID
        """
        event = MonitoringEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            source=source,
            data=data,
            severity=severity,
            task_id=task_id,
            user_id=user_id,
        )

        # 添加到内存存储
        self.monitoring_events.append(event)

        # 限制内存中的事件数量
        if len(self.monitoring_events) > self.max_events:
            self.monitoring_events = self.monitoring_events[-self.max_events :]

        # 发射信号
        self.monitoring_event_triggered.emit(event.to_dict())

        # 检查告警规则
        self._check_event_alerts(event)

        logger.debug(f"监控事件: {event_type.value} from {source}")

    def get_logs(
        self,
        level: Optional[LogLevel] = None,
        module: Optional[str] = None,
        task_id: Optional[str] = None,
        hours: int = 24,
    ) -> List[LogEntry]:
        """获取日志条目

        Args:
            level: 日志级别过滤
            module: 模块过滤
            task_id: 任务ID过滤
            hours: 时间范围（小时）

        Returns:
            List[LogEntry]: 过滤后的日志条目
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        filtered_logs = [
            entry for entry in self.log_entries if entry.timestamp >= cutoff_time
        ]

        if level:
            filtered_logs = [entry for entry in filtered_logs if entry.level == level]

        if module:
            filtered_logs = [entry for entry in filtered_logs if module in entry.module]

        if task_id:
            filtered_logs = [
                entry for entry in filtered_logs if entry.task_id == task_id
            ]

        return filtered_logs

    def get_events(
        self,
        event_type: Optional[MonitoringEventType] = None,
        source: Optional[str] = None,
        hours: int = 24,
    ) -> List[MonitoringEvent]:
        """获取监控事件

        Args:
            event_type: 事件类型过滤
            source: 事件源过滤
            hours: 时间范围（小时）

        Returns:
            List[MonitoringEvent]: 过滤后的监控事件
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        filtered_events = [
            event for event in self.monitoring_events if event.timestamp >= cutoff_time
        ]

        if event_type:
            filtered_events = [
                event for event in filtered_events if event.event_type == event_type
            ]

        if source:
            filtered_events = [
                event for event in filtered_events if source in event.source
            ]

        return filtered_events

    def get_system_metrics(self, hours: int = 1) -> List[SystemMetrics]:
        """获取系统指标

        Args:
            hours: 时间范围（小时）

        Returns:
            List[SystemMetrics]: 系统指标历史
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        return [
            metrics
            for metrics in self.system_metrics_history
            if metrics.timestamp >= cutoff_time
        ]

    def add_alert_rule(
        self,
        name: str,
        condition: Callable[[Any], bool],
        callback: Callable[[str, Any], None],
        description: str = "",
    ):
        """添加告警规则

        Args:
            name: 规则名称
            condition: 条件函数
            callback: 回调函数
            description: 规则描述
        """
        self.alert_rules[name] = {
            "condition": condition,
            "description": description,
            "enabled": True,
        }
        self.alert_callbacks[name] = callback

        logger.info(f"添加告警规则: {name}")

    def remove_alert_rule(self, name: str):
        """移除告警规则

        Args:
            name: 规则名称
        """
        self.alert_rules.pop(name, None)
        self.alert_callbacks.pop(name, None)

        logger.info(f"移除告警规则: {name}")

    def export_logs(
        self, filepath: str, hours: int = 24, level: Optional[LogLevel] = None
    ):
        """导出日志

        Args:
            filepath: 导出文件路径
            hours: 时间范围（小时）
            level: 日志级别过滤
        """
        logs = self.get_logs(level=level, hours=hours)

        export_data = {
            "export_time": datetime.now().isoformat(),
            "time_range_hours": hours,
            "log_count": len(logs),
            "logs": [log.to_dict() for log in logs],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"日志已导出到: {filepath}")

    def export_events(self, filepath: str, hours: int = 24):
        """导出监控事件

        Args:
            filepath: 导出文件路径
            hours: 时间范围（小时）
        """
        events = self.get_events(hours=hours)

        export_data = {
            "export_time": datetime.now().isoformat(),
            "time_range_hours": hours,
            "event_count": len(events),
            "events": [event.to_dict() for event in events],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"监控事件已导出到: {filepath}")

    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据

        Returns:
            Dict[str, Any]: 仪表板数据
        """
        current_metrics = self.performance_monitor.get_current_metrics()
        performance_summary = self.performance_monitor.get_performance_summary()

        # 统计最近的日志
        recent_logs = self.get_logs(hours=1)
        log_stats = {
            "total": len(recent_logs),
            "error": len([log for log in recent_logs if log.level == LogLevel.ERROR]),
            "warning": len(
                [log for log in recent_logs if log.level == LogLevel.WARNING]
            ),
            "info": len([log for log in recent_logs if log.level == LogLevel.INFO]),
        }

        # 统计最近的事件
        recent_events = self.get_events(hours=1)
        event_stats = {
            "total": len(recent_events),
            "critical": len(
                [event for event in recent_events if event.severity == "critical"]
            ),
            "warning": len(
                [event for event in recent_events if event.severity == "warning"]
            ),
            "info": len([event for event in recent_events if event.severity == "info"]),
        }

        # 任务统计
        all_task_status = self.task_monitor.get_all_task_status()
        task_stats = {
            "total": len(all_task_status),
            "running": len(
                [
                    status
                    for status in all_task_status.values()
                    if status.status == TaskStatus.RUNNING
                ]
            ),
            "completed": len(
                [
                    status
                    for status in all_task_status.values()
                    if status.status == TaskStatus.COMPLETED
                ]
            ),
            "failed": len(
                [
                    status
                    for status in all_task_status.values()
                    if status.status == TaskStatus.FAILED
                ]
            ),
        }

        return {
            "timestamp": datetime.now().isoformat(),
            "performance": {
                "current_metrics": (
                    current_metrics.to_dict() if current_metrics else None
                ),
                "summary": performance_summary,
            },
            "logs": log_stats,
            "events": event_stats,
            "tasks": task_stats,
            "system_health": self._get_system_health_status(),
        }

    def _setup_performance_callbacks(self):
        """设置性能监控回调"""

        def on_performance_warning(metrics, level):
            self.add_monitoring_event(
                MonitoringEventType.PERFORMANCE_WARNING,
                "performance_monitor",
                {
                    "level": level.value,
                    "cpu_percent": metrics.cpu_percent,
                    "memory_percent": metrics.memory_percent,
                },
                severity="warning",
            )

        def on_performance_critical(metrics, level):
            self.add_monitoring_event(
                MonitoringEventType.PERFORMANCE_CRITICAL,
                "performance_monitor",
                {
                    "level": level.value,
                    "cpu_percent": metrics.cpu_percent,
                    "memory_percent": metrics.memory_percent,
                },
                severity="critical",
            )

        def on_optimization_applied(strategies, level):
            self.add_monitoring_event(
                MonitoringEventType.RESOURCE_USAGE,
                "performance_optimizer",
                {
                    "strategies": [s.value for s in strategies],
                    "performance_level": level.value,
                },
                severity="info",
            )

        self.performance_monitor.set_callbacks(
            warning_callback=on_performance_warning,
            critical_callback=on_performance_critical,
            optimization_callback=on_optimization_applied,
        )

    def _setup_task_callbacks(self):
        """设置任务监控回调"""
        self.task_monitor.task_status_changed.connect(
            lambda task_id, status: self.add_monitoring_event(
                MonitoringEventType.TASK_STATUS_CHANGE,
                "task_monitor",
                {"task_id": task_id, "status": status},
                task_id=task_id,
            )
        )

        self.task_monitor.task_completed.connect(
            lambda task_id, success, message: self.add_monitoring_event(
                (
                    MonitoringEventType.TASK_COMPLETED
                    if success
                    else MonitoringEventType.TASK_FAILED
                ),
                "task_monitor",
                {"task_id": task_id, "success": success, "message": message},
                severity="info" if success else "warning",
                task_id=task_id,
            )
        )

    def _setup_default_alert_rules(self):
        """设置默认告警规则"""
        # CPU使用率告警
        self.add_alert_rule(
            "high_cpu_usage",
            lambda metrics: hasattr(metrics, "cpu_percent")
            and metrics.cpu_percent > 80,
            lambda name, data: self.alert_triggered.emit(
                "warning", "CPU使用率过高", data
            ),
            "CPU使用率超过80%时触发",
        )

        # 内存使用率告警
        self.add_alert_rule(
            "high_memory_usage",
            lambda metrics: hasattr(metrics, "memory_percent")
            and metrics.memory_percent > 85,
            lambda name, data: self.alert_triggered.emit(
                "critical", "内存使用率过高", data
            ),
            "内存使用率超过85%时触发",
        )

        # 任务失败告警
        self.add_alert_rule(
            "task_failure",
            lambda event: (
                hasattr(event, "event_type")
                and event.event_type == MonitoringEventType.TASK_FAILED
            ),
            lambda name, data: self.alert_triggered.emit("error", "任务执行失败", data),
            "任务执行失败时触发",
        )

    def _collect_system_metrics(self):
        """收集系统指标"""
        try:
            current_metrics = self.performance_monitor.get_current_metrics()
            if not current_metrics:
                return

            # 获取任务统计
            all_task_status = self.task_monitor.get_all_task_status()
            active_tasks = len(
                [s for s in all_task_status.values() if s.status == TaskStatus.RUNNING]
            )
            completed_tasks = len(
                [
                    s
                    for s in all_task_status.values()
                    if s.status == TaskStatus.COMPLETED
                ]
            )
            failed_tasks = len(
                [s for s in all_task_status.values() if s.status == TaskStatus.FAILED]
            )

            # 获取性能等级
            performance_level = self.performance_monitor._analyze_performance(
                current_metrics
            )

            # 获取缓存命中率
            cache_hit_rate = self.performance_monitor.image_metrics.get_cache_hit_rate()

            # 计算自动化操作频率（简化版）
            automation_actions_per_minute = 0.0  # 这里可以从自动化控制器获取实际数据

            # 获取磁盘使用率
            import psutil

            disk_usage = psutil.disk_usage("/")
            disk_usage_percent = (disk_usage.used / disk_usage.total) * 100

            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=current_metrics.cpu_percent,
                memory_percent=current_metrics.memory_percent,
                memory_used_mb=current_metrics.memory_used_mb,
                disk_usage_percent=disk_usage_percent,
                active_tasks=active_tasks,
                completed_tasks=completed_tasks,
                failed_tasks=failed_tasks,
                performance_level=performance_level.value,
                cache_hit_rate=cache_hit_rate,
                automation_actions_per_minute=automation_actions_per_minute,
            )

            # 添加到历史记录
            self.system_metrics_history.append(metrics)

            # 限制历史记录数量
            if len(self.system_metrics_history) > self.max_metrics_history:
                self.system_metrics_history = self.system_metrics_history[
                    -self.max_metrics_history :
                ]

            # 发射信号
            self.system_metrics_updated.emit(metrics.to_dict())

            # 检查告警
            self._check_metrics_alerts(metrics)

        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")

    def _check_log_alerts(self, entry: LogEntry):
        """检查日志告警"""
        for name, rule in self.alert_rules.items():
            if not rule["enabled"]:
                continue

            try:
                if rule["condition"](entry):
                    callback = self.alert_callbacks.get(name)
                    if callback:
                        callback(name, entry.to_dict())
            except Exception as e:
                logger.error(f"检查日志告警规则 {name} 失败: {e}")

    def _check_event_alerts(self, event: MonitoringEvent):
        """检查事件告警"""
        for name, rule in self.alert_rules.items():
            if not rule["enabled"]:
                continue

            try:
                if rule["condition"](event):
                    callback = self.alert_callbacks.get(name)
                    if callback:
                        callback(name, event.to_dict())
            except Exception as e:
                logger.error(f"检查事件告警规则 {name} 失败: {e}")

    def _check_metrics_alerts(self, metrics: SystemMetrics):
        """检查指标告警"""
        for name, rule in self.alert_rules.items():
            if not rule["enabled"]:
                continue

            try:
                if rule["condition"](metrics):
                    callback = self.alert_callbacks.get(name)
                    if callback:
                        callback(name, metrics.to_dict())
            except Exception as e:
                logger.error(f"检查指标告警规则 {name} 失败: {e}")

    def _get_system_health_status(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        current_metrics = self.performance_monitor.get_current_metrics()
        if not current_metrics:
            return {"status": "unknown", "score": 0}

        # 计算健康分数（0-100）
        cpu_score = max(0, 100 - current_metrics.cpu_percent)
        memory_score = max(0, 100 - current_metrics.memory_percent)

        # 检查最近的错误日志
        recent_errors = self.get_logs(level=LogLevel.ERROR, hours=1)
        error_score = max(0, 100 - len(recent_errors) * 10)

        # 检查任务失败率
        all_task_status = self.task_monitor.get_all_task_status()
        if all_task_status:
            failed_count = len(
                [s for s in all_task_status.values() if s.status == TaskStatus.FAILED]
            )
            failure_rate = failed_count / len(all_task_status)
            task_score = max(0, 100 - failure_rate * 100)
        else:
            task_score = 100

        # 综合评分
        overall_score = (cpu_score + memory_score + error_score + task_score) / 4

        # 确定状态
        if overall_score >= 80:
            status = "excellent"
        elif overall_score >= 60:
            status = "good"
        elif overall_score >= 40:
            status = "fair"
        elif overall_score >= 20:
            status = "poor"
        else:
            status = "critical"

        return {
            "status": status,
            "score": round(overall_score, 1),
            "components": {
                "cpu": round(cpu_score, 1),
                "memory": round(memory_score, 1),
                "errors": round(error_score, 1),
                "tasks": round(task_score, 1),
            },
        }

    def _write_log_to_file(self, entry: LogEntry):
        """写入日志到文件"""
        try:
            log_file = (
                self.log_directory / f"app_{datetime.now().strftime('%Y%m%d')}.log"
            )

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(
                    f"{entry.timestamp.isoformat()} [{entry.level.value}] "
                    f"{entry.module}:{entry.function}:{entry.line} - {entry.message}\n"
                )

                if entry.context:
                    f.write(
                        f"Context: {json.dumps(entry.context, ensure_ascii=False)}\n"
                    )

                if entry.exception:
                    f.write(f"Exception: {entry.exception}\n")

                f.write("\n")

        except Exception as e:
            logger.error(f"写入日志文件失败: {e}")

    def _save_logs_to_file(self):
        """保存日志到文件"""
        try:
            if not self.log_entries:
                return

            log_file = (
                self.log_directory
                / f"logs_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

            export_data = {
                "export_time": datetime.now().isoformat(),
                "log_count": len(self.log_entries),
                "logs": [log.to_dict() for log in self.log_entries],
            }

            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            logger.info(f"日志备份已保存到: {log_file}")

        except Exception as e:
            logger.error(f"保存日志备份失败: {e}")

    def _save_events_to_file(self):
        """保存事件到文件"""
        try:
            if not self.monitoring_events:
                return

            events_file = (
                self.log_directory
                / f"events_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

            export_data = {
                "export_time": datetime.now().isoformat(),
                "event_count": len(self.monitoring_events),
                "events": [event.to_dict() for event in self.monitoring_events],
            }

            with open(events_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            logger.info(f"事件备份已保存到: {events_file}")

        except Exception as e:
            logger.error(f"保存事件备份失败: {e}")

    def _save_metrics_to_file(self):
        """保存指标到文件"""
        try:
            if not self.system_metrics_history:
                return

            metrics_file = (
                self.log_directory
                / f"metrics_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

            export_data = {
                "export_time": datetime.now().isoformat(),
                "metrics_count": len(self.system_metrics_history),
                "metrics": [
                    metrics.to_dict() for metrics in self.system_metrics_history
                ],
            }

            with open(metrics_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            logger.info(f"指标备份已保存到: {metrics_file}")

        except Exception as e:
            logger.error(f"保存指标备份失败: {e}")
