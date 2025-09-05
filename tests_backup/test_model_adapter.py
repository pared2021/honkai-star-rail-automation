# -*- coding: utf-8 -*-
"""
模型适配器单元测试

测试ModelAdapter的各种转换功能，包括：
- dataclass到Pydantic的转换
- 字典到模型的转换
- 枚举值的标准化
- 批量转换功能
- 错误处理
"""

from dataclasses import dataclass
from typing import Any, Dict, List

import pytest

from src.adapters.model_adapter import (
    ModelAdapter,
    batch_convert_tasks,
    safe_convert_to_task,
    safe_convert_to_task_config,
)
from src.models.task_models import Task, TaskConfig, TaskPriority, TaskStatus, TaskType


# 模拟旧的dataclass定义
@dataclass
class LegacyTaskConfig:
    """模拟旧的TaskConfig dataclass"""

    name: str
    task_type: str
    description: str = ""
    priority: int = 2
    max_retry_count: int = 3
    timeout_seconds: int = 300
    schedule_enabled: bool = False
    actions: List[Dict[str, Any]] = None
    tags: List[str] = None
    custom_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.actions is None:
            self.actions = []
        if self.tags is None:
            self.tags = []
        if self.custom_params is None:
            self.custom_params = {}


@dataclass
class LegacyTask:
    """模拟旧的Task dataclass"""

    task_id: str
    user_id: str
    config: LegacyTaskConfig
    status: str = "pending"
    retry_count: int = 0
    last_error: str = None


class TestModelAdapter:
    """ModelAdapter测试"""

    def test_dataclass_to_pydantic_basic(self):
        """测试基本的dataclass到Pydantic转换"""
        legacy_config = LegacyTaskConfig(
            name="测试任务", task_type="daily_mission", description="dataclass转换测试"
        )

        converted = ModelAdapter.dataclass_to_pydantic(legacy_config)

        assert isinstance(converted, TaskConfig)
        assert converted.name == "测试任务"
        assert converted.task_type == TaskType.DAILY_MISSION.value
        assert converted.description == "dataclass转换测试"
        assert converted.priority == TaskPriority.MEDIUM.value  # 默认值

    def test_dict_to_task_config(self):
        """测试字典到TaskConfig的转换"""
        config_dict = {
            "name": "字典任务",
            "task_type": "combat",
            "description": "从字典创建",
            "priority": 3,
            "max_retry_count": 5,
            "tags": ["重要", "紧急"],
        }

        converted = ModelAdapter.dict_to_task_config(config_dict)

        assert isinstance(converted, TaskConfig)
        assert converted.name == "字典任务"
        assert converted.task_type == TaskType.COMBAT.value
        assert converted.priority == TaskPriority.HIGH.value
        assert converted.max_retry_count == 5
        assert converted.tags == ["重要", "紧急"]

    def test_dict_to_task(self):
        """测试字典到Task的转换"""
        task_dict = {
            "task_id": "test-task-123",
            "user_id": "test_user",
            "config": {"name": "嵌套任务", "task_type": "exploration", "priority": 1},
            "status": "running",
            "retry_count": 2,
        }

        converted = ModelAdapter.dict_to_task(task_dict)

        assert isinstance(converted, Task)
        assert converted.task_id == "test-task-123"
        assert converted.user_id == "test_user"
        assert isinstance(converted.config, TaskConfig)
        assert converted.config.name == "嵌套任务"
        assert converted.config.task_type == TaskType.EXPLORATION.value
        assert converted.status == TaskStatus.RUNNING.value
        assert converted.retry_count == 2

    def test_ensure_task_config_with_existing_object(self):
        """测试ensure_task_config处理已存在的TaskConfig对象"""
        original_config = TaskConfig(name="原始任务", task_type=TaskType.WEEKLY_MISSION)

        result = ModelAdapter.ensure_task_config(original_config)

        assert result is original_config  # 应该返回同一个对象

    def test_ensure_task_config_with_dict(self):
        """测试ensure_task_config处理字典"""
        config_dict = {"name": "字典转换", "task_type": "custom", "priority": "HIGH"}

        result = ModelAdapter.ensure_task_config(config_dict)

        assert isinstance(result, TaskConfig)
        assert result.name == "字典转换"
        assert result.task_type == TaskType.CUSTOM.value
        assert result.priority == TaskPriority.HIGH.value

    def test_ensure_task_config_with_dataclass(self):
        """测试ensure_task_config处理dataclass"""
        legacy_config = LegacyTaskConfig(
            name="dataclass转换", task_type="daily_mission", priority=4
        )

        result = ModelAdapter.ensure_task_config(legacy_config)

        assert isinstance(result, TaskConfig)
        assert result.name == "dataclass转换"
        assert result.task_type == TaskType.DAILY_MISSION.value
        assert result.priority == TaskPriority.URGENT.value

    def test_normalize_enum_values_task_type(self):
        """测试TaskType枚举值标准化"""
        # 测试字符串值
        data1 = {"task_type": "daily_mission"}
        normalized1 = ModelAdapter._normalize_enum_values(data1)
        assert normalized1["task_type"] == TaskType.DAILY_MISSION.value

        # 测试枚举名称
        data2 = {"task_type": "COMBAT"}
        normalized2 = ModelAdapter._normalize_enum_values(data2)
        assert normalized2["task_type"] == TaskType.COMBAT.value

    def test_normalize_enum_values_task_status(self):
        """测试TaskStatus枚举值标准化"""
        data = {"status": "completed"}
        normalized = ModelAdapter._normalize_enum_values(data)
        assert normalized["status"] == TaskStatus.COMPLETED.value

    def test_normalize_enum_values_task_priority(self):
        """测试TaskPriority枚举值标准化"""
        # 测试数值
        data1 = {"priority": 3}
        normalized1 = ModelAdapter._normalize_enum_values(data1)
        assert normalized1["priority"] == TaskPriority.HIGH.value

        # 测试字符串名称
        data2 = {"priority": "low"}
        normalized2 = ModelAdapter._normalize_enum_values(data2)
        assert normalized2["priority"] == TaskPriority.LOW.value

    def test_convert_legacy_task_list(self):
        """测试转换旧格式任务列表"""
        legacy_tasks = [
            {
                "task_id": "task1",
                "user_id": "user1",
                "config": {"name": "任务1", "task_type": "daily_mission"},
                "status": "pending",
            },
            {
                "task_id": "task2",
                "user_id": "user2",
                "config": {"name": "任务2", "task_type": "combat"},
                "status": "completed",
            },
        ]

        converted_tasks = ModelAdapter.convert_legacy_task_list(legacy_tasks)

        assert len(converted_tasks) == 2
        assert all(isinstance(task, Task) for task in converted_tasks)
        assert converted_tasks[0].task_id == "task1"
        assert converted_tasks[1].config.name == "任务2"

    def test_validation_success(self):
        """测试转换验证成功的情况"""
        original_data = {"name": "验证任务", "task_type": "exploration", "priority": 2}

        converted = ModelAdapter.dict_to_task_config(original_data)
        is_valid = ModelAdapter.validate_conversion(original_data, converted)

        assert is_valid is True

    def test_error_handling_invalid_data(self):
        """测试错误处理 - 无效数据"""
        invalid_data = {
            "name": "错误任务",
            "task_type": "invalid_type",  # 无效的任务类型
        }

        with pytest.raises(ValueError):
            ModelAdapter.dict_to_task_config(invalid_data)

    def test_error_handling_missing_required_fields(self):
        """测试错误处理 - 缺少必需字段"""
        incomplete_data = {
            "description": "缺少必需字段"
            # 缺少name和task_type
        }

        with pytest.raises(ValueError):
            ModelAdapter.dict_to_task_config(incomplete_data)


class TestConvenienceFunctions:
    """便利函数测试"""

    def test_safe_convert_to_task_config_success(self):
        """测试安全转换TaskConfig成功"""
        config_dict = {"name": "安全转换", "task_type": "weekly_mission"}

        result = safe_convert_to_task_config(config_dict)

        assert result is not None
        assert isinstance(result, TaskConfig)
        assert result.name == "安全转换"

    def test_safe_convert_to_task_config_failure(self):
        """测试安全转换TaskConfig失败"""
        invalid_data = {"invalid": "data"}

        result = safe_convert_to_task_config(invalid_data)

        assert result is None

    def test_safe_convert_to_task_success(self):
        """测试安全转换Task成功"""
        task_dict = {
            "task_id": "safe-task",
            "user_id": "safe_user",
            "config": {"name": "安全任务", "task_type": "custom"},
        }

        result = safe_convert_to_task(task_dict)

        assert result is not None
        assert isinstance(result, Task)
        assert result.task_id == "safe-task"

    def test_safe_convert_to_task_failure(self):
        """测试安全转换Task失败"""
        invalid_data = {"invalid": "task_data"}

        result = safe_convert_to_task(invalid_data)

        assert result is None

    def test_batch_convert_tasks_mixed_results(self):
        """测试批量转换任务 - 混合结果"""
        mixed_tasks = [
            {  # 有效任务
                "task_id": "valid1",
                "user_id": "user1",
                "config": {"name": "有效任务1", "task_type": "daily_mission"},
            },
            {"invalid": "data"},  # 无效任务
            {  # 有效任务
                "task_id": "valid2",
                "user_id": "user2",
                "config": {"name": "有效任务2", "task_type": "combat"},
            },
        ]

        success_list, failed_list = batch_convert_tasks(mixed_tasks)

        assert len(success_list) == 2
        assert len(failed_list) == 1
        assert all(isinstance(task, Task) for task in success_list)
        assert failed_list[0][0] == 1  # 失败的是索引1的任务


class TestComplexScenarios:
    """复杂场景测试"""

    def test_nested_dataclass_conversion(self):
        """测试嵌套dataclass转换"""
        legacy_config = LegacyTaskConfig(
            name="嵌套测试",
            task_type="exploration",
            actions=[{"type": "move", "direction": "north"}],
            custom_params={"level": 5, "items": ["sword", "potion"]},
        )

        legacy_task = LegacyTask(
            task_id="nested-task",
            user_id="nested_user",
            config=legacy_config,
            status="running",
        )

        converted_task = ModelAdapter.ensure_task(legacy_task)

        assert isinstance(converted_task, Task)
        assert converted_task.task_id == "nested-task"
        assert isinstance(converted_task.config, TaskConfig)
        assert converted_task.config.name == "嵌套测试"
        assert converted_task.status == TaskStatus.RUNNING.value
        assert len(converted_task.config.actions) == 1
        assert converted_task.config.custom_params["level"] == 5

    def test_enum_edge_cases(self):
        """测试枚举边界情况"""
        # 测试大小写不敏感
        data = {"task_type": "DAILY_MISSION", "status": "PENDING", "priority": "medium"}

        normalized = ModelAdapter._normalize_enum_values(data)

        assert normalized["task_type"] == TaskType.DAILY_MISSION.value
        assert normalized["status"] == TaskStatus.PENDING.value
        assert normalized["priority"] == TaskPriority.MEDIUM.value

    def test_partial_data_conversion(self):
        """测试部分数据转换"""
        # 只包含必需字段的最小数据
        minimal_config = {"name": "最小配置", "task_type": "custom"}

        converted = ModelAdapter.dict_to_task_config(minimal_config)

        assert converted.name == "最小配置"
        assert converted.task_type == TaskType.CUSTOM.value
        # 验证默认值
        assert converted.priority == TaskPriority.MEDIUM.value
        assert converted.max_retry_count == 3
        assert converted.actions == []


if __name__ == "__main__":
    # 运行测试的简单方法
    pytest.main([__file__, "-v"])
