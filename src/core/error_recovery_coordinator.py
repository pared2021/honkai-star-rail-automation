# -*- coding: utf-8 -*-
"""
错误恢复协调器 - 协调各种错误恢复机制的执行
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from typing import Any, Callable, Dict, List, Optional, Set

import asyncio

from application.error_handling_service import ErrorContext, ErrorHandlingService
from config.error_recovery_strategies import (
    ErrorRecoveryStrategy,
    error_recovery_config,
)
from core.exception_recovery import ExceptionRecovery, ExceptionType, RecoveryResult
from core.task_retry_manager import RetryTrigger, TaskRetryManager
from src.services.event_bus import EventBus
from utils.logger import get_logger


class RecoveryPhase(Enum):
    """恢复阶段"""

    DETECTION = "detection"  # 错误检测
    ANALYSIS = "analysis"  # 错误分析
    PLANNING = "planning"  # 恢复规划
    EXECUTION = "execution"  # 恢复执行
    VALIDATION = "validation"  # 恢复验证
    COMPLETION = "completion"  # 恢复完成
    ESCALATION = "escalation"  # 问题升级


class RecoveryStatus(Enum):
    """恢复状态"""

    PENDING = "pending"  # 等待中
    RUNNING = "running"  # 执行中
    SUCCESS = "success"  # 成功
    FAILED = "failed"  # 失败
    PARTIAL = "partial"  # 部分成功
    CANCELLED = "cancelled"  # 已取消
    ESCALATED = "escalated"  # 已升级


@dataclass
class RecoverySession:
    """恢复会话"""

    session_id: str
    error_type: str
    error_context: ErrorContext
    strategy: ErrorRecoveryStrategy

    # 状态信息
    status: RecoveryStatus = RecoveryStatus.PENDING
    current_phase: RecoveryPhase = RecoveryPhase.DETECTION

    # 时间信息
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    last_update: datetime = field(default_factory=datetime.now)

    # 执行信息
    attempt_count: int = 0
    max_attempts: int = 3
    recovery_actions_completed: List[str] = field(default_factory=list)
    recovery_actions_failed: List[str] = field(default_factory=list)

    # 结果信息
    recovery_result: Optional[RecoveryResult] = None
    error_messages: List[str] = field(default_factory=list)
    success_metrics: Dict[str, Any] = field(default_factory=dict)

    # 依赖和关联
    dependent_sessions: Set[str] = field(default_factory=set)
    parent_session: Optional[str] = None

    # 回调函数
    on_phase_change: Optional[Callable] = None
    on_status_change: Optional[Callable] = None
    on_completion: Optional[Callable] = None


class ErrorRecoveryCoordinator:
    """错误恢复协调器"""

    def __init__(
        self,
        exception_recovery: ExceptionRecovery,
        retry_manager: TaskRetryManager,
        error_service: ErrorHandlingService,
        event_bus: EventBus,
        config_manager,
        logger: Optional[logging.Logger] = None,
    ):

        self.exception_recovery = exception_recovery
        self.retry_manager = retry_manager
        self.error_service = error_service
        self.event_bus = event_bus
        self.config_manager = config_manager
        self.logger = logger or get_logger(self.__class__.__name__)

        # 恢复会话管理
        self.active_sessions: Dict[str, RecoverySession] = {}
        self.completed_sessions: Dict[str, RecoverySession] = {}

        # 恢复队列
        self.recovery_queue: asyncio.Queue = asyncio.Queue()
        self.priority_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()

        # 协调器状态
        self.is_running = False
        self.worker_tasks: List[asyncio.Task] = []
        self.max_concurrent_recoveries = self.config_manager.get(
            'error_recovery.max_concurrent_recoveries', 5
        )

        # 统计信息
        self.stats = {
            "total_sessions": 0,
            "successful_recoveries": 0,
            "failed_recoveries": 0,
            "escalated_issues": 0,
            "average_recovery_time": 0.0,
            "by_error_type": {},
            "by_phase": {phase.value: 0 for phase in RecoveryPhase},
            "by_status": {status.value: 0 for status in RecoveryStatus},
        }

        # 从配置管理器加载配置
        self.config = {
            "session_timeout": self.config_manager.get('error_recovery.session_timeout', 300.0),
            "escalation_threshold": self.config_manager.get('error_recovery.escalation_threshold', 3),
            "cleanup_interval": self.config_manager.get('error_recovery.cleanup_interval', 3600.0),
            "max_session_history": self.config_manager.get('error_recovery.max_session_history', 1000),
            "enable_auto_escalation": self.config_manager.get('error_recovery.enable_auto_escalation', True),
            "enable_dependency_tracking": self.config_manager.get('error_recovery.enable_dependency_tracking', True),
        }

        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """设置事件处理器"""
        self.event_bus.on("error_detected", self._on_error_detected)
        self.event_bus.on("recovery_requested", self._on_recovery_requested)
        self.event_bus.on("task_failed", self._on_task_failed)
        self.event_bus.on("system_health_check", self._on_health_check)

    async def start(self):
        """启动协调器"""
        if self.is_running:
            return

        self.is_running = True
        self.logger.info("错误恢复协调器启动")

        # 启动工作线程
        for i in range(self.max_concurrent_recoveries):
            task = asyncio.create_task(self._recovery_worker(f"worker-{i}"))
            self.worker_tasks.append(task)

        # 启动清理任务
        cleanup_task = asyncio.create_task(self._cleanup_worker())
        self.worker_tasks.append(cleanup_task)

        # 启动监控任务
        monitor_task = asyncio.create_task(self._monitor_worker())
        self.worker_tasks.append(monitor_task)

    async def stop(self):
        """停止协调器"""
        if not self.is_running:
            return

        self.is_running = False
        self.logger.info("错误恢复协调器停止")

        # 取消所有工作任务
        for task in self.worker_tasks:
            task.cancel()

        # 等待任务完成
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()

        # 完成所有活动会话
        for session in self.active_sessions.values():
            await self._complete_session(session, RecoveryStatus.CANCELLED)

    async def coordinate_recovery(
        self, error: Exception, context: ErrorContext, priority: int = 5
    ) -> str:
        """协调错误恢复

        Args:
            error: 异常对象
            context: 错误上下文
            priority: 优先级 (1-10, 数字越大优先级越高)

        Returns:
            str: 恢复会话ID
        """

        # 创建恢复会话
        session = await self._create_recovery_session(error, context)

        # 添加到队列
        await self.priority_queue.put((10 - priority, session.session_id))

        self.logger.info(f"恢复会话已创建: {session.session_id}")

        # 发送事件
        self.event_bus.emit(
            "recovery_session_created",
            {
                "session_id": session.session_id,
                "error_type": session.error_type,
                "priority": priority,
                "timestamp": datetime.now(),
            },
        )

        return session.session_id

    async def _create_recovery_session(
        self, error: Exception, context: ErrorContext
    ) -> RecoverySession:
        """创建恢复会话"""

        error_type = type(error).__name__
        session_id = f"recovery_{error_type}_{datetime.now().timestamp()}"

        # 获取恢复策略
        strategy = error_recovery_config.get_strategy(error_type)
        if not strategy:
            # 创建默认策略
            strategy = self._create_default_strategy(error_type)

        session = RecoverySession(
            session_id=session_id,
            error_type=error_type,
            error_context=context,
            strategy=strategy,
            max_attempts=strategy.max_retry_attempts,
        )

        self.active_sessions[session_id] = session
        self.stats["total_sessions"] += 1

        return session

    def _create_default_strategy(self, error_type: str) -> ErrorRecoveryStrategy:
        """创建默认恢复策略"""
        from application.error_handling_service import ErrorSeverity
        from config.error_recovery_strategies import (
            ErrorCategory,
            ErrorRecoveryStrategy,
        )
        from core.task_retry_manager import RetryStrategy

        return ErrorRecoveryStrategy(
            error_type=error_type,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            retry_enabled=True,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            max_retry_attempts=3,
            initial_retry_delay=1.0,
            description=f"默认恢复策略 - {error_type}",
        )

    async def _recovery_worker(self, worker_name: str):
        """恢复工作线程"""
        self.logger.debug(f"恢复工作线程启动: {worker_name}")

        while self.is_running:
            try:
                # 从优先级队列获取会话
                priority, session_id = await asyncio.wait_for(
                    self.priority_queue.get(), timeout=1.0
                )

                session = self.active_sessions.get(session_id)
                if not session:
                    continue

                # 执行恢复
                await self._execute_recovery_session(session)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"恢复工作线程错误 {worker_name}: {e}")
                await asyncio.sleep(1)

        self.logger.debug(f"恢复工作线程停止: {worker_name}")

    async def _execute_recovery_session(self, session: RecoverySession):
        """执行恢复会话"""
        try:
            session.status = RecoveryStatus.RUNNING
            session.last_update = datetime.now()

            # 阶段1: 错误分析
            await self._change_phase(session, RecoveryPhase.ANALYSIS)
            analysis_result = await self._analyze_error(session)

            if not analysis_result:
                await self._complete_session(session, RecoveryStatus.FAILED)
                return

            # 阶段2: 恢复规划
            await self._change_phase(session, RecoveryPhase.PLANNING)
            recovery_plan = await self._plan_recovery(session)

            if not recovery_plan:
                await self._complete_session(session, RecoveryStatus.FAILED)
                return

            # 阶段3: 恢复执行
            await self._change_phase(session, RecoveryPhase.EXECUTION)
            execution_result = await self._execute_recovery(session)

            # 阶段4: 恢复验证
            await self._change_phase(session, RecoveryPhase.VALIDATION)
            validation_result = await self._validate_recovery(session)

            # 确定最终状态
            if validation_result:
                await self._complete_session(session, RecoveryStatus.SUCCESS)
            elif session.attempt_count < session.max_attempts:
                # 重试
                session.attempt_count += 1
                await self._retry_recovery(session)
            else:
                # 升级或失败
                if self.config["enable_auto_escalation"]:
                    await self._escalate_session(session)
                else:
                    await self._complete_session(session, RecoveryStatus.FAILED)

        except Exception as e:
            self.logger.error(f"恢复会话执行错误 {session.session_id}: {e}")
            session.error_messages.append(str(e))
            await self._complete_session(session, RecoveryStatus.FAILED)

    async def _analyze_error(self, session: RecoverySession) -> bool:
        """分析错误"""
        try:
            # 使用异常恢复服务分析
            error_type = getattr(ExceptionType, session.error_type.upper(), None)
            if error_type:
                exceptions = self.exception_recovery.detect_exceptions()
                if error_type in exceptions:
                    session.success_metrics["error_detected"] = True
                    return True

            # 使用错误处理服务分析
            context = session.error_context
            if context and context.severity:
                session.success_metrics["severity_analyzed"] = True
                return True

            return False

        except Exception as e:
            self.logger.error(f"错误分析失败 {session.session_id}: {e}")
            return False

    async def _plan_recovery(self, session: RecoverySession) -> bool:
        """规划恢复"""
        try:
            strategy = session.strategy

            # 检查恢复动作
            if not strategy.recovery_actions:
                session.error_messages.append("没有可用的恢复动作")
                return False

            # 检查重试配置
            if strategy.retry_enabled and strategy.max_retry_attempts > 0:
                session.success_metrics["retry_planned"] = True

            # 检查依赖
            if self.config["enable_dependency_tracking"]:
                await self._check_dependencies(session)

            session.success_metrics["recovery_planned"] = True
            return True

        except Exception as e:
            self.logger.error(f"恢复规划失败 {session.session_id}: {e}")
            return False

    async def _execute_recovery(self, session: RecoverySession) -> bool:
        """执行恢复"""
        try:
            strategy = session.strategy

            # 使用异常恢复服务执行
            error_type = getattr(ExceptionType, session.error_type.upper(), None)
            if error_type:
                result = self.exception_recovery.handle_exception(error_type)
                session.recovery_result = result

                if result and result.success:
                    session.success_metrics["recovery_executed"] = True
                    return True

            # 使用重试管理器
            if strategy.retry_enabled:
                # 这里可以集成重试逻辑
                session.success_metrics["retry_attempted"] = True

            return False

        except Exception as e:
            self.logger.error(f"恢复执行失败 {session.session_id}: {e}")
            return False

    async def _validate_recovery(self, session: RecoverySession) -> bool:
        """验证恢复"""
        try:
            # 检查恢复结果
            if session.recovery_result and session.recovery_result.success:
                session.success_metrics["recovery_validated"] = True
                return True

            # 检查系统状态
            # 这里可以添加具体的验证逻辑

            return False

        except Exception as e:
            self.logger.error(f"恢复验证失败 {session.session_id}: {e}")
            return False

    async def _retry_recovery(self, session: RecoverySession):
        """重试恢复"""
        delay = session.strategy.initial_retry_delay * (
            session.strategy.retry_backoff_factor ** (session.attempt_count - 1)
        )
        delay = min(delay, session.strategy.max_retry_delay)

        self.logger.info(f"恢复会话重试 {session.session_id}, 延迟 {delay}s")

        # 延迟后重新加入队列
        await asyncio.sleep(delay)
        await self.priority_queue.put((5, session.session_id))  # 中等优先级

    async def _escalate_session(self, session: RecoverySession):
        """升级会话"""
        session.status = RecoveryStatus.ESCALATED
        session.current_phase = RecoveryPhase.ESCALATION
        session.end_time = datetime.now()

        self.stats["escalated_issues"] += 1

        # 发送升级事件
        self.event_bus.emit(
            "recovery_escalated",
            {
                "session_id": session.session_id,
                "error_type": session.error_type,
                "attempt_count": session.attempt_count,
                "error_messages": session.error_messages,
                "timestamp": datetime.now(),
            },
        )

        self.logger.warning(f"恢复会话已升级: {session.session_id}")

        # 移动到完成会话
        self.completed_sessions[session.session_id] = session
        del self.active_sessions[session.session_id]

    async def _complete_session(self, session: RecoverySession, status: RecoveryStatus):
        """完成会话"""
        session.status = status
        session.current_phase = RecoveryPhase.COMPLETION
        session.end_time = datetime.now()

        # 更新统计
        if status == RecoveryStatus.SUCCESS:
            self.stats["successful_recoveries"] += 1
        elif status == RecoveryStatus.FAILED:
            self.stats["failed_recoveries"] += 1

        # 计算恢复时间
        recovery_time = (session.end_time - session.start_time).total_seconds()
        self._update_average_recovery_time(recovery_time)

        # 发送完成事件
        self.event_bus.emit(
            "recovery_completed",
            {
                "session_id": session.session_id,
                "status": status.value,
                "recovery_time": recovery_time,
                "attempt_count": session.attempt_count,
                "timestamp": datetime.now(),
            },
        )

        # 执行回调
        if session.on_completion:
            try:
                await session.on_completion(session)
            except Exception as e:
                self.logger.error(f"会话完成回调错误: {e}")

        self.logger.info(f"恢复会话完成: {session.session_id} - {status.value}")

        # 移动到完成会话
        self.completed_sessions[session.session_id] = session
        if session.session_id in self.active_sessions:
            del self.active_sessions[session.session_id]

    async def _change_phase(self, session: RecoverySession, phase: RecoveryPhase):
        """改变阶段"""
        old_phase = session.current_phase
        session.current_phase = phase
        session.last_update = datetime.now()

        self.stats["by_phase"][phase.value] += 1

        # 执行回调
        if session.on_phase_change:
            try:
                await session.on_phase_change(session, old_phase, phase)
            except Exception as e:
                self.logger.error(f"阶段变更回调错误: {e}")

        self.logger.debug(
            f"会话 {session.session_id} 阶段变更: {old_phase.value} -> {phase.value}"
        )

    async def _check_dependencies(self, session: RecoverySession):
        """检查依赖"""
        # 这里可以实现依赖检查逻辑
        pass

    def _update_average_recovery_time(self, recovery_time: float):
        """更新平均恢复时间"""
        total_completed = (
            self.stats["successful_recoveries"] + self.stats["failed_recoveries"]
        )
        if total_completed > 0:
            current_avg = self.stats["average_recovery_time"]
            self.stats["average_recovery_time"] = (
                current_avg * (total_completed - 1) + recovery_time
            ) / total_completed

    async def _cleanup_worker(self):
        """清理工作线程"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config["cleanup_interval"])
                await self._cleanup_completed_sessions()
            except Exception as e:
                self.logger.error(f"清理工作线程错误: {e}")

    async def _cleanup_completed_sessions(self):
        """清理已完成的会话"""
        if len(self.completed_sessions) <= self.config["max_session_history"]:
            return

        # 按时间排序，保留最新的
        sorted_sessions = sorted(
            self.completed_sessions.items(),
            key=lambda x: x[1].end_time or datetime.now(),
            reverse=True,
        )

        # 保留最新的会话
        keep_sessions = dict(sorted_sessions[: self.config["max_session_history"]])

        # 清理旧会话
        removed_count = len(self.completed_sessions) - len(keep_sessions)
        self.completed_sessions = keep_sessions

        if removed_count > 0:
            self.logger.info(f"清理了 {removed_count} 个已完成的恢复会话")

    async def _monitor_worker(self):
        """监控工作线程"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                await self._check_session_timeouts()
                await self._emit_health_metrics()
            except Exception as e:
                self.logger.error(f"监控工作线程错误: {e}")

    async def _check_session_timeouts(self):
        """检查会话超时"""
        timeout_threshold = datetime.now() - timedelta(
            seconds=self.config["session_timeout"]
        )

        timeout_sessions = [
            session
            for session in self.active_sessions.values()
            if session.last_update < timeout_threshold
        ]

        for session in timeout_sessions:
            self.logger.warning(f"恢复会话超时: {session.session_id}")
            await self._complete_session(session, RecoveryStatus.FAILED)

    async def _emit_health_metrics(self):
        """发送健康指标"""
        metrics = {
            "active_sessions": len(self.active_sessions),
            "completed_sessions": len(self.completed_sessions),
            "queue_size": self.priority_queue.qsize(),
            "stats": self.stats.copy(),
            "timestamp": datetime.now(),
        }

        self.event_bus.emit("recovery_coordinator_metrics", metrics)

    # 事件处理器
    async def _on_error_detected(self, event_data: Dict[str, Any]):
        """处理错误检测事件"""
        error = event_data.get("error")
        context = event_data.get("context")

        if error and context:
            await self.coordinate_recovery(error, context)

    async def _on_recovery_requested(self, event_data: Dict[str, Any]):
        """处理恢复请求事件"""
        error = event_data.get("error")
        context = event_data.get("context")
        priority = event_data.get("priority", 5)

        if error and context:
            await self.coordinate_recovery(error, context, priority)

    async def _on_task_failed(self, event_data: Dict[str, Any]):
        """处理任务失败事件"""
        # 可以根据任务失败触发恢复
        pass

    async def _on_health_check(self, event_data: Dict[str, Any]):
        """处理健康检查事件"""
        await self._emit_health_metrics()

    # 公共接口
    def get_session(self, session_id: str) -> Optional[RecoverySession]:
        """获取恢复会话"""
        return self.active_sessions.get(session_id) or self.completed_sessions.get(
            session_id
        )

    def get_active_sessions(self) -> List[RecoverySession]:
        """获取活动会话"""
        return list(self.active_sessions.values())

    def get_completed_sessions(self) -> List[RecoverySession]:
        """获取已完成会话"""
        return list(self.completed_sessions.values())

    async def cancel_session(self, session_id: str) -> bool:
        """取消恢复会话"""
        session = self.active_sessions.get(session_id)
        if session:
            await self._complete_session(session, RecoveryStatus.CANCELLED)
            return True
        return False

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()

    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        total_sessions = self.stats["total_sessions"]
        success_rate = (
            self.stats["successful_recoveries"] / total_sessions * 100
            if total_sessions > 0
            else 100
        )

        status = "healthy"
        if success_rate < 50:
            status = "critical"
        elif success_rate < 80:
            status = "warning"
        elif success_rate < 95:
            status = "degraded"

        return {
            "status": status,
            "success_rate": success_rate,
            "active_sessions": len(self.active_sessions),
            "completed_sessions": len(self.completed_sessions),
            "queue_size": self.priority_queue.qsize(),
            "average_recovery_time": self.stats["average_recovery_time"],
            "escalated_issues": self.stats["escalated_issues"],
        }
