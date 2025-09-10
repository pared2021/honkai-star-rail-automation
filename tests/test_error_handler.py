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
        # 测试网络错误
        network_error = ConnectionError("Network connection failed")
        category = classifier.classify_by_type(network_error)
        assert category == ErrorCategory.NETWORK
        
        # 测试超时错误
        timeout_error = TimeoutError("Operation timed out")
        category = classifier.classify_by_type(timeout_error)
        assert category == ErrorCategory.TIMEOUT
        
        # 测试一般异常
        general_error = ValueError("Invalid value")
        category = classifier.classify_by_type(general_error)
        assert category == ErrorCategory.SYSTEM
    
    def test_classify_by_message(self, classifier):
        """测试按消息分类错误"""
        # 测试UI相关错误
        ui_error = Exception("Element not found on screen")
        category = classifier.classify_by_message(ui_error)
        assert category == ErrorCategory.UI
        
        # 测试游戏状态错误
        game_error = Exception("Game state invalid")
        category = classifier.classify_by_message(game_error)
        assert category == ErrorCategory.GAME_STATE
        
        # 测试OCR错误
        ocr_error = Exception("OCR detection failed")
        category = classifier.classify_by_message(ocr_error)
        assert category == ErrorCategory.OCR
    
    def test_determine_severity(self, classifier):
        """测试确定错误严重程度"""
        # 测试低严重程度
        low_error = Exception("Minor UI glitch")
        severity = classifier.determine_severity(ErrorCategory.UI, low_error)
        assert severity == ErrorSeverity.LOW
        
        # 测试高严重程度
        high_error = Exception("System crash")
        severity = classifier.determine_severity(ErrorCategory.SYSTEM, high_error)
        assert severity == ErrorSeverity.HIGH
        
        # 测试中等严重程度
        medium_error = Exception("Network timeout")
        severity = classifier.determine_severity(ErrorCategory.NETWORK, medium_error)
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
        strategy = RetryStrategy(max_attempts=3, base_delay=1.0)
        
        error_info = ErrorInfo(
            error=Exception("Test error"),
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
            context={'attempt': 1}
        )
        
        # 测试可以重试
        can_recover = await strategy.can_recover(error_info)
        assert can_recover is True
        
        # 测试重试恢复
        result = await strategy.recover(error_info, mock_components['game_operator'])
        assert result.action == RecoveryAction.RETRY
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_retry_strategy_max_attempts(self, mock_components):
        """测试重试策略达到最大尝试次数"""
        strategy = RetryStrategy(max_attempts=2, base_delay=0.1)
        
        error_info = ErrorInfo(
            error=Exception("Test error"),
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
            context={'attempt': 3}  # 超过最大尝试次数
        )
        
        # 测试不能重试
        can_recover = await strategy.can_recover(error_info)
        assert can_recover is False
    
    @pytest.mark.asyncio
    async def test_fallback_strategy(self, mock_components):
        """测试备用方案策略"""
        async def mock_fallback():
            return True
        
        strategy = FallbackStrategy(fallback_action=mock_fallback)
        
        error_info = ErrorInfo(
            error=Exception("Test error"),
            category=ErrorCategory.UI,
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
            context={}
        )
        
        # 测试可以恢复
        can_recover = await strategy.can_recover(error_info)
        assert can_recover is True
        
        # 测试备用方案恢复
        result = await strategy.recover(error_info, mock_components['game_operator'])
        assert result.action == RecoveryAction.FALLBACK
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_restart_strategy(self, mock_components):
        """测试重启策略"""
        strategy = RestartStrategy(restart_threshold=3)
        
        error_info = ErrorInfo(
            error=Exception("Critical error"),
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            timestamp=datetime.now(),
            context={'consecutive_failures': 4}
        )
        
        # 测试可以重启
        can_recover = await strategy.can_recover(error_info)
        assert can_recover is True
        
        # 模拟重启操作
        mock_components['game_operator'].restart_game = AsyncMock(return_value=True)
        
        result = await strategy.recover(error_info, mock_components['game_operator'])
        assert result.action == RecoveryAction.RESTART
        mock_components['game_operator'].restart_game.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_game_state_recovery_strategy(self, mock_components):
        """测试游戏状态恢复策略"""
        strategy = GameStateRecoveryStrategy()
        
        error_info = ErrorInfo(
            error=Exception("Game state error"),
            category=ErrorCategory.GAME_STATE,
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
            context={}
        )
        
        # 模拟游戏操作
        mock_components['game_operator'].get_current_scene = Mock(return_value="unknown")
        mock_components['game_operator'].navigate_to_main_menu = AsyncMock(return_value=True)
        
        result = await strategy.recover(error_info, mock_components['game_operator'])
        assert result.action == RecoveryAction.RESET_STATE
        mock_components['game_operator'].navigate_to_main_menu.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ui_element_recovery_strategy(self, mock_components):
        """测试UI元素恢复策略"""
        strategy = UIElementRecoveryStrategy()
        
        error_info = ErrorInfo(
            error=Exception("Element not found"),
            category=ErrorCategory.UI,
            severity=ErrorSeverity.LOW,
            timestamp=datetime.now(),
            context={'element': 'test_button'}
        )
        
        # 模拟UI操作
        mock_components['game_operator'].refresh_screen = AsyncMock(return_value=True)
        mock_components['game_detector'].find_ui_element = Mock(return_value=Mock(center=(100, 200)))
        
        result = await strategy.recover(error_info, mock_components['game_operator'])
        assert result.action == RecoveryAction.REFRESH_UI
        mock_components['game_operator'].refresh_screen.assert_called_once()


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
            game_operator=mock_components['game_operator'],
            event_bus=mock_components['event_bus'],
            default_retry_config=retry_config
        )
        return handler
    
    def test_initialization(self, error_handler, mock_components, retry_config):
        """测试初始化"""
        assert error_handler.game_operator == mock_components['game_operator']
        assert error_handler.event_bus == mock_components['event_bus']
        assert error_handler.default_retry_config == retry_config
        assert len(error_handler.recovery_strategies) > 0
        assert len(error_handler.error_history) == 0
    
    def test_add_recovery_strategy(self, error_handler):
        """测试添加恢复策略"""
        custom_strategy = RetryStrategy(max_attempts=5, base_delay=2.0)
        
        error_handler.add_recovery_strategy(ErrorCategory.CUSTOM, custom_strategy)
        
        assert ErrorCategory.CUSTOM in error_handler.recovery_strategies
        assert custom_strategy in error_handler.recovery_strategies[ErrorCategory.CUSTOM]
    
    @pytest.mark.asyncio
    async def test_handle_error(self, error_handler, mock_components):
        """测试错误处理"""
        test_error = Exception("Test error")
        context = {'operation': 'test_operation'}
        
        # 模拟恢复策略
        mock_strategy = Mock()
        mock_strategy.can_recover = AsyncMock(return_value=True)
        mock_strategy.recover = AsyncMock(return_value=Mock(
            success=True,
            action=RecoveryAction.RETRY,
            message="Recovery successful"
        ))
        
        # 添加模拟策略
        error_handler.recovery_strategies[ErrorCategory.SYSTEM] = [mock_strategy]
        
        result = await error_handler.handle_error(test_error, context)
        
        assert result.success is True
        assert result.action == RecoveryAction.RETRY
        assert len(error_handler.error_history) == 1
        
        # 验证事件发送
        mock_components['event_bus'].emit.assert_called()
    
    @pytest.mark.asyncio
    async def test_handle_error_no_recovery(self, error_handler, mock_components):
        """测试无法恢复的错误处理"""
        test_error = Exception("Unrecoverable error")
        context = {'operation': 'test_operation'}
        
        # 清空恢复策略
        error_handler.recovery_strategies = {}
        
        result = await error_handler.handle_error(test_error, context)
        
        assert result.success is False
        assert result.action == RecoveryAction.ABORT
        assert len(error_handler.error_history) == 1
    
    def test_get_error_info(self, error_handler):
        """测试获取错误信息"""
        test_error = Exception("Test error")
        context = {'operation': 'test_operation'}
        
        # 添加错误到历史记录
        error_info = ErrorInfo(
            error=test_error,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
            context=context
        )
        error_handler.error_history.append(error_info)
        
        # 获取错误信息
        retrieved_info = error_handler.get_error_info(0)
        assert retrieved_info == error_info
        
        # 测试无效索引
        invalid_info = error_handler.get_error_info(999)
        assert invalid_info is None
    
    def test_get_error_statistics(self, error_handler):
        """测试获取错误统计"""
        # 添加一些错误到历史记录
        errors = [
            ErrorInfo(
                error=Exception("Error 1"),
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.LOW,
                timestamp=datetime.now(),
                context={}
            ),
            ErrorInfo(
                error=Exception("Error 2"),
                category=ErrorCategory.UI,
                severity=ErrorSeverity.MEDIUM,
                timestamp=datetime.now(),
                context={}
            ),
            ErrorInfo(
                error=Exception("Error 3"),
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.HIGH,
                timestamp=datetime.now(),
                context={}
            )
        ]
        
        error_handler.error_history.extend(errors)
        
        stats = error_handler.get_error_statistics()
        
        assert stats['total_errors'] == 3
        assert stats['by_category'][ErrorCategory.NETWORK] == 2
        assert stats['by_category'][ErrorCategory.UI] == 1
        assert stats['by_severity'][ErrorSeverity.LOW] == 1
        assert stats['by_severity'][ErrorSeverity.MEDIUM] == 1
        assert stats['by_severity'][ErrorSeverity.HIGH] == 1
    
    def test_get_recent_errors(self, error_handler):
        """测试获取最近错误"""
        # 添加错误到历史记录
        now = datetime.now()
        errors = [
            ErrorInfo(
                error=Exception("Old error"),
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.LOW,
                timestamp=now - timedelta(hours=2),
                context={}
            ),
            ErrorInfo(
                error=Exception("Recent error"),
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                timestamp=now - timedelta(minutes=30),
                context={}
            )
        ]
        
        error_handler.error_history.extend(errors)
        
        # 获取最近1小时的错误
        recent_errors = error_handler.get_recent_errors(hours=1)
        
        assert len(recent_errors) == 1
        assert recent_errors[0].error.args[0] == "Recent error"
    
    def test_clear_old_errors(self, error_handler):
        """测试清理旧错误"""
        # 添加错误到历史记录
        now = datetime.now()
        errors = [
            ErrorInfo(
                error=Exception("Old error"),
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.LOW,
                timestamp=now - timedelta(days=2),
                context={}
            ),
            ErrorInfo(
                error=Exception("Recent error"),
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                timestamp=now - timedelta(hours=1),
                context={}
            )
        ]
        
        error_handler.error_history.extend(errors)
        
        # 清理1天前的错误
        cleared_count = error_handler.clear_old_errors(days=1)
        
        assert cleared_count == 1
        assert len(error_handler.error_history) == 1
        assert error_handler.error_history[0].error.args[0] == "Recent error"
    
    def test_check_error_frequency(self, error_handler):
        """测试错误频率检查"""
        # 添加频繁错误
        now = datetime.now()
        for i in range(5):
            error_info = ErrorInfo(
                error=Exception(f"Frequent error {i}"),
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                timestamp=now - timedelta(minutes=i),
                context={}
            )
            error_handler.error_history.append(error_info)
        
        # 检查错误频率
        is_frequent = error_handler._check_error_frequency(ErrorCategory.NETWORK, 10, 3)
        
        assert is_frequent is True
    
    def test_get_error_frequency_stats(self, error_handler):
        """测试获取错误频率统计"""
        # 添加错误
        now = datetime.now()
        for i in range(3):
            error_info = ErrorInfo(
                error=Exception(f"Error {i}"),
                category=ErrorCategory.UI,
                severity=ErrorSeverity.LOW,
                timestamp=now - timedelta(minutes=i * 5),
                context={}
            )
            error_handler.error_history.append(error_info)
        
        stats = error_handler.get_error_frequency_stats(30)  # 30分钟内
        
        assert ErrorCategory.UI in stats
        assert stats[ErrorCategory.UI] == 3
    
    def test_reset_error_frequency(self, error_handler):
        """测试重置错误频率"""
        # 添加错误频率记录
        error_handler.error_frequency[ErrorCategory.NETWORK] = [
            datetime.now() - timedelta(minutes=1),
            datetime.now() - timedelta(minutes=2)
        ]
        
        error_handler.reset_error_frequency(ErrorCategory.NETWORK)
        
        assert len(error_handler.error_frequency[ErrorCategory.NETWORK]) == 0
    
    @pytest.mark.asyncio
    async def test_shutdown(self, error_handler):
        """测试关闭"""
        # 添加一些错误历史
        error_handler.error_history = [Mock() for _ in range(5)]
        
        await error_handler.shutdown()
        
        # 验证资源被清理
        assert len(error_handler.error_history) == 0
        assert len(error_handler.error_frequency) == 0