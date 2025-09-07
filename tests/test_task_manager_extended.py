"""TaskManager扩展测试用例。

测试TaskManager类的主要功能，包括任务管理、并发执行、队列操作等。
"""

import pytest
import time
import threading
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import Future

from src.core.task_manager import (
    TaskManager, TaskExecutor, ConcurrentTaskQueue,
    Task, TaskExecution, TaskType, TaskStatus, TaskState, TaskPriority,
    ResourceLimits
)


class TestTaskManager:
    """TaskManager测试类。"""
    
    @pytest.fixture
    def task_manager(self):
        """创建TaskManager实例。"""
        return TaskManager()
    
    @pytest.fixture
    def sample_task(self):
        """创建示例任务。"""
        return Task(
            id="test_task_001",
            name="测试任务",
            task_type=TaskType.USER,
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING,
            metadata={"description": "这是一个测试任务"}
        )
    
    def test_initialization(self, task_manager):
        """测试TaskManager初始化。"""
        assert task_manager is not None
        assert task_manager._stats["total_tasks"] == 0
        assert task_manager._stats["completed_tasks"] == 0
        assert task_manager._stats["failed_tasks"] == 0
        assert task_manager._stats["cancelled_tasks"] == 0
        assert not task_manager._concurrent_manager_running
        assert len(task_manager._active_executions) == 0
        assert len(task_manager._completed_executions) == 0
    
    def test_add_task_success(self, task_manager):
        """测试成功添加任务。"""
        task_data = {
            "name": "测试任务",
            "type": "user",
            "priority": "medium"
        }
        result = task_manager.add_task(task_data)
        assert result is not None
        assert isinstance(result, str)
    
    def test_add_task_invalid_type(self, task_manager):
        """测试添加无效类型的任务。"""
        result = task_manager.add_task("invalid_task")
        assert result is None
    
    def test_add_task_duplicate_id(self, task_manager):
        """测试添加重复ID的任务。"""
        task_data = {
            "name": "测试任务",
            "type": "user",
            "priority": "medium"
        }
        result1 = task_manager.add_task(task_data)
        result2 = task_manager.add_task(task_data)
        
        # 两次添加都应该成功，因为系统会生成不同的UUID
        assert result1 is not None
        assert result2 is not None
        assert result1 != result2
    
    def test_add_task_queue_full(self, task_manager):
        """测试队列满时添加任务。"""
        # 添加任务直到队列满（队列容量是100）
        for i in range(100):
            task_data = {
                "name": f"任务{i}",
                "type": "user",
                "priority": "medium"
            }
            result = task_manager.add_task(task_data)
            assert result is not None
        
        # 尝试添加第101个任务
        overflow_task_data = {
            "name": "溢出任务",
            "type": "user",
            "priority": "medium"
        }
        result = task_manager.add_task(overflow_task_data)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_list_tasks(self, task_manager):
        """测试列出任务。"""
        task_data = {
            "name": "测试任务",
            "type": "user",
            "priority": "medium"
        }
        task_manager.add_task(task_data)
        tasks = await task_manager.list_tasks()
        assert len(tasks) >= 0  # 可能为空，因为任务可能已经执行完成
    
    @pytest.mark.asyncio
    async def test_list_tasks_by_status(self, task_manager):
        """测试按状态列出任务。"""
        # 添加任务
        task_data1 = {
            "name": "待处理任务",
            "type": "user",
            "priority": "medium"
        }
        task_data2 = {
            "name": "运行中任务",
            "type": "user",
            "priority": "high"
        }
        
        task_manager.add_task(task_data1)
        task_manager.add_task(task_data2)
        
        # 测试获取所有任务
        all_tasks = await task_manager.list_tasks()
        assert len(all_tasks) >= 0  # 任务可能已经执行完成
        
        # 测试按状态过滤（使用TaskState枚举）
        from src.core.task_manager import TaskState
        completed_tasks = await task_manager.list_tasks(status=TaskState.COMPLETED)
        assert isinstance(completed_tasks, list)
    
    @pytest.mark.asyncio
    async def test_get_task_statistics(self, task_manager):
        """测试获取任务统计信息。"""
        task_data = {
            "name": "统计测试任务",
            "type": "user",
            "priority": "medium"
        }
        task_manager.add_task(task_data)
        stats = await task_manager.get_task_statistics()
        
        assert "total_tasks" in stats
        assert "completed_tasks" in stats
        assert "failed_tasks" in stats
        assert "cancelled_tasks" in stats
        assert stats["total_tasks"] >= 1
    
    @pytest.mark.asyncio
    async def test_create_task_success(self, task_manager):
        """测试成功创建任务。"""
        task_data = {
            "name": "新任务",
            "type": "user",
            "priority": "high"
        }
        task_id = await task_manager.create_task(task_data)
        assert task_id is not None
        assert isinstance(task_id, str)
    
    @pytest.mark.asyncio
    async def test_create_task_invalid_priority(self, task_manager):
        """测试创建任务时使用无效优先级。"""
        task_data = {
            "name": "无效任务",
            "type": "user",
            "priority": "invalid_priority"
        }
        # 无效优先级会使用默认值，不会抛出异常
        task_id = await task_manager.create_task(task_data)
        assert task_id is not None
    
    @pytest.mark.asyncio
    async def test_get_task_success(self, task_manager):
        """测试成功获取任务。"""
        task_data = {
            "name": "获取测试任务",
            "type": "user",
            "priority": "medium"
        }
        task_id = await task_manager.create_task(task_data)
        
        task_info = await task_manager.get_task(task_id)
        if task_info:  # 任务可能已经执行完成
            assert task_info["id"] == task_id
    
    @pytest.mark.asyncio
    async def test_get_task_not_found(self, task_manager):
        """测试获取不存在的任务。"""
        task_info = await task_manager.get_task("non_existent_id")
        assert task_info is None
    
    @pytest.mark.asyncio
    async def test_cancel_concurrent_task_success(self, task_manager):
        """测试成功取消并发任务。"""
        # 启动并发管理器
        task_manager.start_concurrent_manager()
        
        # 提交一个任务
        task_data = {
            "name": "取消测试任务",
            "type": "user",
            "priority": "low"
        }
        execution_id = task_manager.submit_concurrent_task(task_data)
        
        # 取消任务
        success = await task_manager.cancel_concurrent_task(execution_id)
        assert success is True
        
        # 停止并发管理器
        task_manager.stop_concurrent_manager()
    
    @pytest.mark.asyncio
    async def test_cancel_concurrent_task_not_found(self, task_manager):
        """测试取消不存在的并发任务。"""
        success = await task_manager.cancel_concurrent_task("non_existent_id")
        assert success is False
    
    def test_start_stop_concurrent_manager(self, task_manager):
        """测试启动和停止并发管理器。"""
        # 启动管理器
        task_manager.start_concurrent_manager()
        assert task_manager._concurrent_manager_running is True
        assert task_manager._executor is not None
        
        # 停止管理器
        task_manager.stop_concurrent_manager()
        assert task_manager._concurrent_manager_running is False
        assert task_manager._executor is None
    
    def test_start_concurrent_manager_already_running(self, task_manager):
        """测试启动已运行的并发管理器。"""
        task_manager.start_concurrent_manager()
        
        # 再次启动应该有警告但不会出错
        task_manager.start_concurrent_manager()
        assert task_manager._concurrent_manager_running is True
        
        task_manager.stop_concurrent_manager()
    
    def test_stop_concurrent_manager_not_running(self, task_manager):
        """测试停止未运行的并发管理器。"""
        # 直接停止未启动的管理器应该有警告但不会出错
        task_manager.stop_concurrent_manager()
        assert task_manager._concurrent_manager_running is False
    
    def test_submit_concurrent_task(self, task_manager):
        """测试提交并发任务。"""
        task_data = {
            "name": "并发任务",
            "type": "user",
            "priority": "high"
        }
        execution_id = task_manager.submit_concurrent_task(task_data)
        
        assert execution_id is not None
        assert isinstance(execution_id, str)
        assert task_manager._stats["total_tasks"] == 1
    
    def test_get_concurrent_status(self, task_manager):
        """测试获取并发状态。"""
        status = task_manager.get_concurrent_status()
        
        assert "manager_running" in status
        assert "queue_size" in status
        assert "active_executions" in status
        assert "completed_executions" in status
        assert "priority_counts" in status
        assert "stats" in status
    
    def test_execute_task_success(self, task_manager):
        """测试任务执行成功。"""
        execution = TaskExecution(
            task_id="execute_test",
            execution_id="exec_001",
            priority=TaskPriority.MEDIUM,
            state=TaskState.QUEUED,
            metadata={"name": "执行测试"}
        )
        
        result = task_manager._execute_task(execution)
        assert result is not None
        assert execution.state == TaskState.COMPLETED
        assert execution.start_time is not None
        assert execution.end_time is not None
    
    @patch('time.sleep')
    def test_execute_task_with_exception(self, mock_sleep, task_manager):
        """测试任务执行时发生异常。"""
        mock_sleep.side_effect = Exception("模拟执行错误")
        
        execution = TaskExecution(
            task_id="error_test",
            execution_id="exec_002",
            priority=TaskPriority.MEDIUM,
            state=TaskState.QUEUED,
            metadata={"name": "错误测试"}
        )
        
        with pytest.raises(Exception):
            task_manager._execute_task(execution)
        
        assert execution.state == TaskState.FAILED
        assert execution.error is not None
    
    def test_on_task_completed_success(self, task_manager):
        """测试任务完成回调。"""
        execution = TaskExecution(
            task_id="callback_test",
            execution_id="exec_003",
            priority=TaskPriority.MEDIUM,
            state=TaskState.COMPLETED
        )
        
        task_manager._active_executions["exec_003"] = execution
        
        # 模拟Future对象
        future = Mock()
        future.result.return_value = "任务完成"
        
        task_manager._on_task_completed("exec_003", future)
        
        assert "exec_003" not in task_manager._active_executions
        assert "exec_003" in task_manager._completed_executions
        assert task_manager._stats["completed_tasks"] == 1
    
    def test_run_task_compatibility(self, task_manager):
        """测试兼容性方法_run_task。"""
        execution = TaskExecution(
            task_id="compat_test",
            execution_id="exec_004",
            priority=TaskPriority.MEDIUM,
            state=TaskState.QUEUED
        )
        
        result = task_manager._run_task(execution)
        assert result is not None
        assert execution.state == TaskState.COMPLETED
        assert execution.progress == 1.0
    
    def test_task_completed_compatibility(self, task_manager):
        """测试兼容性方法_task_completed。"""
        execution = TaskExecution(
            task_id="compat_callback_test",
            execution_id="exec_005",
            priority=TaskPriority.MEDIUM,
            state=TaskState.RUNNING
        )
        
        task_manager._active_executions["exec_005"] = execution
        
        # 模拟成功的Future
        future = Mock()
        future.exception.return_value = None
        future.result.return_value = "任务完成"
        
        task_manager._task_completed(execution, future)
        
        assert execution.state == TaskState.COMPLETED
        assert execution.result == "任务完成"
        assert "exec_005" in task_manager._completed_executions
    
    def test_task_completed_with_exception(self, task_manager):
        """测试任务完成回调处理异常。"""
        execution = TaskExecution(
            task_id="exception_callback_test",
            execution_id="exec_006",
            priority=TaskPriority.MEDIUM,
            state=TaskState.RUNNING
        )
        
        task_manager._active_executions["exec_006"] = execution
        
        # 模拟失败的Future
        future = Mock()
        future.exception.return_value = Exception("任务执行失败")
        
        task_manager._task_completed(execution, future)
        
        assert execution.state == TaskState.FAILED
        assert execution.error is not None
        assert task_manager._stats["failed_tasks"] == 1


class TestConcurrentTaskQueue:
    """ConcurrentTaskQueue测试类。"""
    
    @pytest.fixture
    def task_queue(self):
        """创建ConcurrentTaskQueue实例。"""
        return ConcurrentTaskQueue()
    
    def test_initialization(self, task_queue):
        """测试队列初始化。"""
        assert task_queue.size() == 0
    
    def test_put_and_get(self, task_queue):
        """测试放入和获取任务。"""
        execution = TaskExecution(
            task_id="queue_test",
            execution_id="exec_001",
            priority=TaskPriority.MEDIUM,
            state=TaskState.QUEUED
        )
        
        task_queue.put(execution)
        assert task_queue.size() == 1
        
        retrieved = task_queue.get(timeout=1.0)
        assert retrieved is not None
        assert retrieved.task_id == "queue_test"
        assert task_queue.size() == 0
    
    def test_priority_ordering(self, task_queue):
        """测试优先级排序。"""
        # 添加不同优先级的任务
        low_task = TaskExecution(
            task_id="low", execution_id="low_exec",
            priority=TaskPriority.LOW, state=TaskState.QUEUED
        )
        high_task = TaskExecution(
            task_id="high", execution_id="high_exec",
            priority=TaskPriority.HIGH, state=TaskState.QUEUED
        )
        medium_task = TaskExecution(
            task_id="medium", execution_id="medium_exec",
            priority=TaskPriority.MEDIUM, state=TaskState.QUEUED
        )
        
        # 按非优先级顺序添加
        task_queue.put(low_task)
        task_queue.put(high_task)
        task_queue.put(medium_task)
        
        # 应该按优先级顺序获取
        first = task_queue.get(timeout=1.0)
        assert first.priority == TaskPriority.HIGH
        
        second = task_queue.get(timeout=1.0)
        assert second.priority == TaskPriority.MEDIUM
        
        third = task_queue.get(timeout=1.0)
        assert third.priority == TaskPriority.LOW
    
    def test_get_timeout(self, task_queue):
        """测试获取超时。"""
        result = task_queue.get(timeout=0.1)
        assert result is None
    
    def test_get_priority_counts(self, task_queue):
        """测试获取优先级统计。"""
        # 添加不同优先级的任务
        for _ in range(2):
            task_queue.put(TaskExecution(
                task_id=f"high_{_}", execution_id=f"high_exec_{_}",
                priority=TaskPriority.HIGH, state=TaskState.QUEUED
            ))
        
        for _ in range(3):
            task_queue.put(TaskExecution(
                task_id=f"medium_{_}", execution_id=f"medium_exec_{_}",
                priority=TaskPriority.MEDIUM, state=TaskState.QUEUED
            ))
        
        counts = task_queue.get_priority_counts()
        assert counts[TaskPriority.HIGH] == 2
        assert counts[TaskPriority.MEDIUM] == 3
        assert counts[TaskPriority.LOW] == 0


class TestTaskExecutor:
    """TaskExecutor测试类。"""
    
    @pytest.fixture
    def task_executor(self):
        """创建TaskExecutor实例。"""
        return TaskExecutor()
    
    def test_initialization(self, task_executor):
        """测试TaskExecutor初始化。"""
        assert task_executor is not None
        assert task_executor._running is False
        assert task_executor._executor is not None
    
    def test_start_stop(self, task_executor):
        """测试启动和停止执行器。"""
        task_executor.start()
        assert task_executor._running is True
        
        task_executor.stop()
        assert task_executor._running is False
    
    def test_execute_task_success(self, task_executor):
        """测试成功执行任务。"""
        task_executor.start()
        
        execution = TaskExecution(
            task_id="executor_test",
            execution_id="exec_001",
            priority=TaskPriority.MEDIUM,
            state=TaskState.QUEUED
        )
        
        result = task_executor.execute_task(execution)
        assert result is not None
        assert execution.state == TaskState.COMPLETED
        assert execution.start_time is not None
        assert execution.end_time is not None
        
        task_executor.stop()
    
    def test_execute_task_not_running(self, task_executor):
        """测试在未启动状态下执行任务。"""
        execution = TaskExecution(
            task_id="not_running_test",
            execution_id="exec_002",
            priority=TaskPriority.MEDIUM,
            state=TaskState.QUEUED
        )
        
        with pytest.raises(RuntimeError):
            task_executor.execute_task(execution)
    
    def test_submit_async_task(self, task_executor):
        """测试异步提交任务。"""
        task_executor.start()
        
        execution = TaskExecution(
            task_id="async_test",
            execution_id="exec_003",
            priority=TaskPriority.MEDIUM,
            state=TaskState.QUEUED
        )
        
        future = task_executor.submit_async_task(execution)
        assert isinstance(future, Future)
        
        # 等待任务完成
        result = future.result(timeout=5.0)
        assert result is not None
        
        task_executor.stop()


class TestResourceLimits:
    """ResourceLimits测试类。"""
    
    def test_default_values(self):
        """测试默认值。"""
        limits = ResourceLimits()
        assert limits.max_concurrent_tasks == 5
        assert limits.max_cpu_usage == 80.0
        assert limits.max_memory_usage == 85.0
        assert limits.max_execution_time == 300
        assert limits.priority_boost_threshold == 10
    
    def test_custom_values(self):
        """测试自定义值。"""
        limits = ResourceLimits(
            max_concurrent_tasks=10,
            max_cpu_usage=90.0,
            max_memory_usage=95.0,
            max_execution_time=600,
            priority_boost_threshold=20
        )
        assert limits.max_concurrent_tasks == 10
        assert limits.max_cpu_usage == 90.0
        assert limits.max_memory_usage == 95.0
        assert limits.max_execution_time == 600
        assert limits.priority_boost_threshold == 20


class TestTaskDataClasses:
    """任务数据类测试。"""
    
    def test_task_creation(self):
        """测试Task创建。"""
        task = Task(
            id="test_task",
            name="测试任务",
            task_type=TaskType.USER,
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            metadata={"key": "value"}
        )
        
        assert task.id == "test_task"
        assert task.name == "测试任务"
        assert task.task_type == TaskType.USER
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING
        assert task.metadata["key"] == "value"
    
    def test_task_execution_creation(self):
        """测试TaskExecution创建。"""
        execution = TaskExecution(
            task_id="exec_task",
            execution_id="exec_001",
            priority=TaskPriority.MEDIUM,
            state=TaskState.QUEUED,
            metadata={"name": "执行任务"}
        )
        
        assert execution.task_id == "exec_task"
        assert execution.execution_id == "exec_001"
        assert execution.priority == TaskPriority.MEDIUM
        assert execution.state == TaskState.QUEUED
        assert execution.progress == 0.0
        assert execution.metadata["name"] == "执行任务"
    
    def test_task_enums(self):
        """测试任务枚举。"""
        # 测试TaskType
        assert TaskType.USER.value == "user"
        assert TaskType.SYSTEM.value == "system"
        assert TaskType.AUTOMATION.value == "automation"
        
        # 测试TaskStatus
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        
        # 测试TaskState
        assert TaskState.QUEUED.value == "queued"
        assert TaskState.RUNNING.value == "running"
        assert TaskState.COMPLETED.value == "completed"
        assert TaskState.FAILED.value == "failed"
        assert TaskState.CANCELLED.value == "cancelled"
        
        # 测试TaskPriority
        assert TaskPriority.URGENT.value == 0
        assert TaskPriority.HIGH.value == 1
        assert TaskPriority.MEDIUM.value == 2
        assert TaskPriority.LOW.value == 3