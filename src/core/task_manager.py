"""任务管理器模块。.

提供任务调度、执行和管理功能，是系统的核心组件之一。
"""

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from queue import Empty, PriorityQueue
import threading
import time
from typing import Any, Callable, Dict, List, Optional
import uuid


class ExecutionMode(Enum):
    """任务执行模式枚举。."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ADAPTIVE = "adaptive"


class TaskState(Enum):
    """任务状态枚举。."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    TIMEOUT = "timeout"


class TaskPriority(Enum):
    """任务优先级枚举。."""

    LOW = 3
    MEDIUM = 2
    HIGH = 1
    URGENT = 0


@dataclass
class TaskExecution:
    """任务执行信息。."""

    task_id: str
    execution_id: str
    priority: TaskPriority
    state: TaskState
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Any = None
    error: Optional[Exception] = None
    worker_id: Optional[str] = None
    progress: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkerInfo:
    """工作线程信息。."""

    worker_id: str
    thread_id: int
    is_busy: bool = False
    current_task: Optional[str] = None
    tasks_completed: int = 0
    total_execution_time: float = 0.0
    last_activity: Optional[datetime] = None


@dataclass
class ResourceLimits:
    """资源限制配置。."""

    max_concurrent_tasks: int = 5
    max_cpu_usage: float = 80.0
    max_memory_usage: float = 85.0
    max_execution_time: int = 300
    priority_boost_threshold: int = 10


class ConcurrentTaskQueue:
    """并发任务队列，支持优先级调度。."""

    def __init__(self):
        """初始化队列。."""
        self.queues: Dict[TaskPriority, PriorityQueue] = {
            priority: PriorityQueue() for priority in TaskPriority
        }
        self._lock = threading.Lock()
        self.task_count = 0

    def put(self, task_execution: TaskExecution) -> None:
        """添加任务到队列。."""
        with self._lock:
            priority_queue = self.queues[task_execution.priority]
            # 使用任务创建时间作为次要排序键
            priority_queue.put(
                (task_execution.priority.value, time.time(), task_execution)
            )
            self.task_count += 1

    def get(self, timeout: Optional[float] = None) -> Optional[TaskExecution]:
        """从队列获取任务（按优先级）。."""
        with self._lock:
            # 按优先级顺序检查队列
            for priority in sorted(TaskPriority, key=lambda p: p.value):
                queue = self.queues[priority]
                try:
                    _, _, task_execution = queue.get_nowait()
                    task_execution_typed: TaskExecution = task_execution
                    return task_execution_typed
                except Empty:
                    continue
            return None

    def size(self) -> int:
        """获取队列总大小。."""
        with self._lock:
            return sum(queue.qsize() for queue in self.queues.values())

    def get_priority_counts(self) -> Dict[TaskPriority, int]:
        """获取各优先级队列的任务数量。."""
        with self._lock:
            return {priority: queue.qsize() for priority, queue in self.queues.items()}


class TaskManager:
    """任务管理器主类。."""

    def __init__(self, db_manager=None, default_user_id: str = "system"):
        """初始化任务管理器。.

        Args:
            db_manager: 数据库管理器实例
            default_user_id: 默认用户ID
        """
        self.db_manager = db_manager
        self.default_user_id = default_user_id

        # 并发任务管理
        self._concurrent_task_queue = ConcurrentTaskQueue()
        self._active_executions: Dict[str, TaskExecution] = {}
        self._completed_executions: Dict[str, TaskExecution] = {}
        self._workers: Dict[str, WorkerInfo] = {}

        # 线程池和管理器
        self._executor: Optional[ThreadPoolExecutor] = None
        self._concurrent_manager_thread: Optional[threading.Thread] = None
        self._concurrent_manager_running = False
        self._shutdown_event = threading.Event()

        # 资源限制
        self._resource_limits = ResourceLimits()

        # 统计信息
        self._stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "cancelled_tasks": 0,
        }

        # 初始化任务执行器（模拟）
        try:
            from .task_executor import TaskExecutor  # type: ignore

            self._task_executor = TaskExecutor()
        except (ImportError, AttributeError):
            # 如果TaskExecutor不存在，创建一个模拟对象
            self._task_executor = type("MockTaskExecutor", (), {})()

    def start_concurrent_manager(self) -> None:
        """启动并发任务管理器。."""
        if self._concurrent_manager_running:
            return

        self._concurrent_manager_running = True
        self._shutdown_event.clear()

        # 创建线程池
        self._executor = ThreadPoolExecutor(
            max_workers=self._resource_limits.max_concurrent_tasks,
            thread_name_prefix="TaskManager",
        )

        # 启动管理器线程
        self._concurrent_manager_thread = threading.Thread(
            target=self._concurrent_manager_loop, name="ConcurrentTaskManager"
        )
        self._concurrent_manager_thread.start()

    def stop_concurrent_manager(self) -> None:
        """停止并发任务管理器。."""
        if not self._concurrent_manager_running:
            return

        self._concurrent_manager_running = False
        self._shutdown_event.set()

        # 等待管理器线程结束
        if self._concurrent_manager_thread:
            self._concurrent_manager_thread.join(timeout=5.0)

        # 关闭线程池
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None

    def _concurrent_manager_loop(self) -> None:
        """并发任务管理器主循环。."""
        while self._concurrent_manager_running and not self._shutdown_event.is_set():
            try:
                # 检查是否有可用的工作线程
                if (
                    len(self._active_executions)
                    >= self._resource_limits.max_concurrent_tasks
                ):
                    time.sleep(0.1)
                    continue

                # 从队列获取任务
                task_execution = self._concurrent_task_queue.get()
                if task_execution is None:
                    time.sleep(0.1)
                    continue

                # 提交任务执行
                self._execute_task(task_execution)

            except Exception as e:
                # 记录错误但继续运行
                print(f"Concurrent manager error: {e}")
                time.sleep(0.1)

    def _execute_task(self, task_execution: TaskExecution) -> None:
        """执行任务。."""
        if not self._executor:
            return

        # 更新任务状态
        task_execution.state = TaskState.RUNNING
        task_execution.start_time = datetime.now()
        self._active_executions[task_execution.execution_id] = task_execution

        # 提交到线程池
        future = self._executor.submit(self._run_task, task_execution)
        future.add_done_callback(lambda f: self._task_completed(task_execution, f))

    def _run_task(self, task_execution: TaskExecution) -> Any:
        """运行任务的实际逻辑。."""
        try:
            # 模拟任务执行
            time.sleep(0.1)  # 模拟工作
            return f"Task {task_execution.task_id} completed"
        except Exception as e:
            task_execution.error = e
            raise

    def _task_completed(self, task_execution: TaskExecution, future: Future) -> None:
        """任务完成回调。."""
        task_execution.end_time = datetime.now()

        try:
            result = future.result()
            task_execution.result = result
            task_execution.state = TaskState.COMPLETED
            self._stats["completed_tasks"] += 1
        except Exception as e:
            task_execution.error = e
            task_execution.state = TaskState.FAILED
            self._stats["failed_tasks"] += 1

        # 移动到完成列表
        if task_execution.execution_id in self._active_executions:
            del self._active_executions[task_execution.execution_id]
        self._completed_executions[task_execution.execution_id] = task_execution

    def submit_concurrent_task(
        self, task_id: str, priority: TaskPriority = TaskPriority.MEDIUM, **kwargs
    ) -> str:
        """提交并发任务。.

        Args:
            task_id: 任务ID
            priority: 任务优先级
            **kwargs: 其他任务参数

        Returns:
            执行ID
        """
        execution_id = str(uuid.uuid4())

        task_execution = TaskExecution(
            task_id=task_id,
            execution_id=execution_id,
            priority=priority,
            state=TaskState.QUEUED,
        )

        self._concurrent_task_queue.put(task_execution)
        self._stats["total_tasks"] += 1

        return execution_id

    async def cancel_concurrent_task(self, execution_id: str) -> bool:
        """取消并发任务。.

        Args:
            execution_id: 执行ID

        Returns:
            是否成功取消
        """
        if execution_id in self._active_executions:
            execution = self._active_executions[execution_id]
            execution.state = TaskState.CANCELLED
            execution.end_time = datetime.now()

            # 移动到完成列表
            self._completed_executions[execution_id] = execution
            del self._active_executions[execution_id]

            self._stats["cancelled_tasks"] += 1
            return True

        return False

    async def create_task(
        self,
        func: Callable,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
        priority: int = 1,
        **options,
    ) -> str:
        """创建任务。.

        Args:
            func: 要执行的函数
            args: 函数参数
            kwargs: 函数关键字参数
            name: 任务名称
            priority: 任务优先级
            **options: 其他选项

        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())

        # 将优先级转换为TaskPriority
        if priority == 0:
            task_priority = TaskPriority.URGENT
        elif priority == 1:
            task_priority = TaskPriority.HIGH
        elif priority == 2:
            task_priority = TaskPriority.MEDIUM
        else:
            task_priority = TaskPriority.LOW

        # 提交到并发队列
        self.submit_concurrent_task(task_id=task_id, priority=task_priority)

        return task_id

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息。.

        Args:
            task_id: 任务ID

        Returns:
            任务信息字典
        """
        # 在活动任务中查找
        for execution in self._active_executions.values():
            if execution.task_id == task_id:
                return {
                    "id": task_id,
                    "state": execution.state,
                    "progress": execution.progress,
                    "result": execution.result,
                    "error": execution.error,
                }

        # 在完成任务中查找
        for execution in self._completed_executions.values():
            if execution.task_id == task_id:
                return {
                    "id": task_id,
                    "state": execution.state,
                    "progress": execution.progress,
                    "result": execution.result,
                    "error": execution.error,
                }

        return None

    async def list_tasks(
        self, status: Optional[TaskState] = None
    ) -> List[Dict[str, Any]]:
        """列出任务。.

        Args:
            status: 过滤状态

        Returns:
            任务列表
        """
        tasks = []

        # 收集所有任务
        all_executions = list(self._active_executions.values()) + list(
            self._completed_executions.values()
        )

        for execution in all_executions:
            if status is None or execution.state == status:
                tasks.append(
                    {
                        "id": execution.task_id,
                        "name": f"Task {execution.task_id}",
                        "state": execution.state,
                        "progress": execution.progress,
                        "start_time": execution.start_time,
                        "end_time": execution.end_time,
                    }
                )

        return tasks

    async def get_task_statistics(self) -> Dict[str, int]:
        """获取任务统计信息。.

        Returns:
            统计信息字典
        """
        stats = self._stats.copy()
        stats.update(
            {
                "created": len(self._active_executions)
                + len(self._completed_executions),
                "running": len(self._active_executions),
                "total": stats["total_tasks"],
            }
        )
        return stats

    def get_concurrent_status(self) -> Dict[str, Any]:
        """获取并发管理器状态。.

        Returns:
            状态信息字典
        """
        return {
            "manager_running": self._concurrent_manager_running,
            "queue_size": self._concurrent_task_queue.size(),
            "active_executions": len(self._active_executions),
            "completed_executions": len(self._completed_executions),
            "priority_counts": (self._concurrent_task_queue.get_priority_counts()),
            "stats": self._stats.copy(),
        }


class TaskExecutor:
    """任务执行器类。.

    负责实际执行任务的逻辑。
    """

    def __init__(self, db_manager=None):
        """初始化任务执行器。.

        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager
        self._running = False
        self._executor = ThreadPoolExecutor(max_workers=4)

    def start(self):
        """启动执行器。."""
        self._running = True

    def stop(self):
        """停止执行器。."""
        self._running = False
        self._executor.shutdown(wait=True)

    def execute_task(self, task_execution: TaskExecution) -> Any:
        """执行任务。.

        Args:
            task_execution: 任务执行信息

        Returns:
            任务执行结果
        """
        if not self._running:
            raise RuntimeError("TaskExecutor is not running")

        # 模拟任务执行
        task_execution.state = TaskState.RUNNING
        task_execution.start_time = datetime.now()

        try:
            # 这里应该是实际的任务执行逻辑
            result = f"Task {task_execution.task_id} completed"
            task_execution.state = TaskState.COMPLETED
            task_execution.result = result
            return result
        except Exception as e:
            task_execution.state = TaskState.FAILED
            task_execution.result = str(e)
            raise
        finally:
            task_execution.end_time = datetime.now()

    def submit_async_task(self, task_execution: TaskExecution) -> Future:
        """异步提交任务。.

        Args:
            task_execution: 任务执行信息

        Returns:
            Future对象
        """
        return self._executor.submit(self.execute_task, task_execution)
