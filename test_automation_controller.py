#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化控制器测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.automation.automation_controller import AutomationController
from src.core.game_detector import GameDetector
import asyncio

def test_automation_controller():
    """测试自动化控制器的基础功能"""
    print("=" * 50)
    print("自动化控制器功能测试")
    print("=" * 50)
    
    try:
        # 创建游戏检测器和自动化控制器
        print("\n1. 初始化组件...")
        game_detector = GameDetector()
        controller = AutomationController(game_detector)
        print("✅ 自动化控制器初始化成功")
        
        # 测试启动功能
        print("\n2. 测试启动功能...")
        start_result = controller.start()
        print(f"启动结果: {start_result}")
        print(f"控制器状态: {controller.get_automation_status()}")
        print(f"是否运行中: {controller._running}")
        
        # 获取任务状态
        print("\n3. 获取任务状态...")
        task_status = controller.get_task_status()
        print(f"任务状态: {task_status}")
        
        # 测试添加任务
        print("\n4. 测试任务管理...")
        available_tasks = controller.get_available_automation_tasks()
        print(f"可用任务数量: {len(available_tasks)}")
        for task in available_tasks:
            print(f"  - {task.name} (ID: {task.id})")
        
        # 测试执行单个任务
        print("\n5. 测试任务执行...")
        if available_tasks:
            test_task = available_tasks[0]
            print(f"执行任务: {test_task.name}")
            result = controller.execute(test_task.id)
            print(f"执行结果: {result}")
        
        # 测试停止功能
        print("\n6. 测试停止功能...")
        stop_result = controller.stop()
        print(f"停止结果: {stop_result}")
        print(f"最终状态: {controller.get_automation_status()}")
        print(f"是否运行中: {controller._running}")
        
        print("\n=" * 50)
        print("✅ 自动化控制器基础功能测试完成")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_automation_loop():
    """测试自动化循环功能"""
    print("\n=" * 50)
    print("自动化循环功能测试")
    print("=" * 50)
    
    try:
        # 创建控制器
        game_detector = GameDetector()
        controller = AutomationController(game_detector)
        
        # 启动控制器
        print("\n1. 启动自动化控制器...")
        controller.start()
        
        # 测试启动自动化循环
        print("\n2. 启动自动化循环...")
        loop_start_result = await controller.start_automation_loop()
        print(f"循环启动结果: {loop_start_result}")
        
        # 等待一小段时间
        print("\n3. 等待循环运行...")
        await asyncio.sleep(2)
        
        # 停止自动化循环
        print("\n4. 停止自动化循环...")
        loop_stop_result = await controller.stop_automation_loop()
        print(f"循环停止结果: {loop_stop_result}")
        
        # 停止控制器
        controller.stop()
        
        print("\n✅ 自动化循环功能测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 循环测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始自动化控制器测试...")
    
    # 测试基础功能
    basic_test_result = test_automation_controller()
    
    # 测试循环功能
    loop_test_result = asyncio.run(test_automation_loop())
    
    # 总结
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)
    print(f"基础功能测试: {'✅ 通过' if basic_test_result else '❌ 失败'}")
    print(f"循环功能测试: {'✅ 通过' if loop_test_result else '❌ 失败'}")
    
    if basic_test_result and loop_test_result:
        print("\n🎉 所有测试通过！自动化控制器工作正常。")
        return True
    else:
        print("\n❌ 部分测试失败，请检查相关功能。")
        return False

if __name__ == "__main__":
    success = main()
    print("\n测试脚本结束")
    sys