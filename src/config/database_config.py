"""数据库配置模块..

提供数据库连接和配置管理功能。
"""

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class DatabaseConfig:
    """数据库配置类."""

    # 数据库类型
    db_type: str = "sqlite"

    # SQLite配置
    db_path: Optional[str] = None

    # 通用数据库配置
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None

    # 连接池配置
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600

    # 其他配置
    echo: bool = False
    autocommit: bool = False
    autoflush: bool = True

    def __post_init__(self):
        """初始化后处理."""
        if self.db_type == "sqlite" and not self.db_path:
            # 默认SQLite数据库路径
            self.db_path = str(Path("data") / "xingtie.db")

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """从环境变量创建配置."""
        return cls(
            db_type=os.getenv("DB_TYPE", "sqlite"),
            db_path=os.getenv("DB_PATH"),
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", "0")) or None,
            database=os.getenv("DB_NAME"),
            username=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
            autocommit=os.getenv("DB_AUTOCOMMIT", "false").lower() == "true",
            autoflush=os.getenv("DB_AUTOFLUSH", "true").lower() == "true",
        )

    def get_connection_string(self) -> str:
        """获取数据库连接字符串."""
        if self.db_type == "sqlite":
            return f"sqlite:///{self.db_path}"
        elif self.db_type == "postgresql":
            return (
                f"postgresql://{self.username}:{self.password}@"
                f"{self.host}:{self.port}/{self.database}"
            )
        elif self.db_type == "mysql":
            return (
                f"mysql+pymysql://{self.username}:{self.password}@"
                f"{self.host}:{self.port}/{self.database}"
            )
        else:
            raise ValueError(f"不支持的数据库类型: {self.db_type}")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            "db_type": self.db_type,
            "db_path": self.db_path,
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "password": "***" if self.password else None,  # 隐藏密码
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "echo": self.echo,
            "autocommit": self.autocommit,
            "autoflush": self.autoflush,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatabaseConfig":
        """从字典创建配置."""
        return cls(
            db_type=data.get("db_type", "sqlite"),
            db_path=data.get("db_path"),
            host=data.get("host"),
            port=data.get("port"),
            database=data.get("database"),
            username=data.get("username"),
            password=data.get("password"),
            pool_size=data.get("pool_size", 5),
            max_overflow=data.get("max_overflow", 10),
            pool_timeout=data.get("pool_timeout", 30),
            pool_recycle=data.get("pool_recycle", 3600),
            echo=data.get("echo", False),
            autocommit=data.get("autocommit", False),
            autoflush=data.get("autoflush", True),
        )


# 默认配置实例
default_config = DatabaseConfig()
