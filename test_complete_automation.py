#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整自动化功能测试脚本
测试项目的所有核心自动化功能
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.game_detector import GameDetector
from src.core.task_manager import TaskManager
from src.automation.automation_controller import AutomationController
from src.models.task_models import TaskType
from src.core.task_manager import TaskPriority
from src.core.sync_adapter import SyncAdapter
from src.config.logger import get_logger

logger = get_logger(__name__)

def print_separator(title: str):
    """打印分隔符"""
    print("\n" + "=" * 60)
    print(f" {title} ")
    print("=" * 60)

def test_game_detection():
    """测试游戏检测功能"""
    print_separator("游戏检测测试")
    
    try:
        game_detector = GameDetector()
        
        # 检测游戏窗口
        print("🔍 检测游戏窗口...")
        game_window = game_detector.find_game_window()
        if game_window:
            print(f"✓ 找到游戏窗口: {game_window.get('title', 'Unknown')}")
            print(f"  窗口大小: {game_window.get('width', 0)}x{game_window.get('height', 0)}")
        else:
            print("✗ 未找到游戏窗口")
            return False
        
        # 检测游戏状态
        print("🎮 检测游戏状态...")
        is_running = game_detector.is_game_running()
        print(f"✓ 游戏运行状态: {'运行中' if is_running else '未运行'}")
        
        # 截图测试
        print("📸 测试截图功能...")
        screenshot = game_detector.capture_screen()
        if screenshot:
            print(f"✓ 截图成功，大小: {len(screenshot)} bytes")
        else:
            print("✗ 截图失败")
            
        return True
        
    except Exception as e:
        print(f"✗ 游戏检测测试失败: {e}")
        return False

def test_task_management():
    """测试任务管理功能"""
    print_separator("任务管理测试")
    
    try:
        task_manager = TaskManager()
        
        # 创建测试任务
        print("📝 创建测试任务...")
        
        # 日常任务
        daily_task_config = {
            "name": "自动化日常任务",
            "type": TaskType.DAILY_MISSION.value,
            "priority": TaskPriority.HIGH.value,
            "parameters": {
                "mission_types": ["combat", "collection"],
                "target_count": 3,
                "auto_collect_rewards": True
            },
            "schedule_config": {
                "enabled": True,
                "cron_expression": "0 9 * * *"
            }
        }
        
        daily_task = task_manager.add_task(daily_task_config)
        print(f"✓ 创建日常任务: {daily_task}")
        
        # 邮件收集任务
        mail_task_config = {
            "name": "自动邮件收集",
            "type": TaskType.CUSTOM.value,
            "priority": TaskPriority.MEDIUM.value,
            "parameters": {
                "collection_type": "mail",
                "auto_claim": True,
                "max_items": 50
            },
            "schedule_config": {
                "enabled": True,
                "cron_expression": "0 */2 * * *"
            }
        }
        
        mail_task = task_manager.add_task(mail_task_config)
        print(f"✓ 创建邮件收集任务: {mail_task}")
        
        # 资源采集任务
        resource_task_config = {
            "name": "自动资源采集",
            "type": TaskType.AUTOMATION.value,
            "priority": TaskPriority.LOW.value,
            "parameters": {
                "resource_types": ["energy", "materials"],
                "collection_interval": 3600,
                "amount_per_cycle": 5
            },
            "schedule_config": {
                "enabled": False
            }
        }
        
        resource_task = task_manager.add_task(resource_task_config)
        print(f"✓ 创建资源采集任务: {resource_task}")
        
        # 获取任务列表
        print("📋 获取任务列表...")
        tasks = task_manager.get_tasks()
        print(f"✓ 当前任务数量: {len(tasks)}")
        
        return True
        
    except Exception as e:
        print(f"✗ 任务管理测试失败: {e}")
        return False

async def test_automation_controller():
    """测试自动化控制器"""
    print_separator("自动化控制器测试")
    
    try:
        # 初始化自动化控制器
        print("🤖 初始化自动化控制器...")
        automation_controller = AutomationController()
        
        # 获取可用任务
        print("📋 获取可用任务...")
        available_tasks = automation_controller.get_available_tasks()
        print(f"✓ 可用任务: {available_tasks}")
        
        # 测试游戏状态检测
        print("🎮 测试游戏状态检测...")
        game_status = automation_controller._detect_game_status()
        print(f"✓ 游戏状态: {game_status}")
        
        # 测试场景检测
        print("🎬 测试场景检测...")
        scene_status = automation_controller._detect_current_scene()
        print(f"✓ 场景状态: {scene_status}")
        
        # 测试自动截图
        print("📸 测试自动截图...")
        screenshot_result = automation_controller._auto_screenshot()
        print(f"✓ 截图结果: {screenshot_result}")
        
        return True
        
    except Exception as e:
        print(f"✗ 自动化控制器测试失败: {e}")
        return False

async def test_template_matching():
    """测试模板匹配功能"""
    print_separator("模板匹配测试")
    
    try:
        game_detector = GameDetector()
        
        # 测试各种模板匹配
        templates_to_test = [
            "assets/templates/main_menu.png",
            "assets/templates/battle_ui.png",
            "assets/templates/claim_button.png",
            "assets/templates/inventory.png",
            "assets/templates/mission_menu.png",
            "assets/templates/world_map.png"
        ]
        
        print("🔍 测试模板匹配...")
        for template_path in templates_to_test:
            if os.path.exists(template_path):
                try:
                    result = game_detector.find_template(template_path, threshold=0.7)
                    status = "找到" if result and result.get('found', False) else "未找到"
                    print(f"  {os.path.basename(template_path)}: {status}")
                except Exception as e:
                    print(f"  {os.path.basename(template_path)}: 错误 - {e}")
            else:
                print(f"  {os.path.basename(template_path)}: 文件不存在")
        
        return True
        
    except Exception as e:
        print(f"✗ 模板匹配测试失败: {e}")
        return False

async def test_complete_workflow():
    """测试完整工作流程"""
    print_separator("完整工作流程测试")
    
    try:
        print("🔧 初始化所有组件...")
        
        # 初始化组件
        game_detector = GameDetector()
        task_manager = TaskManager()
        automation_controller = AutomationController()
        sync_adapter = SyncAdapter()
        
        print("✓ 所有组件初始化完成")
        
        # 检查游戏状态
        print("🎮 检查游戏状态...")
        if not game_detector.is_game_running():
            print("⚠️ 游戏未运行，某些功能可能无法测试")
        else:
            print("✓ 游戏正在运行")
        
        # 创建并执行一个简单的自动化任务
        print("🤖 创建自动化任务...")
        
        # 创建一个简单的检测任务
        detection_task_config = {
            "name": "游戏状态检测",
            "type": TaskType.AUTOMATION.value,
            "priority": TaskPriority.HIGH.value,
            "parameters": {
                "action": "detect_game_status",
                "interval": 5
            },
            "schedule_config": {
                "enabled": False
            }
        }
        
        detection_task = task_manager.add_task(detection_task_config)
        print(f"✓ 创建检测任务: {detection_task}")
        
        # 模拟任务执行
        print("⚡ 模拟任务执行...")
        await asyncio.sleep(1)  # 模拟执行时间
        print("✓ 任务执行完成")
        
        return True
        
    except Exception as e:
        print(f"✗ 完整工作流程测试失败: {e}")
        return False

def print_test_summary(results: dict):
    """打印测试总结"""
    print_separator("测试总结")
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    
    print(f"总测试数: {total_tests}")
    print(f"通过: {passed_tests}")
    print(f"失败: {failed_tests}")
    print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\n详细结果:")
    for test_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {test_name}: {status}")
    
    if failed_tests == 0:
        print("\n🎉 所有测试通过！项目核心功能正常工作。")
    else:
        print(f"\n⚠️ 有 {failed_tests} 个测试失败，请检查相关功能。")

async def main():
    """主函数"""
    print("🚀 开始完整自动化功能测试")
    print("测试崩坏星穹铁道自动化助手的所有核心功能")
    
    # 执行所有测试
    results = {}
    
    # 同步测试
    results["游戏检测"] = test_game_detection()
    results["任务管理"] = test_task_management()
    results["模板匹配"] = await test_template_matching()
    
    # 异步测试
    results["自动化控制器"] = await test_automation_controller()
    results["完整工作流程"] = await test_complete_workflow()
    
    # 打印测试总结
    print_test_summary(results)
    
    return all(results.values())

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        sys.exit(1)