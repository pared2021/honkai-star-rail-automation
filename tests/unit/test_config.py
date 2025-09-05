#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from unittest.mock import Mock, patch

import pytest

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


class TestConfigModules:
    """配置模块测试"""

    def test_database_config_import(self):
        """测试数据库配置导入"""
        from src.config.database_config import DatabaseConfig

        assert DatabaseConfig is not None

    def test_database_config_creation(self):
        """测试数据库配置创建"""
        from src.config.database_config import DatabaseConfig

        config = DatabaseConfig()
        assert config is not None
        assert hasattr(config, "get_connection_string")

    def test_error_recovery_strategies_import(self):
        """测试错误恢复策略导入"""
        from src.config.error_recovery_strategies import ErrorRecoveryStrategies

        assert ErrorRecoveryStrategies is not None

    def test_error_recovery_strategies_creation(self):
        """测试错误恢复策略创建"""
        from src.config.error_recovery_strategies import ErrorRecoveryStrategies

        strategies = ErrorRecoveryStrategies()
        assert strategies is not None
        assert hasattr(strategies, "get_strategy")
