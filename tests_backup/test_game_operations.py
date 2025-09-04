import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.core.game_operations import (
    GameOperations, OperationResult, OperationConfig, TaskResult, GameTaskType
)
from src.core.game_detector import SceneType


class TestGameOperations:
    """GameOperations类的单元测试"""
    
    @pytest.fixture
    def mock_game_detector(self):
        """创建模拟的GameDetector"""
        detector = Mock()
        detector.detect_current_scene.return_value = SceneType.MAIN_MENU
        detector.find_ui_element.return_value = Mock(x=100, y=100)
        detector.find_multiple_ui_elements.return_value = [Mock(x=100, y=100)]
        detector.wait_for_ui_element.return_value = True
        detector.get_game_status.return_value = {"running": True}
        detector.current_scene = SceneType.MAIN_MENU
        return detector
    
    @pytest.fixture
    def mock_action_executor(self):
        """创建模拟的ActionExecutor"""
        executor = Mock()
        executor.click.return_value = True
        executor.key.return_value = True
        executor.wait.return_value = True
        executor.execute_click.return_value = Mock(success=True)
        return executor
    
    @pytest.fixture
    def mock_config_manager(self):
        """创建模拟的ConfigManager"""
        config_manager = Mock()
        config_manager.get_config.return_value = {}
        return config_manager
    
    @pytest.fixture
    def game_operations(self, mock_game_detector, mock_action_executor, mock_config_manager):
        """创建GameOperations实例"""
        return GameOperations(mock_game_detector, mock_action_executor, mock_config_manager)
    
    def test_initialization(self, game_operations, mock_game_detector, mock_action_executor, mock_config_manager):
        """测试GameOperations初始化"""
        assert game_operations.game_detector == mock_game_detector
        assert game_operations.action_executor == mock_action_executor
        assert game_operations.config_manager == mock_config_manager
        assert game_operations.is_running is False
        assert isinstance(game_operations.operation_config, OperationConfig)
    
    def test_random_delay(self, game_operations):
        """测试随机延迟功能"""
        with patch('time.sleep') as mock_sleep:
            game_operations._random_delay(1.0, 2.0)
            mock_sleep.assert_called_once()
            # 验证延迟时间在指定范围内
            delay_time = mock_sleep.call_args[0][0]
            assert 1.0 <= delay_time <= 2.0
    
    def test_safe_click(self, game_operations):
        """测试安全点击功能"""
        ui_element = Mock(position=(100, 100), size=(50, 30))
        
        # 测试成功点击
        game_operations.action_executor.execute_click.return_value = Mock(success=True)
        result = game_operations._safe_click(ui_element)
        assert result is True
        
        # 测试点击失败
        game_operations.action_executor.execute_click.return_value = Mock(success=False)
        result = game_operations._safe_click(ui_element)
        assert result is False
    
    def test_wait_for_scene_change(self, game_operations):
        """测试场景变化等待"""
        target_scene = SceneType.COMBAT
        
        # 测试场景变化成功
        game_operations.game_detector.detect_current_scene.side_effect = [
            SceneType.MAIN_MENU, SceneType.COMBAT
        ]
        
        with patch('time.time', side_effect=[0, 0.5, 1.0]):
            result = game_operations._wait_for_scene_change(target_scene, timeout=5.0)
            assert result is True
    
    def test_ensure_game_foreground(self, game_operations):
        """测试确保游戏前台"""
        # 测试游戏已在前台
        game_operations.game_detector.is_game_running.return_value = True
        game_operations.game_detector.bring_game_to_front.return_value = True
        result = game_operations._ensure_game_foreground()
        assert result is True
        
        # 测试游戏不运行的情况
        game_operations.game_detector.is_game_running.return_value = False
        result = game_operations._ensure_game_foreground()
        assert result is False  # 游戏不运行时应该返回False
    
    @pytest.mark.asyncio
    async def test_execute_daily_stamina_consumption_success(self, game_operations):
        """测试每日体力消耗执行成功"""
        config = {
            "stamina_threshold": 160,
            "preferred_domains": ["weapon_material", "character_exp"]
        }
        
        # 模拟成功场景
        game_operations.game_detector.detect_current_scene.return_value = SceneType.MAIN_MENU
        game_operations._ensure_game_foreground = Mock(return_value=True)
        game_operations._execute_domain_runs = AsyncMock(return_value=True)
        
        result = await game_operations.execute_daily_stamina_consumption(config)
        
        assert isinstance(result, TaskResult)
        assert result.task_type == GameTaskType.DAILY_STAMINA
        assert result.result == OperationResult.SUCCESS
        assert "体力消耗完成" in result.message
    
    @pytest.mark.asyncio
    async def test_execute_daily_missions_success(self, game_operations):
        """测试每日任务执行成功"""
        config = {
            "auto_claim_rewards": True,
            "mission_types": ["dispatch", "assignment", "synthesis"]
        }
        
        # 模拟成功场景
        game_operations._ensure_game_foreground = Mock(return_value=True)
        game_operations._execute_dispatch_missions = AsyncMock(return_value=True)
        game_operations._execute_assignment_missions = AsyncMock(return_value=True)
        game_operations._execute_synthesis_missions = AsyncMock(return_value=True)
        
        result = await game_operations.execute_daily_missions(config)
        
        assert isinstance(result, TaskResult)
        assert result.task_type == GameTaskType.DAILY_MISSIONS
        assert result.result == OperationResult.SUCCESS
        assert "任务完成" in result.message
    
    @pytest.mark.asyncio
    async def test_execute_auto_combat_success(self, game_operations):
        """测试自动战斗执行成功"""
        config = {
            "auto_battle": True,
            "skill_priority": ["ultimate", "skill", "basic"]
        }
        
        # 模拟战斗场景
        game_operations.game_detector.detect_current_scene.return_value = SceneType.COMBAT
        game_operations._ensure_game_foreground = Mock(return_value=True)
        game_operations.game_detector.wait_for_ui_element.return_value = True
        
        result = await game_operations.execute_auto_combat(config)
        
        assert isinstance(result, TaskResult)
        assert result.task_type == GameTaskType.COMBAT_AUTO
        assert result.result == OperationResult.SUCCESS
        assert "自动战斗完成" in result.message
    
    @pytest.mark.asyncio
    async def test_execute_auto_combat_wrong_scene(self, game_operations):
        """测试自动战斗在错误场景"""
        config = {"auto_battle": True}
        
        # 模拟非战斗场景
        game_operations.game_detector.detect_current_scene.return_value = SceneType.MAIN_MENU
        game_operations._ensure_game_foreground = Mock(return_value=True)
        
        result = await game_operations.execute_auto_combat(config)
        
        assert result.result == OperationResult.SCENE_ERROR
        assert "当前不在战斗场景" in result.message
    
    @pytest.mark.asyncio
    async def test_execute_mail_collection_success(self, game_operations):
        """测试邮件收集执行成功"""
        config = {"auto_delete": True}
        
        # 模拟成功场景
        game_operations._ensure_game_foreground = Mock(return_value=True)
        game_operations._wait_for_scene_change = Mock(return_value=True)
        
        result = await game_operations.execute_mail_collection(config)
        
        assert isinstance(result, TaskResult)
        assert result.task_type == GameTaskType.MAIL_COLLECTION
        assert result.result == OperationResult.SUCCESS
        assert "邮件收集完成" in result.message
    
    @pytest.mark.asyncio
    async def test_execute_operation_failure(self, game_operations):
        """测试操作执行失败"""
        config = {}
        
        # 模拟游戏无法置于前台
        game_operations._ensure_game_foreground = Mock(return_value=False)
        
        result = await game_operations.execute_daily_stamina_consumption(config)
        
        assert result.result == OperationResult.FAILED
        assert "无法将游戏窗口置于前台" in result.message
    
    def test_stop_all_operations(self, game_operations):
        """测试停止所有操作"""
        game_operations.is_running = True
        game_operations.stop_all_operations()
        assert game_operations.is_running is False
    
    def test_get_operation_status(self, game_operations):
        """测试获取操作状态"""
        status = game_operations.get_operation_status()
        
        assert isinstance(status, dict)
        assert "is_running" in status
        assert "game_status" in status
        assert "current_scene" in status
        assert "operation_config" in status
        
        # 验证配置信息
        config = status["operation_config"]
        assert "max_retries" in config
        assert "operation_timeout" in config
        assert "safety_checks" in config
    
    def test_operation_config(self, game_operations):
        """测试操作配置"""
        config = game_operations.operation_config
        assert config.max_retries == 3
        assert config.operation_timeout == 30.0
        assert config.safety_checks is True
    
    @pytest.mark.asyncio
    async def test_execute_dispatch_missions(self, game_operations):
        """测试委托任务执行"""
        # 模拟委托任务成功
        game_operations.game_detector.find_multiple_ui_elements.return_value = [
            Mock(x=100, y=100), Mock(x=150, y=150)
        ]
        
        result = await game_operations._execute_dispatch_missions()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_execute_assignment_missions(self, game_operations):
        """测试派遣任务执行"""
        # 模拟派遣任务成功
        game_operations.game_detector.find_ui_element.side_effect = [
            Mock(x=100, y=100),  # assignment_button
            Mock(x=150, y=150),  # available_assignment
            Mock(x=200, y=200),  # confirm_button
        ]
        
        result = await game_operations._execute_assignment_missions()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_execute_synthesis_missions(self, game_operations):
        """测试合成任务执行"""
        # 模拟合成任务成功
        game_operations.game_detector.find_ui_element.side_effect = [
            Mock(x=100, y=100),  # synthesis_button
            Mock(x=150, y=150),  # craft_button
            Mock(x=200, y=200),  # confirm_button
        ]
        game_operations.game_detector.find_multiple_ui_elements.return_value = [
            Mock(x=100, y=100)
        ]
        
        result = await game_operations._execute_synthesis_missions()
        assert result is True


def run_async_test(coro):
    """运行异步测试的辅助函数"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


if __name__ == "__main__":
    # 运行测试
    pytest.main(["-v", __file__])