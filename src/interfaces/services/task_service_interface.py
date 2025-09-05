"""任务服务接口

定义任务管理的核心业务逻辑接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime


class ITaskService(ABC):
    """任务服务接口
    
    定义任务管理的核心业务操作。
    """
    
    @abstractmethod
    async def create_task(self, task_data: Dict[str, Any]) -> Any:
        """创建任务
        
        Args:
            task_data: 任务数据
            
        Returns:
            创建的任务对象
        """
        pass
    
    @abstractmethod
    async def get_task(self, task_id: str) -> Optional[Any]:
        """获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def update_task(self, task_id: str, task_data: Dict[str, Any]) -> Optional[Any]:
        """更新任务
        
        Args:
            task_id: 任务ID
            task_data: 更新的任务数据
            
        Returns:
            更新后的任务对象
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
    async def execute_task(self, task_id: str) -> bool:
        """执行任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否执行成功
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
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否取消成功
        """
        pass
    
    @abstractmethod
    async def get_task_status(self, task_id: str) -> Optional[str]:
        """获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态
        """
        pass
    
    @abstractmethod
    async def get_task_progress(self, task_id: str) -> Optional[float]:
        """获取任务进度
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务进度(0-100)
        """
        pass
    
    @abstractmethod
    async def list_tasks(self, filters: Optional[Dict[str, Any]] = None) -> List[Any]:
        """列出任务
        
        Args:
            filters: 过滤条件
            
        Returns:
            任务列表
        """
        pass
    
    @abstractmethod
    async def search_tasks(self, keyword: str) -> List[Any]:
        """搜索任务
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的任务列表
        """
        pass
    
    @abstractmethod
    async def get_task_history(self, task_id: str) -> List[Dict[str, Any]]:
        """获取任务执行历史
        
        Args:
            task_id: 任务ID
            
        Returns:
            执行历史列表
        """
        pass
    
    @abstractmethod
    async def schedule_task(self, task_id: str, schedule_time: datetime) -> bool:
        """调度任务
        
        Args:
            task_id: 任务ID
            schedule_time: 调度时间
            
        Returns:
            是否调度成功
        """
        pass
    
    @abstractmethod
    async def validate_task(self, task_data: Dict[str, Any]) -> bool:
        """验证任务数据
        
        Args:
            task_data: 任务数据
            
        Returns:
            是否有效
        """
        pass