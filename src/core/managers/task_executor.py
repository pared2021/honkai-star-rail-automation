# -*- coding: utf-8 -*-
"""任务执行器

专门负责任务执行相关功能，包括：
- 任务执行和控制
- 执行状态管理
- 执行结果处理
- 执行环境管理
- 执行日志记录
"""

import asyncio
import os
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Set
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
import importlib
import inspect

from src.core.interfaces import ITaskExecutor, ExecutionStatus, ExecutionResult
from src.core.dependency_injection import Injectable, inject
from src.exceptions import (
    TaskExecutionError, 
    TaskValidationError, 
    TaskTimeoutError,
    TaskCancellationError
)


class TaskType(Enum):
    """任务类型"""
    PYTHON_SCRIPT = "python_script"
    SHELL_COMMAND = "shell_command"
    HTTP_REQUEST = "http_request"
    DATA_PROCESSING = "data_processing"
    MACHINE_LEARNING = "machine_learning"
    FILE_OPERATION = "file_operation"
    DATABASE_OPERATION = "database_operation"
    CUSTOM = "custom"


@dataclass
class TaskConfig:
    """任务配置"""
    task_type: TaskType
    script_path: Optional[str] = None
    command: Optional[str] = None
    function_name: Optional[str] = None
    module_path: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    timeout: Optional[timedelta] = None
    retry_count: int = 0
    retry_delay: timedelta = timedelta(seconds=5)
    resource_requirements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionContext:
    """执行上下文"""
    task_id: str
    config: TaskConfig
    start_time: datetime
    timeout: Optional[timedelta] = None
    retry_attempt: int = 0
    environment: Dict[str, Any] = field(default_factory=dict)
    resources: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionLog:
    """执行日志"""
    timestamp: datetime
    level: str
    message: str
    task_id: str
    execution_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionStats:
    """执行统计"""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    cancelled_executions: int = 0
    timeout_executions: int = 0
    retry_executions: int = 0
    average_execution_time: timedelta = timedelta()
    total_execution_time: timedelta = timedelta()


class TaskExecutor(Injectable, ITaskExecutor):
    """任务执行器
    
    提供任务执行功能：
    - 执行控制
    - 状态管理
    - 结果处理
    - 环境管理
    - 日志记录
    """
    
    def __init__(
        self,
        config_manager,
        max_concurrent_executions: int = 10,
        default_timeout: timedelta = timedelta(hours=1),
        log_retention: timedelta = timedelta(days=7)
    ):
        """初始化任务执行器
        
        Args:
            config_manager: 配置管理器
            max_concurrent_executions: 最大并发执行数
            default_timeout: 默认超时时间
            log_retention: 日志保留时间
        """
        super().__init__()
        self._config_manager = config_manager
        self._max_concurrent = self._get_config_value(
            'task_executor.max_concurrent_executions', max_concurrent_executions
        )
        self._default_timeout = timedelta(hours=self._get_config_value(
            'task_executor.default_timeout_hours', default_timeout.total_seconds() / 3600
        ))
        self._log_retention = timedelta(days=self._get_config_value(
            'task_executor.log_retention_days', log_retention.days
        ))
        
        # 执行状态跟踪
        self._running_tasks: Dict[str, ExecutionContext] = {}
        self._completed_tasks: Dict[str, ExecutionResult] = {}
        self._failed_tasks: Dict[str, ExecutionResult] = {}
        
        # 执行控制
        self._execution_semaphore = asyncio.Semaphore(max_concurrent_executions)
        self._cancellation_tokens: Dict[str, asyncio.Event] = {}
        self._pause_tokens: Dict[str, asyncio.Event] = {}
        
        # 执行回调
        self._execution_callbacks: List[Callable] = []
        
        # 执行日志
        self._execution_logs: List[ExecutionLog] = []
        
        # 统计信息
        self._stats = ExecutionStats()
        
        # 支持的任务类型
        self._supported_types: Set[TaskType] = {
            TaskType.PYTHON_SCRIPT,
            TaskType.SHELL_COMMAND,
            TaskType.HTTP_REQUEST,
            TaskType.DATA_PROCESSING,
            TaskType.FILE_OPERATION,
            TaskType.CUSTOM
        }
        
        # 任务执行器映射
        self._type_executors = {
            TaskType.PYTHON_SCRIPT: self._execute_python_script,
            TaskType.SHELL_COMMAND: self._execute_shell_command,
            TaskType.HTTP_REQUEST: self._execute_http_request,
            TaskType.DATA_PROCESSING: self._execute_data_processing,
            TaskType.FILE_OPERATION: self._execute_file_operation,
            TaskType.CUSTOM: self._execute_custom_task
        }
        
        logger.info("任务执行器初始化完成")
    
    def _get_config_value(self, key: str, default_value: Any) -> Any:
        """从配置管理器获取配置值"""
        try:
            return self._config_manager.get(key, default_value)
        except Exception:
            return default_value
    
    async def dispose(self):
        """释放资源"""
        # 取消所有运行中的任务
        for task_id in list(self._running_tasks.keys()):
            await self.cancel_task(task_id)
        
        # 清理资源
        self._running_tasks.clear()
        self._completed_tasks.clear()
        self._failed_tasks.clear()
        self._execution_callbacks.clear()
        self._cancellation_tokens.clear()
        self._pause_tokens.clear()
        self._execution_logs.clear()
    
    async def execute_task(
        self,
        task_id: str,
        config: TaskConfig,
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """执行任务
        
        Args:
            task_id: 任务ID
            config: 任务配置
            context: 执行上下文
            
        Returns:
            执行结果
            
        Raises:
            TaskExecutionError: 任务执行失败
        """
        try:
            # 验证任务配置
            if not await self.validate_task_config(config):
                raise TaskValidationError(f"任务配置验证失败: {task_id}")
            
            # 检查并发限制
            async with self._execution_semaphore:
                # 创建执行上下文
                execution_context = ExecutionContext(
                    task_id=task_id,
                    config=config,
                    start_time=datetime.now(),
                    timeout=config.timeout or self._default_timeout,
                    environment=context or {}
                )
                
                # 准备执行环境
                await self._prepare_execution_environment(execution_context)
                
                # 执行任务
                result = await self._execute_with_retry(execution_context)
                
                # 清理执行环境
                await self._cleanup_execution_environment(execution_context)
                
                return result
        
        except Exception as e:
            logger.error(f"任务执行失败: {task_id} - {e}")
            self._stats.failed_executions += 1
            
            # 记录失败结果
            result = ExecutionResult(
                task_id=task_id,
                status=ExecutionStatus.FAILED,
                error=str(e),
                start_time=datetime.now(),
                end_time=datetime.now()
            )
            self._failed_tasks[task_id] = result
            
            # 调用回调
            await self._notify_execution_callbacks(result)
            
            raise TaskExecutionError(f"任务执行失败: {task_id}") from e
    
    async def pause_task(self, task_id: str) -> bool:
        """暂停任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否暂停成功
        """
        try:
            if task_id not in self._running_tasks:
                logger.warning(f"任务未在运行: {task_id}")
                return False
            
            # 设置暂停标志
            if task_id not in self._pause_tokens:
                self._pause_tokens[task_id] = asyncio.Event()
            
            self._pause_tokens[task_id].clear()
            
            # 记录日志
            await self._log_execution(task_id, "INFO", "任务已暂停")
            
            logger.info(f"任务暂停成功: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"暂停任务失败: {task_id} - {e}")
            return False
    
    async def resume_task(self, task_id: str) -> bool:
        """恢复任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否恢复成功
        """
        try:
            if task_id not in self._running_tasks:
                logger.warning(f"任务未在运行: {task_id}")
                return False
            
            # 清除暂停标志
            if task_id in self._pause_tokens:
                self._pause_tokens[task_id].set()
            
            # 记录日志
            await self._log_execution(task_id, "INFO", "任务已恢复")
            
            logger.info(f"任务恢复成功: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"恢复任务失败: {task_id} - {e}")
            return False
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否取消成功
        """
        try:
            if task_id not in self._running_tasks:
                logger.warning(f"任务未在运行: {task_id}")
                return False
            
            # 设置取消标志
            if task_id not in self._cancellation_tokens:
                self._cancellation_tokens[task_id] = asyncio.Event()
            
            self._cancellation_tokens[task_id].set()
            
            # 记录日志
            await self._log_execution(task_id, "INFO", "任务已取消")
            
            # 更新统计
            self._stats.cancelled_executions += 1
            
            logger.info(f"任务取消成功: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"取消任务失败: {task_id} - {e}")
            return False
    
    async def get_execution_status(self, task_id: str) -> Optional[ExecutionStatus]:
        """获取执行状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            执行状态
        """
        # 检查运行中任务
        if task_id in self._running_tasks:
            # 检查是否暂停
            if (task_id in self._pause_tokens and 
                not self._pause_tokens[task_id].is_set()):
                return ExecutionStatus.PAUSED
            return ExecutionStatus.RUNNING
        
        # 检查已完成任务
        if task_id in self._completed_tasks:
            return self._completed_tasks[task_id].status
        
        # 检查失败任务
        if task_id in self._failed_tasks:
            return self._failed_tasks[task_id].status
        
        return None
    
    async def get_execution_result(self, task_id: str) -> Optional[ExecutionResult]:
        """获取执行结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            执行结果
        """
        # 检查已完成任务
        if task_id in self._completed_tasks:
            return self._completed_tasks[task_id]
        
        # 检查失败任务
        if task_id in self._failed_tasks:
            return self._failed_tasks[task_id]
        
        # 检查运行中任务
        if task_id in self._running_tasks:
            context = self._running_tasks[task_id]
            return ExecutionResult(
                task_id=task_id,
                status=ExecutionStatus.RUNNING,
                start_time=context.start_time,
                metadata=context.metadata
            )
        
        return None
    
    async def get_running_tasks(self) -> List[str]:
        """获取运行中任务列表
        
        Returns:
            运行中任务ID列表
        """
        return list(self._running_tasks.keys())
    
    async def get_completed_tasks(self) -> List[str]:
        """获取已完成任务列表
        
        Returns:
            已完成任务ID列表
        """
        return list(self._completed_tasks.keys())
    
    async def get_failed_tasks(self) -> List[str]:
        """获取失败任务列表
        
        Returns:
            失败任务ID列表
        """
        return list(self._failed_tasks.keys())
    
    async def set_execution_callback(self, callback: Callable) -> bool:
        """设置执行回调
        
        Args:
            callback: 回调函数
            
        Returns:
            是否设置成功
        """
        try:
            if callback not in self._execution_callbacks:
                self._execution_callbacks.append(callback)
            return True
        except Exception as e:
            logger.error(f"设置执行回调失败: {e}")
            return False
    
    async def remove_execution_callback(self, callback: Callable) -> bool:
        """移除执行回调
        
        Args:
            callback: 回调函数
            
        Returns:
            是否移除成功
        """
        try:
            if callback in self._execution_callbacks:
                self._execution_callbacks.remove(callback)
            return True
        except Exception as e:
            logger.error(f"移除执行回调失败: {e}")
            return False
    
    async def get_execution_statistics(self) -> ExecutionStats:
        """获取执行统计信息
        
        Returns:
            执行统计信息
        """
        # 更新平均执行时间
        if self._stats.total_executions > 0:
            self._stats.average_execution_time = (
                self._stats.total_execution_time / self._stats.total_executions
            )
        
        return self._stats
    
    async def clear_completed_tasks(self) -> bool:
        """清理已完成任务
        
        Returns:
            是否清理成功
        """
        try:
            self._completed_tasks.clear()
            logger.info("已完成任务已清理")
            return True
        except Exception as e:
            logger.error(f"清理已完成任务失败: {e}")
            return False
    
    async def clear_failed_tasks(self) -> bool:
        """清理失败任务
        
        Returns:
            是否清理成功
        """
        try:
            self._failed_tasks.clear()
            logger.info("失败任务已清理")
            return True
        except Exception as e:
            logger.error(f"清理失败任务失败: {e}")
            return False
    
    async def validate_task_config(self, config: TaskConfig) -> bool:
        """验证任务配置
        
        Args:
            config: 任务配置
            
        Returns:
            是否验证通过
        """
        try:
            # 检查任务类型
            if config.task_type not in self._supported_types:
                logger.error(f"不支持的任务类型: {config.task_type}")
                return False
            
            # 检查必需参数
            if config.task_type == TaskType.PYTHON_SCRIPT:
                if not config.script_path and not config.module_path:
                    logger.error("Python脚本任务需要script_path或module_path")
                    return False
            
            elif config.task_type == TaskType.SHELL_COMMAND:
                if not config.command:
                    logger.error("Shell命令任务需要command")
                    return False
            
            elif config.task_type == TaskType.CUSTOM:
                if not config.module_path or not config.function_name:
                    logger.error("自定义任务需要module_path和function_name")
                    return False
            
            # 检查超时设置
            if config.timeout and config.timeout <= timedelta(0):
                logger.error("超时时间必须大于0")
                return False
            
            # 检查重试设置
            if config.retry_count < 0:
                logger.error("重试次数不能为负数")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证任务配置失败: {e}")
            return False
    
    async def get_supported_task_types(self) -> List[TaskType]:
        """获取支持的任务类型
        
        Returns:
            支持的任务类型列表
        """
        return list(self._supported_types)
    
    async def prepare_execution_environment(
        self,
        task_id: str,
        config: TaskConfig
    ) -> bool:
        """准备执行环境
        
        Args:
            task_id: 任务ID
            config: 任务配置
            
        Returns:
            是否准备成功
        """
        try:
            context = ExecutionContext(
                task_id=task_id,
                config=config,
                start_time=datetime.now()
            )
            
            await self._prepare_execution_environment(context)
            return True
            
        except Exception as e:
            logger.error(f"准备执行环境失败: {task_id} - {e}")
            return False
    
    async def cleanup_execution_environment(self, task_id: str) -> bool:
        """清理执行环境
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否清理成功
        """
        try:
            if task_id in self._running_tasks:
                context = self._running_tasks[task_id]
                await self._cleanup_execution_environment(context)
            
            # 清理控制令牌
            self._cancellation_tokens.pop(task_id, None)
            self._pause_tokens.pop(task_id, None)
            
            return True
            
        except Exception as e:
            logger.error(f"清理执行环境失败: {task_id} - {e}")
            return False
    
    async def get_execution_logs(
        self,
        task_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[ExecutionLog]:
        """获取执行日志
        
        Args:
            task_id: 任务ID（可选）
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
            
        Returns:
            执行日志列表
        """
        logs = self._execution_logs
        
        # 按任务ID过滤
        if task_id:
            logs = [log for log in logs if log.task_id == task_id]
        
        # 按时间过滤
        if start_time:
            logs = [log for log in logs if log.timestamp >= start_time]
        
        if end_time:
            logs = [log for log in logs if log.timestamp <= end_time]
        
        return logs
    
    async def get_task_resource_usage(self, task_id: str) -> Dict[str, Any]:
        """获取任务资源使用情况
        
        Args:
            task_id: 任务ID
            
        Returns:
            资源使用情况
        """
        if task_id in self._running_tasks:
            context = self._running_tasks[task_id]
            return context.resources
        
        return {}
    
    # 私有方法
    
    async def _execute_with_retry(self, context: ExecutionContext) -> ExecutionResult:
        """带重试的执行"""
        last_error = None
        
        for attempt in range(context.config.retry_count + 1):
            try:
                context.retry_attempt = attempt
                
                # 记录开始执行
                self._running_tasks[context.task_id] = context
                await self._log_execution(
                    context.task_id, 
                    "INFO", 
                    f"开始执行任务 (尝试 {attempt + 1}/{context.config.retry_count + 1})"
                )
                
                # 执行任务
                result = await self._execute_task_by_type(context)
                
                # 记录成功
                self._running_tasks.pop(context.task_id, None)
                self._completed_tasks[context.task_id] = result
                self._stats.successful_executions += 1
                
                # 更新执行时间统计
                execution_time = result.end_time - result.start_time
                self._stats.total_execution_time += execution_time
                self._stats.total_executions += 1
                
                await self._log_execution(context.task_id, "INFO", "任务执行成功")
                await self._notify_execution_callbacks(result)
                
                return result
                
            except asyncio.CancelledError:
                # 任务被取消
                self._running_tasks.pop(context.task_id, None)
                result = ExecutionResult(
                    task_id=context.task_id,
                    status=ExecutionStatus.CANCELLED,
                    start_time=context.start_time,
                    end_time=datetime.now(),
                    error="任务被取消"
                )
                self._failed_tasks[context.task_id] = result
                await self._notify_execution_callbacks(result)
                raise TaskCancellationError(f"任务被取消: {context.task_id}")
                
            except Exception as e:
                last_error = e
                await self._log_execution(
                    context.task_id, 
                    "ERROR", 
                    f"执行失败 (尝试 {attempt + 1}): {str(e)}"
                )
                
                # 如果还有重试机会，等待后重试
                if attempt < context.config.retry_count:
                    self._stats.retry_executions += 1
                    await asyncio.sleep(context.config.retry_delay.total_seconds())
                    continue
                
                # 所有重试都失败了
                self._running_tasks.pop(context.task_id, None)
                result = ExecutionResult(
                    task_id=context.task_id,
                    status=ExecutionStatus.FAILED,
                    start_time=context.start_time,
                    end_time=datetime.now(),
                    error=str(e)
                )
                self._failed_tasks[context.task_id] = result
                await self._notify_execution_callbacks(result)
                raise e
        
        # 不应该到达这里
        raise TaskExecutionError(f"任务执行失败: {context.task_id}")
    
    async def _execute_task_by_type(self, context: ExecutionContext) -> ExecutionResult:
        """根据类型执行任务"""
        task_type = context.config.task_type
        
        if task_type not in self._type_executors:
            raise TaskExecutionError(f"不支持的任务类型: {task_type}")
        
        executor = self._type_executors[task_type]
        
        # 设置超时
        timeout = context.timeout or self._default_timeout
        
        try:
            result = await asyncio.wait_for(
                executor(context),
                timeout=timeout.total_seconds()
            )
            return result
            
        except asyncio.TimeoutError:
            self._stats.timeout_executions += 1
            raise TaskTimeoutError(f"任务执行超时: {context.task_id}")
    
    async def _execute_python_script(self, context: ExecutionContext) -> ExecutionResult:
        """执行Python脚本"""
        config = context.config
        start_time = datetime.now()
        
        try:
            if config.script_path:
                # 执行脚本文件
                with open(config.script_path, 'r', encoding='utf-8') as f:
                    script_content = f.read()
                
                # 创建执行环境
                exec_globals = {
                    '__name__': '__main__',
                    '__file__': config.script_path,
                    **context.environment
                }
                exec_globals.update(config.parameters)
                
                # 执行脚本
                exec(script_content, exec_globals)
                result_data = exec_globals.get('result', None)
                
            elif config.module_path and config.function_name:
                # 执行模块函数
                module = importlib.import_module(config.module_path)
                func = getattr(module, config.function_name)
                
                # 检查函数签名
                sig = inspect.signature(func)
                if asyncio.iscoroutinefunction(func):
                    result_data = await func(**config.parameters)
                else:
                    result_data = func(**config.parameters)
            
            else:
                raise TaskExecutionError("Python任务需要script_path或module_path+function_name")
            
            return ExecutionResult(
                task_id=context.task_id,
                status=ExecutionStatus.COMPLETED,
                result=result_data,
                start_time=start_time,
                end_time=datetime.now()
            )
            
        except Exception as e:
            raise TaskExecutionError(f"Python脚本执行失败: {str(e)}") from e
    
    async def _execute_shell_command(self, context: ExecutionContext) -> ExecutionResult:
        """执行Shell命令"""
        config = context.config
        start_time = datetime.now()
        
        try:
            # 创建子进程
            process = await asyncio.create_subprocess_shell(
                config.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, **config.environment}
            )
            
            # 等待执行完成
            stdout, stderr = await process.communicate()
            
            # 检查返回码
            if process.returncode != 0:
                raise TaskExecutionError(
                    f"命令执行失败 (返回码: {process.returncode}): {stderr.decode()}"
                )
            
            return ExecutionResult(
                task_id=context.task_id,
                status=ExecutionStatus.COMPLETED,
                result={
                    'stdout': stdout.decode(),
                    'stderr': stderr.decode(),
                    'returncode': process.returncode
                },
                start_time=start_time,
                end_time=datetime.now()
            )
            
        except Exception as e:
            raise TaskExecutionError(f"Shell命令执行失败: {str(e)}") from e
    
    async def _execute_http_request(self, context: ExecutionContext) -> ExecutionResult:
        """执行HTTP请求"""
        # 这里需要实现HTTP请求逻辑
        # 为了简化，暂时返回模拟结果
        start_time = datetime.now()
        
        return ExecutionResult(
            task_id=context.task_id,
            status=ExecutionStatus.COMPLETED,
            result={'message': 'HTTP请求执行完成'},
            start_time=start_time,
            end_time=datetime.now()
        )
    
    async def _execute_data_processing(self, context: ExecutionContext) -> ExecutionResult:
        """执行数据处理任务"""
        # 这里需要实现数据处理逻辑
        # 为了简化，暂时返回模拟结果
        start_time = datetime.now()
        
        return ExecutionResult(
            task_id=context.task_id,
            status=ExecutionStatus.COMPLETED,
            result={'message': '数据处理任务执行完成'},
            start_time=start_time,
            end_time=datetime.now()
        )
    
    async def _execute_file_operation(self, context: ExecutionContext) -> ExecutionResult:
        """执行文件操作任务"""
        # 这里需要实现文件操作逻辑
        # 为了简化，暂时返回模拟结果
        start_time = datetime.now()
        
        return ExecutionResult(
            task_id=context.task_id,
            status=ExecutionStatus.COMPLETED,
            result={'message': '文件操作任务执行完成'},
            start_time=start_time,
            end_time=datetime.now()
        )
    
    async def _execute_custom_task(self, context: ExecutionContext) -> ExecutionResult:
        """执行自定义任务"""
        config = context.config
        start_time = datetime.now()
        
        try:
            # 动态导入模块
            module = importlib.import_module(config.module_path)
            func = getattr(module, config.function_name)
            
            # 执行函数
            if asyncio.iscoroutinefunction(func):
                result_data = await func(context, **config.parameters)
            else:
                result_data = func(context, **config.parameters)
            
            return ExecutionResult(
                task_id=context.task_id,
                status=ExecutionStatus.COMPLETED,
                result=result_data,
                start_time=start_time,
                end_time=datetime.now()
            )
            
        except Exception as e:
            raise TaskExecutionError(f"自定义任务执行失败: {str(e)}") from e
    
    async def _prepare_execution_environment(self, context: ExecutionContext):
        """准备执行环境"""
        try:
            # 设置环境变量
            context.environment.update(context.config.environment)
            
            # 初始化资源
            context.resources = {
                'cpu_usage': 0.0,
                'memory_usage': 0,
                'start_time': context.start_time
            }
            
            # 创建控制令牌
            self._cancellation_tokens[context.task_id] = asyncio.Event()
            self._pause_tokens[context.task_id] = asyncio.Event()
            self._pause_tokens[context.task_id].set()  # 默认不暂停
            
            await self._log_execution(context.task_id, "INFO", "执行环境准备完成")
            
        except Exception as e:
            raise TaskExecutionError(f"准备执行环境失败: {str(e)}") from e
    
    async def _cleanup_execution_environment(self, context: ExecutionContext):
        """清理执行环境"""
        try:
            # 清理控制令牌
            self._cancellation_tokens.pop(context.task_id, None)
            self._pause_tokens.pop(context.task_id, None)
            
            # 清理资源
            context.resources.clear()
            
            await self._log_execution(context.task_id, "INFO", "执行环境清理完成")
            
        except Exception as e:
            logger.error(f"清理执行环境失败: {context.task_id} - {e}")
    
    async def _log_execution(
        self,
        task_id: str,
        level: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """记录执行日志"""
        log = ExecutionLog(
            timestamp=datetime.now(),
            level=level,
            message=message,
            task_id=task_id,
            metadata=metadata or {}
        )
        
        self._execution_logs.append(log)
        
        # 清理过期日志
        cutoff_time = datetime.now() - self._log_retention
        self._execution_logs = [
            log for log in self._execution_logs 
            if log.timestamp > cutoff_time
        ]
    
    async def _notify_execution_callbacks(self, result: ExecutionResult):
        """通知执行回调"""
        for callback in self._execution_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(result)
                else:
                    callback(result)
            except Exception as e:
                logger.error(f"执行回调失败: {callback} - {e}")
    
    async def _check_cancellation(self, task_id: str):
        """检查取消状态"""
        if (task_id in self._cancellation_tokens and 
            self._cancellation_tokens[task_id].is_set()):
            raise asyncio.CancelledError(f"任务被取消: {task_id}")
    
    async def _check_pause(self, task_id: str):
        """检查暂停状态"""
        if task_id in self._pause_tokens:
            await self._pause_tokens[task_id].wait()