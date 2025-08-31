# -*- coding: utf-8 -*-
"""
多任务并行处理系统 - 支持多个任务同时执行的并发控制
"""

import time
import threading
import queue
import asyncio
from typing import Dict, List, Optional, Callable, Any, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
import uuid
import json

from loguru import logger
from .game_detector import GameDetector, SceneType
from automation.automation_controller import AutomationController
from models.task_model import Task, TaskStatus
from .performance_monitor import PerformanceMonitor, PerformanceLevel


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class ExecutionMode(Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"      # 顺序执行
    PARALLEL = "parallel"          # 并行执行
    ADAPTIVE = "adaptive"          # 自适应执行


class TaskState(Enum):
    """任务状态"""
    QUEUED = "queued"              # 排队中
    RUNNING = "running"            # 运行中
    PAUSED = "paused"              # 暂停
    COMPLETED = "completed"        # 完成
    FAILED = "failed"              # 失败
    CANCELLED = "cancelled"        # 取消
    TIMEOUT = "timeout"            # 超时


@dataclass
class TaskExecution:
    """任务执行信息"""
    task_id: str
    execution_id: str
    priority: TaskPriority
    state: TaskState
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    thread_id: Optional[int] = None
    worker_id: Optional[str] = None
    progress: float = 0.0
    error_message: Optional[str] = None
    result: Optional[Any] = None
    dependencies: List[str] = field(default_factory=list)
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> Optional[timedelta]:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def is_running(self) -> bool:
        return self.state == TaskState.RUNNING
    
    @property
    def is_finished(self) -> bool:
        return self.state in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED, TaskState.TIMEOUT]


@dataclass
class WorkerInfo:
    """工作线程信息"""
    worker_id: str
    thread_id: int
    is_busy: bool = False
    current_task: Optional[str] = None
    tasks_completed: int = 0
    total_execution_time: float = 0.0
    last_activity: Optional[datetime] = None
    capabilities: Set[str] = field(default_factory=set)


@dataclass
class ResourceLimits:
    """资源限制配置"""
    max_concurrent_tasks: int = 4
    max_cpu_usage: float = 80.0
    max_memory_usage: float = 85.0
    max_execution_time: int = 300  # 秒
    priority_boost_threshold: int = 10  # 等待时间超过此值时提升优先级


class TaskQueue:
    """任务队列"""
    
    def __init__(self):
        self.queues: Dict[TaskPriority, queue.PriorityQueue] = {
            priority: queue.PriorityQueue() for priority in TaskPriority
        }
        self.lock = threading.Lock()
        self.task_count = 0
    
    def put(self, task_execution: TaskExecution):
        """添加任务到队列"""
        with self.lock:
            # 使用负的时间戳作为优先级，确保先进先出
            priority_value = (-time.time(), self.task_count, task_execution)
            self.queues[task_execution.priority].put(priority_value)
            self.task_count += 1
    
    def get(self) -> Optional[TaskExecution]:
        """从队列中获取最高优先级的任务"""
        with self.lock:
            # 按优先级从高到低检查队列
            for priority in sorted(TaskPriority, key=lambda x: x.value, reverse=True):
                if not self.queues[priority].empty():
                    _, _, task_execution = self.queues[priority].get()
                    return task_execution
        return None
    
    def size(self) -> int:
        """获取队列总大小"""
        return sum(q.qsize() for q in self.queues.values())
    
    def get_priority_counts(self) -> Dict[TaskPriority, int]:
        """获取各优先级队列的任务数量"""
        return {priority: q.qsize() for priority, q in self.queues.items()}


class TaskWorker:
    """任务工作线程"""
    
    def __init__(self, worker_id: str, game_detector: GameDetector, 
                 automation_controller: AutomationController):
        self.worker_info = WorkerInfo(
            worker_id=worker_id,
            thread_id=threading.get_ident()
        )
        self.game_detector = game_detector
        self.automation_controller = automation_controller
        
        # 工作状态
        self.is_active = False
        self.should_stop = False
        
        # 回调函数
        self.task_started_callback: Optional[Callable] = None
        self.task_completed_callback: Optional[Callable] = None
        self.task_failed_callback: Optional[Callable] = None
        self.progress_callback: Optional[Callable] = None
    
    def execute_task(self, task_execution: TaskExecution) -> bool:
        """执行任务"""
        self.worker_info.is_busy = True
        self.worker_info.current_task = task_execution.task_id
        self.worker_info.last_activity = datetime.now()
        
        task_execution.state = TaskState.RUNNING
        task_execution.start_time = datetime.now()
        task_execution.thread_id = threading.get_ident()
        task_execution.worker_id = self.worker_info.worker_id
        
        logger.info(f"工作线程 {self.worker_info.worker_id} 开始执行任务 {task_execution.task_id}")
        
        # 调用开始回调
        if self.task_started_callback:
            self.task_started_callback(task_execution)
        
        try:
            # 模拟任务执行过程
            success = self._execute_task_logic(task_execution)
            
            if success:
                task_execution.state = TaskState.COMPLETED
                task_execution.end_time = datetime.now()
                self.worker_info.tasks_completed += 1
                
                if task_execution.duration:
                    self.worker_info.total_execution_time += task_execution.duration.total_seconds()
                
                logger.info(f"任务 {task_execution.task_id} 执行成功")
                
                # 调用完成回调
                if self.task_completed_callback:
                    self.task_completed_callback(task_execution)
                
                return True
            else:
                task_execution.state = TaskState.FAILED
                task_execution.end_time = datetime.now()
                task_execution.error_message = "任务执行失败"
                
                logger.error(f"任务 {task_execution.task_id} 执行失败")
                
                # 调用失败回调
                if self.task_failed_callback:
                    self.task_failed_callback(task_execution)
                
                return False
                
        except Exception as e:
            task_execution.state = TaskState.FAILED
            task_execution.end_time = datetime.now()
            task_execution.error_message = str(e)
            
            logger.error(f"任务 {task_execution.task_id} 执行异常: {e}")
            
            # 调用失败回调
            if self.task_failed_callback:
                self.task_failed_callback(task_execution)
            
            return False
        
        finally:
            self.worker_info.is_busy = False
            self.worker_info.current_task = None
    
    def _execute_task_logic(self, task_execution: TaskExecution) -> bool:
        """执行具体的任务逻辑"""
        # 这里实现具体的任务执行逻辑
        # 根据任务类型调用相应的自动化操作
        
        # 模拟任务执行过程，包括进度更新
        total_steps = 10
        for step in range(total_steps):
            if self.should_stop:
                return False
            
            # 模拟执行步骤
            time.sleep(0.5)  # 模拟处理时间
            
            # 更新进度
            progress = (step + 1) / total_steps
            task_execution.progress = progress
            
            # 调用进度回调
            if self.progress_callback:
                self.progress_callback(task_execution)
            
            logger.debug(f"任务 {task_execution.task_id} 进度: {progress:.1%}")
        
        return True
    
    def stop(self):
        """停止工作线程"""
        self.should_stop = True
        self.is_active = False


class MultiTaskManager:
    """多任务并行管理器"""
    
    def __init__(self, game_detector: GameDetector, 
                 automation_controller: AutomationController,
                 performance_monitor: Optional[PerformanceMonitor] = None):
        self.game_detector = game_detector
        self.automation_controller = automation_controller
        self.performance_monitor = performance_monitor
        
        # 任务管理
        self.task_queue = TaskQueue()
        self.active_tasks: Dict[str, TaskExecution] = {}
        self.completed_tasks: Dict[str, TaskExecution] = {}
        self.task_history: List[TaskExecution] = []
        
        # 工作线程管理
        self.workers: Dict[str, TaskWorker] = {}
        self.thread_pool: Optional[ThreadPoolExecutor] = None
        self.worker_futures: Dict[str, Future] = {}
        
        # 配置
        self.resource_limits = ResourceLimits()
        self.execution_mode = ExecutionMode.ADAPTIVE
        
        # 状态
        self.is_running = False
        self.manager_thread: Optional[threading.Thread] = None
        
        # 统计信息
        self.total_tasks_processed = 0
        self.total_execution_time = 0.0
        self.start_time: Optional[datetime] = None
        
        # 回调函数
        self.task_queued_callback: Optional[Callable] = None
        self.task_started_callback: Optional[Callable] = None
        self.task_completed_callback: Optional[Callable] = None
        self.task_failed_callback: Optional[Callable] = None
        self.resource_limit_callback: Optional[Callable] = None
        
        logger.info("多任务并行管理器初始化完成")
    
    def start(self, max_workers: Optional[int] = None):
        """启动多任务管理器"""
        if self.is_running:
            logger.warning("多任务管理器已在运行")
            return
        
        # 确定工作线程数量
        if max_workers is None:
            max_workers = min(self.resource_limits.max_concurrent_tasks, 4)
        
        # 创建线程池
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        
        # 创建工作线程
        for i in range(max_workers):
            worker_id = f"worker_{i+1}"
            worker = TaskWorker(worker_id, self.game_detector, self.automation_controller)
            
            # 设置回调
            worker.task_started_callback = self._on_task_started
            worker.task_completed_callback = self._on_task_completed
            worker.task_failed_callback = self._on_task_failed
            worker.progress_callback = self._on_task_progress
            
            self.workers[worker_id] = worker
        
        # 启动管理线程
        self.is_running = True
        self.start_time = datetime.now()
        self.manager_thread = threading.Thread(target=self._management_loop, daemon=True)
        self.manager_thread.start()
        
        logger.info(f"多任务管理器已启动，工作线程数: {max_workers}")
    
    def stop(self):
        """停止多任务管理器"""
        if not self.is_running:
            return
        
        logger.info("正在停止多任务管理器...")
        
        # 停止管理线程
        self.is_running = False
        
        # 停止所有工作线程
        for worker in self.workers.values():
            worker.stop()
        
        # 等待所有任务完成
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True)
        
        # 等待管理线程结束
        if self.manager_thread and self.manager_thread.is_alive():
            self.manager_thread.join(timeout=5)
        
        logger.info("多任务管理器已停止")
    
    def submit_task(self, task: Task, priority: TaskPriority = TaskPriority.NORMAL,
                   dependencies: Optional[List[str]] = None,
                   resource_requirements: Optional[Dict[str, Any]] = None) -> str:
        """提交任务"""
        execution_id = str(uuid.uuid4())
        
        task_execution = TaskExecution(
            task_id=task.task_id,
            execution_id=execution_id,
            priority=priority,
            state=TaskState.QUEUED,
            dependencies=dependencies or [],
            resource_requirements=resource_requirements or {}
        )
        
        # 检查依赖任务
        if not self._check_dependencies(task_execution):
            logger.warning(f"任务 {task.task_id} 的依赖任务未完成，暂时不能执行")
            return execution_id
        
        # 添加到队列
        self.task_queue.put(task_execution)
        
        logger.info(f"任务已提交: {task.task_id} (执行ID: {execution_id}, 优先级: {priority.name})")
        
        # 调用回调
        if self.task_queued_callback:
            self.task_queued_callback(task_execution)
        
        return execution_id
    
    def cancel_task(self, execution_id: str) -> bool:
        """取消任务"""
        # 检查是否在队列中
        # 注意：这里简化实现，实际需要从优先队列中移除特定任务
        
        # 检查是否在执行中
        if execution_id in self.active_tasks:
            task_execution = self.active_tasks[execution_id]
            task_execution.state = TaskState.CANCELLED
            task_execution.end_time = datetime.now()
            
            # 停止对应的工作线程
            if task_execution.worker_id and task_execution.worker_id in self.workers:
                self.workers[task_execution.worker_id].should_stop = True
            
            logger.info(f"任务已取消: {execution_id}")
            return True
        
        return False
    
    def pause_task(self, execution_id: str) -> bool:
        """暂停任务"""
        if execution_id in self.active_tasks:
            task_execution = self.active_tasks[execution_id]
            if task_execution.state == TaskState.RUNNING:
                task_execution.state = TaskState.PAUSED
                logger.info(f"任务已暂停: {execution_id}")
                return True
        return False
    
    def resume_task(self, execution_id: str) -> bool:
        """恢复任务"""
        if execution_id in self.active_tasks:
            task_execution = self.active_tasks[execution_id]
            if task_execution.state == TaskState.PAUSED:
                task_execution.state = TaskState.RUNNING
                logger.info(f"任务已恢复: {execution_id}")
                return True
        return False
    
    def _management_loop(self):
        """管理循环"""
        while self.is_running:
            try:
                # 检查资源使用情况
                if not self._check_resource_limits():
                    time.sleep(1)
                    continue
                
                # 分配任务给空闲的工作线程
                self._assign_tasks_to_workers()
                
                # 清理完成的任务
                self._cleanup_completed_tasks()
                
                # 检查超时任务
                self._check_timeout_tasks()
                
                time.sleep(0.1)  # 短暂休眠
                
            except Exception as e:
                logger.error(f"管理循环出错: {e}")
                time.sleep(1)
    
    def _assign_tasks_to_workers(self):
        """分配任务给工作线程"""
        # 查找空闲的工作线程
        idle_workers = [w for w in self.workers.values() if not w.worker_info.is_busy]
        
        if not idle_workers:
            return
        
        # 从队列中获取任务
        for _ in range(len(idle_workers)):
            task_execution = self.task_queue.get()
            if not task_execution:
                break
            
            # 检查依赖
            if not self._check_dependencies(task_execution):
                # 重新放回队列
                self.task_queue.put(task_execution)
                continue
            
            # 分配给工作线程
            worker = idle_workers.pop(0)
            self.active_tasks[task_execution.execution_id] = task_execution
            
            # 提交到线程池执行
            future = self.thread_pool.submit(worker.execute_task, task_execution)
            self.worker_futures[task_execution.execution_id] = future
    
    def _check_dependencies(self, task_execution: TaskExecution) -> bool:
        """检查任务依赖"""
        for dep_id in task_execution.dependencies:
            if dep_id not in self.completed_tasks:
                return False
            
            dep_task = self.completed_tasks[dep_id]
            if dep_task.state != TaskState.COMPLETED:
                return False
        
        return True
    
    def _check_resource_limits(self) -> bool:
        """检查资源限制"""
        # 检查并发任务数量
        if len(self.active_tasks) >= self.resource_limits.max_concurrent_tasks:
            return False
        
        # 检查性能指标
        if self.performance_monitor:
            current_metrics = self.performance_monitor.get_current_metrics()
            if current_metrics:
                if (current_metrics.cpu_percent > self.resource_limits.max_cpu_usage or
                    current_metrics.memory_percent > self.resource_limits.max_memory_usage):
                    
                    if self.resource_limit_callback:
                        self.resource_limit_callback(current_metrics)
                    
                    return False
        
        return True
    
    def _cleanup_completed_tasks(self):
        """清理完成的任务"""
        completed_executions = []
        
        for execution_id, future in list(self.worker_futures.items()):
            if future.done():
                completed_executions.append(execution_id)
        
        for execution_id in completed_executions:
            if execution_id in self.active_tasks:
                task_execution = self.active_tasks.pop(execution_id)
                self.completed_tasks[execution_id] = task_execution
                self.task_history.append(task_execution)
                self.total_tasks_processed += 1
                
                if task_execution.duration:
                    self.total_execution_time += task_execution.duration.total_seconds()
            
            if execution_id in self.worker_futures:
                del self.worker_futures[execution_id]
    
    def _check_timeout_tasks(self):
        """检查超时任务"""
        current_time = datetime.now()
        timeout_threshold = timedelta(seconds=self.resource_limits.max_execution_time)
        
        for task_execution in list(self.active_tasks.values()):
            if (task_execution.start_time and 
                current_time - task_execution.start_time > timeout_threshold):
                
                logger.warning(f"任务超时: {task_execution.task_id}")
                
                # 标记为超时
                task_execution.state = TaskState.TIMEOUT
                task_execution.end_time = current_time
                task_execution.error_message = "任务执行超时"
                
                # 停止对应的工作线程
                if task_execution.worker_id and task_execution.worker_id in self.workers:
                    self.workers[task_execution.worker_id].should_stop = True
    
    def _on_task_started(self, task_execution: TaskExecution):
        """任务开始回调"""
        if self.task_started_callback:
            self.task_started_callback(task_execution)
    
    def _on_task_completed(self, task_execution: TaskExecution):
        """任务完成回调"""
        if self.task_completed_callback:
            self.task_completed_callback(task_execution)
    
    def _on_task_failed(self, task_execution: TaskExecution):
        """任务失败回调"""
        if self.task_failed_callback:
            self.task_failed_callback(task_execution)
    
    def _on_task_progress(self, task_execution: TaskExecution):
        """任务进度回调"""
        # 可以在这里更新UI或记录进度
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """获取管理器状态"""
        queue_counts = self.task_queue.get_priority_counts()
        
        worker_stats = {}
        for worker_id, worker in self.workers.items():
            worker_stats[worker_id] = {
                'is_busy': worker.worker_info.is_busy,
                'current_task': worker.worker_info.current_task,
                'tasks_completed': worker.worker_info.tasks_completed,
                'total_execution_time': worker.worker_info.total_execution_time
            }
        
        return {
            'is_running': self.is_running,
            'execution_mode': self.execution_mode.value,
            'queue_size': self.task_queue.size(),
            'queue_by_priority': {p.name: count for p, count in queue_counts.items()},
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.completed_tasks),
            'total_processed': self.total_tasks_processed,
            'average_execution_time': (
                self.total_execution_time / self.total_tasks_processed 
                if self.total_tasks_processed > 0 else 0
            ),
            'workers': worker_stats,
            'uptime': (
                (datetime.now() - self.start_time).total_seconds() 
                if self.start_time else 0
            )
        }
    
    def get_task_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取特定任务状态"""
        # 检查活跃任务
        if execution_id in self.active_tasks:
            task = self.active_tasks[execution_id]
        # 检查已完成任务
        elif execution_id in self.completed_tasks:
            task = self.completed_tasks[execution_id]
        else:
            return None
        
        return {
            'execution_id': task.execution_id,
            'task_id': task.task_id,
            'state': task.state.value,
            'priority': task.priority.name,
            'progress': task.progress,
            'start_time': task.start_time.isoformat() if task.start_time else None,
            'end_time': task.end_time.isoformat() if task.end_time else None,
            'duration': task.duration.total_seconds() if task.duration else None,
            'worker_id': task.worker_id,
            'error_message': task.error_message
        }
    
    def set_callbacks(self, **callbacks):
        """设置回调函数"""
        for name, callback in callbacks.items():
            if hasattr(self, f"{name}_callback"):
                setattr(self, f"{name}_callback", callback)
    
    def update_resource_limits(self, **limits):
        """更新资源限制"""
        for key, value in limits.items():
            if hasattr(self.resource_limits, key):
                setattr(self.resource_limits, key, value)
                logger.info(f"资源限制已更新: {key} = {value}")
    
    def set_execution_mode(self, mode: ExecutionMode):
        """设置执行模式"""
        self.execution_mode = mode
        logger.info(f"执行模式已设置为: {mode.value}")