"""任务管理器适配器模块。

提供任务管理器的适配器实现，用于连接不同的任务管理系统。
"""

from typing import Any, Optional
from unittest.mock import Mock


class TaskManager:
    """任务管理器类。"""

    def __init__(self):
        self._tasks = {}

    def get_task(self, task_id: int) -> Optional[Any]:
        """获取任务。

        Args:
            task_id: 任务ID

        Returns:
            任务对象或None
        """
        return self._tasks.get(task_id)

    def add_task(self, task_id: int, task: Any) -> None:
        """添加任务。

        Args:
            task_id: 任务ID
            task: 任务对象
        """
        self._tasks[task_id] = task


class Container:
    """依赖注入容器。"""

    def __init__(self):
        self.task_manager = TaskManager()


# 全局容器实例
_container = Container()


def get_container() -> Container:
    """获取容器实例。

    Returns:
        容器实例
    """
    return _container


class TaskManagerAdapter:
    """任务管理器适配器类。"""

    def __init__(self, db_manager=None):
        """初始化任务管理器适配器。

        Args:
            db_manager: 数据库管理器实例（可选）
        """
        self._container = get_container()
        self._db_manager = db_manager

    def get_task_sync(self, task_id: Optional[int] = None) -> Any:
        """同步获取任务。

        Args:
            task_id: 任务ID，可选

        Returns:
            任务对象
        """
        if task_id is not None:
            return self._container.task_manager.get_task(task_id)
        else:
            # 返回一个默认任务
            mock_task = Mock()
            mock_task.id = 1
            mock_task.name = "默认任务"
            return mock_task
