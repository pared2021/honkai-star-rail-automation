"""自动化应用服务

实现游戏自动化操作的核心业务逻辑，包括窗口检测、截图、元素识别、操作执行等。
"""

from datetime import datetime
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from PIL import Image, ImageGrab
import asyncio
import cv2
import numpy as np
import pyautogui
import win32api
import win32con
import win32gui

from src.config.database_config import get_database_config
from src.models.task_models import TaskConfig
from src.repositories import (
    ExecutionActionRepository,
    RepositoryError,
    ScreenshotRepository,
)
from src.services.event_bus import EventBus, TaskEventType

logger = logging.getLogger(__name__)

# 禁用pyautogui的安全检查
pyautogui.FAILSAFE = False


class AutomationError(Exception):
    """自动化操作异常基类"""

    pass


class WindowNotFoundError(AutomationError):
    """窗口未找到异常"""

    pass


class ElementNotFoundError(AutomationError):
    """元素未找到异常"""

    pass


class OperationTimeoutError(AutomationError):
    """操作超时异常"""

    pass


class WindowInfo:
    """窗口信息"""

    def __init__(
        self, hwnd: int, title: str, class_name: str, rect: Tuple[int, int, int, int]
    ):
        self.hwnd = hwnd
        self.title = title
        self.class_name = class_name
        self.rect = rect  # (left, top, right, bottom)

    @property
    def width(self) -> int:
        return self.rect[2] - self.rect[0]

    @property
    def height(self) -> int:
        return self.rect[3] - self.rect[1]

    @property
    def center(self) -> Tuple[int, int]:
        return (self.rect[0] + self.width // 2, self.rect[1] + self.height // 2)


class ElementMatch:
    """元素匹配结果"""

    def __init__(self, x: int, y: int, width: int, height: int, confidence: float):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.confidence = confidence

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def rect(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.x + self.width, self.y + self.height)


class AutomationApplicationService:
    """自动化应用服务

    提供游戏自动化操作的核心功能，包括：
    - 窗口检测和管理
    - 屏幕截图
    - 图像识别和元素查找
    - 鼠标和键盘操作
    - 自动化序列执行
    """

    def __init__(
        self,
        event_bus: EventBus,
        screenshot_repository: Optional[ScreenshotRepository] = None,
        action_repository: Optional[ExecutionActionRepository] = None,
    ):
        self.event_bus = event_bus

        if screenshot_repository is None or action_repository is None:
            db_config = get_database_config()
            self.screenshot_repo = screenshot_repository or ScreenshotRepository(
                db_config.db_path
            )
            self.action_repo = action_repository or ExecutionActionRepository(
                db_config.db_path
            )
        else:
            self.screenshot_repo = screenshot_repository
            self.action_repo = action_repository

        # 操作配置
        self.default_timeout = 30.0  # 默认超时时间（秒）
        self.default_confidence = 0.8  # 默认匹配置信度
        self.click_delay = 0.1  # 点击后延迟
        self.type_delay = 0.05  # 输入字符间延迟

        # 缓存
        self._window_cache: Dict[str, WindowInfo] = {}
        self._template_cache: Dict[str, np.ndarray] = {}

    async def detect_game_windows(self, game_names: List[str]) -> List[WindowInfo]:
        """检测游戏窗口

        Args:
            game_names: 游戏名称列表

        Returns:
            检测到的游戏窗口列表
        """
        windows = []

        def enum_windows_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)

                # 检查是否匹配游戏名称
                for game_name in game_names:
                    if game_name.lower() in title.lower():
                        rect = win32gui.GetWindowRect(hwnd)
                        window_info = WindowInfo(hwnd, title, class_name, rect)
                        windows.append(window_info)

                        # 缓存窗口信息
                        self._window_cache[game_name] = window_info
                        break
            return True

        win32gui.EnumWindows(enum_windows_callback, None)

        logger.info(f"检测到 {len(windows)} 个游戏窗口")
        return windows

    async def detect_game_window(self, game_name: str) -> Optional[WindowInfo]:
        """检测单个游戏窗口

        Args:
            game_name: 游戏名称

        Returns:
            检测到的游戏窗口，如果未找到则返回None
        """
        windows = await self.detect_game_windows([game_name])
        return windows[0] if windows else None

    async def get_window_by_title(self, title_pattern: str) -> Optional[WindowInfo]:
        """根据标题模式获取窗口

        Args:
            title_pattern: 窗口标题模式

        Returns:
            匹配的窗口信息，如果未找到则返回None
        """
        # 先检查缓存
        if title_pattern in self._window_cache:
            cached_window = self._window_cache[title_pattern]
            if win32gui.IsWindow(cached_window.hwnd) and win32gui.IsWindowVisible(
                cached_window.hwnd
            ):
                return cached_window
            else:
                # 窗口已关闭，清除缓存
                del self._window_cache[title_pattern]

        # 重新搜索
        windows = await self.detect_game_windows([title_pattern])
        return windows[0] if windows else None

    async def activate_window(self, window: WindowInfo) -> bool:
        """激活窗口

        Args:
            window: 窗口信息

        Returns:
            是否激活成功
        """
        try:
            # 将窗口置于前台
            win32gui.SetForegroundWindow(window.hwnd)
            win32gui.ShowWindow(window.hwnd, win32con.SW_RESTORE)

            # 等待窗口激活
            await asyncio.sleep(0.5)

            # 验证窗口是否已激活
            foreground_hwnd = win32gui.GetForegroundWindow()
            success = foreground_hwnd == window.hwnd

            if success:
                logger.info(f"窗口激活成功: {window.title}")
            else:
                logger.warning(f"窗口激活失败: {window.title}")

            return success

        except Exception as e:
            logger.error(f"激活窗口失败: {e}")
            return False

    async def take_screenshot(
        self,
        execution_id: str,
        window: Optional[WindowInfo] = None,
        region: Optional[Tuple[int, int, int, int]] = None,
        save_to_db: bool = True,
    ) -> np.ndarray:
        """截取屏幕截图

        Args:
            execution_id: 执行ID
            window: 窗口信息，如果提供则截取窗口区域
            region: 截图区域 (left, top, right, bottom)
            save_to_db: 是否保存到数据库

        Returns:
            截图的numpy数组
        """
        try:
            if window:
                # 截取窗口区域
                screenshot = ImageGrab.grab(bbox=window.rect)
            elif region:
                # 截取指定区域
                screenshot = ImageGrab.grab(bbox=region)
            else:
                # 截取全屏
                screenshot = ImageGrab.grab()

            # 转换为numpy数组
            screenshot_array = np.array(screenshot)
            screenshot_bgr = cv2.cvtColor(screenshot_array, cv2.COLOR_RGB2BGR)

            # 保存到数据库
            if save_to_db:
                await self._save_screenshot(execution_id, screenshot_bgr, "action")

            logger.debug(f"截图完成，尺寸: {screenshot_bgr.shape}")
            return screenshot_bgr

        except Exception as e:
            logger.error(f"截图失败: {e}")
            raise AutomationError(f"截图失败: {e}")

    async def find_element(
        self,
        screenshot: np.ndarray,
        template_path: str,
        confidence: float = None,
        region: Optional[Tuple[int, int, int, int]] = None,
    ) -> Optional[ElementMatch]:
        """在截图中查找元素

        Args:
            screenshot: 截图数组
            template_path: 模板图片路径
            confidence: 匹配置信度
            region: 搜索区域

        Returns:
            匹配结果，如果未找到则返回None
        """
        try:
            confidence = confidence or self.default_confidence

            # 加载模板图片
            template = await self._load_template(template_path)
            if template is None:
                return None

            # 如果指定了区域，裁剪截图
            search_area = screenshot
            offset_x, offset_y = 0, 0

            if region:
                x1, y1, x2, y2 = region
                search_area = screenshot[y1:y2, x1:x2]
                offset_x, offset_y = x1, y1

            # 模板匹配
            result = cv2.matchTemplate(search_area, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val >= confidence:
                # 计算匹配位置
                x = max_loc[0] + offset_x
                y = max_loc[1] + offset_y
                h, w = template.shape[:2]

                match = ElementMatch(x, y, w, h, max_val)
                logger.debug(f"元素匹配成功: {template_path}, 置信度: {max_val:.3f}")
                return match
            else:
                logger.debug(
                    f"元素匹配失败: {template_path}, 最高置信度: {max_val:.3f}"
                )
                return None

        except Exception as e:
            logger.error(f"查找元素失败: {e}")
            return None

    async def wait_for_element(
        self,
        execution_id: str,
        template_path: str,
        window: Optional[WindowInfo] = None,
        timeout: float = None,
        confidence: float = None,
        region: Optional[Tuple[int, int, int, int]] = None,
    ) -> ElementMatch:
        """等待元素出现

        Args:
            execution_id: 执行ID
            template_path: 模板图片路径
            window: 窗口信息
            timeout: 超时时间
            confidence: 匹配置信度
            region: 搜索区域

        Returns:
            匹配结果

        Raises:
            OperationTimeoutError: 等待超时
        """
        timeout = timeout or self.default_timeout
        start_time = time.time()

        while time.time() - start_time < timeout:
            # 截图
            screenshot = await self.take_screenshot(
                execution_id, window, save_to_db=False
            )

            # 查找元素
            match = await self.find_element(
                screenshot, template_path, confidence, region
            )
            if match:
                return match

            # 等待一段时间后重试
            await asyncio.sleep(0.5)

        raise OperationTimeoutError(f"等待元素超时: {template_path}")

    async def click_element(
        self,
        execution_id: str,
        match: ElementMatch,
        button: str = "left",
        clicks: int = 1,
        delay: float = None,
    ) -> bool:
        """点击元素

        Args:
            execution_id: 执行ID
            match: 元素匹配结果
            button: 鼠标按钮 ('left', 'right', 'middle')
            clicks: 点击次数
            delay: 点击后延迟时间

        Returns:
            是否点击成功
        """
        try:
            delay = delay or self.click_delay

            # 移动到元素中心并点击
            center_x, center_y = match.center
            pyautogui.click(center_x, center_y, clicks=clicks, button=button)

            # 记录操作
            await self._record_action(
                execution_id,
                "click",
                {
                    "x": center_x,
                    "y": center_y,
                    "button": button,
                    "clicks": clicks,
                    "confidence": match.confidence,
                },
            )

            # 等待
            await asyncio.sleep(delay)

            logger.info(f"点击元素成功: ({center_x}, {center_y})")
            return True

        except Exception as e:
            logger.error(f"点击元素失败: {e}")
            return False

    async def click_position(
        self,
        execution_id: str,
        x: int,
        y: int,
        button: str = "left",
        clicks: int = 1,
        delay: float = None,
    ) -> bool:
        """点击指定位置

        Args:
            execution_id: 执行ID
            x: X坐标
            y: Y坐标
            button: 鼠标按钮
            clicks: 点击次数
            delay: 点击后延迟时间

        Returns:
            是否点击成功
        """
        try:
            delay = delay or self.click_delay

            pyautogui.click(x, y, clicks=clicks, button=button)

            # 记录操作
            await self._record_action(
                execution_id,
                "click_position",
                {"x": x, "y": y, "button": button, "clicks": clicks},
            )

            await asyncio.sleep(delay)

            logger.info(f"点击位置成功: ({x}, {y})")
            return True

        except Exception as e:
            logger.error(f"点击位置失败: {e}")
            return False

    async def type_text(
        self, execution_id: str, text: str, interval: float = None
    ) -> bool:
        """输入文本

        Args:
            execution_id: 执行ID
            text: 要输入的文本
            interval: 字符间隔时间

        Returns:
            是否输入成功
        """
        try:
            interval = interval or self.type_delay

            pyautogui.typewrite(text, interval=interval)

            # 记录操作
            await self._record_action(
                execution_id, "type_text", {"text": text, "interval": interval}
            )

            logger.info(f"输入文本成功: {text}")
            return True

        except Exception as e:
            logger.error(f"输入文本失败: {e}")
            return False

    async def press_key(
        self, execution_id: str, key: str, presses: int = 1, interval: float = 0.1
    ) -> bool:
        """按键

        Args:
            execution_id: 执行ID
            key: 按键名称
            presses: 按键次数
            interval: 按键间隔

        Returns:
            是否按键成功
        """
        try:
            pyautogui.press(key, presses=presses, interval=interval)

            # 记录操作
            await self._record_action(
                execution_id,
                "press_key",
                {"key": key, "presses": presses, "interval": interval},
            )

            logger.info(f"按键成功: {key}")
            return True

        except Exception as e:
            logger.error(f"按键失败: {e}")
            return False

    async def execute_automation_sequence(
        self,
        execution_id: str,
        sequence: List[Dict[str, Any]],
        window: Optional[WindowInfo] = None,
    ) -> bool:
        """执行自动化序列

        Args:
            execution_id: 执行ID
            sequence: 操作序列
            window: 目标窗口

        Returns:
            是否执行成功
        """
        try:
            # 激活窗口
            if window:
                await self.activate_window(window)

            # 执行序列中的每个操作
            for i, action in enumerate(sequence):
                action_type = action.get("type")

                logger.info(f"执行操作 {i+1}/{len(sequence)}: {action_type}")

                if action_type == "wait_element":
                    await self.wait_for_element(
                        execution_id,
                        action["template"],
                        window,
                        action.get("timeout"),
                        action.get("confidence"),
                        action.get("region"),
                    )

                elif action_type == "click_element":
                    match = await self.wait_for_element(
                        execution_id,
                        action["template"],
                        window,
                        action.get("timeout"),
                        action.get("confidence"),
                        action.get("region"),
                    )
                    await self.click_element(
                        execution_id,
                        match,
                        action.get("button", "left"),
                        action.get("clicks", 1),
                        action.get("delay"),
                    )

                elif action_type == "click_position":
                    await self.click_position(
                        execution_id,
                        action["x"],
                        action["y"],
                        action.get("button", "left"),
                        action.get("clicks", 1),
                        action.get("delay"),
                    )

                elif action_type == "type_text":
                    await self.type_text(
                        execution_id, action["text"], action.get("interval")
                    )

                elif action_type == "press_key":
                    await self.press_key(
                        execution_id,
                        action["key"],
                        action.get("presses", 1),
                        action.get("interval", 0.1),
                    )

                elif action_type == "wait":
                    await asyncio.sleep(action["duration"])

                elif action_type == "screenshot":
                    await self.take_screenshot(
                        execution_id, window, action.get("region"), True
                    )

                else:
                    logger.warning(f"未知操作类型: {action_type}")
                    continue

                # 操作间隔
                if "interval" in action:
                    await asyncio.sleep(action["interval"])

            logger.info(f"自动化序列执行完成，共 {len(sequence)} 个操作")
            return True

        except Exception as e:
            logger.error(f"执行自动化序列失败: {e}")
            return False

    async def _load_template(self, template_path: str) -> Optional[np.ndarray]:
        """加载模板图片

        Args:
            template_path: 模板图片路径

        Returns:
            模板图片数组
        """
        # 检查缓存
        if template_path in self._template_cache:
            return self._template_cache[template_path]

        try:
            # 加载图片
            template_file = Path(template_path)
            if not template_file.exists():
                logger.error(f"模板文件不存在: {template_path}")
                return None

            template = cv2.imread(str(template_file))
            if template is None:
                logger.error(f"无法加载模板文件: {template_path}")
                return None

            # 缓存模板
            self._template_cache[template_path] = template
            return template

        except Exception as e:
            logger.error(f"加载模板失败: {e}")
            return None

    async def _save_screenshot(
        self, execution_id: str, screenshot: np.ndarray, screenshot_type: str
    ) -> str:
        """保存截图到数据库

        Args:
            execution_id: 执行ID
            screenshot: 截图数组
            screenshot_type: 截图类型

        Returns:
            截图ID
        """
        try:
            # 编码图片为字节
            _, buffer = cv2.imencode(".png", screenshot)
            image_data = buffer.tobytes()

            # 创建截图记录
            screenshot_record = {
                "screenshot_id": str(uuid4()),
                "execution_id": execution_id,
                "screenshot_type": screenshot_type,
                "image_data": image_data,
                "file_size": len(image_data),
                "created_at": datetime.now(),
            }

            await self.screenshot_repo.create(screenshot_record)
            return screenshot_record["screenshot_id"]

        except Exception as e:
            logger.error(f"保存截图失败: {e}")
            raise AutomationError(f"保存截图失败: {e}")

    async def _record_action(
        self, execution_id: str, action_type: str, action_data: Dict[str, Any]
    ) -> str:
        """记录操作

        Args:
            execution_id: 执行ID
            action_type: 操作类型
            action_data: 操作数据

        Returns:
            操作ID
        """
        try:
            action_record = {
                "action_id": str(uuid4()),
                "execution_id": execution_id,
                "action_type": action_type,
                "action_data": action_data,
                "executed_at": datetime.now(),
            }

            await self.action_repo.create(action_record)

            # 发布自动化操作事件
            await self.event_bus.publish(
                ActionExecutedEvent(
                    execution_id=execution_id,
                    action_id=action_record["action_id"],
                    action_type=action_type,
                    success=True,
                    duration=0.0,  # 这里可以记录实际执行时间
                )
            )

            return action_record["action_id"]

        except Exception as e:
            logger.error(f"记录操作失败: {e}")
            raise AutomationError(f"记录操作失败: {e}")
