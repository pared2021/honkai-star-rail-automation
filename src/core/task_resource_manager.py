# -*- coding: utf-8 -*-
"""
任务资源管理器 - 负责任务执行的资源限制和管理
"""

import asyncio
import psutil
import time
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger
from .dependency_injection import Injectable, inject
from .interfaces import IResourceManager, IConfigManager
from .types.resource_types import ResourceType, ResourceLimits, ResourceUsage

logger = get_logger(__name__)


class TaskResourceManager(Injectable, IResourceManager):
    """任务资源管理器 - 专门负责任务执行的资源限制和管理"""

    @inject
    def __init__(self, config_manager: IConfigManager, default_limits: Optional[ResourceLimits] = None):
        """初始化任务资源管理器

        Args:
            config_manager: 配置管理器
            default_limits: 默认资源限制
        """
        self._config_manager = config_manager
        self._default_limits = default_limits or ResourceLimits.from_config(config_manager)
        self._task_limits: Dict[str, ResourceLimits] = {}
        self._task_usage: Dict[str, ResourceUsage] = {}
        
        # 系统资源监控
        self._system_usage = ResourceUsage()
        self._monitoring_active = False
        self._monitoring_task = None
        self._monitoring_interval = self._get_config_value('task_resource_manager.monitoring_interval', 5)  # 监控间隔（秒）
        
        # 资源使用历史
        self._usage_history: List[ResourceUsage] = []
        self._max_history_size = self._get_config_value('task_resource_manager.max_history_size', 1000)
        
        # 资源警告阈值
        self._warning_thresholds = {
            ResourceType.CPU: self._get_config_value('task_resource_manager.warning_thresholds.cpu', 70.0),
            ResourceType.MEMORY: self._get_config_value('task_resource_manager.warning_thresholds.memory', 80.0),
            ResourceType.DISK: self._get_config_value('task_resource_manager.warning_thresholds.disk', 80.0),
            ResourceType.NETWORK: self._get_config_value('task_resource_manager.warning_thresholds.network', 80.0),
            ResourceType.CONCURRENT_TASKS: self._get_config_value('task_resource_manager.warning_thresholds.concurrent_tasks', 80.0),
        }
        
        # 统计信息
        self._stats = {
            "resource_checks": 0,
            "limit_violations": 0,
            "warnings_issued": 0,
            "tasks_throttled": 0,
        }
    
    def _get_config_value(self, key: str, default_value: Any) -> Any:
        """从配置管理器获取配置值
        
        Args:
            key: 配置键
            default_value: 默认值
            
        Returns:
            Any: 配置值
        """
        if self._config_manager:
            return self._config_manager.get(key, default_value)
        return default_value

    async def start_monitoring(self, interval: int = 5):
        """启动资源监控

        Args:
            interval: 监控间隔（秒）
        """
        if self._monitoring_active:
            logger.warning("资源监控已经在运行中")
            return

        self._monitoring_interval = interval
        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(self._monitor_resources())
        logger.info(f"资源监控已启动，监控间隔: {interval}秒")

    async def stop_monitoring(self):
        """停止资源监控"""
        if not self._monitoring_active:
            logger.warning("资源监控未在运行")
            return

        self._monitoring_active = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("资源监控已停止")

    async def _monitor_resources(self):
        """资源监控主循环"""
        while self._monitoring_active:
            try:
                # 更新系统资源使用情况
                await self._update_system_usage()
                
                # 检查资源限制
                await self._check_resource_limits()
                
                # 记录使用历史
                self._record_usage_history()
                
                # 清理过期数据
                self._cleanup_expired_data()
                
                await asyncio.sleep(self._monitoring_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"资源监控出错: {e}")
                await asyncio.sleep(self._monitoring_interval)

    async def _update_system_usage(self):
        """更新系统资源使用情况"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_mb = (memory.total - memory.available) / 1024 / 1024
            
            # 磁盘IO（简化版本）
            disk_io = psutil.disk_io_counters()
            disk_io_mb_per_sec = 0.0
            if hasattr(self, '_last_disk_io'):
                time_diff = time.time() - self._last_disk_check
                if time_diff > 0:
                    bytes_diff = (disk_io.read_bytes + disk_io.write_bytes) - self._last_disk_io
                    disk_io_mb_per_sec = (bytes_diff / 1024 / 1024) / time_diff
            
            self._last_disk_io = disk_io.read_bytes + disk_io.write_bytes
            self._last_disk_check = time.time()
            
            # 网络IO（简化版本）
            network_io = psutil.net_io_counters()
            network_io_mb_per_sec = 0.0
            if hasattr(self, '_last_network_io'):
                time_diff = time.time() - self._last_network_check
                if time_diff > 0:
                    bytes_diff = (network_io.bytes_sent + network_io.bytes_recv) - self._last_network_io
                    network_io_mb_per_sec = (bytes_diff / 1024 / 1024) / time_diff
            
            self._last_network_io = network_io.bytes_sent + network_io.bytes_recv
            self._last_network_check = time.time()
            
            # 更新系统使用情况
            self._system_usage = ResourceUsage(
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                disk_io_mb_per_sec=disk_io_mb_per_sec,
                network_mb_per_sec=network_io_mb_per_sec,
                concurrent_tasks=len(self._task_usage),
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"更新系统资源使用情况失败: {e}")

    async def _check_resource_limits(self):
        """检查资源限制"""
        self._stats["resource_checks"] += 1
        
        # 检查系统级别的资源限制
        limits = self._default_limits
        usage = self._system_usage
        
        violations = []
        warnings = []
        
        # 检查CPU
        if usage.cpu_percent > limits.max_cpu_percent:
            violations.append(f"CPU使用率超限: {usage.cpu_percent:.1f}% > {limits.max_cpu_percent}%")
        elif usage.cpu_percent > self._warning_thresholds[ResourceType.CPU]:
            warnings.append(f"CPU使用率警告: {usage.cpu_percent:.1f}%")
        
        # 检查内存
        if usage.memory_mb > limits.max_memory_mb:
            violations.append(f"内存使用超限: {usage.memory_mb:.1f}MB > {limits.max_memory_mb}MB")
        elif usage.memory_mb > limits.max_memory_mb * (self._warning_thresholds[ResourceType.MEMORY] / 100):
            warnings.append(f"内存使用警告: {usage.memory_mb:.1f}MB")
        
        # 检查磁盘IO
        if usage.disk_io_mb_per_sec > limits.max_disk_io_mb_per_sec:
            violations.append(f"磁盘IO超限: {usage.disk_io_mb_per_sec:.1f}MB/s > {limits.max_disk_io_mb_per_sec}MB/s")
        
        # 检查网络IO
        if usage.network_mb_per_sec > limits.max_network_mb_per_sec:
            violations.append(f"网络IO超限: {usage.network_mb_per_sec:.1f}MB/s > {limits.max_network_mb_per_sec}MB/s")
        
        # 检查并发任务数
        if usage.concurrent_tasks > limits.max_concurrent_tasks:
            violations.append(f"并发任务数超限: {usage.concurrent_tasks} > {limits.max_concurrent_tasks}")
        
        # 记录违规和警告
        if violations:
            self._stats["limit_violations"] += len(violations)
            for violation in violations:
                logger.warning(f"资源限制违规: {violation}")
        
        if warnings:
            self._stats["warnings_issued"] += len(warnings)
            for warning in warnings:
                logger.info(f"资源使用警告: {warning}")

    def _record_usage_history(self):
        """记录资源使用历史"""
        self._usage_history.append(self._system_usage)
        
        # 限制历史记录大小
        if len(self._usage_history) > self._max_history_size:
            self._usage_history = self._usage_history[-self._max_history_size:]

    def _cleanup_expired_data(self):
        """清理过期数据"""
        current_time = time.time()
        expiry_time = self._get_config_value('task_resource_manager.data_expiry_time', 3600)  # 默认1小时前的数据
        expired_threshold = current_time - expiry_time
        
        # 清理过期的任务使用数据
        expired_tasks = [
            task_id for task_id, usage in self._task_usage.items()
            if usage.timestamp < expired_threshold
        ]
        
        for task_id in expired_tasks:
            del self._task_usage[task_id]
            if task_id in self._task_limits:
                del self._task_limits[task_id]

    def set_task_limits(self, task_id: str, limits: ResourceLimits):
        """设置任务资源限制

        Args:
            task_id: 任务ID
            limits: 资源限制
        """
        self._task_limits[task_id] = limits
        logger.info(f"已设置任务 {task_id} 的资源限制")

    def get_task_limits(self, task_id: str) -> ResourceLimits:
        """获取任务资源限制

        Args:
            task_id: 任务ID

        Returns:
            ResourceLimits: 资源限制
        """
        return self._task_limits.get(task_id, self._default_limits)

    def update_task_usage(self, task_id: str, usage: ResourceUsage):
        """更新任务资源使用情况

        Args:
            task_id: 任务ID
            usage: 资源使用情况
        """
        self._task_usage[task_id] = usage

    def get_task_usage(self, task_id: str) -> Optional[ResourceUsage]:
        """获取任务资源使用情况

        Args:
            task_id: 任务ID

        Returns:
            Optional[ResourceUsage]: 资源使用情况
        """
        return self._task_usage.get(task_id)

    def get_system_usage(self) -> ResourceUsage:
        """获取系统资源使用情况

        Returns:
            ResourceUsage: 系统资源使用情况
        """
        return self._system_usage

    def check_resource_availability(self, required_resources: ResourceUsage) -> bool:
        """检查资源可用性

        Args:
            required_resources: 所需资源

        Returns:
            bool: 资源是否可用
        """
        current_usage = self._system_usage
        limits = self._default_limits
        
        # 检查CPU
        if current_usage.cpu_percent + required_resources.cpu_percent > limits.max_cpu_percent:
            return False
        
        # 检查内存
        if current_usage.memory_mb + required_resources.memory_mb > limits.max_memory_mb:
            return False
        
        # 检查磁盘IO
        if current_usage.disk_io_mb_per_sec + required_resources.disk_io_mb_per_sec > limits.max_disk_io_mb_per_sec:
            return False
        
        # 检查网络IO
        if current_usage.network_mb_per_sec + required_resources.network_mb_per_sec > limits.max_network_mb_per_sec:
            return False
        
        # 检查并发任务数
        if current_usage.concurrent_tasks + 1 > limits.max_concurrent_tasks:
            return False
        
        return True

    def can_execute_task(self, task_id: str) -> bool:
        """检查任务是否可以执行

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否可以执行
        """
        limits = self.get_task_limits(task_id)
        current_usage = self._system_usage
        
        # 检查并发任务数限制
        if current_usage.concurrent_tasks >= limits.max_concurrent_tasks:
            return False
        
        # 检查系统资源使用情况
        cpu_threshold = self._get_config_value('task_resource_manager.execution_threshold.cpu', 0.9)  # 默认90%阈值
        memory_threshold = self._get_config_value('task_resource_manager.execution_threshold.memory', 0.9)  # 默认90%阈值
        
        if current_usage.cpu_percent > limits.max_cpu_percent * cpu_threshold:
            return False
        
        if current_usage.memory_mb > limits.max_memory_mb * memory_threshold:
            return False
        
        return True

    def throttle_task(self, task_id: str, reason: str):
        """限制任务执行

        Args:
            task_id: 任务ID
            reason: 限制原因
        """
        self._stats["tasks_throttled"] += 1
        logger.warning(f"任务 {task_id} 被限制执行: {reason}")

    def get_resource_statistics(self) -> Dict[str, Any]:
        """获取资源统计信息

        Returns:
            Dict[str, Any]: 资源统计信息
        """
        return {
            "monitoring_active": self._monitoring_active,
            "monitoring_interval": self._monitoring_interval,
            "current_usage": self._system_usage.to_dict(),
            "default_limits": self._default_limits.to_dict(),
            "active_tasks": len(self._task_usage),
            "task_limits_count": len(self._task_limits),
            "usage_history_size": len(self._usage_history),
            "stats": dict(self._stats),
            "warning_thresholds": {
                resource_type.value: threshold
                for resource_type, threshold in self._warning_thresholds.items()
            }
        }

    def get_usage_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取资源使用历史

        Args:
            limit: 返回记录数限制

        Returns:
            List[Dict[str, Any]]: 资源使用历史
        """
        history = self._usage_history[-limit:] if limit > 0 else self._usage_history
        return [usage.to_dict() for usage in history]

    def set_warning_threshold(self, resource_type: ResourceType, threshold: float):
        """设置资源警告阈值

        Args:
            resource_type: 资源类型
            threshold: 警告阈值
        """
        self._warning_thresholds[resource_type] = threshold
        logger.info(f"已设置 {resource_type.value} 警告阈值为 {threshold}")

    def set_default_limits(self, limits: ResourceLimits):
        """设置默认资源限制

        Args:
            limits: 资源限制
        """
        self._default_limits = limits
        logger.info("已更新默认资源限制")

    def get_default_limits(self) -> ResourceLimits:
        """获取默认资源限制

        Returns:
            ResourceLimits: 默认资源限制
        """
        return self._default_limits

    def reset_statistics(self):
        """重置统计信息"""
        self._stats = {
            "resource_checks": 0,
            "limit_violations": 0,
            "warnings_issued": 0,
            "tasks_throttled": 0,
        }
        logger.info("资源管理器统计信息已重置")

    def clear_usage_history(self):
        """清空使用历史"""
        self._usage_history.clear()
        logger.info("资源使用历史已清空")

    def is_monitoring_active(self) -> bool:
        """检查监控是否活跃

        Returns:
            bool: 监控是否活跃
        """
        return self._monitoring_active

    def get_resource_pressure(self) -> Dict[str, float]:
        """获取资源压力指标

        Returns:
            Dict[str, float]: 资源压力指标（0-1之间）
        """
        usage = self._system_usage
        limits = self._default_limits
        
        return {
            "cpu_pressure": min(usage.cpu_percent / limits.max_cpu_percent, 1.0),
            "memory_pressure": min(usage.memory_mb / limits.max_memory_mb, 1.0),
            "disk_pressure": min(usage.disk_io_mb_per_sec / limits.max_disk_io_mb_per_sec, 1.0),
            "network_pressure": min(usage.network_mb_per_sec / limits.max_network_mb_per_sec, 1.0),
            "concurrency_pressure": min(usage.concurrent_tasks / limits.max_concurrent_tasks, 1.0),
        }

    def estimate_task_resource_requirements(self, task_config: Dict[str, Any]) -> ResourceUsage:
        """估算任务资源需求

        Args:
            task_config: 任务配置

        Returns:
            ResourceUsage: 估算的资源需求
        """
        # 基于任务类型和配置估算资源需求
        task_type = task_config.get("task_type", "default")
        
        # 默认资源需求
        base_requirements = {
            "system": ResourceUsage(
                cpu_percent=self._get_config_value('task_resource_manager.default_requirements.system.cpu_percent', 20.0),
                memory_mb=self._get_config_value('task_resource_manager.default_requirements.system.memory_mb', 256)
            ),
            "user": ResourceUsage(
                cpu_percent=self._get_config_value('task_resource_manager.default_requirements.user.cpu_percent', 10.0),
                memory_mb=self._get_config_value('task_resource_manager.default_requirements.user.memory_mb', 128)
            ),
            "background": ResourceUsage(
                cpu_percent=self._get_config_value('task_resource_manager.default_requirements.background.cpu_percent', 5.0),
                memory_mb=self._get_config_value('task_resource_manager.default_requirements.background.memory_mb', 64)
            ),
            "maintenance": ResourceUsage(
                cpu_percent=self._get_config_value('task_resource_manager.default_requirements.maintenance.cpu_percent', 15.0),
                memory_mb=self._get_config_value('task_resource_manager.default_requirements.maintenance.memory_mb', 192)
            ),
        }
        
        default_cpu = self._get_config_value('task_resource_manager.default_requirements.default.cpu_percent', 10.0)
        default_memory = self._get_config_value('task_resource_manager.default_requirements.default.memory_mb', 128)
        requirements = base_requirements.get(task_type, ResourceUsage(cpu_percent=default_cpu, memory_mb=default_memory))
        
        # 根据任务配置调整需求
        if "resource_requirements" in task_config:
            resource_config = task_config["resource_requirements"]
            if isinstance(resource_config, dict):
                requirements.cpu_percent = resource_config.get("cpu_percent", requirements.cpu_percent)
                requirements.memory_mb = resource_config.get("memory_mb", requirements.memory_mb)
                requirements.disk_io_mb_per_sec = resource_config.get("disk_io_mb_per_sec", requirements.disk_io_mb_per_sec)
                requirements.network_mb_per_sec = resource_config.get("network_mb_per_sec", requirements.network_mb_per_sec)
        
        return requirements