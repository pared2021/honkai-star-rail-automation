"""服务定位器模块.

提供服务的定位和管理功能。
"""

from typing import Any, Dict, Type, TypeVar
from loguru import logger

T = TypeVar('T')


class ServiceLocator:
    """服务定位器类.
    
    提供依赖注入和服务管理功能。
    """
    
    def __init__(self):
        """初始化服务定位器."""
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
        
    def register(self, service_type: Type[T], instance: T) -> None:
        """注册服务实例.
        
        Args:
            service_type: 服务类型
            instance: 服务实例
        """
        self._services[service_type] = instance
        logger.debug(f"注册服务: {service_type.__name__}")
        
    def register_singleton(self, service_type: Type[T], factory: callable) -> None:
        """注册单例服务.
        
        Args:
            service_type: 服务类型
            factory: 服务工厂函数
        """
        self._singletons[service_type] = factory
        logger.debug(f"注册单例服务: {service_type.__name__}")
        
    def get(self, service_type: Type[T]) -> T:
        """获取服务实例.
        
        Args:
            service_type: 服务类型
            
        Returns:
            服务实例
            
        Raises:
            ValueError: 当服务未注册时
        """
        # 检查已注册的服务
        if service_type in self._services:
            return self._services[service_type]
            
        # 检查单例服务
        if service_type in self._singletons:
            if service_type not in self._services:
                instance = self._singletons[service_type]()
                self._services[service_type] = instance
            return self._services[service_type]
            
        raise ValueError(f"服务未注册: {service_type.__name__}")
        
    def clear(self) -> None:
        """清除所有服务."""
        self._services.clear()
        self._singletons.clear()
        logger.debug("清除所有服务")


# 全局服务定位器实例
_service_locator = ServiceLocator()


def get_service_locator() -> ServiceLocator:
    """获取全局服务定位器实例.
    
    Returns:
        服务定位器实例
    """
    return _service_locator


def register_service(service_type: Type[T], instance: T) -> None:
    """注册服务到全局定位器.
    
    Args:
        service_type: 服务类型
        instance: 服务实例
    """
    _service_locator.register(service_type, instance)


def get_service(service_type: Type[T]) -> T:
    """从全局定位器获取服务.
    
    Args:
        service_type: 服务类型
        
    Returns:
        服务实例
    """
    return _service_locator.get(service_type)


def initialize_services() -> None:
    """初始化服务容器.
    
    注册所有核心服务到服务定位器。
    """
    logger.info("开始初始化服务容器")
    
    try:
        # 导入并注册核心服务
        from src.core.config_manager import ConfigManager
        from src.database.db_manager import DatabaseManager
        
        # 注册配置管理器
        config_manager = ConfigManager()
        register_service(ConfigManager, config_manager)
        
        # 注册数据库管理器
        db_manager = DatabaseManager("data/app.db")
        register_service(DatabaseManager, db_manager)
        
        logger.info("服务容器初始化完成")
        
    except Exception as e:
        logger.error(f"服务容器初始化失败: {e}")
        raise
