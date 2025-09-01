# -*- coding: utf-8 -*-
"""
自动化控制器单元测试
"""

import unittest
import tempfile
import os
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# 添加项目根目录到路径
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.automation.automation_controller import AutomationController
from src.models.task_models import Task, TaskStatus, TaskType, TaskPriority
from src.core.task_manager import TaskManager, TaskConfig
from src.database.db_manager import DatabaseManager
from src.config.config_manager import ConfigManager


class TestAutomationController(unittest.TestCase):
    """自动化控制器测试类"""
    
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
        
        self.config_manager = ConfigManager(config_path=self.temp_config.name)
        self.task_manager = TaskManager(self.config_manager, self.db_manager)
        
        # 初始化自动化控制器
        self.automation_controller = AutomationController(
            self.config_manager, 
            self.db_manager
        )
    
    def tearDown(self):
        """测试后清理"""
        # 停止自动化控制器
        if self.automation_controller.is_running:
            self.automation_controller.stop()
        
        # 删除临时文件
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
        if os.path.exists(self.temp_config.name):
            os.unlink(self.temp_config.name)
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.automation_controller.config_manager)
        self.assertIsNotNone(self.automation_controller.db_manager)
        self.assertFalse(self.automation_controller.is_running)
        self.assertIsNone(self.automation_controller.current_task_id)
        self.assertEqual(len(self.automation_controller.task_queue), 0)
    
    def test_start_stop(self):
        """测试启动和停止"""
        # 测试启动
        self.automation_controller.start()
        self.assertTrue(self.automation_controller.is_running)
        
        # 测试重复启动
        self.automation_controller.start()
        self.assertTrue(self.automation_controller.is_running)
        
        # 测试停止
        self.automation_controller.stop()
        self.assertFalse(self.automation_controller.is_running)
        
        # 测试重复停止
        self.automation_controller.stop()
        self.assertFalse(self.automation_controller.is_running)
    
    def test_add_task_to_queue(self):
        """测试添加任务到队列"""
        # 创建测试任务
        config = TaskConfig(
            name="测试任务",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            description="测试任务描述"
        )
        
        task_id = self.task_manager.create_task(config)
        self.assertIsNotNone(task_id)
        
        # 添加任务到队列
        success = self.automation_controller.add_task_to_queue(task_id)
        self.assertTrue(success)
        self.assertEqual(len(self.automation_controller.task_queue), 1)
        
        # 测试添加不存在的任务
        success = self.automation_controller.add_task_to_queue("non_existent_task")
        self.assertFalse(success)
        self.assertEqual(len(self.automation_controller.task_queue), 1)
        
        # 测试添加重复任务
        success = self.automation_controller.add_task_to_queue(task_id)
        self.assertFalse(success)
        self.assertEqual(len(self.automation_controller.task_queue), 1)
    
    def test_remove_task_from_queue(self):
        """测试从队列移除任务"""
        # 创建测试任务
        config = TaskConfig(
            name="测试任务",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            description="测试任务描述"
        )
        
        task_id = self.task_manager.create_task(config)
        
        # 添加任务到队列
        self.automation_controller.add_task_to_queue(task_id)
        self.assertEqual(len(self.automation_controller.task_queue), 1)
        
        # 从队列移除任务
        success = self.automation_controller.remove_task_from_queue(task_id)
        self.assertTrue(success)
        self.assertEqual(len(self.automation_controller.task_queue), 0)
        
        # 测试移除不存在的任务
        success = self.automation_controller.remove_task_from_queue("non_existent_task")
        self.assertFalse(success)
    
    def test_get_task_status(self):
        """测试获取任务状态"""
        # 创建测试任务
        config = TaskConfig(
            name="测试任务",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            description="测试任务描述"
        )
        
        task_id = self.task_manager.create_task(config)
        
        # 获取任务状态
        status = self.automation_controller.get_task_status(task_id)
        self.assertEqual(status, TaskStatus.CREATED)
        
        # 测试获取不存在任务的状态
        status = self.automation_controller.get_task_status("non_existent_task")
        self.assertIsNone(status)
    
    def test_update_task_status(self):
        """测试更新任务状态"""
        # 创建测试任务
        config = TaskConfig(
            name="测试任务",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            description="测试任务描述"
        )
        
        task_id = self.task_manager.create_task(config)
        
        # 更新任务状态
        success = self.automation_controller.update_task_status(task_id, TaskStatus.RUNNING)
        self.assertTrue(success)
        
        # 验证状态更新
        status = self.automation_controller.get_task_status(task_id)
        self.assertEqual(status, TaskStatus.RUNNING)
        
        # 测试更新不存在任务的状态
        success = self.automation_controller.update_task_status("non_existent_task", TaskStatus.RUNNING)
        self.assertFalse(success)
    
    def test_get_queue_status(self):
        """测试获取队列状态"""
        # 初始状态
        status = self.automation_controller.get_queue_status()
        self.assertEqual(status['total_tasks'], 0)
        self.assertEqual(status['pending_tasks'], 0)
        self.assertEqual(status['running_tasks'], 0)
        self.assertEqual(status['completed_tasks'], 0)
        self.assertEqual(status['failed_tasks'], 0)
        
        # 创建测试任务
        config1 = TaskConfig(
            name="测试任务1",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            description="测试任务1描述"
        )
        
        config2 = TaskConfig(
            name="测试任务2",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.MEDIUM,
            description="测试任务2描述"
        )
        
        task_id1 = self.task_manager.create_task(config1)
        task_id2 = self.task_manager.create_task(config2)
        
        # 添加任务到队列
        self.automation_controller.add_task_to_queue(task_id1)
        self.automation_controller.add_task_to_queue(task_id2)
        
        # 更新任务状态
        self.automation_controller.update_task_status(task_id1, TaskStatus.RUNNING)
        self.automation_controller.update_task_status(task_id2, TaskStatus.COMPLETED)
        
        # 获取队列状态
        status = self.automation_controller.get_queue_status()
        self.assertEqual(status['total_tasks'], 2)
        self.assertEqual(status['running_tasks'], 1)
        self.assertEqual(status['completed_tasks'], 1)
    
    def test_clear_queue(self):
        """测试清空队列"""
        # 创建测试任务
        config = TaskConfig(
            name="测试任务",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            description="测试任务描述"
        )
        
        task_id = self.task_manager.create_task(config)
        
        # 添加任务到队列
        self.automation_controller.add_task_to_queue(task_id)
        self.assertEqual(len(self.automation_controller.task_queue), 1)
        
        # 清空队列
        self.automation_controller.clear_queue()
        self.assertEqual(len(self.automation_controller.task_queue), 0)
    
    @patch('src.automation.automation_controller.AutomationController._execute_task')
    def test_task_execution_flow(self, mock_execute):
        """测试任务执行流程"""
        # 模拟任务执行成功
        mock_execute.return_value = True
        
        # 创建测试任务
        config = TaskConfig(
            name="测试任务",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            description="测试任务描述"
        )
        
        task_id = self.task_manager.create_task(config)
        
        # 添加任务到队列并启动
        self.automation_controller.add_task_to_queue(task_id)
        self.automation_controller.start()
        
        # 等待任务执行
        time.sleep(0.1)
        
        # 验证任务执行被调用
        mock_execute.assert_called()
        
        # 停止控制器
        self.automation_controller.stop()
    
    def test_task_priority_ordering(self):
        """测试任务优先级排序"""
        # 创建不同优先级的任务
        config_low = TaskConfig(
            name="低优先级任务",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.LOW,
            description="低优先级任务描述"
        )
        
        config_high = TaskConfig(
            name="高优先级任务",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            description="高优先级任务描述"
        )
        
        config_medium = TaskConfig(
            name="中优先级任务",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.MEDIUM,
            description="中优先级任务描述"
        )
        
        task_id_low = self.task_manager.create_task(config_low)
        task_id_high = self.task_manager.create_task(config_high)
        task_id_medium = self.task_manager.create_task(config_medium)
        
        # 按低、高、中的顺序添加任务
        self.automation_controller.add_task_to_queue(task_id_low)
        self.automation_controller.add_task_to_queue(task_id_high)
        self.automation_controller.add_task_to_queue(task_id_medium)
        
        # 验证队列中任务的顺序（应该按优先级排序）
        queue = self.automation_controller.task_queue
        self.assertEqual(len(queue), 3)
        
        # 获取任务配置来验证优先级顺序
        first_task = self.task_manager.get_task(queue[0])
        second_task = self.task_manager.get_task(queue[1])
        third_task = self.task_manager.get_task(queue[2])
        
        # 应该按照高、中、低的优先级顺序
        self.assertEqual(first_task.priority, TaskPriority.HIGH)
        self.assertEqual(second_task.priority, TaskPriority.MEDIUM)
        self.assertEqual(third_task.priority, TaskPriority.LOW)
    
    def test_signal_emission(self):
        """测试信号发射"""
        # 创建信号接收器
        status_changed_calls = []
        task_started_calls = []
        task_completed_calls = []
        
        def on_status_changed(task_id, status):
            status_changed_calls.append((task_id, status))
        
        def on_task_started(task_id):
            task_started_calls.append(task_id)
        
        def on_task_completed(task_id, success):
            task_completed_calls.append((task_id, success))
        
        # 连接信号
        self.automation_controller.task_status_changed.connect(on_status_changed)
        self.automation_controller.task_started.connect(on_task_started)
        self.automation_controller.task_completed.connect(on_task_completed)
        
        # 创建测试任务
        config = TaskConfig(
            name="信号测试任务",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            description="信号测试任务描述"
        )
        
        task_id = self.task_manager.create_task(config)
        
        # 更新任务状态
        self.automation_controller.update_task_status(task_id, TaskStatus.RUNNING)
        
        # 验证信号是否被发射
        self.assertEqual(len(status_changed_calls), 1)
        self.assertEqual(status_changed_calls[0][0], task_id)
        self.assertEqual(status_changed_calls[0][1], TaskStatus.RUNNING)


if __name__ == '__main__':
    unittest.main()