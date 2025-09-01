# -*- coding: utf-8 -*-
"""
同步适配器
连接GUI线程和异步世界，解决异步同步混用的问题
"""

import asyncio
import threading
import queue
import time
from typing import Any, Callable, Optional, Dict, List, Union, TypeVar, Generic
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

from loguru import logger
from src.exceptions import SyncAdapterError, AsyncTaskError, CallbackError

T = TypeVar('T')


class AdapterStatus(Enum):
    """适配器状态"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class CallbackType(Enum):
    """回调类型"""
    SUCCESS = "success"
    ERROR = "error"
    PROGRESS = "progress"
    COMPLETE = "complete"


@dataclass
class AsyncResult(Generic[T]):
    """异步结果包装"""
    task_id: str
    result: Optional[T] = None
    error: Optional[Exception] = None
    is_completed: bool = False
    is_success: bool = False
    progress: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'result': self.result,
            'error': str(self.error) if self.error else None,
            'is_completed': self.is_completed,
            'is_success': self.is_success,
            'progress': self.progress,
            'metadata': self.metadata
        }


@dataclass
class CallbackInfo:
    """回调信息"""
    callback_id: str
    callback_type: CallbackType
    callback_func: Callable
    task_id: Optional[str] = None
    active: bool = True





class SyncAdapter:
    """同步适配器
    
    提供GUI线程和异步世界之间的桥梁，解决以下问题：
    1. 在GUI线程中调用异步函数
    2. 异步函数结果的同步等待
    3. 异步任务的进度回调
    4. 异步任务的错误处理
    5. 异步任务的取消和超时
    """
    
    def __init__(self, max_workers: int = 4, callback_queue_size: int = 1000):
        """
        初始化同步适配器
        
        Args:
            max_workers: 最大工作线程数
            callback_queue_size: 回调队列大小
        """
        self.max_workers = max_workers
        self.callback_queue_size = callback_queue_size
        
        # 状态管理
        self._status = AdapterStatus.STOPPED
        self._lock = threading.RLock()
        
        # 事件循环和线程
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._executor: Optional[ThreadPoolExecutor] = None
        
        # 任务管理
        self._tasks: Dict[str, asyncio.Task] = {}
        self._results: Dict[str, AsyncResult] = {}
        self._task_counter = 0
        
        # 回调管理
        self._callbacks: Dict[str, CallbackInfo] = {}
        self._callback_queue: queue.Queue = queue.Queue(maxsize=callback_queue_size)
        self._callback_thread: Optional[threading.Thread] = None
        
        # 统计信息
        self._stats = {
            'tasks_created': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'tasks_cancelled': 0,
            'callbacks_executed': 0,
            'callbacks_failed': 0
        }
        
        logger.info(f"同步适配器初始化完成，最大工作线程: {max_workers}")
    
    # ==================== 生命周期管理 ====================
    
    def start(self) -> bool:
        """
        启动同步适配器
        
        Returns:
            bool: 启动是否成功
        """
        with self._lock:
            if self._status == AdapterStatus.RUNNING:
                logger.warning("同步适配器已经在运行")
                return True
            
            if self._status == AdapterStatus.STARTING:
                logger.warning("同步适配器正在启动中")
                return False
            
            try:
                self._status = AdapterStatus.STARTING
                
                # 启动事件循环线程
                self._start_event_loop()
                
                # 启动线程池
                self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
                
                # 启动回调处理线程
                self._start_callback_thread()
                
                self._status = AdapterStatus.RUNNING
                logger.info("同步适配器启动成功")
                return True
                
            except Exception as e:
                self._status = AdapterStatus.ERROR
                logger.error(f"同步适配器启动失败: {e}")
                return False
    
    def stop(self, timeout: float = 5.0) -> bool:
        """
        停止同步适配器
        
        Args:
            timeout: 停止超时时间
            
        Returns:
            bool: 停止是否成功
        """
        with self._lock:
            if self._status == AdapterStatus.STOPPED:
                return True
            
            if self._status == AdapterStatus.STOPPING:
                logger.warning("同步适配器正在停止中")
                return False
            
            try:
                self._status = AdapterStatus.STOPPING
                
                # 取消所有任务
                self._cancel_all_tasks()
                
                # 停止回调处理线程
                self._stop_callback_thread(timeout)
                
                # 停止线程池
                if self._executor:
                    self._executor.shutdown(wait=True, timeout=timeout)
                    self._executor = None
                
                # 停止事件循环线程
                self._stop_event_loop(timeout)
                
                # 清理资源
                self._cleanup()
                
                self._status = AdapterStatus.STOPPED
                logger.info("同步适配器停止成功")
                return True
                
            except Exception as e:
                self._status = AdapterStatus.ERROR
                logger.error(f"同步适配器停止失败: {e}")
                return False
    
    def _start_event_loop(self):
        """启动事件循环线程"""
        def run_loop():
            try:
                # 创建新的事件循环
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
                
                logger.debug("事件循环线程已启动")
                self._loop.run_forever()
                
            except Exception as e:
                logger.error(f"事件循环线程异常: {e}")
            finally:
                logger.debug("事件循环线程已停止")
        
        self._loop_thread = threading.Thread(target=run_loop, daemon=True)
        self._loop_thread.start()
        
        # 等待事件循环启动
        timeout = 5.0
        start_time = time.time()
        while self._loop is None and (time.time() - start_time) < timeout:
            time.sleep(0.01)
        
        if self._loop is None:
            raise SyncAdapterError("事件循环启动超时")
    
    def _stop_event_loop(self, timeout: float):
        """停止事件循环线程"""
        if self._loop and self._loop.is_running():
            # 停止事件循环
            self._loop.call_soon_threadsafe(self._loop.stop)
        
        # 等待线程结束
        if self._loop_thread and self._loop_thread.is_alive():
            self._loop_thread.join(timeout=timeout)
            
            if self._loop_thread.is_alive():
                logger.warning("事件循环线程停止超时")
        
        self._loop = None
        self._loop_thread = None
    
    def _start_callback_thread(self):
        """启动回调处理线程"""
        def process_callbacks():
            logger.debug("回调处理线程已启动")
            
            while self._status == AdapterStatus.RUNNING or self._status == AdapterStatus.STARTING:
                try:
                    # 获取回调任务（带超时）
                    try:
                        callback_task = self._callback_queue.get(timeout=1.0)
                    except queue.Empty:
                        continue
                    
                    # 执行回调
                    self._execute_callback(callback_task)
                    
                    # 标记任务完成
                    self._callback_queue.task_done()
                    
                except Exception as e:
                    logger.error(f"回调处理线程异常: {e}")
            
            logger.debug("回调处理线程已停止")
        
        self._callback_thread = threading.Thread(target=process_callbacks, daemon=True)
        self._callback_thread.start()
    
    def _stop_callback_thread(self, timeout: float):
        """停止回调处理线程"""
        # 等待队列中的回调处理完成
        try:
            self._callback_queue.join()
        except Exception as e:
            logger.warning(f"等待回调队列完成失败: {e}")
        
        # 等待线程结束
        if self._callback_thread and self._callback_thread.is_alive():
            self._callback_thread.join(timeout=timeout)
            
            if self._callback_thread.is_alive():
                logger.warning("回调处理线程停止超时")
        
        self._callback_thread = None
    
    def _cleanup(self):
        """清理资源"""
        self._tasks.clear()
        self._results.clear()
        self._callbacks.clear()
        
        # 清空回调队列
        while not self._callback_queue.empty():
            try:
                self._callback_queue.get_nowait()
            except queue.Empty:
                break
    
    # ==================== 异步任务执行 ====================
    
    def execute_async(
        self,
        callback_func: Callable,
        success_callback: Optional[Callable] = None,
        error_callback: Optional[Callable] = None,
        timeout: Optional[float] = None
    ) -> str:
        """
        执行异步回调函数
        
        Args:
            callback_func: 要执行的回调函数
            success_callback: 成功回调函数
            error_callback: 错误回调函数
            timeout: 超时时间
            
        Returns:
            str: 任务ID
        """
        async def async_wrapper():
            """异步包装器"""
            try:
                # 如果callback_func是异步函数，直接await
                if asyncio.iscoroutinefunction(callback_func):
                    result = await callback_func()
                else:
                    # 如果是同步函数，在线程池中执行
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, callback_func)
                
                # 调用成功回调
                if success_callback:
                    if asyncio.iscoroutinefunction(success_callback):
                        await success_callback(result)
                    else:
                        success_callback(result)
                
                return result
                
            except Exception as e:
                # 调用错误回调
                if error_callback:
                    if asyncio.iscoroutinefunction(error_callback):
                        await error_callback(e)
                    else:
                        error_callback(e)
                raise
        
        return self.run_async(async_wrapper, timeout=timeout)
    
    def run_async(
        self,
        coro_func: Callable,
        *args,
        timeout: Optional[float] = None,
        callback: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None,
        **kwargs
    ) -> str:
        """
        运行异步函数（非阻塞）
        
        Args:
            coro_func: 异步函数
            *args: 位置参数
            timeout: 超时时间
            callback: 完成回调
            progress_callback: 进度回调
            **kwargs: 关键字参数
            
        Returns:
            str: 任务ID
            
        Raises:
            SyncAdapterError: 适配器未运行或其他错误
        """
        if self._status != AdapterStatus.RUNNING:
            raise SyncAdapterError("Sync adapter is not running")
        
        # 生成任务ID
        with self._lock:
            self._task_counter += 1
            task_id = f"task_{self._task_counter}_{int(time.time() * 1000)}"
        
        # 创建异步结果对象
        result = AsyncResult[Any](task_id=task_id)
        self._results[task_id] = result
        
        # 注册回调
        if callback:
            self.register_callback(task_id, CallbackType.COMPLETE, callback)
        if progress_callback:
            self.register_callback(task_id, CallbackType.PROGRESS, progress_callback)
        
        # 创建异步任务
        async def task_wrapper():
            try:
                # 执行异步函数
                if asyncio.iscoroutinefunction(coro_func):
                    coro_result = await coro_func(*args, **kwargs)
                else:
                    # 如果不是协程函数，在线程池中执行
                    coro_result = await self._loop.run_in_executor(
                        self._executor, coro_func, *args, **kwargs
                    )
                
                # 更新结果
                result.result = coro_result
                result.is_completed = True
                result.is_success = True
                result.progress = 1.0
                
                # 触发成功回调
                self._trigger_callback(task_id, CallbackType.SUCCESS, result)
                self._trigger_callback(task_id, CallbackType.COMPLETE, result)
                
                self._stats['tasks_completed'] += 1
                logger.debug(f"异步任务完成: {task_id}")
                
            except asyncio.CancelledError:
                result.is_completed = True
                result.is_success = False
                result.error = AsyncTaskError("Task was cancelled")
                
                self._stats['tasks_cancelled'] += 1
                logger.debug(f"异步任务被取消: {task_id}")
                raise
                
            except Exception as e:
                result.error = e
                result.is_completed = True
                result.is_success = False
                
                # 触发错误回调
                self._trigger_callback(task_id, CallbackType.ERROR, result)
                self._trigger_callback(task_id, CallbackType.COMPLETE, result)
                
                self._stats['tasks_failed'] += 1
                logger.error(f"异步任务失败: {task_id}, {e}")
        
        # 提交任务到事件循环
        future = asyncio.run_coroutine_threadsafe(task_wrapper(), self._loop)
        
        # 设置超时
        if timeout:
            def timeout_callback():
                if not future.done():
                    future.cancel()
                    logger.warning(f"异步任务超时: {task_id}")
            
            timer = threading.Timer(timeout, timeout_callback)
            timer.start()
        
        # 保存任务引用
        self._tasks[task_id] = future
        self._stats['tasks_created'] += 1
        
        logger.debug(f"异步任务已创建: {task_id}")
        return task_id
    
    def run_async_sync(
        self,
        coro_func: Callable,
        *args,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Any:
        """
        运行异步函数（阻塞等待结果）
        
        Args:
            coro_func: 异步函数
            *args: 位置参数
            timeout: 超时时间
            **kwargs: 关键字参数
            
        Returns:
            Any: 异步函数的返回值
            
        Raises:
            SyncAdapterError: 适配器未运行或其他错误
            AsyncTaskError: 异步任务执行失败
            TimeoutError: 任务超时
        """
        task_id = self.run_async(coro_func, *args, timeout=timeout, **kwargs)
        return self.wait_for_result(task_id, timeout=timeout)
    
    def wait_for_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """
        等待异步任务结果
        
        Args:
            task_id: 任务ID
            timeout: 超时时间
            
        Returns:
            Any: 任务结果
            
        Raises:
            AsyncTaskError: 任务不存在或执行失败
            TimeoutError: 等待超时
        """
        if task_id not in self._tasks:
            raise AsyncTaskError(f"Task not found: {task_id}")
        
        future = self._tasks[task_id]
        
        try:
            # 等待任务完成
            future.result(timeout=timeout)
            
            # 获取结果
            result = self._results.get(task_id)
            if result is None:
                raise AsyncTaskError(f"Result not found: {task_id}")
            
            if result.error:
                raise AsyncTaskError(f"Task failed: {result.error}", result.error)
            
            return result.result
            
        except asyncio.TimeoutError:
            raise TimeoutError(f"Task timeout: {task_id}")
        except Exception as e:
            if isinstance(e, (AsyncTaskError, TimeoutError)):
                raise
            raise AsyncTaskError(f"Wait for result failed: {e}", e)
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消异步任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 取消是否成功
        """
        if task_id not in self._tasks:
            logger.warning(f"任务不存在: {task_id}")
            return False
        
        future = self._tasks[task_id]
        success = future.cancel()
        
        if success:
            logger.info(f"任务已取消: {task_id}")
        else:
            logger.warning(f"任务取消失败: {task_id}")
        
        return success
    
    def _cancel_all_tasks(self):
        """取消所有任务"""
        for task_id, future in self._tasks.items():
            if not future.done():
                future.cancel()
                logger.debug(f"取消任务: {task_id}")
    
    # ==================== 回调管理 ====================
    
    def register_callback(
        self,
        task_id: str,
        callback_type: CallbackType,
        callback_func: Callable,
        callback_id: Optional[str] = None
    ) -> str:
        """
        注册回调函数
        
        Args:
            task_id: 任务ID
            callback_type: 回调类型
            callback_func: 回调函数
            callback_id: 回调ID（可选）
            
        Returns:
            str: 回调ID
        """
        if callback_id is None:
            callback_id = f"callback_{len(self._callbacks)}_{int(time.time() * 1000)}"
        
        callback_info = CallbackInfo(
            callback_id=callback_id,
            callback_type=callback_type,
            callback_func=callback_func,
            task_id=task_id
        )
        
        self._callbacks[callback_id] = callback_info
        logger.debug(f"回调已注册: {callback_id} for task {task_id}")
        return callback_id
    
    def unregister_callback(self, callback_id: str) -> bool:
        """
        注销回调函数
        
        Args:
            callback_id: 回调ID
            
        Returns:
            bool: 注销是否成功
        """
        if callback_id in self._callbacks:
            del self._callbacks[callback_id]
            logger.debug(f"回调已注销: {callback_id}")
            return True
        
        logger.warning(f"回调不存在: {callback_id}")
        return False
    
    def _trigger_callback(self, task_id: str, callback_type: CallbackType, result: AsyncResult):
        """触发回调"""
        # 查找匹配的回调
        matching_callbacks = [
            cb for cb in self._callbacks.values()
            if cb.task_id == task_id and cb.callback_type == callback_type and cb.active
        ]
        
        for callback_info in matching_callbacks:
            try:
                # 添加到回调队列
                callback_task = (callback_info, result)
                self._callback_queue.put_nowait(callback_task)
                
            except queue.Full:
                logger.warning(f"回调队列已满，丢弃回调: {callback_info.callback_id}")
    
    def _execute_callback(self, callback_task):
        """执行回调"""
        callback_info, result = callback_task
        
        try:
            self._stats['callbacks_executed'] += 1
            
            # 执行回调函数
            callback_info.callback_func(result)
            
            logger.debug(f"回调执行成功: {callback_info.callback_id}")
            
        except Exception as e:
            self._stats['callbacks_failed'] += 1
            logger.error(f"回调执行失败: {callback_info.callback_id}, {e}")
    
    # ==================== 任务查询 ====================
    
    def get_task_status(self, task_id: str) -> Optional[AsyncResult]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[AsyncResult]: 任务结果，如果任务不存在则返回None
        """
        return self._results.get(task_id)
    
    def is_task_completed(self, task_id: str) -> bool:
        """
        检查任务是否完成
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 任务是否完成
        """
        result = self._results.get(task_id)
        return result.is_completed if result else False
    
    def is_task_running(self, task_id: str) -> bool:
        """
        检查任务是否正在运行
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 任务是否正在运行
        """
        if task_id not in self._tasks:
            return False
        
        future = self._tasks[task_id]
        return not future.done()
    
    def get_running_tasks(self) -> List[str]:
        """
        获取正在运行的任务列表
        
        Returns:
            List[str]: 正在运行的任务ID列表
        """
        return [
            task_id for task_id, future in self._tasks.items()
            if not future.done()
        ]
    
    def get_completed_tasks(self) -> List[str]:
        """
        获取已完成的任务列表
        
        Returns:
            List[str]: 已完成的任务ID列表
        """
        return [
            task_id for task_id, result in self._results.items()
            if result.is_completed
        ]
    
    # ==================== 统计和监控 ====================
    
    def get_status(self) -> AdapterStatus:
        """
        获取适配器状态
        
        Returns:
            AdapterStatus: 适配器状态
        """
        return self._status
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'status': self._status.value,
            'max_workers': self.max_workers,
            'running_tasks': len(self.get_running_tasks()),
            'completed_tasks': len(self.get_completed_tasks()),
            'total_callbacks': len(self._callbacks),
            'callback_queue_size': self._callback_queue.qsize(),
            'stats': self._stats.copy()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            Dict[str, Any]: 健康状态信息
        """
        try:
            is_healthy = (
                self._status == AdapterStatus.RUNNING and
                self._loop is not None and
                self._loop.is_running() and
                self._loop_thread is not None and
                self._loop_thread.is_alive() and
                self._callback_thread is not None and
                self._callback_thread.is_alive()
            )
            
            status = 'healthy' if is_healthy else 'unhealthy'
            
            return {
                'status': status,
                'message': 'Sync adapter health check',
                'details': {
                    'adapter_status': self._status.value,
                    'loop_running': self._loop.is_running() if self._loop else False,
                    'loop_thread_alive': self._loop_thread.is_alive() if self._loop_thread else False,
                    'callback_thread_alive': self._callback_thread.is_alive() if self._callback_thread else False,
                    'running_tasks': len(self.get_running_tasks()),
                    'callback_queue_size': self._callback_queue.qsize(),
                    'stats': self._stats
                }
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Health check failed: {e}',
                'details': {
                    'error': str(e),
                    'adapter_status': self._status.value
                }
            }
    
    def clear_completed_tasks(self, max_age_seconds: Optional[float] = None):
        """
        清理已完成的任务
        
        Args:
            max_age_seconds: 最大保留时间（秒），None表示清理所有已完成任务
        """
        current_time = time.time()
        tasks_to_remove = []
        
        for task_id, result in self._results.items():
            if not result.is_completed:
                continue
            
            if max_age_seconds is None:
                tasks_to_remove.append(task_id)
            else:
                task_age = current_time - result.metadata.get('start_time', current_time)
                if task_age > max_age_seconds:
                    tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            if task_id in self._tasks:
                del self._tasks[task_id]
            if task_id in self._results:
                del self._results[task_id]
            
            # 清理相关回调
            callbacks_to_remove = [
                cb_id for cb_id, cb_info in self._callbacks.items()
                if cb_info.task_id == task_id
            ]
            for cb_id in callbacks_to_remove:
                del self._callbacks[cb_id]
        
        if tasks_to_remove:
            logger.info(f"清理已完成任务: {len(tasks_to_remove)} 个")


# ==================== 便利函数 ====================

# 全局同步适配器实例（可选）
_global_sync_adapter: Optional[SyncAdapter] = None


def get_global_sync_adapter() -> SyncAdapter:
    """
    获取全局同步适配器实例
    
    Returns:
        SyncAdapter: 全局同步适配器实例
    """
    global _global_sync_adapter
    if _global_sync_adapter is None:
        _global_sync_adapter = SyncAdapter()
        _global_sync_adapter.start()
    return _global_sync_adapter


def initialize_global_sync_adapter(**kwargs) -> SyncAdapter:
    """
    初始化全局同步适配器
    
    Args:
        **kwargs: SyncAdapter构造参数
        
    Returns:
        SyncAdapter: 全局同步适配器实例
    """
    global _global_sync_adapter
    if _global_sync_adapter is not None:
        _global_sync_adapter.stop()
    
    _global_sync_adapter = SyncAdapter(**kwargs)
    _global_sync_adapter.start()
    return _global_sync_adapter


def shutdown_global_sync_adapter():
    """关闭全局同步适配器"""
    global _global_sync_adapter
    if _global_sync_adapter is not None:
        _global_sync_adapter.stop()
        _global_sync_adapter = None


def run_async_in_gui(coro_func: Callable, *args, **kwargs) -> str:
    """
    在GUI线程中运行异步函数的便利函数
    
    Args:
        coro_func: 异步函数
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        str: 任务ID
    """
    adapter = get_global_sync_adapter()
    return adapter.run_async(coro_func, *args, **kwargs)


def run_async_sync_in_gui(coro_func: Callable, *args, timeout: Optional[float] = None, **kwargs) -> Any:
    """
    在GUI线程中同步运行异步函数的便利函数
    
    Args:
        coro_func: 异步函数
        *args: 位置参数
        timeout: 超时时间
        **kwargs: 关键字参数
        
    Returns:
        Any: 异步函数的返回值
    """
    adapter = get_global_sync_adapter()
    return adapter.run_async_sync(coro_func, *args, timeout=timeout, **kwargs)


# ==================== 装饰器 ====================

def async_to_sync(timeout: Optional[float] = None):
    """
    将异步函数转换为同步函数的装饰器
    
    Args:
        timeout: 超时时间
        
    Returns:
        Callable: 装饰器函数
    """
    def decorator(async_func: Callable):
        def sync_wrapper(*args, **kwargs):
            return run_async_sync_in_gui(async_func, *args, timeout=timeout, **kwargs)
        
        sync_wrapper.__name__ = f"sync_{async_func.__name__}"
        sync_wrapper.__doc__ = f"Synchronous wrapper for {async_func.__name__}"
        return sync_wrapper
    
    return decorator


def gui_async(callback: Optional[Callable] = None, progress_callback: Optional[Callable] = None):
    """
    在GUI中异步执行函数的装饰器
    
    Args:
        callback: 完成回调
        progress_callback: 进度回调
        
    Returns:
        Callable: 装饰器函数
    """
    def decorator(async_func: Callable):
        def async_wrapper(*args, **kwargs):
            return run_async_in_gui(
                async_func, *args,
                callback=callback,
                progress_callback=progress_callback,
                **kwargs
            )
        
        async_wrapper.__name__ = f"gui_async_{async_func.__name__}"
        async_wrapper.__doc__ = f"GUI async wrapper for {async_func.__name__}"
        return async_wrapper
    
    return decorator