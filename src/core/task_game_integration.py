"""任务执行引擎与游戏操作库集成模块.

提供TaskExecutor与GameOperator之间的集成适配器和统一接口。
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime

from .enhanced_task_executor import (
    EnhancedTaskExecutor, TaskConfig, TaskExecution, TaskStatus, TaskType, TaskPriority
)
from .game_operator import (
    GameOperator, IGameOperator, OperationConfig, OperationResult, 
    ClickType, WaitCondition, OperationMethod
)
from .game_detector import GameDetector, UIElement
from .events import EventBus
from .logger import get_logger


class BaseTaskRunner:
    """任务运行器基类."""
    
    def __init__(self, name: str):
        """初始化任务运行器.
        
        Args:
            name: 运行器名称
        """
        self.name = name
        self.logger = get_logger(f"TaskRunner.{name}")
    
    def run(self, task_config: Dict[str, Any]) -> bool:
        """执行任务.
        
        Args:
            task_config: 任务配置
            
        Returns:
            bool: 执行是否成功
        """
        raise NotImplementedError("子类必须实现run方法")
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证任务配置.
        
        Args:
            config: 任务配置
            
        Returns:
            bool: 配置是否有效
        """
        return True
    
    def cleanup(self) -> None:
        """清理资源."""
        pass


class GameActionType(Enum):
    """游戏动作类型。"""
    CLICK = "click"
    SWIPE = "swipe"
    INPUT_TEXT = "input_text"
    WAIT_CONDITION = "wait_condition"
    SCREENSHOT = "screenshot"
    DETECT_UI = "detect_ui"
    DETECT_SCENE = "detect_scene"
    CUSTOM = "custom"


@dataclass
class GameAction:
    """游戏动作配置。"""
    action_type: GameActionType
    target: Optional[Union[str, tuple, UIElement]] = None
    params: Dict[str, Any] = field(default_factory=dict)
    config: Optional[OperationConfig] = None
    retry_count: int = 3
    timeout: float = 30.0
    description: str = ""
    
    def __post_init__(self):
        if not self.description:
            self.description = f"{self.action_type.value} action"


@dataclass
class GameActionResult:
    """游戏动作执行结果。"""
    action: GameAction
    operation_result: Optional[OperationResult] = None
    success: bool = False
    execution_time: float = 0.0
    error_message: str = ""
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class GameTaskRunner(BaseTaskRunner):
    """游戏任务运行器基类。"""
    
    def __init__(self, task_type: TaskType, game_operator: IGameOperator, 
                 game_detector: Optional[GameDetector] = None):
        """初始化游戏任务运行器。
        
        Args:
            task_type: 任务类型
            game_operator: 游戏操作器
            game_detector: 游戏检测器
        """
        super().__init__(task_type)
        self.task_type = task_type  # 确保task_type属性被设置
        self.game_operator = game_operator
        self.game_detector = game_detector
        self.action_history: List[GameActionResult] = []
        
    async def execute_game_action(self, action: GameAction) -> GameActionResult:
        """执行游戏动作。
        
        Args:
            action: 游戏动作配置
            
        Returns:
            动作执行结果
        """
        start_time = time.time()
        result = GameActionResult(action=action)
        
        try:
            for attempt in range(action.retry_count + 1):
                try:
                    if action.action_type == GameActionType.CLICK:
                        operation_result = await self._execute_click_action(action)
                    elif action.action_type == GameActionType.SWIPE:
                        operation_result = await self._execute_swipe_action(action)
                    elif action.action_type == GameActionType.INPUT_TEXT:
                        operation_result = await self._execute_input_action(action)
                    elif action.action_type == GameActionType.WAIT_CONDITION:
                        operation_result = await self._execute_wait_action(action)
                    elif action.action_type == GameActionType.SCREENSHOT:
                        operation_result = await self._execute_screenshot_action(action)
                    elif action.action_type == GameActionType.DETECT_UI:
                        operation_result = await self._execute_detect_ui_action(action)
                    elif action.action_type == GameActionType.DETECT_SCENE:
                        operation_result = await self._execute_detect_scene_action(action)
                    elif action.action_type == GameActionType.CUSTOM:
                        operation_result = await self._execute_custom_action(action)
                    else:
                        raise ValueError(f"不支持的动作类型: {action.action_type}")
                    
                    result.operation_result = operation_result
                    result.success = operation_result.success if operation_result else False
                    result.retry_count = attempt
                    
                    if result.success:
                        break
                        
                except Exception as e:
                    self.logger.error(f"执行游戏动作失败 (尝试 {attempt + 1}): {e}")
                    result.error_message = str(e)
                    result.retry_count = attempt
                    
                    if attempt < action.retry_count:
                        await asyncio.sleep(1.0)  # 重试前等待
                    
        except Exception as e:
            result.error_message = f"游戏动作执行异常: {e}"
            self.logger.error(result.error_message)
        
        result.execution_time = time.time() - start_time
        self.action_history.append(result)
        
        return result
    
    async def _execute_click_action(self, action: GameAction) -> OperationResult:
        """执行点击动作。"""
        click_type = ClickType(action.params.get('click_type', 'left'))
        return await self.game_operator.click(
            target=action.target,
            click_type=click_type,
            config=action.config
        )
    
    async def _execute_swipe_action(self, action: GameAction) -> OperationResult:
        """执行滑动动作。"""
        end_target = action.params.get('end_target')
        duration = action.params.get('duration', 1.0)
        
        if not end_target:
            raise ValueError("滑动动作缺少结束位置参数")
        
        return await self.game_operator.swipe(
            start=action.target,
            end=end_target,
            duration=duration,
            config=action.config
        )
    
    async def _execute_input_action(self, action: GameAction) -> OperationResult:
        """执行输入动作。"""
        text = action.params.get('text', '')
        
        if not text:
            raise ValueError("输入动作缺少文本参数")
        
        return await self.game_operator.input_text(
            text=text,
            target=action.target,
            config=action.config
        )
    
    async def _execute_wait_action(self, action: GameAction) -> OperationResult:
        """执行等待动作。"""
        condition = WaitCondition(action.params.get('condition', 'ui_element_appear'))
        condition_params = action.params.get('condition_params', {})
        
        return await self.game_operator.wait_for_condition(
            condition=condition,
            condition_params=condition_params,
            timeout=action.timeout
        )
    
    async def _execute_screenshot_action(self, action: GameAction) -> OperationResult:
        """执行截图动作。"""
        start_time = time.time()
        
        try:
            if self.game_detector:
                screenshot = self.game_detector.capture_screen()
                return OperationResult(
                    success=screenshot is not None,
                    execution_time=time.time() - start_time,
                    metadata={'screenshot': screenshot}
                )
            else:
                return OperationResult(
                    success=False,
                    execution_time=time.time() - start_time,
                    error_message="游戏检测器未初始化"
                )
        except Exception as e:
            return OperationResult(
                success=False,
                execution_time=time.time() - start_time,
                error_message=f"截图失败: {e}"
            )
    
    async def _execute_detect_ui_action(self, action: GameAction) -> OperationResult:
        """执行UI检测动作。"""
        start_time = time.time()
        
        try:
            if not self.game_detector:
                return OperationResult(
                    success=False,
                    execution_time=time.time() - start_time,
                    error_message="游戏检测器未初始化"
                )
            
            element_names = action.params.get('element_names', [])
            if isinstance(action.target, str):
                element_names.append(action.target)
            
            elements = self.game_detector.detect_ui_elements(element_names)
            
            return OperationResult(
                success=len(elements) > 0,
                execution_time=time.time() - start_time,
                metadata={
                    'detected_elements': elements,
                    'element_count': len(elements)
                }
            )
        except Exception as e:
            return OperationResult(
                success=False,
                execution_time=time.time() - start_time,
                error_message=f"UI检测失败: {e}"
            )
    
    async def _execute_detect_scene_action(self, action: GameAction) -> OperationResult:
        """执行场景检测动作。"""
        start_time = time.time()
        
        try:
            if not self.game_detector:
                return OperationResult(
                    success=False,
                    execution_time=time.time() - start_time,
                    error_message="游戏检测器未初始化"
                )
            
            current_scene = self.game_detector.detect_scene()
            expected_scene = action.params.get('expected_scene')
            
            success = True
            if expected_scene:
                success = current_scene.value == expected_scene
            
            return OperationResult(
                success=success,
                execution_time=time.time() - start_time,
                metadata={
                    'current_scene': current_scene.value,
                    'expected_scene': expected_scene
                }
            )
        except Exception as e:
            return OperationResult(
                success=False,
                execution_time=time.time() - start_time,
                error_message=f"场景检测失败: {e}"
            )
    
    async def _execute_custom_action(self, action: GameAction) -> OperationResult:
        """执行自定义动作。"""
        start_time = time.time()
        
        try:
            custom_func = action.params.get('custom_function')
            if not custom_func:
                raise ValueError("自定义动作缺少执行函数")
            
            # 执行自定义函数
            if asyncio.iscoroutinefunction(custom_func):
                result = await custom_func(self.game_operator, self.game_detector, action.params)
            else:
                result = custom_func(self.game_operator, self.game_detector, action.params)
            
            # 处理返回结果
            if isinstance(result, OperationResult):
                return result
            elif isinstance(result, bool):
                return OperationResult(
                    success=result,
                    execution_time=time.time() - start_time
                )
            else:
                return OperationResult(
                    success=True,
                    execution_time=time.time() - start_time,
                    metadata={'custom_result': result}
                )
                
        except Exception as e:
            return OperationResult(
                success=False,
                execution_time=time.time() - start_time,
                error_message=f"自定义动作执行失败: {e}"
            )
    
    def get_action_history(self) -> List[GameActionResult]:
        """获取动作执行历史。"""
        return self.action_history.copy()
    
    def clear_action_history(self):
        """清空动作执行历史。"""
        self.action_history.clear()


class GameTaskIntegration:
    """游戏任务集成管理器。"""
    
    def __init__(self, 
                 task_executor: Optional[EnhancedTaskExecutor] = None,
                 game_operator: Optional[IGameOperator] = None,
                 game_detector: Optional[GameDetector] = None,
                 event_bus: Optional[EventBus] = None):
        """初始化游戏任务集成管理器。
        
        Args:
            task_executor: 任务执行器
            game_operator: 游戏操作器
            game_detector: 游戏检测器
            event_bus: 事件总线
        """
        self.logger = get_logger(__name__)
        self.task_executor = task_executor or EnhancedTaskExecutor()
        self.game_operator = game_operator or GameOperator()
        self.game_detector = game_detector or GameDetector()
        self.event_bus = event_bus or EventBus()
        
        # 游戏任务运行器注册表
        self.game_runners: Dict[TaskType, GameTaskRunner] = {}
        
        # 集成配置
        self.integration_config = {
            'auto_screenshot_on_error': True,
            'max_action_retry': 3,
            'action_timeout': 30.0,
            'ui_detection_interval': 0.5,
            'scene_detection_enabled': True
        }
        
        # 注册事件监听器
        self._register_event_listeners()
        
        self.logger.info("游戏任务集成管理器初始化完成")
    
    def _register_event_listeners(self):
        """注册事件监听器。"""
        self.event_bus.on("task_started", self._on_task_started)
        self.event_bus.on("task_failed", self._on_task_failed)
        self.event_bus.on("task_completed", self._on_task_completed)
    
    async def _on_task_started(self, event_data: Dict[str, Any]):
        """处理任务开始事件。"""
        execution_id = event_data.get("execution_id")
        task_config = event_data.get("task_config")
        
        if task_config and self.integration_config.get('scene_detection_enabled'):
            # 检测当前游戏场景
            try:
                current_scene = self.game_detector.detect_scene()
                self.logger.info(f"任务 {execution_id} 开始时的游戏场景: {current_scene.value}")
                
                # 发送场景检测事件
                await self.event_bus.emit("game_scene_detected", {
                    "execution_id": execution_id,
                    "scene": current_scene.value,
                    "timestamp": datetime.now()
                })
            except Exception as e:
                self.logger.error(f"场景检测失败: {e}")
    
    async def _on_task_failed(self, event_data: Dict[str, Any]):
        """处理任务失败事件。"""
        execution_id = event_data.get("execution_id")
        
        if self.integration_config.get('auto_screenshot_on_error'):
            # 自动截图用于错误分析
            try:
                screenshot = self.game_detector.capture_screen()
                if screenshot:
                    await self.event_bus.emit("error_screenshot_captured", {
                        "execution_id": execution_id,
                        "screenshot": screenshot,
                        "timestamp": datetime.now()
                    })
                    self.logger.info(f"任务 {execution_id} 失败时已自动截图")
            except Exception as e:
                self.logger.error(f"错误截图失败: {e}")
    
    async def _on_task_completed(self, event_data: Dict[str, Any]):
        """处理任务完成事件。"""
        execution_id = event_data.get("execution_id")
        task_execution = event_data.get("task_execution")
        
        if task_execution and execution_id in self.game_runners:
            # 清理游戏运行器的历史记录
            runner = self.game_runners[execution_id]
            if hasattr(runner, 'clear_action_history'):
                runner.clear_action_history()
    
    def register_game_runner(self, task_type: TaskType, runner_class: type):
        """注册游戏任务运行器。
        
        Args:
            task_type: 任务类型
            runner_class: 运行器类
        """
        if not issubclass(runner_class, GameTaskRunner):
            raise ValueError("运行器类必须继承自GameTaskRunner")
        
        # 创建运行器实例
        runner = runner_class(task_type, self.game_operator, self.game_detector)
        
        # 注册到任务执行器
        self.task_executor.register_runner(task_type, runner)
        self.game_runners[task_type] = runner
        
        self.logger.info(f"注册游戏任务运行器: {task_type.value} -> {runner_class.__name__}")
    
    async def submit_game_task(self, 
                              task_type: TaskType,
                              actions: List[GameAction],
                              priority: TaskPriority = TaskPriority.MEDIUM,
                              config: Optional[Dict[str, Any]] = None) -> str:
        """提交游戏任务。
        
        Args:
            task_type: 任务类型
            actions: 游戏动作列表
            priority: 任务优先级
            config: 任务配置
            
        Returns:
            任务执行ID
        """
        task_config = TaskConfig(
            task_id=f"game_task_{int(time.time() * 1000)}",
            task_type=task_type,
            name=f"游戏任务_{task_type.value}",
            priority=priority,
            parameters=config or {}
        )
        
        # 将动作列表添加到配置中
        task_config.parameters['game_actions'] = actions
        
        # 提交任务
        execution = await self.task_executor.submit_task(task_config)
        
        return execution.execution_id
    
    async def execute_action_sequence(self, 
                                    actions: List[GameAction],
                                    stop_on_failure: bool = True) -> List[GameActionResult]:
        """执行游戏动作序列。
        
        Args:
            actions: 动作列表
            stop_on_failure: 失败时是否停止
            
        Returns:
            动作执行结果列表
        """
        results = []
        
        # 创建临时游戏任务运行器
        temp_runner = GameTaskRunner(TaskType.CUSTOM, self.game_operator, self.game_detector)
        
        for action in actions:
            result = await temp_runner.execute_game_action(action)
            results.append(result)
            
            if not result.success and stop_on_failure:
                self.logger.warning(f"动作序列执行失败，停止执行: {action.description}")
                break
        
        return results
    
    def get_integration_config(self) -> Dict[str, Any]:
        """获取集成配置。"""
        return self.integration_config.copy()
    
    def update_integration_config(self, config: Dict[str, Any]):
        """更新集成配置。
        
        Args:
            config: 新的配置项
        """
        self.integration_config.update(config)
        self.logger.info(f"集成配置已更新: {config}")
    
    def get_game_operator(self) -> IGameOperator:
        """获取游戏操作器。"""
        return self.game_operator
    
    def get_game_detector(self) -> GameDetector:
        """获取游戏检测器。"""
        return self.game_detector
    
    def get_task_executor(self) -> EnhancedTaskExecutor:
        """获取任务执行器。"""
        return self.task_executor
    
    async def shutdown(self):
        """关闭集成管理器。"""
        self.logger.info("游戏任务集成管理器正在关闭...")
        
        # 关闭任务执行器
        if hasattr(self.task_executor, 'shutdown'):
            await self.task_executor.shutdown()
        
        # 清理游戏运行器
        for runner in self.game_runners.values():
            if hasattr(runner, 'clear_action_history'):
                runner.clear_action_history()
        
        self.game_runners.clear()
        
        self.logger.info("游戏任务集成管理器已关闭")


# 便捷函数
def create_click_action(target: Union[str, tuple, UIElement], 
                       click_type: ClickType = ClickType.LEFT,
                       config: Optional[OperationConfig] = None,
                       retry_count: int = 3,
                       description: str = "") -> GameAction:
    """创建点击动作。"""
    return GameAction(
        action_type=GameActionType.CLICK,
        target=target,
        params={'click_type': click_type.value},
        config=config,
        retry_count=retry_count,
        description=description or f"点击 {target}"
    )


def create_swipe_action(start: Union[str, tuple, UIElement],
                       end: Union[str, tuple, UIElement],
                       duration: float = 1.0,
                       config: Optional[OperationConfig] = None,
                       retry_count: int = 3,
                       description: str = "") -> GameAction:
    """创建滑动动作。"""
    return GameAction(
        action_type=GameActionType.SWIPE,
        target=start,
        params={'end_target': end, 'duration': duration},
        config=config,
        retry_count=retry_count,
        description=description or f"滑动 {start} -> {end}"
    )


def create_input_action(text: str,
                       target: Optional[Union[str, tuple, UIElement]] = None,
                       config: Optional[OperationConfig] = None,
                       retry_count: int = 3,
                       description: str = "") -> GameAction:
    """创建输入动作。"""
    return GameAction(
        action_type=GameActionType.INPUT_TEXT,
        target=target,
        params={'text': text},
        config=config,
        retry_count=retry_count,
        description=description or f"输入文本: {text[:20]}..."
    )


def create_wait_action(condition: WaitCondition,
                      condition_params: Dict[str, Any],
                      timeout: float = 30.0,
                      retry_count: int = 1,
                      description: str = "") -> GameAction:
    """创建等待动作。"""
    return GameAction(
        action_type=GameActionType.WAIT_CONDITION,
        params={'condition': condition.value, 'condition_params': condition_params},
        timeout=timeout,
        retry_count=retry_count,
        description=description or f"等待条件: {condition.value}"
    )