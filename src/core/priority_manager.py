"""任务优先级管理模块.

提供动态优先级调整、资源分配和智能调度策略。
"""

import asyncio
import time
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Set
from threading import Lock
import heapq
import statistics

from .enhanced_task_executor import TaskConfig, TaskExecution, TaskStatus, TaskType, TaskPriority
from .events import EventBus
from .logger import get_logger


class PriorityAdjustmentReason(Enum):
    """优先级调整原因。"""
    USER_REQUEST = "user_request"         # 用户请求
    DEADLINE_APPROACHING = "deadline"     # 截止时间临近
    DEPENDENCY_READY = "dependency"       # 依赖就绪
    RESOURCE_AVAILABLE = "resource"       # 资源可用
    FAILURE_RECOVERY = "failure"          # 失败恢复
    LOAD_BALANCING = "load_balance"       # 负载均衡
    PERFORMANCE_OPTIMIZATION = "performance" # 性能优化
    SYSTEM_MAINTENANCE = "maintenance"    # 系统维护


class SchedulingStrategy(Enum):
    """调度策略。"""
    FIFO = "fifo"                        # 先进先出
    PRIORITY_FIRST = "priority_first"    # 优先级优先
    SHORTEST_JOB_FIRST = "sjf"           # 最短作业优先
    ROUND_ROBIN = "round_robin"          # 轮转调度
    WEIGHTED_FAIR = "weighted_fair"      # 加权公平调度
    ADAPTIVE = "adaptive"                # 自适应调度


@dataclass
class PriorityAdjustment:
    """优先级调整记录。"""
    task_id: str
    old_priority: TaskPriority
    new_priority: TaskPriority
    reason: PriorityAdjustmentReason
    timestamp: datetime
    adjustment_value: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)
    applied_by: Optional[str] = None


@dataclass
class TaskMetrics:
    """任务性能指标。"""
    task_id: str
    task_type: TaskType
    priority: TaskPriority
    estimated_duration: float = 0.0
    actual_duration: float = 0.0
    resource_usage: Dict[str, float] = field(default_factory=dict)
    success_rate: float = 1.0
    retry_count: int = 0
    last_execution: Optional[datetime] = None
    average_wait_time: float = 0.0
    deadline: Optional[datetime] = None
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)


@dataclass
class ResourceQuota:
    """资源配额。"""
    cpu_quota: float = 1.0
    memory_quota: float = 1.0
    network_quota: float = 1.0
    concurrent_limit: int = 1
    priority_weight: float = 1.0


class PriorityCalculator(ABC):
    """优先级计算器基类。"""
    
    @abstractmethod
    def calculate_priority(self, task_metrics: TaskMetrics, context: Dict[str, Any]) -> float:
        """计算任务优先级分数。
        
        Args:
            task_metrics: 任务指标
            context: 上下文信息
            
        Returns:
            优先级分数（越高越优先）
        """
        pass


class DeadlinePriorityCalculator(PriorityCalculator):
    """基于截止时间的优先级计算器。"""
    
    def calculate_priority(self, task_metrics: TaskMetrics, context: Dict[str, Any]) -> float:
        """根据截止时间计算优先级。"""
        if not task_metrics.deadline:
            return 0.0
        
        now = datetime.now()
        time_to_deadline = (task_metrics.deadline - now).total_seconds()
        
        # 截止时间越近，优先级越高
        if time_to_deadline <= 0:
            return 1000.0  # 已过期，最高优先级
        elif time_to_deadline <= 3600:  # 1小时内
            return 100.0
        elif time_to_deadline <= 86400:  # 1天内
            return 50.0
        else:
            return max(0.0, 10.0 - time_to_deadline / 86400)


class PerformancePriorityCalculator(PriorityCalculator):
    """基于性能的优先级计算器。"""
    
    def calculate_priority(self, task_metrics: TaskMetrics, context: Dict[str, Any]) -> float:
        """根据任务性能计算优先级。"""
        score = 0.0
        
        # 成功率因子
        score += task_metrics.success_rate * 20.0
        
        # 执行时间因子（短任务优先）
        if task_metrics.estimated_duration > 0:
            duration_score = max(0.0, 10.0 - task_metrics.estimated_duration / 60.0)
            score += duration_score
        
        # 重试次数惩罚
        score -= task_metrics.retry_count * 5.0
        
        # 等待时间因子
        if task_metrics.average_wait_time > 0:
            wait_score = min(20.0, task_metrics.average_wait_time / 60.0)
            score += wait_score
        
        return max(0.0, score)


class DependencyPriorityCalculator(PriorityCalculator):
    """基于依赖关系的优先级计算器。"""
    
    def calculate_priority(self, task_metrics: TaskMetrics, context: Dict[str, Any]) -> float:
        """根据依赖关系计算优先级。"""
        score = 0.0
        
        # 被依赖的任务优先级更高
        score += len(task_metrics.dependents) * 10.0
        
        # 依赖较少的任务优先级更高
        pending_dependencies = context.get('pending_dependencies', 0)
        if pending_dependencies == 0:
            score += 30.0  # 无依赖，可立即执行
        else:
            score -= pending_dependencies * 5.0
        
        return max(0.0, score)


class ResourcePriorityCalculator(PriorityCalculator):
    """基于资源的优先级计算器。"""
    
    def calculate_priority(self, task_metrics: TaskMetrics, context: Dict[str, Any]) -> float:
        """根据资源使用情况计算优先级。"""
        score = 0.0
        
        # 资源使用率低的任务优先级更高
        total_resource_usage = sum(task_metrics.resource_usage.values())
        if total_resource_usage > 0:
            score += max(0.0, 20.0 - total_resource_usage)
        else:
            score += 15.0  # 默认中等优先级
        
        # 系统负载因子
        system_load = context.get('system_load', 0.5)
        if system_load < 0.3:  # 低负载时优先执行重任务
            score += total_resource_usage * 0.5
        elif system_load > 0.8:  # 高负载时优先执行轻任务
            score -= total_resource_usage * 0.5
        
        return max(0.0, score)


class PriorityManager:
    """优先级管理器。"""
    
    def __init__(self, event_bus: Optional[EventBus] = None, strategy: SchedulingStrategy = SchedulingStrategy.ADAPTIVE):
        """初始化优先级管理器。
        
        Args:
            event_bus: 事件总线实例
            strategy: 调度策略
        """
        self.logger = get_logger(__name__)
        self.event_bus = event_bus or EventBus()
        self.strategy = strategy
        
        # 任务指标
        self.task_metrics: Dict[str, TaskMetrics] = {}
        self.metrics_lock = Lock()
        
        # 优先级调整历史
        self.adjustment_history: List[PriorityAdjustment] = []
        self.adjustment_lock = Lock()
        
        # 优先级计算器
        self.priority_calculators: List[PriorityCalculator] = [
            DeadlinePriorityCalculator(),
            PerformancePriorityCalculator(),
            DependencyPriorityCalculator(),
            ResourcePriorityCalculator()
        ]
        
        # 资源配额
        self.resource_quotas: Dict[TaskPriority, ResourceQuota] = {
            TaskPriority.CRITICAL: ResourceQuota(cpu_quota=2.0, memory_quota=2.0, concurrent_limit=5, priority_weight=4.0),
            TaskPriority.HIGH: ResourceQuota(cpu_quota=1.5, memory_quota=1.5, concurrent_limit=3, priority_weight=3.0),
            TaskPriority.MEDIUM: ResourceQuota(cpu_quota=1.0, memory_quota=1.0, concurrent_limit=2, priority_weight=2.0),
            TaskPriority.LOW: ResourceQuota(cpu_quota=0.5, memory_quota=0.5, concurrent_limit=1, priority_weight=1.0)
        }
        
        # 调度统计
        self.scheduling_stats = {
            'total_adjustments': 0,
            'automatic_adjustments': 0,
            'manual_adjustments': 0,
            'priority_distribution': {p.value: 0 for p in TaskPriority},
            'average_wait_time': 0.0,
            'throughput': 0.0
        }
        
        # 自动调整配置
        self.auto_adjustment_enabled = True
        self.adjustment_interval = 60.0  # 60秒检查一次
        self.adjustment_task: Optional[asyncio.Task] = None
        
        # 注册事件监听器
        self._register_event_listeners()
        
        self.logger.info(f"优先级管理器初始化完成，调度策略: {strategy.value}")
    
    def _register_event_listeners(self):
        """注册事件监听器。"""
        self.event_bus.on("task_submitted", self._on_task_submitted)
        self.event_bus.on("task_started", self._on_task_started)
        self.event_bus.on("task_completed", self._on_task_completed)
        self.event_bus.on("task_failed", self._on_task_failed)
        self.event_bus.on("system_metrics_updated", self._on_system_metrics_updated)
    
    async def _on_task_submitted(self, event_data: Dict[str, Any]):
        """处理任务提交事件。"""
        execution_id = event_data.get("execution_id")
        task_config = event_data.get("task_config")
        
        if execution_id and task_config:
            # 创建任务指标
            metrics = TaskMetrics(
                task_id=execution_id,
                task_type=task_config.task_type,
                priority=task_config.priority,
                estimated_duration=task_config.config.get('estimated_duration', 0.0),
                deadline=task_config.config.get('deadline'),
                dependencies=set(task_config.config.get('dependencies', []))
            )
            
            with self.metrics_lock:
                self.task_metrics[execution_id] = metrics
                self.scheduling_stats['priority_distribution'][task_config.priority.value] += 1
    
    async def _on_task_started(self, event_data: Dict[str, Any]):
        """处理任务开始事件。"""
        execution_id = event_data.get("execution_id")
        
        if execution_id in self.task_metrics:
            with self.metrics_lock:
                self.task_metrics[execution_id].last_execution = datetime.now()
    
    async def _on_task_completed(self, event_data: Dict[str, Any]):
        """处理任务完成事件。"""
        execution_id = event_data.get("execution_id")
        task_execution = event_data.get("task_execution")
        
        if execution_id in self.task_metrics and task_execution:
            with self.metrics_lock:
                metrics = self.task_metrics[execution_id]
                metrics.actual_duration = task_execution.execution_time
                
                # 更新成功率
                if metrics.retry_count > 0:
                    metrics.success_rate = 1.0 / (1.0 + metrics.retry_count)
                
                # 移除已完成的任务指标
                del self.task_metrics[execution_id]
    
    async def _on_task_failed(self, event_data: Dict[str, Any]):
        """处理任务失败事件。"""
        execution_id = event_data.get("execution_id")
        task_execution = event_data.get("task_execution")
        
        if execution_id in self.task_metrics and task_execution:
            with self.metrics_lock:
                metrics = self.task_metrics[execution_id]
                metrics.retry_count = task_execution.retry_count
                metrics.success_rate = max(0.1, 1.0 - (metrics.retry_count * 0.2))
    
    async def _on_system_metrics_updated(self, event_data: Dict[str, Any]):
        """处理系统指标更新事件。"""
        if self.auto_adjustment_enabled:
            # 触发自动优先级调整
            await self._auto_adjust_priorities(event_data.get('metrics'))
    
    async def start_auto_adjustment(self):
        """启动自动优先级调整。"""
        if self.adjustment_task and not self.adjustment_task.done():
            return
        
        self.auto_adjustment_enabled = True
        self.adjustment_task = asyncio.create_task(self._adjustment_loop())
        self.logger.info("自动优先级调整已启动")
    
    async def stop_auto_adjustment(self):
        """停止自动优先级调整。"""
        self.auto_adjustment_enabled = False
        
        if self.adjustment_task and not self.adjustment_task.done():
            self.adjustment_task.cancel()
            try:
                await self.adjustment_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("自动优先级调整已停止")
    
    async def _adjustment_loop(self):
        """优先级调整循环。"""
        while self.auto_adjustment_enabled:
            try:
                await self._periodic_adjustment()
                await asyncio.sleep(self.adjustment_interval)
                
            except Exception as e:
                self.logger.error(f"优先级调整循环错误: {e}")
                await asyncio.sleep(5.0)
    
    async def _periodic_adjustment(self):
        """定期优先级调整。"""
        with self.metrics_lock:
            current_metrics = list(self.task_metrics.values())
        
        for metrics in current_metrics:
            # 检查截止时间
            if metrics.deadline:
                time_to_deadline = (metrics.deadline - datetime.now()).total_seconds()
                if time_to_deadline <= 3600 and metrics.priority != TaskPriority.CRITICAL:
                    # 1小时内截止，提升为关键优先级
                    await self.adjust_task_priority(
                        metrics.task_id,
                        TaskPriority.CRITICAL,
                        PriorityAdjustmentReason.DEADLINE_APPROACHING
                    )
            
            # 检查等待时间
            if metrics.last_execution:
                wait_time = (datetime.now() - metrics.last_execution).total_seconds()
                if wait_time > 1800 and metrics.priority == TaskPriority.LOW:  # 等待超过30分钟
                    await self.adjust_task_priority(
                        metrics.task_id,
                        TaskPriority.MEDIUM,
                        PriorityAdjustmentReason.PERFORMANCE_OPTIMIZATION
                    )
    
    async def _auto_adjust_priorities(self, system_metrics: Any):
        """自动调整优先级。"""
        if not system_metrics:
            return
        
        # 根据系统负载调整
        if hasattr(system_metrics, 'total_cpu_usage'):
            cpu_usage = system_metrics.total_cpu_usage
            
            if cpu_usage > 0.9:  # 高CPU使用率
                # 降低低优先级任务的优先级
                await self._adjust_by_system_load(high_load=True)
            elif cpu_usage < 0.3:  # 低CPU使用率
                # 可以提升一些任务的优先级
                await self._adjust_by_system_load(high_load=False)
    
    async def _adjust_by_system_load(self, high_load: bool):
        """根据系统负载调整优先级。"""
        with self.metrics_lock:
            current_metrics = list(self.task_metrics.values())
        
        for metrics in current_metrics:
            if high_load:
                # 高负载时降低低优先级任务
                if metrics.priority == TaskPriority.LOW:
                    # 暂时不调整，避免过度调整
                    pass
            else:
                # 低负载时可以提升一些任务
                if (metrics.priority == TaskPriority.MEDIUM and 
                    len(metrics.dependents) > 2):  # 被多个任务依赖
                    await self.adjust_task_priority(
                        metrics.task_id,
                        TaskPriority.HIGH,
                        PriorityAdjustmentReason.LOAD_BALANCING
                    )
    
    async def adjust_task_priority(self, task_id: str, new_priority: TaskPriority, 
                                 reason: PriorityAdjustmentReason, 
                                 applied_by: Optional[str] = None) -> bool:
        """调整任务优先级。
        
        Args:
            task_id: 任务ID
            new_priority: 新优先级
            reason: 调整原因
            applied_by: 调整者
            
        Returns:
            是否调整成功
        """
        with self.metrics_lock:
            if task_id not in self.task_metrics:
                self.logger.warning(f"任务 {task_id} 不存在，无法调整优先级")
                return False
            
            metrics = self.task_metrics[task_id]
            old_priority = metrics.priority
            
            if old_priority == new_priority:
                return True  # 优先级相同，无需调整
            
            # 更新优先级
            metrics.priority = new_priority
            
            # 记录调整
            adjustment = PriorityAdjustment(
                task_id=task_id,
                old_priority=old_priority,
                new_priority=new_priority,
                reason=reason,
                timestamp=datetime.now(),
                applied_by=applied_by or "system"
            )
            
            with self.adjustment_lock:
                self.adjustment_history.append(adjustment)
                self.scheduling_stats['total_adjustments'] += 1
                
                if applied_by:
                    self.scheduling_stats['manual_adjustments'] += 1
                else:
                    self.scheduling_stats['automatic_adjustments'] += 1
                
                # 更新优先级分布
                self.scheduling_stats['priority_distribution'][old_priority.value] -= 1
                self.scheduling_stats['priority_distribution'][new_priority.value] += 1
        
        # 发送优先级调整事件
        await self.event_bus.emit("priority_adjusted", {
            "task_id": task_id,
            "old_priority": old_priority,
            "new_priority": new_priority,
            "reason": reason,
            "adjustment": adjustment
        })
        
        self.logger.info(f"任务 {task_id} 优先级从 {old_priority.value} 调整为 {new_priority.value}，原因: {reason.value}")
        
        return True
    
    def calculate_dynamic_priority(self, task_id: str, context: Dict[str, Any] = None) -> float:
        """计算动态优先级分数。
        
        Args:
            task_id: 任务ID
            context: 上下文信息
            
        Returns:
            优先级分数
        """
        context = context or {}
        
        with self.metrics_lock:
            if task_id not in self.task_metrics:
                return 0.0
            
            metrics = self.task_metrics[task_id]
        
        total_score = 0.0
        
        # 基础优先级分数
        base_scores = {
            TaskPriority.CRITICAL: 1000.0,
            TaskPriority.HIGH: 100.0,
            TaskPriority.MEDIUM: 10.0,
            TaskPriority.LOW: 1.0
        }
        total_score += base_scores.get(metrics.priority, 1.0)
        
        # 使用各个计算器计算额外分数
        for calculator in self.priority_calculators:
            try:
                score = calculator.calculate_priority(metrics, context)
                total_score += score
            except Exception as e:
                self.logger.error(f"优先级计算器 {type(calculator).__name__} 执行失败: {e}")
        
        return max(0.0, total_score)
    
    def get_task_queue_order(self, task_ids: List[str], context: Dict[str, Any] = None) -> List[str]:
        """获取任务队列执行顺序。
        
        Args:
            task_ids: 任务ID列表
            context: 上下文信息
            
        Returns:
            排序后的任务ID列表
        """
        context = context or {}
        
        if self.strategy == SchedulingStrategy.FIFO:
            return task_ids  # 保持原顺序
        
        elif self.strategy == SchedulingStrategy.PRIORITY_FIRST:
            # 按优先级排序
            task_priorities = []
            for task_id in task_ids:
                priority_score = self.calculate_dynamic_priority(task_id, context)
                task_priorities.append((priority_score, task_id))
            
            # 按优先级分数降序排列
            task_priorities.sort(key=lambda x: x[0], reverse=True)
            return [task_id for _, task_id in task_priorities]
        
        elif self.strategy == SchedulingStrategy.SHORTEST_JOB_FIRST:
            # 按预估执行时间排序
            task_durations = []
            for task_id in task_ids:
                with self.metrics_lock:
                    if task_id in self.task_metrics:
                        duration = self.task_metrics[task_id].estimated_duration
                    else:
                        duration = float('inf')
                task_durations.append((duration, task_id))
            
            task_durations.sort(key=lambda x: x[0])
            return [task_id for _, task_id in task_durations]
        
        elif self.strategy == SchedulingStrategy.ADAPTIVE:
            # 自适应调度：综合考虑多个因素
            return self._adaptive_scheduling(task_ids, context)
        
        else:
            # 默认按优先级排序
            return self.get_task_queue_order(task_ids, context)
    
    def _adaptive_scheduling(self, task_ids: List[str], context: Dict[str, Any]) -> List[str]:
        """自适应调度算法。"""
        task_scores = []
        
        for task_id in task_ids:
            # 综合分数计算
            priority_score = self.calculate_dynamic_priority(task_id, context)
            
            # 考虑系统负载
            system_load = context.get('system_load', 0.5)
            
            with self.metrics_lock:
                if task_id in self.task_metrics:
                    metrics = self.task_metrics[task_id]
                    
                    # 资源使用调整
                    resource_factor = 1.0
                    if system_load > 0.8:  # 高负载时偏向轻任务
                        total_resource = sum(metrics.resource_usage.values())
                        resource_factor = max(0.1, 1.0 - total_resource * 0.1)
                    
                    # 等待时间调整
                    wait_factor = 1.0
                    if metrics.last_execution:
                        wait_time = (datetime.now() - metrics.last_execution).total_seconds()
                        wait_factor = min(2.0, 1.0 + wait_time / 3600.0)  # 等待越久权重越高
                    
                    final_score = priority_score * resource_factor * wait_factor
                else:
                    final_score = priority_score
            
            task_scores.append((final_score, task_id))
        
        # 按最终分数降序排列
        task_scores.sort(key=lambda x: x[0], reverse=True)
        return [task_id for _, task_id in task_scores]
    
    def get_resource_quota(self, priority: TaskPriority) -> ResourceQuota:
        """获取优先级对应的资源配额。
        
        Args:
            priority: 任务优先级
            
        Returns:
            资源配额
        """
        return self.resource_quotas.get(priority, ResourceQuota())
    
    def update_resource_quota(self, priority: TaskPriority, quota: ResourceQuota):
        """更新资源配额。
        
        Args:
            priority: 任务优先级
            quota: 新的资源配额
        """
        self.resource_quotas[priority] = quota
        self.logger.info(f"更新 {priority.value} 优先级的资源配额")
    
    def get_priority_statistics(self) -> Dict[str, Any]:
        """获取优先级统计信息。
        
        Returns:
            统计信息
        """
        with self.adjustment_lock:
            stats = self.scheduling_stats.copy()
        
        # 计算调整频率
        if len(self.adjustment_history) > 1:
            time_span = (self.adjustment_history[-1].timestamp - 
                        self.adjustment_history[0].timestamp).total_seconds()
            if time_span > 0:
                stats['adjustment_frequency'] = len(self.adjustment_history) / (time_span / 3600.0)  # 每小时调整次数
            else:
                stats['adjustment_frequency'] = 0.0
        else:
            stats['adjustment_frequency'] = 0.0
        
        # 最近调整
        recent_adjustments = [adj for adj in self.adjustment_history 
                            if (datetime.now() - adj.timestamp).total_seconds() <= 3600]
        stats['recent_adjustments'] = len(recent_adjustments)
        
        # 调整原因分布
        reason_counts = defaultdict(int)
        for adj in recent_adjustments:
            reason_counts[adj.reason.value] += 1
        stats['adjustment_reasons'] = dict(reason_counts)
        
        return stats
    
    def get_adjustment_history(self, hours: int = 24) -> List[PriorityAdjustment]:
        """获取优先级调整历史。
        
        Args:
            hours: 时间范围（小时）
            
        Returns:
            调整历史列表
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.adjustment_lock:
            recent_adjustments = [
                adj for adj in self.adjustment_history
                if adj.timestamp >= cutoff_time
            ]
        
        return sorted(recent_adjustments, key=lambda x: x.timestamp, reverse=True)
    
    async def shutdown(self):
        """关闭优先级管理器。"""
        self.logger.info("优先级管理器正在关闭...")
        
        # 停止自动调整
        await self.stop_auto_adjustment()
        
        # 清理资源
        with self.metrics_lock:
            self.task_metrics.clear()
        
        with self.adjustment_lock:
            self.adjustment_history.clear()
        
        self.logger.info("优先级管理器已关闭")