"""错误处理和重试机制

提供完善的异常分类、重试策略、错误恢复和日志记录功能。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging
import random
import time
import traceback
from typing import Any, Callable, Dict, List, Optional, Type, Union

import asyncio

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """错误严重程度"""

    LOW = "low"  # 轻微错误，可以忽略
    MEDIUM = "medium"  # 中等错误，需要重试
    HIGH = "high"  # 严重错误，需要人工干预
    CRITICAL = "critical"  # 致命错误，系统无法继续


class ErrorCategory(Enum):
    """错误分类"""

    NETWORK = "network"  # 网络相关错误
    DATABASE = "database"  # 数据库相关错误
    AUTOMATION = "automation"  # 自动化操作错误
    VALIDATION = "validation"  # 数据验证错误
    PERMISSION = "permission"  # 权限相关错误
    RESOURCE = "resource"  # 资源相关错误
    TIMEOUT = "timeout"  # 超时错误
    CONFIGURATION = "configuration"  # 配置错误
    EXTERNAL_API = "external_api"  # 外部API错误
    SYSTEM = "system"  # 系统错误
    UNKNOWN = "unknown"  # 未知错误


@dataclass
class ErrorContext:
    """错误上下文信息"""

    error: Exception
    severity: ErrorSeverity
    category: ErrorCategory
    timestamp: datetime
    operation: str
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def can_retry(self) -> bool:
        """是否可以重试"""
        return self.retry_count < self.max_retries and self.severity in [
            ErrorSeverity.LOW,
            ErrorSeverity.MEDIUM,
        ]

    @property
    def error_message(self) -> str:
        """获取错误消息"""
        return str(self.error)

    @property
    def error_type(self) -> str:
        """获取错误类型"""
        return self.error.__class__.__name__

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "error_type": self.error_type,
            "error_message": self.error_message,
            "severity": self.severity.value,
            "category": self.category.value,
            "timestamp": self.timestamp.isoformat(),
            "operation": self.operation,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "can_retry": self.can_retry,
            "metadata": self.metadata,
            "traceback": traceback.format_exception(
                type(self.error), self.error, self.error.__traceback__
            ),
        }


class ErrorClassifier:
    """错误分类器

    根据异常类型和消息内容自动分类错误。
    """

    def __init__(self):
        # 错误类型映射
        self._type_mappings: Dict[
            Type[Exception], tuple[ErrorSeverity, ErrorCategory]
        ] = {
            # 网络错误
            ConnectionError: (ErrorSeverity.MEDIUM, ErrorCategory.NETWORK),
            TimeoutError: (ErrorSeverity.MEDIUM, ErrorCategory.TIMEOUT),
            OSError: (ErrorSeverity.MEDIUM, ErrorCategory.NETWORK),
            # 数据库错误
            # sqlite3.Error: (ErrorSeverity.HIGH, ErrorCategory.DATABASE),
            # 验证错误
            ValueError: (ErrorSeverity.LOW, ErrorCategory.VALIDATION),
            TypeError: (ErrorSeverity.MEDIUM, ErrorCategory.VALIDATION),
            # 权限错误
            PermissionError: (ErrorSeverity.HIGH, ErrorCategory.PERMISSION),
            # 资源错误
            FileNotFoundError: (ErrorSeverity.MEDIUM, ErrorCategory.RESOURCE),
            MemoryError: (ErrorSeverity.CRITICAL, ErrorCategory.RESOURCE),
            # 系统错误
            SystemError: (ErrorSeverity.CRITICAL, ErrorCategory.SYSTEM),
            KeyboardInterrupt: (ErrorSeverity.HIGH, ErrorCategory.SYSTEM),
        }

        # 消息模式映射
        self._message_patterns: List[tuple[str, ErrorSeverity, ErrorCategory]] = [
            # 网络相关
            ("connection", ErrorSeverity.MEDIUM, ErrorCategory.NETWORK),
            ("network", ErrorSeverity.MEDIUM, ErrorCategory.NETWORK),
            ("timeout", ErrorSeverity.MEDIUM, ErrorCategory.TIMEOUT),
            ("dns", ErrorSeverity.MEDIUM, ErrorCategory.NETWORK),
            # 数据库相关
            ("database", ErrorSeverity.HIGH, ErrorCategory.DATABASE),
            ("sql", ErrorSeverity.HIGH, ErrorCategory.DATABASE),
            ("constraint", ErrorSeverity.MEDIUM, ErrorCategory.DATABASE),
            # 自动化相关
            ("window", ErrorSeverity.MEDIUM, ErrorCategory.AUTOMATION),
            ("element", ErrorSeverity.MEDIUM, ErrorCategory.AUTOMATION),
            ("screenshot", ErrorSeverity.LOW, ErrorCategory.AUTOMATION),
            ("click", ErrorSeverity.MEDIUM, ErrorCategory.AUTOMATION),
            # 配置相关
            ("config", ErrorSeverity.HIGH, ErrorCategory.CONFIGURATION),
            ("setting", ErrorSeverity.HIGH, ErrorCategory.CONFIGURATION),
            # API相关
            ("api", ErrorSeverity.MEDIUM, ErrorCategory.EXTERNAL_API),
            ("http", ErrorSeverity.MEDIUM, ErrorCategory.EXTERNAL_API),
            ("response", ErrorSeverity.MEDIUM, ErrorCategory.EXTERNAL_API),
        ]

    def classify(
        self, error: Exception, operation: str = ""
    ) -> tuple[ErrorSeverity, ErrorCategory]:
        """分类错误

        Args:
            error: 异常对象
            operation: 操作名称

        Returns:
            (严重程度, 错误分类)
        """
        # 首先检查异常类型
        error_type = type(error)
        if error_type in self._type_mappings:
            return self._type_mappings[error_type]

        # 检查父类类型
        for exc_type, (severity, category) in self._type_mappings.items():
            if isinstance(error, exc_type):
                return severity, category

        # 检查错误消息模式
        error_message = str(error).lower()
        operation_lower = operation.lower()

        for pattern, severity, category in self._message_patterns:
            if pattern in error_message or pattern in operation_lower:
                return severity, category

        # 默认分类
        return ErrorSeverity.MEDIUM, ErrorCategory.UNKNOWN

    def create_context(
        self,
        error: Exception,
        operation: str,
        max_retries: int = 3,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ErrorContext:
        """创建错误上下文"""
        severity, category = self.classify(error, operation)

        return ErrorContext(
            error=error,
            severity=severity,
            category=category,
            timestamp=datetime.now(),
            operation=operation,
            max_retries=max_retries,
            metadata=metadata or {},
        )


class RetryStrategy(ABC):
    """重试策略基类"""

    @abstractmethod
    def should_retry(self, context: ErrorContext) -> bool:
        """判断是否应该重试"""
        pass

    @abstractmethod
    def get_delay(self, context: ErrorContext) -> float:
        """获取重试延迟时间（秒）"""
        pass

    @abstractmethod
    def on_retry(self, context: ErrorContext) -> None:
        """重试前的回调"""
        pass


class ExponentialBackoffStrategy(RetryStrategy):
    """指数退避重试策略"""

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        jitter_range: float = 0.1,
    ):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.jitter_range = jitter_range

    def should_retry(self, context: ErrorContext) -> bool:
        """判断是否应该重试"""
        return context.can_retry

    def get_delay(self, context: ErrorContext) -> float:
        """获取重试延迟时间"""
        # 计算基础延迟
        delay = self.base_delay * (self.exponential_base**context.retry_count)
        delay = min(delay, self.max_delay)

        # 添加抖动
        if self.jitter:
            jitter_amount = delay * self.jitter_range
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)

    def on_retry(self, context: ErrorContext) -> None:
        """重试前的回调"""
        logger.warning(
            f"重试操作 '{context.operation}' ({context.retry_count + 1}/{context.max_retries}): "
            f"{context.error_type}: {context.error_message}"
        )


class LinearBackoffStrategy(RetryStrategy):
    """线性退避重试策略"""

    def __init__(
        self,
        base_delay: float = 1.0,
        increment: float = 1.0,
        max_delay: float = 30.0,
        jitter: bool = True,
    ):
        self.base_delay = base_delay
        self.increment = increment
        self.max_delay = max_delay
        self.jitter = jitter

    def should_retry(self, context: ErrorContext) -> bool:
        """判断是否应该重试"""
        return context.can_retry

    def get_delay(self, context: ErrorContext) -> float:
        """获取重试延迟时间"""
        delay = self.base_delay + (self.increment * context.retry_count)
        delay = min(delay, self.max_delay)

        if self.jitter:
            delay *= 0.8 + random.random() * 0.4  # ±20%的抖动

        return delay

    def on_retry(self, context: ErrorContext) -> None:
        """重试前的回调"""
        logger.info(
            f"线性重试 '{context.operation}' ({context.retry_count + 1}/{context.max_retries})"
        )


class FixedDelayStrategy(RetryStrategy):
    """固定延迟重试策略"""

    def __init__(self, delay: float = 1.0, jitter: bool = False):
        self.delay = delay
        self.jitter = jitter

    def should_retry(self, context: ErrorContext) -> bool:
        """判断是否应该重试"""
        return context.can_retry

    def get_delay(self, context: ErrorContext) -> float:
        """获取重试延迟时间"""
        delay = self.delay

        if self.jitter:
            delay *= 0.5 + random.random()  # 50%-150%的抖动

        return delay

    def on_retry(self, context: ErrorContext) -> None:
        """重试前的回调"""
        logger.debug(f"固定延迟重试 '{context.operation}'")


class ErrorRecoveryHandler(ABC):
    """错误恢复处理器基类"""

    @abstractmethod
    def can_handle(self, context: ErrorContext) -> bool:
        """判断是否可以处理该错误"""
        pass

    @abstractmethod
    async def handle(self, context: ErrorContext) -> bool:
        """处理错误恢复

        Returns:
            是否恢复成功
        """
        pass


class DatabaseRecoveryHandler(ErrorRecoveryHandler):
    """数据库错误恢复处理器"""

    def can_handle(self, context: ErrorContext) -> bool:
        """判断是否可以处理该错误"""
        return context.category == ErrorCategory.DATABASE

    async def handle(self, context: ErrorContext) -> bool:
        """处理数据库错误恢复"""
        try:
            # 检查数据库连接
            logger.info("尝试恢复数据库连接...")

            # 这里可以添加具体的数据库恢复逻辑
            # 例如：重新连接、检查表结构、修复索引等

            await asyncio.sleep(1.0)  # 模拟恢复过程

            logger.info("数据库连接恢复成功")
            return True

        except Exception as e:
            logger.error(f"数据库恢复失败: {e}")
            return False


class NetworkRecoveryHandler(ErrorRecoveryHandler):
    """网络错误恢复处理器"""

    def can_handle(self, context: ErrorContext) -> bool:
        """判断是否可以处理该错误"""
        return context.category == ErrorCategory.NETWORK

    async def handle(self, context: ErrorContext) -> bool:
        """处理网络错误恢复"""
        try:
            logger.info("检查网络连接...")

            # 这里可以添加网络检查逻辑
            # 例如：ping测试、DNS解析检查等

            await asyncio.sleep(0.5)  # 模拟检查过程

            logger.info("网络连接正常")
            return True

        except Exception as e:
            logger.error(f"网络检查失败: {e}")
            return False


class ErrorHandler:
    """错误处理器

    统一的错误处理、重试和恢复机制。
    """

    def __init__(
        self,
        classifier: Optional[ErrorClassifier] = None,
        default_strategy: Optional[RetryStrategy] = None,
    ):
        self.classifier = classifier or ErrorClassifier()
        self.default_strategy = default_strategy or ExponentialBackoffStrategy()

        # 策略映射
        self._strategies: Dict[ErrorCategory, RetryStrategy] = {
            ErrorCategory.NETWORK: ExponentialBackoffStrategy(
                base_delay=2.0, max_delay=30.0
            ),
            ErrorCategory.DATABASE: ExponentialBackoffStrategy(
                base_delay=1.0, max_delay=10.0
            ),
            ErrorCategory.AUTOMATION: LinearBackoffStrategy(
                base_delay=0.5, increment=0.5
            ),
            ErrorCategory.TIMEOUT: FixedDelayStrategy(delay=5.0),
            ErrorCategory.EXTERNAL_API: ExponentialBackoffStrategy(
                base_delay=3.0, max_delay=60.0
            ),
        }

        # 恢复处理器
        self._recovery_handlers: List[ErrorRecoveryHandler] = [
            DatabaseRecoveryHandler(),
            NetworkRecoveryHandler(),
        ]

    def add_strategy(self, category: ErrorCategory, strategy: RetryStrategy):
        """添加重试策略"""
        self._strategies[category] = strategy

    def add_recovery_handler(self, handler: ErrorRecoveryHandler):
        """添加恢复处理器"""
        self._recovery_handlers.append(handler)

    async def handle_with_retry(
        self,
        operation: Callable,
        operation_name: str,
        max_retries: int = 3,
        metadata: Optional[Dict[str, Any]] = None,
        *args,
        **kwargs,
    ) -> Any:
        """带重试的操作执行

        Args:
            operation: 要执行的操作
            operation_name: 操作名称
            max_retries: 最大重试次数
            metadata: 元数据
            *args: 操作参数
            **kwargs: 操作关键字参数

        Returns:
            操作结果

        Raises:
            最后一次执行的异常
        """
        context = None

        for attempt in range(max_retries + 1):
            try:
                # 执行操作
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args, **kwargs)
                else:
                    result = operation(*args, **kwargs)

                # 成功执行
                if context and context.retry_count > 0:
                    logger.info(f"操作 '{operation_name}' 重试成功")

                return result

            except Exception as e:
                # 创建或更新错误上下文
                if context is None:
                    context = self.classifier.create_context(
                        e, operation_name, max_retries, metadata
                    )
                else:
                    context.error = e
                    context.retry_count = attempt

                # 记录错误
                self._log_error(context)

                # 检查是否是最后一次尝试
                if attempt >= max_retries:
                    logger.error(
                        f"操作 '{operation_name}' 最终失败，已达到最大重试次数"
                    )
                    raise e

                # 获取重试策略
                strategy = self._strategies.get(context.category, self.default_strategy)

                # 检查是否应该重试
                if not strategy.should_retry(context):
                    logger.error(f"操作 '{operation_name}' 不应重试")
                    raise e

                # 尝试错误恢复
                await self._attempt_recovery(context)

                # 执行重试前回调
                strategy.on_retry(context)

                # 等待重试延迟
                delay = strategy.get_delay(context)
                if delay > 0:
                    await asyncio.sleep(delay)

        # 理论上不会到达这里
        raise RuntimeError(f"操作 '{operation_name}' 执行失败")

    async def _attempt_recovery(self, context: ErrorContext) -> bool:
        """尝试错误恢复"""
        for handler in self._recovery_handlers:
            if handler.can_handle(context):
                try:
                    success = await handler.handle(context)
                    if success:
                        logger.info(f"错误恢复成功: {context.category.value}")
                        return True
                except Exception as e:
                    logger.error(f"错误恢复处理器失败: {e}")

        return False

    def _log_error(self, context: ErrorContext):
        """记录错误日志"""
        log_level = {
            ErrorSeverity.LOW: logging.DEBUG,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL,
        }.get(context.severity, logging.ERROR)

        logger.log(
            log_level,
            f"错误 [{context.severity.value}] {context.operation}: "
            f"{context.error_type}: {context.error_message}",
        )

        # 详细错误信息（仅在DEBUG级别）
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"错误详情: {context.to_dict()}")


# 全局错误处理器实例
default_error_handler = ErrorHandler()


def with_error_handling(
    operation_name: str, max_retries: int = 3, metadata: Optional[Dict[str, Any]] = None
):
    """错误处理装饰器

    Args:
        operation_name: 操作名称
        max_retries: 最大重试次数
        metadata: 元数据
    """

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            return await default_error_handler.handle_with_retry(
                func, operation_name, max_retries, metadata, *args, **kwargs
            )

        def sync_wrapper(*args, **kwargs):
            return asyncio.run(
                default_error_handler.handle_with_retry(
                    func, operation_name, max_retries, metadata, *args, **kwargs
                )
            )

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
