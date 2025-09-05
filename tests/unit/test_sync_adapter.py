"""SyncAdapter模块单元测试。"""

import asyncio
import threading
import time
import unittest
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import Future

from src.core.sync_adapter import (
    SyncAdapter,
    AdapterStatus,
    CallbackType,
    SyncAdapterError,
    AsyncTaskError,
    CallbackData,
    AsyncResult,
    CallbackInfo,
    AsyncCallback,
    SyncCallback
)


class MockAsyncCallback(AsyncCallback):
    """测试用异步回调类。"""
    
    def __init__(self):
        self.success_called = False
        self.error_called = False
        self.progress_called = False
        self.last_result = None
        self.last_error = None
        self.last_progress = 0.0
    
    async def on_success(self, result, metadata=None):
        """成功回调。"""
        self.success_called = True
        self.last_result = result
    
    async def on_error(self, error, metadata=None):
        """错误回调。"""
        self.error_called = True
        self.last_error = error
    
    async def on_progress(self, progress, message="", metadata=None):
        """进度回调。"""
        self.progress_called = True
        self.last_progress = progress


class MockSyncCallback(SyncCallback):
    """测试用同步回调类。"""
    
    def __init__(self):
        self.success_called = False
        self.error_called = False
        self.progress_called = False
        self.last_result = None
        self.last_error = None
        self.last_progress = 0.0
    
    def on_success(self, result, metadata=None):
        """成功回调。"""
        self.success_called = True
        self.last_result = result
    
    def on_error(self, error, metadata=None):
        """错误回调。"""
        self.error_called = True
        self.last_error = error
    
    def on_progress(self, progress, message="", metadata=None):
        """进度回调。"""
        self.progress_called = True
        self.last_progress = progress


class TestCallbackData(unittest.TestCase):
    """CallbackData测试类。"""
    
    def test_init_default(self):
        """测试默认初始化。"""
        data = CallbackData(
            task_id="test_task",
            callback_type=CallbackType.SUCCESS
        )
        
        self.assertEqual(data.task_id, "test_task")
        self.assertEqual(data.callback_type, CallbackType.SUCCESS)
        self.assertIsNone(data.data)
        self.assertIsNone(data.error)
        self.assertEqual(data.progress, 0.0)
        self.assertIsNone(data.metadata)
        self.assertIsInstance(data.timestamp, float)
    
    def test_init_with_values(self):
        """测试带值初始化。"""
        test_error = Exception("test error")
        test_metadata = {"key": "value"}
        
        data = CallbackData(
            task_id="test_task",
            callback_type=CallbackType.ERROR,
            data="test_data",
            error=test_error,
            progress=0.5,
            metadata=test_metadata
        )
        
        self.assertEqual(data.task_id, "test_task")
        self.assertEqual(data.callback_type, CallbackType.ERROR)
        self.assertEqual(data.data, "test_data")
        self.assertEqual(data.error, test_error)
        self.assertEqual(data.progress, 0.5)
        self.assertEqual(data.metadata, test_metadata)


class TestAsyncResult(unittest.TestCase):
    """AsyncResult测试类。"""
    
    def test_init_default(self):
        """测试默认初始化。"""
        result = AsyncResult(task_id="test_task")
        
        self.assertEqual(result.task_id, "test_task")
        self.assertFalse(result.is_success)
        self.assertIsNone(result.result)
        self.assertIsNone(result.error)
        self.assertFalse(result.is_completed)
        self.assertEqual(result.progress, 0.0)
        self.assertIsInstance(result.start_time, float)
        self.assertIsNone(result.end_time)
        self.assertIsNone(result.metadata)
    
    def test_init_with_values(self):
        """测试带值初始化。"""
        test_error = Exception("test error")
        test_metadata = {"key": "value"}
        
        result = AsyncResult(
            task_id="test_task",
            is_success=True,
            result="test_result",
            error=test_error,
            is_completed=True,
            progress=1.0,
            end_time=time.time(),
            metadata=test_metadata
        )
        
        self.assertEqual(result.task_id, "test_task")
        self.assertTrue(result.is_success)
        self.assertEqual(result.result, "test_result")
        self.assertEqual(result.error, test_error)
        self.assertTrue(result.is_completed)
        self.assertEqual(result.progress, 1.0)
        self.assertIsNotNone(result.end_time)
        self.assertEqual(result.metadata, test_metadata)


class TestCallbackInfo(unittest.TestCase):
    """CallbackInfo测试类。"""
    
    def test_init_default(self):
        """测试默认初始化。"""
        callback_func = Mock()
        info = CallbackInfo(
            callback_id="test_callback",
            callback_type=CallbackType.SUCCESS,
            callback_func=callback_func
        )
        
        self.assertEqual(info.callback_id, "test_callback")
        self.assertEqual(info.callback_type, CallbackType.SUCCESS)
        self.assertEqual(info.callback_func, callback_func)
        self.assertIsNone(info.task_id)
        self.assertTrue(info.active)
        self.assertIsInstance(info.created_time, float)
        self.assertIsNone(info.metadata)
    
    def test_init_with_values(self):
        """测试带值初始化。"""
        callback_func = Mock()
        test_metadata = {"key": "value"}
        
        info = CallbackInfo(
            callback_id="test_callback",
            callback_type=CallbackType.ERROR,
            callback_func=callback_func,
            task_id="test_task",
            active=False,
            metadata=test_metadata
        )
        
        self.assertEqual(info.callback_id, "test_callback")
        self.assertEqual(info.callback_type, CallbackType.ERROR)
        self.assertEqual(info.callback_func, callback_func)
        self.assertEqual(info.task_id, "test_task")
        self.assertFalse(info.active)
        self.assertEqual(info.metadata, test_metadata)


class TestSyncAdapter(unittest.TestCase):
    """SyncAdapter测试类。"""
    
    def setUp(self):
        """设置测试环境。"""
        self.adapter = SyncAdapter(max_workers=2, max_queue_size=10)
    
    def tearDown(self):
        """清理测试环境。"""
        if self.adapter._status == AdapterStatus.RUNNING:
            self.adapter.stop()
    
    def test_init(self):
        """测试初始化。"""
        self.assertEqual(self.adapter._max_workers, 2)
        self.assertEqual(self.adapter._max_queue_size, 10)
        self.assertEqual(self.adapter._status, AdapterStatus.STOPPED)
        self.assertIsNone(self.adapter._loop)
        self.assertIsNone(self.adapter._loop_thread)
        self.assertIsNone(self.adapter._callback_thread)
        self.assertIsNotNone(self.adapter._callback_queue)
    
    def test_status_property(self):
        """测试状态属性。"""
        self.assertEqual(self.adapter.get_status(), AdapterStatus.STOPPED)
    
    def test_is_running_property(self):
        """测试运行状态属性。"""
        self.assertEqual(self.adapter.get_status(), AdapterStatus.STOPPED)
        
        # 启动后应该为RUNNING
        self.adapter.start()
        self.assertEqual(self.adapter.get_status(), AdapterStatus.RUNNING)
        
        # 停止后应该为STOPPED
        self.adapter.stop()
        self.assertEqual(self.adapter.get_status(), AdapterStatus.STOPPED)
    
    @patch('threading.Thread')
    @patch('asyncio.new_event_loop')
    def test_start(self, mock_new_loop, mock_thread):
        """测试启动适配器。"""
        mock_loop = Mock()
        mock_new_loop.return_value = mock_loop
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        self.adapter.start()
        
        self.assertEqual(self.adapter._status, AdapterStatus.STARTING)
        mock_new_loop.assert_called_once()
        self.assertEqual(mock_thread.call_count, 2)  # loop_thread and callback_thread
    
    def test_start_already_running(self):
        """测试重复启动。"""
        self.adapter.start()
        
        # 重复启动应该返回True（已经在运行）
        result = self.adapter.start()
        self.assertTrue(result)
    
    def test_stop_not_running(self):
        """测试停止未运行的适配器。"""
        # 停止未运行的适配器应该返回True（已经停止）
        result = self.adapter.stop()
        self.assertTrue(result)
    
    def test_stop_running(self):
        """测试停止运行中的适配器。"""
        self.adapter.start()
        
        result = self.adapter.stop()
        
        self.assertTrue(result)
        self.assertEqual(self.adapter.get_status(), AdapterStatus.STOPPED)
    
    async def async_test_function(self):
        """测试用异步函数。"""
        await asyncio.sleep(0.01)
        return "test_result"
    
    async def async_error_function(self):
        """测试用异步错误函数。"""
        await asyncio.sleep(0.01)
        raise ValueError("test error")
    
    def test_submit_async_task_not_running(self):
        """测试在未运行状态下提交任务。"""
        with self.assertRaises(SyncAdapterError):
            self.adapter.submit_async_task(self.async_test_function())
    
    def test_submit_async_task_running(self):
        """测试在运行状态下提交异步任务。"""
        self.adapter.start()
        
        async def test_coro():
            return "test_result"
        
        task_id = self.adapter.submit_async_task(test_coro)
        
        self.assertIsNotNone(task_id)
        self.assertIsInstance(task_id, str)
    
    def test_register_callback_success(self):
        """测试注册回调成功。"""
        callback = MockSyncCallback()
        
        callback_id = self.adapter.register_callback(
            callback.on_success,
            CallbackType.SUCCESS
        )
        
        self.assertIsNotNone(callback_id)
        self.assertIn(callback_id, self.adapter._callbacks)
    
    def test_register_callback_with_task_id(self):
        """测试注册带任务ID的回调。"""
        callback = MockSyncCallback()
        
        callback_id = self.adapter.register_callback(
            callback.on_success,
            CallbackType.SUCCESS,
            task_id="test_task"
        )
        
        self.assertIsNotNone(callback_id)
        callback_info = self.adapter._callbacks[callback_id]
        self.assertEqual(callback_info.task_id, "test_task")
    
    def test_unregister_callback_success(self):
        """测试注销回调成功。"""
        callback = MockSyncCallback()
        callback_id = self.adapter.register_callback(
            callback.on_success,
            CallbackType.SUCCESS
        )
        
        result = self.adapter.unregister_callback(callback_id)
        
        self.assertTrue(result)
        self.assertNotIn(callback_id, self.adapter._callbacks)
    
    def test_unregister_callback_not_found(self):
        """测试注销不存在的回调。"""
        result = self.adapter.unregister_callback("nonexistent_id")
        
        self.assertFalse(result)
    
    def test_get_stats(self):
        """测试获取统计信息。"""
        stats = self.adapter.get_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("tasks_submitted", stats)
        self.assertIn("tasks_completed", stats)
        self.assertIn("tasks_failed", stats)
    
    def test_register_callback_with_correct_params(self):
        """测试使用正确参数注册回调。"""
        callback = MockSyncCallback()
        
        callback_id = self.adapter.register_callback(
            callback.on_success,
            CallbackType.SUCCESS,
            task_id="test_task"
        )
        
        self.assertIsNotNone(callback_id)
        callback_info = self.adapter._callbacks[callback_id]
        self.assertEqual(callback_info.task_id, "test_task")
    
    def test_wait_for_result_not_found(self):
        """测试等待不存在任务的结果。"""
        with self.assertRaises(SyncAdapterError):
            self.adapter.wait_for_result("non_existent_task")


if __name__ == '__main__':
    unittest.main()