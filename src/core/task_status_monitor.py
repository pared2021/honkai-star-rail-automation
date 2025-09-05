# -*- coding: utf-8 -*-
"""
任务状态监控器 - 负责任务状态的监控和回调处理
"""

import asyncio
import time
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

from ..entities.task import TaskStatus
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MonitorType(Enum):
    """监控类型"""
    STATUS_CHANGE = "status_change"
    HEALTH_CHECK = "health_check"
    TIMEOUT = "timeout"
    RESOURCE = "resource"


@dataclass
class StatusMonitor:
    """状态监控器配置"""
    monitor_id: str
    task_id: str
    monitor_type: MonitorType
    callback: Callable
    interval: int = 30  # 监控间隔（秒）
    timeout: Optional[int] = None  # 超时时间（秒）
    enabled: bool = True
    created_at: float = None
    last_check: float = None
    check_count: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.last_check is None:
            self.last_check = time.time()


class TaskStatusMonitor:
    """任务状态监控器 - 专门负责任务状态的监控和回调处理"""

    def __init__(self, config_manager=None):
        """初始化任务状态监控器
        
        Args:
            config_manager: 配置管理器
        """
        self.config_manager = config_manager
        self._monitoring_active = False
        self._monitoring_task = None
        self._monitoring_interval = self._get_config_value('task_status_monitor.monitoring_interval', 30)  # 默认监控间隔（秒）
        
        # 状态监控器
        self._status_monitors: Dict[str, StatusMonitor] = {}
        
        # 任务健康状态
        self._task_health: Dict[str, Dict[str, Any]] = {}
        
        # 监控统计
        self._monitor_stats = {
            "total_checks": 0,
            "health_checks": 0,
            "status_changes": 0,
            "timeouts": 0,
            "errors": 0,
        }
        
        # 超时任务集合
        self._timeout_tasks: Set[str] = set()
    
    def _get_config_value(self, key: str, default_value):
        """获取配置值"""
        if self.config_manager:
            return self.config_manager.get(key, default_value)
        return default_value

    async def start_status_monitoring(self, interval: int = 30):
        """启动状态监控

        Args:
            interval: 监控间隔（秒）
        """
        if self._monitoring_active:
            logger.warning("状态监控已经在运行中")
            return

        self._monitoring_interval = interval
        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(self._monitor_task_status())
        logger.info(f"任务状态监控已启动，监控间隔: {interval}秒")

    async def stop_status_monitoring(self):
        """停止状态监控"""
        if not self._monitoring_active:
            logger.warning("状态监控未在运行")
            return

        self._monitoring_active = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("任务状态监控已停止")

    async def _monitor_task_status(self):
        """任务状态监控主循环"""
        while self._monitoring_active:
            try:
                current_time = time.time()
                
                # 执行所有启用的监控器
                for monitor in list(self._status_monitors.values()):
                    if not monitor.enabled:
                        continue
                        
                    # 检查是否到了监控时间
                    if current_time - monitor.last_check >= monitor.interval:
                        await self._execute_monitor(monitor)
                        monitor.last_check = current_time
                        monitor.check_count += 1
                
                # 清理已完成的监控器
                await self._cleanup_completed_monitors()
                
                # 检查超时任务
                await self._check_timeout_tasks()
                
                await asyncio.sleep(self._monitoring_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"状态监控出错: {e}")
                self._monitor_stats["errors"] += 1
                await asyncio.sleep(self._monitoring_interval)

    async def _execute_monitor(self, monitor: StatusMonitor):
        """执行单个监控器

        Args:
            monitor: 监控器配置
        """
        try:
            self._monitor_stats["total_checks"] += 1
            
            if monitor.monitor_type == MonitorType.HEALTH_CHECK:
                await self._execute_health_check(monitor)
            elif monitor.monitor_type == MonitorType.STATUS_CHANGE:
                await self._execute_status_check(monitor)
            elif monitor.monitor_type == MonitorType.TIMEOUT:
                await self._execute_timeout_check(monitor)
            elif monitor.monitor_type == MonitorType.RESOURCE:
                await self._execute_resource_check(monitor)
                
        except Exception as e:
            logger.error(f"执行监控器 {monitor.monitor_id} 失败: {e}")
            self._monitor_stats["errors"] += 1

    async def _execute_health_check(self, monitor: StatusMonitor):
        """执行健康检查

        Args:
            monitor: 监控器配置
        """
        task_id = monitor.task_id
        
        try:
            # 获取任务当前状态
            # task = await self._db_manager.get_task(task_id)
            # 暂时模拟任务状态
            task = {"task_id": task_id, "status": "running"}
            
            if not task:
                logger.warning(f"任务 {task_id} 不存在，移除监控器")
                await self._remove_monitor(monitor.monitor_id)
                return
            
            # 检查任务健康状态
            health_info = await self._check_task_health(task)
            
            # 更新健康状态
            self._task_health[task_id] = health_info
            
            # 触发回调
            if monitor.callback:
                await self._trigger_callback(monitor.callback, {
                    "task_id": task_id,
                    "monitor_type": "health_check",
                    "health_info": health_info,
                    "timestamp": time.time()
                })
            
            self._monitor_stats["health_checks"] += 1
            
        except Exception as e:
            logger.error(f"健康检查失败 {task_id}: {e}")

    async def _execute_status_check(self, monitor: StatusMonitor):
        """执行状态变化检查

        Args:
            monitor: 监控器配置
        """
        task_id = monitor.task_id
        
        try:
            # 获取任务当前状态
            # task = await self._db_manager.get_task(task_id)
            # 暂时模拟任务状态
            task = {"task_id": task_id, "status": "running"}
            
            if not task:
                logger.warning(f"任务 {task_id} 不存在，移除监控器")
                await self._remove_monitor(monitor.monitor_id)
                return
            
            current_status = task.get("status")
            
            # 检查状态是否发生变化
            last_status = self._task_health.get(task_id, {}).get("last_status")
            
            if last_status and last_status != current_status:
                # 状态发生变化，触发回调
                if monitor.callback:
                    await self._trigger_callback(monitor.callback, {
                        "task_id": task_id,
                        "monitor_type": "status_change",
                        "old_status": last_status,
                        "new_status": current_status,
                        "timestamp": time.time()
                    })
                
                self._monitor_stats["status_changes"] += 1
                logger.info(f"任务 {task_id} 状态变化: {last_status} -> {current_status}")
            
            # 更新最后状态
            if task_id not in self._task_health:
                self._task_health[task_id] = {}
            self._task_health[task_id]["last_status"] = current_status
            
        except Exception as e:
            logger.error(f"状态检查失败 {task_id}: {e}")

    async def _execute_timeout_check(self, monitor: StatusMonitor):
        """执行超时检查

        Args:
            monitor: 监控器配置
        """
        task_id = monitor.task_id
        
        try:
            # 检查任务是否超时
            if monitor.timeout:
                current_time = time.time()
                if current_time - monitor.created_at > monitor.timeout:
                    # 任务超时
                    self._timeout_tasks.add(task_id)
                    
                    # 触发回调
                    if monitor.callback:
                        await self._trigger_callback(monitor.callback, {
                            "task_id": task_id,
                            "monitor_type": "timeout",
                            "timeout_duration": monitor.timeout,
                            "actual_duration": current_time - monitor.created_at,
                            "timestamp": current_time
                        })
                    
                    self._monitor_stats["timeouts"] += 1
                    logger.warning(f"任务 {task_id} 执行超时")
                    
                    # 移除超时监控器
                    await self._remove_monitor(monitor.monitor_id)
            
        except Exception as e:
            logger.error(f"超时检查失败 {task_id}: {e}")

    async def _execute_resource_check(self, monitor: StatusMonitor):
        """执行资源检查

        Args:
            monitor: 监控器配置
        """
        task_id = monitor.task_id
        
        try:
            # 获取任务资源使用情况
            resource_info = await self._get_task_resource_usage(task_id)
            
            # 触发回调
            if monitor.callback:
                await self._trigger_callback(monitor.callback, {
                    "task_id": task_id,
                    "monitor_type": "resource",
                    "resource_info": resource_info,
                    "timestamp": time.time()
                })
            
        except Exception as e:
            logger.error(f"资源检查失败 {task_id}: {e}")

    async def _check_task_health(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """检查任务健康状态

        Args:
            task: 任务信息

        Returns:
            Dict[str, Any]: 健康状态信息
        """
        task_id = task["task_id"]
        status = task.get("status")
        
        health_info = {
            "task_id": task_id,
            "status": status,
            "is_healthy": True,
            "issues": [],
            "last_check": time.time(),
        }
        
        # 检查任务状态
        if status in ["failed", "error"]:
            health_info["is_healthy"] = False
            health_info["issues"].append(f"任务状态异常: {status}")
        
        # 检查任务运行时间
        started_at = task.get("started_at")
        if started_at and status == "running":
            if isinstance(started_at, str):
                from datetime import datetime
                started_timestamp = datetime.fromisoformat(started_at).timestamp()
            else:
                started_timestamp = (
                    started_at.timestamp()
                    if hasattr(started_at, "timestamp")
                    else started_at
                )
            
            running_time = time.time() - started_timestamp
            health_info["running_time"] = running_time
            
            # 检查是否运行时间过长
            max_running_time = self._get_config_value('task_status_monitor.max_running_time', 3600)  # 默认1小时
            if running_time > max_running_time:
                health_info["issues"].append(f"任务运行时间过长: {running_time:.1f}秒")
        
        # 检查重试次数
        retry_count = task.get("retry_count", 0)
        max_retry_count = self._get_config_value('task_status_monitor.max_retry_count', 3)
        if retry_count > max_retry_count:
            health_info["is_healthy"] = False
            health_info["issues"].append(f"重试次数过多: {retry_count}")
        
        health_info["retry_count"] = retry_count
        
        return health_info

    async def _get_task_resource_usage(self, task_id: str) -> Dict[str, Any]:
        """获取任务资源使用情况

        Args:
            task_id: 任务ID

        Returns:
            Dict[str, Any]: 资源使用信息
        """
        # 这里应该实现实际的资源监控逻辑
        # 暂时返回模拟数据
        return {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "disk_usage": 0.0,
            "network_usage": 0.0,
            "timestamp": time.time()
        }

    async def _trigger_callback(self, callback: Callable, data: Dict[str, Any]):
        """触发监控回调

        Args:
            callback: 回调函数
            data: 回调数据
        """
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(data)
            else:
                callback(data)
        except Exception as e:
            logger.error(f"触发监控回调失败: {e}")

    async def _cleanup_completed_monitors(self):
        """清理已完成任务的监控器"""
        completed_monitors = []
        
        for monitor_id, monitor in self._status_monitors.items():
            task_id = monitor.task_id
            
            try:
                # 检查任务是否已完成
                # task = await self._db_manager.get_task(task_id)
                # 暂时模拟检查
                task = {"task_id": task_id, "status": "running"}
                
                if not task or task.get("status") in ["completed", "failed", "cancelled"]:
                    completed_monitors.append(monitor_id)
                    
            except Exception as e:
                logger.error(f"检查任务状态失败 {task_id}: {e}")
        
        # 移除已完成的监控器
        for monitor_id in completed_monitors:
            await self._remove_monitor(monitor_id)

    async def _check_timeout_tasks(self):
        """检查超时任务"""
        current_time = time.time()
        
        for monitor in list(self._status_monitors.values()):
            if monitor.monitor_type == MonitorType.TIMEOUT and monitor.timeout:
                if current_time - monitor.created_at > monitor.timeout:
                    task_id = monitor.task_id
                    if task_id not in self._timeout_tasks:
                        self._timeout_tasks.add(task_id)
                        logger.warning(f"检测到超时任务: {task_id}")

    def add_status_monitor(
        self,
        task_id: str,
        monitor_type: MonitorType,
        callback: Callable,
        interval: int = 30,
        timeout: Optional[int] = None
    ) -> str:
        """添加状态监控器

        Args:
            task_id: 任务ID
            monitor_type: 监控类型
            callback: 回调函数
            interval: 监控间隔（秒）
            timeout: 超时时间（秒）

        Returns:
            str: 监控器ID
        """
        import uuid
        monitor_id = str(uuid.uuid4())
        
        monitor = StatusMonitor(
            monitor_id=monitor_id,
            task_id=task_id,
            monitor_type=monitor_type,
            callback=callback,
            interval=interval,
            timeout=timeout
        )
        
        self._status_monitors[monitor_id] = monitor
        logger.info(f"已添加状态监控器: {monitor_id} for task {task_id}")
        
        return monitor_id

    async def _remove_monitor(self, monitor_id: str):
        """移除监控器

        Args:
            monitor_id: 监控器ID
        """
        if monitor_id in self._status_monitors:
            monitor = self._status_monitors[monitor_id]
            del self._status_monitors[monitor_id]
            logger.info(f"已移除状态监控器: {monitor_id} for task {monitor.task_id}")

    def remove_status_monitor(self, monitor_id: str):
        """移除状态监控器

        Args:
            monitor_id: 监控器ID
        """
        asyncio.create_task(self._remove_monitor(monitor_id))

    def get_task_health(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务健康状态

        Args:
            task_id: 任务ID

        Returns:
            Optional[Dict[str, Any]]: 健康状态信息
        """
        return self._task_health.get(task_id)

    def get_all_task_health(self) -> Dict[str, Dict[str, Any]]:
        """获取所有任务健康状态

        Returns:
            Dict[str, Dict[str, Any]]: 所有任务健康状态
        """
        return dict(self._task_health)

    def get_timeout_tasks(self) -> Set[str]:
        """获取超时任务列表

        Returns:
            Set[str]: 超时任务ID集合
        """
        return set(self._timeout_tasks)

    def clear_timeout_task(self, task_id: str):
        """清除超时任务标记

        Args:
            task_id: 任务ID
        """
        self._timeout_tasks.discard(task_id)
        logger.info(f"已清除任务 {task_id} 的超时标记")

    async def get_monitoring_status(self) -> Dict[str, Any]:
        """获取监控状态信息

        Returns:
            Dict[str, Any]: 监控状态
        """
        return {
            "monitoring_active": self._monitoring_active,
            "monitoring_interval": self._monitoring_interval,
            "active_monitors": len(self._status_monitors),
            "monitored_tasks": len(self._task_health),
            "timeout_tasks": len(self._timeout_tasks),
            "monitor_stats": dict(self._monitor_stats),
            "monitor_types": {
                monitor_type.value: len([
                    m for m in self._status_monitors.values() 
                    if m.monitor_type == monitor_type
                ])
                for monitor_type in MonitorType
            }
        }

    def reset_monitor_stats(self):
        """重置监控统计信息"""
        self._monitor_stats = {
            "total_checks": 0,
            "health_checks": 0,
            "status_changes": 0,
            "timeouts": 0,
            "errors": 0,
        }
        logger.info("监控统计信息已重置")

    def is_monitoring_active(self) -> bool:
        """检查监控是否活跃

        Returns:
            bool: 监控是否活跃
        """
        return self._monitoring_active

    def get_monitor_count(self) -> int:
        """获取监控器数量

        Returns:
            int: 监控器数量
        """
        return len(self._status_monitors)

    def get_monitors_for_task(self, task_id: str) -> List[StatusMonitor]:
        """获取指定任务的所有监控器

        Args:
            task_id: 任务ID

        Returns:
            List[StatusMonitor]: 监控器列表
        """
        return [
            monitor for monitor in self._status_monitors.values()
            if monitor.task_id == task_id
        ]

    def enable_monitor(self, monitor_id: str):
        """启用监控器

        Args:
            monitor_id: 监控器ID
        """
        if monitor_id in self._status_monitors:
            self._status_monitors[monitor_id].enabled = True
            logger.info(f"已启用监控器: {monitor_id}")

    def disable_monitor(self, monitor_id: str):
        """禁用监控器

        Args:
            monitor_id: 监控器ID
        """
        if monitor_id in self._status_monitors:
            self._status_monitors[monitor_id].enabled = False
            logger.info(f"已禁用监控器: {monitor_id}")