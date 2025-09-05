"""依赖注入容器配置

配置所有组件的依赖关系和生命周期。
"""

from .container import DependencyInjectionContainer
from .interfaces import (
    IDatabaseManager, ITaskManager, ICacheManager, ITaskScheduler,
    ITaskMonitor, IResourceManager, ITaskExecutor, IEventBus, IConfigManager
)
from .interfaces.i_action_config_service import IActionConfigService
from .database_manager import DatabaseManager
from .refactored_task_manager import RefactoredTaskManager
from .managers.task_cache_manager import TaskCacheManager
from .managers.task_scheduler import TaskScheduler
from .managers.task_monitor import TaskMonitor
from .managers.task_resource_manager import TaskResourceManager
from .managers.task_executor import TaskExecutor
from .event_bus import EventBus
from .config_manager import ConfigManager
from .services.action_config_service import ActionConfigService

def configure_container(container: DependencyInjectionContainer) -> None:
    """配置依赖注入容器
    
    Args:
        container: 依赖注入容器实例
    """
    
    # 注册配置管理器（最基础的组件，无依赖）
    container.register_singleton(
        IConfigManager,
        ConfigManager,
        dependencies=[]
    )
    
    # 注册动作配置服务（依赖配置管理器）
    container.register_singleton(
        IActionConfigService,
        ActionConfigService,
        dependencies=[IConfigManager]
    )
    
    # 注册事件总线（基础组件，无依赖）
    container.register_singleton(
        IEventBus,
        EventBus,
        dependencies=[]
    )
    
    # 注册数据库管理器（依赖配置管理器）
    container.register_singleton(
        IDatabaseManager,
        DatabaseManager,
        dependencies=[IConfigManager]
    )
    
    # 注册缓存管理器（依赖配置管理器）
    container.register_singleton(
        ICacheManager,
        TaskCacheManager,
        dependencies=[IConfigManager]
    )
    
    # 注册资源管理器（依赖配置管理器和事件总线）
    container.register_singleton(
        IResourceManager,
        TaskResourceManager,
        dependencies=[IConfigManager, IEventBus]
    )
    
    # 注册任务执行器（依赖配置管理器、事件总线和资源管理器）
    container.register_singleton(
        ITaskExecutor,
        TaskExecutor,
        dependencies=[IConfigManager, IEventBus, IResourceManager]
    )
    
    # 注册任务监控器（依赖配置管理器、事件总线和任务执行器）
    container.register_singleton(
        ITaskMonitor,
        TaskMonitor,
        dependencies=[IConfigManager, IEventBus, ITaskExecutor]
    )
    
    # 注册任务调度器（依赖配置管理器、事件总线、任务执行器和资源管理器）
    container.register_singleton(
        ITaskScheduler,
        TaskScheduler,
        dependencies=[IConfigManager, IEventBus, ITaskExecutor, IResourceManager]
    )
    
    # 注册任务管理器（依赖所有其他组件）
    container.register_singleton(
        ITaskManager,
        RefactoredTaskManager,
        dependencies=[
            IDatabaseManager,
            ICacheManager,
            ITaskScheduler,
            ITaskMonitor,
            IResourceManager,
            ITaskExecutor,
            IEventBus,
            IConfigManager
        ]
    )

def create_configured_container() -> DependencyInjectionContainer:
    """创建并配置依赖注入容器
    
    Returns:
        配置好的依赖注入容器
    """
    container = DependencyInjectionContainer()
    configure_container(container)
    return container

# 创建全局容器实例
app_container = create_configured_container()