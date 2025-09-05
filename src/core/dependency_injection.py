"""依赖注入容器模块

提供依赖注入容器的实现，用于管理组件之间的依赖关系，
解决循环依赖问题，支持单例模式和工厂模式。
"""

import threading
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union
from abc import ABC, abstractmethod
import inspect
from functools import wraps

T = TypeVar('T')


class DIContainer:
    """依赖注入容器
    
    提供服务注册、解析和生命周期管理功能。
    支持单例模式、瞬态模式和工厂模式。
    """
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._lock = threading.RLock()
        self._resolving: set = set()
    
    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> None:
        """注册单例服务
        
        Args:
            interface: 服务接口类型
            implementation: 服务实现类型
        """
        with self._lock:
            key = self._get_service_key(interface)
            self._services[key] = {
                'type': 'singleton',
                'interface': interface,
                'implementation': implementation,
                'instance': None
            }
    
    def register_transient(self, interface: Type[T], implementation: Type[T]) -> None:
        """注册瞬态服务
        
        Args:
            interface: 服务接口类型
            implementation: 服务实现类型
        """
        with self._lock:
            key = self._get_service_key(interface)
            self._services[key] = {
                'type': 'transient',
                'interface': interface,
                'implementation': implementation
            }
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """注册工厂服务
        
        Args:
            interface: 服务接口类型
            factory: 工厂函数
        """
        with self._lock:
            key = self._get_service_key(interface)
            self._services[key] = {
                'type': 'factory',
                'interface': interface,
                'factory': factory
            }
    
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """注册实例
        
        Args:
            interface: 服务接口类型
            instance: 服务实例
        """
        with self._lock:
            key = self._get_service_key(interface)
            self._singletons[key] = instance
            self._services[key] = {
                'type': 'instance',
                'interface': interface,
                'instance': instance
            }
    
    def resolve(self, interface: Type[T]) -> T:
        """解析服务
        
        Args:
            interface: 服务接口类型
            
        Returns:
            服务实例
            
        Raises:
            ValueError: 服务未注册或存在循环依赖
        """
        key = self._get_service_key(interface)
        
        # 检查循环依赖
        if key in self._resolving:
            raise ValueError(f"检测到循环依赖: {interface.__name__}")
        
        with self._lock:
            if key not in self._services:
                raise ValueError(f"服务未注册: {interface.__name__}")
            
            service_info = self._services[key]
            service_type = service_info['type']
            
            try:
                self._resolving.add(key)
                
                if service_type == 'singleton':
                    return self._resolve_singleton(key, service_info)
                elif service_type == 'transient':
                    return self._resolve_transient(service_info)
                elif service_type == 'factory':
                    return self._resolve_factory(service_info)
                elif service_type == 'instance':
                    return service_info['instance']
                else:
                    raise ValueError(f"未知的服务类型: {service_type}")
            finally:
                self._resolving.discard(key)
    
    def _resolve_singleton(self, key: str, service_info: Dict[str, Any]) -> Any:
        """解析单例服务"""
        if key in self._singletons:
            return self._singletons[key]
        
        instance = self._create_instance(service_info['implementation'])
        self._singletons[key] = instance
        service_info['instance'] = instance
        return instance
    
    def _resolve_transient(self, service_info: Dict[str, Any]) -> Any:
        """解析瞬态服务"""
        return self._create_instance(service_info['implementation'])
    
    def _resolve_factory(self, service_info: Dict[str, Any]) -> Any:
        """解析工厂服务"""
        factory = service_info['factory']
        return factory()
    
    def _create_instance(self, implementation: Type) -> Any:
        """创建实例，自动注入依赖"""
        # 获取构造函数参数
        signature = inspect.signature(implementation.__init__)
        parameters = signature.parameters
        
        # 准备构造函数参数
        kwargs = {}
        for param_name, param in parameters.items():
            if param_name == 'self':
                continue
            
            # 获取参数类型
            param_type = param.annotation
            if param_type == inspect.Parameter.empty:
                continue
            
            # 解析依赖
            try:
                kwargs[param_name] = self.resolve(param_type)
            except ValueError:
                # 如果依赖无法解析且有默认值，使用默认值
                if param.default != inspect.Parameter.empty:
                    kwargs[param_name] = param.default
                else:
                    raise
        
        return implementation(**kwargs)
    
    def _get_service_key(self, interface: Type) -> str:
        """获取服务键"""
        return f"{interface.__module__}.{interface.__name__}"
    
    def is_registered(self, interface: Type) -> bool:
        """检查服务是否已注册"""
        key = self._get_service_key(interface)
        return key in self._services
    
    def clear(self) -> None:
        """清空容器"""
        with self._lock:
            self._services.clear()
            self._singletons.clear()
            self._factories.clear()
            self._resolving.clear()
    
    def get_registered_services(self) -> Dict[str, str]:
        """获取已注册的服务列表"""
        with self._lock:
            return {
                key: info['type'] 
                for key, info in self._services.items()
            }


class ServiceLocator:
    """服务定位器
    
    提供全局访问依赖注入容器的入口点。
    """
    
    _container: Optional[DIContainer] = None
    _lock = threading.RLock()
    
    @classmethod
    def get_container(cls) -> DIContainer:
        """获取容器实例"""
        if cls._container is None:
            with cls._lock:
                if cls._container is None:
                    cls._container = DIContainer()
        return cls._container
    
    @classmethod
    def set_container(cls, container: DIContainer) -> None:
        """设置容器实例"""
        with cls._lock:
            cls._container = container
    
    @classmethod
    def resolve(cls, interface: Type[T]) -> T:
        """解析服务"""
        return cls.get_container().resolve(interface)
    
    @classmethod
    def register_singleton(cls, interface: Type[T], implementation: Type[T]) -> None:
        """注册单例服务"""
        cls.get_container().register_singleton(interface, implementation)
    
    @classmethod
    def register_transient(cls, interface: Type[T], implementation: Type[T]) -> None:
        """注册瞬态服务"""
        cls.get_container().register_transient(interface, implementation)
    
    @classmethod
    def register_factory(cls, interface: Type[T], factory: Callable[[], T]) -> None:
        """注册工厂服务"""
        cls.get_container().register_factory(interface, factory)
    
    @classmethod
    def register_instance(cls, interface: Type[T], instance: T) -> None:
        """注册实例"""
        cls.get_container().register_instance(interface, instance)


def inject(interface: Type[T]) -> Callable:
    """依赖注入装饰器
    
    Args:
        interface: 要注入的服务接口类型
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 注入依赖
            service = ServiceLocator.resolve(interface)
            return func(service, *args, **kwargs)
        return wrapper
    return decorator


class Injectable(ABC):
    """可注入的基类
    
    所有需要依赖注入的类都应该继承此基类。
    """
    
    def __init__(self):
        self._injected = False
    
    def inject_dependencies(self) -> None:
        """注入依赖"""
        if self._injected:
            return
        
        # 获取类的所有属性
        for attr_name in dir(self):
            if attr_name.startswith('_'):
                continue
            
            attr = getattr(self.__class__, attr_name, None)
            if attr is None:
                continue
            
            # 检查是否有类型注解
            if hasattr(attr, '__annotations__'):
                for annotation_name, annotation_type in attr.__annotations__.items():
                    if ServiceLocator.get_container().is_registered(annotation_type):
                        setattr(self, annotation_name, ServiceLocator.resolve(annotation_type))
        
        self._injected = True


# 全局容器实例
container = ServiceLocator.get_container()