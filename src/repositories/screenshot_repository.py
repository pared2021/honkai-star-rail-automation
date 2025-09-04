"""截图仓储实现

提供截图数据的存储和管理功能。
"""

from datetime import datetime, timedelta
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

logger = logging.getLogger(__name__)


class ExecutionScreenshot:
    """执行截图数据模型"""

    def __init__(
        self,
        id: str = None,
        execution_id: str = None,
        action_id: str = None,
        screenshot_type: str = "action",
        file_path: str = None,
        file_size: int = 0,
        width: int = 0,
        height: int = 0,
        format: str = "png",
        metadata: Dict[str, Any] = None,
        created_at: datetime = None,
    ):
        self.id = id or str(uuid4())
        self.execution_id = execution_id
        self.action_id = action_id
        self.screenshot_type = screenshot_type
        self.file_path = file_path
        self.file_size = file_size
        self.width = width
        self.height = height
        self.format = format
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "execution_id": self.execution_id,
            "action_id": self.action_id,
            "screenshot_type": self.screenshot_type,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "width": self.width,
            "height": self.height,
            "format": self.format,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionScreenshot":
        """从字典创建"""
        return cls(
            id=data["id"],
            execution_id=data["execution_id"],
            action_id=data["action_id"],
            screenshot_type=data["screenshot_type"],
            file_path=data["file_path"],
            file_size=data["file_size"],
            width=data["width"],
            height=data["height"],
            format=data["format"],
            metadata=data["metadata"],
            created_at=datetime.fromisoformat(data["created_at"]),
        )


class ScreenshotRepository(BaseRepository[ExecutionScreenshot, str]):
    """截图仓储实现"""

    def __init__(self, db_path: str):
        super().__init__(db_path)
        self.table_name = "execution_screenshots"

    def _row_to_screenshot(self, row: Dict[str, Any]) -> ExecutionScreenshot:
        """将数据库行转换为ExecutionScreenshot对象"""
        try:
            metadata = json.loads(row["metadata"]) if row["metadata"] else {}

            return ExecutionScreenshot(
                id=row["id"],
                execution_id=row["execution_id"],
                action_id=row["action_id"],
                screenshot_type=row["screenshot_type"],
                file_path=row["file_path"],
                file_size=row["file_size"],
                width=row["width"],
                height=row["height"],
                format=row["format"],
                metadata=metadata,
                created_at=datetime.fromisoformat(row["created_at"]),
            )
        except Exception as e:
            logger.error(
                f"Failed to convert row to ExecutionScreenshot: {e}, row: {row}"
            )
            raise QueryExecutionError("Failed to parse screenshot data", e)

    def _screenshot_to_row(self, screenshot: ExecutionScreenshot) -> Dict[str, Any]:
        """将ExecutionScreenshot对象转换为数据库行"""
        return {
            "id": screenshot.id,
            "execution_id": screenshot.execution_id,
            "action_id": screenshot.action_id,
            "screenshot_type": screenshot.screenshot_type,
            "file_path": screenshot.file_path,
            "file_size": screenshot.file_size,
            "width": screenshot.width,
            "height": screenshot.height,
            "format": screenshot.format,
            "metadata": json.dumps(screenshot.metadata),
            "created_at": screenshot.created_at.isoformat(),
        }

    async def create(self, screenshot: ExecutionScreenshot) -> ExecutionScreenshot:
        """创建截图记录"""
        try:
            if not screenshot.id:
                screenshot.id = str(uuid4())

            screenshot.created_at = datetime.now()
            row_data = self._screenshot_to_row(screenshot)

            async with self.get_connection() as conn:
                await conn.execute(
                    """
                    INSERT INTO execution_screenshots (
                        id, execution_id, action_id, screenshot_type, file_path,
                        file_size, width, height, format, metadata, created_at
                    ) VALUES (
                        :id, :execution_id, :action_id, :screenshot_type, :file_path,
                        :file_size, :width, :height, :format, :metadata, :created_at
                    )
                    """,
                    row_data,
                )
                await conn.commit()

            logger.info(f"Screenshot created: {screenshot.id}")
            return screenshot

        except Exception as e:
            logger.error(f"Failed to create screenshot: {e}")
            raise QueryExecutionError("Failed to create screenshot", e)

    async def get_by_id(self, screenshot_id: str) -> Optional[ExecutionScreenshot]:
        """根据ID获取截图记录"""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT * FROM execution_screenshots WHERE id = ?", (screenshot_id,)
                )
                row = await cursor.fetchone()

                if row:
                    columns = [description[0] for description in cursor.description]
                    row_dict = dict(zip(columns, row))
                    return self._row_to_screenshot(row_dict)

                return None

        except Exception as e:
            logger.error(f"Failed to get screenshot by ID {screenshot_id}: {e}")
            raise QueryExecutionError(
                f"Failed to get screenshot by ID {screenshot_id}", e
            )

    async def update(self, screenshot: ExecutionScreenshot) -> ExecutionScreenshot:
        """更新截图记录"""
        try:
            row_data = self._screenshot_to_row(screenshot)

            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    """
                    UPDATE execution_screenshots SET
                        execution_id = :execution_id,
                        action_id = :action_id,
                        screenshot_type = :screenshot_type,
                        file_path = :file_path,
                        file_size = :file_size,
                        width = :width,
                        height = :height,
                        format = :format,
                        metadata = :metadata
                    WHERE id = :id
                    """,
                    row_data,
                )

                if cursor.rowcount == 0:
                    raise EntityNotFoundError("ExecutionScreenshot", screenshot.id)

                await conn.commit()

            logger.info(f"Screenshot updated: {screenshot.id}")
            return screenshot

        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to update screenshot {screenshot.id}: {e}")
            raise QueryExecutionError(f"Failed to update screenshot {screenshot.id}", e)

    async def delete(self, screenshot_id: str) -> bool:
        """删除截图记录"""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    "DELETE FROM execution_screenshots WHERE id = ?", (screenshot_id,)
                )

                deleted = cursor.rowcount > 0
                await conn.commit()

                if deleted:
                    logger.info(f"Screenshot deleted: {screenshot_id}")

                return deleted

        except Exception as e:
            logger.error(f"Failed to delete screenshot {screenshot_id}: {e}")
            raise QueryExecutionError(f"Failed to delete screenshot {screenshot_id}", e)

    async def list_all(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[ExecutionScreenshot]:
        """获取所有截图记录列表"""
        try:
            query_builder = QueryBuilder(self.table_name)
            query_builder.order_by("created_at", "DESC")

            if limit is not None:
                query_builder.limit(limit).offset(offset)

            sql, params = query_builder.build()

            async with self.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()

                screenshots = []
                columns = [description[0] for description in cursor.description]

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    screenshots.append(self._row_to_screenshot(row_dict))

                return screenshots

        except Exception as e:
            logger.error(f"Failed to list screenshots: {e}")
            raise QueryExecutionError("Failed to list screenshots", e)

    async def count(self) -> int:
        """获取截图记录总数"""
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    "SELECT COUNT(*) FROM execution_screenshots"
                )
                row = await cursor.fetchone()
                return row[0] if row else 0

        except Exception as e:
            logger.error(f"Failed to count screenshots: {e}")
            raise QueryExecutionError("Failed to count screenshots", e)

    async def find_by_execution_id(
        self, execution_id: str
    ) -> List[ExecutionScreenshot]:
        """根据执行ID查找截图"""
        try:
            query_builder = QueryBuilder(self.table_name)
            query_builder.where("execution_id = ?", execution_id)
            query_builder.order_by("created_at", "ASC")

            sql, params = query_builder.build()

            async with self.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()

                screenshots = []
                columns = [description[0] for description in cursor.description]

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    screenshots.append(self._row_to_screenshot(row_dict))

                return screenshots

        except Exception as e:
            logger.error(
                f"Failed to find screenshots by execution ID {execution_id}: {e}"
            )
            raise QueryExecutionError(
                f"Failed to find screenshots by execution ID {execution_id}", e
            )

    async def find_by_action_id(self, action_id: str) -> List[ExecutionScreenshot]:
        """根据动作ID查找截图"""
        try:
            query_builder = QueryBuilder(self.table_name)
            query_builder.where("action_id = ?", action_id)
            query_builder.order_by("created_at", "ASC")

            sql, params = query_builder.build()

            async with self.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()

                screenshots = []
                columns = [description[0] for description in cursor.description]

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    screenshots.append(self._row_to_screenshot(row_dict))

                return screenshots

        except Exception as e:
            logger.error(f"Failed to find screenshots by action ID {action_id}: {e}")
            raise QueryExecutionError(
                f"Failed to find screenshots by action ID {action_id}", e
            )

    async def find_by_type(
        self, screenshot_type: str, limit: Optional[int] = None
    ) -> List[ExecutionScreenshot]:
        """根据截图类型查找截图"""
        try:
            query_builder = QueryBuilder(self.table_name)
            query_builder.where("screenshot_type = ?", screenshot_type)
            query_builder.order_by("created_at", "DESC")

            if limit is not None:
                query_builder.limit(limit)

            sql, params = query_builder.build()

            async with self.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()

                screenshots = []
                columns = [description[0] for description in cursor.description]

                for row in rows:
                    row_dict = dict(zip(columns, row))
                    screenshots.append(self._row_to_screenshot(row_dict))

                return screenshots

        except Exception as e:
            logger.error(f"Failed to find screenshots by type {screenshot_type}: {e}")
            raise QueryExecutionError(
                f"Failed to find screenshots by type {screenshot_type}", e
            )

    async def get_latest_by_execution(
        self, execution_id: str
    ) -> Optional[ExecutionScreenshot]:
        """获取指定执行的最新截图"""
        try:
            query_builder = QueryBuilder(self.table_name)
            query_builder.where("execution_id = ?", execution_id)
            query_builder.order_by("created_at", "DESC")
            query_builder.limit(1)

            sql, params = query_builder.build()

            async with self.get_connection() as conn:
                cursor = await conn.execute(sql, params)
                row = await cursor.fetchone()

                if row:
                    columns = [description[0] for description in cursor.description]
                    row_dict = dict(zip(columns, row))
                    return self._row_to_screenshot(row_dict)

                return None

        except Exception as e:
            logger.error(
                f"Failed to get latest screenshot for execution {execution_id}: {e}"
            )
            raise QueryExecutionError(
                f"Failed to get latest screenshot for execution {execution_id}", e
            )

    async def cleanup_old_screenshots(self, days: int = 30) -> int:
        """清理指定天数之前的截图记录"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            async with self.get_connection() as conn:
                cursor = await conn.execute(
                    "DELETE FROM execution_screenshots WHERE created_at < ?",
                    (cutoff_date.isoformat(),),
                )

                deleted_count = cursor.rowcount
                await conn.commit()

                logger.info(f"Cleaned up {deleted_count} old screenshots")
                return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old screenshots: {e}")
            raise QueryExecutionError("Failed to cleanup old screenshots", e)

    async def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            async with self.get_connection() as conn:
                # 总数量和总大小
                cursor = await conn.execute(
                    "SELECT COUNT(*), SUM(file_size) FROM execution_screenshots"
                )
                count_row = await cursor.fetchone()
                total_count = count_row[0] if count_row else 0
                total_size = count_row[1] if count_row and count_row[1] else 0

                # 按类型统计
                cursor = await conn.execute(
                    "SELECT screenshot_type, COUNT(*), SUM(file_size) FROM execution_screenshots GROUP BY screenshot_type"
                )
                type_stats = {}
                for row in await cursor.fetchall():
                    type_stats[row[0]] = {
                        "count": row[1],
                        "total_size": row[2] if row[2] else 0,
                    }

                # 按格式统计
                cursor = await conn.execute(
                    "SELECT format, COUNT(*) FROM execution_screenshots GROUP BY format"
                )
                format_stats = {}
                for row in await cursor.fetchall():
                    format_stats[row[0]] = row[1]

                return {
                    "total_count": total_count,
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "by_type": type_stats,
                    "by_format": format_stats,
                }

        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            raise QueryExecutionError("Failed to get storage stats", e)
