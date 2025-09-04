"""基础仓储接口

定义仓储层的基础接口和通用功能。
"""

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import UUID

import aiosqlite

# 泛型类型变量
T = TypeVar("T")
ID = TypeVar("ID")


class BaseRepository(ABC, Generic[T, ID]):
    """基础仓储接口"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    @asynccontextmanager
    async def get_connection(self):
        """获取数据库连接的上下文管理器"""
        async with aiosqlite.connect(self.db_path) as conn:
            # 启用外键约束
            await conn.execute("PRAGMA foreign_keys = ON")
            yield conn

    @abstractmethod
    async def create(self, entity: T) -> T:
        """创建实体"""
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: ID) -> Optional[T]:
        """根据ID获取实体"""
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """更新实体"""
        pass

    @abstractmethod
    async def delete(self, entity_id: ID) -> bool:
        """删除实体"""
        pass

    @abstractmethod
    async def list_all(self, limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """获取所有实体列表"""
        pass

    @abstractmethod
    async def count(self) -> int:
        """获取实体总数"""
        pass

    async def exists(self, entity_id: ID) -> bool:
        """检查实体是否存在"""
        entity = await self.get_by_id(entity_id)
        return entity is not None

    async def batch_create(self, entities: List[T]) -> List[T]:
        """批量创建实体"""
        result = []
        for entity in entities:
            created_entity = await self.create(entity)
            result.append(created_entity)
        return result

    async def batch_update(self, entities: List[T]) -> List[T]:
        """批量更新实体"""
        result = []
        for entity in entities:
            updated_entity = await self.update(entity)
            result.append(updated_entity)
        return result

    async def batch_delete(self, entity_ids: List[ID]) -> int:
        """批量删除实体

        Returns:
            删除的实体数量
        """
        deleted_count = 0
        for entity_id in entity_ids:
            if await self.delete(entity_id):
                deleted_count += 1
        return deleted_count


class QueryBuilder:
    """SQL查询构建器"""

    def __init__(self, table_name: str):
        self.table_name = table_name
        self._select_fields = ["*"]
        self._where_conditions = []
        self._order_by = []
        self._limit_value = None
        self._offset_value = 0
        self._join_clauses = []
        self._group_by = []
        self._having_conditions = []
        self._params = []

    def select(self, *fields: str) -> "QueryBuilder":
        """设置查询字段"""
        if fields:
            self._select_fields = list(fields)
        return self

    def where(self, condition: str, *params) -> "QueryBuilder":
        """添加WHERE条件"""
        self._where_conditions.append(condition)
        self._params.extend(params)
        return self

    def where_in(self, field: str, values: List[Any]) -> "QueryBuilder":
        """添加WHERE IN条件"""
        if values:
            placeholders = ",".join(["?" for _ in values])
            self._where_conditions.append(f"{field} IN ({placeholders})")
            self._params.extend(values)
        return self

    def where_between(
        self, field: str, start_value: Any, end_value: Any
    ) -> "QueryBuilder":
        """添加WHERE BETWEEN条件"""
        self._where_conditions.append(f"{field} BETWEEN ? AND ?")
        self._params.extend([start_value, end_value])
        return self

    def where_like(self, field: str, pattern: str) -> "QueryBuilder":
        """添加WHERE LIKE条件"""
        self._where_conditions.append(f"{field} LIKE ?")
        self._params.append(pattern)
        return self

    def join(
        self, table: str, on_condition: str, join_type: str = "INNER"
    ) -> "QueryBuilder":
        """添加JOIN子句"""
        self._join_clauses.append(f"{join_type} JOIN {table} ON {on_condition}")
        return self

    def left_join(self, table: str, on_condition: str) -> "QueryBuilder":
        """添加LEFT JOIN子句"""
        return self.join(table, on_condition, "LEFT")

    def order_by(self, field: str, direction: str = "ASC") -> "QueryBuilder":
        """添加ORDER BY子句"""
        self._order_by.append(f"{field} {direction}")
        return self

    def group_by(self, *fields: str) -> "QueryBuilder":
        """添加GROUP BY子句"""
        self._group_by.extend(fields)
        return self

    def having(self, condition: str, *params) -> "QueryBuilder":
        """添加HAVING条件"""
        self._having_conditions.append(condition)
        self._params.extend(params)
        return self

    def limit(self, count: int) -> "QueryBuilder":
        """设置LIMIT"""
        self._limit_value = count
        return self

    def offset(self, count: int) -> "QueryBuilder":
        """设置OFFSET"""
        self._offset_value = count
        return self

    def build(self) -> tuple[str, List[Any]]:
        """构建SQL查询语句

        Returns:
            (sql_query, parameters)
        """
        # 构建SELECT子句
        select_clause = f"SELECT {', '.join(self._select_fields)}"

        # 构建FROM子句
        from_clause = f"FROM {self.table_name}"

        # 构建JOIN子句
        join_clause = " ".join(self._join_clauses) if self._join_clauses else ""

        # 构建WHERE子句
        where_clause = ""
        if self._where_conditions:
            where_clause = f"WHERE {' AND '.join(self._where_conditions)}"

        # 构建GROUP BY子句
        group_by_clause = ""
        if self._group_by:
            group_by_clause = f"GROUP BY {', '.join(self._group_by)}"

        # 构建HAVING子句
        having_clause = ""
        if self._having_conditions:
            having_clause = f"HAVING {' AND '.join(self._having_conditions)}"

        # 构建ORDER BY子句
        order_by_clause = ""
        if self._order_by:
            order_by_clause = f"ORDER BY {', '.join(self._order_by)}"

        # 构建LIMIT和OFFSET子句
        limit_clause = ""
        if self._limit_value is not None:
            limit_clause = f"LIMIT {self._limit_value}"
            if self._offset_value > 0:
                limit_clause += f" OFFSET {self._offset_value}"

        # 组合所有子句
        clauses = [
            select_clause,
            from_clause,
            join_clause,
            where_clause,
            group_by_clause,
            having_clause,
            order_by_clause,
            limit_clause,
        ]

        # 过滤空子句并组合
        sql = " ".join(clause for clause in clauses if clause.strip())

        return sql, self._params

    def build_count(self) -> tuple[str, List[Any]]:
        """构建COUNT查询语句"""
        # 重置SELECT字段为COUNT(*)
        original_select = self._select_fields
        self._select_fields = ["COUNT(*) as count"]

        # 移除ORDER BY、LIMIT、OFFSET（COUNT查询不需要）
        original_order_by = self._order_by
        original_limit = self._limit_value
        original_offset = self._offset_value

        self._order_by = []
        self._limit_value = None
        self._offset_value = 0

        # 构建查询
        sql, params = self.build()

        # 恢复原始设置
        self._select_fields = original_select
        self._order_by = original_order_by
        self._limit_value = original_limit
        self._offset_value = original_offset

        return sql, params


class RepositoryError(Exception):
    """仓储层异常基类"""

    pass


class EntityNotFoundError(RepositoryError):
    """实体未找到异常"""

    def __init__(self, entity_type: str, entity_id: Any):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with ID {entity_id} not found")


class DuplicateEntityError(RepositoryError):
    """重复实体异常"""

    def __init__(self, entity_type: str, field: str, value: Any):
        self.entity_type = entity_type
        self.field = field
        self.value = value
        super().__init__(f"{entity_type} with {field}={value} already exists")


class DatabaseConnectionError(RepositoryError):
    """数据库连接异常"""

    pass


class QueryExecutionError(RepositoryError):
    """查询执行异常"""

    def __init__(self, query: str, error: Exception):
        self.query = query
        self.original_error = error
        super().__init__(f"Query execution failed: {error}")
