# -*- coding: utf-8 -*-
"""
任务重试管理器 - 专门处理任务级别的重试逻辑和策略
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from PyQt5.QtCore import QObject, pyqtSignal
import asyncio
from loguru import logger

from core.enums import ActionStatus, TaskStatus
from models.task_models import Task
from utils.helpers import retry_on_exception


class RetryTrigger(Enum):
    """重试触发条件"""

    TASK_FAILED = "task_failed"  # 任务失败
    ACTION_FAILED = "action_failed"  # 动作失败
    TIMEOUT = "timeout"  # 超时
    NETWORK_ERROR = "network_error"  # 网络错误
    GAME_CRASH = "game_crash"  # 游戏崩溃
    UI_NOT_FOUND = "ui_not_found"  # UI未找到
    UNEXPECTED_SCENE = "unexpected_scene"  # 意外场景
    MANUAL = "manual"  # 手动触发


class RetryStrategy(Enum):
    """重试策略"""

    IMMEDIATE = "immediate"  # 立即重试
    FIXED_DELAY = "fixed_delay"  # 固定延迟
    LINEAR_BACKOFF = "linear_backoff"  # 线性退避
    EXPONENTIAL_BACKOFF = "exponential_backoff"  # 指数退避
    FIBONACCI = "fibonacci"  # 斐波那契序列
    CUSTOM = "custom"  # 自定义策略


@dataclass
class RetryConfiguration:
    """重试配置"""

    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 300.0  # 5分钟
    backoff_multiplier: float = 2.0
    jitter: bool = True
    timeout_per_attempt: Optional[float] = None

    # 触发条件配置
    triggers: List[RetryTrigger] = field(
        default_factory=lambda: [
            RetryTrigger.TASK_FAILED,
            RetryTrigger.ACTION_FAILED,
            RetryTrigger.TIMEOUT,
        ]
    )

    # 停止条件
    stop_on_success: bool = True
    stop_on_critical_error: bool = True

    # 自定义延迟函数
    custom_delay_func: Optional[Callable[[int], float]] = None


@dataclass
class RetryAttempt:
    """重试尝试记录"""

    attempt_number: int
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    error_message: Optional[str] = None
    delay_before: float = 0.0
    trigger: Optional[RetryTrigger] = None
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskRetryContext:
    """任务重试上下文"""

    task_id: str
    task_name: str
    user_id: Optional[str]
    configuration: RetryConfiguration
    attempts: List[RetryAttempt] = field(default_factory=list)
    total_attempts: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    last_attempt_time: Optional[datetime] = None
    next_retry_time: Optional[datetime] = None
    is_active: bool = True
    final_result: Optional[bool] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskRetryManager(QObject):
    """任务重试管理器"""

    # 信号定义
    retry_scheduled = pyqtSignal(str, int, float)  # task_id, attempt_number, delay
    retry_started = pyqtSignal(str, int)  # task_id, attempt_number
    retry_completed = pyqtSignal(str, int, bool)  # task_id, attempt_number, success
    retry_exhausted = pyqtSignal(str, int)  # task_id, total_attempts
    retry_cancelled = pyqtSignal(str, str)  # task_id, reason

    def __init__(self):
        super().__init__()

        # 重试上下文存储
        self.retry_contexts: Dict[str, TaskRetryContext] = {}

        # 默认配置
        self.default_config = RetryConfiguration()

        # 任务特定配置
        self.task_configs: Dict[str, RetryConfiguration] = {}

        # 重试队列和调度器
        self.retry_queue: List[Tuple[str, datetime]] = []  # (task_id, retry_time)
        self.scheduler_running = False
        self.scheduler_thread: Optional[threading.Thread] = None

        # 统计信息
        self.stats = {
            "total_retries": 0,
            "successful_retries": 0,
            "failed_retries": 0,
            "cancelled_retries": 0,
            "average_attempts": 0.0,
            "trigger_counts": {},
            "strategy_usage": {},
        }

        # 启动调度器
        self.start_scheduler()

        logger.info("任务重试管理器初始化完成")

    def start_scheduler(self):
        """启动重试调度器"""
        if not self.scheduler_running:
            self.scheduler_running = True
            self.scheduler_thread = threading.Thread(
                target=self._scheduler_loop, daemon=True
            )
            self.scheduler_thread.start()
            logger.info("重试调度器已启动")

    def stop_scheduler(self):
        """停止重试调度器"""
        self.scheduler_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5.0)
        logger.info("重试调度器已停止")

    def schedule_retry(
        self,
        task_id: str,
        task_name: str,
        trigger: RetryTrigger,
        error_message: Optional[str] = None,
        user_id: Optional[str] = None,
        config: Optional[RetryConfiguration] = None,
        context: Dict[str, Any] = None,
    ) -> bool:
        """调度任务重试"""
        try:
            # 获取或创建重试上下文
            retry_context = self._get_or_create_context(
                task_id, task_name, user_id, config
            )

            # 检查是否可以重试
            if not self._can_retry(retry_context, trigger):
                logger.warning(f"任务 {task_id} 不能重试")
                return False

            # 计算延迟时间
            delay = self._calculate_delay(retry_context)

            # 创建重试尝试记录
            attempt = RetryAttempt(
                attempt_number=retry_context.total_attempts + 1,
                start_time=datetime.now(),
                trigger=trigger,
                delay_before=delay,
                context=context or {},
            )

            if error_message:
                attempt.error_message = error_message

            # 更新重试上下文
            retry_context.attempts.append(attempt)
            retry_context.total_attempts += 1
            retry_context.next_retry_time = datetime.now() + timedelta(seconds=delay)

            # 添加到重试队列
            self.retry_queue.append((task_id, retry_context.next_retry_time))
            self.retry_queue.sort(key=lambda x: x[1])  # 按时间排序

            # 更新统计信息
            self._update_stats(trigger, retry_context.configuration.strategy)

            # 发送调度信号
            self.retry_scheduled.emit(task_id, attempt.attempt_number, delay)

            logger.info(
                f"已调度任务 {task_id} 重试，第 {attempt.attempt_number} 次尝试，延迟 {delay:.2f} 秒"
            )
            return True

        except Exception as e:
            logger.error(f"调度任务重试失败: {e}")
            return False

    def cancel_retry(self, task_id: str, reason: str = "用户取消") -> bool:
        """取消任务重试"""
        try:
            # 从队列中移除
            self.retry_queue = [
                (tid, time) for tid, time in self.retry_queue if tid != task_id
            ]

            # 更新上下文状态
            if task_id in self.retry_contexts:
                context = self.retry_contexts[task_id]
                context.is_active = False
                context.final_result = False

            # 更新统计
            self.stats["cancelled_retries"] += 1

            # 发送取消信号
            self.retry_cancelled.emit(task_id, reason)

            logger.info(f"已取消任务 {task_id} 的重试: {reason}")
            return True

        except Exception as e:
            logger.error(f"取消任务重试失败: {e}")
            return False

    def mark_retry_result(
        self, task_id: str, success: bool, error_message: Optional[str] = None
    ):
        """标记重试结果"""
        if task_id not in self.retry_contexts:
            return

        context = self.retry_contexts[task_id]

        if context.attempts:
            current_attempt = context.attempts[-1]
            current_attempt.end_time = datetime.now()
            current_attempt.success = success

            if error_message:
                current_attempt.error_message = error_message

            # 发送完成信号
            self.retry_completed.emit(task_id, current_attempt.attempt_number, success)

            if success:
                # 重试成功，停止后续重试
                context.is_active = False
                context.final_result = True
                self.stats["successful_retries"] += 1

                # 从队列中移除
                self.retry_queue = [
                    (tid, time) for tid, time in self.retry_queue if tid != task_id
                ]

                logger.info(f"任务 {task_id} 重试成功")

            elif context.total_attempts >= context.configuration.max_attempts:
                # 重试次数用尽
                context.is_active = False
                context.final_result = False
                self.stats["failed_retries"] += 1

                # 从队列中移除
                self.retry_queue = [
                    (tid, time) for tid, time in self.retry_queue if tid != task_id
                ]

                # 发送重试用尽信号
                self.retry_exhausted.emit(task_id, context.total_attempts)

                logger.warning(
                    f"任务 {task_id} 重试次数用尽，共尝试 {context.total_attempts} 次"
                )

    def get_retry_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务重试状态"""
        if task_id not in self.retry_contexts:
            return None

        context = self.retry_contexts[task_id]

        return {
            "task_id": task_id,
            "task_name": context.task_name,
            "total_attempts": context.total_attempts,
            "max_attempts": context.configuration.max_attempts,
            "is_active": context.is_active,
            "next_retry_time": (
                context.next_retry_time.isoformat() if context.next_retry_time else None
            ),
            "final_result": context.final_result,
            "last_error": (
                context.attempts[-1].error_message if context.attempts else None
            ),
            "strategy": context.configuration.strategy.value,
            "triggers": [t.value for t in context.configuration.triggers],
        }

    def get_all_retry_status(self) -> List[Dict[str, Any]]:
        """获取所有任务的重试状态"""
        return [
            self.get_retry_status(task_id) for task_id in self.retry_contexts.keys()
        ]

    def set_task_config(self, task_id: str, config: RetryConfiguration):
        """设置任务特定的重试配置"""
        self.task_configs[task_id] = config
        logger.info(f"已设置任务 {task_id} 的重试配置")

    def get_statistics(self) -> Dict[str, Any]:
        """获取重试统计信息"""
        # 计算平均尝试次数
        total_contexts = len(self.retry_contexts)
        if total_contexts > 0:
            total_attempts = sum(
                ctx.total_attempts for ctx in self.retry_contexts.values()
            )
            self.stats["average_attempts"] = total_attempts / total_contexts

        return self.stats.copy()

    def _get_or_create_context(
        self,
        task_id: str,
        task_name: str,
        user_id: Optional[str],
        config: Optional[RetryConfiguration],
    ) -> TaskRetryContext:
        """获取或创建重试上下文"""
        if task_id not in self.retry_contexts:
            # 获取配置
            effective_config = (
                config or self.task_configs.get(task_id) or self.default_config
            )

            # 创建新的上下文
            self.retry_contexts[task_id] = TaskRetryContext(
                task_id=task_id,
                task_name=task_name,
                user_id=user_id,
                configuration=effective_config,
            )

        return self.retry_contexts[task_id]

    def _can_retry(self, context: TaskRetryContext, trigger: RetryTrigger) -> bool:
        """检查是否可以重试"""
        # 检查是否激活
        if not context.is_active:
            return False

        # 检查重试次数
        if context.total_attempts >= context.configuration.max_attempts:
            return False

        # 检查触发条件
        if trigger not in context.configuration.triggers:
            return False

        # 检查冷却时间
        if context.last_attempt_time:
            min_interval = context.configuration.initial_delay
            time_since_last = (
                datetime.now() - context.last_attempt_time
            ).total_seconds()
            if time_since_last < min_interval:
                return False

        return True

    def _calculate_delay(self, context: TaskRetryContext) -> float:
        """计算重试延迟"""
        config = context.configuration
        attempt_number = context.total_attempts

        if config.custom_delay_func:
            delay = config.custom_delay_func(attempt_number)
        elif config.strategy == RetryStrategy.IMMEDIATE:
            delay = 0.0
        elif config.strategy == RetryStrategy.FIXED_DELAY:
            delay = config.initial_delay
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.initial_delay * attempt_number
        elif config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.initial_delay * (
                config.backoff_multiplier ** (attempt_number - 1)
            )
        elif config.strategy == RetryStrategy.FIBONACCI:
            delay = config.initial_delay * self._fibonacci(attempt_number)
        else:
            delay = config.initial_delay

        # 限制最大延迟
        delay = min(delay, config.max_delay)

        # 添加抖动
        if config.jitter and delay > 0:
            import random

            jitter = random.uniform(0.8, 1.2)
            delay *= jitter

        return max(0.0, delay)

    def _fibonacci(self, n: int) -> int:
        """计算斐波那契数列"""
        if n <= 1:
            return 1
        elif n == 2:
            return 1
        else:
            a, b = 1, 1
            for _ in range(3, n + 1):
                a, b = b, a + b
            return b

    def _update_stats(self, trigger: RetryTrigger, strategy: RetryStrategy):
        """更新统计信息"""
        self.stats["total_retries"] += 1

        # 按触发条件统计
        trigger_key = trigger.value
        self.stats["trigger_counts"][trigger_key] = (
            self.stats["trigger_counts"].get(trigger_key, 0) + 1
        )

        # 按策略统计
        strategy_key = strategy.value
        self.stats["strategy_usage"][strategy_key] = (
            self.stats["strategy_usage"].get(strategy_key, 0) + 1
        )

    def _scheduler_loop(self):
        """重试调度器主循环"""
        logger.info("重试调度器开始运行")

        while self.scheduler_running:
            try:
                current_time = datetime.now()

                # 检查是否有需要执行的重试
                ready_retries = []
                remaining_retries = []

                for task_id, retry_time in self.retry_queue:
                    if retry_time <= current_time:
                        ready_retries.append(task_id)
                    else:
                        remaining_retries.append((task_id, retry_time))

                # 更新队列
                self.retry_queue = remaining_retries

                # 执行准备好的重试
                for task_id in ready_retries:
                    self._execute_retry(task_id)

                # 短暂休眠
                time.sleep(1.0)

            except Exception as e:
                logger.error(f"重试调度器异常: {e}")
                time.sleep(5.0)

        logger.info("重试调度器已停止")

    def _execute_retry(self, task_id: str):
        """执行重试"""
        try:
            if task_id not in self.retry_contexts:
                return

            context = self.retry_contexts[task_id]

            if not context.is_active:
                return

            current_attempt = context.attempts[-1] if context.attempts else None
            if not current_attempt:
                return

            # 更新时间
            context.last_attempt_time = datetime.now()

            # 发送重试开始信号
            self.retry_started.emit(task_id, current_attempt.attempt_number)

            logger.info(
                f"开始执行任务 {task_id} 的第 {current_attempt.attempt_number} 次重试"
            )

            # 这里应该触发实际的任务执行
            # 由于这是管理器，实际执行由外部系统处理
            # 我们只是发送信号通知

        except Exception as e:
            logger.error(f"执行重试失败: {e}")

    def cleanup_completed_contexts(self, max_age_hours: int = 24):
        """清理已完成的重试上下文"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        completed_tasks = []
        for task_id, context in self.retry_contexts.items():
            if not context.is_active and context.start_time < cutoff_time:
                completed_tasks.append(task_id)

        for task_id in completed_tasks:
            del self.retry_contexts[task_id]

        if completed_tasks:
            logger.info(f"清理了 {len(completed_tasks)} 个已完成的重试上下文")

    def __del__(self):
        """析构函数"""
        self.stop_scheduler()
