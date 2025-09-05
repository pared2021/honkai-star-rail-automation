"""消息传递类型定义

定义消息传递相关的枚举、数据类和异常。
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Callable
from datetime import datetime


class MessagePriority(Enum):
    """消息优先级"""
    LOW = "low"          # 低优先级
    NORMAL = "normal"    # 普通优先级
    HIGH = "high"        # 高优先级
    CRITICAL = "critical"  # 关键优先级


class MessageStatus(Enum):
    """消息状态"""
    PENDING = "pending"      # 待处理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"        # 失败
    RETRYING = "retrying"    # 重试中
    CANCELLED = "cancelled"  # 已取消


class DeliveryMode(Enum):
    """投递模式"""
    FIRE_AND_FORGET = "fire_and_forget"  # 发送即忘
    AT_LEAST_ONCE = "at_least_once"      # 至少一次
    EXACTLY_ONCE = "exactly_once"        # 恰好一次
    AT_MOST_ONCE = "at_most_once"        # 至多一次


class ExchangeType(Enum):
    """交换机类型"""
    DIRECT = "direct"      # 直接交换
    TOPIC = "topic"        # 主题交换
    FANOUT = "fanout"      # 扇出交换
    HEADERS = "headers"    # 头部交换


@dataclass
class Message:
    """消息"""
    id: str
    topic: str
    payload: Any
    headers: Dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    expiration: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MessageResult:
    """消息处理结果"""
    message_id: str
    status: MessageStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Subscription:
    """订阅信息"""
    id: str
    topic: str
    handler: Callable
    filter_expression: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Queue:
    """队列信息"""
    name: str
    durable: bool = True
    auto_delete: bool = False
    exclusive: bool = False
    max_length: Optional[int] = None
    max_priority: Optional[int] = None
    message_ttl: Optional[int] = None
    dead_letter_exchange: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Exchange:
    """交换机信息"""
    name: str
    type: ExchangeType
    durable: bool = True
    auto_delete: bool = False
    internal: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Binding:
    """绑定信息"""
    queue: str
    exchange: str
    routing_key: str = ""
    arguments: Dict[str, Any] = field(default_factory=dict)


# 异常类
class MessagingException(Exception):
    """消息传递异常基类"""
    pass


class ConnectionException(MessagingException):
    """连接异常"""
    pass


class PublishException(MessagingException):
    """发布异常"""
    pass


class SubscriptionException(MessagingException):
    """订阅异常"""
    pass


class MessageProcessingException(MessagingException):
    """消息处理异常"""
    pass


class SerializationException(MessagingException):
    """序列化异常"""
    pass


class RoutingException(MessagingException):
    """路由异常"""
    pass


class QueueException(MessagingException):
    """队列异常"""
    pass