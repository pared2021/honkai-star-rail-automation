"""游戏特定操作模块

实现崩坏星穹铁道的具体自动化操作功能
"""

import time
import random
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio

from .logger import get_logger
from .game_detector import GameDetector, SceneType, UIElement
from .action_executor import ActionExecutor, ClickType, KeyAction
from .enums import ActionType, TaskType
from .config_manager import ConfigManager

logger = get_logger(__name__)

class GameTaskType(Enum):
    """游戏任务类型"""
    DAILY_STAMINA = "daily_stamina"  # 日常体力消耗
    DAILY_MISSIONS = "daily_missions"  # 日常任务
    SIMULATED_UNIVERSE = "simulated_universe"  # 模拟宇宙
    COMBAT_AUTO = "combat_auto"  # 自动战斗
    EXPLORATION = "exploration"  # 探索
    SHOP_OPERATIONS = "shop_operations"  # 商店操作
    MAIL_COLLECTION = "mail_collection"  # 邮件收集

class OperationResult(Enum):
    """操作结果"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    INTERRUPTED = "interrupted"
    SCENE_ERROR = "scene_error"

@dataclass
class OperationConfig:
    """操作配置"""
    max_retries: int = 3
    retry_delay: float = 1.0
    operation_timeout: float = 30.0
    click_delay_range: Tuple[float, float] = (0.1, 0.3)
    safety_checks: bool = True

@dataclass
class TaskResult:
    """任务执行结果"""
    task_type: GameTaskType
    result: OperationResult
    message: str
    duration: float
    details: Dict[str, Any]

class GameOperations:
    """游戏操作类"""
    
    def __init__(self, game_detector: GameDetector, action_executor: ActionExecutor, 
                 config_manager: ConfigManager):
        self.game_detector = game_detector
        self.action_executor = action_executor
        self.config_manager = config_manager
        self.operation_config = OperationConfig()
        self.is_running = False
        
    def _random_delay(self, min_delay: float = None, max_delay: float = None) -> None:
        """随机延迟"""
        if min_delay is None or max_delay is None:
            min_delay, max_delay = self.operation_config.click_delay_range
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def _safe_click(self, element: UIElement, click_type: ClickType = ClickType.SINGLE) -> bool:
        """安全点击UI元素"""
        try:
            # 添加随机偏移
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)
            
            click_x = element.position[0] + element.size[0] // 2 + offset_x
            click_y = element.position[1] + element.size[1] // 2 + offset_y
            
            result = self.action_executor.execute_click(
                position=(click_x, click_y),
                click_type=click_type
            )
            
            self._random_delay()
            return result.success
            
        except Exception as e:
            logger.error(f"Safe click failed: {e}")
            return False
    
    def _wait_for_scene_change(self, target_scene: SceneType, timeout: float = 10.0) -> bool:
        """等待场景切换"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_scene = self.game_detector.detect_current_scene()
            if current_scene == target_scene:
                return True
            time.sleep(0.5)
        return False
    
    def _ensure_game_foreground(self) -> bool:
        """确保游戏窗口在前台"""
        if not self.game_detector.is_game_running():
            logger.error("Game is not running")
            return False
        
        return self.game_detector.bring_game_to_front()
    
    async def execute_daily_stamina_consumption(self, config: Dict[str, Any]) -> TaskResult:
        """执行日常体力消耗"""
        start_time = time.time()
        task_type = GameTaskType.DAILY_STAMINA
        
        try:
            if not self._ensure_game_foreground():
                return TaskResult(
                    task_type=task_type,
                    result=OperationResult.FAILED,
                    message="无法将游戏窗口置于前台",
                    duration=time.time() - start_time,
                    details={}
                )
            
            target_stamina = config.get("target_stamina", 0)
            preferred_stages = config.get("preferred_stages", [])
            auto_use_items = config.get("auto_use_items", True)
            
            logger.info(f"开始执行日常体力消耗，目标体力: {target_stamina}")
            
            # 检查当前场景
            current_scene = self.game_detector.detect_current_scene()
            if current_scene not in [SceneType.GAME_WORLD, SceneType.MAIN_MENU]:
                logger.warning(f"当前场景不适合执行体力消耗: {current_scene.value}")
            
            # 打开活动界面
            activity_button = self.game_detector.find_ui_element("main_activity_button")
            if activity_button:
                self._safe_click(activity_button)
                self._random_delay(1.0, 2.0)
            
            # 选择材料本
            material_dungeon = self.game_detector.find_ui_element("activity_material_dungeon")
            if material_dungeon:
                self._safe_click(material_dungeon)
                self._random_delay(1.0, 2.0)
            
            # 执行体力消耗循环
            consumed_stamina = 0
            attempts = 0
            max_attempts = 20
            
            while consumed_stamina < target_stamina and attempts < max_attempts:
                attempts += 1
                
                # 查找挑战按钮
                challenge_button = self.game_detector.find_ui_element("dungeon_challenge_button")
                if not challenge_button:
                    logger.warning("未找到挑战按钮")
                    break
                
                self._safe_click(challenge_button)
                self._random_delay(1.0, 2.0)
                
                # 检查体力是否足够
                insufficient_stamina = self.game_detector.find_ui_element("insufficient_stamina_dialog")
                if insufficient_stamina:
                    if auto_use_items:
                        # 尝试使用体力道具
                        use_item_button = self.game_detector.find_ui_element("use_stamina_item_button")
                        if use_item_button:
                            self._safe_click(use_item_button)
                            self._random_delay(1.0, 2.0)
                            
                            confirm_button = self.game_detector.find_ui_element("confirm_button")
                            if confirm_button:
                                self._safe_click(confirm_button)
                                self._random_delay(1.0, 2.0)
                        else:
                            logger.info("体力不足且无可用道具")
                            break
                    else:
                        logger.info("体力不足")
                        break
                
                # 开始战斗
                start_battle_button = self.game_detector.find_ui_element("start_battle_button")
                if start_battle_button:
                    self._safe_click(start_battle_button)
                    
                    # 等待战斗结束
                    battle_end = self.game_detector.wait_for_ui_element("battle_result_dialog", timeout=120.0)
                    if battle_end:
                        consumed_stamina += 40  # 假设每次消耗40体力
                        logger.info(f"战斗完成，已消耗体力: {consumed_stamina}")
                        
                        # 点击确认按钮
                        confirm_button = self.game_detector.find_ui_element("confirm_button")
                        if confirm_button:
                            self._safe_click(confirm_button)
                            self._random_delay(1.0, 2.0)
                    else:
                        logger.warning("战斗超时")
                        break
                
                self._random_delay(2.0, 3.0)
            
            duration = time.time() - start_time
            
            if consumed_stamina >= target_stamina:
                return TaskResult(
                    task_type=task_type,
                    result=OperationResult.SUCCESS,
                    message=f"体力消耗完成，消耗了 {consumed_stamina} 体力",
                    duration=duration,
                    details={"consumed_stamina": consumed_stamina, "attempts": attempts}
                )
            else:
                return TaskResult(
                    task_type=task_type,
                    result=OperationResult.FAILED,
                    message=f"体力消耗未完成，仅消耗了 {consumed_stamina} 体力",
                    duration=duration,
                    details={"consumed_stamina": consumed_stamina, "attempts": attempts}
                )
                
        except Exception as e:
            logger.error(f"执行日常体力消耗时发生错误: {e}")
            return TaskResult(
                task_type=task_type,
                result=OperationResult.FAILED,
                message=f"执行失败: {str(e)}",
                duration=time.time() - start_time,
                details={"error": str(e)}
            )
    
    async def execute_daily_missions(self, config: Dict[str, Any]) -> TaskResult:
        """执行日常任务"""
        start_time = time.time()
        task_type = GameTaskType.DAILY_MISSIONS
        
        try:
            if not self._ensure_game_foreground():
                return TaskResult(
                    task_type=task_type,
                    result=OperationResult.FAILED,
                    message="无法将游戏窗口置于前台",
                    duration=time.time() - start_time,
                    details={}
                )
            
            auto_claim = config.get("auto_claim", True)
            priority_order = config.get("priority_order", ["dispatch", "assignment", "synthesis"])
            
            logger.info("开始执行日常任务")
            
            # 打开任务界面
            mission_button = self.game_detector.find_ui_element("main_mission_button")
            if mission_button:
                self._safe_click(mission_button)
                self._random_delay(1.0, 2.0)
            
            # 等待任务界面加载
            if not self._wait_for_scene_change(SceneType.MISSION, timeout=5.0):
                logger.warning("任务界面加载失败")
            
            completed_tasks = 0
            
            # 领取日常任务奖励
            if auto_claim:
                daily_tab = self.game_detector.find_ui_element("mission_daily_tab")
                if daily_tab:
                    self._safe_click(daily_tab)
                    self._random_delay(1.0, 2.0)
                
                # 查找可领取的奖励
                claim_buttons = self.game_detector.find_multiple_ui_elements([
                    "mission_claim_reward", "mission_claim_button"
                ])
                
                for claim_button in claim_buttons:
                    self._safe_click(claim_button)
                    self._random_delay(0.5, 1.0)
                    completed_tasks += 1
                
                # 一键领取
                claim_all_button = self.game_detector.find_ui_element("mission_claim_all")
                if claim_all_button:
                    self._safe_click(claim_all_button)
                    self._random_delay(1.0, 2.0)
                    completed_tasks += 1
            
            # 执行优先级任务
            for task_priority in priority_order:
                if task_priority == "dispatch":
                    # 执行派遣任务
                    dispatch_result = await self._execute_dispatch_missions()
                    if dispatch_result:
                        completed_tasks += 1
                
                elif task_priority == "assignment":
                    # 执行委托任务
                    assignment_result = await self._execute_assignment_missions()
                    if assignment_result:
                        completed_tasks += 1
                
                elif task_priority == "synthesis":
                    # 执行合成任务
                    synthesis_result = await self._execute_synthesis_missions()
                    if synthesis_result:
                        completed_tasks += 1
            
            duration = time.time() - start_time
            
            return TaskResult(
                task_type=task_type,
                result=OperationResult.SUCCESS,
                message=f"日常任务完成，共完成 {completed_tasks} 个任务",
                duration=duration,
                details={"completed_tasks": completed_tasks, "priority_order": priority_order}
            )
            
        except Exception as e:
            logger.error(f"执行日常任务时发生错误: {e}")
            return TaskResult(
                task_type=task_type,
                result=OperationResult.FAILED,
                message=f"执行失败: {str(e)}",
                duration=time.time() - start_time,
                details={"error": str(e)}
            )
    
    async def _execute_dispatch_missions(self) -> bool:
        """执行派遣任务"""
        try:
            # 打开派遣界面
            dispatch_button = self.game_detector.find_ui_element("mission_dispatch_tab")
            if dispatch_button:
                self._safe_click(dispatch_button)
                self._random_delay(1.0, 2.0)
            
            # 查找可派遣的任务
            dispatch_slots = self.game_detector.find_multiple_ui_elements([
                "dispatch_slot_empty", "dispatch_slot_available"
            ])
            
            for slot in dispatch_slots:
                self._safe_click(slot)
                self._random_delay(0.5, 1.0)
                
                # 选择角色
                character_slot = self.game_detector.find_ui_element("dispatch_character_slot")
                if character_slot:
                    self._safe_click(character_slot)
                    self._random_delay(0.5, 1.0)
                
                # 确认派遣
                confirm_dispatch = self.game_detector.find_ui_element("dispatch_confirm_button")
                if confirm_dispatch:
                    self._safe_click(confirm_dispatch)
                    self._random_delay(1.0, 2.0)
            
            return True
            
        except Exception as e:
            logger.error(f"执行派遣任务失败: {e}")
            return False
    
    async def _execute_assignment_missions(self) -> bool:
        """执行委托任务"""
        try:
            # 打开委托界面
            assignment_button = self.game_detector.find_ui_element("mission_assignment_tab")
            if assignment_button:
                self._safe_click(assignment_button)
                self._random_delay(1.0, 2.0)
            
            # 查找可接受的委托
            available_assignments = self.game_detector.find_multiple_ui_elements([
                "assignment_accept_button", "assignment_available"
            ])
            
            for assignment in available_assignments:
                self._safe_click(assignment)
                self._random_delay(0.5, 1.0)
                
                # 确认接受
                confirm_button = self.game_detector.find_ui_element("assignment_confirm_button")
                if confirm_button:
                    self._safe_click(confirm_button)
                    self._random_delay(1.0, 2.0)
            
            return True
            
        except Exception as e:
            logger.error(f"执行委托任务失败: {e}")
            return False
    
    async def _execute_synthesis_missions(self) -> bool:
        """执行合成任务"""
        try:
            # 打开合成界面
            synthesis_button = self.game_detector.find_ui_element("main_synthesis_button")
            if synthesis_button:
                self._safe_click(synthesis_button)
                self._random_delay(1.0, 2.0)
            
            # 查找可合成的物品
            synthesis_items = self.game_detector.find_multiple_ui_elements([
                "synthesis_item_available", "synthesis_craft_button"
            ])
            
            for item in synthesis_items:
                self._safe_click(item)
                self._random_delay(0.5, 1.0)
                
                # 确认合成
                craft_button = self.game_detector.find_ui_element("synthesis_confirm_button")
                if craft_button:
                    self._safe_click(craft_button)
                    self._random_delay(1.0, 2.0)
            
            return True
            
        except Exception as e:
            logger.error(f"执行合成任务失败: {e}")
            return False
    
    async def execute_auto_combat(self, config: Dict[str, Any]) -> TaskResult:
        """执行自动战斗"""
        start_time = time.time()
        task_type = GameTaskType.COMBAT_AUTO
        
        try:
            if not self._ensure_game_foreground():
                return TaskResult(
                    task_type=task_type,
                    result=OperationResult.FAILED,
                    message="无法将游戏窗口置于前台",
                    duration=time.time() - start_time,
                    details={}
                )
            
            auto_battle_enabled = config.get("auto_battle", True)
            skill_priority = config.get("skill_priority", ["ultimate", "skill", "basic"])
            
            logger.info("开始执行自动战斗")
            
            # 检查是否在战斗场景
            current_scene = self.game_detector.detect_current_scene()
            if current_scene != SceneType.COMBAT:
                return TaskResult(
                    task_type=task_type,
                    result=OperationResult.SCENE_ERROR,
                    message="当前不在战斗场景",
                    duration=time.time() - start_time,
                    details={"current_scene": current_scene.value}
                )
            
            # 启用自动战斗
            if auto_battle_enabled:
                auto_battle_button = self.game_detector.find_ui_element("combat_auto_battle")
                if auto_battle_button:
                    self._safe_click(auto_battle_button)
                    logger.info("已启用自动战斗")
            
            # 等待战斗结束
            battle_end = self.game_detector.wait_for_ui_element("battle_result_dialog", timeout=300.0)
            
            duration = time.time() - start_time
            
            if battle_end:
                # 点击确认按钮
                confirm_button = self.game_detector.find_ui_element("confirm_button")
                if confirm_button:
                    self._safe_click(confirm_button)
                
                return TaskResult(
                    task_type=task_type,
                    result=OperationResult.SUCCESS,
                    message="自动战斗完成",
                    duration=duration,
                    details={"auto_battle": auto_battle_enabled}
                )
            else:
                return TaskResult(
                    task_type=task_type,
                    result=OperationResult.TIMEOUT,
                    message="战斗超时",
                    duration=duration,
                    details={"timeout": 300.0}
                )
                
        except Exception as e:
            logger.error(f"执行自动战斗时发生错误: {e}")
            return TaskResult(
                task_type=task_type,
                result=OperationResult.FAILED,
                message=f"执行失败: {str(e)}",
                duration=time.time() - start_time,
                details={"error": str(e)}
            )
    
    async def execute_mail_collection(self, config: Dict[str, Any]) -> TaskResult:
        """执行邮件收集"""
        start_time = time.time()
        task_type = GameTaskType.MAIL_COLLECTION
        
        try:
            if not self._ensure_game_foreground():
                return TaskResult(
                    task_type=task_type,
                    result=OperationResult.FAILED,
                    message="无法将游戏窗口置于前台",
                    duration=time.time() - start_time,
                    details={}
                )
            
            auto_delete = config.get("auto_delete", False)
            
            logger.info("开始执行邮件收集")
            
            # 打开邮件界面
            mail_button = self.game_detector.find_ui_element("main_mail_button")
            if mail_button:
                self._safe_click(mail_button)
                self._random_delay(1.0, 2.0)
            
            # 等待邮件界面加载
            if not self._wait_for_scene_change(SceneType.MAIL, timeout=5.0):
                logger.warning("邮件界面加载失败")
            
            collected_mails = 0
            
            # 一键领取所有邮件
            claim_all_button = self.game_detector.find_ui_element("mail_claim_all")
            if claim_all_button:
                self._safe_click(claim_all_button)
                self._random_delay(1.0, 2.0)
                
                # 确认领取
                confirm_button = self.game_detector.find_ui_element("confirm_button")
                if confirm_button:
                    self._safe_click(confirm_button)
                    self._random_delay(1.0, 2.0)
                    collected_mails += 1
            
            # 如果启用自动删除
            if auto_delete:
                delete_all_button = self.game_detector.find_ui_element("mail_delete_all")
                if delete_all_button:
                    self._safe_click(delete_all_button)
                    self._random_delay(1.0, 2.0)
                    
                    # 确认删除
                    confirm_delete = self.game_detector.find_ui_element("confirm_delete_button")
                    if confirm_delete:
                        self._safe_click(confirm_delete)
                        self._random_delay(1.0, 2.0)
            
            duration = time.time() - start_time
            
            return TaskResult(
                task_type=task_type,
                result=OperationResult.SUCCESS,
                message=f"邮件收集完成，处理了 {collected_mails} 封邮件",
                duration=duration,
                details={"collected_mails": collected_mails, "auto_delete": auto_delete}
            )
            
        except Exception as e:
            logger.error(f"执行邮件收集时发生错误: {e}")
            return TaskResult(
                task_type=task_type,
                result=OperationResult.FAILED,
                message=f"执行失败: {str(e)}",
                duration=time.time() - start_time,
                details={"error": str(e)}
            )
    
    def stop_all_operations(self):
        """停止所有操作"""
        self.is_running = False
        logger.info("所有游戏操作已停止")
    
    def get_operation_status(self) -> Dict[str, Any]:
        """获取操作状态"""
        return {
            "is_running": self.is_running,
            "game_status": self.game_detector.get_game_status(),
            "current_scene": self.game_detector.current_scene.value,
            "operation_config": {
                "max_retries": self.operation_config.max_retries,
                "operation_timeout": self.operation_config.operation_timeout,
                "safety_checks": self.operation_config.safety_checks
            }
        }