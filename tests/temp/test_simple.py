#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import sys

import asyncio

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("开始简单测试...")

try:
    from src.core.database import DatabaseManager

    print("✓ DatabaseManager 导入成功")
except Exception as e:
    print(f"✗ DatabaseManager 导入失败: {e}")

try:
    from src.core.task_manager import TaskManager
    from src.models.task_models import TaskConfig

    print("✓ TaskManager 导入成功")
except Exception as e:
    print(f"✗ TaskManager 导入失败: {e}")

try:
    from src.models.task_model import TaskPriority, TaskStatus, TaskType

    print("✓ 任务模型导入成功")
except Exception as e:
    print(f"✗ 任务模型导入失败: {e}")

print("简单测试完成")
