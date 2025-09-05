#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的集成测试脚本
验证重构后的架构是否正常工作
"""

import os
import sys

# 添加src目录到Python路径
src_path = os.path.join(os.path.dirname(__file__), "src")
sys.path.insert(0, src_path)


def test_basic_imports():
    """测试基本导入"""
    print("测试基本导入...")

    try:
        # 测试枚举导入
        from core.enums import TaskPriority, TaskStatus, TaskType

        print("✓ 枚举导入成功")

        # 测试数据模型导入
        from models.unified_models import TaskConfig

        print("✓ TaskConfig导入成功")

        # 测试数据库管理器导入
        from database.db_manager import DatabaseManager

        print("✓ DatabaseManager导入成功")

        # 测试适配器导入
        from adapters.task_manager_adapter import TaskManagerAdapter

        print("✓ TaskManagerAdapter导入成功")

        return True

    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False


def test_task_config_creation():
    """测试TaskConfig创建"""
    print("\n测试TaskConfig创建...")

    try:
        from core.enums import TaskPriority, TaskType
        from models.unified_models import TaskConfig

        # 创建TaskConfig实例
        config = TaskConfig(
            name="测试任务", task_type=TaskType.AUTOMATION, priority=TaskPriority.MEDIUM
        )

        print(f"✓ TaskConfig创建成功: {config.name}")
        print(f"  - 类型: {config.task_type}")
        print(f"  - 优先级: {config.priority}")
        print(f"  - 启用状态: {config.enabled}")

        # 测试序列化
        config_dict = config.to_dict()
        print(f"✓ 序列化成功: {len(config_dict)} 个字段")

        return True

    except Exception as e:
        print(f"✗ TaskConfig创建失败: {e}")
        return False


def test_database_manager():
    """测试数据库管理器"""
    print("\n测试数据库管理器...")

    try:
        from database.db_manager import DatabaseManager

        # 创建数据库管理器实例
        db_manager = DatabaseManager(":memory:")  # 使用内存数据库
        print("✓ DatabaseManager创建成功")

        # 测试初始化
        db_manager.initialize()
        print("✓ 数据库初始化成功")

        return True

    except Exception as e:
        print(f"✗ 数据库管理器测试失败: {e}")
        return False


def test_task_manager_adapter():
    """测试TaskManagerAdapter"""
    print("\n测试TaskManagerAdapter...")

    try:
        from adapters.task_manager_adapter import TaskManagerAdapter
        from database.db_manager import DatabaseManager

        # 创建数据库管理器
        db_manager = DatabaseManager(":memory:")
        db_manager.initialize()

        # 创建适配器
        adapter = TaskManagerAdapter(db_manager)
        print("✓ TaskManagerAdapter创建成功")

        # 检查方法是否存在
        if hasattr(adapter, "get_task_sync"):
            print("✓ get_task_sync方法存在")
        else:
            print("✗ get_task_sync方法不存在")
            return False

        return True

    except Exception as e:
        print(f"✗ TaskManagerAdapter测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("=== 架构重构集成测试 ===")

    tests = [
        test_basic_imports,
        test_task_config_creation,
        test_database_manager,
        test_task_manager_adapter,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        else:
            print("\n测试失败，停止后续测试")
            break

    print(f"\n=== 测试结果: {passed}/{total} 通过 ===")

    if passed == total:
        print("🎉 所有测试通过！架构重构成功！")
        return True
    else:
        print("❌ 部分测试失败，需要进一步修复")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
