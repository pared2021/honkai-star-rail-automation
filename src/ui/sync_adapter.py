# -*- coding: utf-8 -*-
"""
同步适配器 - 连接GUI线程和异步世界

该模块提供了在PyQt6 GUI线程中安全调用异步函数的机制。
通过事件循环和信号槽机制，实现同步和异步代码的桥接。
"""

import asyncio
import logging
from typing import Any, Callable, TypeVar, Coroutine, Optional, Dict
from concurrent.futures import ThreadPoolExecutor
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication

T = TypeVar('T')
logger = logging.getLogger(__name__)


class SyncAdapter(QObject):
    """同步适配器 - 连接GUI线程和异步世界"""
    
    # 信号定义
    task_completed = pyqtSignal(str, object)  # task_id, result
    task_failed = pyqtSignal(str, str)  # task_id, error_message
    task_progress = pyqtSignal(str, int)  # task_id, progress_percentage
    
    def __init__(self):
        super().__init__()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="AsyncAdapter")
        self._running_tasks: Dict[str, asyncio.Future] = {}
        self._task_counter = 0
        
        # 定时器用于处理异步事件
        self._timer = QTimer()
        self._timer.timeout.connect(self._process_async_events)
        self._timer.start(100)  # 每100ms检查一次
        
        logger.info("同步适配器初始化完成")
    
    def start_event_loop(self):
        """启动事件循环"""
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            self._executor.submit(self._run_event_loop)
            logger.info("异步事件循环已启动")
    
    def _run_event_loop(self):
        """在后台线程运行事件循环"""
        try:
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()
        except Exception as e:
            logger.error(f"事件循环运行错误: {e}")
        finally:
            logger.info("事件循环已停止")
    
    def run_sync(self, coro: Coroutine[Any, Any, T], timeout: float = 30.0) -> T:
        """同步运行异步协程
        
        Args:
            coro: 要运行的协程
            timeout: 超时时间（秒）
            
        Returns:
            协程的返回值
            
        Raises:
            TimeoutError: 超时
            Exception: 协程执行中的异常
        """
        if self._loop is None or self._loop.is_closed():
            self.start_event_loop()
        
        try:
            future = asyncio.run_coroutine_threadsafe(coro, self._loop)
            result = future.result(timeout=timeout)
            logger.debug(f"同步执行协程成功")
            return result
        except Exception as e:
            logger.error(f"同步执行协程失败: {e}")
            raise
    
    def run_async(self, 
                  coro: Coroutine[Any, Any, T], 
                  callback: Optional[Callable[[T], None]] = None,
                  error_callback: Optional[Callable[[Exception], None]] = None,
                  progress_callback: Optional[Callable[[int], None]] = None) -> str:
        """异步运行协程，通过回调返回结果
        
        Args:
            coro: 要运行的协程
            callback: 成功回调函数
            error_callback: 错误回调函数
            progress_callback: 进度回调函数
            
        Returns:
            任务ID，用于跟踪任务状态
        """
        if self._loop is None or self._loop.is_closed():
            self.start_event_loop()
        
        self._task_counter += 1
        task_id = f"task_{self._task_counter}"
        
        async def wrapper():
            try:
                logger.debug(f"开始执行异步任务: {task_id}")
                result = await coro
                
                # 调用成功回调
                if callback:
                    try:
                        callback(result)
                    except Exception as e:
                        logger.error(f"成功回调执行错误: {e}")
                
                # 发射成功信号
                self.task_completed.emit(task_id, result)
                logger.debug(f"异步任务完成: {task_id}")
                return result
                
            except Exception as e:
                logger.error(f"异步任务失败: {task_id}, 错误: {e}")
                
                # 调用错误回调
                if error_callback:
                    try:
                        error_callback(e)
                    except Exception as callback_error:
                        logger.error(f"错误回调执行错误: {callback_error}")
                
                # 发射失败信号
                self.task_failed.emit(task_id, str(e))
                raise
                
            finally:
                # 清理任务
                self._running_tasks.pop(task_id, None)
        
        try:
            task = asyncio.run_coroutine_threadsafe(wrapper(), self._loop)
            self._running_tasks[task_id] = task
            logger.debug(f"异步任务已提交: {task_id}")
            return task_id
        except Exception as e:
            logger.error(f"提交异步任务失败: {e}")
            raise
    
    def cancel_task(self, task_id: str) -> bool:
        """取消指定的异步任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功取消
        """
        task = self._running_tasks.get(task_id)
        if task and not task.done():
            task.cancel()
            self._running_tasks.pop(task_id, None)
            logger.info(f"任务已取消: {task_id}")
            return True
        return False
    
    def get_running_tasks(self) -> list[str]:
        """获取正在运行的任务列表"""
        return list(self._running_tasks.keys())
    
    def _process_async_events(self):
        """处理异步事件（在GUI线程中调用）"""
        # 检查已完成的任务
        completed_tasks = []
        for task_id, task in self._running_tasks.items():
            if task.done():
                completed_tasks.append(task_id)
        
        # 清理已完成的任务
        for task_id in completed_tasks:
            self._running_tasks.pop(task_id, None)
    
    def run_async_task(self, coro: Coroutine[Any, Any, T]) -> str:
        """运行异步任务的简化接口"""
        return self.run_async(coro)
    
    def execute_async(self,
                     callback_func: Callable,
                     success_callback: Optional[Callable] = None,
                     error_callback: Optional[Callable] = None,
                     timeout: Optional[float] = None) -> str:
        """执行异步回调函数
        
        Args:
            callback_func: 要执行的回调函数
            success_callback: 成功回调函数
            error_callback: 错误回调函数
            timeout: 超时时间
            
        Returns:
            任务ID，用于跟踪任务状态
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
                
                return result
                
            except Exception as e:
                logger.error(f"执行回调函数失败: {e}")
                raise
        
        return self.run_async(
            async_wrapper(),
            callback=success_callback,
            error_callback=error_callback
        )
    
    def cleanup(self):
        """清理资源"""
        self.shutdown()
    
    def close(self):
        """关闭适配器（shutdown的别名）"""
        self.shutdown()
    
    def shutdown(self):
        """关闭适配器"""
        logger.info("开始关闭同步适配器")
        
        # 停止定时器
        if self._timer.isActive():
            self._timer.stop()
        
        # 取消所有运行中的任务
        for task_id in list(self._running_tasks.keys()):
            self.cancel_task(task_id)
        
        # 停止事件循环
        if self._loop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._loop.stop)
        
        # 关闭线程池
        self._executor.shutdown(wait=True)
        
        logger.info("同步适配器已关闭")
    
    def __del__(self):
        """析构函数"""
        try:
            self.shutdown()
        except Exception as e:
            logger.error(f"析构函数执行错误: {e}")


# 全局单例实例
_sync_adapter_instance: Optional[SyncAdapter] = None


def get_sync_adapter() -> SyncAdapter:
    """获取全局同步适配器实例"""
    global _sync_adapter_instance
    
    if _sync_adapter_instance is None:
        # 确保在GUI线程中创建
        app = QApplication.instance()
        if app is None:
            raise RuntimeError("必须在QApplication创建后调用")
        
        _sync_adapter_instance = SyncAdapter()
        _sync_adapter_instance.start_event_loop()
        
        # 注册应用退出时的清理函数
        app.aboutToQuit.connect(_sync_adapter_instance.shutdown)
    
    return _sync_adapter_instance


def cleanup_sync_adapter():
    """清理全局同步适配器实例"""
    global _sync_adapter_instance
    
    if _sync_adapter_instance is not None:
        _sync_adapter_instance.shutdown()
        _sync_adapter_instance = None