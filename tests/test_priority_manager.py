"""PriorityManager模块测试。"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from dataclasses import dataclass
from typing import Dict, Any

from src.core.priority_manager import (
    PriorityManager, PriorityAdjustmentReason, SchedulingStrategy,
    PriorityAdjustment, TaskMetrics, ResourceQuota,
    DeadlinePriorityCalculator, PerformancePriorityCalculator,
    DependencyPriorityCalculator, ResourcePriorityCalculator
)
from src.core.enhanced_task_executor import TaskType, TaskPriority, TaskConfig
from src.core.events import EventBus


class TestPriorityAdjustment:
    """测试PriorityAdjustment数据类。"""
    
    def test_priority_adjustment_creation(self):
        """测试优先级调整记录创建。"""
        adjustment = PriorityAdjustment(
            task_id="test_task",
            old_priority=TaskPriority.LOW,
            new_priority=TaskPriority.HIGH,
            reason=PriorityAdjustmentReason.DEADLINE_APPROACHING,
            timestamp=datetime.now(),
            adjustment_value=2.0,
            applied_by="user"
        )
        
        assert adjustment.task_id == "test_task"
        assert adjustment.old_priority == TaskPriority.LOW
        assert adjustment.new_priority == TaskPriority.HIGH
        assert adjustment.reason == PriorityAdjustmentReason.DEADLINE_APPROACHING
        assert adjustment.adjustment_value == 2.0
        assert adjustment.applied_by == "user"
        assert isinstance(adjustment.context, dict)


class TestTaskMetrics:
    """测试TaskMetrics数据类。"""
    
    def test_task_metrics_creation(self):
        """测试任务指标创建。"""
        deadline = datetime.now() + timedelta(hours=2)
        metrics = TaskMetrics(
            task_id="test_task",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            estimated_duration=120.0,
            deadline=deadline
        )
        
        assert metrics.task_id == "test_task"
        assert metrics.task_type == TaskType.DAILY_MISSION
        assert metrics.priority == TaskPriority.HIGH
        assert metrics.estimated_duration == 120.0
        assert metrics.deadline == deadline
        assert metrics.actual_duration == 0.0
        assert metrics.success_rate == 1.0
        assert metrics.retry_count == 0
        assert isinstance(metrics.resource_usage, dict)
        assert isinstance(metrics.dependencies, set)
        assert isinstance(metrics.dependents, set)


class TestResourceQuota:
    """测试ResourceQuota数据类。"""
    
    def test_resource_quota_creation(self):
        """测试资源配额创建。"""
        quota = ResourceQuota(
            cpu_quota=2.0,
            memory_quota=1.5,
            network_quota=1.0,
            concurrent_limit=3,
            priority_weight=2.5
        )
        
        assert quota.cpu_quota == 2.0
        assert quota.memory_quota == 1.5
        assert quota.network_quota == 1.0
        assert quota.concurrent_limit == 3
        assert quota.priority_weight == 2.5
    
    def test_resource_quota_defaults(self):
        """测试资源配额默认值。"""
        quota = ResourceQuota()
        
        assert quota.cpu_quota == 1.0
        assert quota.memory_quota == 1.0
        assert quota.network_quota == 1.0
        assert quota.concurrent_limit == 1
        assert quota.priority_weight == 1.0


class TestDeadlinePriorityCalculator:
    """测试基于截止时间的优先级计算器。"""
    
    def test_no_deadline(self):
        """测试无截止时间的情况。"""
        calculator = DeadlinePriorityCalculator()
        metrics = TaskMetrics(
            task_id="test",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.MEDIUM
        )
        
        score = calculator.calculate_priority(metrics, {})
        assert score == 0.0
    
    def test_expired_deadline(self):
        """测试已过期的截止时间。"""
        calculator = DeadlinePriorityCalculator()
        metrics = TaskMetrics(
            task_id="test",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.MEDIUM,
            deadline=datetime.now() - timedelta(hours=1)
        )
        
        score = calculator.calculate_priority(metrics, {})
        assert score == 1000.0
    
    def test_urgent_deadline(self):
        """测试紧急截止时间（1小时内）。"""
        calculator = DeadlinePriorityCalculator()
        metrics = TaskMetrics(
            task_id="test",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.MEDIUM,
            deadline=datetime.now() + timedelta(minutes=30)
        )
        
        score = calculator.calculate_priority(metrics, {})
        assert score == 100.0
    
    def test_daily_deadline(self):
        """测试1天内的截止时间。"""
        calculator = DeadlinePriorityCalculator()
        metrics = TaskMetrics(
            task_id="test",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.MEDIUM,
            deadline=datetime.now() + timedelta(hours=12)
        )
        
        score = calculator.calculate_priority(metrics, {})
        assert score == 50.0


class TestPerformancePriorityCalculator:
    """测试基于性能的优先级计算器。"""
    
    def test_high_success_rate(self):
        """测试高成功率任务。"""
        calculator = PerformancePriorityCalculator()
        metrics = TaskMetrics(
            task_id="test",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.MEDIUM,
            success_rate=0.95,
            estimated_duration=30.0,
            retry_count=0,
            average_wait_time=120.0
        )
        
        score = calculator.calculate_priority(metrics, {})
        assert score > 0
        # 高成功率应该得到较高分数
        assert score >= 19.0  # 0.95 * 20 = 19
    
    def test_retry_penalty(self):
        """测试重试次数惩罚。"""
        calculator = PerformancePriorityCalculator()
        metrics = TaskMetrics(
            task_id="test",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.MEDIUM,
            success_rate=1.0,
            retry_count=3
        )
        
        score = calculator.calculate_priority(metrics, {})
        # 重试次数会降低分数
        assert score == max(0.0, 20.0 - 3 * 5.0)  # 20 - 15 = 5


class TestDependencyPriorityCalculator:
    """测试基于依赖关系的优先级计算器。"""
    
    def test_many_dependents(self):
        """测试被多个任务依赖的情况。"""
        calculator = DependencyPriorityCalculator()
        metrics = TaskMetrics(
            task_id="test",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.MEDIUM
        )
        metrics.dependents = {"task1", "task2", "task3"}
        
        score = calculator.calculate_priority(metrics, {'pending_dependencies': 0})
        # 3个依赖者 * 10 + 无待处理依赖 30 = 60
        assert score == 60.0
    
    def test_pending_dependencies(self):
        """测试有待处理依赖的情况。"""
        calculator = DependencyPriorityCalculator()
        metrics = TaskMetrics(
            task_id="test",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.MEDIUM
        )
        
        score = calculator.calculate_priority(metrics, {'pending_dependencies': 2})
        # 0个依赖者 + 2个待处理依赖 * -5 = -10，但最小为0
        assert score == 0.0


class TestResourcePriorityCalculator:
    """测试基于资源的优先级计算器。"""
    
    def test_low_resource_usage(self):
        """测试低资源使用率。"""
        calculator = ResourcePriorityCalculator()
        metrics = TaskMetrics(
            task_id="test",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.MEDIUM,
            resource_usage={'cpu': 0.2, 'memory': 0.3}
        )
        
        score = calculator.calculate_priority(metrics, {'system_load': 0.5})
        # 总资源使用 0.5，分数 = 20 - 0.5 = 19.5
        assert score == 19.5
    
    def test_no_resource_usage(self):
        """测试无资源使用信息。"""
        calculator = ResourcePriorityCalculator()
        metrics = TaskMetrics(
            task_id="test",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.MEDIUM
        )
        
        score = calculator.calculate_priority(metrics, {'system_load': 0.5})
        assert score == 15.0  # 默认中等优先级
    
    def test_high_system_load(self):
        """测试高系统负载情况。"""
        calculator = ResourcePriorityCalculator()
        metrics = TaskMetrics(
            task_id="test",
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.MEDIUM,
            resource_usage={'cpu': 2.0}
        )
        
        score = calculator.calculate_priority(metrics, {'system_load': 0.9})
        # 高负载时重任务会被惩罚
        expected = max(0.0, 20.0 - 2.0 - 2.0 * 0.5)  # 20 - 2 - 1 = 17
        assert score == expected


class TestPriorityManager:
    """测试PriorityManager类。"""
    
    @pytest.fixture
    def event_bus(self):
        """创建事件总线实例。"""
        return EventBus()
    
    @pytest.fixture
    def priority_manager(self, event_bus):
        """创建优先级管理器实例。"""
        return PriorityManager(event_bus=event_bus, strategy=SchedulingStrategy.PRIORITY_FIRST)
    
    def test_initialization(self, priority_manager):
        """测试初始化。"""
        assert priority_manager.strategy == SchedulingStrategy.PRIORITY_FIRST
        assert len(priority_manager.priority_calculators) == 4
        assert len(priority_manager.resource_quotas) == 4
        assert priority_manager.auto_adjustment_enabled is True
        assert priority_manager.adjustment_interval == 60.0
    
    @pytest.mark.asyncio
    async def test_task_submitted_event(self, priority_manager):
        """测试任务提交事件处理。"""
        task_config = TaskConfig(
            task_id="test_task_001",
            task_type=TaskType.DAILY_MISSION,
            name="测试任务",
            priority=TaskPriority.HIGH
        )
        # 添加automation_config属性
        task_config.automation_config = {'estimated_duration': 120.0}
        
        event_data = {
            'execution_id': 'test_task_123',
            'task_config': task_config
        }
        
        await priority_manager._on_task_submitted(event_data)
        
        assert 'test_task_123' in priority_manager.task_metrics
        metrics = priority_manager.task_metrics['test_task_123']
        assert metrics.task_type == TaskType.DAILY_MISSION
        assert metrics.priority == TaskPriority.HIGH
        assert metrics.estimated_duration == 120.0
    
    @pytest.mark.asyncio
    async def test_task_started_event(self, priority_manager):
        """测试任务开始事件处理。"""
        # 先添加任务指标
        metrics = TaskMetrics(
            task_id='test_task_123',
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH
        )
        priority_manager.task_metrics['test_task_123'] = metrics
        
        event_data = {'execution_id': 'test_task_123'}
        await priority_manager._on_task_started(event_data)
        
        assert priority_manager.task_metrics['test_task_123'].last_execution is not None
    
    @pytest.mark.asyncio
    async def test_task_completed_event(self, priority_manager):
        """测试任务完成事件处理。"""
        # 先添加任务指标
        metrics = TaskMetrics(
            task_id='test_task_123',
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH
        )
        priority_manager.task_metrics['test_task_123'] = metrics
        
        # 模拟任务执行对象
        task_execution = Mock()
        task_execution.execution_time = 150.0
        
        event_data = {
            'execution_id': 'test_task_123',
            'task_execution': task_execution
        }
        
        await priority_manager._on_task_completed(event_data)
        
        # 任务完成后应该从指标中移除
        assert 'test_task_123' not in priority_manager.task_metrics
    
    @pytest.mark.asyncio
    async def test_task_failed_event(self, priority_manager):
        """测试任务失败事件处理。"""
        # 先添加任务指标
        metrics = TaskMetrics(
            task_id='test_task_123',
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH
        )
        priority_manager.task_metrics['test_task_123'] = metrics
        
        # 模拟任务执行对象
        task_execution = Mock()
        task_execution.retry_count = 2
        
        event_data = {
            'execution_id': 'test_task_123',
            'task_execution': task_execution
        }
        
        await priority_manager._on_task_failed(event_data)
        
        updated_metrics = priority_manager.task_metrics['test_task_123']
        assert updated_metrics.retry_count == 2
        assert updated_metrics.success_rate == max(0.1, 1.0 - 2 * 0.2)  # 0.6
    
    @pytest.mark.asyncio
    async def test_adjust_task_priority(self, priority_manager):
        """测试调整任务优先级。"""
        # 先添加任务指标
        metrics = TaskMetrics(
            task_id='test_task_123',
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.LOW
        )
        priority_manager.task_metrics['test_task_123'] = metrics
        
        # 调整优先级
        result = await priority_manager.adjust_task_priority(
            'test_task_123',
            TaskPriority.HIGH,
            PriorityAdjustmentReason.DEADLINE_APPROACHING,
            'test_user'
        )
        
        assert result is True
        assert priority_manager.task_metrics['test_task_123'].priority == TaskPriority.HIGH
        assert len(priority_manager.adjustment_history) == 1
        
        adjustment = priority_manager.adjustment_history[0]
        assert adjustment.task_id == 'test_task_123'
        assert adjustment.old_priority == TaskPriority.LOW
        assert adjustment.new_priority == TaskPriority.HIGH
        assert adjustment.reason == PriorityAdjustmentReason.DEADLINE_APPROACHING
        assert adjustment.applied_by == 'test_user'
    
    @pytest.mark.asyncio
    async def test_adjust_nonexistent_task(self, priority_manager):
        """测试调整不存在任务的优先级。"""
        result = await priority_manager.adjust_task_priority(
            'nonexistent_task',
            TaskPriority.HIGH,
            PriorityAdjustmentReason.USER_REQUEST
        )
        
        assert result is False
        assert len(priority_manager.adjustment_history) == 0
    
    def test_calculate_dynamic_priority(self, priority_manager):
        """测试动态优先级计算。"""
        # 添加任务指标
        metrics = TaskMetrics(
            task_id='test_task_123',
            task_type=TaskType.DAILY_MISSION,
            priority=TaskPriority.HIGH,
            success_rate=0.9,
            estimated_duration=60.0
        )
        priority_manager.task_metrics['test_task_123'] = metrics
        
        score = priority_manager.calculate_dynamic_priority('test_task_123')
        
        # 应该包含基础分数(100.0)加上各计算器的分数
        assert score >= 100.0
    
    def test_calculate_priority_nonexistent_task(self, priority_manager):
        """测试计算不存在任务的优先级。"""
        score = priority_manager.calculate_dynamic_priority('nonexistent_task')
        assert score == 0.0
    
    def test_get_task_queue_order_fifo(self, priority_manager):
        """测试FIFO调度策略。"""
        priority_manager.strategy = SchedulingStrategy.FIFO
        task_ids = ['task1', 'task2', 'task3']
        
        ordered_tasks = priority_manager.get_task_queue_order(task_ids)
        assert ordered_tasks == task_ids
    
    def test_get_task_queue_order_priority_first(self, priority_manager):
        """测试优先级优先调度策略。"""
        # 添加不同优先级的任务
        metrics1 = TaskMetrics('task1', TaskType.DAILY_MISSION, TaskPriority.LOW)
        metrics2 = TaskMetrics('task2', TaskType.RESOURCE_FARMING, TaskPriority.HIGH)
        metrics3 = TaskMetrics('task3', TaskType.BATTLE_PASS, TaskPriority.MEDIUM)
        
        priority_manager.task_metrics.update({
            'task1': metrics1,
            'task2': metrics2,
            'task3': metrics3
        })
        
        task_ids = ['task1', 'task2', 'task3']
        ordered_tasks = priority_manager.get_task_queue_order(task_ids)
        
        # task2(HIGH)应该排在最前面
        assert ordered_tasks[0] == 'task2'
    
    def test_get_task_queue_order_shortest_job_first(self, priority_manager):
        """测试最短作业优先调度策略。"""
        priority_manager.strategy = SchedulingStrategy.SHORTEST_JOB_FIRST
        
        # 添加不同执行时间的任务
        metrics1 = TaskMetrics('task1', TaskType.DAILY_MISSION, TaskPriority.MEDIUM, estimated_duration=120.0)
        metrics2 = TaskMetrics('task2', TaskType.RESOURCE_FARMING, TaskPriority.MEDIUM, estimated_duration=30.0)
        metrics3 = TaskMetrics('task3', TaskType.BATTLE_PASS, TaskPriority.MEDIUM, estimated_duration=90.0)
        
        priority_manager.task_metrics.update({
            'task1': metrics1,
            'task2': metrics2,
            'task3': metrics3
        })
        
        task_ids = ['task1', 'task2', 'task3']
        ordered_tasks = priority_manager.get_task_queue_order(task_ids)
        
        # task2(30s)应该排在最前面
        assert ordered_tasks[0] == 'task2'
        assert ordered_tasks[1] == 'task3'
        assert ordered_tasks[2] == 'task1'
    
    def test_get_resource_quota(self, priority_manager):
        """测试获取资源配额。"""
        quota = priority_manager.get_resource_quota(TaskPriority.HIGH)
        
        assert quota.cpu_quota == 1.5
        assert quota.memory_quota == 1.5
        assert quota.concurrent_limit == 3
        assert quota.priority_weight == 3.0
    
    def test_update_resource_quota(self, priority_manager):
        """测试更新资源配额。"""
        new_quota = ResourceQuota(
            cpu_quota=3.0,
            memory_quota=2.5,
            concurrent_limit=5
        )
        
        priority_manager.update_resource_quota(TaskPriority.HIGH, new_quota)
        
        updated_quota = priority_manager.get_resource_quota(TaskPriority.HIGH)
        assert updated_quota.cpu_quota == 3.0
        assert updated_quota.memory_quota == 2.5
        assert updated_quota.concurrent_limit == 5
    
    def test_get_priority_statistics(self, priority_manager):
        """测试获取优先级统计信息。"""
        stats = priority_manager.get_priority_statistics()
        
        assert 'total_adjustments' in stats
        assert 'automatic_adjustments' in stats
        assert 'manual_adjustments' in stats
        assert 'priority_distribution' in stats
        assert 'adjustment_frequency' in stats
        assert 'recent_adjustments' in stats
        assert 'adjustment_reasons' in stats
    
    def test_get_adjustment_history(self, priority_manager):
        """测试获取调整历史。"""
        # 添加一些调整记录
        adjustment1 = PriorityAdjustment(
            task_id='task1',
            old_priority=TaskPriority.LOW,
            new_priority=TaskPriority.MEDIUM,
            reason=PriorityAdjustmentReason.USER_REQUEST,
            timestamp=datetime.now() - timedelta(hours=2)
        )
        
        adjustment2 = PriorityAdjustment(
            task_id='task2',
            old_priority=TaskPriority.MEDIUM,
            new_priority=TaskPriority.HIGH,
            reason=PriorityAdjustmentReason.DEADLINE_APPROACHING,
            timestamp=datetime.now() - timedelta(minutes=30)
        )
        
        priority_manager.adjustment_history.extend([adjustment1, adjustment2])
        
        history = priority_manager.get_adjustment_history(hours=24)
        assert len(history) == 2
        # 应该按时间倒序排列
        assert history[0].timestamp > history[1].timestamp
    
    @pytest.mark.asyncio
    async def test_start_stop_auto_adjustment(self, priority_manager):
        """测试启动和停止自动调整。"""
        # 启动自动调整
        await priority_manager.start_auto_adjustment()
        assert priority_manager.auto_adjustment_enabled is True
        assert priority_manager.adjustment_task is not None
        
        # 停止自动调整
        await priority_manager.stop_auto_adjustment()
        assert priority_manager.auto_adjustment_enabled is False
    
    @pytest.mark.asyncio
    async def test_shutdown(self, priority_manager):
        """测试关闭优先级管理器。"""
        # 添加一些数据
        metrics = TaskMetrics('test_task', TaskType.DAILY_MISSION, TaskPriority.MEDIUM)
        priority_manager.task_metrics['test_task'] = metrics
        
        adjustment = PriorityAdjustment(
            task_id='test_task',
            old_priority=TaskPriority.LOW,
            new_priority=TaskPriority.MEDIUM,
            reason=PriorityAdjustmentReason.USER_REQUEST,
            timestamp=datetime.now()
        )
        priority_manager.adjustment_history.append(adjustment)
        
        await priority_manager.shutdown()
        
        # 数据应该被清理
        assert len(priority_manager.task_metrics) == 0
        assert len(priority_manager.adjustment_history) == 0
        assert priority_manager.auto_adjustment_enabled is False