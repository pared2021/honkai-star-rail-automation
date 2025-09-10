#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI集成测试脚本（简化版）

测试UI组件的基本功能。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from loguru import logger


def test_ui_imports():
    """测试UI组件导入."""
    try:
        logger.info("开始测试UI组件导入...")
        
        # 测试任务列表组件导入
        from src.ui.task_list import TaskListView
        logger.info("✅ TaskListView 导入成功")
        
        # 测试任务进度组件导入
        from src.ui.task_progress import TaskProgressView
        logger.info("✅ TaskProgressView 导入成功")
        
        # 测试日志查看器组件导入
        from src.ui.log_viewer import LogViewerView
        logger.info("✅ LogViewerView 导入成功")
        
        logger.info("✅ 所有UI组件导入测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ UI组件导入测试失败: {str(e)}")
        return False


def test_ui_creation():
    """测试UI组件创建."""
    try:
        logger.info("开始测试UI组件创建...")
        
        # 检查是否已有QApplication实例
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 导入UI组件
        from src.ui.task_list import TaskListView
        from src.ui.task_progress import TaskProgressView
        from src.ui.log_viewer import LogViewerView
        
        # 创建UI组件
        task_list_view = TaskListView()
        logger.info("✅ TaskListView 创建成功")
        
        task_progress_view = TaskProgressView()
        logger.info("✅ TaskProgressView 创建成功")
        
        log_viewer_view = LogViewerView()
        logger.info("✅ LogViewerView 创建成功")
        
        # 显示组件
        task_list_view.show()
        task_progress_view.show()
        log_viewer_view.show()
        
        # 设置窗口位置
        task_list_view.move(100, 100)
        task_progress_view.move(500, 100)
        log_viewer_view.move(900, 100)
        
        logger.info("✅ 所有UI组件创建和显示测试通过")
        
        # 延迟关闭
        QTimer.singleShot(3000, lambda: (
            task_list_view.close(),
            task_progress_view.close(),
            log_viewer_view.close()
        ))
        
        # 运行事件循环3秒
        QTimer.singleShot(3000, app.quit)
        app.exec()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ UI组件创建测试失败: {str(e)}")
        return False


def test_backend_imports():
    """测试后端组件导入."""
    try:
        logger.info("开始测试后端组件导入...")
        
        # 测试核心组件导入
        from src.core.task_manager import TaskManager
        logger.info("✅ TaskManager 导入成功")
        
        from src.automation.automation_controller import AutomationController
        logger.info("✅ AutomationController 导入成功")
        
        from src.core.game_detector import GameDetector
        logger.info("✅ GameDetector 导入成功")
        
        # 测试应用服务导入
        from src.application.task_service import TaskService
        logger.info("✅ TaskService 导入成功")
        
        logger.info("✅ 所有后端组件导入测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 后端组件导入测试失败: {str(e)}")
        return False


def main():
    """主函数."""
    try:
        # 设置日志
        logger.add("test_ui_integration.log", rotation="10 MB")
        logger.info("开始UI集成测试")
        
        # 运行测试
        tests = [
            ("后端组件导入", test_backend_imports),
            ("UI组件导入", test_ui_imports),
            ("UI组件创建", test_ui_creation)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n{'='*50}")
            logger.info(f"运行测试: {test_name}")
            logger.info(f"{'='*50}")
            
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name} 测试通过")
            else:
                logger.error(f"❌ {test_name} 测试失败")
        
        # 输出测试结果
        logger.info(f"\n{'='*50}")
        logger.info(f"测试结果: {passed}/{total} 通过")
        logger.info(f"{'='*50}")
        
        if passed == total:
            logger.info("🎉 所有测试通过！UI集成测试成功！")
            return 0
        else:
            logger.error(f"❌ {total - passed} 个测试失败")
            return 1
        
    except Exception as e:
        logger.error(f"测试运行失败: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())