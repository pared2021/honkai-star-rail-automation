#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import pytest

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


class TestTaskManagerIntegration:
    """TaskManager集成测试"""
    
    def test_task_manager_adapter_import(self):
        """测试 TaskManagerAdapter 导入"""
        from src.adapters.task_manager_adapter import TaskManagerAdapter
        assert TaskManagerAdapter is not None
    
    def test_get_task_sync_method_exists(self):
        """检查 get_task_sync 方法存在"""
        from src.adapters.task_manager_adapter import TaskManagerAdapter
        
        has_method = hasattr(TaskManagerAdapter, 'get_task_sync')
        assert has_method, "get_task_sync 方法不存在"
        
        method = getattr(TaskManagerAdapter, 'get_task_sync')
        assert callable(method), "get_task_sync 方法不可调用"
    
    def test_database_manager_import(self):
        """测试 DatabaseManager 导入"""
        from src.database.db_manager import DatabaseManager
        assert DatabaseManager is not None
    
    def test_create_instances(self):
        """测试创建实例"""
        from src.database.db_manager import DatabaseManager
        from src.adapters.task_manager_adapter import TaskManagerAdapter
        
        db_manager = DatabaseManager()
        assert db_manager is not None
        
        task_manager = TaskManagerAdapter(db_manager)
        assert task_manager is not None
    
    def test_instance_methods(self):
        """检查实例方法"""
        from src.database.db_manager import DatabaseManager
        from src.adapters.task_manager_adapter import TaskManagerAdapter
        
        db_manager = DatabaseManager()
        task_manager = TaskManagerAdapter(db_manager)
        
        instance_has_method = hasattr(task_manager, 'get_task_sync')
        assert instance_has_method, "实例不具有 get_task_sync 方法"
        
        instance_method = getattr(task_manager, 'get_task_sync')
        assert callable(instance_method), "实例方法不可调用"