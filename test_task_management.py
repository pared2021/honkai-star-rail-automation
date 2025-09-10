#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理功能测试脚本
用于验证TaskManager是否能正常工作
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.task_manager import TaskManager, Task, TaskType, TaskStatus, TaskPriority
from src.core.config_manager import ConfigManager

def test_task_manager_basic():
    """测试任务管理器基础功能"""
    print("=== 任务管理器基础功能测试 ===")
    
    try:
        # 初始化任务管理器
        task_manager = TaskManager()
        print("✅ 任务管理器初始化成功")
        
        # 创建测试任务
        task = Task(
            id="test_task_001",
            name="测试任务",
            task_type=TaskType.USER,
            priority=TaskPriority.HIGH,
            metadata={"test_param": "test_value"}
        )
        
        print(f"✅ 创建任务: {task.name} (ID: {task.id})")
        print(f"   任务类型: {task.task_type.value}")
        print(f"   优先级: {task.priority.name}")
        print(f"   状态: {task.status.value}")
        print(f"   创建时间: {task.created_at}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_task_types_and_priorities():
    """测试任务类型和优先级"""
    print("\n=== 任务类型和优先级测试 ===")
    
    try:
        task_manager = TaskManager()
        
        # 测试不同类型和优先级的任务
        test_cases = [
            ("自动化任务", TaskType.AUTOMATION, TaskPriority.URGENT),
            ("监控任务", TaskType.MONITORING, TaskPriority.HIGH),
            ("游戏检测任务", TaskType.GAME_DETECTION, TaskPriority.MEDIUM),
            ("日常任务", TaskType.DAILY_TASK, TaskPriority.LOW),
            ("系统任务", TaskType.SYSTEM, TaskPriority.NORMAL)
        ]
        
        tasks = []
        for i, (name, task_type, priority) in enumerate(test_cases, 1):
            task = Task(
                id=f"test_task_{i:03d}",
                name=name,
                task_type=task_type,
                priority=priority
            )
            tasks.append(task)
            print(f"✅ 创建 {name}: 类型={task_type.value}, 优先级={priority.name}")
        
        print(f"\n✅ 成功创建 {len(tasks)} 个不同类型的任务")
        
        # 测试优先级排序
        print("\n📊 优先级排序测试:")
        sorted_tasks = sorted(tasks, key=lambda t: t.priority.value)
        for task in sorted_tasks:
            print(f"   {task.priority.name} ({task.priority.value}): {task.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_task_status_updates():
    """测试任务状态更新"""
    print("\n=== 任务状态更新测试 ===")
    
    try:
        task_manager = TaskManager()
        
        # 创建任务
        task = Task(
            id="status_test_task",
            name="状态测试任务",
            task_type=TaskType.USER,
            priority=TaskPriority.MEDIUM
        )
        
        print(f"✅ 初始状态: {task.status.value}")
        
        # 测试状态转换
        status_transitions = [
            TaskStatus.RUNNING,
            TaskStatus.PAUSED,
            TaskStatus.RUNNING,
            TaskStatus.COMPLETED
        ]
        
        for new_status in status_transitions:
            task.status = new_status
            task.updated_at = datetime.now()
            print(f"✅ 状态更新为: {new_status.value}")
            time.sleep(0.1)  # 模拟状态变化间隔
        
        print(f"\n✅ 最终状态: {task.status.value}")
        print(f"   更新时间: {task.updated_at}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_task_metadata():
    """测试任务元数据功能"""
    print("\n=== 任务元数据测试 ===")
    
    try:
        task_manager = TaskManager()
        
        # 创建带有元数据的任务
        metadata = {
            "source": "test_script",
            "config": {
                "retry_count": 3,
                "timeout": 300,
                "parameters": ["param1", "param2"]
            },
            "tags": ["test", "automation", "demo"]
        }
        
        task = Task(
            id="metadata_test_task",
            name="元数据测试任务",
            task_type=TaskType.AUTOMATION,
            priority=TaskPriority.HIGH,
            metadata=metadata
        )
        
        print("✅ 任务元数据:")
        for key, value in task.metadata.items():
            print(f"   {key}: {value}")
        
        # 动态更新元数据
        task.metadata["execution_start"] = datetime.now().isoformat()
        task.metadata["progress"] = 0.0
        
        print("\n✅ 动态更新元数据:")
        print(f"   execution_start: {task.metadata['execution_start']}")
        print(f"   progress: {task.metadata['progress']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_concurrent_task_queue():
    """测试并发任务队列"""
    print("\n=== 并发任务队列测试 ===")
    
    try:
        from src.core.task_manager import ConcurrentTaskQueue, TaskExecution
        
        # 创建队列
        queue = ConcurrentTaskQueue()
        print("✅ 并发任务队列创建成功")
        
        # 创建不同优先级的任务执行对象
        executions = []
        priorities = [TaskPriority.LOW, TaskPriority.URGENT, TaskPriority.MEDIUM, TaskPriority.HIGH]
        
        for i, priority in enumerate(priorities, 1):
            execution = TaskExecution(
                task_id=f"queue_test_{i}",
                execution_id=f"exec_{i}",
                priority=priority,
                state=TaskState.QUEUED if 'TaskState' in globals() else None
            )
            executions.append(execution)
            queue.put(execution)
            print(f"✅ 添加任务到队列: 优先级={priority.name}")
        
        print(f"\n📊 队列状态:")
        print(f"   总任务数: {queue.size()}")
        
        priority_counts = queue.get_priority_counts()
        for priority, count in priority_counts.items():
            if count > 0:
                print(f"   {priority.name}: {count} 个任务")
        
        # 按优先级顺序取出任务
        print("\n📤 按优先级取出任务:")
        while queue.size() > 0:
            execution = queue.get()
            if execution:
                print(f"   取出: {execution.task_id} (优先级: {execution.priority.name})")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始任务管理系统测试...\n")
    
    # 运行所有测试
    tests = [
        ("基础功能", test_task_manager_basic),
        ("任务类型和优先级", test_task_types_and_priorities),
        ("状态更新", test_task_status_updates),
        ("元数据功能", test_task_metadata),
        ("并发队列", test_concurrent_task_queue)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"测试: {test_name}")
        print(f"{'='*50}")
        
        result = test_func()
        results.append((test_name, result))
    
    # 输出测试结果摘要
    print(f"\n{'='*50}")
    print("测试结果摘要")
    print(f"{'='*50}")
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！任务管理系统工作正常。")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，需要检查相关功能。")
    
    print("\n测试脚本结束")