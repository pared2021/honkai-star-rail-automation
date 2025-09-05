# -*- coding: utf-8 -*-
"""
领域数据模型 - 使用Pydantic实现统一的数据模型
基于技术架构重构文档的设计规范
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
    CUSTOM = "custom"  # 自定义任务


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"  # 等待中
    RUNNING = "running"  # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消
    PAUSED = "paused"  # 已暂停


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class TaskConfig(BaseModel):
    """任务配置模型"""
    model_config = ConfigDict(use_enum_values=True)
    
    name: str = Field(..., description="任务名称")
    task_type: TaskType = Field(..., description="任务类型")
    description: str = Field(default="", description="任务描述")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="任务优先级")
    max_retries: int = Field(default=3, description="最大重试次数")
    timeout_seconds: int = Field(default=300, description="超时时间(秒)")
    automation_config: Dict[str, Any] = Field(default_factory=dict, description="自动化配置")
    schedule_config: Optional[Dict[str, Any]] = Field(default=None, description="调度配置")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = self.model_dump()
        data['task_type'] = self.task_type.value
        data['priority'] = self.priority.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskConfig':
        """从字典创建"""
        data = data.copy()
        if 'task_type' in data:
            data['task_type'] = TaskType(data['task_type'])
        if 'priority' in data:
            data['priority'] = TaskPriority(data['priority'])
        return cls(**data)
    
    def to_json(self) -> str:
        """转换为JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TaskConfig':
        """从JSON创建"""
        return cls.from_dict(json.loads(json_str))


class Task(BaseModel):
    """任务实体模型"""
    model_config = ConfigDict(use_enum_values=True)
    
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="任务ID")
    user_id: str = Field(default="default_user", description="用户ID")
    config: TaskConfig = Field(..., description="任务配置")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="任务状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    retry_count: int = Field(default=0, description="重试次数")
    last_error: Optional[str] = Field(default=None, description="最后错误信息")
    execution_result: Optional[Dict[str, Any]] = Field(default=None, description="执行结果")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = self.model_dump()
        data['config'] = self.config.to_dict()
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        if self.started_at:
            data['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """从字典创建"""
        data = data.copy()
        if 'config' in data:
            data['config'] = TaskConfig.from_dict(data['config'])
        if 'status' in data:
            data['status'] = TaskStatus(data['status'])
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at']