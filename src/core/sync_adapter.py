"""同步适配器

连接GUI线程和异步世界，处理异步事件和回调。
"""

from abc import ABC, abstractmethod
import concurrent.futures
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import queue
import threading
import time
import uuid
from typing import Any, Callable, Coroutine, Dict, List, Optional, Union

import asyncio

try:
    from src.ui.common.ui_components import QApplication, QObject, QTimer, pyqtSignal

    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    QObject = object
    pyqtSignal = None
    QTimer = None
    QApplication = None

logger = logging.getLogger(__name__)


# ==================== 异常类 ====================


class SyncAdapterError(Exception):
    """同步适配器异常"""

    pass


class AsyncTaskError(Exception):
    """异步任务异常"""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


# ==================== 状态枚举 ====================


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
    STATUS_CHANGE = "status_change"
    COMPLETION = "completion"
    COMPLETE = "complete"
    CANCELLED = "cancelled"


@dataclass
class CallbackData:
    """回调数据"""

    callback_type: CallbackType
    data: Any = None
    error: Optional[Exception] = None
    timestamp: float = 0.0
    task_id: Optional[str] = None
    progress: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class AsyncResult:
    """异步结果"""

    task_id: str
    result: Any = None
    error: Optional[Exception] = None
    is_completed: bool = False
    is_success: bool = False
    progress: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None


@dataclass
class CallbackInfo:
    """回调信息"""

    callback_id: str
    callback_type: CallbackType
    callback_func: Callable
    task_id: str
    active: bool = True
    created_time: float = field(default_factory=time.time)


class AsyncCallback(ABC):
    """异步回调基类"""

    @abstractmethod
    async def on_success(self, result: Any, metadata: Optional[Dict[str, Any]] = None):
        """成功回调"""
        pass

    @abstractmethod
    async def on_error(
        self, error: Exception, metadata: Optional[Dict[str, Any]] = None
    ):
        """错误回调"""
        pass

    @abstractmethod
    async def on_progress(
        self,
        progress: float,
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """进度回调"""
        pass


class SyncCallback(ABC):
    """同步回调基类"""

    @abstractmethod
    def on_success(self, result: Any, metadata: Optional[Dict[str, Any]] = None):
        """成功回调"""
        pass

    @abstractmethod
    def on_error(self, error: Exception, metadata: Optional[Dict[str, Any]] = None):
        """错误回调"""
        pass

    @abstractmethod
    def on_progress(
        self,
        progress: float,
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """进度回调"""
        pass


class SyncAdapter(QObject if PYQT6_AVAILABLE else object):
    """统一的同步适配器

    整合了异步任务管理、PyQt6集成和完整的生命周期管理功能
    """

    # PyQt6 信号定义（如果可用）
    if PYQT6_AVAILABLE:
        task_completed = pyqtSignal(str, object)  # task_id, result
        task_failed = pyqtSignal(str, Exception)  # task_id, error
        task_progress = pyqtSignal(str, float)  # task_id, progress
        status_changed = pyqtSignal(str)  # status

    def __init__(self, max_workers: int = 4, max_queue_size: int = 1000, config_manager=None):
        if PYQT6_AVAILABLE:
            super().__init__()

        # 基础配置
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self._config_manager = config_manager

        # 状态管理
        self._status = AdapterStatus.STOPPED
        self._lock = threading.RLock()

        # 异步任务管理
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._executor: Optional[ThreadPoolExecutor] = None
        self._tasks: Dict[str, concurrent.futures.Future] = {}
        self._results: Dict[str, AsyncResult] = {}
        self._task_counter = 0

        # 回调管理
        self._callbacks: Dict[str, CallbackInfo] = {}
        self._callback_queue = queue.Queue(maxsize=max_queue_size)
        self._callback_thread: Optional[threading.Thread] = None

        # PyQt6 集成
        self._qt_timer: Optional[QTimer] = None
        self._pending_qt_tasks: queue.Queue = queue.Queue()

        # 统计信息
        self._stats = {
            "tasks_created": 0,
            "tasks_submitted": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_cancelled": 0,
            "callbacks_executed": 0,
            "callbacks_failed": 0,
        }

        logger.debug("同步适配器已初始化")

    # ==================== 生命周期管理 ====================

    def start(self, timeout: float = 10.0) -> bool:
        """启动同步适配器"""
        with self._lock:
            if self._status == AdapterStatus.RUNNING:
                logger.warning("同步适配器已在运行")
                return True

            if self._status == AdapterStatus.STARTING:
                logger.warning("同步适配器正在启动")
                return False

            try:
                self._status = AdapterStatus.STARTING
                self._emit_status_change()

                # 启动线程池
                self._executor = ThreadPoolExecutor(
                    max_workers=self.max_workers, thread_name_prefix="SyncAdapter"
                )

                # 启动事件循环线程
                self._start_event_loop()

                # 启动回调处理线程
                self._start_callback_thread()

                # 启动PyQt6集成（如果可用）
                self._start_qt_integration()

                self._status = AdapterStatus.RUNNING
                self._emit_status_change()
                logger.info("同步适配器启动成功")
                return True

            except Exception as e:
                self._status = AdapterStatus.ERROR
                self._emit_status_change()
                logger.error(f"同步适配器启动失败: {e}")
                return False

    def stop(self, timeout: float = 10.0) -> bool:
        """停止同步适配器"""
        with self._lock:
            if self._status == AdapterStatus.STOPPED:
                logger.warning("同步适配器已停止")
                return True

            if self._status == AdapterStatus.STOPPING:
                logger.warning("同步适配器正在停止")
                return False

            try:
                self._status = AdapterStatus.STOPPING
                self._emit_status_change()

                # 取消所有任务
                self._cancel_all_tasks()

                # 停止PyQt6集成
                self._stop_qt_integration()

                # 停止回调处理线程
                self._stop_callback_thread(timeout / 3)

                # 停止线程池
                if self._executor:
                    self._executor.shutdown(wait=True)
                    self._executor = None

                # 停止事件循环线程
                self._stop_event_loop(timeout / 3)

                # 清理资源
                self._cleanup()

                self._status = AdapterStatus.STOPPED
                self._emit_status_change()
                logger.info("同步适配器停止成功")
                return True

            except Exception as e:
                self._status = AdapterStatus.ERROR
                self._emit_status_change()
                logger.error(f"同步适配器停止失败: {e}")
                return False

    def _emit_status_change(self):
        """发出状态变化信号"""
        if PYQT6_AVAILABLE and hasattr(self, "status_changed"):
            self.status_changed.emit(self._status.value)

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
        if self._config_manager:
            timeout = self._config_manager.get('sync_adapter.loop_start_timeout', 5.0)
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

            while (
                self._status == AdapterStatus.RUNNING
                or self._status == AdapterStatus.STARTING
            ):
                try:
                    # 获取回调任务（带超时）
                    try:
                        timeout = 1.0
                        if self._config_manager:
                            timeout = self._config_manager.get('sync_adapter.callback_timeout', 1.0)
                        callback_task = self._callback_queue.get(timeout=timeout)
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

    def _start_qt_integration(self):
        """启动PyQt6集成"""
        if not PYQT6_AVAILABLE:
            return

        # 检查是否在主线程中
        app = QApplication.instance()
        if app is None:
            logger.warning("PyQt6应用程序未运行，跳过Qt集成")
            return

        # 创建定时器处理Qt任务
        self._qt_timer = QTimer()
        self._qt_timer.timeout.connect(self._process_qt_tasks)
        self._qt_timer.start(10)  # 10ms间隔

        logger.debug("PyQt6集成已启动")

    def _stop_qt_integration(self):
        """停止PyQt6集成"""
        if self._qt_timer:
            self._qt_timer.stop()
            self._qt_timer = None

        # 清空待处理的Qt任务
        while not self._pending_qt_tasks.empty():
            try:
                self._pending_qt_tasks.get_nowait()
            except queue.Empty:
                break

    def _process_qt_tasks(self):
        """处理Qt任务队列"""
        processed = 0
        max_process = 10  # 每次最多处理10个任务

        while processed < max_process and not self._pending_qt_tasks.empty():
            try:
                task_func = self._pending_qt_tasks.get_nowait()
                task_func()
                processed += 1
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"处理Qt任务失败: {e}")

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

    def _cancel_all_tasks(self):
        """取消所有任务"""
        for task_id, future in self._tasks.items():
            if not future.done():
                future.cancel()
                logger.debug(f"取消任务: {task_id}")

    # ==================== 异步任务管理 ====================

    def execute_async(self, callback_func: Callable, *args, **kwargs) -> str:
        """执行异步回调函数"""
        if self._status != AdapterStatus.RUNNING:
            raise SyncAdapterError("适配器未运行")

        task_id = str(uuid.uuid4())

        def execute():
            try:
                if asyncio.iscoroutinefunction(callback_func):
                    # 协程函数
                    future = asyncio.run_coroutine_threadsafe(
                        callback_func(*args, **kwargs), self._loop
                    )
                    result = future.result()
                else:
                    # 普通函数
                    result = callback_func(*args, **kwargs)

                # 触发成功回调
                self._trigger_callbacks(
                    CallbackType.SUCCESS,
                    CallbackData(callback_type=CallbackType.SUCCESS, task_id=task_id, data=result, timestamp=time.time()),
                )

                return result

            except Exception as e:
                # 触发错误回调
                self._trigger_callbacks(
                    CallbackType.ERROR,
                    CallbackData(callback_type=CallbackType.ERROR, task_id=task_id, error=e, timestamp=time.time()),
                )
                raise

        # 在线程池中执行
        future = self._executor.submit(execute)
        self._tasks[task_id] = future

        return task_id

    def run_async(
        self,
        async_func: Callable,
        *args,
        success_callback: Optional[Callable] = None,
        error_callback: Optional[Callable] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> str:
        """运行异步任务"""
        if self._status != AdapterStatus.RUNNING:
            raise SyncAdapterError("适配器未运行")

        task_id = str(uuid.uuid4())

        # 创建异步结果对象
        async_result = AsyncResult(
            task_id=task_id, is_completed=False, is_success=False, start_time=time.time()
        )
        self._results[task_id] = async_result

        # 注册回调
        if success_callback:
            self.register_callback(CallbackType.SUCCESS, success_callback, task_id)
        if error_callback:
            self.register_callback(CallbackType.ERROR, error_callback, task_id)

        async def execute_task():
            try:
                # 执行异步函数
                if asyncio.iscoroutinefunction(async_func):
                    result = await async_func(*args, **kwargs)
                else:
                    # 在线程池中执行同步函数
                    result = await self._loop.run_in_executor(
                        self._executor, lambda: async_func(*args, **kwargs)
                    )

                # 更新结果
                async_result.result = result
                async_result.is_completed = True
                async_result.is_success = True
                async_result.end_time = time.time()

                # 触发成功回调
                self._trigger_callbacks(
                    CallbackType.SUCCESS,
                    CallbackData(callback_type=CallbackType.SUCCESS, task_id=task_id, data=result, timestamp=time.time()),
                )

                self._stats["tasks_completed"] += 1
                return result

            except asyncio.CancelledError:
                # 任务被取消
                async_result.is_completed = True
                async_result.is_success = False
                async_result.end_time = time.time()

                self._trigger_callbacks(
                    CallbackType.CANCELLED,
                    CallbackData(callback_type=CallbackType.CANCELLED, task_id=task_id, timestamp=time.time()),
                )

                self._stats["tasks_cancelled"] += 1
                raise

            except Exception as e:
                # 任务失败
                async_result.error = e
                async_result.is_completed = True
                async_result.is_success = False
                async_result.end_time = time.time()

                self._trigger_callbacks(
                    CallbackType.ERROR,
                    CallbackData(callback_type=CallbackType.ERROR, task_id=task_id, error=e, timestamp=time.time()),
                )

                self._stats["tasks_failed"] += 1
                raise

        # 在事件循环中执行任务
        if timeout:
            future = asyncio.run_coroutine_threadsafe(
                asyncio.wait_for(execute_task(), timeout=timeout), self._loop
            )
        else:
            future = asyncio.run_coroutine_threadsafe(execute_task(), self._loop)

        self._tasks[task_id] = future
        self._stats["tasks_submitted"] += 1

        return task_id

    def run_async_sync(
        self, async_func: Callable, *args, timeout: Optional[float] = None, **kwargs
    ) -> Any:
        """同步运行异步任务（阻塞等待结果）"""
        task_id = self.run_async(async_func, *args, timeout=timeout, **kwargs)
        return self.wait_for_result(task_id, timeout=timeout)

    def wait_for_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """等待任务结果"""
        if task_id not in self._tasks:
            raise SyncAdapterError(f"任务不存在: {task_id}")

        future = self._tasks[task_id]

        try:
            result = future.result(timeout=timeout)
            return result
        except concurrent.futures.TimeoutError:
            raise SyncAdapterError(f"任务超时: {task_id}")
        except Exception as e:
            raise SyncAdapterError(f"任务失败: {task_id}, 错误: {e}")

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id not in self._tasks:
            return False

        future = self._tasks[task_id]
        cancelled = future.cancel()

        if cancelled:
            logger.debug(f"任务已取消: {task_id}")

            # 更新结果状态
            if task_id in self._results:
                self._results[task_id].is_completed = True
                self._results[task_id].is_success = False
                self._results[task_id].end_time = time.time()

        return cancelled

    # ==================== 回调管理 ====================

    def register_callback(
        self,
        callback_type: CallbackType,
        callback_func: Callable,
        task_id: Optional[str] = None,
    ):
        """注册回调函数"""
        callback_info = CallbackInfo(
            callback_id=f"cb_{int(time.time() * 1000000)}",
            callback_type=callback_type,
            callback_func=callback_func,
            task_id=task_id,
            created_time=time.time(),
        )

        if task_id not in self._callbacks:
            self._callbacks[task_id] = []

        self._callbacks[task_id].append(callback_info)
        logger.debug(f"注册回调: {callback_type}, 任务ID: {task_id}")

    def unregister_callback(
        self,
        callback_type: CallbackType,
        callback_func: Callable,
        task_id: Optional[str] = None,
    ):
        """注销回调函数"""
        if task_id not in self._callbacks:
            return

        self._callbacks[task_id] = [
            cb
            for cb in self._callbacks[task_id]
            if not (
                cb.callback_type == callback_type and cb.callback_func == callback_func
            )
        ]

        if not self._callbacks[task_id]:
            del self._callbacks[task_id]

        logger.debug(f"注销回调: {callback_type}, 任务ID: {task_id}")

    def _trigger_callbacks(self, callback_type: CallbackType, data: CallbackData):
        """触发回调"""
        # 触发特定任务的回调
        if data.task_id in self._callbacks:
            for callback_info in self._callbacks[data.task_id]:
                if callback_info.callback_type == callback_type:
                    self._queue_callback(callback_info.callback_func, data)

        # 触发全局回调
        if None in self._callbacks:
            for callback_info in self._callbacks[None]:
                if callback_info.callback_type == callback_type:
                    self._queue_callback(callback_info.callback_func, data)

    def _queue_callback(self, callback_func: Callable, data: CallbackData):
        """将回调加入队列"""

        def execute_callback():
            try:
                callback_func(data)
                self._stats["callbacks_executed"] += 1
            except Exception as e:
                self._stats["callbacks_failed"] += 1
                logger.error(f"回调执行失败: {e}")

        self._callback_queue.put(execute_callback)

    # ==================== PyQt6集成 ====================

    def run_in_gui_thread(self, func: Callable, *args, **kwargs):
        """在GUI线程中运行函数"""
        if not PYQT6_AVAILABLE:
            raise SyncAdapterError("PyQt6不可用")

        def qt_task():
            try:
                func(*args, **kwargs)
            except Exception as e:
                logger.error(f"GUI线程任务失败: {e}")

        self._pending_qt_tasks.put(qt_task)

    def emit_qt_signal(self, signal_name: str, *args):
        """发出Qt信号"""
        if not PYQT6_AVAILABLE or not hasattr(self, signal_name):
            return

        signal = getattr(self, signal_name)

        def emit_signal():
            try:
                signal.emit(*args)
            except Exception as e:
                logger.error(f"Qt信号发送失败: {e}")

        self._pending_qt_tasks.put(emit_signal)

    # ==================== 任务状态查询 ====================

    def get_task_status(self, task_id: str) -> Optional[str]:
        """获取任务状态"""
        if task_id in self._results:
            return self._results[task_id].status
        elif task_id in self._tasks:
            future = self._tasks[task_id]
            if future.done():
                if future.cancelled():
                    return "cancelled"
                elif future.exception():
                    return "failed"
                else:
                    return "completed"
            else:
                return "running"
        return None

    def is_task_completed(self, task_id: str) -> bool:
        """检查任务是否完成"""
        status = self.get_task_status(task_id)
        return status in ["completed", "failed", "cancelled"]

    def is_task_running(self, task_id: str) -> bool:
        """检查任务是否正在运行"""
        return self.get_task_status(task_id) == "running"

    def get_running_tasks(self) -> List[str]:
        """获取正在运行的任务列表"""
        running_tasks = []
        for task_id in self._tasks:
            if self.is_task_running(task_id):
                running_tasks.append(task_id)
        return running_tasks

    def get_completed_tasks(self) -> List[str]:
        """获取已完成的任务列表"""
        completed_tasks = []
        for task_id in self._tasks:
            if self.is_task_completed(task_id):
                completed_tasks.append(task_id)
        return completed_tasks

    # ==================== 统计和监控 ====================

    def get_status(self) -> AdapterStatus:
        """获取适配器状态"""
        return self._status

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self._stats.copy()
        stats.update(
            {
                "running_tasks": len(self.get_running_tasks()),
                "completed_tasks": len(self.get_completed_tasks()),
                "total_tasks": len(self._tasks),
                "total_callbacks": sum(
                    len(callbacks) for callbacks in self._callbacks.values()
                ),
                "uptime": time.time() - self._start_time if self._start_time else 0,
            }
        )
        return stats

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health = {"status": self._status.value, "healthy": True, "issues": []}

        # 检查事件循环
        if self._loop is None or not self._loop.is_running():
            health["healthy"] = False
            health["issues"].append("事件循环未运行")

        # 检查线程状态
        if self._loop_thread is None or not self._loop_thread.is_alive():
            health["healthy"] = False
            health["issues"].append("事件循环线程未运行")

        if self._callback_thread is None or not self._callback_thread.is_alive():
            health["healthy"] = False
            health["issues"].append("回调处理线程未运行")

        # 检查任务积压
        running_tasks = len(self.get_running_tasks())
        if running_tasks > 100:  # 阈值可配置
            health["issues"].append(f"任务积压过多: {running_tasks}")

        return health

    def cleanup_completed_tasks(self, max_age: float = 3600):
        """清理已完成的任务（默认1小时）"""
        current_time = time.time()
        tasks_to_remove = []

        for task_id, result in self._results.items():
            if (
                result.completed_at
                and current_time - result.completed_at > max_age
                and self.is_task_completed(task_id)
            ):
                tasks_to_remove.append(task_id)

        for task_id in tasks_to_remove:
            if task_id in self._tasks:
                del self._tasks[task_id]
            if task_id in self._results:
                del self._results[task_id]
            if task_id in self._callbacks:
                del self._callbacks[task_id]

        logger.debug(f"清理了 {len(tasks_to_remove)} 个已完成的任务")
        return len(tasks_to_remove)

    def _execute_callback(self, callback_task):
        """执行回调任务"""
        try:
            callback_task()
            self._stats["callbacks_executed"] += 1
        except Exception as e:
            self._stats["callbacks_failed"] += 1
            logger.error(f"回调执行失败: {e}")


# ==================== 全局实例管理 ====================

_global_adapter: Optional[SyncAdapter] = None


def get_sync_adapter() -> SyncAdapter:
    """获取全局SyncAdapter实例"""
    global _global_adapter
    if _global_adapter is None:
        _global_adapter = SyncAdapter()
    return _global_adapter


def init_sync_adapter(**kwargs) -> SyncAdapter:
    """初始化全局SyncAdapter实例"""
    global _global_adapter
    if _global_adapter is not None:
        _global_adapter.stop()

    _global_adapter = SyncAdapter(**kwargs)
    _global_adapter.start()
    return _global_adapter


def shutdown_sync_adapter():
    """关闭全局SyncAdapter实例"""
    global _global_adapter
    if _global_adapter is not None:
        _global_adapter.stop()
        _global_adapter = None


# ==================== 便利函数 ====================


def run_async_in_gui(async_func: Callable, *args, **kwargs) -> str:
    """在GUI线程中运行异步函数"""
    adapter = get_sync_adapter()
    if adapter.get_status() != AdapterStatus.RUNNING:
        adapter.start()
    return adapter.run_async(async_func, *args, **kwargs)


def run_async_sync_in_gui(
    async_func: Callable, *args, timeout: Optional[float] = None, **kwargs
) -> Any:
    """在GUI线程中同步运行异步函数"""
    adapter = get_sync_adapter()
    if adapter.get_status() != AdapterStatus.RUNNING:
        adapter.start()
    return adapter.run_async_sync(async_func, *args, timeout=timeout, **kwargs)


# ==================== 装饰器 ====================


def async_to_sync(timeout: Optional[float] = None):
    """将异步函数转换为同步函数的装饰器"""

    def decorator(async_func: Callable):
        def wrapper(*args, **kwargs):
            return run_async_sync_in_gui(async_func, *args, timeout=timeout, **kwargs)

        return wrapper

    return decorator


def gui_async(
    success_callback: Optional[Callable] = None,
    error_callback: Optional[Callable] = None,
    timeout: Optional[float] = None,
):
    """GUI异步执行装饰器"""

    def decorator(async_func: Callable):
        def wrapper(*args, **kwargs):
            return run_async_in_gui(
                async_func,
                *args,
                success_callback=success_callback,
                error_callback=error_callback,
                timeout=timeout,
                **kwargs,
            )

        return wrapper

    return decorator


class CallbackManager:
    """回调管理器"""

    def __init__(self):
        self._async_callbacks: List[AsyncCallback] = []
        self._sync_callbacks: List[SyncCallback] = []
        self._processing = False
        self._callback_queue = queue.Queue()
        self._callback_thread: Optional[threading.Thread] = None

    def add_async_callback(self, callback: AsyncCallback):
        """添加异步回调"""
        self._async_callbacks.append(callback)

    def add_sync_callback(self, callback: SyncCallback):
        """添加同步回调"""
        self._sync_callbacks.append(callback)

    def remove_async_callback(self, callback: AsyncCallback):
        """移除异步回调"""
        if callback in self._async_callbacks:
            self._async_callbacks.remove(callback)

    def remove_sync_callback(self, callback: SyncCallback):
        """移除同步回调"""
        if callback in self._sync_callbacks:
            self._sync_callbacks.remove(callback)

    def emit_success(self, result: Any, metadata: Optional[Dict[str, Any]] = None):
        """发出成功事件"""
        for callback in self._sync_callbacks:
            try:
                callback.on_success(result, metadata)
            except Exception as e:
                logger.error(f"同步成功回调失败: {e}")

        for callback in self._async_callbacks:
            self._callback_queue.put(
                lambda: self._run_async_callback(callback.on_success, result, metadata)
            )

    def emit_error(self, error: Exception, metadata: Optional[Dict[str, Any]] = None):
        """发出错误事件"""
        for callback in self._sync_callbacks:
            try:
                callback.on_error(error, metadata)
            except Exception as e:
                logger.error(f"同步错误回调失败: {e}")

        for callback in self._async_callbacks:
            self._callback_queue.put(
                lambda: self._run_async_callback(callback.on_error, error, metadata)
            )

    def emit_progress(
        self,
        progress: float,
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """发出进度事件"""
        for callback in self._sync_callbacks:
            try:
                callback.on_progress(progress, message, metadata)
            except Exception as e:
                logger.error(f"同步进度回调失败: {e}")

        for callback in self._async_callbacks:
            self._callback_queue.put(
                lambda: self._run_async_callback(
                    callback.on_progress, progress, message, metadata
                )
            )

    def start_processing(self):
        """开始处理回调"""
        if self._processing:
            return

        self._processing = True
        self._callback_thread = threading.Thread(
            target=self._process_callbacks, daemon=True
        )
        self._callback_thread.start()

    def stop_processing(self):
        """停止处理回调"""
        self._processing = False
        if self._callback_thread:
            timeout = 5.0
            if self._config_manager:
                timeout = self._config_manager.get('sync_adapter.thread_stop_timeout', 5.0)
            self._callback_thread.join(timeout=timeout)

    def _process_callbacks(self):
        """处理回调队列"""
        while self._processing:
            try:
                timeout = 1.0
                if hasattr(self, '_config_manager') and self._config_manager:
                    timeout = self._config_manager.get('sync_adapter.callback_timeout', 1.0)
                callback_task = self._callback_queue.get(timeout=timeout)
                callback_task()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"处理异步回调失败: {e}")

    def _run_async_callback(self, callback_func, *args, **kwargs):
        """运行异步回调"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(callback_func(*args, **kwargs))
        except Exception as e:
            logger.error(f"异步回调执行失败: {e}")
        finally:
            loop.close()


class AsyncToSyncAdapter:
    """异步到同步适配器

    将异步操作转换为同步操作，适用于GUI线程调用。
    """

    def __init__(self, max_workers: int = 4, config_manager=None):
        self.max_workers = max_workers
        self._config_manager = config_manager
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._running = False

    def start(self):
        """启动适配器"""
        if self._running:
            return

        self._running = True
        self._loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._loop_thread.start()

        # 等待事件循环启动
        while self._loop is None:
            threading.Event().wait(0.01)

        logger.info("异步到同步适配器已启动")

    def stop(self):
        """停止适配器"""
        if not self._running:
            return

        self._running = False

        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

        if self._loop_thread:
            timeout = 5.0
            if self._config_manager:
                timeout = self._config_manager.get('async_adapter.thread_stop_timeout', 5.0)
            self._loop_thread.join(timeout=timeout)

        self._executor.shutdown(wait=True)
        logger.info("异步到同步适配器已停止")

    def run_async(self, coro: Coroutine, timeout: Optional[float] = None) -> Any:
        """在同步环境中运行异步协程

        Args:
            coro: 异步协程
            timeout: 超时时间（秒）

        Returns:
            协程执行结果

        Raises:
            TimeoutError: 执行超时
            Exception: 协程执行异常
        """
        if not self._running or not self._loop:
            raise RuntimeError("适配器未启动")

        future = asyncio.run_coroutine_threadsafe(coro, self._loop)

        try:
            return future.result(timeout=timeout)
        except Exception as e:
            future.cancel()
            raise e

    def run_async_with_callback(
        self,
        coro: Coroutine,
        callback_manager: CallbackManager,
        timeout: Optional[float] = None,
    ) -> Future:
        """在同步环境中运行异步协程，并通过回调返回结果

        Args:
            coro: 异步协程
            callback_manager: 回调管理器
            timeout: 超时时间（秒）

        Returns:
            Future对象
        """
        if not self._running or not self._loop:
            raise RuntimeError("适配器未启动")

        async def wrapped_coro():
            try:
                result = await coro
                callback_manager.emit_success(result)
                return result
            except Exception as e:
                callback_manager.emit_error(e)
                raise e

        future = asyncio.run_coroutine_threadsafe(wrapped_coro(), self._loop)

        # 设置超时
        if timeout:

            def timeout_callback():
                if not future.done():
                    future.cancel()
                    callback_manager.emit_error(TimeoutError(f"操作超时: {timeout}秒"))

            timer = threading.Timer(timeout, timeout_callback)
            timer.start()

            # 完成时取消定时器
            def cleanup_timer(fut):
                timer.cancel()

            future.add_done_callback(cleanup_timer)

        return future

    def submit_async_task(
        self, coro: Coroutine, callback_manager: Optional[CallbackManager] = None
    ) -> Future:
        """提交异步任务到线程池

        Args:
            coro: 异步协程
            callback_manager: 回调管理器

        Returns:
            Future对象
        """

        def run_task():
            try:
                if self._loop and self._loop.is_running():
                    future = asyncio.run_coroutine_threadsafe(coro, self._loop)
                    result = future.result()
                else:
                    result = asyncio.run(coro)

                if callback_manager:
                    callback_manager.emit_success(result)

                return result

            except Exception as e:
                if callback_manager:
                    callback_manager.emit_error(e)
                raise e

        return self._executor.submit(run_task)

    def _run_event_loop(self):
        """运行事件循环"""
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            logger.info("事件循环已启动")
            self._loop.run_forever()

        except Exception as e:
            logger.error(f"事件循环运行失败: {e}")
        finally:
            if self._loop:
                self._loop.close()
            logger.info("事件循环已结束")


class SyncToAsyncAdapter:
    """同步到异步适配器

    将同步操作转换为异步操作，避免阻塞事件循环。
    """

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    async def run_sync(self, func: Callable, *args, **kwargs) -> Any:
        """在异步环境中运行同步函数

        Args:
            func: 同步函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果
        """
        loop = asyncio.get_event_loop()

        def wrapped_func():
            return func(*args, **kwargs)

        return await loop.run_in_executor(self._executor, wrapped_func)

    async def run_sync_with_progress(
        self,
        func: Callable,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        *args,
        **kwargs,
    ) -> Any:
        """在异步环境中运行同步函数，支持进度回调

        Args:
            func: 同步函数
            progress_callback: 进度回调函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果
        """
        loop = asyncio.get_event_loop()

        def wrapped_func():
            # 如果函数支持进度回调，传入回调函数
            if progress_callback and "progress_callback" in func.__code__.co_varnames:
                kwargs["progress_callback"] = progress_callback

            return func(*args, **kwargs)

        return await loop.run_in_executor(self._executor, wrapped_func)

    def shutdown(self):
        """关闭适配器"""
        self._executor.shutdown(wait=True)


class EventBridge:
    """事件桥接器

    在异步事件系统和同步GUI之间建立桥梁。
    """

    def __init__(self):
        self.callback_manager = CallbackManager()
        self.async_adapter = AsyncToSyncAdapter()
        self.sync_adapter = SyncToAsyncAdapter()
        self._started = False

    def start(self):
        """启动事件桥接器"""
        if self._started:
            return

        self.callback_manager.start_processing()
        self.async_adapter.start()
        self._started = True
        logger.info("事件桥接器已启动")

    def stop(self):
        """停止事件桥接器"""
        if not self._started:
            return

        self.callback_manager.stop_processing()
        self.async_adapter.stop()
        self.sync_adapter.shutdown()
        self._started = False
        logger.info("事件桥接器已停止")

    def add_callback(self, callback: Union[AsyncCallback, SyncCallback]):
        """添加回调"""
        if isinstance(callback, AsyncCallback):
            self.callback_manager.add_async_callback(callback)
        elif isinstance(callback, SyncCallback):
            self.callback_manager.add_sync_callback(callback)
        else:
            raise ValueError("不支持的回调类型")

    def remove_callback(self, callback: Union[AsyncCallback, SyncCallback]):
        """移除回调"""
        if isinstance(callback, AsyncCallback):
            self.callback_manager.remove_async_callback(callback)
        elif isinstance(callback, SyncCallback):
            self.callback_manager.remove_sync_callback(callback)

    def run_async_in_sync(
        self, coro: Coroutine, timeout: Optional[float] = None
    ) -> Any:
        """在同步环境中运行异步操作"""
        return self.async_adapter.run_async(coro, timeout)

    def run_async_with_callback(
        self, coro: Coroutine, timeout: Optional[float] = None
    ) -> Future:
        """在同步环境中运行异步操作，通过回调返回结果"""
        return self.async_adapter.run_async_with_callback(
            coro, self.callback_manager, timeout
        )

    async def run_sync_in_async(self, func: Callable, *args, **kwargs) -> Any:
        """在异步环境中运行同步操作"""
        return await self.sync_adapter.run_sync(func, *args, **kwargs)

    def emit_success(self, result: Any, metadata: Optional[Dict[str, Any]] = None):
        """发出成功事件"""
        self.callback_manager.emit_success(result, metadata)

    def emit_error(self, error: Exception, metadata: Optional[Dict[str, Any]] = None):
        """发出错误事件"""
        self.callback_manager.emit_error(error, metadata)

    def emit_progress(
        self,
        progress: float,
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """发出进度事件"""
        self.callback_manager.emit_progress(progress, message, metadata)


# 全局事件桥接器实例
default_event_bridge = EventBridge()


def sync_async(timeout: Optional[float] = None):
    """同步异步装饰器

    将异步函数转换为同步函数，适用于GUI调用。

    Args:
        timeout: 超时时间（秒）
    """

    def decorator(async_func):
        def sync_wrapper(*args, **kwargs):
            coro = async_func(*args, **kwargs)
            return default_event_bridge.run_async_in_sync(coro, timeout)

        return sync_wrapper

    return decorator


def async_sync(func):
    """异步同步装饰器

    将同步函数转换为异步函数，避免阻塞事件循环。
    """

    async def async_wrapper(*args, **kwargs):
        return await default_event_bridge.run_sync_in_async(func, *args, **kwargs)

    return async_wrapper
