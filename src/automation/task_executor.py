"""任务执行器模块.

提供具体任务类型的执行逻辑实现。
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .automation_engine import ITaskExecutor, ExecutionContext
from ..core.game_detector import GameDetector, SceneType, GameWindow
from ..core.game_operator import GameOperator, OperationResult, ClickType
from ..core.task_manager import TaskType, TaskStatus
from ..exceptions import AutomationError, GameDetectionError
from ..config.config_manager import ConfigManager


class DailyMissionType(Enum):
    """日常任务类型."""
    LOGIN_REWARD = "login_reward"  # 登录奖励
    DAILY_DUNGEON = "daily_dungeon"  # 日常副本
    ARENA_BATTLE = "arena_battle"  # 竞技场战斗
    GUILD_MISSION = "guild_mission"  # 公会任务
    RESOURCE_COLLECTION = "resource_collection"  # 资源收集
    EQUIPMENT_ENHANCE = "equipment_enhance"  # 装备强化


@dataclass
class TaskStep:
    """任务步骤."""
    name: str
    action: str
    target: Optional[str] = None
    wait_time: float = 1.0
    retry_count: int = 3
    required_scene: Optional[SceneType] = None
    success_condition: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseTaskExecutor(ITaskExecutor):
    """基础任务执行器."""
    
    def __init__(self, 
                 game_detector: GameDetector,
                 game_operator: GameOperator,
                 config_manager: ConfigManager):
        """初始化基础任务执行器.
        
        Args:
            game_detector: 游戏检测器
            game_operator: 游戏操作器
            config_manager: 配置管理器
        """
        self.game_detector = game_detector
        self.game_operator = game_operator
        self.config_manager = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 任务步骤定义
        self.task_steps: List[TaskStep] = []
        
        # 执行统计
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'average_execution_time': 0.0
        }
    
    async def execute(self, context: ExecutionContext) -> OperationResult:
        """执行任务.
        
        Args:
            context: 执行上下文
            
        Returns:
            执行结果
        """
        start_time = time.time()
        self.execution_stats['total_executions'] += 1
        
        try:
            self.logger.info(f"开始执行任务: {context.task_id}")
            
            # 执行前置检查
            if not await self._pre_execution_check(context):
                raise AutomationError("前置检查失败")
            
            # 执行任务步骤
            result = await self._execute_steps(context)
            
            # 执行后置检查
            if not await self._post_execution_check(context):
                self.logger.warning("后置检查失败，但任务已执行")
            
            execution_time = time.time() - start_time
            
            if result.success:
                self.execution_stats['successful_executions'] += 1
                self.logger.info(f"任务执行成功: {context.task_id}, 耗时: {execution_time:.2f}秒")
            else:
                self.execution_stats['failed_executions'] += 1
                self.logger.error(f"任务执行失败: {context.task_id}, 错误: {result.error_message}")
            
            # 更新平均执行时间
            self._update_average_execution_time(execution_time)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.execution_stats['failed_executions'] += 1
            self.logger.error(f"任务执行异常: {context.task_id}, 错误: {e}")
            
            return OperationResult(
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    def can_execute(self, context: ExecutionContext) -> bool:
        """检查是否可以执行.
        
        Args:
            context: 执行上下文
            
        Returns:
            是否可以执行
        """
        try:
            # 检查游戏是否运行
            if not self.game_detector.is_game_running():
                self.logger.warning("游戏未运行")
                return False
            
            # 检查游戏窗口是否可用
            game_window = self.game_detector.get_game_window()
            if not game_window or not game_window.is_active:
                self.logger.warning("游戏窗口不可用")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"执行检查失败: {e}")
            return False
    
    async def _pre_execution_check(self, context: ExecutionContext) -> bool:
        """前置执行检查.
        
        Args:
            context: 执行上下文
            
        Returns:
            检查是否通过
        """
        # 子类可以重写此方法
        return True
    
    async def _post_execution_check(self, context: ExecutionContext) -> bool:
        """后置执行检查.
        
        Args:
            context: 执行上下文
            
        Returns:
            检查是否通过
        """
        # 子类可以重写此方法
        return True
    
    async def _execute_steps(self, context: ExecutionContext) -> OperationResult:
        """执行任务步骤.
        
        Args:
            context: 执行上下文
            
        Returns:
            执行结果
        """
        total_steps = len(self.task_steps)
        completed_steps = 0
        
        for i, step in enumerate(self.task_steps):
            self.logger.info(f"执行步骤 {i+1}/{total_steps}: {step.name}")
            
            try:
                # 检查场景要求
                if step.required_scene:
                    if not await self._wait_for_scene(step.required_scene):
                        raise AutomationError(f"等待场景超时: {step.required_scene}")
                
                # 执行步骤
                step_result = await self._execute_step(step, context)
                
                if not step_result.success:
                    return OperationResult(
                        success=False,
                        execution_time=context.elapsed_time,
                        error_message=f"步骤执行失败: {step.name}, {step_result.error_message}"
                    )
                
                completed_steps += 1
                
                # 步骤间等待
                if step.wait_time > 0:
                    await asyncio.sleep(step.wait_time)
                    
            except Exception as e:
                return OperationResult(
                    success=False,
                    execution_time=context.elapsed_time,
                    error_message=f"步骤执行异常: {step.name}, {e}"
                )
        
        return OperationResult(
            success=True,
            execution_time=context.elapsed_time,
            metadata={'completed_steps': completed_steps, 'total_steps': total_steps}
        )
    
    async def _execute_step(self, step: TaskStep, context: ExecutionContext) -> OperationResult:
        """执行单个步骤.
        
        Args:
            step: 任务步骤
            context: 执行上下文
            
        Returns:
            执行结果
        """
        for attempt in range(step.retry_count):
            try:
                if step.action == "click":
                    result = await self._execute_click_action(step, context)
                elif step.action == "wait":
                    result = await self._execute_wait_action(step, context)
                elif step.action == "detect":
                    result = await self._execute_detect_action(step, context)
                elif step.action == "navigate":
                    result = await self._execute_navigate_action(step, context)
                else:
                    result = await self._execute_custom_action(step, context)
                
                if result.success:
                    return result
                
                if attempt < step.retry_count - 1:
                    self.logger.warning(f"步骤重试 {attempt + 1}: {step.name}")
                    await asyncio.sleep(1.0)
                    
            except Exception as e:
                if attempt == step.retry_count - 1:
                    return OperationResult(
                        success=False,
                        error_message=f"步骤执行异常: {e}"
                    )
                await asyncio.sleep(1.0)
        
        return OperationResult(
            success=False,
            error_message=f"步骤执行失败，已重试 {step.retry_count} 次"
        )
    
    async def _execute_click_action(self, step: TaskStep, context: ExecutionContext) -> OperationResult:
        """执行点击动作."""
        if not step.target:
            return OperationResult(success=False, error_message="缺少点击目标")
        
        # 查找目标元素
        element_pos = await self._find_element(step.target)
        if not element_pos:
            return OperationResult(success=False, error_message=f"未找到目标元素: {step.target}")
        
        # 执行点击
        click_result = self.game_operator.click(
            element_pos[0], element_pos[1], 
            click_type=ClickType.LEFT_CLICK
        )
        
        return click_result
    
    async def _execute_wait_action(self, step: TaskStep, context: ExecutionContext) -> OperationResult:
        """执行等待动作."""
        wait_time = step.metadata.get('wait_time', step.wait_time)
        await asyncio.sleep(wait_time)
        
        return OperationResult(success=True)
    
    async def _execute_detect_action(self, step: TaskStep, context: ExecutionContext) -> OperationResult:
        """执行检测动作."""
        if not step.target:
            return OperationResult(success=False, error_message="缺少检测目标")
        
        # 检测目标是否存在
        element_pos = await self._find_element(step.target)
        success = element_pos is not None
        
        return OperationResult(
            success=success,
            metadata={'detected': success, 'position': element_pos}
        )
    
    async def _execute_navigate_action(self, step: TaskStep, context: ExecutionContext) -> OperationResult:
        """执行导航动作."""
        target_scene = step.metadata.get('target_scene')
        if not target_scene:
            return OperationResult(success=False, error_message="缺少目标场景")
        
        # 等待目标场景
        success = await self._wait_for_scene(target_scene, timeout=30.0)
        
        return OperationResult(
            success=success,
            error_message="导航超时" if not success else None
        )
    
    async def _execute_custom_action(self, step: TaskStep, context: ExecutionContext) -> OperationResult:
        """执行自定义动作.
        
        子类可以重写此方法来实现特定的动作逻辑。
        """
        return OperationResult(
            success=False,
            error_message=f"未知动作类型: {step.action}"
        )
    
    async def _find_element(self, target: str) -> Optional[Tuple[int, int]]:
        """查找界面元素.
        
        Args:
            target: 目标元素标识
            
        Returns:
            元素位置坐标，如果未找到则返回None
        """
        try:
            # 这里可以实现具体的元素查找逻辑
            # 例如模板匹配、OCR识别等
            
            # 示例：使用模板匹配
            template_path = f"templates/{target}.png"
            position = self.game_detector.find_template(template_path)
            
            return position
            
        except Exception as e:
            self.logger.error(f"查找元素失败: {target}, 错误: {e}")
            return None
    
    async def _wait_for_scene(self, target_scene: SceneType, timeout: float = 30.0) -> bool:
        """等待特定场景.
        
        Args:
            target_scene: 目标场景
            timeout: 超时时间
            
        Returns:
            是否成功等待到目标场景
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                current_scene = self.game_detector.detect_current_scene()
                if current_scene == target_scene:
                    return True
                
                await asyncio.sleep(1.0)
                
            except Exception as e:
                self.logger.warning(f"场景检测失败: {e}")
                await asyncio.sleep(2.0)
        
        return False
    
    def _update_average_execution_time(self, execution_time: float) -> None:
        """更新平均执行时间."""
        total_executions = self.execution_stats['total_executions']
        current_avg = self.execution_stats['average_execution_time']
        
        # 计算新的平均值
        new_avg = ((current_avg * (total_executions - 1)) + execution_time) / total_executions
        self.execution_stats['average_execution_time'] = new_avg
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """获取执行统计信息."""
        return self.execution_stats.copy()


class DailyMissionExecutor(BaseTaskExecutor):
    """日常任务执行器."""
    
    def __init__(self, 
                 game_detector: GameDetector,
                 game_operator: GameOperator,
                 config_manager: ConfigManager):
        """初始化日常任务执行器."""
        super().__init__(game_detector, game_operator, config_manager)
        
        # 定义日常任务步骤
        self.task_steps = [
            TaskStep(
                name="导航到任务界面",
                action="navigate",
                target="task_menu",
                required_scene=SceneType.MAIN_MENU,
                metadata={'target_scene': SceneType.TASK_MENU}
            ),
            TaskStep(
                name="检查可用任务",
                action="detect",
                target="available_tasks",
                wait_time=2.0
            ),
            TaskStep(
                name="执行日常任务",
                action="execute_daily_missions",
                wait_time=1.0,
                retry_count=2
            ),
            TaskStep(
                name="领取奖励",
                action="collect_rewards",
                target="reward_button",
                wait_time=1.0
            )
        ]
    
    async def _execute_custom_action(self, step: TaskStep, context: ExecutionContext) -> OperationResult:
        """执行自定义动作."""
        if step.action == "execute_daily_missions":
            return await self._execute_daily_missions(context)
        elif step.action == "collect_rewards":
            return await self._collect_rewards(context)
        else:
            return await super()._execute_custom_action(step, context)
    
    async def _execute_daily_missions(self, context: ExecutionContext) -> OperationResult:
        """执行日常任务."""
        self.logger.info("开始执行日常任务")
        
        # 这里实现具体的日常任务逻辑
        # 例如：点击任务、确认执行、等待完成等
        
        try:
            # 示例：查找并点击日常任务按钮
            daily_button_pos = await self._find_element("daily_mission_button")
            if daily_button_pos:
                click_result = self.game_operator.click(
                    daily_button_pos[0], daily_button_pos[1]
                )
                
                if click_result.success:
                    # 等待任务执行
                    await asyncio.sleep(3.0)
                    return OperationResult(success=True)
            
            return OperationResult(
                success=False,
                error_message="未找到日常任务按钮"
            )
            
        except Exception as e:
            return OperationResult(
                success=False,
                error_message=f"执行日常任务失败: {e}"
            )
    
    async def _collect_rewards(self, context: ExecutionContext) -> OperationResult:
        """收集奖励."""
        self.logger.info("开始收集奖励")
        
        try:
            # 查找奖励按钮
            reward_button_pos = await self._find_element("reward_button")
            if reward_button_pos:
                click_result = self.game_operator.click(
                    reward_button_pos[0], reward_button_pos[1]
                )
                
                if click_result.success:
                    await asyncio.sleep(2.0)
                    return OperationResult(success=True)
            
            return OperationResult(
                success=False,
                error_message="未找到奖励按钮"
            )
            
        except Exception as e:
            return OperationResult(
                success=False,
                error_message=f"收集奖励失败: {e}"
            )


class ArenaExecutor(BaseTaskExecutor):
    """竞技场执行器."""
    
    def __init__(self, 
                 game_detector: GameDetector,
                 game_operator: GameOperator,
                 config_manager: ConfigManager):
        """初始化竞技场执行器."""
        super().__init__(game_detector, game_operator, config_manager)
        
        # 定义竞技场任务步骤
        self.task_steps = [
            TaskStep(
                name="导航到竞技场",
                action="navigate",
                target="arena_menu",
                required_scene=SceneType.MAIN_MENU,
                metadata={'target_scene': SceneType.ARENA}
            ),
            TaskStep(
                name="选择对手",
                action="select_opponent",
                wait_time=2.0
            ),
            TaskStep(
                name="开始战斗",
                action="start_battle",
                target="battle_button",
                wait_time=1.0
            ),
            TaskStep(
                name="等待战斗结束",
                action="wait_battle_end",
                wait_time=30.0
            ),
            TaskStep(
                name="收集战斗奖励",
                action="collect_battle_rewards",
                wait_time=2.0
            )
        ]
    
    async def _execute_custom_action(self, step: TaskStep, context: ExecutionContext) -> OperationResult:
        """执行自定义动作."""
        if step.action == "select_opponent":
            return await self._select_opponent(context)
        elif step.action == "start_battle":
            return await self._start_battle(context)
        elif step.action == "wait_battle_end":
            return await self._wait_battle_end(context)
        elif step.action == "collect_battle_rewards":
            return await self._collect_battle_rewards(context)
        else:
            return await super()._execute_custom_action(step, context)
    
    async def _select_opponent(self, context: ExecutionContext) -> OperationResult:
        """选择对手."""
        self.logger.info("选择竞技场对手")
        
        try:
            # 查找合适的对手
            opponent_pos = await self._find_element("suitable_opponent")
            if opponent_pos:
                click_result = self.game_operator.click(
                    opponent_pos[0], opponent_pos[1]
                )
                return click_result
            
            return OperationResult(
                success=False,
                error_message="未找到合适的对手"
            )
            
        except Exception as e:
            return OperationResult(
                success=False,
                error_message=f"选择对手失败: {e}"
            )
    
    async def _start_battle(self, context: ExecutionContext) -> OperationResult:
        """开始战斗."""
        self.logger.info("开始竞技场战斗")
        
        try:
            battle_button_pos = await self._find_element("battle_button")
            if battle_button_pos:
                click_result = self.game_operator.click(
                    battle_button_pos[0], battle_button_pos[1]
                )
                return click_result
            
            return OperationResult(
                success=False,
                error_message="未找到战斗按钮"
            )
            
        except Exception as e:
            return OperationResult(
                success=False,
                error_message=f"开始战斗失败: {e}"
            )
    
    async def _wait_battle_end(self, context: ExecutionContext) -> OperationResult:
        """等待战斗结束."""
        self.logger.info("等待战斗结束")
        
        # 等待战斗结束的逻辑
        max_wait_time = 60.0  # 最大等待60秒
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                # 检查是否有战斗结束标识
                battle_end_pos = await self._find_element("battle_end_indicator")
                if battle_end_pos:
                    return OperationResult(success=True)
                
                await asyncio.sleep(2.0)
                
            except Exception as e:
                self.logger.warning(f"战斗状态检测失败: {e}")
                await asyncio.sleep(3.0)
        
        return OperationResult(
            success=False,
            error_message="等待战斗结束超时"
        )
    
    async def _collect_battle_rewards(self, context: ExecutionContext) -> OperationResult:
        """收集战斗奖励."""
        self.logger.info("收集战斗奖励")
        
        try:
            # 点击确认按钮收集奖励
            confirm_button_pos = await self._find_element("confirm_button")
            if confirm_button_pos:
                click_result = self.game_operator.click(
                    confirm_button_pos[0], confirm_button_pos[1]
                )
                
                if click_result.success:
                    await asyncio.sleep(2.0)
                    return OperationResult(success=True)
            
            return OperationResult(
                success=False,
                error_message="未找到确认按钮"
            )
            
        except Exception as e:
            return OperationResult(
                success=False,
                error_message=f"收集奖励失败: {e}"
            )


class ResourceCollectionExecutor(BaseTaskExecutor):
    """资源收集执行器."""
    
    def __init__(self, 
                 game_detector: GameDetector,
                 game_operator: GameOperator,
                 config_manager: ConfigManager):
        """初始化资源收集执行器."""
        super().__init__(game_detector, game_operator, config_manager)
        
        # 定义资源收集步骤
        self.task_steps = [
            TaskStep(
                name="导航到资源界面",
                action="navigate",
                target="resource_menu",
                required_scene=SceneType.MAIN_MENU
            ),
            TaskStep(
                name="收集邮件奖励",
                action="collect_mail_rewards",
                wait_time=2.0
            ),
            TaskStep(
                name="收集建筑产出",
                action="collect_building_output",
                wait_time=2.0
            ),
            TaskStep(
                name="领取签到奖励",
                action="collect_signin_rewards",
                wait_time=1.0
            )
        ]
    
    async def _execute_custom_action(self, step: TaskStep, context: ExecutionContext) -> OperationResult:
        """执行自定义动作."""
        if step.action == "collect_mail_rewards":
            return await self._collect_mail_rewards(context)
        elif step.action == "collect_building_output":
            return await self._collect_building_output(context)
        elif step.action == "collect_signin_rewards":
            return await self._collect_signin_rewards(context)
        else:
            return await super()._execute_custom_action(step, context)
    
    async def _collect_mail_rewards(self, context: ExecutionContext) -> OperationResult:
        """收集邮件奖励."""
        self.logger.info("收集邮件奖励")
        
        try:
            # 点击邮件图标
            mail_icon_pos = await self._find_element("mail_icon")
            if mail_icon_pos:
                click_result = self.game_operator.click(
                    mail_icon_pos[0], mail_icon_pos[1]
                )
                
                if click_result.success:
                    await asyncio.sleep(2.0)
                    
                    # 点击一键领取
                    collect_all_pos = await self._find_element("collect_all_button")
                    if collect_all_pos:
                        self.game_operator.click(
                            collect_all_pos[0], collect_all_pos[1]
                        )
                        await asyncio.sleep(1.0)
                    
                    return OperationResult(success=True)
            
            return OperationResult(
                success=False,
                error_message="未找到邮件图标"
            )
            
        except Exception as e:
            return OperationResult(
                success=False,
                error_message=f"收集邮件奖励失败: {e}"
            )
    
    async def _collect_building_output(self, context: ExecutionContext) -> OperationResult:
        """收集建筑产出."""
        self.logger.info("收集建筑产出")
        
        try:
            # 查找可收集的建筑
            building_positions = await self._find_collectible_buildings()
            
            if building_positions:
                for pos in building_positions:
                    self.game_operator.click(pos[0], pos[1])
                    await asyncio.sleep(0.5)
                
                return OperationResult(success=True)
            
            return OperationResult(
                success=True,  # 没有可收集的建筑也算成功
                metadata={'message': '没有可收集的建筑产出'}
            )
            
        except Exception as e:
            return OperationResult(
                success=False,
                error_message=f"收集建筑产出失败: {e}"
            )
    
    async def _collect_signin_rewards(self, context: ExecutionContext) -> OperationResult:
        """收集签到奖励."""
        self.logger.info("收集签到奖励")
        
        try:
            # 查找签到按钮
            signin_button_pos = await self._find_element("signin_button")
            if signin_button_pos:
                click_result = self.game_operator.click(
                    signin_button_pos[0], signin_button_pos[1]
                )
                
                if click_result.success:
                    await asyncio.sleep(2.0)
                    return OperationResult(success=True)
            
            return OperationResult(
                success=True,  # 可能已经签到过了
                metadata={'message': '可能已经完成签到'}
            )
            
        except Exception as e:
            return OperationResult(
                success=False,
                error_message=f"收集签到奖励失败: {e}"
            )
    
    async def _find_collectible_buildings(self) -> List[Tuple[int, int]]:
        """查找可收集的建筑.
        
        Returns:
            可收集建筑的位置列表
        """
        # 这里可以实现具体的建筑识别逻辑
        # 例如查找带有收集标识的建筑
        positions = []
        
        try:
            # 示例：查找收集图标
            collect_icons = await self._find_multiple_elements("collect_icon")
            positions.extend(collect_icons)
            
        except Exception as e:
            self.logger.error(f"查找可收集建筑失败: {e}")
        
        return positions


class GuildMissionExecutor(BaseTaskExecutor):
    """公会任务执行器."""
    
    def __init__(self, 
                 game_detector: GameDetector,
                 game_operator: GameOperator,
                 config_manager: ConfigManager):
        """初始化公会任务执行器."""
        super().__init__(game_detector, game_operator, config_manager)
        
        # 定义公会任务步骤
        self.task_steps = [
            TaskStep(
                name="导航到公会界面",
                action="navigate",
                target="guild_menu",
                required_scene=SceneType.MAIN_MENU,
                metadata={'target_scene': SceneType.GUILD}
            ),
            TaskStep(
                name="检查公会任务",
                action="detect",
                target="guild_missions",
                wait_time=2.0
            ),
            TaskStep(
                name="执行公会任务",
                action="execute_guild_missions",
                wait_time=1.0,
                retry_count=2
            ),
            TaskStep(
                name="领取公会奖励",
                action="collect_guild_rewards",
                target="guild_reward_button",
                wait_time=1.0
            )
        ]
    
    async def _execute_custom_action(self, step: TaskStep, context: ExecutionContext) -> OperationResult:
        """执行自定义动作."""
        if step.action == "execute_guild_missions":
            return await self._execute_guild_missions(context)
        elif step.action == "collect_guild_rewards":
            return await self._collect_guild_rewards(context)
        else:
            return await super()._execute_custom_action(step, context)
    
    async def _execute_guild_missions(self, context: ExecutionContext) -> OperationResult:
        """执行公会任务."""
        self.logger.info("开始执行公会任务")
        
        try:
            # 查找可执行的公会任务
            mission_buttons = await self._find_multiple_elements("guild_mission_button")
            
            if mission_buttons:
                for pos in mission_buttons:
                    click_result = self.game_operator.click(pos[0], pos[1])
                    if click_result.success:
                        await asyncio.sleep(2.0)
                        
                        # 确认执行任务
                        confirm_pos = await self._find_element("confirm_mission_button")
                        if confirm_pos:
                            self.game_operator.click(confirm_pos[0], confirm_pos[1])
                            await asyncio.sleep(1.0)
                
                return OperationResult(success=True)
            
            return OperationResult(
                success=True,
                metadata={'message': '没有可执行的公会任务'}
            )
            
        except Exception as e:
            return OperationResult(
                success=False,
                error_message=f"执行公会任务失败: {e}"
            )
    
    async def _collect_guild_rewards(self, context: ExecutionContext) -> OperationResult:
        """收集公会奖励."""
        self.logger.info("收集公会奖励")
        
        try:
            # 查找公会奖励按钮
            reward_button_pos = await self._find_element("guild_reward_button")
            if reward_button_pos:
                click_result = self.game_operator.click(
                    reward_button_pos[0], reward_button_pos[1]
                )
                
                if click_result.success:
                    await asyncio.sleep(2.0)
                    return OperationResult(success=True)
            
            return OperationResult(
                success=True,
                metadata={'message': '没有可领取的公会奖励'}
            )
            
        except Exception as e:
            return OperationResult(
                success=False,
                error_message=f"收集公会奖励失败: {e}"
            )


class EquipmentEnhanceExecutor(BaseTaskExecutor):
    """装备强化执行器."""
    
    def __init__(self, 
                 game_detector: GameDetector,
                 game_operator: GameOperator,
                 config_manager: ConfigManager):
        """初始化装备强化执行器."""
        super().__init__(game_detector, game_operator, config_manager)
        
        # 定义装备强化步骤
        self.task_steps = [
            TaskStep(
                name="导航到装备界面",
                action="navigate",
                target="equipment_menu",
                required_scene=SceneType.MAIN_MENU,
                metadata={'target_scene': SceneType.EQUIPMENT}
            ),
            TaskStep(
                name="选择装备",
                action="select_equipment",
                wait_time=1.0
            ),
            TaskStep(
                name="执行强化",
                action="enhance_equipment",
                wait_time=2.0,
                retry_count=3
            ),
            TaskStep(
                name="确认强化结果",
                action="confirm_enhancement",
                wait_time=1.0
            )
        ]
    
    async def _execute_custom_action(self, step: TaskStep, context: ExecutionContext) -> OperationResult:
        """执行自定义动作."""
        if step.action == "select_equipment":
            return await self._select_equipment(context)
        elif step.action == "enhance_equipment":
            return await self._enhance_equipment(context)
        elif step.action == "confirm_enhancement":
            return await self._confirm_enhancement(context)
        else:
            return await super()._execute_custom_action(step, context)
    
    async def _select_equipment(self, context: ExecutionContext) -> OperationResult:
        """选择装备."""
        self.logger.info("选择可强化装备")
        
        try:
            # 查找可强化的装备
            equipment_pos = await self._find_element("enhanceable_equipment")
            if equipment_pos:
                click_result = self.game_operator.click(
                    equipment_pos[0], equipment_pos[1]
                )
                return click_result
            
            return OperationResult(
                success=False,
                error_message="未找到可强化的装备"
            )
            
        except Exception as e:
            return OperationResult(
                success=False,
                error_message=f"选择装备失败: {e}"
            )
    
    async def _enhance_equipment(self, context: ExecutionContext) -> OperationResult:
        """强化装备."""
        self.logger.info("开始强化装备")
        
        try:
            # 点击强化按钮
            enhance_button_pos = await self._find_element("enhance_button")
            if enhance_button_pos:
                click_result = self.game_operator.click(
                    enhance_button_pos[0], enhance_button_pos[1]
                )
                
                if click_result.success:
                    await asyncio.sleep(3.0)  # 等待强化动画
                    return OperationResult(success=True)
            
            return OperationResult(
                success=False,
                error_message="未找到强化按钮"
            )
            
        except Exception as e:
            return OperationResult(
                success=False,
                error_message=f"强化装备失败: {e}"
            )
    
    async def _confirm_enhancement(self, context: ExecutionContext) -> OperationResult:
        """确认强化结果."""
        self.logger.info("确认强化结果")
        
        try:
            # 点击确认按钮
            confirm_button_pos = await self._find_element("confirm_button")
            if confirm_button_pos:
                click_result = self.game_operator.click(
                    confirm_button_pos[0], confirm_button_pos[1]
                )
                
                if click_result.success:
                    await asyncio.sleep(1.0)
                    return OperationResult(success=True)
            
            return OperationResult(
                success=True,
                metadata={'message': '可能无需确认'}
            )
            
        except Exception as e:
            return OperationResult(
                success=False,
                error_message=f"确认强化结果失败: {e}"
            )
    
    async def _find_multiple_elements(self, target: str) -> List[Tuple[int, int]]:
        """查找多个相同元素.
        
        Args:
            target: 目标元素标识
            
        Returns:
            元素位置列表
        """
        # 这里可以实现查找多个相同元素的逻辑
        # 例如使用模板匹配查找所有匹配项
        positions = []
        
        try:
            # 示例实现
            template_path = f"templates/{target}.png"
            # 这里应该调用支持多匹配的方法
            # positions = self.game_detector.find_all_templates(template_path)
            
        except Exception as e:
            self.logger.error(f"查找多个元素失败: {target}, 错误: {e}")
        
        return positions