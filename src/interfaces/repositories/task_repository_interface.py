"""任务仓储接口

定义任务相关的数据访问接口。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from .base_repository_interface import IBaseRepository


class ITaskRepository(IBaseRepository, ABC):
    """任务仓储接口
    
    定义任务相关的数据访问操作。
    """
    
    @abstractmethod
    async def find_by_status(self, status: str) -> List[Any]:
        """根据状态查找任务
        
        Args:
            status: 任务状态
            
        Returns:
            任务列表
        """
        pass
    
    @abstractmethod
    async def find_by_priority(self, priority: str) -> List[Any]:
        """根据优先级查找任务
        
        Args:
            priority: 任务优先级
            
        Returns:
            任务列表
        """
        pass
    
    @abstractmethod
    async def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Any]:
        """根据日期范围查找任务
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            任务列表
        """
        pass
    
    @abstractmethod
    async def find_pending_tasks(self) -> List[Any]:
        """查找待执行的任务
        
        Returns:
            待执行任务列表
        """
        pass
    
    @abstractmethod
    async def find_running_tasks(self) -> List[Any]:
        """查找正在运行的任务
        
        Returns:
            正在运行的任务列表
        """
        pass
    
    @abstractmethod
    async def find_completed_tasks(self, limit: Optional[int] = None) -> List[Any]:
        """查找已完成的任务
        
        Args:
            limit: 限制返回数量
            
        Returns:
            已完成任务列表
        """
        pass
    
    @abstractmethod
    async def update_status(self, task_id: str, status: str) -> bool:
        """更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            
        Returns:
            是否更新成功
        """
        pass
    
    @abstractmethod
    async def update_progress(self, task_id: str, progress: float) -> bool:
        """更新任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度百分比(0-100)
            
        Returns:
            是否更新成功
        """
        pass
    
    @abstractmethod
    async def add_execution_log(self, task_id: str, log_entry: Dict[str, Any]) -> bool:
        """添加执行日志
        
        Args:
            task_id: 任务ID
            log_entry: 日志条目
            
        Returns:
            是否添加成功
        """
        pass
    
    @abstractmethod
    async def get_execution_history(self, task_id: str) -> List[Dict[str, Any]]:
        """获取执行历史
        
        Args:
            task_id: 任务ID
            
        Returns:
            执行历史列表
        """
        pass
    
    @abstractmethod
    async def cleanup_old_tasks(self, days: int) -> int:
        """清理旧任务
        
        Args:
            days: 保留天数
            
        Returns:
            清理的任务数量
        """
        pass