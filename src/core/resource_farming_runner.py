"""资源刷取任务执行器模块。

该模块实现了星穹铁道资源刷取的自动化执行逻辑，包括：
- 材料副本自动刷取
- 经验书和信用点获取
- 体力管理和优化
- 刷取策略和路线规划
"""

import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .game_operator import GameOperator
from .smart_waiter import SmartWaiter, WaitConfig
from .logger import get_logger
from .events import EventBus
from .error_handler import ErrorHandler


class ResourceType(Enum):
    """资源类型枚举。"""
    CHARACTER_EXP = "character_exp"  # 角色经验材料
    LIGHT_CONE_EXP = "light_cone_exp"  # 光锥经验材料
    CREDITS = "credits"  # 信用点
    TRACE_MATERIALS = "trace_materials"  # 行迹材料
    ASCENSION_MATERIALS = "ascension_materials"  # 突破材料
    WEEKLY_BOSS_MATERIALS = "weekly_boss_materials"  # 周本材料
    RELIC_MATERIALS = "relic_materials"  # 遗器材料
    SYNTHESIS_MATERIALS = "synthesis_materials"  # 合成材料


class FarmingMode(Enum):
    """刷取模式枚举。"""
    EFFICIENT = "efficient"  # 效率优先
    BALANCED = "balanced"  # 平衡模式
    CONSERVATIVE = "conservative"  # 保守模式
    CUSTOM = "custom"  # 自定义模式


class DungeonType(Enum):
    """副本类型枚举。"""
    CALYX_GOLDEN = "calyx_golden"  # 拟造花萼（金）
    CALYX_CRIMSON = "calyx_crimson"  # 拟造花萼（赤）
    STAGNANT_SHADOW = "stagnant_shadow"  # 凝滞虚影
    CAVERN_OF_CORROSION = "cavern_of_corrosion"  # 侵蚀隧洞
    ECHO_OF_WAR = "echo_of_war"  # 历战余响


@dataclass
class ResourceTarget:
    """资源目标配置。"""
    resource_type: ResourceType
    target_amount: int
    current_amount: int = 0
    priority: int = 1  # 1-5，数字越小优先级越高
    max_energy_cost: int = 240  # 最大体力消耗
    preferred_dungeons: List[DungeonType] = field(default_factory=list)
    
    @property
    def is_completed(self) -> bool:
        """检查目标是否已完成。"""
        return self.current_amount >= self.target_amount
    
    @property
    def completion_rate(self) -> float:
        """获取完成率。"""
        if self.target_amount == 0:
            return 1.0
        return min(self.current_amount / self.target_amount, 1.0)


@dataclass
class DungeonInfo:
    """副本信息。"""
    dungeon_id: str
    dungeon_type: DungeonType
    name: str
    energy_cost: int
    difficulty_level: int
    estimated_time: int  # 预估完成时间（秒）
    drop_resources: List[ResourceType]
    drop_rates: Dict[ResourceType, float]  # 掉落率
    location: Tuple[int, int]  # 副本入口位置
    auto_battle_available: bool = True
    
    def get_efficiency_score(self, target_resource: ResourceType) -> float:
        """计算对特定资源的效率分数。
        
        Args:
            target_resource: 目标资源类型
            
        Returns:
            效率分数
        """
        if target_resource not in self.drop_rates:
            return 0.0
        
        drop_rate = self.drop_rates[target_resource]
        time_efficiency = 60.0 / self.estimated_time  # 每分钟完成次数
        energy_efficiency = 1.0 / self.energy_cost  # 每点体力效率
        
        return drop_rate * time_efficiency * energy_efficiency


@dataclass
class FarmingConfig:
    """刷取配置。"""
    farming_mode: FarmingMode = FarmingMode.BALANCED
    max_total_energy: int = 240  # 最大总体力消耗
    energy_refill_count: int = 0  # 体力补充次数
    auto_use_overflow_energy: bool = True  # 自动使用溢出体力
    min_energy_threshold: int = 40  # 最小体力阈值
    max_execution_time: int = 7200  # 最大执行时间（秒）
    retry_attempts: int = 3  # 重试次数
    battle_timeout: int = 300  # 战斗超时时间
    optimize_route: bool = True  # 优化刷取路线
    

@dataclass
class FarmingSession:
    """刷取会话信息。"""
    session_id: str
    start_time: float
    targets: List[ResourceTarget]
    config: FarmingConfig
    energy_used: int = 0
    dungeons_completed: int = 0
    resources_gained: Dict[ResourceType, int] = field(default_factory=dict)
    execution_log: List[str] = field(default_factory=list)
    
    @property
    def duration(self) -> float:
        """获取会话持续时间。"""
        return time.time() - self.start_time
    
    def add_log(self, message: str) -> None:
        """添加执行日志。"""
        timestamp = time.strftime("%H:%M:%S")
        self.execution_log.append(f"[{timestamp}] {message}")


class ResourceFarmingRunner:
    """资源刷取任务执行器。
    
    负责自动执行星穹铁道的资源刷取任务，包括副本选择、路线优化和效率管理。
    """
    
    def __init__(self, 
                 game_operator: GameOperator,
                 event_bus: Optional[EventBus] = None,
                 error_handler: Optional[ErrorHandler] = None):
        """初始化资源刷取执行器。
        
        Args:
            game_operator: 游戏操作器
            event_bus: 事件总线
            error_handler: 错误处理器
        """
        self.game_operator = game_operator
        self.event_bus = event_bus or EventBus()
        self.error_handler = error_handler or ErrorHandler()
        self.smart_waiter = SmartWaiter()
        self._logger = get_logger(__name__)
        
        # 会话管理
        self._current_session: Optional[FarmingSession] = None
        self._session_history: List[FarmingSession] = []
        
        # 副本和资源配置
        self._dungeons = self._load_dungeon_configs()
        self._ui_elements = self._load_ui_elements()
        
        # 状态跟踪
        self._current_energy: int = 240
        self._max_energy: int = 240
        
        self._logger.info("资源刷取执行器初始化完成")
    
    def _load_dungeon_configs(self) -> Dict[str, DungeonInfo]:
        """加载副本配置信息。
        
        Returns:
            副本配置字典
        """
        return {
            "calyx_golden_exp": DungeonInfo(
                dungeon_id="calyx_golden_exp",
                dungeon_type=DungeonType.CALYX_GOLDEN,
                name="拟造花萼（金）- 角色经验",
                energy_cost=20,
                difficulty_level=1,
                estimated_time=90,
                drop_resources=[ResourceType.CHARACTER_EXP, ResourceType.CREDITS],
                drop_rates={ResourceType.CHARACTER_EXP: 0.95, ResourceType.CREDITS: 0.8},
                location=(400, 300)
            ),
            "calyx_golden_lightcone": DungeonInfo(
                dungeon_id="calyx_golden_lightcone",
                dungeon_type=DungeonType.CALYX_GOLDEN,
                name="拟造花萼（金）- 光锥经验",
                energy_cost=20,
                difficulty_level=1,
                estimated_time=90,
                drop_resources=[ResourceType.LIGHT_CONE_EXP, ResourceType.CREDITS],
                drop_rates={ResourceType.LIGHT_CONE_EXP: 0.95, ResourceType.CREDITS: 0.8},
                location=(400, 400)
            ),
            "calyx_crimson_trace": DungeonInfo(
                dungeon_id="calyx_crimson_trace",
                dungeon_type=DungeonType.CALYX_CRIMSON,
                name="拟造花萼（赤）- 行迹材料",
                energy_cost=20,
                difficulty_level=2,
                estimated_time=120,
                drop_resources=[ResourceType.TRACE_MATERIALS],
                drop_rates={ResourceType.TRACE_MATERIALS: 0.9},
                location=(600, 300)
            ),
            "stagnant_shadow_ascension": DungeonInfo(
                dungeon_id="stagnant_shadow_ascension",
                dungeon_type=DungeonType.STAGNANT_SHADOW,
                name="凝滞虚影 - 突破材料",
                energy_cost=30,
                difficulty_level=3,
                estimated_time=180,
                drop_resources=[ResourceType.ASCENSION_MATERIALS],
                drop_rates={ResourceType.ASCENSION_MATERIALS: 0.85},
                location=(800, 400)
            ),
            "cavern_relic": DungeonInfo(
                dungeon_id="cavern_relic",
                dungeon_type=DungeonType.CAVERN_OF_CORROSION,
                name="侵蚀隧洞 - 遗器",
                energy_cost=40,
                difficulty_level=4,
                estimated_time=240,
                drop_resources=[ResourceType.RELIC_MATERIALS],
                drop_rates={ResourceType.RELIC_MATERIALS: 0.8},
                location=(1000, 300)
            ),
            "echo_weekly": DungeonInfo(
                dungeon_id="echo_weekly",
                dungeon_type=DungeonType.ECHO_OF_WAR,
                name="历战余响 - 周本材料",
                energy_cost=30,
                difficulty_level=5,
                estimated_time=300,
                drop_resources=[ResourceType.WEEKLY_BOSS_MATERIALS, ResourceType.TRACE_MATERIALS],
                drop_rates={ResourceType.WEEKLY_BOSS_MATERIALS: 1.0, ResourceType.TRACE_MATERIALS: 0.6},
                location=(1200, 400)
            )
        }
    
    def _load_ui_elements(self) -> Dict[str, Tuple[int, int]]:
        """加载UI元素位置配置。
        
        Returns:
            UI元素位置字典
        """
        return {
            "survival_guide_tab": (200, 100),
            "calyx_tab": (300, 150),
            "challenge_button": (1200, 650),
            "start_battle_button": (960, 550),
            "auto_battle_toggle": (1200, 100),
            "confirm_button": (960, 550),
            "back_button": (50, 50),
            "energy_refill_button": (800, 300),
            "use_item_button": (600, 400)
        }
    
    async def start_farming_session(self, 
                                   targets: List[ResourceTarget],
                                   config: Optional[FarmingConfig] = None) -> str:
        """开始资源刷取会话。
        
        Args:
            targets: 资源目标列表
            config: 刷取配置
            
        Returns:
            会话ID
        """
        session_id = f"farming_{int(time.time())}"
        config = config or FarmingConfig()
        
        self._current_session = FarmingSession(
            session_id=session_id,
            start_time=time.time(),
            targets=targets,
            config=config
        )
        
        self._logger.info(f"开始资源刷取会话: {session_id}")
        self._current_session.add_log(f"会话开始，目标数量: {len(targets)}")
        
        # 发送会话开始事件
        await self.event_bus.emit("farming_session_started", {
            "session_id": session_id,
            "targets": targets,
            "config": config
        })
        
        return session_id
    
    async def execute_farming_session(self) -> Dict[str, Any]:
        """执行当前刷取会话。
        
        Returns:
            执行结果
        """
        if not self._current_session:
            raise ValueError("没有活动的刷取会话")
        
        session = self._current_session
        
        try:
            self._logger.info(f"开始执行刷取会话: {session.session_id}")
            
            # 检查当前体力
            await self._check_current_energy()
            
            # 导航到生存指南
            if not await self._navigate_to_survival_guide():
                raise Exception("无法导航到生存指南界面")
            
            # 生成刷取计划
            farming_plan = await self._generate_farming_plan(session.targets, session.config)
            session.add_log(f"生成刷取计划，包含 {len(farming_plan)} 个副本")
            
            # 执行刷取计划
            for dungeon_id, run_count in farming_plan.items():
                if session.energy_used >= session.config.max_total_energy:
                    session.add_log("达到体力消耗上限，停止刷取")
                    break
                
                if self._is_session_timeout(session):
                    session.add_log("达到时间限制，停止刷取")
                    break
                
                # 执行副本刷取
                success_count = await self._execute_dungeon_farming(
                    dungeon_id, run_count, session
                )
                
                if success_count > 0:
                    session.add_log(f"完成副本 {dungeon_id}，成功次数: {success_count}/{run_count}")
                else:
                    session.add_log(f"副本 {dungeon_id} 执行失败")
            
            # 生成会话报告
            result = await self._generate_session_report(session)
            
            # 结束会话
            await self._end_farming_session(session)
            
            return result
            
        except Exception as e:
            self._logger.error(f"刷取会话执行失败: {str(e)}")
            session.add_log(f"会话执行失败: {str(e)}")
            await self.event_bus.emit("farming_session_failed", {
                "session_id": session.session_id,
                "error": str(e)
            })
            raise
    
    async def _check_current_energy(self) -> None:
        """检查当前体力值。"""
        try:
            # 这里应该实现体力值的OCR识别
            # 暂时使用模拟值
            self._current_energy = 240
            self._max_energy = 240
            
            self._logger.info(f"当前体力: {self._current_energy}/{self._max_energy}")
            
        except Exception as e:
            self._logger.error(f"检查体力失败: {str(e)}")
            # 使用默认值
            self._current_energy = 240
    
    async def _navigate_to_survival_guide(self) -> bool:
        """导航到生存指南界面。
        
        Returns:
            是否成功导航
        """
        try:
            self._logger.info("导航到生存指南界面")
            
            # 等待主界面加载
            if not await self.smart_waiter.wait_for_ui_element(
                template_path="templates/main_menu.png",
                timeout=30.0,
                description="等待主界面加载"
            ):
                return False
            
            # 点击生存指南标签
            guide_tab_pos = self._ui_elements["survival_guide_tab"]
            await self.game_operator.click(guide_tab_pos[0], guide_tab_pos[1])
            
            # 等待生存指南界面加载
            return await self.smart_waiter.wait_for_ui_element(
                template_path="templates/survival_guide.png",
                timeout=15.0,
                description="等待生存指南界面加载"
            )
            
        except Exception as e:
            self._logger.error(f"导航到生存指南失败: {str(e)}")
            return False
    
    async def _generate_farming_plan(self, 
                                    targets: List[ResourceTarget],
                                    config: FarmingConfig) -> Dict[str, int]:
        """生成刷取计划。
        
        Args:
            targets: 资源目标列表
            config: 刷取配置
            
        Returns:
            刷取计划 {副本ID: 运行次数}
        """
        plan = {}
        available_energy = min(self._current_energy, config.max_total_energy)
        
        # 按优先级排序目标
        sorted_targets = sorted(targets, key=lambda t: t.priority)
        
        for target in sorted_targets:
            if available_energy <= 0:
                break
            
            if target.is_completed:
                continue
            
            # 找到最适合的副本
            best_dungeon = self._find_best_dungeon_for_resource(
                target.resource_type, config.farming_mode
            )
            
            if not best_dungeon:
                continue
            
            # 计算需要的运行次数
            needed_amount = target.target_amount - target.current_amount
            drop_rate = best_dungeon.drop_rates.get(target.resource_type, 0.5)
            estimated_runs = max(1, int(needed_amount / drop_rate * 1.2))  # 增加20%缓冲
            
            # 限制体力消耗
            max_runs_by_energy = min(
                available_energy // best_dungeon.energy_cost,
                target.max_energy_cost // best_dungeon.energy_cost
            )
            
            actual_runs = min(estimated_runs, max_runs_by_energy)
            
            if actual_runs > 0:
                plan[best_dungeon.dungeon_id] = actual_runs
                available_energy -= actual_runs * best_dungeon.energy_cost
        
        self._logger.info(f"生成刷取计划: {plan}")
        return plan
    
    def _find_best_dungeon_for_resource(self, 
                                       resource_type: ResourceType,
                                       farming_mode: FarmingMode) -> Optional[DungeonInfo]:
        """为特定资源找到最佳副本。
        
        Args:
            resource_type: 资源类型
            farming_mode: 刷取模式
            
        Returns:
            最佳副本信息
        """
        suitable_dungeons = [
            dungeon for dungeon in self._dungeons.values()
            if resource_type in dungeon.drop_resources
        ]
        
        if not suitable_dungeons:
            return None
        
        # 根据刷取模式选择最佳副本
        if farming_mode == FarmingMode.EFFICIENT:
            # 效率优先：选择效率分数最高的
            return max(suitable_dungeons, 
                      key=lambda d: d.get_efficiency_score(resource_type))
        elif farming_mode == FarmingMode.CONSERVATIVE:
            # 保守模式：选择体力消耗最少的
            return min(suitable_dungeons, key=lambda d: d.energy_cost)
        else:
            # 平衡模式：综合考虑效率和消耗
            def balance_score(dungeon):
                efficiency = dungeon.get_efficiency_score(resource_type)
                energy_factor = 1.0 / (dungeon.energy_cost / 20.0)  # 标准化到20体力
                return efficiency * energy_factor
            
            return max(suitable_dungeons, key=balance_score)
    
    async def _execute_dungeon_farming(self, 
                                      dungeon_id: str,
                                      run_count: int,
                                      session: FarmingSession) -> int:
        """执行副本刷取。
        
        Args:
            dungeon_id: 副本ID
            run_count: 运行次数
            session: 刷取会话
            
        Returns:
            成功完成的次数
        """
        dungeon = self._dungeons.get(dungeon_id)
        if not dungeon:
            self._logger.error(f"未找到副本配置: {dungeon_id}")
            return 0
        
        self._logger.info(f"开始刷取副本: {dungeon.name}，计划次数: {run_count}")
        session.add_log(f"开始刷取 {dungeon.name}")
        
        success_count = 0
        
        try:
            # 导航到副本
            if not await self._navigate_to_dungeon(dungeon):
                return 0
            
            # 执行多次刷取
            for i in range(run_count):
                if self._is_session_timeout(session):
                    break
                
                self._logger.info(f"执行第 {i+1}/{run_count} 次刷取")
                
                # 检查体力
                if self._current_energy < dungeon.energy_cost:
                    session.add_log("体力不足，尝试补充体力")
                    if not await self._handle_energy_shortage(session.config):
                        session.add_log("体力补充失败，停止刷取")
                        break
                
                # 执行单次刷取
                if await self._execute_single_dungeon_run(dungeon, session):
                    success_count += 1
                    session.dungeons_completed += 1
                    session.energy_used += dungeon.energy_cost
                    self._current_energy -= dungeon.energy_cost
                    
                    # 更新资源获取统计
                    await self._update_resource_gains(dungeon, session)
                else:
                    session.add_log(f"第 {i+1} 次刷取失败")
                
                # 短暂休息
                await self.smart_waiter.wait_for_condition(
                    condition=lambda: False,
                    timeout=2.0,
                    description="刷取间隔休息"
                )
            
            return success_count
            
        except Exception as e:
            self._logger.error(f"副本刷取执行失败: {str(e)}")
            session.add_log(f"副本刷取失败: {str(e)}")
            return success_count
    
    async def _navigate_to_dungeon(self, dungeon: DungeonInfo) -> bool:
        """导航到指定副本。
        
        Args:
            dungeon: 副本信息
            
        Returns:
            是否成功导航
        """
        try:
            # 根据副本类型选择对应标签
            if dungeon.dungeon_type in [DungeonType.CALYX_GOLDEN, DungeonType.CALYX_CRIMSON]:
                tab_pos = self._ui_elements["calyx_tab"]
                await self.game_operator.click(tab_pos[0], tab_pos[1])
                
                # 等待花萼界面加载
                if not await self.smart_waiter.wait_for_ui_element(
                    template_path="templates/calyx_interface.png",
                    timeout=10.0,
                    description="等待花萼界面加载"
                ):
                    return False
            
            # 点击副本位置
            await self.game_operator.click(dungeon.location[0], dungeon.location[1])
            
            # 等待副本详情界面
            return await self.smart_waiter.wait_for_ui_element(
                template_path="templates/dungeon_details.png",
                timeout=10.0,
                description="等待副本详情界面"
            )
            
        except Exception as e:
            self._logger.error(f"导航到副本失败: {str(e)}")
            return False
    
    async def _execute_single_dungeon_run(self, 
                                         dungeon: DungeonInfo,
                                         session: FarmingSession) -> bool:
        """执行单次副本刷取。
        
        Args:
            dungeon: 副本信息
            session: 刷取会话
            
        Returns:
            是否执行成功
        """
        try:
            # 点击挑战按钮
            challenge_pos = self._ui_elements["challenge_button"]
            await self.game_operator.click(challenge_pos[0], challenge_pos[1])
            
            # 等待战斗准备界面
            if not await self.smart_waiter.wait_for_ui_element(
                template_path="templates/battle_prepare.png",
                timeout=10.0,
                description="等待战斗准备界面"
            ):
                return False
            
            # 开启自动战斗（如果可用）
            if dungeon.auto_battle_available:
                auto_pos = self._ui_elements["auto_battle_toggle"]
                await self.game_operator.click(auto_pos[0], auto_pos[1])
            
            # 开始战斗
            start_pos = self._ui_elements["start_battle_button"]
            await self.game_operator.click(start_pos[0], start_pos[1])
            
            # 等待战斗完成
            battle_result = await self.smart_waiter.wait_for_ui_element(
                template_path="templates/battle_victory.png",
                timeout=session.config.battle_timeout,
                description="等待战斗完成"
            )
            
            if battle_result:
                # 点击确认按钮
                confirm_pos = self._ui_elements["confirm_button"]
                await self.game_operator.click(confirm_pos[0], confirm_pos[1])
                
                # 等待返回副本界面
                await self.smart_waiter.wait_for_ui_element(
                    template_path="templates/dungeon_details.png",
                    timeout=10.0,
                    description="等待返回副本界面"
                )
                
                return True
            
            return False
            
        except Exception as e:
            self._logger.error(f"执行副本刷取失败: {str(e)}")
            return False
    
    async def _handle_energy_shortage(self, config: FarmingConfig) -> bool:
        """处理体力不足。
        
        Args:
            config: 刷取配置
            
        Returns:
            是否成功补充体力
        """
        try:
            if config.energy_refill_count <= 0:
                return False
            
            # 使用体力补充道具或星琼
            if config.auto_use_overflow_energy:
                # 点击体力补充按钮
                refill_pos = self._ui_elements["energy_refill_button"]
                await self.game_operator.click(refill_pos[0], refill_pos[1])
                
                # 确认补充
                confirm_pos = self._ui_elements["confirm_button"]
                await self.game_operator.click(confirm_pos[0], confirm_pos[1])
                
                # 更新体力值
                self._current_energy = min(self._current_energy + 60, self._max_energy)
                config.energy_refill_count -= 1
                
                self._logger.info(f"体力补充成功，当前体力: {self._current_energy}")
                return True
            
            return False
            
        except Exception as e:
            self._logger.error(f"体力补充失败: {str(e)}")
            return False
    
    async def _update_resource_gains(self, 
                                   dungeon: DungeonInfo,
                                   session: FarmingSession) -> None:
        """更新资源获取统计。
        
        Args:
            dungeon: 副本信息
            session: 刷取会话
        """
        # 根据副本掉落率估算获得的资源
        for resource_type, drop_rate in dungeon.drop_rates.items():
            if resource_type not in session.resources_gained:
                session.resources_gained[resource_type] = 0
            
            # 简化处理：按掉落率计算期望获得量
            estimated_gain = int(drop_rate * 10)  # 假设每次掉落10个单位
            session.resources_gained[resource_type] += estimated_gain
    
    def _is_session_timeout(self, session: FarmingSession) -> bool:
        """检查会话是否超时。
        
        Args:
            session: 刷取会话
            
        Returns:
            是否超时
        """
        return session.duration > session.config.max_execution_time
    
    async def _generate_session_report(self, session: FarmingSession) -> Dict[str, Any]:
        """生成会话报告。
        
        Args:
            session: 刷取会话
            
        Returns:
            会话报告
        """
        # 计算目标完成情况
        target_completion = {}
        for target in session.targets:
            gained = session.resources_gained.get(target.resource_type, 0)
            target.current_amount += gained
            target_completion[target.resource_type.value] = {
                "target": target.target_amount,
                "current": target.current_amount,
                "gained": gained,
                "completion_rate": target.completion_rate,
                "is_completed": target.is_completed
            }
        
        report = {
            "session_id": session.session_id,
            "duration": session.duration,
            "energy_used": session.energy_used,
            "dungeons_completed": session.dungeons_completed,
            "resources_gained": {k.value: v for k, v in session.resources_gained.items()},
            "target_completion": target_completion,
            "efficiency_score": self._calculate_efficiency_score(session),
            "execution_log": session.execution_log[-10:]  # 最后10条日志
        }
        
        self._logger.info(f"刷取会话完成 - 用时: {session.duration:.1f}秒, 体力: {session.energy_used}, 副本: {session.dungeons_completed}")
        return report
    
    def _calculate_efficiency_score(self, session: FarmingSession) -> float:
        """计算效率分数。
        
        Args:
            session: 刷取会话
            
        Returns:
            效率分数
        """
        if session.energy_used == 0 or session.duration == 0:
            return 0.0
        
        # 基于完成副本数量和时间的效率计算
        dungeons_per_minute = session.dungeons_completed / (session.duration / 60.0)
        energy_efficiency = session.dungeons_completed / session.energy_used
        
        return (dungeons_per_minute * 10 + energy_efficiency * 100) / 2
    
    async def _end_farming_session(self, session: FarmingSession) -> None:
        """结束刷取会话。
        
        Args:
            session: 刷取会话
        """
        session.add_log("会话结束")
        self._session_history.append(session)
        self._current_session = None
        
        # 发送会话完成事件
        await self.event_bus.emit("farming_session_completed", {
            "session_id": session.session_id,
            "duration": session.duration,
            "results": session.resources_gained
        })
        
        self._logger.info(f"刷取会话 {session.session_id} 已结束")
    
    def get_current_session(self) -> Optional[FarmingSession]:
        """获取当前会话。
        
        Returns:
            当前会话信息
        """
        return self._current_session
    
    def get_session_history(self) -> List[FarmingSession]:
        """获取会话历史。
        
        Returns:
            会话历史列表
        """
        return self._session_history.copy()
    
    def get_dungeon_info(self, dungeon_id: str) -> Optional[DungeonInfo]:
        """获取副本信息。
        
        Args:
            dungeon_id: 副本ID
            
        Returns:
            副本信息
        """
        return self._dungeons.get(dungeon_id)
    
    def get_all_dungeons(self) -> List[DungeonInfo]:
        """获取所有副本信息。
        
        Returns:
            副本信息列表
        """
        return list(self._dungeons.values())