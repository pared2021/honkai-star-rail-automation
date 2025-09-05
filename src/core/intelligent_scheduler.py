# -*- coding: utf-8 -*-
"""智能任务调度器 - 根据游戏状态自动选择和调度任务执行."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from queue import PriorityQueue
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from loguru import logger
from src.automation.automation_controller import AutomationController
from src.models.task_models import Task, TaskPriority, TaskStatus, TaskType

from .game_detector import GameDetector, SceneType
from .task_manager import TaskManager


class SchedulerState(Enum):
    """调度器状态."""

    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class TaskExecutionResult(Enum):
    """任务执行结果."""

    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"
    SKIP = "skip"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    """调度任务."""

    task: Task
    priority: int
    scheduled_time: datetime
    retry_count: int = 0
    last_attempt: Optional[datetime] = None
    dependencies: List[str] = None  # 依赖的任务ID列表

    def __post_init__(self):
        """初始化后处理."""
        if self.dependencies is None:
            self.dependencies = []

    def __lt__(self, other):
        """比较运算符，用于优先级队列排序."""
        # 优先级队列排序：优先级高的先执行，时间早的先执行
        if self.priority != other.priority:
            return self.priority > other.priority
        return self.scheduled_time < other.scheduled_time


@dataclass
class SchedulerConfig:
    """调度器配置."""

    max_concurrent_tasks: int = 3
    task_timeout: int = 300  # 秒
    retry_delay: int = 60  # 重试延迟（秒）
    max_retry_count: int = 3
    check_interval: float = 1.0  # 检查间隔（秒）
    auto_pause_on_error: bool = True
    scene_based_scheduling: bool = True
    priority_boost_factor: float = 1.2  # 优先级提升因子
    
    @classmethod
    def from_config_manager(cls, config_manager):
        """从配置管理器创建调度器配置."""
        if config_manager is None:
            return cls()
        
        return cls(
            max_concurrent_tasks=config_manager.get("scheduler.max_concurrent_tasks", 3),
            task_timeout=config_manager.get("scheduler.task_timeout", 300),
            retry_delay=config_manager.get("scheduler.retry_delay", 60),
            max_retry_count=config_manager.get("scheduler.max_retry_count", 3),
            check_interval=config_manager.get("scheduler.check_interval", 1.0),
            auto_pause_on_error=config_manager.get("scheduler.auto_pause_on_error", True),
            scene_based_scheduling=config_manager.get("scheduler.scene_based_scheduling", True),
            priority_boost_factor=config_manager.get("scheduler.priority_boost_factor", 1.2)
        )


class IntelligentScheduler:
    """智能任务调度器."""

    def __init__(
        self,
        task_manager: TaskManager,
        game_detector: GameDetector,
        automation_controller: AutomationController,
        config: Optional[SchedulerConfig] = None,
        config_manager=None,
    ):
        """初始化智能任务调度器."""
        self.task_manager = task_manager
        self.game_detector = game_detector
        self.automation_controller = automation_controller
        self.config_manager = config_manager
        self.config = config or SchedulerConfig.from_config_manager(config_manager)

        # 调度器状态
        self.state = SchedulerState.STOPPED

        # 任务队列
        self.task_queue = PriorityQueue()
        self.running_tasks: Dict[str, threading.Thread] = {}
        self.completed_tasks: List[str] = []
        self.failed_tasks: List[str] = []

        # 线程控制
        self.scheduler_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()

        # 场景任务映射 - 从配置获取
        default_mapping = {
            SceneType.MAIN_MENU: [TaskType.DAILY_MISSION, TaskType.EXPLORATION],
            SceneType.GAME_WORLD: [
                TaskType.EXPLORATION,
                TaskType.DAILY_MISSION,
                TaskType.COMBAT_TRAINING,
            ],
            SceneType.COMBAT: [TaskType.COMBAT_TRAINING],
            SceneType.INVENTORY: [TaskType.DAILY_MISSION],
            SceneType.MISSION: [TaskType.DAILY_MISSION],
            SceneType.SHOP: [TaskType.DAILY_MISSION],
            SceneType.MAIL: [TaskType.DAILY_MISSION],
        }
        
        if config_manager:
            # 从配置管理器获取场景任务映射
            self.scene_task_mapping = config_manager.get("scheduler.scene_task_mapping", default_mapping)
        else:
            self.scene_task_mapping = default_mapping

        # 回调函数
        self.task_started_callback: Optional[Callable] = None
        self.task_completed_callback: Optional[Callable] = None
        self.task_failed_callback: Optional[Callable] = None
        self.scheduler_error_callback: Optional[Callable] = None

        logger.info("智能任务调度器初始化完成")

    def _get_config_value(self, key: str, default_value):
        """从配置管理器获取配置值."""
        if self.config_manager:
            return self.config_manager.get(key, default_value)
        return default_value

    def start(self) -> bool:
        """启动调度器."""
        if self.state == SchedulerState.RUNNING:
            logger.warning("调度器已在运行中")
            return False

        try:
            self.stop_event.clear()
            self.pause_event.clear()
            self.state = SchedulerState.RUNNING

            # 启动调度器线程
            self.scheduler_thread = threading.Thread(
                target=self._scheduler_loop, daemon=True
            )
            self.scheduler_thread.start()

            logger.info("智能任务调度器已启动")
            return True

        except Exception as e:
            logger.error(f"启动调度器失败: {e}")
            self.state = SchedulerState.ERROR
            return False

    def stop(self) -> bool:
        """停止调度器."""
        if self.state == SchedulerState.STOPPED:
            return True

        try:
            self.stop_event.set()
            self.state = SchedulerState.STOPPED

            # 等待调度器线程结束
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                timeout = self._get_config_value("scheduler.stop_timeout", 5.0)
                self.scheduler_thread.join(timeout=timeout)

            # 停止所有运行中的任务
            self._stop_all_running_tasks()

            logger.info("智能任务调度器已停止")
            return True

        except Exception as e:
            logger.error(f"停止调度器失败: {e}")
            return False

    def pause(self) -> bool:
        """暂停调度器."""
        if self.state != SchedulerState.RUNNING:
            return False

        self.pause_event.set()
        self.state = SchedulerState.PAUSED
        logger.info("智能任务调度器已暂停")
        return True

    def resume(self) -> bool:
        """恢复调度器."""
        if self.state != SchedulerState.PAUSED:
            return False

        self.pause_event.clear()
        self.state = SchedulerState.RUNNING
        logger.info("智能任务调度器已恢复")
        return True

    def add_task(
        self,
        task: Task,
        priority: Optional[int] = None,
        scheduled_time: Optional[datetime] = None,
        dependencies: Optional[List[str]] = None,
    ) -> bool:
        """添加任务到调度队列."""
        try:
            # 计算优先级
            if priority is None:
                priority = self._calculate_task_priority(task)

            # 设置调度时间
            if scheduled_time is None:
                scheduled_time = datetime.now()

            # 创建调度任务
            scheduled_task = ScheduledTask(
                task=task,
                priority=priority,
                scheduled_time=scheduled_time,
                dependencies=dependencies or [],
            )

            # 添加到队列
            self.task_queue.put(scheduled_task)

            logger.info(f"任务已添加到调度队列: {task.name} (优先级: {priority})")
            return True

        except Exception as e:
            logger.error(f"添加任务到调度队列失败: {e}")
            return False

    def remove_task(self, task_id: str) -> bool:
        """从调度队列移除任务."""
        # 注意：PriorityQueue不支持直接移除，这里只是标记
        # 实际实现中可能需要重新设计数据结构
        logger.info(f"任务已标记为移除: {task_id}")
        return True

    def get_scheduler_status(self) -> Dict[str, Any]:
        """获取调度器状态."""
        return {
            "state": self.state.value,
            "queue_size": self.task_queue.qsize(),
            "running_tasks_count": len(self.running_tasks),
            "completed_tasks_count": len(self.completed_tasks),
            "failed_tasks_count": len(self.failed_tasks),
            "config": {
                "max_concurrent_tasks": self.config.max_concurrent_tasks,
                "task_timeout": self.config.task_timeout,
                "retry_delay": self.config.retry_delay,
                "max_retry_count": self.config.max_retry_count,
            },
        }

    def update_config(self, config: SchedulerConfig) -> bool:
        """更新调度器配置."""
        try:
            self.config = config
            logger.info("调度器配置已更新")
            return True
        except Exception as e:
            logger.error(f"更新调度器配置失败: {e}")
            return False

    def _scheduler_loop(self):
        """调度器主循环."""
        logger.info("调度器主循环开始")

        while not self.stop_event.is_set():
            try:
                # 检查是否暂停
                if self.pause_event.is_set():
                    time.sleep(self.config.check_interval)
                    continue

                # 清理已完成的任务线程
                self._cleanup_completed_threads()

                # 检查是否可以执行新任务
                if len(self.running_tasks) < self.config.max_concurrent_tasks:
                    self._try_execute_next_task()

                # 检查运行中任务的超时
                self._check_task_timeouts()

                time.sleep(self.config.check_interval)

            except Exception as e:
                logger.error(f"调度器循环出错: {e}")
                if self.config.auto_pause_on_error:
                    self.pause()
                if self.scheduler_error_callback:
                    self.scheduler_error_callback(e)

        logger.info("调度器主循环结束")

    def _try_execute_next_task(self):
        """尝试执行下一个任务."""
        if self.task_queue.empty():
            return

        try:
            scheduled_task = self.task_queue.get_nowait()

            # 检查任务是否可以执行
            if not self._can_execute_task(scheduled_task):
                # 重新放回队列
                self.task_queue.put(scheduled_task)
                return

            # 检查依赖
            if not self._check_dependencies(scheduled_task):
                # 重新放回队列
                self.task_queue.put(scheduled_task)
                return

            # 执行任务
            self._execute_task(scheduled_task)

        except Exception as e:
            logger.error(f"尝试执行任务失败: {e}")

    def _can_execute_task(self, scheduled_task: ScheduledTask) -> bool:
        """检查任务是否可以执行."""
        # 检查调度时间
        if scheduled_task.scheduled_time > datetime.now():
            return False

        # 检查游戏状态
        if self.config.scene_based_scheduling:
            current_scene = self.game_detector.detect_current_scene()
            suitable_tasks = self.scene_task_mapping.get(current_scene, [])

            if scheduled_task.task.task_type not in suitable_tasks:
                logger.debug(
                    f"当前场景 {current_scene.value} 不适合执行任务 {scheduled_task.task.task_type.value}"
                )
                return False

        # 检查重试延迟
        if (
            scheduled_task.last_attempt
            and datetime.now() - scheduled_task.last_attempt
            < timedelta(seconds=self.config.retry_delay)
        ):
            return False

        return True

    def _check_dependencies(self, scheduled_task: ScheduledTask) -> bool:
        """检查任务依赖."""
        for dep_task_id in scheduled_task.dependencies:
            if dep_task_id not in self.completed_tasks:
                logger.debug(
                    f"任务 {scheduled_task.task.task_id} 等待依赖任务 {dep_task_id} 完成"
                )
                return False
        return True

    def _execute_task(self, scheduled_task: ScheduledTask):
        """执行任务."""
        task = scheduled_task.task
        task_id = task.task_id

        # 更新任务状态
        self.task_manager.update_task_status(task_id, TaskStatus.RUNNING)
        scheduled_task.last_attempt = datetime.now()

        # 创建任务执行线程
        task_thread = threading.Thread(
            target=self._task_execution_wrapper, args=(scheduled_task,), daemon=True
        )

        # 记录运行中的任务
        self.running_tasks[task_id] = task_thread

        # 启动任务
        task_thread.start()

        # 调用回调
        if self.task_started_callback:
            self.task_started_callback(task)

        logger.info(f"开始执行任务: {task.name} (ID: {task_id})")

    def _task_execution_wrapper(self, scheduled_task: ScheduledTask):
        """任务执行包装器."""
        task = scheduled_task.task
        task_id = task.task_id

        try:
            # 执行任务
            result = self._run_task_actions(task)

            if result == TaskExecutionResult.SUCCESS:
                # 任务成功
                self.task_manager.update_task_status(task_id, TaskStatus.COMPLETED)
                self.completed_tasks.append(task_id)

                if self.task_completed_callback:
                    self.task_completed_callback(task, result)

                logger.info(f"任务执行成功: {task.name}")

            elif result == TaskExecutionResult.RETRY:
                # 需要重试
                scheduled_task.retry_count += 1

                if scheduled_task.retry_count < self.config.max_retry_count:
                    # 重新加入队列
                    retry_time = datetime.now() + timedelta(
                        seconds=self.config.retry_delay
                    )
                    scheduled_task.scheduled_time = retry_time
                    self.task_queue.put(scheduled_task)

                    logger.info(
                        f"任务将重试: {task.name} (第{scheduled_task.retry_count}次)"
                    )
                else:
                    # 重试次数用尽，标记为失败
                    self.task_manager.update_task_status(task_id, TaskStatus.FAILED)
                    self.failed_tasks.append(task_id)

                    if self.task_failed_callback:
                        self.task_failed_callback(task, "重试次数用尽")

                    logger.error(f"任务重试次数用尽，执行失败: {task.name}")

            else:
                # 任务失败
                self.task_manager.update_task_status(task_id, TaskStatus.FAILED)
                self.failed_tasks.append(task_id)

                if self.task_failed_callback:
                    self.task_failed_callback(task, f"执行结果: {result.value}")

                logger.error(f"任务执行失败: {task.name}")

        except Exception as e:
            # 异常处理
            self.task_manager.update_task_status(task_id, TaskStatus.FAILED)
            self.failed_tasks.append(task_id)

            if self.task_failed_callback:
                self.task_failed_callback(task, str(e))

            logger.error(f"任务执行异常: {task.name} - {e}")

        finally:
            # 清理运行中的任务记录
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

    def _run_task_actions(self, task: Task) -> TaskExecutionResult:
        """执行任务操作."""
        try:
            # 确保游戏窗口在前台
            if not self.game_detector.bring_game_to_front():
                logger.warning("无法将游戏窗口置于前台")
                return TaskExecutionResult.RETRY

            # 等待游戏窗口稳定
            wait_time = self._get_config_value("scheduler.game_window_wait_time", 1.0)
            time.sleep(wait_time)

            # 执行任务配置中的操作序列
            for action_data in task.config.get("actions", []):
                if self.stop_event.is_set():
                    return TaskExecutionResult.CANCELLED

                # 执行单个操作
                success = self.automation_controller.execute_action_from_dict(
                    action_data
                )
                if not success:
                    logger.warning(f"操作执行失败: {action_data}")
                    return TaskExecutionResult.RETRY

            return TaskExecutionResult.SUCCESS

        except Exception as e:
            logger.error(f"执行任务操作时出错: {e}")
            return TaskExecutionResult.FAILED

    def _calculate_task_priority(self, task: Task) -> int:
        """计算任务优先级."""
        # 从配置获取基础优先级映射
        default_base_priority = {
            TaskPriority.LOW: 1,
            TaskPriority.MEDIUM: 5,
            TaskPriority.HIGH: 10,
            TaskPriority.URGENT: 20,
        }
        
        if self.config_manager:
            base_priority_mapping = self.config_manager.get("scheduler.base_priority_mapping", default_base_priority)
        else:
            base_priority_mapping = default_base_priority
            
        base_priority = base_priority_mapping.get(task.priority, 5)

        # 根据任务类型调整优先级 - 从配置获取
        default_type_bonus = {
            TaskType.DAILY_MISSION: 5,
            TaskType.COMBAT_TRAINING: 3,
            TaskType.EXPLORATION: 2,
            TaskType.CUSTOM: 1,
        }
        
        if self.config_manager:
            type_bonus_mapping = self.config_manager.get("scheduler.type_bonus_mapping", default_type_bonus)
        else:
            type_bonus_mapping = default_type_bonus
            
        type_bonus = type_bonus_mapping.get(task.task_type, 1)

        # 根据当前游戏场景调整优先级
        current_scene = self.game_detector.detect_current_scene()
        suitable_tasks = self.scene_task_mapping.get(current_scene, [])

        scene_bonus = 0
        if task.task_type in suitable_tasks:
            scene_bonus = int(base_priority * self.config.priority_boost_factor)

        return base_priority + type_bonus + scene_bonus

    def _cleanup_completed_threads(self):
        """清理已完成的线程."""
        completed_task_ids = []

        for task_id, thread in self.running_tasks.items():
            if not thread.is_alive():
                completed_task_ids.append(task_id)

        for task_id in completed_task_ids:
            del self.running_tasks[task_id]

    def _check_task_timeouts(self):
        """检查任务超时."""
        # TODO: 实现任务超时检查逻辑
        # 需要记录任务开始时间并检查是否超时
        for task_id, thread in self.running_tasks.items():
            # 这里需要记录任务开始时间，简化实现
            # 实际应该在任务开始时记录时间戳
            pass

    def _stop_all_running_tasks(self):
        """停止所有运行中的任务."""
        for task_id, thread in self.running_tasks.items():
            try:
                # 设置停止标志
                self.stop_event.set()

                # 等待线程结束
                if thread.is_alive():
                    timeout = self._get_config_value("scheduler.task_stop_timeout", 2.0)
                    thread.join(timeout=timeout)

                # 更新任务状态
                self.task_manager.update_task_status(task_id, TaskStatus.CANCELLED)

            except Exception as e:
                logger.error(f"停止任务失败: {task_id} - {e}")

        self.running_tasks.clear()

    def set_callbacks(
        self,
        task_started: Optional[Callable] = None,
        task_completed: Optional[Callable] = None,
        task_failed: Optional[Callable] = None,
        scheduler_error: Optional[Callable] = None,
    ):
        """设置回调函数."""
        self.task_started_callback = task_started
        self.task_completed_callback = task_completed
        self.task_failed_callback = task_failed
        self.scheduler_error_callback = scheduler_error
