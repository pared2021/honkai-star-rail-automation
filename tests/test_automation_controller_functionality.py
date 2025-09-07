"""AutomationController功能测试."""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from src.automation.automation_controller import AutomationController
from src.interfaces.automation_interface import IAutomationController


class TestAutomationControllerFunctionality:
    """AutomationController功能测试类."""
    
    def setup_method(self):
        """设置测试环境."""
        self.mock_game_detector = MagicMock()
        self.mock_task_manager = MagicMock()
        
        self.controller = AutomationController(config={})
        
        # 手动设置模拟对象
        self.controller._game_detector = self.mock_game_detector
        self.controller._task_manager = self.mock_task_manager
    
    def test_implements_interface(self):
        """测试AutomationController实现了IAutomationController接口."""
        assert isinstance(self.controller, IAutomationController)
    
    def test_interface_methods_exist(self):
        """测试接口方法存在."""
        # 检查接口方法是否存在
        assert hasattr(self.controller, 'start_automation')
        assert hasattr(self.controller, 'stop_automation')
        assert hasattr(self.controller, 'get_automation_status')
        assert hasattr(self.controller, 'get_available_tasks')
        
        # 检查方法是否可调用
        assert callable(self.controller.start_automation)
        assert callable(self.controller.stop_automation)
        assert callable(self.controller.get_automation_status)
        assert callable(self.controller.get_available_tasks)
    
    def test_start_stop_automation(self):
        """测试启动和停止自动化."""
        # 测试启动
        result = self.controller.start_automation()
        assert result is True
        assert self.controller.get_automation_status() == 'running'
        
        # 测试停止
        result = self.controller.stop_automation()
        assert result is True
        assert self.controller.get_automation_status() == 'stopped'
    
    def test_get_available_tasks(self):
        """测试获取可用任务."""
        tasks = self.controller.get_available_tasks()
        assert isinstance(tasks, list)
        # 应该包含基本任务
        expected_tasks = ['游戏检测', '场景检测', '自动截图']
        for task in expected_tasks:
            assert task in tasks
    
    @pytest.mark.asyncio
    async def test_automation_loop_start_stop(self):
        """测试自动化循环的启动和停止."""
        # 测试启动自动化循环
        result = await self.controller.start_automation_loop()
        assert result is True
        
        # 等待一小段时间让循环开始
        await asyncio.sleep(0.1)
        
        # 测试停止自动化循环
        result = await self.controller.stop_automation_loop()
        assert result is True
    
    def test_scene_detection(self):
        """测试场景检测功能."""
        # 模拟游戏检测器返回截图
        self.mock_game_detector.capture_screen.return_value = Mock()
        self.mock_game_detector.detect_scene.return_value = Mock(value='main_menu')
        
        # 测试场景检测
        result = self.controller._detect_current_scene()
        assert result['status'] == 'success'
        assert result['scene'] in ['main_menu', 'world_map', 'battle', 'mission_menu', 'inventory', 'unknown']
    
    def test_scene_detection_no_game_detector(self):
        """测试没有游戏检测器时的场景检测."""
        controller = AutomationController()
        result = controller._detect_current_scene()
        assert result['status'] == 'error'
        assert result['message'] == '游戏检测器未初始化'
    
    @pytest.mark.asyncio
    async def test_handle_scenes(self):
        """测试场景处理功能."""
        # 测试各种场景处理
        scenes = ['main_menu', 'world_map', 'battle', 'mission_menu', 'unknown']
        
        for scene in scenes:
            try:
                await self.controller._handle_scene(scene)
                # 如果没有抛出异常，说明处理成功
                assert True
            except Exception as e:
                pytest.fail(f"处理场景{scene}时出错: {e}")
    
    def test_automation_config(self):
        """测试自动化配置功能."""
        # 获取默认配置
        config = self.controller.get_automation_config()
        assert isinstance(config, dict)
        assert 'auto_restart_game' in config
        assert 'max_continuous_failures' in config
        assert 'check_interval' in config
        assert 'scene_detection_threshold' in config
        
        # 设置新配置
        new_config = {'check_interval': 5.0, 'max_continuous_failures': 10}
        self.controller.set_automation_config(new_config)
        
        # 验证配置已更新
        updated_config = self.controller.get_automation_config()
        assert updated_config['check_interval'] == 5.0
        assert updated_config['max_continuous_failures'] == 10
    
    def test_current_automation_tasks(self):
        """测试当前自动化任务管理."""
        # 初始应该为空
        tasks = self.controller.get_current_automation_tasks()
        assert isinstance(tasks, list)
        assert len(tasks) == 0
    
    @pytest.mark.asyncio
    async def test_start_daily_missions(self):
        """测试启动日常任务."""
        # 模拟任务管理器
        self.mock_task_manager.create_task.return_value = 'task_123'
        self.mock_task_manager.start_task.return_value = True
        
        # 启动日常任务
        await self.controller._start_daily_missions()
        
        # 验证任务管理器被调用
        self.mock_task_manager.create_task.assert_called_once()
        self.mock_task_manager.start_task.assert_called_once_with('task_123')
    
    @pytest.mark.asyncio
    async def test_start_resource_collection(self):
        """测试启动资源收集."""
        # 模拟任务管理器
        self.mock_task_manager.create_task.return_value = 'task_456'
        self.mock_task_manager.start_task.return_value = True
        
        # 启动资源收集
        await self.controller._start_resource_collection()
        
        # 验证任务管理器被调用
        self.mock_task_manager.create_task.assert_called_once()
        self.mock_task_manager.start_task.assert_called_once_with('task_456')
    
    @pytest.mark.asyncio
    async def test_claim_available_missions(self):
        """测试领取可用任务."""
        # 模拟找到任务领取按钮
        self.mock_game_detector.find_template.return_value = {
            'found': True,
            'center': (200, 150),
            'confidence': 0.9
        }
        
        # 模拟点击操作
        with patch('pyautogui.click') as mock_click:
            await self.controller._claim_available_missions()
            # 由于pyautogui可能未安装，这里主要测试逻辑流程
    
    @pytest.mark.asyncio
    async def test_process_pending_tasks(self):
        """测试处理待处理任务."""
        # 添加一些模拟任务
        self.controller._current_automation_tasks = ['task1', 'task2', 'task3']
        
        # 模拟任务状态
        self.mock_task_manager.get_task_status.side_effect = [
            'completed',  # task1 已完成
            'running',    # task2 运行中
            'failed'      # task3 失败
        ]
        
        # 处理待处理任务
        await self.controller._process_pending_tasks()
        
        # 验证已完成和失败的任务被移除
        remaining_tasks = self.controller.get_current_automation_tasks()
        assert 'task2' in remaining_tasks  # 运行中的任务应该保留
        assert 'task1' not in remaining_tasks  # 已完成的任务应该被移除
        assert 'task3' not in remaining_tasks  # 失败的任务应该被移除
    
    @pytest.mark.asyncio
    async def test_should_do_daily_missions(self):
        """测试是否应该执行日常任务的判断."""
        # 当前实现总是返回False以避免无限循环
        result = await self.controller._should_do_daily_missions()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_should_collect_resources(self):
        """测试是否应该收集资源的判断."""
        # 当前实现总是返回False以避免无限循环
        result = await self.controller._should_collect_resources()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_handle_game_closed(self):
        """测试处理游戏关闭的情况."""
        # 启动自动化
        self.controller.start_automation()
        assert self.controller._running is True
        
        # 处理游戏关闭
        await self.controller._handle_game_closed()
        
        # 验证自动化已停止
        assert self.controller._running is False


class TestAutomationControllerIntegration:
    """AutomationController集成测试类."""
    
    def test_controller_with_real_dependencies(self):
        """测试使用真实依赖的控制器."""
        # 这里可以测试与真实GameDetector和TaskManager的集成
        # 由于依赖复杂，暂时跳过
        pass
    
    @pytest.mark.asyncio
    async def test_full_automation_workflow(self):
        """测试完整的自动化工作流程."""
        # 创建真实的依赖对象（如果可用）
        try:
            from src.core.game_detector import GameDetector
            from src.task_management.task_manager import TaskManager
            
            controller = AutomationController(config={})
            
            # 如果依赖可用，设置真实对象
            try:
                game_detector = GameDetector()
                task_manager = TaskManager()
                controller._game_detector = game_detector
                controller._task_manager = task_manager
            except Exception:
                # 如果真实对象创建失败，使用模拟对象
                controller._game_detector = MagicMock()
                controller._task_manager = MagicMock()
        except ImportError:
            # 如果导入失败，使用模拟对象
            mock_game_detector = Mock()
            mock_task_manager = Mock()
            
            controller = AutomationController(config={})
            controller._game_detector = mock_game_detector
            controller._task_manager = mock_task_manager
        
        # 模拟游戏运行
        controller._game_detector.is_game_running.return_value = True
        controller._game_detector.capture_screen.return_value = Mock()
        controller._game_detector.find_template.return_value = {'found': False}
        
        # 启动自动化
        controller.start_automation()
        
        # 启动自动化循环（短时间）
        loop_task = asyncio.create_task(controller._automation_loop())
        
        # 等待一小段时间
        await asyncio.sleep(0.1)
        
        # 停止自动化
        controller.stop_automation()
        
        # 等待循环结束
        try:
            await asyncio.wait_for(loop_task, timeout=1.0)
        except asyncio.TimeoutError:
            loop_task.cancel()
        
        # 验证状态
        assert controller.get_automation_status() == 'stopped'