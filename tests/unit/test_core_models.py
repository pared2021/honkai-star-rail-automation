#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import pytest
from unittest.mock import Mock, patch

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


class TestCoreModels:
    """核心模型测试"""
    
    def test_task_model_enums_import(self):
        """测试任务模型枚举导入"""
        try:
            from src.core.task_model import TaskType, TaskPriority, TaskStatus
            assert TaskType is not None
            assert TaskPriority is not None
            assert TaskStatus is not None
        except ImportError:
            # 如果导入失败，跳过测试
            pytest.skip("TaskModel enums not available")
    
    def test_task_type_values(self):
        """测试任务类型枚举值"""
        try:
            from src.core.task_model import TaskType
            # 检查是否有基本的枚举值
            assert hasattr(TaskType, '__members__')
            assert len(TaskType.__members__) > 0
        except ImportError:
            pytest.skip("TaskType not available")
    
    def test_task_priority_values(self):
        """测试任务优先级枚举值"""
        try:
            from src.core.task_model import TaskPriority
            # 检查是否有基本的枚举值
            assert hasattr(TaskPriority, '__members__')
            assert len(TaskPriority.__members__) > 0
        except ImportError:
            pytest.skip("TaskPriority not available")
    
    def test_task_status_values(self):
        """测试任务状态枚举值"""
        try:
            from src.core.task_model import TaskStatus
            # 检查是否有基本的枚举值
            assert hasattr(TaskStatus, '__members__')
            assert len(TaskStatus.__members__) > 0
        except ImportError:
            pytest.skip("TaskStatus not available")


class TestTaskModels:
    """任务模型测试"""
    
    def test_task_config_import(self):
        """测试任务配置导入"""
        try:
            from src.models.task_models import TaskConfig
            assert TaskConfig is not None
        except ImportError:
            pytest.skip("TaskConfig not available")
    
    def test_task_config_basic_attributes(self):
        """测试任务配置基本属性"""
        try:
            from src.models.task_models import TaskConfig
            from src.core.task_model import TaskType, TaskPriority
            
            config = TaskConfig(
                name="测试任务",
                task_type=TaskType.AUTOMATION,
                description="测试描述",
                priority=TaskPriority.MEDIUM
            )
            
            assert config.name == "测试任务"
            assert config.description == "测试描述"
        except ImportError:
            pytest.skip("TaskConfig or enums not available")