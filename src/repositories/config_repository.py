"""配置仓储实现

提供配置相关的数据访问功能。
"""

from datetime import datetime
import json
import logging
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from .base_repository import (
    BaseRepository,
    EntityNotFoundError,
    QueryBuilder,
    QueryExecutionError,
)
from .repository_mixins import CrudMixin, QueryMixin, BatchOperationMixin, TimestampMixin, JsonFieldMixin

logger = logging.getLogger(__name__)


class ConfigItem:
    """配置项数据模型"""

    def __init__(
        self,
        id: UUID = None,
        key: str = None,
        value: str = None,
        description: str = None,
        category: str = "general",
        is_encrypted: bool = False,
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        self.id = id or uuid4()
        self.key = key
        self.value = value
        self.description = description
        self.category = category
        self.is_encrypted = is_encrypted
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": str(self.id),
            "key": self.key,
            "value": self.value,
            "description": self.description,
            "category": self.category,
            "is_encrypted": self.is_encrypted,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigItem":
        """从字典创建"""
        return cls(
            id=UUID(data["id"]),
            key=data["key"],
            value=data["value"],
            description=data["description"],
            category=data["category"],
            is_encrypted=bool(data["is_encrypted"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


class ConfigRepository(BaseRepository[ConfigItem, UUID], CrudMixin, QueryMixin, BatchOperationMixin, TimestampMixin, JsonFieldMixin):
    """配置仓储实现"""

    def __init__(self, db_path: str):
        super().__init__(db_path)
        CrudMixin.__init__(self, db_path, "configs")
        QueryMixin.__init__(self, self.query_executor)
        self.table_name = "configs"

    def _entity_to_row(self, entity: ConfigItem) -> Dict[str, Any]:
        """将配置实体转换为数据库行数据"""
        return self._config_to_row(entity)

    def _row_to_entity(self, row: Dict[str, Any]) -> ConfigItem:
        """将数据库行数据转换为配置实体"""
        return self._row_to_config(row)

    def _get_entity_id(self, entity: ConfigItem) -> UUID:
        """获取配置实体ID"""
        return entity.id

    def _set_entity_id(self, entity: ConfigItem, entity_id: UUID) -> None:
        """设置配置实体ID"""
        entity.id = entity_id

    def _row_to_config(self, row: Dict[str, Any]) -> ConfigItem:
        """将数据库行转换为ConfigItem对象"""
        try:
            return ConfigItem(
                id=UUID(row["id"]),
                key=row["key"],
                value=row["value"],
                description=row["description"],
                category=row["category"],
                is_encrypted=bool(row["is_encrypted"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
        except Exception as e:
            logger.error(f"Failed to convert row to ConfigItem: {e}, row: {row}")
            raise QueryExecutionError("Failed to parse config data", e)

    def _config_to_row(self, config: ConfigItem) -> Dict[str, Any]:
        """将ConfigItem对象转换为数据库行"""
        return {
            "id": str(config.id),
            "key": config.key,
            "value": config.value,
            "description": config.description,
            "category": config.category,
            "is_encrypted": 1 if config.is_encrypted else 0,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat(),
        }

    async def create(self, config: ConfigItem) -> ConfigItem:
        """创建配置项"""
        return await CrudMixin.create(self, config)

    async def get_by_id(self, config_id: UUID) -> Optional[ConfigItem]:
        """根据ID获取配置项"""
        return await CrudMixin.get_by_id(self, config_id)

    async def get_by_key(self, key: str) -> Optional[ConfigItem]:
        """根据键获取配置项"""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT * FROM configs WHERE key = ?", (key,)
                )
                row = await cursor.fetchone()

                if row:
                    columns = [description[0] for description in cursor.description]
                    row_dict = dict(zip(columns, row))
                    return self._row_to_config(row_dict)

                return None

        except Exception as e:
            logger.error(f"Failed to get config by key {key}: {e}")
            raise QueryExecutionError(f"Failed to get config by key {key}", e)

    async def update(self, config: ConfigItem) -> ConfigItem:
        """更新配置项"""
        return await CrudMixin.update(self, config)

    async def delete(self, config_id: UUID) -> bool:
        """删除配置项"""
        return await CrudMixin.delete(self, config_id)

    async def delete_by_key(self, key: str) -> bool:
        """根据键删除配置项"""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute("DELETE FROM configs WHERE key = ?", (key,))

                deleted = cursor.rowcount > 0
                await conn.commit()

                if deleted:
                    logger.info(f"Config deleted by key: {key}")

                return deleted

        except Exception as e:
            logger.error(f"Failed to delete config by key {key}: {e}")
            raise QueryExecutionError(f"Failed to delete config by key {key}", e)

    async def list_all(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[ConfigItem]:
        """获取所有配置项列表"""
        try:
            query_builder = QueryBuilder(self.table_name)
            query_builder.order_by("category", "ASC").order_by("key", "ASC")

            if limit is not None:
                query_builder.limit(limit).offset(offset)

            sql, params = query_builder.build()

            async with self.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()

                configs = []
                columns = [description[0] for description in cursor.description]

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    configs.append(self._row_to_config(row_dict))

                return configs

        except Exception as e:
            logger.error(f"Failed to list configs: {e}")
            raise QueryExecutionError("Failed to list configs", e)

    async def count(self) -> int:
        """获取配置项总数"""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute("SELECT COUNT(*) FROM configs")
                row = await cursor.fetchone()
                return row[0] if row else 0

        except Exception as e:
            logger.error(f"Failed to count configs: {e}")
            raise QueryExecutionError("Failed to count configs", e)

    async def get_by_category(self, category: str) -> List[ConfigItem]:
        """根据分类获取配置项"""
        try:
            query_builder = QueryBuilder(self.table_name)
            query_builder.where("category = ?", category)
            query_builder.order_by("key", "ASC")

            sql, params = query_builder.build()

            async with self.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()

                configs = []
                columns = [description[0] for description in cursor.description]

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    configs.append(self._row_to_config(row_dict))

                return configs

        except Exception as e:
            logger.error(f"Failed to get configs by category {category}: {e}")
            raise QueryExecutionError(
                f"Failed to get configs by category {category}", e
            )

    async def set_value(
        self, key: str, value: str, description: str = None, category: str = "general"
    ) -> ConfigItem:
        """设置配置值（如果不存在则创建，存在则更新）"""
        try:
            existing_config = await self.get_by_key(key)

            if existing_config:
                # 更新现有配置
                existing_config.value = value
                if description is not None:
                    existing_config.description = description
                return await self.update(existing_config)
            else:
                # 创建新配置
                new_config = ConfigItem(
                    key=key, value=value, description=description, category=category
                )
                return await self.create(new_config)

        except Exception as e:
            logger.error(f"Failed to set config value for key {key}: {e}")
            raise QueryExecutionError(f"Failed to set config value for key {key}", e)

    async def get_value(self, key: str, default_value: str = None) -> Optional[str]:
        """获取配置值"""
        try:
            config = await self.get_by_key(key)
            return config.value if config else default_value

        except Exception as e:
            logger.error(f"Failed to get config value for key {key}: {e}")
            raise QueryExecutionError(f"Failed to get config value for key {key}", e)

    async def get_typed_value(
        self, key: str, value_type: type, default_value: Any = None
    ) -> Any:
        """获取指定类型的配置值"""
        try:
            value_str = await self.get_value(key)

            if value_str is None:
                return default_value

            # 类型转换
            if value_type == bool:
                return value_str.lower() in ("true", "1", "yes", "on")
            elif value_type == int:
                return int(value_str)
            elif value_type == float:
                return float(value_str)
            elif value_type == list:
                return json.loads(value_str)
            elif value_type == dict:
                return json.loads(value_str)
            else:
                return value_str

        except (ValueError, json.JSONDecodeError) as e:
            logger.warning(
                f"Failed to convert config value for key {key} to type {value_type}: {e}"
            )
            return default_value
        except Exception as e:
            logger.error(f"Failed to get typed config value for key {key}: {e}")
            raise QueryExecutionError(
                f"Failed to get typed config value for key {key}", e
            )

    async def set_typed_value(
        self, key: str, value: Any, description: str = None, category: str = "general"
    ) -> ConfigItem:
        """设置指定类型的配置值"""
        try:
            # 类型转换为字符串
            if isinstance(value, (list, dict)):
                value_str = json.dumps(value)
            elif isinstance(value, bool):
                value_str = "true" if value else "false"
            else:
                value_str = str(value)

            return await self.set_value(key, value_str, description, category)

        except Exception as e:
            logger.error(f"Failed to set typed config value for key {key}: {e}")
            raise QueryExecutionError(
                f"Failed to set typed config value for key {key}", e
            )

    async def get_categories(self) -> List[str]:
        """获取所有配置分类"""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT DISTINCT category FROM configs ORDER BY category"
                )
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

        except Exception as e:
            logger.error(f"Failed to get config categories: {e}")
            raise QueryExecutionError("Failed to get config categories", e)

    async def search_configs(
        self, query: str = None, category: str = None, limit: int = 50
    ) -> List[ConfigItem]:
        """搜索配置项"""
        try:
            query_builder = QueryBuilder(self.table_name)

            # 文本搜索
            if query:
                query_builder.where(
                    "(key LIKE ? OR description LIKE ?)", f"%{query}%", f"%{query}%"
                )

            # 分类过滤
            if category:
                query_builder.where("category = ?", category)

            query_builder.order_by("category", "ASC").order_by("key", "ASC")
            query_builder.limit(limit)

            sql, params = query_builder.build()

            async with self.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()

                configs = []
                columns = [description[0] for description in cursor.description]

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    configs.append(self._row_to_config(row_dict))

                return configs

        except Exception as e:
            logger.error(f"Failed to search configs: {e}")
            raise QueryExecutionError("Failed to search configs", e)
