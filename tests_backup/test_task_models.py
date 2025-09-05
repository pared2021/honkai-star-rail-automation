# -*- coding: utf-8 -*-
"""
任务模型单元测试

测试统一的TaskConfig和Task模型的功能，包括：
- 模型创建和验证
- 序列化和反序列化
- 状态更新和属性访问
- 便利函数
"""

from datetime import datetime
import json

import pytest

from src.models.task_models import (
    Task,
    TaskConfig,
    TaskPriority,
    TaskStatus,
    TaskType,
    create_task,
    create_task_config,
)


class TestTaskConfig:
    """TaskConfig模型测试"""

    def test_create_basic_task_config(self):
        """测试创建基本任务配置"""
        config = TaskConfig(
            name="测试任务",
            task_type=TaskType.DAILY_MISSION,
            description="这是一个测试任务",
        )

        assert config.name == "测试任务"
        assert config.task_type == TaskType.DAILY_MISSION.value
        assert config.description == "这是一个测试任务"
        assert config.priority == TaskPriority.MEDIUM.value  # 默认值
        assert config.max_retry_count == 3  # 默认值
        assert config.timeout_seconds == 300  # 默认值
        assert config.schedule_enabled is False  # 默认值
        assert config.actions == []  # 默认值
        assert config.tags == []  # 默认值
        assert config.custom_params == {}  # 默认值

    def test_create_full_task_config(self):
        """测试创建完整任务配置"""
        config = TaskConfig(
            name="完整任务",
            task_type=TaskType.COMBAT,
            description="完整的任务配置",
            priority=TaskPriority.HIGH,
            max_retry_count=5,
            timeout_seconds=600,
            schedule_enabled=True,
            actions=[{"type": "click", "target": "button"}],
            tags=["重要", "紧急"],
            custom_params={"level": 10, "difficulty": "hard"},
        )

        assert config.name == "完整任务"
        assert config.task_type == TaskType.COMBAT.value
        assert config.priority == TaskPriority.HIGH.value
        assert config.max_retry_count == 5
        assert config.timeout_seconds == 600
        assert config.schedule_enabled is True
        assert len(config.actions) == 1
        assert len(config.tags) == 2
        assert config.custom_params["level"] == 10

    def test_task_config_serialization(self):
        """测试任务配置序列化"""
        config = TaskConfig(
            name="序列化测试", task_type=TaskType.EXPLORATION, priority=TaskPriority.LOW
        )

        # 测试to_dict
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert config_dict["name"] == "序列化测试"
        assert config_dict["task_type"] == "exploration"
        assert config_dict["priority"] == 1

        # 测试from_dict
        restored_config = TaskConfig.from_dict(config_dict)
        assert restored_config.name == config.name
        assert restored_config.task_type == config.task_type
        assert restored_config.priority == config.priority

    def test_task_config_json_serialization(self):
        """测试任务配置JSON序列化"""
        config = TaskConfig(
            name="JSON测试", task_type=TaskType.WEEKLY_MISSION, tags=["测试", "JSON"]
        )

        # 测试to_json
        json_str = config.to_json()
        assert isinstance(json_str, str)

        # 验证JSON格式
        parsed = json.loads(json_str)
        assert parsed["name"] == "JSON测试"

        # 测试from_json
        restored_config = TaskConfig.from_json(json_str)
        assert restored_config.name == config.name
        assert restored_config.task_type == config.task_type
        assert restored_config.tags == config.tags

    def test_create_task_config_convenience_function(self):
        """测试便利函数create_task_config"""
        config = create_task_config(
            name="便利函数测试",
            task_type=TaskType.CUSTOM,
            description="使用便利函数创建",
            max_retry_count=10,
        )

        assert isinstance(config, TaskConfig)
        assert config.name == "便利函数测试"
        assert config.task_type == TaskType.CUSTOM.value
        assert config.max_retry_count == 10


class TestTask:
    """Task模型测试"""

    def test_create_basic_task(self):
        """测试创建基本任务"""
        config = TaskConfig(name="基本任务", task_type=TaskType.DAILY_MISSION)

        task = Task(config=config)

        assert task.config == config
        assert task.status == TaskStatus.PENDING.value  # 默认值
        assert task.user_id == "default_user"  # 默认值
        assert task.retry_count == 0  # 默认值
        assert task.last_error is None  # 默认值
        assert task.execution_result is None  # 默认值
        assert isinstance(task.task_id, str)
        assert len(task.task_id) > 0
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)

    def test_task_properties(self):
        """测试任务属性"""
        config = TaskConfig(
            name="属性测试", task_type=TaskType.COMBAT, priority=TaskPriority.URGENT
        )

        task = Task(config=config, user_id="test_user")

        # 测试属性访问
        assert task.name == "属性测试"
        assert task.task_type == TaskType.COMBAT.value
        assert task.priority == TaskPriority.URGENT.value
        assert task.user_id == "test_user"

        # 测试状态检查属性
        assert task.is_running is False
        assert task.is_completed is False
        assert task.is_failed is False

    def test_task_status_update(self):
        """测试任务状态更新"""
        config = TaskConfig(name="状态测试", task_type=TaskType.EXPLORATION)
        task = Task(config=config)

        original_updated_at = task.updated_at

        # 测试开始运行
        task.update_status(TaskStatus.RUNNING)
        assert task.status == TaskStatus.RUNNING.value
        assert task.is_running is True
        assert task.started_at is not None
        assert task.updated_at > original_updated_at

        # 测试完成
        task.update_status(TaskStatus.COMPLETED)
        assert task.status == TaskStatus.COMPLETED.value
        assert task.is_completed is True
        assert task.completed_at is not None

        # 测试失败状态
        task.update_status(TaskStatus.FAILED, "测试错误")
        assert task.status == TaskStatus.FAILED.value
        assert task.is_failed is True
        assert task.last_error == "测试错误"

    def test_task_retry_functionality(self):
        """测试任务重试功能"""
        config = TaskConfig(
            name="重试测试", task_type=TaskType.CUSTOM, max_retry_count=3
        )
        task = Task(config=config)

        # 初始状态
        assert task.retry_count == 0
        assert task.can_retry() is True

        # 增加重试次数
        task.increment_retry()
        assert task.retry_count == 1
        assert task.can_retry() is True

        # 达到最大重试次数
        task.increment_retry()
        task.increment_retry()
        assert task.retry_count == 3
        assert task.can_retry() is False

    def test_task_execution_result(self):
        """测试任务执行结果"""
        config = TaskConfig(name="结果测试", task_type=TaskType.DAILY_MISSION)
        task = Task(config=config)

        result = {
            "success": True,
            "data": {"score": 100, "time": 30},
            "message": "任务执行成功",
        }

        task.set_execution_result(result)
        assert task.execution_result == result
        assert task.execution_result["success"] is True
        assert task.execution_result["data"]["score"] == 100

    def test_task_duration(self):
        """测试任务执行时长计算"""
        config = TaskConfig(name="时长测试", task_type=TaskType.COMBAT)
        task = Task(config=config)

        # 未开始时
        assert task.duration_seconds is None

        # 设置开始和结束时间
        start_time = datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime(2024, 1, 1, 10, 5, 30)  # 5分30秒后

        task.started_at = start_time
        task.completed_at = end_time

        duration = task.duration_seconds
        assert duration == 330.0  # 5分30秒 = 330秒

    def test_task_serialization(self):
        """测试任务序列化"""
        config = TaskConfig(
            name="序列化任务",
            task_type=TaskType.WEEKLY_MISSION,
            priority=TaskPriority.HIGH,
        )
        task = Task(config=config, user_id="serialization_user")

        # 测试to_dict
        task_dict = task.to_dict()
        assert isinstance(task_dict, dict)
        assert task_dict["user_id"] == "serialization_user"
        assert "config" in task_dict
        assert task_dict["config"]["name"] == "序列化任务"

        # 测试from_dict
        restored_task = Task.from_dict(task_dict)
        assert restored_task.user_id == task.user_id
        assert restored_task.config.name == task.config.name
        assert restored_task.task_id == task.task_id

    def test_create_task_convenience_function(self):
        """测试便利函数create_task"""
        config = TaskConfig(name="便利任务", task_type=TaskType.EXPLORATION)
        task = create_task(config, user_id="convenience_user")

        assert isinstance(task, Task)
        assert task.config == config
        assert task.user_id == "convenience_user"


class TestEnums:
    """枚举类型测试"""

    def test_task_type_enum(self):
        """测试TaskType枚举"""
        assert TaskType.DAILY_MISSION.value == "daily_mission"
        assert TaskType.WEEKLY_MISSION.value == "weekly_mission"
        assert TaskType.EXPLORATION.value == "exploration"
        assert TaskType.COMBAT.value == "combat"
        assert TaskType.CUSTOM.value == "custom"

    def test_task_status_enum(self):
        """测试TaskStatus枚举"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"

    def test_task_priority_enum(self):
        """测试TaskPriority枚举"""
        assert TaskPriority.LOW.value == 1
        assert TaskPriority.MEDIUM.value == 2
        assert TaskPriority.HIGH.value == 3
        assert TaskPriority.URGENT.value == 4


if __name__ == "__main__":
    # 运行测试的简单方法
    pytest.main([__file__, "-v"])
