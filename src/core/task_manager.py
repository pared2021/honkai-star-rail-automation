"""任务管理器模块。

提供任务调度、执行和管理功能，是系统的核心组件之一。
"""

import logging
import threading
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from queue import Empty, PriorityQueue
from typing import Any, Callable, Dict, List, Optional


class TaskType(Enum):
    """任务类型枚举。"""
    
    AUTOMATION = "automation"
    MONITORING = "monitoring"
    GAME_DETECTION = "game_detection"
    SYSTEM = "system"
    USER = "user"
    DAILY_TASK = "daily_task"
    SCREENSHOT = "screenshot"


class TaskStatus(Enum):
    """任务状态枚举（兼容性别名）。"""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    TIMEOUT = "timeout"


class ExecutionMode(Enum):
    """任务执行模式枚举。"""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ADAPTIVE = "adaptive"


class TaskState(Enum):
    """任务状态枚举。"""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    TIMEOUT = "timeout"


class TaskPriority(Enum):
    """任务优先级枚举。"""
    
    URGENT = 0  # 最高优先级，数值最小
    HIGH = 1
    MEDIUM = 2
    LOW = 3     # 最低优先级
    NORMAL = 3  # 与LOW相同级别


@dataclass
class Task:
    """任务数据类。"""
    
    id: str
    name: str
    task_type: TaskType
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: Optional[str] = None


@dataclass
class TaskExecution:
    """任务执行信息。"""

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
    """工作线程信息。"""

    worker_id: str
    thread_id: int
    is_busy: bool = False
    current_task: Optional[str] = None
    tasks_completed: int = 0
    total_execution_time: float = 0.0
    last_activity: Optional[datetime] = None


@dataclass
class ResourceLimits:
    """资源限制配置。"""

    max_concurrent_tasks: int = 5
    max_cpu_usage: float = 80.0
    max_memory_usage: float = 85.0
    max_execution_time: int = 300
    priority_boost_threshold: int = 10


class ConcurrentTaskQueue:
    """并发任务队列，支持优先级调度。"""

    def __init__(self):
        """初始化队列。"""
        self.queues: Dict[TaskPriority, PriorityQueue] = {
            priority: PriorityQueue() for priority in TaskPriority
        }
        self._lock = threading.Lock()
        self.task_count = 0

    def put(self, task_execution: TaskExecution) -> None:
        """添加任务到队列。"""
        with self._lock:
            priority_queue = self.queues[task_execution.priority]
            # 使用任务创建时间作为次要排序键
            priority_queue.put(
                (task_execution.priority.value, time.time(), task_execution)
            )
            self.task_count += 1

    def get(self, timeout: Optional[float] = None) -> Optional[TaskExecution]:
        """从队列获取任务（按优先级）。"""
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
        """获取队列总大小。"""
        with self._lock:
            return sum(queue.qsize() for queue in self.queues.values())

    def get_priority_counts(self) -> Dict[TaskPriority, int]:
        """获取各优先级队列的任务数量。"""
        with self._lock:
            return {priority: queue.qsize() for priority, queue in self.queues.items()}


class TaskManager:
    """任务管理器主类。"""

    def __init__(self, db_manager=None, default_user_id: str = "system"):
        """初始化任务管理器。

        Args:
            db_manager: 数据库管理器实例
            default_user_id: 默认用户ID
        """
        self.db_manager = db_manager
        self.default_user_id = default_user_id
        self._logger = logging.getLogger(__name__)

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
        
        self._logger.info(f"TaskManager 初始化完成，用户ID: {default_user_id}")
        
        # 统计信息
        self._stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "cancelled_tasks": 0
        }

    def add_task(self, task_data: Dict[str, Any], user_id: Optional[str] = None) -> Optional[str]:
        """添加任务。

        Args:
            task_data: 任务数据字典
            user_id: 用户ID，如果为None则使用默认用户ID

        Returns:
            任务ID，如果添加失败则返回None
        """
        try:
            # 验证输入参数
            if not isinstance(task_data, dict):
                print(f"无效的任务数据类型: {type(task_data)}")
                return None
            
            if not task_data.get('name'):
                print("任务名称不能为空")
                return None
            
            user_id = user_id or self.default_user_id
            task_id = str(uuid.uuid4())
            
            # 验证优先级
            priority_str = task_data.get('priority', 'medium')
            try:
                if priority_str == 'urgent':
                    priority = TaskPriority.URGENT
                elif priority_str == 'high':
                    priority = TaskPriority.HIGH
                elif priority_str == 'medium':
                    priority = TaskPriority.MEDIUM
                elif priority_str == 'normal':
                    priority = TaskPriority.NORMAL
                elif priority_str == 'low':
                    priority = TaskPriority.LOW
                else:
                    priority = TaskPriority.MEDIUM
            except Exception:
                print(f"无效的优先级 '{priority_str}'，使用默认值 'medium'")
                priority = TaskPriority.MEDIUM
            
            # 创建任务执行对象
            execution = TaskExecution(
                task_id=task_id,
                execution_id=str(uuid.uuid4()),
                priority=priority,
                state=TaskState.QUEUED,
                metadata={
                    'name': task_data.get('name'),
                    'type': task_data.get('type', 'user'),
                    'user_id': user_id,
                    'created_at': datetime.now().isoformat()
                }
            )
            
            # 检查队列容量
            if self._concurrent_task_queue.size() >= 100:
                print("任务队列已满，无法添加新任务")
                return None
            
            # 添加到队列
            self._concurrent_task_queue.put(execution)
            
            # 更新统计信息
            self._stats["total_tasks"] += 1
            
            print(f"任务已添加: {task_id} (名称: {task_data.get('name')}, 优先级: {priority.value})")
            return task_id
            
        except Exception as e:
            print(f"添加任务失败: {str(e)}")
            return None

    async def list_tasks(self, status: Optional[TaskState] = None) -> List[Dict[str, Any]]:
        """列出任务。

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
        """获取任务统计信息。

        Returns:
            统计信息字典
        """
        # 计算各种状态的任务数量
        running_count = len([e for e in self._active_executions.values() if e.state == TaskState.RUNNING])
        queued_count = len([e for e in self._active_executions.values() if e.state == TaskState.QUEUED])
        completed_count = len([e for e in self._completed_executions.values() if e.state == TaskState.COMPLETED])
        failed_count = len([e for e in self._completed_executions.values() if e.state == TaskState.FAILED])
        cancelled_count = len([e for e in self._completed_executions.values() if e.state == TaskState.CANCELLED])
        
        return {
            "total_tasks": self._stats.get("total_tasks", 0),
            "completed_tasks": completed_count,
            "failed_tasks": failed_count,
            "cancelled_tasks": cancelled_count,
            "running_tasks": running_count,
            "queued_tasks": queued_count,
            "total": len(self._active_executions) + len(self._completed_executions)
        }

    async def create_task(self, task_data: Dict[str, Any], user_id: Optional[str] = None) -> Optional[str]:
        """创建任务（异步版本）。

        Args:
            task_data: 任务数据字典
            user_id: 用户ID，如果为None则使用默认用户ID

        Returns:
            任务ID，如果创建失败则返回None
        """
        return self.add_task(task_data, user_id)

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息。

        Args:
            task_id: 任务ID

        Returns:
            任务信息字典，如果任务不存在则返回None
        """
        # 在活动任务中查找
        for execution in self._active_executions.values():
            if execution.task_id == task_id:
                return {
                    "id": execution.task_id,
                    "execution_id": execution.execution_id,
                    "state": execution.state.value,
                    "priority": execution.priority.value,
                    "progress": execution.progress,
                    "start_time": execution.start_time.isoformat() if execution.start_time else None,
                    "end_time": execution.end_time.isoformat() if execution.end_time else None,
                    "result": execution.result,
                    "error": str(execution.error) if execution.error else None,
                    "metadata": execution.metadata
                }
        
        # 在已完成任务中查找
        for execution in self._completed_executions.values():
            if execution.task_id == task_id:
                return {
                    "id": execution.task_id,
                    "execution_id": execution.execution_id,
                    "state": execution.state.value,
                    "priority": execution.priority.value,
                    "progress": execution.progress,
                    "start_time": execution.start_time.isoformat() if execution.start_time else None,
                    "end_time": execution.end_time.isoformat() if execution.end_time else None,
                    "result": execution.result,
                    "error": str(execution.error) if execution.error else None,
                    "metadata": execution.metadata
                }
        
        return None

    async def cancel_concurrent_task(self, execution_id: str) -> bool:
        """取消并发任务。
        
        Args:
            execution_id: 要取消的任务执行ID
            
        Returns:
            是否成功取消
        """
        try:
            # 查找要取消的任务
            if execution_id not in self._active_executions:
                self._logger.warning(f"未找到要取消的任务: {execution_id}")
                return False
            
            execution_to_cancel = self._active_executions[execution_id]
            
            # 更新任务状态
            execution_to_cancel.state = TaskState.CANCELLED
            execution_to_cancel.end_time = datetime.now()
            
            # 移动到已完成任务
            self._completed_executions[execution_id] = execution_to_cancel
            del self._active_executions[execution_id]
            
            # 更新统计
            self._stats["cancelled_tasks"] += 1
            
            self._logger.info(f"任务已取消: {execution_to_cancel.task_id} (执行ID: {execution_id})")
            return True
            
        except Exception as e:
            self._logger.error(f"取消任务失败 {execution_id}: {str(e)}")
            return False

    def start_concurrent_manager(self):
        """启动并发管理器。"""
        try:
            if self._concurrent_manager_running:
                self._logger.warning("并发管理器已在运行中")
                return
            
            self._concurrent_manager_running = True
            self._shutdown_event.clear()
            
            # 启动线程池
            if self._executor is None:
                self._executor = ThreadPoolExecutor(max_workers=self._resource_limits.max_concurrent_tasks)
                self._logger.info(f"线程池已启动，最大工作线程数: {self._resource_limits.max_concurrent_tasks}")
            
            # 启动管理器线程
            if self._concurrent_manager_thread is None or not self._concurrent_manager_thread.is_alive():
                self._concurrent_manager_thread = threading.Thread(
                    target=self._concurrent_manager_loop,
                    daemon=True
                )
                self._concurrent_manager_thread.start()
                self._logger.info("并发管理器线程已启动")
            
            self._logger.info("并发管理器启动成功")
        except Exception as e:
            self._logger.error(f"启动并发管理器失败: {str(e)}")
            self._concurrent_manager_running = False
            raise
    
    def stop_concurrent_manager(self):
        """停止并发管理器。"""
        try:
            if not self._concurrent_manager_running:
                self._logger.warning("并发管理器未在运行")
                return
            
            self._logger.info("开始停止并发管理器")
            self._concurrent_manager_running = False
            self._shutdown_event.set()
            
            # 等待管理器线程结束
            if self._concurrent_manager_thread and self._concurrent_manager_thread.is_alive():
                self._logger.debug("等待管理器线程结束")
                self._concurrent_manager_thread.join(timeout=5.0)
                if self._concurrent_manager_thread.is_alive():
                    self._logger.warning("管理器线程未能在超时时间内结束")
            
            # 关闭线程池
            if self._executor:
                self._logger.debug("关闭线程池")
                self._executor.shutdown(wait=True)
                self._executor = None
                self._logger.info("线程池已关闭")
            
            self._logger.info("并发管理器停止成功")
        except Exception as e:
            self._logger.error(f"停止并发管理器时发生错误: {str(e)}")
            raise
    
    def _concurrent_manager_loop(self):
        """并发管理器主循环。"""
        while self._concurrent_manager_running and not self._shutdown_event.is_set():
            try:
                # 从队列获取任务
                task_execution = self._concurrent_task_queue.get(timeout=1.0)
                if task_execution:
                    # 提交任务到线程池
                    future = self._executor.submit(self._execute_task, task_execution)
                    self._active_executions[task_execution.execution_id] = task_execution
                    
                    # 设置完成回调
                    future.add_done_callback(
                        lambda f, exec_id=task_execution.execution_id: self._on_task_completed(exec_id, f)
                    )
                
                # 检查是否需要关闭
                if self._shutdown_event.wait(0.1):
                    break
                    
            except Exception as e:
                print(f"并发管理器循环错误: {e}")
                time.sleep(1.0)
    
    def _execute_task(self, task_execution: TaskExecution):
        """执行单个任务。"""
        task_execution.state = TaskState.RUNNING
        task_execution.start_time = datetime.now()
        
        task_name = task_execution.metadata.get('name', 'Unknown Task')
        self._logger.info(f"开始执行任务: {task_name} (ID: {task_execution.task_id})")
        
        try:
            # 这里可以根据任务类型执行不同的逻辑
            task_type = task_execution.metadata.get('type', 'user')
            self._logger.debug(f"任务类型: {task_type}")
            
            # 模拟任务执行时间
            execution_time = 1.0
            time.sleep(execution_time)
            
            result = f"任务 {task_name} 执行完成"
            task_execution.result = result
            task_execution.state = TaskState.COMPLETED
            task_execution.progress = 1.0
            
            execution_duration = (datetime.now() - task_execution.start_time).total_seconds()
            self._logger.info(f"任务执行成功: {task_name} (耗时: {execution_duration:.2f}s)")
            
            return result
            
        except Exception as e:
            task_execution.state = TaskState.FAILED
            task_execution.error = e
            task_execution.result = f"任务执行失败: {str(e)}"
            
            execution_duration = (datetime.now() - task_execution.start_time).total_seconds()
            self._logger.error(f"任务执行失败: {task_name} (耗时: {execution_duration:.2f}s) - {str(e)}")
            raise
        finally:
            task_execution.end_time = datetime.now()
    
    def _on_task_completed(self, execution_id: str, future: Future):
        """任务完成回调。"""
        if execution_id in self._active_executions:
            execution = self._active_executions.pop(execution_id)
            self._completed_executions[execution_id] = execution
            
            # 更新统计信息
            if execution.state == TaskState.COMPLETED:
                self._stats["completed_tasks"] += 1
            elif execution.state == TaskState.FAILED:
                self._stats["failed_tasks"] += 1
            
            print(f"任务完成: {execution.task_id} (状态: {execution.state.value})")
    
    def _run_task(self, task_execution: TaskExecution) -> Any:
        """运行任务（测试兼容方法）。
        
        Args:
            task_execution: 任务执行对象
            
        Returns:
            任务执行结果
        """
        task_execution.state = TaskState.RUNNING
        task_execution.start_time = datetime.now()
        
        try:
            # 模拟任务执行
            time.sleep(0.1)  # 短暂延迟模拟执行时间
            result = f"任务 {task_execution.task_id} 执行完成"
            task_execution.result = result
            task_execution.state = TaskState.COMPLETED
            task_execution.progress = 1.0
            task_execution.end_time = datetime.now()
            
            return result
            
        except Exception as e:
            task_execution.state = TaskState.FAILED
            task_execution.error = e
            task_execution.end_time = datetime.now()
            raise
    
    def _task_completed(self, task_execution: TaskExecution, future: Future) -> None:
        """任务完成处理（测试兼容方法）。
        
        Args:
            task_execution: 任务执行对象
            future: Future对象
        """
        try:
            # 处理Future的结果或异常
            if future.exception():
                task_execution.state = TaskState.FAILED
                task_execution.error = future.exception()
                task_execution.end_time = datetime.now()
                self._stats["failed_tasks"] += 1
            else:
                task_execution.state = TaskState.COMPLETED
                task_execution.result = future.result()
                task_execution.end_time = datetime.now()
                self._stats["completed_tasks"] += 1
            
            # 从活动任务中移除并添加到已完成任务
            if task_execution.execution_id in self._active_executions:
                del self._active_executions[task_execution.execution_id]
            self._completed_executions[task_execution.execution_id] = task_execution
            
        except Exception as e:
            self._logger.error(f"处理任务完成时发生错误: {str(e)}")
    
    def submit_concurrent_task(self, task_data: Dict[str, Any]) -> str:
        """提交并发任务。
        
        Args:
            task_data: 任务数据字典
        
        Returns:
            任务执行ID
        """
        # 验证优先级
        priority_str = task_data.get('priority', 'medium')
        try:
            if priority_str == 'urgent':
                priority = TaskPriority.URGENT
            elif priority_str == 'high':
                priority = TaskPriority.HIGH
            elif priority_str == 'medium':
                priority = TaskPriority.MEDIUM
            elif priority_str == 'normal':
                priority = TaskPriority.NORMAL
            elif priority_str == 'low':
                priority = TaskPriority.LOW
            else:
                priority = TaskPriority.MEDIUM
        except Exception:
            priority = TaskPriority.MEDIUM
        
        task_id = str(uuid.uuid4())
        execution = TaskExecution(
            task_id=task_id,
            execution_id=str(uuid.uuid4()),
            priority=priority,
            state=TaskState.QUEUED,
            metadata={
                'name': task_data.get('name'),
                'type': task_data.get('type', 'user'),
                'created_at': datetime.now().isoformat()
            }
        )
        
        self._concurrent_task_queue.put(execution)
        self._active_executions[execution.execution_id] = execution
        self._stats["total_tasks"] += 1
        
        return execution.execution_id

    def get_concurrent_status(self) -> Dict[str, Any]:
        """获取并发管理器状态。

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
    
    def stop_task(self, task_id: str) -> bool:
        """停止任务。
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 停止成功返回True，失败返回False
        """
        try:
            # 查找要停止的任务
            execution_to_stop = None
            execution_id_to_stop = None
            
            # 在活动任务中查找
            for execution_id, execution in self._active_executions.items():
                if execution.task_id == task_id:
                    execution_to_stop = execution
                    execution_id_to_stop = execution_id
                    break
            
            if execution_to_stop is None:
                self._logger.warning(f"未找到要停止的任务: {task_id}")
                return False
            
            # 更新任务状态
            execution_to_stop.state = TaskState.CANCELLED
            execution_to_stop.end_time = datetime.now()
            
            # 移动到已完成任务
            self._completed_executions[execution_id_to_stop] = execution_to_stop
            del self._active_executions[execution_id_to_stop]
            
            # 更新统计
            self._stats["cancelled_tasks"] += 1
            
            self._logger.info(f"任务已停止: {task_id} (执行ID: {execution_id_to_stop})")
            return True
            
        except Exception as e:
            self._logger.error(f"停止任务失败 {task_id}: {str(e)}")
            return False


class TaskExecutor:
    """任务执行器类。

    负责实际执行任务的逻辑。
    """

    def __init__(self, db_manager=None):
        """初始化任务执行器。

        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager
        self._running = False
        self._executor = ThreadPoolExecutor(max_workers=4)

    def start(self):
        """启动执行器。"""
        self._running = True

    def stop(self):
        """停止执行器。"""
        self._running = False
        self._executor.shutdown(wait=True)

    def execute_task(self, task_execution: TaskExecution) -> Any:
        """执行任务。

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
        """异步提交任务。

        Args:
            task_execution: 任务执行信息

        Returns:
            Future对象
        """
        return self._executor.submit(self.execute_task, task_execution)