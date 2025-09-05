"""依赖注入类型定义

定义依赖注入相关的枚举、异常和类型。
"""

from enum import Enum


class LifetimeScope(Enum):
    """生命周期范围"""
    SINGLETON = "singleton"  # 单例
    TRANSIENT = "transient"  # 瞬态
    SCOPED = "scoped"       # 作用域


class DependencyResolutionError(Exception):
    """依赖解析异常"""
    pass


class CircularDependencyError(DependencyResolutionError):
    """循环依赖异常"""
    pass


class ServiceNotRegisteredException(DependencyResolutionError):
    """服务未注册异常"""
    pass