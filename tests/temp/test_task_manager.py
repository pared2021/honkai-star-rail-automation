#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试TaskManager类的get_task_sync方法
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from adapters.task_manager_adapter import TaskManagerAdapter
    print("✓ 成功导入TaskManagerAdapter")
    
    # 检查get_task_sync方法是否存在
    if hasattr(TaskManagerAdapter, 'get_task_sync'):
        print("✓ get_task_sync方法存在于TaskManagerAdapter类中")
        print(f"方法类型: {type(getattr(TaskManagerAdapter, 'get_task_sync'))}")
    else:
        print("✗ get_task_sync方法不存在于TaskManagerAdapter类中")
    
    # 列出TaskManagerAdapter的所有方法
    print("\nTaskManagerAdapter的所有方法:")
    methods = [method for method in dir(TaskManagerAdapter) if not method.startswith('_')]
    get_task_methods = [method for method in methods if 'get_task' in method]
    print(f"包含'get_task'的方法: {get_task_methods}")
    
    # 尝试创建实例（不需要数据库连接）
    print("\n尝试创建TaskManagerAdapter实例...")
    try:
        from database.db_manager import DatabaseManager
        db_manager = DatabaseManager()
        task_manager = TaskManagerAdapter(db_manager)
        print("✓ 成功创建TaskManagerAdapter实例")
        
        # 检查实例是否有get_task_sync方法
        if hasattr(task_manager, 'get_task_sync'):
            print("✓ 实例有get_task_sync方法")
        else:
            print("✗ 实例没有get_task_sync方法")
            
    except Exception as e:
        print(f"✗ 创建TaskManagerAdapter实例失败: {e}")
    
except Exception as e:
    print(f"✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()

print("\n测试完成")