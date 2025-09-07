#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
功能测试脚本
测试修复后的核心功能是否正常工作
"""

import sys
from pathlib import Path
import asyncio
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.game_detector import GameDetector, SceneType
from src.core.task_manager import TaskManager, TaskType, TaskPriority
from src.automation.automation_controller import AutomationController
from src.monitoring.health_checker import HealthChecker
from src.monitoring.metrics_collector import MetricsCollector

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def test_game_detector():
    """测试游戏检测功能"""
    logger.info("开始测试游戏检测功能")
    
    try:
        detector = GameDetector()
        
        # 测试游戏是否运行
        is_running = detector.is_game_running()
        logger.info(f"游戏是否运行: {is_running}")
        
        if detector.game_window:
            logger.info(f"找到游戏窗口: {detector.game_window.title}")
        else:
            logger.info("未找到游戏窗口")
        
        # 测试场景检测
        current_scene = detector.detect_scene()
        logger.info(f"当前场景: {current_scene}")
        
        # 测试UI元素检测
        ui_elements = detector.detect_ui_elements(["inventory_bag_icon", "main_menu_start_button"])
        logger.info(f"检测到UI元素数量: {len(ui_elements)}")
        
        logger.info("游戏检测功能测试完成")
        return True
        
    except Exception as e:
        logger.error(f"游戏检测功能测试失败: {e}")
        return False

def test_task_manager():
    """测试任务管理功能"""
    logger.info("开始测试任务管理功能")
    
    try:
        task_manager = TaskManager()
        
        # 添加测试任务
        task_data = {
            'name': '测试任务',
            'type': 'test',
            'description': '这是一个测试任务',
            'priority': 'medium'
        }
        task_id = task_manager.add_task(task_data)
        logger.info(f"添加任务成功，任务ID: {task_id}")
        
        # 启动并发管理器
        task_manager.start_concurrent_manager()
        logger.info("并发管理器启动成功")
        
        # 等待一下让任务执行
        import time
        time.sleep(2)
        
        # 获取任务列表
        import asyncio
        tasks = asyncio.run(task_manager.list_tasks())
        logger.info(f"当前任务数量: {len(tasks)}")
        
        # 获取任务统计
        stats = asyncio.run(task_manager.get_task_statistics())
        logger.info(f"任务统计: {stats}")
        
        # 停止并发管理器
        task_manager.stop_concurrent_manager()
        logger.info("并发管理器停止成功")
        
        logger.info("任务管理功能测试完成")
        return True
        
    except Exception as e:
        logger.error(f"任务管理功能测试失败: {e}")
        return False

def test_automation_controller():
    """测试自动化控制器功能"""
    logger.info("开始测试自动化控制器功能")
    
    try:
        controller = AutomationController()
        
        # 启动控制器
        controller.start()
        logger.info("自动化控制器启动成功")
        
        # 执行基本任务（游戏检测）
        result = controller.execute("game_detection")
        logger.info(f"执行游戏检测任务结果: {result}")
        
        # 执行动作
        action_result = controller.execute_action("click", x=100, y=200)
        logger.info(f"执行点击动作结果: {action_result}")
        
        # 停止控制器
        controller.stop()
        logger.info("自动化控制器停止成功")
        
        logger.info("自动化控制器功能测试完成")
        return True
        
    except Exception as e:
        logger.error(f"自动化控制器功能测试失败: {e}")
        return False

def test_monitoring_system():
    """测试监控系统功能"""
    logger.info("开始测试监控系统功能")
    
    try:
        health_checker = HealthChecker()
        
        # 创建基本检查
        health_checker.create_basic_checks()
        logger.info("基本健康检查创建成功")
        
        # 执行健康检查
        health_results = health_checker.check_health()
        logger.info(f"健康检查结果: {len(health_results) if isinstance(health_results, dict) else 1} 项检查")
        
        # 获取整体状态
        overall_status = health_checker.get_overall_status()
        logger.info(f"整体健康状态: {overall_status}")
        
        # 启动监控
        health_checker.start_monitoring()
        logger.info("监控系统启动成功")
        
        # 等待一下让监控运行
        import time
        time.sleep(2)
        
        # 停止监控
        health_checker.stop_monitoring()
        logger.info("监控系统停止成功")
        
        logger.info("监控系统功能测试完成")
        return True
        
    except Exception as e:
        logger.error(f"监控系统功能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    logger.info("开始功能测试")
    logger.info("=" * 50)
    
    test_results = {
        "游戏检测": test_game_detector(),
        "任务管理": test_task_manager(),
        "自动化控制器": test_automation_controller(),
        "监控系统": test_monitoring_system()
    }
    
    logger.info("=" * 50)
    logger.info("测试结果汇总:")
    
    all_passed = True
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    logger.info("=" * 50)
    if all_passed:
        logger.info("🎉 所有功能测试通过！系统已修复并可正常使用")
    else:
        logger.info("⚠️ 部分功能测试失败，需要进一步修复")
    
    return all_passed

if __name__ == "__main__":
    main()