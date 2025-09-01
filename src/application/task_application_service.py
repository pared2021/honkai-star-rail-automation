# -*- coding: utf-8 -*-
"""
任务应用服务层
提供任务管理的应用层业务逻辑，协调领域服务和基础设施服务
"""

import uuid
import asyncio
import time
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass

from loguru import logger
import os
import sys
from PyQt6.QtCore import QObject, pyqtSignal

# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.task_models import (
    Task, TaskConfig, TaskStatus, TaskType, TaskPriority
)
from services.event_bus import TaskEvent, TaskEventType
from services.task_service import TaskService, TaskSearchCriteria, TaskExecutionResult
from services.event_bus import EventBus
from services.base_async_service import BaseAsyncService
from repositories.task_repository import TaskRepository
from core.task_executor import TaskExecutor, ExecutionStatus, ExecutionContext
from automation.automation_controller import AutomationController
from automation.game_detector import GameDetector
from database.db_manager import DatabaseManager
from src.exceptions import (
    TaskValidationError, TaskNotFoundError, TaskPermissionError,
    TaskStateError, TaskExecutionError, ServiceError
)


# 异常类已移至统一的exceptions模块


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


class TaskApplicationService(BaseAsyncService, QObject):
    """任务应用服务
    
    负责任务管理的业务逻辑，协调领域服务和基础设施服务。
    提供应用层的任务操作接口，包括权限检查、请求验证等。
    同时负责任务执行的协调、状态管理和错误处理。
    """
    
    # 执行信号
    execution_started = pyqtSignal(str)  # task_id
    execution_progress = pyqtSignal(str, int)  # task_id, progress
    execution_completed = pyqtSignal(str, dict)  # task_id, result
    execution_paused = pyqtSignal(str)  # task_id
    execution_resumed = pyqtSignal(str)  # task_id
    execution_stopped = pyqtSignal(str)  # task_id
    execution_error = pyqtSignal(str, str)  # task_id, error
    
    def __init__(
        self,
        task_service: TaskService,
        event_bus: EventBus,
        task_executor: TaskExecutor = None,
        automation_controller: AutomationController = None,
        game_detector: GameDetector = None,
        database_manager: DatabaseManager = None
    ):
        from src.services.base_async_service import ServiceConfig
        
        # 创建服务配置
        config = ServiceConfig(
            name="TaskApplicationService",
            version="1.0.0",
            description="任务应用服务",
            auto_start=True
        )
        
        BaseAsyncService.__init__(self, config)
        QObject.__init__(self)
        self.task_service = task_service
        self.event_bus = event_bus
        self.task_executor = task_executor
        self.automation_controller = automation_controller
        self.game_detector = game_detector
        self.database_manager = database_manager
        self._initialized = False
        
        # 执行状态管理
        self._execution_queue = asyncio.Queue()
        self._running_tasks = {}
        self._execution_lock = asyncio.Lock()
        self._queue_processor_task = None
        
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
                
                # 初始化执行相关组件
                if self.task_executor:
                    await self.task_executor.initialize()
                    # 连接执行器信号
                    self.task_executor.execution_started.connect(self._on_execution_started)
                    self.task_executor.execution_progress.connect(self._on_execution_progress)
                    self.task_executor.execution_completed.connect(self._on_execution_completed)
                    self.task_executor.execution_paused.connect(self._on_execution_paused)
                    self.task_executor.execution_resumed.connect(self._on_execution_resumed)
                    self.task_executor.execution_stopped.connect(self._on_execution_stopped)
                    self.task_executor.execution_error.connect(self._on_execution_error)
                
                if self.automation_controller:
                    await self.automation_controller.initialize()
                
                if self.game_detector:
                    await self.game_detector.initialize()
                
                if self.database_manager:
                    await self.database_manager.initialize()
                
                # 启动队列处理器
                self._queue_processor_task = asyncio.create_task(self._process_execution_queue())
                
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
    
    # ==================== 任务执行方法 ====================
    
    async def start_task(self, task_id: str, user_id: str = "default") -> bool:
        """
        启动任务执行
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            bool: 启动是否成功
        """
        await self._ensure_initialized()
        
        try:
            # 获取任务
            task = await self.get_task(task_id, user_id)
            if not task:
                raise TaskNotFoundError(task_id)
            
            # 验证执行请求
            self._validate_execution_request(task)
            
            # 检查游戏状态
            if self.game_detector and not await self._check_game_status():
                raise TaskExecutionError("Game not detected or not ready")
            
            # 添加到执行队列
            await self._execution_queue.put({
                'action': 'start',
                'task_id': task_id,
                'task': task,
                'timestamp': time.time()
            })
            
            logger.info(f"任务 {task_id} 已添加到执行队列")
            return True
            
        except Exception as e:
            logger.error(f"启动任务执行失败: {e}")
            if isinstance(e, (TaskNotFoundError, TaskPermissionError, TaskExecutionError)):
                raise
            raise TaskApplicationServiceError(f"Failed to start task: {e}", "START_ERROR", e)
    
    async def pause_task(self, task_id: str, user_id: str = "default") -> bool:
        """
        暂停任务执行
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            bool: 暂停是否成功
        """
        await self._ensure_initialized()
        
        try:
            # 检查任务是否在运行
            if task_id not in self._running_tasks:
                raise TaskExecutionError(f"Task {task_id} is not running")
            
            # 获取任务
            task = await self.get_task(task_id, user_id)
            if not task:
                raise TaskNotFoundError(task_id)
            
            # 暂停执行
            if self.task_executor:
                success = await self.task_executor.pause_task(task_id)
                if success:
                    # 更新任务状态
                    await self.task_service.update_task_status(task_id, TaskStatus.PAUSED)
                    logger.info(f"任务 {task_id} 已暂停")
                return success
            
            return False
            
        except Exception as e:
            logger.error(f"暂停任务执行失败: {e}")
            if isinstance(e, (TaskNotFoundError, TaskPermissionError, TaskExecutionError)):
                raise
            raise TaskApplicationServiceError(f"Failed to pause task: {e}", "PAUSE_ERROR", e)
    
    async def resume_task(self, task_id: str, user_id: str = "default") -> bool:
        """
        恢复任务执行
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            bool: 恢复是否成功
        """
        await self._ensure_initialized()
        
        try:
            # 获取任务
            task = await self.get_task(task_id, user_id)
            if not task:
                raise TaskNotFoundError(task_id)
            
            # 检查任务状态
            if task.status != TaskStatus.PAUSED:
                raise TaskExecutionError(f"Task {task_id} is not paused")
            
            # 恢复执行
            if self.task_executor:
                success = await self.task_executor.resume_task(task_id)
                if success:
                    # 更新任务状态
                    await self.task_service.update_task_status(task_id, TaskStatus.RUNNING)
                    logger.info(f"任务 {task_id} 已恢复")
                return success
            
            return False
            
        except Exception as e:
            logger.error(f"恢复任务执行失败: {e}")
            if isinstance(e, (TaskNotFoundError, TaskPermissionError, TaskExecutionError)):
                raise
            raise TaskApplicationServiceError(f"Failed to resume task: {e}", "RESUME_ERROR", e)
    
    async def stop_task(self, task_id: str, user_id: str = "default") -> bool:
        """
        停止任务执行
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            bool: 停止是否成功
        """
        await self._ensure_initialized()
        
        try:
            # 获取任务
            task = await self.get_task(task_id, user_id)
            if not task:
                raise TaskNotFoundError(task_id)
            
            # 停止执行
            if self.task_executor:
                success = await self.task_executor.stop_task(task_id)
                if success:
                    # 更新任务状态
                    await self.task_service.update_task_status(task_id, TaskStatus.STOPPED)
                    # 从运行任务列表中移除
                    self._running_tasks.pop(task_id, None)
                    logger.info(f"任务 {task_id} 已停止")
                return success
            
            return False
            
        except Exception as e:
            logger.error(f"停止任务执行失败: {e}")
            if isinstance(e, (TaskNotFoundError, TaskPermissionError, TaskExecutionError)):
                raise
            raise TaskApplicationServiceError(f"Failed to stop task: {e}", "STOP_ERROR", e)
    
    async def get_task_status(self, task_id: str, user_id: str = "default") -> Dict[str, Any]:
        """
        获取任务执行状态
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 任务状态信息
        """
        await self._ensure_initialized()
        
        try:
            # 获取任务
            task = await self.get_task(task_id, user_id)
            if not task:
                raise TaskNotFoundError(task_id)
            
            # 获取执行状态
            execution_status = None
            if self.task_executor and task_id in self._running_tasks:
                execution_status = await self.task_executor.get_task_status(task_id)
            
            return {
                'task_id': task_id,
                'status': task.status.value,
                'progress': execution_status.get('progress', 0) if execution_status else 0,
                'is_running': task_id in self._running_tasks,
                'execution_details': execution_status
            }
            
        except Exception as e:
            logger.error(f"获取任务状态失败: {e}")
            if isinstance(e, (TaskNotFoundError, TaskPermissionError)):
                raise
            raise TaskApplicationServiceError(f"Failed to get task status: {e}", "STATUS_ERROR", e)
    
    async def get_execution_queue_status(self) -> Dict[str, Any]:
        """
        获取执行队列状态
        
        Returns:
            Dict[str, Any]: 队列状态信息
        """
        await self._ensure_initialized()
        
        return {
             'queue_size': self._execution_queue.qsize(),
             'running_tasks': list(self._running_tasks.keys()),
             'running_count': len(self._running_tasks)
         }
    
    # ==================== 执行辅助方法 ====================
    
    def _validate_execution_request(self, task: Task):
        """验证执行请求"""
        if task.status in [TaskStatus.RUNNING, TaskStatus.PAUSED]:
            raise TaskExecutionError(f"Task {task.task_id} is already running or paused")
        
        if task.status == TaskStatus.COMPLETED:
            raise TaskExecutionError(f"Task {task.task_id} is already completed")
    
    async def _check_game_status(self) -> bool:
        """检查游戏状态"""
        try:
            if self.game_detector:
                return await self.game_detector.is_game_running()
            return True
        except Exception as e:
            logger.warning(f"检查游戏状态失败: {e}")
            return False
    
    async def _process_execution_queue(self):
        """处理执行队列"""
        logger.info("执行队列处理器已启动")
        
        while True:
            try:
                # 从队列获取任务
                queue_item = await self._execution_queue.get()
                
                if queue_item['action'] == 'start':
                    await self._execute_task(queue_item['task'])
                
                # 标记队列项已处理
                self._execution_queue.task_done()
                
            except asyncio.CancelledError:
                logger.info("执行队列处理器已取消")
                break
            except Exception as e:
                logger.error(f"处理执行队列项失败: {e}")
    
    async def _execute_task(self, task: Task):
        """执行任务"""
        task_id = task.task_id
        
        try:
            async with self._execution_lock:
                # 添加到运行任务列表
                self._running_tasks[task_id] = {
                    'task': task,
                    'start_time': time.time(),
                    'status': ExecutionStatus.RUNNING
                }
            
            # 更新任务状态
            await self.task_service.update_task_status(task_id, TaskStatus.RUNNING)
            
            # 创建执行上下文
            context = ExecutionContext(
                task_id=task_id,
                task_config=task.config,
                automation_controller=self.automation_controller,
                game_detector=self.game_detector,
                database_manager=self.database_manager
            )
            
            # 执行任务
            if self.task_executor:
                result = await self.task_executor.execute_task(task, context)
                
                # 处理执行结果
                await self._handle_execution_result(task_id, result)
            
        except Exception as e:
            logger.error(f"执行任务 {task_id} 失败: {e}")
            await self._handle_execution_error(task_id, str(e))
        finally:
            # 从运行任务列表中移除
            async with self._execution_lock:
                self._running_tasks.pop(task_id, None)
    
    async def _handle_execution_result(self, task_id: str, result: TaskExecutionResult):
        """处理执行结果"""
        try:
            if result.success:
                # 更新任务状态为完成
                await self.task_service.update_task_status(task_id, TaskStatus.COMPLETED)
                await self.task_service.update_execution_result(task_id, result)
                
                # 发布完成事件
                await self.event_bus.publish(TaskEvent(
                    event_type=TaskEventType.TASK_EXECUTION_COMPLETED,
                    task_id=task_id,
                    data={'result': result.to_dict()}
                ))
                
                logger.info(f"任务 {task_id} 执行完成")
            else:
                # 处理执行失败
                await self._handle_execution_error(task_id, result.error_message)
                
        except Exception as e:
            logger.error(f"处理执行结果失败: {e}")
    
    async def _handle_execution_error(self, task_id: str, error_message: str):
        """处理执行错误"""
        try:
            # 更新任务状态为失败
            await self.task_service.update_task_status(task_id, TaskStatus.FAILED)
            await self.task_service.update_task_error(task_id, error_message)
            
            # 发布失败事件
            await self.event_bus.publish(TaskEvent(
                event_type=TaskEventType.TASK_EXECUTION_FAILED,
                task_id=task_id,
                data={'error': error_message}
            ))
            
            logger.error(f"任务 {task_id} 执行失败: {error_message}")
            
        except Exception as e:
            logger.error(f"处理执行错误失败: {e}")
    
    # ==================== 执行信号处理器 ====================
    
    def _on_execution_started(self, task_id: str):
        """执行开始信号处理器"""
        self.execution_started.emit(task_id)
        logger.debug(f"任务 {task_id} 执行开始")
    
    def _on_execution_progress(self, task_id: str, progress: int):
        """执行进度信号处理器"""
        self.execution_progress.emit(task_id, progress)
        logger.debug(f"任务 {task_id} 执行进度: {progress}%")
    
    def _on_execution_completed(self, task_id: str, result: dict):
        """执行完成信号处理器"""
        self.execution_completed.emit(task_id, result)
        logger.debug(f"任务 {task_id} 执行完成")
    
    def _on_execution_paused(self, task_id: str):
        """执行暂停信号处理器"""
        self.execution_paused.emit(task_id)
        logger.debug(f"任务 {task_id} 执行暂停")
    
    def _on_execution_resumed(self, task_id: str):
        """执行恢复信号处理器"""
        self.execution_resumed.emit(task_id)
        logger.debug(f"任务 {task_id} 执行恢复")
    
    def _on_execution_stopped(self, task_id: str):
        """执行停止信号处理器"""
        self.execution_stopped.emit(task_id)
        logger.debug(f"任务 {task_id} 执行停止")
    
    def _on_execution_error(self, task_id: str, error: str):
        """执行错误信号处理器"""
        self.execution_error.emit(task_id, error)
        logger.debug(f"任务 {task_id} 执行错误: {error}")
     
     # ==================== 服务生命周期 ====================
     
     async def start(self) -> bool:
         """启动服务"""
         try:
             logger.info("启动任务应用服务...")
             
             # 启动任务执行器
             if self.task_executor:
                 await self.task_executor.start()
             
             # 启动自动化控制器
             if self.automation_controller:
                 await self.automation_controller.start()
             
             # 启动游戏检测器
             if self.game_detector:
                 await self.game_detector.start()
             
             # 启动队列处理器
             if not self._queue_processor_task or self._queue_processor_task.done():
                 self._queue_processor_task = asyncio.create_task(self._process_execution_queue())
             
             logger.info("任务应用服务启动成功")
             return True
             
         except Exception as e:
             logger.error(f"启动任务应用服务失败: {e}")
             return False
     
     async def stop(self) -> bool:
         """停止服务"""
         try:
             logger.info("停止任务应用服务...")
             
             # 停止队列处理器
             if self._queue_processor_task and not self._queue_processor_task.done():
                 self._queue_processor_task.cancel()
                 try:
                     await self._queue_processor_task
                 except asyncio.CancelledError:
                     pass
             
             # 停止所有运行中的任务
             running_task_ids = list(self._running_tasks.keys())
             for task_id in running_task_ids:
                 await self.stop_task(task_id)
             
             # 停止任务执行器
             if self.task_executor:
                 await self.task_executor.stop()
             
             # 停止自动化控制器
             if self.automation_controller:
                 await self.automation_controller.stop()
             
             # 停止游戏检测器
             if self.game_detector:
                 await self.game_detector.stop()
             
             logger.info("任务应用服务停止成功")
             return True
             
         except Exception as e:
             logger.error(f"停止任务应用服务失败: {e}")
             return False
     
     def get_service_status(self) -> dict:
         """获取服务状态"""
         return {
             'service_name': 'TaskApplicationService',
             'status': 'running' if self._queue_processor_task and not self._queue_processor_task.done() else 'stopped',
             'running_tasks': len(self._running_tasks),
             'queue_size': self._execution_queue.qsize(),
             'components': {
                 'task_executor': self.task_executor is not None,
                 'automation_controller': self.automation_controller is not None,
                 'game_detector': self.game_detector is not None,
                 'database_manager': self.database_manager is not None
             }
         }
     
     async def health_check(self) -> dict:
         """健康检查"""
         health_status = {
             'service': 'healthy',
             'components': {},
             'errors': []
         }
         
         try:
             # 检查任务执行器
             if self.task_executor:
                 try:
                     executor_status = await self.task_executor.health_check()
                     health_status['components']['task_executor'] = executor_status
                 except Exception as e:
                     health_status['components']['task_executor'] = 'unhealthy'
                     health_status['errors'].append(f"TaskExecutor: {str(e)}")
             
             # 检查自动化控制器
             if self.automation_controller:
                 try:
                     controller_status = await self.automation_controller.health_check()
                     health_status['components']['automation_controller'] = controller_status
                 except Exception as e:
                     health_status['components']['automation_controller'] = 'unhealthy'
                     health_status['errors'].append(f"AutomationController: {str(e)}")
             
             # 检查游戏检测器
             if self.game_detector:
                 try:
                     detector_status = await self.game_detector.health_check()
                     health_status['components']['game_detector'] = detector_status
                 except Exception as e:
                     health_status['components']['game_detector'] = 'unhealthy'
                     health_status['errors'].append(f"GameDetector: {str(e)}")
             
             # 检查数据库管理器
             if self.database_manager:
                 try:
                     db_status = await self.database_manager.health_check()
                     health_status['components']['database_manager'] = db_status
                 except Exception as e:
                     health_status['components']['database_manager'] = 'unhealthy'
                     health_status['errors'].append(f"DatabaseManager: {str(e)}")
             
             # 如果有错误，标记服务为不健康
             if health_status['errors']:
                 health_status['service'] = 'unhealthy'
             
         except Exception as e:
             health_status['service'] = 'unhealthy'
             health_status['errors'].append(f"Health check failed: {str(e)}")
         
         return health_status
     
     async def close(self) -> bool:
        """
        关闭服务
        
        Returns:
            bool: 关闭是否成功
        """
        try:
            logger.info("关闭任务应用服务...")
            
            # 停止服务
            await self.stop()
            
            # 关闭任务服务
            if self.task_service:
                await self.task_service.close()
            
            # 关闭事件总线
            if self.event_bus:
                await self.event_bus.close()
            
            self._initialized = False
            logger.info("任务应用服务已关闭")
            return True
            
        except Exception as e:
            logger.error(f"关闭任务应用服务失败: {e}")
            return False
    
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