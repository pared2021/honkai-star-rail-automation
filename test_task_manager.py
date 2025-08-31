#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试TaskManager类的get_task_sync方法
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from core.task_manager import TaskManager
    print("✓ 成功导入TaskManager")
    
    # 检查get_task_sync方法是否存在
    if hasattr(TaskManager, 'get_task_sync'):
        print("✓ get_task_sync方法存在于TaskManager类中")
        print(f"方法类型: {type(getattr(TaskManager, 'get_task_sync'))}")
    else:
        print("✗ get_task_sync方法不存在于TaskManager类中")
    
    # 列出TaskManager的所有方法
    print("\nTaskManager的所有方法:")
    methods = [method for method in dir(TaskManager) if not method.startswith('_')]
    get_task_methods = [method for method in methods if 'get_task' in method]
    print(f"包含'get_task'的方法: {get_task_methods}")
    
    # 尝试创建实例（不需要数据库连接）
    print("\n尝试创建TaskManager实例...")
    try:
        from core.database_manager import DatabaseManager
        db_manager = DatabaseManager()
        task_manager = TaskManager(db_manager)
        print("✓ 成功创建TaskManager实例")
        
        # 检查实例是否有get_task_sync方法
        if hasattr(task_manager, 'get_task_sync'):
            print("✓ 实例有get_task_sync方法")
        else:
            print("✗ 实例没有get_task_sync方法")
            
    except Exception as e:
        print(f"✗ 创建TaskManager实例失败: {e}")
    
except Exception as e:
    print(f"✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()

print("\n测试完成")