#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import pytest

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


class TestTaskConfig:
    """TaskConfig测试"""
    
    def test_task_config_import(self):
        """测试 TaskConfig 导入"""
        from src.models.task_models import TaskConfig
        from src.core.task_model import TaskType, TaskPriority
        
        assert TaskConfig is not None
        assert TaskType is not None
        assert TaskPriority is not None
    
    def test_task_config_creation(self):
        """测试 TaskConfig 创建"""
        from src.models.task_models import TaskConfig
        from src.core.task_model import TaskType, TaskPriority
        
        config = TaskConfig(
            name="测试任务",
            task_type=TaskType.AUTOMATION,
            description="测试描述",
            priority=TaskPriority.MEDIUM
        )
        
        assert config is not None
        assert config.name == "测试任务"
        assert config.task_type == TaskType.AUTOMATION
        assert config.description == "测试描述"
        assert config.priority == TaskPriority.MEDIUM