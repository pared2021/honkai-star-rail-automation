"""数据库迁移执行脚本

用于执行数据库迁移的命令行工具。
"""

import os
from pathlib import Path
import sys

import asyncio

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import logging

from src.config.database_config import get_database_path
from src.database.migration_manager import MigrationManager, SyncMigrationManager

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_migrations_dir() -> str:
    """获取迁移文件目录"""
    return str(Path(__file__).parent / "migrations")


async def run_migrations():
    """异步执行迁移"""
    try:
        db_path = get_database_path()
        migrations_dir = get_migrations_dir()

        logger.info(f"数据库路径: {db_path}")
        logger.info(f"迁移目录: {migrations_dir}")

        # 确保数据库目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # 创建迁移管理器
        migration_manager = MigrationManager(db_path, migrations_dir)

        # 获取迁移状态
        status = await migration_manager.get_migration_status()
        logger.info(f"迁移状态: {status}")

        # 执行迁移
        success = await migration_manager.migrate()

        if success:
            logger.info("数据库迁移完成")
            # 再次获取状态
            final_status = await migration_manager.get_migration_status()
            logger.info(f"最终状态: {final_status}")
        else:
            logger.error("数据库迁移失败")
            sys.exit(1)

    except Exception as e:
        logger.error(f"迁移过程中发生错误: {e}")
        sys.exit(1)


def run_migrations_sync():
    """同步执行迁移"""
    try:
        db_path = get_database_path()
        migrations_dir = get_migrations_dir()

        logger.info(f"数据库路径: {db_path}")
        logger.info(f"迁移目录: {migrations_dir}")

        # 确保数据库目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # 创建同步迁移管理器
        migration_manager = SyncMigrationManager(db_path, migrations_dir)

        # 执行迁移
        success = migration_manager.migrate()

        if success:
            logger.info("数据库迁移完成")
        else:
            logger.error("数据库迁移失败")
            sys.exit(1)

    except Exception as e:
        logger.error(f"迁移过程中发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="数据库迁移工具")
    parser.add_argument("--sync", action="store_true", help="使用同步模式执行迁移")
    parser.add_argument("--status", action="store_true", help="显示迁移状态")

    args = parser.parse_args()

    if args.status:
        # 显示迁移状态
        async def show_status():
            db_path = get_database_path()
            migrations_dir = get_migrations_dir()
            migration_manager = MigrationManager(db_path, migrations_dir)
            status = await migration_manager.get_migration_status()
            print(f"迁移状态: {status}")

        asyncio.run(show_status())
    elif args.sync:
        # 同步模式
        run_migrations_sync()
    else:
        # 异步模式（默认）
        asyncio.run(run_migrations())
