# -*- coding: utf-8 -*-
"""
任务监控器单元测试
"""

import unittest
import tempfile
import os
import time
from unittest.mock import Mock, patch, MagicMock
from PyQt5.QtCore import QCoreApplication, QTimer
from PyQt5.QtTest import QTest

# 添加项目根目录到路径
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.monitoring.task_monitor import TaskMonitor
from src.automation.automation_controller import AutomationController
from src.automation.game_detector import GameDetector
from src.models.task_model import Task, TaskStatus, TaskPriority
from src.core.enums import TaskType
from src.core.task_manager import TaskManager, TaskConfig
from src.database.db_manager import DatabaseManager
from src.core.config_manager import ConfigManager, ConfigType


class TestTaskMonitor(unittest.TestCase):
    """任务监控器测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        # 创建QApplication实例（如果不存在）
        if not QCoreApplication.instance():
            cls.app = QCoreApplication([])
        else:
            cls.app = QCoreApplication.instance()
    
    def setUp(self):
        """测试前准备"""
        # 创建临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # 创建临时配置文件
        self.temp_config = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_config.close()
        
        # 初始化管理器
        self.db_manager = DatabaseManager(db_path=self.temp_db.name)
        self.db_manager.initialize_database()
        
        self.config_manager = ConfigManager(config_dir=os.path.dirname(self.temp_config.name))
        self.task_manager = TaskManager(self.config_manager, self.db_manager)
        
        # 模拟配置方法
        def mock_get_config(config_type):
            if config_type == ConfigType.UI_PREFERENCES:
                return {
                    'update_interval': 1000,
                    'max_history': 100
                }
            return {}
        
        self.config_manager.get_config = Mock(side_effect=mock_get_config)
        
        # 初始化游戏检测器
        self.game_detector = GameDetector(self.config_manager)
        
        # 初始化自动化控制器
        self.automation_controller = AutomationController(
            self.config_manager, 
            self.db_manager,
            self.game_detector
        )
        
        # 初始化任务监控器
        self.task_monitor = TaskMonitor(
            self.db_manager,
            self.automation_controller
        )
    
    def tearDown(self):
        """测试后清理"""
        # 停止监控器
        if self.task_monitor.is_monitoring:
            self.task_monitor.stop_monitoring()
        
        # 停止自动化控制器
        if self.automation_controller.task_status == TaskStatus.RUNNING:
            self.automation_controller.stop_task()
        
        # 删除临时文件
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
        if os.path.exists(self.temp_config.name):
            os.unlink(self.temp_config.name)
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.task_monitor.config_manager)
        self.assertIsNotNone(self.task_monitor.db_manager)
        self.assertIsNotNone(self.task_monitor.automation_controller)
        self.assertFalse(self.task_monitor.is_monitoring)
        self.assertIsNotNone(self.task_monitor.status_queue)
        self.assertIsNone(self.task_monitor.monitor_thread)
    
    def test_start_stop_monitoring(self):
        """测试启动和停止监控"""
        # 测试启动监控
        self.task_monitor.start_monitoring()
        self.assertTrue(self.task_monitor.is_monitoring)
        self.assertIsNotNone(self.task_monitor.monitor_thread)
        self.assertTrue(self.task_monitor.monitor_thread.is_alive())
        
        # 测试重复启动
        self.task_monitor.start_monitoring()
        self.assertTrue(self.task_monitor.is_monitoring)
        
        # 测试停止监控
        self.task_monitor.stop_monitoring()
        self.assertFalse(self.task_monitor.is_monitoring)
        
        # 等待线程结束
        if self.task_monitor.monitor_thread:
            self.task_monitor.monitor_thread.join(timeout=1.0)
        
        # 测试重复停止
        self.task_monitor.stop_monitoring()
        self.assertFalse(self.task_monitor.is_monitoring)
    
    def test_get_task_status(self):
        """测试获取任务状态"""
        # 创建测试任务
        config = TaskConfig(
            name="监控测试任务",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            description="监控测试任务描述"
        )
        
        task_id = self.task_manager.create_task(config)
        
        # 获取任务状态
        status = self.task_monitor.get_task_status(task_id)
        self.assertEqual(status, TaskStatus.CREATED)
        
        # 更新任务状态
        self.automation_controller.update_task_status(task_id, TaskStatus.RUNNING)
        
        # 再次获取任务状态
        status = self.task_monitor.get_task_status(task_id)
        self.assertEqual(status, TaskStatus.RUNNING)
        
        # 测试获取不存在任务的状态
        status = self.task_monitor.get_task_status("non_existent_task")
        self.assertIsNone(status)
    
    def test_update_task_progress(self):
        """测试更新任务进度"""
        # 创建测试任务
        config = TaskConfig(
            name="进度测试任务",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            description="进度测试任务描述"
        )
        
        task_id = self.task_manager.create_task(config)
        
        # 更新任务进度
        self.task_monitor.update_task_progress(task_id, 50, "执行中...")
        
        # 验证进度更新（这里主要测试方法不会抛出异常）
        # 实际的进度验证需要通过信号来测试
        self.assertTrue(True)  # 如果没有异常，测试通过
    
    def test_signal_emission(self):
        """测试信号发射"""
        # 创建信号接收器
        status_changed_calls = []
        progress_updated_calls = []
        message_updated_calls = []
        task_completed_calls = []
        
        def on_status_changed(task_id, status):
            status_changed_calls.append((task_id, status))
        
        def on_progress_updated(task_id, progress, message):
            progress_updated_calls.append((task_id, progress, message))
        
        def on_message_updated(task_id, message):
            message_updated_calls.append((task_id, message))
        
        def on_task_completed(task_id, success, message):
            task_completed_calls.append((task_id, success, message))
        
        # 连接信号
        self.task_monitor.task_status_changed.connect(on_status_changed)
        self.task_monitor.task_progress_updated.connect(on_progress_updated)
        self.task_monitor.task_message_updated.connect(on_message_updated)
        self.task_monitor.task_completed.connect(on_task_completed)
        
        # 创建测试任务
        config = TaskConfig(
            name="信号测试任务",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            description="信号测试任务描述"
        )
        
        task_id = self.task_manager.create_task(config)
        
        # 更新任务进度
        self.task_monitor.update_task_progress(task_id, 25, "开始执行")
        
        # 处理事件循环以确保信号被发射
        QTest.qWait(10)
        
        # 验证信号是否被发射
        self.assertEqual(len(progress_updated_calls), 1)
        self.assertEqual(progress_updated_calls[0][0], task_id)
        self.assertEqual(progress_updated_calls[0][1], 25)
        self.assertEqual(progress_updated_calls[0][2], "开始执行")
    
    @patch('src.monitoring.task_monitor.TaskMonitor._monitor_loop')
    def test_monitoring_thread(self, mock_monitor_loop):
        """测试监控线程"""
        # 启动监控
        self.task_monitor.start_monitoring()
        
        # 等待线程启动
        time.sleep(0.1)
        
        # 验证监控循环被调用
        mock_monitor_loop.assert_called()
        
        # 停止监控
        self.task_monitor.stop_monitoring()
    
    def test_status_queue_operations(self):
        """测试状态队列操作"""
        # 创建测试任务
        config = TaskConfig(
            name="队列测试任务",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            description="队列测试任务描述"
        )
        
        task_id = self.task_manager.create_task(config)
        
        # 添加状态更新到队列
        status_update = {
            'type': 'status_change',
            'task_id': task_id,
            'status': TaskStatus.RUNNING
        }
        
        self.task_monitor.status_queue.put(status_update)
        
        # 验证队列不为空
        self.assertFalse(self.task_monitor.status_queue.empty())
        
        # 从队列获取状态更新
        retrieved_update = self.task_monitor.status_queue.get()
        
        self.assertEqual(retrieved_update['type'], 'status_change')
        self.assertEqual(retrieved_update['task_id'], task_id)
        self.assertEqual(retrieved_update['status'], TaskStatus.RUNNING)
        
        # 验证队列为空
        self.assertTrue(self.task_monitor.status_queue.empty())
    
    def test_monitor_with_automation_controller(self):
        """测试与自动化控制器的集成"""
        # 创建测试任务
        config = TaskConfig(
            name="集成测试任务",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            description="集成测试任务描述"
        )
        
        task_id = self.task_manager.create_task(config)
        
        # 添加任务到自动化控制器队列
        self.automation_controller.add_task_to_queue(task_id)
        
        # 启动监控
        self.task_monitor.start_monitoring()
        
        # 更新任务状态
        self.automation_controller.update_task_status(task_id, TaskStatus.RUNNING)
        
        # 等待监控器处理
        time.sleep(0.1)
        
        # 验证监控器能够获取到更新的状态
        status = self.task_monitor.get_task_status(task_id)
        self.assertEqual(status, TaskStatus.RUNNING)
        
        # 停止监控
        self.task_monitor.stop_monitoring()
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试获取不存在任务的状态
        status = self.task_monitor.get_task_status("invalid_task_id")
        self.assertIsNone(status)
        
        # 测试更新不存在任务的进度
        try:
            self.task_monitor.update_task_progress("invalid_task_id", 50, "测试")
            # 如果没有抛出异常，测试通过
            self.assertTrue(True)
        except Exception as e:
            # 如果抛出异常，确保是预期的异常类型
            self.fail(f"Unexpected exception: {e}")
    
    def test_multiple_task_monitoring(self):
        """测试多任务监控"""
        # 创建多个测试任务
        configs = [
            TaskConfig(
                name=f"多任务测试{i}",
                task_type=TaskType.DAILY_MISSION,
                priority=TaskPriority.HIGH,
                description=f"多任务测试{i}描述"
            ) for i in range(3)
        ]
        
        task_ids = []
        for config in configs:
            task_id = self.task_manager.create_task(config)
            task_ids.append(task_id)
            self.automation_controller.add_task_to_queue(task_id)
        
        # 启动监控
        self.task_monitor.start_monitoring()
        
        # 更新所有任务状态
        for i, task_id in enumerate(task_ids):
            status = TaskStatus.RUNNING if i % 2 == 0 else TaskStatus.COMPLETED
            self.automation_controller.update_task_status(task_id, status)
        
        # 等待监控器处理
        time.sleep(0.1)
        
        # 验证所有任务状态
        for i, task_id in enumerate(task_ids):
            expected_status = TaskStatus.RUNNING if i % 2 == 0 else TaskStatus.COMPLETED
            actual_status = self.task_monitor.get_task_status(task_id)
            self.assertEqual(actual_status, expected_status)
        
        # 停止监控
        self.task_monitor.stop_monitoring()


if __name__ == '__main__':
    unittest.main()