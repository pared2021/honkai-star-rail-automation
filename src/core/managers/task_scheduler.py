# -*- coding: utf-8 -*-
"""任务调度管理器

专门负责任务调度相关功能，包括：
- 任务调度队列管理
- 优先级调度
- 依赖关系管理
- 调度策略
- 并发控制
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Callable
from collections import defaultdict, deque
from enum import Enum
import heapq
from loguru import logger

from src.core.interfaces import ITaskScheduler, IConfigManager
from src.core.dependency_injection import Injectable, inject
from src.models.task_models import TaskPriority, TaskStatus
from src.exceptions import TaskSchedulingError, CircularDependencyError


class SchedulingStrategy(Enum):
    """调度策略"""
    FIFO = "fifo"  # 先进先出
    PRIORITY = "priority"  # 优先级调度
    FAIR_SHARE = "fair_share"  # 公平共享
    DEADLINE = "deadline"  # 截止时间优先


class TaskScheduler(Injectable, ITaskScheduler):
    """任务调度管理器
    
    提供任务调度功能：
    - 多种调度策略
    - 优先级队列管理
    - 依赖关系处理
    - 并发控制
    - 调度统计
    """
    
    def __init__(
        self,
        config_manager: IConfigManager,
        max_concurrent_tasks: Optional[int] = None,
        strategy: Optional[SchedulingStrategy] = None
    ):
        """初始化任务调度器
        
        Args:
            config_manager: 配置管理器
            max_concurrent_tasks: 最大并发任务数
            strategy: 调度策略
        """
        super().__init__()
        self._config_manager = config_manager
        self._max_concurrent_tasks = max_concurrent_tasks or config_manager.get('scheduler.max_concurrent_tasks', 10)
        self._strategy = strategy or SchedulingStrategy(config_manager.get('scheduler.strategy', 'priority'))
        self._is_running = False
        
        # 调度队列
        self._priority_queues = {
            TaskPriority.CRITICAL: [],
            TaskPriority.HIGH: [],
            TaskPriority.MEDIUM: [],
            TaskPriority.LOW: []
        }
        
        # 依赖关系图
        self._dependencies: Dict[str, Set[str]] = defaultdict(set)  # task_id -> dependencies
        self._dependents: Dict[str, Set[str]] = defaultdict(set)    # task_id -> dependents
        
        # 调度状态
        self._scheduled_tasks: Set[str] = set()
        self._pending_tasks: Set[str] = set()
        self._running_tasks: Set[str] = set()
        
        # 优先级权重
        self._priority_weights = {
            TaskPriority.CRITICAL: config_manager.get('scheduler.priority_weights.critical', 1000),
            TaskPriority.HIGH: config_manager.get('scheduler.priority_weights.high', 100),
            TaskPriority.MEDIUM: config_manager.get('scheduler.priority_weights.medium', 10),
            TaskPriority.LOW: config_manager.get('scheduler.priority_weights.low', 1)
        }
        
        # 调度回调
        self._execution_callbacks: List[Callable] = []
        
        # 调度统计
        self._stats = {
            'total_scheduled': 0,
            'total_executed': 0,
            'total_failed': 0,
            'total_cancelled': 0,
            'avg_wait_time': 0.0,
            'avg_execution_time': 0.0
        }
        
        # 任务时间记录
        self._task_times: Dict[str, Dict[str, datetime]] = {}
        
        # 调度器任务
        self._scheduler_task: Optional[asyncio.Task] = None
        
        logger.info(f"任务调度器初始化完成，最大并发: {max_concurrent_tasks}，策略: {strategy.value}")
    
    async def start_scheduler(self) -> bool:
        """启动调度器
        
        Returns:
            是否启动成功
        """
        try:
            if self._is_running:
                logger.warning("调度器已在运行")
                return True
            
            self._is_running = True
            self._scheduler_task = asyncio.create_task(self._scheduler_loop())
            
            logger.info("任务调度器已启动")
            return True
            
        except Exception as e:
            logger.error(f"启动调度器失败: {e}")
            self._is_running = False
            return False
    
    async def stop_scheduler(self) -> bool:
        """停止调度器
        
        Returns:
            是否停止成功
        """
        try:
            if not self._is_running:
                logger.warning("调度器未在运行")
                return True
            
            self._is_running = False
            
            if self._scheduler_task:
                self._scheduler_task.cancel()
                try:
                    await self._scheduler_task
                except asyncio.CancelledError:
                    pass
                self._scheduler_task = None
            
            logger.info("任务调度器已停止")
            return True
            
        except Exception as e:
            logger.error(f"停止调度器失败: {e}")
            return False
    
    async def schedule_task(
        self,
        task_id: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        delay: Optional[timedelta] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """调度任务
        
        Args:
            task_id: 任务ID
            priority: 任务优先级
            delay: 延迟执行时间
            metadata: 任务元数据
            
        Returns:
            是否调度成功
        """
        try:
            if task_id in self._scheduled_tasks:
                logger.warning(f"任务已被调度: {task_id}")
                return False
            
            # 计算调度时间
            scheduled_time = datetime.now()
            if delay:
                scheduled_time += delay
            
            # 创建调度项
            schedule_item = {
                'task_id': task_id,
                'priority': priority,
                'scheduled_time': scheduled_time,
                'created_time': datetime.now(),
                'metadata': metadata or {}
            }
            
            # 添加到优先级队列
            priority_score = self._calculate_priority_score(priority, scheduled_time)
            heapq.heappush(
                self._priority_queues[priority],
                (priority_score, scheduled_time, task_id, schedule_item)
            )
            
            # 更新状态
            self._scheduled_tasks.add(task_id)
            self._pending_tasks.add(task_id)
            
            # 记录调度时间
            self._task_times[task_id] = {
                'scheduled_at': datetime.now(),
                'priority': priority
            }
            
            self._stats['total_scheduled'] += 1
            
            logger.info(f"任务调度成功: {task_id} - 优先级: {priority.value}")
            return True
            
        except Exception as e:
            logger.error(f"调度任务失败: {task_id} - {e}")
            return False
    
    async def cancel_task_schedule(self, task_id: str) -> bool:
        """取消任务调度
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否取消成功
        """
        try:
            if task_id not in self._scheduled_tasks:
                logger.warning(f"任务未被调度: {task_id}")
                return False
            
            # 从队列中移除（标记为取消）
            for priority_queue in self._priority_queues.values():
                for i, (score, time, tid, item) in enumerate(priority_queue):
                    if tid == task_id:
                        item['cancelled'] = True
                        break
            
            # 更新状态
            self._scheduled_tasks.discard(task_id)
            self._pending_tasks.discard(task_id)
            self._running_tasks.discard(task_id)
            
            # 清理时间记录
            self._task_times.pop(task_id, None)
            
            self._stats['total_cancelled'] += 1
            
            logger.info(f"任务调度取消成功: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"取消任务调度失败: {task_id} - {e}")
            return False
    
    async def get_scheduled_tasks(self) -> List[str]:
        """获取已调度任务列表
        
        Returns:
            任务ID列表
        """
        return list(self._scheduled_tasks)
    
    async def get_pending_tasks(self) -> List[str]:
        """获取待执行任务列表
        
        Returns:
            任务ID列表
        """
        return list(self._pending_tasks)
    
    async def add_task_dependency(self, task_id: str, dependency_id: str) -> bool:
        """添加任务依赖
        
        Args:
            task_id: 任务ID
            dependency_id: 依赖任务ID
            
        Returns:
            是否添加成功
            
        Raises:
            CircularDependencyError: 检测到循环依赖
        """
        try:
            # 检查循环依赖
            if await self._would_create_cycle(task_id, dependency_id):
                raise CircularDependencyError(
                    f"添加依赖会创建循环: {task_id} -> {dependency_id}"
                )
            
            # 添加依赖关系
            self._dependencies[task_id].add(dependency_id)
            self._dependents[dependency_id].add(task_id)
            
            logger.info(f"添加任务依赖: {task_id} -> {dependency_id}")
            return True
            
        except Exception as e:
            logger.error(f"添加任务依赖失败: {task_id} -> {dependency_id} - {e}")
            return False
    
    async def remove_task_dependency(self, task_id: str, dependency_id: str) -> bool:
        """移除任务依赖
        
        Args:
            task_id: 任务ID
            dependency_id: 依赖任务ID
            
        Returns:
            是否移除成功
        """
        try:
            self._dependencies[task_id].discard(dependency_id)
            self._dependents[dependency_id].discard(task_id)
            
            # 清理空集合
            if not self._dependencies[task_id]:
                del self._dependencies[task_id]
            if not self._dependents[dependency_id]:
                del self._dependents[dependency_id]
            
            logger.info(f"移除任务依赖: {task_id} -> {dependency_id}")
            return True
            
        except Exception as e:
            logger.error(f"移除任务依赖失败: {task_id} -> {dependency_id} - {e}")
            return False
    
    async def get_task_dependencies(self, task_id: str) -> List[str]:
        """获取任务依赖列表
        
        Args:
            task_id: 任务ID
            
        Returns:
            依赖任务ID列表
        """
        return list(self._dependencies.get(task_id, set()))
    
    async def clear_task_dependencies(self, task_id: str) -> bool:
        """清除任务的所有依赖
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否清除成功
        """
        try:
            # 移除作为依赖者的关系
            dependencies = self._dependencies.get(task_id, set()).copy()
            for dep_id in dependencies:
                await self.remove_task_dependency(task_id, dep_id)
            
            # 移除作为被依赖者的关系
            dependents = self._dependents.get(task_id, set()).copy()
            for dep_id in dependents:
                await self.remove_task_dependency(dep_id, task_id)
            
            logger.info(f"清除任务依赖: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"清除任务依赖失败: {task_id} - {e}")
            return False
    
    async def check_dependencies_satisfied(self, task_id: str) -> bool:
        """检查任务依赖是否满足
        
        Args:
            task_id: 任务ID
            
        Returns:
            依赖是否全部满足
        """
        dependencies = self._dependencies.get(task_id, set())
        if not dependencies:
            return True
        
        # 这里需要查询依赖任务的状态
        # 实际实现中需要注入任务管理器来查询状态
        # 暂时返回True，实际使用时需要完善
        return True
    
    async def check_circular_dependency(self, task_id: str) -> bool:
        """检查是否存在循环依赖
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否存在循环依赖
        """
        visited = set()
        rec_stack = set()
        
        def dfs(node: str) -> bool:
            if node in rec_stack:
                return True  # 发现循环
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self._dependencies.get(node, set()):
                if dfs(neighbor):
                    return True
            
            rec_stack.remove(node)
            return False
        
        return dfs(task_id)
    
    async def set_priority_weights(self, weights: Dict[TaskPriority, int]) -> bool:
        """设置优先级权重
        
        Args:
            weights: 优先级权重映射
            
        Returns:
            是否设置成功
        """
        try:
            self._priority_weights.update(weights)
            logger.info(f"优先级权重已更新: {weights}")
            return True
        except Exception as e:
            logger.error(f"设置优先级权重失败: {e}")
            return False
    
    async def calculate_task_priority(self, task_id: str, base_priority: TaskPriority) -> float:
        """计算任务优先级分数
        
        Args:
            task_id: 任务ID
            base_priority: 基础优先级
            
        Returns:
            优先级分数
        """
        base_score = self._priority_weights.get(base_priority, 1)
        
        # 考虑等待时间
        if task_id in self._task_times:
            wait_time = datetime.now() - self._task_times[task_id]['scheduled_at']
            wait_bonus = wait_time.total_seconds() / 3600  # 每小时增加1分
            base_score += wait_bonus
        
        return base_score
    
    async def set_max_concurrent_tasks(self, max_tasks: int) -> bool:
        """设置最大并发任务数
        
        Args:
            max_tasks: 最大并发任务数
            
        Returns:
            是否设置成功
        """
        try:
            self._max_concurrent_tasks = max_tasks
            logger.info(f"最大并发任务数已更新: {max_tasks}")
            return True
        except Exception as e:
            logger.error(f"设置最大并发任务数失败: {e}")
            return False
    
    async def get_scheduler_status(self) -> Dict[str, Any]:
        """获取调度器状态
        
        Returns:
            状态信息字典
        """
        return {
            'is_running': self._is_running,
            'max_concurrent_tasks': self._max_concurrent_tasks,
            'strategy': self._strategy.value,
            'scheduled_tasks_count': len(self._scheduled_tasks),
            'pending_tasks_count': len(self._pending_tasks),
            'running_tasks_count': len(self._running_tasks),
            'queue_sizes': {
                priority.value: len(queue)
                for priority, queue in self._priority_queues.items()
            },
            'dependencies_count': len(self._dependencies),
            'stats': self._stats.copy()
        }
    
    async def reset_statistics(self) -> bool:
        """重置调度统计信息
        
        Returns:
            是否重置成功
        """
        try:
            self._stats = {
                'total_scheduled': 0,
                'total_executed': 0,
                'total_failed': 0,
                'total_cancelled': 0,
                'avg_wait_time': 0.0,
                'avg_execution_time': 0.0
            }
            self._task_times.clear()
            logger.info("调度统计信息已重置")
            return True
        except Exception as e:
            logger.error(f"重置统计信息失败: {e}")
            return False
    
    async def get_dependency_graph(self) -> Dict[str, List[str]]:
        """获取依赖关系图
        
        Returns:
            依赖关系图
        """
        return {
            task_id: list(deps)
            for task_id, deps in self._dependencies.items()
        }
    
    async def set_task_execution_callback(self, callback: Callable) -> bool:
        """设置任务执行回调
        
        Args:
            callback: 回调函数
            
        Returns:
            是否设置成功
        """
        try:
            if callback not in self._execution_callbacks:
                self._execution_callbacks.append(callback)
            return True
        except Exception as e:
            logger.error(f"设置执行回调失败: {e}")
            return False
    
    async def remove_task_execution_callback(self, callback: Callable) -> bool:
        """移除任务执行回调
        
        Args:
            callback: 回调函数
            
        Returns:
            是否移除成功
        """
        try:
            if callback in self._execution_callbacks:
                self._execution_callbacks.remove(callback)
            return True
        except Exception as e:
            logger.error(f"移除执行回调失败: {e}")
            return False
    
    # 私有方法
    
    async def _scheduler_loop(self):
        """调度器主循环"""
        logger.info("调度器主循环开始")
        
        while self._is_running:
            try:
                await self._process_scheduled_tasks()
                await asyncio.sleep(self._config_manager.get('scheduler.loop_interval', 1))  # 调度间隔
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"调度器循环错误: {e}")
                await asyncio.sleep(self._config_manager.get('scheduler.error_wait_time', 5))  # 错误后等待
        
        logger.info("调度器主循环结束")
    
    async def _process_scheduled_tasks(self):
        """处理调度的任务"""
        if len(self._running_tasks) >= self._max_concurrent_tasks:
            return
        
        # 按优先级顺序处理队列
        for priority in [TaskPriority.CRITICAL, TaskPriority.HIGH, TaskPriority.MEDIUM, TaskPriority.LOW]:
            queue = self._priority_queues[priority]
            
            while queue and len(self._running_tasks) < self._max_concurrent_tasks:
                try:
                    score, scheduled_time, task_id, item = heapq.heappop(queue)
                    
                    # 检查是否被取消
                    if item.get('cancelled', False):
                        continue
                    
                    # 检查是否到达调度时间
                    if datetime.now() < scheduled_time:
                        # 重新放回队列
                        heapq.heappush(queue, (score, scheduled_time, task_id, item))
                        break
                    
                    # 检查依赖是否满足
                    if not await self.check_dependencies_satisfied(task_id):
                        # 重新调度
                        retry_delay = self._config_manager.get('scheduler.dependency_retry_delay', 30)
                        new_time = datetime.now() + timedelta(seconds=retry_delay)
                        new_score = self._calculate_priority_score(priority, new_time)
                        item['scheduled_time'] = new_time
                        heapq.heappush(queue, (new_score, new_time, task_id, item))
                        continue
                    
                    # 执行任务
                    await self._execute_task(task_id, item)
                    
                except Exception as e:
                    logger.error(f"处理调度任务失败: {e}")
    
    async def _execute_task(self, task_id: str, item: Dict[str, Any]):
        """执行任务"""
        try:
            # 更新状态
            self._pending_tasks.discard(task_id)
            self._running_tasks.add(task_id)
            
            # 记录开始时间
            if task_id in self._task_times:
                self._task_times[task_id]['started_at'] = datetime.now()
            
            # 调用执行回调
            for callback in self._execution_callbacks:
                try:
                    await callback(task_id, item)
                except Exception as e:
                    logger.error(f"执行回调失败: {callback} - {e}")
            
            self._stats['total_executed'] += 1
            logger.info(f"任务开始执行: {task_id}")
            
        except Exception as e:
            logger.error(f"执行任务失败: {task_id} - {e}")
            self._stats['total_failed'] += 1
            
            # 清理状态
            self._running_tasks.discard(task_id)
            self._scheduled_tasks.discard(task_id)
    
    def _calculate_priority_score(self, priority: TaskPriority, scheduled_time: datetime) -> float:
        """计算优先级分数"""
        base_score = -self._priority_weights.get(priority, 1)  # 负数用于最小堆
        
        # 添加时间因子
        time_factor = scheduled_time.timestamp()
        
        return base_score + time_factor
    
    async def _would_create_cycle(self, task_id: str, dependency_id: str) -> bool:
        """检查添加依赖是否会创建循环"""
        # 从dependency_id开始DFS，看是否能到达task_id
        visited = set()
        
        def dfs(node: str) -> bool:
            if node == task_id:
                return True
            if node in visited:
                return False
            
            visited.add(node)
            for dep in self._dependencies.get(node, set()):
                if dfs(dep):
                    return True
            return False
        
        return dfs(dependency_id)