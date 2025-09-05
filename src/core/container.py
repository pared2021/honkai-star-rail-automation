"""依赖注入容器

提供统一的依赖管理和注入机制，解决循环依赖问题。
"""

import asyncio
from typing import Any, Dict, Type, TypeVar, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
from loguru import logger

T = TypeVar('T')

class LifecycleType(Enum):
    """组件生命周期类型"""
    SINGLETON = "singleton"  # 单例
    TRANSIENT = "transient"  # 瞬态
    SCOPED = "scoped"       # 作用域

@dataclass
class ComponentRegistration:
    """组件注册信息"""
    interface: Type
    implementation: Type
    lifecycle: LifecycleType
    factory: Optional[Callable] = None
    dependencies: List[Type] = None
    instance: Any = None
    initialized: bool = False

class DependencyInjectionContainer:
    """依赖注入容器
    
    提供组件注册、依赖解析和生命周期管理功能。
    """
    
    def __init__(self):
        self._registrations: Dict[Type, ComponentRegistration] = {}
        self._instances: Dict[Type, Any] = {}
        self._scoped_instances: Dict[str, Dict[Type, Any]] = {}
        self._current_scope: Optional[str] = None
        self._resolving: set = set()  # 防止循环依赖
        self._initialization_order: List[Type] = []
        
    def register_singleton(self, interface: Type[T], implementation: Type[T], 
                          dependencies: Optional[List[Type]] = None) -> 'DependencyInjectionContainer':
        """注册单例组件"""
        return self._register(interface, implementation, LifecycleType.SINGLETON, dependencies)
    
    def register_transient(self, interface: Type[T], implementation: Type[T],
                          dependencies: Optional[List[Type]] = None) -> 'DependencyInjectionContainer':
        """注册瞬态组件"""
        return self._register(interface, implementation, LifecycleType.TRANSIENT, dependencies)
    
    def register_scoped(self, interface: Type[T], implementation: Type[T],
                       dependencies: Optional[List[Type]] = None) -> 'DependencyInjectionContainer':
        """注册作用域组件"""
        return self._register(interface, implementation, LifecycleType.SCOPED, dependencies)
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T],
                        lifecycle: LifecycleType = LifecycleType.SINGLETON,
                        dependencies: Optional[List[Type]] = None) -> 'DependencyInjectionContainer':
        """注册工厂方法"""
        registration = ComponentRegistration(
            interface=interface,
            implementation=None,
            lifecycle=lifecycle,
            factory=factory,
            dependencies=dependencies or []
        )
        self._registrations[interface] = registration
        return self
    
    def register_instance(self, interface: Type[T], instance: T) -> 'DependencyInjectionContainer':
        """注册实例"""
        registration = ComponentRegistration(
            interface=interface,
            implementation=type(instance),
            lifecycle=LifecycleType.SINGLETON,
            instance=instance,
            initialized=True
        )
        self._registrations[interface] = registration
        self._instances[interface] = instance
        return self
    
    def _register(self, interface: Type[T], implementation: Type[T], 
                 lifecycle: LifecycleType, dependencies: Optional[List[Type]]) -> 'DependencyInjectionContainer':
        """内部注册方法"""
        registration = ComponentRegistration(
            interface=interface,
            implementation=implementation,
            lifecycle=lifecycle,
            dependencies=dependencies or []
        )
        self._registrations[interface] = registration
        return self
    
    def resolve(self, interface: Type[T]) -> T:
        """解析组件"""
        if interface in self._resolving:
            raise ValueError(f"检测到循环依赖: {interface.__name__}")
        
        try:
            self._resolving.add(interface)
            return self._resolve_internal(interface)
        finally:
            self._resolving.discard(interface)
    
    def _resolve_internal(self, interface: Type[T]) -> T:
        """内部解析方法"""
        if interface not in self._registrations:
            raise ValueError(f"未注册的接口: {interface.__name__}")
        
        registration = self._registrations[interface]
        
        # 检查是否已有实例
        if registration.lifecycle == LifecycleType.SINGLETON:
            if interface in self._instances:
                return self._instances[interface]
        elif registration.lifecycle == LifecycleType.SCOPED:
            if self._current_scope and self._current_scope in self._scoped_instances:
                if interface in self._scoped_instances[self._current_scope]:
                    return self._scoped_instances[self._current_scope][interface]
        
        # 创建实例
        instance = self._create_instance(registration)
        
        # 缓存实例
        if registration.lifecycle == LifecycleType.SINGLETON:
            self._instances[interface] = instance
        elif registration.lifecycle == LifecycleType.SCOPED and self._current_scope:
            if self._current_scope not in self._scoped_instances:
                self._scoped_instances[self._current_scope] = {}
            self._scoped_instances[self._current_scope][interface] = instance
        
        return instance
    
    def _create_instance(self, registration: ComponentRegistration) -> Any:
        """创建实例"""
        if registration.instance is not None:
            return registration.instance
        
        if registration.factory:
            # 使用工厂方法
            dependencies = self._resolve_dependencies(registration.dependencies)
            return registration.factory(*dependencies)
        else:
            # 使用构造函数
            dependencies = self._resolve_dependencies(registration.dependencies)
            return registration.implementation(*dependencies)
    
    def _resolve_dependencies(self, dependencies: List[Type]) -> List[Any]:
        """解析依赖"""
        resolved_dependencies = []
        for dep in dependencies:
            resolved_dependencies.append(self.resolve(dep))
        return resolved_dependencies
    
    def begin_scope(self, scope_name: str) -> 'ScopeContext':
        """开始作用域"""
        return ScopeContext(self, scope_name)
    
    def _enter_scope(self, scope_name: str):
        """进入作用域"""
        self._current_scope = scope_name
    
    def _exit_scope(self, scope_name: str):
        """退出作用域"""
        if scope_name in self._scoped_instances:
            # 清理作用域实例
            for instance in self._scoped_instances[scope_name].values():
                if hasattr(instance, 'dispose'):
                    try:
                        instance.dispose()
                    except Exception as e:
                        logger.warning(f"清理作用域实例时出错: {e}")
            del self._scoped_instances[scope_name]
        
        if self._current_scope == scope_name:
            self._current_scope = None
    
    async def initialize_all(self):
        """初始化所有单例组件"""
        # 计算初始化顺序
        self._calculate_initialization_order()
        
        # 按顺序初始化
        for interface in self._initialization_order:
            registration = self._registrations[interface]
            if registration.lifecycle == LifecycleType.SINGLETON and not registration.initialized:
                try:
                    instance = self.resolve(interface)
                    if hasattr(instance, 'initialize'):
                        if asyncio.iscoroutinefunction(instance.initialize):
                            await instance.initialize()
                        else:
                            instance.initialize()
                    registration.initialized = True
                    logger.info(f"已初始化组件: {interface.__name__}")
                except Exception as e:
                    logger.error(f"初始化组件 {interface.__name__} 失败: {e}")
                    raise
    
    def _calculate_initialization_order(self):
        """计算初始化顺序（拓扑排序）"""
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(interface: Type):
            if interface in temp_visited:
                raise ValueError(f"检测到循环依赖: {interface.__name__}")
            if interface in visited:
                return
            
            temp_visited.add(interface)
            
            if interface in self._registrations:
                registration = self._registrations[interface]
                for dep in registration.dependencies:
                    visit(dep)
            
            temp_visited.remove(interface)
            visited.add(interface)
            order.append(interface)
        
        for interface in self._registrations:
            if interface not in visited:
                visit(interface)
        
        self._initialization_order = order
    
    async def dispose_all(self):
        """清理所有组件"""
        # 反向清理
        for interface in reversed(self._initialization_order):
            if interface in self._instances:
                instance = self._instances[interface]
                if hasattr(instance, 'dispose'):
                    try:
                        if asyncio.iscoroutinefunction(instance.dispose):
                            await instance.dispose()
                        else:
                            instance.dispose()
                        logger.info(f"已清理组件: {interface.__name__}")
                    except Exception as e:
                        logger.warning(f"清理组件 {interface.__name__} 时出错: {e}")
        
        # 清理所有作用域
        for scope_name in list(self._scoped_instances.keys()):
            self._exit_scope(scope_name)
        
        self._instances.clear()
        self._initialization_order.clear()
    
    def is_registered(self, interface: Type) -> bool:
        """检查接口是否已注册"""
        return interface in self._registrations
    
    def get_registration_info(self, interface: Type) -> Optional[ComponentRegistration]:
        """获取注册信息"""
        return self._registrations.get(interface)
    
    def get_all_registrations(self) -> Dict[Type, ComponentRegistration]:
        """获取所有注册信息"""
        return self._registrations.copy()

class ScopeContext:
    """作用域上下文管理器"""
    
    def __init__(self, container: DependencyInjectionContainer, scope_name: str):
        self.container = container
        self.scope_name = scope_name
    
    def __enter__(self):
        self.container._enter_scope(self.scope_name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.container._exit_scope(self.scope_name)

# 全局容器实例
container = DependencyInjectionContainer()