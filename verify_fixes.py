#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证所有修复是否生效的测试脚本
"""

import sys
import os
sys.path.insert(0, 'src')

def test_task_manager_import():
    """测试 TaskManager 导入"""
    try:
        from core.task_manager import TaskManager, TaskConfig
        from core.task_model import TaskType, TaskPriority
        print("✓ TaskManager 导入成功")
        return True
    except Exception as e:
        print(f"✗ TaskManager 导入失败: {e}")
        return False

def test_task_config_structure():
    """测试 TaskConfig 结构"""
    try:
        from core.task_manager import TaskConfig
        from core.task_model import TaskType, TaskPriority
        
        # 创建 TaskConfig 实例
        config = TaskConfig(
            name="测试任务",
            task_type=TaskType.AUTOMATION,
            description="这是一个测试任务",
            priority=TaskPriority.MEDIUM
        )
        
        # 验证属性
        assert hasattr(config, 'name'), "TaskConfig 缺少 name 属性"
        assert config.name == "测试任务", "TaskConfig.name 值不正确"
        
        print("✓ TaskConfig 结构正确")
        return True
    except Exception as e:
        print(f"✗ TaskConfig 结构测试失败: {e}")
        return False

def test_get_task_sync_method():
    """测试 get_task_sync 方法存在性"""
    try:
        from core.task_manager import TaskManager
        
        # 检查方法是否存在
        assert hasattr(TaskManager, 'get_task_sync'), "TaskManager 缺少 get_task_sync 方法"
        
        # 检查方法是否可调用
        assert callable(getattr(TaskManager, 'get_task_sync')), "get_task_sync 不是可调用方法"
        
        print("✓ get_task_sync 方法存在且可调用")
        return True
    except Exception as e:
        print(f"✗ get_task_sync 方法测试失败: {e}")
        return False

def test_database_manager_import():
    """测试 DatabaseManager 导入"""
    try:
        from database.db_manager import DatabaseManager
        print("✓ DatabaseManager 导入成功")
        return True
    except Exception as e:
        print(f"✗ DatabaseManager 导入失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始验证修复...\n")
    
    tests = [
        test_task_manager_import,
        test_task_config_structure,
        test_get_task_sync_method,
        test_database_manager_import
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有修复验证通过！")
        return True
    else:
        print("❌ 部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)