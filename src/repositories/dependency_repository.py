"""任务依赖仓储实现

提供任务依赖关系的数据访问功能。
"""

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional, Set
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
)

logger = logging.getLogger(__name__)


class TaskDependency:
    """任务依赖关系数据模型"""

    def __init__(
        self,
        id: str = None,
        task_id: str = None,
        depends_on_task_id: str = None,
        dependency_type: str = "finish_to_start",
        is_active: bool = True,
        created_at: datetime = None,
    ):
        self.id = id or str(uuid4())
        self.task_id = task_id
        self.depends_on_task_id = depends_on_task_id
        self.dependency_type = dependency_type
        self.is_active = is_active
        self.created_at = created_at or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "depends_on_task_id": self.depends_on_task_id,
            "dependency_type": self.dependency_type,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskDependency":
        """从字典创建"""
        return cls(
            id=data["id"],
            task_id=data["task_id"],
            depends_on_task_id=data["depends_on_task_id"],
            dependency_type=data["dependency_type"],
            is_active=data["is_active"],
            created_at=datetime.fromisoformat(data["created_at"]),
        )


class TaskDependencyRepository(
    BaseRepository[TaskDependency, str],
    CrudMixin,
    QueryMixin,
    BatchOperationMixin,
    TimestampMixin,
):
    """任务依赖仓储实现"""

    def __init__(self, db_path: str):
        super().__init__(db_path)
        self.table_name = "task_dependencies"
        CrudMixin.__init__(self)
        QueryMixin.__init__(self)
        BatchOperationMixin.__init__(self)
        TimestampMixin.__init__(self)

    def _row_to_dependency(self, row: Dict[str, Any]) -> TaskDependency:
        """将数据库行转换为TaskDependency对象"""
        try:
            return TaskDependency(
                id=row["id"],
                task_id=row["task_id"],
                depends_on_task_id=row["depends_on_task_id"],
                dependency_type=row["dependency_type"],
                is_active=bool(row["is_active"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
        except Exception as e:
            logger.error(f"Failed to convert row to TaskDependency: {e}, row: {row}")
            raise QueryExecutionError("Failed to parse dependency data", e)

    def _dependency_to_row(self, dependency: TaskDependency) -> Dict[str, Any]:
        """将TaskDependency对象转换为数据库行"""
        return {
            "id": dependency.id,
            "task_id": dependency.task_id,
            "depends_on_task_id": dependency.depends_on_task_id,
            "dependency_type": dependency.dependency_type,
            "is_active": 1 if dependency.is_active else 0,
            "created_at": dependency.created_at.isoformat(),
        }

    # 混入类所需的抽象方法实现
    def _entity_to_row(self, entity: TaskDependency) -> Dict[str, Any]:
        """将实体转换为数据库行"""
        return self._dependency_to_row(entity)

    def _row_to_entity(self, row: Dict[str, Any]) -> TaskDependency:
        """将数据库行转换为实体"""
        return self._row_to_dependency(row)

    def _get_entity_id(self, entity: TaskDependency) -> str:
        """获取实体ID"""
        return entity.id

    def _set_entity_id(self, entity: TaskDependency, entity_id: str) -> None:
        """设置实体ID"""
        entity.id = entity_id

    async def create(self, dependency: TaskDependency) -> TaskDependency:
        """创建任务依赖关系"""
        try:
            if not dependency.id:
                dependency.id = str(uuid4())

            dependency.created_at = datetime.now()

            # 检查是否会形成循环依赖
            if await self._would_create_cycle(
                dependency.task_id, dependency.depends_on_task_id
            ):
                raise QueryExecutionError(
                    "Creating this dependency would create a cycle"
                )

            row_data = self._dependency_to_row(dependency)

            async with self.get_connection() as conn:
                await conn.execute(
                    """
                    INSERT INTO task_dependencies (
                        id, task_id, depends_on_task_id, dependency_type, is_active, created_at
                    ) VALUES (
                        :id, :task_id, :depends_on_task_id, :dependency_type, :is_active, :created_at
                    )
                    """,
                    row_data,
                )
                await conn.commit()

            logger.info(f"Task dependency created: {dependency.id}")
            return dependency

        except Exception as e:
            logger.error(f"Failed to create task dependency: {e}")
            raise QueryExecutionError("Failed to create task dependency", e)

    async def get_by_id(self, dependency_id: str) -> Optional[TaskDependency]:
        """根据ID获取任务依赖关系"""
        return await CrudMixin.get_by_id(self, dependency_id)

    async def update(self, dependency: TaskDependency) -> TaskDependency:
        """更新任务依赖关系"""
        return await CrudMixin.update(self, dependency)

    async def delete(self, dependency_id: str) -> bool:
        """删除任务依赖关系"""
        return await CrudMixin.delete(self, dependency_id)

    async def list_all(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[TaskDependency]:
        """获取所有任务依赖关系列表"""
        try:
            query_builder = QueryBuilder(self.table_name)
            query_builder.where("is_active = ?", 1)
            query_builder.order_by("created_at", "DESC")

            if limit is not None:
                query_builder.limit(limit).offset(offset)

            sql, params = query_builder.build()

            async with self.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()

                dependencies = []
                columns = [description[0] for description in cursor.description]

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    dependencies.append(self._row_to_dependency(row_dict))

                return dependencies

        except Exception as e:
            logger.error(f"Failed to list dependencies: {e}")
            raise QueryExecutionError("Failed to list dependencies", e)

    async def count(self) -> int:
        """获取活跃任务依赖关系总数"""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT COUNT(*) FROM task_dependencies WHERE is_active = 1"
                )
                row = await cursor.fetchone()
                return row[0] if row else 0

        except Exception as e:
            logger.error(f"Failed to count dependencies: {e}")
            raise QueryExecutionError("Failed to count dependencies", e)

    async def find_dependencies_for_task(self, task_id: str) -> List[TaskDependency]:
        """查找指定任务的所有依赖关系（该任务依赖的其他任务）"""
        try:
            query_builder = QueryBuilder(self.table_name)
            query_builder.where("task_id = ? AND is_active = ?", task_id, 1)
            query_builder.order_by("created_at", "ASC")

            sql, params = query_builder.build()

            async with self.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()

                dependencies = []
                columns = [description[0] for description in cursor.description]

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    dependencies.append(self._row_to_dependency(row_dict))

                return dependencies

        except Exception as e:
            logger.error(f"Failed to find dependencies for task {task_id}: {e}")
            raise QueryExecutionError(
                f"Failed to find dependencies for task {task_id}", e
            )

    async def find_dependents_of_task(self, task_id: str) -> List[TaskDependency]:
        """查找依赖于指定任务的所有任务"""
        try:
            query_builder = QueryBuilder(self.table_name)
            query_builder.where("depends_on_task_id = ? AND is_active = ?", task_id, 1)
            query_builder.order_by("created_at", "ASC")

            sql, params = query_builder.build()

            async with self.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()

                dependencies = []
                columns = [description[0] for description in cursor.description]

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    dependencies.append(self._row_to_dependency(row_dict))

                return dependencies

        except Exception as e:
            logger.error(f"Failed to find dependents of task {task_id}: {e}")
            raise QueryExecutionError(f"Failed to find dependents of task {task_id}", e)

    async def get_dependency_chain(self, task_id: str) -> List[str]:
        """获取任务的完整依赖链（递归获取所有依赖）"""
        try:
            visited = set()
            chain = []

            async def _get_dependencies_recursive(current_task_id: str):
                if current_task_id in visited:
                    return  # 避免循环依赖

                visited.add(current_task_id)
                dependencies = await self.find_dependencies_for_task(current_task_id)

                for dep in dependencies:
                    if dep.depends_on_task_id not in chain:
                        chain.append(dep.depends_on_task_id)
                    await _get_dependencies_recursive(dep.depends_on_task_id)

            await _get_dependencies_recursive(task_id)
            return chain

        except Exception as e:
            logger.error(f"Failed to get dependency chain for task {task_id}: {e}")
            raise QueryExecutionError(
                f"Failed to get dependency chain for task {task_id}", e
            )

    async def get_ready_tasks(self, task_ids: List[str]) -> List[str]:
        """获取可以执行的任务（所有依赖都已完成）"""
        try:
            if not task_ids:
                return []

            ready_tasks = []

            for task_id in task_ids:
                dependencies = await self.find_dependencies_for_task(task_id)

                if not dependencies:
                    # 没有依赖的任务可以直接执行
                    ready_tasks.append(task_id)
                else:
                    # 检查所有依赖是否都已完成
                    all_dependencies_completed = True

                    for dep in dependencies:
                        # 这里需要检查依赖任务的状态，但由于我们在仓储层，
                        # 不应该直接访问任务状态，这个逻辑应该在应用服务层实现
                        # 这里只返回依赖信息，让上层决定
                        pass

                    # 暂时将有依赖的任务也加入，让上层服务处理状态检查
                    ready_tasks.append(task_id)

            return ready_tasks

        except Exception as e:
            logger.error(f"Failed to get ready tasks: {e}")
            raise QueryExecutionError("Failed to get ready tasks", e)

    async def _would_create_cycle(self, task_id: str, depends_on_task_id: str) -> bool:
        """检查添加依赖关系是否会创建循环依赖"""
        try:
            # 如果依赖的任务最终依赖于当前任务，则会形成循环
            visited = set()

            async def _has_path_to_task(from_task: str, to_task: str) -> bool:
                if from_task == to_task:
                    return True

                if from_task in visited:
                    return False

                visited.add(from_task)

                dependencies = await self.find_dependencies_for_task(from_task)
                for dep in dependencies:
                    if await _has_path_to_task(dep.depends_on_task_id, to_task):
                        return True

                return False

            return await _has_path_to_task(depends_on_task_id, task_id)

        except Exception as e:
            logger.error(f"Failed to check for cycle: {e}")
            return False  # 如果检查失败，假设不会形成循环

    async def remove_dependencies_for_task(self, task_id: str) -> int:
        """移除指定任务的所有依赖关系"""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    "UPDATE task_dependencies SET is_active = 0 WHERE task_id = ?",
                    (task_id,),
                )

                updated_count = cursor.rowcount
                await conn.commit()

                logger.info(f"Removed {updated_count} dependencies for task {task_id}")
                return updated_count

        except Exception as e:
            logger.error(f"Failed to remove dependencies for task {task_id}: {e}")
            raise QueryExecutionError(
                f"Failed to remove dependencies for task {task_id}", e
            )

    async def remove_dependents_of_task(self, task_id: str) -> int:
        """移除依赖于指定任务的所有关系"""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    "UPDATE task_dependencies SET is_active = 0 WHERE depends_on_task_id = ?",
                    (task_id,),
                )

                updated_count = cursor.rowcount
                await conn.commit()

                logger.info(f"Removed {updated_count} dependents of task {task_id}")
                return updated_count

        except Exception as e:
            logger.error(f"Failed to remove dependents of task {task_id}: {e}")
            raise QueryExecutionError(
                f"Failed to remove dependents of task {task_id}", e
            )

    async def get_dependency_graph(self) -> Dict[str, List[str]]:
        """获取完整的依赖关系图"""
        try:
            dependencies = await self.list_all()
            graph = {}

            for dep in dependencies:
                if dep.task_id not in graph:
                    graph[dep.task_id] = []
                graph[dep.task_id].append(dep.depends_on_task_id)

            return graph

        except Exception as e:
            logger.error(f"Failed to get dependency graph: {e}")
            raise QueryExecutionError("Failed to get dependency graph", e)
