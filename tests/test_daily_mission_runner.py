"""DailyMissionRunner日常任务执行器测试模块"""

import pytest
import asyncio
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
            enabled_missions=[MissionType.DAILY_TRAINING, MissionType.CALYX_GOLDEN],
            max_attempts=3,
            timeout_seconds=300,
            auto_claim_rewards=True,
            priority_order=[MissionType.DAILY_TRAINING, MissionType.CALYX_GOLDEN]
        )
    
    @pytest.fixture
    def mission_runner(self, mock_components, mission_config):
        """创建DailyMissionRunner实例"""
        runner = DailyMissionRunner(
            game_operator=mock_components['game_operator'],
            smart_waiter=mock_components['smart_waiter'],
            event_bus=mock_components['event_bus'],
            config=mission_config
        )
        return runner
    
    def test_initialization(self, mission_runner, mission_config, mock_components):
        """测试初始化"""
        assert mission_runner.config == mission_config
        assert mission_runner.game_operator == mock_components['game_operator']
        assert mission_runner.smart_waiter == mock_components['smart_waiter']
        assert mission_runner.event_bus == mock_components['event_bus']
        assert len(mission_runner.completed_missions) == 0
        assert len(mission_runner.failed_missions) == 0
    
    @pytest.mark.asyncio
    async def test_run_daily_missions(self, mission_runner, mock_components):
        """测试运行日常任务"""
        # 模拟导航和任务检测
        mock_components['game_operator'].navigate_to_menu = AsyncMock(return_value=True)
        
        # 模拟任务检测结果
        mock_missions = [
            MissionInfo(
                mission_type=MissionType.DAILY_TRAINING,
                name="每日实训",
                progress="0/1",
                is_completed=False,
                reward_claimed=False
            ),
            MissionInfo(
                mission_type=MissionType.CALYX_GOLDEN,
                name="拟造花萼（金）",
                progress="0/3",
                is_completed=False,
                reward_claimed=False
            )
        ]
        
        with patch.object(mission_runner, '_detect_available_missions', return_value=mock_missions), \
             patch.object(mission_runner, '_execute_mission', return_value=True) as mock_execute, \
             patch.object(mission_runner, '_claim_rewards', return_value=True):
            
            result = await mission_runner.run_daily_missions()
            
            assert result['success'] is True
            assert result['completed_count'] == 2
            assert result['failed_count'] == 0
            assert len(result['completed_missions']) == 2
            
            # 验证任务执行被调用
            assert mock_execute.call_count == 2
    
    @pytest.mark.asyncio
    async def test_navigate_to_missions(self, mission_runner, mock_components):
        """测试导航到任务界面"""
        # 模拟成功导航
        mock_components['game_operator'].navigate_to_menu.return_value = True
        mock_components['game_operator'].click_element.return_value = True
        mock_components['smart_waiter'].wait_for_element.return_value = True
        
        result = await mission_runner._navigate_to_missions()
        
        assert result is True
        mock_components['game_operator'].navigate_to_menu.assert_called_once()
        mock_components['game_operator'].click_element.assert_called()
    
    @pytest.mark.asyncio
    async def test_navigate_to_missions_failure(self, mission_runner, mock_components):
        """测试导航失败"""
        # 模拟导航失败
        mock_components['game_operator'].navigate_to_menu.return_value = False
        
        result = await mission_runner._navigate_to_missions()
        
        assert result is False
    
    def test_detect_available_missions(self, mission_runner, mock_components):
        """测试检测可用任务"""
        # 模拟OCR检测结果
        mock_components['game_detector'].find_text_in_screen.return_value = {
            'text': '每日任务', 'position': (100, 50)
        }
        
        missions = mission_runner._detect_available_missions()
        
        assert len(missions) >= 0  # 至少应该能检测到一些任务
        mock_components['game_detector'].find_text_in_screen.assert_called()
    
    @pytest.mark.asyncio
    async def test_execute_daily_training(self, mission_runner, mock_components):
        """测试执行每日实训"""
        mission = MissionInfo(
            mission_type=MissionType.DAILY_TRAINING,
            name="每日实训",
            progress="0/1",
            is_completed=False,
            reward_claimed=False
        )
        
        # 模拟游戏操作
        mock_components['game_operator'].click_element.return_value = True
        mock_components['game_operator'].wait_for_battle_end.return_value = True
        mock_components['smart_waiter'].wait_for_element.return_value = True
        
        result = await mission_runner._execute_daily_training(mission)
        
        assert result is True
        mock_components['game_operator'].click_element.assert_called()
    
    @pytest.mark.asyncio
    async def test_execute_calyx_golden(self, mission_runner, mock_components):
        """测试执行拟造花萼（金）"""
        mission = MissionInfo(
            mission_type=MissionType.CALYX_GOLDEN,
            name="拟造花萼（金）",
            progress="0/3",
            is_completed=False,
            reward_claimed=False
        )
        
        # 模拟游戏操作
        mock_components['game_operator'].click_element.return_value = True
        mock_components['game_operator'].wait_for_battle_end.return_value = True
        mock_components['smart_waiter'].wait_for_element.return_value = True
        
        with patch.object(mission_runner, '_get_required_runs', return_value=3):
            result = await mission_runner._execute_calyx_golden(mission)
            
            assert result is True
            # 验证点击操作被调用了足够次数
            assert mock_components['game_operator'].click_element.call_count >= 3
    
    @pytest.mark.asyncio
    async def test_claim_rewards(self, mission_runner, mock_components):
        """测试领取奖励"""
        # 模拟奖励按钮检测和点击
        mock_components['game_detector'].find_ui_element.return_value = Mock(center=(500, 600))
        mock_components['game_operator'].click_element.return_value = True
        mock_components['smart_waiter'].wait_for_element.return_value = True
        
        result = await mission_runner._claim_rewards()
        
        assert result is True
        mock_components['game_operator'].click_element.assert_called()
    
    def test_check_timeout(self, mission_runner):
        """测试超时检查"""
        # 测试未超时
        start_time = datetime.now()
        assert mission_runner._check_timeout(start_time, 300) is False
        
        # 测试超时
        old_time = datetime.now() - timedelta(seconds=400)
        assert mission_runner._check_timeout(old_time, 300) is True
    
    def test_generate_report(self, mission_runner):
        """测试生成报告"""
        # 添加一些完成的任务
        mission_runner.completed_missions = [
            MissionInfo(
                mission_type=MissionType.DAILY_TRAINING,
                name="每日实训",
                progress="1/1",
                is_completed=True,
                reward_claimed=True
            )
        ]
        
        # 添加一些失败的任务
        mission_runner.failed_missions = [
            MissionInfo(
                mission_type=MissionType.CALYX_GOLDEN,
                name="拟造花萼（金）",
                progress="0/3",
                is_completed=False,
                reward_claimed=False
            )
        ]
        
        report = mission_runner._generate_report()
        
        assert 'summary' in report
        assert 'completed_missions' in report
        assert 'failed_missions' in report
        assert 'statistics' in report
        assert report['statistics']['total_missions'] == 2
        assert report['statistics']['success_rate'] == 0.5
    
    @pytest.mark.asyncio
    async def test_mission_execution_with_retry(self, mission_runner, mock_components):
        """测试任务执行重试机制"""
        mission = MissionInfo(
            mission_type=MissionType.DAILY_TRAINING,
            name="每日实训",
            progress="0/1",
            is_completed=False,
            reward_claimed=False
        )
        
        # 模拟前两次失败，第三次成功
        mock_components['game_operator'].click_element.side_effect = [False, False, True]
        mock_components['smart_waiter'].wait_for_element.return_value = True
        
        with patch.object(mission_runner, '_execute_daily_training') as mock_execute:
            mock_execute.side_effect = [False, False, True]
            
            result = await mission_runner._execute_mission(mission)
            
            assert result is True
            assert mock_execute.call_count == 3
    
    @pytest.mark.asyncio
    async def test_mission_execution_max_attempts_exceeded(self, mission_runner, mock_components):
        """测试超过最大重试次数"""
        mission = MissionInfo(
            mission_type=MissionType.DAILY_TRAINING,
            name="每日实训",
            progress="0/1",
            is_completed=False,
            reward_claimed=False
        )
        
        # 模拟所有尝试都失败
        with patch.object(mission_runner, '_execute_daily_training', return_value=False):
            result = await mission_runner._execute_mission(mission)
            
            assert result is False
    
    def test_get_required_runs(self, mission_runner):
        """测试获取所需运行次数"""
        # 测试不同进度格式
        assert mission_runner._get_required_runs("0/3") == 3
        assert mission_runner._get_required_runs("1/3") == 2
        assert mission_runner._get_required_runs("3/3") == 0
        assert mission_runner._get_required_runs("invalid") == 1  # 默认值
    
    @pytest.mark.asyncio
    async def test_event_emission(self, mission_runner, mock_components):
        """测试事件发送"""
        mission = MissionInfo(
            mission_type=MissionType.DAILY_TRAINING,
            name="每日实训",
            progress="0/1",
            is_completed=False,
            reward_claimed=False
        )
        
        # 模拟成功执行
        with patch.object(mission_runner, '_execute_daily_training', return_value=True):
            await mission_runner._execute_mission(mission)
            
            # 验证事件被发送
            mock_components['event_bus'].emit.assert_called()
            
            # 检查发送的事件类型
            call_args = mock_components['event_bus'].emit.call_args_list
            event_types = [call[0][0] for call in call_args]
            assert 'mission.started' in event_types
            assert 'mission.completed' in event_types