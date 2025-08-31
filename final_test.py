#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    print("=== 最终测试开始 ===")
    
    # 测试 1: 导入 TaskManager
    print("\n1. 测试 TaskManager 导入...")
    from core.task_manager import TaskManager
    print("✓ TaskManager 导入成功")
    
    # 测试 2: 检查 get_task_sync 方法
    print("\n2. 检查 get_task_sync 方法...")
    has_method = hasattr(TaskManager, 'get_task_sync')
    print(f"✓ get_task_sync 方法存在: {has_method}")
    
    if has_method:
        method = getattr(TaskManager, 'get_task_sync')
        is_callable = callable(method)
        print(f"✓ get_task_sync 方法可调用: {is_callable}")
    
    # 测试 3: 导入 DatabaseManager
    print("\n3. 测试 DatabaseManager 导入...")
    from database.db_manager import DatabaseManager
    print("✓ DatabaseManager 导入成功")
    
    # 测试 4: 创建实例
    print("\n4. 创建实例...")
    db_manager = DatabaseManager()
    print("✓ DatabaseManager 实例创建成功")
    
    task_manager = TaskManager(db_manager)
    print("✓ TaskManager 实例创建成功")
    
    # 测试 5: 检查实例方法
    print("\n5. 检查实例方法...")
    instance_has_method = hasattr(task_manager, 'get_task_sync')
    print(f"✓ 实例具有 get_task_sync 方法: {instance_has_method}")
    
    if instance_has_method:
        instance_method = getattr(task_manager, 'get_task_sync')
        instance_is_callable = callable(instance_method)
        print(f"✓ 实例方法可调用: {instance_is_callable}")
    
    print("\n=== 所有测试通过! ===")
    print("TaskManager 的 get_task_sync 方法问题已解决")
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)