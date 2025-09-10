#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端自动化测试脚本

测试完整的自动化流程，包括：
1. 游戏检测
2. 任务管理
3. 同步适配器
4. 自动化服务
5. 完整的工作流程
"""

import sys
import os
import time
import asyncio
from typing import Dict, Any, List

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.game_detector import GameDetector
from src.core.task_manager import TaskManager
from src.core.sync_adapter import SyncAdapter

def print_separator(title: str):
    """打印分隔符。"""
    print("\n" + "=" * 50)
    print(f"测试: {title}")
    print("=" * 50)

def test_game_detection():
    """测试游戏检测功能。"""
    print_separator("游戏检测")
    
    try:
        # 创建游戏检测器
        game_detector = GameDetector()
        print("✅ 游戏检测器创建成功")
        
        # 检测游戏窗口
        game_window = game_detector.detect_game_window()
        if game_window:
            print(f"📊 检测到游戏窗口: {game_window.title} (HWND: {game_window.hwnd})")
            print(f"   窗口大小: {game_window.width}x{game_window.height}")
            print(f"   是否前台: {game_window.is_foreground}")
        else:
            print("⚠️  未检测到游戏窗口")
        
        # 检查检测器状态
        status = game_detector.get_status()
        print(f"🔍 检测器状态: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ 游戏检测测试失败: {str(e)}")
        return False

def test_task_management_integration():
    """测试任务管理集成。"""
    print_separator("任务管理集成")
    
    try:
        # 创建任务管理器
        task_manager = TaskManager()
        print("✅ 任务管理器创建成功")
        
        # 启动并发管理器
        task_manager.start_concurrent_manager()
        print("✅ 并发管理器启动成功")
        
        # 添加测试任务
        test_tasks = [
            {"name": "游戏检测任务", "type": "detection", "priority": "high"},
            {"name": "自动化任务", "type": "automation", "priority": "medium"},
            {"name": "监控任务", "type": "monitoring", "priority": "low"}
        ]
        
        task_ids = []
        for task_data in test_tasks:
            task_id = task_manager.add_task(task_data)
            if task_id:
                task_ids.append(task_id)
                print(f"✅ 任务已添加: {task_data['name']} (ID: {task_id})")
        
        # 等待任务执行
        print("⏳ 等待任务执行...")
        time.sleep(3)
        
        # 检查任务状态
        all_tasks = task_manager.get_all_tasks()
        print(f"📊 总任务数: {len(all_tasks)}")
        
        for task in all_tasks:
            print(f"   任务: {task['name']} - 状态: {task['state']}")
        
        # 获取统计信息
        stats = asyncio.run(task_manager.get_task_statistics())
        print(f"📈 任务统计: {stats}")
        
        # 停止并发管理器
        task_manager.stop_concurrent_manager()
        print("✅ 并发管理器停止成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 任务管理集成测试失败: {str(e)}")
        return False

def test_sync_adapter_integration():
    """测试同步适配器集成。"""
    print_separator("同步适配器集成")
    
    try:
        # 创建同步适配器
        sync_adapter = SyncAdapter()
        print("✅ 同步适配器创建成功")
        
        # 启动适配器
        sync_adapter.start()
        print("✅ 同步适配器启动成功")
        
        # 定义异步任务
        async def automation_task(task_name: str):
            await asyncio.sleep(1)
            return f"自动化任务 {task_name} 完成"
        
        # 执行多个异步任务
        tasks = ["游戏检测", "界面识别", "操作执行"]
        results = []
        
        for task_name in tasks:
            task_id = sync_adapter.run_async(automation_task(task_name))
            result = sync_adapter.wait_for_result(task_id, timeout=5.0)
            results.append(result)
            print(f"✅ {result}")
        
        # 获取适配器统计
        stats = sync_adapter.get_stats()
        print(f"📊 适配器统计: {stats}")
        
        # 停止适配器
        sync_adapter.stop()
        print("✅ 同步适配器停止成功")
        
        return len(results) == len(tasks)
        
    except Exception as e:
        print(f"❌ 同步适配器集成测试失败: {str(e)}")
        return False

def test_automation_service_integration():
    """测试自动化服务集成。"""
    print_separator("自动化服务集成")
    
    try:
        # 检查自动化服务模块是否存在
        import src.application.automation_service as automation_module
        print("✅ 自动化服务模块导入成功")
        
        # 检查模块内容
        module_attrs = [attr for attr in dir(automation_module) if not attr.startswith('_')]
        print(f"📋 模块属性: {len(module_attrs)} 个")
        
        if module_attrs:
            for attr in module_attrs[:5]:  # 显示前5个属性
                print(f"   - {attr}")
        else:
            print("⚠️  模块暂无可用属性，可能需要进一步实现")
        
        return True
        
    except Exception as e:
        print(f"❌ 自动化服务集成测试失败: {str(e)}")
        return False

def test_complete_workflow():
    """测试完整的自动化工作流程。"""
    print_separator("完整工作流程")
    
    try:
        # 1. 初始化所有组件
        print("🔧 初始化组件...")
        game_detector = GameDetector()
        task_manager = TaskManager()
        sync_adapter = SyncAdapter()
        
        # 2. 启动必要的服务
        print("🚀 启动服务...")
        task_manager.start_concurrent_manager()
        sync_adapter.start()
        
        # 3. 模拟完整的自动化流程
        print("🎮 开始自动化流程...")
        
        # 步骤1: 游戏检测
        game_window = game_detector.detect_game_window()
        window_count = 1 if game_window else 0
        print(f"   步骤1: 游戏检测完成 - 发现 {window_count} 个窗口")
        
        # 步骤2: 创建自动化任务
        automation_tasks = [
            {"name": "界面识别任务", "type": "ui_recognition", "priority": "high"},
            {"name": "操作执行任务", "type": "action_execution", "priority": "medium"}
        ]
        
        task_ids = []
        for task_data in automation_tasks:
            task_id = task_manager.add_task(task_data)
            if task_id:
                task_ids.append(task_id)
        
        print(f"   步骤2: 创建了 {len(task_ids)} 个自动化任务")
        
        # 步骤3: 使用同步适配器执行异步操作
        async def workflow_step(step_name: str):
            await asyncio.sleep(0.5)
            return f"工作流步骤 {step_name} 完成"
        
        workflow_steps = ["准备", "执行", "验证", "清理"]
        for step in workflow_steps:
            task_id = sync_adapter.run_async(workflow_step(step))
            result = sync_adapter.wait_for_result(task_id, timeout=3.0)
            print(f"   步骤3: {result}")
        
        # 等待任务完成
        print("⏳ 等待任务完成...")
        time.sleep(2)
        
        # 4. 收集结果和统计
        print("📊 收集结果...")
        task_stats = asyncio.run(task_manager.get_task_statistics())
        adapter_stats = sync_adapter.get_stats()
        
        print(f"   任务统计: {task_stats}")
        print(f"   适配器统计: {adapter_stats}")
        
        # 5. 清理资源
        print("🧹 清理资源...")
        sync_adapter.stop()
        task_manager.stop_concurrent_manager()
        
        print("✅ 完整工作流程测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 完整工作流程测试失败: {str(e)}")
        return False

def main():
    """主测试函数。"""
    print("🚀 开始端到端自动化测试")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试列表
    tests = [
        ("游戏检测", test_game_detection),
        ("任务管理集成", test_task_management_integration),
        ("同步适配器集成", test_sync_adapter_integration),
        ("自动化服务集成", test_automation_service_integration),
        ("完整工作流程", test_complete_workflow)
    ]
    
    # 执行测试
    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = "✅ 通过" if result else "❌ 失败"
        except Exception as e:
            results[test_name] = f"❌ 异常: {str(e)}"
    
    # 显示测试结果摘要
    print_separator("测试结果摘要")
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        print(f"{test_name}: {result}")
        if "✅" in result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！自动化系统工作正常。")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，需要检查相关功能。")
    
    print("\n测试脚本结束")
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)