"""错误处理和恢复模块.

提供任务执行过程中的错误处理、重试策略和恢复机制。
"""

import uuid
import traceback
import time
import asyncio
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, List, Optional, Any, Tuple, Type, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import random
import math

from .events import EventBus
from .logger import get_logger


class ErrorSeverity(Enum):
    """错误严重程度。"""
    LOW = "low"          # 轻微错误，可以忽略
    MEDIUM = "medium"    # 中等错误，需要重试
    HIGH = "high"        # 严重错误，需要人工干预
    CRITICAL = "critical" # 致命错误，停止所有相关任务


class ErrorCategory(Enum):
    """错误类别。"""
    NETWORK = "network"           # 网络相关错误
    GAME_STATE = "game_state"     # 游戏状态错误
    UI_ELEMENT = "ui_element"     # UI元素错误
    RESOURCE = "resource"         # 资源相关错误
    PERMISSION = "permission"     # 权限错误
    TIMEOUT = "timeout"           # 超时错误
    VALIDATION = "validation"     # 验证错误
    SYSTEM = "system"             # 系统错误
    UNKNOWN = "unknown"           # 未知错误


class RecoveryAction(Enum):
    """恢复动作。"""
    RETRY = "retry"               # 重试
    SKIP = "skip"                 # 跳过
    RESTART = "restart"           # 重启任务
    FALLBACK = "fallback"         # 使用备用方案
    ABORT = "abort"               # 中止任务
    ESCALATE = "escalate"         # 上报处理
    WAIT_AND_RETRY = "wait_retry" # 等待后重试


@dataclass
class ErrorInfo:
    """错误信息。"""
    error_id: str
    timestamp: datetime
    error_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    task_id: Optional[str] = None
    task_type: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    retry_count: int = 0
    recovery_attempts: List[str] = field(default_factory=list)
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    resolution_method: Optional[str] = None


@dataclass
class RetryConfig:
    """重试配置。"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: bool = True
    exponential_backoff: bool = True
    retry_on_exceptions: List[Type[Exception]] = field(default_factory=list)
    stop_on_exceptions: List[Type[Exception]] = field(default_factory=list)


class ErrorClassifier:
    """错误分类器。"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # 错误模式映射
        self.error_patterns = {
            # 网络错误
            ErrorCategory.NETWORK: [
                "connection", "timeout", "network", "socket", "dns",
                "http", "ssl", "certificate", "proxy"
            ],
            # 游戏状态错误
            ErrorCategory.GAME_STATE: [
                "game not found", "game closed", "invalid state",
                "unexpected screen", "wrong scene"
            ],
            # UI元素错误
            ErrorCategory.UI_ELEMENT: [
                "element not found", "click failed", "ui element",
                "button not clickable", "text not found"
            ],
            # 资源错误
            ErrorCategory.RESOURCE: [
                "memory", "disk space", "file not found",
                "permission denied", "resource busy"
            ],
            # 超时错误
            ErrorCategory.TIMEOUT: [
                "timeout", "timed out", "deadline exceeded",
                "operation timeout"
            ],
            # 验证错误
            ErrorCategory.VALIDATION: [
                "validation", "invalid input", "format error",
                "parse error", "schema error"
            ]
        }
    
    def classify_error(self, error: Exception, context: Dict[str, Any] = None) -> tuple[ErrorCategory, ErrorSeverity]:
        """分类错误。
        
        Args:
            error: 异常对象
            context: 上下文信息
            
        Returns:
            错误类别和严重程度
        """
        error_message = str(error).lower()
        error_type = type(error).__name__
        
        # 根据异常类型分类
        category = self._classify_by_type(error)
        if category == ErrorCategory.UNKNOWN:
            # 根据错误消息分类
            category = self._classify_by_message(error_message)
        
        # 确定严重程度
        severity = self._determine_severity(error, category, context)
        
        self.logger.debug(f"错误分类: {error_type} -> {category.value}, 严重程度: {severity.value}")
        
        return category, severity
    
    def _classify_by_type(self, error: Exception) -> ErrorCategory:
        """根据异常类型分类。"""
        error_type = type(error).__name__
        
        # 网络相关异常
        if error_type in ['ConnectionError', 'TimeoutError', 'HTTPError', 'URLError', 'SSLError']:
            return ErrorCategory.NETWORK
        
        # 文件/资源相关异常
        if error_type in ['FileNotFoundError', 'PermissionError', 'OSError', 'IOError']:
            return ErrorCategory.RESOURCE
        
        # 验证相关异常
        if error_type in ['ValueError', 'TypeError', 'ValidationError', 'ParseError']:
            return ErrorCategory.VALIDATION
        
        # 系统相关异常
        if error_type in ['SystemError', 'MemoryError', 'RuntimeError']:
            return ErrorCategory.SYSTEM
        
        return ErrorCategory.UNKNOWN
    
    def _classify_by_message(self, error_message: str) -> ErrorCategory:
        """根据错误消息分类。"""
        for category, patterns in self.error_patterns.items():
            for pattern in patterns:
                if pattern in error_message:
                    return category
        
        return ErrorCategory.UNKNOWN
    
    def _determine_severity(self, error: Exception, category: ErrorCategory, context: Dict[str, Any] = None) -> ErrorSeverity:
        """确定错误严重程度。"""
        context = context or {}
        
        # 根据错误类别确定基础严重程度
        base_severity = {
            ErrorCategory.NETWORK: ErrorSeverity.MEDIUM,
            ErrorCategory.GAME_STATE: ErrorSeverity.HIGH,
            ErrorCategory.UI_ELEMENT: ErrorSeverity.MEDIUM,
            ErrorCategory.RESOURCE: ErrorSeverity.HIGH,
            ErrorCategory.PERMISSION: ErrorSeverity.HIGH,
            ErrorCategory.TIMEOUT: ErrorSeverity.MEDIUM,
            ErrorCategory.VALIDATION: ErrorSeverity.LOW,
            ErrorCategory.SYSTEM: ErrorSeverity.CRITICAL,
            ErrorCategory.UNKNOWN: ErrorSeverity.MEDIUM
        }.get(category, ErrorSeverity.MEDIUM)
        
        # 根据上下文调整严重程度
        retry_count = context.get('retry_count', 0)
        if retry_count > 3:
            # 多次重试失败，提升严重程度
            if base_severity == ErrorSeverity.LOW:
                base_severity = ErrorSeverity.MEDIUM
            elif base_severity == ErrorSeverity.MEDIUM:
                base_severity = ErrorSeverity.HIGH
        
        # 检查是否为致命异常
        if isinstance(error, (MemoryError, SystemExit, KeyboardInterrupt)):
            return ErrorSeverity.CRITICAL
        
        return base_severity


class RecoveryStrategy(ABC):
    """恢复策略基类。"""
    
    @abstractmethod
    async def can_handle(self, error_info: ErrorInfo) -> bool:
        """检查是否可以处理该错误。"""
        pass
    
    @abstractmethod
    async def recover(self, error_info: ErrorInfo, context: Dict[str, Any]) -> tuple[bool, str]:
        """执行恢复操作。
        
        Returns:
            (是否成功, 恢复描述)
        """
        pass


class RetryStrategy(RecoveryStrategy):
    """重试策略。"""
    
    def __init__(self, retry_config: RetryConfig):
        self.config = retry_config
        self.logger = get_logger(__name__)
    
    async def can_handle(self, error_info: ErrorInfo) -> bool:
        """检查是否可以重试。"""
        # 检查重试次数
        if error_info.retry_count >= self.config.max_attempts:
            return False
        
        # 检查错误严重程度
        if error_info.severity == ErrorSeverity.CRITICAL:
            return False
        
        # 检查错误类别
        retryable_categories = [
            ErrorCategory.NETWORK,
            ErrorCategory.TIMEOUT,
            ErrorCategory.UI_ELEMENT
        ]
        
        return error_info.category in retryable_categories
    
    async def recover(self, error_info: ErrorInfo, context: Dict[str, Any]) -> tuple[bool, str]:
        """执行重试。"""
        try:
            # 计算延迟时间
            delay = self._calculate_delay(error_info.retry_count)
            
            self.logger.info(f"重试任务 {error_info.task_id}，延迟 {delay:.2f} 秒")
            
            # 等待
            await asyncio.sleep(delay)
            
            # 记录恢复尝试
            error_info.recovery_attempts.append(f"retry_{error_info.retry_count + 1}")
            
            return True, f"重试第 {error_info.retry_count + 1} 次"
            
        except Exception as e:
            self.logger.error(f"重试失败: {e}")
            return False, f"重试失败: {e}"
    
    def _calculate_delay(self, retry_count: int) -> float:
        """计算重试延迟。"""
        if self.config.exponential_backoff:
            delay = self.config.base_delay * (self.config.backoff_factor ** retry_count)
        else:
            delay = self.config.base_delay
        
        # 限制最大延迟
        delay = min(delay, self.config.max_delay)
        
        # 添加抖动
        if self.config.jitter:
            jitter = delay * 0.1 * random.random()
            delay += jitter
        
        return delay


class FallbackStrategy(RecoveryStrategy):
    """备用方案策略。"""
    
    def __init__(self, fallback_actions: Dict[ErrorCategory, Callable]):
        self.fallback_actions = fallback_actions
        self.logger = get_logger(__name__)
    
    async def can_handle(self, error_info: ErrorInfo) -> bool:
        """检查是否有备用方案。"""
        return error_info.category in self.fallback_actions
    
    async def recover(self, error_info: ErrorInfo, context: Dict[str, Any]) -> tuple[bool, str]:
        """执行备用方案。"""
        try:
            fallback_action = self.fallback_actions[error_info.category]
            
            self.logger.info(f"执行备用方案: {error_info.category.value}")
            
            # 执行备用动作
            if asyncio.iscoroutinefunction(fallback_action):
                result = await fallback_action(error_info, context)
            else:
                result = fallback_action(error_info, context)
            
            error_info.recovery_attempts.append(f"fallback_{error_info.category.value}")
            
            return True, f"执行备用方案: {error_info.category.value}"
            
        except Exception as e:
            self.logger.error(f"备用方案执行失败: {e}")
            return False, f"备用方案失败: {e}"


class RestartStrategy(RecoveryStrategy):
    """重启策略。"""
    
    def __init__(self, restart_threshold: int = 3):
        self.restart_threshold = restart_threshold
        self.logger = get_logger(__name__)
    
    async def can_handle(self, error_info: ErrorInfo) -> bool:
        """检查是否需要重启。"""
        # 高严重程度错误且重试多次失败
        return (error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] and 
                error_info.retry_count >= self.restart_threshold)
    
    async def recover(self, error_info: ErrorInfo, context: Dict[str, Any]) -> tuple[bool, str]:
        """执行重启。"""
        try:
            self.logger.warning(f"重启任务 {error_info.task_id}")
            
            # 这里应该调用任务重启逻辑
            # 具体实现依赖于任务执行器
            restart_callback = context.get('restart_callback')
            if restart_callback:
                if asyncio.iscoroutinefunction(restart_callback):
                    await restart_callback(error_info.task_id)
                else:
                    restart_callback(error_info.task_id)
            
            error_info.recovery_attempts.append("restart")
            
            return True, "任务已重启"
            
        except Exception as e:
            self.logger.error(f"任务重启失败: {e}")
            return False, f"重启失败: {e}"


class GameStateRecoveryStrategy(RecoveryStrategy):
    """游戏状态恢复策略。"""
    
    def __init__(self, game_operator=None):
        self.game_operator = game_operator
        self.logger = get_logger(__name__)
    
    async def can_handle(self, error_info: ErrorInfo) -> bool:
        """检查是否可以处理游戏状态错误。"""
        return (error_info.category == ErrorCategory.GAME_STATE and 
                self.game_operator is not None)
    
    async def recover(self, error_info: ErrorInfo, context: Dict[str, Any]) -> tuple[bool, str]:
        """执行游戏状态恢复。"""
        try:
            self.logger.info("尝试恢复游戏状态")
            
            # 截图检查当前状态
            screenshot = await self.game_operator.take_screenshot()
            
            # 尝试返回主界面
            if await self._return_to_main_menu():
                error_info.recovery_attempts.append("return_to_main")
                return True, "已返回主界面"
            
            # 尝试重启游戏
            if await self._restart_game():
                error_info.recovery_attempts.append("restart_game")
                return True, "已重启游戏"
            
            return False, "游戏状态恢复失败"
            
        except Exception as e:
            self.logger.error(f"游戏状态恢复异常: {e}")
            return False, f"恢复异常: {e}"
    
    async def _return_to_main_menu(self) -> bool:
        """返回主界面。"""
        try:
            # 多次按ESC键尝试返回
            for _ in range(3):
                await self.game_operator.press_key('escape')
                await asyncio.sleep(1.0)
                
                # 检查是否到达主界面
                if await self.game_operator.wait_for_ui_element(
                    template_path="templates/main_menu.png",
                    timeout=5.0
                ):
                    return True
            
            return False
            
        except Exception:
            return False
    
    async def _restart_game(self) -> bool:
        """重启游戏。"""
        try:
            # 这里应该实现游戏重启逻辑
            # 具体实现依赖于游戏启动器
            self.logger.warning("游戏重启功能需要具体实现")
            return False
            
        except Exception:
            return False


class UIElementRecoveryStrategy(RecoveryStrategy):
    """UI元素恢复策略。"""
    
    def __init__(self, game_operator=None):
        self.game_operator = game_operator
        self.logger = get_logger(__name__)
    
    async def can_handle(self, error_info: ErrorInfo) -> bool:
        """检查是否可以处理UI元素错误。"""
        return (error_info.category == ErrorCategory.UI_ELEMENT and 
                self.game_operator is not None)
    
    async def recover(self, error_info: ErrorInfo, context: Dict[str, Any]) -> tuple[bool, str]:
        """执行UI元素恢复。"""
        try:
            self.logger.info("尝试恢复UI元素问题")
            
            # 等待界面稳定
            await asyncio.sleep(2.0)
            
            # 尝试刷新界面
            if await self._refresh_ui():
                error_info.recovery_attempts.append("refresh_ui")
                return True, "界面已刷新"
            
            # 尝试重新导航
            if await self._re_navigate():
                error_info.recovery_attempts.append("re_navigate")
                return True, "重新导航成功"
            
            return False, "UI元素恢复失败"
            
        except Exception as e:
            self.logger.error(f"UI元素恢复异常: {e}")
            return False, f"恢复异常: {e}"
    
    async def _refresh_ui(self) -> bool:
        """刷新界面。"""
        try:
            # 按F5或其他刷新键
            await self.game_operator.press_key('f5')
            await asyncio.sleep(3.0)
            return True
            
        except Exception:
            return False
    
    async def _re_navigate(self) -> bool:
        """重新导航。"""
        try:
            # 返回上一级界面再重新进入
            await self.game_operator.press_key('escape')
            await asyncio.sleep(1.0)
            return True
            
        except Exception:
            return False


class ErrorHandler:
    """错误处理器。"""
    
    def __init__(self, event_bus: Optional[EventBus] = None, game_operator=None):
        """初始化错误处理器。
        
        Args:
            event_bus: 事件总线实例
            game_operator: 游戏操作器实例
        """
        self.logger = get_logger(__name__)
        self.event_bus = event_bus or EventBus()
        self.game_operator = game_operator
        
        # 组件
        self.classifier = ErrorClassifier()
        
        # 恢复策略
        self.recovery_strategies: List[RecoveryStrategy] = []
        
        # 错误记录
        self.error_history: Dict[str, ErrorInfo] = {}
        self.error_stats = {
            'total_errors': 0,
            'resolved_errors': 0,
            'category_counts': {category.value: 0 for category in ErrorCategory},
            'severity_counts': {severity.value: 0 for severity in ErrorSeverity}
        }
        self.stats_lock = Lock()
        
        # 错误频率监控
        self.error_frequency = {}
        self.frequency_threshold = 5  # 5分钟内同类错误超过阈值则升级
        self.frequency_window = 300  # 5分钟窗口
        
        # 默认重试配置
        self.default_retry_config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=30.0,
            backoff_factor=2.0,
            jitter=True,
            exponential_backoff=True
        )
        
        # 注册默认策略
        self._register_default_strategies()
        
        self.logger.info("错误处理器初始化完成")
    
    def _register_default_strategies(self):
        """注册默认恢复策略。"""
        # 重试策略
        retry_strategy = RetryStrategy(self.default_retry_config)
        self.add_recovery_strategy(retry_strategy)
        
        # 重启策略
        restart_strategy = RestartStrategy(restart_threshold=3)
        self.add_recovery_strategy(restart_strategy)
        
        # 游戏特定策略
        if self.game_operator:
            game_state_strategy = GameStateRecoveryStrategy(self.game_operator)
            self.add_recovery_strategy(game_state_strategy)
            
            ui_element_strategy = UIElementRecoveryStrategy(self.game_operator)
            self.add_recovery_strategy(ui_element_strategy)
    
    def add_recovery_strategy(self, strategy: RecoveryStrategy):
        """添加恢复策略。
        
        Args:
            strategy: 恢复策略实例
        """
        self.recovery_strategies.append(strategy)
        self.logger.debug(f"添加恢复策略: {type(strategy).__name__}")
    
    async def handle_error(self, error: Exception, task_id: str = None, 
                          task_type: str = None, context: Dict[str, Any] = None) -> ErrorInfo:
        """处理错误。
        
        Args:
            error: 异常对象
            task_id: 任务ID
            task_type: 任务类型
            context: 上下文信息
            
        Returns:
            错误信息对象
        """
        context = context or {}
        
        # 分类错误
        category, severity = self.classifier.classify_error(error, context)
        
        # 创建错误信息
        error_id = f"error_{int(time.time() * 1000)}"
        error_info = ErrorInfo(
            error_id=error_id,
            timestamp=datetime.now(),
            error_type=type(error).__name__,
            error_message=str(error),
            severity=severity,
            category=category,
            task_id=task_id,
            task_type=task_type,
            context=context,
            stack_trace=traceback.format_exc(),
            retry_count=context.get('retry_count', 0)
        )
        
        # 记录错误
        self.error_history[error_id] = error_info
        
        # 更新统计
        with self.stats_lock:
            self.error_stats['total_errors'] += 1
            self.error_stats['category_counts'][category.value] += 1
            self.error_stats['severity_counts'][severity.value] += 1
        
        # 发送错误事件
        await self.event_bus.emit_async("error_occurred", {
            "error_info": error_info,
            "task_id": task_id,
            "task_type": task_type,
            "context": context
        })
        
        self.logger.error(f"错误处理: {error_info.error_id} - {error_info.error_message}")
        
        # 尝试恢复
        recovery_success = await self._attempt_recovery(error_info, context)
        
        if recovery_success:
            error_info.resolved = True
            error_info.resolution_time = datetime.now()
            
            with self.stats_lock:
                self.error_stats['resolved_errors'] += 1
            
            await self.event_bus.emit("error_resolved", {
                "error_info": error_info
            })
        
        return error_info
    
    async def try_recovery(self, error_info: ErrorInfo, context: Dict[str, Any] = None) -> bool:
        """尝试错误恢复（公共接口）。
        
        Args:
            error_info: 错误信息
            context: 上下文信息
            
        Returns:
            是否恢复成功
        """
        context = context or {}
        return await self._attempt_recovery(error_info, context)
    
    async def _attempt_recovery(self, error_info: ErrorInfo, context: Dict[str, Any]) -> bool:
        """尝试错误恢复。
        
        Args:
            error_info: 错误信息
            context: 上下文信息
            
        Returns:
            是否恢复成功
        """
        for strategy in self.recovery_strategies:
            try:
                if await strategy.can_handle(error_info):
                    self.logger.info(f"尝试恢复策略: {type(strategy).__name__}")
                    
                    success, description = await strategy.recover(error_info, context)
                    
                    if success:
                        error_info.resolution_method = type(strategy).__name__
                        self.logger.info(f"恢复成功: {description}")
                        return True
                    else:
                        self.logger.warning(f"恢复失败: {description}")
                
            except Exception as e:
                self.logger.error(f"恢复策略执行异常: {e}")
        
        return False
    
    def get_error_info(self, error_id: str) -> Optional[ErrorInfo]:
        """获取错误信息。
        
        Args:
            error_id: 错误ID
            
        Returns:
            错误信息或None
        """
        return self.error_history.get(error_id)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计。
        
        Returns:
            错误统计信息
        """
        with self.stats_lock:
            stats = self.error_stats.copy()
        
        # 计算解决率
        if stats['total_errors'] > 0:
            stats['resolution_rate'] = (stats['resolved_errors'] / stats['total_errors']) * 100
        else:
            stats['resolution_rate'] = 0.0
        
        return stats
    
    def get_recent_errors(self, hours: int = 24, severity: Optional[ErrorSeverity] = None) -> List[ErrorInfo]:
        """获取最近的错误。
        
        Args:
            hours: 时间范围（小时）
            severity: 错误严重程度过滤
            
        Returns:
            错误信息列表
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_errors = [
            error_info for error_info in self.error_history.values()
            if error_info.timestamp >= cutoff_time
        ]
        
        if severity:
            recent_errors = [e for e in recent_errors if e.severity == severity]
        
        # 按时间倒序排列
        recent_errors.sort(key=lambda x: x.timestamp, reverse=True)
        
        return recent_errors
    
    def clear_old_errors(self, days: int = 7):
        """清理旧错误记录。
        
        Args:
            days: 保留天数
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        
        old_error_ids = [
            error_id for error_id, error_info in self.error_history.items()
            if error_info.timestamp < cutoff_time
        ]
        
        for error_id in old_error_ids:
            del self.error_history[error_id]
        
        self.logger.info(f"清理了 {len(old_error_ids)} 条旧错误记录")
    
    def _check_error_frequency(self, error: Exception, category: ErrorCategory, severity: ErrorSeverity) -> ErrorSeverity:
        """检查错误频率并可能升级严重程度。"""
        error_key = f"{category.value}_{type(error).__name__}"
        current_time = time.time()
        
        # 初始化错误频率记录
        if error_key not in self.error_frequency:
            self.error_frequency[error_key] = []
        
        # 添加当前错误时间
        self.error_frequency[error_key].append(current_time)
        
        # 清理过期记录
        cutoff_time = current_time - self.frequency_window
        self.error_frequency[error_key] = [
            timestamp for timestamp in self.error_frequency[error_key]
            if timestamp > cutoff_time
        ]
        
        # 检查频率是否超过阈值
        error_count = len(self.error_frequency[error_key])
        if error_count >= self.frequency_threshold:
            # 升级严重程度
            if severity == ErrorSeverity.LOW:
                severity = ErrorSeverity.MEDIUM
                self.logger.warning(f"错误频率过高，升级严重程度: {error_key} ({error_count}次)")
            elif severity == ErrorSeverity.MEDIUM:
                severity = ErrorSeverity.HIGH
                self.logger.warning(f"错误频率过高，升级严重程度: {error_key} ({error_count}次)")
        
        return severity
    
    def get_error_frequency_stats(self) -> Dict[str, int]:
        """获取错误频率统计。"""
        current_time = time.time()
        cutoff_time = current_time - self.frequency_window
        
        stats = {}
        for error_key, timestamps in self.error_frequency.items():
            # 只统计时间窗口内的错误
            recent_errors = [t for t in timestamps if t > cutoff_time]
            if recent_errors:
                stats[error_key] = len(recent_errors)
        
        return stats
    
    def reset_error_frequency(self, error_key: Optional[str] = None):
        """重置错误频率记录。"""
        if error_key:
            self.error_frequency.pop(error_key, None)
            self.logger.info(f"已重置错误频率记录: {error_key}")
        else:
            self.error_frequency.clear()
            self.logger.info("已重置所有错误频率记录")
    
    async def shutdown(self):
        """关闭错误处理器。"""
        self.logger.info("错误处理器正在关闭...")
        
        # 清理资源
        self.recovery_strategies.clear()
        
        self.logger.info("错误处理器已关闭")