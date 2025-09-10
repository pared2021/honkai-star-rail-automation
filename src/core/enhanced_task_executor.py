"""增强任务执行引擎模块.

提供完整的任务执行引擎，包括任务队列管理、执行调度、状态跟踪和错误处理。
"""

import asyncio
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from queue import PriorityQueue, Empty
from typing import Any, Dict, List, Optional, Callable, Union
from threading import Lock, Event
import logging

from .events import EventBus
from .logger import get_logger
from .error_handler import ErrorHandler, ErrorSeverity
from .game_operator import GameOperator, OperationResult
from .task_executor import TaskExecutor as BaseTaskExecutor, ActionConfig, ExecutionResult


class TaskType(Enum):
    """任务类型枚举。"""
    DAILY_MISSION = "daily_mission"
    RESOURCE_FARMING = "resource_farming"
    BATTLE_PASS = "battle_pass"
    MAIL_COLLECTION = "mail_collection"
    CUSTOM = "custom"
    SYSTEM = "system"


class TaskPriority(Enum):
    """任务优先级枚举。"""
    URGENT = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKGROUND = 5


class TaskStatus(Enum):
    """任务状态枚举。"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class TaskConfig:
    """任务配置。"""
    task_id: str
    task_type: TaskType
    name: str
    description: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    timeout: float = 300.0  # 5分钟默认超时
    retry_count: int = 3
    retry_delay: float = 5.0
    parameters: Dict[str, Any] = field(default_factory=dict)
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __lt__(self, other):
        """支持优先级队列排序。"""
        return self.priority.value < other.priority.value


@dataclass
class TaskExecution:
    """任务执行信息。"""
    execution_id: str
    task_config: TaskConfig
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    progress: float = 0.0
    result: Any = None
    error: Optional[Exception] = None
    retry_count: int = 0
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def task_id(self) -> str:
        return self.task_config.task_id
    
    @property
    def is_completed(self) -> bool:
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
    
    @property
    def is_running(self) -> bool:
        return self.status == TaskStatus.RUNNING
    
    def complete(self, result: Any = None):
        """标记任务为完成状态。"""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.end_time = datetime.now()
    
    def fail(self, error: Exception):
        """标记任务为失败状态。"""
        self.status = TaskStatus.FAILED
        self.error = error
        self.end_time = datetime.now()
        self.error_message = str(error)  # 添加error_message属性


class TaskQueue:
    """任务队列管理器。"""
    
    def __init__(self, max_size: int = 1000):
        """初始化任务队列。
        
        Args:
            max_size: 队列最大容量
        """
        self.max_size = max_size
        self._queue = PriorityQueue(maxsize=max_size)
        self._lock = Lock()
        self._task_map: Dict[str, TaskConfig] = {}
        
    def put(self, task_config: TaskConfig) -> bool:
        """添加任务到队列。
        
        Args:
            task_config: 任务配置
            
        Returns:
            是否添加成功
        """
        try:
            with self._lock:
                if task_config.task_id in self._task_map:
                    return False  # 任务已存在
                
                # 检查队列是否已满
                if self._queue.qsize() >= self.max_size:
                    raise Exception(f"队列已满，最大容量: {self.max_size}")
                
                self._queue.put_nowait((task_config.priority.value, time.time(), task_config))
                self._task_map[task_config.task_id] = task_config
                return True
        except Exception as e:
            if "队列已满" in str(e):
                raise e  # 重新抛出队列满异常
            return False
    
    def get(self, timeout: Optional[float] = None) -> Optional[TaskConfig]:
        """从队列获取任务。
        
        Args:
            timeout: 超时时间
            
        Returns:
            任务配置或None
        """
        try:
            if timeout is None:
                _, _, task_config = self._queue.get_nowait()
            else:
                _, _, task_config = self._queue.get(timeout=timeout)
            
            with self._lock:
                self._task_map.pop(task_config.task_id, None)
            
            return task_config
        except Empty:
            return None
    
    def remove(self, task_id: str) -> bool:
        """从队列移除任务。
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否移除成功
        """
        with self._lock:
            if task_id in self._task_map:
                del self._task_map[task_id]
                # 注意：PriorityQueue不支持直接移除，这里只是从映射中移除
                return True
            return False
    
    def size(self) -> int:
        """获取队列大小。"""
        return self._queue.qsize()
    
    def is_empty(self) -> bool:
        """检查队列是否为空。"""
        return self._queue.empty()
    
    def contains(self, task_id: str) -> bool:
        """检查是否包含指定任务。"""
        with self._lock:
            return task_id in self._task_map


class TaskRunner:
    """任务运行器基类。"""
    
    def __init__(self, task_type: TaskType):
        """初始化任务运行器。
        
        Args:
            task_type: 支持的任务类型
        """
        self.task_type = task_type
        self.logger = get_logger(f"{__name__}.{task_type.value}")
    
    async def run(self, task_execution: TaskExecution, game_operator: GameOperator) -> ExecutionResult:
        """执行任务。
        
        Args:
            task_execution: 任务执行信息
            game_operator: 游戏操作器
            
        Returns:
            执行结果
        """
        raise NotImplementedError("子类必须实现run方法")
    
    async def validate_preconditions(self, task_execution: TaskExecution, game_operator: GameOperator) -> bool:
        """验证前置条件。
        
        Args:
            task_execution: 任务执行信息
            game_operator: 游戏操作器
            
        Returns:
            是否满足前置条件
        """
        return True
    
    async def validate_postconditions(self, task_execution: TaskExecution, game_operator: GameOperator) -> bool:
        """验证后置条件。
        
        Args:
            task_execution: 任务执行信息
            game_operator: 游戏操作器
            
        Returns:
            是否满足后置条件
        """
        return True


class EnhancedTaskExecutor:
    """增强任务执行引擎。"""
    
    def __init__(self, 
                 game_operator: Optional[GameOperator] = None,
                 event_bus: Optional[EventBus] = None,
                 max_workers: int = 4,
                 max_queue_size: int = 1000):
        """初始化任务执行引擎。
        
        Args:
            game_operator: 游戏操作器实例
            event_bus: 事件总线实例
            max_workers: 最大工作线程数
            max_queue_size: 最大队列容量
        """
        self.logger = get_logger(__name__)
        self.game_operator = game_operator or GameOperator()
        self.event_bus = event_bus or EventBus()
        self.error_handler = ErrorHandler()
        
        # 任务队列和执行管理
        self.task_queue = TaskQueue(max_queue_size)
        self.active_executions: Dict[str, TaskExecution] = {}
        self.completed_executions: Dict[str, TaskExecution] = {}
        
        # 任务运行器注册
        self.task_runners: Dict[TaskType, TaskRunner] = {}
        
        # 线程池和控制
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.is_running = False
        self.shutdown_event = Event()
        
        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "cancelled_tasks": 0,
            "retry_tasks": 0
        }
        
        # 注册默认任务运行器
        self._register_default_runners()
        
        self.logger.info("增强任务执行引擎初始化完成")
    
    def _register_default_runners(self):
        """注册默认任务运行器。"""
        # 这里可以注册默认的任务运行器
        # 具体的运行器实现将在后续创建
        pass
    
    def register_task_runner(self, task_runner: TaskRunner):
        """注册任务运行器。
        
        Args:
            task_runner: 任务运行器实例
        """
        self.task_runners[task_runner.task_type] = task_runner
        self.logger.info(f"注册任务运行器: {task_runner.task_type.value}")
    
    async def submit_task(self, task_config: TaskConfig) -> TaskExecution:
        """提交任务到执行队列。
        
        Args:
            task_config: 任务配置
            
        Returns:
            任务执行对象
        """
        # 检查是否有对应的任务运行器
        if task_config.task_type not in self.task_runners:
            raise ValueError(f"未找到任务类型 {task_config.task_type.value} 的运行器")
        
        # 创建任务执行对象
        execution = TaskExecution(
            execution_id=str(uuid.uuid4()),
            task_config=task_config,
            status=TaskStatus.PENDING
        )
        
        # 添加到活跃执行列表
        self.active_executions[execution.execution_id] = execution
        
        try:
            # 添加到任务队列
            success = self.task_queue.put(task_config)
            if not success:
                raise RuntimeError("无法添加任务到队列")
            
            self.stats["total_tasks"] += 1
            
            # 发送任务提交事件
            self.event_bus.emit("task_submitted", {
                "execution_id": execution.execution_id,
                "task_config": task_config
            })
            
            self.logger.info(f"任务已提交: {task_config.name}")
            
        except Exception as e:
            # 如果队列满了，重新抛出异常
            if "队列已满" in str(e):
                raise
            # 其他异常处理
            del self.active_executions[execution.execution_id]
            raise RuntimeError(f"提交任务失败: {e}")
        
        return execution
    
    async def submit_and_wait(self, task_config: TaskConfig) -> ExecutionResult:
        """提交任务并等待执行完成。
        
        Args:
            task_config: 任务配置
            
        Returns:
            执行结果
        """
        execution = await self.submit_task(task_config)
        
        # 如果执行引擎没有启动，直接执行任务
        if not self.is_running:
            result = await self._execute_task(execution)
            return result
        
        # 等待任务完成（最多等待30秒避免无限循环）
        timeout = 30.0
        start_wait_time = time.time()
        while execution.status in [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.RETRYING]:
            if time.time() - start_wait_time > timeout:
                self.logger.error(f"任务等待超时: {task_config.name}")
                execution.status = TaskStatus.FAILED
                execution.error = TimeoutError("任务执行超时")
                break
            await asyncio.sleep(0.1)
        
        return ExecutionResult(
            status=execution.status.value,
            result=execution.result,
            error=execution.error,
            execution_time=execution.execution_time
        )
    
    async def cancel_task(self, execution_id: str) -> bool:
        """取消任务。
        
        Args:
            execution_id: 执行ID
            
        Returns:
            是否取消成功
        """
        if execution_id in self.active_executions:
            task_execution = self.active_executions[execution_id]
            
            if task_execution.status in [TaskStatus.PENDING, TaskStatus.QUEUED]:
                task_execution.status = TaskStatus.CANCELLED
                task_execution.end_time = datetime.now()
                
                # 移动到完成列表
                self.completed_executions[execution_id] = task_execution
                del self.active_executions[execution_id]
                
                self.stats["cancelled_tasks"] += 1
                
                # 发送任务取消事件
                self.event_bus.emit("task_cancelled", {
                    "execution_id": execution_id,
                    "task_execution": task_execution
                })
                
                self.logger.info(f"任务已取消: {task_execution.task_config.name}")
                return True
        
        return False
    
    async def get_task_status(self, execution_id: str) -> Optional[TaskExecution]:
        """获取任务状态。
        
        Args:
            execution_id: 执行ID
            
        Returns:
            任务执行信息
        """
        if execution_id in self.active_executions:
            return self.active_executions[execution_id]
        elif execution_id in self.completed_executions:
            return self.completed_executions[execution_id]
        else:
            return None
    
    async def list_tasks(self, status_filter: Optional[TaskStatus] = None) -> List[TaskExecution]:
        """列出任务。
        
        Args:
            status_filter: 状态过滤器
            
        Returns:
            任务执行列表
        """
        all_executions = list(self.active_executions.values()) + list(self.completed_executions.values())
        
        if status_filter:
            return [exec for exec in all_executions if exec.status == status_filter]
        else:
            return all_executions
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息。
        
        Returns:
            统计信息字典
        """
        active_count = len(self.active_executions)
        completed_count = len(self.completed_executions)
        
        return {
            **self.stats,
            "active_tasks": active_count,
            "completed_tasks_total": completed_count,
            "queue_size": self.task_queue.size(),
            "is_running": self.is_running
        }
    
    async def start(self):
        """启动任务执行引擎。"""
        if self.is_running:
            return
        
        self.is_running = True
        self.shutdown_event.clear()
        
        # 启动任务处理循环
        asyncio.create_task(self._task_processing_loop())
        
        self.logger.info("任务执行引擎已启动")
    
    async def stop(self):
        """停止任务执行引擎。"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.shutdown_event.set()
        
        # 等待所有任务完成
        self.executor.shutdown(wait=True)
        
        self.logger.info("任务执行引擎已停止")
    
    async def _task_processing_loop(self):
        """任务处理循环。"""
        while self.is_running and not self.shutdown_event.is_set():
            try:
                # 从队列获取任务
                task_config = self.task_queue.get(timeout=1.0)
                
                if task_config:
                    # 查找对应的执行对象
                    execution = None
                    for exec_id, exec_obj in self.active_executions.items():
                        if exec_obj.task_config.task_id == task_config.task_id:
                            execution = exec_obj
                            break
                    
                    if execution:
                        # 提交到线程池执行
                        future = self.executor.submit(self._execute_task_sync, execution)
                        # 不等待结果，让任务异步执行
                
            except Exception as e:
                self.logger.error(f"任务处理循环错误: {e}")
                await asyncio.sleep(1.0)
    
    def _execute_task_sync(self, task_execution: TaskExecution):
        """同步执行任务（在线程池中运行）。
        
        Args:
            task_execution: 任务执行对象
        """
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # 在新的事件循环中执行异步任务
            result = loop.run_until_complete(self._execute_task(task_execution))
            return result
        finally:
            loop.close()
    
    async def _execute_task(self, task_execution: TaskExecution) -> ExecutionResult:
        """执行单个任务。
        
        Args:
            task_execution: 任务执行对象
            
        Returns:
            执行结果
        """
        start_time = time.time()
        task_execution.status = TaskStatus.RUNNING
        task_execution.start_time = datetime.now()
        
        try:
            # 获取任务运行器
            runner = self.task_runners.get(task_execution.task_config.task_type)
            if not runner:
                raise ValueError(f"未找到任务类型 {task_execution.task_config.task_type.value} 的运行器")
            
            # 验证前置条件
            if not await runner.validate_preconditions(task_execution, self.game_operator):
                raise RuntimeError("前置条件验证失败")
            
            # 发送任务开始事件
            self.event_bus.emit("task_started", {
                "execution_id": task_execution.execution_id,
                "task_execution": task_execution
            })
            
            # 执行任务
            result = await runner.run(task_execution, self.game_operator)
            
            # 验证后置条件
            if not await runner.validate_postconditions(task_execution, self.game_operator):
                self.logger.warning(f"任务 {task_execution.task_config.name} 后置条件验证失败")
            
            # 更新执行状态
            task_execution.status = TaskStatus.COMPLETED
            task_execution.result = result
            task_execution.end_time = datetime.now()
            task_execution.execution_time = time.time() - start_time
            
            self.stats["completed_tasks"] += 1
            
            # 发送任务完成事件
            self.event_bus.emit("task_completed", {
                "execution_id": task_execution.execution_id,
                "task_execution": task_execution,
                "result": result
            })
            
            self.logger.info(f"任务执行成功: {task_execution.task_config.name}")
            
        except Exception as e:
            # 使用错误处理器处理错误
            error_info = await self.error_handler.handle_error(
                error=e,
                task_id=task_execution.task_config.task_id,
                task_type=task_execution.task_config.task_type.value,
                context={
                    "execution_id": task_execution.execution_id,
                    "task_name": task_execution.task_config.name,
                    "retry_count": task_execution.retry_count,
                    "execution_time": time.time() - start_time
                }
            )
            
            # 处理执行错误
            task_execution.error = e
            task_execution.end_time = datetime.now()
            task_execution.execution_time = time.time() - start_time
            
            # 尝试错误恢复
            recovery_success = await self.error_handler.try_recovery(error_info)
            
            # 检查是否需要重试
            if (task_execution.retry_count < task_execution.task_config.retry_count and 
                (recovery_success or error_info.severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM])):  # 只有轻微或中等错误才重试
                task_execution.retry_count += 1
                task_execution.status = TaskStatus.RETRYING
                
                self.stats["retry_tasks"] += 1
                
                # 延迟后重试
                await asyncio.sleep(task_execution.task_config.retry_delay)
                
                self.logger.warning(f"任务重试 ({task_execution.retry_count}/{task_execution.task_config.retry_count}): {task_execution.task_config.name}")
                
                # 如果执行引擎正在运行，重新提交到队列；否则直接递归重试
                if self.is_running:
                    self.task_queue.put(task_execution.task_config)
                    return ExecutionResult(
                        status=task_execution.status.value,
                        result=task_execution.result,
                        error=task_execution.error,
                        execution_time=task_execution.execution_time
                    )
                else:
                    # 直接重试执行
                    return await self._execute_task(task_execution)
            else:
                task_execution.status = TaskStatus.FAILED
                self.stats["failed_tasks"] += 1
                
                # 发送任务失败事件
                self.event_bus.emit("task_failed", {
                    "execution_id": task_execution.execution_id,
                    "task_execution": task_execution,
                    "error": e,
                    "error_info": error_info
                })
                
                self.logger.error(f"任务执行失败: {task_execution.task_config.name}, 错误: {e}, 错误ID: {error_info.error_id}")
        
        finally:
            # 移动到完成列表
            if task_execution.execution_id in self.active_executions:
                self.completed_executions[task_execution.execution_id] = task_execution
                del self.active_executions[task_execution.execution_id]
        
        return ExecutionResult(
            status=task_execution.status.value,
            result=task_execution.result,
            error=task_execution.error,
            execution_time=task_execution.execution_time
        )