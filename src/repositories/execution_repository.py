"""任务执行仓储实现

提供任务执行相关的数据访问功能。
"""

from datetime import datetime
import json
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .base_repository import (
    BaseRepository,
    EntityNotFoundError,
    QueryBuilder,
    QueryExecutionError,
)
from .repository_mixins import (
    CrudMixin,
    QueryMixin,
    BatchOperationMixin,
    TimestampMixin,
    JsonFieldMixin,
)

logger = logging.getLogger(__name__)


class TaskExecution:
    """任务执行记录数据模型"""

    def __init__(
        self,
        id: str = None,
        task_id: str = None,
        status: str = "pending",
        started_at: datetime = None,
        completed_at: datetime = None,
        error_message: str = None,
        retry_count: int = 0,
        execution_context: Dict[str, Any] = None,
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        self.id = id or str(uuid4())
        self.task_id = task_id
        self.status = status
        self.started_at = started_at
        self.completed_at = completed_at
        self.error_message = error_message
        self.retry_count = retry_count
        self.execution_context = execution_context or {}
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "execution_context": self.execution_context,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskExecution":
        """从字典创建"""
        return cls(
            id=data["id"],
            task_id=data["task_id"],
            status=data["status"],
            started_at=(
                datetime.fromisoformat(data["started_at"])
                if data["started_at"]
                else None
            ),
            completed_at=(
                datetime.fromisoformat(data["completed_at"])
                if data["completed_at"]
                else None
            ),
            error_message=data["error_message"],
            retry_count=data["retry_count"],
            execution_context=data["execution_context"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


class ExecutionAction:
    """执行动作数据模型"""

    def __init__(
        self,
        id: str = None,
        execution_id: str = None,
        action_type: str = None,
        action_data: Dict[str, Any] = None,
        status: str = "pending",
        started_at: datetime = None,
        completed_at: datetime = None,
        error_message: str = None,
        result_data: Dict[str, Any] = None,
        created_at: datetime = None,
    ):
        self.id = id or str(uuid4())
        self.execution_id = execution_id
        self.action_type = action_type
        self.action_data = action_data or {}
        self.status = status
        self.started_at = started_at
        self.completed_at = completed_at
        self.error_message = error_message
        self.result_data = result_data or {}
        self.created_at = created_at or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "execution_id": self.execution_id,
            "action_type": self.action_type,
            "action_data": self.action_data,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "error_message": self.error_message,
            "result_data": self.result_data,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionAction":
        """从字典创建"""
        return cls(
            id=data["id"],
            execution_id=data["execution_id"],
            action_type=data["action_type"],
            action_data=data["action_data"],
            status=data["status"],
            started_at=(
                datetime.fromisoformat(data["started_at"])
                if data["started_at"]
                else None
            ),
            completed_at=(
                datetime.fromisoformat(data["completed_at"])
                if data["completed_at"]
                else None
            ),
            error_message=data["error_message"],
            result_data=data["result_data"],
            created_at=datetime.fromisoformat(data["created_at"]),
        )


class TaskExecutionRepository(
    BaseRepository[TaskExecution, str],
    CrudMixin,
    QueryMixin,
    BatchOperationMixin,
    TimestampMixin,
    JsonFieldMixin,
):
    """任务执行仓储实现"""

    def __init__(self, db_path: str):
        super().__init__(db_path)
        self.table_name = "task_executions"
        CrudMixin.__init__(self)
        QueryMixin.__init__(self)
        BatchOperationMixin.__init__(self)
        TimestampMixin.__init__(self)
        JsonFieldMixin.__init__(self)

    def _row_to_execution(self, row: Dict[str, Any]) -> TaskExecution:
        """将数据库行转换为TaskExecution对象"""
        try:
            execution_context = (
                json.loads(row["execution_context"]) if row["execution_context"] else {}
            )

            return TaskExecution(
                id=row["id"],
                task_id=row["task_id"],
                status=row["status"],
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
                error_message=row["error_message"],
                retry_count=row["retry_count"],
                execution_context=execution_context,
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
        except Exception as e:
            logger.error(f"Failed to convert row to TaskExecution: {e}, row: {row}")
            raise QueryExecutionError("Failed to parse execution data", e)

    def _execution_to_row(self, execution: TaskExecution) -> Dict[str, Any]:
        """将TaskExecution对象转换为数据库行"""
        return {
            "id": execution.id,
            "task_id": execution.task_id,
            "status": execution.status,
            "started_at": (
                execution.started_at.isoformat() if execution.started_at else None
            ),
            "completed_at": (
                execution.completed_at.isoformat() if execution.completed_at else None
            ),
            "error_message": execution.error_message,
            "retry_count": execution.retry_count,
            "execution_context": json.dumps(execution.execution_context),
            "created_at": execution.created_at.isoformat(),
            "updated_at": execution.updated_at.isoformat(),
        }

    # 混入类所需的抽象方法实现
    def _entity_to_row(self, entity: TaskExecution) -> Dict[str, Any]:
        """将实体转换为数据库行"""
        return self._execution_to_row(entity)

    def _row_to_entity(self, row: Dict[str, Any]) -> TaskExecution:
        """将数据库行转换为实体"""
        return self._row_to_execution(row)

    def _get_entity_id(self, entity: TaskExecution) -> str:
        """获取实体ID"""
        return entity.id

    def _set_entity_id(self, entity: TaskExecution, entity_id: str) -> None:
        """设置实体ID"""
        entity.id = entity_id

    async def create(self, execution: TaskExecution) -> TaskExecution:
        """创建任务执行记录"""
        return await CrudMixin.create(self, execution)

    async def get_by_id(self, execution_id: str) -> Optional[TaskExecution]:
        """根据ID获取任务执行记录"""
        return await CrudMixin.get_by_id(self, execution_id)

    async def update(self, execution: TaskExecution) -> TaskExecution:
        """更新任务执行记录"""
        return await CrudMixin.update(self, execution)

    async def delete(self, execution_id: str) -> bool:
        """删除任务执行记录"""
        return await CrudMixin.delete(self, execution_id)

    async def list_all(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[TaskExecution]:
        """获取所有任务执行记录列表"""
        try:
            query_builder = QueryBuilder(self.table_name)
            query_builder.order_by("created_at", "DESC")

            if limit is not None:
                query_builder.limit(limit).offset(offset)

            sql, params = query_builder.build()

            async with self.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()

                executions = []
                columns = [description[0] for description in cursor.description]

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    executions.append(self._row_to_execution(row_dict))

                return executions

        except Exception as e:
            logger.error(f"Failed to list executions: {e}")
            raise QueryExecutionError("Failed to list executions", e)

    async def count(self) -> int:
        """获取任务执行记录总数"""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute("SELECT COUNT(*) FROM task_executions")
                row = await cursor.fetchone()
                return row[0] if row else 0

        except Exception as e:
            logger.error(f"Failed to count executions: {e}")
            raise QueryExecutionError("Failed to count executions", e)

    async def find_by_task_id(
        self, task_id: str, limit: Optional[int] = None
    ) -> List[TaskExecution]:
        """根据任务ID查找执行记录"""
        try:
            query_builder = QueryBuilder(self.table_name)
            query_builder.where("task_id = ?", task_id)
            query_builder.order_by("created_at", "DESC")

            if limit is not None:
                query_builder.limit(limit)

            sql, params = query_builder.build()

            async with self.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()

                executions = []
                columns = [description[0] for description in cursor.description]

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    executions.append(self._row_to_execution(row_dict))

                return executions

        except Exception as e:
            logger.error(f"Failed to find executions by task ID {task_id}: {e}")
            raise QueryExecutionError(
                f"Failed to find executions by task ID {task_id}", e
            )

    async def find_by_status(
        self, status: str, limit: Optional[int] = None
    ) -> List[TaskExecution]:
        """根据状态查找执行记录"""
        try:
            query_builder = QueryBuilder(self.table_name)
            query_builder.where("status = ?", status)
            query_builder.order_by("created_at", "DESC")

            if limit is not None:
                query_builder.limit(limit)

            sql, params = query_builder.build()

            async with self.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()

                executions = []
                columns = [description[0] for description in cursor.description]

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    executions.append(self._row_to_execution(row_dict))

                return executions

        except Exception as e:
            logger.error(f"Failed to find executions by status {status}: {e}")
            raise QueryExecutionError(
                f"Failed to find executions by status {status}", e
            )


class ExecutionActionRepository(BaseRepository[ExecutionAction, str]):
    """执行动作仓储实现"""

    def __init__(self, db_path: str):
        super().__init__(db_path)
        self.table_name = "execution_actions"

    def _row_to_action(self, row: Dict[str, Any]) -> ExecutionAction:
        """将数据库行转换为ExecutionAction对象"""
        try:
            action_data = json.loads(row["action_data"]) if row["action_data"] else {}
            result_data = json.loads(row["result_data"]) if row["result_data"] else {}

            return ExecutionAction(
                id=row["id"],
                execution_id=row["execution_id"],
                action_type=row["action_type"],
                action_data=action_data,
                status=row["status"],
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
                error_message=row["error_message"],
                result_data=result_data,
                created_at=datetime.fromisoformat(row["created_at"]),
            )
        except Exception as e:
            logger.error(f"Failed to convert row to ExecutionAction: {e}, row: {row}")
            raise QueryExecutionError("Failed to parse action data", e)

    def _action_to_row(self, action: ExecutionAction) -> Dict[str, Any]:
        """将ExecutionAction对象转换为数据库行"""
        return {
            "id": action.id,
            "execution_id": action.execution_id,
            "action_type": action.action_type,
            "action_data": json.dumps(action.action_data),
            "status": action.status,
            "started_at": action.started_at.isoformat() if action.started_at else None,
            "completed_at": (
                action.completed_at.isoformat() if action.completed_at else None
            ),
            "error_message": action.error_message,
            "result_data": json.dumps(action.result_data),
            "created_at": action.created_at.isoformat(),
        }

    async def create(self, action: ExecutionAction) -> ExecutionAction:
        """创建执行动作"""
        try:
            if not action.id:
                action.id = str(uuid4())

            action.created_at = datetime.now()
            row_data = self._action_to_row(action)

            async with self.get_connection() as conn:
                await conn.execute(
                    """
                    INSERT INTO execution_actions (
                        id, execution_id, action_type, action_data, status,
                        started_at, completed_at, error_message, result_data, created_at
                    ) VALUES (
                        :id, :execution_id, :action_type, :action_data, :status,
                        :started_at, :completed_at, :error_message, :result_data, :created_at
                    )
                    """,
                    row_data,
                )
                await conn.commit()

            logger.info(f"Execution action created: {action.id}")
            return action

        except Exception as e:
            logger.error(f"Failed to create execution action: {e}")
            raise QueryExecutionError("Failed to create execution action", e)

    async def get_by_id(self, action_id: str) -> Optional[ExecutionAction]:
        """根据ID获取执行动作"""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT * FROM execution_actions WHERE id = ?", (action_id,)
                )
                row = await cursor.fetchone()

                if row:
                    columns = [description[0] for description in cursor.description]
                    row_dict = dict(zip(columns, row))
                    return self._row_to_action(row_dict)

                return None

        except Exception as e:
            logger.error(f"Failed to get action by ID {action_id}: {e}")
            raise QueryExecutionError(f"Failed to get action by ID {action_id}", e)

    async def update(self, action: ExecutionAction) -> ExecutionAction:
        """更新执行动作"""
        try:
            row_data = self._action_to_row(action)

            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    """
                    UPDATE execution_actions SET
                        execution_id = :execution_id,
                        action_type = :action_type,
                        action_data = :action_data,
                        status = :status,
                        started_at = :started_at,
                        completed_at = :completed_at,
                        error_message = :error_message,
                        result_data = :result_data
                    WHERE id = :id
                    """,
                    row_data,
                )

                if cursor.rowcount == 0:
                    raise EntityNotFoundError("ExecutionAction", action.id)

                await conn.commit()

            logger.info(f"Execution action updated: {action.id}")
            return action

        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to update action {action.id}: {e}")
            raise QueryExecutionError(f"Failed to update action {action.id}", e)

    async def delete(self, action_id: str) -> bool:
        """删除执行动作"""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    "DELETE FROM execution_actions WHERE id = ?", (action_id,)
                )

                deleted = cursor.rowcount > 0
                await conn.commit()

                if deleted:
                    logger.info(f"Execution action deleted: {action_id}")

                return deleted

        except Exception as e:
            logger.error(f"Failed to delete action {action_id}: {e}")
            raise QueryExecutionError(f"Failed to delete action {action_id}", e)

    async def list_all(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[ExecutionAction]:
        """获取所有执行动作列表"""
        try:
            query_builder = QueryBuilder(self.table_name)
            query_builder.order_by("created_at", "ASC")

            if limit is not None:
                query_builder.limit(limit).offset(offset)

            sql, params = query_builder.build()

            async with self.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()

                actions = []
                columns = [description[0] for description in cursor.description]

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    actions.append(self._row_to_action(row_dict))

                return actions

        except Exception as e:
            logger.error(f"Failed to list actions: {e}")
            raise QueryExecutionError("Failed to list actions", e)

    async def count(self) -> int:
        """获取执行动作总数"""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute("SELECT COUNT(*) FROM execution_actions")
                row = await cursor.fetchone()
                return row[0] if row else 0

        except Exception as e:
            logger.error(f"Failed to count actions: {e}")
            raise QueryExecutionError("Failed to count actions", e)

    async def find_by_execution_id(self, execution_id: str) -> List[ExecutionAction]:
        """根据执行ID查找动作"""
        try:
            query_builder = QueryBuilder(self.table_name)
            query_builder.where("execution_id = ?", execution_id)
            query_builder.order_by("created_at", "ASC")

            sql, params = query_builder.build()

            async with self.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()

                actions = []
                columns = [description[0] for description in cursor.description]

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    actions.append(self._row_to_action(row_dict))

                return actions

        except Exception as e:
            logger.error(f"Failed to find actions by execution ID {execution_id}: {e}")
            raise QueryExecutionError(
                f"Failed to find actions by execution ID {execution_id}", e
            )
