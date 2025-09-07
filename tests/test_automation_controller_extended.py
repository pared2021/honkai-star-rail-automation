"""AutomationController扩展测试用例.

本模块包含AutomationController的扩展测试用例，用于提升测试覆盖率。
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
from typing import Dict, Any, List

from src.automation.automation_controller import AutomationController, AutomationStatus, AutomationTask
from src.core.config_manager import ConfigManager
from src.core.game_detector import GameDetector
from src.core.task_manager import TaskManager


class TestAutomationControllerExtended:
    """AutomationController扩展测试类."""
    
    @pytest.fixture
    def mock_config_manager(self):
        """创建模拟配置管理器."""
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_automation_config.return_value = {
            'auto_restart_game': True,
            'max_continuous_failures': 3,
            'check_interval': 1.0,
            'scene_detection_threshold': 0.7
        }
        return config_manager
    
    @pytest.fixture
    def mock_game_detector(self):
        """创建模拟游戏检测器."""
        detector = Mock(spec=GameDetector)
        detector.is_game_running.return_value = True
        detector.capture_screen.return_value = Mock()
        detector.capture_screenshot.return_value = Mock()
        detector.find_template.return_value = {'found': True, 'confidence': 0.8}
        return detector
    
    @pytest.fixture
    def mock_task_manager(self):
        """创建模拟任务管理器."""
        task_manager = Mock(spec=TaskManager)
        task_manager.create_task.return_value = "task_123"
        task_manager.stop_task.return_value = True
        task_manager.get_task.return_value = None
        task_manager.cancel_concurrent_task.return_value = True
        return task_manager
    
    @pytest.fixture
    def automation_controller(self, mock_config_manager, mock_game_detector, mock_task_manager):
        """创建自动化控制器实例."""
        controller = AutomationController(
            config_manager=mock_config_manager,
            game_detector=mock_game_detector,
            task_manager=mock_task_manager
        )
        return controller
    
    def test_execute_action_click_success(self, automation_controller):
        """测试点击动作执行成功."""
        automation_controller.start()
        
        with patch('pyautogui.click') as mock_click:
            result = automation_controller.execute_action('click', x=100, y=200)
            assert result is True
            mock_click.assert_called_once_with(100, 200)
    
    def test_execute_action_click_without_pyautogui(self, automation_controller):
        """测试没有pyautogui时的点击动作."""
        automation_controller.start()
        
        with patch('pyautogui.click', side_effect=ImportError()):
            result = automation_controller.execute_action('click', x=100, y=200)
            assert result is True  # 应该使用模拟点击
    
    def test_execute_action_click_invalid_coordinates(self, automation_controller):
        """测试无效坐标的点击动作."""
        automation_controller.start()
        
        # 测试负坐标
        result = automation_controller.execute_action('click', x=-10, y=20)
        assert result is False
        
        # 测试无效类型
        result = automation_controller.execute_action('click', x='invalid', y=20)
        assert result is False
    
    def test_execute_action_screenshot_success(self, automation_controller):
        """测试截图动作执行成功."""
        automation_controller.start()
        
        with patch('cv2.imwrite') as mock_imwrite:
            mock_imwrite.return_value = True
            result = automation_controller.execute_action('screenshot', path='test.png')
            assert result is True
            mock_imwrite.assert_called_once()
    
    def test_execute_action_screenshot_invalid_path(self, automation_controller):
        """测试无效路径的截图动作."""
        automation_controller.start()
        
        result = automation_controller.execute_action('screenshot', path=123)
        assert result is False
    
    def test_execute_action_wait_success(self, automation_controller):
        """测试等待动作执行成功."""
        automation_controller.start()
        
        start_time = time.time()
        result = automation_controller.execute_action('wait', duration=0.1)
        end_time = time.time()
        
        assert result is True
        assert end_time - start_time >= 0.1
    
    def test_execute_action_wait_invalid_duration(self, automation_controller):
        """测试无效等待时间."""
        automation_controller.start()
        
        # 测试负数
        result = automation_controller.execute_action('wait', duration=-1)
        assert result is False
        
        # 测试无效类型
        result = automation_controller.execute_action('wait', duration='invalid')
        assert result is False
    
    def test_execute_action_wait_long_duration(self, automation_controller):
        """测试过长等待时间被限制."""
        automation_controller.start()
        
        start_time = time.time()
        result = automation_controller.execute_action('wait', duration=100)  # 超过60秒限制
        end_time = time.time()
        
        assert result is True
        # 应该被限制为60秒，但测试中我们不等那么久
        assert end_time - start_time < 100
    
    def test_execute_action_unknown_action(self, automation_controller):
        """测试未知动作."""
        automation_controller.start()
        
        result = automation_controller.execute_action('unknown_action')
        assert result is False
    
    def test_execute_action_not_running(self, automation_controller):
        """测试控制器未运行时执行动作."""
        result = automation_controller.execute_action('click', x=100, y=200)
        assert result is False
    
    def test_execute_action_empty_action(self, automation_controller):
        """测试空动作名称."""
        automation_controller.start()
        
        result = automation_controller.execute_action('')
        assert result is False
    
    def test_run_tasks_success(self, automation_controller):
        """测试运行任务列表成功."""
        # 清空预注册的任务
        automation_controller.clear_tasks()
        
        # 创建测试任务
        task1 = AutomationTask(
            id="task1",
            name="测试任务1",
            action=lambda: {"status": "success"},
            priority=1
        )
        task2 = AutomationTask(
            id="task2",
            name="测试任务2",
            action=lambda: {"status": "success"},
            priority=2
        )
        
        automation_controller.add_task(task1)
        automation_controller.add_task(task2)
        
        with patch.object(automation_controller, 'execute') as mock_execute:
            mock_execute.return_value = {"status": "success"}
            result = automation_controller.run()
            
            assert result is True
            assert mock_execute.call_count == 2
    
    def test_run_tasks_with_failures(self, automation_controller):
        """测试运行任务列表有失败."""
        task1 = AutomationTask(
            id="task1",
            name="测试任务1",
            action=lambda: {"status": "success"},
            priority=1
        )
        
        automation_controller.add_task(task1)
        
        with patch.object(automation_controller, 'execute') as mock_execute:
            mock_execute.return_value = {"status": "failed", "message": "任务失败"}
            result = automation_controller.run()
            
            assert result is False
    
    def test_run_custom_task_list(self, automation_controller):
        """测试运行自定义任务列表."""
        task = AutomationTask(
            id="custom_task",
            name="自定义任务",
            action=lambda: {"status": "success"},
            priority=1
        )
        
        with patch.object(automation_controller, 'execute') as mock_execute:
            mock_execute.return_value = {"status": "success"}
            result = automation_controller.run([task])
            
            assert result is True
            mock_execute.assert_called_once_with("custom_task")
    
    def test_task_management_methods(self, automation_controller):
        """测试任务管理方法."""
        # 清空预注册的任务
        automation_controller.clear_tasks()
        
        task = AutomationTask(
            id="test_task",
            name="测试任务",
            action=lambda: {"status": "success"},
            priority=1
        )
        
        # 测试添加任务
        automation_controller.add_task(task)
        assert len(automation_controller.get_tasks()) == 1
        
        # 测试根据ID获取任务
        found_task = automation_controller.get_task_by_id("test_task")
        assert found_task is not None
        assert found_task.id == "test_task"
        
        # 测试获取不存在的任务
        not_found = automation_controller.get_task_by_id("nonexistent")
        assert not_found is None
        
        # 测试移除任务
        result = automation_controller.remove_task("test_task")
        assert result is True
        assert len(automation_controller.get_tasks()) == 0
        
        # 测试移除不存在的任务
        result = automation_controller.remove_task("nonexistent")
        assert result is False
        
        # 测试清空任务
        automation_controller.add_task(task)
        automation_controller.clear_tasks()
        assert len(automation_controller.get_tasks()) == 0
    
    def test_get_available_automation_tasks(self, automation_controller):
        """测试获取可用自动化任务."""
        # 初始状态应该注册基本任务
        tasks = automation_controller.get_available_automation_tasks()
        assert len(tasks) > 0
        
        # 再次调用应该返回相同的任务
        tasks2 = automation_controller.get_available_automation_tasks()
        assert len(tasks2) == len(tasks)
    
    def test_get_task_status(self, automation_controller):
        """测试获取任务状态."""
        task = AutomationTask(
            id="status_task",
            name="状态测试任务",
            action=lambda: {"status": "success"},
            priority=1,
            scene_requirement="main_menu"
        )
        automation_controller.add_task(task)
        
        status = automation_controller.get_task_status()
        
        assert "controller_status" in status
        assert "is_running" in status
        assert "total_tasks" in status
        assert "tasks" in status
        assert "game_detector_available" in status
        assert "task_manager_available" in status
        
        assert status["total_tasks"] >= 1
        assert len(status["tasks"]) >= 1
        
        # 检查任务信息
        task_info = next((t for t in status["tasks"] if t["id"] == "status_task"), None)
        assert task_info is not None
        assert task_info["name"] == "状态测试任务"
        assert task_info["scene_requirement"] == "main_menu"
    
    def test_interface_methods(self, automation_controller):
        """测试接口方法."""
        # 测试启动自动化
        result = automation_controller.start_automation()
        assert result is True
        
        # 测试获取自动化状态
        status = automation_controller.get_automation_status()
        assert status == "running"
        
        # 测试获取可用任务
        tasks = automation_controller.get_available_tasks()
        assert isinstance(tasks, list)
        assert len(tasks) > 0
        
        # 测试停止自动化
        result = automation_controller.stop_automation()
        assert result is True
        
        status = automation_controller.get_automation_status()
        assert status == "stopped"
    
    def test_execute_with_scene_requirement_mismatch(self, automation_controller):
        """测试场景要求不匹配的任务执行."""
        task = AutomationTask(
            id="scene_task",
            name="场景任务",
            action=lambda: {"status": "success"},
            priority=1,
            scene_requirement="battle"
        )
        automation_controller.add_task(task)
        automation_controller.start()
        
        with patch.object(automation_controller, '_detect_current_scene') as mock_detect:
            mock_detect.return_value = {"scene": "main_menu"}
            result = automation_controller.execute("scene_task")
            
            assert result["status"] == "skipped"
            assert "场景不匹配" in result["message"]
    
    def test_execute_with_retry_logic(self, automation_controller):
        """测试任务重试逻辑."""
        retry_count = 0
        
        def failing_action():
            nonlocal retry_count
            retry_count += 1
            if retry_count < 3:
                raise Exception("模拟失败")
            return {"status": "success"}
        
        task = AutomationTask(
            id="retry_task",
            name="重试任务",
            action=failing_action,
            priority=1,
            max_retries=3
        )
        automation_controller.add_task(task)
        automation_controller.start()
        
        # 第一次执行应该失败并重试
        result1 = automation_controller.execute("retry_task")
        assert result1["status"] == "retry"
        assert result1["retry_count"] == 1
        
        # 第二次执行应该再次失败并重试
        result2 = automation_controller.execute("retry_task")
        assert result2["status"] == "retry"
        assert result2["retry_count"] == 2
        
        # 第三次执行应该成功
        result3 = automation_controller.execute("retry_task")
        assert result3["status"] == "success"
    
    def test_execute_max_retries_exceeded(self, automation_controller):
        """测试超过最大重试次数."""
        def always_failing_action():
            raise Exception("总是失败")
        
        task = AutomationTask(
            id="failing_task",
            name="失败任务",
            action=always_failing_action,
            priority=1,
            max_retries=2
        )
        automation_controller.add_task(task)
        automation_controller.start()
        
        # 第一次执行应该返回retry
        result1 = automation_controller.execute("failing_task")
        assert result1["status"] == "retry"
        assert result1["retry_count"] == 1
        
        # 第二次执行应该返回failed（达到最大重试次数）
        result2 = automation_controller.execute("failing_task")
        assert result2["status"] == "failed"
        assert result2["retry_count"] == 2
    
    @pytest.mark.asyncio
    async def test_automation_loop_methods(self, automation_controller):
        """测试自动化循环方法."""
        # 测试启动自动化循环
        result = await automation_controller.start_automation_loop()
        assert result is True
        
        # 测试重复启动
        result = await automation_controller.start_automation_loop()
        assert result is True
        
        # 测试停止自动化循环
        result = await automation_controller.stop_automation_loop()
        assert result is True
    
    def test_basic_task_actions(self, automation_controller):
        """测试基本任务动作."""
        automation_controller.start()
        
        # 测试游戏状态检测任务
        result = automation_controller._detect_game_status()
        assert "status" in result
        assert "timestamp" in result
        
        # 测试场景检测任务
        result = automation_controller._detect_current_scene()
        assert "status" in result
        assert "timestamp" in result
        
        # 测试截图任务
        result = automation_controller._take_screenshot()
        assert "status" in result
        assert "timestamp" in result
    
    def test_error_handling_in_basic_tasks(self, automation_controller):
        """测试基本任务的错误处理."""
        # 测试没有游戏检测器的情况
        controller_no_detector = AutomationController()
        
        result = controller_no_detector._detect_game_status()
        assert result["status"] == "error"
        
        result = controller_no_detector._detect_current_scene()
        assert result["status"] == "error"
        
        result = controller_no_detector._take_screenshot()
        assert result["status"] == "error"
    
    def test_automation_status_error_state(self, automation_controller):
        """测试错误状态的自动化状态."""
        automation_controller._status = AutomationStatus.ERROR
        
        status = automation_controller.get_automation_status()
        assert status == "error"