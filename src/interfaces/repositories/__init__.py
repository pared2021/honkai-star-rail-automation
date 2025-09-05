"""仓储层接口

定义数据访问层的抽象接口。
"""

from .task_repository_interface import ITaskRepository
from .config_repository_interface import IConfigRepository
from .base_repository_interface import IBaseRepository

__all__ = [
    'ITaskRepository',
    'IConfigRepository', 
    'IBaseRepository'
]