"""消息传递接口

定义消息传递和事件驱动架构的抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, AsyncIterator
import asyncio

from .messaging_types import (
    Message,
    MessageResult,
    Subscription,
    Queue,
    Exchange,
    Binding,
    DeliveryMode
)


class IMessageBroker(ABC):
    """消息代理接口"""
    
    @abstractmethod
    async def connect(self) -> None:
        """连接到消息代理"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """断开消息代理连接"""
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """检查连接状态
        
        Returns:
            是否已连接
        """
        pass
    
    @abstractmethod
    async def publish(self, 
                     message: Message, 
                     delivery_mode: DeliveryMode = DeliveryMode.AT_LEAST_ONCE) -> str:
        """发布消息
        
        Args:
            message: 消息
            delivery_mode: 投递模式
            
        Returns:
            消息ID
        """
        pass
    
    @abstractmethod
    async def subscribe(self, 
                       topic: str, 
                       handler: Callable[[Message], Any],
                       filter_expression: Optional[str] = None) -> str:
        """订阅主题
        
        Args:
            topic: 主题
            handler: 处理函数
            filter_expression: 过滤表达式
            
        Returns:
            订阅ID
        """
        pass
    
    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> None:
        """取消订阅
        
        Args:
            subscription_id: 订阅ID
        """
        pass
    
    @abstractmethod
    async def create_queue(self, queue: Queue) -> None:
        """创建队列
        
        Args:
            queue: 队列信息
        """
        pass
    
    @abstractmethod
    async def delete_queue(self, queue_name: str) -> None:
        """删除队列
        
        Args:
            queue_name: 队列名称
        """
        pass
    
    @abstractmethod
    async def create_exchange(self, exchange: Exchange) -> None:
        """创建交换机
        
        Args:
            exchange: 交换机信息
        """
        pass
    
    @abstractmethod
    async def delete_exchange(self, exchange_name: str) -> None:
        """删除交换机
        
        Args:
            exchange_name: 交换机名称
        """
        pass
    
    @abstractmethod
    async def bind_queue(self, binding: Binding) -> None:
        """绑定队列到交换机
        
        Args:
            binding: 绑定信息
        """
        pass
    
    @abstractmethod
    async def unbind_queue(self, binding: Binding) -> None:
        """解绑队列
        
        Args:
            binding: 绑定信息
        """
        pass
    
    @abstractmethod
    async def get_queue_info(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """获取队列信息
        
        Args:
            queue_name: 队列名称
            
        Returns:
            队列信息
        """
        pass
    
    @abstractmethod
    async def purge_queue(self, queue_name: str) -> int:
        """清空队列
        
        Args:
            queue_name: 队列名称
            
        Returns:
            清除的消息数量
        """
        pass


class IEventBus(ABC):
    """事件总线接口"""
    
    @abstractmethod
    async def publish_event(self, event_type: str, data: Any, **kwargs) -> None:
        """发布事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
            **kwargs: 额外参数
        """
        pass
    
    @abstractmethod
    async def subscribe_event(self, 
                             event_type: str, 
                             handler: Callable[[str, Any], Any]) -> str:
        """订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理函数
            
        Returns:
            订阅ID
        """
        pass
    
    @abstractmethod
    async def unsubscribe_event(self, subscription_id: str) -> None:
        """取消事件订阅
        
        Args:
            subscription_id: 订阅ID
        """
        pass
    
    @abstractmethod
    async def get_event_history(self, 
                               event_type: Optional[str] = None,
                               start_time: Optional[datetime] = None,
                               end_time: Optional[datetime] = None,
                               limit: int = 100) -> List[Dict[str, Any]]:
        """获取事件历史
        
        Args:
            event_type: 事件类型
            start_time: 开始时间
            end_time: 结束时间
            limit: 限制数量
            
        Returns:
            事件历史列表
        """
        pass
    
    @abstractmethod
    async def clear_event_history(self, 
                                 event_type: Optional[str] = None,
                                 before_time: Optional[datetime] = None) -> int:
        """清除事件历史
        
        Args:
            event_type: 事件类型
            before_time: 清除此时间之前的事件
            
        Returns:
            清除的事件数量
        """
        pass


class IMessageQueue(ABC):
    """消息队列接口"""
    
    @abstractmethod
    async def enqueue(self, 
                     queue_name: str, 
                     message: Message,
                     priority: Optional[MessagePriority] = None) -> str:
        """入队消息
        
        Args:
            queue_name: 队列名称
            message: 消息
            priority: 优先级
            
        Returns:
            消息ID
        """
        pass
    
    @abstractmethod
    async def dequeue(self, 
                     queue_name: str, 
                     timeout: Optional[float] = None) -> Optional[Message]:
        """出队消息
        
        Args:
            queue_name: 队列名称
            timeout: 超时时间
            
        Returns:
            消息或None
        """
        pass
    
    @abstractmethod
    async def peek(self, queue_name: str) -> Optional[Message]:
        """查看队列头部消息（不移除）
        
        Args:
            queue_name: 队列名称
            
        Returns:
            消息或None
        """
        pass
    
    @abstractmethod
    async def ack_message(self, queue_name: str, message_id: str) -> None:
        """确认消息处理
        
        Args:
            queue_name: 队列名称
            message_id: 消息ID
        """
        pass
    
    @abstractmethod
    async def nack_message(self, 
                          queue_name: str, 
                          message_id: str, 
                          requeue: bool = True) -> None:
        """拒绝消息
        
        Args:
            queue_name: 队列名称
            message_id: 消息ID
            requeue: 是否重新入队
        """
        pass
    
    @abstractmethod
    async def get_queue_size(self, queue_name: str) -> int:
        """获取队列大小
        
        Args:
            queue_name: 队列名称
            
        Returns:
            队列大小
        """
        pass
    
    @abstractmethod
    async def is_empty(self, queue_name: str) -> bool:
        """检查队列是否为空
        
        Args:
            queue_name: 队列名称
            
        Returns:
            是否为空
        """
        pass
    
    @abstractmethod
    async def clear_queue(self, queue_name: str) -> int:
        """清空队列
        
        Args:
            queue_name: 队列名称
            
        Returns:
            清除的消息数量
        """
        pass


class IMessageProcessor(ABC):
    """消息处理器接口"""
    
    @abstractmethod
    async def process_message(self, message: Message) -> MessageResult:
        """处理消息
        
        Args:
            message: 消息
            
        Returns:
            处理结果
        """
        pass
    
    @abstractmethod
    async def can_handle(self, message: Message) -> bool:
        """检查是否能处理消息
        
        Args:
            message: 消息
            
        Returns:
            是否能处理
        """
        pass
    
    @abstractmethod
    async def get_supported_topics(self) -> List[str]:
        """获取支持的主题
        
        Returns:
            支持的主题列表
        """
        pass


class IMessageRouter(ABC):
    """消息路由器接口"""
    
    @abstractmethod
    async def route_message(self, message: Message) -> List[str]:
        """路由消息
        
        Args:
            message: 消息
            
        Returns:
            目标队列列表
        """
        pass
    
    @abstractmethod
    async def add_route(self, 
                       pattern: str, 
                       destination: str, 
                       condition: Optional[Callable[[Message], bool]] = None) -> None:
        """添加路由规则
        
        Args:
            pattern: 匹配模式
            destination: 目标队列
            condition: 条件函数
        """
        pass
    
    @abstractmethod
    async def remove_route(self, pattern: str, destination: str) -> None:
        """移除路由规则
        
        Args:
            pattern: 匹配模式
            destination: 目标队列
        """
        pass
    
    @abstractmethod
    async def get_routes(self) -> List[Dict[str, Any]]:
        """获取所有路由规则
        
        Returns:
            路由规则列表
        """
        pass


class IMessageSerializer(ABC):
    """消息序列化器接口"""
    
    @abstractmethod
    async def serialize(self, message: Message) -> bytes:
        """序列化消息
        
        Args:
            message: 消息
            
        Returns:
            序列化后的数据
        """
        pass
    
    @abstractmethod
    async def deserialize(self, data: bytes) -> Message:
        """反序列化消息
        
        Args:
            data: 序列化数据
            
        Returns:
            消息对象
        """
        pass
    
    @abstractmethod
    async def get_content_type(self) -> str:
        """获取内容类型
        
        Returns:
            内容类型
        """
        pass


class IMessageMonitor(ABC):
    """消息监控接口"""
    
    @abstractmethod
    async def get_message_stats(self, 
                               queue_name: Optional[str] = None) -> Dict[str, Any]:
        """获取消息统计
        
        Args:
            queue_name: 队列名称
            
        Returns:
            统计信息
        """
        pass
    
    @abstractmethod
    async def get_processing_metrics(self) -> Dict[str, Any]:
        """获取处理指标
        
        Returns:
            处理指标
        """
        pass
    
    @abstractmethod
    async def get_error_rate(self, 
                            time_window: Optional[int] = None) -> float:
        """获取错误率
        
        Args:
            time_window: 时间窗口（秒）
            
        Returns:
            错误率
        """
        pass
    
    @abstractmethod
    async def get_throughput(self, 
                            time_window: Optional[int] = None) -> float:
        """获取吞吐量
        
        Args:
            time_window: 时间窗口（秒）
            
        Returns:
            吞吐量（消息/秒）
        """
        pass
    
    @abstractmethod
    async def get_latency_stats(self) -> Dict[str, float]:
        """获取延迟统计
        
        Returns:
            延迟统计（平均值、最小值、最大值等）
        """
        pass