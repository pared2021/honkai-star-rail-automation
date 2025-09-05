# -*- coding: utf-8 -*-
"""
资源管理相关类型定义

独立的类型定义，避免循环依赖。
"""

import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class ResourceType(Enum):
    """资源类型"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    CONCURRENT_TASKS = "concurrent_tasks"


@dataclass
class ResourceLimits:
    """资源限制配置"""
    max_cpu_percent: float = 80.0  # 最大CPU使用率（%）
    max_memory_mb: int = 1024  # 最大内存使用（MB）
    max_disk_io_mb_per_sec: float = 100.0  # 最大磁盘IO（MB/s）
    max_network_mb_per_sec: float = 50.0  # 最大网络IO（MB/s）
    max_concurrent_tasks: int = 10  # 最大并发任务数
    max_task_duration: int = 3600  # 最大任务执行时间（秒）
    
    @classmethod
    def from_config(cls, config_manager=None) -> "ResourceLimits":
        """从配置管理器创建资源限制
        
        Args:
            config_manager: 配置管理器
            
        Returns:
            ResourceLimits: 资源限制实例
        """
        def get_config_value(key: str, default_value):
            if config_manager:
                return config_manager.get(key, default_value)
            return default_value
        
        return cls(
            max_cpu_percent=get_config_value('resource_limits.max_cpu_percent', 80.0),
            max_memory_mb=get_config_value('resource_limits.max_memory_mb', 1024),
            max_disk_io_mb_per_sec=get_config_value('resource_limits.max_disk_io_mb_per_sec', 100.0),
            max_network_mb_per_sec=get_config_value('resource_limits.max_network_mb_per_sec', 50.0),
            max_concurrent_tasks=get_config_value('resource_limits.max_concurrent_tasks', 10),
            max_task_duration=get_config_value('resource_limits.max_task_duration', 3600),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "max_cpu_percent": self.max_cpu_percent,
            "max_memory_mb": self.max_memory_mb,
            "max_disk_io_mb_per_sec": self.max_disk_io_mb_per_sec,
            "max_network_mb_per_sec": self.max_network_mb_per_sec,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "max_task_duration": self.max_task_duration,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceLimits":
        """从字典创建"""
        return cls(
            max_cpu_percent=data.get("max_cpu_percent", 80.0),
            max_memory_mb=data.get("max_memory_mb", 1024),
            max_disk_io_mb_per_sec=data.get("max_disk_io_mb_per_sec", 100.0),
            max_network_mb_per_sec=data.get("max_network_mb_per_sec", 50.0),
            max_concurrent_tasks=data.get("max_concurrent_tasks", 10),
            max_task_duration=data.get("max_task_duration", 3600),
        )


@dataclass
class ResourceUsage:
    """资源使用情况"""
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    disk_io_mb_per_sec: float = 0.0
    network_mb_per_sec: float = 0.0
    concurrent_tasks: int = 0
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "disk_io_mb_per_sec": self.disk_io_mb_per_sec,
            "network_mb_per_sec": self.network_mb_per_sec,
            "concurrent_tasks": self.concurrent_tasks,
            "timestamp": self.timestamp,
        }