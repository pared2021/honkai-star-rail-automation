# -*- coding: utf-8 -*-
"""
错误处理和恢复服务 - 统一的错误处理、重试逻辑和异常恢复机制
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import threading
import time
import traceback
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import asyncio
from loguru import logger

from automation.automation_controller import AutomationController
from core.enums import ActionStatus, TaskStatus
from core.exception_recovery import (
    ExceptionInfo,
    ExceptionRecovery,
    ExceptionType,
    RecoveryAction,
    RecoveryResult,
    RecoveryStrategy,
)
from core.game_detector import GameDetector, SceneType
from models.task_models import Task
from services.base_async_service import BaseAsyncService
from src.services.event_bus import EventBus
from utils.helpers import retry_on_exception

# 移除PyQt依赖，使用回调函数替代信号


class ErrorSeverity(Enum):
    """错误严重程度"""

    LOW = "low"  # 轻微错误，可自动恢复
    MEDIUM = "medium"  # 中等错误，需要重试
    HIGH = "high"  # 严重错误，需要人工干预
    CRITICAL = "critical"  # 致命错误，停止所有操作


class RetryPolicy(Enum):
    """重试策略"""

    NONE = "none"  # 不重试
    IMMEDIATE = "immediate"  # 立即重试
    LINEAR = "linear"  # 线性延迟重试
    EXPONENTIAL = "exponential"  # 指数退避重试
    CUSTOM = "custom"  # 自定义重试策略


@dataclass
class ErrorContext:
    """错误上下文信息"""

    error_id: str
    error_type: str
    severity: ErrorSeverity
    timestamp: datetime
    task_id: Optional[str] = None
    action_id: Optional[str] = None
    user_id: Optional[str] = None
    scene: Optional[SceneType] = None
    error_message: str = ""
    stack_trace: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)
    screenshot_path: Optional[str] = None


@dataclass
class RetryConfig:
    """重试配置"""

    policy: RetryPolicy = RetryPolicy.EXPONENTIAL
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: bool = True  # 添加随机抖动
    timeout: Optional[float] = None
    retry_exceptions: Tuple[type, ...] = (Exception,)
    stop_exceptions: Tuple[type, ...] = (KeyboardInterrupt, SystemExit)


@dataclass
class ErrorHandlingResult:
    """错误处理结果"""

    success: bool
    error_context: ErrorContext
    recovery_actions: List[str] = field(default_factory=list)
    retry_count: int = 0
    time_taken: float = 0.0
    final_status: str = ""
    error_message: Optional[str] = None


class ErrorHandlingService(BaseAsyncService):
    """错误处理和恢复服务"""

    def __init__(
        self,
        game_detector: GameDetector,
        automation_controller: AutomationController,
        event_bus: EventBus,
    ):
        BaseAsyncService.__init__(self)

        # 回调函数列表
        self._error_detected_callbacks = []
        self._error_handled_callbacks = []
        self._recovery_started_callbacks = []
        self._recovery_completed_callbacks = []

        self.game_detector = game_detector
        self.automation_controller = automation_controller
        self.event_bus = event_bus

        # 异常恢复系统
        self.exception_recovery = ExceptionRecovery(
            game_detector, automation_controller
        )

        # 错误处理配置
        self.error_contexts: Dict[str, ErrorContext] = {}
        self.retry_configs: Dict[str, RetryConfig] = {}
        self.error_handlers: Dict[str, Callable] = {}
        self.recovery_callbacks: Dict[str, Callable] = {}

        # 统计信息
        self.error_stats = {
            "total_errors": 0,
            "handled_errors": 0,
            "failed_recoveries": 0,
            "retry_attempts": 0,
            "error_types": {},
            "severity_counts": {},
        }

        # 默认重试配置
        self.default_retry_config = RetryConfig()

        # 初始化默认错误处理器
        self._init_default_handlers()

        # 设置异常恢复回调
        self.exception_recovery.set_callbacks(
            exception_detected=self._on_exception_detected,
            recovery_started=self._on_recovery_started,
            recovery_completed=self._on_recovery_completed,
        )

        logger.info("错误处理和恢复服务初始化完成")

    async def start(self) -> bool:
        """启动服务"""
        try:
            self._status = "starting"

            # 注册事件监听器
            self.event_bus.subscribe("task.error", self._handle_task_error)
            self.event_bus.subscribe("action.error", self._handle_action_error)
            self.event_bus.subscribe("automation.error", self._handle_automation_error)

            self._status = "running"
            logger.info("错误处理服务启动成功")
            return True

        except Exception as e:
            self._status = "error"
            logger.error(f"错误处理服务启动失败: {e}")
            return False

    async def stop(self) -> bool:
        """停止服务"""
        try:
            self._status = "stopping"

            # 取消事件监听器
            self.event_bus.unsubscribe("task.error", self._handle_task_error)
            self.event_bus.unsubscribe("action.error", self._handle_action_error)
            self.event_bus.unsubscribe(
                "automation.error", self._handle_automation_error
            )

            self._status = "stopped"
            logger.info("错误处理服务已停止")
            return True

        except Exception as e:
            self._status = "error"
            logger.error(f"错误处理服务停止失败: {e}")
            return False

    async def handle_error(
        self,
        error: Exception,
        context: Dict[str, Any] = None,
        retry_config: Optional[RetryConfig] = None,
    ) -> ErrorHandlingResult:
        """处理错误"""
        start_time = time.time()

        # 创建错误上下文
        error_context = self._create_error_context(error, context or {})

        # 更新统计信息
        self._update_error_stats(error_context)

        # 调用错误检测回调
        for callback in self._error_detected_callbacks:
            try:
                callback(error_context)
            except Exception as e:
                logger.error(f"错误检测回调失败: {e}")

        logger.warning(
            f"处理错误: {error_context.error_type} - {error_context.error_message}"
        )

        try:
            # 获取重试配置
            config = retry_config or self.default_retry_config

            # 检查是否为停止异常
            if isinstance(error, config.stop_exceptions):
                return ErrorHandlingResult(
                    success=False,
                    error_context=error_context,
                    final_status="stopped",
                    error_message="收到停止信号",
                )

            # 执行重试逻辑
            result = await self._execute_with_retry(error_context, config)

            # 如果重试失败，尝试异常恢复
            if not result.success and error_context.severity != ErrorSeverity.LOW:
                recovery_result = await self._attempt_recovery(error_context)
                if recovery_result:
                    result.success = recovery_result.success
                    result.recovery_actions.extend(
                        [action.value for action in recovery_result.actions_taken]
                    )

            result.time_taken = time.time() - start_time

            # 调用处理完成回调
            for callback in self._error_handled_callbacks:
                try:
                    callback(result)
                except Exception as e:
                    logger.error(f"错误处理回调失败: {e}")

            return result

        except Exception as e:
            logger.error(f"错误处理过程中出现异常: {e}")
            return ErrorHandlingResult(
                success=False,
                error_context=error_context,
                time_taken=time.time() - start_time,
                error_message=f"处理过程异常: {str(e)}",
            )

    async def _execute_with_retry(
        self, error_context: ErrorContext, config: RetryConfig
    ) -> ErrorHandlingResult:
        """执行重试逻辑"""
        if config.policy == RetryPolicy.NONE:
            return ErrorHandlingResult(
                success=False, error_context=error_context, final_status="no_retry"
            )

        retry_count = 0
        last_error = None
        delay = config.initial_delay

        for attempt in range(config.max_attempts):
            try:
                # 获取错误处理器
                handler = self.error_handlers.get(
                    error_context.error_type, self._default_error_handler
                )

                # 执行处理器
                success = await handler(error_context)

                if success:
                    return ErrorHandlingResult(
                        success=True,
                        error_context=error_context,
                        retry_count=retry_count,
                        final_status="recovered",
                    )

            except Exception as e:
                last_error = e
                logger.warning(f"重试第{attempt + 1}次失败: {e}")

            retry_count += 1
            self.error_stats["retry_attempts"] += 1

            # 如果不是最后一次尝试，等待后重试
            if attempt < config.max_attempts - 1:
                await self._wait_for_retry(delay, config)
                delay = self._calculate_next_delay(delay, config)

        return ErrorHandlingResult(
            success=False,
            error_context=error_context,
            retry_count=retry_count,
            final_status="retry_exhausted",
            error_message=str(last_error) if last_error else "重试次数用尽",
        )

    async def _attempt_recovery(
        self, error_context: ErrorContext
    ) -> Optional[RecoveryResult]:
        """尝试异常恢复"""
        try:
            # 将错误上下文转换为异常信息
            exception_info = ExceptionInfo(
                exception_type=self._map_error_to_exception_type(
                    error_context.error_type
                ),
                description=error_context.error_message,
                timestamp=error_context.timestamp,
                task_id=error_context.task_id,
                scene=error_context.scene,
                error_details=error_context.additional_data,
                screenshot_path=error_context.screenshot_path,
            )

            # 执行异常恢复
            recovery_result = self.exception_recovery.handle_exception(exception_info)

            return recovery_result

        except Exception as e:
            logger.error(f"异常恢复失败: {e}")
            return None

    def _create_error_context(
        self, error: Exception, context: Dict[str, Any]
    ) -> ErrorContext:
        """创建错误上下文"""
        error_id = f"error_{int(time.time() * 1000)}"
        error_type = type(error).__name__

        # 确定错误严重程度
        severity = self._determine_error_severity(error, context)

        error_context = ErrorContext(
            error_id=error_id,
            error_type=error_type,
            severity=severity,
            timestamp=datetime.now(),
            task_id=context.get("task_id"),
            action_id=context.get("action_id"),
            user_id=context.get("user_id"),
            scene=context.get("scene"),
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            additional_data=context,
        )

        # 保存错误上下文
        self.error_contexts[error_id] = error_context

        return error_context

    def _determine_error_severity(
        self, error: Exception, context: Dict[str, Any]
    ) -> ErrorSeverity:
        """确定错误严重程度"""
        # 根据异常类型确定严重程度
        if isinstance(error, (KeyboardInterrupt, SystemExit)):
            return ErrorSeverity.CRITICAL

        if isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorSeverity.MEDIUM

        if isinstance(error, (ValueError, TypeError)):
            return ErrorSeverity.LOW

        # 根据上下文确定严重程度
        if context.get("critical", False):
            return ErrorSeverity.CRITICAL

        if context.get("task_id"):
            return ErrorSeverity.MEDIUM

        return ErrorSeverity.LOW

    def _map_error_to_exception_type(self, error_type: str) -> ExceptionType:
        """将错误类型映射到异常类型"""
        mapping = {
            "ConnectionError": ExceptionType.NETWORK_ERROR,
            "TimeoutError": ExceptionType.OPERATION_TIMEOUT,
            "GameNotFoundError": ExceptionType.GAME_CRASH,
            "UIElementNotFoundError": ExceptionType.UI_NOT_FOUND,
            "UnexpectedSceneError": ExceptionType.UNEXPECTED_SCENE,
        }

        return mapping.get(error_type, ExceptionType.UNKNOWN_ERROR)

    async def _wait_for_retry(self, delay: float, config: RetryConfig):
        """等待重试"""
        actual_delay = delay

        # 添加随机抖动
        if config.jitter:
            import random

            jitter = random.uniform(0.1, 0.3) * delay
            actual_delay += jitter

        # 限制最大延迟
        actual_delay = min(actual_delay, config.max_delay)

        await asyncio.sleep(actual_delay)

    def _calculate_next_delay(self, current_delay: float, config: RetryConfig) -> float:
        """计算下一次重试延迟"""
        if config.policy == RetryPolicy.LINEAR:
            return current_delay + config.initial_delay
        elif config.policy == RetryPolicy.EXPONENTIAL:
            return current_delay * config.backoff_factor
        else:
            return current_delay

    def _update_error_stats(self, error_context: ErrorContext):
        """更新错误统计信息"""
        self.error_stats["total_errors"] += 1

        # 按错误类型统计
        error_type = error_context.error_type
        self.error_stats["error_types"][error_type] = (
            self.error_stats["error_types"].get(error_type, 0) + 1
        )

        # 按严重程度统计
        severity = error_context.severity.value
        self.error_stats["severity_counts"][severity] = (
            self.error_stats["severity_counts"].get(severity, 0) + 1
        )

    def _init_default_handlers(self):
        """初始化默认错误处理器"""
        self.error_handlers.update(
            {
                "ConnectionError": self._handle_connection_error,
                "TimeoutError": self._handle_timeout_error,
                "GameNotFoundError": self._handle_game_not_found_error,
                "UIElementNotFoundError": self._handle_ui_not_found_error,
            }
        )

    async def _default_error_handler(self, error_context: ErrorContext) -> bool:
        """默认错误处理器"""
        logger.info(f"使用默认处理器处理错误: {error_context.error_type}")

        # 简单的等待重试
        await asyncio.sleep(1.0)
        return False

    async def _handle_connection_error(self, error_context: ErrorContext) -> bool:
        """处理连接错误"""
        logger.info("处理连接错误")

        # 等待网络恢复
        await asyncio.sleep(5.0)

        # 检查网络连接
        # 这里可以添加网络检测逻辑
        return True

    async def _handle_timeout_error(self, error_context: ErrorContext) -> bool:
        """处理超时错误"""
        logger.info("处理超时错误")

        # 增加超时时间后重试
        await asyncio.sleep(2.0)
        return True

    async def _handle_game_not_found_error(self, error_context: ErrorContext) -> bool:
        """处理游戏未找到错误"""
        logger.info("处理游戏未找到错误")

        # 尝试重新检测游戏
        return self.game_detector.is_game_running()

    async def _handle_ui_not_found_error(self, error_context: ErrorContext) -> bool:
        """处理UI元素未找到错误"""
        logger.info("处理UI元素未找到错误")

        # 等待UI加载
        await asyncio.sleep(3.0)
        return True

    # 事件处理器
    async def _handle_task_error(self, event_data: Dict[str, Any]):
        """处理任务错误事件"""
        error = event_data.get("error")
        context = event_data.get("context", {})

        if error:
            await self.handle_error(error, context)

    async def _handle_action_error(self, event_data: Dict[str, Any]):
        """处理动作错误事件"""
        error = event_data.get("error")
        context = event_data.get("context", {})

        if error:
            await self.handle_error(error, context)

    async def _handle_automation_error(self, event_data: Dict[str, Any]):
        """处理自动化错误事件"""
        error = event_data.get("error")
        context = event_data.get("context", {})

        if error:
            await self.handle_error(error, context)

    # 异常恢复回调
    def _on_exception_detected(self, exception_info: ExceptionInfo):
        """异常检测回调"""
        logger.info(f"检测到异常: {exception_info.exception_type.value}")

    def _on_recovery_started(self, strategy, exception_info: ExceptionInfo):
        """恢复开始回调"""
        error_id = f"recovery_{int(time.time() * 1000)}"
        action = strategy.actions[0].value if strategy.actions else "unknown"

        for callback in self._recovery_started_callbacks:
            try:
                callback(error_id, action)
            except Exception as e:
                logger.error(f"恢复开始回调失败: {e}")
        logger.info(f"开始异常恢复: {action}")

    def _on_recovery_completed(self, result: RecoveryResult):
        """恢复完成回调"""
        error_id = f"recovery_{int(time.time() * 1000)}"

        for callback in self._recovery_completed_callbacks:
            try:
                callback(error_id, result.success)
            except Exception as e:
                logger.error(f"恢复完成回调失败: {e}")

        if result.success:
            self.error_stats["handled_errors"] += 1
            logger.info(f"异常恢复成功，耗时 {result.time_taken:.2f} 秒")
        else:
            self.error_stats["failed_recoveries"] += 1
            logger.error(f"异常恢复失败: {result.error_message}")

    # 公共接口
    def register_error_detected_callback(self, callback: Callable):
        """注册错误检测回调"""
        self._error_detected_callbacks.append(callback)

    def register_error_handled_callback(self, callback: Callable):
        """注册错误处理回调"""
        self._error_handled_callbacks.append(callback)

    def register_recovery_started_callback(self, callback: Callable):
        """注册恢复开始回调"""
        self._recovery_started_callbacks.append(callback)

    def register_recovery_completed_callback(self, callback: Callable):
        """注册恢复完成回调"""
        self._recovery_completed_callbacks.append(callback)

    def register_error_handler(self, error_type: str, handler: Callable):
        """注册错误处理器"""
        self.error_handlers[error_type] = handler
        logger.info(f"已注册错误处理器: {error_type}")

    def set_retry_config(self, error_type: str, config: RetryConfig):
        """设置重试配置"""
        self.retry_configs[error_type] = config
        logger.info(f"已设置重试配置: {error_type}")

    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        return self.error_stats.copy()

    def get_recent_errors(self, limit: int = 10) -> List[ErrorContext]:
        """获取最近的错误"""
        sorted_errors = sorted(
            self.error_contexts.values(), key=lambda x: x.timestamp, reverse=True
        )
        return sorted_errors[:limit]

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "status": self._status,
            "error_count": self.error_stats["total_errors"],
            "recovery_rate": (
                self.error_stats["handled_errors"]
                / max(self.error_stats["total_errors"], 1)
            ),
            "exception_recovery_available": self.exception_recovery is not None,
        }
