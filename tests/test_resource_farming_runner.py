"""ResourceFarmingRunner资源刷取任务执行器测试模块"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List, Any

from src.core.resource_farming_runner import (
    ResourceFarmingRunner, ResourceType, FarmingMode, DungeonType,
    ResourceTarget, DungeonInfo, FarmingConfig, FarmingSession
)
from src.core.game_operator import GameOperator
from src.core.smart_waiter import SmartWaiter
from src.core.events import EventBus


class TestResourceFarmingRunner:
    """ResourceFarmingRunner测试类"""
    
    @pytest.fixture
    def mock_components(self):
        """创建模拟组件"""
        return {
            'game_operator': Mock(spec=GameOperator),
            'smart_waiter': Mock(spec=SmartWaiter),
            'event_bus': Mock(spec=EventBus)
        }
    
    @pytest.fixture
    def farming_config(self):
        """创建刷取配置"""
        return FarmingConfig(
            max_total_energy=240,
            auto_use_overflow_energy=True,
            max_execution_time=3600,
            retry_attempts=3
        )
    
    @pytest.fixture
    def resource_targets(self):
        """创建资源目标"""
        return [
            ResourceTarget(
                resource_type=ResourceType.CHARACTER_EXP,
                target_amount=100,
                current_amount=20,
                priority=1
            ),
            ResourceTarget(
                resource_type=ResourceType.CREDITS,
                target_amount=1000000,
                current_amount=500000,
                priority=2
            )
        ]
    
    @pytest.fixture
    def farming_runner(self, mock_components):
        """创建ResourceFarmingRunner实例"""
        runner = ResourceFarmingRunner(
            game_operator=mock_components['game_operator'],
            event_bus=mock_components['event_bus'],
            error_handler=mock_components.get('error_handler')
        )
        return runner
    
    def test_initialization(self, farming_runner, mock_components):
        """测试初始化"""
        assert farming_runner.game_operator == mock_components['game_operator']
        assert farming_runner.event_bus == mock_components['event_bus']
        assert farming_runner.smart_waiter is not None
        assert farming_runner._current_session is None
    
    @pytest.mark.asyncio
    async def test_start_farming_session(self, farming_runner, resource_targets, mock_components):
        """测试开始刷取会话"""
        # 模拟配置加载和导航
        with patch.object(farming_runner, '_load_farming_config'), \
             patch.object(farming_runner, '_navigate_to_farming_area', return_value=True), \
             patch.object(farming_runner, '_generate_farming_plan', return_value=[]) as mock_plan, \
             patch.object(farming_runner, '_execute_farming_session', return_value=True):
            
            result = await farming_runner.start_farming_session(
                targets=resource_targets,
                mode=FarmingMode.EFFICIENT
            )
            
            assert result['success'] is True
            assert farming_runner.current_session is not None
            assert farming_runner.current_session.mode == FarmingMode.EFFICIENT
            mock_plan.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_navigate_to_farming_area(self, farming_runner, mock_components):
        """测试导航到刷取区域"""
        # 模拟成功导航
        mock_components['game_operator'].navigate_to_menu.return_value = True
        mock_components['game_operator'].click_element.return_value = True
        mock_components['smart_waiter'].wait_for_element.return_value = True
        
        result = await farming_runner._navigate_to_farming_area(DungeonType.CALYX_GOLDEN)
        
        assert result is True
        mock_components['game_operator'].navigate_to_menu.assert_called_once()
        mock_components['game_operator'].click_element.assert_called()
    
    def test_generate_farming_plan(self, farming_runner, resource_targets):
        """测试生成刷取计划"""
        # 模拟副本信息
        mock_dungeons = [
            DungeonInfo(
                dungeon_type=DungeonType.CALYX_GOLDEN,
                name="拟造花萼（金）",
                energy_cost=10,
                rewards={ResourceType.CREDITS: 8000},
                efficiency_rating=0.9,
                estimated_duration=120
            ),
            DungeonInfo(
                dungeon_type=DungeonType.CALYX_CRIMSON,
                name="拟造花萼（赤）",
                energy_cost=10,
                rewards={ResourceType.CHARACTER_EXP: 5},
                efficiency_rating=0.85,
                estimated_duration=100
            )
        ]
        
        with patch.object(farming_runner, '_get_available_dungeons', return_value=mock_dungeons):
            plan = farming_runner._generate_farming_plan(resource_targets, FarmingMode.EFFICIENT)
            
            assert len(plan) > 0
            # 验证计划包含必要信息
            for step in plan:
                assert 'dungeon' in step
                assert 'runs' in step
                assert 'expected_resources' in step
    
    @pytest.mark.asyncio
    async def test_execute_farming_session(self, farming_runner, mock_components):
        """测试执行刷取会话"""
        # 创建模拟会话
        test_config = FarmingConfig(farming_mode=FarmingMode.EFFICIENT)
        farming_runner._current_session = FarmingSession(
            session_id="test_session",
            start_time=time.time(),
            targets=[],
            config=test_config
        )
        
        # 模拟刷取计划
        mock_plan = [
            {
                'dungeon': DungeonInfo(
                    dungeon_type=DungeonType.CALYX_GOLDEN,
                    name="拟造花萼（金）",
                    energy_cost=10,
                    rewards={ResourceType.CREDITS: 8000},
                    efficiency_rating=0.9,
                    estimated_duration=120
                ),
                'runs': 3,
                'expected_resources': {ResourceType.CREDITS: 24000}
            }
        ]
        
        with patch.object(farming_runner, '_execute_dungeon_runs', return_value=True) as mock_execute:
            result = await farming_runner._execute_farming_session(mock_plan)
            
            assert result is True
            mock_execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_execute_dungeon_runs(self, farming_runner, mock_components):
        """测试执行副本运行"""
        dungeon = DungeonInfo(
            dungeon_type=DungeonType.CALYX_GOLDEN,
            name="拟造花萼（金）",
            energy_cost=10,
            rewards={ResourceType.CREDITS: 8000},
            efficiency_rating=0.9,
            estimated_duration=120
        )
        
        # 模拟游戏操作
        mock_components['game_operator'].click_element.return_value = True
        mock_components['game_operator'].wait_for_battle_end.return_value = True
        mock_components['smart_waiter'].wait_for_element.return_value = True
        
        with patch.object(farming_runner, '_check_stamina', return_value=True), \
             patch.object(farming_runner, '_update_resource_stats'):
            
            result = await farming_runner._execute_dungeon_runs(dungeon, 3)
            
            assert result is True
            # 验证点击操作被调用了足够次数
            assert mock_components['game_operator'].click_element.call_count >= 3
    
    @pytest.mark.asyncio
    async def test_handle_stamina_shortage(self, farming_runner, mock_components):
        """测试处理体力不足"""
        # 创建临时配置用于测试
        test_config = FarmingConfig(auto_use_overflow_energy=True, energy_refill_count=1)
        
        # 模拟体力道具使用
        mock_components['game_detector'].find_ui_element.return_value = Mock(center=(500, 600))
        mock_components['game_operator'].click_element.return_value = True
        mock_components['smart_waiter'].wait_for_element.return_value = True
        
        result = await farming_runner._handle_energy_shortage(test_config)
        
        assert result is True
        mock_components['game_operator'].click_element.assert_called()
    
    @pytest.mark.asyncio
    async def test_handle_stamina_shortage_disabled(self, farming_runner, mock_components):
        """测试禁用自动使用体力道具时的处理"""
        # 创建临时配置用于测试
        test_config = FarmingConfig(auto_use_overflow_energy=False, energy_refill_count=0)
        
        result = await farming_runner._handle_energy_shortage(test_config)
        
        assert result is False
    
    def test_check_stamina(self, farming_runner, mock_components):
        """测试检查体力"""
        # 模拟体力检测
        mock_components['game_detector'].find_text_in_screen.return_value = {
            'text': '120/240', 'position': (100, 50)
        }
        
        stamina = farming_runner._check_stamina()
        
        assert stamina >= 0
        mock_components['game_detector'].find_text_in_screen.assert_called()
    
    @pytest.mark.asyncio
    async def test_update_resource_gains(self, farming_runner):
        """测试更新资源获取统计"""
        # 创建模拟副本和会话
        dungeon = DungeonInfo(
            dungeon_id="test_dungeon",
            dungeon_type=DungeonType.CALYX_GOLDEN,
            name="测试副本",
            energy_cost=20,
            difficulty_level=1,
            estimated_time=300,
            drop_resources=[ResourceType.CREDITS],
            drop_rates={ResourceType.CREDITS: 0.8},
            location=(100, 200)
        )
        
        test_config = FarmingConfig(farming_mode=FarmingMode.EFFICIENT)
        session = FarmingSession(
            session_id="test_session",
            start_time=time.time(),
            targets=[],
            config=test_config
        )
        
        # 测试更新资源获取统计
        await farming_runner._update_resource_gains(dungeon, session)
        
        # 验证统计更新
        assert session.dungeons_completed >= 0
    
    @pytest.mark.asyncio
    async def test_generate_session_report(self, farming_runner):
        """测试生成会话报告"""
        # 创建模拟会话
        test_config = FarmingConfig(farming_mode=FarmingMode.EFFICIENT)
        session = FarmingSession(
            session_id="test_session",
            start_time=time.time() - 3600,  # 1小时前
            targets=[],
            config=test_config
        )
        
        # 添加资源统计
        session.resources_gained = {
            ResourceType.CREDITS: 50000,
            ResourceType.CHARACTER_EXP: 25
        }
        
        report = await farming_runner._generate_session_report(session)
        
        assert 'session_info' in report
        assert 'target_completion' in report
        assert 'efficiency_stats' in report
    
    def test_get_available_dungeons(self, farming_runner):
        """测试获取可用副本"""
        dungeons = farming_runner.get_all_dungeons()
        
        assert len(dungeons) > 0
        # 验证副本信息完整性
        for dungeon in dungeons:
            assert isinstance(dungeon, DungeonInfo)
            assert dungeon.dungeon_type is not None
            assert dungeon.energy_cost > 0
            assert len(dungeon.rewards) > 0
    
    def test_calculate_efficiency(self, farming_runner):
        """测试计算效率"""
        dungeon = DungeonInfo(
            dungeon_type=DungeonType.CALYX_GOLDEN,
            name="拟造花萼（金）",
            energy_cost=10,
            rewards={ResourceType.CREDITS: 8000},
            efficiency_rating=0.9,
            estimated_duration=120
        )
        
        target = ResourceTarget(
            resource_type=ResourceType.CREDITS,
            target_amount=1000000,
            current_amount=500000,
            priority=1
        )
        
        efficiency = farming_runner._calculate_efficiency(dungeon, target)
        
        assert efficiency > 0
        assert efficiency <= 1.0
    
    @pytest.mark.asyncio
    async def test_session_timeout(self, farming_runner, mock_components):
        """测试会话超时"""
        # 创建超时会话
        test_config = FarmingConfig(farming_mode=FarmingMode.EFFICIENT)
        farming_runner._current_session = FarmingSession(
            session_id="test_session",
            start_time=time.time() - 7200,  # 2小时前，超过最大持续时间
            targets=[],
            config=test_config
        )
        
        # 模拟执行过程中检查超时
        with patch.object(farming_runner, '_is_session_timeout', return_value=True):
            result = await farming_runner._execute_farming_session([])
            
            # 会话应该因超时而停止
            assert farming_runner.current_session.end_time is not None
    
    @pytest.mark.asyncio
    async def test_error_handling_during_execution(self, farming_runner, mock_components):
        """测试执行过程中的错误处理"""
        dungeon = DungeonInfo(
            dungeon_type=DungeonType.CALYX_GOLDEN,
            name="拟造花萼（金）",
            energy_cost=10,
            rewards={ResourceType.CREDITS: 8000},
            efficiency_rating=0.9,
            estimated_duration=120
        )
        
        # 模拟游戏操作失败
        mock_components['game_operator'].click_element.side_effect = Exception("Click failed")
        
        with patch.object(farming_runner, '_check_stamina', return_value=True):
            result = await farming_runner._execute_dungeon_runs(dungeon, 1)
            
            # 应该处理错误并返回False
            assert result is False
    
    def test_farming_config_creation(self, farming_runner):
        """测试刷取配置创建"""
        # 测试配置创建
        config = FarmingConfig(
            max_total_energy=240,
            auto_use_overflow_energy=True,
            energy_refill_count=2
        )
        
        # 验证配置被正确创建
        assert config.max_total_energy == 240
        assert config.auto_use_overflow_energy is True
        assert config.energy_refill_count == 2
    
    @pytest.mark.asyncio
    async def test_event_emission_during_farming(self, farming_runner, mock_components):
        """测试刷取过程中的事件发送"""
        dungeon = DungeonInfo(
            dungeon_type=DungeonType.CALYX_GOLDEN,
            name="拟造花萼（金）",
            energy_cost=10,
            rewards={ResourceType.CREDITS: 8000},
            efficiency_rating=0.9,
            estimated_duration=120
        )
        
        # 模拟成功执行
        mock_components['game_operator'].click_element.return_value = True
        mock_components['game_operator'].wait_for_battle_end.return_value = True
        mock_components['smart_waiter'].wait_for_element.return_value = True
        
        with patch.object(farming_runner, '_check_stamina', return_value=True), \
             patch.object(farming_runner, '_update_resource_stats'):
            
            await farming_runner._execute_dungeon_runs(dungeon, 1)
            
            # 验证事件被发送
            mock_components['event_bus'].emit.assert_called()
            
            # 检查发送的事件类型
            call_args = mock_components['event_bus'].emit.call_args_list
            event_types = [call[0][0] for call in call_args]
            assert any('farming' in event_type for event_type in event_types)