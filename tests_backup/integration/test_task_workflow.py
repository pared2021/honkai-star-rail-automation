"""任务工作流集成测试

测试任务创建、执行、状态管理等完整流程。
"""

import asyncio
import pytest
import pytest_asyncio
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.models.task_models import Task, TaskType, TaskStatus, TaskPriority, TaskConfig
from src.application.task_application_service import TaskApplicationService, TaskCreateRequest
from src.services.task_application_service import TaskApplicationServiceError
from src.exceptions import TaskPermissionError
from src.application.automation_application_service import AutomationApplicationService
from src.core.task_executor import TaskExecutor, ExecutorStatus
from src.services.event_bus import EventBus, TaskCreatedEvent, TaskStatusChangedEvent
from src.services.event_bus import TaskEventType
from src.core.sync_adapter import EventBridge, CallbackManager, SyncCallback
from src.repositories.sqlite_task_repository import SQLiteTaskRepository
from src.repositories import (
    ConfigRepository, 
    TaskExecutionRepository,
    ExecutionActionRepository,
    ScreenshotRepository
)


class TestTaskWorkflow:
    """任务工作流集成测试"""
    
    @pytest_asyncio.fixture
    async def setup_services(self):
        """设置测试服务"""
        # 创建临时数据库
        db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        db_path = db_file.name
        db_file.close()
        
        try:
            # 初始化仓储
            task_repo = SQLiteTaskRepository(":memory:")
            await task_repo.initialize()
            config_repo = ConfigRepository(":memory:")
            execution_repo = TaskExecutionRepository(":memory:")
            action_repo = ExecutionActionRepository(":memory:")
            screenshot_repo = ScreenshotRepository(":memory:")
            
            # 初始化事件系统
            event_bus = EventBus()
            await event_bus.start()  # 启动事件总线
            event_bridge = EventBridge()
            event_bridge.start()
            
            # 初始化任务领域服务
            from src.services.task_service import TaskService
            task_domain_service = TaskService(
                task_repository=task_repo,
                event_bus=event_bus
            )
            
            # 创建Mock依赖
            from unittest.mock import Mock
            mock_game_detector = Mock()
            mock_automation_controller = Mock()
            
            automation_service = AutomationApplicationService(
                game_detector=mock_game_detector,
                automation_controller=mock_automation_controller,
                event_bus=event_bus
            )
            
            # 初始化任务执行器
            task_executor = TaskExecutor(
                task_service=task_domain_service,
                automation_service=automation_service,
                event_bus=event_bus
            )
            
            # 初始化服务
            task_service = TaskApplicationService(
                task_service=task_domain_service,
                event_bus=event_bus,
                task_executor=task_executor,
                automation_controller=automation_service,
                game_detector=mock_game_detector,
                database_manager=None
            )
            
            yield {
                'task_service': task_service,
                'automation_service': automation_service,
                'task_executor': task_executor,
                'event_bus': event_bus,
                'event_bridge': event_bridge,
                'repositories': {
                    'task': task_repo,
                    'config': config_repo,
                    'execution': execution_repo,
                    'action': action_repo,
                    'screenshot': screenshot_repo
                }
            }
            
        finally:
            # 停止所有服务
            try:
                if 'task_service' in locals():
                    await task_service.stop()
            except Exception as e:
                print(f"停止task_service失败: {e}")
            
            try:
                if 'automation_service' in locals():
                    await automation_service.close()
            except Exception as e:
                print(f"停止automation_service失败: {e}")
            
            try:
                if 'task_executor' in locals():
                    await task_executor.stop()
            except Exception as e:
                print(f"停止task_executor失败: {e}")
            
            # 清理
            await event_bus.stop()  # 停止事件总线
            event_bridge.stop()
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    @pytest.mark.asyncio
    async def test_manual_task_creation_and_execution(self, setup_services):
        """测试手动任务创建和执行"""
        services = setup_services
        task_service = services['task_service']
        task_executor = services['task_executor']
        event_bus = services['event_bus']
        
        # 事件收集器
        events = []
        
        def event_handler(event):
            events.append(event)
        
        event_bus.subscribe(event_type=TaskEventType.TASK_CREATED, handler=event_handler)
        event_bus.subscribe(event_type=TaskEventType.TASK_STATUS_CHANGED, handler=event_handler)
        
        # 创建手动任务
        task_config = TaskConfig(
            name="测试手动任务",
            description="这是一个测试任务",
            task_type=TaskType.MANUAL,
            priority=TaskPriority.MEDIUM
        )
        
        # 创建任务请求
        create_request = TaskCreateRequest(
            name=task_config.name,
            task_type=task_config.task_type,
            description=task_config.description,
            priority=task_config.priority
        )
        
        task_id = await task_service.create_task(create_request, "test_user")
        task = await task_service.get_task(task_id, "test_user")
        
        # 验证任务创建
        assert task.task_id is not None
        assert task.status == TaskStatus.PENDING.value
        assert task.config.get('name') == "测试手动任务"
        
        # 验证事件发布
        assert len(events) >= 1
        assert isinstance(events[0], TaskCreatedEvent)
        assert events[0].task_id == task.task_id
        
        # 启动任务执行器
        await task_executor.start()
        assert task_executor.get_status() == ExecutorStatus.RUNNING
        
        # 提交任务执行
        await task_executor.submit_task(task.task_id)
        
        # 等待任务状态变化
        await asyncio.sleep(0.1)
        
        # 获取更新后的任务
        updated_task = await task_service.get_task(task.task_id, "test_user")
        
        # 验证任务状态
        assert updated_task.status in [TaskStatus.RUNNING.value, TaskStatus.COMPLETED.value]
        
        # 停止任务执行器
        await task_executor.stop()
        
        # 验证状态变化事件
        status_events = [e for e in events if isinstance(e, TaskStatusChangedEvent)]
        assert len(status_events) > 0
    
    @pytest.mark.asyncio
    async def test_automation_task_workflow(self, setup_services):
        """测试自动化任务工作流"""
        services = setup_services
        task_service = services['task_service']
        automation_service = services['automation_service']
        task_executor = services['task_executor']
        
        # Mock自动化操作
        with patch.object(automation_service, 'detect_game_window') as mock_detect, \
             patch.object(automation_service, 'capture_screenshot') as mock_screenshot, \
             patch.object(automation_service, 'click_at_position') as mock_click:
            
            # 设置Mock返回值
            mock_detect.return_value = {
                'window_id': 'test_window',
                'title': '测试游戏窗口',
                'rect': {'x': 0, 'y': 0, 'width': 1920, 'height': 1080}
            }
            mock_screenshot.return_value = b'fake_screenshot_data'
            mock_click.return_value = True
            
            # 创建自动化任务
            automation_config = {
                'actions': [
                    {'type': 'detect_window', 'window_title': '测试游戏'},
                    {'type': 'capture_screenshot'},
                    {'type': 'click', 'x': 100, 'y': 200}
                ]
            }
            
            task_config = TaskConfig(
                name="自动化测试任务",
                description="测试自动化操作",
                task_type=TaskType.AUTOMATION,
                priority=TaskPriority.HIGH,
                automation_config=automation_config
            )
            
            # 创建任务请求
            create_request = TaskCreateRequest(
                name=task_config.name,
                task_type=task_config.task_type,
                description=task_config.description,
                priority=task_config.priority,
                automation_config=automation_config
            )
            
            task_id = await task_service.create_task(create_request, "test_user")
            task = await task_service.get_task(task_id, "test_user")
            
            # 启动任务执行器
            await task_executor.start()
            
            # 提交任务执行
            await task_executor.submit_task(task.task_id)
            
            # 等待任务执行
            await asyncio.sleep(0.2)
            
            # 验证自动化操作被调用
            mock_detect.assert_called()
            mock_screenshot.assert_called()
            mock_click.assert_called()
            
            # 获取任务状态
            updated_task = await task_service.get_task(task.task_id, "test_user")
            
            # 验证任务完成
            assert updated_task.status in [TaskStatus.RUNNING.value, TaskStatus.COMPLETED.value]
            
            await task_executor.stop()
    
    @pytest.mark.asyncio
    async def test_scheduled_task_workflow(self, setup_services):
        """测试计划任务工作流"""
        services = setup_services
        task_service = services['task_service']
        task_executor = services['task_executor']
        
        # 创建计划任务（1秒后执行）
        scheduled_time = datetime.now() + timedelta(seconds=1)
        
        task_config = TaskConfig(
            name="计划测试任务",
            description="测试计划执行",
            task_type=TaskType.SCHEDULED,
            priority=TaskPriority.LOW,
            scheduled_time=scheduled_time,
            schedule_config={'enabled': True, 'interval': 60}
        )
        
        # 创建任务请求
        create_request = TaskCreateRequest(
            name=task_config.name,
            task_type=task_config.task_type,
            description=task_config.description,
            priority=task_config.priority,
            schedule_config=task_config.schedule_config
        )
        
        task_id = await task_service.create_task(create_request, "test_user")
        task = await task_service.get_task(task_id, "test_user")
        
        # 验证任务创建
        assert task.status == TaskStatus.PENDING.value
        assert task.config.get('scheduled_time') == scheduled_time
        
        # 启动任务执行器
        await task_executor.start()
        
        # 等待计划时间到达
        await asyncio.sleep(1.2)
        
        # 获取任务状态
        updated_task = await task_service.get_task(task.task_id, "test_user")
        
        # 验证任务被执行
        assert updated_task.status in [TaskStatus.RUNNING.value, TaskStatus.COMPLETED.value]
        
        await task_executor.stop()
    
    @pytest.mark.asyncio
    async def test_task_dependency_workflow(self, setup_services):
        """测试任务依赖工作流"""
        services = setup_services
        task_service = services['task_service']
        task_executor = services['task_executor']
        
        # 创建父任务
        parent_config = TaskConfig(
            name="父任务",
            description="父任务描述",
            task_type=TaskType.MANUAL,
            priority=TaskPriority.HIGH
        )
        
        # 创建父任务请求
        parent_create_request = TaskCreateRequest(
            name=parent_config.name,
            task_type=parent_config.task_type,
            description=parent_config.description,
            priority=parent_config.priority
        )
        
        parent_task_id = await task_service.create_task(parent_create_request, "test_user")
        parent_task = await task_service.get_task(parent_task_id, "test_user")
        
        # 创建子任务
        child_config = TaskConfig(
            name="子任务",
            description="子任务描述",
            task_type=TaskType.MANUAL,
            priority=TaskPriority.MEDIUM
        )
        
        # 创建子任务请求
        child_create_request = TaskCreateRequest(
            name=child_config.name,
            task_type=child_config.task_type,
            description=child_config.description,
            priority=child_config.priority
        )
        
        child_task_id = await task_service.create_task(child_create_request, "test_user")
        child_task = await task_service.get_task(child_task_id, "test_user")
        
        # 设置任务依赖关系
        await task_service.add_task_dependency(child_task_id, parent_task_id, "test_user")
        
        # 验证任务关系
        assert child_task.parent_task_id == parent_task.task_id
        
        # 启动任务执行器
        await task_executor.start()
        
        # 提交父任务
        await task_executor.submit_task(parent_task.task_id)
        
        # 等待执行
        await asyncio.sleep(0.1)
        
        # 完成父任务
        await task_service.complete_task(parent_task.task_id, "父任务完成")
        
        # 提交子任务
        await task_executor.submit_task(child_task.task_id)
        
        # 等待执行
        await asyncio.sleep(0.1)
        
        # 获取任务状态
        parent_status = await task_service.get_task(parent_task.task_id)
        child_status = await task_service.get_task(child_task.task_id)
        
        # 验证任务状态
        assert parent_status.status == TaskStatus.COMPLETED.value
        assert child_status.status in [TaskStatus.RUNNING.value, TaskStatus.COMPLETED.value]
        
        await task_executor.stop()
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, setup_services):
        """测试错误处理工作流"""
        services = setup_services
        task_service = services['task_service']
        automation_service = services['automation_service']
        task_executor = services['task_executor']
        
        # Mock自动化操作抛出异常
        with patch.object(automation_service, 'detect_game_window') as mock_detect:
            mock_detect.side_effect = Exception("窗口检测失败")
            
            # 创建会失败的自动化任务
            task_config = TaskConfig(
                name="失败测试任务",
                description="测试错误处理",
                task_type=TaskType.AUTOMATION,
                priority=TaskPriority.MEDIUM,
                automation_config={'actions': [{'type': 'detect_window'}]}
            )
            
            # 创建任务请求
            create_request = TaskCreateRequest(
                name=task_config.name,
                task_type=task_config.task_type,
                description=task_config.description,
                priority=task_config.priority,
                automation_config=task_config.automation_config
            )
            
            task_id = await task_service.create_task(create_request, "test_user")
            task = await task_service.get_task(task_id, "test_user")
            
            # 启动任务执行器
            await task_executor.start()
            
            # 提交任务执行
            await task_executor.submit_task(task.task_id)
            
            # 等待任务执行和错误处理
            await asyncio.sleep(0.2)
            
            # 获取任务状态
            updated_task = await task_service.get_task(task.task_id)
            
            # 验证任务失败
            assert updated_task.status == TaskStatus.FAILED.value
            assert updated_task.error_message is not None
            assert "窗口检测失败" in updated_task.error_message
            
            await task_executor.stop()
    
    @pytest.mark.asyncio
    async def test_event_bridge_integration(self, setup_services):
        """测试事件桥接器集成"""
        services = setup_services
        task_service = services['task_service']
        event_bridge = services['event_bridge']
        
        # 同步回调收集器
        sync_results = []
        
        class TestSyncCallback(SyncCallback):
            def on_success(self, result, metadata=None):
                sync_results.append(('success', result, metadata))
            
            def on_error(self, error, metadata=None):
                sync_results.append(('error', error, metadata))
            
            def on_progress(self, progress, message="", metadata=None):
                sync_results.append(('progress', progress, message, metadata))
        
        # 添加同步回调
        sync_callback = TestSyncCallback()
        event_bridge.add_callback(sync_callback)
        
        # 在同步环境中运行异步任务创建
        async def create_task_async():
            task_config = TaskConfig(
                name="事件桥接测试任务",
                description="测试事件桥接",
                task_type=TaskType.MANUAL,
                priority=TaskPriority.LOW
            )
            
            # 创建任务请求
            create_request = TaskCreateRequest(
                name=task_config.name,
                task_type=task_config.task_type,
                description=task_config.description,
                priority=task_config.priority
            )
            
            task_id = await task_service.create_task(create_request, "test_user")
            return await task_service.get_task(task_id, "test_user")
        
        # 使用事件桥接器运行异步操作
        future = event_bridge.run_async_with_callback(create_task_async())
        
        # 等待完成
        task = future.result(timeout=5.0)
        
        # 等待回调处理
        await asyncio.sleep(0.1)
        
        # 验证任务创建成功
        assert task.task_id is not None
        assert task.status == TaskStatus.PENDING.value
        
        # 验证同步回调被调用
        assert len(sync_results) > 0
        success_callbacks = [r for r in sync_results if r[0] == 'success']
        assert len(success_callbacks) > 0
        
        # 移除回调
        event_bridge.remove_callback(sync_callback)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])