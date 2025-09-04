"""仓储混入类

提供通用的仓储操作实现，减少重复代码。
"""

from abc import ABC, abstractmethod
from datetime import datetime
import logging
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from uuid import UUID, uuid4

from .base_repository import BaseRepository, EntityNotFoundError
from .query_executor import QueryExecutor, DataConverter

logger = logging.getLogger(__name__)

# 泛型类型变量
T = TypeVar("T")
ID = TypeVar("ID")


class CrudMixin(ABC):
    """CRUD操作混入类
    
    提供标准的创建、读取、更新、删除操作实现。
    """

    def __init__(self, db_path: str, table_name: str):
        self.query_executor = QueryExecutor(db_path, table_name)
        self.table_name = table_name

    @abstractmethod
    def _entity_to_row(self, entity: T) -> Dict[str, Any]:
        """将实体转换为数据库行数据"""
        pass

    @abstractmethod
    def _row_to_entity(self, row: Dict[str, Any]) -> T:
        """将数据库行数据转换为实体"""
        pass

    @abstractmethod
    def _get_entity_id(self, entity: T) -> ID:
        """获取实体ID"""
        pass

    @abstractmethod
    def _set_entity_id(self, entity: T, entity_id: ID) -> None:
        """设置实体ID"""
        pass

    def _get_id_field_name(self) -> str:
        """获取ID字段名，默认为'id'"""
        return "id"

    def _prepare_entity_for_create(self, entity: T) -> T:
        """为创建操作准备实体
        
        设置ID、创建时间等默认值。
        """
        # 确保实体有ID
        if not self._get_entity_id(entity):
            if hasattr(entity, 'id') and isinstance(getattr(entity, 'id', None), type(None)):
                self._set_entity_id(entity, str(uuid4()))

        # 设置时间戳
        now = datetime.now()
        if hasattr(entity, 'created_at'):
            entity.created_at = now
        if hasattr(entity, 'updated_at'):
            entity.updated_at = now

        return entity

    def _prepare_entity_for_update(self, entity: T) -> T:
        """为更新操作准备实体
        
        更新修改时间等。
        """
        # 更新时间戳
        if hasattr(entity, 'updated_at'):
            entity.updated_at = datetime.now()

        return entity

    async def create(self, entity: T) -> T:
        """创建实体"""
        entity = self._prepare_entity_for_create(entity)
        row_data = self._entity_to_row(entity)
        
        success = await self.query_executor.create_entity(
            row_data, f"create_{self.table_name}"
        )
        
        if not success:
            raise Exception(f"Failed to create {self.table_name}")
        
        return entity

    async def get_by_id(self, entity_id: ID) -> Optional[T]:
        """根据ID获取实体"""
        return await self.query_executor.get_entity_by_id(
            entity_id,
            self._row_to_entity,
            self._get_id_field_name(),
            f"get_{self.table_name}_by_id"
        )

    async def update(self, entity: T) -> T:
        """更新实体"""
        entity = self._prepare_entity_for_update(entity)
        entity_id = self._get_entity_id(entity)
        row_data = self._entity_to_row(entity)
        
        success = await self.query_executor.update_entity(
            entity_id,
            row_data,
            self._get_id_field_name(),
            f"update_{self.table_name}"
        )
        
        if not success:
            raise EntityNotFoundError(self.table_name, entity_id)
        
        return entity

    async def delete(self, entity_id: ID) -> bool:
        """删除实体"""
        return await self.query_executor.delete_entity(
            entity_id,
            self._get_id_field_name(),
            f"delete_{self.table_name}"
        )

    async def count(self) -> int:
        """获取实体总数"""
        return await self.query_executor.count_entities(
            operation_name=f"count_{self.table_name}"
        )

    async def exists(self, entity_id: ID) -> bool:
        """检查实体是否存在"""
        entity = await self.get_by_id(entity_id)
        return entity is not None


class QueryMixin(ABC):
    """查询操作混入类
    
    提供通用的查询操作实现。
    """

    def __init__(self, query_executor: QueryExecutor):
        self.query_executor = query_executor

    @abstractmethod
    def _row_to_entity(self, row: Dict[str, Any]) -> T:
        """将数据库行数据转换为实体"""
        pass

    async def find_by_field(
        self,
        field_name: str,
        field_value: Any,
        limit: Optional[int] = None,
        order_by: str = "created_at",
        order_direction: str = "DESC"
    ) -> List[T]:
        """根据字段值查找实体"""
        from .base_repository import QueryBuilder
        
        query_builder = QueryBuilder(self.query_executor.table_name)
        query_builder.where(f"{field_name} = ?", field_value)
        query_builder.order_by(order_by, order_direction)
        
        if limit is not None:
            query_builder.limit(limit)
        
        return await self.query_executor.execute_builder_query(
            query_builder,
            self._row_to_entity,
            f"find_{self.query_executor.table_name}_by_{field_name}"
        )

    async def find_by_fields(
        self,
        conditions: Dict[str, Any],
        limit: Optional[int] = None,
        order_by: str = "created_at",
        order_direction: str = "DESC"
    ) -> List[T]:
        """根据多个字段条件查找实体"""
        from .base_repository import QueryBuilder
        
        query_builder = QueryBuilder(self.query_executor.table_name)
        
        for field_name, field_value in conditions.items():
            query_builder.where(f"{field_name} = ?", field_value)
        
        query_builder.order_by(order_by, order_direction)
        
        if limit is not None:
            query_builder.limit(limit)
        
        return await self.query_executor.execute_builder_query(
            query_builder,
            self._row_to_entity,
            f"find_{self.query_executor.table_name}_by_fields"
        )

    async def find_in_range(
        self,
        field_name: str,
        start_value: Any,
        end_value: Any,
        limit: Optional[int] = None,
        order_by: str = "created_at",
        order_direction: str = "DESC"
    ) -> List[T]:
        """根据字段范围查找实体"""
        from .base_repository import QueryBuilder
        
        query_builder = QueryBuilder(self.query_executor.table_name)
        query_builder.where_between(field_name, start_value, end_value)
        query_builder.order_by(order_by, order_direction)
        
        if limit is not None:
            query_builder.limit(limit)
        
        return await self.query_executor.execute_builder_query(
            query_builder,
            self._row_to_entity,
            f"find_{self.query_executor.table_name}_in_range"
        )

    async def search_by_pattern(
        self,
        field_name: str,
        pattern: str,
        limit: Optional[int] = None,
        order_by: str = "created_at",
        order_direction: str = "DESC"
    ) -> List[T]:
        """根据模式搜索实体"""
        from .base_repository import QueryBuilder
        
        query_builder = QueryBuilder(self.query_executor.table_name)
        query_builder.where_like(field_name, pattern)
        query_builder.order_by(order_by, order_direction)
        
        if limit is not None:
            query_builder.limit(limit)
        
        return await self.query_executor.execute_builder_query(
            query_builder,
            self._row_to_entity,
            f"search_{self.query_executor.table_name}_by_pattern"
        )

    async def list_all(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        order_by: str = "created_at",
        order_direction: str = "DESC"
    ) -> List[T]:
        """获取所有实体列表"""
        from .base_repository import QueryBuilder
        
        query_builder = QueryBuilder(self.query_executor.table_name)
        query_builder.order_by(order_by, order_direction)
        
        if limit is not None:
            query_builder.limit(limit).offset(offset)
        
        return await self.query_executor.execute_builder_query(
            query_builder,
            self._row_to_entity,
            f"list_all_{self.query_executor.table_name}"
        )


class BatchOperationMixin(ABC):
    """批量操作混入类
    
    提供批量操作的实现。
    """

    @abstractmethod
    async def create(self, entity: T) -> T:
        """创建单个实体"""
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """更新单个实体"""
        pass

    @abstractmethod
    async def delete(self, entity_id: ID) -> bool:
        """删除单个实体"""
        pass

    async def batch_create(self, entities: List[T]) -> List[T]:
        """批量创建实体"""
        result = []
        for entity in entities:
            try:
                created_entity = await self.create(entity)
                result.append(created_entity)
            except Exception as e:
                logger.error(f"Failed to create entity in batch: {e}")
                # 继续处理其他实体
                continue
        return result

    async def batch_update(self, entities: List[T]) -> List[T]:
        """批量更新实体"""
        result = []
        for entity in entities:
            try:
                updated_entity = await self.update(entity)
                result.append(updated_entity)
            except Exception as e:
                logger.error(f"Failed to update entity in batch: {e}")
                # 继续处理其他实体
                continue
        return result

    async def batch_delete(self, entity_ids: List[ID]) -> int:
        """批量删除实体
        
        Returns:
            删除的实体数量
        """
        deleted_count = 0
        for entity_id in entity_ids:
            try:
                if await self.delete(entity_id):
                    deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete entity {entity_id} in batch: {e}")
                # 继续处理其他实体
                continue
        return deleted_count


class TimestampMixin:
    """时间戳混入类
    
    提供时间戳相关的工具方法。
    """

    @staticmethod
    def set_timestamps(entity: Any, is_create: bool = False) -> None:
        """设置实体的时间戳
        
        Args:
            entity: 实体对象
            is_create: 是否为创建操作
        """
        now = datetime.now()
        
        if is_create and hasattr(entity, 'created_at'):
            entity.created_at = now
        
        if hasattr(entity, 'updated_at'):
            entity.updated_at = now

    @staticmethod
    def parse_timestamp(value: Optional[str]) -> Optional[datetime]:
        """解析时间戳字符串"""
        return DataConverter.parse_datetime(value)

    @staticmethod
    def format_timestamp(value: Optional[datetime]) -> Optional[str]:
        """格式化时间戳"""
        return DataConverter.format_datetime(value)


class JsonFieldMixin:
    """JSON字段混入类
    
    提供JSON字段处理的工具方法。
    """

    @staticmethod
    def parse_json_field(value: Optional[str], default: Any = None) -> Any:
        """解析JSON字段"""
        return DataConverter.parse_json(value, default)

    @staticmethod
    def format_json_field(value: Any) -> Optional[str]:
        """格式化JSON字段"""
        return DataConverter.format_json(value)


class UuidMixin:
    """UUID混入类
    
    提供UUID处理的工具方法。
    """

    @staticmethod
    def parse_uuid_field(value: Union[str, UUID, None]) -> Optional[UUID]:
        """解析UUID字段"""
        return DataConverter.parse_uuid(value)

    @staticmethod
    def format_uuid_field(value: Optional[UUID]) -> Optional[str]:
        """格式化UUID字段"""
        return DataConverter.format_uuid(value)

    @staticmethod
    def generate_uuid() -> str:
        """生成新的UUID"""
        return str(uuid4())