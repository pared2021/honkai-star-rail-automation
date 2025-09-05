"""端到端集成测试

测试完整的任务执行流程，从任务创建到完成的整个生命周期。
"""

from datetime import datetime, timedelta
import os
import tempfile
from unittest.mock import AsyncMock, Mock, patch

import asyncio
import pytest
import pytest_asyncio

from src.application.automation_application_service import AutomationApplicationService
from src.application.task_application_service import TaskApplicationService
from src.core.error_handling import ErrorHandler, ExponentialBackoffStrategy
from src.core.task_executor import (
    ExecutorStatus,
    RetryPolicy,
    TaskExecutionContext,
    TaskExecutor,
)
from src.exceptions import TaskPermissionError
from src.models.task_models import Task, TaskConfig, TaskPriority, TaskStatus, TaskType
from src.repositories import (
    ConfigRepository,
    ExecutionActionRepository,
    ScreenshotRepository,
    TaskDependencyRepository,
    TaskExecutionRepository,
    TaskRepository,
)
from src.services.event_bus import EventBus, LoggingEventHandler, MetricsEventHandler


class TestEndToEnd:
    """端到端集成测试"""

    @pytest_asyncio.fixture
    async def setup_complete_system(self):
        """设置完整系统"""
        # 创建临时数据库
        db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        db_path = db_file.name
        db_file.close()

        try:
            # 初始化所有仓储
            task_repo = TaskRepository(db_path)
            config_repo = ConfigRepository(db_path)
            execution_repo = TaskExecutionRepository(db_path)
            action_repo = ExecutionActionRepository(db_path)
            screenshot_repo = ScreenshotRepository(db_path)
            dependency_repo = TaskDependencyRepository(db_path)

            # 初始化事件系统
            event_bus = EventBus()
            logging_handler = LoggingEventHandler()
            metrics_handler = MetricsEventHandler()
            event_bus.subscribe_all(logging_handler.handle)
            event_bus.subscribe_all(metrics_handler.handle)

            # 初始化错误处理
            error_handler = ErrorHandler(
                default_strategy=ExponentialBackoffStrategy(
                    base_delay=1.0, max_delay=60.0, exponential_base=2.0
                )
            )

            # 初始化任务领域服务
            from src.services.task_service import TaskService

            task_domain_service = TaskService(
                task_repository=task_repo, event_bus=event_bus
            )

            # 创建Mock的游戏检测器和自动化控制器
            from unittest.mock import Mock

            mock_game_detector = Mock()
            mock_automation_controller = Mock()

            automation_service = AutomationApplicationService(
                game_detector=mock_game_detector,
                automation_controller=mock_automation_controller,
                event_bus=event_bus,
            )

            # 初始化任务执行器
            task_executor = TaskExecutor(
                task_service=task_domain_service,
                automation_service=automation_service,
                event_bus=event_bus,
                max_concurrent_tasks=2,
            )

            # 初始化应用服务
            task_app_service = TaskApplicationService(
                task_service=task_domain_service,
                event_bus=event_bus,
                task_executor=task_executor,
                automation_controller=automation_service,
                game_detector=automation_service,
                database_manager=None,
            )

            yield {
                "task_service": task_app_service,
                "automation_service": automation_service,
                "task_executor": task_executor,
                "event_bus": event_bus,
                "error_handler": error_handler,
                "repositories": {
                    "task": task_repo,
                    "config": config_repo,
                    "execution": execution_repo,
                    "action": action_repo,
                    "screenshot": screenshot_repo,
                    "dependency": dependency_repo,
                },
                "handlers": {"logging": logging_handler, "metrics": metrics_handler},
            }

        finally:
            # 停止所有服务
            try:
                if "task_app_service" in locals():
                    await task_app_service.stop()
            except Exception as e:
                print(f"停止task_app_service失败: {e}")

            try:
                if "automation_service" in locals():
                    await automation_service.close()
            except Exception as e:
                print(f"停止automation_service失败: {e}")

            try:
                if "task_executor" in locals():
                    await task_executor.stop()
            except Exception as e:
                print(f"停止task_executor失败: {e}")

            try:
                if "event_bus" in locals():
                    await event_bus.stop()
            except Exception as e:
                print(f"停止event_bus失败: {e}")

            # 清理
            if os.path.exists(db_path):
                os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_complete_automation_workflow(self, setup_complete_system):
        """测试完整的自动化工作流程"""
        system = setup_complete_system
        task_service = system["task_service"]
        automation_service = system["automation_service"]
        task_executor = system["task_executor"]
        event_bus = system["event_bus"]

        # 事件收集器
        events = []

        def collect_events(event):
            events.append(event)

        event_bus.subscribe_all(collect_events)

        # Mock自动化操作
        with patch.object(
            automation_service, "detect_game_window"
        ) as mock_detect, patch.object(
            automation_service, "take_screenshot"
        ) as mock_screenshot, patch.object(
            automation_service, "find_element"
        ) as mock_find, patch.object(
            automation_service, "click_element"
        ) as mock_click, patch.object(
            automation_service, "execute_automation_sequence"
        ) as mock_sequence:

            # 设置Mock返回值
            from dataclasses import dataclass
            from typing import Dict, Tuple

            from src.application.automation_application_service import (
                AutomationApplicationService,
            )

            @dataclass
            class WindowInfo:
                hwnd: int
                title: str
                class_name: str
                rect: Tuple[int, int, int, int]

            @dataclass
            class ElementMatch:
                element_id: str
                confidence: float
                position: Dict[str, int]
                size: Dict[str, int]

            window_info = WindowInfo(
                hwnd=1234,
                title="星铁助手测试",
                class_name="GameWindowClass",
                rect=(0, 0, 1920, 1080),
            )
            mock_detect.return_value = window_info
            mock_screenshot.return_value = "workflow_screenshot.png"

            element_match = ElementMatch(
                element_id="start_button",
                confidence=0.95,
                position={"x": 960, "y": 540},
                size={"width": 120, "height": 50},
            )
            mock_find.return_value = element_match
            mock_click.return_value = True
            mock_sequence.return_value = True

            # 创建复杂的自动化任务
            automation_config = {
                "window_title": "星铁助手测试",
                "timeout": 30.0,
                "retry_count": 3,
                "actions": [
                    {
                        "type": "detect_window",
                        "window_title": "星铁助手测试",
                        "timeout": 10.0,
                    },
                    {"type": "take_screenshot", "save_path": "initial_state.png"},
                    {
                        "type": "find_element",
                        "element_type": "button",
                        "element_text": "开始游戏",
                        "confidence_threshold": 0.9,
                    },
                    {"type": "click", "target": "found_element", "click_type": "left"},
                    {"type": "wait", "duration": 2.0},
                    {"type": "take_screenshot", "save_path": "after_click.png"},
                ],
            }

            task_config = TaskConfig(
                name="完整自动化工作流程测试",
                description="测试从任务创建到完成的完整流程",
                task_type=TaskType.AUTOMATION,
                priority=TaskPriority.HIGH,
                automation_config=automation_config,
                timeout=60.0,
                retry_count=2,
            )

            # 启动任务执行器
            await task_executor.start()
            assert task_executor.get_status()["status"] == ExecutorStatus.RUNNING.value

            # 创建并提交任务
            task = await task_service.create_task(
                user_id="test_user", config=task_config
            )

            # 提交任务到执行器
            await task_executor.submit_task(task)

            # 等待任务执行完成
            await asyncio.sleep(2.0)

            # 验证任务状态
            completed_task = await task_service.get_task(task.task_id)
            assert completed_task.status in [TaskStatus.COMPLETED, TaskStatus.RUNNING]

            # 停止任务执行器
            await task_executor.stop()
            assert task_executor.get_status()["status"] == ExecutorStatus.STOPPED.value

            # 验证事件发布
            assert len(events) > 0

            # 检查关键事件
            event_types = [type(event).__name__ for event in events]
            assert "TaskCreatedEvent" in event_types
            assert "TaskExecutionStartedEvent" in event_types

    @pytest.mark.asyncio
    async def test_task_dependency_workflow(self, setup_complete_system):
        """测试任务依赖工作流程"""
        system = setup_complete_system
        task_service = system["task_service"]
        dependency_repo = system["repositories"]["dependency"]

        # 创建父任务
        parent_config = TaskConfig(
            name="父任务",
            description="需要先完成的任务",
            task_type=TaskType.MANUAL,
            priority=TaskPriority.HIGH,
        )

        parent_task = await task_service.create_task(
            user_id="test_user", config=parent_config
        )

        # 创建子任务
        child_config = TaskConfig(
            name="子任务",
            description="依赖父任务的任务",
            task_type=TaskType.MANUAL,
            priority=TaskPriority.MEDIUM,
            parent_task_id=parent_task.task_id,
        )

        child_task = await task_service.create_task(
            user_id="test_user", config=child_config
        )

        # 创建任务依赖关系
        await dependency_repo.create_dependency(
            task_id=child_task.task_id,
            depends_on_task_id=parent_task.task_id,
            dependency_type="prerequisite",
        )

        # 验证依赖关系
        dependencies = await dependency_repo.get_task_dependencies(child_task.task_id)
        assert len(dependencies) == 1
        assert dependencies[0].depends_on_task_id == parent_task.task_id

        # 尝试启动子任务（应该失败，因为父任务未完成）
        with pytest.raises(Exception):
            await task_service.start_task(child_task.task_id)

        # 完成父任务
        await task_service.start_task(parent_task.task_id)
        await task_service.complete_task(parent_task.task_id, "父任务完成")

        # 现在可以启动子任务
        await task_service.start_task(child_task.task_id)
        child_task_updated = await task_service.get_task(child_task.task_id)
        assert child_task_updated.status == TaskStatus.RUNNING.value

        # 完成子任务
        await task_service.complete_task(child_task.task_id, "子任务完成")
        child_task_final = await task_service.get_task(child_task.task_id)
        assert child_task_final.status == TaskStatus.COMPLETED.value

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, setup_complete_system):
        """测试错误处理和恢复机制"""
        system = setup_complete_system
        task_service = system["task_service"]
        automation_service = system["automation_service"]
        error_handler = system["error_handler"]

        # Mock自动化操作，模拟失败然后成功
        call_count = 0

        async def mock_failing_operation(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # 前两次调用失败
                raise Exception(f"模拟操作失败 (尝试 {call_count})")
            return True  # 第三次成功

        with patch.object(
            automation_service, "detect_game_window", side_effect=mock_failing_operation
        ):

            # 创建任务
            task_config = TaskConfig(
                name="错误处理测试任务",
                description="测试错误处理和重试机制",
                task_type=TaskType.AUTOMATION,
                priority=TaskPriority.MEDIUM,
                automation_config={
                    "window_title": "测试窗口",
                    "actions": [{"type": "detect_window"}],
                },
                retry_count=3,
            )

            task = await task_service.create_task(
                user_id="test_user", config=task_config
            )

            # 使用错误处理器包装操作
            @error_handler.with_error_handling
            async def execute_with_retry():
                return await automation_service.detect_game_window(
                    window_title="测试窗口"
                )

            # 执行操作（应该在重试后成功）
            result = await execute_with_retry()
            assert result is True
            assert call_count == 3  # 验证重试了3次

    @pytest.mark.asyncio
    async def test_concurrent_task_execution_with_limits(self, setup_complete_system):
        """测试并发任务执行限制"""
        system = setup_complete_system
        task_service = system["task_service"]
        task_executor = system["task_executor"]

        # 启动任务执行器（最大2个工作线程）
        await task_executor.start()

        # 创建多个任务
        tasks = []
        for i in range(5):
            config = TaskConfig(
                name=f"并发测试任务_{i+1}",
                description=f"测试并发执行限制_{i+1}",
                task_type=TaskType.MANUAL,
                priority=TaskPriority.MEDIUM,
            )

            task = await task_service.create_task(user_id="test_user", config=config)
            tasks.append(task)

        # 提交所有任务
        for task in tasks:
            await task_executor.submit_task(task)

        # 等待一段时间
        await asyncio.sleep(1.0)

        # 检查运行中的任务数量（应该不超过最大工作线程数）
        running_tasks = task_executor.get_running_tasks()
        assert len(running_tasks) <= 2

        # 停止执行器
        await task_executor.stop()

    @pytest.mark.asyncio
    async def test_data_consistency_across_operations(self, setup_complete_system):
        """测试跨操作的数据一致性"""
        system = setup_complete_system
        task_service = system["task_service"]
        repositories = system["repositories"]

        # 创建任务
        task_config = TaskConfig(
            name="数据一致性测试任务",
            description="测试数据一致性",
            task_type=TaskType.AUTOMATION,
            priority=TaskPriority.HIGH,
            automation_config={
                "window_title": "测试窗口",
                "actions": [{"type": "detect_window"}],
            },
        )

        task = await task_service.create_task(user_id="test_user", config=task_config)

        # 验证任务在所有相关表中的一致性

        # 1. 检查任务表
        db_task = await repositories["task"].get_by_id(task.task_id)
        assert db_task is not None
        assert db_task.name == "数据一致性测试任务"

        # 2. 启动任务并检查执行记录
        await task_service.start_task(task.task_id)

        # 验证任务状态更新
        updated_task = await repositories["task"].get_by_id(task.task_id)
        assert updated_task.status == TaskStatus.RUNNING.value

        # 3. 模拟执行操作并检查相关记录
        execution_id = "consistency_test_001"

        # 模拟截图操作
        with patch.object(
            system["automation_service"], "take_screenshot"
        ) as mock_screenshot:
            mock_screenshot.return_value = "consistency_screenshot.png"

            await system["automation_service"].take_screenshot(
                execution_id=execution_id, window_info=None
            )

            # 验证截图记录
            screenshots = await repositories["screenshot"].find_by_execution_id(
                execution_id
            )
            assert len(screenshots) > 0

        # 4. 完成任务并验证最终状态
        await task_service.complete_task(task.task_id, "数据一致性测试完成")

        final_task = await repositories["task"].get_by_id(task.task_id)
        assert final_task.status == TaskStatus.COMPLETED.value
        assert final_task.execution_result == "数据一致性测试完成"
        assert final_task.completed_at is not None

    @pytest.mark.asyncio
    async def test_system_performance_under_load(self, setup_complete_system):
        """测试系统在负载下的性能"""
        system = setup_complete_system
        task_service = system["task_service"]
        metrics_handler = system["handlers"]["metrics"]

        # 记录开始时间
        start_time = datetime.now()

        # 创建大量任务
        tasks = []
        for i in range(20):
            config = TaskConfig(
                name=f"性能测试任务_{i+1}",
                description=f"测试系统性能_{i+1}",
                task_type=TaskType.MANUAL,
                priority=TaskPriority.LOW,
            )

            task = await task_service.create_task(user_id="test_user", config=config)
            tasks.append(task)

        # 批量操作
        batch_operations = []
        for task in tasks[:10]:
            batch_operations.append(task_service.start_task(task.task_id))

        await asyncio.gather(*batch_operations)

        # 批量完成
        complete_operations = []
        for i, task in enumerate(tasks[:10]):
            complete_operations.append(
                task_service.complete_task(task.task_id, f"批量完成_{i+1}")
            )

        await asyncio.gather(*complete_operations)

        # 记录结束时间
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        # 验证性能（20个任务的创建和10个任务的执行应该在合理时间内完成）
        assert execution_time < 10.0  # 应该在10秒内完成

        # 验证所有操作都成功
        for task in tasks[:10]:
            final_task = await task_service.get_task(task.task_id)
            assert final_task.status == TaskStatus.COMPLETED.value

        # 检查指标收集
        assert metrics_handler.task_created_count >= 20
        assert metrics_handler.task_completed_count >= 10


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
