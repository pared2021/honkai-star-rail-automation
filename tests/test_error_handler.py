"""ErrorHandler错误处理器测试模块"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List, Any

from src.core.error_handler import (
    ErrorHandler, ErrorSeverity, ErrorCategory, RecoveryAction,
    ErrorInfo, RetryConfig, ErrorClassifier,
    RetryStrategy, FallbackStrategy, RestartStrategy,
    GameStateRecoveryStrategy, UIElementRecoveryStrategy
)
from src.core.game_operator import GameOperator
from src.core.events import EventBus


class TestErrorClassifier:
    """ErrorClassifier测试类"""
    
    @pytest.fixture
    def classifier(self):
        """创建ErrorClassifier实例"""
        return ErrorClassifier()
    
    def test_classify_by_type(self, classifier):
        """测试按类型分类错误"""
        # 网络错误
        network_error = ConnectionError("Connection failed")
        category = classifier._classify_by_type(network_error)
        assert category == ErrorCategory.NETWORK
        
        # 超时错误
        timeout_error = TimeoutError("Operation timed out")
        category = classifier._classify_by_type(timeout_error)
        assert category == ErrorCategory.NETWORK  # TimeoutError被归类为NETWORK
        
        # 文件错误
        file_error = FileNotFoundError("File not found")
        category = classifier._classify_by_type(file_error)
        assert category == ErrorCategory.RESOURCE
        
        # 验证错误
        validation_error = ValueError("Invalid value")
        category = classifier._classify_by_type(validation_error)
        assert category == ErrorCategory.VALIDATION
        
        # 未知错误
        unknown_error = Exception("Unknown error")
        category = classifier._classify_by_type(unknown_error)
        assert category == ErrorCategory.UNKNOWN
    
    def test_classify_by_message(self, classifier):
        """测试按消息分类错误"""
        # 测试超时错误消息
        category = classifier._classify_by_message("deadline exceeded")
        assert category == ErrorCategory.TIMEOUT
        
        # 测试UI元素错误消息
        category = classifier._classify_by_message("element not found")
        assert category == ErrorCategory.UI_ELEMENT
        
        # 测试游戏状态错误
        category = classifier._classify_by_message("invalid state")
        assert category == ErrorCategory.GAME_STATE
        
        # 测试系统错误
        category = classifier._classify_by_message("system crash")
        assert category == ErrorCategory.UNKNOWN  # 没有匹配的模式，应该返回UNKNOWN
    
    def test_determine_severity(self, classifier):
        """测试确定错误严重程度"""
        # 测试验证错误（低严重程度）
        validation_error = Exception("Validation failed")
        severity = classifier._determine_severity(validation_error, ErrorCategory.VALIDATION)
        assert severity == ErrorSeverity.LOW
        
        # 测试系统错误（严重程度）
        system_error = Exception("System crash")
        severity = classifier._determine_severity(system_error, ErrorCategory.SYSTEM)
        assert severity == ErrorSeverity.CRITICAL
        
        # 测试UI元素错误（中等严重程度）
        ui_error = Exception("Element not found")
        severity = classifier._determine_severity(ui_error, ErrorCategory.UI_ELEMENT)
        assert severity == ErrorSeverity.MEDIUM
        
        # 测试网络错误（中等严重程度）
        network_error = Exception("Network timeout")
        severity = classifier._determine_severity(network_error, ErrorCategory.NETWORK)
        assert severity == ErrorSeverity.MEDIUM


class TestRecoveryStrategies:
    """恢复策略测试类"""
    
    @pytest.fixture
    def mock_components(self):
        """创建模拟组件"""
        return {
            'game_operator': Mock(spec=GameOperator),
            'event_bus': Mock(spec=EventBus)
        }
    
    @pytest.mark.asyncio
    async def test_retry_strategy(self, mock_components):
        """测试重试策略"""
        retry_config = RetryConfig(max_attempts=3, base_delay=1.0)
        strategy = RetryStrategy(retry_config)
        
        error_info = ErrorInfo(
            error_id="test_error_1",
            error_message="Test error",
            error_type="Exception",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
            task_id="test_task",
            task_type="test",
            context={'attempt': 1},
            stack_trace="",
            retry_count=0
        )
        
        # 测试可以处理
        can_handle = await strategy.can_handle(error_info)
        assert can_handle is True
        
        # 测试重试恢复
        success, description = await strategy.recover(error_info, {})
        assert success is True
        assert "重试" in description
    
    @pytest.mark.asyncio
    async def test_retry_strategy_max_attempts(self, mock_components):
        """测试重试策略达到最大尝试次数"""
        retry_config = RetryConfig(max_attempts=2, base_delay=0.1)
        strategy = RetryStrategy(retry_config)
        
        error_info = ErrorInfo(
            error_id="test_error_2",
            error_message="Test error",
            error_type="Exception",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
            task_id="test_task",
            task_type="test",
            context={'attempt': 3},
            stack_trace="",
            retry_count=3
        )
        
        # 测试不能重试
        can_handle = await strategy.can_handle(error_info)
        assert can_handle is False
    
    @pytest.mark.asyncio
    async def test_fallback_strategy(self, mock_components):
        """测试备用方案策略"""
        def mock_fallback(error_info, context):
            return True
        
        fallback_actions = {ErrorCategory.NETWORK: mock_fallback}
        strategy = FallbackStrategy(fallback_actions=fallback_actions)
        
        # 测试可以处理的错误类型
        error_info = ErrorInfo(
            error_id="test_error_3",
            error_message="Test error",
            error_type="Exception",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
            task_id="test_task",
            task_type="test",
            context={},
            stack_trace="",
            retry_count=0
        )
        
        # 应该能够处理网络错误
        can_handle = await strategy.can_handle(error_info)
        assert can_handle is True
        
        # 测试不能处理的错误类型
        error_info_system = ErrorInfo(
            error_id="test_error_3_system",
            error_message="Test error",
            error_type="Exception",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
            task_id="test_task",
            task_type="test",
            context={},
            stack_trace="",
            retry_count=0
        )
        
        # 不应该能够处理系统错误
        can_handle = await strategy.can_handle(error_info_system)
        assert can_handle is False
        
        # 测试备用方案恢复
        success, description = await strategy.recover(error_info, {})
        assert success is True
        assert "备用方案" in description
    
    @pytest.mark.asyncio
    async def test_restart_strategy(self, mock_components):
        """测试重启策略"""
        strategy = RestartStrategy(restart_threshold=2)
        
        # 测试高严重程度且重试次数超过阈值的情况
        error_info_high = ErrorInfo(
            error_id="test_error_4",
            error_message="Test error",
            error_type="Exception",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            timestamp=datetime.now(),
            task_id="test_task",
            task_type="test",
            context={},
            stack_trace="",
            retry_count=3
        )
        
        # 高严重程度且重试次数超过阈值，应该能够处理
        can_handle = await strategy.can_handle(error_info_high)
        assert can_handle is True
        
        # 测试低严重程度的情况
        error_info_low = ErrorInfo(
            error_id="test_error_4_low",
            error_message="Test error",
            error_type="Exception",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.LOW,
            timestamp=datetime.now(),
            task_id="test_task",
            task_type="test",
            context={},
            stack_trace="",
            retry_count=3
        )
        
        # 低严重程度，不应该能够处理
        can_handle = await strategy.can_handle(error_info_low)
        assert can_handle is False
        
        # 模拟重启操作
        mock_components['game_operator'].restart_game = AsyncMock(return_value=True)
        
        success, description = await strategy.recover(error_info_high, mock_components)
        assert success is True
        assert "重启" in description
    
    @pytest.mark.asyncio
    async def test_game_state_recovery_strategy(self, mock_components):
        """测试游戏状态恢复策略"""
        # 测试有游戏操作器的情况
        strategy = GameStateRecoveryStrategy(game_operator=mock_components['game_operator'])
        
        error_info_game = ErrorInfo(
            error_id="test_error_5",
            error_message="Game state error",
            error_type="Exception",
            category=ErrorCategory.GAME_STATE,
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
            task_id="test_task",
            task_type="test",
            context={},
            stack_trace="",
            retry_count=0
        )
        
        # 游戏状态错误且有游戏操作器，应该能够处理
        can_handle = await strategy.can_handle(error_info_game)
        assert can_handle is True
        
        # 测试没有游戏操作器的情况
        strategy_no_operator = GameStateRecoveryStrategy(game_operator=None)
        can_handle = await strategy_no_operator.can_handle(error_info_game)
        assert can_handle is False
        
        # 测试非游戏状态错误
        error_info_network = ErrorInfo(
            error_id="test_error_5_network",
            error_message="Network error",
            error_type="Exception",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
            task_id="test_task",
            task_type="test",
            context={},
            stack_trace="",
            retry_count=0
        )
        
        can_handle = await strategy.can_handle(error_info_network)
        assert can_handle is False
        
        # 模拟游戏操作器的所有必需方法（使用AsyncMock）
        mock_components['game_operator'].take_screenshot = AsyncMock(return_value="screenshot.png")
        mock_components['game_operator'].restart_game = AsyncMock(return_value=True)
        mock_components['game_operator'].save_game_state = AsyncMock(return_value=True)
        mock_components['game_operator'].load_game_state = AsyncMock(return_value=True)
        mock_components['game_operator'].click_element = AsyncMock(return_value=True)
        mock_components['game_operator'].get_current_scene = AsyncMock(return_value="main_menu")
        mock_components['game_operator'].navigate_to_scene = AsyncMock(return_value=True)
        mock_components['game_operator'].press_key = AsyncMock(return_value=True)
        mock_components['game_operator'].wait_for_ui_element = AsyncMock(return_value=True)
        
        success, description = await strategy.recover(error_info_game, mock_components)
        # 游戏状态恢复策略应该成功
        assert success is True
        assert "主界面" in description or "游戏" in description
    
    @pytest.mark.asyncio
    async def test_ui_element_recovery_strategy(self, mock_components):
        """测试UI元素恢复策略"""
        # 测试有游戏操作器的情况
        strategy = UIElementRecoveryStrategy(game_operator=mock_components['game_operator'])
        
        error_info_ui = ErrorInfo(
            error_id="test_error_6",
            error_message="Element not found",
            error_type="Exception",
            category=ErrorCategory.UI_ELEMENT,
            severity=ErrorSeverity.LOW,
            timestamp=datetime.now(),
            task_id="test_task",
            task_type="test",
            context={'element': 'test_button'},
            stack_trace="",
            retry_count=0
        )
        
        # UI元素错误且有游戏操作器，应该能够处理
        can_handle = await strategy.can_handle(error_info_ui)
        assert can_handle is True
        
        # 测试没有游戏操作器的情况
        strategy_no_operator = UIElementRecoveryStrategy(game_operator=None)
        can_handle = await strategy_no_operator.can_handle(error_info_ui)
        assert can_handle is False
        
        # 测试非UI元素错误
        error_info_system = ErrorInfo(
            error_id="test_error_6_system",
            error_message="System error",
            error_type="Exception",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
            task_id="test_task",
            task_type="test",
            context={},
            stack_trace="",
            retry_count=0
        )
        
        can_handle = await strategy.can_handle(error_info_system)
        assert can_handle is False
        
        # 模拟游戏检测器和游戏操作器的所有必需方法（使用AsyncMock）
        mock_components['game_detector'] = Mock()
        mock_components['game_detector'].capture_screen = AsyncMock(return_value=True)
        mock_components['game_detector'].find_ui_element = Mock(return_value=Mock(center=(100, 200)))
        mock_components['game_operator'].take_screenshot = AsyncMock(return_value="screenshot.png")
        mock_components['game_operator'].click_element = AsyncMock(return_value=True)
        mock_components['game_operator'].scroll_to_element = AsyncMock(return_value=True)
        mock_components['game_operator'].wait_for_element = AsyncMock(return_value=True)
        mock_components['game_operator'].press_key = AsyncMock(return_value=True)
        
        success, description = await strategy.recover(error_info_ui, mock_components)
        # UI元素恢复策略应该成功
        assert success is True
        assert "界面" in description or "刷新" in description


class TestErrorHandler:
    """ErrorHandler测试类"""
    
    @pytest.fixture
    def mock_components(self):
        """创建模拟组件"""
        return {
            'game_operator': Mock(spec=GameOperator),
            'event_bus': Mock(spec=EventBus)
        }
    
    @pytest.fixture
    def retry_config(self):
        """创建重试配置"""
        return RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            backoff_factor=2.0,
            jitter=True
        )
    
    @pytest.fixture
    def error_handler(self, mock_components, retry_config):
        """创建ErrorHandler实例"""
        handler = ErrorHandler(
            event_bus=mock_components['event_bus'],
            game_operator=mock_components['game_operator']
        )
        return handler
    
    def test_initialization(self, error_handler, mock_components, retry_config):
        """测试初始化"""
        assert error_handler.game_operator == mock_components['game_operator']
        assert error_handler.event_bus == mock_components['event_bus']
        assert len(error_handler.recovery_strategies) > 0
        assert len(error_handler.error_history) == 0
    
    def test_add_recovery_strategy(self, error_handler):
        """测试添加恢复策略"""
        # 添加自定义重试策略
        retry_config = RetryConfig(max_attempts=5, base_delay=2.0)
        custom_strategy = RetryStrategy(retry_config)
        error_handler.add_recovery_strategy(custom_strategy)
        
        # 验证策略已添加
        assert len(error_handler.recovery_strategies) == 5  # 4个默认 + 1个自定义
    
    @pytest.mark.asyncio
    async def test_handle_error(self, error_handler, mock_components):
        """测试错误处理"""
        test_error = Exception("Test error")
        context = {'operation': 'test_operation'}
        
        # 模拟事件总线
        mock_components['event_bus'].emit_async = AsyncMock()
        mock_components['event_bus'].emit = Mock()
        
        result = await error_handler.handle_error(
            test_error, 
            task_id="test_task",
            task_type="test",
            context=context
        )
        
        assert result is not None
        assert len(error_handler.error_history) == 1
        
        # 验证事件发送
        mock_components['event_bus'].emit_async.assert_called()
    
    @pytest.mark.asyncio
    async def test_handle_error_no_recovery(self, error_handler, mock_components):
        """测试无法恢复的错误处理"""
        test_error = Exception("Unrecoverable error")
        context = {'operation': 'test_operation'}
        
        # 清空恢复策略
        error_handler.recovery_strategies = {}
        
        result = await error_handler.handle_error(
            test_error,
            task_id="test_task", 
            task_type="test",
            context=context
        )
        
        assert result is not None
        assert len(error_handler.error_history) == 1
    
    def test_get_error_info(self, error_handler):
        """测试获取错误信息"""
        test_error = Exception("Test error")
        context = {'operation': 'test_operation'}
        
        # 添加错误到历史记录
        error_info = ErrorInfo(
            error_id="test_error_7",
            error_message="Test error",
            error_type="Exception",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
            task_id="test_task",
            task_type="test",
            context=context,
            stack_trace="",
            retry_count=0
        )
        error_handler.error_history["test_error_7"] = error_info
        
        # 获取错误信息
        retrieved_info = error_handler.get_error_info("test_error_7")
        assert retrieved_info == error_info
        
        # 测试无效ID
        invalid_info = error_handler.get_error_info("invalid_id")
        assert invalid_info is None
    
    def test_get_error_statistics(self, error_handler):
        """测试获取错误统计"""
        # 直接更新统计信息来模拟错误处理
        error_handler.error_stats['total_errors'] = 3
        error_handler.error_stats['resolved_errors'] = 1
        error_handler.error_stats['category_counts'][ErrorCategory.NETWORK.value] = 2
        error_handler.error_stats['category_counts'][ErrorCategory.UI_ELEMENT.value] = 1
        error_handler.error_stats['severity_counts'][ErrorSeverity.LOW.value] = 1
        error_handler.error_stats['severity_counts'][ErrorSeverity.MEDIUM.value] = 1
        error_handler.error_stats['severity_counts'][ErrorSeverity.HIGH.value] = 1
        
        stats = error_handler.get_error_statistics()
        
        assert stats['total_errors'] == 3
        assert stats['resolved_errors'] == 1
        assert stats['resolution_rate'] == 33.33333333333333
        assert stats['category_counts'][ErrorCategory.NETWORK.value] == 2
        assert stats['category_counts'][ErrorCategory.UI_ELEMENT.value] == 1
        assert stats['severity_counts'][ErrorSeverity.LOW.value] == 1
        assert stats['severity_counts'][ErrorSeverity.MEDIUM.value] == 1
        assert stats['severity_counts'][ErrorSeverity.HIGH.value] == 1
    
    def test_get_recent_errors(self, error_handler):
        """测试获取最近错误"""
        # 添加一些错误，时间间隔不同
        now = datetime.now()
        old_error = ErrorInfo(
            error_id="old_error",
            error_message="Old error",
            error_type="Exception",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.LOW,
            timestamp=now - timedelta(hours=2),
            task_id="old_task",
            task_type="test",
            context={},
            stack_trace="",
            retry_count=0
        )
        recent_error = ErrorInfo(
            error_id="recent_error",
            error_message="Recent error",
            error_type="Exception",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            timestamp=now - timedelta(minutes=30),
            task_id="recent_task",
            task_type="test",
            context={},
            stack_trace="",
            retry_count=0
        )
        
        error_handler.error_history["old_error"] = old_error
        error_handler.error_history["recent_error"] = recent_error
        
        # 获取最近1小时的错误
        recent_errors = error_handler.get_recent_errors(hours=1)
        
        assert len(recent_errors) == 1
        assert recent_errors[0] == recent_error
    
    def test_clear_old_errors(self, error_handler):
        """测试清理旧错误"""
        # 添加一些旧错误
        now = datetime.now()
        old_errors = [
            ErrorInfo(
                error_id=f"old_error_{i}",
                error_message=f"Old error {i}",
                error_type="Exception",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.LOW,
                timestamp=now - timedelta(days=i+3),  # 3天前、4天前、5天前
                task_id=f"old_task_{i}",
                task_type="test",
                context={},
                stack_trace="",
                retry_count=0
            ) for i in range(3)
        ]
        recent_error = ErrorInfo(
            error_id="recent_error",
            error_message="Recent error",
            error_type="Exception",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            timestamp=now,
            task_id="recent_task",
            task_type="test",
            context={},
            stack_trace="",
            retry_count=0
        )
        
        for error in old_errors:
            error_handler.error_history[error.error_id] = error
        error_handler.error_history[recent_error.error_id] = recent_error
        
        # 清理超过2天的错误
        error_handler.clear_old_errors(days=2)
        
        assert len(error_handler.error_history) == 1  # 只剩下最新错误
    
    def test_check_error_frequency(self, error_handler):
        """测试错误频率检查"""
        # 模拟多次相同错误
        error = Exception("Test error")
        category = ErrorCategory.SYSTEM
        severity = ErrorSeverity.LOW
        
        # 第一次错误
        result_severity = error_handler._check_error_frequency(error, category, severity)
        assert result_severity == ErrorSeverity.LOW
        
        # 多次错误后应该升级严重程度
        for _ in range(5):
            result_severity = error_handler._check_error_frequency(error, category, severity)
        
        assert result_severity != ErrorSeverity.LOW
    
    def test_get_error_frequency_stats(self, error_handler):
        """测试获取错误频率统计"""
        # 添加一些错误频率记录
        import time
        error_key = f"{ErrorCategory.UI_ELEMENT.value}_Exception"
        error_handler.error_frequency = {
            error_key: [time.time() - 30, time.time() - 10],
            f"{ErrorCategory.SYSTEM.value}_Exception": [time.time() - 100]  # 过期的记录
        }
        
        stats = error_handler.get_error_frequency_stats()
        
        # 应该只包含时间窗口内的错误
        assert error_key in stats
        assert stats[error_key] == 2
        

    
    def test_reset_error_frequency(self, error_handler):
        """测试重置错误频率"""
        # 添加错误频率记录
        import time
        error_key1 = f"{ErrorCategory.SYSTEM.value}_Exception"
        error_key2 = f"{ErrorCategory.UI_ELEMENT.value}_Exception"
        error_handler.error_frequency = {
            error_key1: [time.time()],
            error_key2: [time.time()]
        }
        
        # 重置特定错误
        error_handler.reset_error_frequency(error_key1)
        assert error_key1 not in error_handler.error_frequency
        assert error_key2 in error_handler.error_frequency
        
        # 重置所有错误
        error_handler.reset_error_frequency()
        assert len(error_handler.error_frequency) == 0
    
    @pytest.mark.asyncio
    async def test_shutdown(self, error_handler):
        """测试关闭"""
        # 添加一些恢复策略
        error_handler.recovery_strategies = [Mock(), Mock(), Mock()]
        
        await error_handler.shutdown()
        
        # 验证恢复策略被清空
        assert len(error_handler.recovery_strategies) == 0