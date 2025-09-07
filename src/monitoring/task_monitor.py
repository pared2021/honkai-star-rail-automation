"""任务监控器模块.

提供任务执行状态的监控功能。
"""

from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Set

from ..core.task_manager import TaskStatus


class MonitoringLevel(Enum):
    """监控级别枚举."""

    BASIC = "basic"
    DETAILED = "detailed"
    FULL = "full"


@dataclass
class TaskMetrics:
    """任务指标数据类."""

    task_id: str
    task_type: str
    status: TaskStatus
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    success_count: int = 0
    failure_count: int = 0
    retry_count: int = 0
    last_error: Optional[str] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    custom_metrics: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后处理."""
        if self.end_time and self.duration is None:
            self.duration = self.end_time - self.start_time


@dataclass
class TaskEvent:
    """任务事件数据类."""

    task_id: str
    event_type: str
    timestamp: float = field(default_factory=time.time)
    data: Dict[str, Any] = field(default_factory=dict)
    message: Optional[str] = None


class TaskMonitor:
    """任务监控器.

    负责监控任务执行状态和性能指标。
    """

    def __init__(
        self,
        monitoring_level: MonitoringLevel = MonitoringLevel.BASIC,
        max_events: int = 10000,
        max_metrics: int = 1000,
    ):
        """初始化任务监控器.

        Args:
            monitoring_level: 监控级别
            max_events: 最大事件数量
            max_metrics: 最大指标数量
        """
        self._monitoring_level = monitoring_level
        self._max_events = max_events
        self._max_metrics = max_metrics
        self._metrics: Dict[str, TaskMetrics] = {}
        self._events: List[TaskEvent] = []
        self._active_tasks: Set[str] = set()
        self._task_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._listeners: List[Callable[[TaskEvent], None]] = []
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start_monitoring(self) -> None:
        """开始监控."""
        if self._running:
            return

        self._running = True
        if self._monitoring_level in [MonitoringLevel.DETAILED, MonitoringLevel.FULL]:
            self._thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self._thread.start()

        self._logger.info(f"Task monitoring started with level: {self._monitoring_level}")

    def stop_monitoring(self) -> None:
        """停止监控."""
        if not self._running:
            return

        self._running = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)

        self._logger.info("Task monitoring stopped")

    def on_task_started(self, task_id: str, task_type: str, **kwargs) -> None:
        """任务开始事件.

        Args:
            task_id: 任务ID
            task_type: 任务类型
            **kwargs: 额外参数
        """
        with self._lock:
            self._active_tasks.add(task_id)

            # 创建任务指标
            metrics = TaskMetrics(
                task_id=task_id,
                task_type=task_type,
                status=TaskStatus.RUNNING,
                start_time=time.time(),
            )
            self._metrics[task_id] = metrics

            # 记录事件
            event = TaskEvent(
                task_id=task_id,
                event_type="task_started",
                data={"task_type": task_type, **kwargs},
                message=f"Task {task_id} started",
            )
            self._add_event(event)

        self._logger.debug(f"Task started: {task_id} ({task_type})")

    def on_task_completed(self, task_id: str, success: bool = True, **kwargs) -> None:
        """任务完成事件.

        Args:
            task_id: 任务ID
            success: 是否成功
            **kwargs: 额外参数
        """
        with self._lock:
            self._active_tasks.discard(task_id)

            if task_id in self._metrics:
                metrics = self._metrics[task_id]
                metrics.end_time = time.time()
                metrics.duration = metrics.end_time - metrics.start_time
                metrics.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED

                if success:
                    metrics.success_count += 1
                else:
                    metrics.failure_count += 1
                    if "error" in kwargs:
                        metrics.last_error = str(kwargs["error"])

            # 记录事件
            event = TaskEvent(
                task_id=task_id,
                event_type="task_completed",
                data={"success": success, **kwargs},
                message=f"Task {task_id} {'completed' if success else 'failed'}",
            )
            self._add_event(event)

        self._logger.debug(f"Task completed: {task_id} (success={success})")

    def on_task_retry(self, task_id: str, retry_count: int, **kwargs) -> None:
        """任务重试事件.

        Args:
            task_id: 任务ID
            retry_count: 重试次数
            **kwargs: 额外参数
        """
        with self._lock:
            if task_id in self._metrics:
                self._metrics[task_id].retry_count = retry_count

            # 记录事件
            event = TaskEvent(
                task_id=task_id,
                event_type="task_retry",
                data={"retry_count": retry_count, **kwargs},
                message=f"Task {task_id} retry #{retry_count}",
            )
            self._add_event(event)

        self._logger.debug(f"Task retry: {task_id} (#{retry_count})")

    def on_task_error(self, task_id: str, error: Exception, **kwargs) -> None:
        """任务错误事件.

        Args:
            task_id: 任务ID
            error: 错误对象
            **kwargs: 额外参数
        """
        with self._lock:
            if task_id in self._metrics:
                self._metrics[task_id].last_error = str(error)
                self._metrics[task_id].failure_count += 1

            # 记录事件
            event = TaskEvent(
                task_id=task_id,
                event_type="task_error",
                data={"error": str(error), "error_type": type(error).__name__, **kwargs},
                message=f"Task {task_id} error: {str(error)}",
            )
            self._add_event(event)

        self._logger.warning(f"Task error: {task_id} - {error}")

    def update_task_metrics(
        self, task_id: str, metrics: Dict[str, Any]
    ) -> None:
        """更新任务指标.

        Args:
            task_id: 任务ID
            metrics: 指标数据
        """
        with self._lock:
            if task_id in self._metrics:
                task_metrics = self._metrics[task_id]
                task_metrics.custom_metrics.update(metrics)

                # 更新系统指标
                if "memory_usage" in metrics:
                    task_metrics.memory_usage = metrics["memory_usage"]
                if "cpu_usage" in metrics:
                    task_metrics.cpu_usage = metrics["cpu_usage"]

    def get_task_metrics(self, task_id: str) -> Optional[TaskMetrics]:
        """获取任务指标.

        Args:
            task_id: 任务ID

        Returns:
            任务指标
        """
        with self._lock:
            return self._metrics.get(task_id)

    def get_all_metrics(self) -> Dict[str, TaskMetrics]:
        """获取所有任务指标.

        Returns:
            任务指标字典
        """
        with self._lock:
            return self._metrics.copy()

    def get_active_tasks(self) -> Set[str]:
        """获取活跃任务列表.

        Returns:
            活跃任务ID集合
        """
        with self._lock:
            return self._active_tasks.copy()

    def get_task_events(
        self,
        task_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[TaskEvent]:
        """获取任务事件.

        Args:
            task_id: 任务ID过滤
            event_type: 事件类型过滤
            limit: 限制数量

        Returns:
            事件列表
        """
        with self._lock:
            events = self._events.copy()

        # 应用过滤器
        if task_id is not None:
            events = [e for e in events if e.task_id == task_id]
        if event_type is not None:
            events = [e for e in events if e.event_type == event_type]

        # 按时间戳排序（最新的在前）
        events.sort(key=lambda x: x.timestamp, reverse=True)

        # 应用限制
        if limit is not None:
            events = events[:limit]

        return events

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息.

        Returns:
            统计信息字典
        """
        with self._lock:
            total_tasks = len(self._metrics)
            active_tasks = len(self._active_tasks)
            completed_tasks = len(
                [m for m in self._metrics.values() if m.status == TaskStatus.COMPLETED]
            )
            failed_tasks = len(
                [m for m in self._metrics.values() if m.status == TaskStatus.FAILED]
            )

            # 计算平均执行时间
            durations = [
                m.duration
                for m in self._metrics.values()
                if m.duration is not None
            ]
            avg_duration = sum(durations) / len(durations) if durations else 0

            # 按任务类型统计
            task_type_stats = defaultdict(int)
            for metrics in self._metrics.values():
                task_type_stats[metrics.task_type] += 1

            return {
                "total_tasks": total_tasks,
                "active_tasks": active_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "success_rate": (
                    completed_tasks / (completed_tasks + failed_tasks)
                    if (completed_tasks + failed_tasks) > 0
                    else 0
                ),
                "average_duration": avg_duration,
                "task_type_distribution": dict(task_type_stats),
                "total_events": len(self._events),
            }

    def add_listener(self, listener: Callable[[TaskEvent], None]) -> None:
        """添加事件监听器.

        Args:
            listener: 监听器函数
        """
        with self._lock:
            self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[TaskEvent], None]) -> bool:
        """移除事件监听器.

        Args:
            listener: 监听器函数

        Returns:
            是否成功移除
        """
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)
                return True
        return False

    def clear_metrics(self, older_than: Optional[float] = None) -> int:
        """清理指标数据.

        Args:
            older_than: 清理早于指定时间的数据（秒）

        Returns:
            清理的指标数量
        """
        if older_than is None:
            older_than = 24 * 3600  # 默认24小时

        current_time = time.time()
        cutoff_time = current_time - older_than
        cleared_count = 0

        with self._lock:
            metrics_to_remove = []

            for task_id, metrics in self._metrics.items():
                if (
                    metrics.end_time is not None
                    and metrics.end_time < cutoff_time
                    and task_id not in self._active_tasks
                ):
                    metrics_to_remove.append(task_id)

            for task_id in metrics_to_remove:
                del self._metrics[task_id]
                cleared_count += 1

            # 清理事件
            events_to_remove = [
                i
                for i, event in enumerate(self._events)
                if event.timestamp < cutoff_time
            ]

            for i in reversed(events_to_remove):
                del self._events[i]

        if cleared_count > 0:
            self._logger.info(f"Cleared {cleared_count} old task metrics")

        return cleared_count

    def _add_event(self, event: TaskEvent) -> None:
        """添加事件.

        Args:
            event: 事件对象
        """
        self._events.append(event)

        # 保持事件数量限制
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events :]

        # 通知监听器
        for listener in self._listeners:
            try:
                listener(event)
            except Exception as e:
                self._logger.error(f"Error in event listener: {e}")

    def _monitoring_loop(self) -> None:
        """监控循环."""
        while self._running:
            try:
                self._collect_system_metrics()
                time.sleep(5.0)  # 每5秒收集一次系统指标
            except Exception as e:
                self._logger.error(f"Error in monitoring loop: {e}")
                time.sleep(1.0)

    def _collect_system_metrics(self) -> None:
        """收集系统指标."""
        if self._monitoring_level != MonitoringLevel.FULL:
            return

        try:
            import psutil

            # 获取当前进程的资源使用情况
            process = psutil.Process()
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent()

            # 更新活跃任务的系统指标
            with self._lock:
                for task_id in self._active_tasks:
                    if task_id in self._metrics:
                        metrics = self._metrics[task_id]
                        metrics.memory_usage = memory_info.rss / 1024 / 1024  # MB
                        metrics.cpu_usage = cpu_percent

        except ImportError:
            # psutil 不可用
            pass
        except Exception as e:
            self._logger.error(f"Error collecting system metrics: {e}")
