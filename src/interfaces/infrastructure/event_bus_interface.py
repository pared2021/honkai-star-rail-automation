"""事件总线接口

定义事件发布订阅的基础设施抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


class IEvent(ABC):
    """事件接口"""
    
    @property
    @abstractmethod
    def event_type(self) -> str:
        """事件类型"""
        pass
    
    @property
    @abstractmethod
    def event_id(self) -> str:
        """事件ID"""
        pass
    
    @property
    @abstractmethod
    def timestamp(self) -> datetime:
        """事件时间戳"""
        pass
    
    @property
    @abstractmethod
    def data(self) -> Dict[str, Any]:
        """事件数据"""
        pass


class IEventBus(ABC):
    """事件总线接口
    
    定义事件发布订阅的基础设施操作。
    """
    
    @abstractmethod
    async def publish(self, event: IEvent) -> bool:
        """发布事件
        
        Args:
            event: 事件对象
            
        Returns:
            是否发布成功
        """
        pass
    
    @abstractmethod
    async def publish_async(self, event: IEvent) -> bool:
        """异步发布事件
        
        Args:
            event: 事件对象
            
        Returns:
            是否发布成功
        """
        pass
    
    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable[[IEvent], None]) -> str:
        """订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
            
        Returns:
            订阅ID
        """
        pass
    
    @abstractmethod
    def subscribe_async(self, event_type: str, handler: Callable[[IEvent], None]) -> str:
        """异步订阅事件
        
        Args:
            event_type: 事件类型
            handler: 异步事件处理器
            
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
    def unsubscribe_all(self, event_type: str) -> bool:
        """取消所有订阅
        
        Args:
            event_type: 事件类型
            
        Returns:
            是否取消成功
        """
        pass
    
    @abstractmethod
    async def publish_and_wait(self, event: IEvent, timeout: Optional[float] = None) -> List[Any]:
        """发布事件并等待处理结果
        
        Args:
            event: 事件对象
            timeout: 超时时间（秒）
            
        Returns:
            处理结果列表
        """
        pass
    
    @abstractmethod
    def get_subscribers(self, event_type: str) -> List[str]:
        """获取订阅者列表
        
        Args:
            event_type: 事件类型
            
        Returns:
            订阅者ID列表
        """
        pass
    
    @abstractmethod
    def get_event_types(self) -> List[str]:
        """获取所有事件类型
        
        Returns:
            事件类型列表
        """
        pass
    
    @abstractmethod
    async def get_event_history(
        self,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取事件历史
        
        Args:
            event_type: 事件类型过滤
            start_time: 开始时间
            end_time: 结束时间
            limit: 限制数量
            
        Returns:
            事件历史列表
        """
        pass
    
    @abstractmethod
    def clear_event_history(self, event_type: Optional[str] = None) -> bool:
        """清理事件历史
        
        Args:
            event_type: 事件类型，None表示清理所有
            
        Returns:
            是否清理成功
        """
        pass
    
    @abstractmethod
    def start(self) -> bool:
        """启动事件总线
        
        Returns:
            是否启动成功
        """
        pass
    
    @abstractmethod
    def stop(self) -> bool:
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
    def get_statistics(self) -> Dict[str, Any]:
        """获取事件总线统计信息
        
        Returns:
            统计信息字典
        """
        pass