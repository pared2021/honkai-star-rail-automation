#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

import pytest

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


class TestTaskConfig:
    """TaskConfig测试"""

    def test_task_config_import(self):
        """测试 TaskConfig 导入"""
        from src.core.task_manager import TaskPriority
        from src.models.task_models import TaskConfig, TaskType

        assert TaskConfig is not None
        assert TaskType is not None
        assert TaskPriority is not None

    def test_task_config_creation(self):
        """测试 TaskConfig 创建"""
        from src.core.task_manager import TaskPriority
        from src.models.task_models import TaskConfig, TaskType

        config = TaskConfig(
            name="测试任务",
            task_type="automation",
            description="测试描述",
            priority="MEDIUM",
        )

        assert config is not None
        assert config.name == "测试任务"
        assert config.task_type == "automation"
        assert config.description == "测试描述"
        assert config.priority == "MEDIUM"
