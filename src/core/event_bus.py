"""事件总线实现

提供事件发布和订阅功能。
"""

import asyncio
from typing import Dict, List, Callable, Any, Optional
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

from .interfaces.event_interface import IEventBus, IEventPublisher, IEventSubscriber, Event, EventPriority

@dataclass
class EventSubscription:
    """事件订阅信息"""
    subscriber_id: str
    callback: Callable[[Event], None]
    event_type: str
    priority: EventPriority = EventPriority.NORMAL
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class EventBus(IEventBus, IEventPublisher, IEventSubscriber):
    """事件总线实现
    
    提供事件发布、订阅和管理功能。
    """
    
    def __init__(self, config_manager=None):
        self._subscriptions: Dict[str, List[EventSubscription]] = defaultdict(list)
        self._global_subscriptions: List[EventSubscription] = []
        self._event_history: List[Event] = []
        self.config_manager = config_manager
        self._max_history_size: int = self._get_config_value("event_bus.max_history_size", 1000)
        self._stats = {
            'published_events': 0,
            'failed_deliveries': 0,
            'active_subscriptions': 0
        }
        self._lock = asyncio.Lock()
    
    def _get_config_value(self, key: str, default_value):
        """从配置管理器获取配置值."""
        if self.config_manager:
            return self.config_manager.get(key, default_value)
        return default_value
    
    async def publish(self, event: Event) -> None:
        """发布事件
        
        Args:
            event: 要发布的事件
        """
        async with self._lock:
            try:
                # 记录事件历史
                self._add_to_history(event)
                
                # 获取订阅者
                subscribers = self._get_subscribers_for_event(event)
                
                # 按优先级排序
                subscribers.sort(key=lambda s: s.priority.value, reverse=True)
                
                # 通知订阅者
                for subscription in subscribers:
                    try:
                        if asyncio.iscoroutinefunction(subscription.callback):
                            await subscription.callback(event)
                        else:
                            subscription.callback(event)
                    except Exception as e:
                        self._stats['failed_deliveries'] += 1
                        logger.error(f"事件处理失败 - 订阅者: {subscription.subscriber_id}, 事件: {event.event_type}, 错误: {e}")
                
                self._stats['published_events'] += 1
                logger.debug(f"事件已发布: {event.event_type}, 通知了 {len(subscribers)} 个订阅者")
                
            except Exception as e:
                logger.error(f"发布事件失败: {e}")
                raise
    
    def subscribe(self, event_type: str, callback: Callable[[Event], None], 
                 subscriber_id: str, priority: EventPriority = EventPriority.NORMAL) -> str:
        """订阅事件
        
        Args:
            event_type: 事件类型，使用 '*' 订阅所有事件
            callback: 回调函数
            subscriber_id: 订阅者ID
            priority: 优先级
            
        Returns:
            订阅ID
        """
        subscription = EventSubscription(
            subscriber_id=subscriber_id,
            callback=callback,
            event_type=event_type,
            priority=priority
        )
        
        if event_type == '*':
            self._global_subscriptions.append(subscription)
        else:
            self._subscriptions[event_type].append(subscription)
        
        self._stats['active_subscriptions'] += 1
        
        subscription_id = f"{subscriber_id}_{event_type}_{len(self._subscriptions[event_type])}"
        logger.debug(f"新增订阅: {subscription_id}, 事件类型: {event_type}")
        
        return subscription_id
    
    def unsubscribe(self, event_type: str, subscriber_id: str) -> bool:
        """取消订阅
        
        Args:
            event_type: 事件类型
            subscriber_id: 订阅者ID
            
        Returns:
            是否成功取消订阅
        """
        removed = False
        
        if event_type == '*':
            # 移除全局订阅
            original_count = len(self._global_subscriptions)
            self._global_subscriptions = [
                sub for sub in self._global_subscriptions 
                if sub.subscriber_id != subscriber_id
            ]
            removed = len(self._global_subscriptions) < original_count
        else:
            # 移除特定事件订阅
            if event_type in self._subscriptions:
                original_count = len(self._subscriptions[event_type])
                self._subscriptions[event_type] = [
                    sub for sub in self._subscriptions[event_type]
                    if sub.subscriber_id != subscriber_id
                ]
                removed = len(self._subscriptions[event_type]) < original_count
                
                # 如果没有订阅者了，删除事件类型
                if not self._subscriptions[event_type]:
                    del self._subscriptions[event_type]
        
        if removed:
            self._stats['active_subscriptions'] -= 1
            logger.debug(f"取消订阅: {subscriber_id}, 事件类型: {event_type}")
        
        return removed
    
    def unsubscribe_all(self, subscriber_id: str) -> int:
        """取消订阅者的所有订阅
        
        Args:
            subscriber_id: 订阅者ID
            
        Returns:
            取消的订阅数量
        """
        removed_count = 0
        
        # 移除全局订阅
        original_global_count = len(self._global_subscriptions)
        self._global_subscriptions = [
            sub for sub in self._global_subscriptions 
            if sub.subscriber_id != subscriber_id
        ]
        removed_count += original_global_count - len(self._global_subscriptions)
        
        # 移除特定事件订阅
        event_types_to_remove = []
        for event_type, subscriptions in self._subscriptions.items():
            original_count = len(subscriptions)
            self._subscriptions[event_type] = [
                sub for sub in subscriptions
                if sub.subscriber_id != subscriber_id
            ]
            removed_count += original_count - len(self._subscriptions[event_type])
            
            # 标记空的事件类型
            if not self._subscriptions[event_type]:
                event_types_to_remove.append(event_type)
        
        # 删除空的事件类型
        for event_type in event_types_to_remove:
            del self._subscriptions[event_type]
        
        self._stats['active_subscriptions'] -= removed_count
        
        if removed_count > 0:
            logger.debug(f"取消订阅者 {subscriber_id} 的所有订阅，共 {removed_count} 个")
        
        return removed_count
    
    def get_subscribers(self, event_type: str) -> List[str]:
        """获取事件订阅者列表
        
        Args:
            event_type: 事件类型
            
        Returns:
            订阅者ID列表
        """
        subscribers = set()
        
        # 添加全局订阅者
        for sub in self._global_subscriptions:
            subscribers.add(sub.subscriber_id)
        
        # 添加特定事件订阅者
        if event_type in self._subscriptions:
            for sub in self._subscriptions[event_type]:
                subscribers.add(sub.subscriber_id)
        
        return list(subscribers)
    
    def get_event_types(self) -> List[str]:
        """获取所有事件类型
        
        Returns:
            事件类型列表
        """
        return list(self._subscriptions.keys())
    
    def get_subscription_count(self, event_type: Optional[str] = None) -> int:
        """获取订阅数量
        
        Args:
            event_type: 事件类型，None表示获取总数
            
        Returns:
            订阅数量
        """
        if event_type is None:
            return self._stats['active_subscriptions']
        elif event_type == '*':
            return len(self._global_subscriptions)
        else:
            return len(self._subscriptions.get(event_type, []))
    
    def get_event_history(self, event_type: Optional[str] = None, 
                         limit: Optional[int] = None) -> List[Event]:
        """获取事件历史
        
        Args:
            event_type: 事件类型过滤，None表示所有事件
            limit: 限制数量
            
        Returns:
            事件历史列表
        """
        history = self._event_history
        
        if event_type:
            history = [event for event in history if event.event_type == event_type]
        
        if limit:
            history = history[-limit:]
        
        return history
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        return {
            **self._stats,
            'event_types_count': len(self._subscriptions),
            'global_subscriptions': len(self._global_subscriptions),
            'history_size': len(self._event_history)
        }
    
    def clear_history(self) -> None:
        """清空事件历史"""
        self._event_history.clear()
        logger.debug("事件历史已清空")
    
    def clear_all_subscriptions(self) -> None:
        """清空所有订阅"""
        self._subscriptions.clear()
        self._global_subscriptions.clear()
        self._stats['active_subscriptions'] = 0
        logger.debug("所有订阅已清空")
    
    def _get_subscribers_for_event(self, event: Event) -> List[EventSubscription]:
        """获取事件的订阅者
        
        Args:
            event: 事件
            
        Returns:
            订阅者列表
        """
        subscribers = []
        
        # 添加全局订阅者
        subscribers.extend(self._global_subscriptions)
        
        # 添加特定事件订阅者
        if event.event_type in self._subscriptions:
            subscribers.extend(self._subscriptions[event.event_type])
        
        return subscribers
    
    def _add_to_history(self, event: Event) -> None:
        """添加事件到历史记录
        
        Args:
            event: 事件
        """
        self._event_history.append(event)
        
        # 限制历史记录大小
        if len(self._event_history) > self._max_history_size:
            self._event_history = self._event_history[-self._max_history_size:]
    
    async def dispose(self) -> None:
        """清理资源"""
        self.clear_all_subscriptions()
        self.clear_history()
        logger.info("事件总线已清理")