"""服务定位器模式实现

提供服务定位和获取功能，作为依赖注入的补充。
用于在现有代码中逐步引入依赖注入机制。
"""

from typing import Type, TypeVar, Optional, Dict, Any
from .dependency_injection import get_container, DIContainer

T = TypeVar('T')


class ServiceLocator:
    """服务定位器
    
    提供全局服务访问点，简化服务获取过程。
    """
    
    def __init__(self, container: Optional[DIContainer] = None):
        self._container = container or get_container()
        self._instances: Dict[Type, Any] = {}
    
    def get_service(self, service_type: Type[T]) -> T:
        """获取服务实例
        
        Args:
            service_type: 服务类型
            
        Returns:
            服务实例
            
        Raises:
            ValueError: 服务未注册
        """
        try:
            return self._container.resolve(service_type)
        except ValueError as e:
            # 如果容器中没有注册，尝试从缓存获取
            if service_type in self._instances:
                return self._instances[service_type]
            raise e
    
    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """注册服务实例
        
        Args:
            service_type: 服务类型
            instance: 服务实例
        """
        self._instances[service_type] = instance
        self._container.register_instance(service_type, instance)
    
    def is_registered(self, service_type: Type) -> bool:
        """检查服务是否已注册
        
        Args:
            service_type: 服务类型
            
        Returns:
            是否已注册
        """
        return (
            self._container.is_registered(service_type) or 
            service_type in self._instances
        )
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self._instances.clear()


# 全局服务定位器实例
_service_locator: Optional[ServiceLocator] = None


def get_service_locator() -> ServiceLocator:
    """获取全局服务定位器
    
    Returns:
        服务定位器实例
    """
    global _service_locator
    if _service_locator is None:
        _service_locator = ServiceLocator()
    return _service_locator


def get_service(service_type: Type[T]) -> T:
    """获取服务实例的便捷方法
    
    Args:
        service_type: 服务类型
        
    Returns:
        服务实例
    """
    return get_service_locator().get_service(service_type)


def register_service(service_type: Type[T], instance: T) -> None:
    """注册服务实例的便捷方法
    
    Args:
        service_type: 服务类型
        instance: 服务实例
    """
    get_service_locator().register_instance(service_type, instance)


def is_service_registered(service_type: Type) -> bool:
    """检查服务是否已注册的便捷方法
    
    Args:
        service_type: 服务类型
        
    Returns:
        是否已注册
    """
    return get_service_locator().is_registered(service_type)


def initialize_services() -> None:
    """初始化服务
    
    配置依赖注入容器并注册所有服务。
    """
    from .dependency_injection import configure_container
    
    # 配置容器
    container = configure_container()
    
    # 创建服务定位器
    global _service_locator
    _service_locator = ServiceLocator(container)
    
    print("服务定位器初始化完成")


class ServiceMixin:
    """服务混入类
    
    为类提供便捷的服务访问方法。
    """
    
    def get_service(self, service_type: Type[T]) -> T:
        """获取服务实例
        
        Args:
            service_type: 服务类型
            
        Returns:
            服务实例
        """
        return get_service(service_type)
    
    def is_service_available(self, service_type: Type) -> bool:
        """检查服务是否可用
        
        Args:
            service_type: 服务类型
            
        Returns:
            是否可用
        """
        return is_service_registered(service_type)