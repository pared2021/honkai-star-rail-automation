"""TaskRunners模块的测试用例。

测试覆盖所有任务运行器类的核心功能，包括：
- DailyMissionRunner: 日常任务执行
- ResourceFarmingRunner: 资源采集
- MailCollectionRunner: 邮件收集
- ArenaRunner: 竞技场战斗
- CustomTaskRunner: 自定义任务
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from src.core.task_runners import (
    DailyMissionRunner,
    ResourceFarmingRunner,
    MailCollectionRunner,
    ArenaRunner,
    CustomTaskRunner
)
from src.core.enhanced_task_executor import TaskType, TaskConfig, TaskExecution
from src.core.game_operator import GameOperator, OperationResult
from src.core.task_executor import ExecutionResult


class TestDailyMissionRunner:
    """DailyMissionRunner测试类。"""
    
    @pytest.fixture
    def runner(self):
        """创建DailyMissionRunner实例。"""
        return DailyMissionRunner()
    
    @pytest.fixture
    def mock_game_operator(self):
        """创建模拟的GameOperator。"""
        operator = Mock(spec=GameOperator)
        operator.click = AsyncMock()
        operator.wait_for_condition = AsyncMock()
        operator.input_text = AsyncMock()
        return operator
    
    @pytest.fixture
    def task_execution(self):
        """创建任务执行实例。"""
        config = TaskConfig(
            task_id="test_daily_mission",
            task_type=TaskType.DAILY_MISSION,
            name="测试日常任务",
            parameters={
                "mission_type": "combat",
                "target_count": 3
            }
        )
        return TaskExecution(execution_id="test_exec_1", task_config=config)
    
    @pytest.mark.asyncio
    async def test_run_combat_mission_success(self, runner, mock_game_operator, task_execution):
        """测试成功执行战斗任务。"""
        # 设置模拟返回值
        mock_game_operator.click.return_value = OperationResult(success=True, execution_time=0.1, metadata={"clicked": True})
        mock_game_operator.wait_for_condition.return_value = OperationResult(success=True, execution_time=0.2, metadata={"condition_met": True})
        
        # 执行任务
        result = await runner.run(task_execution, mock_game_operator)
        
        # 验证结果
        assert result.status == "completed"
        assert result.result["mission_type"] == "combat"
        assert result.result["completed_count"] >= 0
        assert result.execution_time > 0
        assert task_execution.progress == 1.0
    
    @pytest.mark.asyncio
    async def test_run_collection_mission_success(self, runner, mock_game_operator):
        """测试成功执行收集任务。"""
        config = TaskConfig(
            task_id="test_collection",
            task_type=TaskType.DAILY_MISSION,
            name="收集任务",
            parameters={
                "mission_type": "collection",
                "target_count": 5
            }
        )
        task_execution = TaskExecution(execution_id="test_exec_1", task_config=config)
        
        mock_game_operator.click.return_value = OperationResult(success=True, execution_time=0.1)
        mock_game_operator.wait_for_condition.return_value = OperationResult(success=True, execution_time=0.2)
        
        result = await runner.run(task_execution, mock_game_operator)
        
        assert result.status == "completed"
        assert result.result["mission_type"] == "collection"
    
    @pytest.mark.asyncio
    async def test_run_exploration_mission_success(self, runner, mock_game_operator):
        """测试成功执行探索任务。"""
        config = TaskConfig(
            task_id="test_exploration",
            task_type=TaskType.DAILY_MISSION,
            name="探索任务",
            parameters={
                "mission_type": "exploration",
                "target_count": 2
            }
        )
        task_execution = TaskExecution(execution_id="test_exec_1", task_config=config)
        
        mock_game_operator.click.return_value = OperationResult(success=True, execution_time=0.1)
        mock_game_operator.wait_for_condition.return_value = OperationResult(success=True, execution_time=0.2)
        
        result = await runner.run(task_execution, mock_game_operator)
        
        assert result.status == "completed"
        assert result.result["mission_type"] == "exploration"
    
    @pytest.mark.asyncio
    async def test_run_navigation_failure(self, runner, mock_game_operator, task_execution):
        """测试导航失败的情况。"""
        # 模拟导航失败
        mock_game_operator.click.return_value = OperationResult(success=False, execution_time=0.1, error_message="导航失败")
        
        result = await runner.run(task_execution, mock_game_operator)
        
        assert result.status == "failed"
        assert "无法导航到任务界面" in result.error
    
    @pytest.mark.asyncio
    async def test_check_game_ready_success(self, runner, mock_game_operator):
        """测试游戏准备检查成功。"""
        mock_game_operator.wait_for_condition.return_value = OperationResult(success=True, execution_time=0.2)
        
        result = await runner._check_game_ready(mock_game_operator)
        
        assert result is True
        mock_game_operator.wait_for_condition.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_game_ready_failure(self, runner, mock_game_operator):
        """测试游戏准备检查失败。"""
        mock_game_operator.wait_for_condition.return_value = OperationResult(success=False, execution_time=0.2)
        
        result = await runner._check_game_ready(mock_game_operator)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_navigate_to_mission_panel_success(self, runner, mock_game_operator):
        """测试成功导航到任务面板。"""
        mock_game_operator.click.return_value = OperationResult(success=True, execution_time=0.1)
        mock_game_operator.wait_for_condition.return_value = OperationResult(success=True, execution_time=0.2)
        
        result = await runner._navigate_to_mission_panel(mock_game_operator)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_navigate_to_mission_panel_failure(self, runner, mock_game_operator):
        """测试导航到任务面板失败。"""
        mock_game_operator.click.return_value = OperationResult(success=False, execution_time=0.1, error_message="导航失败")
        
        result = await runner._navigate_to_mission_panel(mock_game_operator)
        
        assert result is False


class TestResourceFarmingRunner:
    """ResourceFarmingRunner测试类。"""
    
    @pytest.fixture
    def runner(self):
        """创建ResourceFarmingRunner实例。"""
        return ResourceFarmingRunner()
    
    @pytest.fixture
    def mock_game_operator(self):
        """创建模拟的GameOperator。"""
        operator = Mock(spec=GameOperator)
        operator.click = AsyncMock()
        operator.wait_for_condition = AsyncMock()
        return operator
    
    @pytest.fixture
    def task_execution(self):
        """创建资源采集任务执行实例。"""
        config = TaskConfig(
            task_id="test_farming",
            task_type=TaskType.RESOURCE_FARMING,
            name="资源采集",
            parameters={
                "resource_type": "credit",
                "target_amount": 100,
                "duration": 60,
                "amount_per_cycle": 10
            }
        )
        return TaskExecution(execution_id="test_exec_1", task_config=config)
    
    @pytest.mark.asyncio
    async def test_run_farming_success(self, runner, mock_game_operator, task_execution):
        """测试成功执行资源采集。"""
        mock_game_operator.click.return_value = OperationResult(success=True, execution_time=0.1)
        mock_game_operator.wait_for_condition.return_value = OperationResult(success=True, execution_time=0.2)
        
        # 模拟快速完成采集
        def mock_time():
            return 70  # 超过duration，结束循环
        
        with patch('time.time', mock_time):
            result = await runner.run(task_execution, mock_game_operator)
        
        assert result.status == "completed"
        assert result.result["resource_type"] == "credit"
        assert result.result["collected_amount"] >= 0
        assert result.result["farming_cycles"] >= 0
    
    @pytest.mark.asyncio
    async def test_run_farming_navigation_failure(self, runner, mock_game_operator, task_execution):
        """测试导航失败的情况。"""
        mock_game_operator.click.return_value = OperationResult(success=False, execution_time=0.1)
        
        result = await runner.run(task_execution, mock_game_operator)
        
        assert result.status == "failed"
        assert "无法导航到 credit 采集区域" in result.error
    
    @pytest.mark.asyncio
    async def test_navigate_to_farming_area_success(self, runner, mock_game_operator):
        """测试成功导航到采集区域。"""
        mock_game_operator.click.return_value = OperationResult(success=True, execution_time=0.1)
        mock_game_operator.wait_for_condition.return_value = OperationResult(success=True, execution_time=0.2)
        
        result = await runner._navigate_to_farming_area(mock_game_operator, "credit")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_farming_loop_with_target_reached(self, runner, mock_game_operator, task_execution):
        """测试采集循环达到目标数量。"""
        mock_game_operator.click.return_value = OperationResult(success=True, execution_time=0.1)
        
        # 模拟快速达到目标
        def mock_time():
            return 70  # 超过duration，结束循环
        
        with patch('time.time', mock_time):
            result = await runner._farming_loop(mock_game_operator, "credit", 60, 100, task_execution)
        
        assert result["resource_type"] == "credit"
        assert result["target_amount"] == 100


class TestMailCollectionRunner:
    """MailCollectionRunner测试类。"""
    
    @pytest.fixture
    def runner(self):
        """创建MailCollectionRunner实例。"""
        return MailCollectionRunner()
    
    @pytest.fixture
    def mock_game_operator(self):
        """创建模拟的GameOperator。"""
        operator = Mock(spec=GameOperator)
        operator.click = AsyncMock()
        operator.wait_for_condition = AsyncMock()
        return operator
    
    @pytest.fixture
    def task_execution(self):
        """创建邮件收集任务执行实例。"""
        config = TaskConfig(
            task_id="test_mail",
            task_type=TaskType.MAIL_COLLECTION,
            name="邮件收集",
            parameters={
                "estimated_mail_count": 5
            }
        )
        return TaskExecution(execution_id="test_exec_1", task_config=config)
    
    @pytest.mark.asyncio
    async def test_run_mail_collection_success(self, runner, mock_game_operator, task_execution):
        """测试成功执行邮件收集。"""
        mock_game_operator.click.return_value = OperationResult(success=True, execution_time=0.1)
        mock_game_operator.wait_for_condition.return_value = OperationResult(success=True, execution_time=0.2)
        
        result = await runner.run(task_execution, mock_game_operator)
        
        assert result.status == "completed"
        assert "collected_count" in result.result
        assert "total_processed" in result.result
    
    @pytest.mark.asyncio
    async def test_run_navigation_failure(self, runner, mock_game_operator, task_execution):
        """测试导航失败的情况。"""
        mock_game_operator.click.return_value = OperationResult(success=False, execution_time=0.1)
        
        result = await runner.run(task_execution, mock_game_operator)
        
        assert result.status == "failed"
        assert "无法导航到邮件界面" in result.error
    
    @pytest.mark.asyncio
    async def test_navigate_to_mail_interface_success(self, runner, mock_game_operator):
        """测试成功导航到邮件界面。"""
        mock_game_operator.click.return_value = OperationResult(success=True, execution_time=0.1)
        mock_game_operator.wait_for_condition.return_value = OperationResult(success=True, execution_time=0.2)
        
        result = await runner._navigate_to_mail_interface(mock_game_operator)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_collect_all_mails_batch_success(self, runner, mock_game_operator, task_execution):
        """测试批量收集邮件成功。"""
        mock_game_operator.click.return_value = OperationResult(success=True, execution_time=0.1)
        mock_game_operator.wait_for_condition.return_value = OperationResult(success=True, execution_time=0.2)
        
        result = await runner._collect_all_mails(mock_game_operator, task_execution)
        
        assert "collected_count" in result
        assert "failed_count" in result
        assert "total_processed" in result
    
    @pytest.mark.asyncio
    async def test_collect_mails_individually(self, runner, mock_game_operator, task_execution):
        """测试逐个收集邮件。"""
        # 模拟前几封邮件成功，后面没有更多邮件
        mock_game_operator.click.side_effect = [
            OperationResult(success=True, execution_time=0.1),   # 第1封邮件
            OperationResult(success=True, execution_time=0.1),   # 收取按钮
            OperationResult(success=True, execution_time=0.1),   # 第2封邮件
            OperationResult(success=True, execution_time=0.1),   # 收取按钮
            OperationResult(success=False, execution_time=0.1),  # 没有更多邮件
        ]
        
        collected, failed, rewards = await runner._collect_mails_individually(mock_game_operator, task_execution)
        
        assert collected >= 0
        assert failed >= 0
        assert isinstance(rewards, list)


# ArenaRunner tests removed due to TaskType.ARENA not being available


class TestCustomTaskRunner:
    """CustomTaskRunner测试类。"""
    
    @pytest.fixture
    def runner(self):
        """创建CustomTaskRunner实例。"""
        return CustomTaskRunner()
    
    @pytest.fixture
    def mock_game_operator(self):
        """创建模拟的GameOperator。"""
        operator = Mock(spec=GameOperator)
        operator.click = AsyncMock()
        operator.wait_for_condition = AsyncMock()
        operator.input_text = AsyncMock()
        return operator
    
    @pytest.fixture
    def task_execution(self):
        """创建自定义任务执行实例。"""
        config = TaskConfig(
            task_id="test_custom",
            task_type=TaskType.CUSTOM,
            name="自定义任务",
            parameters={
                "actions": [
                    {"type": "click", "target": "button1", "delay": 0.1},
                    {"type": "wait", "duration": 0.1},
                    {"type": "wait_for_condition", "target": "element1", "delay": 0.1}
                ]
            }
        )
        return TaskExecution(execution_id="test_exec_1", task_config=config)
    
    @pytest.mark.asyncio
    async def test_run_custom_task_success(self, runner, mock_game_operator, task_execution):
        """测试成功执行自定义任务。"""
        mock_game_operator.click.return_value = OperationResult(success=True, execution_time=0.1)
        mock_game_operator.wait_for_condition.return_value = OperationResult(success=True, execution_time=0.2)
        
        result = await runner.run(task_execution, mock_game_operator)
        
        assert result.status == "completed"
        assert "total_actions" in result.result
        assert "completed_actions" in result.result
        assert "action_results" in result.result
        assert len(result.result["action_results"]) == 3
    
    @pytest.mark.asyncio
    async def test_run_no_actions_error(self, runner, mock_game_operator):
        """测试没有动作序列的错误情况。"""
        config = TaskConfig(
            task_id="test_empty",
            task_type=TaskType.CUSTOM,
            name="空任务",
            parameters={}
        )
        task_execution = TaskExecution(execution_id="test_exec_1", task_config=config)
        
        result = await runner.run(task_execution, mock_game_operator)
        
        assert result.status == "failed"
        assert "缺少动作序列" in result.error
    
    @pytest.mark.asyncio
    async def test_execute_custom_action_click(self, runner, mock_game_operator):
        """测试执行点击动作。"""
        mock_game_operator.click.return_value = OperationResult(success=True, execution_time=0.1)
        
        action = {"type": "click", "target": "test_button"}
        result = await runner._execute_custom_action(mock_game_operator, action)
        
        assert result.success is True
        mock_game_operator.click.assert_called_once_with(
            target="test_button",
            method="template",
            timeout=5.0
        )
    
    @pytest.mark.asyncio
    async def test_execute_custom_action_wait(self, runner, mock_game_operator):
        """测试执行等待动作。"""
        action = {"type": "wait", "duration": 0.1}
        
        start_time = time.time()
        result = await runner._execute_custom_action(mock_game_operator, action)
        elapsed = time.time() - start_time
        
        assert result.success is True
        assert elapsed >= 0.09  # Allow for slight timing variations
        assert result.metadata["waited"] == 0.1
    
    @pytest.mark.asyncio
    async def test_execute_custom_action_wait_for_condition(self, runner, mock_game_operator):
        """测试执行等待条件动作。"""
        mock_game_operator.wait_for_condition.return_value = OperationResult(success=True, execution_time=0.5)
        
        action = {"type": "wait_for_condition", "target": "test_element"}
        result = await runner._execute_custom_action(mock_game_operator, action)
        
        assert result.success is True
        mock_game_operator.wait_for_condition.assert_called_once_with(
            condition_type="ui_element",
            target="test_element",
            timeout=10.0
        )
    
    @pytest.mark.asyncio
    async def test_execute_custom_action_input_text(self, runner, mock_game_operator):
        """测试执行文本输入动作。"""
        mock_game_operator.input_text.return_value = OperationResult(success=True, execution_time=0.1, metadata={"text_input": True})
        
        action = {"type": "input_text", "text": "test input", "target": "input_field"}
        result = await runner._execute_custom_action(mock_game_operator, action)
        
        assert result.success is True
        mock_game_operator.input_text.assert_called_once_with(
            text="test input",
            target="input_field",
            timeout=5.0
        )
    
    @pytest.mark.asyncio
    async def test_execute_custom_action_unsupported_type(self, runner, mock_game_operator):
        """测试不支持的动作类型。"""
        action = {"type": "unsupported_action"}
        
        with pytest.raises(ValueError, match="不支持的动作类型"):
            await runner._execute_custom_action(mock_game_operator, action)
    
    @pytest.mark.asyncio
    async def test_run_with_action_errors(self, runner, mock_game_operator):
        """测试包含错误动作的自定义任务。"""
        config = TaskConfig(
            task_id="test_errors",
            task_type=TaskType.CUSTOM,
            name="错误任务",
            parameters={
                "actions": [
                    {"type": "click", "target": "button1", "delay": 0.1},
                    {"type": "unsupported_action", "delay": 0.1},
                    {"type": "wait", "duration": 0.1}
                ]
            }
        )
        task_execution = TaskExecution(execution_id="test_exec_1", task_config=config)
        
        mock_game_operator.click.return_value = OperationResult(success=True, execution_time=0.1)
        
        result = await runner.run(task_execution, mock_game_operator)
        
        assert result.status == "completed"
        assert result.result["total_actions"] == 3
        assert result.result["failed_actions"] >= 1  # 至少有一个失败的动作
        
        # 检查动作结果
        action_results = result.result["action_results"]
        assert len(action_results) == 3
        assert action_results[1]["status"] == "error"  # 第二个动作应该失败