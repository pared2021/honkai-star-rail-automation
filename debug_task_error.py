#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试任务错误的脚本
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from core.task_manager import TaskManager
    from database.db_manager import DatabaseManager
    
    print("正在初始化数据库管理器...")
    db_manager = DatabaseManager()
    
    print("正在初始化任务管理器...")
    task_manager = TaskManager(db_manager)
    
    print("正在获取任务列表...")
    tasks = task_manager.list_tasks_sync()
    
    print(f"获取到 {len(tasks)} 个任务")
    
    if tasks:
        task = tasks[0]
        print(f"第一个任务: {task}")
        print(f"任务名称: {task.name}")
        print(f"任务配置: {task.config}")
        print(f"任务配置类型: {type(task.config)}")
        
        # 尝试访问可能导致错误的属性
        if hasattr(task.config, 'task_name'):
            print(f"config.task_name: {task.config.task_name}")
        else:
            print("config 没有 task_name 属性")
            
except Exception as e:
    import traceback
    print(f"错误: {e}")
    print("详细错误信息:")
    traceback.print_exc()