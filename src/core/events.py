"""事件系统

定义任务执行过程中的各种事件和事件总线。
"""

from abc import ABC, abstractmethod
from datetime import datetime
import logging
from typing import Any, Callable, Dict, List, Optional, Type
from uuid import uuid4

import asyncio

logger = logging.getLogger(__name__)


class Event(ABC):
    """事件基类"""

    def __init__(
        self, event_id: Optional[str] = None, timestamp: Optional[datetime] = None
    ):
        self.event_id = event_id or str(uuid4())
        self.timestamp = timestamp or datetime.now()
        self.source: Optional[str] = None
        self.metadata: Dict[str, Any] = {}

    @property
    @abstractmethod
    def event_type(self) -> str:
        """事件类型"""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "metadata": self.metadata,
        }


class TaskEvent(Event):
    """任务相关事件基类"""

    def __init__(self, task_id: str, user_id: str, **kwargs):
        super().__init__(**kwargs)
        self.task_id = task_id
        self.user_id = user_id

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({"task_id": self.task_id, "user_id": self.user_id})
        return data


class TaskCreatedEvent(TaskEvent):
    """任务创建事件"""

    def __init__(self, task_id: str, user_id: str, task_type: str, **kwargs):
        super().__init__(task_id, user_id, **kwargs)
        self.task_type = task_type

    @property
    def event_type(self) -> str:
        return "task.created"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["task_type"] = self.task_type
        return data


class TaskStatusChangedEvent(TaskEvent):
    """任务状态变更事件"""

    def __init__(
        self, task_id: str, user_id: str, old_status: str, new_status: str, **kwargs
    ):
        super().__init__(task_id, user_id, **kwargs)
        self.old_status = old_status
        self.new_status = new_status

    @property
    def event_type(self) -> str:
        return "task.status_changed"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({"old_status": self.old_status, "new_status": self.new_status})
        return data


class TaskExecutionStartedEvent(TaskEvent):
    """任务执行开始事件"""

    def __init__(self, task_id: str, user_id: str, execution_id: str, **kwargs):
        super().__init__(task_id, user_id, **kwargs)
        self.execution_id = execution_id

    @property
    def event_type(self) -> str:
        return "task.execution_started"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["execution_id"] = self.execution_id
        return data


class TaskExecutionCompletedEvent(TaskEvent):
    """任务执行完成事件"""

    def __init__(
        self,
        task_id: str,
        user_id: str,
        execution_id: str,
        success: bool,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(task_id, user_id, **kwargs)
        self.execution_id = execution_id
        self.success = success
        self.result = result
        self.error = error

    @property
    def event_type(self) -> str:
        return "task.execution_completed"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "execution_id": self.execution_id,
                "success": self.success,
                "result": self.result,
                "error": self.error,
            }
        )
        return data


class AutomationEvent(Event):
    """自动化相关事件基类"""

    def __init__(self, execution_id: str, **kwargs):
        super().__init__(**kwargs)
        self.execution_id = execution_id

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["execution_id"] = self.execution_id
        return data


class WindowDetectedEvent(AutomationEvent):
    """窗口检测事件"""

    def __init__(
        self, execution_id: str, window_title: str, window_handle: int, **kwargs
    ):
        super().__init__(execution_id, **kwargs)
        self.window_title = window_title
        self.window_handle = window_handle

    @property
    def event_type(self) -> str:
        return "automation.window_detected"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {"window_title": self.window_title, "window_handle": self.window_handle}
        )
        return data


class ActionExecutedEvent(AutomationEvent):
    """动作执行事件"""

    def __init__(
        self,
        execution_id: str,
        action_id: str,
        action_type: str,
        success: bool,
        duration: float,
        **kwargs,
    ):
        super().__init__(execution_id, **kwargs)
        self.action_id = action_id
        self.action_type = action_type
        self.success = success
        self.duration = duration

    @property
    def event_type(self) -> str:
        return "automation.action_executed"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "action_id": self.action_id,
                "action_type": self.action_type,
                "success": self.success,
                "duration": self.duration,
            }
        )
        return data


class ScreenshotTakenEvent(AutomationEvent):
    """截图事件"""

    def __init__(
        self,
        execution_id: str,
        screenshot_id: str,
        screenshot_type: str,
        file_path: str,
        **kwargs,
    ):
        super().__init__(execution_id, **kwargs)
        self.screenshot_id = screenshot_id
        self.screenshot_type = screenshot_type
        self.file_path = file_path

    @property
    def event_type(self) -> str:
        return "automation.screenshot_taken"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "screenshot_id": self.screenshot_id,
                "screenshot_type": self.screenshot_type,
                "file_path": self.file_path,
            }
        )
        return data


class EventHandler(ABC):
    """事件处理器基类"""

    @abstractmethod
    async def handle(self, event: Event) -> None:
        """处理事件"""
        pass

    @property
    @abstractmethod
    def supported_event_types(self) -> List[str]:
        """支持的事件类型"""
        pass


class EventBus:
    """事件总线

    负责事件的订阅、发布和分发。
    """

    def __init__(self, config_manager=None):
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._processor_task: Optional[asyncio.Task] = None
        self._running = False
        self._config_manager = config_manager

    async def start(self):
        """启动事件总线"""
        if self._running:
            return

        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())
        logger.info("事件总线已启动")

    async def stop(self):
        """停止事件总线"""
        if not self._running:
            return

        self._running = False

        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass

        logger.info("事件总线已停止")

    def subscribe(self, handler: EventHandler):
        """订阅事件处理器

        Args:
            handler: 事件处理器
        """
        for event_type in handler.supported_event_types:
            if event_type not in self._handlers:
                self._handlers[event_type] = []

            if handler not in self._handlers[event_type]:
                self._handlers[event_type].append(handler)
                logger.debug(
                    f"订阅事件处理器: {event_type} -> {handler.__class__.__name__}"
                )

    def unsubscribe(self, handler: EventHandler):
        """取消订阅事件处理器

        Args:
            handler: 事件处理器
        """
        for event_type in handler.supported_event_types:
            if event_type in self._handlers:
                if handler in self._handlers[event_type]:
                    self._handlers[event_type].remove(handler)
                    logger.debug(
                        f"取消订阅事件处理器: {event_type} -> {handler.__class__.__name__}"
                    )

                # 清理空列表
                if not self._handlers[event_type]:
                    del self._handlers[event_type]

    async def publish(self, event: Event):
        """发布事件

        Args:
            event: 要发布的事件
        """
        if not self._running:
            logger.warning(f"事件总线未运行，忽略事件: {event.event_type}")
            return

        try:
            await self._event_queue.put(event)
            logger.debug(f"发布事件: {event.event_type} ({event.event_id})")
        except Exception as e:
            logger.error(f"发布事件失败: {e}")

    def get_handler_count(self, event_type: str) -> int:
        """获取指定事件类型的处理器数量"""
        return len(self._handlers.get(event_type, []))

    def get_all_event_types(self) -> List[str]:
        """获取所有已订阅的事件类型"""
        return list(self._handlers.keys())

    async def _process_events(self):
        """处理事件队列"""
        logger.info("事件处理器启动")

        try:
            while self._running:
                try:
                    # 等待事件
                    timeout = 1.0
                    if self._config_manager:
                        timeout = self._config_manager.get('event_bus.queue_timeout', 1.0)
                    event = await asyncio.wait_for(self._event_queue.get(), timeout=timeout)

                    # 分发事件
                    await self._dispatch_event(event)

                except asyncio.TimeoutError:
                    # 超时是正常的，继续循环
                    continue
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"处理事件时出错: {e}")
                    await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            pass
        finally:
            logger.info("事件处理器结束")

    async def _dispatch_event(self, event: Event):
        """分发事件到处理器"""
        handlers = self._handlers.get(event.event_type, [])

        if not handlers:
            logger.debug(f"没有处理器订阅事件: {event.event_type}")
            return

        # 并发执行所有处理器
        tasks = []
        for handler in handlers:
            task = asyncio.create_task(self._handle_event_safely(handler, event))
            tasks.append(task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _handle_event_safely(self, handler: EventHandler, event: Event):
        """安全地执行事件处理器"""
        try:
            await handler.handle(event)
            logger.debug(
                f"事件处理成功: {event.event_type} -> {handler.__class__.__name__}"
            )
        except Exception as e:
            logger.error(
                f"事件处理失败: {event.event_type} -> {handler.__class__.__name__}, 错误: {e}"
            )


class LoggingEventHandler(EventHandler):
    """日志事件处理器

    将所有事件记录到日志中。
    """

    def __init__(self, log_level: int = logging.INFO):
        self.log_level = log_level

    async def handle(self, event: Event) -> None:
        """处理事件"""
        logger.log(
            self.log_level,
            f"事件: {event.event_type} ({event.event_id}) - {event.to_dict()}",
        )

    @property
    def supported_event_types(self) -> List[str]:
        """支持所有事件类型"""
        return ["*"]  # 特殊标记，表示支持所有事件


class MetricsEventHandler(EventHandler):
    """指标事件处理器

    收集事件相关的指标数据。
    """

    def __init__(self):
        self.event_counts: Dict[str, int] = {}
        self.last_event_time: Dict[str, datetime] = {}

    async def handle(self, event: Event) -> None:
        """处理事件"""
        event_type = event.event_type

        # 更新计数
        self.event_counts[event_type] = self.event_counts.get(event_type, 0) + 1

        # 更新时间
        self.last_event_time[event_type] = event.timestamp

    @property
    def supported_event_types(self) -> List[str]:
        """支持所有事件类型"""
        return ["*"]

    def get_metrics(self) -> Dict[str, Any]:
        """获取指标数据"""
        return {
            "event_counts": self.event_counts.copy(),
            "last_event_times": {
                event_type: time.isoformat()
                for event_type, time in self.last_event_time.items()
            },
        }

    def reset_metrics(self):
        """重置指标数据"""
        self.event_counts.clear()
        self.last_event_time.clear()
