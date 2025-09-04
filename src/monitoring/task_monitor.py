# -*- coding: utf-8 -*-
"""
任务状态监控器 - 负责监控任务执行状态和进度更新
"""

from dataclasses import dataclass
from datetime import datetime
from queue import Empty, Queue
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from src.core.logger import get_logger

logger = get_logger(__name__)
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from src.automation.automation_controller import AutomationController
from src.core.enums import TaskStatus
from src.database.db_manager import DatabaseManager


@dataclass
class TaskStatusUpdate:
    """任务状态更新信息"""

    task_id: str
    status: TaskStatus
    progress: float
    message: str
    timestamp: datetime
    execution_time: float = 0.0
    actions_completed: int = 0
    actions_failed: int = 0


class TaskMonitor(QObject):
    """任务状态监控器"""

    # 信号定义
    task_status_changed = pyqtSignal(str, str)  # task_id, status
    task_progress_updated = pyqtSignal(str, float)  # task_id, progress
    task_message_updated = pyqtSignal(str, str)  # task_id, message
    task_completed = pyqtSignal(str, bool, str)  # task_id, success, message

    def __init__(
        self, db_manager: DatabaseManager, automation_controller: AutomationController
    ):
        """初始化任务监控器

        Args:
            db_manager: 数据库管理器
            automation_controller: 自动化控制器
        """
        super().__init__()

        self.db_manager = db_manager
        self.automation_controller = automation_controller

        # 监控状态
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # 任务状态缓存
        self.task_status_cache: Dict[str, TaskStatusUpdate] = {}

        # 状态更新队列
        self.update_queue: Queue[TaskStatusUpdate] = Queue()

        # 监控配置
        self.monitor_interval = 1.0  # 监控间隔（秒）
        self.progress_update_interval = 0.5  # 进度更新间隔（秒）

        # 定时器用于UI更新
        self.ui_update_timer = QTimer()
        self.ui_update_timer.timeout.connect(self._process_updates)

        logger.info("任务监控器初始化完成")

    def start_monitoring(self):
        """开始监控任务状态"""
        if self.is_monitoring:
            logger.warning("任务监控器已在运行")
            return

        self.is_monitoring = True
        self.stop_event.clear()

        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

        # 启动UI更新定时器
        self.ui_update_timer.start(100)  # 100ms间隔更新UI

        logger.info("任务监控器开始运行")

    def stop_monitoring(self):
        """停止监控任务状态"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        self.stop_event.set()

        # 停止UI更新定时器
        self.ui_update_timer.stop()

        # 等待监控线程结束
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=3.0)

        logger.info("任务监控器已停止")

    def get_task_status(self, task_id: str) -> Optional[TaskStatusUpdate]:
        """获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            Optional[TaskStatusUpdate]: 任务状态信息
        """
        return self.task_status_cache.get(task_id)

    def get_all_task_status(self) -> Dict[str, TaskStatusUpdate]:
        """获取所有任务状态

        Returns:
            Dict[str, TaskStatusUpdate]: 所有任务状态
        """
        return self.task_status_cache.copy()

    def update_task_progress(self, task_id: str, progress: float, message: str = ""):
        """手动更新任务进度

        Args:
            task_id: 任务ID
            progress: 进度百分比 (0.0-1.0)
            message: 状态消息
        """
        # 获取当前任务状态
        current_status = self.task_status_cache.get(task_id)
        if current_status:
            status = current_status.status
        else:
            # 从数据库获取状态
            task_data = self.db_manager.get_task_by_id(task_id)
            if task_data:
                status = TaskStatus(task_data["status"])
            else:
                logger.warning(f"未找到任务: {task_id}")
                return

        # 创建状态更新
        update = TaskStatusUpdate(
            task_id=task_id,
            status=status,
            progress=progress,
            message=message,
            timestamp=datetime.now(),
        )

        # 添加到更新队列
        self.update_queue.put(update)

        # 更新数据库
        self.db_manager.update_task(task_id, progress=progress)
        if message:
            self.db_manager.add_execution_log(task_id, "INFO", message)

    def _monitor_loop(self):
        """监控主循环"""
        logger.info("任务监控循环开始")

        while not self.stop_event.is_set():
            try:
                # 获取所有活动任务
                active_tasks = self._get_active_tasks()

                # 监控每个活动任务
                for task_id in active_tasks:
                    self._monitor_task(task_id)

                # 等待下次监控
                time.sleep(self.monitor_interval)

            except Exception as e:
                logger.error(f"任务监控异常: {e}")
                time.sleep(1.0)

        logger.info("任务监控循环结束")

    def _get_active_tasks(self) -> List[str]:
        """获取活动任务列表

        Returns:
            List[str]: 活动任务ID列表
        """
        try:
            # 获取所有非完成状态的任务
            active_statuses = ["created", "running", "paused"]
            tasks = []

            for status in active_statuses:
                user_tasks = self.db_manager.get_tasks_by_user("default_user", status)
                tasks.extend([task["task_id"] for task in user_tasks])

            return tasks

        except Exception as e:
            logger.error(f"获取活动任务失败: {e}")
            return []

    def _monitor_task(self, task_id: str):
        """监控单个任务

        Args:
            task_id: 任务ID
        """
        try:
            # 从数据库获取任务信息
            task_data = self.db_manager.get_task_by_id(task_id)
            if not task_data:
                return

            # 获取当前状态
            current_status = TaskStatus(task_data["status"])
            progress = task_data.get("progress", 0.0)

            # 检查自动化控制器状态
            if (
                self.automation_controller.current_task_id == task_id
                and self.automation_controller.task_status != current_status
            ):
                # 状态不同步，更新数据库
                new_status = self.automation_controller.task_status
                self.db_manager.update_task_status(task_id, new_status.value)
                current_status = new_status

            # 计算执行时间
            execution_time = 0.0
            if task_data.get("last_execution"):
                start_time = datetime.fromisoformat(task_data["last_execution"])
                execution_time = (datetime.now() - start_time).total_seconds()

            # 创建状态更新
            update = TaskStatusUpdate(
                task_id=task_id,
                status=current_status,
                progress=progress,
                message=f"任务{current_status.value}",
                timestamp=datetime.now(),
                execution_time=execution_time,
                actions_completed=self.automation_controller.stats.get(
                    "actions_executed", 0
                ),
                actions_failed=self.automation_controller.stats.get(
                    "actions_failed", 0
                ),
            )

            # 检查状态是否有变化
            previous_update = self.task_status_cache.get(task_id)
            if (
                not previous_update
                or previous_update.status != update.status
                or abs(previous_update.progress - update.progress) > 0.01
            ):

                # 添加到更新队列
                self.update_queue.put(update)

        except Exception as e:
            logger.error(f"监控任务 {task_id} 失败: {e}")

    def _process_updates(self):
        """处理状态更新队列"""
        try:
            while not self.update_queue.empty():
                try:
                    update = self.update_queue.get_nowait()
                    self._apply_update(update)
                except Empty:
                    break
        except Exception as e:
            logger.error(f"处理状态更新失败: {e}")

    def _apply_update(self, update: TaskStatusUpdate):
        """应用状态更新

        Args:
            update: 状态更新信息
        """
        # 更新缓存
        previous_update = self.task_status_cache.get(update.task_id)
        self.task_status_cache[update.task_id] = update

        # 发射信号
        if not previous_update or previous_update.status != update.status:
            self.task_status_changed.emit(update.task_id, update.status.value)

        if (
            not previous_update
            or abs(previous_update.progress - update.progress) > 0.01
        ):
            self.task_progress_updated.emit(update.task_id, update.progress)

        if not previous_update or previous_update.message != update.message:
            self.task_message_updated.emit(update.task_id, update.message)

        # 检查任务是否完成
        if update.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.STOPPED,
        ]:
            success = update.status == TaskStatus.COMPLETED
            self.task_completed.emit(update.task_id, success, update.message)

        logger.debug(
            f"任务状态更新: {update.task_id} -> {update.status.value} ({update.progress:.1%})"
        )
