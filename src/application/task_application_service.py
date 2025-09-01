# -*- coding: utf-8 -*-
"""
任务应用服务层
提供任务管理的应用层业务逻辑，协调领域服务和基础设施服务
"""

import uuid
import asyncio
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass

from loguru import logger
import os
import sys

# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.unified_models import (
    Task, TaskConfig, TaskStatus, TaskType, TaskPriority
)
from services.event_bus import TaskEvent, TaskEventType
from services.task_service import TaskService, TaskSearchCriteria, TaskExecutionResult
from services.event_bus import EventBus
from services.base_async_service import BaseAsyncService
from repositories.task_repository import TaskRepository


class TaskApplicationServiceError(Exception):
    """任务应用服务异常基类"""
    def __init__(self, message: str, error_code: str = "TASK_APP_SERVICE_ERROR", original_error: Exception = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.original_error = original_error


class TaskValidationError(TaskApplicationServiceError):
    """任务验证错误"""
    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message, "VALIDATION_ERROR", original_error)


class TaskNotFoundError(TaskApplicationServiceError):
    """任务不存在错误"""
    def __init__(self, task_id: str, original_error: Exception = None):
        super().__init__(f"Task not found: {task_id}", "TASK_NOT_FOUND", original_error)
        self.task_id = task_id


class TaskPermissionError(TaskApplicationServiceError):
    """任务权限错误"""
    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message, "PERMISSION_ERROR", original_error)


@dataclass
class TaskCreateRequest:
    """任务创建请求"""
    name: str
    task_type: TaskType
    description: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    max_retries: int = 3
    timeout_seconds: int = 300
    automation_config: Dict[str, Any] = None
    schedule_config: Optional[Dict[str, Any]] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.automation_config is None:
            self.automation_config = {}
        if self.tags is None:
            self.tags = []


@dataclass
class TaskUpdateRequest:
    """任务更新请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    max_retries: Optional[int] = None
    timeout_seconds: Optional[int] = None
    automation_config: Optional[Dict[str, Any]] = None
    schedule_config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


@dataclass
class TaskListRequest:
    """任务列表查询请求"""
    user_id: str = "default"
    status: Optional[Union[TaskStatus, List[TaskStatus]]] = None
    task_type: Optional[Union[TaskType, List[TaskType]]] = None
    priority: Optional[Union[TaskPriority, List[TaskPriority]]] = None
    tags: Optional[List[str]] = None
    name_pattern: Optional[str] = None
    description_pattern: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: Optional[int] = None
    offset: int = 0
    order_by: str = "created_at"
    order_desc: bool = True


@dataclass
class TaskSearchRequest:
    """任务搜索请求"""
    query: str
    user_id: str = "default"
    limit: Optional[int] = None
    offset: int = 0


@dataclass
class TaskStatisticsRequest:
    """任务统计请求"""
    user_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class TaskApplicationService(BaseAsyncService):
    """任务应用服务"""
    
    def __init__(
        self,
        task_service: TaskService,
        event_bus: EventBus
    ):
        from src.services.base_async_service import ServiceConfig
        
        # 创建服务配置
        config = ServiceConfig(
            name="TaskApplicationService",
            version="1.0.0",
            description="任务应用服务",
            auto_start=True
        )
        
        super().__init__(config)
        self.task_service = task_service
        self.event_bus = event_bus
        self._initialized = False
        
        # 注册事件监听器
        self._register_event_handlers()
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        self.event_bus.subscribe(TaskEventType.TASK_CREATED, self._on_task_created)
        self.event_bus.subscribe(TaskEventType.TASK_UPDATED, self._on_task_updated)
        self.event_bus.subscribe(TaskEventType.TASK_DELETED, self._on_task_deleted)
        self.event_bus.subscribe(TaskEventType.TASK_STATUS_CHANGED, self._on_task_status_changed)
        self.event_bus.subscribe(TaskEventType.TASK_EXECUTION_STARTED, self._on_task_execution_started)
        self.event_bus.subscribe(TaskEventType.TASK_EXECUTION_COMPLETED, self._on_task_execution_completed)
        self.event_bus.subscribe(TaskEventType.TASK_EXECUTION_FAILED, self._on_task_execution_failed)
    
    async def initialize(self) -> bool:
        """初始化服务"""
        try:
            if not self._initialized:
                # 确保任务服务已初始化
                await self.task_service.initialize()
                
                self._initialized = True
                logger.info("任务应用服务初始化完成")
            
            return True
            
        except Exception as e:
            logger.error(f"任务应用服务初始化失败: {e}")
            return False
    
    async def _ensure_initialized(self) -> None:
        """确保服务已初始化"""
        if not self._initialized:
            await self.initialize()
    
    # ==================== 任务CRUD操作 ====================
    
    async def create_task(self, request: TaskCreateRequest, user_id: str = "default") -> str:
        """
        创建任务
        
        Args:
            request: 任务创建请求
            user_id: 用户ID
            
        Returns:
            str: 任务ID
            
        Raises:
            TaskValidationError: 任务验证失败
        """
        await self._ensure_initialized()
        
        try:
            # 验证请求
            self._validate_create_request(request)
            
            # 创建任务配置
            task_config = TaskConfig(
                name=request.name,
                task_type=request.task_type,
                description=request.description,
                priority=request.priority,
                max_retries=request.max_retries,
                timeout_seconds=request.timeout_seconds,
                automation_config=request.automation_config,
                schedule_config=request.schedule_config,
                tags=request.tags
            )
            
            # 调用领域服务创建任务
            task_id = await self.task_service.create_task(task_config, user_id)
            
            logger.info(f"应用服务创建任务成功: {task_id}")
            return task_id
            
        except Exception as e:
            if isinstance(e, TaskValidationError):
                raise
            logger.error(f"应用服务创建任务失败: {e}")
            raise TaskApplicationServiceError(f"Failed to create task: {e}", "CREATE_ERROR", e)
    
    async def get_task(self, task_id: str, user_id: str = "default") -> Optional[Task]:
        """
        获取任务
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            Optional[Task]: 任务对象
            
        Raises:
            TaskPermissionError: 权限不足
        """
        await self._ensure_initialized()
        
        try:
            # 获取任务
            task = await self.task_service.get_task(task_id)
            
            if task:
                # 检查权限
                self._check_task_permission(task, user_id)
            
            return task
            
        except Exception as e:
            if isinstance(e, TaskPermissionError):
                raise
            logger.error(f"应用服务获取任务失败: {e}")
            raise TaskApplicationServiceError(f"Failed to get task: {e}", "GET_ERROR", e)
    
    async def get_all_tasks(self, user_id: str = "default") -> List[Task]:
        """
        获取所有任务
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[Task]: 所有任务列表
        """
        await self._ensure_initialized()
        
        try:
            # 构建简单的搜索条件，获取所有任务
            criteria = TaskSearchCriteria(
                user_id=user_id,
                limit=1000,  # 设置一个较大的限制
                order_by="created_at",
                order_desc=True
            )
            
            # 调用领域服务查询
            return await self.task_service.list_tasks(criteria)
            
        except Exception as e:
            logger.error(f"应用服务获取所有任务失败: {e}")
            raise TaskApplicationServiceError(f"Failed to get all tasks: {e}", "GET_ALL_ERROR", e)
    
    async def list_tasks(self, request: TaskListRequest) -> List[Task]:
        """
        列出任务
        
        Args:
            request: 任务列表查询请求
            
        Returns:
            List[Task]: 任务列表
        """
        await self._ensure_initialized()
        
        try:
            # 构建搜索条件
            criteria = TaskSearchCriteria(
                user_id=request.user_id,
                status=request.status,
                task_type=request.task_type,
                priority=request.priority,
                tags=request.tags,
                name_pattern=request.name_pattern,
                description_pattern=request.description_pattern,
                created_after=request.created_after,
                created_before=request.created_before,
                limit=request.limit,
                offset=request.offset,
                order_by=request.order_by,
                order_desc=request.order_desc
            )
            
            # 调用领域服务查询
            return await self.task_service.list_tasks(criteria)
            
        except Exception as e:
            logger.error(f"应用服务列出任务失败: {e}")
            raise TaskApplicationServiceError(f"Failed to list tasks: {e}", "LIST_ERROR", e)
    
    async def update_task(self, task_id: str, request: TaskUpdateRequest, user_id: str = "default") -> bool:
        """
        更新任务
        
        Args:
            task_id: 任务ID
            request: 任务更新请求
            user_id: 用户ID
            
        Returns:
            bool: 更新是否成功
            
        Raises:
            TaskNotFoundError: 任务不存在
            TaskPermissionError: 权限不足
            TaskValidationError: 验证失败
        """
        await self._ensure_initialized()
        
        try:
            # 获取现有任务
            task = await self.task_service.get_task(task_id)
            if not task:
                raise TaskNotFoundError(task_id)
            
            # 检查权限
            self._check_task_permission(task, user_id)
            
            # 验证更新请求
            self._validate_update_request(request)
            
            # 应用更新
            updated_task = self._apply_task_updates(task, request)
            
            # 调用领域服务更新
            success = await self.task_service.update_task(updated_task)
            
            if success:
                logger.info(f"应用服务更新任务成功: {task_id}")
            
            return success
            
        except Exception as e:
            if isinstance(e, (TaskNotFoundError, TaskPermissionError, TaskValidationError)):
                raise
            logger.error(f"应用服务更新任务失败: {e}")
            raise TaskApplicationServiceError(f"Failed to update task: {e}", "UPDATE_ERROR", e)
    
    async def delete_task(self, task_id: str, user_id: str = "default") -> bool:
        """
        删除任务
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            bool: 删除是否成功
            
        Raises:
            TaskNotFoundError: 任务不存在
            TaskPermissionError: 权限不足
        """
        await self._ensure_initialized()
        
        try:
            # 获取任务
            task = await self.task_service.get_task(task_id)
            if not task:
                raise TaskNotFoundError(task_id)
            
            # 检查权限
            self._check_task_permission(task, user_id)
            
            # 调用领域服务删除
            success = await self.task_service.delete_task(task_id)
            
            if success:
                logger.info(f"应用服务删除任务成功: {task_id}")
            
            return success
            
        except Exception as e:
            if isinstance(e, (TaskNotFoundError, TaskPermissionError)):
                raise
            logger.error(f"应用服务删除任务失败: {e}")
            raise TaskApplicationServiceError(f"Failed to delete task: {e}", "DELETE_ERROR", e)
    
    # ==================== 任务执行操作 ====================
    
    async def execute_task(self, task_id: str, user_id: str = "default") -> TaskExecutionResult:
        """
        执行任务
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            TaskExecutionResult: 执行结果
            
        Raises:
            TaskNotFoundError: 任务不存在
            TaskPermissionError: 权限不足
        """
        await self._ensure_initialized()
        
        try:
            # 获取任务
            task = await self.task_service.get_task(task_id)
            if not task:
                raise TaskNotFoundError(task_id)
            
            # 检查权限
            self._check_task_permission(task, user_id)
            
            # 调用领域服务执行
            result = await self.task_service.execute_task(task_id)
            
            logger.info(f"应用服务执行任务完成: {task_id}, 成功: {result.success}")
            return result
            
        except Exception as e:
            if isinstance(e, (TaskNotFoundError, TaskPermissionError)):
                raise
            logger.error(f"应用服务执行任务失败: {e}")
            raise TaskApplicationServiceError(f"Failed to execute task: {e}", "EXECUTE_ERROR", e)
    
    async def pause_task(self, task_id: str, user_id: str = "default") -> bool:
        """
        暂停任务
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            bool: 暂停是否成功
        """
        await self._ensure_initialized()
        
        try:
            # 获取任务
            task = await self.task_service.get_task(task_id)
            if not task:
                raise TaskNotFoundError(task_id)
            
            # 检查权限
            self._check_task_permission(task, user_id)
            
            # 更新状态为暂停
            success = await self.task_service.update_task_status(task_id, TaskStatus.PAUSED)
            
            if success:
                logger.info(f"应用服务暂停任务成功: {task_id}")
            
            return success
            
        except Exception as e:
            if isinstance(e, (TaskNotFoundError, TaskPermissionError)):
                raise
            logger.error(f"应用服务暂停任务失败: {e}")
            raise TaskApplicationServiceError(f"Failed to pause task: {e}", "PAUSE_ERROR", e)
    
    async def resume_task(self, task_id: str, user_id: str = "default") -> bool:
        """
        恢复任务
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            bool: 恢复是否成功
        """
        await self._ensure_initialized()
        
        try:
            # 获取任务
            task = await self.task_service.get_task(task_id)
            if not task:
                raise TaskNotFoundError(task_id)
            
            # 检查权限
            self._check_task_permission(task, user_id)
            
            # 更新状态为运行中
            success = await self.task_service.update_task_status(task_id, TaskStatus.RUNNING)
            
            if success:
                logger.info(f"应用服务恢复任务成功: {task_id}")
            
            return success
            
        except Exception as e:
            if isinstance(e, (TaskNotFoundError, TaskPermissionError)):
                raise
            logger.error(f"应用服务恢复任务失败: {e}")
            raise TaskApplicationServiceError(f"Failed to resume task: {e}", "RESUME_ERROR", e)
    
    async def cancel_task(self, task_id: str, user_id: str = "default") -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            bool: 取消是否成功
        """
        await self._ensure_initialized()
        
        try:
            # 获取任务
            task = await self.task_service.get_task(task_id)
            if not task:
                raise TaskNotFoundError(task_id)
            
            # 检查权限
            self._check_task_permission(task, user_id)
            
            # 更新状态为已取消
            success = await self.task_service.update_task_status(task_id, TaskStatus.CANCELLED)
            
            if success:
                logger.info(f"应用服务取消任务成功: {task_id}")
            
            return success
            
        except Exception as e:
            if isinstance(e, (TaskNotFoundError, TaskPermissionError)):
                raise
            logger.error(f"应用服务取消任务失败: {e}")
            raise TaskApplicationServiceError(f"Failed to cancel task: {e}", "CANCEL_ERROR", e)
    
    # ==================== 任务查询操作 ====================
    
    async def search_tasks(self, request: TaskSearchRequest) -> List[Task]:
        """
        搜索任务
        
        Args:
            request: 搜索请求
            
        Returns:
            List[Task]: 匹配的任务列表
        """
        await self._ensure_initialized()
        
        try:
            return await self.task_service.search_tasks(
                query=request.query,
                user_id=request.user_id,
                limit=request.limit,
                offset=request.offset
            )
            
        except Exception as e:
            logger.error(f"应用服务搜索任务失败: {e}")
            raise TaskApplicationServiceError(f"Failed to search tasks: {e}", "SEARCH_ERROR", e)
    
    async def count_tasks(self, request: TaskListRequest) -> int:
        """
        统计任务数量
        
        Args:
            request: 任务列表查询请求
            
        Returns:
            int: 任务数量
        """
        await self._ensure_initialized()
        
        try:
            # 构建搜索条件
            criteria = TaskSearchCriteria(
                user_id=request.user_id,
                status=request.status,
                task_type=request.task_type,
                priority=request.priority,
                tags=request.tags,
                name_pattern=request.name_pattern,
                description_pattern=request.description_pattern,
                created_after=request.created_after,
                created_before=request.created_before
            )
            
            return await self.task_service.count_tasks(criteria)
            
        except Exception as e:
            logger.error(f"应用服务统计任务失败: {e}")
            raise TaskApplicationServiceError(f"Failed to count tasks: {e}", "COUNT_ERROR", e)
    
    async def get_task_statistics(self, request: TaskStatisticsRequest) -> Dict[str, Any]:
        """
        获取任务统计信息
        
        Args:
            request: 统计请求
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        await self._ensure_initialized()
        
        try:
            return await self.task_service.get_task_statistics(
                user_id=request.user_id,
                start_date=request.start_date,
                end_date=request.end_date
            )
            
        except Exception as e:
            logger.error(f"应用服务获取统计失败: {e}")
            raise TaskApplicationServiceError(f"Failed to get statistics: {e}", "STATISTICS_ERROR", e)
    
    async def get_running_tasks(self, user_id: str = "default") -> List[str]:
        """
        获取正在运行的任务列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[str]: 正在运行的任务ID列表
        """
        await self._ensure_initialized()
        
        try:
            # 获取所有正在运行的任务
            running_task_ids = await self.task_service.get_running_tasks()
            
            # 过滤用户权限
            filtered_task_ids = []
            for task_id in running_task_ids:
                task = await self.task_service.get_task(task_id)
                if task and task.user_id == user_id:
                    filtered_task_ids.append(task_id)
            
            return filtered_task_ids
            
        except Exception as e:
            logger.error(f"应用服务获取运行任务失败: {e}")
            raise TaskApplicationServiceError(f"Failed to get running tasks: {e}", "GET_RUNNING_ERROR", e)
    
    async def get_recent_tasks(self, user_id: str = "default", limit: int = 10) -> List[Task]:
        """
        获取最近的任务列表
        
        Args:
            user_id: 用户ID
            limit: 返回任务数量限制，默认10个
            
        Returns:
            List[Task]: 按创建时间倒序排列的最近任务列表
        """
        await self._ensure_initialized()
        
        try:
            # 构建搜索条件，按创建时间倒序
            criteria = TaskSearchCriteria(
                user_id=user_id,
                order_by="created_at",
                order_desc=True,
                limit=limit
            )
            
            # 获取任务列表
            tasks = await self.task_service.list_tasks(criteria)
            
            return tasks
            
        except Exception as e:
            logger.error(f"应用服务获取最近任务失败: {e}")
            raise TaskApplicationServiceError(f"Failed to get recent tasks: {e}", "GET_RECENT_ERROR", e)
    
    # ==================== 数据管理操作 ====================
    
    async def backup_tasks(self, user_id: str = "default", backup_path: Optional[str] = None) -> str:
        """
        备份任务数据
        
        Args:
            user_id: 用户ID
            backup_path: 备份文件路径
            
        Returns:
            str: 备份文件路径
        """
        await self._ensure_initialized()
        
        try:
            return await self.task_service.backup_tasks(
                user_id=user_id,
                backup_path=backup_path
            )
            
        except Exception as e:
            logger.error(f"应用服务备份任务失败: {e}")
            raise TaskApplicationServiceError(f"Failed to backup tasks: {e}", "BACKUP_ERROR", e)
    
    async def restore_tasks(self, backup_path: str, user_id: str = "default") -> int:
        """
        恢复任务数据
        
        Args:
            backup_path: 备份文件路径
            user_id: 用户ID
            
        Returns:
            int: 恢复的任务数量
        """
        await self._ensure_initialized()
        
        try:
            return await self.task_service.restore_tasks(
                backup_path=backup_path,
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"应用服务恢复任务失败: {e}")
            raise TaskApplicationServiceError(f"Failed to restore tasks: {e}", "RESTORE_ERROR", e)
    
    # ==================== 私有方法 ====================
    
    def _validate_create_request(self, request: TaskCreateRequest):
        """验证任务创建请求"""
        if not request.name or not request.name.strip():
            raise TaskValidationError("Task name cannot be empty")
        
        if len(request.name) > 255:
            raise TaskValidationError("Task name too long (max 255 characters)")
        
        if request.max_retries < 0:
            raise TaskValidationError("Max retries cannot be negative")
        
        if request.timeout_seconds <= 0:
            raise TaskValidationError("Timeout must be positive")
    
    def _validate_update_request(self, request: TaskUpdateRequest):
        """验证任务更新请求"""
        if request.name is not None:
            if not request.name or not request.name.strip():
                raise TaskValidationError("Task name cannot be empty")
            
            if len(request.name) > 255:
                raise TaskValidationError("Task name too long (max 255 characters)")
        
        if request.max_retries is not None and request.max_retries < 0:
            raise TaskValidationError("Max retries cannot be negative")
        
        if request.timeout_seconds is not None and request.timeout_seconds <= 0:
            raise TaskValidationError("Timeout must be positive")
    
    def _check_task_permission(self, task: Task, user_id: str):
        """检查任务权限"""
        if task.user_id != user_id:
            raise TaskPermissionError(f"User {user_id} does not have permission to access task {task.task_id}")
    
    def _apply_task_updates(self, task: Task, request: TaskUpdateRequest) -> Task:
        """应用任务更新"""
        # 创建任务副本
        updated_config = TaskConfig(
            name=request.name if request.name is not None else task.config.name,
            task_type=task.config.task_type,  # 任务类型不允许修改
            description=request.description if request.description is not None else task.config.description,
            priority=request.priority if request.priority is not None else task.config.priority,
            max_retries=request.max_retries if request.max_retries is not None else task.config.max_retries,
            timeout_seconds=request.timeout_seconds if request.timeout_seconds is not None else task.config.timeout_seconds,
            automation_config=request.automation_config if request.automation_config is not None else task.config.automation_config,
            schedule_config=request.schedule_config if request.schedule_config is not None else task.config.schedule_config,
            tags=request.tags if request.tags is not None else task.config.tags
        )
        
        # 创建更新后的任务
        updated_task = Task(
            task_id=task.task_id,
            user_id=task.user_id,
            config=updated_config,
            status=task.status,
            created_at=task.created_at,
            updated_at=datetime.now(),
            started_at=task.started_at,
            completed_at=task.completed_at,
            retry_count=task.retry_count,
            last_error=task.last_error,
            execution_result=task.execution_result
        )
        
        return updated_task
    
    # ==================== 事件处理器 ====================
    
    async def _on_task_created(self, event: TaskEvent):
        """任务创建事件处理器"""
        logger.debug(f"应用服务处理任务创建事件: {event.task_id}")
    
    async def _on_task_updated(self, event: TaskEvent):
        """任务更新事件处理器"""
        logger.debug(f"应用服务处理任务更新事件: {event.task_id}")
    
    async def _on_task_deleted(self, event: TaskEvent):
        """任务删除事件处理器"""
        logger.debug(f"应用服务处理任务删除事件: {event.task_id}")
    
    async def _on_task_status_changed(self, event: TaskEvent):
        """任务状态变更事件处理器"""
        logger.debug(f"应用服务处理任务状态变更事件: {event.task_id}")
    
    async def _on_task_execution_started(self, event: TaskEvent):
        """任务执行开始事件处理器"""
        logger.debug(f"应用服务处理任务执行开始事件: {event.task_id}")
    
    async def _on_task_execution_completed(self, event: TaskEvent):
        """任务执行完成事件处理器"""
        logger.debug(f"应用服务处理任务执行完成事件: {event.task_id}")
    
    async def _on_task_execution_failed(self, event: TaskEvent):
        """任务执行失败事件处理器"""
        logger.debug(f"应用服务处理任务执行失败事件: {event.task_id}")
    
    # ==================== 服务生命周期 ====================
    
    async def close(self) -> bool:
        """
        关闭服务
        
        Returns:
            bool: 关闭是否成功
        """
        try:
            # 关闭任务服务
            await self.task_service.close()
            
            self._initialized = False
            logger.info("任务应用服务已关闭")
            return True
            
        except Exception as e:
            logger.error(f"关闭任务应用服务失败: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            Dict[str, Any]: 健康状态信息
        """
        try:
            # 检查任务服务健康状态
            task_service_health = await self.task_service.health_check()
            
            # 检查应用服务状态
            app_service_status = {
                'initialized': self._initialized
            }
            
            overall_status = 'healthy' if (self._initialized and task_service_health['status'] == 'healthy') else 'unhealthy'
            
            return {
                'status': overall_status,
                'message': 'Task application service health check',
                'details': {
                    'application_service': app_service_status,
                    'task_service': task_service_health
                }
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Health check failed: {e}',
                'details': {
                    'error': str(e),
                    'initialized': self._initialized
                }
            }
    
    # ==================== BaseAsyncService抽象方法实现 ====================
    
    async def _startup(self) -> None:
        """服务启动"""
        await self.initialize()
        logger.info("TaskApplicationService启动完成")
    
    async def _shutdown(self) -> None:
        """服务关闭"""
        await self.close()
        logger.info("TaskApplicationService关闭完成")
    
    async def _health_check(self) -> bool:
        """健康检查"""
        health_result = await self.health_check()
        return health_result['status'] == 'healthy'