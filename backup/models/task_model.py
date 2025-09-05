# -*- coding: utf-8 -*-
"""
任务数据模型
"""

from dataclasses import dataclass
from datetime import datetime
import os
import sys
from typing import Any, Dict, Optional

# 添加父目录到Python路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from core.enums import TaskPriority, TaskStatus, TaskType


@dataclass
class Task:
    """任务数据模型"""

    task_id: Optional[str] = None
    user_id: str = ""
    name: str = ""
    description: str = ""
    task_type: TaskType = TaskType.CUSTOM
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    config: Dict[str, Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_executed_at: Optional[datetime] = None
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    is_repeatable: bool = False
    repeat_interval: int = 0  # 重复间隔（秒）
    max_executions: int = 1  # 最大执行次数

    def __post_init__(self):
        if self.config is None:
            self.config = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "task_type": self.task_type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "config": self.config or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_executed_at": (
                self.last_executed_at.isoformat() if self.last_executed_at else None
            ),
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "is_repeatable": self.is_repeatable,
            "repeat_interval": self.repeat_interval,
            "max_executions": self.max_executions,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """从字典创建任务对象"""
        task = cls()
        task.task_id = data.get("task_id")
        task.user_id = data.get("user_id", "")
        task.name = data.get("name", "")
        task.description = data.get("description", "")
        task.task_type = TaskType(data.get("task_type", TaskType.CUSTOM.value))
        task.priority = TaskPriority(data.get("priority", TaskPriority.MEDIUM.value))
        task.status = TaskStatus(data.get("status", TaskStatus.PENDING.value))
        task.config = data.get("config", {})

        # 处理日期时间字段
        if data.get("created_at"):
            task.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            task.updated_at = datetime.fromisoformat(data["updated_at"])
        if data.get("last_executed_at"):
            task.last_executed_at = datetime.fromisoformat(data["last_executed_at"])

        task.execution_count = data.get("execution_count", 0)
        task.success_count = data.get("success_count", 0)
        task.failure_count = data.get("failure_count", 0)
        task.is_repeatable = data.get("is_repeatable", False)
        task.repeat_interval = data.get("repeat_interval", 0)
        task.max_executions = data.get("max_executions", 1)

        return task
