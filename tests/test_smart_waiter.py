"""SmartWaiter智能等待机制测试模块"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List, Any, Callable

from src.core.smart_waiter import (
    SmartWaiter, WaitConfig, WaitStrategy, WaitResult, WaitCondition,
    ElementWaitCondition, SceneWaitCondition, CustomWaitCondition,
    TimeoutWaitStrategy, ExponentialBackoffStrategy, AdaptiveWaitStrategy
)
from src.core.game_operator import GameOperator
from src.core.events import EventBus


class TestWaitConditions:
    """等待条件测试类"""
    
    @pytest.fixture
    def mock_game_operator(self):
        """创建模拟游戏操作器"""
        mock = Mock(spec=GameOperator)
        mock.click = AsyncMock()
        mock.swipe = AsyncMock()
        mock.input_text = AsyncMock()
        mock.find_ui_element = Mock(return_value=Mock(center=(100, 200)))
        mock.get_current_scene = Mock(return_value='main_menu')
        return mock
    
    @pytest.mark.asyncio
    async def test_element_wait_condition(self, mock_game_operator):
        """测试元素等待条件"""
        condition = ElementWaitCondition(
            element_name="test_button",
            timeout=5.0,
            check_interval=0.5
        )
        
        # 测试元素存在
        mock_game_detector.find_ui_element.return_value = Mock(center=(100, 200))
        
        result = await condition.check(mock_game_operator)
        
        assert result is True
        mock_game_detector.find_ui_element.assert_called_with("test_button")
    
    @pytest.mark.asyncio
    async def test_element_wait_condition_not_found(self, mock_game_operator):
        """测试元素不存在的等待条件"""
        condition = ElementWaitCondition(
            element_name="missing_button",
            timeout=1.0,
            check_interval=0.1
        )
        
        # 测试元素不存在
        mock_game_detector.find_ui_element.return_value = None
        
        result = await condition.check(mock_game_operator)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_scene_wait_condition(self, mock_game_operator):
        """测试场景等待条件"""
        condition = SceneWaitCondition(
            expected_scene="main_menu",
            timeout=5.0,
            check_interval=0.5
        )
        
        # 测试场景匹配
        mock_game_operator.get_current_scene.return_value = "main_menu"
        
        result = await condition.check(mock_game_operator)
        
        assert result is True
        mock_game_operator.get_current_scene.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_scene_wait_condition_mismatch(self, mock_game_operator):
        """测试场景不匹配的等待条件"""
        condition = SceneWaitCondition(
            expected_scene="main_menu",
            timeout=1.0,
            check_interval=0.1
        )
        
        # 测试场景不匹配
        mock_game_operator.get_current_scene.return_value = "battle_scene"
        
        result = await condition.check(mock_game_operator)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_custom_wait_condition(self, mock_game_operator):
        """测试自定义等待条件"""
        async def custom_check(game_operator):
            return True
        
        condition = CustomWaitCondition(
            check_function=custom_check,
            timeout=5.0,
            check_interval=0.5,
            description="Custom condition test"
        )
        
        result = await condition.check(mock_game_operator)
        
        assert result is True
        assert condition.description == "Custom condition test"
    
    @pytest.mark.asyncio
    async def test_custom_wait_condition_with_exception(self, mock_game_operator):
        """测试自定义等待条件异常处理"""
        async def failing_check(game_operator):
            raise Exception("Check failed")
        
        condition = CustomWaitCondition(
            check_function=failing_check,
            timeout=1.0,
            check_interval=0.1
        )
        
        result = await condition.check(mock_game_operator)
        
        assert result is False


class TestWaitStrategies:
    """等待策略测试类"""
    
    @pytest.fixture
    def mock_condition(self):
        """创建模拟等待条件"""
        condition = Mock(spec=WaitCondition)
        condition.timeout = 5.0
        condition.check_interval = 0.5
        return condition
    
    @pytest.fixture
    def mock_game_operator(self):
        """创建模拟游戏操作器"""
        return Mock(spec=GameOperator)
    
    @pytest.mark.asyncio
    async def test_timeout_wait_strategy_success(self, mock_condition, mock_game_operator):
        """测试超时等待策略成功情况"""
        strategy = TimeoutWaitStrategy()
        
        # 模拟条件检查成功
        mock_condition.check = AsyncMock(return_value=True)
        
        result = await strategy.wait(mock_condition, mock_game_operator)
        
        assert result.success is True
        assert result.elapsed_time > 0
        assert "successfully" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_timeout_wait_strategy_timeout(self, mock_condition, mock_game_operator):
        """测试超时等待策略超时情况"""
        strategy = TimeoutWaitStrategy()
        
        # 设置短超时时间
        mock_condition.timeout = 0.1
        mock_condition.check_interval = 0.05
        
        # 模拟条件检查失败
        mock_condition.check = AsyncMock(return_value=False)
        
        result = await strategy.wait(mock_condition, mock_game_operator)
        
        assert result.success is False
        assert result.elapsed_time >= 0.1
        assert "timeout" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_strategy(self, mock_condition, mock_game_operator):
        """测试指数退避策略"""
        strategy = ExponentialBackoffStrategy(
            initial_delay=0.1,
            max_delay=1.0,
            backoff_factor=2.0
        )
        
        # 设置短超时时间
        mock_condition.timeout = 0.5
        
        # 模拟条件检查在第3次成功
        call_count = 0
        async def mock_check(game_operator):
            nonlocal call_count
            call_count += 1
            return call_count >= 3
        
        mock_condition.check = mock_check
        
        result = await strategy.wait(mock_condition, mock_game_operator)
        
        assert result.success is True
        assert call_count >= 3
    
    @pytest.mark.asyncio
    async def test_adaptive_wait_strategy(self, mock_condition, mock_game_operator):
        """测试自适应等待策略"""
        strategy = AdaptiveWaitStrategy(
            min_interval=0.1,
            max_interval=1.0,
            success_factor=0.8,
            failure_factor=1.5
        )
        
        # 模拟条件检查成功
        mock_condition.check = AsyncMock(return_value=True)
        
        result = await strategy.wait(mock_condition, mock_game_operator)
        
        assert result.success is True
        assert result.elapsed_time > 0
    
    @pytest.mark.asyncio
    async def test_adaptive_wait_strategy_adaptation(self, mock_game_operator):
        """测试自适应等待策略的适应性调整"""
        strategy = AdaptiveWaitStrategy()
        condition = Mock(spec=WaitCondition)
        condition.timeout = 1.0
        condition.check = AsyncMock(return_value=True)
        
        import time
        start_time = time.time()
        result = await strategy.wait(condition, mock_game_operator)
        elapsed = time.time() - start_time
        
        assert result.success
        assert elapsed < 1.0


class TestSmartWaiter:
    """SmartWaiter测试类"""
    
    @pytest.fixture
    def mock_game_operator(self):
        """创建模拟游戏操作器"""
        return Mock(spec=GameOperator)
    
    @pytest.fixture
    def mock_event_bus(self):
        """创建模拟事件总线"""
        return Mock(spec=EventBus)
    
    @pytest.fixture
    def smart_waiter(self, mock_game_operator, mock_event_bus):
        """创建SmartWaiter实例"""
        waiter = SmartWaiter()
        waiter.game_operator = mock_game_operator
        waiter.event_bus = mock_event_bus
        return waiter
    
    def test_initialization(self, smart_waiter, mock_game_operator, mock_event_bus):
        """测试初始化"""
        assert smart_waiter.game_operator == mock_game_operator
        assert smart_waiter.event_bus == mock_event_bus
        assert len(smart_waiter.wait_history) == 0
        assert smart_waiter.default_config is not None
    
    def test_set_default_config(self, smart_waiter):
        """测试设置默认配置"""
        from src.core.smart_waiter import WaitConfig, WaitStrategy
        new_config = WaitConfig(strategy=WaitStrategy.EXPONENTIAL)
        
        smart_waiter.default_config = new_config
        
        assert smart_waiter.default_config == new_config
    
    @pytest.mark.asyncio
    async def test_wait_for_element(self, smart_waiter, mock_game_operator):
        """测试等待元素"""
        # 模拟元素存在
        mock_game_detector.find_ui_element.return_value = Mock(center=(100, 200))
        
        # 创建条件函数
        async def element_condition():
            return mock_game_detector.find_ui_element("test_button")
        
        result, value = await smart_waiter.wait_for_condition(
            condition_func=element_condition,
            condition_name="test_button_element"
        )
        
        assert result == WaitResult.SUCCESS
        assert len(smart_waiter.wait_history) == 1
        mock_game_operator.find_element.assert_called_with("test_button")
    
    @pytest.mark.asyncio
    async def test_wait_for_element_timeout(self, smart_waiter, mock_game_operator):
        """测试等待元素超时"""
        from src.core.smart_waiter import WaitConfig
        # 模拟元素不存在
        mock_game_operator.find_element.return_value = None
        
        # 创建条件函数
        async def element_condition():
            return mock_game_operator.find_element("missing_button")
        
        config = WaitConfig(timeout=0.1)
        result, value = await smart_waiter.wait_for_condition(
            condition_func=element_condition,
            condition_name="missing_button_element",
            config=config
        )
        
        assert result == WaitResult.TIMEOUT
        assert len(smart_waiter.wait_history) == 1
    
    @pytest.mark.asyncio
    async def test_wait_for_scene(self, smart_waiter, mock_game_operator):
        """测试等待场景"""
        # 模拟场景匹配
        mock_game_operator.get_current_scene.return_value = "main_menu"
        
        # 创建条件函数
        async def scene_condition():
            return mock_game_operator.get_current_scene() == "main_menu"
        
        result, value = await smart_waiter.wait_for_condition(
            condition_func=scene_condition,
            condition_name="main_menu_scene"
        )
        
        assert result == WaitResult.SUCCESS
        assert len(smart_waiter.wait_history) == 1
        mock_game_operator.get_current_scene.assert_called()
    
    @pytest.mark.asyncio
    async def test_wait_for_scene_change(self, smart_waiter, mock_game_operator):
        """测试等待场景变化"""
        # 模拟场景变化
        call_count = 0
        def mock_get_scene():
            nonlocal call_count
            call_count += 1
            return "battle_scene" if call_count > 2 else "main_menu"
        
        mock_game_operator.get_current_scene.side_effect = mock_get_scene
        
        # 创建条件函数
        initial_scene = "main_menu"
        async def scene_change_condition():
            current_scene = mock_game_operator.get_current_scene()
            return current_scene != initial_scene
        
        result, value = await smart_waiter.wait_for_condition(
            condition_func=scene_change_condition,
            condition_name="scene_change"
        )
        
        assert result == WaitResult.SUCCESS
        assert len(smart_waiter.wait_history) == 1
    
    @pytest.mark.asyncio
    async def test_wait_for_condition(self, smart_waiter, mock_game_operator):
        """测试等待自定义条件"""
        async def custom_condition():
            return True
        
        result, value = await smart_waiter.wait_for_condition(
            condition_func=custom_condition,
            condition_name="Custom test condition"
        )
        
        assert result == WaitResult.SUCCESS
        assert len(smart_waiter.wait_history) == 1
    
    @pytest.mark.asyncio
    async def test_wait_with_custom_strategy(self, smart_waiter, mock_game_operator):
        """测试使用自定义策略等待"""
        from src.core.smart_waiter import WaitConfig, WaitStrategy
        custom_config = WaitConfig(strategy=WaitStrategy.EXPONENTIAL, initial_delay=0.1)
        
        # 模拟元素存在
        mock_game_operator.find_element.return_value = {'position': (100, 200)}
        
        # 创建条件函数
        async def element_condition():
            return mock_game_operator.find_element("test_button")
        
        result, value = await smart_waiter.wait_for_condition(
            condition_func=element_condition,
            condition_name="test_button_custom_strategy",
            config=custom_config
        )
        
        assert result == WaitResult.SUCCESS
    
    @pytest.mark.asyncio
    async def test_wait_multiple_conditions(self, smart_waiter, mock_game_operator):
        """测试等待多个条件"""
        # 模拟元素存在
        mock_game_operator.find_element.return_value = {'position': (100, 200)}
        
        # 创建条件函数列表
        async def button1_condition():
            return mock_game_operator.find_element("button1")
        
        async def button2_condition():
            return mock_game_operator.find_element("button2")
        
        conditions = [
            (button1_condition, "button1"),
            (button2_condition, "button2")
        ]
        
        result, results = await smart_waiter.wait_for_multiple_conditions(
            conditions, require_all=True
        )
        
        assert result == WaitResult.SUCCESS
        assert len(results) == 2
        assert len(smart_waiter.wait_history) == 1
    
    @pytest.mark.asyncio
    async def test_wait_multiple_conditions_any(self, smart_waiter, mock_game_operator):
        """测试等待多个条件（任一满足）"""
        # 模拟第一个元素不存在，第二个存在
        def mock_find_element(element_name):
            if element_name == "existing_button":
                return {'position': (100, 200)}
            return None
        
        mock_game_operator.find_element.side_effect = mock_find_element
        
        # 创建条件函数列表
        async def missing_button_condition():
            return mock_game_operator.find_element("missing_button")
        
        async def existing_button_condition():
            return mock_game_operator.find_element("existing_button")
        
        conditions = [
            (missing_button_condition, "missing_button"),
            (existing_button_condition, "existing_button")
        ]
        
        result, results = await smart_waiter.wait_for_multiple_conditions(
            conditions, require_all=False
        )
        
        assert result == WaitResult.SUCCESS
        assert len(results) == 2
        assert any(results.values())
    
    def test_get_wait_statistics(self, smart_waiter):
        """测试获取等待统计"""
        # 手动设置统计数据
        smart_waiter.stats['total_waits'] = 3
        smart_waiter.stats['successful_waits'] = 2
        smart_waiter.stats['timeout_waits'] = 1
        smart_waiter.stats['average_wait_time'] = 2.43
        
        stats = smart_waiter.get_statistics()
        
        assert stats['total_waits'] == 3
        assert stats['successful_waits'] == 2
        assert stats['timeout_waits'] == 1
        assert stats['average_wait_time'] == 2.43
    
    def test_get_recent_wait_history(self, smart_waiter):
        """测试获取等待历史"""
        from src.core.smart_waiter import WaitContext
        
        # 添加等待历史
        now = datetime.now()
        history_items = [
            WaitContext(
                condition_name='element_test',
                start_time=now - timedelta(hours=2)
            ),
            WaitContext(
                condition_name='scene_test',
                start_time=now - timedelta(minutes=30)
            )
        ]
        
        smart_waiter.wait_history.extend(history_items)
        
        # 获取等待历史
        recent_history = smart_waiter.get_wait_history(limit=10)
        
        assert len(recent_history) == 2
        assert recent_history[1].condition_name == 'scene_test'
    
    def test_clear_wait_history(self, smart_waiter):
        """测试清理等待历史"""
        from src.core.smart_waiter import WaitContext
        
        # 添加一些历史记录
        smart_waiter.wait_history = [
            WaitContext(condition_name=f'test_{i}', start_time=datetime.now()) 
            for i in range(5)
        ]
        
        smart_waiter.clear_history()
        
        assert len(smart_waiter.wait_history) == 0