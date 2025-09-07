"""游戏操作模块.

提供游戏相关的操作功能，包括游戏控制、UI交互和状态管理。
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from .game_detector import GameDetector, SceneType, UIElement
from .task_executor import TaskExecutor, ActionConfig, ActionType, ExecutionResult
from .events import EventBus
from .logger import get_logger


class GameState(Enum):
    """游戏状态枚举。"""
    UNKNOWN = "unknown"
    MENU = "menu"
    LOADING = "loading"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"


class OperationType(Enum):
    """操作类型枚举。"""
    NAVIGATION = "navigation"
    INTERACTION = "interaction"
    COMBAT = "combat"
    COLLECTION = "collection"
    QUEST = "quest"
    SYSTEM = "system"


@dataclass
class GameOperation:
    """游戏操作配置。"""
    name: str
    operation_type: OperationType
    actions: List[ActionConfig]
    preconditions: List[str] = None
    postconditions: List[str] = None
    timeout: float = 60.0
    description: str = ""

    def __post_init__(self):
        if self.preconditions is None:
            self.preconditions = []
        if self.postconditions is None:
            self.postconditions = []


@dataclass
class OperationResult:
    """操作执行结果。"""
    operation_name: str
    success: bool
    execution_results: List[ExecutionResult]
    start_time: datetime
    end_time: datetime
    error_message: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def duration(self) -> float:
        """获取执行时长（秒）。"""
        return (self.end_time - self.start_time).total_seconds()


class GameOperations:
    """游戏操作管理器。"""

    def __init__(self, 
                 game_detector: Optional[GameDetector] = None,
                 task_executor: Optional[TaskExecutor] = None,
                 event_bus: Optional[EventBus] = None):
        """初始化游戏操作管理器。
        
        Args:
            game_detector: 游戏检测器实例
            task_executor: 任务执行器实例
            event_bus: 事件总线实例
        """
        self.logger = get_logger(__name__)
        self.game_detector = game_detector or GameDetector()
        self.task_executor = task_executor or TaskExecutor()
        self.event_bus = event_bus or EventBus()
        
        # 操作状态
        self.current_state = GameState.UNKNOWN
        self.is_operating = False
        self.operation_history: List[OperationResult] = []
        
        # 预定义操作
        self.operations: Dict[str, GameOperation] = {}
        self._initialize_default_operations()

    def _initialize_default_operations(self) -> None:
        """初始化默认操作。"""
        # 基础导航操作
        self.operations["click_ui_element"] = GameOperation(
            name="click_ui_element",
            operation_type=OperationType.INTERACTION,
            actions=[
                ActionConfig(
                    action_type=ActionType.DETECT_UI,
                    parameters={"element_name": "target_element"},
                    description="检测目标UI元素"
                ),
                ActionConfig(
                    action_type=ActionType.CLICK,
                    parameters={"x": 0, "y": 0},
                    description="点击UI元素"
                )
            ],
            description="点击指定的UI元素"
        )
        
        # 截图操作
        self.operations["take_screenshot"] = GameOperation(
            name="take_screenshot",
            operation_type=OperationType.SYSTEM,
            actions=[
                ActionConfig(
                    action_type=ActionType.SCREENSHOT,
                    parameters={"save_path": "screenshots/game_screenshot.png"},
                    description="截取游戏画面"
                )
            ],
            description="截取当前游戏画面"
        )
        
        # 等待操作
        self.operations["wait_for_scene"] = GameOperation(
            name="wait_for_scene",
            operation_type=OperationType.SYSTEM,
            actions=[
                ActionConfig(
                    action_type=ActionType.WAIT,
                    parameters={"duration": 2.0},
                    description="等待场景加载"
                )
            ],
            description="等待场景切换完成"
        )

    async def execute_operation(self, operation_name: str, **kwargs) -> OperationResult:
        """执行游戏操作。
        
        Args:
            operation_name: 操作名称
            **kwargs: 操作参数
            
        Returns:
            OperationResult: 操作执行结果
        """
        start_time = datetime.now()
        
        if operation_name not in self.operations:
            error_msg = f"未找到操作: {operation_name}"
            self.logger.error(error_msg)
            return OperationResult(
                operation_name=operation_name,
                success=False,
                execution_results=[],
                start_time=start_time,
                end_time=datetime.now(),
                error_message=error_msg
            )
        
        operation = self.operations[operation_name]
        self.is_operating = True
        
        try:
            self.logger.info(f"开始执行游戏操作: {operation_name}")
            
            # 检查前置条件
            if not await self._check_preconditions(operation):
                error_msg = f"操作 {operation_name} 的前置条件不满足"
                self.logger.warning(error_msg)
                return OperationResult(
                    operation_name=operation_name,
                    success=False,
                    execution_results=[],
                    start_time=start_time,
                    end_time=datetime.now(),
                    error_message=error_msg
                )
            
            # 准备动作参数
            prepared_actions = self._prepare_actions(operation.actions, kwargs)
            
            # 执行动作序列
            execution_results = await self.task_executor.execute_sequence(prepared_actions)
            
            # 检查执行结果
            success = all(result.status.value == "completed" for result in execution_results)
            
            # 检查后置条件
            if success:
                success = await self._check_postconditions(operation)
            
            end_time = datetime.now()
            
            result = OperationResult(
                operation_name=operation_name,
                success=success,
                execution_results=execution_results,
                start_time=start_time,
                end_time=end_time
            )
            
            self.operation_history.append(result)
            
            # 发送操作完成事件
            await self.event_bus.emit("operation_completed", {
                "operation_name": operation_name,
                "result": result
            })
            
            if success:
                self.logger.info(f"游戏操作执行成功: {operation_name}")
            else:
                self.logger.warning(f"游戏操作执行失败: {operation_name}")
            
            return result
            
        except Exception as e:
            error_msg = f"执行操作 {operation_name} 时发生异常: {e}"
            self.logger.error(error_msg)
            
            return OperationResult(
                operation_name=operation_name,
                success=False,
                execution_results=[],
                start_time=start_time,
                end_time=datetime.now(),
                error_message=error_msg
            )
        
        finally:
            self.is_operating = False

    def _prepare_actions(self, actions: List[ActionConfig], kwargs: Dict[str, Any]) -> List[ActionConfig]:
        """准备动作参数。
        
        Args:
            actions: 原始动作列表
            kwargs: 参数字典
            
        Returns:
            准备好的动作列表
        """
        prepared_actions = []
        
        for action in actions:
            # 复制动作配置
            new_action = ActionConfig(
                action_type=action.action_type,
                parameters=action.parameters.copy(),
                timeout=action.timeout,
                retry_count=action.retry_count,
                retry_delay=action.retry_delay,
                description=action.description
            )
            
            # 更新参数
            for key, value in kwargs.items():
                if key in new_action.parameters:
                    new_action.parameters[key] = value
            
            prepared_actions.append(new_action)
        
        return prepared_actions

    async def _check_preconditions(self, operation: GameOperation) -> bool:
        """检查操作前置条件。
        
        Args:
            operation: 游戏操作
            
        Returns:
            前置条件是否满足
        """
        if not operation.preconditions:
            return True
        
        for condition in operation.preconditions:
            if not await self._evaluate_condition(condition):
                return False
        
        return True

    async def _check_postconditions(self, operation: GameOperation) -> bool:
        """检查操作后置条件。
        
        Args:
            operation: 游戏操作
            
        Returns:
            后置条件是否满足
        """
        if not operation.postconditions:
            return True
        
        for condition in operation.postconditions:
            if not await self._evaluate_condition(condition):
                return False
        
        return True

    async def _evaluate_condition(self, condition: str) -> bool:
        """评估条件。
        
        Args:
            condition: 条件字符串
            
        Returns:
            条件是否满足
        """
        # 简单的条件评估逻辑
        if condition == "game_running":
            return self.game_detector.is_game_running()
        elif condition == "main_menu_visible":
            scene = self.game_detector.detect_scene()
            return scene == SceneType.MAIN_MENU
        elif condition.startswith("ui_element_visible:"):
            element_name = condition.split(":")[1]
            elements = self.game_detector.detect_ui_elements([element_name])
            return len(elements) > 0
        
        # 默认返回True
        return True

    async def click_ui_element(self, element_name: str, **kwargs) -> OperationResult:
        """点击UI元素的便捷方法。
        
        Args:
            element_name: UI元素名称
            **kwargs: 其他参数
            
        Returns:
            操作执行结果
        """
        # 首先检测UI元素
        elements = self.game_detector.detect_ui_elements([element_name])
        if not elements:
            error_msg = f"未找到UI元素: {element_name}"
            self.logger.warning(error_msg)
            return OperationResult(
                operation_name="click_ui_element",
                success=False,
                execution_results=[],
                start_time=datetime.now(),
                end_time=datetime.now(),
                error_message=error_msg
            )
        
        element = elements[0]
        kwargs.update({
            "element_name": element_name,
            "x": element.position[0],
            "y": element.position[1]
        })
        
        return await self.execute_operation("click_ui_element", **kwargs)

    async def take_screenshot(self, save_path: str = None) -> OperationResult:
        """截图的便捷方法。
        
        Args:
            save_path: 保存路径
            
        Returns:
            操作执行结果
        """
        kwargs = {}
        if save_path:
            kwargs["save_path"] = save_path
        
        return await self.execute_operation("take_screenshot", **kwargs)

    async def wait_for_scene_change(self, duration: float = 2.0) -> OperationResult:
        """等待场景切换的便捷方法。
        
        Args:
            duration: 等待时长
            
        Returns:
            操作执行结果
        """
        return await self.execute_operation("wait_for_scene", duration=duration)

    def register_operation(self, operation: GameOperation) -> None:
        """注册新的游戏操作。
        
        Args:
            operation: 游戏操作配置
        """
        self.operations[operation.name] = operation
        self.logger.info(f"注册游戏操作: {operation.name}")

    def get_operation_history(self) -> List[OperationResult]:
        """获取操作历史。
        
        Returns:
            操作历史列表
        """
        return self.operation_history.copy()

    def clear_operation_history(self) -> None:
        """清空操作历史。"""
        self.operation_history.clear()

    def get_current_state(self) -> GameState:
        """获取当前游戏状态。
        
        Returns:
            当前游戏状态
        """
        return self.current_state

    def update_game_state(self) -> GameState:
        """更新游戏状态。
        
        Returns:
            更新后的游戏状态
        """
        if not self.game_detector.is_game_running():
            self.current_state = GameState.UNKNOWN
        else:
            scene = self.game_detector.detect_scene()
            if scene == SceneType.MAIN_MENU:
                self.current_state = GameState.MENU
            elif scene == SceneType.GAME_PLAY:
                self.current_state = GameState.PLAYING
            else:
                self.current_state = GameState.UNKNOWN
        
        return self.current_state

    def is_busy(self) -> bool:
        """检查是否正在执行操作。
        
        Returns:
            是否正在执行操作
        """
        return self.is_operating
