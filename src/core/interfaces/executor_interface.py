"""任务执行器接口

定义任务执行器的核心接口契约。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable, List
from enum import Enum
from datetime import datetime


class ExecutionStatus(Enum):
    """执行状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class ExecutionResult:
    """执行结果数据类"""
    
    def __init__(
        self,
        task_id: str,
        status: ExecutionStatus,
        result: Any = None,
        error: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        execution_time: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.task_id = task_id
        self.status = status
        self.result = result
        self.error = error
        self.start_time = start_time
        self.end_time = end_time
        self.execution_time = execution_time
        self.metadata = metadata or {}


class ITaskExecutor(ABC):
    """任务执行器接口
    
    定义任务执行的核心接口。
    """
    
    @abstractmethod
    async def execute_task(
        self, 
        task_id: str,
        task_config: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """执行任务
        
        Args:
            task_id: 任务ID
            task_config: 任务配置
            context: 执行上下文
            
        Returns:
            执行结果
        """
        pass
    
    @abstractmethod
    async def pause_task(self, task_id: str) -> bool:
        """暂停任务执行
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否暂停成功
        """
        pass
    
    @abstractmethod
    async def resume_task(self, task_id: str) -> bool:
        """恢复任务执行
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否恢复成功
        """
        pass
    
    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务执行
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否取消成功
        """
        pass
    
    @abstractmethod
    def get_execution_status(self, task_id: str) -> Optional[ExecutionStatus]:
        """获取任务执行状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            执行状态，如果任务不存在则返回None
        """
        pass
    
    @abstractmethod
    def get_execution_result(self, task_id: str) -> Optional[ExecutionResult]:
        """获取任务执行结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            执行结果，如果任务不存在则返回None
        """
        pass
    
    @abstractmethod
    def get_running_tasks(self) -> List[str]:
        """获取正在运行的任务列表
        
        Returns:
            正在运行的任务ID列表
        """
        pass
    
    @abstractmethod
    def get_completed_tasks(self) -> List[str]:
        """获取已完成的任务列表
        
        Returns:
            已完成的任务ID列表
        """
        pass
    
    @abstractmethod
    def get_failed_tasks(self) -> List[str]:
        """获取失败的任务列表
        
        Returns:
            失败的任务ID列表
        """
        pass
    
    @abstractmethod
    def set_execution_callback(
        self, 
        callback: Callable[[str, ExecutionStatus, Optional[Any]], None]
    ) -> None:
        """设置执行状态回调
        
        Args:
            callback: 回调函数，参数为(task_id, status, result)
        """
        pass
    
    @abstractmethod
    def remove_execution_callback(self) -> None:
        """移除执行状态回调"""
        pass
    
    @abstractmethod
    def get_execution_statistics(self) -> Dict[str, Any]:
        """获取执行统计信息
        
        Returns:
            统计信息字典
        """
        pass
    
    @abstractmethod
    def clear_completed_tasks(self) -> int:
        """清理已完成的任务
        
        Returns:
            清理的任务数量
        """
        pass
    
    @abstractmethod
    def clear_failed_tasks(self) -> int:
        """清理失败的任务
        
        Returns:
            清理的任务数量
        """
        pass
    
    @abstractmethod
    async def validate_task_config(self, task_config: Dict[str, Any]) -> bool:
        """验证任务配置
        
        Args:
            task_config: 任务配置
            
        Returns:
            是否有效
        """
        pass
    
    @abstractmethod
    def get_supported_task_types(self) -> List[str]:
        """获取支持的任务类型
        
        Returns:
            支持的任务类型列表
        """
        pass
    
    @abstractmethod
    def is_task_type_supported(self, task_type: str) -> bool:
        """检查是否支持指定的任务类型
        
        Args:
            task_type: 任务类型
            
        Returns:
            是否支持
        """
        pass
    
    @abstractmethod
    async def prepare_execution_environment(
        self, 
        task_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """准备执行环境
        
        Args:
            task_config: 任务配置
            
        Returns:
            执行环境信息
        """
        pass
    
    @abstractmethod
    async def cleanup_execution_environment(
        self, 
        task_id: str,
        environment_info: Dict[str, Any]
    ) -> bool:
        """清理执行环境
        
        Args:
            task_id: 任务ID
            environment_info: 执行环境信息
            
        Returns:
            是否清理成功
        """
        pass
    
    @abstractmethod
    def get_execution_logs(self, task_id: str) -> List[str]:
        """获取任务执行日志
        
        Args:
            task_id: 任务ID
            
        Returns:
            执行日志列表
        """
        pass
    
    @abstractmethod
    def get_resource_usage(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务资源使用情况
        
        Args:
            task_id: 任务ID
            
        Returns:
            资源使用情况，如果任务不存在则返回None
        """
        pass