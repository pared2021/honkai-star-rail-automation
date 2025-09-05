"""资源管理器接口

定义资源管理器的核心接口契约。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..types.resource_types import ResourceType, ResourceLimits, ResourceUsage


class IResourceManager(ABC):
    """资源管理器接口
    
    定义任务执行资源限制和管理的核心接口。
    """
    
    @abstractmethod
    def start_monitoring(self) -> bool:
        """启动资源监控
        
        Returns:
            是否启动成功
        """
        pass
    
    @abstractmethod
    def stop_monitoring(self) -> bool:
        """停止资源监控
        
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
    def check_resource_availability(self, required_resources: ResourceLimits) -> bool:
        """检查资源可用性
        
        Args:
            required_resources: 所需资源
            
        Returns:
            资源是否可用
        """
        pass
    
    @abstractmethod
    def can_execute_task(self, task_id: str) -> bool:
        """检查任务是否可以执行
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否可以执行
        """
        pass
    
    @abstractmethod
    def acquire_resources(self, task_id: str, resources: ResourceLimits) -> bool:
        """获取资源
        
        Args:
            task_id: 任务ID
            resources: 所需资源
            
        Returns:
            是否获取成功
        """
        pass
    
    @abstractmethod
    def release_resources(self, task_id: str) -> bool:
        """释放资源
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否释放成功
        """
        pass
    
    @abstractmethod
    def set_task_resource_limits(self, task_id: str, limits: ResourceLimits) -> None:
        """设置任务资源限制
        
        Args:
            task_id: 任务ID
            limits: 资源限制
        """
        pass
    
    @abstractmethod
    def get_task_resource_limits(self, task_id: str) -> Optional[ResourceLimits]:
        """获取任务资源限制
        
        Args:
            task_id: 任务ID
            
        Returns:
            资源限制，如果未设置则返回None
        """
        pass
    
    @abstractmethod
    def update_task_resource_usage(self, task_id: str, usage: ResourceUsage) -> None:
        """更新任务资源使用情况
        
        Args:
            task_id: 任务ID
            usage: 资源使用情况
        """
        pass
    
    @abstractmethod
    def get_task_resource_usage(self, task_id: str) -> Optional[ResourceUsage]:
        """获取任务资源使用情况
        
        Args:
            task_id: 任务ID
            
        Returns:
            资源使用情况，如果任务不存在则返回None
        """
        pass
    
    @abstractmethod
    def get_system_resource_usage(self) -> ResourceUsage:
        """获取系统资源使用情况
        
        Returns:
            系统资源使用情况
        """
        pass
    
    @abstractmethod
    def get_resource_statistics(self) -> Dict[str, Any]:
        """获取资源统计信息
        
        Returns:
            资源统计信息
        """
        pass
    
    @abstractmethod
    def get_usage_history(
        self, 
        resource_type: ResourceType, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """获取资源使用历史
        
        Args:
            resource_type: 资源类型
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            使用历史记录列表
        """
        pass
    
    @abstractmethod
    def set_warning_thresholds(self, thresholds: Dict[ResourceType, float]) -> None:
        """设置警告阈值
        
        Args:
            thresholds: 资源类型到阈值的映射
        """
        pass
    
    @abstractmethod
    def get_warning_thresholds(self) -> Dict[ResourceType, float]:
        """获取警告阈值
        
        Returns:
            资源类型到阈值的映射
        """
        pass
    
    @abstractmethod
    def set_default_limits(self, limits: ResourceLimits) -> None:
        """设置默认资源限制
        
        Args:
            limits: 默认资源限制
        """
        pass
    
    @abstractmethod
    def get_default_limits(self) -> ResourceLimits:
        """获取默认资源限制
        
        Returns:
            默认资源限制
        """
        pass
    
    @abstractmethod
    def reset_statistics(self) -> None:
        """重置统计信息"""
        pass
    
    @abstractmethod
    def clear_usage_history(self) -> None:
        """清空使用历史"""
        pass
    
    @abstractmethod
    def get_resource_pressure(self) -> Dict[ResourceType, float]:
        """获取资源压力
        
        Returns:
            资源类型到压力值的映射（0.0-1.0）
        """
        pass
    
    @abstractmethod
    def estimate_task_resource_requirements(self, task_id: str) -> ResourceLimits:
        """估算任务资源需求
        
        Args:
            task_id: 任务ID
            
        Returns:
            估算的资源需求
        """
        pass
    
    @abstractmethod
    def get_available_resources(self) -> ResourceLimits:
        """获取可用资源
        
        Returns:
            当前可用资源
        """
        pass
    
    @abstractmethod
    def add_resource_monitor_callback(
        self, 
        callback: callable,
        resource_type: Optional[ResourceType] = None
    ) -> str:
        """添加资源监控回调
        
        Args:
            callback: 回调函数
            resource_type: 资源类型，如果为None则监控所有资源
            
        Returns:
            回调ID
        """
        pass
    
    @abstractmethod
    def remove_resource_monitor_callback(self, callback_id: str) -> bool:
        """移除资源监控回调
        
        Args:
            callback_id: 回调ID
            
        Returns:
            是否移除成功
        """
        pass