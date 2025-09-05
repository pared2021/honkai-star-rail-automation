#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试TaskManager类的get_task_sync方法问题
"""

import sys
import os
import inspect

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=== TaskManager调试信息 ===")

try:
    # 导入TaskManagerAdapter
    from adapters.task_manager_adapter import TaskManagerAdapter
    print("✓ 成功导入TaskManagerAdapter")
    
    # 检查类的源文件
    source_file = inspect.getfile(TaskManagerAdapter)
    print(f"源文件: {source_file}")
    
    # 检查类的所有方法
    methods = inspect.getmembers(TaskManagerAdapter, predicate=inspect.isfunction)
    print(f"\n类方法总数: {len(methods)}")
    
    # 查找包含'get_task'的方法
    get_task_methods = [name for name, method in methods if 'get_task' in name]
    print(f"包含'get_task'的方法: {get_task_methods}")
    
    # 检查get_task_sync方法
    if hasattr(TaskManagerAdapter, 'get_task_sync'):
        print("✓ get_task_sync方法存在于类中")
        method = getattr(TaskManagerAdapter, 'get_task_sync')
        print(f"方法类型: {type(method)}")
        print(f"方法签名: {inspect.signature(method)}")
        
        # 获取方法源码位置
        try:
            source_lines = inspect.getsourcelines(method)
            print(f"方法定义行数: {source_lines[1]}")
            print(f"方法代码行数: {len(source_lines[0])}")
        except Exception as e:
            print(f"无法获取源码信息: {e}")
    else:
        print("✗ get_task_sync方法不存在于类中")
    
    # 尝试创建实例
    print("\n=== 实例测试 ===")
    try:
        from database.db_manager import DatabaseManager
        db_manager = DatabaseManager()
        task_manager = TaskManagerAdapter(db_manager)
        print("✓ 成功创建TaskManagerAdapter实例")
        
        # 检查实例方法
        if hasattr(task_manager, 'get_task_sync'):
            print("✓ 实例有get_task_sync方法")
            method = getattr(task_manager, 'get_task_sync')
            print(f"实例方法类型: {type(method)}")
        else:
            print("✗ 实例没有get_task_sync方法")
            
            # 列出实例的所有方法
            instance_methods = [attr for attr in dir(task_manager) if not attr.startswith('_') and callable(getattr(task_manager, attr))]
            get_task_instance_methods = [method for method in instance_methods if 'get_task' in method]
            print(f"实例中包含'get_task'的方法: {get_task_instance_methods}")
            
    except Exception as e:
        print(f"✗ 创建实例失败: {e}")
        import traceback
        traceback.print_exc()
    
except Exception as e:
    print(f"✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 调试完成 ===")