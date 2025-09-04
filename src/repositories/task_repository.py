"""任务仓储实现

提供任务相关的数据访问功能。"""

from datetime import datetime
import json
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from src.models.task_models import Task, TaskConfig, TaskPriority, TaskStatus, TaskType
from src.repositories.base_repository import (
    BaseRepository,
    EntityNotFoundError,
    QueryBuilder,
    QueryExecutionError,
)
from src.repositories.repository_mixins import CrudMixin, QueryMixin, BatchOperationMixin, TimestampMixin, JsonFieldMixin

logger = logging.getLogger(__name__)


class TaskRepository(BaseRepository[Task, UUID], CrudMixin, QueryMixin, BatchOperationMixin, TimestampMixin, JsonFieldMixin):
    """任务仓储实现"""

    def __init__(self, db_path: str):
        super().__init__(db_path)
        CrudMixin.__init__(self, db_path, "tasks")
        QueryMixin.__init__(self, self.query_executor)
        self.table_name = "tasks"

    def _entity_to_row(self, entity: Task) -> Dict[str, Any]:
        """将任务实体转换为数据库行数据"""
        return self._task_to_row(entity)

    def _row_to_entity(self, row: Dict[str, Any]) -> Task:
        """将数据库行数据转换为任务实体"""
        return self._row_to_task(row)

    def _get_entity_id(self, entity: Task) -> str:
        """获取任务实体ID"""
        return entity.task_id

    def _set_entity_id(self, entity: Task, entity_id: str) -> None:
        """设置任务实体ID"""
        entity.task_id = entity_id

    async def initialize(self) -> bool:
        """初始化仓储

        默认实现，子类可以重写以提供特定的初始化逻辑
        """
        logger.info(f"TaskRepository initialized with db_path: {self.db_path}")
        return True

    def _row_to_task(self, row: Dict[str, Any]) -> Task:
        """将数据库行转换为Task对象"""
        try:
            # 解析配置JSON
            config_data = json.loads(row["config"]) if row["config"] else {}
            config = TaskConfig.from_dict(config_data)

            # 创建Task对象，适配现有模型结构
            task = Task(
                task_id=row["id"],
                user_id=row["user_id"] or "default_user",
                config=config,
                status=TaskStatus(row["status"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                started_at=(
                    datetime.fromisoformat(row["started_at"])
                    if row["started_at"]
                    else None
                ),
                completed_at=(
                    datetime.fromisoformat(row["completed_at"])
                    if row["completed_at"]
                    else None
                ),
                retry_count=row.get("retry_count", 0),
                last_error=row.get("last_error"),
                execution_result=(
                    json.loads(row["execution_result"])
                    if row.get("execution_result")
                    else None
                ),
            )

            # 设置额外属性（如果数据库中有的话）
            if hasattr(task, "parent_task_id"):
                task.parent_task_id = (
                    UUID(row["parent_task_id"]) if row["parent_task_id"] else None
                )
            if hasattr(task, "scheduled_at"):
                task.scheduled_at = (
                    datetime.fromisoformat(row["scheduled_at"])
                    if row["scheduled_at"]
                    else None
                )

            return task
        except Exception as e:
            logger.error(f"Failed to convert row to Task: {e}, row: {row}")
            raise QueryExecutionError("Failed to parse task data", e)

    def _task_to_row(self, task: Task) -> Dict[str, Any]:
        """将Task对象转换为数据库行"""
        # 处理config字段 - 可能是TaskConfig对象或字典
        if hasattr(task.config, "to_json"):
            config_json = task.config.to_json()
        else:
            config_json = json.dumps(task.config)

        # 获取配置属性
        if hasattr(task.config, "name"):
            name = task.config.name
            description = task.config.description
            task_type = (
                task.config.task_type.value
                if hasattr(task.config.task_type, "value")
                else task.config.task_type
            )
            priority = (
                task.config.priority.value
                if hasattr(task.config.priority, "value")
                else task.config.priority
            )
        else:
            name = task.config.get("name", "")
            description = task.config.get("description", "")
            task_type = task.config.get("task_type", "")
            priority = task.config.get("priority", 2)

        row_data = {
            "id": task.task_id,
            "name": name,
            "description": description,
            "task_type": task_type,
            "status": (
                task.status.value if hasattr(task.status, "value") else task.status
            ),
            "priority": priority,
            "config": config_json,
            "user_id": task.user_id,
            "parent_task_id": getattr(task, "parent_task_id", None),
            "scheduled_at": (
                getattr(task, "scheduled_at", None).isoformat()
                if getattr(task, "scheduled_at", None)
                else None
            ),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": (
                task.completed_at.isoformat() if task.completed_at else None
            ),
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "retry_count": task.retry_count,
            "last_error": task.last_error,
            "execution_result": (
                json.dumps(task.execution_result) if task.execution_result else None
            ),
        }
        return row_data

    async def create(self, task: Task) -> Task:
        """创建任务"""
        return await CrudMixin.create(self, task)

    async def get_by_id(self, task_id: str) -> Optional[Task]:
        """根据ID获取任务"""
        return await CrudMixin.get_by_id(self, task_id)

    async def update(self, task: Task) -> Task:
        """更新任务"""
        return await CrudMixin.update(self, task)

    async def delete(self, task_id: str) -> bool:
        """删除任务"""
        return await CrudMixin.delete(self, task_id)

    async def list_all(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[Task]:
        """获取所有任务列表"""
        try:
            query_builder = QueryBuilder(self.table_name)
            query_builder.order_by("created_at", "DESC")

            if limit is not None:
                query_builder.limit(limit).offset(offset)

            sql, params = query_builder.build()

            async with self.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()

                tasks = []
                columns = [description[0] for description in cursor.description]

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    tasks.append(self._row_to_task(row_dict))

                return tasks

        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            raise QueryExecutionError("Failed to list tasks", e)

    async def count(self) -> int:
        """获取任务总数"""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute("SELECT COUNT(*) FROM tasks")
                row = await cursor.fetchone()
                return row[0] if row else 0

        except Exception as e:
            logger.error(f"Failed to count tasks: {e}")
            raise QueryExecutionError("Failed to count tasks", e)

    async def find_by_status(
        self, status: TaskStatus, limit: Optional[int] = None
    ) -> List[Task]:
        """根据状态查找任务"""
        try:
            query_builder = QueryBuilder(self.table_name)
            query_builder.where("status = ?", status.value)
            query_builder.order_by("created_at", "DESC")

            if limit is not None:
                query_builder.limit(limit)

            sql, params = query_builder.build()

            async with self.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()

                tasks = []
                columns = [description[0] for description in cursor.description]

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    tasks.append(self._row_to_task(row_dict))

                return tasks

        except Exception as e:
            logger.error(f"Failed to find tasks by status {status}: {e}")
            raise QueryExecutionError(f"Failed to find tasks by status {status}", e)

    async def find_by_type(
        self, task_type: TaskType, limit: Optional[int] = None
    ) -> List[Task]:
        """根据类型查找任务"""
        try:
            query_builder = QueryBuilder(self.table_name)
            query_builder.where("task_type = ?", task_type.value)
            query_builder.order_by("created_at", "DESC")

            if limit is not None:
                query_builder.limit(limit)

            sql, params = query_builder.build()

            async with self.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()

                tasks = []
                columns = [description[0] for description in cursor.description]

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    tasks.append(self._row_to_task(row_dict))

                return tasks

        except Exception as e:
            logger.error(f"Failed to find tasks by type {task_type}: {e}")
            raise QueryExecutionError(f"Failed to find tasks by type {task_type}", e)

    async def find_by_user(
        self, user_id: str, limit: Optional[int] = None
    ) -> List[Task]:
        """根据用户ID查找任务"""
        try:
            query_builder = QueryBuilder(self.table_name)
            query_builder.where("user_id = ?", user_id)
            query_builder.order_by("created_at", "DESC")

            if limit is not None:
                query_builder.limit(limit)

            sql, params = query_builder.build()

            async with self.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()

                tasks = []
                columns = [description[0] for description in cursor.description]

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    tasks.append(self._row_to_task(row_dict))

                return tasks

        except Exception as e:
            logger.error(f"Failed to find tasks by user {user_id}: {e}")
            raise QueryExecutionError(f"Failed to find tasks by user {user_id}", e)

    async def find_scheduled_tasks(self, before_time: datetime = None) -> List[Task]:
        """查找已调度的任务"""
        try:
            query_builder = QueryBuilder(self.table_name)
            query_builder.where("status = ?", TaskStatus.PENDING.value)
            query_builder.where("scheduled_at IS NOT NULL")

            if before_time:
                query_builder.where("scheduled_at <= ?", before_time.isoformat())

            query_builder.order_by("scheduled_at", "ASC")

            sql, params = query_builder.build()

            async with self.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()

                tasks = []
                columns = [description[0] for description in cursor.description]

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    tasks.append(self._row_to_task(row_dict))

                return tasks

        except Exception as e:
            logger.error(f"Failed to find scheduled tasks: {e}")
            raise QueryExecutionError("Failed to find scheduled tasks", e)

    async def find_subtasks(self, parent_task_id: str) -> List[Task]:
        """查找子任务"""
        try:
            query_builder = QueryBuilder(self.table_name)
            query_builder.where("parent_task_id = ?", parent_task_id)
            query_builder.order_by("created_at", "ASC")

            sql, params = query_builder.build()

            async with self.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()

                tasks = []
                columns = [description[0] for description in cursor.description]

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    tasks.append(self._row_to_task(row_dict))

                return tasks

        except Exception as e:
            logger.error(f"Failed to find subtasks for {parent_task_id}: {e}")
            raise QueryExecutionError(
                f"Failed to find subtasks for {parent_task_id}", e
            )

    async def update_status(self, task_id: str, status: TaskStatus) -> bool:
        """更新任务状态"""
        try:
            now = datetime.now()

            # 根据状态设置相应的时间字段
            update_fields = {"status": status.value, "updated_at": now.isoformat()}

            if status == TaskStatus.RUNNING:
                update_fields["started_at"] = now.isoformat()
            elif status in [
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED,
            ]:
                update_fields["completed_at"] = now.isoformat()

            # 构建SET子句
            set_clause = ", ".join([f"{key} = ?" for key in update_fields.keys()])
            values = list(update_fields.values()) + [task_id]

            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    f"UPDATE tasks SET {set_clause} WHERE id = ?", values
                )

                updated = cursor.rowcount > 0
                await conn.commit()

                if updated:
                    logger.info(f"Task {task_id} status updated to {status}")

                return updated

        except Exception as e:
            logger.error(f"Failed to update task status {task_id}: {e}")
            raise QueryExecutionError(f"Failed to update task status {task_id}", e)

    async def list_tasks(
        self,
        user_id: str = None,
        status: TaskStatus = None,
        task_type: TaskType = None,
        priority: TaskPriority = None,
        tags: List[str] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> List[Task]:
        """列出任务"""
        try:
            query_builder = QueryBuilder(self.table_name)

            # 用户过滤
            if user_id:
                query_builder.where("user_id = ?", user_id)

            # 状态过滤
            if status:
                query_builder.where("status = ?", status.value)

            # 类型过滤
            if task_type:
                query_builder.where("task_type = ?", task_type.value)

            # 优先级过滤
            if priority:
                query_builder.where("priority = ?", priority.value)

            # 标签过滤（简化实现，实际可能需要JSON查询）
            if tags:
                for tag in tags:
                    query_builder.where("config LIKE ?", f"%{tag}%")

            # 排序
            order_direction = "DESC" if order_desc else "ASC"
            query_builder.order_by(order_by, order_direction)

            query_builder.limit(limit).offset(offset)

            sql, params = query_builder.build()

            async with self.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()

                tasks = []
                columns = [description[0] for description in cursor.description]

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    tasks.append(self._row_to_task(row_dict))

                return tasks

        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            raise QueryExecutionError("Failed to list tasks", e)

    async def search_tasks(
        self,
        query: str = None,
        status: TaskStatus = None,
        task_type: TaskType = None,
        priority: TaskPriority = None,
        user_id: str = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Task]:
        """搜索任务"""
        try:
            query_builder = QueryBuilder(self.table_name)

            # 文本搜索
            if query:
                query_builder.where(
                    "(name LIKE ? OR description LIKE ?)", f"%{query}%", f"%{query}%"
                )

            # 状态过滤
            if status:
                query_builder.where("status = ?", status.value)

            # 类型过滤
            if task_type:
                query_builder.where("task_type = ?", task_type.value)

            # 优先级过滤
            if priority:
                query_builder.where("priority = ?", priority.value)

            # 用户过滤
            if user_id:
                query_builder.where("user_id = ?", user_id)

            query_builder.order_by("created_at", "DESC")
            query_builder.limit(limit).offset(offset)

            sql, params = query_builder.build()

            async with self.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()

                tasks = []
                columns = [description[0] for description in cursor.description]

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    tasks.append(self._row_to_task(row_dict))

                return tasks

        except Exception as e:
            logger.error(f"Failed to search tasks: {e}")
            raise QueryExecutionError("Failed to search tasks", e)

    # ==================== 方法别名（兼容TaskService调用） ====================

    async def create_task(self, task: Task) -> Task:
        """创建任务（别名）"""
        return await self.create(task)

    async def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务（别名）"""
        return await self.get_by_id(task_id)

    async def update_task(self, task: Task) -> bool:
        """更新任务（别名）"""
        try:
            await self.update(task)
            return True
        except Exception:
            return False

    async def delete_task(self, task_id: str) -> bool:
        """删除任务（别名）"""
        return await self.delete(task_id)
