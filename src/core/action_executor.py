"""动作执行器模块..

提供动作的执行功能，包括鼠标操作、键盘操作、窗口操作等。
"""

import asyncio
import time
import pyautogui
import win32gui
import win32con
import win32api
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import cv2
import numpy as np

from .game_detector import GameDetector
from .logger import get_logger


class ActionType(Enum):
    """动作类型枚举。"""
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    KEY_PRESS = "key_press"
    KEY_COMBINATION = "key_combination"
    MOUSE_MOVE = "mouse_move"
    MOUSE_DRAG = "mouse_drag"
    SCROLL = "scroll"
    WAIT = "wait"
    SCREENSHOT = "screenshot"
    WINDOW_OPERATION = "window_operation"
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
    action_config: ActionConfig
    status: ExecutionStatus
    start_time: datetime
    end_time: datetime
    result_data: Dict[str, Any] = None
    error_message: str = ""
    retry_count: int = 0

    def __post_init__(self):
        if self.result_data is None:
            self.result_data = {}

    @property
    def duration(self) -> float:
        """获取执行时长（秒）。"""
        return (self.end_time - self.start_time).total_seconds()

    @property
    def success(self) -> bool:
        """是否执行成功。"""
        return self.status == ExecutionStatus.COMPLETED


class ActionExecutor:
    """动作执行器。"""

    def __init__(self, game_detector: Optional[GameDetector] = None):
        """初始化动作执行器。
        
        Args:
            game_detector: 游戏检测器实例
        """
        self.logger = get_logger(__name__)
        self.game_detector = game_detector or GameDetector()
        
        # 配置pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        # 执行状态
        self.is_executing = False
        self.current_action = None

    async def execute_action(self, action_config: ActionConfig) -> ExecutionResult:
        """执行单个动作。
        
        Args:
            action_config: 动作配置
            
        Returns:
            ExecutionResult: 执行结果
        """
        start_time = datetime.now()
        self.current_action = action_config
        self.is_executing = True
        
        result = ExecutionResult(
            action_config=action_config,
            status=ExecutionStatus.PENDING,
            start_time=start_time,
            end_time=start_time
        )
        
        try:
            self.logger.info(f"开始执行动作: {action_config.action_type.value}")
            result.status = ExecutionStatus.RUNNING
            
            # 执行动作（带重试机制）
            for attempt in range(action_config.retry_count + 1):
                try:
                    result.retry_count = attempt
                    
                    # 根据动作类型执行相应操作
                    if action_config.action_type == ActionType.CLICK:
                        await self._execute_click(action_config, result)
                    elif action_config.action_type == ActionType.DOUBLE_CLICK:
                        await self._execute_double_click(action_config, result)
                    elif action_config.action_type == ActionType.RIGHT_CLICK:
                        await self._execute_right_click(action_config, result)
                    elif action_config.action_type == ActionType.KEY_PRESS:
                        await self._execute_key_press(action_config, result)
                    elif action_config.action_type == ActionType.KEY_COMBINATION:
                        await self._execute_key_combination(action_config, result)
                    elif action_config.action_type == ActionType.MOUSE_MOVE:
                        await self._execute_mouse_move(action_config, result)
                    elif action_config.action_type == ActionType.MOUSE_DRAG:
                        await self._execute_mouse_drag(action_config, result)
                    elif action_config.action_type == ActionType.SCROLL:
                        await self._execute_scroll(action_config, result)
                    elif action_config.action_type == ActionType.WAIT:
                        await self._execute_wait(action_config, result)
                    elif action_config.action_type == ActionType.SCREENSHOT:
                        await self._execute_screenshot(action_config, result)
                    elif action_config.action_type == ActionType.WINDOW_OPERATION:
                        await self._execute_window_operation(action_config, result)
                    elif action_config.action_type == ActionType.CUSTOM:
                        await self._execute_custom_action(action_config, result)
                    else:
                        raise ValueError(f"不支持的动作类型: {action_config.action_type}")
                    
                    # 如果执行成功，跳出重试循环
                    result.status = ExecutionStatus.COMPLETED
                    break
                    
                except Exception as e:
                    error_msg = f"执行动作失败 (尝试 {attempt + 1}/{action_config.retry_count + 1}): {e}"
                    self.logger.warning(error_msg)
                    result.error_message = str(e)
                    
                    if attempt < action_config.retry_count:
                        # 等待重试
                        await asyncio.sleep(action_config.retry_delay)
                    else:
                        # 所有重试都失败
                        result.status = ExecutionStatus.FAILED
                        self.logger.error(f"动作执行最终失败: {action_config.action_type.value}")
            
            result.end_time = datetime.now()
            
            if result.status == ExecutionStatus.COMPLETED:
                self.logger.info(f"动作执行成功: {action_config.action_type.value}")
            
            return result
            
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error_message = str(e)
            result.end_time = datetime.now()
            self.logger.error(f"动作执行异常: {e}")
            return result
        
        finally:
            self.is_executing = False
            self.current_action = None

    async def execute_sequence(self, actions: List[ActionConfig]) -> List[ExecutionResult]:
        """执行动作序列。
        
        Args:
            actions: 动作配置列表
            
        Returns:
            执行结果列表
        """
        results = []
        
        for i, action in enumerate(actions):
            self.logger.info(f"执行动作序列 {i + 1}/{len(actions)}: {action.action_type.value}")
            
            result = await self.execute_action(action)
            results.append(result)
            
            # 如果动作失败且不是可选动作，停止执行
            if not result.success and not action.parameters.get("optional", False):
                self.logger.error(f"必需动作执行失败，停止序列执行: {action.action_type.value}")
                break
        
        return results

    async def _execute_click(self, action_config: ActionConfig, result: ExecutionResult) -> None:
        """执行点击操作。"""
        params = action_config.parameters
        x = params.get("x", 0)
        y = params.get("y", 0)
        button = params.get("button", "left")
        
        # 确保坐标在屏幕范围内
        screen_width, screen_height = pyautogui.size()
        x = max(0, min(x, screen_width - 1))
        y = max(0, min(y, screen_height - 1))
        
        pyautogui.click(x, y, button=button)
        
        result.result_data = {
            "clicked_position": (x, y),
            "button": button
        }

    async def _execute_double_click(self, action_config: ActionConfig, result: ExecutionResult) -> None:
        """执行双击操作。"""
        params = action_config.parameters
        x = params.get("x", 0)
        y = params.get("y", 0)
        
        screen_width, screen_height = pyautogui.size()
        x = max(0, min(x, screen_width - 1))
        y = max(0, min(y, screen_height - 1))
        
        pyautogui.doubleClick(x, y)
        
        result.result_data = {
            "clicked_position": (x, y)
        }

    async def _execute_right_click(self, action_config: ActionConfig, result: ExecutionResult) -> None:
        """执行右键点击操作。"""
        params = action_config.parameters
        x = params.get("x", 0)
        y = params.get("y", 0)
        
        screen_width, screen_height = pyautogui.size()
        x = max(0, min(x, screen_width - 1))
        y = max(0, min(y, screen_height - 1))
        
        pyautogui.rightClick(x, y)
        
        result.result_data = {
            "clicked_position": (x, y)
        }

    async def _execute_key_press(self, action_config: ActionConfig, result: ExecutionResult) -> None:
        """执行按键操作。"""
        params = action_config.parameters
        key = params.get("key", "")
        duration = params.get("duration", 0.1)
        
        if not key:
            raise ValueError("按键参数不能为空")
        
        pyautogui.keyDown(key)
        await asyncio.sleep(duration)
        pyautogui.keyUp(key)
        
        result.result_data = {
            "key": key,
            "duration": duration
        }

    async def _execute_key_combination(self, action_config: ActionConfig, result: ExecutionResult) -> None:
        """执行组合键操作。"""
        params = action_config.parameters
        keys = params.get("keys", [])
        
        if not keys:
            raise ValueError("组合键参数不能为空")
        
        pyautogui.hotkey(*keys)
        
        result.result_data = {
            "keys": keys
        }

    async def _execute_mouse_move(self, action_config: ActionConfig, result: ExecutionResult) -> None:
        """执行鼠标移动操作。"""
        params = action_config.parameters
        x = params.get("x", 0)
        y = params.get("y", 0)
        duration = params.get("duration", 0.5)
        
        screen_width, screen_height = pyautogui.size()
        x = max(0, min(x, screen_width - 1))
        y = max(0, min(y, screen_height - 1))
        
        pyautogui.moveTo(x, y, duration=duration)
        
        result.result_data = {
            "target_position": (x, y),
            "duration": duration
        }

    async def _execute_mouse_drag(self, action_config: ActionConfig, result: ExecutionResult) -> None:
        """执行鼠标拖拽操作。"""
        params = action_config.parameters
        start_x = params.get("start_x", 0)
        start_y = params.get("start_y", 0)
        end_x = params.get("end_x", 0)
        end_y = params.get("end_y", 0)
        duration = params.get("duration", 1.0)
        button = params.get("button", "left")
        
        screen_width, screen_height = pyautogui.size()
        start_x = max(0, min(start_x, screen_width - 1))
        start_y = max(0, min(start_y, screen_height - 1))
        end_x = max(0, min(end_x, screen_width - 1))
        end_y = max(0, min(end_y, screen_height - 1))
        
        pyautogui.drag(end_x - start_x, end_y - start_y, duration=duration, button=button)
        
        result.result_data = {
            "start_position": (start_x, start_y),
            "end_position": (end_x, end_y),
            "duration": duration,
            "button": button
        }

    async def _execute_scroll(self, action_config: ActionConfig, result: ExecutionResult) -> None:
        """执行滚轮操作。"""
        params = action_config.parameters
        x = params.get("x", None)
        y = params.get("y", None)
        clicks = params.get("clicks", 1)
        
        if x is not None and y is not None:
            pyautogui.scroll(clicks, x=x, y=y)
        else:
            pyautogui.scroll(clicks)
        
        result.result_data = {
            "position": (x, y) if x is not None and y is not None else None,
            "clicks": clicks
        }

    async def _execute_wait(self, action_config: ActionConfig, result: ExecutionResult) -> None:
        """执行等待操作。"""
        params = action_config.parameters
        duration = params.get("duration", 1.0)
        
        await asyncio.sleep(duration)
        
        result.result_data = {
            "duration": duration
        }

    async def _execute_screenshot(self, action_config: ActionConfig, result: ExecutionResult) -> None:
        """执行截图操作。"""
        params = action_config.parameters
        save_path = params.get("save_path", "screenshot.png")
        region = params.get("region", None)  # (x, y, width, height)
        
        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()
        
        screenshot.save(save_path)
        
        result.result_data = {
            "save_path": save_path,
            "region": region,
            "size": screenshot.size
        }

    async def _execute_window_operation(self, action_config: ActionConfig, result: ExecutionResult) -> None:
        """执行窗口操作。"""
        params = action_config.parameters
        operation = params.get("operation", "")
        window_title = params.get("window_title", "")
        
        if operation == "activate":
            # 激活窗口
            hwnd = win32gui.FindWindow(None, window_title)
            if hwnd:
                win32gui.SetForegroundWindow(hwnd)
                result.result_data = {"window_activated": True}
            else:
                raise ValueError(f"未找到窗口: {window_title}")
        
        elif operation == "minimize":
            # 最小化窗口
            hwnd = win32gui.FindWindow(None, window_title)
            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                result.result_data = {"window_minimized": True}
            else:
                raise ValueError(f"未找到窗口: {window_title}")
        
        elif operation == "maximize":
            # 最大化窗口
            hwnd = win32gui.FindWindow(None, window_title)
            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                result.result_data = {"window_maximized": True}
            else:
                raise ValueError(f"未找到窗口: {window_title}")
        
        else:
            raise ValueError(f"不支持的窗口操作: {operation}")

    async def _execute_custom_action(self, action_config: ActionConfig, result: ExecutionResult) -> None:
        """执行自定义动作。"""
        params = action_config.parameters
        custom_function = params.get("function", None)
        custom_args = params.get("args", [])
        custom_kwargs = params.get("kwargs", {})
        
        if not custom_function:
            raise ValueError("自定义动作必须提供function参数")
        
        if callable(custom_function):
            if asyncio.iscoroutinefunction(custom_function):
                custom_result = await custom_function(*custom_args, **custom_kwargs)
            else:
                custom_result = custom_function(*custom_args, **custom_kwargs)
            
            result.result_data = {
                "custom_result": custom_result
            }
        else:
            raise ValueError("function参数必须是可调用对象")

    def is_busy(self) -> bool:
        """检查是否正在执行动作。
        
        Returns:
            是否正在执行动作
        """
        return self.is_executing

    def get_current_action(self) -> Optional[ActionConfig]:
        """获取当前正在执行的动作。
        
        Returns:
            当前动作配置，如果没有则返回None
        """
        return self.current_action

    def cancel_current_action(self) -> bool:
        """取消当前正在执行的动作。
        
        Returns:
            是否成功取消
        """
        if self.is_executing:
            # 这里可以添加取消逻辑
            # 由于pyautogui的操作通常很快，实际取消可能比较困难
            self.logger.warning("尝试取消当前动作")
            return True
        return False
