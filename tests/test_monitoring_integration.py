"""监控系统集成测试."""

import asyncio
import time
import unittest
from unittest.mock import Mock, patch, MagicMock
from src.monitoring.health_checker import HealthChecker
from src.monitoring.metrics_collector import MetricsCollector
from src.monitoring.types import HealthStatus, HealthCheckResult


class TestMonitoringIntegration(unittest.TestCase):
    """监控系统集成测试类."""

    def setUp(self):
        """设置测试环境."""
        self.health_checker = HealthChecker()
        self.metrics_collector = MetricsCollector()

    def tearDown(self):
        """清理测试环境."""
        self.health_checker.stop_monitoring()
        self.metrics_collector.stop()

    def test_health_checker_game_checks(self):
        """测试健康检查器的游戏相关检查."""
        # 创建游戏相关检查
        self.health_checker.create_game_checks()
        
        # 验证检查已添加
        checks = self.health_checker.get_checks()
        check_names = list(checks.keys())
        
        expected_checks = [
            'game_process_check',
            'game_window_check', 
            'automation_system_check',
            'template_files_check'
        ]
        
        for check_name in expected_checks:
            self.assertIn(check_name, check_names)

    @patch('psutil.process_iter')
    def test_health_checker_game_process_check(self, mock_process_iter):
        """测试游戏进程检查."""
        # 模拟游戏进程
        mock_proc = Mock()
        mock_proc.info = {'name': 'game_client.exe'}
        mock_process_iter.return_value = [mock_proc]
        
        self.health_checker.create_game_checks()
        
        # 执行检查
        result = self.health_checker.check_health('game_process_check')
        
        # 验证结果
        self.assertIsInstance(result, HealthCheckResult)
        self.assertEqual(result.component, 'game_process_check')
        # 在模拟环境中应该找到游戏进程
        self.assertEqual(result.status, HealthStatus.HEALTHY)
        self.assertIn('Game process found', result.message)

    @patch('win32gui.EnumWindows')
    @patch('win32gui.IsWindowVisible')
    @patch('win32gui.GetWindowText')
    @patch('win32process.GetWindowThreadProcessId')
    @patch('psutil.Process')
    def test_health_checker_game_window_check(self, mock_process, mock_get_thread_pid, mock_get_text, mock_is_visible, mock_enum):
        """测试游戏窗口检查."""
        # 模拟游戏窗口
        mock_is_visible.return_value = True
        mock_get_text.return_value = 'Game Client'
        mock_get_thread_pid.return_value = (123, 456)  # (thread_id, process_id)
        
        # 模拟进程
        mock_proc = Mock()
        mock_proc.name.return_value = 'game_client.exe'
        mock_process.return_value = mock_proc
        
        def mock_enum_callback(callback, param):
            callback(12345, param)  # 模拟窗口句柄
            return True
        
        mock_enum.side_effect = mock_enum_callback
        
        self.health_checker.create_game_checks()
        
        # 执行检查
        result = self.health_checker.check_health('game_window_check')
        
        # 验证结果
        self.assertIsInstance(result, HealthCheckResult)
        self.assertEqual(result.component, 'game_window_check')
        # 在模拟环境中应该找到游戏窗口
        self.assertEqual(result.status, HealthStatus.HEALTHY)
        self.assertIn('Game window found', result.message)

    def test_health_checker_automation_system_check(self):
        """测试自动化系统检查."""
        self.health_checker.create_game_checks()
        
        # 执行检查
        result = self.health_checker.check_health('automation_system_check')
        
        # 验证结果（应该总是健康的，因为这是基本检查）
        self.assertIsInstance(result, HealthCheckResult)
        self.assertEqual(result.component, 'automation_system_check')
        self.assertEqual(result.status, HealthStatus.HEALTHY)
        self.assertIn('Automation system is ready', result.message)

    @patch('os.path.exists')
    @patch('os.walk')
    def test_health_checker_template_files_check(self, mock_walk, mock_exists):
        """测试模板文件检查."""
        # 模拟模板目录存在且有文件
        mock_exists.return_value = True
        mock_walk.return_value = [
            ('templates', [], ['template1.png', 'template2.jpg'])
        ]
        
        self.health_checker.create_game_checks()
        
        # 执行检查
        result = self.health_checker.check_health('template_files_check')
        
        # 验证结果
        self.assertIsInstance(result, HealthCheckResult)
        self.assertEqual(result.component, 'template_files_check')
        self.assertEqual(result.status, HealthStatus.HEALTHY)
        self.assertIn('Template files found: 2', result.message)

    def test_metrics_collector_game_collectors(self):
        """测试指标收集器的游戏相关收集器."""
        # 创建游戏相关收集器
        self.metrics_collector.create_game_collectors()
        
        # 验证收集器已注册
        collectors = self.metrics_collector._collectors
        
        expected_collectors = [
            'game_performance',
            'automation_metrics',
            'template_metrics',
            'system_health'
        ]
        
        for collector_name in expected_collectors:
            self.assertIn(collector_name, collectors)

    @patch('psutil.process_iter')
    @patch('win32gui.EnumWindows')
    def test_metrics_collector_game_performance(self, mock_enum, mock_process_iter):
        """测试游戏性能指标收集."""
        # 模拟游戏进程
        mock_proc = Mock()
        mock_proc.info = {
            'name': 'game_client.exe',
            'cpu_percent': 15.5,
            'memory_info': {'rss': 1024*1024*512}  # 512MB
        }
        mock_process_iter.return_value = [mock_proc]
        
        # 模拟游戏窗口
        mock_enum.return_value = None
        
        self.metrics_collector.create_game_collectors()
        
        # 收集指标
        self.metrics_collector._run_collectors()
        
        # 验证指标
        metrics = self.metrics_collector.get_all_metrics()
        
        # 检查是否有游戏性能相关的指标
        gauges = metrics.get('gauges', {})
        self.assertTrue(any('game_performance' in key for key in gauges.keys()))

    def test_metrics_collector_automation_metrics(self):
        """测试自动化系统指标收集."""
        self.metrics_collector.create_game_collectors()
        
        # 收集指标
        self.metrics_collector._run_collectors()
        
        # 验证指标
        metrics = self.metrics_collector.get_all_metrics()
        
        # 检查是否有自动化相关的指标
        gauges = metrics.get('gauges', {})
        self.assertTrue(any('automation_metrics' in key for key in gauges.keys()))

    @patch('os.path.exists')
    @patch('os.walk')
    @patch('os.path.getsize')
    def test_metrics_collector_template_metrics(self, mock_getsize, mock_walk, mock_exists):
        """测试模板文件指标收集."""
        # 模拟模板目录和文件
        mock_exists.return_value = True
        mock_walk.return_value = [
            ('templates', [], ['template1.png', 'template2.jpg', 'readme.txt'])
        ]
        mock_getsize.return_value = 1024 * 100  # 100KB per file
        
        self.metrics_collector.create_game_collectors()
        
        # 收集指标
        self.metrics_collector._run_collectors()
        
        # 验证指标
        metrics = self.metrics_collector.get_all_metrics()
        
        # 检查是否有模板相关的指标
        gauges = metrics.get('gauges', {})
        self.assertTrue(any('template_metrics' in key for key in gauges.keys()))

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_metrics_collector_system_health(self, mock_disk, mock_memory, mock_cpu):
        """测试系统健康指标收集."""
        # 模拟系统指标
        mock_cpu.return_value = 25.5
        mock_memory.return_value = Mock(percent=60.0, available=4*1024*1024*1024)
        mock_disk.return_value = Mock(
            used=50*1024*1024*1024,
            total=100*1024*1024*1024,
            free=50*1024*1024*1024
        )
        
        self.metrics_collector.create_game_collectors()
        
        # 收集指标
        self.metrics_collector._run_collectors()
        
        # 验证指标
        metrics = self.metrics_collector.get_all_metrics()
        
        # 检查是否有系统健康相关的指标
        gauges = metrics.get('gauges', {})
        self.assertTrue(any('system_health' in key for key in gauges.keys()))

    def test_monitoring_integration(self):
        """测试监控系统集成."""
        # 创建所有检查和收集器
        self.health_checker.create_basic_checks()
        self.health_checker.create_game_checks()
        self.metrics_collector.create_game_collectors()
        
        # 启动监控
        self.health_checker.start_monitoring()
        self.metrics_collector.start()
        
        # 等待一段时间让监控运行
        time.sleep(0.5)
        
        # 检查健康状态
        overall_status = self.health_checker.get_overall_status()
        self.assertIn(overall_status, [HealthStatus.HEALTHY, HealthStatus.UNHEALTHY, HealthStatus.DEGRADED, HealthStatus.UNKNOWN])
        
        # 检查指标收集
        metrics = self.metrics_collector.get_all_metrics()
        self.assertGreater(len(metrics), 0)
        
        # 停止监控
        self.health_checker.stop_monitoring()
        self.metrics_collector.stop()

    def test_monitoring_error_handling(self):
        """测试监控系统错误处理."""
        # 创建一个会失败的检查
        def failing_check():
            raise Exception("Test error")
        
        self.health_checker.add_check("failing_check", failing_check)
        
        # 执行检查
        result = self.health_checker.check_health("failing_check")
        
        # 验证错误处理
        self.assertEqual(result.status, HealthStatus.UNHEALTHY)
        self.assertIn("Test error", result.message)

    def test_metrics_collector_error_handling(self):
        """测试指标收集器错误处理."""
        # 创建一个会失败的收集器
        def failing_collector():
            raise Exception("Collector error")
        
        self.metrics_collector.register_collector("failing_collector", failing_collector)
        
        # 收集指标（不应该抛出异常）
        try:
            self.metrics_collector.collect_metrics()
        except Exception as e:
            self.fail(f"Metrics collection should handle errors gracefully: {e}")


if __name__ == '__main__':
    unittest.main()