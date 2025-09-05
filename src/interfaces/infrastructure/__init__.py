"""基础设施层接口

定义基础设施层的抽象接口。
"""

from .event_bus_interface import IEvent, IEventBus
from .cache_interface import ICacheService
from .logger_interface import ILogger, LogLevel
from .filesystem_interface import IFileSystemService, FileType, FilePermission
from .network_interface import INetworkService, HttpMethod, NetworkProtocol
from .dependency_injection_interface import (
    IDependencyContainer, IDependencyScope, LifetimeScope,
    DependencyResolutionError, CircularDependencyError, ServiceNotRegisteredException
)
from .configuration_interface import (
    IConfigurationProvider, IConfigurationManager, IConfigurationBuilder,
    IConfigurationValidator, IConfigurationEncryption,
    ConfigurationSource, ConfigurationFormat, ConfigurationLevel
)
from .architecture_validation_interface import (
    IArchitectureValidator,
    IDependencyAnalyzer,
    ILayerValidator,
    ISOLIDValidator,
    IArchitectureReporter,
    ValidationLevel,
    ArchitectureLayer,
    DependencyType,
    ValidationResult,
    DependencyInfo,
    ModuleInfo,
    ArchitectureMetrics
)

__all__ = [
    # 事件总线
    'IEvent',
    'IEventBus',
    
    # 缓存服务
    'ICacheService',
    
    # 日志服务
    'ILogger',
    'LogLevel',
    
    # 文件系统服务
    'IFileSystemService',
    'FileType',
    'FilePermission',
    
    # 网络服务
    'INetworkService',
    'HttpMethod',
    'NetworkProtocol',
    
    # 依赖注入
    'IDependencyContainer',
    'IDependencyScope',
    'LifetimeScope',
    'DependencyResolutionError',
    'CircularDependencyError',
    'ServiceNotRegisteredException',
    
    # 配置管理
    'IConfigurationProvider',
    'IConfigurationManager',
    'IConfigurationBuilder',
    'IConfigurationValidator',
    'IConfigurationEncryption',
    'ConfigurationSource',
    'ConfigurationFormat',
    'ConfigurationLevel',
    
    # 架构验证
    'IArchitectureValidator',
    'IDependencyAnalyzer',
    'ILayerValidator',
    'ISOLIDValidator',
    'IArchitectureReporter',
    'ValidationLevel',
    'ArchitectureLayer',
    'DependencyType',
    'ValidationResult',
    'DependencyInfo',
    'ModuleInfo',
    'ArchitectureMetrics'
]