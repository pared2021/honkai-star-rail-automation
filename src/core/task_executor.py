"""任务执行器模块.

提供任务执行功能，包括动作执行、状态监控和错误处理。
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from .events import EventBus
from .logger import get_logger
from .error_handler import ErrorHandler


class ActionType(Enum):
    """动作类型枚举。"""
    CLICK = "click"
    KEY_PRESS = "key_press"
    WAIT = "wait"
    SCREENSHOT = "screenshot"
    DETECT_UI = "detect_ui"
    CUSTOM = "custom"


class ExecutionStatus(Enum):
    """执行状态枚举。"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ActionConfig:
    """动作配置。"""
    action_type: ActionType
    parameters: Dict[str, Any]
    timeout: float = 30.0
    retry_count: int = 3
    retry_delay: float = 1.0
    description: str = ""


@dataclass
class ExecutionResult:
    """执行结果。"""
    status: ExecutionStatus
    result: Any = None
    error: Optional[Exception] = None
    execution_time: float = 0.0
    timestamp: datetime = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class TaskExecutor:
    """任务执行器。"""

    def __init__(self, event_bus: Optional[EventBus] = None):
        """初始化任务执行器。
        
        Args:
            event_bus: 事件总线实例
        """
        self.logger = get_logger(__name__)
        self.event_bus = event_bus or EventBus()
        self.error_handler = ErrorHandler()
        
        # 执行状态
        self._is_running = False
        self._current_action: Optional[ActionConfig] = None
        self._execution_history: List[ExecutionResult] = []
        
        # 注册动作处理器
        self._action_handlers: Dict[ActionType, Callable] = {
            ActionType.CLICK: self._handle_click,
            ActionType.KEY_PRESS: self._handle_key_press,
            ActionType.WAIT: self._handle_wait,
            ActionType.SCREENSHOT: self._handle_screenshot,
            ActionType.DETECT_UI: self._handle_detect_ui,
            ActionType.CUSTOM: self._handle_custom,
        }

    async def execute_action(self, action_config: ActionConfig) -> ExecutionResult:
        """执行单个动作。
        
        Args:
            action_config: 动作配置
            
        Returns:
            ExecutionResult: 执行结果
        """
        start_time = time.time()
        self._current_action = action_config
        
        try:
            self.logger.info(f"开始执行动作: {action_config.action_type.value}")
            
            # 获取动作处理器
            handler = self._action_handlers.get(action_config.action_type)
            if not handler:
                raise ValueError(f"不支持的动作类型: {action_config.action_type}")
            
            # 执行动作（带重试机制）
            result = await self._execute_with_retry(handler, action_config)
            
            execution_time = time.time() - start_time
            execution_result = ExecutionResult(
                status=ExecutionStatus.COMPLETED,
                result=result,
                execution_time=execution_time
            )
            
            self.logger.info(f"动作执行成功: {action_config.action_type.value}")
            
        except Exception as e:
            execution_time = time.time() - start_time
            execution_result = ExecutionResult(
                status=ExecutionStatus.FAILED,
                error=e,
                execution_time=execution_time
            )
            
            self.logger.error(f"动作执行失败: {action_config.action_type.value}, 错误: {e}")
            
        finally:
            self._current_action = None
            self._execution_history.append(execution_result)
            
            # 发送执行完成事件
            await self.event_bus.emit("action_executed", {
                "action_config": action_config,
                "result": execution_result
            })
        
        return execution_result

    async def execute_sequence(self, actions: List[ActionConfig]) -> List[ExecutionResult]:
        """执行动作序列。
        
        Args:
            actions: 动作配置列表
            
        Returns:
            List[ExecutionResult]: 执行结果列表
        """
        results = []
        
        for i, action in enumerate(actions):
            self.logger.info(f"执行序列动作 {i+1}/{len(actions)}: {action.action_type.value}")
            
            result = await self.execute_action(action)
            results.append(result)
            
            # 如果动作失败，停止执行序列
            if result.status == ExecutionStatus.FAILED:
                self.logger.error(f"序列执行在第 {i+1} 个动作失败，停止执行")
                break
        
        return results

    async def _execute_with_retry(self, handler: Callable, action_config: ActionConfig) -> Any:
        """带重试机制的执行。
        
        Args:
            handler: 动作处理器
            action_config: 动作配置
            
        Returns:
            执行结果
        """
        last_error = None
        
        for attempt in range(action_config.retry_count + 1):
            try:
                if attempt > 0:
                    self.logger.info(f"重试执行动作，第 {attempt} 次")
                    await asyncio.sleep(action_config.retry_delay)
                
                # 设置超时
                result = await asyncio.wait_for(
                    handler(action_config.parameters),
                    timeout=action_config.timeout
                )
                
                return result
                
            except Exception as e:
                last_error = e
                self.logger.warning(f"动作执行失败 (尝试 {attempt + 1}/{action_config.retry_count + 1}): {e}")
        
        # 所有重试都失败
        raise last_error or Exception("执行失败")

    async def _handle_click(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """处理点击动作。
        
        Args:
            parameters: 动作参数
            
        Returns:
            执行结果
        """
        x = parameters.get("x", 0)
        y = parameters.get("y", 0)
        button = parameters.get("button", "left")
        
        self.logger.debug(f"模拟点击: ({x}, {y}), 按钮: {button}")
        
        # 模拟点击操作
        await asyncio.sleep(0.1)  # 模拟执行时间
        
        return {
            "action": "click",
            "position": (x, y),
            "button": button,
            "success": True
        }

    async def _handle_key_press(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """处理按键动作。
        
        Args:
            parameters: 动作参数
            
        Returns:
            执行结果
        """
        key = parameters.get("key", "")
        modifiers = parameters.get("modifiers", [])
        
        self.logger.debug(f"模拟按键: {key}, 修饰键: {modifiers}")
        
        # 模拟按键操作
        await asyncio.sleep(0.1)  # 模拟执行时间
        
        return {
            "action": "key_press",
            "key": key,
            "modifiers": modifiers,
            "success": True
        }

    async def _handle_wait(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """处理等待动作。
        
        Args:
            parameters: 动作参数
            
        Returns:
            执行结果
        """
        duration = parameters.get("duration", 1.0)
        
        self.logger.debug(f"等待 {duration} 秒")
        
        await asyncio.sleep(duration)
        
        return {
            "action": "wait",
            "duration": duration,
            "success": True
        }

    async def _handle_screenshot(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """处理截图动作。
        
        Args:
            parameters: 动作参数
            
        Returns:
            执行结果
        """
        save_path = parameters.get("save_path", "")
        
        self.logger.debug(f"截图保存到: {save_path}")
        
        # 模拟截图操作
        await asyncio.sleep(0.2)  # 模拟执行时间
        
        return {
            "action": "screenshot",
            "save_path": save_path,
            "success": True
        }

    async def _handle_detect_ui(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """处理UI检测动作。
        
        Args:
            parameters: 动作参数
            
        Returns:
            执行结果
        """
        element_name = parameters.get("element_name", "")
        
        self.logger.debug(f"检测UI元素: {element_name}")
        
        # 模拟UI检测操作
        await asyncio.sleep(0.3)  # 模拟执行时间
        
        return {
            "action": "detect_ui",
            "element_name": element_name,
            "found": True,
            "position": (100, 100),
            "confidence": 0.95
        }

    async def _handle_custom(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """处理自定义动作。
        
        Args:
            parameters: 动作参数
            
        Returns:
            执行结果
        """
        custom_func = parameters.get("function")
        custom_args = parameters.get("args", [])
        custom_kwargs = parameters.get("kwargs", {})
        
        if not custom_func:
            raise ValueError("自定义动作需要提供function参数")
        
        self.logger.debug(f"执行自定义动作: {custom_func.__name__ if hasattr(custom_func, '__name__') else 'unknown'}")
        
        # 执行自定义函数
        if asyncio.iscoroutinefunction(custom_func):
            result = await custom_func(*custom_args, **custom_kwargs)
        else:
            result = custom_func(*custom_args, **custom_kwargs)
        
        return {
            "action": "custom",
            "result": result,
            "success": True
        }

    def get_execution_history(self) -> List[ExecutionResult]:
        """获取执行历史。
        
        Returns:
            执行历史列表
        """
        return self._execution_history.copy()

    def clear_execution_history(self) -> None:
        """清空执行历史。"""
        self._execution_history.clear()

    def is_running(self) -> bool:
        """检查是否正在执行。
        
        Returns:
            是否正在执行
        """
        return self._current_action is not None

    def get_current_action(self) -> Optional[ActionConfig]:
        """获取当前执行的动作。
        
        Returns:
            当前动作配置
        """
        return self._current_action
