# -*- coding: utf-8 -*-
"""
统一的任务数据模型

本模块定义了项目中使用的统一任务数据模型，解决了之前多重定义的问题。
使用Pydantic作为基础，提供类型安全和自动验证功能。
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class TaskType(Enum):
    """任务类型枚举"""
    DAILY_MISSION = "daily_mission"
    WEEKLY_MISSION = "weekly_mission" 
    EXPLORATION = "exploration"
    COMBAT = "combat"
    CUSTOM = "custom"


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class TaskConfig(BaseModel):
    """统一的任务配置模型"""
    name: str = Field(..., description="任务名称")
    task_type: TaskType = Field(..., description="任务类型")
    description: str = Field(default="", description="任务描述")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM.value, description="任务优先级")
    max_retry_count: int = Field(default=3, description="最大重试次数")
    timeout_seconds: int = Field(default=300, description="超时时间(秒)")
    schedule_enabled: bool = Field(default=False, description="是否启用调度")
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="操作列表")
    tags: List[str] = Field(default_factory=list, description="标签")
    custom_params: Dict[str, Any] = Field(default_factory=dict, description="自定义参数")
    
    class Config:
        use_enum_values = True
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskConfig':
        """从字典创建"""
        return cls.model_validate(data)
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return self.model_dump_json()
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TaskConfig':
        """从JSON字符串创建"""
        return cls.model_validate_json(json_str)


class Task(BaseModel):
    """统一的任务模型"""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="任务ID")
    user_id: str = Field(default="default_user", description="用户ID")
    config: TaskConfig = Field(..., description="任务配置")
    status: TaskStatus = Field(default=TaskStatus.PENDING.value, description="任务状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    retry_count: int = Field(default=0, description="重试次数")
    last_error: Optional[str] = Field(default=None, description="最后错误")
    execution_result: Optional[Dict[str, Any]] = Field(default=None, description="执行结果")
    
    class Config:
        use_enum_values = True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """从字典创建"""
        return cls.model_validate(data)
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return self.model_dump_json()
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Task':
        """从JSON字符串创建"""
        return cls.model_validate_json(json_str)
    
    def update_status(self, new_status: TaskStatus, error_msg: Optional[str] = None) -> None:
        """更新任务状态"""
        self.status = new_status.value if isinstance(new_status, TaskStatus) else new_status
        self.updated_at = datetime.now()
        
        if new_status == TaskStatus.RUNNING and self.started_at is None:
            self.started_at = datetime.now()
        elif new_status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            if self.completed_at is None:
                self.completed_at = datetime.now()
        
        if error_msg:
            self.last_error = error_msg
    
    def increment_retry(self) -> None:
        """增加重试次数"""
        self.retry_count += 1
        self.updated_at = datetime.now()
    
    def can_retry(self) -> bool:
        """检查是否可以重试"""
        return self.retry_count < self.config.max_retry_count
    
    def set_execution_result(self, result: Dict[str, Any]) -> None:
        """设置执行结果"""
        self.execution_result = result
        self.updated_at = datetime.now()
    
    @property
    def name(self) -> str:
        """获取任务名称"""
        return self.config.name
    
    @property
    def task_type(self):
        """获取任务类型"""
        return self.config.task_type
    
    @property
    def priority(self):
        """获取任务优先级"""
        return self.config.priority
    
    @property
    def is_running(self) -> bool:
        """检查任务是否正在运行"""
        return self.status == TaskStatus.RUNNING.value
    
    @property
    def is_completed(self) -> bool:
        """检查任务是否已完成"""
        return self.status == TaskStatus.COMPLETED.value
    
    @property
    def is_failed(self) -> bool:
        """检查任务是否失败"""
        return self.status == TaskStatus.FAILED.value
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """获取任务执行时长（秒）"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


# 为了向后兼容，提供一些便利函数
def create_task_config(
    name: str,
    task_type: TaskType,
    description: str = "",
    priority: TaskPriority = TaskPriority.MEDIUM,
    **kwargs
) -> TaskConfig:
    """创建任务配置的便利函数"""
    return TaskConfig(
        name=name,
        task_type=task_type,
        description=description,
        priority=priority,
        **kwargs
    )


def create_task(
    config: TaskConfig,
    user_id: str = "default_user",
    **kwargs
) -> Task:
    """创建任务的便利函数"""
    return Task(
        config=config,
        user_id=user_id,
        **kwargs
    )