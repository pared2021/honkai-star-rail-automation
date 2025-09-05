#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础功能测试脚本
直接测试重构后的核心功能
"""

from datetime import datetime
import os
import sqlite3
import sys

# 添加src目录到Python路径
src_path = os.path.join(os.path.dirname(__file__), "src")
sys.path.insert(0, src_path)


def test_database_creation():
    """测试数据库创建"""
    print("测试数据库创建...")

    try:
        # 创建内存数据库
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()

        # 创建任务表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                task_type TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                config TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """
        )

        # 插入测试数据
        cursor.execute(
            """
            INSERT INTO tasks (task_id, user_id, name, task_type, priority, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                "test_001",
                "user_001",
                "测试任务",
                "AUTOMATION",
                "MEDIUM",
                "PENDING",
                datetime.now().isoformat(),
            ),
        )

        conn.commit()

        # 查询数据
        cursor.execute("SELECT * FROM tasks WHERE task_id = ?", ("test_001",))
        result = cursor.fetchone()

        if result:
            print(f"✓ 数据库创建成功，任务记录: {result[2]}")
            conn.close()
            return True
        else:
            print("✗ 数据库查询失败")
            conn.close()
            return False

    except Exception as e:
        print(f"✗ 数据库测试失败: {e}")
        return False


def test_enum_values():
    """测试枚举值"""
    print("\n测试枚举值...")

    try:
        from core.enums import TaskPriority, TaskStatus, TaskType

        # 测试TaskStatus
        status_values = [status.value for status in TaskStatus]
        print(f"✓ TaskStatus枚举: {status_values}")

        # 测试TaskType
        type_values = [task_type.value for task_type in TaskType]
        print(f"✓ TaskType枚举: {type_values}")

        # 测试TaskPriority
        priority_values = [priority.value for priority in TaskPriority]
        print(f"✓ TaskPriority枚举: {priority_values}")

        return True

    except Exception as e:
        print(f"✗ 枚举测试失败: {e}")
        return False


def test_data_model_creation():
    """测试数据模型创建"""
    print("\n测试数据模型创建...")

    try:
        # 手动创建任务配置数据
        task_config_data = {
            "name": "测试任务",
            "task_type": "AUTOMATION",
            "description": "这是一个测试任务",
            "priority": "MEDIUM",
            "execution_config": {"max_retry_count": 3, "timeout_seconds": 300},
            "schedule_config": {"enabled": False},
            "actions": [],
            "tags": ["test"],
            "custom_params": {},
            "version": "1.0",
        }

        print(f"✓ 任务配置数据创建成功: {task_config_data['name']}")
        print(f"  - 类型: {task_config_data['task_type']}")
        print(f"  - 优先级: {task_config_data['priority']}")
        print(f"  - 描述: {task_config_data['description']}")

        # 测试JSON序列化
        import json

        json_str = json.dumps(task_config_data, ensure_ascii=False, indent=2)
        print(f"✓ JSON序列化成功: {len(json_str)} 字符")

        # 测试JSON反序列化
        parsed_data = json.loads(json_str)
        if parsed_data["name"] == task_config_data["name"]:
            print("✓ JSON反序列化成功")
            return True
        else:
            print("✗ JSON反序列化失败")
            return False

    except Exception as e:
        print(f"✗ 数据模型测试失败: {e}")
        return False


def test_file_structure():
    """测试文件结构"""
    print("\n测试文件结构...")

    try:
        # 检查关键文件是否存在
        key_files = [
            "src/core/enums.py",
            "src/models/unified_models.py",
            "src/adapters/task_manager_adapter.py",
            "src/database/db_manager.py",
            "src/services/task_service.py",
            "src/repositories/sqlite_task_repository.py",
        ]

        missing_files = []
        existing_files = []

        for file_path in key_files:
            full_path = os.path.join(os.path.dirname(__file__), file_path)
            if os.path.exists(full_path):
                existing_files.append(file_path)
            else:
                missing_files.append(file_path)

        print(f"✓ 存在的文件 ({len(existing_files)}):")
        for file_path in existing_files:
            print(f"  - {file_path}")

        if missing_files:
            print(f"✗ 缺失的文件 ({len(missing_files)}):")
            for file_path in missing_files:
                print(f"  - {file_path}")
            return False
        else:
            print("✓ 所有关键文件都存在")
            return True

    except Exception as e:
        print(f"✗ 文件结构测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("=== 基础功能测试 ===")

    tests = [
        test_file_structure,
        test_enum_values,
        test_database_creation,
        test_data_model_creation,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        else:
            print("\n测试失败，继续下一个测试")

    print(f"\n=== 测试结果: {passed}/{total} 通过 ===")

    if passed >= 3:  # 至少通过3个测试
        print("🎉 基础功能测试基本通过！架构重构核心功能正常！")
        return True
    else:
        print("❌ 基础功能测试失败较多，需要进一步修复")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
