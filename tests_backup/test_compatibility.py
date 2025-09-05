# -*- coding: utf-8 -*-
"""
兼容性测试 - 验证新统一模型与旧模型的兼容性
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from src.adapters.model_adapter import ModelAdapter

# 导入新的统一模型
from src.models.task_models import (
    Task as NewTask,
    TaskConfig as NewTaskConfig,
    TaskPriority,
    TaskStatus,
    TaskType,
)


# 模拟旧的dataclass模型（来自task_manager.py）
@dataclass
class OldTaskConfig:
    """旧的任务配置数据结构"""

    name: str
    task_type: str  # 字符串类型
    description: str = ""
    priority: str = "medium"  # 字符串类型
    max_retry_count: int = 3
    timeout_seconds: int = 300
    auto_restart: bool = False
    schedule_enabled: bool = False
    schedule_time: Optional[str] = None
    schedule_days: List[str] = None
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
        if self.schedule_days is None:
            self.schedule_days = []


@dataclass
class OldTask:
    """旧的任务实体模型"""

    task_id: str
    user_id: str
    config: OldTaskConfig
    status: str  # 字符串类型
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    last_error: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None


def test_old_taskconfig_conversion():
    """测试旧TaskConfig转换为新TaskConfig"""
    print("\n=== 测试旧TaskConfig转换 ===")

    # 创建旧的TaskConfig
    old_config = OldTaskConfig(
        name="测试任务",
        task_type="daily_mission",
        description="这是一个测试任务",
        priority="high",
        max_retry_count=5,
        timeout_seconds=600,
        auto_restart=True,
        schedule_enabled=True,
        schedule_time="09:00",
        schedule_days=["monday", "friday"],
        actions=[{"type": "click", "target": "button"}],
        tags=["test", "automation"],
        custom_params={"param1": "value1"},
    )

    print(f"旧配置: {old_config}")

    # 转换为新模型
    try:
        new_config = ModelAdapter.dataclass_to_pydantic(old_config, NewTaskConfig)
        print(f"转换成功: {new_config}")
        print(f"新配置类型: {type(new_config)}")
        print(f"任务类型: {new_config.task_type} (类型: {type(new_config.task_type)})")
        print(f"优先级: {new_config.priority} (类型: {type(new_config.priority)})")

        # 验证字段映射
        assert new_config.name == old_config.name
        assert new_config.task_type == TaskType.DAILY_MISSION.value
        assert new_config.priority == TaskPriority.HIGH.value
        assert new_config.max_retry_count == old_config.max_retry_count

        print("✓ 字段映射验证通过")

    except Exception as e:
        print(f"✗ 转换失败: {e}")
        return False

    return True


def test_old_task_conversion():
    """测试旧Task转换为新Task"""
    print("\n=== 测试旧Task转换 ===")

    # 创建旧的Task
    old_config = OldTaskConfig(
        name="日常任务", task_type="daily_mission", priority="medium"
    )

    old_task = OldTask(
        task_id="test-123",
        user_id="user-456",
        config=old_config,
        status="running",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        retry_count=1,
        last_error="网络超时",
        execution_result={"step1": "completed"},
    )

    print(f"旧任务: {old_task}")

    # 转换为新模型
    try:
        new_task = ModelAdapter.dataclass_to_pydantic(old_task, NewTask)
        print(f"转换成功: {new_task}")
        print(f"任务状态: {new_task.status} (类型: {type(new_task.status)})")

        # 验证字段
        assert new_task.task_id == old_task.task_id
        assert new_task.user_id == old_task.user_id
        assert new_task.status == TaskStatus.RUNNING.value
        assert new_task.retry_count == old_task.retry_count

        print("✓ 任务转换验证通过")

    except Exception as e:
        print(f"✗ 转换失败: {e}")
        return False

    return True


def test_dict_conversion():
    """测试字典数据转换"""
    print("\n=== 测试字典数据转换 ===")

    # 模拟从数据库或API获取的字典数据
    config_dict = {
        "name": "探索任务",
        "task_type": "exploration",
        "description": "自动探索地图",
        "priority": "urgent",
        "max_retry_count": 2,
        "timeout_seconds": 1200,
        "schedule_enabled": False,
    }

    task_dict = {
        "task_id": "dict-test-789",
        "user_id": "dict-user-123",
        "config": config_dict,
        "status": "pending",
        "created_at": "2024-01-15T10:30:00",
        "updated_at": "2024-01-15T10:30:00",
        "retry_count": 0,
    }

    print(f"配置字典: {config_dict}")
    print(f"任务字典: {task_dict}")

    try:
        # 转换配置
        new_config = ModelAdapter.dict_to_model(config_dict, NewTaskConfig)
        print(f"配置转换成功: {new_config}")

        # 转换任务
        new_task = ModelAdapter.dict_to_model(task_dict, NewTask)
        print(f"任务转换成功: {new_task}")

        # 验证
        assert new_config.task_type == TaskType.EXPLORATION.value
        assert new_config.priority == TaskPriority.URGENT.value
        assert new_task.status == TaskStatus.PENDING.value

        print("✓ 字典转换验证通过")

    except Exception as e:
        print(f"✗ 字典转换失败: {e}")
        return False

    return True


def test_batch_conversion():
    """测试批量转换"""
    print("\n=== 测试批量转换 ===")

    # 创建多个旧配置
    old_configs = [
        OldTaskConfig(name="任务1", task_type="daily_mission", priority="low"),
        OldTaskConfig(name="任务2", task_type="weekly_mission", priority="high"),
        OldTaskConfig(name="任务3", task_type="combat", priority="medium"),
    ]

    print(f"旧配置列表: {len(old_configs)} 个")

    try:
        new_configs = ModelAdapter.batch_convert(old_configs, NewTaskConfig)
        print(f"批量转换成功: {len(new_configs)} 个")

        # 验证每个转换结果
        for i, (old, new) in enumerate(zip(old_configs, new_configs)):
            assert new.name == old.name
            print(f"  配置{i+1}: {old.name} -> {new.name} ✓")

        print("✓ 批量转换验证通过")

    except Exception as e:
        print(f"✗ 批量转换失败: {e}")
        return False

    return True


def test_error_handling():
    """测试错误处理"""
    print("\n=== 测试错误处理 ===")

    # 测试无效的枚举值
    invalid_config_dict = {
        "name": "无效任务",
        "task_type": "invalid_type",  # 无效的任务类型
        "priority": "super_urgent",  # 无效的优先级
    }

    print(f"无效配置字典: {invalid_config_dict}")

    try:
        new_config = ModelAdapter.dict_to_model(invalid_config_dict, NewTaskConfig)
        print(f"意外成功: {new_config}")
        return False  # 应该失败的
    except Exception as e:
        print(f"✓ 正确捕获错误: {e}")

    # 测试缺少必需字段
    incomplete_dict = {
        "task_type": "daily_mission"
        # 缺少name字段
    }

    try:
        new_config = ModelAdapter.dict_to_model(incomplete_dict, NewTaskConfig)
        print(f"意外成功: {new_config}")
        return False  # 应该失败的
    except Exception as e:
        print(f"✓ 正确捕获缺少字段错误: {e}")

    return True


def test_serialization_compatibility():
    """测试序列化兼容性"""
    print("\n=== 测试序列化兼容性 ===")

    # 创建新模型
    new_config = NewTaskConfig(
        name="序列化测试",
        task_type=TaskType.CUSTOM,
        priority=TaskPriority.HIGH,
        max_retries=3,
    )

    new_task = NewTask(
        task_id="serial-test",
        user_id="serial-user",
        config=new_config,
        status=TaskStatus.COMPLETED,
    )

    try:
        # 测试JSON序列化
        config_json = new_config.to_json()
        task_json = new_task.to_json()

        print(f"配置JSON长度: {len(config_json)}")
        print(f"任务JSON长度: {len(task_json)}")

        # 测试反序列化
        restored_config = NewTaskConfig.from_json(config_json)
        restored_task = NewTask.from_json(task_json)

        # 验证
        assert restored_config.name == new_config.name
        assert restored_config.task_type == new_config.task_type
        assert restored_task.task_id == new_task.task_id
        assert restored_task.status == new_task.status

        print("✓ 序列化兼容性验证通过")

    except Exception as e:
        print(f"✗ 序列化测试失败: {e}")
        return False

    return True


def main():
    """运行所有兼容性测试"""
    print("开始兼容性测试...")

    tests = [
        test_old_taskconfig_conversion,
        test_old_task_conversion,
        test_dict_conversion,
        test_batch_conversion,
        test_error_handling,
        test_serialization_compatibility,
    ]

    passed = 0
    total = len(tests)

    for test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_func.__name__} 通过")
            else:
                print(f"✗ {test_func.__name__} 失败")
        except Exception as e:
            print(f"✗ {test_func.__name__} 异常: {e}")

    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")
    print(f"成功率: {passed/total*100:.1f}%")

    if passed == total:
        print("🎉 所有兼容性测试通过！")
        return True
    else:
        print("❌ 部分测试失败，需要修复")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
