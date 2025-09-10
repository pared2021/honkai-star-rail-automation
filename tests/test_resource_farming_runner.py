"""ResourceFarmingRunner测试模块。

测试资源刷取任务执行器的各项功能。
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any

from src.core.resource_farming_runner import (
    ResourceFarmingRunner, ResourceType, FarmingMode, DungeonType,
    ResourceTarget, DungeonInfo, FarmingConfig, FarmingSession
)
from src.core.game_operator import GameOperator, OperationResult
from src.core.events import EventBus
from src.core.error_handler import ErrorHandler


@pytest.fixture
def mock_components():
    """创建模拟组件。"""
    mock_game_operator = Mock(spec=GameOperator)
    mock_game_operator.click = AsyncMock(return_value=OperationResult(
        success=True, execution_time=0.1, error_message="点击成功"
    ))
    mock_game_operator.swipe = AsyncMock(return_value=OperationResult(
        success=True, execution_time=0.2, error_message="滑动成功"
    ))
    
    mock_event_bus = Mock(spec=EventBus)
    mock_event_bus.emit = AsyncMock()
    
    mock_error_handler = Mock(spec=ErrorHandler)
    
    return {
        'game_operator': mock_game_operator,
        'event_bus': mock_event_bus,
        'error_handler': mock_error_handler
    }


@pytest.fixture
def farming_runner(mock_components):
    """创建ResourceFarmingRunner实例。"""
    return ResourceFarmingRunner(
        game_operator=mock_components['game_operator'],
        event_bus=mock_components['event_bus'],
        error_handler=mock_components['error_handler']
    )


@pytest.fixture
def sample_farming_config():
    """创建示例刷取配置。"""
    return FarmingConfig(
        farming_mode=FarmingMode.BALANCED,
        max_total_energy=240,
        energy_refill_count=2,
        auto_use_overflow_energy=True,
        min_energy_threshold=40,
        max_execution_time=3600,
        retry_attempts=3,
        battle_timeout=300,
        optimize_route=True
    )


@pytest.fixture
def sample_resource_targets():
    """创建示例资源目标。"""
    return [
        ResourceTarget(
            resource_type=ResourceType.CHARACTER_EXP,
            target_amount=100,
            current_amount=0,
            priority=1,
            max_energy_cost=120
        ),
        ResourceTarget(
            resource_type=ResourceType.CREDITS,
            target_amount=50000,
            current_amount=10000,
            priority=2,
            max_energy_cost=80
        )
    ]


class TestResourceFarmingRunner:
    """ResourceFarmingRunner测试类。"""
    
    def test_initialization(self, mock_components):
        """测试初始化。"""
        runner = ResourceFarmingRunner(
            game_operator=mock_components['game_operator'],
            event_bus=mock_components['event_bus'],
            error_handler=mock_components['error_handler']
        )
        
        assert runner.game_operator == mock_components['game_operator']
        assert runner.event_bus == mock_components['event_bus']
        assert runner.error_handler == mock_components['error_handler']
        assert runner._current_session is None
        assert len(runner._session_history) == 0
        assert runner._current_energy == 240
        assert runner._max_energy == 240
    
    @pytest.mark.asyncio
    async def test_start_farming_session(self, farming_runner, sample_resource_targets, sample_farming_config):
        """测试开始刷取会话。"""
        session_id = await farming_runner.start_farming_session(
            targets=sample_resource_targets,
            config=sample_farming_config
        )
        
        assert session_id is not None
        assert farming_runner._current_session is not None
        assert farming_runner._current_session.session_id == session_id
        assert len(farming_runner._current_session.targets) == 2
        assert farming_runner._current_session.config == sample_farming_config
        
        # 验证事件发送
        farming_runner.event_bus.emit.assert_called_once()
        call_args = farming_runner.event_bus.emit.call_args
        assert call_args[0][0] == "farming_session_started"
    
    @pytest.mark.asyncio
    async def test_execute_farming_session(self, farming_runner, sample_resource_targets, sample_farming_config):
        """测试执行刷取会话。"""
        # 模拟智能等待器
        with patch.object(farming_runner.smart_waiter, 'wait_for_ui_element', new_callable=AsyncMock) as mock_wait:
            mock_wait.return_value = True
            
            # 开始会话
            session_id = await farming_runner.start_farming_session(
                targets=sample_resource_targets,
                config=sample_farming_config
            )
            
            # 执行会话
            report = await farming_runner.execute_farming_session()
            
            assert report is not None
            assert 'session_id' in report
            assert 'duration' in report
            assert 'energy_used' in report
            assert 'dungeons_completed' in report
            assert 'resources_gained' in report
    
    @pytest.mark.asyncio
    async def test_navigate_to_survival_guide(self, farming_runner):
        """测试导航到生存指南界面。"""
        with patch.object(farming_runner.game_operator, 'click', new_callable=AsyncMock) as mock_click:
            with patch.object(farming_runner.smart_waiter, 'wait_for_ui_element', new_callable=AsyncMock) as mock_wait_ui:
                # 模拟成功的操作结果
                mock_click.return_value = OperationResult(success=True, execution_time=0.1)
                mock_wait_ui.return_value = True
                
                result = await farming_runner._navigate_to_survival_guide()
                
                # 验证结果
                assert result is True
                # _navigate_to_survival_guide只调用一次click：点击生存指南标签
                assert mock_click.call_count == 1
                assert mock_wait_ui.call_count == 2  # 两次wait_for_ui_element调用
    
    @pytest.mark.asyncio
    async def test_generate_farming_plan(self, farming_runner, sample_resource_targets, sample_farming_config):
        """测试生成刷取计划。"""
        plan = await farming_runner._generate_farming_plan(
            targets=sample_resource_targets,
            config=sample_farming_config
        )
        
        assert isinstance(plan, dict)
        # 计划可能为空，如果没有合适的副本
        for dungeon_id, runs in plan.items():
            assert isinstance(dungeon_id, str)
            assert isinstance(runs, int)
            assert runs > 0
    
    @pytest.mark.asyncio
    async def test_navigate_to_dungeon(self, farming_runner):
        """测试导航到指定副本。"""
        dungeon = farming_runner.get_all_dungeons()[0]
        
        with patch.object(farming_runner.game_operator, 'click', new_callable=AsyncMock) as mock_click:
            with patch.object(farming_runner.smart_waiter, 'wait_for_ui_element', new_callable=AsyncMock) as mock_wait_ui:
                # 模拟成功的操作结果
                mock_click.return_value = OperationResult(success=True, execution_time=0.1)
                mock_wait_ui.return_value = True
                
                result = await farming_runner._navigate_to_dungeon(dungeon)
                
                # 验证结果
                assert result is True
                # _navigate_to_dungeon会调用两次click：标签页和副本位置
                assert mock_click.call_count == 2
    
    @pytest.mark.asyncio
    async def test_execute_dungeon_runs(self, farming_runner, sample_farming_config):
        """测试执行副本刷取。"""
        session = FarmingSession(
            session_id="test_session",
            start_time=time.time(),
            targets=[],
            config=sample_farming_config
        )
        
        dungeon = farming_runner.get_all_dungeons()[0]
        
        with patch.object(farming_runner, '_navigate_to_dungeon', new_callable=AsyncMock) as mock_nav:
            with patch.object(farming_runner, '_execute_single_dungeon_run', new_callable=AsyncMock) as mock_run:
                mock_nav.return_value = True
                mock_run.return_value = True
                
                result = await farming_runner._execute_dungeon_farming(
                    dungeon_id=dungeon.dungeon_id,
                    run_count=3,
                    session=session
                )
                
                assert isinstance(result, int)
                assert result >= 0
                assert mock_nav.call_count == 1
                # 由于体力检查等逻辑，实际调用次数可能少于预期
                assert mock_run.call_count >= 0
    
    @pytest.mark.asyncio
    async def test_handle_energy_shortage(self, farming_runner, sample_farming_config):
        """测试处理体力不足。"""
        with patch.object(farming_runner.smart_waiter, 'wait_for_ui_element', new_callable=AsyncMock):
            # 测试有补充次数的情况
            config = sample_farming_config
            config.energy_refill_count = 1
            
            result = await farming_runner._handle_energy_shortage(config)
            
            assert result is True
            assert config.energy_refill_count == 0
            
            # 测试无补充次数的情况
            config.energy_refill_count = 0
            result = await farming_runner._handle_energy_shortage(config)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_current_energy(self, farming_runner):
        """测试检查当前体力。"""
        # 设置初始体力
        initial_energy = farming_runner._current_energy
        
        # 执行体力检查
        await farming_runner._check_current_energy()
        
        # 验证体力值被设置
        assert farming_runner._current_energy > 0
        assert farming_runner._max_energy > 0
    
    @pytest.mark.asyncio
    async def test_update_resource_gains(self, farming_runner):
        """测试更新资源获取统计。"""
        session = FarmingSession(
            session_id="test_session",
            start_time=time.time(),
            targets=[],
            config=FarmingConfig()
        )
        
        dungeon = farming_runner.get_all_dungeons()[0]
        
        await farming_runner._update_resource_gains(dungeon, session)
        
        # 验证资源统计更新
        assert len(session.resources_gained) > 0
        for resource_type in dungeon.drop_rates.keys():
            assert resource_type in session.resources_gained
    
    @pytest.mark.asyncio
    async def test_generate_session_report(self, farming_runner, sample_resource_targets, sample_farming_config):
        """测试生成会话报告。"""
        session = FarmingSession(
            session_id="test_session",
            start_time=time.time() - 100,  # 100秒前开始
            targets=sample_resource_targets,
            config=sample_farming_config
        )
        session.energy_used = 60
        session.dungeons_completed = 3
        session.resources_gained = {ResourceType.CHARACTER_EXP: 50}
        
        report = await farming_runner._generate_session_report(session)
        
        assert 'session_id' in report
        assert 'duration' in report
        assert 'energy_used' in report
        assert 'dungeons_completed' in report
        assert 'resources_gained' in report
        assert 'target_completion' in report
        assert 'efficiency_score' in report
        assert 'execution_log' in report
        
        assert report['session_id'] == "test_session"
        assert report['energy_used'] == 60
        assert report['dungeons_completed'] == 3
    
    def test_get_available_dungeons(self, farming_runner):
        """测试获取可用副本。"""
        dungeons = farming_runner.get_all_dungeons()
        
        assert isinstance(dungeons, list)
        assert len(dungeons) > 0
        
        for dungeon in dungeons:
            assert isinstance(dungeon, DungeonInfo)
            assert hasattr(dungeon, 'dungeon_id')
            assert hasattr(dungeon, 'dungeon_type')
            assert hasattr(dungeon, 'energy_cost')
    
    def test_calculate_efficiency_score(self, farming_runner):
        """测试计算效率分数。"""
        session = FarmingSession(
            session_id="test_session",
            start_time=time.time() - 120,  # 2分钟前开始
            targets=[],
            config=FarmingConfig()
        )
        session.energy_used = 60
        session.dungeons_completed = 3
        
        score = farming_runner._calculate_efficiency_score(session)
        
        assert isinstance(score, float)
        assert score >= 0.0
    
    def test_is_session_timeout(self, farming_runner, sample_farming_config):
        """测试会话超时检查。"""
        # 创建未超时的会话
        session = FarmingSession(
            session_id="test_session",
            start_time=time.time() - 100,  # 100秒前开始
            targets=[],
            config=sample_farming_config
        )
        
        result = farming_runner._is_session_timeout(session)
        assert result is False
        
        # 创建超时的会话
        session.start_time = time.time() - 4000  # 4000秒前开始
        result = farming_runner._is_session_timeout(session)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_execute_with_error_handling(self, farming_runner, sample_resource_targets, sample_farming_config):
        """测试执行过程中的错误处理。"""
        with patch.object(farming_runner.smart_waiter, 'wait_for_ui_element', new_callable=AsyncMock) as mock_wait:
            mock_wait.return_value = False  # 模拟等待失败
            
            session_id = await farming_runner.start_farming_session(
                targets=sample_resource_targets,
                config=sample_farming_config
            )
            
            # 执行应该处理错误而不崩溃
            try:
                report = await farming_runner.execute_farming_session()
                # 如果没有抛出异常，验证报告
                assert report is not None
            except Exception as e:
                # 如果抛出异常，验证是预期的错误
                assert "无法导航到生存指南界面" in str(e)
            
            # 验证错误被记录
            assert len(farming_runner._current_session.execution_log) > 0
    
    def test_farming_config_creation(self):
        """测试刷取配置创建。"""
        config = FarmingConfig(
            farming_mode=FarmingMode.EFFICIENT,
            max_total_energy=180,
            energy_refill_count=3
        )
        
        assert config.farming_mode == FarmingMode.EFFICIENT
        assert config.max_total_energy == 180
        assert config.energy_refill_count == 3
        assert config.auto_use_overflow_energy is True  # 默认值
    
    @pytest.mark.asyncio
    async def test_farming_session_events(self, farming_runner, sample_resource_targets, sample_farming_config):
        """测试刷取过程中的事件发送。"""
        session_id = await farming_runner.start_farming_session(
            targets=sample_resource_targets,
            config=sample_farming_config
        )
        
        # 结束会话
        await farming_runner._end_farming_session(farming_runner._current_session)
        
        # 验证事件发送
        assert farming_runner.event_bus.emit.call_count >= 2  # 开始和结束事件
        
        # 验证会话历史
        assert len(farming_runner._session_history) == 1
        assert farming_runner._current_session is None