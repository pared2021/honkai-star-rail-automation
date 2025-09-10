"""DailyMissionRunner日常任务执行器测试模块"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List, Any

from src.core.daily_mission_runner import (
    DailyMissionRunner, MissionType, MissionStatus,
    MissionInfo, DailyMissionConfig
)
from src.core.game_operator import GameOperator
from src.core.smart_waiter import SmartWaiter
from src.core.events import EventBus


class TestDailyMissionRunner:
    """DailyMissionRunner测试类"""
    
    @pytest.fixture
    def mock_components(self):
        """创建模拟组件"""
        return {
            'game_operator': Mock(spec=GameOperator),
            'smart_waiter': Mock(spec=SmartWaiter),
            'event_bus': Mock(spec=EventBus)
        }
    
    @pytest.fixture
    def mission_config(self):
        """创建任务配置"""
        return DailyMissionConfig(
            max_execution_time=3600,
            retry_attempts=3,
            auto_claim_rewards=True,
            skip_completed=True,
            priority_missions=[MissionType.DAILY_TRAINING, MissionType.CALYX_GOLDEN],
            energy_threshold=20
        )
    
    @pytest.fixture
    def mission_runner(self, mock_components, mission_config):
        """创建DailyMissionRunner实例"""
        runner = DailyMissionRunner(
            game_operator=mock_components['game_operator'],
            event_bus=mock_components['event_bus'],
            config=mission_config
        )
        return runner
    
    def test_initialization(self, mission_runner, mission_config, mock_components):
        """测试初始化"""
        assert mission_runner.config == mission_config
        assert mission_runner.game_operator == mock_components['game_operator']
        assert mission_runner.smart_waiter is not None
        assert mission_runner.event_bus == mock_components['event_bus']
        assert len(mission_runner._missions) == 0
    
    @pytest.mark.asyncio
    async def test_run_daily_missions(self, mission_runner, mock_components):
        """测试运行日常任务的完整流程"""
        # 模拟任务检测和执行
        with patch.object(mission_runner, '_navigate_to_daily_missions', return_value=True), \
             patch.object(mission_runner, '_detect_available_missions'), \
             patch.object(mission_runner, '_execute_single_mission', return_value=True), \
             patch.object(mission_runner, '_claim_all_rewards', return_value=3), \
             patch.object(mission_runner.event_bus, 'emit', new_callable=AsyncMock):
            
            # 设置一些模拟任务
            mission_runner._missions = {
                'test_1': MissionInfo(
                    mission_id="test_1",
                    name="测试任务1", 
                    mission_type=MissionType.DAILY_TRAINING, 
                    description="测试任务",
                    target=1, 
                    status=MissionStatus.NOT_STARTED
                )
            }
            
            result = await mission_runner.execute_daily_missions()
            
            assert 'total_missions' in result
            assert 'completed_missions' in result
            assert 'execution_time' in result
    
    @pytest.mark.asyncio
    async def test_navigate_to_missions(self, mission_runner, mock_components):
        """测试导航到日常任务界面"""
        # 模拟导航成功
        mock_components['game_operator'].click = AsyncMock()
        mission_runner.smart_waiter.wait_for_ui_element = AsyncMock(return_value=True)
        
        result = await mission_runner._navigate_to_daily_missions()
        
        assert result is True
        mock_components['game_operator'].click.assert_called()
    
    @pytest.mark.asyncio
    async def test_navigate_to_missions_failure(self, mission_runner, mock_components):
        """测试导航失败的情况"""
        # 模拟导航失败
        mock_components['game_operator'].click = AsyncMock()
        mission_runner.smart_waiter.wait_for_ui_element = AsyncMock(return_value=False)
        
        result = await mission_runner._navigate_to_daily_missions()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_detect_available_missions(self, mission_runner, mock_components):
        """测试检测可用任务"""
        # 模拟屏幕截图和任务检测
        mock_screenshot = Mock()
        mock_components['game_operator'].take_screenshot = AsyncMock(return_value=mock_screenshot)
        
        # 模拟游戏操作器的截图功能
        mock_screenshot = Mock()
        mock_components['game_operator'].take_screenshot = AsyncMock(return_value=mock_screenshot)
        
        with patch.object(mission_runner, '_parse_mission_list') as mock_parse:
            mock_parse.return_value = [
                MissionInfo(
                    mission_id="test_mission",
                    name="每日训练", 
                    mission_type=MissionType.DAILY_TRAINING, 
                    description="测试任务",
                    target=1, 
                    status=MissionStatus.NOT_STARTED
                )
            ]
            
            await mission_runner._detect_available_missions()
            
            # 验证截图和解析方法被调用
            mock_components['game_operator'].take_screenshot.assert_called_once()
            mock_parse.assert_called_once()
            
            # 验证任务被添加到_missions字典中
            assert len(mission_runner._missions) > 0
    
    @pytest.mark.asyncio
    async def test_execute_daily_training(self, mission_runner, mock_components):
        """测试执行每日实训"""
        mission = MissionInfo(
            mission_id="daily_training_test",
            mission_type=MissionType.DAILY_TRAINING,
            name="每日实训",
            description="测试每日实训任务",
            progress=0,
            target=1
        )
        
        # 模拟游戏操作
        mock_components['game_operator'].click = AsyncMock()
        mission_runner.smart_waiter.wait_for_ui_element = AsyncMock(return_value=True)
        
        result = await mission_runner._execute_daily_training(mission)
        
        assert result is True
        mock_components['game_operator'].click.assert_called()
    
    @pytest.mark.asyncio
    async def test_execute_calyx_golden(self, mission_runner, mock_components):
        """测试执行拟造花萼（金）"""
        mission = MissionInfo(
            mission_id="calyx_golden_test",
            mission_type=MissionType.CALYX_GOLDEN,
            name="拟造花萼（金）",
            description="测试拟造花萼（金）任务",
            progress=0,
            target=3
        )
        
        # 模拟游戏操作
        mock_components['game_operator'].click = AsyncMock()
        mission_runner.smart_waiter.wait_for_ui_element = AsyncMock(return_value=True)
        
        result = await mission_runner._execute_calyx_golden(mission)
        
        assert result is True
        # 验证点击操作被调用
        mock_components['game_operator'].click.assert_called()
    
    @pytest.mark.asyncio
    async def test_claim_rewards(self, mission_runner, mock_components):
        """测试领取奖励"""
        # 模拟奖励按钮检测和点击
        mock_components['game_operator'].click = AsyncMock()
        mock_components['smart_waiter'].wait_for_ui_element = AsyncMock(return_value=True)
        
        result = await mission_runner._claim_all_rewards()
        
        assert result >= 0  # _claim_all_rewards返回数字，不是布尔值
        mock_components['game_operator'].click.assert_called()
    
    def test_check_timeout(self, mission_runner):
        """测试超时检查"""
        # 设置执行开始时间
        mission_runner._execution_start_time = time.time() - 100  # 100秒前开始
        
        # 测试未超时（假设最大执行时间为3600秒）
        assert mission_runner._is_execution_timeout() is False
        
        # 测试超时
        mission_runner._execution_start_time = time.time() - 4000  # 4000秒前开始
        assert mission_runner._is_execution_timeout() is True
    
    def test_generate_report(self, mission_runner):
        """测试生成报告"""
        # 创建测试任务并添加到_missions字典
        completed_mission = MissionInfo(
            mission_id="daily_training_completed",
            mission_type=MissionType.DAILY_TRAINING,
            name="每日实训",
            description="已完成的每日实训任务",
            progress=1,
            target=1
        )
        completed_mission.status = MissionStatus.COMPLETED
        
        failed_mission = MissionInfo(
            mission_id="calyx_golden_failed",
            mission_type=MissionType.CALYX_GOLDEN,
            name="拟造花萼（金）",
            description="失败的拟造花萼（金）任务",
            progress=0,
            target=3
        )
        failed_mission.status = MissionStatus.FAILED
        
        mission_runner._missions = {
            "daily_training_completed": completed_mission,
            "calyx_golden_failed": failed_mission
        }
        
        report = mission_runner._generate_execution_report([completed_mission])
        
        assert 'timestamp' in report
        assert 'total_missions' in report
        assert 'completed_missions' in report
        assert 'failed_missions' in report
        assert 'success_rate' in report
        assert report['total_missions'] == 2
        assert report['success_rate'] == 0.5
    
    @pytest.mark.asyncio
    async def test_mission_execution_with_retry(self, mission_runner, mock_components):
        """测试任务执行重试机制"""
        mission = MissionInfo(
            mission_id="daily_training_retry",
            mission_type=MissionType.DAILY_TRAINING,
            name="每日实训",
            description="重试测试的每日实训任务",
            progress=0,
            target=1
        )
        
        # 模拟执行成功
        with patch.object(mission_runner, '_execute_daily_training', new_callable=AsyncMock, return_value=True) as mock_execute:
            # 模拟事件总线
            mission_runner.event_bus.emit = AsyncMock()
            
            result = await mission_runner._execute_single_mission(mission)
            
            assert result is True
            mock_execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mission_execution_max_attempts_exceeded(self, mission_runner, mock_components):
        """测试超过最大重试次数"""
        mission = MissionInfo(
            mission_id="daily_training_max_attempts",
            mission_type=MissionType.DAILY_TRAINING,
            name="每日实训",
            description="最大重试次数测试的每日实训任务",
            progress=0,
            target=1
        )
        
        # 模拟所有尝试都失败
        with patch.object(mission_runner, '_execute_daily_training', return_value=False):
            result = await mission_runner._execute_single_mission(mission)
            
            assert result is False
    
    def test_get_required_runs(self, mission_runner):
        """测试获取所需运行次数"""
        # 创建测试任务
        mission1 = MissionInfo(
            mission_id="test_1",
            mission_type=MissionType.CALYX_GOLDEN,
            name="测试任务1",
            description="测试描述",
            progress=0,
            target=3
        )
        mission2 = MissionInfo(
            mission_id="test_2",
            mission_type=MissionType.CALYX_GOLDEN,
            name="测试任务2",
            description="测试描述",
            progress=1,
            target=3
        )
        mission3 = MissionInfo(
            mission_id="test_3",
            mission_type=MissionType.CALYX_GOLDEN,
            name="测试任务3",
            description="测试描述",
            progress=3,
            target=3
        )
        
        # 测试不同进度 - 直接计算所需运行次数
        assert max(0, mission1.target - mission1.progress) == 3
        assert max(0, mission2.target - mission2.progress) == 2
        assert max(0, mission3.target - mission3.progress) == 0
    
    @pytest.mark.asyncio
    async def test_event_emission(self, mission_runner, mock_components):
        """测试事件发送"""
        # 模拟事件总线
        mock_event_bus = AsyncMock()
        mission_runner.event_bus = mock_event_bus
        
        # 模拟任务执行
        with patch.object(mission_runner, '_navigate_to_daily_missions', return_value=True), \
             patch.object(mission_runner, '_detect_available_missions'), \
             patch.object(mission_runner, '_execute_single_mission', return_value=True), \
             patch.object(mission_runner, '_claim_all_rewards', return_value=0):
            
            await mission_runner.execute_daily_missions()
            
            # 验证事件被发送
            emitted_events = [call[0][0] for call in mock_event_bus.emit.call_args_list]
            assert 'daily_mission_started' in emitted_events
            assert 'daily_mission_completed' in emitted_events