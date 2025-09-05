# -*- coding: utf-8 -*-
"""任务监控管理器

专门负责任务监控相关功能，包括：
- 任务健康检查
- 超时监控
- 状态变化监控
- 性能监控
- 异常检测
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Set
from collections import defaultdict, deque
from enum import Enum
from dataclasses import dataclass
from loguru import logger

from src.core.interfaces import ITaskMonitor, IConfigManager
from src.core.dependency_injection import Injectable, inject
from src.models.task_models import TaskStatus
from src.exceptions import TaskMonitoringError


class HealthStatus(Enum):
    """健康状态"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class TaskMonitorInfo:
    """任务监控信息"""
    task_id: str
    status: TaskStatus
    health_status: HealthStatus
    start_time: Optional[datetime]
    last_heartbeat: Optional[datetime]
    timeout_at: Optional[datetime]
    warning_count: int
    error_count: int
    metadata: Dict[str, Any]


@dataclass
class MonitoringStats:
    """监控统计信息"""
    total_monitored: int
    healthy_count: int
    warning_count: int
    critical_count: int
    timeout_count: int
    avg_response_time: float
    uptime_percentage: float


class TaskMonitor(Injectable, ITaskMonitor):
    """任务监控管理器
    
    提供任务监控功能：
    - 健康状态检查
    - 超时监控
    - 状态变化监控
    - 性能指标收集
    - 异常检测和告警
    """
    
    def __init__(
        self,
        config_manager: IConfigManager,
        default_timeout: Optional[timedelta] = None,
        health_check_interval: Optional[timedelta] = None,
        max_warning_count: Optional[int] = None
    ):
        """初始化任务监控器
        
        Args:
            config_manager: 配置管理器
            default_timeout: 默认超时时间
            health_check_interval: 健康检查间隔
            max_warning_count: 最大警告次数
        """
        super().__init__()
        self._config_manager = config_manager
        self._default_timeout = default_timeout or timedelta(hours=config_manager.get('monitor.default_timeout_hours', 1))
        self._health_check_interval = health_check_interval or timedelta(minutes=config_manager.get('monitor.health_check_interval_minutes', 5))
        self._max_warning_count = max_warning_count or config_manager.get('monitor.max_warning_count', 3)
        self._is_monitoring = False
        
        # 监控数据
        self._monitored_tasks: Dict[str, TaskMonitorInfo] = {}
        self._task_timeouts: Dict[str, timedelta] = {}
        
        # 回调函数
        self._status_change_callbacks: List[Callable] = []
        self._health_check_callbacks: List[Callable] = []
        
        # 监控统计
        self._stats = MonitoringStats(
            total_monitored=0,
            healthy_count=0,
            warning_count=0,
            critical_count=0,
            timeout_count=0,
            avg_response_time=0.0,
            uptime_percentage=100.0
        )
        
        # 性能数据
        max_records = config_manager.get('monitor.max_performance_records', 1000)
        self._response_times: deque = deque(maxlen=max_records)
        self._uptime_records: deque = deque(maxlen=max_records)
        
        # 监控任务
        self._monitor_task: Optional[asyncio.Task] = None
        
        logger.info(f"任务监控器初始化完成，默认超时: {default_timeout}")
    
    async def start_monitoring(self) -> bool:
        """启动监控
        
        Returns:
            是否启动成功
        """
        try:
            if self._is_monitoring:
                logger.warning("监控器已在运行")
                return True
            
            self._is_monitoring = True
            self._monitor_task = asyncio.create_task(self._monitoring_loop())
            
            logger.info("任务监控器已启动")
            return True
            
        except Exception as e:
            logger.error(f"启动监控器失败: {e}")
            self._is_monitoring = False
            return False
    
    async def stop_monitoring(self) -> bool:
        """停止监控
        
        Returns:
            是否停止成功
        """
        try:
            if not self._is_monitoring:
                logger.warning("监控器未在运行")
                return True
            
            self._is_monitoring = False
            
            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
                self._monitor_task = None
            
            logger.info("任务监控器已停止")
            return True
            
        except Exception as e:
            logger.error(f"停止监控器失败: {e}")
            return False
    
    async def add_task_monitoring(
        self,
        task_id: str,
        timeout: Optional[timedelta] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """添加任务监控
        
        Args:
            task_id: 任务ID
            timeout: 超时时间
            metadata: 元数据
            
        Returns:
            是否添加成功
        """
        try:
            if task_id in self._monitored_tasks:
                logger.warning(f"任务已在监控中: {task_id}")
                return False
            
            # 设置超时时间
            task_timeout = timeout or self._default_timeout
            self._task_timeouts[task_id] = task_timeout
            
            # 创建监控信息
            monitor_info = TaskMonitorInfo(
                task_id=task_id,
                status=TaskStatus.PENDING,
                health_status=HealthStatus.UNKNOWN,
                start_time=datetime.now(),
                last_heartbeat=datetime.now(),
                timeout_at=datetime.now() + task_timeout,
                warning_count=0,
                error_count=0,
                metadata=metadata or {}
            )
            
            self._monitored_tasks[task_id] = monitor_info
            self._stats.total_monitored += 1
            
            logger.info(f"添加任务监控: {task_id} - 超时: {task_timeout}")
            return True
            
        except Exception as e:
            logger.error(f"添加任务监控失败: {task_id} - {e}")
            return False
    
    async def remove_task_monitoring(self, task_id: str) -> bool:
        """移除任务监控
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否移除成功
        """
        try:
            if task_id not in self._monitored_tasks:
                logger.warning(f"任务未在监控中: {task_id}")
                return False
            
            # 移除监控数据
            del self._monitored_tasks[task_id]
            self._task_timeouts.pop(task_id, None)
            
            logger.info(f"移除任务监控: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"移除任务监控失败: {task_id} - {e}")
            return False
    
    async def check_task_health(self, task_id: str) -> HealthStatus:
        """检查任务健康状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            健康状态
        """
        try:
            if task_id not in self._monitored_tasks:
                return HealthStatus.UNKNOWN
            
            monitor_info = self._monitored_tasks[task_id]
            now = datetime.now()
            
            # 检查超时
            if monitor_info.timeout_at and now > monitor_info.timeout_at:
                monitor_info.health_status = HealthStatus.CRITICAL
                monitor_info.error_count += 1
                return HealthStatus.CRITICAL
            
            # 检查心跳
            if monitor_info.last_heartbeat:
                heartbeat_age = now - monitor_info.last_heartbeat
                heartbeat_threshold_multiplier = self._config_manager.get('monitor.heartbeat_threshold_multiplier', 2)
                if heartbeat_age > self._health_check_interval * heartbeat_threshold_multiplier:
                    monitor_info.health_status = HealthStatus.WARNING
                    monitor_info.warning_count += 1
                    return HealthStatus.WARNING
            
            # 检查错误次数
            if monitor_info.error_count > 0:
                monitor_info.health_status = HealthStatus.WARNING
                return HealthStatus.WARNING
            
            # 检查警告次数
            if monitor_info.warning_count >= self._max_warning_count:
                monitor_info.health_status = HealthStatus.CRITICAL
                return HealthStatus.CRITICAL
            
            monitor_info.health_status = HealthStatus.HEALTHY
            return HealthStatus.HEALTHY
            
        except Exception as e:
            logger.error(f"检查任务健康状态失败: {task_id} - {e}")
            return HealthStatus.UNKNOWN
    
    async def get_timeout_tasks(self) -> List[str]:
        """获取超时任务列表
        
        Returns:
            超时任务ID列表
        """
        timeout_tasks = []
        now = datetime.now()
        
        for task_id, monitor_info in self._monitored_tasks.items():
            if monitor_info.timeout_at and now > monitor_info.timeout_at:
                timeout_tasks.append(task_id)
        
        return timeout_tasks
    
    async def set_global_timeout(self, timeout: timedelta) -> bool:
        """设置全局超时时间
        
        Args:
            timeout: 超时时间
            
        Returns:
            是否设置成功
        """
        try:
            self._default_timeout = timeout
            logger.info(f"全局超时时间已更新: {timeout}")
            return True
        except Exception as e:
            logger.error(f"设置全局超时时间失败: {e}")
            return False
    
    async def set_task_timeout(self, task_id: str, timeout: timedelta) -> bool:
        """设置任务超时时间
        
        Args:
            task_id: 任务ID
            timeout: 超时时间
            
        Returns:
            是否设置成功
        """
        try:
            if task_id not in self._monitored_tasks:
                logger.warning(f"任务未在监控中: {task_id}")
                return False
            
            self._task_timeouts[task_id] = timeout
            
            # 更新超时时间
            monitor_info = self._monitored_tasks[task_id]
            if monitor_info.start_time:
                monitor_info.timeout_at = monitor_info.start_time + timeout
            
            logger.info(f"任务超时时间已更新: {task_id} - {timeout}")
            return True
            
        except Exception as e:
            logger.error(f"设置任务超时时间失败: {task_id} - {e}")
            return False
    
    async def get_monitoring_statistics(self) -> MonitoringStats:
        """获取监控统计信息
        
        Returns:
            监控统计信息
        """
        # 更新统计信息
        await self._update_statistics()
        return self._stats
    
    async def reset_statistics(self) -> bool:
        """重置统计信息
        
        Returns:
            是否重置成功
        """
        try:
            self._stats = MonitoringStats(
                total_monitored=len(self._monitored_tasks),
                healthy_count=0,
                warning_count=0,
                critical_count=0,
                timeout_count=0,
                avg_response_time=0.0,
                uptime_percentage=100.0
            )
            
            self._response_times.clear()
            self._uptime_records.clear()
            
            # 重置任务计数器
            for monitor_info in self._monitored_tasks.values():
                monitor_info.warning_count = 0
                monitor_info.error_count = 0
            
            logger.info("监控统计信息已重置")
            return True
            
        except Exception as e:
            logger.error(f"重置统计信息失败: {e}")
            return False
    
    async def add_status_change_callback(self, callback: Callable) -> bool:
        """添加状态变化回调
        
        Args:
            callback: 回调函数
            
        Returns:
            是否添加成功
        """
        try:
            if callback not in self._status_change_callbacks:
                self._status_change_callbacks.append(callback)
            return True
        except Exception as e:
            logger.error(f"添加状态变化回调失败: {e}")
            return False
    
    async def remove_status_change_callback(self, callback: Callable) -> bool:
        """移除状态变化回调
        
        Args:
            callback: 回调函数
            
        Returns:
            是否移除成功
        """
        try:
            if callback in self._status_change_callbacks:
                self._status_change_callbacks.remove(callback)
            return True
        except Exception as e:
            logger.error(f"移除状态变化回调失败: {e}")
            return False
    
    async def add_health_check_callback(self, callback: Callable) -> bool:
        """添加健康检查回调
        
        Args:
            callback: 回调函数
            
        Returns:
            是否添加成功
        """
        try:
            if callback not in self._health_check_callbacks:
                self._health_check_callbacks.append(callback)
            return True
        except Exception as e:
            logger.error(f"添加健康检查回调失败: {e}")
            return False
    
    async def remove_health_check_callback(self, callback: Callable) -> bool:
        """移除健康检查回调
        
        Args:
            callback: 回调函数
            
        Returns:
            是否移除成功
        """
        try:
            if callback in self._health_check_callbacks:
                self._health_check_callbacks.remove(callback)
            return True
        except Exception as e:
            logger.error(f"移除健康检查回调失败: {e}")
            return False
    
    async def force_health_check(self, task_id: Optional[str] = None) -> Dict[str, HealthStatus]:
        """强制执行健康检查
        
        Args:
            task_id: 任务ID，为None时检查所有任务
            
        Returns:
            健康检查结果
        """
        results = {}
        
        if task_id:
            if task_id in self._monitored_tasks:
                results[task_id] = await self.check_task_health(task_id)
        else:
            for tid in self._monitored_tasks.keys():
                results[tid] = await self.check_task_health(tid)
        
        return results
    
    async def get_task_monitoring_info(self, task_id: str) -> Optional[TaskMonitorInfo]:
        """获取任务监控信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            监控信息
        """
        return self._monitored_tasks.get(task_id)
    
    # 私有方法
    
    async def _monitoring_loop(self):
        """监控主循环"""
        logger.info("监控器主循环开始")
        
        while self._is_monitoring:
            try:
                await self._perform_health_checks()
                await self._check_timeouts()
                await self._update_statistics()
                await asyncio.sleep(self._health_check_interval.total_seconds())
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                error_wait_time = self._config_manager.get('monitor.error_wait_time', 30)
                await asyncio.sleep(error_wait_time)  # 错误后等待
        
        logger.info("监控器主循环结束")
    
    async def _perform_health_checks(self):
        """执行健康检查"""
        for task_id in list(self._monitored_tasks.keys()):
            try:
                start_time = datetime.now()
                health_status = await self.check_task_health(task_id)
                response_time = (datetime.now() - start_time).total_seconds()
                
                # 记录响应时间
                self._response_times.append(response_time)
                
                # 调用健康检查回调
                for callback in self._health_check_callbacks:
                    try:
                        await callback(task_id, health_status)
                    except Exception as e:
                        logger.error(f"健康检查回调失败: {callback} - {e}")
                
            except Exception as e:
                logger.error(f"健康检查失败: {task_id} - {e}")
    
    async def _check_timeouts(self):
        """检查超时任务"""
        timeout_tasks = await self.get_timeout_tasks()
        
        for task_id in timeout_tasks:
            try:
                monitor_info = self._monitored_tasks[task_id]
                old_status = monitor_info.health_status
                monitor_info.health_status = HealthStatus.CRITICAL
                
                # 调用状态变化回调
                if old_status != HealthStatus.CRITICAL:
                    for callback in self._status_change_callbacks:
                        try:
                            await callback(task_id, old_status, HealthStatus.CRITICAL)
                        except Exception as e:
                            logger.error(f"状态变化回调失败: {callback} - {e}")
                
                self._stats.timeout_count += 1
                logger.warning(f"任务超时: {task_id}")
                
            except Exception as e:
                logger.error(f"处理超时任务失败: {task_id} - {e}")
    
    async def _update_statistics(self):
        """更新统计信息"""
        try:
            total = len(self._monitored_tasks)
            if total == 0:
                return
            
            healthy_count = 0
            warning_count = 0
            critical_count = 0
            
            for monitor_info in self._monitored_tasks.values():
                if monitor_info.health_status == HealthStatus.HEALTHY:
                    healthy_count += 1
                elif monitor_info.health_status == HealthStatus.WARNING:
                    warning_count += 1
                elif monitor_info.health_status == HealthStatus.CRITICAL:
                    critical_count += 1
            
            # 更新统计信息
            self._stats.total_monitored = total
            self._stats.healthy_count = healthy_count
            self._stats.warning_count = warning_count
            self._stats.critical_count = critical_count
            
            # 计算平均响应时间
            if self._response_times:
                self._stats.avg_response_time = sum(self._response_times) / len(self._response_times)
            
            # 计算正常运行时间百分比
            if total > 0:
                self._stats.uptime_percentage = (healthy_count / total) * 100
            
        except Exception as e:
            logger.error(f"更新统计信息失败: {e}")
    
    async def update_task_heartbeat(self, task_id: str) -> bool:
        """更新任务心跳
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否更新成功
        """
        try:
            if task_id in self._monitored_tasks:
                self._monitored_tasks[task_id].last_heartbeat = datetime.now()
                return True
            return False
        except Exception as e:
            logger.error(f"更新任务心跳失败: {task_id} - {e}")
            return False
    
    async def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            
        Returns:
            是否更新成功
        """
        try:
            if task_id in self._monitored_tasks:
                old_status = self._monitored_tasks[task_id].status
                self._monitored_tasks[task_id].status = status
                
                # 调用状态变化回调
                for callback in self._status_change_callbacks:
                    try:
                        await callback(task_id, old_status, status)
                    except Exception as e:
                        logger.error(f"状态变化回调失败: {callback} - {e}")
                
                return True
            return False
        except Exception as e:
            logger.error(f"更新任务状态失败: {task_id} - {e}")
            return False