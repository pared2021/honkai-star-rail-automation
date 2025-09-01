# -*- coding: utf-8 -*-
"""
任务数据访问层接口定义
定义统一的数据访问接口，支持异步操作
"""

import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

from src.models.task_models import Task, TaskConfig
from src.core.enums import TaskStatus, TaskType, TaskPriority
from src.exceptions import (
    RepositoryError, TaskNotFoundError, DuplicateTaskError,
    DatabaseConnectionError, QueryExecutionError, ValidationError
)


class TaskRepository(ABC):
    """任务数据访问层抽象接口"""
    
    @abstractmethod
    async def create_task(self, task: Task) -> str:
        """创建任务
        
        Args:
            task: 任务对象
            
        Returns:
            str: 创建的任务ID
            
        Raises:
            RepositoryError: 数据访问错误
        """
        pass
    
    @abstractmethod
    async def get_task(self, task_id: str) -> Optional[Task]:
        """根据ID获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Task]: 任务对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def update_task(self, task: Task) -> bool:
        """更新任务
        
        Args:
            task: 任务对象
            
        Returns:
            bool: 更新是否成功
        """
        pass
    
    @abstractmethod
    async def delete_task(self, task_id: str) -> bool:
        """删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 删除是否成功
        """
        pass
    
    @abstractmethod
    async def list_tasks(
        self,
        user_id: Optional[str] = None,
        status: Optional[Union[TaskStatus, List[TaskStatus]]] = None,
        task_type: Optional[Union[TaskType, List[TaskType]]] = None,
        priority: Optional[Union[TaskPriority, List[TaskPriority]]] = None,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        order_by: str = "created_at",
        order_desc: bool = True
    ) -> List[Task]:
        """查询任务列表
        
        Args:
            user_id: 用户ID过滤
            status: 状态过滤
            task_type: 任务类型过滤
            priority: 优先级过滤
            tags: 标签过滤
            limit: 限制返回数量
            offset: 偏移量
            order_by: 排序字段
            order_desc: 是否降序
            
        Returns:
            List[Task]: 任务列表
        """
        pass
    
    @abstractmethod
    async def count_tasks(
        self,
        user_id: Optional[str] = None,
        status: Optional[Union[TaskStatus, List[TaskStatus]]] = None,
        task_type: Optional[Union[TaskType, List[TaskType]]] = None,
        priority: Optional[Union[TaskPriority, List[TaskPriority]]] = None,
        tags: Optional[List[str]] = None
    ) -> int:
        """统计任务数量
        
        Args:
            user_id: 用户ID过滤
            status: 状态过滤
            task_type: 任务类型过滤
            priority: 优先级过滤
            tags: 标签过滤
            
        Returns:
            int: 任务数量
        """
        pass
    
    @abstractmethod
    async def get_tasks_by_schedule(
        self,
        current_time: datetime,
        user_id: Optional[str] = None
    ) -> List[Task]:
        """获取需要调度的任务
        
        Args:
            current_time: 当前时间
            user_id: 用户ID过滤
            
        Returns:
            List[Task]: 需要调度的任务列表
        """
        pass
    
    @abstractmethod
    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        error_message: Optional[str] = None
    ) -> bool:
        """更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            error_message: 错误信息（可选）
            
        Returns:
            bool: 更新是否成功
        """
        pass
    
    @abstractmethod
    async def record_task_execution(
        self,
        task_id: str,
        success: bool,
        message: Optional[str] = None
    ) -> bool:
        """记录任务执行结果
        
        Args:
            task_id: 任务ID
            success: 是否成功
            message: 执行信息
            
        Returns:
            bool: 记录是否成功
        """
        pass
    
    @abstractmethod
    async def get_task_statistics(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取任务统计信息
        
        Args:
            user_id: 用户ID过滤
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        pass
    
    @abstractmethod
    async def search_tasks(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Task]:
        """搜索任务
        
        Args:
            query: 搜索关键词
            user_id: 用户ID过滤
            limit: 限制返回数量
            offset: 偏移量
            
        Returns:
            List[Task]: 搜索结果
        """
        pass
    
    @abstractmethod
    async def backup_tasks(
        self,
        user_id: Optional[str] = None,
        backup_path: Optional[str] = None
    ) -> str:
        """备份任务数据
        
        Args:
            user_id: 用户ID过滤
            backup_path: 备份路径
            
        Returns:
            str: 备份文件路径
        """
        pass
    
    @abstractmethod
    async def restore_tasks(
        self,
        backup_path: str,
        user_id: Optional[str] = None
    ) -> int:
        """恢复任务数据
        
        Args:
            backup_path: 备份文件路径
            user_id: 用户ID过滤
            
        Returns:
            int: 恢复的任务数量
        """
        pass
    
    @abstractmethod
    async def cleanup_old_tasks(
        self,
        days: int = 30,
        status_filter: Optional[List[TaskStatus]] = None
    ) -> int:
        """清理旧任务
        
        Args:
            days: 保留天数
            status_filter: 状态过滤
            
        Returns:
            int: 清理的任务数量
        """
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化数据访问层
        
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    async def close(self) -> bool:
        """关闭数据访问层
        
        Returns:
            bool: 关闭是否成功
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            Dict[str, Any]: 健康状态信息
        """
        pass