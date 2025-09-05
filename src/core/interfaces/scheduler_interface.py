"""任务调度器接口

定义任务调度器的核心接口契约。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime

from ..models.task import Task, TaskPriority


class ITaskScheduler(ABC):
    """任务调度器接口
    
    定义任务调度和优先级管理的核心接口。
    """
    
    @abstractmethod
    def start(self) -> bool:
        """启动调度器
        
        Returns:
            是否启动成功
        """
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """停止调度器
        
        Returns:
            是否停止成功
        """
        pass
    
    @abstractmethod
    def is_running(self) -> bool:
        """检查调度器是否运行中
        
        Returns:
            是否运行中
        """
        pass
    
    @abstractmethod
    def schedule_task(self, task: Task, scheduled_time: Optional[datetime] = None) -> bool:
        """调度任务
        
        Args:
            task: 要调度的任务
            scheduled_time: 调度时间，如果为None则立即调度
            
        Returns:
            是否调度成功
        """
        pass
    
    @abstractmethod
    def unschedule_task(self, task_id: str) -> bool:
        """取消调度任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否取消成功
        """
        pass
    
    @abstractmethod
    def get_scheduled_tasks(self) -> List[Task]:
        """获取已调度的任务列表
        
        Returns:
            已调度的任务列表
        """
        pass
    
    @abstractmethod
    def get_pending_tasks(self) -> List[Task]:
        """获取待调度的任务列表
        
        Returns:
            待调度的任务列表
        """
        pass
    
    @abstractmethod
    def add_task_dependency(self, task_id: str, dependency_id: str) -> bool:
        """添加任务依赖
        
        Args:
            task_id: 任务ID
            dependency_id: 依赖任务ID
            
        Returns:
            是否添加成功
        """
        pass
    
    @abstractmethod
    def remove_task_dependency(self, task_id: str, dependency_id: str) -> bool:
        """移除任务依赖
        
        Args:
            task_id: 任务ID
            dependency_id: 依赖任务ID
            
        Returns:
            是否移除成功
        """
        pass
    
    @abstractmethod
    def get_task_dependencies(self, task_id: str) -> List[str]:
        """获取任务依赖列表
        
        Args:
            task_id: 任务ID
            
        Returns:
            依赖任务ID列表
        """
        pass
    
    @abstractmethod
    def clear_task_dependencies(self, task_id: str) -> bool:
        """清除任务所有依赖
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否清除成功
        """
        pass
    
    @abstractmethod
    def check_dependencies_satisfied(self, task_id: str) -> bool:
        """检查任务依赖是否满足
        
        Args:
            task_id: 任务ID
            
        Returns:
            依赖是否满足
        """
        pass
    
    @abstractmethod
    def has_circular_dependency(self, task_id: str, dependency_id: str) -> bool:
        """检查是否存在循环依赖
        
        Args:
            task_id: 任务ID
            dependency_id: 依赖任务ID
            
        Returns:
            是否存在循环依赖
        """
        pass
    
    @abstractmethod
    def set_priority_weights(self, weights: Dict[TaskPriority, float]) -> None:
        """设置优先级权重
        
        Args:
            weights: 优先级权重映射
        """
        pass
    
    @abstractmethod
    def calculate_task_priority(self, task: Task) -> float:
        """计算任务优先级分数
        
        Args:
            task: 任务对象
            
        Returns:
            优先级分数
        """
        pass
    
    @abstractmethod
    def set_max_concurrent_tasks(self, max_tasks: int) -> None:
        """设置最大并发任务数
        
        Args:
            max_tasks: 最大并发任务数
        """
        pass
    
    @abstractmethod
    def get_scheduler_status(self) -> Dict[str, Any]:
        """获取调度器状态
        
        Returns:
            调度器状态信息
        """
        pass
    
    @abstractmethod
    def reset_statistics(self) -> None:
        """重置统计信息"""
        pass
    
    @abstractmethod
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """获取依赖关系图
        
        Returns:
            依赖关系图，键为任务ID，值为依赖任务ID列表
        """
        pass
    
    @abstractmethod
    def set_task_execution_callback(self, callback: Callable[[str], None]) -> None:
        """设置任务执行回调
        
        Args:
            callback: 回调函数，接收任务ID参数
        """
        pass
    
    @abstractmethod
    def remove_task_execution_callback(self) -> None:
        """移除任务执行回调"""
        pass