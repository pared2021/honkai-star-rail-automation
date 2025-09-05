# -*- coding: utf-8 -*-
"""
任务管理器 - 负责任务的创建、查询、更新和删除操作
"""

from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from queue import PriorityQueue, Queue
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import uuid
import weakref

import aiosqlite
import asyncio
from loguru import logger
import psutil

from src.database.db_manager import DatabaseManager
from src.exceptions import TaskStateError, TaskValidationError
from src.models.task_models import Task, TaskConfig, TaskPriority, TaskStatus, TaskType

from .enums import ActionType
from .task_actions import ActionFactory
from .task_executor import TaskExecutor

# TaskConfig和Task类已从models.task_models导入


class ExecutionMode(Enum):
    """执行模式"""

    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"  # 并行执行
    ADAPTIVE = "adaptive"  # 自适应执行


class TaskState(Enum):
    """任务执行状态"""

    QUEUED = "queued"  # 排队中
    RUNNING = "running"  # 运行中
    PAUSED = "paused"  # 暂停
    COMPLETED = "completed"  # 完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 取消
    TIMEOUT = "timeout"  # 超时


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
        return self.state in [
            TaskState.COMPLETED,
            TaskState.FAILED,
            TaskState.CANCELLED,
            TaskState.TIMEOUT,
        ]


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
    
    @classmethod
    def from_config_manager(cls, config_manager, defaults=None):
        """从配置管理器创建资源限制配置."""
        if config_manager is None:
            return cls() if defaults is None else cls(**defaults)
        
        return cls(
            max_concurrent_tasks=config_manager.get("resource_limits.max_concurrent_tasks", 4),
            max_cpu_usage=config_manager.get("resource_limits.max_cpu_usage", 80.0),
            max_memory_usage=config_manager.get("resource_limits.max_memory_usage", 85.0),
            max_execution_time=config_manager.get("resource_limits.max_execution_time", 300),
            priority_boost_threshold=config_manager.get("resource_limits.priority_boost_threshold", 10)
        )


class ConcurrentTaskQueue:
    """并发任务队列"""

    def __init__(self):
        self.queues: Dict[TaskPriority, PriorityQueue] = {
            priority: PriorityQueue() for priority in TaskPriority
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


class TaskManager:
    """异步任务管理器 - 负责任务的创建、管理和执行"""

    def __init__(
        self, db_manager: DatabaseManager, default_user_id: str = "default_user", config_manager=None
    ):
        """初始化任务管理器

        Args:
            db_manager: 数据库管理器
            default_user_id: 默认用户ID
            config_manager: 配置管理器
        """
        self.db_manager = db_manager
        self.default_user_id = default_user_id
        self.config_manager = config_manager
        self.task_executor = TaskExecutor(db_manager)
        
        # 从配置管理器获取配置值
        self._connection_pool = {}
        self._pool_size = config_manager.get("task_manager.pool_size", 10) if config_manager else 10
        self._connection_timeout = config_manager.get("task_manager.connection_timeout", 30) if config_manager else 30
        self._query_cache = {}
        self._cache_size = config_manager.get("task_manager.cache_size", 100) if config_manager else 100
        self._cache_ttl = config_manager.get("task_manager.cache_ttl", 300) if config_manager else 300  # 5分钟缓存过期

        # 状态监控相关
        self._status_monitors = {}  # 任务状态监控器
        self._status_callbacks = {}  # 状态变更回调
        self._monitoring_active = False
        self._monitor_interval = config_manager.get("task_manager.monitor_interval", 5) if config_manager else 5  # 监控间隔（秒）
        self._monitor_task = None

        # 调度相关
        self._scheduler_active = False
        self._scheduler_task = None
        self._scheduler_interval = config_manager.get("task_manager.scheduler_interval", 10) if config_manager else 10  # 调度间隔（秒）
        self._task_dependencies = {}  # 任务依赖关系
        
        # 优先级权重从配置获取
        default_priority_weights = {"low": 1, "medium": 2, "high": 3, "urgent": 4}
        self._priority_weights = config_manager.get("task_manager.priority_weights", default_priority_weights) if config_manager else default_priority_weights

        # 并发执行相关（从MultiTaskManager整合）
        self._max_concurrent_tasks = config_manager.get("task_manager.max_concurrent_tasks", 5) if config_manager else 5
        self._execution_semaphore = asyncio.Semaphore(self._max_concurrent_tasks)
        self._running_tasks = {}  # 正在运行的任务
        self._concurrent_task_queue = ConcurrentTaskQueue()  # 并发任务队列
        self._worker_threads = {}  # 工作线程
        self._thread_pool = ThreadPoolExecutor(max_workers=self._max_concurrent_tasks)
        self._execution_callbacks = {}  # 执行回调函数
        self._worker_futures: Dict[str, Future] = {}  # 工作线程Future对象
        self._active_executions: Dict[str, TaskExecution] = {}  # 活跃的任务执行
        self._completed_executions: Dict[str, TaskExecution] = {}  # 已完成的任务执行
        self._execution_history: List[TaskExecution] = []  # 执行历史

        # 资源限制和配置 - 从配置管理器获取
        max_cpu_usage = config_manager.get("task_manager.max_cpu_usage", 80.0) if config_manager else 80.0
        max_memory_usage = config_manager.get("task_manager.max_memory_usage", 80.0) if config_manager else 80.0
        max_execution_time = config_manager.get("task_manager.max_execution_time", 300) if config_manager else 300
        
        self._resource_limits = ResourceLimits(
            max_concurrent_tasks=self._max_concurrent_tasks,
            max_cpu_usage=max_cpu_usage,
            max_memory_usage=max_memory_usage,
            max_execution_time=max_execution_time,
        )
        
        # 执行模式从配置获取
        execution_mode_str = config_manager.get("task_manager.execution_mode", "adaptive") if config_manager else "adaptive"
        self._execution_mode = ExecutionMode(execution_mode_str)

        # 并发管理状态
        self._concurrent_manager_running = False
        self._concurrent_manager_thread: Optional[threading.Thread] = None
        self._total_executions_processed = 0
        self._total_execution_time = 0.0
        self._concurrent_start_time: Optional[datetime] = None

        logger.info("任务管理器初始化完成")

    @asynccontextmanager
    async def get_async_connection(self):
        """获取异步数据库连接（带连接池管理）"""
        conn = await self._get_pooled_connection()
        try:
            yield conn
        finally:
            await self._return_connection(conn)

    async def _get_pooled_connection(self):
        """从连接池获取连接"""
        current_time = time.time()

        # 清理过期连接
        expired_keys = []
        for key, (conn, timestamp) in self._connection_pool.items():
            if current_time - timestamp > self._connection_timeout:
                expired_keys.append(key)

        for key in expired_keys:
            conn, _ = self._connection_pool.pop(key)
            try:
                await conn.close()
            except:
                pass

        # 如果池中有可用连接，直接返回
        if self._connection_pool:
            key = next(iter(self._connection_pool))
            conn, _ = self._connection_pool.pop(key)
            return conn

        # 创建新连接
        conn = await aiosqlite.connect(self.db_manager.db_path)
        conn.row_factory = aiosqlite.Row

        # 启用WAL模式以减少锁定问题
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA synchronous=NORMAL")
        await conn.execute("PRAGMA cache_size=10000")
        await conn.execute("PRAGMA temp_store=memory")

        return conn

    async def _return_connection(self, conn):
        """将连接返回到连接池"""
        if len(self._connection_pool) < self._pool_size:
            connection_id = id(conn)
            self._connection_pool[connection_id] = (conn, time.time())
        else:
            await conn.close()

    def _get_cache_key(self, query: str, params: tuple = None) -> str:
        """生成查询缓存键"""
        params_str = str(params) if params else ""
        return f"{hash(query + params_str)}"

    async def _cached_query(
        self, query: str, params: tuple = None, cache_key: str = None
    ) -> List[Dict]:
        """执行带缓存的查询"""
        if cache_key is None:
            cache_key = self._get_cache_key(query, params)

        current_time = time.time()

        # 检查缓存
        if cache_key in self._query_cache:
            cached_data, timestamp = self._query_cache[cache_key]
            if current_time - timestamp < self._cache_ttl:
                logger.debug(f"查询缓存命中: {cache_key}")
                return cached_data
            else:
                # 缓存过期，删除
                del self._query_cache[cache_key]

        # 执行查询
        async with self.get_async_connection() as conn:
            cursor = await conn.execute(query, params or ())
            rows = await cursor.fetchall()
            result = [dict(row) for row in rows]

        # 缓存结果（如果缓存未满）
        if len(self._query_cache) < self._cache_size:
            self._query_cache[cache_key] = (result, current_time)
            logger.debug(f"查询结果已缓存: {cache_key}")

        return result

    def _clear_cache(self, pattern: str = None):
        """清理查询缓存"""
        if pattern:
            # 清理匹配模式的缓存
            keys_to_remove = [
                key for key in self._query_cache.keys() if pattern in str(key)
            ]
            for key in keys_to_remove:
                del self._query_cache[key]
            logger.debug(f"清理缓存，模式: {pattern}，清理数量: {len(keys_to_remove)}")
        else:
            # 清理所有缓存
            cache_count = len(self._query_cache)
            self._query_cache.clear()
            logger.debug(f"清理所有缓存，清理数量: {cache_count}")

    async def close_connections(self):
        """关闭所有连接池中的连接"""
        for conn, _ in self._connection_pool.values():
            try:
                await conn.close()
            except:
                pass
        self._connection_pool.clear()
        logger.info("所有数据库连接已关闭")

    async def start_status_monitoring(self, interval: int = None):
        """启动任务状态监控"""
        if self._monitoring_active:
            logger.warning("状态监控已经在运行中")
            return

        # 如果没有指定间隔，使用配置管理器的值或默认值
        if interval is None:
            interval = self.config_manager.get("task_manager.monitor_interval", 5) if self.config_manager else 5
            
        self._monitor_interval = interval
        self._monitoring_active = True
        self._monitor_task = asyncio.create_task(self._monitor_task_status())
        logger.info(f"任务状态监控已启动，监控间隔: {interval}秒")

    async def stop_status_monitoring(self):
        """停止任务状态监控"""
        if not self._monitoring_active:
            logger.warning("状态监控未在运行")
            return

        self._monitoring_active = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("任务状态监控已停止")

    async def _monitor_task_status(self):
        """监控任务状态变更"""
        while self._monitoring_active:
            try:
                # 获取所有正在运行的任务
                running_tasks = await self.list_tasks(status="running", use_cache=False)

                for task in running_tasks:
                    task_id = task["task_id"]

                    # 检查任务是否有监控器
                    if task_id in self._status_monitors:
                        await self._check_task_health(task_id)

                # 清理已完成任务的监控器
                await self._cleanup_completed_monitors()

                await asyncio.sleep(self._monitor_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"状态监控出错: {e}")
                await asyncio.sleep(self._monitor_interval)

    async def _check_task_health(self, task_id: str):
        """检查任务健康状态"""
        try:
            task = await self.get_task(task_id)
            if not task:
                return

            monitor_info = self._status_monitors.get(task_id, {})
            last_check = monitor_info.get("last_check", 0)
            current_time = time.time()

            # 更新监控信息
            self._status_monitors[task_id] = {
                "last_check": current_time,
                "status": task["status"],
                "check_count": monitor_info.get("check_count", 0) + 1,
            }

            # 检查任务是否超时
            if task["status"] == "running":
                last_execution = task.get("last_execution")
                if last_execution:
                    # 解析时间戳
                    if isinstance(last_execution, str):
                        from datetime import datetime

                        last_execution = datetime.fromisoformat(
                            last_execution
                        ).timestamp()
                    elif isinstance(last_execution, datetime):
                        last_execution = last_execution.timestamp()

                    # 检查是否超时（从配置获取或默认30分钟）
                    timeout_threshold = self.config_manager.get("task_manager.task_timeout_threshold", 30 * 60) if self.config_manager else 30 * 60  # 30分钟
                    if current_time - last_execution > timeout_threshold:
                        logger.warning(f"任务 {task_id} 可能已超时")
                        await self._trigger_status_callback(
                            task_id,
                            "timeout",
                            {
                                "message": "任务执行超时",
                                "last_execution": last_execution,
                                "current_time": current_time,
                            },
                        )

        except Exception as e:
            logger.error(f"检查任务 {task_id} 健康状态失败: {e}")

    async def _cleanup_completed_monitors(self):
        """清理已完成任务的监控器"""
        completed_statuses = ["completed", "failed", "cancelled"]
        tasks_to_remove = []

        for task_id in self._status_monitors:
            try:
                task = await self.get_task(task_id)
                if not task or task["status"] in completed_statuses:
                    tasks_to_remove.append(task_id)
            except Exception:
                tasks_to_remove.append(task_id)

        for task_id in tasks_to_remove:
            self._status_monitors.pop(task_id, None)
            self._status_callbacks.pop(task_id, None)
            logger.debug(f"清理任务 {task_id} 的监控器")

    def add_status_monitor(self, task_id: str, callback: callable = None):
        """添加任务状态监控"""
        self._status_monitors[task_id] = {
            "last_check": time.time(),
            "status": None,
            "check_count": 0,
        }

        if callback:
            self._status_callbacks[task_id] = callback

        logger.info(f"已添加任务 {task_id} 的状态监控")

    def remove_status_monitor(self, task_id: str):
        """移除任务状态监控"""
        self._status_monitors.pop(task_id, None)
        self._status_callbacks.pop(task_id, None)
        logger.info(f"已移除任务 {task_id} 的状态监控")

    async def _trigger_status_callback(self, task_id: str, event_type: str, data: Dict):
        """触发状态变更回调"""
        callback = self._status_callbacks.get(task_id)
        if callback:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(task_id, event_type, data)
                else:
                    callback(task_id, event_type, data)
                logger.debug(f"任务 {task_id} 状态回调已触发: {event_type}")
            except Exception as e:
                logger.error(f"执行任务 {task_id} 状态回调失败: {e}")

    async def get_monitoring_status(self) -> Dict[str, Any]:
        """获取监控状态信息"""
        return {
            "monitoring_active": self._monitoring_active,
            "monitor_interval": self._monitor_interval,
            "monitored_tasks": len(self._status_monitors),
            "monitors": dict(self._status_monitors),
        }

    async def start_scheduler(self, interval: int = None):
        """启动任务调度器"""
        if self._scheduler_active:
            logger.warning("任务调度器已经在运行中")
            return

        # 如果没有指定间隔，使用配置管理器的值或默认值
        if interval is None:
            interval = self.config_manager.get("task_manager.scheduler_interval", 10) if self.config_manager else 10
            
        self._scheduler_interval = interval
        self._scheduler_active = True
        self._scheduler_task = asyncio.create_task(self._schedule_tasks())
        logger.info(f"任务调度器已启动，调度间隔: {interval}秒")

    async def stop_scheduler(self):
        """停止任务调度器"""
        if not self._scheduler_active:
            logger.warning("任务调度器未在运行")
            return

        self._scheduler_active = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("任务调度器已停止")

    async def _schedule_tasks(self):
        """任务调度主循环"""
        while self._scheduler_active:
            try:
                # 获取待调度的任务
                pending_tasks = await self.list_tasks(status="pending", use_cache=False)

                if pending_tasks:
                    # 按优先级和依赖关系排序
                    scheduled_tasks = await self._prioritize_tasks(pending_tasks)

                    # 执行可调度的任务
                    for task in scheduled_tasks:
                        if await self._can_execute_task(task):
                            await self._schedule_task_execution(task)

                await asyncio.sleep(self._scheduler_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"任务调度出错: {e}")
                await asyncio.sleep(self._scheduler_interval)

    async def _prioritize_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """按优先级和依赖关系对任务进行排序"""
        # 计算任务优先级分数
        task_scores = []
        for task in tasks:
            score = await self._calculate_task_priority(task)
            task_scores.append((task, score))

        # 按分数降序排序
        task_scores.sort(key=lambda x: x[1], reverse=True)

        # 应用依赖关系约束
        prioritized_tasks = []
        processed_tasks = set()

        for task, score in task_scores:
            task_id = task["task_id"]
            if await self._dependencies_satisfied(task_id, processed_tasks):
                prioritized_tasks.append(task)
                processed_tasks.add(task_id)

        return prioritized_tasks

    async def _calculate_task_priority(self, task: Dict) -> float:
        """计算任务优先级分数"""
        base_score = self._priority_weights.get(task.get("priority", "medium"), 2)

        # 考虑任务创建时间（越早创建优先级越高）
        created_at = task.get("created_at")
        if created_at:
            if isinstance(created_at, str):
                from datetime import datetime

                created_timestamp = datetime.fromisoformat(created_at).timestamp()
            else:
                created_timestamp = (
                    created_at.timestamp()
                    if hasattr(created_at, "timestamp")
                    else created_at
                )

            # 时间权重：每小时增加0.1分
            time_weight = (time.time() - created_timestamp) / 3600 * 0.1
            base_score += time_weight

        # 考虑任务类型权重
        task_type = task.get("task_type", "default")
        type_weights = {
            "system": 1.5,
            "user": 1.0,
            "background": 0.8,
            "maintenance": 0.6,
        }
        type_weight = type_weights.get(task_type, 1.0)
        base_score *= type_weight

        # 考虑重试次数（重试次数越多优先级越低）
        retry_count = task.get("retry_count", 0)
        retry_penalty = retry_count * 0.2
        base_score -= retry_penalty

        return max(base_score, 0.1)  # 确保最小优先级

    async def _dependencies_satisfied(self, task_id: str, processed_tasks: set) -> bool:
        """检查任务依赖是否满足"""
        dependencies = self._task_dependencies.get(task_id, [])

        for dep_id in dependencies:
            # 检查依赖任务是否已完成
            try:
                dep_task = await self.get_task(dep_id)
                if not dep_task or dep_task["status"] not in ["completed"]:
                    return False
            except Exception:
                return False

        return True

    async def _can_execute_task(self, task: Dict) -> bool:
        """检查任务是否可以执行"""
        # 检查调度配置
        config = task.get("config", {})
        if isinstance(config, str):
            try:
                import json

                config = json.loads(config)
            except:
                config = {}

        schedule_config = config.get("schedule", {})

        # 检查调度时间
        if not await self._check_schedule_time(schedule_config):
            return False

        # 检查资源限制
        if not await self._check_resource_limits():
            return False

        return True

    async def _check_schedule_time(self, schedule_config: Dict) -> bool:
        """检查调度时间是否满足"""
        if not schedule_config:
            return True

        schedule_type = schedule_config.get("type")

        if schedule_type == "cron":
            # 简单的cron检查（这里可以集成更完整的cron库）
            cron_expr = schedule_config.get("expression", "")
            # 暂时返回True，实际应该解析cron表达式
            return True

        elif schedule_type == "interval":
            interval = schedule_config.get("interval", 0)
            last_execution = schedule_config.get("last_execution", 0)
            current_time = time.time()

            return (current_time - last_execution) >= interval

        elif schedule_type == "once":
            scheduled_time = schedule_config.get("scheduled_time", 0)
            return time.time() >= scheduled_time

        return True

    async def _check_resource_limits(self) -> bool:
        """检查资源限制"""
        # 检查当前运行的任务数量
        running_tasks = await self.list_tasks(status="running", use_cache=False)
        max_concurrent = self.config_manager.get("task_manager.max_concurrent_tasks", 10) if self.config_manager else 10

        return len(running_tasks) < max_concurrent

    def _check_resource_limits_sync(self) -> bool:
        """检查资源限制（同步版本）"""
        # 检查当前活跃的执行数量
        max_concurrent = self.config_manager.get("task_manager.max_concurrent_tasks", 10) if self.config_manager else 10
        return len(self._active_executions) < max_concurrent

    async def _schedule_task_execution(self, task: Dict):
        """调度任务执行"""
        task_id = task["task_id"]

        try:
            # 更新任务状态为运行中
            await self.update_task_status(task_id, TaskStatus.RUNNING)

            # 添加状态监控
            self.add_status_monitor(task_id)

            # 这里应该调用实际的任务执行器
            # await self.execute_task(task_id)

            logger.info(f"任务 {task_id} 已调度执行")

        except Exception as e:
            logger.error(f"调度任务 {task_id} 执行失败: {e}")
            await self.update_task_status(task_id, TaskStatus.FAILED)

    def add_task_dependency(self, task_id: str, dependency_id: str):
        """添加任务依赖关系"""
        if task_id not in self._task_dependencies:
            self._task_dependencies[task_id] = []

        if dependency_id not in self._task_dependencies[task_id]:
            self._task_dependencies[task_id].append(dependency_id)
            logger.info(f"已添加任务依赖: {task_id} -> {dependency_id}")

    def remove_task_dependency(self, task_id: str, dependency_id: str):
        """移除任务依赖关系"""
        if task_id in self._task_dependencies:
            if dependency_id in self._task_dependencies[task_id]:
                self._task_dependencies[task_id].remove(dependency_id)
                logger.info(f"已移除任务依赖: {task_id} -> {dependency_id}")

    def get_task_dependencies(self, task_id: str) -> List[str]:
        """获取任务依赖列表"""
        return self._task_dependencies.get(task_id, [])

    async def get_scheduler_status(self) -> Dict[str, Any]:
        """获取调度器状态信息"""
        pending_tasks = await self.list_tasks(status="pending", use_cache=False)
        running_tasks = await self.list_tasks(status="running", use_cache=False)

        return {
            "scheduler_active": self._scheduler_active,
            "scheduler_interval": self._scheduler_interval,
            "pending_tasks_count": len(pending_tasks),
            "running_tasks_count": len(running_tasks),
            "task_dependencies": dict(self._task_dependencies),
        }

    def _validate_task_config(self, config: TaskConfig) -> None:
        """验证任务配置

        Args:
            config: 任务配置

        Raises:
            TaskValidationError: 配置验证失败
        """
        if not config.name or not config.name.strip():
            raise TaskValidationError("任务名称不能为空")

        if len(config.name) > 255:
            raise TaskValidationError("任务名称长度不能超过255个字符")

        if config.description and len(config.description) > 1000:
            raise TaskValidationError("任务描述长度不能超过1000个字符")

        if config.timeout_seconds and config.timeout_seconds <= 0:
            raise TaskValidationError("超时时间必须大于0")

        if config.max_retry_count and config.max_retry_count < 0:
            raise TaskValidationError("最大重试次数不能为负数")

        # 验证任务类型和优先级
        if not isinstance(config.task_type, TaskType):
            raise TaskValidationError("无效的任务类型")

        if not isinstance(config.priority, TaskPriority):
            raise TaskValidationError("无效的任务优先级")

        # 验证参数格式
        if config.custom_params and not isinstance(config.custom_params, dict):
            raise TaskValidationError("任务参数必须是字典格式")

        # 验证调度配置
        if config.schedule_enabled and config.schedule_time:
            self._validate_schedule_config(config)

    def _validate_schedule_config(self, config: TaskConfig) -> None:
        """验证调度配置

        Args:
            config: 任务配置

        Raises:
            TaskValidationError: 调度配置验证失败
        """
        if config.schedule_time:
            import re

            time_pattern = r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$"
            if not re.match(time_pattern, config.schedule_time):
                raise TaskValidationError("调度时间格式无效，应为HH:MM格式")

        if config.schedule_days:
            valid_days = [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ]
            for day in config.schedule_days:
                if day.lower() not in valid_days:
                    raise TaskValidationError(f"无效的星期: {day}")

    def _validate_status_transition(self, current_status: str, new_status: str) -> None:
        """验证状态转换是否合法

        Args:
            current_status: 当前状态
            new_status: 新状态

        Raises:
            TaskStateError: 状态转换不合法
        """
        # 定义合法的状态转换矩阵
        valid_transitions = {
            "pending": ["running", "cancelled"],
            "running": ["completed", "failed", "paused", "cancelled"],
            "paused": ["running", "cancelled"],
            "completed": [],  # 完成状态不能转换到其他状态
            "failed": ["pending", "running"],  # 失败可以重新开始或重试
            "cancelled": ["pending"],  # 取消可以重新开始
        }

        # 验证状态值的有效性
        all_valid_statuses = set(valid_transitions.keys())
        for transitions in valid_transitions.values():
            all_valid_statuses.update(transitions)

        if current_status not in all_valid_statuses:
            raise TaskStateError(f"未知的当前状态: {current_status}")

        if new_status not in all_valid_statuses:
            raise TaskStateError(f"未知的目标状态: {new_status}")

        # 检查是否为相同状态（允许但记录警告）
        if current_status == new_status:
            logger.warning(f"状态转换为相同状态: {current_status}")
            return

        # 检查转换是否合法
        if new_status not in valid_transitions.get(current_status, []):
            raise TaskStateError(
                f"不能从状态 '{current_status}' 转换到 '{new_status}'。"
                f"允许的转换: {valid_transitions.get(current_status, [])}"
            )

        logger.debug(f"状态转换验证通过: {current_status} -> {new_status}")

    def _handle_database_error(
        self, error: Exception, operation: str, task_id: str = None
    ):
        """统一处理数据库错误"""
        error_msg = str(error).lower()

        if "unique constraint" in error_msg or "duplicate" in error_msg:
            logger.error(f"{operation}失败 - 数据重复: {error}")
            raise TaskValidationError(f"任务ID或名称已存在")
        elif "foreign key" in error_msg:
            logger.error(f"{operation}失败 - 外键约束: {error}")
            raise TaskValidationError(f"关联数据不存在")
        elif "database is locked" in error_msg:
            logger.error(f"{operation}失败 - 数据库锁定: {error}")
            raise RuntimeError(f"数据库繁忙，请稍后重试")
        else:
            logger.error(f"{operation}失败: {error}")
            raise RuntimeError(f"{operation}操作失败")

    async def batch_create_tasks(self, tasks_data: List[Dict]) -> List[str]:
        """批量创建任务"""
        task_ids = []
        async with self.get_async_connection() as conn:
            try:
                await conn.execute("BEGIN TRANSACTION")

                for task_data in tasks_data:
                    # 验证任务配置
                    config_data = task_data.get("config", {})
                    # 转换枚举类型
                    if "task_type" in config_data and isinstance(
                        config_data["task_type"], str
                    ):
                        config_data["task_type"] = TaskType(config_data["task_type"])
                    if "priority" in config_data and isinstance(
                        config_data["priority"], str
                    ):
                        config_data["priority"] = TaskPriority(config_data["priority"])

                    config = TaskConfig.from_dict(config_data)
                    self._validate_task_config(config)

                    task_id = str(uuid.uuid4())
                    task_ids.append(task_id)

                    # 插入任务基本信息
                    await conn.execute(
                        "INSERT INTO tasks (task_id, user_id, task_name, description, task_type, priority, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            task_id,
                            task_data["user_id"],
                            task_data["name"],
                            task_data.get("description", ""),
                            config.task_type.value,
                            config.priority.value,
                            "pending",
                            datetime.now(),
                            datetime.now(),
                        ),
                    )

                    # 插入任务配置
                    config_dict = config.to_dict()
                    # 转换枚举为字符串值以便JSON序列化
                    if "task_type" in config_dict:
                        config_dict["task_type"] = config_dict["task_type"].value
                    if "priority" in config_dict:
                        config_dict["priority"] = config_dict["priority"].value

                    await conn.execute(
                        "INSERT INTO task_configs (config_id, task_id, config_key, config_value) VALUES (?, ?, ?, ?)",
                        (
                            str(uuid.uuid4()),
                            task_id,
                            "full_config",
                            json.dumps(config_dict, ensure_ascii=False),
                        ),
                    )

                await conn.commit()
                logger.info(f"批量创建任务成功，共创建 {len(task_ids)} 个任务")
                return task_ids

            except Exception as e:
                await conn.rollback()
                self._handle_database_error(e, "批量创建任务")
                raise

    async def batch_update_task_status(
        self, task_status_updates: List[Dict[str, str]]
    ) -> bool:
        """批量更新任务状态"""
        async with self.get_async_connection() as conn:
            try:
                await conn.execute("BEGIN TRANSACTION")

                for update in task_status_updates:
                    task_id = update["task_id"]
                    new_status = update["status"]

                    # 获取当前状态
                    cursor = await conn.execute(
                        "SELECT status FROM tasks WHERE task_id = ?", (task_id,)
                    )
                    result = await cursor.fetchone()
                    if not result:
                        raise TaskValidationError(f"任务 {task_id} 不存在")

                    current_status = result[0]
                    self._validate_status_transition(current_status, new_status)

                    # 更新状态
                    update_time = datetime.now()
                    last_execution = (
                        update_time
                        if new_status in ["running", "completed", "failed"]
                        else None
                    )

                    await conn.execute(
                        "UPDATE tasks SET status = ?, updated_at = ?, last_execution = ? WHERE task_id = ?",
                        (new_status, update_time, last_execution, task_id),
                    )

                await conn.commit()
                logger.info(
                    f"批量更新任务状态成功，共更新 {len(task_status_updates)} 个任务"
                )
                return True

            except Exception as e:
                await conn.rollback()
                self._handle_database_error(e, "批量更新任务状态")
                raise

    async def execute_in_transaction(self, operations: List[callable]) -> List:
        """在事务中执行多个操作"""
        results = []
        async with self.get_async_connection() as conn:
            try:
                await conn.execute("BEGIN TRANSACTION")

                for operation in operations:
                    if asyncio.iscoroutinefunction(operation):
                        result = await operation(conn)
                    else:
                        result = operation(conn)
                    results.append(result)

                await conn.commit()
                logger.info(f"事务执行成功，共执行 {len(operations)} 个操作")
                return results

            except Exception as e:
                await conn.rollback()
                self._handle_database_error(e, "事务执行")
                raise

    async def create_task(
        self, config: TaskConfig, user_id: Optional[str] = None
    ) -> str:
        """异步创建新任务

        Args:
            config: 任务配置
            user_id: 用户ID，如果为None则使用默认用户

        Returns:
            str: 任务ID

        Raises:
            TaskValidationError: 配置验证失败
        """
        # 验证任务配置
        self._validate_task_config(config)

        if user_id is None:
            user_id = self.default_user_id

        # 生成任务ID
        task_id = str(uuid.uuid4())

        # 创建任务对象
        task = Task(
            task_id=task_id,
            user_id=user_id,
            config=config,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # 使用事务保存到数据库
        async with self.get_async_connection() as conn:
            try:
                await conn.execute("BEGIN TRANSACTION")

                # 插入任务基本信息
                await conn.execute(
                    "INSERT INTO tasks (task_id, user_id, task_name, description, task_type, priority, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        task_id,
                        user_id,
                        config.name,
                        config.description or "",
                        config.task_type.value,
                        config.priority.value,
                        TaskStatus.PENDING.value,
                        task.created_at.isoformat(),
                        task.updated_at.isoformat(),
                    ),
                )

                # 插入任务配置
                config_data = config.to_dict()
                config_data["task_type"] = config.task_type.value
                config_data["priority"] = config.priority.value

                await conn.execute(
                    "INSERT INTO task_configs (config_id, task_id, config_key, config_value) VALUES (?, ?, ?, ?)",
                    (
                        str(uuid.uuid4()),
                        task_id,
                        "full_config",
                        json.dumps(config_data, ensure_ascii=False),
                    ),
                )

                await conn.commit()
                logger.info(f"创建任务成功: {config.name} (ID: {task_id})")
                return task_id

            except Exception as e:
                await conn.rollback()
                self._handle_database_error(e, "创建任务", task_id)
                raise

    async def get_task(self, task_id: str) -> Optional[Task]:
        """异步获取任务详情

        Args:
            task_id: 任务ID

        Returns:
            Optional[Task]: 任务对象，如果不存在则返回None
        """
        async with self.get_async_connection() as conn:
            try:
                # 获取任务基本信息
                cursor = await conn.execute(
                    "SELECT task_id, user_id, task_name, description, task_type, priority, status, created_at, updated_at, last_execution FROM tasks WHERE task_id = ?",
                    (task_id,),
                )

                task_row = await cursor.fetchone()
                if not task_row:
                    return None

                # 获取任务配置
                cursor = await conn.execute(
                    "SELECT config_value FROM task_configs WHERE task_id = ? AND config_key = 'full_config'",
                    (task_id,),
                )

                config_row = await cursor.fetchone()
                if not config_row:
                    logger.warning(f"任务 {task_id} 缺少配置信息")
                    return None

                config_data = json.loads(config_row[0])

                task = Task(
                    task_id=task_row[0],  # task_id
                    user_id=task_row[1],  # user_id
                    name=task_row[2],  # task_name
                    description=task_row[3] or "",  # description
                    task_type=TaskType(task_row[4]),  # task_type
                    priority=TaskPriority(task_row[5]),  # priority
                    status=TaskStatus(task_row[6]),  # status
                    config=config_data,  # 直接使用配置字典
                    created_at=datetime.fromisoformat(task_row[7]),  # created_at
                    updated_at=datetime.fromisoformat(task_row[8]),  # updated_at
                    last_executed_at=(
                        datetime.fromisoformat(task_row[9]) if task_row[9] else None
                    ),  # last_execution
                )

                return task

            except Exception as e:
                logger.error(f"获取任务失败: {e}")
                return None

    def get_task_sync(self, task_id: str) -> Optional[Task]:
        """同步获取任务详情

        Args:
            task_id: 任务ID

        Returns:
            Optional[Task]: 任务对象，如果不存在则返回None
        """
        try:
            with self.db_manager.get_connection() as conn:
                # 获取任务基本信息
                cursor = conn.execute(
                    "SELECT task_id, user_id, task_name, description, task_type, priority, status, created_at, updated_at, last_execution FROM tasks WHERE task_id = ?",
                    (task_id,),
                )

                task_row = cursor.fetchone()
                if not task_row:
                    return None

                # 获取任务配置
                cursor = conn.execute(
                    "SELECT config_value FROM task_configs WHERE task_id = ? AND config_key = 'full_config'",
                    (task_id,),
                )

                config_row = cursor.fetchone()
                if not config_row:
                    logger.warning(f"任务 {task_id} 缺少配置信息")
                    return None

                config_data = json.loads(config_row[0])

                task = Task(
                    task_id=task_row[0],  # task_id
                    user_id=task_row[1],  # user_id
                    name=task_row[2],  # task_name
                    description=task_row[3] or "",  # description
                    task_type=TaskType(task_row[4]),  # task_type
                    priority=TaskPriority(task_row[5]),  # priority
                    status=TaskStatus(task_row[6]),  # status
                    config=config_data,  # 直接使用配置字典
                    created_at=datetime.fromisoformat(task_row[7]),  # created_at
                    updated_at=datetime.fromisoformat(task_row[8]),  # updated_at
                    last_executed_at=(
                        datetime.fromisoformat(task_row[9]) if task_row[9] else None
                    ),  # last_execution
                )

                return task

        except Exception as e:
            logger.error(f"获取任务失败: {e}")
            return None

    async def update_task(
        self,
        task_id: str,
        config: Optional[TaskConfig] = None,
        status: Optional[TaskStatus] = None,
    ) -> bool:
        """异步更新任务信息

        Args:
            task_id: 任务ID
            config: 新的任务配置（可选）
            status: 新的任务状态（可选）

        Returns:
            bool: 更新是否成功

        Raises:
            TaskValidationError: 配置验证失败
            TaskStateError: 状态转换不合法
        """
        # 验证配置
        if config is not None:
            self._validate_task_config(config)

        async with self.get_async_connection() as conn:
            try:
                await conn.execute("BEGIN TRANSACTION")

                # 检查任务是否存在并获取当前状态
                cursor = await conn.execute(
                    "SELECT status FROM tasks WHERE task_id = ?", (task_id,)
                )
                task_row = await cursor.fetchone()

                if not task_row:
                    logger.warning(f"任务不存在: {task_id}")
                    return False

                current_status = task_row[0]

                # 验证状态转换
                if status is not None:
                    self._validate_status_transition(current_status, status.value)

                    await conn.execute(
                        "UPDATE tasks SET status = ?, updated_at = ? WHERE task_id = ?",
                        (status.value, datetime.now().isoformat(), task_id),
                    )

                # 更新任务配置
                if config is not None:
                    config_data = asdict(config)
                    config_data["task_type"] = config.task_type.value
                    config_data["priority"] = config.priority.value

                    # 同时更新tasks表中的基本信息
                    await conn.execute(
                        "UPDATE tasks SET task_name = ?, description = ?, task_type = ?, priority = ?, updated_at = ? WHERE task_id = ?",
                        (
                            config.name,
                            config.description or "",
                            config.task_type.value,
                            config.priority.value,
                            datetime.now().isoformat(),
                            task_id,
                        ),
                    )

                    await conn.execute(
                        "UPDATE task_configs SET config_value = ? WHERE task_id = ? AND config_key = 'full_config'",
                        (json.dumps(config_data, ensure_ascii=False), task_id),
                    )

                await conn.commit()
                logger.info(f"更新任务成功: {task_id}")
                return True

            except Exception as e:
                await conn.rollback()
                self._handle_database_error(e, "更新任务", task_id)
                raise

    async def delete_task(self, task_id: str) -> bool:
        """异步删除任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 删除是否成功
        """
        max_retries = 3
        retry_delay = 0.1

        for attempt in range(max_retries):
            try:
                async with self.get_async_connection() as conn:
                    await conn.execute("BEGIN IMMEDIATE TRANSACTION")

                    # 检查任务是否存在
                    cursor = await conn.execute(
                        "SELECT 1 FROM tasks WHERE task_id = ?", (task_id,)
                    )
                    if not await cursor.fetchone():
                        logger.warning(f"任务 {task_id} 不存在")
                        return False

                    # 删除相关数据（按依赖关系顺序）
                    await conn.execute(
                        "DELETE FROM execution_logs WHERE task_id = ?", (task_id,)
                    )
                    await conn.execute(
                        "DELETE FROM task_configs WHERE task_id = ?", (task_id,)
                    )
                    await conn.execute(
                        "DELETE FROM tasks WHERE task_id = ?", (task_id,)
                    )

                    await conn.commit()
                    logger.info(f"删除任务成功: {task_id}")
                    return True

            except Exception as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    logger.warning(f"数据库锁定，重试 {attempt + 1}/{max_retries}: {e}")
                    await asyncio.sleep(retry_delay * (2**attempt))  # 指数退避
                    continue
                else:
                    self._handle_database_error(e, "删除任务", task_id)
                    raise

        return False

    async def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """异步更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态

        Returns:
            bool: 更新是否成功

        Raises:
            TaskStateError: 状态转换不合法
        """
        async with self.get_async_connection() as conn:
            try:
                await conn.execute("BEGIN TRANSACTION")

                # 检查任务是否存在并获取当前状态
                cursor = await conn.execute(
                    "SELECT status FROM tasks WHERE task_id = ?", (task_id,)
                )
                task_row = await cursor.fetchone()

                if not task_row:
                    logger.warning(f"任务 {task_id} 不存在")
                    return False

                current_status = task_row[0]

                # 验证状态转换
                self._validate_status_transition(current_status, status.value)

                # 更新状态和时间戳
                update_fields = ["status = ?", "updated_at = ?"]
                update_values = [status.value, datetime.now().isoformat()]

                # 根据状态更新相应的时间戳
                if status == TaskStatus.RUNNING:
                    # 如果是开始运行，记录最后执行时间
                    update_fields.append("last_execution = ?")
                    update_values.append(datetime.now().isoformat())
                elif status in [
                    TaskStatus.COMPLETED,
                    TaskStatus.FAILED,
                    TaskStatus.CANCELLED,
                ]:
                    # 如果是结束状态，也记录最后执行时间
                    update_fields.append("last_execution = ?")
                    update_values.append(datetime.now().isoformat())

                update_values.append(task_id)

                await conn.execute(
                    f"UPDATE tasks SET {', '.join(update_fields)} WHERE task_id = ?",
                    update_values,
                )

                await conn.commit()
                logger.info(f"更新任务状态成功: {task_id} -> {status.value}")
                return True

            except Exception as e:
                await conn.rollback()
                self._handle_database_error(e, "更新任务状态", task_id)
                raise

    async def list_tasks(
        self,
        user_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        limit: int = 100,
        offset: int = 0,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """异步获取任务列表（支持缓存）

        Args:
            user_id: 用户ID（可选）
            status: 任务状态（可选）
            limit: 返回数量限制
            offset: 偏移量
            use_cache: 是否使用缓存

        Returns:
            List[Dict]: 任务列表
        """
        # 构建查询条件
        where_conditions = []
        params = []

        if user_id:
            where_conditions.append("user_id = ?")
            params.append(user_id)

        if status:
            where_conditions.append("status = ?")
            # 处理字符串和枚举类型
            if isinstance(status, str):
                params.append(status)
            else:
                params.append(status.value)

        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)

        # 执行查询（使用索引优化）
        query = f"""
            SELECT task_id, task_name, task_type, status, priority, 
                   created_at, updated_at, last_execution, user_id
            FROM tasks 
            {where_clause}
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        """

        params.extend([limit, offset])

        if use_cache:
            # 使用缓存查询
            rows_data = await self._cached_query(query, tuple(params))
            tasks = []
            for row_dict in rows_data:
                task_dict = {
                    "task_id": row_dict["task_id"],
                    "task_name": row_dict["task_name"],  # 保持数据库字段名
                    "task_type": row_dict["task_type"],
                    "status": row_dict["status"],
                    "priority": row_dict["priority"],
                    "created_at": row_dict["created_at"],
                    "updated_at": row_dict["updated_at"],
                    "last_execution": row_dict["last_execution"],
                    "user_id": row_dict["user_id"],
                }
                tasks.append(task_dict)
        else:
            # 直接查询
            async with self.get_async_connection() as conn:
                cursor = await conn.execute(query, params)
                rows = await cursor.fetchall()

                tasks = []
                for row in rows:
                    task_dict = {
                        "task_id": row[0],
                        "task_name": row[1],  # 保持数据库字段名
                        "task_type": row[2],
                        "status": row[3],
                        "priority": row[4],
                        "created_at": row[5],
                        "updated_at": row[6],
                        "last_execution": row[7],
                        "user_id": row[8],
                    }
                    tasks.append(task_dict)

        return tasks

    def list_tasks_sync(
        self,
        user_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Task]:
        """同步获取任务列表（用于GUI调用）

        Args:
            user_id: 用户ID（可选）
            status: 任务状态（可选）
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            List[Task]: 任务对象列表
        """
        try:
            # 使用数据库管理器的同步方法
            tasks_data = self.db_manager.get_tasks_by_user(
                user_id or "default_user", status
            )

            # 转换为Task对象
            tasks = []
            for task_data in tasks_data[:limit]:
                try:
                    # 获取任务配置
                    config_data = self.db_manager.get_task_config(task_data["task_id"])

                    # 创建Task对象，config字段使用字典
                    task = Task(
                        task_id=task_data["task_id"],
                        user_id=task_data["user_id"],
                        name=task_data["task_name"],
                        description=task_data.get("description", ""),
                        task_type=TaskType(
                            task_data.get("task_type", TaskType.CUSTOM.value)
                        ),
                        priority=TaskPriority(task_data.get("priority", "medium")),
                        status=TaskStatus(task_data["status"]),
                        config=config_data or {},  # 使用字典而不是TaskConfig对象
                        created_at=(
                            datetime.fromisoformat(task_data["created_at"])
                            if isinstance(task_data["created_at"], str)
                            else task_data["created_at"]
                        ),
                        updated_at=(
                            datetime.fromisoformat(task_data["updated_at"])
                            if isinstance(task_data["updated_at"], str)
                            else task_data["updated_at"]
                        ),
                    )

                    # 设置执行时间
                    if task_data.get("last_execution"):
                        task.last_executed_at = (
                            datetime.fromisoformat(task_data["last_execution"])
                            if isinstance(task_data["last_execution"], str)
                            else task_data["last_execution"]
                        )

                    tasks.append(task)

                except Exception as e:
                    logger.error(
                        f"转换任务数据失败 {task_data.get('task_id', 'unknown')}: {e}"
                    )
                    continue

            logger.debug(f"同步获取任务列表成功，共 {len(tasks)} 个任务")
            return tasks

        except Exception as e:
            logger.error(f"同步获取任务列表失败: {e}")
            return []

    async def get_task_statistics(
        self, user_id: Optional[str] = None, use_cache: bool = True
    ) -> Dict[str, Any]:
        """异步获取任务统计信息（支持缓存）

        Args:
            user_id: 用户ID（可选）
            use_cache: 是否使用缓存

        Returns:
            Dict[str, Any]: 统计信息
        """
        # 构建查询条件
        where_clause = ""
        params = []

        if user_id:
            where_clause = "WHERE user_id = ?"
            params = [user_id]

        # 使用单个查询获取所有统计信息（性能优化）
        query = f"""
            SELECT 
                COUNT(*) as total_tasks,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running_count,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_count,
                SUM(CASE WHEN priority = 'low' THEN 1 ELSE 0 END) as low_priority_count,
                SUM(CASE WHEN priority = 'medium' THEN 1 ELSE 0 END) as medium_priority_count,
                SUM(CASE WHEN priority = 'high' THEN 1 ELSE 0 END) as high_priority_count
            FROM tasks 
            {where_clause}
        """

        if use_cache:
            # 使用缓存查询
            rows_data = await self._cached_query(query, tuple(params))
            stats_row = rows_data[0] if rows_data else {}
        else:
            # 直接查询
            async with self.get_async_connection() as conn:
                cursor = await conn.execute(query, params)
                row = await cursor.fetchone()
                # 将Row对象转换为字典以便统一处理
                if row:
                    stats_row = {
                        "total_count": row[0],
                        "pending_count": row[1],
                        "running_count": row[2],
                        "completed_count": row[3],
                        "failed_count": row[4],
                        "cancelled_count": row[5],
                        "low_priority_count": row[6],
                        "medium_priority_count": row[7],
                        "high_priority_count": row[8],
                    }
                else:
                    stats_row = {}

        # 获取类型统计
        type_query = f"""
            SELECT task_type, COUNT(*) as count
            FROM tasks 
            {where_clause}
            GROUP BY task_type
        """

        if use_cache:
            type_rows_data = await self._cached_query(type_query, tuple(params))
            type_stats = {row["task_type"]: row["count"] for row in type_rows_data}
        else:
            async with self.get_async_connection() as conn:
                cursor = await conn.execute(type_query, params)
                type_rows = await cursor.fetchall()
                type_stats = {row[0]: row[1] for row in type_rows}

        return {
            "total_tasks": stats_row.get("total_count", 0) if stats_row else 0,
            "status_distribution": {
                "pending": stats_row.get("pending_count", 0) if stats_row else 0,
                "running": stats_row.get("running_count", 0) if stats_row else 0,
                "completed": stats_row.get("completed_count", 0) if stats_row else 0,
                "failed": stats_row.get("failed_count", 0) if stats_row else 0,
                "cancelled": stats_row.get("cancelled_count", 0) if stats_row else 0,
            },
            "priority_distribution": {
                "low": stats_row.get("low_priority_count", 0) if stats_row else 0,
                "medium": stats_row.get("medium_priority_count", 0) if stats_row else 0,
                "high": stats_row.get("high_priority_count", 0) if stats_row else 0,
            },
            "type_distribution": type_stats,
        }

    def add_task_action(
        self, task_id: str, action_type: str, action_data: Dict[str, Any]
    ) -> str:
        """为任务添加动作

        Args:
            task_id: 任务ID
            action_type: 动作类型
            action_data: 动作数据

        Returns:
            str: 动作ID
        """
        action_id = str(uuid.uuid4())

        # 准备动作数据
        coordinates = action_data.get("coordinates", "{}")
        if isinstance(coordinates, dict):
            coordinates = json.dumps(coordinates)

        parameters = action_data.get("parameters", {})
        if isinstance(parameters, dict):
            parameters = json.dumps(parameters)

        # 创建动作记录
        self.db_manager.create_task_action(
            task_id=task_id,
            action_type=action_type,
            action_order=action_data.get("sequence_order", 0),
            target_element=action_data.get("target_element", ""),
            coordinates=coordinates,
            key_code=action_data.get("key_code", ""),
            wait_duration=action_data.get("wait_duration", 0.0),
            screenshot_path=action_data.get("screenshot_path", ""),
            custom_script=action_data.get("custom_script", ""),
            parameters=parameters,
        )

        logger.info(f"为任务 {task_id} 添加动作: {action_type} (ID: {action_id})")
        return action_id

    def get_task_actions(self, task_id: str) -> List[Dict[str, Any]]:
        """获取任务的所有动作

        Args:
            task_id: 任务ID

        Returns:
            List[Dict[str, Any]]: 动作列表
        """
        return self.db_manager.get_task_actions(task_id)

    def update_task_action(self, action_id: str, action_data: Dict[str, Any]) -> bool:
        """更新任务动作

        Args:
            action_id: 动作ID
            action_data: 新的动作数据

        Returns:
            bool: 是否更新成功
        """
        # 准备更新数据
        update_data = {}

        if "action_type" in action_data:
            update_data["action_type"] = action_data["action_type"]

        if "sequence_order" in action_data:
            update_data["action_order"] = action_data["sequence_order"]

        if "coordinates" in action_data:
            coordinates = action_data["coordinates"]
            if isinstance(coordinates, dict):
                coordinates = json.dumps(coordinates)
            update_data["coordinates"] = coordinates

        if "key_code" in action_data:
            update_data["key_code"] = action_data["key_code"]

        if "wait_duration" in action_data:
            update_data["wait_duration"] = action_data["wait_duration"]

        if "screenshot_path" in action_data:
            update_data["screenshot_path"] = action_data["screenshot_path"]

        if "custom_script" in action_data:
            update_data["custom_script"] = action_data["custom_script"]

        if "parameters" in action_data:
            parameters = action_data["parameters"]
            if isinstance(parameters, dict):
                parameters = json.dumps(parameters)
            update_data["parameters"] = parameters

        if "description" in action_data:
            update_data["description"] = action_data["description"]

        if not update_data:
            return False

        success = self.db_manager.update_task_action(action_id, **update_data)

        if success:
            logger.info(f"更新动作成功: {action_id}")
        else:
            logger.warning(f"更新动作失败: {action_id}")

        return success

    def delete_task_action(self, action_id: str) -> bool:
        """删除任务动作

        Args:
            action_id: 动作ID

        Returns:
            bool: 是否删除成功
        """
        success = self.db_manager.delete_task_action(action_id)

        if success:
            logger.info(f"删除动作成功: {action_id}")
        else:
            logger.warning(f"删除动作失败: {action_id}")

        return success

    async def execute_task(self, task_id: str, user_id: Optional[str] = None) -> str:
        """异步执行任务

        Args:
            task_id: 任务ID
            user_id: 用户ID（可选）

        Returns:
            str: 执行ID
        """
        if user_id is None:
            user_id = self.default_user_id

        # 获取任务
        task = await self.get_task(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        # 检查任务状态
        if task.status == TaskStatus.RUNNING:
            raise RuntimeError(f"任务正在执行中: {task_id}")

        # 执行任务
        execution_id = await self.task_executor.execute_task(task, user_id)

        logger.info(f"开始执行任务: {task_id} (执行ID: {execution_id})")
        return execution_id

    def pause_task_execution(self):
        """暂停当前任务执行"""
        self.task_executor.pause_execution()

    def resume_task_execution(self):
        """恢复当前任务执行"""
        self.task_executor.resume_execution()

    def stop_task_execution(self):
        """停止当前任务执行"""
        self.task_executor.stop_execution()

    def get_execution_status(self) -> Optional[Dict[str, Any]]:
        """获取当前执行状态

        Returns:
            Optional[Dict[str, Any]]: 执行状态信息
        """
        return self.task_executor.get_execution_status()

    def get_task_executions(self, task_id: str) -> List[Dict[str, Any]]:
        """获取任务的执行历史

        Args:
            task_id: 任务ID

        Returns:
            List[Dict[str, Any]]: 执行历史列表
        """
        return self.db_manager.get_task_executions(task_id)

    def create_task_sync(
        self, config: TaskConfig, user_id: Optional[str] = None
    ) -> str:
        """同步创建新任务（用于GUI调用）

        Args:
            config: 任务配置
            user_id: 用户ID，如果为None则使用默认用户

        Returns:
            str: 任务ID

        Raises:
            TaskValidationError: 配置验证失败
        """
        # 验证任务配置
        self._validate_task_config(config)

        if user_id is None:
            user_id = self.default_user_id

        # 生成任务ID
        task_id = str(uuid.uuid4())

        # 创建任务对象
        task = Task(
            task_id=task_id,
            user_id=user_id,
            config=config,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # 使用同步连接保存到数据库
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute("BEGIN TRANSACTION")

                # 插入任务基本信息
                conn.execute(
                    "INSERT INTO tasks (task_id, user_id, task_name, description, task_type, priority, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        task_id,
                        user_id,
                        config.name,
                        config.description or "",
                        config.task_type.value,
                        config.priority.value,
                        TaskStatus.PENDING.value,
                        task.created_at.isoformat(),
                        task.updated_at.isoformat(),
                    ),
                )

                # 插入任务配置
                config_data = asdict(config)
                config_data["task_type"] = config.task_type.value
                config_data["priority"] = config.priority.value

                conn.execute(
                    "INSERT INTO task_configs (config_id, task_id, config_key, config_value) VALUES (?, ?, ?, ?)",
                    (
                        str(uuid.uuid4()),
                        task_id,
                        "full_config",
                        json.dumps(config_data, ensure_ascii=False),
                    ),
                )

                conn.commit()
                logger.info(f"创建任务成功: {config.name} (ID: {task_id})")
                return task_id

        except Exception as e:
            self._handle_database_error(e, "创建任务", task_id)
            raise

    # ==================== 并发执行管理（从MultiTaskManager整合） ====================

    async def submit_concurrent_task(self, task_id: str, priority: int = 1) -> bool:
        """提交任务到并发执行队列

        Args:
            task_id: 任务ID
            priority: 任务优先级（数字越小优先级越高）

        Returns:
            bool: 是否成功提交
        """
        try:
            # 检查资源限制
            if not await self._check_resource_limits():
                logger.warning(f"资源限制阻止任务提交: {task_id}")
                return False

            # 添加到优先级队列
            self._task_queue.put((priority, time.time(), task_id))
            logger.info(f"任务已提交到执行队列: {task_id}, 优先级: {priority}")

            # 启动任务分配器（如果未运行）
            if not hasattr(self, "_task_dispatcher") or self._task_dispatcher.done():
                self._task_dispatcher = asyncio.create_task(self._dispatch_tasks())

            return True

        except Exception as e:
            logger.error(f"提交任务失败: {task_id}, 错误: {e}")
            return False

    async def _dispatch_tasks(self):
        """任务分配器 - 从队列中取出任务并分配给工作线程"""
        while True:
            try:
                if self._task_queue.empty():
                    await asyncio.sleep(1)
                    continue

                # 检查是否有可用的执行槽位
                if len(self._running_tasks) >= self._max_concurrent_tasks:
                    await asyncio.sleep(1)
                    continue

                # 从队列中取出任务
                priority, submit_time, task_id = self._task_queue.get()

                # 检查任务是否仍然有效
                task = await self.get_task(task_id)
                if not task or task.status != TaskStatus.PENDING:
                    logger.warning(f"跳过无效或已处理的任务: {task_id}")
                    continue

                # 分配任务执行
                await self._assign_task_execution(task_id)

            except Exception as e:
                logger.error(f"任务分配器错误: {e}")
                await asyncio.sleep(5)

    async def _assign_task_execution(self, task_id: str):
        """分配任务执行

        Args:
            task_id: 任务ID
        """
        try:
            # 获取执行信号量
            async with self._execution_semaphore:
                # 创建执行任务
                execution_task = asyncio.create_task(
                    self._execute_task_with_monitoring(task_id)
                )

                # 记录运行中的任务
                self._running_tasks[task_id] = {
                    "task": execution_task,
                    "start_time": datetime.now(),
                    "status": "running",
                }

                logger.info(f"任务开始执行: {task_id}")

                # 等待任务完成
                await execution_task

        except Exception as e:
            logger.error(f"任务执行分配失败: {task_id}, 错误: {e}")
        finally:
            # 清理运行记录
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]

    async def _execute_task_with_monitoring(self, task_id: str):
        """带监控的任务执行

        Args:
            task_id: 任务ID
        """
        try:
            # 更新任务状态为运行中
            await self.update_task_status(task_id, TaskStatus.RUNNING)

            # 触发执行开始回调
            await self._trigger_execution_callback(task_id, "started")

            # 执行任务
            execution_id = await self.execute_task(task_id)

            # 等待执行完成
            while True:
                status = self.get_execution_status()
                if not status or status.get("status") in [
                    "completed",
                    "failed",
                    "cancelled",
                ]:
                    break
                await asyncio.sleep(1)

            # 更新任务状态
            final_status = status.get("status", "completed") if status else "completed"
            if final_status == "completed":
                await self.update_task_status(task_id, TaskStatus.COMPLETED)
                await self._trigger_execution_callback(task_id, "completed")
            else:
                await self.update_task_status(task_id, TaskStatus.FAILED)
                await self._trigger_execution_callback(task_id, "failed")

            logger.info(f"任务执行完成: {task_id}, 状态: {final_status}")

        except Exception as e:
            logger.error(f"任务执行失败: {task_id}, 错误: {e}")
            await self.update_task_status(task_id, TaskStatus.FAILED)
            await self._trigger_execution_callback(task_id, "failed", str(e))

    async def cancel_concurrent_task(self, task_id: str) -> bool:
        """取消并发执行的任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功取消
        """
        try:
            # 如果任务正在运行，取消执行
            if task_id in self._running_tasks:
                task_info = self._running_tasks[task_id]
                task_info["task"].cancel()
                task_info["status"] = "cancelled"

                # 更新任务状态
                await self.update_task_status(task_id, TaskStatus.CANCELLED)

                logger.info(f"任务已取消: {task_id}")
                return True

            # 如果任务在队列中，从队列中移除
            # 注意：PriorityQueue不支持直接删除，这里简化处理
            logger.warning(f"任务不在运行状态，无法取消: {task_id}")
            return False

        except Exception as e:
            logger.error(f"取消任务失败: {task_id}, 错误: {e}")
            return False

    def _check_resource_limits(self) -> bool:
        """检查系统资源限制

        Returns:
            bool: 是否满足资源限制
        """
        try:
            # 检查CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self._resource_limits["max_cpu_percent"]:
                logger.warning(f"CPU使用率过高: {cpu_percent}%")
                return False

            # 检查内存使用率
            memory = psutil.virtual_memory()
            if memory.percent > self._resource_limits["max_memory_percent"]:
                logger.warning(f"内存使用率过高: {memory.percent}%")
                return False

            # 检查并发任务数量
            if (
                len(self._running_tasks)
                >= self._resource_limits.max_concurrent_tasks
            ):
                logger.warning(f"并发任务数量已达上限: {len(self._running_tasks)}")
                return False

            return True

        except Exception as e:
            logger.error(f"检查资源限制失败: {e}")
            return True  # 检查失败时允许执行

    async def _trigger_execution_callback(
        self, task_id: str, event: str, data: Any = None
    ) -> None:
        """触发执行回调

        Args:
            task_id: 任务ID
            event: 事件类型 ('started', 'completed', 'failed', 'progress')
            data: 事件数据
        """
        try:
            if task_id in self._execution_callbacks:
                callback = self._execution_callbacks[task_id]
                if asyncio.iscoroutinefunction(callback):
                    await callback(task_id, event, data)
                else:
                    callback(task_id, event, data)
        except Exception as e:
            logger.error(f"执行回调失败: {task_id}, 事件: {event}, 错误: {e}")

    def set_execution_callback(self, task_id: str, callback: Callable) -> None:
        """设置任务执行回调

        Args:
            task_id: 任务ID
            callback: 回调函数
        """
        self._execution_callbacks[task_id] = callback

    def remove_execution_callback(self, task_id: str) -> None:
        """移除任务执行回调

        Args:
            task_id: 任务ID
        """
        if task_id in self._execution_callbacks:
            del self._execution_callbacks[task_id]

    def get_concurrent_execution_status(self) -> Dict[str, Any]:
        """获取并发执行状态

        Returns:
            Dict[str, Any]: 执行状态信息
        """
        return {
            "running_tasks": len(self._running_tasks),
            "max_concurrent_tasks": self._max_concurrent_tasks,
            "queue_size": self._task_queue.qsize(),
            "resource_limits": {
                "max_concurrent_tasks": self._resource_limits.max_concurrent_tasks,
                "max_cpu_usage": self._resource_limits.max_cpu_usage,
                "max_memory_usage": self._resource_limits.max_memory_usage,
            },
            "running_task_ids": list(self._running_tasks.keys()),
        }

    def update_resource_limits(self, limits: Dict[str, Any]) -> None:
        """更新资源限制

        Args:
            limits: 新的资源限制配置
        """
        # 逐个更新ResourceLimits属性
        if "max_concurrent_tasks" in limits:
            self._resource_limits.max_concurrent_tasks = limits["max_concurrent_tasks"]
            new_limit = limits["max_concurrent_tasks"]
            self._max_concurrent_tasks = new_limit
            self._execution_semaphore = asyncio.Semaphore(new_limit)
        
        if "max_cpu_usage" in limits:
            self._resource_limits.max_cpu_usage = limits["max_cpu_usage"]
        
        if "max_memory_usage" in limits:
            self._resource_limits.max_memory_usage = limits["max_memory_usage"]

        logger.info(f"资源限制已更新: {self._resource_limits}")

    async def shutdown_concurrent_execution(self) -> None:
        """关闭并发执行系统"""
        try:
            # 取消所有运行中的任务
            for task_id, task_info in self._running_tasks.items():
                task_info["task"].cancel()

            # 等待所有任务完成
            if self._running_tasks:
                await asyncio.gather(
                    *[task_info["task"] for task_info in self._running_tasks.values()],
                    return_exceptions=True,
                )

            # 关闭线程池
            self._thread_pool.shutdown(wait=True)

            logger.info("并发执行系统已关闭")

        except Exception as e:
            logger.error(f"关闭并发执行系统失败: {e}")

    # ==================== 应用服务层方法 ====================

    async def create_task_async(
        self,
        user_id: str,
        task_type: str,
        config: Dict[str, Any],
        priority: str = "medium",
        scheduled_at: Optional[datetime] = None,
        parent_task_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """异步创建任务（应用服务层）

        Args:
            user_id: 用户ID
            task_type: 任务类型
            config: 任务配置
            priority: 任务优先级
            scheduled_at: 计划执行时间
            parent_task_id: 父任务ID
            description: 任务描述

        Returns:
            创建的任务信息
        """
        try:
            # 验证任务配置
            await self._validate_task_config_async(task_type, config)

            # 验证父任务
            if parent_task_id:
                await self._validate_parent_task_async(parent_task_id, user_id)

            # 创建任务
            task_id = str(uuid.uuid4())
            task_data = {
                "task_id": task_id,
                "user_id": user_id,
                "task_type": task_type,
                "config": config,
                "status": "pending",
                "priority": priority,
                "scheduled_at": scheduled_at,
                "parent_task_id": parent_task_id,
                "description": description,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }

            # 保存到数据库
            created_task = await self._save_task_async(task_data)

            # 发布任务创建事件
            await self._publish_event_async(
                "task_created",
                {
                    "task_id": task_id,
                    "user_id": user_id,
                    "task_type": task_type,
                    "priority": priority,
                },
            )

            logger.info(f"任务创建成功: {task_id}")
            return created_task

        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            raise

    async def get_task_async(self, task_id: str, user_id: str) -> Dict[str, Any]:
        """异步获取任务详情

        Args:
            task_id: 任务ID
            user_id: 用户ID

        Returns:
            任务信息
        """
        try:
            task = await self._get_task_from_db_async(task_id)
            if not task or task.get("user_id") != user_id:
                raise ValueError(f"任务不存在: {task_id}")
            return task
        except Exception as e:
            logger.error(f"获取任务失败: {e}")
            raise

    async def update_task_async(
        self, task_id: str, user_id: str, **updates: Any
    ) -> Dict[str, Any]:
        """异步更新任务

        Args:
            task_id: 任务ID
            user_id: 用户ID
            **updates: 更新字段

        Returns:
            更新后的任务信息
        """
        try:
            # 获取现有任务
            task = await self.get_task_async(task_id, user_id)
            old_status = task.get("status")

            # 验证更新数据
            if "config" in updates and "task_type" in updates:
                await self._validate_task_config_async(
                    updates["task_type"], updates["config"]
                )
            elif "config" in updates:
                await self._validate_task_config_async(
                    task["task_type"], updates["config"]
                )

            # 更新时间戳
            updates["updated_at"] = datetime.now()

            # 执行更新
            updated_task = await self._update_task_in_db_async(task_id, updates)

            # 如果状态发生变化，发布事件
            if "status" in updates and updates["status"] != old_status:
                await self._publish_event_async(
                    "task_status_changed",
                    {
                        "task_id": task_id,
                        "old_status": old_status,
                        "new_status": updates["status"],
                        "user_id": user_id,
                    },
                )

            logger.info(f"任务更新成功: {task_id}")
            return updated_task

        except Exception as e:
            logger.error(f"更新任务失败: {e}")
            raise

    async def delete_task_async(self, task_id: str, user_id: str) -> bool:
        """异步删除任务

        Args:
            task_id: 任务ID
            user_id: 用户ID

        Returns:
            是否删除成功
        """
        try:
            # 获取任务
            task = await self.get_task_async(task_id, user_id)

            # 检查任务状态
            if task["status"] in ["running", "paused"]:
                raise ValueError("无法删除正在执行的任务")

            # 删除任务依赖
            await self._remove_task_dependencies_async(task_id)

            # 删除任务
            success = await self._delete_task_from_db_async(task_id)

            if success:
                logger.info(f"任务删除成功: {task_id}")

            return success

        except Exception as e:
            logger.error(f"删除任务失败: {e}")
            raise

    async def list_tasks_async(
        self,
        user_id: str,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        parent_task_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """异步获取任务列表

        Args:
            user_id: 用户ID
            status: 任务状态过滤
            task_type: 任务类型过滤
            parent_task_id: 父任务ID过滤
            limit: 限制数量
            offset: 偏移量

        Returns:
            任务列表
        """
        try:
            return await self._query_tasks_async(
                user_id=user_id,
                status=status,
                task_type=task_type,
                parent_task_id=parent_task_id,
                limit=limit,
                offset=offset,
            )
        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            raise

    async def search_tasks_async(
        self, user_id: str, query: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """异步搜索任务

        Args:
            user_id: 用户ID
            query: 搜索关键词
            limit: 限制数量
            offset: 偏移量

        Returns:
            匹配的任务列表
        """
        try:
            return await self._search_tasks_in_db_async(query, user_id, limit, offset)
        except Exception as e:
            logger.error(f"搜索任务失败: {e}")
            raise

    async def execute_task_async(self, task_id: str, user_id: str) -> str:
        """异步执行任务

        Args:
            task_id: 任务ID
            user_id: 用户ID

        Returns:
            执行ID
        """
        try:
            # 获取任务
            task = await self.get_task_async(task_id, user_id)

            # 检查任务状态
            if task["status"] not in ["pending", "paused"]:
                raise ValueError(f"任务状态不允许执行: {task['status']}")

            # 检查依赖任务
            await self._check_task_dependencies_async(task_id)

            # 更新任务状态为运行中
            await self.update_task_async(task_id, user_id, status="running")

            # 创建执行记录
            execution_id = str(uuid.uuid4())
            await self._create_execution_record_async(execution_id, task_id)

            # 发布任务执行开始事件
            await self._publish_event_async(
                "task_execution_started",
                {"task_id": task_id, "execution_id": execution_id, "user_id": user_id},
            )

            logger.info(f"任务开始执行: {task_id}, 执行ID: {execution_id}")
            return execution_id

        except Exception as e:
            logger.error(f"执行任务失败: {e}")
            raise

    # ==================== 辅助方法 ====================

    async def _validate_task_config_async(self, task_type: str, config: Dict[str, Any]) -> bool:
        """异步验证任务配置"""
        if not config:
            raise ValueError("任务配置不能为空")

        # 根据任务类型进行特定验证
        if task_type == "automation":
            if not config.get("automation_config"):
                raise ValueError("自动化任务必须提供automation_config")
        elif task_type == "scheduled":
            if not config.get("schedule_config"):
                raise ValueError("计划任务必须提供schedule_config")

    async def _validate_parent_task_async(self, parent_task_id: str, user_id: str) -> bool:
        """异步验证父任务"""
        try:
            parent_task = await self.get_task_async(parent_task_id, user_id)
            if parent_task["status"] in ["failed", "cancelled"]:
                raise ValueError("父任务状态不允许创建子任务")
        except ValueError:
            raise ValueError("父任务不存在")

    async def _save_task_async(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """异步保存任务到数据库"""
        # 这里应该实现实际的数据库保存逻辑
        # 暂时返回输入数据作为示例
        return task_data

    async def _get_task_from_db_async(self, task_id: str) -> Optional[Dict[str, Any]]:
        """异步从数据库获取任务"""
        # 这里应该实现实际的数据库查询逻辑
        # 暂时返回None作为示例
        return None

    async def _update_task_in_db_async(
        self, task_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """异步更新数据库中的任务"""
        # 这里应该实现实际的数据库更新逻辑
        # 暂时返回更新数据作为示例
        return updates

    async def _delete_task_from_db_async(self, task_id: str) -> bool:
        """异步从数据库删除任务"""
        # 这里应该实现实际的数据库删除逻辑
        return True

    async def _remove_task_dependencies_async(self, task_id: str) -> None:
        """异步删除任务依赖"""
        # 这里应该实现实际的依赖删除逻辑
        pass

    async def _query_tasks_async(self, **filters: Any) -> List[Dict[str, Any]]:
        """异步查询任务"""
        # 这里应该实现实际的数据库查询逻辑
        return []

    async def _search_tasks_in_db_async(
        self, query: str, user_id: str, limit: int, offset: int
    ) -> List[Dict[str, Any]]:
        """异步在数据库中搜索任务"""
        # 这里应该实现实际的搜索逻辑
        return []

    async def _check_task_dependencies_async(self, task_id: str) -> bool:
        """异步检查任务依赖"""
        # 这里应该实现实际的依赖检查逻辑
        pass

    async def _create_execution_record_async(self, execution_id: str, task_id: str) -> None:
        """异步创建执行记录"""
        # 这里应该实现实际的执行记录创建逻辑
        pass

    async def _publish_event_async(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """异步发布事件"""
        # 这里应该实现实际的事件发布逻辑
        logger.info(f"发布事件: {event_type}, 数据: {event_data}")

    # ==================== 并发执行功能（从MultiTaskManager整合） ====================



    def start_concurrent_manager(self) -> None:
        """启动并发管理器"""
        if self._concurrent_manager_running:
            return

        self._concurrent_manager_running = True
        self._concurrent_start_time = datetime.now()
        self._concurrent_manager_thread = threading.Thread(
            target=self._concurrent_management_loop,
            daemon=True,
            name="TaskManager-ConcurrentManager",
        )
        self._concurrent_manager_thread.start()
        logger.info("并发管理器已启动")

    def stop_concurrent_manager(self) -> None:
        """停止并发管理器"""
        self._concurrent_manager_running = False
        if (
            self._concurrent_manager_thread
            and self._concurrent_manager_thread.is_alive()
        ):
            self._concurrent_manager_thread.join(timeout=5.0)
        logger.info("并发管理器已停止")

    def submit_concurrent_task_sync(
        self,
        task_id: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        dependencies: Optional[List[str]] = None,
        resource_requirements: Optional[Dict[str, Any]] = None,
    ) -> str:
        """提交任务到并发执行队列"""
        execution_id = str(uuid.uuid4())

        task_execution = TaskExecution(
            task_id=task_id,
            execution_id=execution_id,
            priority=priority,
            state=TaskState.QUEUED,
            dependencies=dependencies or [],
            resource_requirements=resource_requirements or {},
        )

        self._concurrent_task_queue.put(task_execution)
        logger.info(f"任务 {task_id} 已提交到并发队列，执行ID: {execution_id}")

        # 如果管理器未运行，自动启动
        if not self._concurrent_manager_running:
            self.start_concurrent_manager()

        return execution_id

    async def cancel_concurrent_execution(self, execution_id: str) -> bool:
        """取消并发任务执行"""
        if execution_id in self._active_executions:
            execution = self._active_executions[execution_id]
            execution.state = TaskState.CANCELLED
            execution.end_time = datetime.now()

            # 取消对应的Future
            if execution_id in self._worker_futures:
                future = self._worker_futures[execution_id]
                future.cancel()
                del self._worker_futures[execution_id]

            # 移动到已完成列表
            self._completed_executions[execution_id] = execution
            del self._active_executions[execution_id]

            logger.info(f"并发任务执行 {execution_id} 已取消")
            return True

        return False

    def get_concurrent_status(self) -> Dict[str, Any]:
        """获取并发执行状态"""
        return {
            "manager_running": self._concurrent_manager_running,
            "queue_size": self._concurrent_task_queue.size(),
            "active_executions": len(self._active_executions),
            "completed_executions": len(self._completed_executions),
            "total_processed": self._total_executions_processed,
            "average_execution_time": (
                self._total_execution_time / max(1, self._total_executions_processed)
            ),
            "uptime": (
                (datetime.now() - self._concurrent_start_time).total_seconds()
                if self._concurrent_start_time
                else 0
            ),
            "resource_limits": {
                "max_concurrent_tasks": self._resource_limits.max_concurrent_tasks,
                "max_cpu_usage": self._resource_limits.max_cpu_usage,
                "max_memory_usage": self._resource_limits.max_memory_usage,
            },
            "execution_mode": self._execution_mode.value,
            "queue_by_priority": self._concurrent_task_queue.get_priority_counts(),
        }

    def _concurrent_management_loop(self) -> None:
        """并发管理循环"""
        logger.info("并发管理循环已启动")

        while self._concurrent_manager_running:
            try:
                # 分配任务给工作线程
                self._assign_tasks_to_workers()

                # 检查已完成的任务
                self._check_completed_tasks()

                # 清理已完成的任务
                self._cleanup_completed_executions()

                # 检查资源限制
                self._check_resource_limits_sync()

                # 检查超时任务
                self._check_timeout_tasks()

                # 短暂休眠
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"并发管理循环出错: {e}")
                time.sleep(1.0)

        logger.info("并发管理循环已停止")

    def _assign_tasks_to_workers(self) -> None:
        """分配任务给工作线程"""
        # 检查是否有可用的工作线程槽位
        if len(self._active_executions) >= self._resource_limits.max_concurrent_tasks:
            return

        # 从队列中获取任务
        task_execution = self._concurrent_task_queue.get()
        if not task_execution:
            return

        # 检查依赖是否满足
        if not self._check_dependencies(task_execution):
            # 依赖未满足，重新放回队列
            self._concurrent_task_queue.put(task_execution)
            return

        # 检查资源要求
        if not self._check_resource_requirements(task_execution):
            # 资源不足，重新放回队列
            self._concurrent_task_queue.put(task_execution)
            return

        # 提交任务到线程池
        task_execution.state = TaskState.RUNNING
        task_execution.start_time = datetime.now()

        future = self._thread_pool.submit(self._execute_task_in_thread, task_execution)

        self._active_executions[task_execution.execution_id] = task_execution
        self._worker_futures[task_execution.execution_id] = future

        logger.info(
            f"任务 {task_execution.task_id} 已分配给工作线程，执行ID: {task_execution.execution_id}"
        )

    def _check_dependencies(self, task_execution: TaskExecution) -> bool:
        """检查任务依赖是否满足"""
        for dep_id in task_execution.dependencies:
            # 检查依赖任务是否已完成
            if dep_id not in self._completed_executions:
                return False

            dep_execution = self._completed_executions[dep_id]
            if dep_execution.state != TaskState.COMPLETED:
                return False

        return True

    def _check_resource_requirements(self, task_execution: TaskExecution) -> bool:
        """检查资源要求是否满足"""
        # 检查CPU使用率
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            if cpu_percent > self._resource_limits.max_cpu_usage:
                return False
        except Exception:
            pass

        # 检查内存使用率
        try:
            memory_percent = psutil.virtual_memory().percent
            if memory_percent > self._resource_limits.max_memory_usage:
                return False
        except Exception:
            pass

        return True

    def _check_completed_tasks(self) -> None:
        """检查已完成的任务"""
        completed_executions = []

        for execution_id, future in list(self._worker_futures.items()):
            if future.done():
                execution = self._active_executions.get(execution_id)
                if execution:
                    execution.end_time = datetime.now()

                    try:
                        result = future.result()
                        execution.state = TaskState.COMPLETED
                        execution.result = result
                        logger.info(
                            f"任务执行完成: {execution.task_id}, 执行ID: {execution_id}"
                        )
                    except Exception as e:
                        execution.state = TaskState.FAILED
                        execution.error_message = str(e)
                        logger.error(
                            f"任务执行失败: {execution.task_id}, 执行ID: {execution_id}, 错误: {e}"
                        )

                    completed_executions.append(execution)

                # 清理
                del self._worker_futures[execution_id]
                if execution_id in self._active_executions:
                    del self._active_executions[execution_id]

        # 移动到已完成列表
        for execution in completed_executions:
            self._completed_executions[execution.execution_id] = execution
            self._execution_history.append(execution)
            self._total_executions_processed += 1

            if execution.duration:
                self._total_execution_time += execution.duration.total_seconds()

    def _cleanup_completed_executions(self) -> None:
        """清理已完成的任务执行记录"""
        # 保留最近的1000条记录
        if len(self._completed_executions) > 1000:
            # 按完成时间排序，删除最旧的记录
            sorted_executions = sorted(
                self._completed_executions.values(),
                key=lambda x: x.end_time or datetime.min,
            )

            to_remove = sorted_executions[:-1000]
            for execution in to_remove:
                del self._completed_executions[execution.execution_id]



    def _check_timeout_tasks(self) -> None:
        """检查超时任务"""
        current_time = datetime.now()
        timeout_threshold = timedelta(seconds=self._resource_limits.max_execution_time)

        for execution_id, execution in list(self._active_executions.items()):
            if execution.start_time:
                elapsed = current_time - execution.start_time
                if elapsed > timeout_threshold:
                    # 任务超时，取消执行
                    logger.warning(
                        f"任务执行超时: {execution.task_id}, 执行ID: {execution_id}"
                    )

                    if execution_id in self._worker_futures:
                        future = self._worker_futures[execution_id]
                        future.cancel()
                        del self._worker_futures[execution_id]

                    execution.state = TaskState.TIMEOUT
                    execution.end_time = current_time
                    execution.error_message = "任务执行超时"

                    self._completed_executions[execution_id] = execution
                    del self._active_executions[execution_id]

    def _execute_task_in_thread(self, task_execution: TaskExecution) -> Any:
        """在线程中执行任务"""
        try:
            # 这里应该调用实际的任务执行逻辑
            # 暂时返回一个模拟结果
            logger.info(f"开始执行任务: {task_execution.task_id}")

            # 模拟任务执行
            time.sleep(1.0)

            result = f"任务 {task_execution.task_id} 执行完成"
            logger.info(f"任务执行完成: {task_execution.task_id}")

            return result

        except Exception as e:
            logger.error(f"任务执行出错: {task_execution.task_id}, 错误: {e}")
            raise

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否取消成功
        """
        # 委托给task_executor处理
        return await self.task_executor.cancel_task(task_id)
