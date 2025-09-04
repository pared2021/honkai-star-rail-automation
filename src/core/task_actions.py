# -*- coding: utf-8 -*-
"""
任务动作系统 - 定义和执行各种自动化动作
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple
import uuid

from loguru import logger
import pyautogui

from .enums import ActionStatus, ActionType


@dataclass
class ActionResult:
    """动作执行结果"""

    action_id: str
    status: ActionStatus
    start_time: float
    end_time: Optional[float] = None
    error_message: Optional[str] = None
    output_data: Optional[Dict[str, Any]] = None
    screenshot_path: Optional[str] = None

    @property
    def duration(self) -> Optional[float]:
        """执行时长"""
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "action_id": self.action_id,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "error_message": self.error_message,
            "output_data": self.output_data,
            "screenshot_path": self.screenshot_path,
        }


class BaseAction(ABC):
    """动作基类"""

    def __init__(
        self, action_id: str, action_type: ActionType, parameters: Dict[str, Any] = None
    ):
        self.action_id = action_id
        self.action_type = action_type
        self.parameters = parameters or {}
        self.result: Optional[ActionResult] = None

    @abstractmethod
    def validate(self) -> bool:
        """验证动作参数"""
        pass

    @abstractmethod
    def execute(self) -> ActionResult:
        """执行动作"""
        pass

    def pre_execute(self):
        """执行前的准备工作"""
        logger.info(f"开始执行动作: {self.action_type.value} (ID: {self.action_id})")
        self.result = ActionResult(
            action_id=self.action_id,
            status=ActionStatus.RUNNING,
            start_time=time.time(),
        )

    def post_execute(self, success: bool, error_message: str = None):
        """执行后的清理工作"""
        if self.result:
            self.result.end_time = time.time()
            self.result.status = (
                ActionStatus.COMPLETED if success else ActionStatus.FAILED
            )
            if error_message:
                self.result.error_message = error_message

            logger.info(
                f"动作执行完成: {self.action_type.value} - {self.result.status.value}"
            )


class ClickAction(BaseAction):
    """点击动作"""

    def __init__(
        self,
        action_id: str,
        x: int,
        y: int,
        button: str = "left",
        clicks: int = 1,
        interval: float = 0.0,
    ):
        super().__init__(action_id, ActionType.CLICK)
        self.x = x
        self.y = y
        self.button = button
        self.clicks = clicks
        self.interval = interval
        self.parameters = {
            "x": x,
            "y": y,
            "button": button,
            "clicks": clicks,
            "interval": interval,
        }

    def validate(self) -> bool:
        """验证点击参数"""
        if not isinstance(self.x, int) or not isinstance(self.y, int):
            return False
        if self.x < 0 or self.y < 0:
            return False
        if self.button not in ["left", "right", "middle"]:
            return False
        if self.clicks < 1:
            return False
        return True

    def execute(self) -> ActionResult:
        """执行点击动作"""
        self.pre_execute()

        try:
            if not self.validate():
                raise ValueError("点击参数验证失败")

            # 执行点击
            pyautogui.click(
                x=self.x,
                y=self.y,
                clicks=self.clicks,
                interval=self.interval,
                button=self.button,
            )

            self.result.output_data = {
                "clicked_position": (self.x, self.y),
                "button": self.button,
                "clicks": self.clicks,
            }

            self.post_execute(True)

        except Exception as e:
            error_msg = f"点击动作执行失败: {str(e)}"
            logger.error(error_msg)
            self.post_execute(False, error_msg)

        return self.result


class KeyPressAction(BaseAction):
    """按键动作"""

    def __init__(
        self, action_id: str, key: str, presses: int = 1, interval: float = 0.0
    ):
        super().__init__(action_id, ActionType.KEY_PRESS)
        self.key = key
        self.presses = presses
        self.interval = interval
        self.parameters = {"key": key, "presses": presses, "interval": interval}

    def validate(self) -> bool:
        """验证按键参数"""
        if not self.key or not isinstance(self.key, str):
            return False
        if self.presses < 1:
            return False
        return True

    def execute(self) -> ActionResult:
        """执行按键动作"""
        self.pre_execute()

        try:
            if not self.validate():
                raise ValueError("按键参数验证失败")

            # 执行按键
            pyautogui.press(self.key, presses=self.presses, interval=self.interval)

            self.result.output_data = {"key": self.key, "presses": self.presses}

            self.post_execute(True)

        except Exception as e:
            error_msg = f"按键动作执行失败: {str(e)}"
            logger.error(error_msg)
            self.post_execute(False, error_msg)

        return self.result


class WaitAction(BaseAction):
    """等待动作"""

    def __init__(self, action_id: str, duration: float):
        super().__init__(action_id, ActionType.WAIT)
        self.duration = duration
        self.parameters = {"duration": duration}

    def validate(self) -> bool:
        """验证等待参数"""
        return isinstance(self.duration, (int, float)) and self.duration > 0

    def execute(self) -> ActionResult:
        """执行等待动作"""
        self.pre_execute()

        try:
            if not self.validate():
                raise ValueError("等待参数验证失败")

            # 执行等待
            time.sleep(self.duration)

            self.result.output_data = {"wait_duration": self.duration}

            self.post_execute(True)

        except Exception as e:
            error_msg = f"等待动作执行失败: {str(e)}"
            logger.error(error_msg)
            self.post_execute(False, error_msg)

        return self.result


class ScreenshotAction(BaseAction):
    """截图动作"""

    def __init__(
        self,
        action_id: str,
        save_path: str = None,
        region: Tuple[int, int, int, int] = None,
    ):
        super().__init__(action_id, ActionType.SCREENSHOT)
        self.save_path = save_path
        self.region = region  # (left, top, width, height)
        self.parameters = {"save_path": save_path, "region": region}

    def validate(self) -> bool:
        """验证截图参数"""
        if self.region:
            if len(self.region) != 4:
                return False
            if any(not isinstance(x, int) or x < 0 for x in self.region):
                return False
        return True

    def execute(self) -> ActionResult:
        """执行截图动作"""
        self.pre_execute()

        try:
            if not self.validate():
                raise ValueError("截图参数验证失败")

            # 生成截图路径
            if not self.save_path:
                screenshots_dir = Path("data/screenshots")
                screenshots_dir.mkdir(parents=True, exist_ok=True)
                timestamp = int(time.time() * 1000)
                self.save_path = str(screenshots_dir / f"screenshot_{timestamp}.png")

            # 执行截图
            if self.region:
                screenshot = pyautogui.screenshot(region=self.region)
            else:
                screenshot = pyautogui.screenshot()

            screenshot.save(self.save_path)

            self.result.output_data = {
                "screenshot_path": self.save_path,
                "region": self.region,
            }
            self.result.screenshot_path = self.save_path

            self.post_execute(True)

        except Exception as e:
            error_msg = f"截图动作执行失败: {str(e)}"
            logger.error(error_msg)
            self.post_execute(False, error_msg)

        return self.result


class CustomAction(BaseAction):
    """自定义动作"""

    def __init__(
        self, action_id: str, script: str, script_params: Dict[str, Any] = None
    ):
        super().__init__(action_id, ActionType.CUSTOM)
        self.script = script
        self.script_params = script_params or {}
        self.parameters = {"script": script, "script_params": script_params}

    def validate(self) -> bool:
        """验证自定义脚本参数"""
        return bool(self.script and isinstance(self.script, str))

    def execute(self) -> ActionResult:
        """执行自定义动作"""
        self.pre_execute()

        try:
            if not self.validate():
                raise ValueError("自定义脚本参数验证失败")

            # 创建执行环境
            exec_globals = {
                "pyautogui": pyautogui,
                "time": time,
                "logger": logger,
                "params": self.script_params,
                "result_data": {},
            }

            # 执行自定义脚本
            exec(self.script, exec_globals)

            self.result.output_data = exec_globals.get("result_data", {})

            self.post_execute(True)

        except Exception as e:
            error_msg = f"自定义动作执行失败: {str(e)}"
            logger.error(error_msg)
            self.post_execute(False, error_msg)

        return self.result


class ActionFactory:
    """动作工厂类"""

    @staticmethod
    def create_action(action_data: Dict[str, Any]) -> BaseAction:
        """根据数据创建动作实例

        Args:
            action_data: 动作数据字典

        Returns:
            BaseAction: 动作实例
        """
        action_id = action_data.get("action_id", str(uuid.uuid4()))
        action_type = action_data.get("action_type")

        if action_type == ActionType.CLICK.value:
            coordinates = action_data.get("coordinates", "{}")
            if isinstance(coordinates, str):
                coordinates = json.loads(coordinates)

            parameters = action_data.get("parameters", "{}")
            if isinstance(parameters, str):
                parameters = json.loads(parameters)

            return ClickAction(
                action_id=action_id,
                x=coordinates.get("x", 0),
                y=coordinates.get("y", 0),
                button=parameters.get("button", "left"),
                clicks=parameters.get("clicks", 1),
                interval=parameters.get("interval", 0.0),
            )

        elif action_type == ActionType.KEY_PRESS.value:
            parameters = action_data.get("parameters", "{}")
            if isinstance(parameters, str):
                parameters = json.loads(parameters)

            return KeyPressAction(
                action_id=action_id,
                key=action_data.get("key_code", ""),
                presses=parameters.get("presses", 1),
                interval=parameters.get("interval", 0.0),
            )

        elif action_type == ActionType.WAIT.value:
            return WaitAction(
                action_id=action_id, duration=action_data.get("wait_duration", 1.0)
            )

        elif action_type == ActionType.SCREENSHOT.value:
            screenshot_path = action_data.get("screenshot_path", "screenshot.png")
            region = action_data.get("region")
            if isinstance(region, str):
                region = json.loads(region) if region else None

            # 处理parameters字段
            parameters = action_data.get("parameters", {})
            if isinstance(parameters, str):
                parameters = json.loads(parameters) if parameters else {}

            return ScreenshotAction(
                action_id=action_id,
                save_path=screenshot_path,
                region=tuple(region) if region else None,
            )

        elif action_type == ActionType.CUSTOM.value:
            parameters = action_data.get("parameters", {})
            if isinstance(parameters, str):
                parameters = json.loads(parameters)

            return CustomAction(
                action_id=action_id,
                script=action_data.get("custom_script", ""),
                script_params=parameters,
            )

        else:
            raise ValueError(f"不支持的动作类型: {action_type}")
