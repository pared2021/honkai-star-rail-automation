# -*- coding: utf-8 -*-
"""
统一数据模型定义
重构后的数据模型，支持统一的序列化和验证
"""

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
import json
from typing import Any, Dict, List, Optional, Union
import uuid

from core.enums import ActionType, TaskPriority, TaskStatus, TaskType


class BaseModel(ABC):
    """基础模型类，提供统一的序列化和验证接口"""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        if hasattr(self, "__dataclass_fields__"):
            return asdict(self)
        else:
            return self._to_dict_impl()

    @abstractmethod
    def _to_dict_impl(self) -> Dict[str, Any]:
        """子类实现的字典转换方法"""
        pass

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(
            self.to_dict(), ensure_ascii=False, indent=2, default=self._json_serializer
        )

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]):
        """从字典创建实例"""
        pass

    @classmethod
    def from_json(cls, json_str: str):
        """从JSON字符串创建实例"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    @staticmethod
    def _json_serializer(obj):
        """JSON序列化器，处理特殊类型"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Enum):
            return obj.value
        elif hasattr(obj, "to_dict"):
            return obj.to_dict()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def validate(self):
        """验证数据模型"""
        self._validate_impl()

    @abstractmethod
    def _validate_impl(self):
        """子类实现的验证方法"""
        pass


@dataclass
class ActionConfig(BaseModel):
    """动作配置数据模型"""

    action_type: ActionType
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 30
    retry_count: int = 3
    description: str = ""
    enabled: bool = True

    def _to_dict_impl(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type.value,
            "parameters": self.parameters,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "description": self.description,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionConfig":
        return cls(
            action_type=ActionType(data.get("action_type", ActionType.CUSTOM.value)),
            parameters=data.get("parameters", {}),
            timeout=data.get("timeout", 30),
            retry_count=data.get("retry_count", 3),
            description=data.get("description", ""),
            enabled=data.get("enabled", True),
        )

    def _validate_impl(self):
        if not isinstance(self.action_type, ActionType):
            raise ValueError("action_type must be an ActionType enum")
        if self.timeout < 0:
            raise ValueError("timeout cannot be negative")
        if self.retry_count < 0:
            raise ValueError("retry_count cannot be negative")


@dataclass
class ScheduleConfig(BaseModel):
    """调度配置数据模型"""

    enabled: bool = False
    schedule_time: Optional[str] = None  # "HH:MM" 格式
    schedule_days: List[str] = field(default_factory=list)  # ["monday", "tuesday", ...]
    repeat_interval: int = 0  # 重复间隔（秒）
    max_executions: int = 1  # 最大执行次数

    def _to_dict_impl(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "schedule_time": self.schedule_time,
            "schedule_days": self.schedule_days,
            "repeat_interval": self.repeat_interval,
            "max_executions": self.max_executions,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScheduleConfig":
        return cls(
            enabled=data.get("enabled", False),
            schedule_time=data.get("schedule_time"),
            schedule_days=data.get("schedule_days", []),
            repeat_interval=data.get("repeat_interval", 0),
            max_executions=data.get("max_executions", 1),
        )

    def _validate_impl(self):
        if self.schedule_time:
            # 验证时间格式 HH:MM
            try:
                hour, minute = map(int, self.schedule_time.split(":"))
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError("Invalid time format")
            except (ValueError, AttributeError):
                raise ValueError("schedule_time must be in HH:MM format")

        if self.repeat_interval < 0:
            raise ValueError("repeat_interval cannot be negative")
        if self.max_executions < 1:
            raise ValueError("max_executions must be at least 1")


@dataclass
class ExecutionConfig(BaseModel):
    """执行配置数据模型"""

    max_retry_count: int = 3
    timeout_seconds: int = 300
    auto_restart: bool = False
    parallel_execution: bool = False
    execution_order: str = "sequential"  # "sequential" or "parallel"

    def _to_dict_impl(self) -> Dict[str, Any]:
        return {
            "max_retry_count": self.max_retry_count,
            "timeout_seconds": self.timeout_seconds,
            "auto_restart": self.auto_restart,
            "parallel_execution": self.parallel_execution,
            "execution_order": self.execution_order,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionConfig":
        return cls(
            max_retry_count=data.get("max_retry_count", 3),
            timeout_seconds=data.get("timeout_seconds", 300),
            auto_restart=data.get("auto_restart", False),
            parallel_execution=data.get("parallel_execution", False),
            execution_order=data.get("execution_order", "sequential"),
        )

    def _validate_impl(self):
        if self.max_retry_count < 0:
            raise ValueError("max_retry_count cannot be negative")
        if self.timeout_seconds < 0:
            raise ValueError("timeout_seconds cannot be negative")
        if self.execution_order not in ["sequential", "parallel"]:
            raise ValueError("execution_order must be 'sequential' or 'parallel'")


@dataclass
class TaskConfig(BaseModel):
    """重构后的任务配置数据模型"""

    # 基本信息
    name: str
    task_type: TaskType
    description: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM

    # 配置组件
    execution_config: ExecutionConfig = field(default_factory=ExecutionConfig)
    schedule_config: ScheduleConfig = field(default_factory=ScheduleConfig)

    # 操作序列
    actions: List[ActionConfig] = field(default_factory=list)

    # 其他配置
    tags: List[str] = field(default_factory=list)
    custom_params: Dict[str, Any] = field(default_factory=dict)

    # 元数据
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    version: str = "1.0"

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def _to_dict_impl(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "task_type": self.task_type.value,
            "description": self.description,
            "priority": self.priority.value,
            "execution_config": self.execution_config.to_dict(),
            "schedule_config": self.schedule_config.to_dict(),
            "actions": [action.to_dict() for action in self.actions],
            "tags": self.tags,
            "custom_params": self.custom_params,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskConfig":
        # 处理执行配置
        execution_config_data = data.get("execution_config", {})
        execution_config = ExecutionConfig.from_dict(execution_config_data)

        # 处理调度配置
        schedule_config_data = data.get("schedule_config", {})
        schedule_config = ScheduleConfig.from_dict(schedule_config_data)

        # 处理动作配置
        actions_data = data.get("actions", [])
        actions = [ActionConfig.from_dict(action_data) for action_data in actions_data]

        # 处理日期时间
        created_at = None
        if data.get("created_at"):
            created_at_value = data["created_at"]
            if isinstance(created_at_value, str):
                created_at = datetime.fromisoformat(created_at_value)
            elif isinstance(created_at_value, datetime):
                created_at = created_at_value

        updated_at = None
        if data.get("updated_at"):
            updated_at_value = data["updated_at"]
            if isinstance(updated_at_value, str):
                updated_at = datetime.fromisoformat(updated_at_value)
            elif isinstance(updated_at_value, datetime):
                updated_at = updated_at_value

        return cls(
            name=data.get("name", ""),
            task_type=TaskType(data.get("task_type", TaskType.CUSTOM.value)),
            description=data.get("description", ""),
            priority=TaskPriority(data.get("priority", TaskPriority.MEDIUM.value)),
            execution_config=execution_config,
            schedule_config=schedule_config,
            actions=actions,
            tags=data.get("tags", []),
            custom_params=data.get("custom_params", {}),
            created_at=created_at,
            updated_at=updated_at,
            version=data.get("version", "1.0"),
        )

    def _validate_impl(self):
        if not self.name or not self.name.strip():
            raise ValueError("任务名称不能为空")

        if not isinstance(self.task_type, TaskType):
            raise ValueError("task_type must be a TaskType enum")

        if not isinstance(self.priority, TaskPriority):
            raise ValueError("priority must be a TaskPriority enum")

        # 验证子配置
        self.execution_config._validate_impl()
        self.schedule_config._validate_impl()

        # 验证动作配置
        for action in self.actions:
            action._validate_impl()

    def add_action(self, action: ActionConfig):
        """添加动作配置"""
        action._validate_impl()
        self.actions.append(action)
        self.updated_at = datetime.now()

    def remove_action(self, index: int):
        """移除动作配置"""
        if 0 <= index < len(self.actions):
            self.actions.pop(index)
            self.updated_at = datetime.now()

    def update_action(self, index: int, action: ActionConfig):
        """更新动作配置"""
        if 0 <= index < len(self.actions):
            action._validate_impl()
            self.actions[index] = action
            self.updated_at = datetime.now()


@dataclass
class Task(BaseModel):
    """重构后的任务实体模型"""

    # 基本信息
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default_user"
    config: TaskConfig = field(
        default_factory=lambda: TaskConfig(name="", task_type=TaskType.CUSTOM)
    )

    # 状态信息
    status: TaskStatus = TaskStatus.PENDING

    # 执行统计
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0

    # 时间戳
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_executed_at: Optional[datetime] = None

    # 执行结果
    last_error: Optional[str] = None
    execution_log: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def _to_dict_impl(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "user_id": self.user_id,
            "config": self.config.to_dict(),
            "status": self.status.value,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_executed_at": (
                self.last_executed_at.isoformat() if self.last_executed_at else None
            ),
            "last_error": self.last_error,
            "execution_log": self.execution_log,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        # 处理配置
        config_data = data.get("config", {})
        config = TaskConfig.from_dict(config_data)

        # 处理日期时间
        created_at = None
        if data.get("created_at"):
            created_at_value = data["created_at"]
            if isinstance(created_at_value, str):
                created_at = datetime.fromisoformat(created_at_value)
            elif isinstance(created_at_value, datetime):
                created_at = created_at_value

        updated_at = None
        if data.get("updated_at"):
            updated_at_value = data["updated_at"]
            if isinstance(updated_at_value, str):
                updated_at = datetime.fromisoformat(updated_at_value)
            elif isinstance(updated_at_value, datetime):
                updated_at = updated_at_value

        last_executed_at = None
        if data.get("last_executed_at"):
            last_executed_at_value = data["last_executed_at"]
            if isinstance(last_executed_at_value, str):
                last_executed_at = datetime.fromisoformat(last_executed_at_value)
            elif isinstance(last_executed_at_value, datetime):
                last_executed_at = last_executed_at_value

        return cls(
            task_id=data.get("task_id", str(uuid.uuid4())),
            user_id=data.get("user_id", "default_user"),
            config=config,
            status=TaskStatus(data.get("status", TaskStatus.PENDING.value)),
            execution_count=data.get("execution_count", 0),
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0),
            created_at=created_at,
            updated_at=updated_at,
            last_executed_at=last_executed_at,
            last_error=data.get("last_error"),
            execution_log=data.get("execution_log", []),
        )

    def _validate_impl(self):
        if not self.task_id:
            raise ValueError("task_id cannot be empty")

        if not self.user_id:
            raise ValueError("user_id cannot be empty")

        if not isinstance(self.status, TaskStatus):
            raise ValueError("status must be a TaskStatus enum")

        # 验证配置
        self.config._validate_impl()

        # 验证统计数据
        if self.execution_count < 0:
            raise ValueError("execution_count cannot be negative")
        if self.success_count < 0:
            raise ValueError("success_count cannot be negative")
        if self.failure_count < 0:
            raise ValueError("failure_count cannot be negative")

    def update_status(self, new_status: TaskStatus, error_message: str = None):
        """更新任务状态"""
        self.status = new_status
        self.updated_at = datetime.now()

        if error_message:
            self.last_error = error_message
            self.execution_log.append(
                f"[{datetime.now().isoformat()}] ERROR: {error_message}"
            )

    def record_execution(self, success: bool, message: str = None):
        """记录执行结果"""
        self.execution_count += 1
        self.last_executed_at = datetime.now()
        self.updated_at = datetime.now()

        if success:
            self.success_count += 1
            log_message = f"[{datetime.now().isoformat()}] SUCCESS: {message or 'Execution completed successfully'}"
        else:
            self.failure_count += 1
            self.last_error = message
            log_message = f"[{datetime.now().isoformat()}] FAILURE: {message or 'Execution failed'}"

        self.execution_log.append(log_message)

        # 限制日志长度
        if len(self.execution_log) > 100:
            self.execution_log = self.execution_log[-100:]

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.execution_count == 0:
            return 0.0
        return self.success_count / self.execution_count

    @property
    def name(self) -> str:
        """任务名称"""
        return self.config.name

    @property
    def task_type(self) -> TaskType:
        """任务类型"""
        return self.config.task_type

    @property
    def priority(self) -> TaskPriority:
        """任务优先级"""
        return self.config.priority
