"""通用查询执行器

提供统一的数据库查询执行逻辑，消除repository文件中的重复代码。
"""

from contextlib import asynccontextmanager
from datetime import datetime
import json
import logging
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from uuid import UUID

import aiosqlite

from .base_repository import QueryBuilder, QueryExecutionError

logger = logging.getLogger(__name__)

# 泛型类型变量
T = TypeVar("T")


class QueryExecutor:
    """通用查询执行器
    
    提供统一的数据库查询执行逻辑，包括：
    - 连接管理
    - 错误处理
    - 结果转换
    - 日志记录
    """

    def __init__(self, db_path: str, table_name: str):
        self.db_path = db_path
        self.table_name = table_name

    @asynccontextmanager
    async def get_connection(self):
        """获取数据库连接的上下文管理器"""
        async with aiosqlite.connect(self.db_path) as conn:
            # 启用外键约束
            await conn.execute("PRAGMA foreign_keys = ON")
            yield conn

    async def execute_query(
        self,
        sql: str,
        params: Union[tuple, dict, List[Any]] = None,
        fetch_one: bool = False,
        fetch_all: bool = True,
        commit: bool = False,
        operation_name: str = "query"
    ) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]], int]]:
        """执行SQL查询
        
        Args:
            sql: SQL查询语句
            params: 查询参数
            fetch_one: 是否只获取一行结果
            fetch_all: 是否获取所有结果
            commit: 是否提交事务
            operation_name: 操作名称，用于日志记录
            
        Returns:
            查询结果或受影响的行数
        """
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(sql, params or [])
                
                if commit:
                    await conn.commit()
                    return cursor.rowcount
                
                if fetch_one:
                    row = await cursor.fetchone()
                    if row:
                        columns = [description[0] for description in cursor.description]
                        return dict(zip(columns, row))
                    return None
                
                if fetch_all:
                    rows = await cursor.fetchall()
                    columns = [description[0] for description in cursor.description]
                    return [dict(zip(columns, row)) for row in rows]
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to execute {operation_name}: {e}, SQL: {sql}")
            raise QueryExecutionError(f"Failed to execute {operation_name}", e)

    async def execute_builder_query(
        self,
        query_builder: QueryBuilder,
        row_converter: Callable[[Dict[str, Any]], T],
        operation_name: str = "builder_query"
    ) -> List[T]:
        """执行QueryBuilder构建的查询
        
        Args:
            query_builder: 查询构建器
            row_converter: 行数据转换函数
            operation_name: 操作名称
            
        Returns:
            转换后的实体列表
        """
        try:
            sql, params = query_builder.build()
            rows = await self.execute_query(
                sql, params, fetch_all=True, operation_name=operation_name
            )
            
            if not rows:
                return []
            
            entities = []
            for row in rows:
                try:
                    entity = row_converter(row)
                    entities.append(entity)
                except Exception as e:
                    logger.warning(f"Failed to convert row to entity: {e}, row: {row}")
                    continue
            
            return entities
            
        except Exception as e:
            logger.error(f"Failed to execute builder query: {e}")
            raise QueryExecutionError(f"Failed to execute {operation_name}", e)

    async def create_entity(
        self,
        entity_data: Dict[str, Any],
        operation_name: str = "create"
    ) -> bool:
        """创建实体
        
        Args:
            entity_data: 实体数据字典
            operation_name: 操作名称
            
        Returns:
            是否创建成功
        """
        try:
            # 构建INSERT语句
            fields = list(entity_data.keys())
            placeholders = [f":{field}" for field in fields]
            
            sql = f"""
                INSERT INTO {self.table_name} (
                    {', '.join(fields)}
                ) VALUES (
                    {', '.join(placeholders)}
                )
            """
            
            row_count = await self.execute_query(
                sql, entity_data, commit=True, operation_name=operation_name
            )
            
            success = row_count > 0
            if success:
                logger.info(f"{operation_name.capitalize()} successful for {self.table_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to {operation_name} entity: {e}")
            raise QueryExecutionError(f"Failed to {operation_name} entity", e)

    async def update_entity(
        self,
        entity_id: Union[str, UUID],
        entity_data: Dict[str, Any],
        id_field: str = "id",
        operation_name: str = "update"
    ) -> bool:
        """更新实体
        
        Args:
            entity_id: 实体ID
            entity_data: 实体数据字典
            id_field: ID字段名
            operation_name: 操作名称
            
        Returns:
            是否更新成功
        """
        try:
            # 构建UPDATE语句
            set_clauses = [f"{field} = :{field}" for field in entity_data.keys()]
            
            sql = f"""
                UPDATE {self.table_name} SET
                    {', '.join(set_clauses)}
                WHERE {id_field} = :entity_id
            """
            
            # 添加ID参数
            params = dict(entity_data)
            params['entity_id'] = str(entity_id) if isinstance(entity_id, UUID) else entity_id
            
            row_count = await self.execute_query(
                sql, params, commit=True, operation_name=operation_name
            )
            
            success = row_count > 0
            if success:
                logger.info(f"{operation_name.capitalize()} successful for {self.table_name}: {entity_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to {operation_name} entity {entity_id}: {e}")
            raise QueryExecutionError(f"Failed to {operation_name} entity", e)

    async def delete_entity(
        self,
        entity_id: Union[str, UUID],
        id_field: str = "id",
        operation_name: str = "delete"
    ) -> bool:
        """删除实体
        
        Args:
            entity_id: 实体ID
            id_field: ID字段名
            operation_name: 操作名称
            
        Returns:
            是否删除成功
        """
        try:
            sql = f"DELETE FROM {self.table_name} WHERE {id_field} = ?"
            params = [str(entity_id) if isinstance(entity_id, UUID) else entity_id]
            
            row_count = await self.execute_query(
                sql, params, commit=True, operation_name=operation_name
            )
            
            success = row_count > 0
            if success:
                logger.info(f"{operation_name.capitalize()} successful for {self.table_name}: {entity_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to {operation_name} entity {entity_id}: {e}")
            raise QueryExecutionError(f"Failed to {operation_name} entity", e)

    async def get_entity_by_id(
        self,
        entity_id: Union[str, UUID],
        row_converter: Callable[[Dict[str, Any]], T],
        id_field: str = "id",
        operation_name: str = "get_by_id"
    ) -> Optional[T]:
        """根据ID获取实体
        
        Args:
            entity_id: 实体ID
            row_converter: 行数据转换函数
            id_field: ID字段名
            operation_name: 操作名称
            
        Returns:
            实体对象或None
        """
        try:
            sql = f"SELECT * FROM {self.table_name} WHERE {id_field} = ?"
            params = [str(entity_id) if isinstance(entity_id, UUID) else entity_id]
            
            row = await self.execute_query(
                sql, params, fetch_one=True, operation_name=operation_name
            )
            
            if row:
                return row_converter(row)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to {operation_name} {entity_id}: {e}")
            raise QueryExecutionError(f"Failed to {operation_name}", e)

    async def count_entities(
        self,
        where_condition: str = None,
        params: List[Any] = None,
        operation_name: str = "count"
    ) -> int:
        """统计实体数量
        
        Args:
            where_condition: WHERE条件
            params: 查询参数
            operation_name: 操作名称
            
        Returns:
            实体数量
        """
        try:
            sql = f"SELECT COUNT(*) as count FROM {self.table_name}"
            if where_condition:
                sql += f" WHERE {where_condition}"
            
            row = await self.execute_query(
                sql, params or [], fetch_one=True, operation_name=operation_name
            )
            
            return row['count'] if row else 0
            
        except Exception as e:
            logger.error(f"Failed to {operation_name} entities: {e}")
            raise QueryExecutionError(f"Failed to {operation_name} entities", e)


class DataConverter:
    """数据转换工具类
    
    提供常用的数据转换方法。
    """

    @staticmethod
    def parse_datetime(value: Optional[str]) -> Optional[datetime]:
        """解析日期时间字符串"""
        if value:
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                logger.warning(f"Invalid datetime format: {value}")
        return None

    @staticmethod
    def parse_json(value: Optional[str], default: Any = None) -> Any:
        """解析JSON字符串"""
        if value:
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Invalid JSON format: {value}")
        return default or {}

    @staticmethod
    def format_datetime(value: Optional[datetime]) -> Optional[str]:
        """格式化日期时间"""
        return value.isoformat() if value else None

    @staticmethod
    def format_json(value: Any) -> Optional[str]:
        """格式化为JSON字符串"""
        if value is not None:
            try:
                return json.dumps(value)
            except (TypeError, ValueError):
                logger.warning(f"Failed to serialize to JSON: {value}")
        return None

    @staticmethod
    def parse_uuid(value: Union[str, UUID, None]) -> Optional[UUID]:
        """解析UUID"""
        if value:
            try:
                return UUID(str(value))
            except (ValueError, TypeError):
                logger.warning(f"Invalid UUID format: {value}")
        return None

    @staticmethod
    def format_uuid(value: Optional[UUID]) -> Optional[str]:
        """格式化UUID"""
        return str(value) if value else None