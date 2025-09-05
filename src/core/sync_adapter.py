# -*- coding: utf-8 -*-
"""同步适配器模块.

提供异步和同步操作之间的桥梁.
"""

from abc import ABC, abstractmethod
from concurrent.futures import Future
import contextlib
from dataclasses import dataclass, field
from enum import Enum
from queue import Empty, Queue
import threading
import time
from typing import Any, Callable, Dict, Optional
import uuid

import asyncio


class AdapterStatus(Enum):
    """适配器状态枚举。."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class CallbackType(Enum):
    """回调类型枚举。."""

    SUCCESS = "success"
    ERROR = "error"
    PROGRESS = "progress"
    STATUS_CHANGE = "status_change"


class SyncAdapterError(Exception):
    """同步适配器异常。."""

    pass


class AsyncTaskError(Exception):
    """异步任务异常。."""

    pass


@dataclass
class CallbackData:
    """回调数据类。."""

    task_id: str
    callback_type: CallbackType
    data: Any = None
    error: Optional[Exception] = None
    timestamp: float = field(default_factory=time.time)
    progress: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AsyncResult:
    """异步结果数据类。."""

    task_id: str
    is_success: bool = False
    result: Any = None
    error: Optional[Exception] = None
    is_completed: bool = False
    progress: float = 0.0
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CallbackInfo:
    """回调信息数据类。."""

    callback_id: str
    callback_type: CallbackType
    callback_func: Callable
    task_id: Optional[str] = None
    active: bool = True
    created_time: float = field(default_factory=time.time)
    metadata: Optional[Dict[str, Any]] = None


class AsyncCallback(ABC):
    """异步回调抽象基类。."""

    @abstractmethod
    async def on_success(
        self, result: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """成功回调。.

        Args:
            result: 任务结果
            metadata: 元数据
        """
        pass

    @abstractmethod
    async def on_error(
        self, error: Exception, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """错误回调。.

        Args:
            error: 错误信息
            metadata: 元数据
        """
        pass

    @abstractmethod
    async def on_progress(
        self,
        progress: float,
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """进度回调。.

        Args:
            progress: 进度值(0.0-1.0)
            message: 进度消息
            metadata: 元数据
        """
        pass


class SyncCallback(ABC):
    """同步回调抽象基类。."""

    @abstractmethod
    def on_success(
        self, result: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """成功回调。.

        Args:
            result: 任务结果
            metadata: 元数据
        """
        pass

    @abstractmethod
    def on_error(
        self, error: Exception, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """错误回调。.

        Args:
            error: 错误信息
            metadata: 元数据
        """
        pass

    @abstractmethod
    def on_progress(
        self,
        progress: float,
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """进度回调。.

        Args:
            progress: 进度值(0.0-1.0)
            message: 进度消息
            metadata: 元数据
        """
        pass


class SyncAdapter:
    """同步适配器主类。.

    提供异步任务管理、回调处理、线程同步等功能。
    """

    def __init__(self, max_workers: int = 4, max_queue_size: int = 1000):
        """初始化同步适配器。.

        Args:
            max_workers: 最大工作线程数
            max_queue_size: 最大队列大小
        """
        self._max_workers = max_workers
        self._max_queue_size = max_queue_size
        self._status = AdapterStatus.STOPPED
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._callback_thread: Optional[threading.Thread] = None
        self._callback_queue: Queue = Queue(maxsize=max_queue_size)
        self._stop_callback_event = threading.Event()

        # 数据存储
        self._results: Dict[str, AsyncResult] = {}
        self._callbacks: Dict[str, CallbackInfo] = {}
        self._tasks: Dict[str, Future] = {}
        self._task_counter = 0

        # 统计信息
        self._stats = {
            "tasks_submitted": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "callbacks_registered": 0,
            "pending_results": 0,
        }

        # 线程锁
        self._lock = threading.RLock()

    def get_status(self) -> AdapterStatus:
        """获取适配器状态。.

        Returns:
            当前状态
        """
        return self._status

    def start(self) -> bool:
        """启动适配器。.

        Returns:
            是否启动成功
        """
        with self._lock:
            if self._status == AdapterStatus.RUNNING:
                return True

            try:
                self._status = AdapterStatus.STARTING
                self._start_event_loop()
                self._start_callback_thread()
                self._status = AdapterStatus.RUNNING
                self._emit_status_change()
                return True
            except Exception as e:
                self._status = AdapterStatus.ERROR
                raise SyncAdapterError(f"Failed to start adapter: {e}")

    def stop(self) -> bool:
        """停止适配器。.

        Returns:
            是否停止成功
        """
        with self._lock:
            if self._status == AdapterStatus.STOPPED:
                return True

            try:
                self._status = AdapterStatus.STOPPING
                self._stop_event_loop()
                self._stop_callback_thread()
                self._status = AdapterStatus.STOPPED
                self._emit_status_change()
                return True
            except Exception as e:
                self._status = AdapterStatus.ERROR
                raise SyncAdapterError(f"Failed to stop adapter: {e}")

    def _start_event_loop(self) -> None:
        """启动事件循环。."""
        import threading

        # 使用事件来同步线程启动
        loop_ready = threading.Event()

        def run_loop():
            try:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
                loop_ready.set()  # 通知主线程事件循环已准备好
                self._loop.run_forever()
            except Exception:
                loop_ready.set()  # 即使出错也要通知主线程
                raise

        self._loop_thread = threading.Thread(target=run_loop, daemon=True)
        self._loop_thread.start()

        # 等待事件循环启动
        if not loop_ready.wait(timeout=5.0):
            raise SyncAdapterError("Failed to start event loop")

        if self._loop is None:
            raise SyncAdapterError("Failed to start event loop")

    def _stop_event_loop(self, timeout: float = 5.0) -> None:
        """停止事件循环。.

        Args:
            timeout: 超时时间
        """
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

        if self._loop_thread and self._loop_thread.is_alive():
            self._loop_thread.join(timeout=timeout)

        self._loop = None
        self._loop_thread = None

    def _start_callback_thread(self) -> None:
        """启动回调处理线程。."""
        self._stop_callback_event.clear()
        self._callback_thread = threading.Thread(
            target=self._process_callbacks, daemon=True
        )
        self._callback_thread.start()

    def _stop_callback_thread(self, timeout: float = 5.0) -> None:
        """停止回调处理线程。.

        Args:
            timeout: 超时时间
        """
        self._stop_callback_event.set()
        if self._callback_thread and self._callback_thread.is_alive():
            self._callback_thread.join(timeout=timeout)
        self._callback_thread = None

    def _process_callbacks(self) -> None:
        """处理回调队列。."""
        while not self._stop_callback_event.is_set():
            try:
                callback_data = self._callback_queue.get(timeout=0.1)
                self._execute_callback(callback_data)
            except Empty:
                continue
            except Exception:
                # 记录回调执行错误，但不中断处理
                pass

    def _execute_callback(self, callback_data: CallbackData) -> None:
        """执行回调。.

        Args:
            callback_data: 回调数据
        """
        for callback_info in self._callbacks.values():
            if (
                callback_info.active
                and callback_info.callback_type == callback_data.callback_type
                and (
                    callback_info.task_id is None
                    or callback_info.task_id == callback_data.task_id
                )
            ):

                try:
                    if asyncio.iscoroutinefunction(callback_info.callback_func):
                        # 异步回调
                        if self._loop:
                            asyncio.run_coroutine_threadsafe(
                                callback_info.callback_func(callback_data), self._loop
                            )
                    else:
                        # 同步回调
                        callback_info.callback_func(callback_data)
                except Exception as e:
                    # 记录回调执行错误，但不中断处理
                    import logging

                    logging.getLogger(__name__).warning(
                        f"Callback execution failed: {e}"
                    )

    def register_callback(
        self,
        callback_func: Callable,
        callback_type: CallbackType,
        task_id: Optional[str] = None,
    ) -> str:
        """注册回调函数。.

        Args:
            callback_func: 回调函数
            callback_type: 回调类型
            task_id: 任务ID（可选）

        Returns:
            回调ID
        """
        callback_id = str(uuid.uuid4())
        callback_info = CallbackInfo(
            callback_id=callback_id,
            callback_type=callback_type,
            callback_func=callback_func,
            task_id=task_id,
        )

        with self._lock:
            self._callbacks[callback_id] = callback_info
            self._stats["callbacks_registered"] += 1

        return callback_id

    def unregister_callback(self, callback_id: str) -> bool:
        """注销回调函数。.

        Args:
            callback_id: 回调ID

        Returns:
            是否注销成功
        """
        with self._lock:
            if callback_id in self._callbacks:
                del self._callbacks[callback_id]
                return True
            return False

    def submit_async_task(self, coro: Callable, *args, **kwargs) -> str:
        """提交异步任务。.

        Args:
            coro: 协程函数或协程对象
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            任务ID
        """
        if self._status != AdapterStatus.RUNNING:
            raise SyncAdapterError("Adapter is not running")

        if self._loop is None:
            raise SyncAdapterError("Event loop is not available")

        task_id = str(uuid.uuid4())

        # 包装协程以处理异常
        async def wrapped_coro():
            try:
                # 检查是否是协程函数还是协程对象
                if asyncio.iscoroutinefunction(coro):
                    result = await coro(*args, **kwargs)
                elif asyncio.iscoroutine(coro):
                    result = await coro
                else:
                    # 如果是普通函数，在线程池中执行
                    import concurrent.futures

                    if self._loop is not None:
                        with concurrent.futures.ThreadPoolExecutor() as ex:
                            result = await self._loop.run_in_executor(
                                ex, lambda: coro(*args, **kwargs)
                            )
                    else:
                        result = coro(*args, **kwargs)

                # 创建成功结果
                async_result = AsyncResult(
                    task_id=task_id,
                    result=result,
                    is_success=True,
                    is_completed=True,
                    start_time=time.time(),
                    end_time=time.time(),
                )
                self._results[task_id] = async_result

                # 触发成功回调
                callback_data = CallbackData(
                    task_id=task_id, callback_type=CallbackType.SUCCESS, data=result
                )
                self._callback_queue.put(callback_data)

                with self._lock:
                    self._stats["tasks_completed"] += 1

                return result
            except Exception as e:
                # 创建失败结果
                async_result = AsyncResult(
                    task_id=task_id,
                    result=None,
                    error=e,
                    is_success=False,
                    is_completed=True,
                    start_time=time.time(),
                    end_time=time.time(),
                )
                self._results[task_id] = async_result

                # 触发错误回调
                callback_data = CallbackData(
                    task_id=task_id, callback_type=CallbackType.ERROR, error=e
                )
                self._callback_queue.put(callback_data)

                with self._lock:
                    self._stats["tasks_failed"] += 1

                raise

        # 在事件循环中调度任务
        future = asyncio.run_coroutine_threadsafe(wrapped_coro(), self._loop)
        self._tasks[task_id] = future

        with self._lock:
            self._stats["tasks_submitted"] += 1

        return task_id

    def run_async(self, coro, *args, **kwargs) -> str:
        """运行异步任务（submit_async_task的别名）。.

        Args:
            coro: 协程函数或协程对象
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            任务ID
        """
        return self.submit_async_task(coro, *args, **kwargs)

    def wait_for_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """等待任务结果。.

        Args:
            task_id: 任务ID
            timeout: 超时时间

        Returns:
            任务结果

        Raises:
            SyncAdapterError: 当任务不存在时
        """
        if task_id not in self._tasks:
            raise SyncAdapterError(f"Task {task_id} not found")

        future = self._tasks[task_id]

        try:
            result = future.result(timeout=timeout)
            return result
        except Exception as e:
            if task_id in self._results:
                async_result = self._results[task_id]
                if async_result.error:
                    raise async_result.error
            raise e

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息。.

        Returns:
            统计信息字典
        """
        with self._lock:
            stats = self._stats.copy()
            stats["pending_results"] = len(
                [r for r in self._results.values() if not r.is_completed]
            )
            return stats

    def _emit_status_change(self) -> None:
        """发出状态变更信号。."""
        callback_data = CallbackData(
            task_id="", callback_type=CallbackType.STATUS_CHANGE, data=self._status
        )
        with contextlib.suppress(Exception):
            self._callback_queue.put_nowait(callback_data)
