"""仓储层模块

提供数据访问层的统一入口。
"""

from .base_repository import (
    BaseRepository,
    DatabaseConnectionError,
    DuplicateEntityError,
    EntityNotFoundError,
    QueryBuilder,
    QueryExecutionError,
    RepositoryError,
)
from .config_repository import ConfigItem, ConfigRepository
from .dependency_repository import TaskDependency, TaskDependencyRepository
from .execution_repository import (
    ExecutionAction,
    ExecutionActionRepository,
    TaskExecution,
    TaskExecutionRepository,
)
from .screenshot_repository import ExecutionScreenshot, ScreenshotRepository
from .task_repository import TaskRepository

__all__ = [
    # 基础类
    "BaseRepository",
    "QueryBuilder",
    "RepositoryError",
    "EntityNotFoundError",
    "DuplicateEntityError",
    "DatabaseConnectionError",
    "QueryExecutionError",
    # 任务相关
    "TaskRepository",
    # 配置相关
    "ConfigItem",
    "ConfigRepository",
    # 执行相关
    "TaskExecution",
    "ExecutionAction",
    "TaskExecutionRepository",
    "ExecutionActionRepository",
    # 截图相关
    "ExecutionScreenshot",
    "ScreenshotRepository",
    # 依赖关系相关
    "TaskDependency",
    "TaskDependencyRepository",
]
