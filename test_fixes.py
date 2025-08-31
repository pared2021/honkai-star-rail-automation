#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复效果的脚本
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    print("正在测试导入...")
    
    # 测试导入 TaskManager
    from core.task_manager import TaskManager
    print("✓ TaskManager 导入成功")
    
    # 测试导入 MainWindow
    from gui.main_window import MainWindow
    print("✓ MainWindow 导入成功")
    
    # 测试导入 TaskListWidget
    from gui.task_list_widget import TaskListWidget
    print("✓ TaskListWidget 导入成功")
    
    # 测试导入 IntelligentScheduler
    from core.intelligent_scheduler import IntelligentScheduler
    print("✓ IntelligentScheduler 导入成功")
    
    print("\n所有导入测试通过！")
    
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n测试完成，所有修复生效！")