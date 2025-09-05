"""事件发布订阅接口

定义事件发布和订阅的核心接口契约。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable, List, Union
from datetime import datetime
from enum import Enum


class EventPriority(Enum):
    """事件优先级枚举"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class Event:
    """事件数据类"""
    
    def __init__(
        self,
        event_type: str,
        data: Any = None,
        source: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.event_type = event_type
        self.data = data
        self.source = source
        self.priority = priority
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
        self.event_id = f"{self.timestamp.timestamp()}_{id(self)}"


class IEventPublisher(ABC):
    """事件发布器接口
    
    定义事件发布的核心接口。
    """
    
    @abstractmethod
    async def publish(
        self, 
        event_type: str,
        data: Any = None,
        source: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """发布事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
            source: 事件源
            priority: 事件优先级
            metadata: 事件元数据
            
        Returns:
            事件ID
        """
        pass
    
    @abstractmethod
    async def publish_event(self, event: Event) -> str:
        """发布事件对象
        
        Args:
            event: 事件对象
            
        Returns:
            事件ID
        """
        pass
    
    @abstractmethod
    async def publish_batch(
        self, 
        events: List[Union[Event, Dict[str, Any]]]
    ) -> List[str]:
        """批量发布事件
        
        Args:
            events: 事件列表
            
        Returns:
            事件ID列表
        """
        pass
    
    @abstractmethod
    def get_published_events(
        self, 
        event_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Event]:
        """获取已发布的事件
        
        Args:
            event_type: 事件类型过滤
            limit: 限制数量
            
        Returns:
            事件列表
        """
        pass
    
    @abstractmethod
    def get_event_statistics(self) -> Dict[str, Any]:
        """获取事件统计信息
        
        Returns:
            统计信息字典
        """
        pass
    
    @abstractmethod
    def clear_event_history(self, event_type: Optional[str] = None) -> int:
        """清理事件历史
        
        Args:
            event_type: 事件类型，如果为None则清理所有
            
        Returns:
            清理的事件数量
        """
        pass


class IEventSubscriber(ABC):
    """事件订阅器接口
    
    定义事件订阅的核心接口。
    """
    
    @abstractmethod
    def subscribe(
        self, 
        event_type: str,
        handler: Callable[[Event], None],
        priority: Optional[EventPriority] = None
    ) -> str:
        """订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理函数
            priority: 订阅优先级
            
        Returns:
            订阅ID
        """
        pass
    
    @abstractmethod
    def subscribe_async(
        self, 
        event_type: str,
        handler: Callable[[Event], Any],
        priority: Optional[EventPriority] = None
    ) -> str:
        """异步订阅事件
        
        Args:
            event_type: 事件类型
            handler: 异步事件处理函数
            priority: 订阅优先级
            
        Returns:
            订阅ID
        """
        pass
    
    @abstractmethod
    def subscribe_pattern(
        self, 
        pattern: str,
        handler: Callable[[Event], None],
        priority: Optional[EventPriority] = None
    ) -> str:
        """按模式订阅事件
        
        Args:
            pattern: 事件类型模式（支持通配符）
            handler: 事件处理函数
            priority: 订阅优先级
            
        Returns:
            订阅ID
        """
        pass
    
    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅
        
        Args:
            subscription_id: 订阅ID
            
        Returns:
            是否取消成功
        """
        pass
    
    @abstractmethod
    def unsubscribe_all(self, event_type: Optional[str] = None) -> int:
        """取消所有订阅
        
        Args:
            event_type: 事件类型，如果为None则取消所有订阅
            
        Returns:
            取消的订阅数量
        """
        pass
    
    @abstractmethod
    def get_subscriptions(
        self, 
        event_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取订阅信息
        
        Args:
            event_type: 事件类型过滤
            
        Returns:
            订阅信息列表
        """
        pass
    
    @abstractmethod
    def is_subscribed(self, event_type: str) -> bool:
        """检查是否已订阅事件类型
        
        Args:
            event_type: 事件类型
            
        Returns:
            是否已订阅
        """
        pass
    
    @abstractmethod
    def get_subscription_statistics(self) -> Dict[str, Any]:
        """获取订阅统计信息
        
        Returns:
            统计信息字典
        """
        pass


class IEventBus(IEventPublisher, IEventSubscriber):
    """事件总线接口
    
    结合事件发布和订阅功能的统一接口。
    """
    
    @abstractmethod
    async def start(self) -> bool:
        """启动事件总线
        
        Returns:
            是否启动成功
        """
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """停止事件总线
        
        Returns:
            是否停止成功
        """
        pass
    
    @abstractmethod
    def is_running(self) -> bool:
        """检查事件总线是否运行中
        
        Returns:
            是否运行中
        """
        pass
    
    @abstractmethod
    async def process_pending_events(self) -> int:
        """处理待处理的事件
        
        Returns:
            处理的事件数量
        """
        pass
    
    @abstractmethod
    def get_pending_event_count(self) -> int:
        """获取待处理事件数量
        
        Returns:
            待处理事件数量
        """
        pass
    
    @abstractmethod
    def set_max_queue_size(self, size: int) -> None:
        """设置最大队列大小
        
        Args:
            size: 最大队列大小
        """
        pass
    
    @abstractmethod
    def get_max_queue_size(self) -> int:
        """获取最大队列大小
        
        Returns:
            最大队列大小
        """
        pass
    
    @abstractmethod
    def set_event_retention_time(self, seconds: int) -> None:
        """设置事件保留时间
        
        Args:
            seconds: 保留时间（秒）
        """
        pass
    
    @abstractmethod
    def get_event_retention_time(self) -> int:
        """获取事件保留时间
        
        Returns:
            保留时间（秒）
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            健康状态信息
        """
        pass