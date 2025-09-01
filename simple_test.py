#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的集成测试
用于验证基本的数据库和服务功能
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from models.unified_models import Task, TaskConfig, TaskType, TaskPriority, TaskStatus
from repositories.sqlite_task_repository import SQLiteTaskRepository
from services.task_service import TaskService
from services.event_bus import EventBus
from datetime import datetime

async def test_basic_repository():
    """测试基本的仓库功能"""
    print("\n=== 测试基本仓库功能 ===")
    
    # 使用内存数据库
    repository = SQLiteTaskRepository(":memory:")
    
    try:
        # 初始化
        await repository.initialize()
        print("✓ 仓库初始化成功")
        
        # 创建任务配置
        task_config = TaskConfig(
            name="测试任务",
            description="这是一个测试任务",
            task_type=TaskType.CUSTOM,
            priority=TaskPriority.MEDIUM
        )
        
        # 创建任务
        task = Task(
            task_id="test_001",
            user_id="user_001",
            config=task_config,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 保存任务
        task_id = await repository.create_task(task)
        print(f"✓ 任务创建成功: {task_id}")
        
        # 获取任务
        retrieved_task = await repository.get_task(task_id)
        if retrieved_task:
            print(f"✓ 任务获取成功: {retrieved_task.config.name}")
        else:
            print("✗ 任务获取失败")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ 仓库测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await repository.close()

async def test_basic_service():
    """测试基本的服务功能"""
    print("\n=== 测试基本服务功能 ===")
    
    try:
        # 创建事件总线
        event_bus = EventBus()
        await event_bus.start()  # 启动事件总线
        print("✓ 事件总线启动成功")
        
        # 创建仓库
        repository = SQLiteTaskRepository(":memory:")
        await repository.initialize()
        
        # 创建服务
        service = TaskService(repository, event_bus)
        await service.initialize()
        print("✓ 服务初始化成功")
        
        # 创建任务配置
        task_config = TaskConfig(
            name="服务测试任务",
            description="通过服务创建的测试任务",
            task_type=TaskType.CUSTOM_SEQUENCE,
            priority=TaskPriority.HIGH
        )
        
        # 通过服务创建任务
        task_id = await service.create_task(task_config, "user_002")
        print(f"✓ 通过服务创建任务成功: {task_id}")
        
        # 通过服务获取任务
        task = await service.get_task(task_id)
        if task:
            print(f"✓ 通过服务获取任务成功: {task.config.name}")
        else:
            print("✗ 通过服务获取任务失败")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ 服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await service.close()
        await repository.close()
        await event_bus.stop()  # 停止事件总线

async def main():
    """主测试函数"""
    print("开始简化集成测试...")
    
    # 测试仓库
    repo_success = await test_basic_repository()
    
    # 测试服务
    service_success = await test_basic_service()
    
    # 总结
    print("\n=== 测试结果 ===")
    if repo_success and service_success:
        print("✓ 所有测试通过")
        return True
    else:
        print("✗ 部分测试失败")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)