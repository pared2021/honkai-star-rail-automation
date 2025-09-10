"""事件系统模块.

提供事件总线和事件处理功能。
"""

import asyncio
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from .logger import get_logger


@dataclass
class Event:
    """事件数据类。"""
    name: str
    data: Dict[str, Any]
    timestamp: datetime
    source: Optional[str] = None


class EventBus:
    """事件总线。"""
    
    def __init__(self):
        """初始化事件总线。"""
        self.logger = get_logger(__name__)
        self._listeners: Dict[str, List[Callable]] = {}
        self._async_listeners: Dict[str, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000
    
    def on(self, event_name: str, callback: Callable):
        """注册同步事件监听器。
        
        Args:
            event_name: 事件名称
            callback: 回调函数
        """
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(callback)
        self.logger.debug(f"注册同步事件监听器: {event_name}")
    
    def on_async(self, event_name: str, callback: Callable):
        """注册异步事件监听器。
        
        Args:
            event_name: 事件名称
            callback: 异步回调函数
        """
        if event_name not in self._async_listeners:
            self._async_listeners[event_name] = []
        self._async_listeners[event_name].append(callback)
        self.logger.debug(f"注册异步事件监听器: {event_name}")
    
    def off(self, event_name: str, callback: Callable):
        """移除事件监听器。
        
        Args:
            event_name: 事件名称
            callback: 回调函数
        """
        if event_name in self._listeners and callback in self._listeners[event_name]:
            self._listeners[event_name].remove(callback)
        
        if event_name in self._async_listeners and callback in self._async_listeners[event_name]:
            self._async_listeners[event_name].remove(callback)
        
        self.logger.debug(f"移除事件监听器: {event_name}")
    
    def emit(self, event_name: str, data: Dict[str, Any], source: Optional[str] = None):
        """发送同步事件。
        
        Args:
            event_name: 事件名称
            data: 事件数据
            source: 事件源
        """
        event = Event(
            name=event_name,
            data=data,
            timestamp=datetime.now(),
            source=source
        )
        
        # 添加到历史记录
        self._add_to_history(event)
        
        # 触发同步监听器
        if event_name in self._listeners:
            for callback in self._listeners[event_name]:
                try:
                    callback(data)
                except Exception as e:
                    self.logger.error(f"同步事件处理器错误 {event_name}: {e}")
        
        self.logger.debug(f"发送同步事件: {event_name}")
    
    async def emit_async(self, event_name: str, data: Dict[str, Any], source: Optional[str] = None):
        """发送异步事件。
        
        Args:
            event_name: 事件名称
            data: 事件数据
            source: 事件源
        """
        event = Event(
            name=event_name,
            data=data,
            timestamp=datetime.now(),
            source=source
        )
        
        # 添加到历史记录
        self._add_to_history(event)
        
        # 触发异步监听器
        if event_name in self._async_listeners:
            tasks = []
            for callback in self._async_listeners[event_name]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        tasks.append(callback(data))
                    else:
                        callback(data)
                except Exception as e:
                    self.logger.error(f"异步事件处理器错误 {event_name}: {e}")
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        
        self.logger.debug(f"发送异步事件: {event_name}")
    
    def _add_to_history(self, event: Event):
        """添加事件到历史记录。
        
        Args:
            event: 事件对象
        """
        self._event_history.append(event)
        
        # 限制历史记录大小
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
    
    def get_event_history(self, event_name: Optional[str] = None, limit: int = 100) -> List[Event]:
        """获取事件历史记录。
        
        Args:
            event_name: 事件名称过滤器
            limit: 返回数量限制
            
        Returns:
            事件列表
        """
        events = self._event_history
        
        if event_name:
            events = [e for e in events if e.name == event_name]
        
        return events[-limit:]
    
    def clear_history(self):
        """清空事件历史记录。"""
        self._event_history.clear()
        self.logger.debug("事件历史记录已清空")
    
    def get_listener_count(self, event_name: str) -> int:
        """获取事件监听器数量。
        
        Args:
            event_name: 事件名称
            
        Returns:
            监听器数量
        """
        sync_count = len(self._listeners.get(event_name, []))
        async_count = len(self._async_listeners.get(event_name, []))
        return sync_count + async_count
    
    def get_all_events(self) -> List[str]:
        """获取所有已注册的事件名称。
        
        Returns:
            事件名称列表
        """
        events = set()
        events.update(self._listeners.keys())
        events.update(self._async_listeners.keys())
        return list(events)


# 全局事件总线实例
_global_event_bus = None


def get_event_bus() -> EventBus:
    """获取全局事件总线实例。
    
    Returns:
        事件总线实例
    """
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus
