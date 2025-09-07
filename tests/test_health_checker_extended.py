"""HealthChecker扩展测试用例.

测试HealthChecker类的所有方法和功能，包括：
- 健康检查的添加、移除、执行
- 监控循环的启动和停止
- 基本系统检查（CPU、内存、磁盘）
- 游戏相关检查（进程、窗口、自动化系统、模板文件）
- 超时处理和异常处理
- 状态管理和结果获取
"""

import pytest
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from src.monitoring.health_checker import (
    HealthChecker,
    HealthStatus,
    HealthCheckResult
)


class TestHealthChecker:
    """HealthChecker类的测试."""
    
    def setup_method(self):
        """测试前的设置."""
        self.health_checker = HealthChecker()
    
    def teardown_method(self):
        """测试后的清理."""
        if self.health_checker.is_monitoring:
            self.health_checker.stop_monitoring()
    
    def test_init(self):
        """测试初始化."""
        assert self.health_checker._check_interval == 30.0
        assert len(self.health_checker._checks) == 0
        assert not self.health_checker.is_monitoring
    
    def test_add_check(self):
        """测试添加检查."""
        def dummy_check():
            return HealthCheckResult(
                component="test",
                status=HealthStatus.HEALTHY,
                message="Test check"
            )
        
        self.health_checker.add_check("test", dummy_check)
        assert "test" in self.health_checker._checks
        assert len(self.health_checker._checks) == 1
    
    def test_remove_check(self):
        """测试移除检查."""
        def dummy_check():
            return HealthCheckResult(
                component="test",
                status=HealthStatus.HEALTHY,
                message="Test check"
            )
        
        self.health_checker.add_check("test", dummy_check)
        assert "test" in self.health_checker._checks
        
        result = self.health_checker.remove_check("test")
        assert result is True
        assert "test" not in self.health_checker._checks
        
        # 测试移除不存在的检查
        result = self.health_checker.remove_check("nonexistent")
        assert result is False
    
    def test_remove_nonexistent_check(self):
        """测试移除不存在的检查."""
        # 应该不会抛出异常
        self.health_checker.remove_check("nonexistent")
    
    def test_check_health_single(self):
        """测试单个健康检查."""
        def dummy_check():
            return HealthCheckResult(
                component="test",
                status=HealthStatus.HEALTHY,
                message="Test check"
            )
        
        self.health_checker.add_check("test", dummy_check)
        result = self.health_checker.check_health("test")
        
        # 检查结果是否保存
        assert "test" in self.health_checker._results
        assert self.health_checker._results["test"].status == HealthStatus.HEALTHY
    
    def test_check_health_nonexistent(self):
        """测试检查不存在的组件."""
        result = self.health_checker.check_health("nonexistent")
        
        assert result.component == "nonexistent"
        assert result.status == HealthStatus.UNKNOWN
        assert "not found" in result.message
    
    def test_check_health_all(self):
        """测试检查所有组件."""
        def check1():
            return HealthCheckResult(
                component="test1",
                status=HealthStatus.HEALTHY,
                message="Test check 1"
            )
        
        def check2():
            return HealthCheckResult(
                component="test2",
                status=HealthStatus.DEGRADED,
                message="Test check 2"
            )
        
        self.health_checker.add_check("test1", check1)
        self.health_checker.add_check("test2", check2)
        
        results = self.health_checker.check_health()
        
        assert len(results) == 2
        assert "test1" in results
        assert "test2" in results
        assert results["test1"].status == HealthStatus.HEALTHY
        assert results["test2"].status == HealthStatus.DEGRADED
    
    def test_check_health_with_exception(self):
        """测试检查过程中的异常处理."""
        def failing_check():
            raise ValueError("Test error")
        
        self.health_checker.add_check("failing", failing_check)
        result = self.health_checker.check_health("failing")
        
        assert result.component == "failing"
        assert result.status == HealthStatus.UNHEALTHY
        assert "Test error" in result.message
    
    def test_get_checks(self):
        """测试获取检查列表."""
        def dummy_check():
            return HealthCheckResult(
                component="test",
                status=HealthStatus.HEALTHY,
                message="Test check"
            )
        
        self.health_checker.add_check("test", dummy_check)
        checks = self.health_checker.get_checks()
        
        assert "test" in checks
        assert checks["test"] == dummy_check
    
    def test_get_status(self):
        """测试获取状态."""
        def dummy_check():
            return HealthCheckResult(
                component="test",
                status=HealthStatus.HEALTHY,
                message="Test check"
            )
        
        self.health_checker.add_check("test", dummy_check)
        self.health_checker.check_health("test")
        
        status = self.health_checker.get_status("test")
        assert status == HealthStatus.HEALTHY
        
        # 测试不存在的组件
        status = self.health_checker.get_status("nonexistent")
        assert status == HealthStatus.UNKNOWN
    
    def test_get_overall_status(self):
        """测试获取整体状态."""
        def healthy_check():
            return HealthCheckResult(
                component="healthy",
                status=HealthStatus.HEALTHY,
                message="Healthy check"
            )
        
        def degraded_check():
            return HealthCheckResult(
                component="degraded",
                status=HealthStatus.DEGRADED,
                message="Degraded check"
            )
        
        # 测试空状态
        assert self.health_checker.get_overall_status() == HealthStatus.UNKNOWN
        
        # 测试单个健康状态
        self.health_checker.add_check("healthy", healthy_check)
        self.health_checker.check_health("healthy")
        assert self.health_checker.get_overall_status() == HealthStatus.HEALTHY
        
        # 测试混合状态
        self.health_checker.add_check("degraded", degraded_check)
        self.health_checker.check_health("degraded")
        assert self.health_checker.get_overall_status() == HealthStatus.DEGRADED
    
    def test_get_results(self):
        """测试获取结果."""
        def dummy_check():
            return HealthCheckResult(
                component="test",
                status=HealthStatus.HEALTHY,
                message="Test check"
            )
        
        self.health_checker.add_check("test", dummy_check)
        self.health_checker.check_health("test")
        
        results = self.health_checker.get_results()
        assert "test" in results
        assert results["test"].status == HealthStatus.HEALTHY
    
    def test_start_stop(self):
        """测试启动和停止."""
        # 测试启动
        self.health_checker.start()
        assert self.health_checker.is_monitoring
        
        # 测试停止
        self.health_checker.stop()
        assert not self.health_checker.is_monitoring
    
    def test_start_stop_monitoring(self):
        """测试启动和停止监控."""
        def dummy_check():
            return HealthCheckResult(
                component="test",
                status=HealthStatus.HEALTHY,
                message="Test check"
            )
        
        self.health_checker.add_check("test", dummy_check)
        
        # 测试启动监控
        self.health_checker.start_monitoring()
        assert self.health_checker.is_monitoring
        assert self.health_checker._thread is not None
        
        # 等待一次监控循环
        time.sleep(0.2)
        
        # 测试停止监控
        self.health_checker.stop_monitoring()
        assert not self.health_checker.is_monitoring
        
        # 等待线程完全停止
        if self.health_checker._thread:
            self.health_checker._thread.join(timeout=1.0)
        assert self.health_checker._thread is None or not self.health_checker._thread.is_alive()
    
    def test_monitoring_loop(self):
        """测试监控循环."""
        check_count = 0
        
        def counting_check():
            nonlocal check_count
            check_count += 1
            return HealthCheckResult(
                component="counter",
                status=HealthStatus.HEALTHY,
                message=f"Check #{check_count}"
            )
        
        self.health_checker.add_check("counter", counting_check)
        self.health_checker.start_monitoring()
        
        # 等待几次检查
        time.sleep(0.3)
        
        self.health_checker.stop_monitoring()
        
        # 应该至少执行了1次检查
        assert check_count >= 1
        assert "counter" in self.health_checker._results
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_create_basic_checks(self, mock_disk, mock_memory, mock_cpu):
        """测试创建基本检查."""
        # 模拟psutil返回值
        mock_cpu.return_value = 50.0
        mock_memory.return_value = Mock(percent=60.0, available=4000000000, total=8000000000)
        mock_disk.return_value = Mock(used=350000000000, free=150000000000, total=500000000000)
        
        self.health_checker.create_basic_checks()
        
        # 检查是否添加了基本检查
        checks = self.health_checker.get_checks()
        assert "cpu" in checks
        assert "memory" in checks
        assert "disk" in checks
        
        # 执行检查
        results = self.health_checker.check_health()
        
        assert results["cpu"].status == HealthStatus.HEALTHY
        assert results["memory"].status == HealthStatus.HEALTHY
        assert results["disk"].status == HealthStatus.HEALTHY
    
    @patch('psutil.cpu_percent')
    def test_cpu_check_high_usage(self, mock_cpu):
        """测试CPU高使用率检查."""
        mock_cpu.return_value = 95.0
        
        self.health_checker.create_basic_checks()
        result = self.health_checker.check_health("cpu")
        
        assert result.status == HealthStatus.UNHEALTHY
        assert "95.0%" in result.message
    
    @patch('psutil.virtual_memory')
    def test_memory_check_high_usage(self, mock_memory):
        """测试内存高使用率检查."""
        mock_memory.return_value = Mock(percent=95.0, available=400000000, total=8000000000)
        
        self.health_checker.create_basic_checks()
        result = self.health_checker.check_health("memory")
        
        assert result.status == HealthStatus.UNHEALTHY
        assert "95.0%" in result.message
    
    @patch('psutil.disk_usage')
    def test_disk_check_high_usage(self, mock_disk):
        """测试磁盘高使用率检查."""
        # 设置used和total属性，使得使用率为95%
        mock_disk.return_value = Mock(used=475000000000, free=25000000000, total=500000000000)
        
        self.health_checker.create_basic_checks()
        result = self.health_checker.check_health("disk")
        
        assert result.status == HealthStatus.UNHEALTHY
        assert "95.0%" in result.message
    
    def test_basic_checks_without_psutil(self):
        """测试没有psutil时的基本检查."""
        with patch.dict('sys.modules', {'psutil': None}):
            self.health_checker.create_basic_checks()
            
            # 执行检查
            results = self.health_checker.check_health()
            
            # 应该返回UNKNOWN状态
            assert results["cpu"].status == HealthStatus.UNKNOWN
            assert results["memory"].status == HealthStatus.UNKNOWN
            assert results["disk"].status == HealthStatus.UNKNOWN
    
    @patch('psutil.process_iter')
    def test_create_game_checks(self, mock_process_iter):
        """测试创建游戏检查."""
        # 模拟游戏进程
        mock_proc = Mock()
        mock_proc.info = {'pid': 1234, 'name': 'game.exe'}
        mock_process_iter.return_value = [mock_proc]
        
        self.health_checker.create_game_checks()
        
        # 检查是否添加了游戏检查
        checks = self.health_checker.get_checks()
        assert "game_process_check" in checks
        assert "game_window_check" in checks
        assert "automation_system_check" in checks
        assert "template_files_check" in checks
        
        # 执行游戏进程检查
        result = self.health_checker.check_health("game_process_check")
        assert result.status == HealthStatus.HEALTHY
        assert "Game process found" in result.message
    
    @patch('psutil.process_iter')
    def test_game_process_check_no_game(self, mock_process_iter):
        """测试没有游戏进程时的检查."""
        # 模拟非游戏进程
        mock_proc = Mock()
        mock_proc.info = {'pid': 1234, 'name': 'notepad.exe'}
        mock_process_iter.return_value = [mock_proc]
        
        self.health_checker.create_game_checks()
        result = self.health_checker.check_health("game_process_check")
        
        assert result.status == HealthStatus.DEGRADED
        assert "No game processes detected" in result.message
    
    @patch('win32gui.EnumWindows')
    @patch('win32gui.IsWindowVisible')
    @patch('win32gui.GetWindowText')
    @patch('win32process.GetWindowThreadProcessId')
    @patch('psutil.Process')
    def test_game_window_check(self, mock_process, mock_get_pid, mock_get_text, mock_visible, mock_enum):
        """测试游戏窗口检查."""
        # 模拟窗口枚举
        def enum_callback(callback, windows):
            callback(12345, windows)  # 模拟一个窗口句柄
            return True
        
        mock_enum.side_effect = enum_callback
        mock_visible.return_value = True
        mock_get_text.return_value = "Game Client"
        mock_get_pid.return_value = (None, 1234)
        mock_process.return_value.name.return_value = "game.exe"
        
        self.health_checker.create_game_checks()
        result = self.health_checker.check_health("game_window_check")
        
        assert result.status == HealthStatus.HEALTHY
        assert "Game window found" in result.message
    
    def test_automation_system_check(self):
        """测试自动化系统检查."""
        self.health_checker.create_game_checks()
        result = self.health_checker.check_health("automation_system_check")
        
        assert result.status == HealthStatus.HEALTHY
        assert "Automation system is ready" in result.message
    
    @patch('os.path.exists')
    @patch('os.walk')
    def test_template_files_check(self, mock_walk, mock_exists):
        """测试模板文件检查."""
        mock_exists.return_value = True
        mock_walk.return_value = [
            ('templates', [], ['template1.png', 'template2.jpg', 'readme.txt'])
        ]
        
        self.health_checker.create_game_checks()
        result = self.health_checker.check_health("template_files_check")
        
        assert result.status == HealthStatus.HEALTHY
        assert "Template files found: 2" in result.message
    
    @patch('os.path.exists')
    def test_template_files_check_no_directory(self, mock_exists):
        """测试模板目录不存在时的检查."""
        mock_exists.return_value = False
        
        self.health_checker.create_game_checks()
        result = self.health_checker.check_health("template_files_check")
        
        assert result.status == HealthStatus.UNHEALTHY
        assert "Template directory not found" in result.message
    
    def test_run_check_with_timeout_success(self):
        """测试超时检查成功."""
        def quick_check():
            return HealthCheckResult(
                component="quick",
                status=HealthStatus.HEALTHY,
                message="Quick check"
            )
        
        result = self.health_checker._run_check_with_timeout(quick_check, "quick", 1.0)
        
        assert result.component == "quick"
        assert result.status == HealthStatus.HEALTHY
    
    def test_run_check_with_timeout_timeout(self):
        """测试超时检查超时."""
        def slow_check():
            time.sleep(2.0)
            return HealthCheckResult(
                component="slow",
                status=HealthStatus.HEALTHY,
                message="Slow check"
            )
        
        with pytest.raises(TimeoutError):
            self.health_checker._run_check_with_timeout(slow_check, "slow", 0.1)
    
    def test_run_check_with_timeout_exception(self):
        """测试超时检查异常."""
        def failing_check():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            self.health_checker._run_check_with_timeout(failing_check, "failing", 1.0)
    
    def test_update_overall_status(self):
        """测试更新整体状态."""
        # 添加不同状态的结果
        results = {
            "healthy": HealthCheckResult(
                component="healthy",
                status=HealthStatus.HEALTHY,
                message="Healthy"
            ),
            "degraded": HealthCheckResult(
                component="degraded",
                status=HealthStatus.DEGRADED,
                message="Degraded"
            )
        }
        
        self.health_checker._update_overall_status(results)
        
        # 应该是最差的状态
        assert self.health_checker.get_overall_status() == HealthStatus.DEGRADED
    
    def test_update_overall_status_with_unhealthy(self):
        """测试包含不健康状态的整体状态更新."""
        results = {
            "healthy": HealthCheckResult(
                component="healthy",
                status=HealthStatus.HEALTHY,
                message="Healthy"
            ),
            "unhealthy": HealthCheckResult(
                component="unhealthy",
                status=HealthStatus.UNHEALTHY,
                message="Unhealthy"
            )
        }
        
        self.health_checker._update_overall_status(results)
        
        # 应该是不健康状态
        assert self.health_checker.get_overall_status() == HealthStatus.UNHEALTHY


class TestHealthCheckResult:
    """HealthCheckResult类的测试."""
    
    def test_init(self):
        """测试初始化."""
        result = HealthCheckResult(
            component="test",
            status=HealthStatus.HEALTHY,
            message="Test message"
        )
        
        assert result.component == "test"
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Test message"
        assert result.details == {}
        assert result.timestamp is not None
    
    def test_init_with_details(self):
        """测试带详细信息的初始化."""
        details = {"key": "value"}
        result = HealthCheckResult(
            component="test",
            status=HealthStatus.HEALTHY,
            message="Test message",
            details=details
        )
        
        assert result.details == details
    
    def test_to_dict(self):
        """测试转换为字典."""
        result = HealthCheckResult(
            component="test",
            status=HealthStatus.HEALTHY,
            message="Test message",
            details={"key": "value"}
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["component"] == "test"
        assert result_dict["status"] == "healthy"
        assert result_dict["message"] == "Test message"
        assert result_dict["details"] == {"key": "value"}
        assert "timestamp" in result_dict


class TestHealthStatus:
    """HealthStatus枚举的测试."""
    
    def test_enum_values(self):
        """测试枚举值."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.UNKNOWN.value == "unknown"
    
    def test_enum_comparison(self):
        """测试枚举比较."""
        assert HealthStatus.HEALTHY != HealthStatus.DEGRADED
        assert HealthStatus.DEGRADED != HealthStatus.UNHEALTHY
        assert HealthStatus.UNHEALTHY != HealthStatus.UNKNOWN