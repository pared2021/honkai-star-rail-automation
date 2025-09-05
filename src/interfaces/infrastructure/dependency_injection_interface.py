"""依赖注入容器接口

定义依赖注入容器的抽象接口，用于管理对象的创建和依赖关系。
"""

from abc import ABC, abstractmethod
from typing import Type, TypeVar, Optional, List, Callable

from .dependency_injection_types import LifetimeScope

T = TypeVar('T')


class IDependencyContainer(ABC):
    """依赖注入容器接口"""
    
    @abstractmethod
    def register(self, 
                interface: Type[T], 
                implementation: Type[T], 
                lifetime: LifetimeScope = LifetimeScope.TRANSIENT) -> None:
        """注册服务
        
        Args:
            interface: 接口类型
            implementation: 实现类型
            lifetime: 生命周期
        """
        pass
    
    @abstractmethod
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """注册实例
        
        Args:
            interface: 接口类型
            instance: 实例对象
        """
        pass
    
    @abstractmethod
    def register_factory(self, 
                        interface: Type[T], 
                        factory: Callable[[], T],
                        lifetime: LifetimeScope = LifetimeScope.TRANSIENT) -> None:
        """注册工厂方法
        
        Args:
            interface: 接口类型
            factory: 工厂方法
            lifetime: 生命周期
        """
        pass
    
    @abstractmethod
    def resolve(self, interface: Type[T]) -> T:
        """解析服务
        
        Args:
            interface: 接口类型
            
        Returns:
            服务实例
            
        Raises:
            DependencyResolutionError: 解析失败
        """
        pass
    
    @abstractmethod
    def try_resolve(self, interface: Type[T]) -> Optional[T]:
        """尝试解析服务
        
        Args:
            interface: 接口类型
            
        Returns:
            服务实例或None
        """
        pass
    
    @abstractmethod
    def is_registered(self, interface: Type) -> bool:
        """检查服务是否已注册
        
        Args:
            interface: 接口类型
            
        Returns:
            是否已注册
        """
        pass
    
    @abstractmethod
    def unregister(self, interface: Type) -> None:
        """取消注册服务
        
        Args:
            interface: 接口类型
        """
        pass
    
    @abstractmethod
    def get_registered_services(self) -> List[Type]:
        """获取已注册的服务列表
        
        Returns:
            已注册的服务类型列表
        """
        pass
    
    @abstractmethod
    def create_scope(self) -> 'IDependencyScope':
        """创建作用域
        
        Returns:
            依赖作用域
        """
        pass
    
    @abstractmethod
    def dispose(self) -> None:
        """释放容器资源"""
        pass


class IDependencyScope(ABC):
    """依赖作用域接口"""
    
    @abstractmethod
    def resolve(self, interface: Type[T]) -> T:
        """在作用域内解析服务
        
        Args:
            interface: 接口类型
            
        Returns:
            服务实例
        """
        pass
    
    @abstractmethod
    def try_resolve(self, interface: Type[T]) -> Optional[T]:
        """在作用域内尝试解析服务
        
        Args:
            interface: 接口类型
            
        Returns:
            服务实例或None
        """
        pass
    
    @abstractmethod
    def dispose(self) -> None:
        """释放作用域资源"""
        pass