#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, 'src')

try:
    from core.task_manager import TaskManager
    from database.db_manager import DatabaseManager
    
    print("=== TaskManager 类检查 ===")
    print(f"TaskManager 类: {TaskManager}")
    print(f"get_task_sync 方法存在: {hasattr(TaskManager, 'get_task_sync')}")
    
    if hasattr(TaskManager, 'get_task_sync'):
        method = getattr(TaskManager, 'get_task_sync')
        print(f"get_task_sync 方法: {method}")
        print(f"方法类型: {type(method)}")
    
    # 列出所有包含 'sync' 的方法
    sync_methods = [attr for attr in dir(TaskManager) if 'sync' in attr.lower()]
    print(f"包含 'sync' 的方法: {sync_methods}")
    
    print("\n=== DatabaseManager 类检查 ===")
    print(f"DatabaseManager 类: {DatabaseManager}")
    print(f"get_task_config 方法存在: {hasattr(DatabaseManager, 'get_task_config')}")
    
    if hasattr(DatabaseManager, 'get_task_config'):
        method = getattr(DatabaseManager, 'get_task_config')
        print(f"get_task_config 方法: {method}")
        print(f"方法类型: {type(method)}")
    
    print("\n=== 实例化测试 ===")
    # 创建数据库管理器实例
    db_manager = DatabaseManager()
    print(f"DatabaseManager 实例: {db_manager}")
    print(f"实例的 get_task_config 方法存在: {hasattr(db_manager, 'get_task_config')}")
    
    # 创建任务管理器实例
    task_manager = TaskManager(db_manager)
    print(f"TaskManager 实例: {task_manager}")
    print(f"实例的 get_task_sync 方法存在: {hasattr(task_manager, 'get_task_sync')}")
    
    print("\n=== 测试完成，所有导入和实例化成功 ===")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()