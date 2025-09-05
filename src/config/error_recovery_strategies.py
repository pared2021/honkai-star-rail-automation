"""错误恢复策略配置模块。

定义错误恢复的策略配置。
"""

from enum import Enum
from typing import Any, Dict, Optional


class RecoveryStrategy(Enum):
    """恢复策略枚举。"""

    RETRY = "retry"
    FALLBACK = "fallback"
    IGNORE = "ignore"
    ABORT = "abort"


class ErrorRecoveryStrategies:
    """错误恢复策略配置类。"""

    def __init__(self):
        """初始化错误恢复策略。"""
        self._strategies: Dict[str, RecoveryStrategy] = {
            "connection_error": RecoveryStrategy.RETRY,
            "timeout_error": RecoveryStrategy.RETRY,
            "validation_error": RecoveryStrategy.IGNORE,
            "critical_error": RecoveryStrategy.ABORT,
            "default": RecoveryStrategy.FALLBACK,
        }

        self._retry_configs: Dict[str, Dict[str, Any]] = {
            "connection_error": {"max_retries": 3, "delay": 1.0},
            "timeout_error": {"max_retries": 2, "delay": 0.5},
            "default": {"max_retries": 1, "delay": 0.1},
        }

    def get_strategy(self, error_type: str) -> RecoveryStrategy:
        """获取指定错误类型的恢复策略。

        Args:
            error_type: 错误类型

        Returns:
            RecoveryStrategy: 恢复策略
        """
        return self._strategies.get(error_type, self._strategies["default"])

    def get_retry_config(self, error_type: str) -> Dict[str, Any]:
        """获取重试配置。

        Args:
            error_type: 错误类型

        Returns:
            Dict[str, Any]: 重试配置
        """
        return self._retry_configs.get(error_type, self._retry_configs["default"])

    def set_strategy(self, error_type: str, strategy: RecoveryStrategy) -> None:
        """设置错误恢复策略。

        Args:
            error_type: 错误类型
            strategy: 恢复策略
        """
        self._strategies[error_type] = strategy

    def set_retry_config(self, error_type: str, max_retries: int, delay: float) -> None:
        """设置重试配置。

        Args:
            error_type: 错误类型
            max_retries: 最大重试次数
            delay: 重试延迟（秒）
        """
        self._retry_configs[error_type] = {"max_retries": max_retries, "delay": delay}
