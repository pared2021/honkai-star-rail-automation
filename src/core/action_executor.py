#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
操作执行器模块
负责执行具体的游戏自动化操作，包括点击、键盘、等待和循环控制
"""

import time
import random
import asyncio
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from dataclasses import dataclass
import pyautogui
import win32api
import win32con
import win32gui
from loguru import logger

from .enums import ActionType, ClickType, WaitType, LoopType


@dataclass
class ActionResult:
    """操作结果"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0
    error: Optional[Exception] = None


@dataclass
class ClickAction:
    """点击操作配置"""
    x: int
    y: int
    click_type: Union[ClickType, str] = ClickType.SINGLE
    button: str = "left"  # left, right, middle
    delay_before: float = 0.1
    delay_after: float = 0.1
    count: int = 1  # 连续点击次数
    interval: float = 0.1  # 连续点击间隔
    area_radius: int = 5  # 区域点击半径
    randomize: bool = True  # 是否随机化位置
    
    def __post_init__(self):
        if isinstance(self.click_type, str):
            self.click_type = ClickType(self.click_type)


@dataclass
class KeyAction:
    """键盘操作配置"""
    keys: Union[str, List[str]]
    action_type: str = "press"  # press, down, up, combination
    delay_before: float = 0.1
    delay_after: float = 0.1
    hold_duration: float = 0.05
    interval: float = 0.05  # 按键间隔


@dataclass
class WaitAction:
    """等待操作配置"""
    wait_type: Union[WaitType, str]
    duration: float = 1.0
    min_duration: float = 0.5
    max_duration: float = 2.0
    condition_func: Optional[Callable[[], bool]] = None
    timeout: float = 30.0
    check_interval: float = 0.1
    
    def __post_init__(self):
        if isinstance(self.wait_type, str):
            self.wait_type = WaitType(self.wait_type)


@dataclass
class LoopAction:
    """循环操作配置"""
    loop_type: Union[LoopType, str]
    count: int = 1
    condition_func: Optional[Callable[[], bool]] = None
    actions: List[Dict[str, Any]] = None
    max_iterations: int = 1000
    break_on_error: bool = True
    delay_between_iterations: float = 0.1
    
    def __post_init__(self):
        if isinstance(self.loop_type, str):
            self.loop_type = LoopType(self.loop_type)
        if self.actions is None:
            self.actions = []


class ActionExecutor:
    """操作执行器
    
    负责执行各种自动化操作，包括：
    1. 点击操作（精确点击、区域点击、连续点击）
    2. 键盘操作（按键序列、组合键、文本输入）
    3. 等待机制（固定等待、条件等待、超时处理）
    4. 循环控制（次数循环、条件循环、异常处理）
    """
    
    def __init__(self, config_manager=None):
        """初始化操作执行器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.is_running = False
        self.current_action = None
        self.execution_stats = {
            "total_actions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "total_execution_time": 0.0
        }
        
        # 初始化pyautogui设置
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.01
        
        logger.info("ActionExecutor initialized")
    
    def get_random_offset(self, radius: int = 5) -> Tuple[int, int]:
        """获取随机偏移量
        
        Args:
            radius: 随机偏移半径
            
        Returns:
            (x_offset, y_offset): 随机偏移量
        """
        angle = random.uniform(0, 2 * 3.14159)
        distance = random.uniform(0, radius)
        x_offset = int(distance * random.uniform(-1, 1))
        y_offset = int(distance * random.uniform(-1, 1))
        return x_offset, y_offset
    
    def add_random_delay(self, base_delay: float, variance: float = 0.1) -> float:
        """添加随机延迟
        
        Args:
            base_delay: 基础延迟时间
            variance: 延迟变化范围（比例）
            
        Returns:
            实际延迟时间
        """
        min_delay = base_delay * (1 - variance)
        max_delay = base_delay * (1 + variance)
        actual_delay = random.uniform(min_delay, max_delay)
        return actual_delay
    
    async def execute_click(self, action: ClickAction) -> ActionResult:
        """执行点击操作
        
        Args:
            action: 点击操作配置
            
        Returns:
            操作结果
        """
        start_time = time.time()
        
        try:
            # 前置延迟
            if action.delay_before > 0:
                actual_delay = self.add_random_delay(action.delay_before)
                await asyncio.sleep(actual_delay)
            
            # 计算实际点击位置
            x, y = action.x, action.y
            if action.randomize:
                offset_x, offset_y = self.get_random_offset(action.area_radius)
                x += offset_x
                y += offset_y
            
            logger.debug(f"Executing click at ({x}, {y}), type: {action.click_type.value}")
            
            # 执行点击操作
            if action.click_type == ClickType.SINGLE:
                pyautogui.click(x, y, button=action.button)
            
            elif action.click_type == ClickType.DOUBLE:
                pyautogui.doubleClick(x, y, button=action.button)
            
            elif action.click_type == ClickType.RIGHT:
                pyautogui.rightClick(x, y)
            
            elif action.click_type == ClickType.AREA:
                # 区域点击：在指定区域内随机点击
                for _ in range(action.count):
                    offset_x, offset_y = self.get_random_offset(action.area_radius)
                    click_x = x + offset_x
                    click_y = y + offset_y
                    pyautogui.click(click_x, click_y, button=action.button)
                    if action.count > 1:
                        await asyncio.sleep(action.interval)
            
            elif action.click_type == ClickType.CONTINUOUS:
                # 连续点击
                for i in range(action.count):
                    if action.randomize:
                        offset_x, offset_y = self.get_random_offset(action.area_radius)
                        click_x = x + offset_x
                        click_y = y + offset_y
                    else:
                        click_x, click_y = x, y
                    
                    pyautogui.click(click_x, click_y, button=action.button)
                    
                    if i < action.count - 1:  # 不是最后一次点击
                        interval = self.add_random_delay(action.interval)
                        await asyncio.sleep(interval)
            
            # 后置延迟
            if action.delay_after > 0:
                actual_delay = self.add_random_delay(action.delay_after)
                await asyncio.sleep(actual_delay)
            
            execution_time = time.time() - start_time
            
            return ActionResult(
                success=True,
                message=f"Click executed successfully at ({x}, {y})",
                data={"position": (x, y), "type": action.click_type.value},
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Click execution failed: {str(e)}")
            
            return ActionResult(
                success=False,
                message=f"Click execution failed: {str(e)}",
                error=e,
                execution_time=execution_time
            )
    
    async def execute_key_action(self, action: KeyAction) -> ActionResult:
        """执行键盘操作
        
        Args:
            action: 键盘操作配置
            
        Returns:
            操作结果
        """
        start_time = time.time()
        
        try:
            # 前置延迟
            if action.delay_before > 0:
                actual_delay = self.add_random_delay(action.delay_before)
                await asyncio.sleep(actual_delay)
            
            logger.debug(f"Executing key action: {action.keys}, type: {action.action_type}")
            
            if action.action_type == "press":
                if isinstance(action.keys, str):
                    pyautogui.press(action.keys)
                else:
                    for key in action.keys:
                        pyautogui.press(key)
                        if len(action.keys) > 1:
                            await asyncio.sleep(action.interval)
            
            elif action.action_type == "combination":
                if isinstance(action.keys, list):
                    pyautogui.hotkey(*action.keys)
                else:
                    pyautogui.press(action.keys)
            
            elif action.action_type == "down":
                if isinstance(action.keys, str):
                    pyautogui.keyDown(action.keys)
                else:
                    for key in action.keys:
                        pyautogui.keyDown(key)
                        if len(action.keys) > 1:
                            await asyncio.sleep(action.interval)
            
            elif action.action_type == "up":
                if isinstance(action.keys, str):
                    pyautogui.keyUp(action.keys)
                else:
                    for key in action.keys:
                        pyautogui.keyUp(key)
                        if len(action.keys) > 1:
                            await asyncio.sleep(action.interval)
            
            elif action.action_type == "hold":
                if isinstance(action.keys, str):
                    pyautogui.keyDown(action.keys)
                    await asyncio.sleep(action.hold_duration)
                    pyautogui.keyUp(action.keys)
                else:
                    for key in action.keys:
                        pyautogui.keyDown(key)
                    await asyncio.sleep(action.hold_duration)
                    for key in reversed(action.keys):
                        pyautogui.keyUp(key)
            
            # 后置延迟
            if action.delay_after > 0:
                actual_delay = self.add_random_delay(action.delay_after)
                await asyncio.sleep(actual_delay)
            
            execution_time = time.time() - start_time
            
            return ActionResult(
                success=True,
                message=f"Key action executed successfully: {action.keys}",
                data={"keys": action.keys, "type": action.action_type},
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Key action execution failed: {str(e)}")
            
            return ActionResult(
                success=False,
                message=f"Key action execution failed: {str(e)}",
                error=e,
                execution_time=execution_time
            )
    
    async def execute_text_input(self, text: str, interval: float = 0.01) -> ActionResult:
        """执行文本输入
        
        Args:
            text: 要输入的文本
            interval: 字符间隔时间
            
        Returns:
            操作结果
        """
        start_time = time.time()
        
        try:
            logger.debug(f"Typing text: {text[:50]}{'...' if len(text) > 50 else ''}")
            
            # 使用pyautogui的typewrite方法，支持中文
            pyautogui.typewrite(text, interval=interval)
            
            execution_time = time.time() - start_time
            
            return ActionResult(
                success=True,
                message=f"Text input completed: {len(text)} characters",
                data={"text_length": len(text), "interval": interval},
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Text input failed: {str(e)}")
            
            return ActionResult(
                success=False,
                message=f"Text input failed: {str(e)}",
                error=e,
                execution_time=execution_time
            )
    
    async def execute_wait(self, action: WaitAction) -> ActionResult:
        """执行等待操作
        
        Args:
            action: 等待操作配置
            
        Returns:
            操作结果
        """
        start_time = time.time()
        
        try:
            logger.debug(f"Executing wait: {action.wait_type.value}")
            
            if action.wait_type == WaitType.FIXED:
                await asyncio.sleep(action.duration)
                
            elif action.wait_type == WaitType.RANDOM:
                duration = random.uniform(action.min_duration, action.max_duration)
                await asyncio.sleep(duration)
                
            elif action.wait_type == WaitType.CONDITION:
                if action.condition_func is None:
                    raise ValueError("Condition function is required for condition wait")
                
                elapsed = 0.0
                while elapsed < action.timeout:
                    if action.condition_func():
                        break
                    
                    await asyncio.sleep(action.check_interval)
                    elapsed += action.check_interval
                
                if elapsed >= action.timeout:
                    raise TimeoutError(f"Condition wait timeout after {action.timeout} seconds")
            
            execution_time = time.time() - start_time
            
            return ActionResult(
                success=True,
                message=f"Wait completed: {action.wait_type.value}",
                data={"wait_type": action.wait_type.value, "actual_duration": execution_time},
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Wait execution failed: {str(e)}")
            
            return ActionResult(
                success=False,
                message=f"Wait execution failed: {str(e)}",
                error=e,
                execution_time=execution_time
            )
    
    async def execute_loop(self, action: LoopAction) -> ActionResult:
        """执行循环操作
        
        Args:
            action: 循环操作配置
            
        Returns:
            操作结果
        """
        start_time = time.time()
        
        try:
            logger.debug(f"Executing loop: {action.loop_type.value}")
            
            iteration_count = 0
            successful_iterations = 0
            failed_iterations = 0
            
            while True:
                # 检查循环条件
                if action.loop_type == LoopType.COUNT:
                    if iteration_count >= action.count:
                        break
                elif action.loop_type == LoopType.CONDITION:
                    if action.condition_func is None:
                        raise ValueError("Condition function is required for condition loop")
                    if not action.condition_func():
                        break
                elif action.loop_type == LoopType.INFINITE:
                    # 无限循环，需要外部条件终止
                    pass
                
                # 检查最大迭代次数
                if iteration_count >= action.max_iterations:
                    logger.warning(f"Loop reached maximum iterations: {action.max_iterations}")
                    break
                
                iteration_start = time.time()
                iteration_success = True
                
                try:
                    # 执行循环体中的操作
                    if action.actions:
                        for sub_action in action.actions:
                            result = await self.execute_action(sub_action)
                            if not result.success and action.break_on_error:
                                iteration_success = False
                                break
                    
                    if iteration_success:
                        successful_iterations += 1
                    else:
                        failed_iterations += 1
                        if action.break_on_error:
                            break
                    
                except Exception as e:
                    failed_iterations += 1
                    logger.error(f"Loop iteration {iteration_count} failed: {str(e)}")
                    
                    if action.break_on_error:
                        break
                
                iteration_count += 1
                
                # 迭代间延迟
                if action.delay_between_iterations > 0:
                    delay = self.add_random_delay(action.delay_between_iterations)
                    await asyncio.sleep(delay)
            
            execution_time = time.time() - start_time
            
            return ActionResult(
                success=True,
                message=f"Loop completed: {iteration_count} iterations",
                data={
                    "loop_type": action.loop_type.value,
                    "total_iterations": iteration_count,
                    "successful_iterations": successful_iterations,
                    "failed_iterations": failed_iterations
                },
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Loop execution failed: {str(e)}")
            
            return ActionResult(
                success=False,
                message=f"Loop execution failed: {str(e)}",
                error=e,
                execution_time=execution_time
            )
    
    async def execute_scroll(self, x: int, y: int, clicks: int = 3, direction: str = "up") -> ActionResult:
        """执行滚动操作
        
        Args:
            x: 滚动位置x坐标
            y: 滚动位置y坐标
            clicks: 滚动次数
            direction: 滚动方向 (up/down)
            
        Returns:
            操作结果
        """
        start_time = time.time()
        
        try:
            logger.debug(f"Executing scroll at ({x}, {y}), direction: {direction}, clicks: {clicks}")
            
            pyautogui.scroll(clicks if direction == "up" else -clicks, x=x, y=y)
            
            execution_time = time.time() - start_time
            
            return ActionResult(
                success=True,
                message=f"Scroll executed at ({x}, {y})",
                data={"position": (x, y), "direction": direction, "clicks": clicks},
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Scroll execution failed: {str(e)}")
            
            return ActionResult(
                success=False,
                message=f"Scroll execution failed: {str(e)}",
                error=e,
                execution_time=execution_time
            )
    
    async def execute_drag(self, start_x: int, start_y: int, end_x: int, end_y: int, 
                          duration: float = 1.0, button: str = "left") -> ActionResult:
        """执行拖拽操作
        
        Args:
            start_x: 起始x坐标
            start_y: 起始y坐标
            end_x: 结束x坐标
            end_y: 结束y坐标
            duration: 拖拽持续时间
            button: 鼠标按钮
            
        Returns:
            操作结果
        """
        start_time = time.time()
        
        try:
            logger.debug(f"Executing drag from ({start_x}, {start_y}) to ({end_x}, {end_y})")
            
            pyautogui.drag(end_x - start_x, end_y - start_y, duration=duration, 
                          button=button, mouseDownUp=False)
            
            execution_time = time.time() - start_time
            
            return ActionResult(
                success=True,
                message=f"Drag executed from ({start_x}, {start_y}) to ({end_x}, {end_y})",
                data={
                    "start_position": (start_x, start_y),
                    "end_position": (end_x, end_y),
                    "duration": duration
                },
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Drag execution failed: {str(e)}")
            
            return ActionResult(
                success=False,
                message=f"Drag execution failed: {str(e)}",
                error=e,
                execution_time=execution_time
            )
    
    async def execute_action(self, action_config: Dict[str, Any]) -> ActionResult:
        """执行通用操作
        
        Args:
            action_config: 操作配置字典
            
        Returns:
            操作结果
        """
        try:
            action_type = ActionType(action_config.get("type"))
            self.current_action = action_config
            
            # 更新统计信息
            self.execution_stats["total_actions"] += 1
            
            if action_type == ActionType.CLICK:
                click_action = ClickAction(**action_config.get("params", {}))
                result = await self.execute_click(click_action)
                
            elif action_type == ActionType.KEY_PRESS:
                key_action = KeyAction(**action_config.get("params", {}))
                result = await self.execute_key_action(key_action)
                
            elif action_type == ActionType.TEXT_INPUT:
                params = action_config.get("params", {})
                result = await self.execute_text_input(
                    params.get("text", ""),
                    params.get("interval", 0.01)
                )
                
            elif action_type == ActionType.WAIT:
                wait_action = WaitAction(**action_config.get("params", {}))
                result = await self.execute_wait(wait_action)
                
            elif action_type == ActionType.LOOP:
                loop_action = LoopAction(**action_config.get("params", {}))
                result = await self.execute_loop(loop_action)
                
            elif action_type == ActionType.SCROLL:
                params = action_config.get("params", {})
                result = await self.execute_scroll(
                    params.get("x", 0),
                    params.get("y", 0),
                    params.get("clicks", 3),
                    params.get("direction", "up")
                )
                
            elif action_type == ActionType.DRAG:
                params = action_config.get("params", {})
                result = await self.execute_drag(
                    params.get("start_x", 0),
                    params.get("start_y", 0),
                    params.get("end_x", 0),
                    params.get("end_y", 0),
                    params.get("duration", 1.0),
                    params.get("button", "left")
                )
                
            else:
                result = ActionResult(
                    success=False,
                    message=f"Unsupported action type: {action_type}"
                )
            
            # 更新统计信息
            if result.success:
                self.execution_stats["successful_actions"] += 1
            else:
                self.execution_stats["failed_actions"] += 1
            
            self.execution_stats["total_execution_time"] += result.execution_time
            
            return result
            
        except Exception as e:
            logger.error(f"Action execution failed: {str(e)}")
            self.execution_stats["failed_actions"] += 1
            
            return ActionResult(
                success=False,
                message=f"Action execution failed: {str(e)}",
                error=e
            )
        finally:
            self.current_action = None
    
    async def execute_action_sequence(self, actions: List[Dict[str, Any]], 
                                    stop_on_error: bool = True) -> List[ActionResult]:
        """执行操作序列
        
        Args:
            actions: 操作序列
            stop_on_error: 遇到错误时是否停止
            
        Returns:
            操作结果列表
        """
        results = []
        
        logger.info(f"Executing action sequence with {len(actions)} actions")
        
        for i, action in enumerate(actions):
            logger.debug(f"Executing action {i+1}/{len(actions)}: {action.get('type')}")
            
            result = await self.execute_action(action)
            results.append(result)
            
            if not result.success and stop_on_error:
                logger.error(f"Action sequence stopped at action {i+1} due to error")
                break
        
        successful_count = sum(1 for r in results if r.success)
        logger.info(f"Action sequence completed: {successful_count}/{len(results)} successful")
        
        return results
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """获取执行统计信息
        
        Returns:
            统计信息字典
        """
        stats = self.execution_stats.copy()
        
        if stats["total_actions"] > 0:
            stats["success_rate"] = stats["successful_actions"] / stats["total_actions"]
            stats["average_execution_time"] = stats["total_execution_time"] / stats["total_actions"]
        else:
            stats["success_rate"] = 0.0
            stats["average_execution_time"] = 0.0
        
        return stats
    
    def reset_stats(self):
        """重置统计信息"""
        self.execution_stats = {
            "total_actions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "total_execution_time": 0.0
        }
        logger.info("Execution stats reset")
    
    def stop_execution(self):
        """停止当前执行"""
        self.is_running = False
        logger.info("Action execution stopped")
    
    def is_action_safe(self, action_config: Dict[str, Any]) -> bool:
        """检查操作是否安全
        
        Args:
            action_config: 操作配置
            
        Returns:
            是否安全
        """
        # 基础安全检查
        action_type = action_config.get("type")
        
        if action_type == "click":
            params = action_config.get("params", {})
            x, y = params.get("x", 0), params.get("y", 0)
            
            # 检查点击位置是否在屏幕范围内
            screen_width, screen_height = pyautogui.size()
            if not (0 <= x <= screen_width and 0 <= y <= screen_height):
                return False
        
        return True