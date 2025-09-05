"""任务执行引擎

实现任务调度、执行状态管理、重试机制和超时控制的核心组件。
"""

from datetime import datetime, timedelta
import logging
import time
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

import asyncio

from src.core.service_locator import get_service, ServiceMixin

if TYPE_CHECKING:
    from src.application.task_service import TaskService as TaskApplicationService
    from src.application.automation_service import AutomationApplicationService

from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from uuid import uuid4

from src.models.task_models import Task, TaskStatus, TaskType
from src.repositories import TaskExecutionRepository, TaskRepository
from src.services.event_bus import EventBus, TaskEventType

logger = logging.getLogger(__name__)


class TaskExecutionError(Exception):
    """任务执行错误"""

    pass


class ExecutorStatus(Enum):
    """执行器状态"""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    PAUSED = "paused"


class TaskExecutionContext:
    """任务执行上下文"""

    def __init__(self, task: Task, execution_id: str):
        self.task = task
        self.execution_id = execution_id
        self.start_time = datetime.now()
        self.retry_count = 0
        self.last_error: Optional[Exception] = None
        self.is_cancelled = False
        self.timeout_handle: Optional[asyncio.Handle] = None

    @property
    def elapsed_time(self) -> float:
        """获取已执行时间（秒）"""
        return (datetime.now() - self.start_time).total_seconds()

    def cancel_timeout(self):
        """取消超时处理"""
        if self.timeout_handle and not self.timeout_handle.cancelled():
            self.timeout_handle.cancel()
            self.timeout_handle = None


class RetryPolicy:
    """重试策略"""

    def __init__(
        self,
        config_manager=None,
        max_retries: int = None,
        base_delay: float = None,
        max_delay: float = None,
        exponential_base: float = None,
        jitter: bool = None,
    ):
        self.config_manager = config_manager
        self.max_retries = max_retries or self._get_config_value('task_executor.retry_policy.max_retries', 3)
        self.base_delay = base_delay or self._get_config_value('task_executor.retry_policy.base_delay', 1.0)
        self.max_delay = max_delay or self._get_config_value('task_executor.retry_policy.max_delay', 60.0)
        self.exponential_base = exponential_base or self._get_config_value('task_executor.retry_policy.exponential_base', 2.0)
        self.jitter = jitter if jitter is not None else self._get_config_value('task_executor.retry_policy.jitter', True)

    def _get_config_value(self, key: str, default):
        """从配置管理器获取配置值"""
        if self.config_manager:
            return self.config_manager.get(key, default)
        return default

    def should_retry(self, retry_count: int, error: Exception) -> bool:
        """判断是否应该重试"""
        if retry_count >= self.max_retries:
            return False

        # 某些错误不应该重试
        if isinstance(error, ValueError):
            return False

        # 检查是否是TaskExecutionError
        if error.__class__.__name__ == "TaskExecutionError":
            return False

        return True

    def get_delay(self, retry_count: int) -> float:
        """获取重试延迟时间"""
        delay = self.base_delay * (self.exponential_base**retry_count)
        delay = min(delay, self.max_delay)

        if self.jitter:
            import random

            delay *= 0.5 + random.random() * 0.5  # 添加50%的随机抖动

        return delay


class TaskExecutor(ServiceMixin):
    """任务执行引擎

    负责任务的调度、执行、状态管理和错误处理。
    """

    def __init__(
        self,
        event_bus: EventBus,
        max_concurrent_tasks: int = None,
        default_timeout: float = None,
        config_manager=None,
    ):
        self.event_bus = event_bus
        # 使用服务定位器延迟获取服务，避免循环依赖
        self._task_service = None
        self._automation_service = None
        self._config_manager = config_manager
        self.max_concurrent_tasks = max_concurrent_tasks or self._get_config_value('task_executor.max_concurrent_tasks', 5)
        self.default_timeout = default_timeout or self._get_config_value('task_executor.default_timeout', 300.0)

        # 执行器状态
        self.status = ExecutorStatus.STOPPED
        self._running_tasks: Dict[str, TaskExecutionContext] = {}
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._worker_tasks: List[asyncio.Task] = []
        self._scheduler_task: Optional[asyncio.Task] = None

        # 重试策略
        self.retry_policy = RetryPolicy(config_manager)

    def _get_config_value(self, key: str, default):
        """从配置管理器获取配置值"""
        if self._config_manager:
            return self._config_manager.get(key, default)
        return default

        # 线程池用于CPU密集型任务
        self.thread_pool = ThreadPoolExecutor(max_workers=2)

        # 任务执行器映射
        self._task_executors: Dict[TaskType, Callable] = {
            TaskType.AUTOMATION: self._execute_automation_task,
            TaskType.SCHEDULED: self._execute_scheduled_task,
            TaskType.MANUAL: self._execute_manual_task,
        }
    
    @property
    def task_service(self) -> "TaskApplicationService":
        """延迟获取任务服务"""
        if self._task_service is None:
            from src.application.task_service import TaskService
            self._task_service = get_service(TaskService)
        return self._task_service
    
    @property
    def automation_service(self) -> "AutomationApplicationService":
        """延迟获取自动化服务"""
        if self._automation_service is None:
            from src.application.automation_service import AutomationApplicationService
            self._automation_service = get_service(AutomationApplicationService)
        return self._automation_service

    async def start(self) -> bool:
        """启动执行引擎"""
        if self.status != ExecutorStatus.STOPPED:
            logger.warning(f"执行引擎已在运行，当前状态: {self.status}")
            return False

        try:
            self.status = ExecutorStatus.STARTING
            logger.info("启动任务执行引擎...")

            # 启动工作线程
            self._worker_tasks = [
                asyncio.create_task(self._worker_loop(i))
                for i in range(self.max_concurrent_tasks)
            ]

            # 启动调度器
            self._scheduler_task = asyncio.create_task(self._scheduler_loop())

            self.status = ExecutorStatus.RUNNING
            logger.info(
                f"任务执行引擎启动成功，工作线程数: {self.max_concurrent_tasks}"
            )
            return True

        except Exception as e:
            logger.error(f"启动执行引擎失败: {e}")
            self.status = ExecutorStatus.STOPPED
            return False

    async def stop(self, timeout: float = None) -> bool:
        """停止执行引擎"""
        if self.status == ExecutorStatus.STOPPED:
            return True

        if timeout is None:
            timeout = self._get_config_value('task_executor.stop_timeout', 30.0)

        try:
            self.status = ExecutorStatus.STOPPING
            logger.info("停止任务执行引擎...")

            # 取消所有正在执行的任务
            for context in self._running_tasks.values():
                context.is_cancelled = True
                context.cancel_timeout()

            # 停止调度器
            if self._scheduler_task:
                self._scheduler_task.cancel()
                try:
                    scheduler_timeout = self._get_config_value('task_executor.scheduler_stop_timeout', 5.0)
                    await asyncio.wait_for(self._scheduler_task, timeout=scheduler_timeout)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass

            # 停止工作线程
            for task in self._worker_tasks:
                task.cancel()

            if self._worker_tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*self._worker_tasks, return_exceptions=True),
                        timeout=timeout,
                    )
                except asyncio.TimeoutError:
                    logger.warning("工作线程停止超时")

            # 关闭线程池
            self.thread_pool.shutdown(wait=True)

            self.status = ExecutorStatus.STOPPED
            logger.info("任务执行引擎已停止")
            return True

        except Exception as e:
            logger.error(f"停止执行引擎失败: {e}")
            return False

    async def pause(self) -> bool:
        """暂停执行引擎"""
        if self.status != ExecutorStatus.RUNNING:
            return False

        self.status = ExecutorStatus.PAUSED
        logger.info("任务执行引擎已暂停")
        return True

    async def resume(self) -> bool:
        """恢复执行引擎"""
        if self.status != ExecutorStatus.PAUSED:
            return False

        self.status = ExecutorStatus.RUNNING
        logger.info("任务执行引擎已恢复")
        return True

    async def submit_task(self, task: Task) -> bool:
        """提交任务到执行队列

        Args:
            task: 要执行的任务

        Returns:
            是否提交成功
        """
        if self.status not in [ExecutorStatus.RUNNING, ExecutorStatus.PAUSED]:
            logger.warning(f"执行引擎未运行，无法提交任务: {task.task_id}")
            return False

        try:
            await self._task_queue.put(task)
            logger.info(f"任务已提交到执行队列: {task.task_id}")
            return True
        except Exception as e:
            logger.error(f"提交任务失败: {e}")
            return False

    async def cancel_task(self, task_id: str) -> bool:
        """取消正在执行的任务

        Args:
            task_id: 任务ID

        Returns:
            是否取消成功
        """
        context = self._running_tasks.get(task_id)
        if not context:
            logger.warning(f"任务未在执行中: {task_id}")
            return False

        context.is_cancelled = True
        context.cancel_timeout()
        logger.info(f"任务已标记为取消: {task_id}")
        return True

    def get_running_tasks(self) -> List[str]:
        """获取正在执行的任务列表"""
        return list(self._running_tasks.keys())

    def get_executor_status(self) -> Dict[str, Any]:
        """获取执行器状态信息"""
        return {
            "status": self.status.value,
            "running_tasks_count": len(self._running_tasks),
            "queue_size": self._task_queue.qsize(),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "worker_tasks_count": len(self._worker_tasks),
        }

    async def _scheduler_loop(self):
        """调度器循环"""
        logger.info("调度器循环启动")
        
        scheduler_interval = self._get_config_value('task_executor.scheduler_interval', 10.0)
        error_retry_interval = self._get_config_value('task_executor.error_retry_interval', 5.0)

        try:
            while self.status != ExecutorStatus.STOPPING:
                try:
                    # 检查计划任务
                    await self._check_scheduled_tasks()

                    # 等待一段时间后再次检查
                    await asyncio.sleep(scheduler_interval)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"调度器循环错误: {e}")
                    await asyncio.sleep(error_retry_interval)

        except asyncio.CancelledError:
            pass
        finally:
            logger.info("调度器循环结束")

    async def _worker_loop(self, worker_id: int):
        """工作线程循环"""
        logger.info(f"工作线程 {worker_id} 启动")
        
        queue_timeout = self._get_config_value('task_executor.queue_timeout', 1.0)
        worker_sleep_interval = self._get_config_value('task_executor.worker_sleep_interval', 1.0)

        try:
            while self.status != ExecutorStatus.STOPPING:
                try:
                    # 等待任务
                    task = await asyncio.wait_for(self._task_queue.get(), timeout=queue_timeout)

                    # 检查执行器状态
                    if self.status == ExecutorStatus.PAUSED:
                        # 暂停状态下重新放回队列
                        await self._task_queue.put(task)
                        await asyncio.sleep(worker_sleep_interval)
                        continue

                    # 执行任务
                    await self._execute_task(task)

                except asyncio.TimeoutError:
                    # 超时是正常的，继续循环
                    continue
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"工作线程 {worker_id} 错误: {e}")
                    await asyncio.sleep(worker_sleep_interval)

        except asyncio.CancelledError:
            pass
        finally:
            logger.info(f"工作线程 {worker_id} 结束")

    async def _check_scheduled_tasks(self):
        """检查计划任务"""
        try:
            # 获取应该执行的计划任务
            now = datetime.now()
            scheduled_tasks = await self.task_service.get_scheduled_tasks(now)

            for task in scheduled_tasks:
                if task.task_id not in self._running_tasks:
                    await self.submit_task(task)

        except Exception as e:
            logger.error(f"检查计划任务失败: {e}")

    async def _execute_task(self, task: Task):
        """执行单个任务"""
        execution_id = str(uuid4())
        context = TaskExecutionContext(task, execution_id)

        try:
            # 记录执行开始
            self._running_tasks[task.task_id] = context

            # 启动任务执行
            execution_id = await self.task_service.execute_task(
                task.task_id, task.user_id
            )
            context.execution_id = execution_id

            # 设置超时
            timeout = getattr(task.config, "timeout", self.default_timeout)
            if timeout > 0:
                context.timeout_handle = asyncio.get_event_loop().call_later(
                    timeout, self._handle_task_timeout, task.task_id
                )

            # 执行任务
            await self._execute_task_with_retry(context)

        except Exception as e:
            logger.error(f"任务执行失败: {task.task_id}, 错误: {e}")
            await self._handle_task_failure(context, e)
        finally:
            # 清理
            context.cancel_timeout()
            self._running_tasks.pop(task.task_id, None)

    async def _execute_task_with_retry(self, context: TaskExecutionContext):
        """带重试的任务执行"""
        task = context.task

        while True:
            try:
                # 检查是否被取消
                if context.is_cancelled:
                    await self.task_service.cancel_task(task.task_id, task.user_id)
                    return

                # 执行任务
                result = await self._execute_task_by_type(context)

                # 任务成功完成
                await self.task_service.complete_task(
                    task.task_id, context.execution_id, result
                )

                logger.info(f"任务执行成功: {task.task_id}")
                return

            except Exception as e:
                context.last_error = e
                context.retry_count += 1

                # 检查是否应该重试
                if not self.retry_policy.should_retry(context.retry_count - 1, e):
                    raise e

                # 计算重试延迟
                delay = self.retry_policy.get_delay(context.retry_count - 1)
                logger.warning(
                    f"任务执行失败，{delay:.1f}秒后重试 ({context.retry_count}/{self.retry_policy.max_retries}): "
                    f"{task.task_id}, 错误: {e}"
                )

                # 等待重试
                await asyncio.sleep(delay)

    async def _execute_task_by_type(
        self, context: TaskExecutionContext
    ) -> Optional[Dict[str, Any]]:
        """根据任务类型执行任务"""
        task = context.task
        executor = self._task_executors.get(task.task_type)

        if not executor:
            raise TaskExecutionError(f"不支持的任务类型: {task.task_type}")

        return await executor(context)

    async def _execute_automation_task(
        self, context: TaskExecutionContext
    ) -> Optional[Dict[str, Any]]:
        """执行自动化任务"""
        task = context.task
        config = task.config

        if not config.automation_config:
            raise TaskExecutionError("自动化任务缺少automation_config")

        automation_config = config.automation_config

        # 检测游戏窗口
        game_names = automation_config.get("game_names", [])
        if game_names:
            windows = await self.automation_service.detect_game_windows(game_names)
            if not windows:
                raise TaskExecutionError(f"未找到游戏窗口: {game_names}")
            window = windows[0]
        else:
            window = None

        # 执行自动化序列
        sequence = automation_config.get("sequence", [])
        if sequence:
            success = await self.automation_service.execute_automation_sequence(
                context.execution_id, sequence, window
            )

            if not success:
                raise TaskExecutionError("自动化序列执行失败")

        return {
            "window_title": window.title if window else None,
            "sequence_length": len(sequence),
            "execution_time": context.elapsed_time,
        }

    async def _execute_scheduled_task(
        self, context: TaskExecutionContext
    ) -> Optional[Dict[str, Any]]:
        """执行计划任务"""
        task = context.task
        config = task.config

        if not config.schedule_config:
            raise TaskExecutionError("计划任务缺少schedule_config")

        schedule_config = config.schedule_config

        # 根据计划配置执行相应的操作
        action_type = schedule_config.get("action_type")

        if action_type == "automation":
            # 执行自动化操作
            automation_config = schedule_config.get("automation_config")
            if automation_config:
                # 临时设置automation_config
                task.config.automation_config = automation_config
                return await self._execute_automation_task(context)

        elif action_type == "notification":
            # 发送通知
            message = schedule_config.get("message", "计划任务执行")
            logger.info(f"计划任务通知: {message}")
            return {"message": message}

        else:
            raise TaskExecutionError(f"不支持的计划任务类型: {action_type}")

        return {"action_type": action_type}

    async def _execute_manual_task(
        self, context: TaskExecutionContext
    ) -> Optional[Dict[str, Any]]:
        """执行手动任务"""
        task = context.task

        # 手动任务通常需要用户交互，这里只是示例
        logger.info(f"执行手动任务: {task.task_id}")

        # 模拟一些处理时间
        processing_delay = self._get_config_value('task_executor.manual_task_processing_delay', 1.0)
        await asyncio.sleep(processing_delay)

        return {"task_type": "manual", "execution_time": context.elapsed_time}

    async def _handle_task_failure(
        self, context: TaskExecutionContext, error: Exception
    ):
        """处理任务失败"""
        try:
            await self.task_service.complete_task(
                context.task.task_id, context.execution_id, None, str(error)
            )
        except Exception as e:
            logger.error(f"处理任务失败时出错: {e}")

    def _handle_task_timeout(self, task_id: str):
        """处理任务超时"""
        context = self._running_tasks.get(task_id)
        if context:
            context.is_cancelled = True
            logger.warning(f"任务执行超时: {task_id}")

    def get_status(self) -> Dict[str, Any]:
        """获取执行器状态"""
        return {
            "status": self.status.value,
            "running_tasks": len(self._running_tasks),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "queue_size": self._task_queue.qsize(),
            "worker_tasks": len(self._worker_tasks),
        }

    def get_running_tasks(self) -> List[str]:
        """获取正在运行的任务ID列表"""
        return list(self._running_tasks.keys())

    def __del__(self):
        """析构函数"""
        if hasattr(self, "thread_pool"):
            self.thread_pool.shutdown(wait=False)
