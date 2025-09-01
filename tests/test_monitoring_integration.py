# -*- coding: utf-8 -*-
"""
监控系统集成测试
"""

import pytest
import tempfile
import os
import time
import json
import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# 导入监控系统组件
from src.monitoring import (
    MonitoringSystem,
    LoggingMonitoringService,
    AlertManager,
    HealthChecker,
    MonitoringConfigManager,
    LogLevel,
    MonitoringEventType,
    AlertSeverity,
    HealthStatus,
    ComponentType,
    ConfigType,
    initialize_monitoring_system,
    get_monitoring_system,
    set_monitoring_system
)


class TestMonitoringSystemIntegration:
    """监控系统集成测试"""
    
    def setup_method(self):
        """测试前设置"""
        # 创建临时配置目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建模拟的事件总线和数据库管理器
        self.mock_event_bus = Mock()
        self.mock_db_manager = Mock()
        
        # 创建监控系统实例
        self.monitoring_system = MonitoringSystem(
            event_bus=self.mock_event_bus,
            db_manager=self.mock_db_manager,
            config_directory=self.temp_dir
        )
    
    def teardown_method(self):
        """测试后清理"""
        # 停止监控系统
        if self.monitoring_system.is_running:
            self.monitoring_system.stop()
        
        # 清理临时目录
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # 清理全局实例
        set_monitoring_system(None)
    
    def test_monitoring_system_initialization(self):
        """测试监控系统初始化"""
        # 测试初始化
        assert self.monitoring_system.initialize() == True
        assert self.monitoring_system.logging_service is not None
        assert self.monitoring_system.alert_manager is not None
        assert self.monitoring_system.health_checker is not None
        assert self.monitoring_system.config_manager is not None
        
        # 测试配置加载
        config = self.monitoring_system.config
        assert config is not None
        assert hasattr(config, 'monitoring')
        assert hasattr(config, 'alerting')
        assert hasattr(config, 'health_check')
    
    def test_monitoring_system_start_stop(self):
        """测试监控系统启动和停止"""
        # 初始化
        assert self.monitoring_system.initialize() == True
        
        # 测试启动
        assert self.monitoring_system.start() == True
        assert self.monitoring_system.is_running == True
        
        # 验证组件启动状态
        assert self.monitoring_system.logging_service.is_running == True
        assert getattr(self.monitoring_system.alert_manager, 'running', False) == True
        assert getattr(self.monitoring_system.health_checker, 'running', False) == True
        
        # 验证事件总线调用
        self.mock_event_bus.emit.assert_called_with(
            'monitoring_system_started',
            unittest.mock.ANY
        )
        
        # 测试停止
        assert self.monitoring_system.stop() == True
        assert self.monitoring_system.is_running == False
        
        # 验证组件停止状态
        assert self.monitoring_system.logging_service.is_running == False
        assert getattr(self.monitoring_system.alert_manager, 'running', True) == False
        assert getattr(self.monitoring_system.health_checker, 'running', True) == False
    
    def test_monitoring_system_restart(self):
        """测试监控系统重启"""
        # 初始化并启动
        assert self.monitoring_system.initialize() == True
        assert self.monitoring_system.start() == True
        
        # 记录重启前的组件实例
        old_logging_service = self.monitoring_system.logging_service
        old_alert_manager = self.monitoring_system.alert_manager
        old_health_checker = self.monitoring_system.health_checker
        
        # 测试重启
        assert self.monitoring_system.restart() == True
        assert self.monitoring_system.is_running == True
        
        # 验证组件重新启动
        assert self.monitoring_system.logging_service.is_running == True
        assert getattr(self.monitoring_system.alert_manager, 'running', False) == True
        assert getattr(self.monitoring_system.health_checker, 'running', False) == True
    
    def test_component_integration(self):
        """测试组件间集成"""
        # 初始化并启动
        assert self.monitoring_system.initialize() == True
        assert self.monitoring_system.start() == True
        
        # 测试日志记录
        self.monitoring_system.logging_service.add_log_entry(
            level=LogLevel.ERROR,
            message="测试错误日志",
            module="test_component"
        )
        
        # 测试事件记录
        self.monitoring_system.logging_service.add_monitoring_event(
            event_type=MonitoringEventType.SYSTEM_ERROR,
            source="test_component",
            data={"message": "测试系统错误事件"}
        )
        
        # 等待一小段时间让组件处理
        time.sleep(0.1)
        
        # 验证日志和事件被记录
        logs = self.monitoring_system.logging_service.get_logs()[:10]
        events = self.monitoring_system.logging_service.get_events()[:10]
        
        assert len(logs) > 0
        assert len(events) > 0
        assert any(log.message == "测试错误日志" for log in logs)
        assert any(event.data.get("message") == "测试系统错误事件" for event in events)
    
    def test_alert_integration(self):
        """测试告警集成"""
        # 初始化并启动
        assert self.monitoring_system.initialize() == True
        assert self.monitoring_system.start() == True
        
        # 添加告警规则
        from src.monitoring.alert_manager import AlertRule, AlertChannel
        rule = AlertRule(
            id="cpu_alert_rule",
            name="CPU使用率告警",
            description="监控CPU使用率过高的情况",
            condition="cpu_usage() > 80",
            severity=AlertSeverity.MEDIUM,
            channels=[AlertChannel.LOG]
        )
        self.monitoring_system.alert_manager.add_rule(rule)
        # 验证规则已添加
        assert self.monitoring_system.alert_manager.get_rule("cpu_alert_rule") is not None
        
        # 模拟高CPU使用率
        self.monitoring_system.alert_manager.update_metrics({
            'cpu_percent': 85.0,
            'memory_percent': 60.0
        })
        
        # 手动触发规则评估（避免等待30秒的评估循环）
        self.monitoring_system.alert_manager._evaluate_rules()
        
        # 等待告警处理
        time.sleep(1)
        
        # 验证告警是否被触发
        alerts = self.monitoring_system.alert_manager.get_active_alerts()
        print(f"Active alerts count: {len(alerts)}")
        if len(alerts) > 0:
            for alert in alerts:
                print(f"Alert: {alert.title} - {alert.message}")
        assert len(alerts) > 0, "应该有告警被触发"
    
    def test_health_check_integration(self):
        """测试健康检查集成"""
        # 初始化并启动
        assert self.monitoring_system.initialize() == True
        assert self.monitoring_system.start() == True
        
        # 运行健康检查
        self.monitoring_system.health_checker.run_immediate_check()
        
        # 等待检查完成
        time.sleep(0.5)
        
        # 获取健康状态
        overall_status = self.monitoring_system.health_checker.get_overall_health_status()
        health_summary = self.monitoring_system.health_checker.get_health_summary()
        
        assert overall_status in [HealthStatus.HEALTHY, HealthStatus.WARNING, HealthStatus.CRITICAL]
        assert 'overall_status' in health_summary
        assert 'components' in health_summary
        assert 'statistics' in health_summary
    
    def test_config_management_integration(self):
        """测试配置管理集成"""
        # 初始化
        assert self.monitoring_system.initialize() == True
        
        # 测试配置更新
        new_config = {
            'enabled': True,
            'alert_cooldown_minutes': 5,
            'max_alerts_per_hour': 20
        }
        
        success = self.monitoring_system.update_config(
            ConfigType.ALERTING,
            new_config
        )
        assert success == True
        
        # 验证配置已更新
        updated_config = self.monitoring_system.config_manager.get_config()
        assert updated_config.alerting.alert_cooldown_minutes == 5
        assert updated_config.alerting.max_alerts_per_hour == 20
    
    def test_status_reporting(self):
        """测试状态报告"""
        # 初始化并启动
        assert self.monitoring_system.initialize() == True
        assert self.monitoring_system.start() == True
        
        # 获取系统状态
        status = self.monitoring_system.get_status()
        
        # 验证状态结构
        assert 'is_running' in status
        assert 'components' in status
        assert 'configuration' in status
        assert 'statistics' in status
        
        assert status['is_running'] == True
        assert 'logging_service' in status['components']
        assert 'alert_manager' in status['components']
        assert 'health_checker' in status['components']
        
        # 获取健康摘要
        health_summary = self.monitoring_system.get_health_summary()
        assert 'overall_status' in health_summary
        
        # 获取告警摘要
        alert_summary = self.monitoring_system.get_alert_summary()
        assert 'statistics' in alert_summary
        assert 'active_alerts' in alert_summary
        assert 'recent_alerts' in alert_summary
        
        # 获取性能指标
        performance_metrics = self.monitoring_system.get_performance_metrics()
        assert isinstance(performance_metrics, dict)
    
    def test_data_export(self):
        """测试数据导出"""
        # 初始化并启动
        assert self.monitoring_system.initialize() == True
        assert self.monitoring_system.start() == True
        
        # 添加一些测试数据
        self.monitoring_system.logging_service.add_log_entry(
            level=LogLevel.INFO,
            message="测试导出日志",
            module="test_export"
        )
        
        # 导出数据
        export_file = os.path.join(self.temp_dir, "monitoring_export.json")
        success = self.monitoring_system.export_monitoring_data(
            export_file,
            include_config=True
        )
        assert success == True
        assert os.path.exists(export_file)
        
        # 验证导出文件内容
        with open(export_file, 'r', encoding='utf-8') as f:
            export_data = json.load(f)
        
        assert 'export_timestamp' in export_data
        assert 'system_status' in export_data
        assert 'health_summary' in export_data
        assert 'alert_summary' in export_data
        assert 'performance_metrics' in export_data
        assert 'configuration' in export_data
    
    def test_global_instance_management(self):
        """测试全局实例管理"""
        # 测试初始化全局实例
        global_system = initialize_monitoring_system(
            event_bus=self.mock_event_bus,
            db_manager=self.mock_db_manager,
            config_directory=self.temp_dir
        )
        
        assert global_system is not None
        assert get_monitoring_system() == global_system
        
        # 测试全局实例功能
        assert global_system.start() == True
        assert global_system.is_running == True
        
        # 清理
        assert global_system.stop() == True
        set_monitoring_system(None)
        assert get_monitoring_system() is None
    
    @patch('src.ui.MonitoringDashboard')
    def test_dashboard_integration(self, mock_dashboard_class):
        """测试仪表板集成"""
        # 创建模拟仪表板实例
        mock_dashboard = Mock()
        mock_dashboard_class.return_value = mock_dashboard
        
        # 初始化监控系统
        assert self.monitoring_system.initialize() == True
        
        # 验证仪表板被创建
        if self.monitoring_system.dashboard:
            assert self.monitoring_system.dashboard == mock_dashboard
            
            # 测试显示和隐藏仪表板
            self.monitoring_system.show_dashboard()
            mock_dashboard.show.assert_called_once()
            
            self.monitoring_system.hide_dashboard()
            mock_dashboard.hide.assert_called_once()
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试重复启动
        assert self.monitoring_system.initialize() == True
        assert self.monitoring_system.start() == True
        
        # 重复启动应该返回True但不会重复启动组件
        assert self.monitoring_system.start() == True
        
        # 测试停止未运行的系统
        assert self.monitoring_system.stop() == True
        assert self.monitoring_system.stop() == True  # 重复停止
        
        # 测试无效配置更新
        invalid_config = "invalid_config_data"
        success = self.monitoring_system.config_manager.update_config(
            ConfigType.MONITORING,
            invalid_config
        )
        # 配置管理器应该处理无效数据
        assert success == False
    
    def test_performance_under_load(self):
        """测试负载下的性能"""
        # 初始化并启动
        assert self.monitoring_system.initialize() == True
        assert self.monitoring_system.start() == True
        
        # 模拟大量日志和事件
        start_time = time.time()
        
        for i in range(100):
            self.monitoring_system.logging_service.add_log_entry(
                level=LogLevel.INFO,
                message=f"测试日志 {i}",
                module="performance_test"
            )
            
            self.monitoring_system.logging_service.add_monitoring_event(
                event_type=MonitoringEventType.SYSTEM_ERROR,
                source="performance_test",
                data={"message": f"测试事件 {i}"}
            )
        
        # 等待处理完成
        time.sleep(0.5)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # 验证处理时间合理（应该在几秒内完成）
        assert processing_time < 5.0
        
        # 验证数据完整性
        logs = self.monitoring_system.logging_service.get_logs()[:200]
        events = self.monitoring_system.logging_service.get_events()[:200]
        
        assert len(logs) >= 100
        assert len(events) >= 100
    
    def test_concurrent_operations(self):
        """测试并发操作"""
        import threading
        
        # 初始化并启动
        assert self.monitoring_system.initialize() == True
        assert self.monitoring_system.start() == True
        
        # 定义并发操作函数
        def add_logs_and_events(thread_id):
            for i in range(50):
                self.monitoring_system.logging_service.add_log_entry(
                    level=LogLevel.INFO,
                    message=f"线程{thread_id}日志{i}",
                    module=f"thread_{thread_id}"
                )
                
                self.monitoring_system.logging_service.add_monitoring_event(
                    event_type=MonitoringEventType.SYSTEM_ERROR,
                    source=f"thread_{thread_id}",
                    data={"message": f"线程{thread_id}事件{i}"}
                )
        
        # 创建多个线程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=add_logs_and_events, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 等待处理完成
        time.sleep(1.0)
        
        # 验证数据完整性
        logs = self.monitoring_system.logging_service.get_logs()[:500]
        events = self.monitoring_system.logging_service.get_events()[:500]
        
        # 应该有250个日志和250个事件（5个线程 × 50个）
        assert len(logs) >= 250
        assert len(events) >= 250
        
        # 验证没有数据丢失或损坏
        log_sources = set(log.module for log in logs)
        event_sources = set(event.source for event in events)
        
        expected_sources = {f"thread_{i}" for i in range(5)}
        assert expected_sources.issubset(log_sources)
        assert expected_sources.issubset(event_sources)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])