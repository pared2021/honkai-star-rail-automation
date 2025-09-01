# -*- coding: utf-8 -*-
"""
错误恢复策略配置 - 定义各种错误场景的恢复策略和配置
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from core.exception_recovery import ExceptionType, RecoveryAction
from application.error_handling_service import ErrorSeverity, RetryPolicy
from core.task_retry_manager import RetryStrategy, RetryTrigger


class ErrorCategory(Enum):
    """错误分类"""
    SYSTEM = "system"              # 系统级错误
    NETWORK = "network"            # 网络相关错误
    GAME = "game"                  # 游戏相关错误
    UI = "ui"                      # 用户界面错误
    AUTOMATION = "automation"      # 自动化操作错误
    TASK = "task"                  # 任务执行错误
    RESOURCE = "resource"          # 资源相关错误


@dataclass
class ErrorRecoveryStrategy:
    """错误恢复策略"""
    error_type: str
    category: ErrorCategory
    severity: ErrorSeverity
    
    # 重试配置
    retry_enabled: bool = True
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    max_retry_attempts: int = 3
    initial_retry_delay: float = 1.0
    max_retry_delay: float = 60.0
    retry_backoff_factor: float = 2.0
    
    # 恢复动作
    recovery_actions: List[RecoveryAction] = field(default_factory=list)
    
    # 触发条件
    retry_triggers: List[RetryTrigger] = field(default_factory=list)
    
    # 自定义处理器
    custom_handler: Optional[str] = None
    
    # 预防措施
    prevention_actions: List[str] = field(default_factory=list)
    
    # 监控和告警
    enable_monitoring: bool = True
    alert_threshold: int = 5  # 连续失败次数阈值
    
    # 其他配置
    timeout: Optional[float] = None
    requires_user_intervention: bool = False
    auto_escalate: bool = True
    escalation_delay: float = 300.0  # 5分钟后升级
    
    # 元数据
    description: str = ""
    tags: List[str] = field(default_factory=list)
    priority: int = 1  # 1-10，数字越大优先级越高


class ErrorRecoveryConfig:
    """错误恢复配置管理器"""
    
    def __init__(self):
        self.strategies: Dict[str, ErrorRecoveryStrategy] = {}
        self._init_default_strategies()
    
    def _init_default_strategies(self):
        """初始化默认恢复策略"""
        
        # 系统级错误策略
        self.strategies.update({
            # 内存不足
            "MemoryError": ErrorRecoveryStrategy(
                error_type="MemoryError",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.HIGH,
                retry_enabled=True,
                retry_strategy=RetryStrategy.LINEAR_BACKOFF,
                max_retry_attempts=2,
                initial_retry_delay=5.0,
                recovery_actions=[RecoveryAction.CLEAR_CACHE, RecoveryAction.WAIT_AND_RETRY],
                retry_triggers=[RetryTrigger.TASK_FAILED],
                prevention_actions=["定期清理缓存", "监控内存使用"],
                description="内存不足错误恢复策略",
                tags=["memory", "system", "resource"],
                priority=8
            ),
            
            # 磁盘空间不足
            "DiskSpaceError": ErrorRecoveryStrategy(
                error_type="DiskSpaceError",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                retry_enabled=False,
                recovery_actions=[RecoveryAction.CLEAR_CACHE],
                requires_user_intervention=True,
                description="磁盘空间不足错误策略",
                tags=["disk", "system", "resource"],
                priority=10
            ),
            
            # 权限错误
            "PermissionError": ErrorRecoveryStrategy(
                error_type="PermissionError",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.HIGH,
                retry_enabled=False,
                requires_user_intervention=True,
                description="权限错误策略",
                tags=["permission", "system"],
                priority=7
            )
        })
        
        # 网络相关错误策略
        self.strategies.update({
            # 连接错误
            "ConnectionError": ErrorRecoveryStrategy(
                error_type="ConnectionError",
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                retry_enabled=True,
                retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                max_retry_attempts=5,
                initial_retry_delay=2.0,
                max_retry_delay=30.0,
                recovery_actions=[RecoveryAction.WAIT_AND_RETRY],
                retry_triggers=[RetryTrigger.NETWORK_ERROR, RetryTrigger.TASK_FAILED],
                prevention_actions=["检查网络连接", "使用连接池"],
                description="网络连接错误恢复策略",
                tags=["network", "connection"],
                priority=6
            ),
            
            # 超时错误
            "TimeoutError": ErrorRecoveryStrategy(
                error_type="TimeoutError",
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                retry_enabled=True,
                retry_strategy=RetryStrategy.LINEAR_BACKOFF,
                max_retry_attempts=3,
                initial_retry_delay=3.0,
                recovery_actions=[RecoveryAction.WAIT_AND_RETRY],
                retry_triggers=[RetryTrigger.TIMEOUT, RetryTrigger.NETWORK_ERROR],
                timeout=60.0,
                description="网络超时错误恢复策略",
                tags=["network", "timeout"],
                priority=5
            ),
            
            # DNS解析错误
            "DNSError": ErrorRecoveryStrategy(
                error_type="DNSError",
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                retry_enabled=True,
                retry_strategy=RetryStrategy.FIXED_DELAY,
                max_retry_attempts=3,
                initial_retry_delay=5.0,
                recovery_actions=[RecoveryAction.WAIT_AND_RETRY],
                retry_triggers=[RetryTrigger.NETWORK_ERROR],
                description="DNS解析错误恢复策略",
                tags=["network", "dns"],
                priority=4
            )
        })
        
        # 游戏相关错误策略
        self.strategies.update({
            # 游戏崩溃
            "GameCrashError": ErrorRecoveryStrategy(
                error_type="GameCrashError",
                category=ErrorCategory.GAME,
                severity=ErrorSeverity.HIGH,
                retry_enabled=True,
                retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                max_retry_attempts=3,
                initial_retry_delay=10.0,
                max_retry_delay=120.0,
                recovery_actions=[
                    RecoveryAction.FORCE_CLOSE_GAME,
                    RecoveryAction.WAIT_AND_RETRY,
                    RecoveryAction.RESTART_GAME
                ],
                retry_triggers=[RetryTrigger.GAME_CRASH],
                prevention_actions=["定期重启游戏", "监控游戏进程"],
                description="游戏崩溃错误恢复策略",
                tags=["game", "crash"],
                priority=9
            ),
            
            # 游戏冻结
            "GameFreezeError": ErrorRecoveryStrategy(
                error_type="GameFreezeError",
                category=ErrorCategory.GAME,
                severity=ErrorSeverity.HIGH,
                retry_enabled=True,
                retry_strategy=RetryStrategy.IMMEDIATE,
                max_retry_attempts=2,
                recovery_actions=[
                    RecoveryAction.FORCE_CLOSE_GAME,
                    RecoveryAction.RESTART_GAME
                ],
                retry_triggers=[RetryTrigger.GAME_CRASH],
                timeout=30.0,
                description="游戏冻结错误恢复策略",
                tags=["game", "freeze"],
                priority=8
            ),
            
            # 游戏未找到
            "GameNotFoundError": ErrorRecoveryStrategy(
                error_type="GameNotFoundError",
                category=ErrorCategory.GAME,
                severity=ErrorSeverity.HIGH,
                retry_enabled=True,
                retry_strategy=RetryStrategy.LINEAR_BACKOFF,
                max_retry_attempts=5,
                initial_retry_delay=5.0,
                recovery_actions=[RecoveryAction.RESTART_GAME],
                retry_triggers=[RetryTrigger.GAME_CRASH],
                description="游戏未找到错误恢复策略",
                tags=["game", "detection"],
                priority=7
            )
        })
        
        # UI相关错误策略
        self.strategies.update({
            # UI元素未找到
            "UIElementNotFoundError": ErrorRecoveryStrategy(
                error_type="UIElementNotFoundError",
                category=ErrorCategory.UI,
                severity=ErrorSeverity.MEDIUM,
                retry_enabled=True,
                retry_strategy=RetryStrategy.LINEAR_BACKOFF,
                max_retry_attempts=5,
                initial_retry_delay=2.0,
                max_retry_delay=10.0,
                recovery_actions=[RecoveryAction.WAIT_AND_RETRY],
                retry_triggers=[RetryTrigger.UI_NOT_FOUND, RetryTrigger.ACTION_FAILED],
                prevention_actions=["更新UI模板", "增加等待时间"],
                description="UI元素未找到错误恢复策略",
                tags=["ui", "element", "detection"],
                priority=5
            ),
            
            # 意外场景
            "UnexpectedSceneError": ErrorRecoveryStrategy(
                error_type="UnexpectedSceneError",
                category=ErrorCategory.UI,
                severity=ErrorSeverity.MEDIUM,
                retry_enabled=True,
                retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                max_retry_attempts=3,
                initial_retry_delay=3.0,
                recovery_actions=[
                    RecoveryAction.RETURN_TO_MAIN,
                    RecoveryAction.WAIT_AND_RETRY
                ],
                retry_triggers=[RetryTrigger.UNEXPECTED_SCENE],
                description="意外场景错误恢复策略",
                tags=["ui", "scene", "navigation"],
                priority=6
            ),
            
            # UI响应超时
            "UITimeoutError": ErrorRecoveryStrategy(
                error_type="UITimeoutError",
                category=ErrorCategory.UI,
                severity=ErrorSeverity.MEDIUM,
                retry_enabled=True,
                retry_strategy=RetryStrategy.LINEAR_BACKOFF,
                max_retry_attempts=3,
                initial_retry_delay=5.0,
                recovery_actions=[RecoveryAction.REFRESH_PAGE, RecoveryAction.WAIT_AND_RETRY],
                retry_triggers=[RetryTrigger.TIMEOUT, RetryTrigger.UI_NOT_FOUND],
                description="UI响应超时错误恢复策略",
                tags=["ui", "timeout"],
                priority=4
            )
        })
        
        # 自动化操作错误策略
        self.strategies.update({
            # 点击失败
            "ClickFailedError": ErrorRecoveryStrategy(
                error_type="ClickFailedError",
                category=ErrorCategory.AUTOMATION,
                severity=ErrorSeverity.LOW,
                retry_enabled=True,
                retry_strategy=RetryStrategy.IMMEDIATE,
                max_retry_attempts=3,
                initial_retry_delay=0.5,
                recovery_actions=[RecoveryAction.WAIT_AND_RETRY],
                retry_triggers=[RetryTrigger.ACTION_FAILED],
                description="点击操作失败错误恢复策略",
                tags=["automation", "click"],
                priority=3
            ),
            
            # 键盘输入失败
            "KeyInputFailedError": ErrorRecoveryStrategy(
                error_type="KeyInputFailedError",
                category=ErrorCategory.AUTOMATION,
                severity=ErrorSeverity.LOW,
                retry_enabled=True,
                retry_strategy=RetryStrategy.IMMEDIATE,
                max_retry_attempts=3,
                initial_retry_delay=0.5,
                recovery_actions=[RecoveryAction.WAIT_AND_RETRY],
                retry_triggers=[RetryTrigger.ACTION_FAILED],
                description="键盘输入失败错误恢复策略",
                tags=["automation", "keyboard"],
                priority=3
            ),
            
            # 截图失败
            "ScreenshotFailedError": ErrorRecoveryStrategy(
                error_type="ScreenshotFailedError",
                category=ErrorCategory.AUTOMATION,
                severity=ErrorSeverity.LOW,
                retry_enabled=True,
                retry_strategy=RetryStrategy.IMMEDIATE,
                max_retry_attempts=2,
                initial_retry_delay=1.0,
                recovery_actions=[RecoveryAction.WAIT_AND_RETRY],
                retry_triggers=[RetryTrigger.ACTION_FAILED],
                description="截图失败错误恢复策略",
                tags=["automation", "screenshot"],
                priority=2
            )
        })
        
        # 任务执行错误策略
        self.strategies.update({
            # 任务超时
            "TaskTimeoutError": ErrorRecoveryStrategy(
                error_type="TaskTimeoutError",
                category=ErrorCategory.TASK,
                severity=ErrorSeverity.MEDIUM,
                retry_enabled=True,
                retry_strategy=RetryStrategy.LINEAR_BACKOFF,
                max_retry_attempts=2,
                initial_retry_delay=10.0,
                recovery_actions=[RecoveryAction.WAIT_AND_RETRY],
                retry_triggers=[RetryTrigger.TIMEOUT, RetryTrigger.TASK_FAILED],
                description="任务超时错误恢复策略",
                tags=["task", "timeout"],
                priority=6
            ),
            
            # 任务配置错误
            "TaskConfigError": ErrorRecoveryStrategy(
                error_type="TaskConfigError",
                category=ErrorCategory.TASK,
                severity=ErrorSeverity.HIGH,
                retry_enabled=False,
                requires_user_intervention=True,
                description="任务配置错误策略",
                tags=["task", "config"],
                priority=8
            ),
            
            # 任务依赖错误
            "TaskDependencyError": ErrorRecoveryStrategy(
                error_type="TaskDependencyError",
                category=ErrorCategory.TASK,
                severity=ErrorSeverity.MEDIUM,
                retry_enabled=True,
                retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                max_retry_attempts=3,
                initial_retry_delay=5.0,
                recovery_actions=[RecoveryAction.WAIT_AND_RETRY],
                retry_triggers=[RetryTrigger.TASK_FAILED],
                description="任务依赖错误恢复策略",
                tags=["task", "dependency"],
                priority=5
            )
        })
        
        # 资源相关错误策略
        self.strategies.update({
            # 文件不存在
            "FileNotFoundError": ErrorRecoveryStrategy(
                error_type="FileNotFoundError",
                category=ErrorCategory.RESOURCE,
                severity=ErrorSeverity.MEDIUM,
                retry_enabled=True,
                retry_strategy=RetryStrategy.LINEAR_BACKOFF,
                max_retry_attempts=2,
                initial_retry_delay=2.0,
                recovery_actions=[RecoveryAction.WAIT_AND_RETRY],
                retry_triggers=[RetryTrigger.TASK_FAILED],
                description="文件不存在错误恢复策略",
                tags=["resource", "file"],
                priority=4
            ),
            
            # 资源锁定
            "ResourceLockedError": ErrorRecoveryStrategy(
                error_type="ResourceLockedError",
                category=ErrorCategory.RESOURCE,
                severity=ErrorSeverity.MEDIUM,
                retry_enabled=True,
                retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                max_retry_attempts=5,
                initial_retry_delay=1.0,
                max_retry_delay=30.0,
                recovery_actions=[RecoveryAction.WAIT_AND_RETRY],
                retry_triggers=[RetryTrigger.TASK_FAILED],
                description="资源锁定错误恢复策略",
                tags=["resource", "lock"],
                priority=5
            )
        })
    
    def get_strategy(self, error_type: str) -> Optional[ErrorRecoveryStrategy]:
        """获取错误恢复策略"""
        return self.strategies.get(error_type)
    
    def add_strategy(self, strategy: ErrorRecoveryStrategy):
        """添加自定义恢复策略"""
        self.strategies[strategy.error_type] = strategy
    
    def update_strategy(self, error_type: str, **kwargs):
        """更新恢复策略"""
        if error_type in self.strategies:
            strategy = self.strategies[error_type]
            for key, value in kwargs.items():
                if hasattr(strategy, key):
                    setattr(strategy, key, value)
    
    def get_strategies_by_category(self, category: ErrorCategory) -> List[ErrorRecoveryStrategy]:
        """按分类获取恢复策略"""
        return [
            strategy for strategy in self.strategies.values()
            if strategy.category == category
        ]
    
    def get_strategies_by_severity(self, severity: ErrorSeverity) -> List[ErrorRecoveryStrategy]:
        """按严重程度获取恢复策略"""
        return [
            strategy for strategy in self.strategies.values()
            if strategy.severity == severity
        ]
    
    def get_strategies_by_priority(self, min_priority: int = 1) -> List[ErrorRecoveryStrategy]:
        """按优先级获取恢复策略"""
        return sorted(
            [strategy for strategy in self.strategies.values() if strategy.priority >= min_priority],
            key=lambda x: x.priority,
            reverse=True
        )
    
    def export_config(self) -> Dict[str, Any]:
        """导出配置"""
        return {
            error_type: {
                "category": strategy.category.value,
                "severity": strategy.severity.value,
                "retry_enabled": strategy.retry_enabled,
                "retry_strategy": strategy.retry_strategy.value,
                "max_retry_attempts": strategy.max_retry_attempts,
                "initial_retry_delay": strategy.initial_retry_delay,
                "max_retry_delay": strategy.max_retry_delay,
                "retry_backoff_factor": strategy.retry_backoff_factor,
                "recovery_actions": [action.value for action in strategy.recovery_actions],
                "retry_triggers": [trigger.value for trigger in strategy.retry_triggers],
                "custom_handler": strategy.custom_handler,
                "prevention_actions": strategy.prevention_actions,
                "enable_monitoring": strategy.enable_monitoring,
                "alert_threshold": strategy.alert_threshold,
                "timeout": strategy.timeout,
                "requires_user_intervention": strategy.requires_user_intervention,
                "auto_escalate": strategy.auto_escalate,
                "escalation_delay": strategy.escalation_delay,
                "description": strategy.description,
                "tags": strategy.tags,
                "priority": strategy.priority
            }
            for error_type, strategy in self.strategies.items()
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        total_strategies = len(self.strategies)
        
        category_counts = {}
        severity_counts = {}
        retry_enabled_count = 0
        
        for strategy in self.strategies.values():
            # 按分类统计
            category = strategy.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
            
            # 按严重程度统计
            severity = strategy.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # 重试启用统计
            if strategy.retry_enabled:
                retry_enabled_count += 1
        
        return {
            "total_strategies": total_strategies,
            "category_distribution": category_counts,
            "severity_distribution": severity_counts,
            "retry_enabled_count": retry_enabled_count,
            "retry_enabled_percentage": (retry_enabled_count / total_strategies * 100) if total_strategies > 0 else 0
        }


# 全局配置实例
error_recovery_config = ErrorRecoveryConfig()