"""任务运行器实现模块.

提供各种类型任务的具体执行逻辑。
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .enhanced_task_executor import TaskRunner, TaskType, TaskExecution, TaskStatus
from .game_operator import GameOperator, OperationResult
from .task_executor import ExecutionResult, ActionConfig, ActionType
from .logger import get_logger


class DailyMissionRunner(TaskRunner):
    """日常任务运行器。"""
    
    def __init__(self):
        super().__init__(TaskType.DAILY_MISSION)
        self.logger = get_logger(f"{__name__}.DailyMission")
    
    async def run(self, task_execution: TaskExecution, game_operator: GameOperator) -> ExecutionResult:
        """执行日常任务。
        
        Args:
            task_execution: 任务执行信息
            game_operator: 游戏操作器
            
        Returns:
            执行结果
        """
        start_time = time.time()
        task_config = task_execution.task_config
        
        try:
            self.logger.info(f"开始执行日常任务: {task_config.name}")
            
            # 获取任务参数
            mission_type = task_config.parameters.get("mission_type", "unknown")
            target_count = task_config.parameters.get("target_count", 1)
            
            # 更新进度
            task_execution.progress = 0.1
            
            # 检查游戏状态
            if not await self._check_game_ready(game_operator):
                raise RuntimeError("游戏未准备就绪")
            
            task_execution.progress = 0.2
            
            # 导航到任务界面
            if not await self._navigate_to_mission_panel(game_operator):
                raise RuntimeError("无法导航到任务界面")
            
            task_execution.progress = 0.4
            
            # 执行具体任务类型
            if mission_type == "combat":
                result = await self._execute_combat_mission(game_operator, target_count, task_execution)
            elif mission_type == "collection":
                result = await self._execute_collection_mission(game_operator, target_count, task_execution)
            elif mission_type == "exploration":
                result = await self._execute_exploration_mission(game_operator, target_count, task_execution)
            else:
                result = await self._execute_generic_mission(game_operator, task_execution)
            
            task_execution.progress = 0.9
            
            # 收集奖励
            await self._collect_rewards(game_operator)
            
            task_execution.progress = 1.0
            
            execution_time = time.time() - start_time
            self.logger.info(f"日常任务完成: {task_config.name}, 耗时: {execution_time:.2f}秒")
            
            return ExecutionResult(
                status="completed",
                result=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"日常任务执行失败: {task_config.name}, 错误: {e}")
            
            return ExecutionResult(
                status="failed",
                error=str(e),
                execution_time=execution_time
            )
    
    async def _check_game_ready(self, game_operator: GameOperator) -> bool:
        """检查游戏是否准备就绪。"""
        try:
            # 检查游戏窗口是否存在
            result = await game_operator.wait_for_condition(
                condition_type="ui_element",
                target="main_menu",
                timeout=10.0
            )
            return result.success
        except Exception as e:
            self.logger.warning(f"游戏状态检查失败: {e}")
            return False
    
    async def _navigate_to_mission_panel(self, game_operator: GameOperator) -> bool:
        """导航到任务面板。"""
        try:
            # 点击任务按钮
            result = await game_operator.click(
                target="mission_button",
                method="template",
                timeout=5.0
            )
            
            if not result.success:
                return False
            
            # 等待任务面板加载
            result = await game_operator.wait_for_condition(
                condition_type="ui_element",
                target="mission_panel",
                timeout=10.0
            )
            
            return result.success
            
        except Exception as e:
            self.logger.error(f"导航到任务面板失败: {e}")
            return False
    
    async def _execute_combat_mission(self, game_operator: GameOperator, target_count: int, task_execution: TaskExecution) -> Dict[str, Any]:
        """执行战斗任务。"""
        completed_count = 0
        results = []
        
        for i in range(target_count):
            try:
                # 开始战斗
                battle_result = await game_operator.click(
                    target="start_battle_button",
                    method="template",
                    timeout=5.0
                )
                
                if battle_result.success:
                    # 等待战斗结束
                    await game_operator.wait_for_condition(
                        condition_type="ui_element",
                        target="battle_result",
                        timeout=120.0  # 战斗最多2分钟
                    )
                    
                    completed_count += 1
                    results.append({"battle_index": i + 1, "status": "completed"})
                    
                    # 更新进度
                    progress = 0.4 + (0.5 * (i + 1) / target_count)
                    task_execution.progress = min(progress, 0.9)
                    
                else:
                    results.append({"battle_index": i + 1, "status": "failed", "reason": "无法开始战斗"})
                
                # 短暂休息
                await asyncio.sleep(2.0)
                
            except Exception as e:
                self.logger.warning(f"战斗 {i + 1} 执行失败: {e}")
                results.append({"battle_index": i + 1, "status": "error", "reason": str(e)})
        
        return {
            "mission_type": "combat",
            "target_count": target_count,
            "completed_count": completed_count,
            "results": results
        }
    
    async def _execute_collection_mission(self, game_operator: GameOperator, target_count: int, task_execution: TaskExecution) -> Dict[str, Any]:
        """执行收集任务。"""
        collected_count = 0
        results = []
        
        for i in range(target_count):
            try:
                # 寻找收集目标
                collect_result = await game_operator.click(
                    target="collection_item",
                    method="template",
                    timeout=10.0
                )
                
                if collect_result.success:
                    collected_count += 1
                    results.append({"item_index": i + 1, "status": "collected"})
                    
                    # 更新进度
                    progress = 0.4 + (0.5 * (i + 1) / target_count)
                    task_execution.progress = min(progress, 0.9)
                    
                else:
                    results.append({"item_index": i + 1, "status": "not_found"})
                
                await asyncio.sleep(1.0)
                
            except Exception as e:
                self.logger.warning(f"收集项目 {i + 1} 失败: {e}")
                results.append({"item_index": i + 1, "status": "error", "reason": str(e)})
        
        return {
            "mission_type": "collection",
            "target_count": target_count,
            "collected_count": collected_count,
            "results": results
        }
    
    async def _execute_exploration_mission(self, game_operator: GameOperator, target_count: int, task_execution: TaskExecution) -> Dict[str, Any]:
        """执行探索任务。"""
        explored_count = 0
        results = []
        
        for i in range(target_count):
            try:
                # 移动到探索点
                move_result = await game_operator.click(
                    target=f"exploration_point_{i + 1}",
                    method="template",
                    timeout=5.0
                )
                
                if move_result.success:
                    # 等待探索完成
                    await asyncio.sleep(3.0)
                    explored_count += 1
                    results.append({"point_index": i + 1, "status": "explored"})
                    
                    # 更新进度
                    progress = 0.4 + (0.5 * (i + 1) / target_count)
                    task_execution.progress = min(progress, 0.9)
                    
                else:
                    results.append({"point_index": i + 1, "status": "unreachable"})
                
            except Exception as e:
                self.logger.warning(f"探索点 {i + 1} 失败: {e}")
                results.append({"point_index": i + 1, "status": "error", "reason": str(e)})
        
        return {
            "mission_type": "exploration",
            "target_count": target_count,
            "explored_count": explored_count,
            "results": results
        }
    
    async def _execute_generic_mission(self, game_operator: GameOperator, task_execution: TaskExecution) -> Dict[str, Any]:
        """执行通用任务。"""
        try:
            # 点击任务完成按钮
            result = await game_operator.click(
                target="complete_mission_button",
                method="template",
                timeout=5.0
            )
            
            task_execution.progress = 0.8
            
            return {
                "mission_type": "generic",
                "status": "completed" if result.success else "failed",
                "result": result.data if result.success else None
            }
            
        except Exception as e:
            return {
                "mission_type": "generic",
                "status": "error",
                "reason": str(e)
            }
    
    async def _collect_rewards(self, game_operator: GameOperator):
        """收集任务奖励。"""
        try:
            # 点击奖励收集按钮
            await game_operator.click(
                target="collect_reward_button",
                method="template",
                timeout=5.0
            )
            
            # 等待奖励收集完成
            await asyncio.sleep(2.0)
            
        except Exception as e:
            self.logger.warning(f"收集奖励失败: {e}")


class ResourceFarmingRunner(TaskRunner):
    """资源采集任务运行器。"""
    
    def __init__(self):
        super().__init__(TaskType.RESOURCE_FARMING)
        self.logger = get_logger(f"{__name__}.ResourceFarming")
    
    async def run(self, task_execution: TaskExecution, game_operator: GameOperator) -> ExecutionResult:
        """执行资源采集任务。
        
        Args:
            task_execution: 任务执行信息
            game_operator: 游戏操作器
            
        Returns:
            执行结果
        """
        start_time = time.time()
        task_config = task_execution.task_config
        
        try:
            self.logger.info(f"开始执行资源采集: {task_config.name}")
            
            # 获取任务参数
            resource_type = task_config.parameters.get("resource_type", "energy")
            farming_duration = task_config.parameters.get("duration", 300)  # 默认5分钟
            target_amount = task_config.parameters.get("target_amount", 100)
            
            task_execution.progress = 0.1
            
            # 导航到资源采集区域
            if not await self._navigate_to_farming_area(game_operator, resource_type):
                raise RuntimeError(f"无法导航到 {resource_type} 采集区域")
            
            task_execution.progress = 0.2
            
            # 开始采集循环
            result = await self._farming_loop(game_operator, resource_type, farming_duration, target_amount, task_execution)
            
            task_execution.progress = 1.0
            
            execution_time = time.time() - start_time
            self.logger.info(f"资源采集完成: {task_config.name}, 耗时: {execution_time:.2f}秒")
            
            return ExecutionResult(
                status="completed",
                result=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"资源采集失败: {task_config.name}, 错误: {e}")
            
            return ExecutionResult(
                status="failed",
                error=str(e),
                execution_time=execution_time
            )
    
    async def _navigate_to_farming_area(self, game_operator: GameOperator, resource_type: str) -> bool:
        """导航到采集区域。"""
        try:
            # 点击对应的资源采集按钮
            result = await game_operator.click(
                target=f"{resource_type}_farming_button",
                method="template",
                timeout=5.0
            )
            
            if not result.success:
                return False
            
            # 等待采集界面加载
            result = await game_operator.wait_for_condition(
                condition_type="ui_element",
                target="farming_interface",
                timeout=10.0
            )
            
            return result.success
            
        except Exception as e:
            self.logger.error(f"导航到采集区域失败: {e}")
            return False
    
    async def _farming_loop(self, game_operator: GameOperator, resource_type: str, duration: int, target_amount: int, task_execution: TaskExecution) -> Dict[str, Any]:
        """采集循环。"""
        start_time = time.time()
        collected_amount = 0
        farming_cycles = 0
        
        while time.time() - start_time < duration and collected_amount < target_amount:
            try:
                # 点击采集按钮
                collect_result = await game_operator.click(
                    target="collect_resource_button",
                    method="template",
                    timeout=5.0
                )
                
                if collect_result.success:
                    farming_cycles += 1
                    # 假设每次采集获得随机数量的资源
                    cycle_amount = task_execution.task_config.parameters.get("amount_per_cycle", 5)
                    collected_amount += cycle_amount
                    
                    # 更新进度
                    time_progress = (time.time() - start_time) / duration
                    amount_progress = collected_amount / target_amount
                    overall_progress = 0.2 + 0.8 * max(time_progress, amount_progress)
                    task_execution.progress = min(overall_progress, 0.95)
                    
                    self.logger.debug(f"采集周期 {farming_cycles}: 获得 {cycle_amount} {resource_type}, 总计: {collected_amount}")
                
                # 等待采集冷却
                await asyncio.sleep(2.0)
                
            except Exception as e:
                self.logger.warning(f"采集周期 {farming_cycles + 1} 失败: {e}")
                await asyncio.sleep(5.0)  # 错误后等待更长时间
        
        elapsed_time = time.time() - start_time
        
        return {
            "resource_type": resource_type,
            "collected_amount": collected_amount,
            "target_amount": target_amount,
            "farming_cycles": farming_cycles,
            "elapsed_time": elapsed_time,
            "efficiency": collected_amount / elapsed_time if elapsed_time > 0 else 0
        }


class MailCollectionRunner(TaskRunner):
    """邮件收集任务运行器。"""
    
    def __init__(self):
        super().__init__(TaskType.MAIL_COLLECTION)
        self.logger = get_logger(f"{__name__}.MailCollection")
    
    async def run(self, task_execution: TaskExecution, game_operator: GameOperator) -> ExecutionResult:
        """执行邮件收集任务。
        
        Args:
            task_execution: 任务执行信息
            game_operator: 游戏操作器
            
        Returns:
            执行结果
        """
        start_time = time.time()
        task_config = task_execution.task_config
        
        try:
            self.logger.info(f"开始执行邮件收集: {task_config.name}")
            
            task_execution.progress = 0.1
            
            # 导航到邮件界面
            if not await self._navigate_to_mail_interface(game_operator):
                raise RuntimeError("无法导航到邮件界面")
            
            task_execution.progress = 0.3
            
            # 收集所有邮件
            result = await self._collect_all_mails(game_operator, task_execution)
            
            task_execution.progress = 1.0
            
            execution_time = time.time() - start_time
            self.logger.info(f"邮件收集完成: {task_config.name}, 耗时: {execution_time:.2f}秒")
            
            return ExecutionResult(
                status="completed",
                result=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"邮件收集失败: {task_config.name}, 错误: {e}")
            
            return ExecutionResult(
                status="failed",
                error=str(e),
                execution_time=execution_time
            )
    
    async def _navigate_to_mail_interface(self, game_operator: GameOperator) -> bool:
        """导航到邮件界面。"""
        try:
            # 点击邮件按钮
            result = await game_operator.click(
                target="mail_button",
                method="template",
                timeout=5.0
            )
            
            if not result.success:
                return False
            
            # 等待邮件界面加载
            result = await game_operator.wait_for_condition(
                condition_type="ui_element",
                target="mail_interface",
                timeout=10.0
            )
            
            return result.success
            
        except Exception as e:
            self.logger.error(f"导航到邮件界面失败: {e}")
            return False
    
    async def _collect_all_mails(self, game_operator: GameOperator, task_execution: TaskExecution) -> Dict[str, Any]:
        """收集所有邮件。"""
        collected_count = 0
        failed_count = 0
        rewards = []
        
        try:
            # 点击全部收取按钮
            collect_all_result = await game_operator.click(
                target="collect_all_mail_button",
                method="template",
                timeout=5.0
            )
            
            if collect_all_result.success:
                # 等待收集完成
                await asyncio.sleep(3.0)
                
                # 检查收集结果
                result = await game_operator.wait_for_condition(
                    condition_type="ui_element",
                    target="mail_collected_notification",
                    timeout=10.0
                )
                
                if result.success:
                    collected_count = task_execution.task_config.parameters.get("estimated_mail_count", 10)
                    task_execution.progress = 0.8
                else:
                    # 如果全部收取失败，尝试逐个收取
                    collected_count, failed_count, rewards = await self._collect_mails_individually(game_operator, task_execution)
            else:
                # 全部收取按钮不可用，逐个收取
                collected_count, failed_count, rewards = await self._collect_mails_individually(game_operator, task_execution)
            
        except Exception as e:
            self.logger.warning(f"批量收集邮件失败，尝试逐个收取: {e}")
            collected_count, failed_count, rewards = await self._collect_mails_individually(game_operator, task_execution)
        
        return {
            "collected_count": collected_count,
            "failed_count": failed_count,
            "total_processed": collected_count + failed_count,
            "rewards": rewards
        }
    
    async def _collect_mails_individually(self, game_operator: GameOperator, task_execution: TaskExecution) -> tuple:
        """逐个收集邮件。"""
        collected_count = 0
        failed_count = 0
        rewards = []
        max_mails = 50  # 最多处理50封邮件
        
        for i in range(max_mails):
            try:
                # 查找邮件项目
                mail_result = await game_operator.click(
                    target=f"mail_item_{i + 1}",
                    method="template",
                    timeout=2.0
                )
                
                if not mail_result.success:
                    # 没有更多邮件
                    break
                
                # 点击收取按钮
                collect_result = await game_operator.click(
                    target="collect_mail_reward_button",
                    method="template",
                    timeout=3.0
                )
                
                if collect_result.success:
                    collected_count += 1
                    rewards.append({"mail_index": i + 1, "status": "collected"})
                else:
                    failed_count += 1
                    rewards.append({"mail_index": i + 1, "status": "failed"})
                
                # 更新进度
                progress = 0.3 + 0.6 * (i + 1) / min(max_mails, 20)
                task_execution.progress = min(progress, 0.9)
                
                await asyncio.sleep(1.0)
                
            except Exception as e:
                self.logger.warning(f"收集邮件 {i + 1} 失败: {e}")
                failed_count += 1
                rewards.append({"mail_index": i + 1, "status": "error", "reason": str(e)})
        
        return collected_count, failed_count, rewards


class ArenaRunner(TaskRunner):
    """竞技场任务运行器。"""
    
    def __init__(self):
        super().__init__(TaskType.ARENA)
        self.logger = get_logger(f"{__name__}.Arena")
    
    async def run(self, task_execution: TaskExecution, game_operator: GameOperator) -> ExecutionResult:
        """执行竞技场任务。
        
        Args:
            task_execution: 任务执行信息
            game_operator: 游戏操作器
            
        Returns:
            执行结果
        """
        start_time = time.time()
        task_config = task_execution.task_config
        
        try:
            self.logger.info(f"开始执行竞技场任务: {task_config.name}")
            
            # 获取任务参数
            battle_count = task_config.parameters.get("battle_count", 1)
            opponent_type = task_config.parameters.get("opponent_type", "auto")
            
            task_execution.progress = 0.1
            
            # 导航到竞技场
            if not await self._navigate_to_arena(game_operator):
                raise RuntimeError("无法导航到竞技场")
            
            task_execution.progress = 0.3
            
            # 执行竞技场战斗
            result = await self._execute_arena_battles(game_operator, battle_count, opponent_type, task_execution)
            
            task_execution.progress = 1.0
            
            execution_time = time.time() - start_time
            self.logger.info(f"竞技场任务完成: {task_config.name}, 耗时: {execution_time:.2f}秒")
            
            return ExecutionResult(
                status="completed",
                result=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"竞技场任务失败: {task_config.name}, 错误: {e}")
            
            return ExecutionResult(
                status="failed",
                error=str(e),
                execution_time=execution_time
            )
    
    async def _navigate_to_arena(self, game_operator: GameOperator) -> bool:
        """导航到竞技场。"""
        try:
            # 点击竞技场按钮
            result = await game_operator.click(
                target="arena_button",
                method="template",
                timeout=5.0
            )
            
            if not result.success:
                return False
            
            # 等待竞技场界面加载
            result = await game_operator.wait_for_condition(
                condition_type="ui_element",
                target="arena_interface",
                timeout=10.0
            )
            
            return result.success
            
        except Exception as e:
            self.logger.error(f"导航到竞技场失败: {e}")
            return False
    
    async def _execute_arena_battles(self, game_operator: GameOperator, battle_count: int, opponent_type: str, task_execution: TaskExecution) -> Dict[str, Any]:
        """执行竞技场战斗。"""
        completed_battles = 0
        failed_battles = 0
        battle_results = []
        
        for i in range(battle_count):
            try:
                self.logger.info(f"开始第 {i + 1} 场竞技场战斗")
                
                # 选择对手
                if not await self._select_opponent(game_operator, opponent_type):
                    failed_battles += 1
                    battle_results.append({"battle_index": i + 1, "status": "failed", "reason": "无法选择对手"})
                    continue
                
                # 开始战斗
                battle_result = await game_operator.click(
                    target="start_arena_battle_button",
                    method="template",
                    timeout=5.0
                )
                
                if not battle_result.success:
                    failed_battles += 1
                    battle_results.append({"battle_index": i + 1, "status": "failed", "reason": "无法开始战斗"})
                    continue
                
                # 等待战斗结束
                battle_end_result = await game_operator.wait_for_condition(
                    condition_type="ui_element",
                    target="arena_battle_result",
                    timeout=120.0  # 竞技场战斗最多2分钟
                )
                
                if battle_end_result.success:
                    # 收集战斗奖励
                    await self._collect_battle_rewards(game_operator)
                    
                    completed_battles += 1
                    battle_results.append({"battle_index": i + 1, "status": "completed"})
                    
                    self.logger.info(f"第 {i + 1} 场竞技场战斗完成")
                else:
                    failed_battles += 1
                    battle_results.append({"battle_index": i + 1, "status": "timeout", "reason": "战斗超时"})
                
                # 更新进度
                progress = 0.3 + 0.6 * (i + 1) / battle_count
                task_execution.progress = min(progress, 0.9)
                
                # 战斗间隔
                await asyncio.sleep(3.0)
                
            except Exception as e:
                self.logger.warning(f"第 {i + 1} 场竞技场战斗异常: {e}")
                failed_battles += 1
                battle_results.append({"battle_index": i + 1, "status": "error", "reason": str(e)})
        
        return {
            "total_battles": battle_count,
            "completed_battles": completed_battles,
            "failed_battles": failed_battles,
            "success_rate": completed_battles / battle_count if battle_count > 0 else 0,
            "battle_results": battle_results
        }
    
    async def _select_opponent(self, game_operator: GameOperator, opponent_type: str) -> bool:
        """选择对手。"""
        try:
            if opponent_type == "auto":
                # 自动选择第一个可用对手
                result = await game_operator.click(
                    target="first_arena_opponent",
                    method="template",
                    timeout=5.0
                )
            elif opponent_type == "weak":
                # 选择较弱的对手
                result = await game_operator.click(
                    target="weak_arena_opponent",
                    method="template",
                    timeout=5.0
                )
            else:
                # 默认选择第一个对手
                result = await game_operator.click(
                    target="first_arena_opponent",
                    method="template",
                    timeout=5.0
                )
            
            return result.success
            
        except Exception as e:
            self.logger.error(f"选择对手失败: {e}")
            return False
    
    async def _collect_battle_rewards(self, game_operator: GameOperator) -> bool:
        """收集战斗奖励。"""
        try:
            # 点击确认按钮收集奖励
            result = await game_operator.click(
                target="arena_reward_confirm_button",
                method="template",
                timeout=5.0
            )
            
            if result.success:
                await asyncio.sleep(2.0)  # 等待奖励收集完成
            
            return result.success
            
        except Exception as e:
            self.logger.warning(f"收集竞技场奖励失败: {e}")
            return False


class CustomTaskRunner(TaskRunner):
    """自定义任务运行器。"""
    
    def __init__(self):
        super().__init__(TaskType.CUSTOM)
        self.logger = get_logger(f"{__name__}.CustomTask")
    
    async def run(self, task_execution: TaskExecution, game_operator: GameOperator) -> ExecutionResult:
        """执行自定义任务。
        
        Args:
            task_execution: 任务执行信息
            game_operator: 游戏操作器
            
        Returns:
            执行结果
        """
        start_time = time.time()
        task_config = task_execution.task_config
        
        try:
            self.logger.info(f"开始执行自定义任务: {task_config.name}")
            
            # 获取自定义动作序列
            actions = task_config.parameters.get("actions", [])
            
            if not actions:
                raise ValueError("自定义任务缺少动作序列")
            
            task_execution.progress = 0.1
            
            # 执行动作序列
            results = []
            total_actions = len(actions)
            
            for i, action in enumerate(actions):
                try:
                    action_result = await self._execute_custom_action(game_operator, action)
                    results.append({
                        "action_index": i + 1,
                        "action": action,
                        "result": action_result,
                        "status": "completed" if action_result.success else "failed"
                    })
                    
                    # 更新进度
                    progress = 0.1 + 0.8 * (i + 1) / total_actions
                    task_execution.progress = min(progress, 0.9)
                    
                except Exception as e:
                    self.logger.warning(f"自定义动作 {i + 1} 执行失败: {e}")
                    results.append({
                        "action_index": i + 1,
                        "action": action,
                        "status": "error",
                        "reason": str(e)
                    })
                
                # 动作间延迟
                delay = action.get("delay", 1.0)
                await asyncio.sleep(delay)
            
            task_execution.progress = 1.0
            
            execution_time = time.time() - start_time
            self.logger.info(f"自定义任务完成: {task_config.name}, 耗时: {execution_time:.2f}秒")
            
            return ExecutionResult(
                status="completed",
                result={
                    "total_actions": total_actions,
                    "completed_actions": len([r for r in results if r["status"] == "completed"]),
                    "failed_actions": len([r for r in results if r["status"] in ["failed", "error"]]),
                    "action_results": results
                },
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"自定义任务失败: {task_config.name}, 错误: {e}")
            
            return ExecutionResult(
                status="failed",
                error=str(e),
                execution_time=execution_time
            )
    
    async def _execute_custom_action(self, game_operator: GameOperator, action: Dict[str, Any]) -> OperationResult:
        """执行自定义动作。
        
        Args:
            game_operator: 游戏操作器
            action: 动作配置
            
        Returns:
            操作结果
        """
        action_type = action.get("type", "click")
        
        if action_type == "click":
            return await game_operator.click(
                target=action.get("target"),
                method=action.get("method", "template"),
                timeout=action.get("timeout", 5.0)
            )
        
        elif action_type == "wait":
            duration = action.get("duration", 1.0)
            await asyncio.sleep(duration)
            return OperationResult(success=True, execution_time=duration, metadata={"waited": duration})
        
        elif action_type == "wait_for_condition":
            return await game_operator.wait_for_condition(
                condition_type=action.get("condition_type", "ui_element"),
                target=action.get("target"),
                timeout=action.get("timeout", 10.0)
            )
        
        elif action_type == "input_text":
            return await game_operator.input_text(
                text=action.get("text", ""),
                target=action.get("target"),
                timeout=action.get("timeout", 5.0)
            )
        
        else:
            raise ValueError(f"不支持的动作类型: {action_type}")