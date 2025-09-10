"""游戏操作器模块.

提供底层游戏操作功能，包括点击、滑动、输入等基础操作。
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import logging

try:
    import win32api
    import win32con
    import win32gui
    import pyautogui
    import cv2
    import numpy as np
except ImportError:
    win32api = None
    win32con = None
    win32gui = None
    pyautogui = None
    cv2 = None
    np = None

from .game_detector import GameDetector, UIElement, TemplateInfo
from .sync_adapter import SyncAdapter
from .logger import setup_logger
from .error_handler import ErrorHandler
from src.config.config_manager import ConfigManager


class OperationMethod(Enum):
    """操作方法枚举."""
    WIN32_API = "win32_api"
    PYAUTOGUI = "pyautogui"
    AUTO = "auto"


class ClickType(Enum):
    """点击类型枚举."""
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"
    DOUBLE = "double"


class WaitCondition(Enum):
    """等待条件枚举."""
    UI_ELEMENT_APPEAR = "ui_element_appear"
    UI_ELEMENT_DISAPPEAR = "ui_element_disappear"
    SCENE_CHANGE = "scene_change"
    CUSTOM = "custom"


@dataclass
class OperationConfig:
    """操作配置."""
    method: OperationMethod = OperationMethod.AUTO
    timeout: float = 30.0
    retry_count: int = 3
    retry_delay: float = 1.0
    verify_result: bool = True
    screenshot_before: bool = False
    screenshot_after: bool = False


@dataclass
class OperationResult:
    """操作结果."""
    success: bool
    execution_time: float
    error_message: str = ""
    screenshot_before: Optional[bytes] = None
    screenshot_after: Optional[bytes] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class IGameOperator(ABC):
    """游戏操作器接口."""

    @abstractmethod
    async def click(self, 
                   target: Union[Tuple[int, int], str, UIElement], 
                   click_type: ClickType = ClickType.LEFT,
                   config: Optional[OperationConfig] = None) -> OperationResult:
        """点击操作.
        
        Args:
            target: 点击目标（坐标、模板名称或UI元素）
            click_type: 点击类型
            config: 操作配置
            
        Returns:
            操作结果
        """
        pass

    @abstractmethod
    async def swipe(self, 
                   start: Union[Tuple[int, int], str, UIElement],
                   end: Union[Tuple[int, int], str, UIElement],
                   duration: float = 1.0,
                   config: Optional[OperationConfig] = None) -> OperationResult:
        """滑动操作.
        
        Args:
            start: 起始位置
            end: 结束位置
            duration: 滑动持续时间
            config: 操作配置
            
        Returns:
            操作结果
        """
        pass

    @abstractmethod
    async def input_text(self, 
                        text: str,
                        target: Optional[Union[Tuple[int, int], str, UIElement]] = None,
                        config: Optional[OperationConfig] = None) -> OperationResult:
        """输入文本.
        
        Args:
            text: 要输入的文本
            target: 输入目标位置（可选）
            config: 操作配置
            
        Returns:
            操作结果
        """
        pass

    @abstractmethod
    async def wait_for_condition(self, 
                               condition: WaitCondition,
                               condition_params: Dict[str, Any],
                               timeout: float = 30.0) -> OperationResult:
        """等待条件满足.
        
        Args:
            condition: 等待条件
            condition_params: 条件参数
            timeout: 超时时间
            
        Returns:
            操作结果
        """
        pass


class GameOperator(IGameOperator):
    """游戏操作器实现类."""

    def __init__(self, 
                 game_detector: Optional[GameDetector] = None,
                 sync_adapter: Optional[SyncAdapter] = None):
        """初始化游戏操作器.
        
        Args:
            game_detector: 游戏检测器实例
            sync_adapter: 同步适配器实例
        """
        self.logger = setup_logger()
        self.game_detector = game_detector or GameDetector()
        self.sync_adapter = sync_adapter or SyncAdapter()
        
        # 初始化错误处理器
        self.error_handler = ErrorHandler()
        
        # 操作配置
        self.default_config = OperationConfig()
        self._operation_history: List[OperationResult] = []
        
        # 检查依赖
        self._check_dependencies()
        
        self.logger.info("GameOperator初始化完成")

    def _check_dependencies(self) -> None:
        """检查依赖库."""
        missing_deps = []
        
        if win32api is None:
            missing_deps.append("pywin32")
        if pyautogui is None:
            missing_deps.append("pyautogui")
        if cv2 is None:
            missing_deps.append("opencv-python")
            
        if missing_deps:
            self.logger.warning(f"缺少依赖库: {', '.join(missing_deps)}")
            self.logger.warning("某些功能可能无法正常工作")

    async def click(self, 
                   target: Union[Tuple[int, int], str, UIElement], 
                   click_type: ClickType = ClickType.LEFT,
                   config: Optional[OperationConfig] = None) -> OperationResult:
        """点击操作实现."""
        start_time = time.time()
        config = config or self.default_config
        
        try:
            # 解析目标位置
            position = await self._resolve_target_position(target)
            if position is None:
                return OperationResult(
                    success=False,
                    execution_time=time.time() - start_time,
                    error_message=f"无法解析目标位置: {target}"
                )
            
            # 截图（如果需要）
            screenshot_before = None
            if config.screenshot_before:
                screenshot_before = await self._take_screenshot()
            
            # 执行点击操作（带重试机制）
            click_success, verification_success = await self._execute_click_with_retry(
                target, position, click_type, max_retries=config.retry_count
            )
            
            # 截图（如果需要）
            screenshot_after = None
            if config.screenshot_after:
                screenshot_after = await self._take_screenshot()
            
            # 最终成功状态
            success = click_success and (verification_success if config.verify_result else True)
            
            execution_time = time.time() - start_time
            result = OperationResult(
                success=success,
                execution_time=execution_time,
                screenshot_before=screenshot_before,
                screenshot_after=screenshot_after,
                metadata={
                    "target": str(target),
                    "position": position,
                    "click_type": click_type.value
                }
            )
            
            self._operation_history.append(result)
            
            if success:
                self.logger.info(f"点击操作成功: {position}")
            else:
                self.logger.warning(f"点击操作失败: {position}")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # 使用错误处理器处理错误
            error_info = await self.error_handler.handle_error(
                error=e,
                task_id=f"click_{int(time.time())}",
                task_type="game_operation",
                context={
                    "operation": "click",
                    "target": str(target),
                    "click_type": click_type.value,
                    "execution_time": execution_time
                }
            )
            
            # 尝试恢复
            recovery_success = await self.error_handler.try_recovery(error_info)
            
            error_msg = f"点击操作异常: {e}, 错误ID: {error_info.error_id}, 恢复成功: {recovery_success}"
            self.logger.error(error_msg)
            
            return OperationResult(
                success=False,
                execution_time=execution_time,
                error_message=error_msg,
                metadata={"error_id": error_info.error_id, "recovery_success": recovery_success}
            )

    async def swipe(self, 
                   start: Union[Tuple[int, int], str, UIElement],
                   end: Union[Tuple[int, int], str, UIElement],
                   duration: float = 1.0,
                   config: Optional[OperationConfig] = None) -> OperationResult:
        """滑动操作实现."""
        start_time = time.time()
        config = config or self.default_config
        
        try:
            # 解析起始和结束位置
            start_pos = await self._resolve_target_position(start)
            end_pos = await self._resolve_target_position(end)
            
            if start_pos is None or end_pos is None:
                return OperationResult(
                    success=False,
                    execution_time=time.time() - start_time,
                    error_message=f"无法解析滑动位置: {start} -> {end}"
                )
            
            # 截图（如果需要）
            screenshot_before = None
            if config.screenshot_before:
                screenshot_before = await self._take_screenshot()
            
            # 执行滑动操作（带重试机制）
            swipe_success, verification_success = await self._execute_swipe_with_retry(
                start_pos, end_pos, duration, max_retries=config.retry_count
            )
            
            # 截图（如果需要）
            screenshot_after = None
            if config.screenshot_after:
                screenshot_after = await self._take_screenshot()
            
            # 最终成功状态
            success = swipe_success and (verification_success if config.verify_result else True)
            
            execution_time = time.time() - start_time
            result = OperationResult(
                success=success,
                execution_time=execution_time,
                screenshot_before=screenshot_before,
                screenshot_after=screenshot_after,
                metadata={
                    "start": start_pos,
                    "end": end_pos,
                    "duration": duration
                }
            )
            
            self._operation_history.append(result)
            
            if success:
                self.logger.info(f"滑动操作成功: {start_pos} -> {end_pos}")
            else:
                self.logger.warning(f"滑动操作失败: {start_pos} -> {end_pos}")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # 使用错误处理器处理错误
            error_info = await self.error_handler.handle_error(
                error=e,
                task_id=f"swipe_{int(time.time())}",
                task_type="game_operation",
                context={
                    "operation": "swipe",
                    "start": str(start),
                    "end": str(end),
                    "duration": duration,
                    "execution_time": execution_time
                }
            )
            
            # 尝试恢复
            recovery_success = await self.error_handler.try_recovery(error_info)
            
            error_msg = f"滑动操作异常: {e}, 错误ID: {error_info.error_id}, 恢复成功: {recovery_success}"
            self.logger.error(error_msg)
            
            return OperationResult(
                success=False,
                execution_time=execution_time,
                error_message=error_msg,
                metadata={"error_id": error_info.error_id, "recovery_success": recovery_success}
            )

    async def input_text(self, 
                        text: str,
                        target: Optional[Union[Tuple[int, int], str, UIElement]] = None,
                        config: Optional[OperationConfig] = None) -> OperationResult:
        """输入文本实现."""
        start_time = time.time()
        config = config or self.default_config
        
        try:
            # 如果指定了目标位置，先点击
            if target is not None:
                click_result = await self.click(target, config=config)
                if not click_result.success:
                    return OperationResult(
                        success=False,
                        execution_time=time.time() - start_time,
                        error_message=f"点击输入目标失败: {click_result.error_message}"
                    )
                
                # 等待一下确保焦点切换
                await asyncio.sleep(0.5)
            
            # 截图（如果需要）
            screenshot_before = None
            if config.screenshot_before:
                screenshot_before = await self._take_screenshot()
            
            # 执行文本输入
            success = await self._perform_text_input(text, config)
            
            # 截图（如果需要）
            screenshot_after = None
            if config.screenshot_after:
                screenshot_after = await self._take_screenshot()
            
            execution_time = time.time() - start_time
            result = OperationResult(
                success=success,
                execution_time=execution_time,
                screenshot_before=screenshot_before,
                screenshot_after=screenshot_after,
                metadata={
                    "text": text,
                    "target": str(target) if target else None
                }
            )
            
            self._operation_history.append(result)
            
            if success:
                self.logger.info(f"文本输入成功: {text[:20]}...")
            else:
                self.logger.warning(f"文本输入失败: {text[:20]}...")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # 使用错误处理器处理错误
            error_info = await self.error_handler.handle_error(
                error=e,
                task_id=f"input_text_{int(time.time())}",
                task_type="game_operation",
                context={
                    "operation": "input_text",
                    "text": text[:50],  # 限制文本长度
                    "target": str(target) if target else None,
                    "execution_time": execution_time
                }
            )
            
            # 尝试恢复
            recovery_success = await self.error_handler.try_recovery(error_info)
            
            error_msg = f"文本输入异常: {e}, 错误ID: {error_info.error_id}, 恢复成功: {recovery_success}"
            self.logger.error(error_msg)
            
            return OperationResult(
                success=False,
                execution_time=execution_time,
                error_message=error_msg,
                metadata={"error_id": error_info.error_id, "recovery_success": recovery_success}
            )

    async def wait_for_condition(self, 
                               condition: WaitCondition,
                               condition_params: Dict[str, Any],
                               timeout: float = 30.0) -> OperationResult:
        """等待条件满足实现."""
        start_time = time.time()
        
        try:
            success = False
            
            if condition == WaitCondition.UI_ELEMENT_APPEAR:
                success = await self._wait_for_ui_element_appear(
                    condition_params.get("element_name"),
                    condition_params.get("template_path"),
                    timeout
                )
            elif condition == WaitCondition.UI_ELEMENT_DISAPPEAR:
                success = await self._wait_for_ui_element_disappear(
                    condition_params.get("element_name"),
                    condition_params.get("template_path"),
                    timeout
                )
            elif condition == WaitCondition.SCENE_CHANGE:
                success = await self._wait_for_scene_change(
                    condition_params.get("target_scene"),
                    timeout
                )
            elif condition == WaitCondition.CUSTOM:
                custom_func = condition_params.get("custom_function")
                if custom_func:
                    success = await self._wait_for_custom_condition(custom_func, timeout)
            
            execution_time = time.time() - start_time
            result = OperationResult(
                success=success,
                execution_time=execution_time,
                metadata={
                    "condition": condition.value,
                    "condition_params": condition_params,
                    "timeout": timeout
                }
            )
            
            self._operation_history.append(result)
            
            if success:
                self.logger.info(f"等待条件满足: {condition.value}")
            else:
                self.logger.warning(f"等待条件超时: {condition.value}")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # 使用错误处理器处理错误
            error_info = await self.error_handler.handle_error(
                error=e,
                task_id=f"wait_condition_{int(time.time())}",
                task_type="game_operation",
                context={
                    "operation": "wait_for_condition",
                    "condition": condition.value,
                    "condition_params": str(condition_params),
                    "timeout": timeout,
                    "execution_time": execution_time
                }
            )
            
            # 尝试恢复
            recovery_success = await self.error_handler.try_recovery(error_info)
            
            error_msg = f"等待条件异常: {e}, 错误ID: {error_info.error_id}, 恢复成功: {recovery_success}"
            self.logger.error(error_msg)
            
            return OperationResult(
                success=False,
                execution_time=execution_time,
                error_message=error_msg,
                metadata={"error_id": error_info.error_id, "recovery_success": recovery_success}
            )

    # 私有辅助方法
    async def _resolve_target_position(self, target: Union[Tuple[int, int], str, UIElement]) -> Optional[Tuple[int, int]]:
        """解析目标位置."""
        if isinstance(target, tuple) and len(target) == 2:
            return target
        elif isinstance(target, UIElement):
            return target.center
        elif isinstance(target, str):
            # 通过模板名称查找UI元素
            elements = self.game_detector.detect_ui_elements([target])
            if elements:
                return elements[0].center
            return None
        else:
            return None

    async def _perform_click(self, position: Tuple[int, int], click_type: ClickType, config: OperationConfig) -> bool:
        """执行点击操作."""
        try:
            x, y = position
            
            # 坐标验证和调整
            if not self._validate_coordinates(x, y):
                self.logger.error(f"无效坐标: ({x}, {y})")
                return False
            
            # 调整坐标到屏幕范围内
            x, y = self._adjust_coordinates_to_screen(x, y)
            
            # 操作前验证
            if not await self._pre_operation_validation(position):
                self.logger.warning(f"操作前验证失败: ({x}, {y})")
                return False
            
            # 移动鼠标到目标位置（平滑移动）
            await self._smooth_move_to_position(x, y)
            
            # 执行点击操作
            success = False
            if config.method == OperationMethod.WIN32_API and win32api:
                success = await self._perform_win32_click(x, y, click_type)
            elif pyautogui:
                success = await self._perform_pyautogui_click(x, y, click_type)
            else:
                self.logger.error("没有可用的点击方法")
                return False
            
            # 操作后延迟
            await self._post_operation_delay(click_type)
            
            return success
            
        except Exception as e:
            self.logger.error(f"执行点击失败: {e}")
            return False
    
    def _validate_coordinates(self, x: int, y: int) -> bool:
        """验证坐标有效性."""
        try:
            # 检查坐标类型
            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                return False
            
            # 检查坐标范围（允许负值，但会在后续调整）
            if abs(x) > 10000 or abs(y) > 10000:
                return False
            
            return True
        except Exception:
            return False
    
    def _adjust_coordinates_to_screen(self, x: int, y: int) -> Tuple[int, int]:
        """调整坐标到屏幕范围内."""
        try:
            if pyautogui:
                screen_width, screen_height = pyautogui.size()
            else:
                # 默认屏幕尺寸
                screen_width, screen_height = 1920, 1080
            
            # 确保坐标在屏幕范围内
            x = max(0, min(x, screen_width - 1))
            y = max(0, min(y, screen_height - 1))
            
            return int(x), int(y)
        except Exception as e:
            self.logger.warning(f"坐标调整失败: {e}")
            return int(x), int(y)
    
    async def _pre_operation_validation(self, position: Tuple[int, int]) -> bool:
        """操作前验证."""
        try:
            # 检查游戏窗口是否存在且可操作
            if hasattr(self.game_detector, 'window_manager'):
                if not self.game_detector.window_manager.is_game_window_active():
                    self.logger.warning("游戏窗口不活跃")
                    return False
            
            # 检查坐标是否在游戏窗口内
            if hasattr(self.game_detector, 'window_manager'):
                window_rect = self.game_detector.window_manager.get_game_window_rect()
                if window_rect:
                    x, y = position
                    if not (window_rect[0] <= x <= window_rect[2] and window_rect[1] <= y <= window_rect[3]):
                        self.logger.warning(f"坐标超出游戏窗口范围: ({x}, {y})")
                        # 不返回False，允许在窗口外点击
            
            return True
        except Exception as e:
            self.logger.warning(f"操作前验证异常: {e}")
            return True  # 验证失败时允许继续操作
    
    async def _smooth_move_to_position(self, x: int, y: int) -> None:
        """平滑移动鼠标到目标位置."""
        try:
            if pyautogui:
                # 获取当前鼠标位置
                current_x, current_y = pyautogui.position()
                
                # 计算移动距离
                distance = ((x - current_x) ** 2 + (y - current_y) ** 2) ** 0.5
                
                # 如果距离较远，使用平滑移动
                if distance > 50:
                    duration = min(0.3, distance / 1000)  # 根据距离调整移动时间
                    pyautogui.moveTo(x, y, duration=duration)
                else:
                    pyautogui.moveTo(x, y)
            elif win32api:
                win32api.SetCursorPos((x, y))
            
            # 短暂延迟确保鼠标到位
            await asyncio.sleep(0.05)
        except Exception as e:
            self.logger.warning(f"鼠标移动失败: {e}")
    
    async def _perform_win32_click(self, x: int, y: int, click_type: ClickType) -> bool:
        """使用Win32 API执行点击."""
        try:
            if click_type == ClickType.LEFT:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
                await asyncio.sleep(0.05)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
            elif click_type == ClickType.RIGHT:
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, x, y, 0, 0)
                await asyncio.sleep(0.05)
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, x, y, 0, 0)
            elif click_type == ClickType.MIDDLE:
                win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN, x, y, 0, 0)
                await asyncio.sleep(0.05)
                win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP, x, y, 0, 0)
            elif click_type == ClickType.DOUBLE:
                # 双击
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
                await asyncio.sleep(0.05)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
            
            return True
        except Exception as e:
            self.logger.error(f"Win32点击失败: {e}")
            return False
    
    async def _perform_pyautogui_click(self, x: int, y: int, click_type: ClickType) -> bool:
        """使用PyAutoGUI执行点击."""
        try:
            if click_type == ClickType.LEFT:
                pyautogui.click(x, y, button='left')
            elif click_type == ClickType.RIGHT:
                pyautogui.click(x, y, button='right')
            elif click_type == ClickType.MIDDLE:
                pyautogui.click(x, y, button='middle')
            elif click_type == ClickType.DOUBLE:
                pyautogui.doubleClick(x, y)
            
            return True
        except Exception as e:
            self.logger.error(f"PyAutoGUI点击失败: {e}")
            return False
    
    async def _post_operation_delay(self, click_type: ClickType) -> None:
        """操作后延迟."""
        try:
            # 根据操作类型设置不同的延迟
            if click_type == ClickType.DOUBLE:
                await asyncio.sleep(0.2)  # 双击后稍长延迟
            else:
                await asyncio.sleep(0.1)  # 普通点击延迟
        except Exception:
            pass

    async def _perform_swipe(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], duration: float, config: OperationConfig) -> bool:
        """执行滑动操作."""
        try:
            if pyautogui:
                pyautogui.drag(start_pos[0], start_pos[1], end_pos[0], end_pos[1], duration=duration)
                return True
            elif win32api:
                # 使用Win32 API模拟拖拽
                x1, y1 = start_pos
                x2, y2 = end_pos
                
                # 移动到起始位置
                win32api.SetCursorPos((x1, y1))
                await asyncio.sleep(0.1)
                
                # 按下鼠标
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x1, y1, 0, 0)
                await asyncio.sleep(0.1)
                
                # 分步移动到结束位置
                steps = max(10, int(duration * 30))  # 30fps
                for i in range(steps):
                    progress = (i + 1) / steps
                    current_x = int(x1 + (x2 - x1) * progress)
                    current_y = int(y1 + (y2 - y1) * progress)
                    win32api.SetCursorPos((current_x, current_y))
                    await asyncio.sleep(duration / steps)
                
                # 释放鼠标
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x2, y2, 0, 0)
                return True
            else:
                self.logger.error("没有可用的滑动方法")
                return False
                
        except Exception as e:
            self.logger.error(f"执行滑动失败: {e}")
            return False

    async def _perform_text_input(self, text: str, config: OperationConfig) -> bool:
        """执行文本输入."""
        try:
            if pyautogui:
                pyautogui.typewrite(text, interval=0.05)
                return True
            else:
                self.logger.error("没有可用的文本输入方法")
                return False
                
        except Exception as e:
            self.logger.error(f"执行文本输入失败: {e}")
            return False

    async def _take_screenshot(self) -> Optional[bytes]:
        """截取屏幕截图."""
        try:
            return self.game_detector.capture_screen()
        except Exception as e:
            self.logger.error(f"截图失败: {e}")
            return None

    async def _verify_click_result(self, target: Union[Tuple[int, int], str, UIElement], position: Tuple[int, int]) -> bool:
        """验证点击结果."""
        try:
            # 等待UI响应
            await asyncio.sleep(0.3)
            
            # 如果目标是字符串（UI元素名称），检查元素状态变化
            if isinstance(target, str):
                return await self._verify_ui_element_click(target)
            
            # 如果目标是UIElement对象，检查元素状态
            elif hasattr(target, '__class__') and hasattr(target, 'name'):
                return await self._verify_ui_element_click(target.name)
            
            # 如果是坐标点击，进行通用验证
            else:
                return await self._verify_coordinate_click(position)
                
        except Exception as e:
            self.logger.error(f"点击结果验证失败: {e}")
            return False
    
    async def _verify_ui_element_click(self, element_name: str) -> bool:
        """验证UI元素点击结果."""
        try:
            # 检查元素是否仍然存在（某些按钮点击后会消失）
            elements_after = self.game_detector.detect_ui_elements([element_name])
            
            # 检查场景是否发生变化（点击可能导致场景切换）
            current_scene = self.game_detector.detect_scene()
            
            # 如果是按钮类元素，点击后可能消失或场景改变
            if 'button' in element_name.lower() or 'btn' in element_name.lower():
                # 按钮点击通常会导致场景变化或元素消失
                return len(elements_after) == 0 or current_scene is not None
            
            # 对于其他元素，检查是否有状态变化
            return True
            
        except Exception as e:
            self.logger.warning(f"UI元素点击验证失败: {e}")
            return True  # 验证失败时假设成功
    
    async def _verify_coordinate_click(self, position: Tuple[int, int]) -> bool:
        """验证坐标点击结果."""
        try:
            # 检查鼠标位置是否正确
            if pyautogui:
                current_pos = pyautogui.position()
                distance = ((current_pos[0] - position[0]) ** 2 + (current_pos[1] - position[1]) ** 2) ** 0.5
                
                # 如果鼠标位置偏差太大，认为点击失败
                if distance > 10:
                    self.logger.warning(f"鼠标位置偏差过大: {distance}")
                    return False
            
            # 检查屏幕是否有变化（简单的像素对比）
            return await self._detect_screen_change()
            
        except Exception as e:
            self.logger.warning(f"坐标点击验证失败: {e}")
            return True  # 验证失败时假设成功
    
    async def _detect_screen_change(self) -> bool:
        """检测屏幕变化."""
        try:
            # 等待一段时间让变化发生
            await asyncio.sleep(0.2)
            
            # 简单的屏幕变化检测
            # 这里可以通过截图对比来实现更精确的检测
            return True  # 暂时假设总是有变化
            
        except Exception as e:
            self.logger.warning(f"屏幕变化检测失败: {e}")
            return True
    
    async def _execute_click_with_retry(self, target: Union[Tuple[int, int], str, UIElement], 
                                      position: Tuple[int, int], click_type: ClickType, 
                                      max_retries: int = 2) -> Tuple[bool, bool]:
        """执行点击操作，带重试机制."""
        click_success = False
        verification_success = False
        
        for attempt in range(max_retries + 1):
            try:
                self.logger.debug(f"点击尝试 {attempt + 1}/{max_retries + 1}")
                
                # 执行点击
                click_success = await self._perform_click(position, click_type, self.default_config)
                if not click_success:
                    self.logger.warning(f"点击执行失败，尝试 {attempt + 1}")
                    if attempt < max_retries:
                        await asyncio.sleep(0.5)  # 重试前等待
                        continue
                    break
                
                # 验证点击结果
                verification_success = await self._verify_click_result(target, position)
                if verification_success:
                    self.logger.debug(f"点击成功，尝试 {attempt + 1}")
                    break
                else:
                    self.logger.warning(f"点击验证失败，尝试 {attempt + 1}")
                    if attempt < max_retries:
                        await asyncio.sleep(0.5)  # 重试前等待
                        continue
                
            except Exception as e:
                self.logger.error(f"点击执行异常，尝试 {attempt + 1}: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(0.5)
                    continue
                break
        
        return click_success, verification_success
    
    async def _execute_swipe_with_retry(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int], 
                                      duration: float, max_retries: int = 2) -> Tuple[bool, bool]:
        """执行滑动操作，带重试机制."""
        swipe_success = False
        verification_success = False
        
        for attempt in range(max_retries + 1):
            try:
                self.logger.debug(f"滑动尝试 {attempt + 1}/{max_retries + 1}")
                
                # 执行滑动
                swipe_success = await self._perform_swipe(start_pos, end_pos, duration, self.default_config)
                if not swipe_success:
                    self.logger.warning(f"滑动执行失败，尝试 {attempt + 1}")
                    if attempt < max_retries:
                        await asyncio.sleep(0.5)  # 重试前等待
                        continue
                    break
                
                # 验证滑动结果
                verification_success = await self._verify_swipe_result(start_pos, end_pos)
                if verification_success:
                    self.logger.debug(f"滑动成功，尝试 {attempt + 1}")
                    break
                else:
                    self.logger.warning(f"滑动验证失败，尝试 {attempt + 1}")
                    if attempt < max_retries:
                        await asyncio.sleep(0.5)  # 重试前等待
                        continue
                
            except Exception as e:
                self.logger.error(f"滑动执行异常，尝试 {attempt + 1}: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(0.5)
                    continue
                break
        
        return swipe_success, verification_success
    
    async def _verify_swipe_result(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int]) -> bool:
        """验证滑动结果."""
        try:
            # 等待UI响应
            await asyncio.sleep(0.3)
            
            # 检查屏幕是否有变化（滑动通常会导致内容滚动）
            screen_changed = await self._detect_screen_change()
            
            # 检查鼠标位置是否在预期的结束位置附近
            if pyautogui:
                current_pos = pyautogui.position()
                distance = ((current_pos[0] - end_pos[0]) ** 2 + (current_pos[1] - end_pos[1]) ** 2) ** 0.5
                
                # 如果鼠标位置偏差太大，认为滑动失败
                if distance > 20:  # 滑动的容差比点击大一些
                    self.logger.warning(f"滑动结束位置偏差过大: {distance}")
                    return False
            
            return screen_changed
            
        except Exception as e:
            self.logger.warning(f"滑动结果验证失败: {e}")
            return True  # 验证失败时假设成功
    
    async def _capture_operation_state(self) -> dict:
        """捕获操作前后的状态信息."""
        try:
            state = {
                'timestamp': time.time(),
                'scene': None,
                'ui_elements': [],
                'screenshot_hash': None
            }
            
            # 检测当前场景
            try:
                state['scene'] = self.game_detector.detect_scene()
            except Exception as e:
                self.logger.warning(f"场景检测失败: {e}")
            
            # 检测UI元素（仅检测常见元素）
            try:
                common_elements = ['button', 'menu', 'dialog', 'popup']
                state['ui_elements'] = self.game_detector.detect_ui_elements(common_elements)
            except Exception as e:
                self.logger.warning(f"UI元素检测失败: {e}")
            
            return state
            
        except Exception as e:
            self.logger.error(f"状态捕获失败: {e}")
            return {}
    
    async def _compare_operation_states(self, before_state: dict, after_state: dict) -> bool:
        """比较操作前后的状态变化."""
        try:
            # 检查场景变化
            scene_changed = before_state.get('scene') != after_state.get('scene')
            
            # 检查UI元素变化
            before_elements = set(before_state.get('ui_elements', []))
            after_elements = set(after_state.get('ui_elements', []))
            elements_changed = before_elements != after_elements
            
            # 如果有任何变化，认为操作生效
            state_changed = scene_changed or elements_changed
            
            if state_changed:
                self.logger.debug(f"检测到状态变化 - 场景: {scene_changed}, UI元素: {elements_changed}")
            
            return state_changed
            
        except Exception as e:
            self.logger.warning(f"状态比较失败: {e}")
            return True  # 比较失败时假设有变化

    async def _wait_for_ui_element_appear(self, element_name: Optional[str], template_path: Optional[str], timeout: float) -> bool:
        """等待UI元素出现."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if element_name:
                elements = self.game_detector.detect_ui_elements([element_name])
                if elements:
                    return True
            
            if template_path:
                # 使用模板匹配
                # 这里需要实现模板匹配逻辑
                pass
            
            await asyncio.sleep(0.5)
        
        return False

    async def _wait_for_ui_element_disappear(self, element_name: Optional[str], template_path: Optional[str], timeout: float) -> bool:
        """等待UI元素消失."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if element_name:
                elements = self.game_detector.detect_ui_elements([element_name])
                if not elements:
                    return True
            
            if template_path:
                # 使用模板匹配
                # 这里需要实现模板匹配逻辑
                pass
            
            await asyncio.sleep(0.5)
        
        return False

    async def _wait_for_scene_change(self, target_scene: Optional[str], timeout: float) -> bool:
        """等待场景切换."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            current_scene = self.game_detector.detect_scene()
            if target_scene is None or current_scene.value == target_scene:
                return True
            
            await asyncio.sleep(0.5)
        
        return False

    async def _wait_for_custom_condition(self, custom_func, timeout: float) -> bool:
        """等待自定义条件."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if await custom_func():
                    return True
            except Exception as e:
                self.logger.error(f"自定义条件检查失败: {e}")
                return False
            
            await asyncio.sleep(0.5)
        
        return False

    # 公共方法
    def get_operation_history(self) -> List[OperationResult]:
        """获取操作历史."""
        return self._operation_history.copy()

    def clear_operation_history(self) -> None:
        """清空操作历史."""
        self._operation_history.clear()

    def set_default_config(self, config: OperationConfig) -> None:
        """设置默认配置."""
        self.default_config = config

    def get_default_config(self) -> OperationConfig:
        """获取默认配置."""
        return self.default_config