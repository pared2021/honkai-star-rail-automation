"""告警管理器测试模块."""

import time
import unittest
from unittest.mock import Mock, patch
from src.monitoring.alert_manager import (
    AlertManager, create_console_notification_handler
)
from src.monitoring.types import (
    AlertSeverity, AlertStatus, Alert, AlertRule, HealthStatus, HealthCheckResult
)


class TestAlertManager(unittest.TestCase):
    """告警管理器测试类."""
    
    def setUp(self):
        """设置测试环境."""
        self.alert_manager = AlertManager()
        self.notification_calls = []
        
        # 添加测试通知处理器
        def test_handler(alert: Alert):
            self.notification_calls.append(alert)
        
        self.alert_manager.add_notification_handler(test_handler)
    
    def test_alert_creation(self):
        """测试告警创建。"""
        alert = Alert(
            name="test_alert",
            severity=AlertSeverity.WARNING,
            status=AlertStatus.ACTIVE,
            message="Test alert message",
            component="test_component"
        )
        
        self.assertEqual(alert.name, "test_alert")
        self.assertEqual(alert.severity, AlertSeverity.WARNING)
        self.assertEqual(alert.status, AlertStatus.ACTIVE)
        self.assertEqual(alert.component, "test_component")
        self.assertIsInstance(alert.duration, float)
    
    def test_health_check_evaluation_unhealthy(self):
        """测试不健康状态的健康检查评估."""
        result = HealthCheckResult(
            component="test_component",
            status=HealthStatus.UNHEALTHY,
            message="Component is unhealthy",
            duration=1.0
        )
        
        self.alert_manager.evaluate_health_check(result)
        
        # 检查是否生成了告警
        active_alerts = self.alert_manager.get_active_alerts()
        self.assertEqual(len(active_alerts), 1)
        
        alert = active_alerts[0]
        self.assertEqual(alert.name, "health_check_test_component")
        self.assertEqual(alert.severity, AlertSeverity.CRITICAL)
        self.assertEqual(alert.component, "test_component")
        
        # 检查是否发送了通知
        self.assertEqual(len(self.notification_calls), 1)
    
    def test_health_check_evaluation_degraded(self):
        """测试降级状态的健康检查评估."""
        result = HealthCheckResult(
            component="test_component",
            status=HealthStatus.DEGRADED,
            message="Component is degraded",
            duration=1.0
        )
        
        self.alert_manager.evaluate_health_check(result)
        
        # 检查是否生成了告警
        active_alerts = self.alert_manager.get_active_alerts()
        self.assertEqual(len(active_alerts), 1)
        
        alert = active_alerts[0]
        self.assertEqual(alert.severity, AlertSeverity.WARNING)
    
    def test_health_check_evaluation_healthy_resolves_alert(self):
        """测试健康状态解决告警."""
        # 先创建一个不健康的告警
        unhealthy_result = HealthCheckResult(
            component="test_component",
            status=HealthStatus.UNHEALTHY,
            message="Component is unhealthy",
            duration=1.0
        )
        self.alert_manager.evaluate_health_check(unhealthy_result)
        
        # 确认告警存在
        self.assertEqual(len(self.alert_manager.get_active_alerts()), 1)
        
        # 发送健康状态
        healthy_result = HealthCheckResult(
            component="test_component",
            status=HealthStatus.HEALTHY,
            message="Component is healthy",
            duration=1.0
        )
        self.alert_manager.evaluate_health_check(healthy_result)
        
        # 确认告警已解决
        self.assertEqual(len(self.alert_manager.get_active_alerts()), 0)
    
    def test_metrics_evaluation_high_cpu(self):
        """测试高CPU使用率指标评估."""
        metrics = {
            'gauges': {
                'system_health.system_cpu_usage': 95.0
            }
        }
        
        self.alert_manager.evaluate_metrics(metrics)
        
        # 检查是否生成了告警
        active_alerts = self.alert_manager.get_active_alerts()
        self.assertEqual(len(active_alerts), 1)
        
        alert = active_alerts[0]
        self.assertEqual(alert.name, "high_cpu_usage")
        self.assertEqual(alert.severity, AlertSeverity.CRITICAL)
        self.assertIn("95.0%", alert.message)
    
    def test_metrics_evaluation_high_memory(self):
        """测试高内存使用率指标评估."""
        metrics = {
            'gauges': {
                'system_health.system_memory_usage': 85.0
            }
        }
        
        self.alert_manager.evaluate_metrics(metrics)
        
        # 检查是否生成了告警
        active_alerts = self.alert_manager.get_active_alerts()
        self.assertEqual(len(active_alerts), 1)
        
        alert = active_alerts[0]
        self.assertEqual(alert.name, "high_memory_usage")
        self.assertEqual(alert.severity, AlertSeverity.WARNING)
    
    def test_metrics_evaluation_no_game_process(self):
        """测试无游戏进程指标评估."""
        metrics = {
            'gauges': {
                'game_performance.game_process_count': 0
            }
        }
        
        self.alert_manager.evaluate_metrics(metrics)
        
        # 检查是否生成了告警
        active_alerts = self.alert_manager.get_active_alerts()
        self.assertEqual(len(active_alerts), 1)
        
        alert = active_alerts[0]
        self.assertEqual(alert.name, "no_game_process")
        self.assertEqual(alert.severity, AlertSeverity.WARNING)
    
    def test_alert_cooldown(self):
        """测试告警冷却时间."""
        # 设置较短的冷却时间进行测试
        original_time = time.time
        mock_time = Mock(return_value=1000.0)
        
        with patch('time.time', mock_time):
            # 第一次触发告警
            self.alert_manager._trigger_alert(
                name="test_alert",
                severity=AlertSeverity.WARNING,
                message="Test message",
                component="test"
            )
            
            # 立即再次触发（应该被冷却时间阻止）
            mock_time.return_value = 1100.0  # 100秒后
            self.alert_manager._trigger_alert(
                name="test_alert",
                severity=AlertSeverity.WARNING,
                message="Test message 2",
                component="test"
            )
            
            # 应该只有一个告警（第二次被冷却时间阻止）
            self.assertEqual(len(self.notification_calls), 1)
            
            # 超过冷却时间后再次触发
            mock_time.return_value = 1400.0  # 400秒后
            self.alert_manager._trigger_alert(
                name="test_alert",
                severity=AlertSeverity.WARNING,
                message="Test message 3",
                component="test"
            )
            
            # 现在应该有两个通知
            self.assertEqual(len(self.notification_calls), 2)
    
    def test_alert_stats(self):
        """测试告警统计信息."""
        # 创建不同严重程度的告警
        self.alert_manager._trigger_alert(
            name="critical_alert",
            severity=AlertSeverity.CRITICAL,
            message="Critical issue",
            component="system"
        )
        
        self.alert_manager._trigger_alert(
            name="warning_alert",
            severity=AlertSeverity.WARNING,
            message="Warning issue",
            component="app"
        )
        
        stats = self.alert_manager.get_alert_stats()
        
        self.assertEqual(stats['active_alerts'], 2)
        self.assertEqual(stats['severity_breakdown']['critical'], 1)
        self.assertEqual(stats['severity_breakdown']['warning'], 1)
        self.assertEqual(stats['severity_breakdown']['info'], 0)
    
    def test_alert_history(self):
        """测试告警历史记录."""
        # 创建告警
        self.alert_manager._trigger_alert(
            name="test_alert",
            severity=AlertSeverity.WARNING,
            message="Test message",
            component="test"
        )
        
        # 解决告警
        self.alert_manager._resolve_alert("test_alert")
        
        # 检查历史记录
        history = self.alert_manager.get_alert_history(24)
        self.assertEqual(len(history), 1)
        
        alert = history[0]
        self.assertEqual(alert.status, AlertStatus.RESOLVED)
        self.assertIsNotNone(alert.resolved_at)
    
    def test_console_notification_handler(self):
        """测试控制台通知处理器。"""
        handler = create_console_notification_handler()
        
        alert = Alert(
            name="test_alert",
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.ACTIVE,
            message="Test critical alert",
            component="test_component"
        )
        
        # 测试处理器不会抛出异常
        try:
            handler(alert)
        except Exception as e:
            self.fail(f"Console handler raised exception: {e}")


if __name__ == '__main__':
    unittest.main()