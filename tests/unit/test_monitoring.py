#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


class TestMonitoringSystem:
    """监控系统测试"""

    def test_monitoring_system_import(self):
        """测试监控系统导入"""
        from src.monitoring import MonitoringSystem

        assert MonitoringSystem is not None

    @patch("src.monitoring.AlertManager")
    @patch("src.monitoring.HealthChecker")
    @patch("src.monitoring.MetricsCollector")
    def test_monitoring_system_creation(self, mock_metrics, mock_health, mock_alert):
        """测试监控系统创建"""
        from src.monitoring import MonitoringSystem

        # 模拟依赖
        mock_alert.return_value = Mock()
        mock_health.return_value = Mock()
        mock_metrics.return_value = Mock()

        system = MonitoringSystem()
        assert system is not None

    def test_monitoring_functions_import(self):
        """测试监控函数导入"""
        from src.monitoring import (
            get_monitoring_system,
            initialize_monitoring_system,
            set_monitoring_system,
        )

        assert get_monitoring_system is not None
        assert set_monitoring_system is not None
        assert initialize_monitoring_system is not None

    def test_get_monitoring_system_none(self):
        """测试获取监控系统（未初始化）"""
        # 重置全局变量
        import src.monitoring
        from src.monitoring import _monitoring_system, get_monitoring_system

        src.monitoring._monitoring_system = None

        result = get_monitoring_system()
        assert result is None

    @patch("src.monitoring.MonitoringSystem")
    def test_set_monitoring_system(self, mock_monitoring_class):
        """测试设置监控系统"""
        from src.monitoring import set_monitoring_system

        mock_system = Mock()
        set_monitoring_system(mock_system)

        # 验证系统被设置
        from src.monitoring import get_monitoring_system

        result = get_monitoring_system()
        assert result == mock_system


class TestAlertManager:
    """告警管理器测试"""

    def test_alert_manager_import(self):
        """测试告警管理器导入"""
        from src.monitoring.alert_manager import AlertManager

        assert AlertManager is not None

    def test_alert_manager_creation(self):
        """测试告警管理器创建"""
        from src.monitoring.alert_manager import AlertManager

        manager = AlertManager()
        assert manager is not None
        assert hasattr(manager, "create_alert")

    def test_create_alert_method_signature(self):
        """测试创建告警方法签名"""
        import inspect

        from src.monitoring.alert_manager import AlertManager

        manager = AlertManager()
        sig = inspect.signature(manager.create_alert)

        # 检查方法存在且可调用
        assert callable(manager.create_alert)
        assert "rule_id" in sig.parameters
        assert "title" in sig.parameters
        assert "source" in sig.parameters
        assert "data" in sig.parameters


class TestHealthChecker:
    """健康检查器测试"""

    def test_health_checker_import(self):
        """测试健康检查器导入"""
        from src.monitoring.health_checker import HealthChecker

        assert HealthChecker is not None

    def test_health_checker_creation(self):
        """测试健康检查器创建"""
        from src.monitoring.health_checker import HealthChecker

        checker = HealthChecker()
        assert checker is not None
        assert hasattr(checker, "check_health")


class TestMetricsCollector:
    """指标收集器测试"""

    def test_metrics_collector_import(self):
        """测试指标收集器导入"""
        from src.monitoring.metrics_collector import MetricsCollector

        assert MetricsCollector is not None

    def test_metrics_collector_creation(self):
        """测试指标收集器创建"""
        from src.monitoring.metrics_collector import MetricsCollector

        collector = MetricsCollector()
        assert collector is not None
        assert hasattr(collector, "collect_metrics")
