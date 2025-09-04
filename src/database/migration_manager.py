"""数据库迁移管理器

负责管理和执行数据库迁移脚本。
"""

from datetime import datetime
import logging
import os
from pathlib import Path
import sqlite3
from typing import Dict, List, Optional

import aiosqlite

logger = logging.getLogger(__name__)


class MigrationManager:
    """数据库迁移管理器"""

    def __init__(self, db_path: str, migrations_dir: str = None):
        self.db_path = db_path
        if migrations_dir is None:
            # 默认迁移目录为当前文件所在目录的migrations子目录
            current_dir = Path(__file__).parent
            self.migrations_dir = current_dir / "migrations"
        else:
            self.migrations_dir = Path(migrations_dir)

        self.migrations_dir.mkdir(exist_ok=True)

    async def initialize_migration_table(self) -> None:
        """初始化迁移记录表"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    checksum TEXT
                )
            """
            )
            await db.commit()
            logger.info("迁移记录表已初始化")

    def _get_migration_files(self) -> List[Dict[str, str]]:
        """获取所有迁移文件"""
        migrations = []

        if not self.migrations_dir.exists():
            logger.warning(f"迁移目录不存在: {self.migrations_dir}")
            return migrations

        for file_path in sorted(self.migrations_dir.glob("*.sql")):
            # 从文件名提取版本号（假设格式为 001_description.sql）
            filename = file_path.name
            version = filename.split("_")[0]

            migrations.append(
                {"version": version, "filename": filename, "path": str(file_path)}
            )

        return migrations

    async def get_applied_migrations(self) -> List[str]:
        """获取已应用的迁移版本列表"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT version FROM schema_migrations ORDER BY version"
                )
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
        except sqlite3.OperationalError:
            # 如果表不存在，返回空列表
            return []

    async def get_pending_migrations(self) -> List[Dict[str, str]]:
        """获取待应用的迁移"""
        all_migrations = self._get_migration_files()
        applied_versions = await self.get_applied_migrations()

        pending = []
        for migration in all_migrations:
            if migration["version"] not in applied_versions:
                pending.append(migration)

        return pending

    def _calculate_checksum(self, content: str) -> str:
        """计算文件内容的校验和"""
        import hashlib

        return hashlib.md5(content.encode("utf-8")).hexdigest()

    async def apply_migration(self, migration: Dict[str, str]) -> bool:
        """应用单个迁移"""
        try:
            # 读取迁移文件内容
            with open(migration["path"], "r", encoding="utf-8") as f:
                sql_content = f.read()

            checksum = self._calculate_checksum(sql_content)

            async with aiosqlite.connect(self.db_path) as db:
                # 执行迁移SQL
                await db.executescript(sql_content)

                # 记录迁移
                await db.execute(
                    """
                    INSERT INTO schema_migrations (version, filename, checksum)
                    VALUES (?, ?, ?)
                    """,
                    (migration["version"], migration["filename"], checksum),
                )

                await db.commit()

            logger.info(f"迁移已应用: {migration['filename']}")
            return True

        except Exception as e:
            logger.error(f"应用迁移失败 {migration['filename']}: {e}")
            return False

    async def migrate(self) -> bool:
        """执行所有待应用的迁移"""
        try:
            # 确保迁移表存在
            await self.initialize_migration_table()

            # 获取待应用的迁移
            pending_migrations = await self.get_pending_migrations()

            if not pending_migrations:
                logger.info("没有待应用的迁移")
                return True

            logger.info(f"发现 {len(pending_migrations)} 个待应用的迁移")

            # 按版本顺序应用迁移
            for migration in pending_migrations:
                success = await self.apply_migration(migration)
                if not success:
                    logger.error(f"迁移失败，停止后续迁移: {migration['filename']}")
                    return False

            logger.info("所有迁移已成功应用")
            return True

        except Exception as e:
            logger.error(f"迁移过程中发生错误: {e}")
            return False

    async def rollback_migration(self, version: str) -> bool:
        """回滚指定版本的迁移（注意：SQLite不支持复杂的回滚操作）"""
        logger.warning("SQLite不支持自动回滚，请手动处理数据库状态")
        return False

    async def get_migration_status(self) -> Dict[str, any]:
        """获取迁移状态信息"""
        all_migrations = self._get_migration_files()
        applied_migrations = await self.get_applied_migrations()
        pending_migrations = await self.get_pending_migrations()

        return {
            "total_migrations": len(all_migrations),
            "applied_count": len(applied_migrations),
            "pending_count": len(pending_migrations),
            "applied_versions": applied_migrations,
            "pending_migrations": [m["filename"] for m in pending_migrations],
            "last_applied": applied_migrations[-1] if applied_migrations else None,
        }

    def create_migration_file(self, description: str) -> str:
        """创建新的迁移文件"""
        # 获取下一个版本号
        existing_migrations = self._get_migration_files()
        if existing_migrations:
            last_version = int(existing_migrations[-1]["version"])
            next_version = f"{last_version + 1:03d}"
        else:
            next_version = "001"

        # 生成文件名
        safe_description = description.lower().replace(" ", "_").replace("-", "_")
        filename = f"{next_version}_{safe_description}.sql"
        file_path = self.migrations_dir / filename

        # 创建迁移文件模板
        template = f"""-- Migration: {description}
-- Created: {datetime.now().isoformat()}
-- Version: {next_version}

-- Add your SQL statements here
-- Example:
-- CREATE TABLE example (
--     id INTEGER PRIMARY KEY,
--     name TEXT NOT NULL
-- );

-- Remember to add appropriate indexes
-- CREATE INDEX idx_example_name ON example(name);
"""

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(template)

        logger.info(f"迁移文件已创建: {filename}")
        return str(file_path)


# 同步版本的迁移管理器（用于非异步环境）
class SyncMigrationManager:
    """同步版本的数据库迁移管理器"""

    def __init__(self, db_path: str, migrations_dir: str = None):
        self.db_path = db_path
        if migrations_dir is None:
            current_dir = Path(__file__).parent
            self.migrations_dir = current_dir / "migrations"
        else:
            self.migrations_dir = Path(migrations_dir)

        self.migrations_dir.mkdir(exist_ok=True)

    def initialize_migration_table(self) -> None:
        """初始化迁移记录表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    checksum TEXT
                )
            """
            )
            conn.commit()
            logger.info("迁移记录表已初始化")

    def migrate(self) -> bool:
        """执行所有待应用的迁移"""
        try:
            self.initialize_migration_table()

            # 获取所有迁移文件
            migrations = []
            for file_path in sorted(self.migrations_dir.glob("*.sql")):
                filename = file_path.name
                version = filename.split("_")[0]
                migrations.append(
                    {"version": version, "filename": filename, "path": str(file_path)}
                )

            if not migrations:
                logger.info("没有找到迁移文件")
                return True

            # 获取已应用的迁移
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT version FROM schema_migrations ORDER BY version"
                )
                applied_versions = [row[0] for row in cursor.fetchall()]

            # 应用待处理的迁移
            for migration in migrations:
                if migration["version"] not in applied_versions:
                    self._apply_migration_sync(migration)

            logger.info("所有迁移已成功应用")
            return True

        except Exception as e:
            logger.error(f"迁移过程中发生错误: {e}")
            return False

    def _apply_migration_sync(self, migration: Dict[str, str]) -> None:
        """同步应用单个迁移"""
        with open(migration["path"], "r", encoding="utf-8") as f:
            sql_content = f.read()

        import hashlib

        checksum = hashlib.md5(sql_content.encode("utf-8")).hexdigest()

        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(sql_content)
            conn.execute(
                """
                INSERT INTO schema_migrations (version, filename, checksum)
                VALUES (?, ?, ?)
                """,
                (migration["version"], migration["filename"], checksum),
            )
            conn.commit()

        logger.info(f"迁移已应用: {migration['filename']}")
