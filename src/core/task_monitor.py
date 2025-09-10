"""任务监控模块.

提供任务状态跟踪、性能监控和统计报告功能。
"""

import asyncio
import time
import json
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from threading import Lock
import statistics

from .enhanced_task_executor import TaskExecution, TaskStatus, TaskType, TaskPriority
from .events import EventBus
from .logger import get_logger


@dataclass
class TaskMetrics:
    """任务执行指标。"""
    task_id: str
    task_type: TaskType
    priority: TaskPriority
    start_time: datetime
    end_time: Optional[datetime] = None
    execution_time: float = 0.0
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    error_message: Optional[str] = None
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    
    @property
    def duration(self) -> float:
        """获取任务持续时间（秒）。"""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        elif self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return 0.0
    
    @property
    def is_completed(self) -> bool:
        """检查任务是否已完成。"""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]


@dataclass
class SystemMetrics:
    """系统性能指标。"""
    timestamp: datetime
    active_tasks: int = 0
    queued_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_memory_usage: float = 0.0
    total_cpu_usage: float = 0.0
    average_execution_time: float = 0.0
    throughput: float = 0.0  # 每分钟完成的任务数
    error_rate: float = 0.0  # 错误率百分比


@dataclass
class PerformanceReport:
    """性能报告。"""
    report_id: str
    start_time: datetime
    end_time: datetime
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    cancelled_tasks: int
    average_execution_time: float
    min_execution_time: float
    max_execution_time: float
    throughput: float
    error_rate: float
    task_type_stats: Dict[str, Dict[str, Any]]
    priority_stats: Dict[str, Dict[str, Any]]
    hourly_stats: List[Dict[str, Any]]
    top_errors: List[Dict[str, Any]]


class TaskMonitor:
    """任务监控器。"""
    
    def __init__(self, event_bus: Optional[EventBus] = None, max_history: int = 10000):
        """初始化任务监控器。
        
        Args:
            event_bus: 事件总线实例
            max_history: 最大历史记录数量
        """
        self.logger = get_logger(__name__)
        self.event_bus = event_bus or EventBus()
        self.max_history = max_history
        
        # 任务指标存储
        self.task_metrics: Dict[str, TaskMetrics] = {}
        self.completed_metrics: deque = deque(maxlen=max_history)
        
        # 系统指标历史
        self.system_metrics_history: deque = deque(maxlen=1000)  # 保留最近1000个系统指标
        
        # 统计数据
        self.stats_lock = Lock()
        self.task_type_counters = defaultdict(lambda: defaultdict(int))
        self.priority_counters = defaultdict(lambda: defaultdict(int))
        self.error_counters = defaultdict(int)
        self.hourly_stats = defaultdict(lambda: defaultdict(int))
        
        # 性能监控
        self.monitoring_enabled = True
        self.monitoring_interval = 30.0  # 30秒监控间隔
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # 注册事件监听器
        self._register_event_listeners()
        
        self.logger.info("任务监控器初始化完成")
    
    def _register_event_listeners(self):
        """注册事件监听器。"""
        self.event_bus.on("task_submitted", self._on_task_submitted)
        self.event_bus.on("task_started", self._on_task_started)
        self.event_bus.on("task_completed", self._on_task_completed)
        self.event_bus.on("task_failed", self._on_task_failed)
        self.event_bus.on("task_cancelled", self._on_task_cancelled)
    
    async def _on_task_submitted(self, event_data: Dict[str, Any]):
        """处理任务提交事件。"""
        execution_id = event_data.get("execution_id")
        task_config = event_data.get("task_config")
        
        if execution_id and task_config:
            metrics = TaskMetrics(
                task_id=execution_id,
                task_type=task_config.task_type,
                priority=task_config.priority,
                start_time=datetime.now(),
                status=TaskStatus.QUEUED
            )
            
            self.task_metrics[execution_id] = metrics
            
            with self.stats_lock:
                self.task_type_counters[task_config.task_type.value]["submitted"] += 1
                self.priority_counters[task_config.priority.value]["submitted"] += 1
    
    async def _on_task_started(self, event_data: Dict[str, Any]):
        """处理任务开始事件。"""
        execution_id = event_data.get("execution_id")
        
        if execution_id in self.task_metrics:
            metrics = self.task_metrics[execution_id]
            metrics.status = TaskStatus.RUNNING
            metrics.start_time = datetime.now()
            
            with self.stats_lock:
                self.task_type_counters[metrics.task_type.value]["started"] += 1
                self.priority_counters[metrics.priority.value]["started"] += 1
    
    async def _on_task_completed(self, event_data: Dict[str, Any]):
        """处理任务完成事件。"""
        execution_id = event_data.get("execution_id")
        task_execution = event_data.get("task_execution")
        
        if execution_id in self.task_metrics and task_execution:
            metrics = self.task_metrics[execution_id]
            metrics.status = TaskStatus.COMPLETED
            metrics.end_time = datetime.now()
            metrics.execution_time = task_execution.execution_time
            
            # 移动到完成历史
            self.completed_metrics.append(metrics)
            del self.task_metrics[execution_id]
            
            with self.stats_lock:
                self.task_type_counters[metrics.task_type.value]["completed"] += 1
                self.priority_counters[metrics.priority.value]["completed"] += 1
                
                # 更新小时统计
                hour_key = metrics.end_time.strftime("%Y-%m-%d %H")
                self.hourly_stats[hour_key]["completed"] += 1
    
    async def _on_task_failed(self, event_data: Dict[str, Any]):
        """处理任务失败事件。"""
        execution_id = event_data.get("execution_id")
        task_execution = event_data.get("task_execution")
        error = event_data.get("error")
        
        if execution_id in self.task_metrics and task_execution:
            metrics = self.task_metrics[execution_id]
            metrics.status = TaskStatus.FAILED
            metrics.end_time = datetime.now()
            metrics.execution_time = task_execution.execution_time
            metrics.retry_count = task_execution.retry_count
            metrics.error_message = str(error) if error else "未知错误"
            
            # 移动到完成历史
            self.completed_metrics.append(metrics)
            del self.task_metrics[execution_id]
            
            with self.stats_lock:
                self.task_type_counters[metrics.task_type.value]["failed"] += 1
                self.priority_counters[metrics.priority.value]["failed"] += 1
                self.error_counters[metrics.error_message] += 1
                
                # 更新小时统计
                hour_key = metrics.end_time.strftime("%Y-%m-%d %H")
                self.hourly_stats[hour_key]["failed"] += 1
    
    async def _on_task_cancelled(self, event_data: Dict[str, Any]):
        """处理任务取消事件。"""
        execution_id = event_data.get("execution_id")
        task_execution = event_data.get("task_execution")
        
        if execution_id in self.task_metrics and task_execution:
            metrics = self.task_metrics[execution_id]
            metrics.status = TaskStatus.CANCELLED
            metrics.end_time = datetime.now()
            
            # 移动到完成历史
            self.completed_metrics.append(metrics)
            del self.task_metrics[execution_id]
            
            with self.stats_lock:
                self.task_type_counters[metrics.task_type.value]["cancelled"] += 1
                self.priority_counters[metrics.priority.value]["cancelled"] += 1
                
                # 更新小时统计
                hour_key = metrics.end_time.strftime("%Y-%m-%d %H")
                self.hourly_stats[hour_key]["cancelled"] += 1
    
    async def start_monitoring(self):
        """启动性能监控。"""
        if self.monitoring_task and not self.monitoring_task.done():
            return
        
        self.monitoring_enabled = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("性能监控已启动")
    
    async def stop_monitoring(self):
        """停止性能监控。"""
        self.monitoring_enabled = False
        
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("性能监控已停止")
    
    async def _monitoring_loop(self):
        """监控循环。"""
        while self.monitoring_enabled:
            try:
                # 收集系统指标
                system_metrics = await self._collect_system_metrics()
                self.system_metrics_history.append(system_metrics)
                
                # 发送监控事件
                await self.event_bus.emit("system_metrics_updated", {
                    "metrics": system_metrics
                })
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"监控循环错误: {e}")
                await asyncio.sleep(5.0)
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """收集系统性能指标。"""
        now = datetime.now()
        
        # 统计活跃任务
        active_tasks = len([m for m in self.task_metrics.values() if m.status == TaskStatus.RUNNING])
        queued_tasks = len([m for m in self.task_metrics.values() if m.status == TaskStatus.QUEUED])
        
        # 统计完成任务（最近1小时）
        one_hour_ago = now - timedelta(hours=1)
        recent_completed = [m for m in self.completed_metrics 
                          if m.end_time and m.end_time >= one_hour_ago and m.status == TaskStatus.COMPLETED]
        recent_failed = [m for m in self.completed_metrics 
                        if m.end_time and m.end_time >= one_hour_ago and m.status == TaskStatus.FAILED]
        
        completed_tasks = len(recent_completed)
        failed_tasks = len(recent_failed)
        
        # 计算平均执行时间
        if recent_completed:
            avg_execution_time = statistics.mean([m.execution_time for m in recent_completed if m.execution_time > 0])
        else:
            avg_execution_time = 0.0
        
        # 计算吞吐量（每分钟完成任务数）
        throughput = completed_tasks  # 1小时内完成的任务数，可以换算为每分钟
        
        # 计算错误率
        total_recent = completed_tasks + failed_tasks
        error_rate = (failed_tasks / total_recent * 100) if total_recent > 0 else 0.0
        
        return SystemMetrics(
            timestamp=now,
            active_tasks=active_tasks,
            queued_tasks=queued_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            average_execution_time=avg_execution_time,
            throughput=throughput,
            error_rate=error_rate
        )
    
    def get_current_status(self) -> Dict[str, Any]:
        """获取当前状态。
        
        Returns:
            当前状态信息
        """
        active_metrics = list(self.task_metrics.values())
        
        status_counts = defaultdict(int)
        for metrics in active_metrics:
            status_counts[metrics.status.value] += 1
        
        type_counts = defaultdict(int)
        for metrics in active_metrics:
            type_counts[metrics.task_type.value] += 1
        
        priority_counts = defaultdict(int)
        for metrics in active_metrics:
            priority_counts[metrics.priority.value] += 1
        
        return {
            "timestamp": datetime.now().isoformat(),
            "active_tasks": len(active_metrics),
            "completed_history": len(self.completed_metrics),
            "status_distribution": dict(status_counts),
            "type_distribution": dict(type_counts),
            "priority_distribution": dict(priority_counts)
        }
    
    def get_task_metrics(self, execution_id: str) -> Optional[TaskMetrics]:
        """获取指定任务的指标。
        
        Args:
            execution_id: 执行ID
            
        Returns:
            任务指标或None
        """
        # 先查找活跃任务
        if execution_id in self.task_metrics:
            return self.task_metrics[execution_id]
        
        # 再查找完成历史
        for metrics in self.completed_metrics:
            if metrics.task_id == execution_id:
                return metrics
        
        return None
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取性能摘要。
        
        Args:
            hours: 统计时间范围（小时）
            
        Returns:
            性能摘要
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # 过滤指定时间范围内的指标
        recent_metrics = [m for m in self.completed_metrics 
                         if m.end_time and m.end_time >= cutoff_time]
        
        if not recent_metrics:
            return {
                "period_hours": hours,
                "total_tasks": 0,
                "message": "指定时间范围内无任务数据"
            }
        
        # 统计各种状态的任务
        completed = [m for m in recent_metrics if m.status == TaskStatus.COMPLETED]
        failed = [m for m in recent_metrics if m.status == TaskStatus.FAILED]
        cancelled = [m for m in recent_metrics if m.status == TaskStatus.CANCELLED]
        
        # 计算执行时间统计
        execution_times = [m.execution_time for m in completed if m.execution_time > 0]
        
        if execution_times:
            avg_time = statistics.mean(execution_times)
            min_time = min(execution_times)
            max_time = max(execution_times)
            median_time = statistics.median(execution_times)
        else:
            avg_time = min_time = max_time = median_time = 0.0
        
        # 计算成功率
        total_finished = len(completed) + len(failed)
        success_rate = (len(completed) / total_finished * 100) if total_finished > 0 else 0.0
        
        # 任务类型分布
        type_stats = defaultdict(int)
        for metrics in recent_metrics:
            type_stats[metrics.task_type.value] += 1
        
        # 优先级分布
        priority_stats = defaultdict(int)
        for metrics in recent_metrics:
            priority_stats[metrics.priority.value] += 1
        
        return {
            "period_hours": hours,
            "total_tasks": len(recent_metrics),
            "completed_tasks": len(completed),
            "failed_tasks": len(failed),
            "cancelled_tasks": len(cancelled),
            "success_rate": round(success_rate, 2),
            "execution_time_stats": {
                "average": round(avg_time, 2),
                "minimum": round(min_time, 2),
                "maximum": round(max_time, 2),
                "median": round(median_time, 2)
            },
            "task_type_distribution": dict(type_stats),
            "priority_distribution": dict(priority_stats),
            "throughput_per_hour": round(len(completed) / hours, 2) if hours > 0 else 0.0
        }
    
    def generate_performance_report(self, start_time: datetime, end_time: datetime) -> PerformanceReport:
        """生成性能报告。
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            性能报告
        """
        report_id = f"report_{int(time.time())}"
        
        # 过滤时间范围内的指标
        period_metrics = [m for m in self.completed_metrics 
                         if m.end_time and start_time <= m.end_time <= end_time]
        
        if not period_metrics:
            # 返回空报告
            return PerformanceReport(
                report_id=report_id,
                start_time=start_time,
                end_time=end_time,
                total_tasks=0,
                completed_tasks=0,
                failed_tasks=0,
                cancelled_tasks=0,
                average_execution_time=0.0,
                min_execution_time=0.0,
                max_execution_time=0.0,
                throughput=0.0,
                error_rate=0.0,
                task_type_stats={},
                priority_stats={},
                hourly_stats=[],
                top_errors=[]
            )
        
        # 基本统计
        completed = [m for m in period_metrics if m.status == TaskStatus.COMPLETED]
        failed = [m for m in period_metrics if m.status == TaskStatus.FAILED]
        cancelled = [m for m in period_metrics if m.status == TaskStatus.CANCELLED]
        
        # 执行时间统计
        execution_times = [m.execution_time for m in completed if m.execution_time > 0]
        if execution_times:
            avg_time = statistics.mean(execution_times)
            min_time = min(execution_times)
            max_time = max(execution_times)
        else:
            avg_time = min_time = max_time = 0.0
        
        # 吞吐量计算
        period_hours = (end_time - start_time).total_seconds() / 3600
        throughput = len(completed) / period_hours if period_hours > 0 else 0.0
        
        # 错误率计算
        total_finished = len(completed) + len(failed)
        error_rate = (len(failed) / total_finished * 100) if total_finished > 0 else 0.0
        
        # 任务类型统计
        task_type_stats = {}
        for task_type in TaskType:
            type_metrics = [m for m in period_metrics if m.task_type == task_type]
            if type_metrics:
                type_completed = [m for m in type_metrics if m.status == TaskStatus.COMPLETED]
                type_failed = [m for m in type_metrics if m.status == TaskStatus.FAILED]
                type_times = [m.execution_time for m in type_completed if m.execution_time > 0]
                
                task_type_stats[task_type.value] = {
                    "total": len(type_metrics),
                    "completed": len(type_completed),
                    "failed": len(type_failed),
                    "success_rate": (len(type_completed) / len(type_metrics) * 100) if type_metrics else 0.0,
                    "average_time": statistics.mean(type_times) if type_times else 0.0
                }
        
        # 优先级统计
        priority_stats = {}
        for priority in TaskPriority:
            priority_metrics = [m for m in period_metrics if m.priority == priority]
            if priority_metrics:
                priority_completed = [m for m in priority_metrics if m.status == TaskStatus.COMPLETED]
                priority_failed = [m for m in priority_metrics if m.status == TaskStatus.FAILED]
                
                priority_stats[priority.value] = {
                    "total": len(priority_metrics),
                    "completed": len(priority_completed),
                    "failed": len(priority_failed),
                    "success_rate": (len(priority_completed) / len(priority_metrics) * 100) if priority_metrics else 0.0
                }
        
        # 小时统计
        hourly_stats = []
        current_hour = start_time.replace(minute=0, second=0, microsecond=0)
        while current_hour <= end_time:
            next_hour = current_hour + timedelta(hours=1)
            hour_metrics = [m for m in period_metrics 
                           if m.end_time and current_hour <= m.end_time < next_hour]
            
            hour_completed = [m for m in hour_metrics if m.status == TaskStatus.COMPLETED]
            hour_failed = [m for m in hour_metrics if m.status == TaskStatus.FAILED]
            
            hourly_stats.append({
                "hour": current_hour.strftime("%Y-%m-%d %H:00"),
                "total": len(hour_metrics),
                "completed": len(hour_completed),
                "failed": len(hour_failed)
            })
            
            current_hour = next_hour
        
        # 错误统计
        error_counts = defaultdict(int)
        for metrics in failed:
            if metrics.error_message:
                error_counts[metrics.error_message] += 1
        
        top_errors = [
            {"error": error, "count": count}
            for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        return PerformanceReport(
            report_id=report_id,
            start_time=start_time,
            end_time=end_time,
            total_tasks=len(period_metrics),
            completed_tasks=len(completed),
            failed_tasks=len(failed),
            cancelled_tasks=len(cancelled),
            average_execution_time=avg_time,
            min_execution_time=min_time,
            max_execution_time=max_time,
            throughput=throughput,
            error_rate=error_rate,
            task_type_stats=task_type_stats,
            priority_stats=priority_stats,
            hourly_stats=hourly_stats,
            top_errors=top_errors
        )
    
    def export_metrics(self, file_path: str, format: str = "json"):
        """导出指标数据。
        
        Args:
            file_path: 导出文件路径
            format: 导出格式（json或csv）
        """
        try:
            if format.lower() == "json":
                data = {
                    "active_metrics": [asdict(m) for m in self.task_metrics.values()],
                    "completed_metrics": [asdict(m) for m in self.completed_metrics],
                    "system_metrics": [asdict(m) for m in self.system_metrics_history],
                    "export_time": datetime.now().isoformat()
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            elif format.lower() == "csv":
                import csv
                
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    # 写入表头
                    writer.writerow([
                        'task_id', 'task_type', 'priority', 'status',
                        'start_time', 'end_time', 'execution_time',
                        'retry_count', 'error_message'
                    ])
                    
                    # 写入数据
                    all_metrics = list(self.task_metrics.values()) + list(self.completed_metrics)
                    for metrics in all_metrics:
                        writer.writerow([
                            metrics.task_id,
                            metrics.task_type.value,
                            metrics.priority.value,
                            metrics.status.value,
                            metrics.start_time.isoformat() if metrics.start_time else '',
                            metrics.end_time.isoformat() if metrics.end_time else '',
                            metrics.execution_time,
                            metrics.retry_count,
                            metrics.error_message or ''
                        ])
            
            else:
                raise ValueError(f"不支持的导出格式: {format}")
            
            self.logger.info(f"指标数据已导出到: {file_path}")
            
        except Exception as e:
            self.logger.error(f"导出指标数据失败: {e}")
            raise