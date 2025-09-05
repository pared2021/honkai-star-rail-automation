#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用程序主入口模块

提供统一的应用程序初始化和依赖注入容器管理。
负责：
1. 应用程序生命周期管理
2. 依赖注入容器初始化
3. 核心组件配置和启动
4. 统一的服务访问接口
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from .container import DependencyInjectionContainer
from .container_config import configure_container
from .interfaces.task_manager import ITaskManager
from .interfaces.config_manager import IConfigManager
from .interfaces.event_bus import IEventBus
from .interfaces.database_manager import IDatabaseManager
from .interfaces.cache_manager import ICacheManager
from .interfaces.task_scheduler import ITaskScheduler
from .interfaces.task_monitor import ITaskMonitor
from .interfaces.task_executor import ITaskExecutor
from .interfaces.resource_manager import IResourceManager

logger = logging.getLogger(__name__)


class Application:
    """应用程序主类
    
    负责管理应用程序的生命周期和依赖注入容器。
    提供统一的服务访问接口。
    """
    
    def __init__(self):
        self._container: Optional[DependencyInjectionContainer] = None
        self._initialized = False
        self._running = False
    
    async def initialize(self, config_path: Optional[str] = None) -> None:
        """初始化应用程序
        
        Args:
            config_path: 配置文件路径
        """
        if self._initialized:
            logger.warning("应用程序已经初始化")
            return
        
        try:
            logger.info("开始初始化应用程序...")
            
            # 创建依赖注入容器
            self._container = DependencyInjectionContainer()
            
            # 配置容器
            configure_container(self._container)
            
            # 初始化配置管理器
            config_manager = self._container.resolve(IConfigManager)
            if config_path:
                await config_manager.load_config(config_path)
            
            # 初始化数据库管理器
            db_manager = self._container.resolve(IDatabaseManager)
            await db_manager.initialize()
            
            # 初始化事件总线
            event_bus = self._container.resolve(IEventBus)
            await event_bus.initialize()
            
            self._initialized = True
            logger.info("应用程序初始化完成")
            
        except Exception as e:
            logger.error(f"应用程序初始化失败: {e}")
            await self.cleanup()
            raise
    
    async def start(self) -> None:
        """启动应用程序"""
        if not self._initialized:
            raise RuntimeError("应用程序未初始化")
        
        if self._running:
            logger.warning("应用程序已经在运行")
            return
        
        try:
            logger.info("启动应用程序...")
            
            # 启动任务调度器
            scheduler = self._container.resolve(ITaskScheduler)
            await scheduler.start()
            
            # 启动任务监控器
            monitor = self._container.resolve(ITaskMonitor)
            await monitor.start()
            
            self._running = True
            logger.info("应用程序启动完成")
            
        except Exception as e:
            logger.error(f"应用程序启动失败: {e}")
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """停止应用程序"""
        if not self._running:
            return
        
        try:
            logger.info("停止应用程序...")
            
            # 停止任务监控器
            if self._container:
                monitor = self._container.resolve(ITaskMonitor)
                await monitor.stop()
                
                # 停止任务调度器
                scheduler = self._container.resolve(ITaskScheduler)
                await scheduler.stop()
            
            self._running = False
            logger.info("应用程序停止完成")
            
        except Exception as e:
            logger.error(f"应用程序停止失败: {e}")
    
    async def cleanup(self) -> None:
        """清理应用程序资源"""
        try:
            logger.info("清理应用程序资源...")
            
            # 停止应用程序
            await self.stop()
            
            # 清理容器
            if self._container:
                await self._container.cleanup()
                self._container = None
            
            self._initialized = False
            logger.info("应用程序资源清理完成")
            
        except Exception as e:
            logger.error(f"应用程序资源清理失败: {e}")
    
    @asynccontextmanager
    async def lifespan(self, config_path: Optional[str] = None):
        """应用程序生命周期上下文管理器
        
        Args:
            config_path: 配置文件路径
        """
        try:
            await self.initialize(config_path)
            await self.start()
            yield self
        finally:
            await self.cleanup()
    
    # 服务访问接口
    
    @property
    def task_manager(self) -> ITaskManager:
        """获取任务管理器"""
        if not self._container:
            raise RuntimeError("应用程序未初始化")
        return self._container.resolve(ITaskManager)
    
    @property
    def config_manager(self) -> IConfigManager:
        """获取配置管理器"""
        if not self._container:
            raise RuntimeError("应用程序未初始化")
        return self._container.resolve(IConfigManager)
    
    @property
    def event_bus(self) -> IEventBus:
        """获取事件总线"""
        if not self._container:
            raise RuntimeError("应用程序未初始化")
        return self._container.resolve(IEventBus)
    
    @property
    def database_manager(self) -> IDatabaseManager:
        """获取数据库管理器"""
        if not self._container:
            raise RuntimeError("应用程序未初始化")
        return self._container.resolve(IDatabaseManager)
    
    @property
    def cache_manager(self) -> ICacheManager:
        """获取缓存管理器"""
        if not self._container:
            raise RuntimeError("应用程序未初始化")
        return self._container.resolve(ICacheManager)
    
    @property
    def task_scheduler(self) -> ITaskScheduler:
        """获取任务调度器"""
        if not self._container:
            raise RuntimeError("应用程序未初始化")
        return self._container.resolve(ITaskScheduler)
    
    @property
    def task_monitor(self) -> ITaskMonitor:
        """获取任务监控器"""
        if not self._container:
            raise RuntimeError("应用程序未初始化")
        return self._container.resolve(ITaskMonitor)
    
    @property
    def task_executor(self) -> ITaskExecutor:
        """获取任务执行器"""
        if not self._container:
            raise RuntimeError("应用程序未初始化")
        return self._container.resolve(ITaskExecutor)
    
    @property
    def resource_manager(self) -> IResourceManager:
        """获取资源管理器"""
        if not self._container:
            raise RuntimeError("应用程序未初始化")
        return self._container.resolve(IResourceManager)
    
    def get_service(self, service_type: type) -> Any:
        """获取指定类型的服务
        
        Args:
            service_type: 服务类型
            
        Returns:
            服务实例
        """
        if not self._container:
            raise RuntimeError("应用程序未初始化")
        return self._container.resolve(service_type)
    
    @property
    def is_initialized(self) -> bool:
        """检查应用程序是否已初始化"""
        return self._initialized
    
    @property
    def is_running(self) -> bool:
        """检查应用程序是否正在运行"""
        return self._running


# 全局应用程序实例
_app_instance: Optional[Application] = None


def get_app() -> Application:
    """获取全局应用程序实例"""
    global _app_instance
    if _app_instance is None:
        _app_instance = Application()
    return _app_instance


async def create_app(config_path: Optional[str] = None) -> Application:
    """创建并初始化应用程序实例
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        应用程序实例
    """
    app = get_app()
    if not app.is_initialized:
        await app.initialize(config_path)
    return app


# 便捷访问函数

def get_task_manager() -> ITaskManager:
    """获取任务管理器"""
    return get_app().task_manager


def get_config_manager() -> IConfigManager:
    """获取配置管理器"""
    return get_app().config_manager


def get_event_bus() -> IEventBus:
    """获取事件总线"""
    return get_app().event_bus


def get_database_manager() -> IDatabaseManager:
    """获取数据库管理器"""
    return get_app().database_manager


def get_cache_manager() -> ICacheManager:
    """获取缓存管理器"""
    return get_app().cache_manager


def get_task_scheduler() -> ITaskScheduler:
    """获取任务调度器"""
    return get_app().task_scheduler


def get_task_monitor() -> ITaskMonitor:
    """获取任务监控器"""
    return get_app().task_monitor


def get_task_executor() -> ITaskExecutor:
    """获取任务执行器"""
    return get_app().task_executor


def get_resource_manager() -> IResourceManager:
    """获取资源管理器"""
    return get_app().resource_manager