"""数据库配置模块

提供数据库连接和配置相关的功能。
"""

import os
from pathlib import Path
from typing import Optional

# 默认数据库配置
DEFAULT_DB_NAME = "xingtie_assistant.db"
DEFAULT_DB_DIR = "data"


def get_project_root() -> Path:
    """获取项目根目录"""
    # 从当前文件向上查找项目根目录
    current_path = Path(__file__).parent
    while current_path.parent != current_path:
        # 检查是否包含标识项目根目录的文件
        if (
            (current_path / "pyproject.toml").exists()
            or (current_path / "requirements.txt").exists()
            or (current_path / "setup.py").exists()
            or (current_path / ".git").exists()
        ):
            return current_path
        current_path = current_path.parent

    # 如果没找到，返回当前文件的上上级目录（假设项目结构）
    return Path(__file__).parent.parent.parent


def get_database_path(db_name: Optional[str] = None) -> str:
    """获取数据库文件路径

    Args:
        db_name: 数据库文件名，如果为None则使用默认名称

    Returns:
        数据库文件的完整路径
    """
    if db_name is None:
        db_name = DEFAULT_DB_NAME

    # 从环境变量获取数据库路径
    db_path_env = os.getenv("XINGTIE_DB_PATH")
    if db_path_env:
        return db_path_env

    # 使用项目根目录下的data目录
    project_root = get_project_root()
    db_dir = project_root / DEFAULT_DB_DIR

    # 确保目录存在
    db_dir.mkdir(exist_ok=True)

    return str(db_dir / db_name)


def get_database_url(db_path: Optional[str] = None) -> str:
    """获取数据库连接URL

    Args:
        db_path: 数据库文件路径，如果为None则使用默认路径

    Returns:
        SQLite数据库连接URL
    """
    if db_path is None:
        db_path = get_database_path()

    return f"sqlite:///{db_path}"


def get_async_database_url(db_path: Optional[str] = None) -> str:
    """获取异步数据库连接URL

    Args:
        db_path: 数据库文件路径，如果为None则使用默认路径

    Returns:
        异步SQLite数据库连接URL
    """
    if db_path is None:
        db_path = get_database_path()

    return f"sqlite+aiosqlite:///{db_path}"


class DatabaseConfig:
    """数据库配置类"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_database_path()
        self.db_url = get_database_url(self.db_path)
        self.async_db_url = get_async_database_url(self.db_path)

    @property
    def connection_params(self) -> dict:
        """获取连接参数"""
        return {
            "check_same_thread": False,  # 允许多线程访问
            "timeout": 30.0,  # 连接超时时间
        }

    @property
    def async_connection_params(self) -> dict:
        """获取异步连接参数"""
        return {
            "timeout": 30.0,  # 连接超时时间
        }

    def ensure_database_directory(self) -> None:
        """确保数据库目录存在"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def database_exists(self) -> bool:
        """检查数据库文件是否存在"""
        return Path(self.db_path).exists()

    def get_backup_path(self, suffix: str = None) -> str:
        """获取数据库备份路径

        Args:
            suffix: 备份文件后缀，如果为None则使用时间戳

        Returns:
            备份文件路径
        """
        if suffix is None:
            from datetime import datetime

            suffix = datetime.now().strftime("%Y%m%d_%H%M%S")

        db_path = Path(self.db_path)
        backup_name = f"{db_path.stem}_backup_{suffix}{db_path.suffix}"
        return str(db_path.parent / backup_name)


# 全局数据库配置实例
_global_config: Optional[DatabaseConfig] = None


def get_database_config() -> DatabaseConfig:
    """获取全局数据库配置实例"""
    global _global_config
    if _global_config is None:
        _global_config = DatabaseConfig()
    return _global_config


def set_database_config(config: DatabaseConfig) -> None:
    """设置全局数据库配置实例"""
    global _global_config
    _global_config = config


# 便捷函数
def init_database_config(db_path: Optional[str] = None) -> DatabaseConfig:
    """初始化数据库配置

    Args:
        db_path: 数据库文件路径

    Returns:
        数据库配置实例
    """
    config = DatabaseConfig(db_path)
    config.ensure_database_directory()
    set_database_config(config)
    return config
