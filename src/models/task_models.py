"""任务数据模型模块。.

定义任务相关的数据模型和实体类。
"""

from datetime import datetime
from enum import Enum
import json
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field


class TaskType(Enum):
    """任务类型枚举"""

    DAILY_MISSION = "daily_mission"  # 日常任务
    WEEKLY_MISSION = "weekly_mission"  # 周常任务
    EXPLORATION = "exploration"  # 探索任务
    COMBAT = "combat"  # 战斗任务
    AUTOMATION = "automation"  # 自动化任务
    CUSTOM = "custom"  # 自定义任务


class TaskStatus(Enum):
    """任务状态枚举"""

    PENDING = "pending"  # 等待中
    RUNNING = "running"  # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消
    PAUSED = "paused"  # 已暂停


class TaskConfig(BaseModel):
    """任务配置模型"""

    model_config = ConfigDict(use_enum_values=True)

    name: str = Field(..., description="任务名称")
    task_type: TaskType = Field(..., description="任务类型")
    description: str = Field(default="", description="任务描述")
    priority: str = Field(default="MEDIUM", description="任务优先级")
    max_retries: int = Field(default=3, description="最大重试次数")
    timeout_seconds: int = Field(default=300, description="超时时间(秒)")
    automation_config: Dict[str, Any] = Field(
        default_factory=dict, description="自动化配置"
    )
    schedule_config: Optional[Dict[str, Any]] = Field(
        default=None, description="调度配置"
    )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = self.model_dump()
        data["task_type"] = self.task_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskConfig":
        """从字典创建"""
        data = data.copy()
        if "task_type" in data:
            data["task_type"] = TaskType(data["task_type"])
        return cls(**data)

    def to_json(self) -> str:
        """转换为JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "TaskConfig":
        """从JSON创建"""
        return cls.from_dict(json.loads(json_str))
