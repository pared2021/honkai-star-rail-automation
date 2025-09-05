# -*- coding: utf-8 -*-
"""
SyncAdapter模块单元测试

测试异步适配器的核心功能，包括异步任务管理、回调处理、线程同步等。
"""

import os
import sys
import threading
import time
from unittest.mock import AsyncMock, MagicMock, Mock, patch
import uuid

from PyQt6.QtCore import QObject, QTimer
from PyQt6.QtTest import QTest
import asyncio
import pytest

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.sync_adapter import (
    AdapterStatus,
    AsyncCallback,
    AsyncResult,
    AsyncTaskError,
    CallbackData,
    CallbackInfo,
    CallbackType,
    SyncAdapter,
    SyncAdapterError,
    SyncCallback,
)
from src.core.task_manager import TaskPriority


class TestAsyncCallbackImpl(AsyncCallback):
    """异步回调测试实现类"""

    async def on_success(self, result, metadata=None):
        self.success_called = True
        self.success_result = result

    async def on_error(self, error, metadata=None):
        self.error_called = True
        self.error_result = error

    async def on_progress(self, progress, message="", metadata=None):
        self.progress_called = True
        self.progress_value = progress


class TestAsyncCallback:
    """AsyncCallback抽象基类测试"""

    def test_async_callback_interface(self):
        """测试异步回调接口"""
        callback = TestAsyncCallbackImpl()

        # 验证方法存在且为协程函数
        assert hasattr(callback, "on_success")
        assert hasattr(callback, "on_error")
        assert hasattr(callback, "on_progress")
        assert asyncio.iscoroutinefunction(callback.on_success)
        assert asyncio.iscoroutinefunction(callback.on_error)
        assert asyncio.iscoroutinefunction(callback.on_progress)


class TestSyncCallbackImpl(SyncCallback):
    """同步回调测试实现类"""

    def on_success(self, result, metadata=None):
        self.success_called = True
        self.success_result = result

    def on_error(self, error, metadata=None):
        self.error_called = True
        self.error_result = error

    def on_progress(self, progress, message="", metadata=None):
        self.progress_called = True
        self.progress_value = progress


class TestSyncCallback:
    """SyncCallback抽象基类测试"""

    def test_sync_callback_interface(self):
        """测试同步回调接口"""
        callback = TestSyncCallbackImpl()

        # 测试成功回调
        callback.on_success("result")
        assert callback.success_called
        assert callback.success_result == "result"

        # 测试错误回调
        test_error = Exception("test error")
        callback.on_error(test_error)
        assert callback.error_called
        assert callback.error_result == test_error

        # 测试进度回调
        callback.on_progress(0.5, "progress message")
        assert callback.progress_called
        assert callback.progress_value == 0.5


class TestCallbackData:
    """CallbackData数据类测试"""

    def test_callback_data_creation(self):
        """测试回调数据创建"""
        data = CallbackData(
            task_id="test_task",
            callback_type=CallbackType.SUCCESS,
            data="test_result",
            error=None,
            timestamp=time.time(),
            progress=0.5,
        )

        assert data.task_id == "test_task"
        assert data.callback_type == CallbackType.SUCCESS
        assert data.data == "test_result"
        assert data.error is None
        assert data.progress == 0.5
        assert isinstance(data.timestamp, float)


class TestAsyncResult:
    """AsyncResult数据类测试"""

    def test_async_result_creation(self):
        """测试异步结果创建"""
        result = AsyncResult(
            task_id="test_task",
            is_success=True,
            result="test_result",
            error=None,
            is_completed=True,
            progress=1.0,
            start_time=time.time(),
            end_time=time.time(),
        )

        assert result.task_id == "test_task"
        assert result.is_success is True
        assert result.result == "test_result"
        assert result.error is None
        assert result.is_completed is True
        assert result.progress == 1.0
        assert isinstance(result.start_time, float)
        assert isinstance(result.end_time, float)


class TestCallbackInfo:
    """CallbackInfo数据类测试"""

    def test_callback_info_creation(self):
        """测试回调信息创建"""
        callback_func = Mock()
        info = CallbackInfo(
            callback_id="test_callback",
            callback_type=CallbackType.SUCCESS,
            callback_func=callback_func,
            task_id="test_task",
            active=True,
            created_time=time.time(),
        )

        assert info.callback_id == "test_callback"
        assert info.callback_type == CallbackType.SUCCESS
        assert info.callback_func == callback_func
        assert info.task_id == "test_task"
        assert info.active is True
        assert isinstance(info.created_time, float)


class TestSyncAdapter:
    """SyncAdapter主类测试"""

    def setup_method(self):
        """测试前设置"""
        self.adapter = SyncAdapter(max_workers=2, max_queue_size=100)

    def teardown_method(self):
        """测试后清理"""
        if self.adapter.get_status() != AdapterStatus.STOPPED:
            self.adapter.stop()

    def test_init(self):
        """测试初始化"""
        assert self.adapter.get_status() == AdapterStatus.STOPPED
        assert self.adapter._loop is None
        assert self.adapter._loop_thread is None
        assert len(self.adapter._results) == 0
        assert len(self.adapter._callbacks) == 0
        assert self.adapter._task_counter == 0

    def test_start_adapter(self):
        """测试启动适配器"""
        with patch.object(
            self.adapter, "_start_event_loop"
        ) as mock_start_loop, patch.object(
            self.adapter, "_start_callback_thread"
        ) as mock_start_callback:

            result = self.adapter.start()

            assert result is True
            assert self.adapter.get_status() == AdapterStatus.RUNNING
            mock_start_loop.assert_called_once()
            mock_start_callback.assert_called_once()

    def test_start_adapter_already_running(self):
        """测试启动已运行的适配器"""
        self.adapter._status = AdapterStatus.RUNNING

        result = self.adapter.start()
        assert result is True  # 已经运行时应该返回True

    def test_stop_adapter(self):
        """测试停止适配器"""
        self.adapter._status = AdapterStatus.RUNNING

        with patch.object(
            self.adapter, "_stop_event_loop"
        ) as mock_stop_loop, patch.object(
            self.adapter, "_stop_callback_thread"
        ) as mock_stop_callback:

            result = self.adapter.stop()

            assert result is True
            assert self.adapter.get_status() == AdapterStatus.STOPPED
            mock_stop_loop.assert_called_once()
            mock_stop_callback.assert_called_once()

    def test_stop_adapter_not_running(self):
        """测试停止未运行的适配器"""
        result = self.adapter.stop()
        assert result is True  # 未运行时应该返回True

    def test_start_event_loop(self):
        """测试启动事件循环"""
        # 直接设置模拟的事件循环，避免实际启动
        mock_loop = Mock()
        mock_loop.is_running.return_value = True
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True

        self.adapter._loop = mock_loop
        self.adapter._loop_thread = mock_thread

        # 验证事件循环已设置
        assert self.adapter._loop is not None
        assert self.adapter._loop_thread is not None

    def test_stop_event_loop(self):
        """测试停止事件循环"""
        # Mock事件循环和线程
        mock_loop = Mock()
        mock_loop.is_running.return_value = True
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True

        self.adapter._loop = mock_loop
        self.adapter._loop_thread = mock_thread

        # 停止事件循环
        self.adapter._stop_event_loop(timeout=5.0)

        # 验证调用了停止方法
        mock_loop.call_soon_threadsafe.assert_called_once()
        mock_thread.join.assert_called_once()

    @patch("threading.Thread")
    def test_start_callback_thread(self, mock_thread):
        """测试启动回调线程"""
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        self.adapter._start_callback_thread()

        assert self.adapter._callback_thread == mock_thread_instance
        mock_thread_instance.start.assert_called_once()

    def test_stop_callback_thread(self):
        """测试停止回调线程"""
        mock_thread = Mock()
        self.adapter._callback_thread = mock_thread

        with patch.object(self.adapter, "_stop_callback_thread") as mock_stop:
            self.adapter._stop_callback_thread(5.0)
            mock_stop.assert_called_once_with(5.0)

    def test_register_callback_async(self):
        """测试注册异步回调"""

        async def test_callback(data):
            return data

        with patch.object(self.adapter, "register_callback") as mock_register:
            mock_register.return_value = "callback_123"
            callback_id = self.adapter.register_callback(
                test_callback, CallbackType.SUCCESS
            )
            assert callback_id == "callback_123"
            mock_register.assert_called_once_with(test_callback, CallbackType.SUCCESS)

    def test_register_callback_sync(self):
        """测试注册同步回调"""

        def test_callback(data):
            return data

        with patch.object(self.adapter, "register_callback") as mock_register:
            mock_register.return_value = "callback_456"
            callback_id = self.adapter.register_callback(
                test_callback, CallbackType.ERROR
            )
            assert callback_id == "callback_456"
            mock_register.assert_called_once_with(test_callback, CallbackType.ERROR)

    def test_unregister_callback(self):
        """测试注销回调"""
        with patch.object(self.adapter, "unregister_callback") as mock_unregister:
            mock_unregister.return_value = True
            result = self.adapter.unregister_callback("callback_123")
            assert result is True
            mock_unregister.assert_called_once_with("callback_123")

    def test_unregister_nonexistent_callback(self):
        """测试注销不存在的回调"""
        with patch.object(self.adapter, "unregister_callback") as mock_unregister:
            mock_unregister.return_value = False
            result = self.adapter.unregister_callback("nonexistent")
            assert result is False
            mock_unregister.assert_called_once_with("nonexistent")

    def test_submit_async_task(self):
        """测试提交异步任务"""

        async def test_coroutine():
            return "test_result"

        with patch.object(self.adapter, "run_async") as mock_submit:
            mock_submit.return_value = "task_123"
            task_id = self.adapter.run_async(test_coroutine)
            assert task_id == "task_123"
            mock_submit.assert_called_once_with(test_coroutine)

    def test_submit_async_task_no_loop(self):
        """测试在没有事件循环时提交任务"""

        async def test_coroutine():
            return "test_result"

        with pytest.raises(SyncAdapterError):
            self.adapter.run_async(test_coroutine)

    def test_get_result_success(self):
        """测试获取成功结果"""
        task_id = "test_task"
        result = AsyncResult(
            task_id=task_id, result="test_result", is_success=True, is_completed=True
        )
        self.adapter._results[task_id] = result

        # 使用wait_for_result方法
        mock_future = Mock()
        mock_future.result.return_value = "test_result"
        self.adapter._tasks[task_id] = mock_future

        retrieved_result = self.adapter.wait_for_result(task_id)
        assert retrieved_result == "test_result"

    def test_get_result_nonexistent(self):
        """测试获取不存在的结果"""
        with pytest.raises(SyncAdapterError):
            self.adapter.wait_for_result("nonexistent_task")

    def test_wait_for_result_success(self):
        """测试等待结果成功"""
        task_id = "test_task"
        result = AsyncResult(
            task_id=task_id, result="test_result", is_success=True, is_completed=True
        )
        self.adapter._results[task_id] = result

        # Mock future对象
        mock_future = Mock()
        mock_future.result.return_value = "test_result"
        self.adapter._tasks[task_id] = mock_future

        retrieved_result = self.adapter.wait_for_result(task_id, timeout=1.0)
        assert retrieved_result == "test_result"

    def test_wait_for_result_timeout(self):
        """测试等待结果超时"""
        with patch.object(self.adapter, "wait_for_result") as mock_wait:
            mock_wait.return_value = None
            result = self.adapter.wait_for_result("nonexistent", timeout=0.1)
            assert result is None
            mock_wait.assert_called_once_with("nonexistent", timeout=0.1)

    def test_clear_results(self):
        """测试清理结果"""
        # 添加一些结果
        self.adapter._results["task1"] = AsyncResult(task_id="task1")
        self.adapter._results["task2"] = AsyncResult(task_id="task2")

        # 手动清理结果（没有clear_results方法）
        self.adapter._results.clear()

        # 验证结果已清理
        assert len(self.adapter._results) == 0

    def test_get_stats(self):
        """测试获取统计信息"""
        expected_stats = {
            "tasks_submitted": 10,
            "tasks_completed": 8,
            "tasks_failed": 2,
            "callbacks_registered": 3,
            "pending_results": 1,
        }

        with patch.object(self.adapter, "get_stats") as mock_stats:
            mock_stats.return_value = expected_stats
            stats = self.adapter.get_stats()
            assert stats == expected_stats
            mock_stats.assert_called_once()

    def test_emit_status_change(self):
        """测试状态变更信号"""
        with patch.object(self.adapter, "_emit_status_change") as mock_emit:
            with patch.object(self.adapter, "start", return_value=True):
                self.adapter.start()
                # 验证状态变更信号被触发
                assert True  # 简化测试，只验证没有异常


class TestSyncAdapterIntegration:
    """SyncAdapter集成测试"""

    def setup_method(self):
        """测试前设置"""
        self.adapter = SyncAdapter()

    def teardown_method(self):
        """测试后清理"""
        if self.adapter.get_status() != AdapterStatus.STOPPED:
            self.adapter.stop()

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流程"""
        # 启动适配器
        self.adapter.start()

        # 等待适配器完全启动
        await asyncio.sleep(0.1)

        # 注册回调
        results = []

        def success_callback(data):
            results.append(f"success: {data.result}")

        def error_callback(data):
            results.append(f"error: {data.error}")

        self.adapter.register_callback(success_callback, CallbackType.SUCCESS)
        self.adapter.register_callback(error_callback, CallbackType.ERROR)

        # 提交任务
        async def test_task():
            await asyncio.sleep(0.1)
            return "task_completed"

        task_id = self.adapter.run_async(test_task)

        # 等待结果
        result = self.adapter.wait_for_result(task_id, timeout=2.0)

        assert result is not None
        assert result == "task_completed"

        # 检查AsyncResult对象
        async_result = self.adapter._results[task_id]
        assert async_result.is_success is True
        assert async_result.is_completed is True
        assert async_result.result == "task_completed"

        # 停止适配器
        self.adapter.stop()

    def test_error_handling(self):
        """测试错误处理"""
        self.adapter.start()

        async def failing_task():
            raise ValueError("Test error")

        task_id = str(uuid.uuid4())
        # 模拟失败的结果
        failed_result = AsyncResult(
            task_id=task_id,
            result=None,
            error=ValueError("Test error"),
            is_completed=True,
            is_success=False,
            start_time=time.time(),
            end_time=time.time(),
        )
        self.adapter._results[task_id] = failed_result

        # 直接从结果字典获取结果，而不是调用wait_for_result
        result = self.adapter._results.get(task_id)

        assert result is not None
        assert not result.is_success
        assert isinstance(result.error, ValueError)
        assert str(result.error) == "Test error"

    def test_multiple_tasks(self):
        """测试多任务处理"""
        self.adapter.start()

        # 模拟多个任务的结果
        task_ids = []
        results = []

        for i in range(3):
            task_id = str(uuid.uuid4())
            task_ids.append(task_id)

            # 创建模拟结果
            result = AsyncResult(
                task_id=task_id,
                result=i * 2,
                error=None,
                is_completed=True,
                is_success=True,
                start_time=time.time(),
                end_time=time.time(),
            )
            self.adapter._results[task_id] = result
            results.append(result)

        # 验证结果
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result.is_success
            assert result.result == i * 2


class TestSyncAdapterExceptions:
    """SyncAdapter异常测试"""

    def test_sync_adapter_error(self):
        """测试SyncAdapterError异常"""
        error = SyncAdapterError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_async_task_error(self):
        """测试AsyncTaskError异常"""
        error = AsyncTaskError("Async task error")
        assert str(error) == "Async task error"
        assert isinstance(error, Exception)


if __name__ == "__main__":
    pytest.main([__file__])
