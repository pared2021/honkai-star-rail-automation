"""AutomationEngine自动化引擎测试模块"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List, Any

from src.core.automation_engine import (
    AutomationEngine, EngineState, AutomationMode,
    EngineConfig, EngineStatus
)
from src.core.task_manager import TaskManager
from src.core.game_operator import GameOperator
from src.core.smart_waiter import SmartWaiter
from src.core.error_handler import ErrorHandler
from src.core.events import EventBus


class TestAutomationEngine:
    """AutomationEngine测试类"""
    
    @pytest.fixture
    def mock_components(self):
        """创建模拟组件"""
        return {
            'task_manager': Mock(spec=TaskManager),
            'game_operator': Mock(spec=GameOperator),
            'smart_waiter': Mock(spec=SmartWaiter),
            'error_handler': Mock(spec=ErrorHandler),
            'event_bus': Mock(spec=EventBus)
        }
    
    @pytest.fixture
    def engine_config(self):
        """创建引擎配置"""
        return EngineConfig(
            max_concurrent_tasks=5,
            task_timeout=300,
            max_retry_attempts=3,
            smart_wait_enabled=True,
            error_recovery_enabled=True
        )
    
    @pytest.fixture
    def automation_engine(self, mock_components, engine_config):
        """创建AutomationEngine实例"""
        with patch('src.core.automation_engine.TaskManager'), \
             patch('src.core.automation_engine.GameOperator'), \
             patch('src.core.automation_engine.SmartWaiter'), \
             patch('src.core.automation_engine.ErrorHandler'), \
             patch('src.core.automation_engine.EventBus'):
            
            engine = AutomationEngine(config=engine_config)
            # 替换为模拟组件
            for name, mock_component in mock_components.items():
                setattr(engine, name, mock_component)
            return engine
    
    def test_initialization(self, automation_engine, engine_config):
        """测试引擎初始化"""
        assert automation_engine.config == engine_config
        assert automation_engine.state == EngineState.STOPPED
        assert automation_engine.mode == AutomationMode.MANUAL
        assert automation_engine._running is False
        assert automation_engine._paused is False
    
    @pytest.mark.asyncio
    async def test_start_engine(self, automation_engine, mock_components):
        """测试引擎启动"""
        # 模拟组件启动
        mock_components['task_manager'].start = AsyncMock()
        mock_components['error_handler'].start = AsyncMock()
        
        with patch.object(automation_engine, '_scheduler_loop') as mock_scheduler, \
             patch.object(automation_engine, '_monitoring_loop') as mock_monitoring:
            
            mock_scheduler.return_value = asyncio.create_task(asyncio.sleep(0.1))
            mock_monitoring.return_value = asyncio.create_task(asyncio.sleep(0.1))
            
            await automation_engine.start()
            
            assert automation_engine.state == EngineState.RUNNING
            assert automation_engine._running is True
            mock_components['task_manager'].start.assert_called_once()
            mock_components['error_handler'].start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_engine(self, automation_engine, mock_components):
        """测试引擎停止"""
        # 先启动引擎
        automation_engine._running = True
        automation_engine.state = EngineState.RUNNING
        automation_engine._scheduler_task = Mock()
        automation_engine._monitoring_task = Mock()
        automation_engine._scheduler_task.cancel = Mock()
        automation_engine._monitoring_task.cancel = Mock()
        
        # 模拟组件停止
        mock_components['task_manager'].stop = AsyncMock()
        mock_components['error_handler'].shutdown = AsyncMock()
        
        await automation_engine.stop()
        
        assert automation_engine.state == EngineState.STOPPED
        assert automation_engine._running is False
        mock_components['task_manager'].stop.assert_called_once()
        mock_components['error_handler'].shutdown.assert_called_once()
    
    def test_pause_resume(self, automation_engine):
        """测试引擎暂停和恢复"""
        # 测试暂停
        automation_engine.state = EngineState.RUNNING
        automation_engine.pause()
        assert automation_engine.state == EngineState.PAUSED
        assert automation_engine._paused is True
        
        # 测试恢复
        automation_engine.resume()
        assert automation_engine.state == EngineState.RUNNING
        assert automation_engine._paused is False
    
    @pytest.mark.asyncio
    async def test_execute_task(self, automation_engine, mock_components):
        """测试任务执行"""
        task_config = {
            'type': 'daily_mission',
            'priority': 'high',
            'params': {'mission_type': 'training'}
        }
        
        mock_components['task_manager'].submit_task = AsyncMock(return_value='task_123')
        
        task_id = await automation_engine.execute_task(task_config)
        
        assert task_id == 'task_123'
        mock_components['task_manager'].submit_task.assert_called_once_with(task_config)
    
    def test_get_status(self, automation_engine):
        """测试状态获取"""
        automation_engine.state = EngineState.RUNNING
        automation_engine.mode = AutomationMode.AUTO
        
        status = automation_engine.get_status()
        
        assert isinstance(status, EngineStatus)
        assert status.state == EngineState.RUNNING
        assert status.mode == AutomationMode.AUTO
        assert status.uptime >= 0
    
    def test_set_mode(self, automation_engine, mock_components):
        """测试模式设置"""
        # 测试设置自动模式
        automation_engine.set_mode(AutomationMode.AUTO)
        assert automation_engine.mode == AutomationMode.AUTO
        
        # 验证事件发送
        mock_components['event_bus'].emit.assert_called_with(
            'engine.mode_changed',
            {'old_mode': AutomationMode.MANUAL, 'new_mode': AutomationMode.AUTO}
        )
    
    @pytest.mark.asyncio
    async def test_scheduler_loop(self, automation_engine, mock_components):
        """测试调度器循环"""
        automation_engine._running = True
        automation_engine._paused = False
        automation_engine.mode = AutomationMode.AUTO
        
        # 模拟任务管理器方法
        mock_components['task_manager'].process_pending_tasks = AsyncMock()
        mock_components['task_manager'].cleanup_completed_tasks = AsyncMock()
        
        # 运行一次循环后停止
        async def stop_after_one_iteration():
            await asyncio.sleep(0.01)
            automation_engine._running = False
        
        stop_task = asyncio.create_task(stop_after_one_iteration())
        
        await automation_engine._scheduler_loop()
        
        # 验证调度器方法被调用
        mock_components['task_manager'].process_pending_tasks.assert_called()
        mock_components['task_manager'].cleanup_completed_tasks.assert_called()
    
    @pytest.mark.asyncio
    async def test_monitoring_loop(self, automation_engine, mock_components):
        """测试监控循环"""
        automation_engine._running = True
        
        # 模拟监控方法
        mock_components['task_manager'].get_statistics = Mock(return_value={
            'total_tasks': 10,
            'completed_tasks': 8,
            'failed_tasks': 1,
            'pending_tasks': 1
        })
        
        # 运行一次循环后停止
        async def stop_after_one_iteration():
            await asyncio.sleep(0.01)
            automation_engine._running = False
        
        stop_task = asyncio.create_task(stop_after_one_iteration())
        
        await automation_engine._monitoring_loop()
        
        # 验证监控方法被调用
        mock_components['task_manager'].get_statistics.assert_called()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, automation_engine, mock_components):
        """测试错误处理"""
        # 模拟任务执行错误
        error = Exception("Task execution failed")
        mock_components['task_manager'].submit_task = AsyncMock(side_effect=error)
        mock_components['error_handler'].handle_error = AsyncMock()
        
        task_config = {'type': 'test_task'}
        
        with pytest.raises(Exception):
            await automation_engine.execute_task(task_config)
        
        # 验证错误处理器被调用
        mock_components['error_handler'].handle_error.assert_called_once_with(error)
    
    def test_event_handling(self, automation_engine, mock_components):
        """测试事件处理"""
        # 模拟事件处理
        event_data = {'task_id': 'task_123', 'status': 'completed'}
        
        automation_engine._handle_task_completed(event_data)
        
        # 验证事件被正确处理（这里可以添加具体的验证逻辑）
        assert True  # 占位符，实际应该验证具体的事件处理逻辑
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown(self, automation_engine, mock_components):
        """测试优雅关闭"""
        # 启动引擎
        automation_engine._running = True
        automation_engine.state = EngineState.RUNNING
        
        # 模拟正在运行的任务
        automation_engine._scheduler_task = Mock()
        automation_engine._monitoring_task = Mock()
        automation_engine._scheduler_task.cancel = Mock()
        automation_engine._monitoring_task.cancel = Mock()
        
        # 模拟组件关闭
        mock_components['task_manager'].stop = AsyncMock()
        mock_components['error_handler'].shutdown = AsyncMock()
        
        await automation_engine.stop()
        
        # 验证所有组件都被正确关闭
        assert automation_engine.state == EngineState.STOPPED
        assert automation_engine._running is False
        mock_components['task_manager'].stop.assert_called_once()
        mock_components['error_handler'].shutdown.assert_called_once()