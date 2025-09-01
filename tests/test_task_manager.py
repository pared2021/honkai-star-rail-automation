# -*- coding: utf-8 -*-
"""
任务管理器单元测试
"""

import unittest
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# 添加项目根目录和src目录到 Python 路径
import sys
project_root = os.path.join(os.path.dirname(__file__), '..')
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

from adapters.task_manager_adapter import TaskManagerAdapter
from database.db_manager import DatabaseManager
from src.models.task_models import Task, TaskConfig, TaskStatus, TaskType, TaskPriority


class TestTaskManager(unittest.TestCase):
    """任务管理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # 初始化数据库管理器
        self.db_manager = DatabaseManager(db_path=self.temp_db.name)
        self.db_manager.initialize_database()
        
        # 初始化任务管理器适配器
        self.task_manager = TaskManagerAdapter(self.db_manager)
        
        # 创建测试用户
        self.test_user_id = self.db_manager.create_user("测试用户")
    
    def tearDown(self):
        """测试后清理"""
        # 删除临时数据库文件
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_create_task_config(self):
        """测试创建任务配置"""
        config = TaskConfig(
            task_name="测试任务",
            task_type=TaskType.CUSTOM,
            priority=TaskPriority.MEDIUM,
            description="这是一个测试任务"
        )
        
        self.assertEqual(config.task_name, "测试任务")
        self.assertEqual(config.task_type, TaskType.CUSTOM)
        self.assertEqual(config.priority, TaskPriority.MEDIUM)
        self.assertEqual(config.description, "这是一个测试任务")
    
    def test_create_task(self):
        """测试创建任务"""
        config = TaskConfig(
            task_name="测试任务",
            task_type=TaskType.CUSTOM,
            priority=TaskPriority.HIGH
        )
        
        task_id = self.task_manager.create_task(
            user_id=self.test_user_id,
            config=config
        )
        
        self.assertIsNotNone(task_id)
        self.assertIsInstance(task_id, str)
        
        # 验证任务是否正确创建
        task = self.task_manager.get_task(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task.config.task_name, "测试任务")
        self.assertEqual(task.config.task_type, TaskType.CUSTOM)
        self.assertEqual(task.config.priority, TaskPriority.HIGH)
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.user_id, self.test_user_id)
    
    def test_get_task(self):
        """测试获取任务"""
        # 创建测试任务
        config = TaskConfig(
            task_name="获取测试任务",
            task_type=TaskType.CUSTOM,
            priority=TaskPriority.LOW
        )
        
        task_id = self.task_manager.create_task(
            user_id=self.test_user_id,
            config=config
        )
        
        # 获取任务
        task = self.task_manager.get_task(task_id)
        
        self.assertIsNotNone(task)
        self.assertEqual(task.task_id, task_id)
        self.assertEqual(task.config.task_name, "获取测试任务")
        
        # 测试获取不存在的任务
        non_existent_task = self.task_manager.get_task("non_existent_id")
        self.assertIsNone(non_existent_task)
    
    def test_update_task(self):
        """测试更新任务"""
        # 创建测试任务
        config = TaskConfig(
            task_name="原始任务",
            task_type=TaskType.CUSTOM,
            priority=TaskPriority.MEDIUM
        )
        
        task_id = self.task_manager.create_task(
            user_id=self.test_user_id,
            config=config
        )
        
        # 更新任务配置
        new_config = TaskConfig(
            task_name="更新后的任务",
            task_type=TaskType.CUSTOM,
            priority=TaskPriority.HIGH,
            description="任务已更新"
        )
        
        success = self.task_manager.update_task(task_id, new_config)
        self.assertTrue(success)
        
        # 验证更新结果
        updated_task = self.task_manager.get_task(task_id)
        self.assertEqual(updated_task.config.task_name, "更新后的任务")
        self.assertEqual(updated_task.config.priority, TaskPriority.HIGH)
        self.assertEqual(updated_task.config.description, "任务已更新")
        
        # 测试更新不存在的任务
        update_result = self.task_manager.update_task("non_existent_id", new_config)
        self.assertFalse(update_result)
    
    def test_delete_task(self):
        """测试删除任务"""
        # 创建测试任务
        config = TaskConfig(
            task_name="待删除任务",
            task_type=TaskType.CUSTOM,
            priority=TaskPriority.LOW
        )
        
        task_id = self.task_manager.create_task(
            user_id=self.test_user_id,
            config=config
        )
        
        # 验证任务存在
        task = self.task_manager.get_task(task_id)
        self.assertIsNotNone(task)
        
        # 删除任务
        success = self.task_manager.delete_task(task_id)
        self.assertTrue(success)
        
        # 验证任务已删除
        deleted_task = self.task_manager.get_task(task_id)
        self.assertIsNone(deleted_task)
        
        # 测试删除不存在的任务
        delete_result = self.task_manager.delete_task("non_existent_id")
        self.assertFalse(delete_result)
    
    def test_list_tasks(self):
        """测试列出任务"""
        # 创建多个测试任务
        configs = [
            TaskConfig(task_name="任务1", task_type=TaskType.CUSTOM, priority=TaskPriority.HIGH),
            TaskConfig(task_name="任务2", task_type=TaskType.CUSTOM, priority=TaskPriority.MEDIUM),
            TaskConfig(task_name="任务3", task_type=TaskType.CUSTOM, priority=TaskPriority.LOW)
        ]
        
        task_ids = []
        for config in configs:
            task_id = self.task_manager.create_task(
                user_id=self.test_user_id,
                config=config
            )
            task_ids.append(task_id)
        
        # 获取任务列表
        tasks = self.task_manager.list_tasks(user_id=self.test_user_id)
        
        self.assertEqual(len(tasks), 3)
        
        # 验证任务顺序（应该按创建时间排序）
        task_names = [task.config.task_name for task in tasks]
        self.assertIn("任务1", task_names)
        self.assertIn("任务2", task_names)
        self.assertIn("任务3", task_names)
        
        # 测试空用户的任务列表
        empty_tasks = self.task_manager.list_tasks(user_id="empty_user")
        self.assertEqual(len(empty_tasks), 0)
    
    def test_update_task_status(self):
        """测试更新任务状态"""
        # 创建测试任务
        config = TaskConfig(
            task_name="状态测试任务",
            task_type=TaskType.CUSTOM,
            priority=TaskPriority.MEDIUM
        )
        
        task_id = self.task_manager.create_task(
            user_id=self.test_user_id,
            config=config
        )
        
        # 更新任务状态为运行中
        success = self.task_manager.update_task_status(task_id, TaskStatus.RUNNING)
        self.assertTrue(success)
        
        # 验证状态更新
        task = self.task_manager.get_task(task_id)
        self.assertEqual(task.status, TaskStatus.RUNNING)
        self.assertIsNotNone(task.last_executed_at)
        
        # 更新任务状态为完成
        success = self.task_manager.update_task_status(task_id, TaskStatus.COMPLETED)
        self.assertTrue(success)
        
        # 验证状态更新
        task = self.task_manager.get_task(task_id)
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(task.last_executed_at)
        
        # 测试更新不存在任务的状态
        update_result = self.task_manager.update_task_status("non_existent_id", TaskStatus.FAILED)
        self.assertFalse(update_result)
    
    def test_task_validation(self):
        """测试任务验证"""
        # 测试无效的任务配置
        with self.assertRaises(ValueError):
            TaskConfig(
                task_name="",  # 空名称应该引发错误
                task_type=TaskType.CUSTOM,
                priority=TaskPriority.MEDIUM
            )
        
        with self.assertRaises(ValueError):
            TaskConfig(
                task_name="测试任务",
                task_type=TaskType.CUSTOM,
                priority=TaskPriority.MEDIUM,
                timeout_seconds=-1  # 负数应该引发错误
            )
        
        with self.assertRaises(ValueError):
            TaskConfig(
                task_name="测试任务",
                task_type=TaskType.CUSTOM,
                priority=TaskPriority.MEDIUM,
                max_retry_count=-1  # 负数应该引发错误
            )
    
    def test_task_scheduling(self):
        """测试任务调度"""
        # 创建计划任务
        scheduled_time = datetime.now() + timedelta(hours=1)
        config = TaskConfig(
            task_name="计划任务",
            task_type=TaskType.CUSTOM,
            priority=TaskPriority.MEDIUM,
            schedule_time="12:00"
        )
        
        task_id = self.task_manager.create_task(
            user_id=self.test_user_id,
            config=config
        )
        
        task = self.task_manager.get_task(task_id)
        self.assertEqual(task.config.schedule_time, "12:00")
    
    def test_task_repeat(self):
        """测试重复任务"""
        # 创建重复任务
        config = TaskConfig(
            task_name="重复任务",
            task_type=TaskType.CUSTOM,
            priority=TaskPriority.MEDIUM,
            schedule_enabled=True
        )
        
        task_id = self.task_manager.create_task(
            user_id=self.test_user_id,
            config=config
        )
        
        task = self.task_manager.get_task(task_id)
        self.assertEqual(task.config.schedule_enabled, True)


if __name__ == '__main__':
    unittest.main()