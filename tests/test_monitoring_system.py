"""监控系统测试模块."""

import time
import unittest
from unittest.mock import Mock, patch
from src.monitoring.monitoring_system import (
    MonitoringSystem, get_monitoring_system, start_monitoring, stop_monitoring
)
from src.monitoring.types import HealthCheckResult, HealthStatus, AlertSeverity


class TestMonitoringSystem(unittest.TestCase):
    """监控系统测试类."""
    
    def setUp(self):
        """设置测试环境."""
        self.monitoring_system = MonitoringSystem(
            health_check_interval=1.0,
            metrics_collection_interval=1.0
        )
    
    def tearDown(self):
        """清理测试环境."""
        if self.monitoring_system.is_running():
            self.monitoring_system.stop()
    
    def test_system_initialization(self):
        """测试系统初始化."""
        self.assertIsNotNone(self.monitoring_system.health_checker)
        self.assertIsNotNone(self.monitoring_system.metrics_collector)
        self.assertIsNotNone(self.monitoring_system.alert_manager)
        self.assertFalse(self.monitoring_system.is_running())
    
    def test_system_start_stop(self):
        """测试系统启动和停止."""
        # 启动系统
        self.monitoring_system.start()
        self.assertTrue(self.monitoring_system.is_running())
        
        # 停止系统
        self.monitoring_system.stop()
        self.assertFalse(self.monitoring_system.is_running())
    
    def test_system_start_already_running(self):
        """测试重复启动系统."""
        self.monitoring_system.start()
        
        # 再次启动应该不会出错
        self.monitoring_system.start()
        self.assertTrue(self.monitoring_system.is_running())
    
    def test_system_stop_not_running(self):
        """测试停止未运行的系统."""
        # 停止未运行的系统应该不会出错
        self.monitoring_system.stop()
        self.assertFalse(self.monitoring_system.is_running())
    
    def test_get_system_status(self):
        """测试获取系统状态."""
        status = self.monitoring_system.get_system_status()
        
        self.assertIn('timestamp', status)
        self.assertIn('running', status)
        self.assertIn('health', status)
        self.assertIn('metrics', status)
        self.assertIn('alerts', status)
        
        # 检查健康状态结构
        health = status['health']
        self.assertIn('overall_status', health)
        self.assertIn('component_count', health)
        self.assertIn('healthy_components', health)
        self.assertIn('unhealthy_components', health)
        
        # 检查指标状态结构
        metrics = status['metrics']
        self.assertIn('total_metrics', metrics)
        self.assertIn('collectors_count', metrics)
        
        # 检查告警状态结构
        alerts = status['alerts']
        self.assertIn('active_count', alerts)
        self.assertIn('recent_24h', alerts)
        self.assertIn('critical_count', alerts)
        self.assertIn('warning_count', alerts)
        self.assertIn('active_alerts', alerts)
    
    def test_get_health_report(self):
        """测试获取健康报告."""
        report = self.monitoring_system.get_health_report()
        
        self.assertIn('timestamp', report)
        self.assertIn('overall_status', report)
        self.assertIn('components', report)
        
        # 应该有一些基本的健康检查组件
        components = report['components']
        self.assertIsInstance(components, dict)
    
    def test_get_metrics_report(self):
        """测试获取指标报告."""
        report = self.monitoring_system.get_metrics_report()
        
        self.assertIn('timestamp', report)
        self.assertIn('gauges', report)
        self.assertIn('counters', report)
    
    def test_get_alerts_report(self):
        """测试获取告警报告."""
        report = self.monitoring_system.get_alerts_report()
        
        self.assertIn('timestamp', report)
        self.assertIn('statistics', report)
        self.assertIn('active_alerts', report)
        self.assertIn('recent_alerts', report)
    
    def test_add_custom_health_check(self):
        """测试添加自定义健康检查."""
        def custom_check():
            return HealthCheckResult(
                component="custom_component",
                status=HealthStatus.HEALTHY,
                message="Custom check passed"
            )
        
        self.monitoring_system.add_custom_health_check("custom_check", custom_check)
        
        # 执行健康检查
        results = self.monitoring_system.health_checker.check_health()
        self.assertIn("custom_check", results)
        
        result = results["custom_check"]
        self.assertEqual(result.status, HealthStatus.HEALTHY)
        self.assertEqual(result.component, "custom_component")
    
    def test_add_custom_metrics_collector(self):
        """测试添加自定义指标收集器."""
        def custom_collector():
            return {
                'custom_metric': 42.0
            }
        
        self.monitoring_system.add_custom_metrics_collector("custom_collector", custom_collector)
        
        # 收集指标
        metrics = self.monitoring_system.metrics_collector.get_all_metrics()
        self.assertIn('custom_collector.custom_metric', metrics.get('gauges', {}))
        self.assertEqual(metrics['gauges']['custom_collector.custom_metric'], 42.0)
    
    def test_add_notification_handler(self):
        """测试添加通知处理器."""
        notifications = []
        
        def custom_handler(alert):
            notifications.append(alert)
        
        self.monitoring_system.add_notification_handler(custom_handler)
        
        # 触发一个告警
        self.monitoring_system.alert_manager._trigger_alert(
            name="test_alert",
            severity=AlertSeverity.WARNING,
            message="Test notification",
            component="test"
        )
        
        # 检查是否收到通知
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].name, "test_alert")
    
    @patch('src.monitoring.monitoring_system._monitoring_system', None)
    def test_global_monitoring_system(self):
        """测试全局监控系统实例."""
        # 获取全局实例
        system1 = get_monitoring_system()
        system2 = get_monitoring_system()
        
        # 应该是同一个实例
        self.assertIs(system1, system2)
    
    @patch('src.monitoring.monitoring_system._monitoring_system', None)
    def test_global_start_stop_monitoring(self):
        """测试全局启动停止监控."""
        # 启动全局监控
        start_monitoring()
        
        system = get_monitoring_system()
        self.assertTrue(system.is_running())
        
        # 停止全局监控
        stop_monitoring()
        self.assertFalse(system.is_running())
    
    def test_integration_health_check_alert(self):
        """测试健康检查与告警集成."""
        # 添加一个会失败的健康检查
        def failing_check():
            return HealthCheckResult(
                component="failing_component",
                status=HealthStatus.UNHEALTHY,
                message="Component is down"
            )
        
        self.monitoring_system.add_custom_health_check("failing_check", failing_check)
        
        # 执行健康检查
        self.monitoring_system.health_checker.check_health()
        
        # 检查是否生成了告警
        active_alerts = self.monitoring_system.alert_manager.get_active_alerts()
        self.assertTrue(len(active_alerts) > 0)
        
        # 查找相关告警
        failing_alerts = [alert for alert in active_alerts 
                         if alert.name == "health_check_failing_component"]
        self.assertEqual(len(failing_alerts), 1)
        
        alert = failing_alerts[0]
        self.assertEqual(alert.severity, AlertSeverity.CRITICAL)
        self.assertEqual(alert.component, "failing_component")
    
    def test_integration_metrics_alert(self):
        """测试指标收集与告警集成."""
        # 添加一个会产生高CPU使用率的指标收集器
        def system_health_collector():
            return {
                'system_cpu_usage': 95.0
            }
        
        self.monitoring_system.add_custom_metrics_collector("system_health", system_health_collector)
        
        # 收集指标
        self.monitoring_system.metrics_collector.collect_metrics()
        
        # 评估指标并触发告警
        metrics = self.monitoring_system.metrics_collector.get_all_metrics()
        self.monitoring_system.alert_manager.evaluate_metrics(metrics)
        
        # 检查是否生成了告警
        active_alerts = self.monitoring_system.alert_manager.get_active_alerts()
        
        # 查找CPU告警
        cpu_alerts = [alert for alert in active_alerts 
                     if alert.name == "high_cpu_usage"]
        self.assertEqual(len(cpu_alerts), 1)
        
        alert = cpu_alerts[0]
        self.assertEqual(alert.severity, AlertSeverity.CRITICAL)
        self.assertIn("95.0%", alert.message)
    
    def test_system_status_with_alerts(self):
        """测试带有告警的系统状态."""
        # 触发一些告警
        self.monitoring_system.alert_manager._trigger_alert(
            name="test_critical",
            severity=AlertSeverity.CRITICAL,
            message="Critical issue",
            component="system"
        )
        
        self.monitoring_system.alert_manager._trigger_alert(
            name="test_warning",
            severity=AlertSeverity.WARNING,
            message="Warning issue",
            component="app"
        )
        
        status = self.monitoring_system.get_system_status()
        
        alerts = status['alerts']
        self.assertEqual(alerts['active_count'], 2)
        self.assertEqual(alerts['critical_count'], 1)
        self.assertEqual(alerts['warning_count'], 1)
        
        # 检查活跃告警列表
        active_alerts = alerts['active_alerts']
        self.assertEqual(len(active_alerts), 2)
        
        # 验证告警信息结构
        for alert_info in active_alerts:
            self.assertIn('name', alert_info)
            self.assertIn('severity', alert_info)
            self.assertIn('component', alert_info)
            self.assertIn('message', alert_info)
            self.assertIn('duration', alert_info)


if __name__ == '__main__':
    unittest.main()