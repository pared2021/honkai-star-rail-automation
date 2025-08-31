#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, 'src')

try:
    print("测试 TaskConfig 导入...")
    from core.task_manager import TaskConfig
    from core.task_model import TaskType, TaskPriority
    print("✓ 导入成功")
    
    print("\n测试 TaskConfig 创建...")
    config = TaskConfig(
        name="测试任务",
        task_type=TaskType.AUTOMATION,
        description="测试描述",
        priority=TaskPriority.MEDIUM
    )
    print("✓ TaskConfig 创建成功")
    
    print(f"\n验证属性:")
    print(f"config.name = {config.name}")
    print(f"config.task_type = {config.task_type}")
    print(f"config.description = {config.description}")
    print(f"config.priority = {config.priority}")
    
    print("\n✅ 所有测试通过！")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)