# -*- coding: utf-8 -*-
"""
数据库管理器单元测试
"""

import unittest
import tempfile
import os
from datetime import datetime

# 添加项目根目录到路径
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database.db_manager import DatabaseManager
from src.models.task_model import Task, TaskStatus, TaskType, TaskPriority
from src.core.task_manager import TaskConfig


class TestDatabaseManager(unittest.TestCase):
    """数据库管理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # 初始化数据库管理器
        self.db_manager = DatabaseManager(db_path=self.temp_db.name)
        self.db_manager.initialize_database()
    
    def tearDown(self):
        """测试后清理"""
        # 删除临时数据库文件
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """测试数据库初始化"""
        # 验证数据库文件存在
        self.assertTrue(os.path.exists(self.temp_db.name))
        
        # 验证表是否创建
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查用户表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            self.assertIsNotNone(cursor.fetchone())
            
            # 检查任务表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
            self.assertIsNotNone(cursor.fetchone())
            
            # 检查任务配置表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='task_configs'")
            self.assertIsNotNone(cursor.fetchone())
            
            # 检查执行日志表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='execution_logs'")
            self.assertIsNotNone(cursor.fetchone())
            
            # 检查用户配置表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_configs'")
            self.assertIsNotNone(cursor.fetchone())
    
    def test_create_user(self):
        """测试创建用户"""
        user_id = "test_user"
        username = "测试用户"
        email = "test@example.com"
        
        # 创建用户
        success = self.db_manager.create_user(
            user_id=user_id,
            username=username,
            email=email
        )
        
        self.assertTrue(success)
        
        # 验证用户是否创建成功
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, username, email FROM users WHERE user_id = ?",
                (user_id,)
            )
            result = cursor.fetchone()
            
            self.assertIsNotNone(result)
            self.assertEqual(result[0], user_id)
            self.assertEqual(result[1], username)
            self.assertEqual(result[2], email)
    
    def test_create_duplicate_user(self):
        """测试创建重复用户"""
        user_id = "duplicate_user"
        username = "重复用户"
        email = "duplicate@example.com"
        
        # 第一次创建应该成功
        success1 = self.db_manager.create_user(
            user_id=user_id,
            username=username,
            email=email
        )
        self.assertTrue(success1)
        
        # 第二次创建相同用户应该失败
        success2 = self.db_manager.create_user(
            user_id=user_id,
            username=username,
            email=email
        )
        self.assertFalse(success2)
    
    def test_task_operations(self):
        """测试任务相关操作"""
        # 先创建用户
        user_id = "task_test_user"
        self.db_manager.create_user(
            user_id=user_id,
            username="任务测试用户",
            email="tasktest@example.com"
        )
        
        # 创建任务配置
        config = TaskConfig(
            name="数据库测试任务",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            description="这是一个数据库测试任务",
            max_duration=300,
            retry_count=3,
            retry_interval=10,
            safe_mode=True
        )
        
        # 创建任务
        task_id = "test_task_001"
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 插入任务配置
            cursor.execute("""
                INSERT INTO task_configs (
                    task_id, name, task_type, priority, description,
                    max_duration, retry_count, retry_interval, safe_mode,
                    actions, custom_params
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id, config.name, config.task_type.value, config.priority.value,
                config.description, config.max_duration, config.retry_count,
                config.retry_interval, config.safe_mode, 
                config.actions or "", config.custom_params or ""
            ))
            
            # 插入任务
            cursor.execute("""
                INSERT INTO tasks (
                    task_id, user_id, status, created_at
                ) VALUES (?, ?, ?, ?)
            """, (
                task_id, user_id, TaskStatus.CREATED.value, datetime.now()
            ))
            
            conn.commit()
        
        # 验证任务是否创建成功
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查任务
            cursor.execute(
                "SELECT task_id, user_id, status FROM tasks WHERE task_id = ?",
                (task_id,)
            )
            task_result = cursor.fetchone()
            
            self.assertIsNotNone(task_result)
            self.assertEqual(task_result[0], task_id)
            self.assertEqual(task_result[1], user_id)
            self.assertEqual(task_result[2], TaskStatus.CREATED.value)
            
            # 检查任务配置
            cursor.execute(
                "SELECT name, task_type, priority FROM task_configs WHERE task_id = ?",
                (task_id,)
            )
            config_result = cursor.fetchone()
            
            self.assertIsNotNone(config_result)
            self.assertEqual(config_result[0], config.name)
            self.assertEqual(config_result[1], config.task_type.value)
            self.assertEqual(config_result[2], config.priority.value)
    
    def test_execution_log(self):
        """测试执行日志"""
        # 先创建用户和任务
        user_id = "log_test_user"
        task_id = "log_test_task"
        
        self.db_manager.create_user(
            user_id=user_id,
            username="日志测试用户",
            email="logtest@example.com"
        )
        
        # 创建执行日志
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO execution_logs (
                    task_id, user_id, action_type, action_data,
                    execution_time, success, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id, user_id, "click", "{'x': 100, 'y': 200}",
                datetime.now(), True, None
            ))
            
            conn.commit()
        
        # 验证日志是否创建成功
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT task_id, action_type, success FROM execution_logs WHERE task_id = ?",
                (task_id,)
            )
            result = cursor.fetchone()
            
            self.assertIsNotNone(result)
            self.assertEqual(result[0], task_id)
            self.assertEqual(result[1], "click")
            self.assertTrue(result[2])
    
    def test_user_config(self):
        """测试用户配置"""
        user_id = "config_test_user"
        
        # 创建用户
        self.db_manager.create_user(
            user_id=user_id,
            username="配置测试用户",
            email="configtest@example.com"
        )
        
        # 创建用户配置
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO user_configs (
                    user_id, config_key, config_value
                ) VALUES (?, ?, ?)
            """, (
                user_id, "theme", "dark"
            ))
            
            cursor.execute("""
                INSERT INTO user_configs (
                    user_id, config_key, config_value
                ) VALUES (?, ?, ?)
            """, (
                user_id, "auto_save", "true"
            ))
            
            conn.commit()
        
        # 验证配置是否创建成功
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT config_key, config_value FROM user_configs WHERE user_id = ? ORDER BY config_key",
                (user_id,)
            )
            results = cursor.fetchall()
            
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0][0], "auto_save")
            self.assertEqual(results[0][1], "true")
            self.assertEqual(results[1][0], "theme")
            self.assertEqual(results[1][1], "dark")
    
    def test_connection_context_manager(self):
        """测试连接上下文管理器"""
        # 测试正常使用
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)
        
        # 测试异常处理
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                raise Exception("测试异常")
        except Exception as e:
            self.assertEqual(str(e), "测试异常")
        
        # 连接应该仍然可用
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)


if __name__ == '__main__':
    unittest.main()