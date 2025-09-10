"""任务执行引擎测试模块.

测试TaskExecutor及相关组件的功能。
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from src.core.enhanced_task_executor import (
    EnhancedTaskExecutor, TaskConfig, TaskExecution, TaskStatus, 
    TaskType, TaskPriority, TaskQueue, TaskRunner, ExecutionResult
)
from src.core.task_game_integration import GameTaskRunner, BaseTaskRunner
from src.core.game_operator import GameOperator
from src.core.task_runners import (
    DailyMissionRunner, ResourceFarmingRunner,
    MailCollectionRunner, CustomTaskRunner
)
from src.core.task_monitor import TaskMonitor, TaskMetrics
from src.core.error_handler import ErrorHandler, ErrorSeverity
from src.core.priority_manager import PriorityManager
from src.core.task_game_integration import (
    GameTaskIntegration, GameTaskRunner, GameAction, GameActionType,
    create_click_action, create_swipe_action
)
from src.core.game_operator import GameOperator, OperationResult, ClickType
from src.core.game_detector import GameDetector, UIElement
from src.core.events import EventBus


class TestTaskConfig:
    """测试TaskConfig类。"""
    
    def test_task_config_creation(self):
        """测试任务配置创建。"""
        config = TaskConfig(
            task_id="test_task_1",
            task_type=TaskType.DAILY_MISSION,
            name="测试日常任务",
            priority=TaskPriority.HIGH,
            parameters={'mission_type': 'daily_login'}
        )
        
        assert config.task_type == TaskType.DAILY_MISSION
        assert config.priority == TaskPriority.HIGH
        assert config.parameters['mission_type'] == 'daily_login'
        assert config.retry_count == 3
        assert config.timeout == 300.0
    
    def test_task_config_validation(self):
        """测试任务配置验证。"""
        # 测试无效的重试次数
        with pytest.raises(ValueError):
            TaskConfig(
                task_id="invalid_task_1",
                task_type=TaskType.DAILY_MISSION,
                name="无效任务1",
                retry_count=-1
            )
        
        # 测试无效的超时时间
        with pytest.raises(ValueError):
            TaskConfig(
                task_id="invalid_task_2",
                task_type=TaskType.DAILY_MISSION,
                name="无效任务2",
                timeout=0
            )


class TestTaskExecution:
    """测试TaskExecution类。"""
    
    def test_task_execution_creation(self):
        """测试任务执行对象创建。"""
        config = TaskConfig(
            task_id="test_task_3",
            task_type=TaskType.DAILY_MISSION,
            name="测试任务3"
        )
        execution = TaskExecution(execution_id="test_execution", task_config=config)
        
        assert execution.task_config == config
        assert execution.status == TaskStatus.PENDING
        assert execution.progress == 0.0
        assert execution.retry_count == 0
        assert execution.result is None
        assert execution.error is None
    
    def test_task_execution_update_progress(self):
        """测试任务执行进度更新。"""
        config = TaskConfig(
            task_id="test_task_4",
            task_type=TaskType.DAILY_MISSION,
            name="测试任务4"
        )
        execution = TaskExecution(execution_id="daily_mission_execution", task_config=config)
        
        execution.progress = 50.0
        assert execution.progress == 50.0
    
    def test_task_execution_complete(self):
        """测试任务执行完成。"""
        config = TaskConfig(
            task_id="test_task_5",
            task_type=TaskType.DAILY_MISSION,
            name="测试任务5"
        )
        execution = TaskExecution(execution_id="resource_farming_execution", task_config=config)
        
        result = {'success': True, 'data': 'test'}
        execution.status = TaskStatus.COMPLETED
        execution.progress = 100.0
        execution.result = result
        execution.end_time = datetime.now()
        
        assert execution.status == TaskStatus.COMPLETED
        assert execution.progress == 100.0
        assert execution.result == result
        assert execution.end_time is not None
    
    def test_task_execution_fail(self):
        """测试任务执行失败。"""
        config = TaskConfig(
            task_id="test_task_6",
            task_type=TaskType.DAILY_MISSION,
            name="测试任务6"
        )
        execution = TaskExecution(execution_id="custom_execution", task_config=config)
        
        execution.status = TaskStatus.FAILED
        execution.error = Exception("测试错误")
        execution.end_time = datetime.now()
        
        assert execution.status == TaskStatus.FAILED
        assert str(execution.error) == "测试错误"
        assert execution.end_time is not None


class MockTaskRunner(TaskRunner):
    """模拟任务运行器。"""
    
    def __init__(self, task_type=TaskType.DAILY_MISSION, should_fail=False, execution_time=1.0):
        super().__init__(task_type)
        self.should_fail = should_fail
        self.execution_time = execution_time
    
    async def run(self, task_execution: TaskExecution, game_operator: GameOperator) -> ExecutionResult:
        """执行任务。"""
        await asyncio.sleep(self.execution_time)
        
        if self.should_fail:
            raise Exception("任务执行失败")
        
        result = {
            'success': True,
            'result': f"任务 {task_execution.task_config.task_id} 执行成功",
            'execution_time': self.execution_time
        }
        
        # 创建一个简单的action_config用于测试
        from src.core.action_executor import ActionConfig, ActionType
        action_config = ActionConfig(
            action_type=ActionType.CUSTOM,
            parameters={"test": "data"}
        )
        
        return ExecutionResult(
            status="completed",
            result=result,
            error=None,
            execution_time=self.execution_time
        )


class TestTaskQueue:
    """测试TaskQueue类。"""
    
    def test_task_queue_creation(self):
        """测试任务队列创建。"""
        queue = TaskQueue(max_size=10)
        assert queue.max_size == 10
        assert queue.size() == 0
        assert queue.is_empty()
    
    def test_task_queue_add_task(self):
        """测试添加任务到队列。"""
        queue = TaskQueue(max_size=2)
        config = TaskConfig(
            task_id="test_task_7",
            task_type=TaskType.DAILY_MISSION,
            name="测试任务7"
        )
        execution = TaskExecution(execution_id="daily_mission_task", task_config=config)
        
        queue.put(config)
        assert queue.size() == 1
        assert not queue.is_empty()
    
    def test_task_queue_full(self):
        """测试队列满时的行为。"""
        queue = TaskQueue(max_size=1)
        config1 = TaskConfig(
            task_id="test_task_1",
            name="测试任务1",
            task_type=TaskType.DAILY_MISSION
        )
        config2 = TaskConfig(
            task_id="test_task_2",
            name="测试任务2",
            task_type=TaskType.DAILY_MISSION
        )
        
        # 添加第一个任务
        queue.put(config1)
        
        # 尝试添加第二个任务（应该失败）
        with pytest.raises(Exception):
            queue.put(config2)
    
    def test_task_queue_get_next_task(self):
        """测试获取下一个任务。"""
        queue = TaskQueue()
        
        # 高优先级任务
        high_config = TaskConfig(
            task_id="high_task",
            task_type=TaskType.DAILY_MISSION,
            name="高优先级任务",
            priority=TaskPriority.HIGH
        )
        high_execution = TaskExecution(execution_id="high_exec", task_config=high_config)
        
        # 低优先级任务
        low_config = TaskConfig(
            task_id="low_task",
            task_type=TaskType.RESOURCE_FARMING,
            name="低优先级任务",
            priority=TaskPriority.LOW
        )
        low_execution = TaskExecution(execution_id="low_exec", task_config=low_config)
        
        # 先添加低优先级，再添加高优先级
        queue.put(low_config)
        queue.put(high_config)
        
        # 应该先获取高优先级任务
        next_task = queue.get()
        assert next_task == high_config
        assert queue.size() == 1


@pytest.mark.asyncio
class TestEnhancedTaskExecutor:
    """测试EnhancedTaskExecutor类。"""
    
    async def test_task_executor_creation(self):
        """测试任务执行器创建。"""
        executor = EnhancedTaskExecutor(max_workers=2)
        
        assert executor.executor._max_workers == 2
        assert len(executor.task_runners) == 0
        assert executor.task_queue.max_size == 1000  # 默认值
    
    async def test_register_runner(self):
        """测试注册任务运行器。"""
        executor = EnhancedTaskExecutor()
        runner = MockTaskRunner(TaskType.DAILY_MISSION)
        
        executor.register_task_runner(runner)
        
        assert TaskType.DAILY_MISSION in executor.task_runners
        assert executor.task_runners[TaskType.DAILY_MISSION] == runner
    
    async def test_submit_task(self):
        """测试提交任务。"""
        executor = EnhancedTaskExecutor()
        runner = MockTaskRunner(TaskType.DAILY_MISSION)
        executor.register_task_runner(runner)
        
        config = TaskConfig(
            task_id="test_task_8",
            task_type=TaskType.DAILY_MISSION,
            name="测试任务8"
        )
        execution = await executor.submit_task(config)
        
        assert execution is not None
        assert execution.execution_id is not None
        assert len(execution.execution_id) > 0
        
        # 检查任务是否在队列中
        assert executor.task_queue.size() == 1
    
    async def test_submit_task_without_runner(self):
        """测试提交没有运行器的任务。"""
        executor = EnhancedTaskExecutor()
        config = TaskConfig(
            task_id="test_task_9",
            task_type=TaskType.DAILY_MISSION,
            name="测试任务9"
        )
        
        with pytest.raises(ValueError):
            await executor.submit_task(config)
    
    async def test_execute_task_success(self):
        """测试任务执行成功。"""
        executor = EnhancedTaskExecutor()
        runner = MockTaskRunner(TaskType.DAILY_MISSION, execution_time=0.01)
        executor.register_task_runner(runner)
        
        config = TaskConfig(
            task_id="test_task_10",
            task_type=TaskType.DAILY_MISSION,
            name="测试任务10"
        )
        result = await executor.submit_and_wait(config)
        
        # 检查执行结果
        assert result.status == "completed"
        assert result.result is not None
    
    async def test_execute_task_failure(self):
        """测试任务执行失败。"""
        executor = EnhancedTaskExecutor()
        runner = MockTaskRunner(TaskType.DAILY_MISSION, execution_time=0.01, should_fail=True)
        executor.register_task_runner(runner)
        
        config = TaskConfig(
            task_id="test_task_11",
            task_type=TaskType.DAILY_MISSION,
            name="测试任务11",
            retry_count=1
        )
        result = await executor.submit_and_wait(config)
        
        # 检查执行结果
        assert result.status == "failed"
        assert result.error is not None
    
    async def test_cancel_task(self):
        """测试取消任务。"""
        executor = EnhancedTaskExecutor()
        runner = MockTaskRunner(TaskType.DAILY_MISSION, execution_time=1.0)  # 长时间执行
        executor.register_task_runner(runner)
        
        config = TaskConfig(
            task_id="test_task_12",
            task_type=TaskType.DAILY_MISSION,
            name="测试任务12"
        )
        execution = await executor.submit_task(config)
        
        # 取消任务
        success = await executor.cancel_task(execution.execution_id)
        assert success
        
        # 检查任务状态
        updated_execution = await executor.get_task_status(execution.execution_id)
        assert updated_execution.status == TaskStatus.CANCELLED
    
    async def test_get_task_statistics(self):
        """测试获取任务统计。"""
        executor = EnhancedTaskExecutor()
        runner = MockTaskRunner(TaskType.DAILY_MISSION, execution_time=0.01)
        executor.register_task_runner(runner)
        
        # 提交多个任务
        for i in range(3):
            config = TaskConfig(
                task_id=f"test_task_{13+i}",
                task_type=TaskType.DAILY_MISSION,
                name=f"测试任务{13+i}"
            )
            result = await executor.submit_and_wait(config)
        
        # 检查执行结果
        assert result.status == "completed"
        
        stats = await executor.get_statistics()
        assert stats['completed_tasks'] >= 1


@pytest.mark.asyncio
class TestTaskRunners:
    """测试任务运行器。"""
    
    def test_game_task_runner_creation(self):
        """测试游戏任务运行器创建。"""
        from unittest.mock import Mock
        mock_operator = Mock()
        runner = GameTaskRunner(TaskType.DAILY_MISSION, mock_operator)
        assert runner.name == TaskType.DAILY_MISSION
        assert runner.game_operator == mock_operator
    
    async def test_daily_mission_runner(self):
        """测试日常任务运行器。"""
        # 模拟游戏操作器
        mock_game_operator = Mock()
        mock_game_operator.click = AsyncMock(return_value=OperationResult(success=True, execution_time=0.1, error_message="点击成功"))
        mock_game_operator.wait_for_condition = AsyncMock(return_value=OperationResult(success=True, execution_time=0.1, error_message="等待成功"))
        
        runner = DailyMissionRunner()
        
        config = TaskConfig(
            task_id="daily_mission_task",
            task_type=TaskType.DAILY_MISSION,
            name="日常登录任务",
            parameters={'mission_type': 'daily_login'}
        )
        execution = TaskExecution(execution_id="resource_farming_task", task_config=config)
        
        result = await runner.run(execution, mock_game_operator)
        
        assert result.status == "completed"
        assert 'mission_type' in result.result
    
    async def test_resource_farming_runner(self):
        """测试资源采集运行器。"""
        mock_game_operator = Mock()
        mock_game_operator.click = AsyncMock(return_value=OperationResult(success=True, execution_time=0.1, error_message="点击成功"))
        mock_game_operator.wait_for_condition = AsyncMock(return_value=OperationResult(success=True, execution_time=0.1, error_message="等待成功"))
        
        runner = ResourceFarmingRunner()
        
        config = TaskConfig(
            task_id="resource_farming_task",
            task_type=TaskType.RESOURCE_FARMING,
            name="资源采集任务",
            parameters={
                'resource_type': 'energy',
                'target_amount': 100
            }
        )
        execution = TaskExecution(execution_id="custom_task", task_config=config)
        
        result = await runner.run(execution, mock_game_operator)
        
        assert result.status == "completed"
        assert 'collected_amount' in result.result
    
    async def test_custom_task_runner(self):
        """测试自定义任务运行器。"""
        async def custom_function(config: Dict[str, Any], execution: TaskExecution) -> Dict[str, Any]:
            return {'success': True, 'custom_data': config.get('custom_param', 'default')}
        
        runner = CustomTaskRunner()
        
        config = TaskConfig(
            task_id="custom_task",
            task_type=TaskType.CUSTOM,
            name="自定义任务",
            parameters={
                "actions": [
                    {"type": "click", "target": "test_button", "method": "template"},
                    {"type": "wait", "duration": 0.1}
                ]
            }
        )
        execution = TaskExecution(execution_id="custom_task", task_config=config)
        
        # 创建模拟的GameOperator
        mock_game_operator = Mock()
        result = await runner.run(execution, mock_game_operator)
        
        assert result.status == "completed"
        assert 'total_actions' in result.result


@pytest.mark.asyncio
class TestGameTaskIntegration:
    """测试游戏任务集成。"""
    
    async def test_game_task_integration_creation(self):
        """测试游戏任务集成创建。"""
        mock_game_operator = Mock()
        mock_game_detector = Mock()
        
        integration = GameTaskIntegration(
            game_operator=mock_game_operator,
            game_detector=mock_game_detector
        )
        
        assert integration.game_operator == mock_game_operator
        assert integration.game_detector == mock_game_detector
        assert isinstance(integration.task_executor, EnhancedTaskExecutor)
    
    async def test_register_game_runner(self):
        """测试注册游戏任务运行器。"""
        integration = GameTaskIntegration()
        
        class TestGameRunner(TaskRunner):
            def __init__(self, task_type: TaskType):
                super().__init__(task_type)
            
            async def run(self, task_execution: TaskExecution, game_operator: GameOperator) -> ExecutionResult:
                return ExecutionResult(
                    status="completed",
                    result={'success': True},
                    error=None,
                    execution_time=0.1
                )
        
        integration.task_executor.register_task_runner(TestGameRunner(TaskType.DAILY_MISSION))
        
        assert TaskType.DAILY_MISSION in integration.task_executor.task_runners
        assert isinstance(integration.task_executor.task_runners[TaskType.DAILY_MISSION], TestGameRunner)
    
    async def test_submit_game_task(self):
        """测试提交游戏任务。"""
        integration = GameTaskIntegration()
        
        # 注册运行器
        class TestGameRunner(TaskRunner):
            def __init__(self, task_type: TaskType):
                super().__init__(task_type)
            
            async def run(self, task_execution: TaskExecution, game_operator: GameOperator) -> ExecutionResult:
                return ExecutionResult(
                    status="completed",
                    result={'success': True},
                    error=None,
                    execution_time=0.1
                )
        
        integration.task_executor.register_task_runner(TestGameRunner(TaskType.DAILY_MISSION))
        
        # 创建游戏动作
        actions = [
            create_click_action("login_button"),
            create_click_action("claim_reward_button")
        ]
        
        execution_id = await integration.submit_game_task(
            task_type=TaskType.DAILY_MISSION,
            actions=actions,
            priority=TaskPriority.HIGH
        )
        
        assert execution_id is not None
        
        # 检查任务配置
        execution = await integration.task_executor.get_task_status(execution_id)
        assert execution.task_config.task_type == TaskType.DAILY_MISSION
        assert execution.task_config.priority == TaskPriority.HIGH
        assert 'game_actions' in execution.task_config.parameters
        assert len(execution.task_config.parameters['game_actions']) == 2
    
    async def test_execute_action_sequence(self):
        """测试执行动作序列。"""
        mock_game_operator = Mock()
        mock_game_operator.click = AsyncMock(return_value=OperationResult(success=True, error_message="点击成功", execution_time=0.1))
        
        integration = GameTaskIntegration(game_operator=mock_game_operator)
        
        actions = [
            create_click_action("button1"),
            create_click_action("button2")
        ]
        
        results = await integration.execute_action_sequence(actions)
        
        assert len(results) == 2
        assert all(result.success for result in results)
        assert mock_game_operator.click.call_count == 2


class TestGameAction:
    """测试游戏动作。"""
    
    def test_create_click_action(self):
        """测试创建点击动作。"""
        action = create_click_action(
            target="test_button",
            click_type=ClickType.LEFT,
            description="点击测试按钮"
        )
        
        assert action.action_type == GameActionType.CLICK
        assert action.target == "test_button"
        assert action.params['click_type'] == ClickType.LEFT.value
        assert action.description == "点击测试按钮"
    
    def test_create_swipe_action(self):
        """测试创建滑动动作。"""
        action = create_swipe_action(
            start=(100, 100),
            end=(200, 200),
            duration=1.5,
            description="向右滑动"
        )
        
        assert action.action_type == GameActionType.SWIPE
        assert action.target == (100, 100)
        assert action.params['end_target'] == (200, 200)
        assert action.params['duration'] == 1.5
        assert action.description == "向右滑动"


@pytest.mark.asyncio
class TestIntegrationScenarios:
    """测试集成场景。"""
    
    async def test_complete_task_workflow(self):
        """测试完整的任务工作流。"""
        # 创建模拟组件
        mock_game_operator = Mock()
        mock_game_operator.click = AsyncMock(return_value=OperationResult(success=True, execution_time=0.1))
        mock_game_operator.wait_for_condition = AsyncMock(return_value=OperationResult(success=True, execution_time=0.1))
        
        mock_game_detector = Mock()
        mock_game_detector.detect_scene = Mock(return_value="MAIN_MENU")
        
        # 创建集成管理器
        integration = GameTaskIntegration(
            game_operator=mock_game_operator,
            game_detector=mock_game_detector
        )
        
        # 注册游戏任务运行器
        class CompleteGameRunner(GameTaskRunner):
            def __init__(self, task_type: TaskType, game_operator, game_detector=None):
                super().__init__(task_type, game_operator, game_detector)
                
            async def execute(self, execution: TaskExecution) -> Dict[str, Any]:
                actions = execution.task_config.parameters.get('game_actions', [])
                results = []
                
                for action in actions:
                    result = await self.execute_game_action(action)
                    results.append(result)
                    
                    if not result.success:
                        return {'success': False, 'error': result.error_message}
                
                return {
                    'success': True,
                    'actions_executed': len(results),
                    'action_results': results
                }
        
        integration.task_executor.register_task_runner(CompleteGameRunner(TaskType.DAILY_MISSION, mock_game_operator, mock_game_detector))
        
        # 创建任务动作序列
        actions = [
            create_click_action("main_menu_button"),
            create_click_action("daily_mission_button"),
            create_click_action("claim_all_button")
        ]
        
        # 提交任务
        execution_id = await integration.submit_game_task(
            task_type=TaskType.DAILY_MISSION,
            actions=actions,
            priority=TaskPriority.HIGH
        )
        
        # 启动任务执行器
        await integration.task_executor.start()
        
        # 等待任务完成
        await asyncio.sleep(0.5)
        
        # 检查任务结果
        execution = await integration.task_executor.get_task_status(execution_id)
        assert execution.status in [TaskStatus.COMPLETED, TaskStatus.RUNNING]
        
        # 停止任务执行器
        await integration.task_executor.stop()
        
        # 验证游戏操作器被正确调用
        assert mock_game_operator.click.call_count == 3


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])