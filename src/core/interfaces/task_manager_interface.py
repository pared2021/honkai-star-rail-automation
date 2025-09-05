"""任务管理器接口

定义任务管理器的核心接口契约。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.task import Task, TaskStatus, TaskPriority
from ..models.task_execution import TaskExecution


class ITaskManager(ABC):
    """任务管理器接口
    
    定义任务管理的核心操作接口。
    """
    
    @abstractmethod
    async def create_task(self, task_data: Dict[str, Any]) -> Task:
        """创建任务
        
        Args:
            task_data: 任务数据
            
        Returns:
            创建的任务对象
        """
        pass
    
    @abstractmethod
    async def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """更新任务
        
        Args:
            task_id: 任务ID
            updates: 更新数据
            
        Returns:
            是否更新成功
        """
        pass
    
    @abstractmethod
    async def delete_task(self, task_id: str) -> bool:
        """删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def list_tasks(
        self, 
        user_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Task]:
        """列出任务
        
        Args:
            user_id: 用户ID过滤
            status: 状态过滤
            priority: 优先级过滤
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            任务列表
        """
        pass
    
    @abstractmethod
    async def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            
        Returns:
            是否更新成功
        """
        pass
    
    @abstractmethod
    async def execute_task(self, task_id: str) -> TaskExecution:
        """执行任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务执行对象
        """
        pass
    
    @abstractmethod
    async def pause_task(self, task_id: str) -> bool:
        """暂停任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否暂停成功
        """
        pass
    
    @abstractmethod
    async def resume_task(self, task_id: str) -> bool:
        """恢复任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否恢复成功
        """
        pass
    
    @abstractmethod
    async def stop_task(self, task_id: str) -> bool:
        """停止任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否停止成功
        """
        pass
    
    @abstractmethod
    async def get_task_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """获取任务统计信息
        
        Args:
            user_id: 用户ID过滤
            
        Returns:
            统计信息字典
        """
        pass
    
    @abstractmethod
    async def search_tasks(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Task]:
        """搜索任务
        
        Args:
            query: 搜索查询
            user_id: 用户ID过滤
            limit: 限制数量
            
        Returns:
            匹配的任务列表
        """
        pass