"""任务监控器接口

定义任务监控器的核心接口契约。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime, timedelta

from ..models.task import Task, TaskStatus


class ITaskMonitor(ABC):
    """任务监控器接口
    
    定义任务状态监控和回调处理的核心接口。
    """
    
    @abstractmethod
    def start_monitoring(self) -> bool:
        """启动监控
        
        Returns:
            是否启动成功
        """
        pass
    
    @abstractmethod
    def stop_monitoring(self) -> bool:
        """停止监控
        
        Returns:
            是否停止成功
        """
        pass
    
    @abstractmethod
    def is_monitoring(self) -> bool:
        """检查是否正在监控
        
        Returns:
            是否正在监控
        """
        pass
    
    @abstractmethod
    def add_task_monitor(
        self, 
        task_id: str, 
        callback: Callable[[str, TaskStatus, TaskStatus], None],
        health_check_interval: Optional[timedelta] = None
    ) -> bool:
        """添加任务监控
        
        Args:
            task_id: 任务ID
            callback: 状态变化回调函数
            health_check_interval: 健康检查间隔
            
        Returns:
            是否添加成功
        """
        pass
    
    @abstractmethod
    def remove_task_monitor(self, task_id: str) -> bool:
        """移除任务监控
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否移除成功
        """
        pass
    
    @abstractmethod
    def get_monitored_tasks(self) -> List[str]:
        """获取被监控的任务列表
        
        Returns:
            被监控的任务ID列表
        """
        pass
    
    @abstractmethod
    def check_task_health(self, task_id: str) -> Dict[str, Any]:
        """检查任务健康状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            健康状态信息
        """
        pass
    
    @abstractmethod
    def get_task_health_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务健康状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            健康状态信息，如果任务未被监控则返回None
        """
        pass
    
    @abstractmethod
    def get_timeout_tasks(self, timeout_threshold: timedelta) -> List[str]:
        """获取超时任务列表
        
        Args:
            timeout_threshold: 超时阈值
            
        Returns:
            超时任务ID列表
        """
        pass
    
    @abstractmethod
    def set_global_timeout(self, timeout: timedelta) -> None:
        """设置全局超时时间
        
        Args:
            timeout: 超时时间
        """
        pass
    
    @abstractmethod
    def set_task_timeout(self, task_id: str, timeout: timedelta) -> bool:
        """设置任务超时时间
        
        Args:
            task_id: 任务ID
            timeout: 超时时间
            
        Returns:
            是否设置成功
        """
        pass
    
    @abstractmethod
    def get_monitoring_statistics(self) -> Dict[str, Any]:
        """获取监控统计信息
        
        Returns:
            监控统计信息
        """
        pass
    
    @abstractmethod
    def reset_statistics(self) -> None:
        """重置统计信息"""
        pass
    
    @abstractmethod
    def add_global_status_callback(
        self, 
        callback: Callable[[str, TaskStatus, TaskStatus], None]
    ) -> str:
        """添加全局状态变化回调
        
        Args:
            callback: 回调函数
            
        Returns:
            回调ID
        """
        pass
    
    @abstractmethod
    def remove_global_status_callback(self, callback_id: str) -> bool:
        """移除全局状态变化回调
        
        Args:
            callback_id: 回调ID
            
        Returns:
            是否移除成功
        """
        pass
    
    @abstractmethod
    def add_health_check_callback(
        self, 
        callback: Callable[[str, Dict[str, Any]], None]
    ) -> str:
        """添加健康检查回调
        
        Args:
            callback: 回调函数
            
        Returns:
            回调ID
        """
        pass
    
    @abstractmethod
    def remove_health_check_callback(self, callback_id: str) -> bool:
        """移除健康检查回调
        
        Args:
            callback_id: 回调ID
            
        Returns:
            是否移除成功
        """
        pass
    
    @abstractmethod
    def force_health_check(self, task_id: Optional[str] = None) -> Dict[str, Any]:
        """强制执行健康检查
        
        Args:
            task_id: 任务ID，如果为None则检查所有监控的任务
            
        Returns:
            健康检查结果
        """
        pass
    
    @abstractmethod
    def get_task_monitor_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务监控信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            监控信息，如果任务未被监控则返回None
        """
        pass