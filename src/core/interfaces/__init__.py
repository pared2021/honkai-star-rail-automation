"""核心组件接口定义

定义系统核心组件的统一接口抽象层。
"""

from .task_manager_interface import ITaskManager
from .cache_manager_interface import ICacheManager
from .scheduler_interface import ITaskScheduler
from .monitor_interface import ITaskMonitor
from .resource_manager_interface import IResourceManager
from .database_interface import IDatabaseManager
from .executor_interface import ITaskExecutor, ExecutionStatus, ExecutionResult
from .event_interface import (
    IEventPublisher, 
    IEventSubscriber, 
    IEventBus,
    Event,
    EventPriority
)
from .config_interface import IConfigManager, ConfigFormat, ConfigScope

__all__ = [
    'ITaskManager',
    'ICacheManager', 
    'ITaskScheduler',
    'ITaskMonitor',
    'IResourceManager',
    'IDatabaseManager',
    'ITaskExecutor',
    'ExecutionStatus',
    'ExecutionResult',
    'IEventPublisher',
    'IEventSubscriber',
    'IEventBus',
    'Event',
    'EventPriority',
    'IConfigManager',
    'ConfigFormat',
    'ConfigScope'
]