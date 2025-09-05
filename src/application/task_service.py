# -*- coding: utf-8 -*-
"""
任务业务逻辑服务层
提供任务管理的核心业务逻辑，连接数据访问层和表示层
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import os
import sys
from typing import Any, Callable, Dict, List, Optional, Union
import uuid

import asyncio
from loguru import logger

# 添加父目录到Python路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src.core.enums import TaskPriority, TaskStatus, TaskType
from src.exceptions import (
    DuplicateTaskError,
    ServiceError,
    TaskExecutionError,
    TaskStateError,
    TaskValidationError,
)
from src.models.task_models import Task, TaskConfig
from src.repositories.base_repository import EntityNotFoundError as TaskNotFoundError
from src.repositories.task_repository import TaskRepository
from src.services.base_async_service import BaseAsyncService
from src.services.event_bus import EventBus, TaskEvent, TaskEventType

# 异常类已移至统一的exceptions模块


@dataclass
class TaskSearchCriteria:
    """任务搜索条件"""

    user_id: Optional[str] = None
    status: Optional[Union[TaskStatus, List[TaskStatus]]] = None
    task_type: Optional[Union[TaskType, List[TaskType]]] = None
    priority: Optional[Union[TaskPriority, List[TaskPriority]]] = None
    tags: Optional[List[str]] = None
    name_pattern: Optional[str] = None
    description_pattern: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    updated_after: Optional[datetime] = None
    updated_before: Optional[datetime] = None
    limit: Optional[int] = None
    offset: int = 0
    order_by: str = "created_at"
    order_desc: bool = True


@dataclass
class TaskExecutionResult:
    """任务执行结果"""

    task_id: str
    success: bool
    message: Optional[str] = None
    execution_time: Optional[float] = None
    error_details: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None


class TaskService:
    """任务服务

    提供任务管理的核心业务逻辑，包括：
    - 任务的CRUD操作
    - 任务执行管理
    - 任务状态变更
    - 任务调度
    - 事件发布
    - 应用层服务功能（整合TaskApplicationService）
    """

    def __init__(
        self,
        task_repository: TaskRepository,
        event_bus: EventBus,
        default_user_id: str = "default_user",
    ):
        """
        初始化任务服务

        Args:
            task_repository: 任务数据访问层
            event_bus: 事件总线
            default_user_id: 默认用户ID
        """
        self.task_repository = task_repository
        self.event_bus = event_bus
        self.default_user_id = default_user_id

        # 任务执行器映射
        self._task_executors: Dict[TaskType, Callable] = {}

        # 任务依赖关系
        self._task_dependencies: Dict[str, List[str]] = {}

        # 任务状态监控
        self._status_monitors: Dict[str, Callable] = {}

        # 调度配置
        self._scheduler_active = False
        self._scheduler_task = None
        self._scheduler_interval = 10  # 秒

        # 执行配置
        self._max_concurrent_executions = 5
        self._execution_semaphore = asyncio.Semaphore(self._max_concurrent_executions)
        self._running_tasks: Dict[str, asyncio.Task] = {}

        # 整合TaskApplicationService的功能
        from src.config.database_config import get_database_config
        from src.repositories import TaskDependencyRepository, TaskExecutionRepository

        db_config = get_database_config()
        self.execution_repo = TaskExecutionRepository(db_config.db_path)
        self.dependency_repo = TaskDependencyRepository(db_config.db_path)

        logger.info("任务服务初始化完成")

    async def initialize(self) -> bool:
        """初始化领域服务"""
        try:
            # 初始化数据访问层
            await self.task_repository.initialize()

            # 注册事件监听器
            self._register_event_listeners()

            self._initialized = True
            logger.info("任务领域服务初始化成功")
            return True

        except Exception as e:
            logger.error(f"任务领域服务初始化失败: {e}")
            raise ServiceError(
                f"Failed to initialize task service: {e}",
                "INITIALIZATION_ERROR",
                "TaskService",
                e,
            )

    def _register_event_listeners(self):
        """注册事件监听器"""
        self.event_bus.subscribe(TaskEventType.TASK_CREATED, self._on_task_created)
        self.event_bus.subscribe(TaskEventType.TASK_UPDATED, self._on_task_updated)
        self.event_bus.subscribe(TaskEventType.TASK_DELETED, self._on_task_deleted)
        self.event_bus.subscribe(
            TaskEventType.TASK_STATUS_CHANGED, self._on_task_status_changed
        )
        self.event_bus.subscribe(
            TaskEventType.TASK_EXECUTION_STARTED, self._on_task_execution_started
        )
        self.event_bus.subscribe(
            TaskEventType.TASK_EXECUTION_COMPLETED, self._on_task_execution_completed
        )
        self.event_bus.subscribe(
            TaskEventType.TASK_EXECUTION_FAILED, self._on_task_execution_failed
        )

    # ==================== 私有方法 ====================

    async def _ensure_initialized(self) -> None:
        """确保服务已初始化"""
        if not hasattr(self, "_initialized") or not self._initialized:
            await self.initialize()

    # ==================== 任务CRUD操作 ====================

    async def create_task(
        self, config: TaskConfig, user_id: Optional[str] = None
    ) -> str:
        """
        创建任务 - 领域逻辑

        Args:
            config: 任务配置（已验证）
            user_id: 用户ID，如果为None则使用默认用户

        Returns:
            str: 任务ID

        Raises:
            DuplicateTaskError: 任务已存在
        """
        await self._ensure_initialized()

        try:
            # 使用默认用户ID
            if user_id is None:
                user_id = self.default_user_id

            # 检查任务名称是否重复（领域规则）
            existing_tasks = await self.task_repository.list_tasks(
                user_id=user_id, limit=1
            )

            for task in existing_tasks:
                task_name = (
                    task.config.get("name", "")
                    if isinstance(task.config, dict)
                    else task.config.name
                )
                config_name = (
                    config.name
                    if isinstance(config, TaskConfig)
                    else config.get("name", "")
                )
                if task_name == config_name:
                    raise DuplicateTaskError(
                        f"Task with name '{config_name}' already exists"
                    )

            # 生成任务ID
            task_id = str(uuid.uuid4())

            # 创建任务对象
            # 确保config是字典类型
            config_dict = config.to_dict() if isinstance(config, TaskConfig) else config
            task = Task(
                task_id=task_id,
                user_id=user_id,
                config=config_dict,
                status=TaskStatus.PENDING.value,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            # 保存到数据库
            await self.task_repository.create_task(task)

            # 发布领域事件
            await self.event_bus.publish(
                TaskEvent(
                    event_type=TaskEventType.TASK_CREATED,
                    task_id=task_id,
                    user_id=user_id,
                    data={"config": config.to_dict()},
                )
            )

            logger.info(f"任务创建成功: {config.name} (ID: {task_id})")
            return task_id

        except Exception as e:
            if isinstance(e, DuplicateTaskError):
                raise
            logger.error(f"创建任务失败: {e}")
            raise ServiceError(
                f"Failed to create task: {e}", "CREATE_ERROR", "TaskService", e
            )

    async def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务详情

        Args:
            task_id: 任务ID

        Returns:
            Optional[Task]: 任务对象，如果不存在则返回None
        """
        await self._ensure_initialized()

        try:
            return await self.task_repository.get_task(task_id)
        except Exception as e:
            logger.error(f"获取任务失败: {e}")
            raise ServiceError(
                f"Failed to get task: {e}", "GET_ERROR", "TaskService", e
            )

    async def update_task(self, task: Task) -> bool:
        """
        更新任务 - 领域逻辑

        Args:
            task: 任务对象（已验证）

        Returns:
            bool: 更新是否成功

        Raises:
            TaskNotFoundError: 任务不存在
        """
        await self._ensure_initialized()

        try:
            # 检查任务是否存在（领域规则）
            existing_task = await self.task_repository.get_task(task.task_id)
            if not existing_task:
                raise TaskNotFoundError(task.task_id)

            # 更新时间戳
            task.updated_at = datetime.now()

            # 保存更新
            success = await self.task_repository.update_task(task)

            if success:
                # 发布领域事件
                await self.event_bus.publish(
                    TaskEvent(
                        event_type=TaskEventType.TASK_UPDATED,
                        task_id=task.task_id,
                        user_id=task.user_id,
                        data={"task": task.to_dict()},
                    )
                )

                logger.info(f"任务更新成功: {task.task_id}")

            return success

        except Exception as e:
            if isinstance(e, TaskNotFoundError):
                raise
            logger.error(f"更新任务失败: {e}")
            raise ServiceError(
                f"Failed to update task: {e}", "UPDATE_ERROR", "TaskService", e
            )

    async def delete_task(self, task_id: str) -> bool:
        """
        删除任务 - 领域逻辑

        Args:
            task_id: 任务ID

        Returns:
            bool: 删除是否成功

        Raises:
            TaskNotFoundError: 任务不存在
        """
        await self._ensure_initialized()

        try:
            # 检查任务是否存在（领域规则）
            task = await self.task_repository.get_task(task_id)
            if not task:
                raise TaskNotFoundError(task_id)

            # 如果任务正在运行，先停止（领域规则）
            if task_id in self._running_tasks:
                await self._stop_task_execution(task_id)

            # 删除任务
            success = await self.task_repository.delete_task(task_id)

            if success:
                # 发布领域事件
                await self.event_bus.publish(
                    TaskEvent(
                        event_type=TaskEventType.TASK_DELETED,
                        task_id=task_id,
                        user_id=task.user_id,
                        data={"task": task.to_dict()},
                    )
                )

                logger.info(f"任务删除成功: {task_id}")

            return success

        except Exception as e:
            if isinstance(e, TaskNotFoundError):
                raise
            logger.error(f"删除任务失败: {e}")
            raise ServiceError(
                f"Failed to delete task: {e}", "DELETE_ERROR", "TaskService", e
            )

    # ==================== 任务查询操作 ====================

    async def list_tasks(self, criteria: TaskSearchCriteria) -> List[Task]:
        """
        查询任务列表 - 领域逻辑

        Args:
            criteria: 搜索条件（已验证）

        Returns:
            List[Task]: 任务列表
        """
        await self._ensure_initialized()

        try:
            return await self.task_repository.list_tasks(
                user_id=criteria.user_id,
                status=criteria.status,
                task_type=criteria.task_type,
                priority=criteria.priority,
                tags=criteria.tags,
                limit=criteria.limit,
                offset=criteria.offset,
                order_by=criteria.order_by,
                order_desc=criteria.order_desc,
            )
        except Exception as e:
            logger.error(f"查询任务列表失败: {e}")
            raise ServiceError(
                f"Failed to list tasks: {e}", "LIST_ERROR", "TaskService", e
            )

    async def count_tasks(self, criteria: TaskSearchCriteria) -> int:
        """
        统计任务数量

        Args:
            criteria: 搜索条件

        Returns:
            int: 任务数量
        """
        await self._ensure_initialized()

        try:
            return await self.task_repository.count_tasks(
                user_id=criteria.user_id,
                status=criteria.status,
                task_type=criteria.task_type,
                priority=criteria.priority,
                tags=criteria.tags,
            )
        except Exception as e:
            logger.error(f"统计任务数量失败: {e}")
            raise ServiceError(
                f"Failed to count tasks: {e}", "COUNT_ERROR", "TaskService", e
            )

    async def search_tasks(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Task]:
        """
        搜索任务

        Args:
            query: 搜索关键词
            user_id: 用户ID
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            List[Task]: 匹配的任务列表
        """
        await self._ensure_initialized()

        try:
            return await self.task_repository.search_tasks(
                query=query, user_id=user_id, limit=limit, offset=offset
            )
        except Exception as e:
            logger.error(f"搜索任务失败: {e}")
            raise ServiceError(
                f"Failed to search tasks: {e}", "SEARCH_ERROR", "TaskService", e
            )

    # ==================== 任务状态管理 ====================

    async def update_task_status(
        self, task_id: str, status: TaskStatus, error_message: Optional[str] = None
    ) -> bool:
        """
        更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态
            error_message: 错误信息（可选）

        Returns:
            bool: 更新是否成功

        Raises:
            TaskNotFoundError: 任务不存在
            TaskStateError: 状态转换无效
        """
        await self._ensure_initialized()

        try:
            # 获取当前任务
            task = await self.task_repository.get_task(task_id)
            if not task:
                raise TaskNotFoundError(task_id)

            # 验证状态转换
            self._validate_status_transition(task.status, status)

            # 更新状态
            old_status = task.status
            success = await self.task_repository.update_task_status(
                task_id=task_id, status=status, error_message=error_message
            )

            if success:
                # 发布状态变更事件
                await self.event_bus.publish(
                    TaskEvent(
                        event_type=TaskEventType.TASK_STATUS_CHANGED,
                        task_id=task_id,
                        user_id=task.user_id,
                        data={
                            "old_status": old_status.value,
                            "new_status": status.value,
                            "error_message": error_message,
                        },
                    )
                )

                logger.info(
                    f"任务状态更新成功: {task_id} {old_status.value} -> {status.value}"
                )

            return success

        except Exception as e:
            if isinstance(e, (TaskNotFoundError, TaskStateError)):
                raise
            logger.error(f"更新任务状态失败: {e}")
            raise ServiceError(
                f"Failed to update task status: {e}",
                "STATUS_UPDATE_ERROR",
                "TaskService",
                e,
            )

    def _validate_status_transition(
        self, current_status: TaskStatus, new_status: TaskStatus
    ):
        """
        验证状态转换是否有效

        Args:
            current_status: 当前状态
            new_status: 新状态

        Raises:
            TaskStateError: 状态转换无效
        """
        # 定义有效的状态转换
        valid_transitions = {
            TaskStatus.PENDING: [TaskStatus.RUNNING, TaskStatus.CANCELLED],
            TaskStatus.RUNNING: [
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED,
                TaskStatus.PAUSED,
            ],
            TaskStatus.PAUSED: [TaskStatus.RUNNING, TaskStatus.CANCELLED],
            TaskStatus.COMPLETED: [TaskStatus.PENDING],  # 允许重新运行
            TaskStatus.FAILED: [TaskStatus.PENDING, TaskStatus.CANCELLED],  # 允许重试
            TaskStatus.CANCELLED: [TaskStatus.PENDING],  # 允许重新激活
        }

        if new_status not in valid_transitions.get(current_status, []):
            raise TaskStateError(
                f"Invalid status transition: {current_status.value} -> {new_status.value}"
            )

    # ==================== 任务执行管理 ====================

    async def execute_task(
        self, task_id: str, user_id: Optional[str] = None
    ) -> Union[TaskExecutionResult, str]:
        """
        执行任务

        Args:
            task_id: 任务ID
            user_id: 用户ID（可选，用于权限验证）

        Returns:
            任务执行结果或执行ID

        Raises:
            TaskNotFoundError: 任务不存在
            TaskStateError: 任务状态不允许执行
        """
        await self._ensure_initialized()

        try:
            # 获取任务
            task = await self.task_repository.get_task(task_id)
            if not task:
                raise TaskNotFoundError(task_id)

            # 验证用户权限（如果提供了user_id）
            if user_id and task.user_id != user_id:
                raise TaskExecutionError(f"无权限操作任务: {task_id}")

            # 检查任务状态
            if task.status not in [TaskStatus.PENDING, TaskStatus.FAILED]:
                raise TaskStateError(
                    f"Task {task_id} is not in executable state: {task.status.value}"
                )

            # 检查依赖任务
            await self._check_task_dependencies(task_id)

            # 检查并发限制
            async with self._execution_semaphore:
                # 更新状态为运行中
                await self.update_task_status(task_id, TaskStatus.RUNNING)

                # 创建执行记录
                execution_id = str(uuid.uuid4())
                execution = {
                    "execution_id": execution_id,
                    "task_id": task_id,
                    "status": "running",
                    "started_at": datetime.now(),
                }
                await self.execution_repo.create(execution)

                # 发布执行开始事件
                await self.event_bus.publish(
                    TaskEvent(
                        event_type=TaskEventType.TASK_EXECUTION_STARTED,
                        task_id=task_id,
                        user_id=task.user_id,
                        data={
                            "start_time": datetime.now().isoformat(),
                            "execution_id": execution_id,
                        },
                    )
                )

                # 如果提供了user_id，返回执行ID（应用层模式）
                if user_id:
                    logger.info(f"任务开始执行: {task_id}, 执行ID: {execution_id}")
                    return execution_id

                # 否则执行完整的任务逻辑（领域层模式）
                start_time = datetime.now()
                try:
                    result = await self._execute_task_logic(task)
                    execution_time = (datetime.now() - start_time).total_seconds()

                    # 完成任务执行
                    await self.complete_task_execution(
                        task_id, execution_id, result=result.output_data
                    )

                    result.execution_time = execution_time
                    logger.info(f"任务执行完成: {task_id}, 成功: {result.success}")
                    return result

                except Exception as e:
                    execution_time = (datetime.now() - start_time).total_seconds()

                    # 完成任务执行（失败）
                    await self.complete_task_execution(
                        task_id, execution_id, error_message=str(e)
                    )

                    return TaskExecutionResult(
                        task_id=task_id,
                        success=False,
                        message=str(e),
                        execution_time=execution_time,
                        error_details={
                            "exception": type(e).__name__,
                            "message": str(e),
                        },
                    )

        except Exception as e:
            if isinstance(e, (TaskNotFoundError, TaskStateError)):
                raise
            logger.error(f"执行任务失败: {e}")
            raise TaskExecutionError(f"Failed to execute task: {e}", e)

    async def _execute_task_logic(self, task: Task) -> TaskExecutionResult:
        """
        执行具体的任务逻辑

        Args:
            task: 任务对象

        Returns:
            TaskExecutionResult: 执行结果
        """
        # 获取任务执行器
        executor = self._task_executors.get(task.config.task_type)
        if not executor:
            raise TaskExecutionError(
                f"No executor found for task type: {task.config.task_type.value}"
            )

        # 执行任务
        try:
            result = await executor(task)
            return result
        except Exception as e:
            logger.error(f"任务执行器执行失败: {e}")
            raise TaskExecutionError(f"Task executor failed: {e}", e)

    async def _stop_task_execution(self, task_id: str):
        """
        停止任务执行

        Args:
            task_id: 任务ID
        """
        if task_id in self._running_tasks:
            task = self._running_tasks[task_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            finally:
                del self._running_tasks[task_id]

    # ==================== 任务调度管理 ====================

    async def start_scheduler(self):
        """
        启动任务调度器
        """
        if self._scheduler_active:
            logger.warning("任务调度器已经在运行")
            return

        self._scheduler_active = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("任务调度器已启动")

    async def stop_scheduler(self):
        """
        停止任务调度器
        """
        if not self._scheduler_active:
            return

        self._scheduler_active = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
            finally:
                self._scheduler_task = None

        logger.info("任务调度器已停止")

    async def _scheduler_loop(self):
        """
        调度器主循环
        """
        while self._scheduler_active:
            try:
                await self._process_scheduled_tasks()
                await asyncio.sleep(self._scheduler_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"调度器循环异常: {e}")
                await asyncio.sleep(self._scheduler_interval)

    async def _process_scheduled_tasks(self):
        """
        处理需要调度的任务
        """
        try:
            current_time = datetime.now()
            scheduled_tasks = await self.task_repository.get_tasks_by_schedule(
                current_time
            )

            for task in scheduled_tasks:
                if task.task_id not in self._running_tasks:
                    # 创建执行任务
                    execution_task = asyncio.create_task(
                        self.execute_task(task.task_id)
                    )
                    self._running_tasks[task.task_id] = execution_task

                    # 设置完成回调
                    execution_task.add_done_callback(
                        lambda t, tid=task.task_id: self._running_tasks.pop(tid, None)
                    )

                    logger.info(f"调度执行任务: {task.task_id}")

        except Exception as e:
            logger.error(f"处理调度任务失败: {e}")

    # ==================== 任务执行器管理 ====================

    def register_task_executor(self, task_type: TaskType, executor: Callable):
        """
        注册任务执行器

        Args:
            task_type: 任务类型
            executor: 执行器函数
        """
        self._task_executors[task_type] = executor
        logger.info(f"注册任务执行器: {task_type.value}")

    def unregister_task_executor(self, task_type: TaskType):
        """
        注销任务执行器

        Args:
            task_type: 任务类型
        """
        if task_type in self._task_executors:
            del self._task_executors[task_type]
            logger.info(f"注销任务执行器: {task_type.value}")

    # ==================== 统计和监控 ====================

    async def get_task_statistics(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        获取任务统计信息

        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            Dict[str, Any]: 统计信息
        """
        await self._ensure_initialized()

        try:
            return await self.task_repository.get_task_statistics(
                user_id=user_id, start_date=start_date, end_date=end_date
            )
        except Exception as e:
            logger.error(f"获取任务统计失败: {e}")
            raise ServiceError(
                f"Failed to get task statistics: {e}",
                "STATISTICS_ERROR",
                "TaskService",
                e,
            )

    async def get_running_tasks(self) -> List[str]:
        """
        获取正在运行的任务列表

        Returns:
            List[str]: 正在运行的任务ID列表
        """
        return list(self._running_tasks.keys())

    # ==================== 数据管理 ====================

    async def backup_tasks(
        self, user_id: Optional[str] = None, backup_path: Optional[str] = None
    ) -> str:
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
            return await self.task_repository.backup_tasks(
                user_id=user_id, backup_path=backup_path
            )
        except Exception as e:
            logger.error(f"备份任务失败: {e}")
            raise ServiceError(
                f"Failed to backup tasks: {e}", "BACKUP_ERROR", "TaskService", e
            )

    async def restore_tasks(
        self, backup_path: str, user_id: Optional[str] = None
    ) -> int:
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
            return await self.task_repository.restore_tasks(
                backup_path=backup_path, user_id=user_id
            )
        except Exception as e:
            logger.error(f"恢复任务失败: {e}")
            raise ServiceError(
                f"Failed to restore tasks: {e}", "RESTORE_ERROR", "TaskService", e
            )

    async def cleanup_old_tasks(
        self, days: int = 30, status_filter: Optional[List[TaskStatus]] = None
    ) -> int:
        """
        清理旧任务

        Args:
            days: 保留天数
            status_filter: 状态过滤器

        Returns:
            int: 清理的任务数量
        """
        await self._ensure_initialized()

        try:
            return await self.task_repository.cleanup_old_tasks(
                days=days, status_filter=status_filter
            )
        except Exception as e:
            logger.error(f"清理旧任务失败: {e}")
            raise ServiceError(
                f"Failed to cleanup old tasks: {e}", "CLEANUP_ERROR", "TaskService", e
            )

    # ==================== 事件处理器 ====================

    async def _on_task_created(self, event: TaskEvent):
        """任务创建事件处理器"""
        logger.debug(f"处理任务创建事件: {event.task_id}")

    async def _on_task_updated(self, event: TaskEvent):
        """任务更新事件处理器"""
        logger.debug(f"处理任务更新事件: {event.task_id}")

    async def _on_task_deleted(self, event: TaskEvent):
        """任务删除事件处理器"""
        logger.debug(f"处理任务删除事件: {event.task_id}")

    async def _on_task_status_changed(self, event: TaskEvent):
        """任务状态变更事件处理器"""
        logger.debug(f"处理任务状态变更事件: {event.task_id}")

        # 调用状态监控器
        if event.task_id in self._status_monitors:
            try:
                await self._status_monitors[event.task_id](event)
            except Exception as e:
                logger.error(f"状态监控器执行失败: {e}")

    async def _on_task_execution_started(self, event: TaskEvent):
        """任务执行开始事件处理器"""
        logger.debug(f"处理任务执行开始事件: {event.task_id}")

    async def _on_task_execution_completed(self, event: TaskEvent):
        """任务执行完成事件处理器"""
        logger.debug(f"处理任务执行完成事件: {event.task_id}")

    async def _on_task_execution_failed(self, event: TaskEvent):
        """任务执行失败事件处理器"""
        logger.debug(f"处理任务执行失败事件: {event.task_id}")

    # ==================== 服务生命周期 ====================

    # ==================== 应用层服务方法（整合自TaskApplicationService） ====================

    async def pause_task(self, task_id: str, user_id: str) -> bool:
        """暂停任务

        Args:
            task_id: 任务ID
            user_id: 用户ID

        Returns:
            是否暂停成功
        """
        try:
            task = await self.get_task(task_id)

            # 验证用户权限
            if task.user_id != user_id:
                raise TaskExecutionError(f"无权限操作任务: {task_id}")

            if task.status != TaskStatus.RUNNING:
                raise TaskExecutionError(f"任务状态不允许暂停: {task.status}")

            await self.update_task_status(task_id, TaskStatus.PAUSED)
            logger.info(f"任务暂停成功: {task_id}")
            return True

        except Exception as e:
            logger.error(f"暂停任务失败: {e}")
            raise TaskExecutionError(f"暂停任务失败: {e}")

    async def resume_task(self, task_id: str, user_id: str) -> bool:
        """恢复任务

        Args:
            task_id: 任务ID
            user_id: 用户ID

        Returns:
            是否恢复成功
        """
        try:
            task = await self.get_task(task_id)

            # 验证用户权限
            if task.user_id != user_id:
                raise TaskExecutionError(f"无权限操作任务: {task_id}")

            if task.status != TaskStatus.PAUSED:
                raise TaskExecutionError(f"任务状态不允许恢复: {task.status}")

            await self.update_task_status(task_id, TaskStatus.RUNNING)
            logger.info(f"任务恢复成功: {task_id}")
            return True

        except Exception as e:
            logger.error(f"恢复任务失败: {e}")
            raise TaskExecutionError(f"恢复任务失败: {e}")

    async def cancel_task(self, task_id: str, user_id: str) -> bool:
        """取消任务

        Args:
            task_id: 任务ID
            user_id: 用户ID

        Returns:
            是否取消成功
        """
        try:
            task = await self.get_task(task_id)

            # 验证用户权限
            if task.user_id != user_id:
                raise TaskExecutionError(f"无权限操作任务: {task_id}")

            if task.status in [
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED,
            ]:
                raise TaskExecutionError(f"任务状态不允许取消: {task.status}")

            await self.update_task_status(task_id, TaskStatus.CANCELLED)
            logger.info(f"任务取消成功: {task_id}")
            return True

        except Exception as e:
            logger.error(f"取消任务失败: {e}")
            raise TaskExecutionError(f"取消任务失败: {e}")

    async def complete_task_execution(
        self,
        task_id: str,
        execution_id: str,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """完成任务执行

        Args:
            task_id: 任务ID
            execution_id: 执行ID
            result: 执行结果
            error_message: 错误信息

        Returns:
            是否完成成功
        """
        try:
            # 更新执行记录
            execution_updates = {
                "completed_at": datetime.now(),
                "status": "failed" if error_message else "completed",
            }
            if result:
                execution_updates["result"] = result
            if error_message:
                execution_updates["error_message"] = error_message

            await self.execution_repo.update(execution_id, execution_updates)

            # 更新任务状态
            task_status = TaskStatus.FAILED if error_message else TaskStatus.COMPLETED
            task_updates = {"status": task_status}
            if result:
                task_updates["execution_result"] = result
            if error_message:
                task_updates["error_message"] = error_message

            task = await self.get_task(task_id)
            await self.update_task(task_id, **task_updates)

            # 发布任务执行完成事件
            from src.core.events import TaskExecutionCompletedEvent

            await self.event_bus.publish(
                TaskExecutionCompletedEvent(
                    task_id=task_id,
                    execution_id=execution_id,
                    user_id=task.user_id,
                    success=error_message is None,
                    result=result,
                    error_message=error_message,
                )
            )

            logger.info(f"任务执行完成: {task_id}, 状态: {task_status}")
            return True

        except Exception as e:
            logger.error(f"完成任务失败: {e}")
            raise TaskExecutionError(f"完成任务失败: {e}")

    async def get_scheduled_tasks(self, before: datetime) -> List[Task]:
        """获取计划执行的任务

        Args:
            before: 截止时间

        Returns:
            计划执行的任务列表
        """
        try:
            return await self.task_repository.find_scheduled_tasks(before)
        except Exception as e:
            logger.error(f"获取计划任务失败: {e}")
            raise TaskServiceError(f"获取计划任务失败: {e}")

    async def _check_task_dependencies(self, task_id: str) -> None:
        """检查任务依赖

        Args:
            task_id: 任务ID

        Raises:
            TaskExecutionError: 依赖检查失败
        """
        try:
            dependencies = await self.dependency_repo.get_task_dependencies(task_id)

            for dep in dependencies:
                dep_task = await self.get_task(dep.dependency_task_id)
                if dep_task.status != TaskStatus.COMPLETED:
                    raise TaskExecutionError(
                        f"依赖任务未完成: {dep.dependency_task_id}"
                    )

        except Exception as e:
            logger.error(f"检查任务依赖失败: {e}")
            raise TaskExecutionError(f"检查任务依赖失败: {e}")

    async def close(self) -> bool:
        """
        关闭服务

        Returns:
            bool: 关闭是否成功
        """
        try:
            # 停止调度器
            await self.stop_scheduler()

            # 停止所有正在运行的任务
            for task_id in list(self._running_tasks.keys()):
                await self._stop_task_execution(task_id)

            # 关闭数据访问层
            await self.task_repository.close()

            self._initialized = False
            logger.info("任务服务已关闭")
            return True

        except Exception as e:
            logger.error(f"关闭任务服务失败: {e}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            Dict[str, Any]: 健康状态信息
        """
        try:
            # 检查数据访问层健康状态
            repo_health = await self.task_repository.health_check()

            # 检查服务状态
            service_status = {
                "initialized": self._initialized,
                "scheduler_active": self._scheduler_active,
                "running_tasks_count": len(self._running_tasks),
                "registered_executors": list(self._task_executors.keys()),
            }

            overall_status = (
                "healthy"
                if (self._initialized and repo_health["status"] == "healthy")
                else "unhealthy"
            )

            return {
                "status": overall_status,
                "message": "Task service health check",
                "details": {"service": service_status, "repository": repo_health},
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Health check failed: {e}",
                "details": {"error": str(e), "initialized": self._initialized},
            }

    # ==================== BaseAsyncService抽象方法实现 ====================

    async def _startup(self) -> None:
        """服务启动"""
        await self.initialize()
        logger.info("TaskService启动完成")

    async def _shutdown(self) -> None:
        """服务关闭"""
        await self.close()
        logger.info("TaskService关闭完成")

    async def _health_check(self) -> bool:
        """健康检查"""
        health_result = await self.health_check()
        return health_result["status"] == "healthy"
