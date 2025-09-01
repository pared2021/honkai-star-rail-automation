# -*- coding: utf-8 -*-
"""
事件总线机制
实现事件驱动架构，提供组件间的解耦通信
"""

import asyncio
import uuid
from typing import Dict, List, Callable, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

from loguru import logger
from src.exceptions import EventError


class EventPriority(Enum):
    """事件优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskEventType(Enum):
    """任务事件类型"""
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_DELETED = "task_deleted"
    TASK_STATUS_CHANGED = "task_status_changed"
    TASK_EXECUTION_STARTED = "task_execution_started"
    TASK_EXECUTION_COMPLETED = "task_execution_completed"
    TASK_EXECUTION_FAILED = "task_execution_failed"
    TASK_SCHEDULED = "task_scheduled"
    TASK_CANCELLED = "task_cancelled"
    TASK_TIMEOUT = "task_timeout"
    TASK_RETRY = "task_retry"


class SystemEventType(Enum):
    """系统事件类型"""
    SERVICE_STARTED = "service_started"
    SERVICE_STOPPED = "service_stopped"
    SERVICE_ERROR = "service_error"
    DATABASE_CONNECTED = "database_connected"
    DATABASE_DISCONNECTED = "database_disconnected"
    DATABASE_ERROR = "database_error"
    SCHEDULER_STARTED = "scheduler_started"
    SCHEDULER_STOPPED = "scheduler_stopped"
    HEALTH_CHECK_FAILED = "health_check_failed"
    RESOURCE_EXHAUSTED = "resource_exhausted"


class AutomationEventType(Enum):
    """自动化事件类型"""
    GAME_DETECTED = "game_detected"
    AUTOMATION_STARTED = "automation_started"
    AUTOMATION_COMPLETED = "automation_completed"
    AUTOMATION_PAUSED = "automation_paused"
    AUTOMATION_RESUMED = "automation_resumed"
    AUTOMATION_STOPPED = "automation_stopped"
    AUTOMATION_ERROR = "automation_error"
    AUTOMATION_PROGRESS = "automation_progress"


@dataclass
class BaseEvent:
    """基础事件类"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: Union[TaskEventType, SystemEventType, AutomationEventType, str] = field(default="unknown")
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    priority: EventPriority = EventPriority.NORMAL
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value if hasattr(self.event_type, 'value') else str(self.event_type),
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'priority': self.priority.value,
            'data': self.data,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseEvent':
        """从字典创建事件"""
        event = cls()
        event.event_id = data.get('event_id', str(uuid.uuid4()))
        event.event_type = data.get('event_type', 'unknown')
        event.timestamp = datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))
        event.source = data.get('source')
        event.priority = EventPriority(data.get('priority', 'normal'))
        event.data = data.get('data', {})
        event.metadata = data.get('metadata', {})
        return event


@dataclass
class TaskEvent(BaseEvent):
    """任务事件"""
    task_id: Optional[str] = None
    user_id: Optional[str] = None
    
    def __post_init__(self):
        if self.source is None:
            self.source = "task_service"
        
        # 添加任务相关的元数据
        if self.task_id:
            self.metadata['task_id'] = self.task_id
        if self.user_id:
            self.metadata['user_id'] = self.user_id
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = super().to_dict()
        result.update({
            'task_id': self.task_id,
            'user_id': self.user_id
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskEvent':
        """从字典创建任务事件"""
        event = cls()
        event.event_id = data.get('event_id', str(uuid.uuid4()))
        event.event_type = data.get('event_type', 'unknown')
        event.timestamp = datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))
        event.source = data.get('source')
        event.priority = EventPriority(data.get('priority', 'normal'))
        event.data = data.get('data', {})
        event.metadata = data.get('metadata', {})
        event.task_id = data.get('task_id')
        event.user_id = data.get('user_id')
        return event


@dataclass
class SystemEvent(BaseEvent):
    """系统事件"""
    service_name: Optional[str] = None
    component: Optional[str] = None
    
    def __post_init__(self):
        if self.source is None:
            self.source = "system"
        
        # 添加系统相关的元数据
        if self.service_name:
            self.metadata['service_name'] = self.service_name
        if self.component:
            self.metadata['component'] = self.component
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = super().to_dict()
        result.update({
            'service_name': self.service_name,
            'component': self.component
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemEvent':
        """从字典创建系统事件"""
        event = cls()
        event.event_id = data.get('event_id', str(uuid.uuid4()))
        event.event_type = data.get('event_type', 'unknown')
        event.timestamp = datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))
        event.source = data.get('source')
        event.priority = EventPriority(data.get('priority', 'normal'))
        event.data = data.get('data', {})
        event.metadata = data.get('metadata', {})
        event.service_name = data.get('service_name')
        event.component = data.get('component')
        return event


@dataclass
class AutomationEvent(BaseEvent):
    """自动化事件"""
    automation_id: Optional[str] = None
    task_name: Optional[str] = None
    
    def __post_init__(self):
        if self.source is None:
            self.source = "automation_service"
        
        # 添加自动化相关的元数据
        if self.automation_id:
            self.metadata['automation_id'] = self.automation_id
        if self.task_name:
            self.metadata['task_name'] = self.task_name
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = super().to_dict()
        result.update({
            'automation_id': self.automation_id,
            'task_name': self.task_name
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AutomationEvent':
        """从字典创建自动化事件"""
        event = cls()
        event.event_id = data.get('event_id', str(uuid.uuid4()))
        event.event_type = data.get('event_type', 'unknown')
        event.timestamp = datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))
        event.source = data.get('source')
        event.priority = EventPriority(data.get('priority', 'normal'))
        event.data = data.get('data', {})
        event.metadata = data.get('metadata', {})
        event.automation_id = data.get('automation_id')
        event.task_name = data.get('task_name')
        return event


class EventHandler(ABC):
    """事件处理器抽象基类"""
    
    @abstractmethod
    async def handle(self, event: BaseEvent) -> bool:
        """
        处理事件
        
        Args:
            event: 事件对象
            
        Returns:
            bool: 处理是否成功
        """
        pass
    
    @property
    @abstractmethod
    def supported_events(self) -> List[Union[TaskEventType, SystemEventType, AutomationEventType, str]]:
        """
        支持的事件类型列表
        
        Returns:
            List[Union[TaskEventType, SystemEventType, str]]: 支持的事件类型
        """
        pass
    
    @property
    def handler_id(self) -> str:
        """处理器ID"""
        return f"{self.__class__.__name__}_{id(self)}"


@dataclass
class EventSubscription:
    """事件订阅信息"""
    subscription_id: str
    event_type: Union[TaskEventType, SystemEventType, AutomationEventType, str]
    handler: Union[Callable, EventHandler]
    priority: EventPriority = EventPriority.NORMAL
    filter_func: Optional[Callable[[BaseEvent], bool]] = None
    max_retries: int = 3
    retry_delay: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    active: bool = True





class EventBus:
    """事件总线"""
    
    def __init__(self, max_queue_size: int = 10000, worker_count: int = 3):
        """
        初始化事件总线
        
        Args:
            max_queue_size: 事件队列最大大小
            worker_count: 工作线程数量
        """
        self.max_queue_size = max_queue_size
        self.worker_count = worker_count
        
        # 事件队列
        self._event_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        
        # 订阅管理
        self._subscriptions: Dict[str, List[EventSubscription]] = {}
        self._subscription_by_id: Dict[str, EventSubscription] = {}
        
        # 工作线程
        self._workers: List[asyncio.Task] = []
        self._running = False
        
        # 统计信息
        self._stats = {
            'events_published': 0,
            'events_processed': 0,
            'events_failed': 0,
            'handlers_executed': 0,
            'handlers_failed': 0
        }
        
        # 事件历史（可选，用于调试）
        self._event_history: List[BaseEvent] = []
        self._max_history_size = 1000
        self._keep_history = False
        
        logger.info(f"事件总线初始化完成，队列大小: {max_queue_size}, 工作线程: {worker_count}")
    
    async def start(self):
        """启动事件总线"""
        if self._running:
            logger.warning("事件总线已经在运行")
            return
        
        self._running = True
        
        # 启动工作线程
        for i in range(self.worker_count):
            worker = asyncio.create_task(self._worker_loop(f"worker_{i}"))
            self._workers.append(worker)
        
        logger.info(f"事件总线已启动，工作线程数: {len(self._workers)}")
    
    async def stop(self):
        """停止事件总线"""
        if not self._running:
            return
        
        self._running = False
        
        # 等待队列中的事件处理完成
        await self._event_queue.join()
        
        # 停止工作线程
        for worker in self._workers:
            worker.cancel()
        
        # 等待所有工作线程结束
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        
        logger.info("事件总线已停止")
    
    async def _worker_loop(self, worker_name: str):
        """工作线程主循环"""
        logger.debug(f"事件总线工作线程 {worker_name} 已启动")
        
        while self._running:
            try:
                # 获取事件（带超时）
                try:
                    event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # 处理事件
                await self._process_event(event)
                
                # 标记任务完成
                self._event_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"工作线程 {worker_name} 异常: {e}")
                await asyncio.sleep(0.1)
        
        logger.debug(f"事件总线工作线程 {worker_name} 已停止")
    
    async def _process_event(self, event: BaseEvent):
        """处理单个事件"""
        try:
            self._stats['events_processed'] += 1
            
            # 记录事件历史
            if self._keep_history:
                self._event_history.append(event)
                if len(self._event_history) > self._max_history_size:
                    self._event_history.pop(0)
            
            # 获取事件类型的订阅者
            event_type_str = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
            subscriptions = self._subscriptions.get(event_type_str, [])
            
            if not subscriptions:
                logger.debug(f"没有找到事件类型 {event_type_str} 的订阅者")
                return
            
            # 按优先级排序
            subscriptions.sort(key=lambda s: s.priority.value, reverse=True)
            
            # 执行处理器
            for subscription in subscriptions:
                if not subscription.active:
                    continue
                
                # 应用过滤器
                if subscription.filter_func and not subscription.filter_func(event):
                    continue
                
                await self._execute_handler(subscription, event)
            
        except Exception as e:
            self._stats['events_failed'] += 1
            logger.error(f"处理事件失败: {e}")
    
    async def _execute_handler(self, subscription: EventSubscription, event: BaseEvent):
        """执行事件处理器"""
        handler = subscription.handler
        retries = 0
        
        while retries <= subscription.max_retries:
            try:
                self._stats['handlers_executed'] += 1
                
                # 执行处理器
                if isinstance(handler, EventHandler):
                    success = await handler.handle(event)
                elif asyncio.iscoroutinefunction(handler):
                    success = await handler(event)
                else:
                    success = handler(event)
                
                if success is not False:  # 允许返回None表示成功
                    logger.debug(f"事件处理器执行成功: {subscription.subscription_id}")
                    return
                else:
                    raise EventError("Handler returned False")
                
            except Exception as e:
                retries += 1
                self._stats['handlers_failed'] += 1
                
                if retries <= subscription.max_retries:
                    logger.warning(
                        f"事件处理器执行失败，重试 {retries}/{subscription.max_retries}: {e}"
                    )
                    await asyncio.sleep(subscription.retry_delay * retries)
                else:
                    logger.error(
                        f"事件处理器执行失败，已达最大重试次数: {subscription.subscription_id}, {e}"
                    )
                    break
    
    # ==================== 发布事件 ====================
    
    async def publish(self, event: BaseEvent) -> bool:
        """
        发布事件
        
        Args:
            event: 事件对象
            
        Returns:
            bool: 发布是否成功
            
        Raises:
            EventError: 发布失败
        """
        try:
            if not self._running:
                raise EventError("Event bus is not running")
            
            # 检查队列是否已满
            if self._event_queue.full():
                logger.warning("事件队列已满，丢弃事件")
                return False
            
            # 添加到队列
            await self._event_queue.put(event)
            self._stats['events_published'] += 1
            
            logger.debug(f"事件已发布: {event.event_type} (ID: {event.event_id})")
            return True
            
        except Exception as e:
            logger.error(f"发布事件失败: {e}")
            raise EventError(f"Failed to publish event: {e}", original_error=e)
    
    def publish_sync(self, event: BaseEvent) -> bool:
        """
        同步发布事件（非阻塞）
        
        Args:
            event: 事件对象
            
        Returns:
            bool: 发布是否成功
        """
        try:
            if not self._running:
                return False
            
            # 检查队列是否已满
            if self._event_queue.full():
                logger.warning("事件队列已满，丢弃事件")
                return False
            
            # 非阻塞添加到队列
            self._event_queue.put_nowait(event)
            self._stats['events_published'] += 1
            
            logger.debug(f"事件已发布（同步）: {event.event_type} (ID: {event.event_id})")
            return True
            
        except asyncio.QueueFull:
            logger.warning("事件队列已满，丢弃事件")
            return False
        except Exception as e:
            logger.error(f"同步发布事件失败: {e}")
            return False
    
    # ==================== 订阅管理 ====================
    
    def subscribe(
        self,
        event_type: Union[TaskEventType, SystemEventType, str],
        handler: Union[Callable, EventHandler],
        priority: EventPriority = EventPriority.NORMAL,
        filter_func: Optional[Callable[[BaseEvent], bool]] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> str:
        """
        订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
            priority: 优先级
            filter_func: 过滤函数
            max_retries: 最大重试次数
            retry_delay: 重试延迟
            
        Returns:
            str: 订阅ID
        """
        subscription_id = str(uuid.uuid4())
        event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)
        
        subscription = EventSubscription(
            subscription_id=subscription_id,
            event_type=event_type,
            handler=handler,
            priority=priority,
            filter_func=filter_func,
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        
        # 添加到订阅列表
        if event_type_str not in self._subscriptions:
            self._subscriptions[event_type_str] = []
        
        self._subscriptions[event_type_str].append(subscription)
        self._subscription_by_id[subscription_id] = subscription
        
        logger.info(f"事件订阅成功: {event_type_str} (ID: {subscription_id})")
        return subscription_id
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        取消订阅
        
        Args:
            subscription_id: 订阅ID
            
        Returns:
            bool: 取消是否成功
        """
        if subscription_id not in self._subscription_by_id:
            logger.warning(f"订阅ID不存在: {subscription_id}")
            return False
        
        subscription = self._subscription_by_id[subscription_id]
        event_type_str = subscription.event_type.value if hasattr(subscription.event_type, 'value') else str(subscription.event_type)
        
        # 从订阅列表中移除
        if event_type_str in self._subscriptions:
            self._subscriptions[event_type_str] = [
                s for s in self._subscriptions[event_type_str] 
                if s.subscription_id != subscription_id
            ]
            
            # 如果列表为空，删除键
            if not self._subscriptions[event_type_str]:
                del self._subscriptions[event_type_str]
        
        # 从ID映射中移除
        del self._subscription_by_id[subscription_id]
        
        logger.info(f"取消事件订阅: {event_type_str} (ID: {subscription_id})")
        return True
    
    async def unsubscribe_all(self, event_type: Union[TaskEventType, SystemEventType, str]) -> int:
        """
        取消指定事件类型的所有订阅
        
        Args:
            event_type: 事件类型
            
        Returns:
            int: 取消的订阅数量
        """
        event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)
        
        if event_type_str not in self._subscriptions:
            return 0
        
        subscriptions = self._subscriptions[event_type_str]
        count = len(subscriptions)
        
        # 从ID映射中移除
        for subscription in subscriptions:
            if subscription.subscription_id in self._subscription_by_id:
                del self._subscription_by_id[subscription.subscription_id]
        
        # 删除事件类型的所有订阅
        del self._subscriptions[event_type_str]
        
        logger.info(f"取消事件类型 {event_type_str} 的所有订阅，数量: {count}")
        return count
    
    def get_subscriptions(self, event_type: Optional[Union[TaskEventType, SystemEventType, str]] = None) -> List[EventSubscription]:
        """
        获取订阅列表
        
        Args:
            event_type: 事件类型，如果为None则返回所有订阅
            
        Returns:
            List[EventSubscription]: 订阅列表
        """
        if event_type is None:
            return list(self._subscription_by_id.values())
        
        event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)
        return self._subscriptions.get(event_type_str, [])
    
    # ==================== 统计和监控 ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'running': self._running,
            'worker_count': len(self._workers),
            'queue_size': self._event_queue.qsize(),
            'max_queue_size': self.max_queue_size,
            'subscription_count': len(self._subscription_by_id),
            'event_types': list(self._subscriptions.keys()),
            'stats': self._stats.copy()
        }
    
    def get_event_history(self, limit: Optional[int] = None) -> List[BaseEvent]:
        """
        获取事件历史
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[BaseEvent]: 事件历史列表
        """
        if not self._keep_history:
            return []
        
        if limit is None:
            return self._event_history.copy()
        
        return self._event_history[-limit:]
    
    def enable_history(self, max_size: int = 1000):
        """
        启用事件历史记录
        
        Args:
            max_size: 最大历史记录数量
        """
        self._keep_history = True
        self._max_history_size = max_size
        logger.info(f"事件历史记录已启用，最大记录数: {max_size}")
    
    def disable_history(self):
        """禁用事件历史记录"""
        self._keep_history = False
        self._event_history.clear()
        logger.info("事件历史记录已禁用")
    
    def clear_statistics(self):
        """清空统计信息"""
        self._stats = {
            'events_published': 0,
            'events_processed': 0,
            'events_failed': 0,
            'handlers_executed': 0,
            'handlers_failed': 0
        }
        logger.info("统计信息已清空")
    
    # ==================== 健康检查 ====================
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            Dict[str, Any]: 健康状态信息
        """
        try:
            queue_usage = self._event_queue.qsize() / self.max_queue_size if self.max_queue_size > 0 else 0
            
            # 判断健康状态
            is_healthy = (
                self._running and
                len(self._workers) == self.worker_count and
                queue_usage < 0.9  # 队列使用率小于90%
            )
            
            status = 'healthy' if is_healthy else 'unhealthy'
            
            return {
                'status': status,
                'message': 'Event bus health check',
                'details': {
                    'running': self._running,
                    'worker_count': len(self._workers),
                    'expected_workers': self.worker_count,
                    'queue_size': self._event_queue.qsize(),
                    'queue_usage': queue_usage,
                    'subscription_count': len(self._subscription_by_id),
                    'stats': self._stats
                }
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Health check failed: {e}',
                'details': {
                    'error': str(e),
                    'running': self._running
                }
            }


# ==================== 便利函数 ====================

def create_task_event(
    event_type: TaskEventType,
    task_id: str,
    user_id: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    priority: EventPriority = EventPriority.NORMAL
) -> TaskEvent:
    """
    创建任务事件的便利函数
    
    Args:
        event_type: 事件类型
        task_id: 任务ID
        user_id: 用户ID
        data: 事件数据
        priority: 优先级
        
    Returns:
        TaskEvent: 任务事件对象
    """
    return TaskEvent(
        event_type=event_type,
        task_id=task_id,
        user_id=user_id,
        data=data or {},
        priority=priority
    )


def create_system_event(
    event_type: SystemEventType,
    service_name: Optional[str] = None,
    component: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    priority: EventPriority = EventPriority.NORMAL
) -> SystemEvent:
    """
    创建系统事件的便利函数
    
    Args:
        event_type: 事件类型
        service_name: 服务名称
        component: 组件名称
        data: 事件数据
        priority: 优先级
        
    Returns:
        SystemEvent: 系统事件对象
    """
    return SystemEvent(
        event_type=event_type,
        service_name=service_name,
        component=component,
        data=data or {},
        priority=priority
    )


# ==================== 全局事件总线实例 ====================

# 全局事件总线实例（可选）
_global_event_bus: Optional[EventBus] = None


def get_global_event_bus() -> EventBus:
    """
    获取全局事件总线实例
    
    Returns:
        EventBus: 全局事件总线实例
    """
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


async def initialize_global_event_bus(**kwargs) -> EventBus:
    """
    初始化全局事件总线
    
    Args:
        **kwargs: EventBus构造参数
        
    Returns:
        EventBus: 全局事件总线实例
    """
    global _global_event_bus
    if _global_event_bus is not None:
        await _global_event_bus.stop()
    
    _global_event_bus = EventBus(**kwargs)
    await _global_event_bus.start()
    return _global_event_bus


async def shutdown_global_event_bus():
    """关闭全局事件总线"""
    global _global_event_bus
    if _global_event_bus is not None:
        await _global_event_bus.stop()
        _global_event_bus = None