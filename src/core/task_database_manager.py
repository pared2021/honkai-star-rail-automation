# -*- coding: utf-8 -*-
"""
任务数据库管理器 - 负责任务的数据库操作
"""

import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..database.db_manager import DatabaseManager
from ..entities.task import Task, TaskConfig, TaskPriority, TaskStatus, TaskType
from ..exceptions.task_exceptions import TaskValidationError, TaskStateError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TaskDatabaseManager:
    """任务数据库管理器 - 专门负责任务的数据库操作"""

    def __init__(self, db_manager: DatabaseManager):
        """初始化任务数据库管理器

        Args:
            db_manager: 数据库管理器
        """
        self.db_manager = db_manager
        self._connection_pool = {}
        self._pool_size = 10

    @asynccontextmanager
    async def get_async_connection(self):
        """获取异步数据库连接"""
        conn = await self.db_manager.get_async_connection()
        try:
            yield conn
        finally:
            await conn.close()

    def _get_pooled_connection(self):
        """获取连接池中的连接"""
        thread_id = threading.current_thread().ident
        if thread_id not in self._connection_pool:
            self._connection_pool[thread_id] = self.db_manager.get_connection()
        return self._connection_pool[thread_id]

    def _return_connection(self, thread_id):
        """归还连接到连接池"""
        if thread_id in self._connection_pool:
            conn = self._connection_pool.pop(thread_id)
            conn.close()

    async def create_task(self, user_id: str, config: TaskConfig) -> str:
        """创建新任务

        Args:
            user_id: 用户ID
            config: 任务配置

        Returns:
            str: 任务ID

        Raises:
            TaskValidationError: 任务配置验证失败
        """
        self._validate_task_config(config)
        
        task_id = str(uuid.uuid4())
        current_time = datetime.now()

        async with self.get_async_connection() as conn:
            try:
                await conn.execute("BEGIN TRANSACTION")

                # 插入任务基本信息
                await conn.execute(
                    "INSERT INTO tasks (task_id, user_id, task_name, description, task_type, priority, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        task_id,
                        user_id,
                        config.name,
                        config.description,
                        config.task_type.value,
                        config.priority.value,
                        "pending",
                        current_time,
                        current_time,
                    ),
                )

                # 插入任务配置
                config_dict = config.to_dict()
                # 转换枚举为字符串值以便JSON序列化
                if "task_type" in config_dict:
                    config_dict["task_type"] = config_dict["task_type"].value
                if "priority" in config_dict:
                    config_dict["priority"] = config_dict["priority"].value

                await conn.execute(
                    "INSERT INTO task_configs (config_id, task_id, config_key, config_value) VALUES (?, ?, ?, ?)",
                    (
                        str(uuid.uuid4()),
                        task_id,
                        "full_config",
                        json.dumps(config_dict, ensure_ascii=False),
                    ),
                )

                await conn.commit()
                logger.info(f"任务创建成功: {task_id}")
                return task_id

            except Exception as e:
                await conn.rollback()
                self._handle_database_error(e, "创建任务", task_id)
                raise

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息

        Args:
            task_id: 任务ID

        Returns:
            Optional[Dict[str, Any]]: 任务信息，如果不存在返回None
        """
        async with self.get_async_connection() as conn:
            try:
                # 获取任务基本信息
                cursor = await conn.execute(
                    "SELECT task_id, user_id, task_name, description, task_type, priority, status, created_at, updated_at, last_execution FROM tasks WHERE task_id = ?",
                    (task_id,),
                )
                task_row = await cursor.fetchone()

                if not task_row:
                    return None

                # 获取任务配置
                config_cursor = await conn.execute(
                    "SELECT config_value FROM task_configs WHERE task_id = ? AND config_key = ?",
                    (task_id, "full_config"),
                )
                config_row = await config_cursor.fetchone()
                config_data = {}
                if config_row:
                    try:
                        config_data = json.loads(config_row[0])
                    except json.JSONDecodeError:
                        logger.warning(f"任务 {task_id} 的配置数据格式错误")

                # 构建任务信息
                task_info = {
                    "task_id": task_row[0],
                    "user_id": task_row[1],
                    "name": task_row[2],
                    "description": task_row[3] or "",
                    "task_type": TaskType(task_row[4]),
                    "priority": TaskPriority(task_row[5]),
                    "status": TaskStatus(task_row[6]),
                    "config": config_data,
                    "created_at": datetime.fromisoformat(task_row[7]),
                    "updated_at": datetime.fromisoformat(task_row[8]),
                    "last_executed_at": (
                        datetime.fromisoformat(task_row[9]) if task_row[9] else None
                    ),
                }

                return task_info

            except Exception as e:
                self._handle_database_error(e, "获取任务", task_id)
                raise

    async def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态

        Returns:
            bool: 更新是否成功

        Raises:
            TaskValidationError: 任务不存在
            TaskStateError: 状态转换不合法
        """
        async with self.get_async_connection() as conn:
            try:
                # 获取当前状态
                cursor = await conn.execute(
                    "SELECT status FROM tasks WHERE task_id = ?", (task_id,)
                )
                result = await cursor.fetchone()
                if not result:
                    raise TaskValidationError(f"任务 {task_id} 不存在")

                current_status = result[0]
                self._validate_status_transition(current_status, status.value)

                # 更新状态
                update_time = datetime.now()
                last_execution = (
                    update_time
                    if status in [TaskStatus.RUNNING, TaskStatus.COMPLETED, TaskStatus.FAILED]
                    else None
                )

                await conn.execute(
                    "UPDATE tasks SET status = ?, updated_at = ?, last_execution = ? WHERE task_id = ?",
                    (status.value, update_time, last_execution, task_id),
                )

                logger.info(f"任务 {task_id} 状态更新: {current_status} -> {status.value}")
                return True

            except Exception as e:
                self._handle_database_error(e, "更新任务状态", task_id)
                raise

    async def list_tasks(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """列出任务

        Args:
            user_id: 用户ID过滤
            status: 状态过滤
            task_type: 任务类型过滤
            limit: 限制数量
            offset: 偏移量

        Returns:
            List[Dict[str, Any]]: 任务列表
        """
        async with self.get_async_connection() as conn:
            try:
                # 构建查询条件
                where_conditions = []
                params = []

                if user_id:
                    where_conditions.append("user_id = ?")
                    params.append(user_id)

                if status:
                    where_conditions.append("status = ?")
                    params.append(status)

                if task_type:
                    where_conditions.append("task_type = ?")
                    params.append(task_type)

                where_clause = ""
                if where_conditions:
                    where_clause = "WHERE " + " AND ".join(where_conditions)

                # 执行查询
                query = f"""
                    SELECT task_id, user_id, task_name, description, task_type, priority, status, created_at, updated_at, last_execution
                    FROM tasks
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """
                params.extend([limit, offset])

                cursor = await conn.execute(query, params)
                rows = await cursor.fetchall()

                tasks = []
                for row in rows:
                    task_info = {
                        "task_id": row[0],
                        "user_id": row[1],
                        "name": row[2],
                        "description": row[3] or "",
                        "task_type": TaskType(row[4]),
                        "priority": TaskPriority(row[5]),
                        "status": TaskStatus(row[6]),
                        "created_at": datetime.fromisoformat(row[7]),
                        "updated_at": datetime.fromisoformat(row[8]),
                        "last_executed_at": (
                            datetime.fromisoformat(row[9]) if row[9] else None
                        ),
                    }
                    tasks.append(task_info)

                return tasks

            except Exception as e:
                self._handle_database_error(e, "列出任务")
                raise

    async def delete_task(self, task_id: str) -> bool:
        """删除任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 删除是否成功
        """
        async with self.get_async_connection() as conn:
            try:
                await conn.execute("BEGIN TRANSACTION")

                # 删除任务配置
                await conn.execute(
                    "DELETE FROM task_configs WHERE task_id = ?", (task_id,)
                )

                # 删除任务
                cursor = await conn.execute(
                    "DELETE FROM tasks WHERE task_id = ?", (task_id,)
                )

                if cursor.rowcount == 0:
                    await conn.rollback()
                    raise TaskValidationError(f"任务 {task_id} 不存在")

                await conn.commit()
                logger.info(f"任务删除成功: {task_id}")
                return True

            except Exception as e:
                await conn.rollback()
                self._handle_database_error(e, "删除任务", task_id)
                raise

    def _validate_task_config(self, config: TaskConfig) -> None:
        """验证任务配置

        Args:
            config: 任务配置

        Raises:
            TaskValidationError: 配置验证失败
        """
        if not config.name or not config.name.strip():
            raise TaskValidationError("任务名称不能为空")

        if len(config.name) > 255:
            raise TaskValidationError("任务名称长度不能超过255个字符")

        if config.description and len(config.description) > 1000:
            raise TaskValidationError("任务描述长度不能超过1000个字符")

        if config.timeout_seconds and config.timeout_seconds <= 0:
            raise TaskValidationError("超时时间必须大于0")

        if config.max_retry_count and config.max_retry_count < 0:
            raise TaskValidationError("最大重试次数不能为负数")

        # 验证任务类型和优先级
        if not isinstance(config.task_type, TaskType):
            raise TaskValidationError("无效的任务类型")

        if not isinstance(config.priority, TaskPriority):
            raise TaskValidationError("无效的任务优先级")

        # 验证参数格式
        if config.custom_params and not isinstance(config.custom_params, dict):
            raise TaskValidationError("任务参数必须是字典格式")

    def _validate_status_transition(self, current_status: str, new_status: str) -> None:
        """验证状态转换是否合法

        Args:
            current_status: 当前状态
            new_status: 新状态

        Raises:
            TaskStateError: 状态转换不合法
        """
        # 定义合法的状态转换矩阵
        valid_transitions = {
            "pending": ["running", "cancelled"],
            "running": ["completed", "failed", "paused", "cancelled"],
            "paused": ["running", "cancelled"],
            "completed": [],  # 完成状态不能转换到其他状态
            "failed": ["pending", "running"],  # 失败可以重新开始或重试
            "cancelled": ["pending"],  # 取消可以重新开始
        }

        # 验证状态值的有效性
        all_valid_statuses = set(valid_transitions.keys())
        for transitions in valid_transitions.values():
            all_valid_statuses.update(transitions)

        if current_status not in all_valid_statuses:
            raise TaskStateError(f"未知的当前状态: {current_status}")

        if new_status not in all_valid_statuses:
            raise TaskStateError(f"未知的目标状态: {new_status}")

        # 检查是否为相同状态（允许但记录警告）
        if current_status == new_status:
            logger.warning(f"状态转换为相同状态: {current_status}")
            return

        # 检查转换是否合法
        if new_status not in valid_transitions.get(current_status, []):
            raise TaskStateError(
                f"不能从状态 '{current_status}' 转换到 '{new_status}'。"
                f"允许的转换: {valid_transitions.get(current_status, [])}"
            )

        logger.debug(f"状态转换验证通过: {current_status} -> {new_status}")

    def _handle_database_error(
        self, error: Exception, operation: str, task_id: str = None
    ):
        """统一处理数据库错误"""
        error_msg = str(error).lower()

        if "unique constraint" in error_msg or "duplicate" in error_msg:
            logger.error(f"{operation}失败 - 数据重复: {error}")
            raise TaskValidationError(f"任务ID或名称已存在")
        elif "foreign key" in error_msg:
            logger.error(f"{operation}失败 - 外键约束: {error}")
            raise TaskValidationError(f"关联数据不存在")
        elif "database is locked" in error_msg:
            logger.error(f"{operation}失败 - 数据库锁定: {error}")
            raise RuntimeError(f"数据库繁忙，请稍后重试")
        else:
            logger.error(f"{operation}失败: {error}")
            raise RuntimeError(f"{operation}操作失败")