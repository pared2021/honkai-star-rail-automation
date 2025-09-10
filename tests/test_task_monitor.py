"""TaskMonitor模块测试。"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from collections import deque

from src.core.task_monitor import (
    TaskMonitor, TaskMetrics, SystemMetrics, PerformanceReport
)
from src.core.enhanced_task_executor import TaskStatus, TaskType, TaskPriority
from src.core.events import EventBus


class TestTaskMetrics:
    """TaskMetrics测试类。"""
    
    def test_task_metrics_creation(self):
        """测试TaskMetrics创建。"""
        start_time = datetime.now()
        metrics = TaskMetrics(
            task_id="test_task_1",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            start_time=start_time
        )
        
        assert metrics.task_id == "test_task_1"
        assert metrics.task_type == TaskType.DAILY_MISSION
        assert metrics.priority == TaskPriority.HIGH
        assert metrics.start_time == start_time
        assert metrics.end_time is None
        assert metrics.status == TaskStatus.PENDING
        assert metrics.retry_count == 0
        assert metrics.error_message is None
    
    def test_task_metrics_duration_property(self):
        """测试duration属性。"""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=5)
        
        metrics = TaskMetrics(
            task_id="test_task_1",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            start_time=start_time,
            end_time=end_time
        )
        
        assert abs(metrics.duration - 5.0) < 0.1
    
    def test_task_metrics_duration_without_end_time(self):
        """测试没有结束时间的duration。"""
        start_time = datetime.now() - timedelta(seconds=3)
        
        metrics = TaskMetrics(
            task_id="test_task_1",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            start_time=start_time
        )
        
        # 应该返回从开始到现在的时间
        assert metrics.duration >= 2.5
    
    def test_task_metrics_is_completed_property(self):
        """测试is_completed属性。"""
        metrics = TaskMetrics(
            task_id="test_task_1",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            start_time=datetime.now()
        )
        
        # 初始状态不是完成状态
        assert not metrics.is_completed
        
        # 设置为完成状态
        metrics.status = TaskStatus.COMPLETED
        assert metrics.is_completed
        
        # 设置为失败状态
        metrics.status = TaskStatus.FAILED
        assert metrics.is_completed
        
        # 设置为取消状态
        metrics.status = TaskStatus.CANCELLED
        assert metrics.is_completed
        
        # 设置为运行状态
        metrics.status = TaskStatus.RUNNING
        assert not metrics.is_completed


class TestSystemMetrics:
    """SystemMetrics测试类。"""
    
    def test_system_metrics_creation(self):
        """测试SystemMetrics创建。"""
        timestamp = datetime.now()
        metrics = SystemMetrics(
            timestamp=timestamp,
            active_tasks=5,
            queued_tasks=3,
            completed_tasks=10,
            failed_tasks=2
        )
        
        assert metrics.timestamp == timestamp
        assert metrics.active_tasks == 5
        assert metrics.queued_tasks == 3
        assert metrics.completed_tasks == 10
        assert metrics.failed_tasks == 2
        assert metrics.total_memory_usage == 0.0
        assert metrics.total_cpu_usage == 0.0


class TestTaskMonitor:
    """TaskMonitor测试类。"""
    
    @pytest.fixture
    def event_bus(self):
        """创建事件总线实例。"""
        return EventBus()
    
    @pytest.fixture
    def task_monitor(self, event_bus):
        """创建TaskMonitor实例。"""
        return TaskMonitor(event_bus=event_bus, max_history=100)
    
    def test_task_monitor_creation(self, task_monitor):
        """测试TaskMonitor创建。"""
        assert task_monitor.max_history == 100
        assert len(task_monitor.task_metrics) == 0
        assert len(task_monitor.completed_metrics) == 0
        assert task_monitor.monitoring_enabled is True
        assert task_monitor.monitoring_interval == 30.0
    
    @pytest.mark.asyncio
    async def test_on_task_submitted(self, task_monitor):
        """测试任务提交事件处理。"""
        event_data = {
            "execution_id": "test_exec_1",
            "task_config": Mock(
                task_type=TaskType.DAILY_MISSION,
                priority=TaskPriority.HIGH
            )
        }
        
        await task_monitor._on_task_submitted(event_data)
        
        assert "test_exec_1" in task_monitor.task_metrics
        metrics = task_monitor.task_metrics["test_exec_1"]
        assert metrics.task_id == "test_exec_1"
        assert metrics.task_type == TaskType.DAILY_MISSION
        assert metrics.priority == TaskPriority.HIGH
        assert metrics.status == TaskStatus.QUEUED
    
    @pytest.mark.asyncio
    async def test_on_task_started(self, task_monitor):
        """测试任务开始事件处理。"""
        # 先添加一个任务
        task_monitor.task_metrics["test_exec_1"] = TaskMetrics(
            task_id="test_exec_1",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            start_time=datetime.now()
        )
        
        event_data = {"execution_id": "test_exec_1"}
        await task_monitor._on_task_started(event_data)
        
        metrics = task_monitor.task_metrics["test_exec_1"]
        assert metrics.status == TaskStatus.RUNNING
    
    @pytest.mark.asyncio
    async def test_on_task_completed(self, task_monitor):
        """测试任务完成事件处理。"""
        # 先添加一个任务
        task_monitor.task_metrics["test_exec_1"] = TaskMetrics(
            task_id="test_exec_1",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            start_time=datetime.now()
        )
        
        mock_execution = Mock()
        mock_execution.execution_time = 2.5
        
        event_data = {
            "execution_id": "test_exec_1",
            "task_execution": mock_execution
        }
        
        await task_monitor._on_task_completed(event_data)
        
        # 任务应该从活跃列表移除
        assert "test_exec_1" not in task_monitor.task_metrics
        
        # 任务应该添加到完成历史
        assert len(task_monitor.completed_metrics) == 1
        completed_metrics = task_monitor.completed_metrics[0]
        assert completed_metrics.task_id == "test_exec_1"
        assert completed_metrics.status == TaskStatus.COMPLETED
        assert completed_metrics.execution_time == 2.5
    
    @pytest.mark.asyncio
    async def test_on_task_failed(self, task_monitor):
        """测试任务失败事件处理。"""
        # 先添加一个任务
        task_monitor.task_metrics["test_exec_1"] = TaskMetrics(
            task_id="test_exec_1",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            start_time=datetime.now()
        )
        
        mock_execution = Mock()
        mock_execution.execution_time = 1.5
        mock_execution.retry_count = 2
        
        event_data = {
            "execution_id": "test_exec_1",
            "task_execution": mock_execution,
            "error": Exception("测试错误")
        }
        
        await task_monitor._on_task_failed(event_data)
        
        # 任务应该从活跃列表移除
        assert "test_exec_1" not in task_monitor.task_metrics
        
        # 任务应该添加到完成历史
        assert len(task_monitor.completed_metrics) == 1
        failed_metrics = task_monitor.completed_metrics[0]
        assert failed_metrics.task_id == "test_exec_1"
        assert failed_metrics.status == TaskStatus.FAILED
        assert failed_metrics.execution_time == 1.5
        assert failed_metrics.retry_count == 2
        assert "测试错误" in failed_metrics.error_message
    
    @pytest.mark.asyncio
    async def test_on_task_cancelled(self, task_monitor):
        """测试任务取消事件处理。"""
        # 先添加一个任务
        task_monitor.task_metrics["test_exec_1"] = TaskMetrics(
            task_id="test_exec_1",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            start_time=datetime.now()
        )
        
        mock_execution = Mock()
        
        event_data = {
            "execution_id": "test_exec_1",
            "task_execution": mock_execution
        }
        
        await task_monitor._on_task_cancelled(event_data)
        
        # 任务应该从活跃列表移除
        assert "test_exec_1" not in task_monitor.task_metrics
        
        # 任务应该添加到完成历史
        assert len(task_monitor.completed_metrics) == 1
        cancelled_metrics = task_monitor.completed_metrics[0]
        assert cancelled_metrics.task_id == "test_exec_1"
        assert cancelled_metrics.status == TaskStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, task_monitor):
        """测试启动和停止监控。"""
        # 启动监控
        await task_monitor.start_monitoring()
        assert task_monitor.monitoring_enabled is True
        assert task_monitor.monitoring_task is not None
        assert not task_monitor.monitoring_task.done()
        
        # 停止监控
        await task_monitor.stop_monitoring()
        assert task_monitor.monitoring_enabled is False
    
    @pytest.mark.asyncio
    async def test_collect_system_metrics(self, task_monitor):
        """测试收集系统指标。"""
        # 添加一些测试数据
        task_monitor.task_metrics["running_1"] = TaskMetrics(
            task_id="running_1",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            start_time=datetime.now(),
            status=TaskStatus.RUNNING
        )
        
        task_monitor.task_metrics["queued_1"] = TaskMetrics(
            task_id="queued_1",
            task_type=TaskType.RESOURCE_FARMING,
            priority=TaskPriority.MEDIUM,
            start_time=datetime.now(),
            status=TaskStatus.QUEUED
        )
        
        # 添加完成的任务
        completed_metrics = TaskMetrics(
            task_id="completed_1",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.LOW,
            start_time=datetime.now() - timedelta(minutes=30),
            end_time=datetime.now() - timedelta(minutes=25),
            status=TaskStatus.COMPLETED,
            execution_time=5.0
        )
        task_monitor.completed_metrics.append(completed_metrics)
        
        # 收集系统指标
        metrics = await task_monitor._collect_system_metrics()
        
        assert metrics.active_tasks == 1  # 1个运行中的任务
        assert metrics.queued_tasks == 1  # 1个排队的任务
        assert metrics.completed_tasks == 1  # 1个完成的任务（最近1小时内）
        assert metrics.failed_tasks == 0
        assert metrics.average_execution_time == 5.0
    
    def test_get_current_status(self, task_monitor):
        """测试获取当前状态。"""
        # 添加一些测试数据
        task_monitor.task_metrics["task_1"] = TaskMetrics(
            task_id="task_1",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            start_time=datetime.now(),
            status=TaskStatus.RUNNING
        )
        
        task_monitor.task_metrics["task_2"] = TaskMetrics(
            task_id="task_2",
            task_type=TaskType.RESOURCE_FARMING,
            priority=TaskPriority.MEDIUM,
            start_time=datetime.now(),
            status=TaskStatus.QUEUED
        )
        
        status = task_monitor.get_current_status()
        
        assert status["active_tasks"] == 2
        assert status["status_distribution"]["running"] == 1
        assert status["status_distribution"]["queued"] == 1
        assert status["type_distribution"]["daily_mission"] == 1
        assert status["type_distribution"]["resource_farming"] == 1
        assert status["priority_distribution"][2] == 1  # TaskPriority.HIGH.value
        assert status["priority_distribution"][3] == 1  # TaskPriority.MEDIUM.value
    
    def test_get_task_metrics(self, task_monitor):
        """测试获取任务指标。"""
        # 添加活跃任务
        active_metrics = TaskMetrics(
            task_id="active_task",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            start_time=datetime.now()
        )
        task_monitor.task_metrics["active_task"] = active_metrics
        
        # 添加完成任务
        completed_metrics = TaskMetrics(
            task_id="completed_task",
            task_type=TaskType.RESOURCE_FARMING,
            priority=TaskPriority.MEDIUM,
            start_time=datetime.now(),
            status=TaskStatus.COMPLETED
        )
        task_monitor.completed_metrics.append(completed_metrics)
        
        # 测试获取活跃任务
        result = task_monitor.get_task_metrics("active_task")
        assert result is not None
        assert result.task_id == "active_task"
        
        # 测试获取完成任务
        result = task_monitor.get_task_metrics("completed_task")
        assert result is not None
        assert result.task_id == "completed_task"
        
        # 测试获取不存在的任务
        result = task_monitor.get_task_metrics("nonexistent_task")
        assert result is None
    
    def test_get_performance_summary(self, task_monitor):
        """测试获取性能摘要。"""
        # 添加一些测试数据
        now = datetime.now()
        
        # 完成的任务
        completed_metrics = TaskMetrics(
            task_id="completed_1",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            start_time=now - timedelta(hours=2),
            end_time=now - timedelta(hours=1, minutes=55),
            status=TaskStatus.COMPLETED,
            execution_time=3.0
        )
        task_monitor.completed_metrics.append(completed_metrics)
        
        # 失败的任务
        failed_metrics = TaskMetrics(
            task_id="failed_1",
            task_type=TaskType.RESOURCE_FARMING,
            priority=TaskPriority.MEDIUM,
            start_time=now - timedelta(hours=1, minutes=30),
            end_time=now - timedelta(hours=1, minutes=25),
            status=TaskStatus.FAILED,
            execution_time=2.0
        )
        task_monitor.completed_metrics.append(failed_metrics)
        
        summary = task_monitor.get_performance_summary(hours=24)
        
        assert summary["period_hours"] == 24
        assert summary["total_tasks"] == 2
        assert summary["completed_tasks"] == 1
        assert summary["failed_tasks"] == 1
        assert summary["cancelled_tasks"] == 0
        assert summary["success_rate"] == 50.0
        assert summary["execution_time_stats"]["average"] == 3.0
        assert summary["task_type_distribution"]["daily_mission"] == 1
        assert summary["task_type_distribution"]["resource_farming"] == 1
    
    def test_get_performance_summary_empty(self, task_monitor):
        """测试空数据的性能摘要。"""
        summary = task_monitor.get_performance_summary(hours=24)
        
        assert summary["total_tasks"] == 0
        assert "message" in summary
    
    def test_generate_performance_report(self, task_monitor):
        """测试生成性能报告。"""
        # 添加测试数据
        now = datetime.now()
        start_time = now - timedelta(hours=2)
        end_time = now
        
        completed_metrics = TaskMetrics(
            task_id="completed_1",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            start_time=start_time + timedelta(minutes=10),
            end_time=start_time + timedelta(minutes=15),
            status=TaskStatus.COMPLETED,
            execution_time=5.0
        )
        task_monitor.completed_metrics.append(completed_metrics)
        
        failed_metrics = TaskMetrics(
            task_id="failed_1",
            task_type=TaskType.RESOURCE_FARMING,
            priority=TaskPriority.MEDIUM,
            start_time=start_time + timedelta(minutes=30),
            end_time=start_time + timedelta(minutes=32),
            status=TaskStatus.FAILED,
            execution_time=2.0,
            error_message="测试错误"
        )
        task_monitor.completed_metrics.append(failed_metrics)
        
        report = task_monitor.generate_performance_report(start_time, end_time)
        
        assert report.start_time == start_time
        assert report.end_time == end_time
        assert report.total_tasks == 2
        assert report.completed_tasks == 1
        assert report.failed_tasks == 1
        assert report.cancelled_tasks == 0
        assert report.average_execution_time == 5.0
        assert report.error_rate == 50.0
        assert len(report.task_type_stats) == 2
        assert len(report.priority_stats) == 2
        assert len(report.top_errors) == 1
        assert report.top_errors[0]["error"] == "测试错误"
    
    def test_generate_performance_report_empty(self, task_monitor):
        """测试空数据的性能报告。"""
        start_time = datetime.now() - timedelta(hours=2)
        end_time = datetime.now()
        
        report = task_monitor.generate_performance_report(start_time, end_time)
        
        assert report.total_tasks == 0
        assert report.completed_tasks == 0
        assert report.failed_tasks == 0
        assert report.average_execution_time == 0.0
        assert report.error_rate == 0.0
    
    @patch('builtins.open')
    @patch('json.dump')
    def test_export_metrics_json(self, mock_json_dump, mock_open, task_monitor):
        """测试导出JSON格式指标。"""
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        task_monitor.export_metrics("/test/path.json", "json")
        
        mock_open.assert_called_once_with("/test/path.json", 'w', encoding='utf-8')
        mock_json_dump.assert_called_once()
    
    @patch('builtins.open')
    @patch('csv.writer')
    def test_export_metrics_csv(self, mock_csv_writer, mock_open, task_monitor):
        """测试导出CSV格式指标。"""
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_writer = Mock()
        mock_csv_writer.return_value = mock_writer
        
        # 添加测试数据
        metrics = TaskMetrics(
            task_id="test_task",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            start_time=datetime.now()
        )
        task_monitor.task_metrics["test_task"] = metrics
        
        task_monitor.export_metrics("/test/path.csv", "csv")
        
        mock_open.assert_called_once_with("/test/path.csv", 'w', newline='', encoding='utf-8')
        mock_writer.writerow.assert_called()  # 至少调用一次writerow
    
    def test_export_metrics_invalid_format(self, task_monitor):
        """测试导出无效格式。"""
        with pytest.raises(ValueError, match="不支持的导出格式"):
            task_monitor.export_metrics("/test/path.txt", "invalid")