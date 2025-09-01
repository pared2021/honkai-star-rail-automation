# -*- coding: utf-8 -*-
"""
统一的异步服务基类
建立异步编程模型规范，为所有异步服务提供统一的基础架构
"""

import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional, Callable, TypeVar, Generic, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager

from loguru import logger
from src.exceptions import ServiceError

T = TypeVar('T')


class ServiceStatus(Enum):
    """服务状态"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class ServicePriority(Enum):
    """服务优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class HealthStatus(Enum):
    """健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceConfig:
    """服务配置"""
    name: str
    version: str = "1.0.0"
    description: str = ""
    priority: ServicePriority = ServicePriority.NORMAL
    auto_start: bool = True
    auto_restart: bool = False
    max_restart_attempts: int = 3
    restart_delay: float = 1.0
    health_check_interval: float = 30.0
    enable_metrics: bool = True
    enable_logging: bool = True
    timeout_seconds: float = 30.0
    max_concurrent_operations: int = 100
    custom_config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'priority': self.priority.value,
            'auto_start': self.auto_start,
            'auto_restart': self.auto_restart,
            'max_restart_attempts': self.max_restart_attempts,
            'restart_delay': self.restart_delay,
            'health_check_interval': self.health_check_interval,
            'enable_metrics': self.enable_metrics,
            'enable_logging': self.enable_logging,
            'timeout_seconds': self.timeout_seconds,
            'max_concurrent_operations': self.max_concurrent_operations,
            'custom_config': self.custom_config
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceConfig':
        """从字典创建"""
        config = cls(
            name=data['name'],
            version=data.get('version', '1.0.0'),
            description=data.get('description', ''),
            priority=ServicePriority(data.get('priority', 'normal')),
            auto_start=data.get('auto_start', True),
            auto_restart=data.get('auto_restart', False),
            max_restart_attempts=data.get('max_restart_attempts', 3),
            restart_delay=data.get('restart_delay', 1.0),
            health_check_interval=data.get('health_check_interval', 30.0),
            enable_metrics=data.get('enable_metrics', True),
            enable_logging=data.get('enable_logging', True),
            timeout_seconds=data.get('timeout_seconds', 30.0),
            max_concurrent_operations=data.get('max_concurrent_operations', 100),
            custom_config=data.get('custom_config', {})
        )
        return config


@dataclass
class ServiceMetrics:
    """服务指标"""
    service_name: str
    start_time: float = field(default_factory=time.time)
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    current_concurrent_operations: int = 0
    max_concurrent_operations_reached: int = 0
    total_errors: int = 0
    last_error_time: Optional[float] = None
    last_error_message: Optional[str] = None
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def uptime_seconds(self) -> float:
        """运行时间（秒）"""
        return time.time() - self.start_time
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def error_rate(self) -> float:
        """错误率"""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'service_name': self.service_name,
            'start_time': self.start_time,
            'uptime_seconds': self.uptime_seconds,
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': self.success_rate,
            'error_rate': self.error_rate,
            'average_response_time': self.average_response_time,
            'current_concurrent_operations': self.current_concurrent_operations,
            'max_concurrent_operations_reached': self.max_concurrent_operations_reached,
            'total_errors': self.total_errors,
            'last_error_time': self.last_error_time,
            'last_error_message': self.last_error_message,
            'custom_metrics': self.custom_metrics
        }


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    check_time: float = field(default_factory=time.time)
    response_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'status': self.status.value,
            'message': self.message,
            'details': self.details,
            'check_time': self.check_time,
            'response_time_ms': self.response_time_ms
        }





class BaseAsyncService(ABC):
    """异步服务基类
    
    提供统一的异步服务架构，包括：
    1. 生命周期管理（启动、停止、重启）
    2. 健康检查和监控
    3. 指标收集和统计
    4. 错误处理和恢复
    5. 并发控制和资源管理
    6. 配置管理
    7. 日志记录
    """
    
    def __init__(self, config: ServiceConfig):
        """
        初始化异步服务
        
        Args:
            config: 服务配置
        """
        self.config = config
        self.service_id = str(uuid.uuid4())
        
        # 状态管理
        self._status = ServiceStatus.STOPPED
        self._status_lock = asyncio.Lock()
        
        # 指标和监控
        self._metrics = ServiceMetrics(service_name=config.name)
        self._health_status = HealthStatus.UNKNOWN
        self._last_health_check: Optional[HealthCheckResult] = None
        
        # 任务管理
        self._background_tasks: List[asyncio.Task] = []
        self._health_check_task: Optional[asyncio.Task] = None
        self._semaphore = asyncio.Semaphore(config.max_concurrent_operations)
        
        # 重启管理
        self._restart_attempts = 0
        self._last_restart_time = 0.0
        
        # 事件回调
        self._status_change_callbacks: List[Callable[[ServiceStatus, ServiceStatus], None]] = []
        self._error_callbacks: List[Callable[[ServiceError], None]] = []
        
        # 响应时间统计
        self._response_times: List[float] = []
        self._max_response_time_samples = 1000
        
        logger.info(f"异步服务初始化: {config.name} (ID: {self.service_id})")
    
    # ==================== 抽象方法 ====================
    
    @abstractmethod
    async def _startup(self) -> None:
        """
        服务启动逻辑（子类实现）
        
        Raises:
            ServiceError: 启动失败
        """
        pass
    
    @abstractmethod
    async def _shutdown(self) -> None:
        """
        服务关闭逻辑（子类实现）
        
        Raises:
            ServiceError: 关闭失败
        """
        pass
    
    @abstractmethod
    async def _health_check(self) -> HealthCheckResult:
        """
        健康检查逻辑（子类实现）
        
        Returns:
            HealthCheckResult: 健康检查结果
        """
        pass
    
    # ==================== 生命周期管理 ====================
    
    async def start(self) -> bool:
        """
        启动服务
        
        Returns:
            bool: 启动是否成功
        """
        async with self._status_lock:
            if self._status == ServiceStatus.RUNNING:
                logger.warning(f"服务已在运行: {self.config.name}")
                return True
            
            if self._status == ServiceStatus.STARTING:
                logger.warning(f"服务正在启动: {self.config.name}")
                return False
            
            try:
                await self._change_status(ServiceStatus.STARTING)
                
                # 重置指标
                self._metrics = ServiceMetrics(service_name=self.config.name)
                
                # 执行启动逻辑
                await self._startup()
                
                # 启动健康检查
                if self.config.health_check_interval > 0:
                    self._start_health_check()
                
                await self._change_status(ServiceStatus.RUNNING)
                
                logger.info(f"服务启动成功: {self.config.name}")
                return True
                
            except Exception as e:
                await self._change_status(ServiceStatus.ERROR)
                error = ServiceError(f"服务启动失败: {e}", original_error=e)
                await self._handle_error(error)
                return False
    
    async def stop(self, timeout: Optional[float] = None) -> bool:
        """
        停止服务
        
        Args:
            timeout: 停止超时时间
            
        Returns:
            bool: 停止是否成功
        """
        async with self._status_lock:
            if self._status == ServiceStatus.STOPPED:
                return True
            
            if self._status == ServiceStatus.STOPPING:
                logger.warning(f"服务正在停止: {self.config.name}")
                return False
            
            try:
                await self._change_status(ServiceStatus.STOPPING)
                
                # 停止健康检查
                await self._stop_health_check()
                
                # 取消后台任务
                await self._cancel_background_tasks()
                
                # 执行关闭逻辑
                if timeout:
                    await asyncio.wait_for(self._shutdown(), timeout=timeout)
                else:
                    await self._shutdown()
                
                await self._change_status(ServiceStatus.STOPPED)
                
                logger.info(f"服务停止成功: {self.config.name}")
                return True
                
            except Exception as e:
                await self._change_status(ServiceStatus.ERROR)
                error = ServiceError(f"服务停止失败: {e}", original_error=e)
                await self._handle_error(error)
                return False
    
    async def restart(self, timeout: Optional[float] = None) -> bool:
        """
        重启服务
        
        Args:
            timeout: 重启超时时间
            
        Returns:
            bool: 重启是否成功
        """
        logger.info(f"重启服务: {self.config.name}")
        
        # 检查重启限制
        current_time = time.time()
        if (current_time - self._last_restart_time) < self.config.restart_delay:
            logger.warning(f"重启过于频繁，跳过: {self.config.name}")
            return False
        
        if self._restart_attempts >= self.config.max_restart_attempts:
            logger.error(f"重启次数超限，停止重启: {self.config.name}")
            return False
        
        self._restart_attempts += 1
        self._last_restart_time = current_time
        
        # 执行重启
        stop_success = await self.stop(timeout)
        if not stop_success:
            logger.error(f"停止服务失败，重启中止: {self.config.name}")
            return False
        
        # 等待重启延迟
        if self.config.restart_delay > 0:
            await asyncio.sleep(self.config.restart_delay)
        
        start_success = await self.start()
        if start_success:
            self._restart_attempts = 0  # 重启成功，重置计数
            logger.info(f"服务重启成功: {self.config.name}")
        else:
            logger.error(f"服务重启失败: {self.config.name}")
        
        return start_success
    
    async def _change_status(self, new_status: ServiceStatus):
        """改变服务状态"""
        old_status = self._status
        self._status = new_status
        
        # 触发状态变更回调
        for callback in self._status_change_callbacks:
            try:
                callback(old_status, new_status)
            except Exception as e:
                logger.error(f"状态变更回调失败: {e}")
        
        logger.debug(f"服务状态变更: {self.config.name} {old_status.value} -> {new_status.value}")
    
    # ==================== 健康检查 ====================
    
    def _start_health_check(self):
        """启动健康检查"""
        async def health_check_loop():
            while self._status == ServiceStatus.RUNNING:
                try:
                    start_time = time.time()
                    result = await self._health_check()
                    result.response_time_ms = (time.time() - start_time) * 1000
                    
                    self._last_health_check = result
                    self._health_status = result.status
                    
                    if result.status == HealthStatus.UNHEALTHY and self.config.auto_restart:
                        logger.warning(f"健康检查失败，尝试重启服务: {self.config.name}")
                        await self.restart()
                    
                except Exception as e:
                    logger.error(f"健康检查异常: {self.config.name}, {e}")
                    self._health_status = HealthStatus.UNKNOWN
                
                await asyncio.sleep(self.config.health_check_interval)
        
        self._health_check_task = asyncio.create_task(health_check_loop())
        self._background_tasks.append(self._health_check_task)
    
    async def _stop_health_check(self):
        """停止健康检查"""
        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None
    
    async def get_health_status(self) -> HealthCheckResult:
        """
        获取健康状态
        
        Returns:
            HealthCheckResult: 健康检查结果
        """
        if self._last_health_check is None:
            # 执行一次健康检查
            try:
                start_time = time.time()
                result = await self._health_check()
                result.response_time_ms = (time.time() - start_time) * 1000
                self._last_health_check = result
                return result
            except Exception as e:
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    message=f"健康检查失败: {e}",
                    details={'error': str(e)}
                )
        
        return self._last_health_check
    
    # ==================== 并发控制 ====================
    
    @asynccontextmanager
    async def _acquire_operation_slot(self):
        """获取操作槽位（并发控制）"""
        await self._semaphore.acquire()
        self._metrics.current_concurrent_operations += 1
        
        if self._metrics.current_concurrent_operations > self._metrics.max_concurrent_operations_reached:
            self._metrics.max_concurrent_operations_reached = self._metrics.current_concurrent_operations
        
        try:
            yield
        finally:
            self._metrics.current_concurrent_operations -= 1
            self._semaphore.release()
    
    async def execute_with_metrics(self, operation: Callable[[], T], operation_name: str = "operation") -> T:
        """
        执行操作并收集指标
        
        Args:
            operation: 要执行的操作
            operation_name: 操作名称
            
        Returns:
            T: 操作结果
            
        Raises:
            ServiceError: 操作失败或超时
        """
        if self._status != ServiceStatus.RUNNING:
            raise ServiceError(f"服务未运行: {self.config.name}")
        
        async with self._acquire_operation_slot():
            start_time = time.time()
            self._metrics.total_requests += 1
            
            try:
                # 执行操作（带超时）
                if self.config.timeout_seconds > 0:
                    result = await asyncio.wait_for(operation(), timeout=self.config.timeout_seconds)
                else:
                    result = await operation()
                
                # 记录成功指标
                response_time = time.time() - start_time
                self._record_response_time(response_time)
                self._metrics.successful_requests += 1
                
                logger.debug(f"操作成功: {operation_name}, 耗时: {response_time:.3f}s")
                return result
                
            except asyncio.TimeoutError as e:
                self._metrics.failed_requests += 1
                self._metrics.total_errors += 1
                self._metrics.last_error_time = time.time()
                self._metrics.last_error_message = f"操作超时: {operation_name}"
                
                error = ServiceError(f"操作超时: {operation_name}", original_error=e)
                await self._handle_error(error)
                raise error
                
            except Exception as e:
                self._metrics.failed_requests += 1
                self._metrics.total_errors += 1
                self._metrics.last_error_time = time.time()
                self._metrics.last_error_message = str(e)
                
                error = ServiceError(f"操作失败: {operation_name}, {e}", original_error=e)
                await self._handle_error(error)
                raise error
    
    def _record_response_time(self, response_time: float):
        """记录响应时间"""
        self._response_times.append(response_time)
        
        # 限制样本数量
        if len(self._response_times) > self._max_response_time_samples:
            self._response_times = self._response_times[-self._max_response_time_samples:]
        
        # 更新平均响应时间
        self._metrics.average_response_time = sum(self._response_times) / len(self._response_times)
    
    # ==================== 任务管理 ====================
    
    def add_background_task(self, coro) -> asyncio.Task:
        """
        添加后台任务
        
        Args:
            coro: 协程对象
            
        Returns:
            asyncio.Task: 任务对象
        """
        task = asyncio.create_task(coro)
        self._background_tasks.append(task)
        return task
    
    async def _cancel_background_tasks(self):
        """取消所有后台任务"""
        for task in self._background_tasks:
            if not task.done():
                task.cancel()
        
        # 等待任务取消完成
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        self._background_tasks.clear()
    
    # ==================== 错误处理 ====================
    
    async def _handle_error(self, error: ServiceError):
        """处理错误"""
        if self.config.enable_logging:
            logger.error(f"服务错误: {self.config.name}, {error.message}")
        
        # 触发错误回调
        for callback in self._error_callbacks:
            try:
                callback(error)
            except Exception as e:
                logger.error(f"错误回调失败: {e}")
    
    # ==================== 事件回调 ====================
    
    def add_status_change_callback(self, callback: Callable[[ServiceStatus, ServiceStatus], None]):
        """添加状态变更回调"""
        self._status_change_callbacks.append(callback)
    
    def remove_status_change_callback(self, callback: Callable[[ServiceStatus, ServiceStatus], None]):
        """移除状态变更回调"""
        if callback in self._status_change_callbacks:
            self._status_change_callbacks.remove(callback)
    
    def add_error_callback(self, callback: Callable[[ServiceError], None]):
        """添加错误回调"""
        self._error_callbacks.append(callback)
    
    def remove_error_callback(self, callback: Callable[[ServiceError], None]):
        """移除错误回调"""
        if callback in self._error_callbacks:
            self._error_callbacks.remove(callback)
    
    # ==================== 状态查询 ====================
    
    @property
    def status(self) -> ServiceStatus:
        """获取服务状态"""
        return self._status
    
    @property
    def is_running(self) -> bool:
        """检查服务是否运行中"""
        return self._status == ServiceStatus.RUNNING
    
    @property
    def is_healthy(self) -> bool:
        """检查服务是否健康"""
        return self._health_status == HealthStatus.HEALTHY
    
    def get_metrics(self) -> ServiceMetrics:
        """获取服务指标"""
        return self._metrics
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        获取服务信息
        
        Returns:
            Dict[str, Any]: 服务信息
        """
        return {
            'service_id': self.service_id,
            'config': self.config.to_dict(),
            'status': self._status.value,
            'health_status': self._health_status.value,
            'metrics': self._metrics.to_dict(),
            'last_health_check': self._last_health_check.to_dict() if self._last_health_check else None,
            'restart_attempts': self._restart_attempts,
            'background_tasks_count': len(self._background_tasks)
        }
    
    # ==================== 配置管理 ====================
    
    async def update_config(self, new_config: ServiceConfig) -> bool:
        """
        更新服务配置
        
        Args:
            new_config: 新配置
            
        Returns:
            bool: 更新是否成功
        """
        try:
            old_config = self.config
            self.config = new_config
            
            # 如果并发限制改变，更新信号量
            if old_config.max_concurrent_operations != new_config.max_concurrent_operations:
                self._semaphore = asyncio.Semaphore(new_config.max_concurrent_operations)
            
            logger.info(f"服务配置已更新: {self.config.name}")
            return True
            
        except Exception as e:
            logger.error(f"更新服务配置失败: {e}")
            return False
    
    def get_config(self) -> ServiceConfig:
        """获取服务配置"""
        return self.config
    
    # ==================== 便利方法 ====================
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.stop()


# ==================== 服务管理器 ====================

class AsyncServiceManager:
    """异步服务管理器
    
    管理多个异步服务的生命周期
    """
    
    def __init__(self):
        self._services: Dict[str, BaseAsyncService] = {}
        self._service_dependencies: Dict[str, List[str]] = {}
        self._startup_order: List[str] = []
        self._shutdown_order: List[str] = []
    
    def register_service(self, service: BaseAsyncService, dependencies: Optional[List[str]] = None):
        """
        注册服务
        
        Args:
            service: 服务实例
            dependencies: 依赖的服务名称列表
        """
        service_name = service.config.name
        self._services[service_name] = service
        self._service_dependencies[service_name] = dependencies or []
        
        # 重新计算启动顺序
        self._calculate_startup_order()
        
        logger.info(f"服务已注册: {service_name}")
    
    def unregister_service(self, service_name: str) -> bool:
        """
        注销服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            bool: 注销是否成功
        """
        if service_name in self._services:
            del self._services[service_name]
            del self._service_dependencies[service_name]
            
            # 重新计算启动顺序
            self._calculate_startup_order()
            
            logger.info(f"服务已注销: {service_name}")
            return True
        
        return False
    
    def _calculate_startup_order(self):
        """计算服务启动顺序（拓扑排序）"""
        # 简单的拓扑排序实现
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(service_name: str):
            if service_name in temp_visited:
                raise ValueError(f"检测到循环依赖: {service_name}")
            
            if service_name not in visited:
                temp_visited.add(service_name)
                
                # 先访问依赖
                for dep in self._service_dependencies.get(service_name, []):
                    if dep in self._services:
                        visit(dep)
                
                temp_visited.remove(service_name)
                visited.add(service_name)
                order.append(service_name)
        
        for service_name in self._services:
            if service_name not in visited:
                visit(service_name)
        
        self._startup_order = order
        self._shutdown_order = list(reversed(order))
    
    async def start_all_services(self) -> Dict[str, bool]:
        """
        启动所有服务
        
        Returns:
            Dict[str, bool]: 各服务启动结果
        """
        results = {}
        
        for service_name in self._startup_order:
            service = self._services[service_name]
            
            if service.config.auto_start:
                logger.info(f"启动服务: {service_name}")
                results[service_name] = await service.start()
            else:
                logger.info(f"跳过自动启动: {service_name}")
                results[service_name] = True
        
        return results
    
    async def stop_all_services(self, timeout: Optional[float] = None) -> Dict[str, bool]:
        """
        停止所有服务
        
        Args:
            timeout: 停止超时时间
            
        Returns:
            Dict[str, bool]: 各服务停止结果
        """
        results = {}
        
        for service_name in self._shutdown_order:
            service = self._services[service_name]
            
            if service.is_running:
                logger.info(f"停止服务: {service_name}")
                results[service_name] = await service.stop(timeout)
            else:
                results[service_name] = True
        
        return results
    
    def get_service(self, service_name: str) -> Optional[BaseAsyncService]:
        """
        获取服务实例
        
        Args:
            service_name: 服务名称
            
        Returns:
            Optional[BaseAsyncService]: 服务实例
        """
        return self._services.get(service_name)
    
    def get_all_services(self) -> Dict[str, BaseAsyncService]:
        """
        获取所有服务
        
        Returns:
            Dict[str, BaseAsyncService]: 所有服务
        """
        return self._services.copy()
    
    def get_service_status_summary(self) -> Dict[str, Any]:
        """
        获取所有服务状态摘要
        
        Returns:
            Dict[str, Any]: 状态摘要
        """
        summary = {
            'total_services': len(self._services),
            'running_services': 0,
            'stopped_services': 0,
            'error_services': 0,
            'healthy_services': 0,
            'unhealthy_services': 0,
            'services': {}
        }
        
        for name, service in self._services.items():
            status = service.status
            health = service._health_status
            
            summary['services'][name] = {
                'status': status.value,
                'health': health.value,
                'uptime': service.get_metrics().uptime_seconds
            }
            
            # 统计计数
            if status == ServiceStatus.RUNNING:
                summary['running_services'] += 1
            elif status == ServiceStatus.STOPPED:
                summary['stopped_services'] += 1
            elif status == ServiceStatus.ERROR:
                summary['error_services'] += 1
            
            if health == HealthStatus.HEALTHY:
                summary['healthy_services'] += 1
            elif health in [HealthStatus.UNHEALTHY, HealthStatus.DEGRADED]:
                summary['unhealthy_services'] += 1
        
        return summary


# ==================== 全局服务管理器 ====================

_global_service_manager: Optional[AsyncServiceManager] = None


def get_global_service_manager() -> AsyncServiceManager:
    """
    获取全局服务管理器
    
    Returns:
        AsyncServiceManager: 全局服务管理器实例
    """
    global _global_service_manager
    if _global_service_manager is None:
        _global_service_manager = AsyncServiceManager()
    return _global_service_manager


def register_global_service(service: BaseAsyncService, dependencies: Optional[List[str]] = None):
    """
    注册全局服务
    
    Args:
        service: 服务实例
        dependencies: 依赖的服务名称列表
    """
    manager = get_global_service_manager()
    manager.register_service(service, dependencies)


async def start_all_global_services() -> Dict[str, bool]:
    """
    启动所有全局服务
    
    Returns:
        Dict[str, bool]: 各服务启动结果
    """
    manager = get_global_service_manager()
    return await manager.start_all_services()


async def stop_all_global_services(timeout: Optional[float] = None) -> Dict[str, bool]:
    """
    停止所有全局服务
    
    Args:
        timeout: 停止超时时间
        
    Returns:
        Dict[str, bool]: 各服务停止结果
    """
    manager = get_global_service_manager()
    return await manager.stop_all_services(timeout)