#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 TaskManager 类中的方法是否存在
"""

import os
from pathlib import Path
import sys

# 添加src目录到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    # 导入必要的模块
    from adapters.task_manager_adapter import TaskManagerAdapter
    from database.db_manager import DatabaseManager

    print("模块导入成功")

    # 检查 TaskManagerAdapter 类的方法
    print("\nTaskManagerAdapter 类的方法:")
    methods = [
        method for method in dir(TaskManagerAdapter) if not method.startswith("_")
    ]
    for method in sorted(methods):
        print(f"  - {method}")

    # 特别检查 get_task_sync 方法
    has_get_task_sync = hasattr(TaskManagerAdapter, "get_task_sync")
    print(f"\nget_task_sync 方法存在: {has_get_task_sync}")

    if has_get_task_sync:
        method = getattr(TaskManagerAdapter, "get_task_sync")
        print(f"方法类型: {type(method)}")
        print(f"方法文档: {method.__doc__}")

    # 尝试创建实例
    print("\n尝试创建 TaskManagerAdapter 实例...")
    db_manager = DatabaseManager()
    task_manager = TaskManagerAdapter(db_manager)

    print("TaskManagerAdapter 实例创建成功")

    # 检查实例方法
    has_instance_method = hasattr(task_manager, "get_task_sync")
    print(f"实例中 get_task_sync 方法存在: {has_instance_method}")

except Exception as e:
    print(f"错误: {e}")
    import traceback

    traceback.print_exc()
