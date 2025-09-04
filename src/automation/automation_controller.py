# -*- coding: utf-8 -*-
"""
自动化控制器 - 负责执行自动化操作和任务管理
"""

from dataclasses import dataclass
from queue import Empty, Queue
import random
import threading
import time
from typing import Any, Callable, Dict, List, Optional

import pyautogui

from src.core.logger import get_logger

logger = get_logger(__name__)

from src.core.config_manager import ConfigManager, ConfigType
from src.core.enums import ActionType, TaskStatus
from src.core.game_detector import DetectionResult, GameDetector
from src.database.db_manager import DatabaseManager


@dataclass
class AutomationAction:
    """自动化操作"""

    action_type: ActionType
    params: Dict[str, Any]
    description: str = ""
    retry_count: int = 3
    timeout: float = 10.0


@dataclass
class TaskResult:
    """任务执行结果"""

    success: bool
    message: str
    execution_time: float
    actions_completed: int
    actions_failed: int
    error_details: Optional[str] = None


class AutomationController:
    """自动化控制器类"""

    def __init__(
        self,
        config_manager: ConfigManager,
        db_manager: DatabaseManager,
        game_detector: GameDetector,
    ):
        """初始化自动化控制器

        Args:
            config_manager: 配置管理器
            db_manager: 数据库管理器
            game_detector: 游戏检测器
        """
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.game_detector = game_detector

        # 自动化配置
        automation_config = config_manager.get_config(ConfigType.AUTOMATION_CONFIG)
        self.click_delay = float(
            automation_config.get("click_delay", 1.0) if automation_config else 1.0
        )
        self.random_delay = (
            automation_config.get("random_delay", True) if automation_config else True
        )
        self.safe_mode = (
            automation_config.get("safe_mode", True) if automation_config else True
        )

        # 任务管理
        self.current_task_id: Optional[str] = None
        self.task_status = TaskStatus.CREATED
        self.task_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()

        # 操作队列
        self.action_queue: Queue[AutomationAction] = Queue()

        # 统计信息
        self.stats = {
            "actions_executed": 0,
            "actions_failed": 0,
            "total_execution_time": 0.0,
            "last_action_time": None,
        }

        # 运行状态
        self.is_running = False
        self.last_run_time = None

        # 设置pyautogui
        pyautogui.FAILSAFE = True  # 鼠标移到左上角停止
        pyautogui.PAUSE = 0.1  # 操作间隔

        logger.info("自动化控制器初始化完成")

    def start_task(self, task_id: str, actions: List[AutomationAction]) -> bool:
        """开始执行任务

        Args:
            task_id: 任务ID
            actions: 操作列表

        Returns:
            bool: 是否成功开始
        """
        if self.task_status == TaskStatus.RUNNING:
            logger.warning("已有任务在运行中")
            return False

        # 检查游戏状态
        if not self.game_detector.is_game_running():
            logger.error("游戏未运行，无法开始自动化")
            return False

        # 初始化任务
        self.current_task_id = task_id
        self.task_status = TaskStatus.RUNNING
        self.stop_event.clear()
        self.pause_event.clear()

        # 清空操作队列并添加新操作
        while not self.action_queue.empty():
            try:
                self.action_queue.get_nowait()
            except Empty:
                break

        for action in actions:
            self.action_queue.put(action)

        # 更新数据库状态
        self.db_manager.update_task_status(task_id, TaskStatus.RUNNING.value)
        self.db_manager.add_execution_log(task_id, "INFO", "任务开始执行")

        # 启动执行线程
        self.task_thread = threading.Thread(target=self._execute_task, daemon=True)
        self.task_thread.start()

        # 更新运行状态
        self.is_running = True
        self.last_run_time = time.time()

        logger.info(f"任务开始执行: {task_id}")
        return True

    def stop_task(self) -> bool:
        """停止当前任务

        Returns:
            bool: 是否成功停止
        """
        if self.task_status != TaskStatus.RUNNING:
            logger.warning("没有正在运行的任务")
            return False

        # 设置停止事件
        self.stop_event.set()

        # 等待线程结束
        if self.task_thread and self.task_thread.is_alive():
            self.task_thread.join(timeout=5.0)

        # 更新状态
        self.task_status = TaskStatus.STOPPED
        self.is_running = False

        if self.current_task_id:
            self.db_manager.update_task_status(
                self.current_task_id, TaskStatus.STOPPED.value
            )
            self.db_manager.add_execution_log(
                self.current_task_id, "INFO", "任务已停止"
            )

        logger.info("任务已停止")
        return True

    def pause_task(self) -> bool:
        """暂停当前任务

        Returns:
            bool: 是否成功暂停
        """
        if self.task_status != TaskStatus.RUNNING:
            logger.warning("没有正在运行的任务")
            return False

        self.pause_event.set()
        self.task_status = TaskStatus.PAUSED

        if self.current_task_id:
            self.db_manager.add_execution_log(
                self.current_task_id, "INFO", "任务已暂停"
            )

        logger.info("任务已暂停")
        return True

    def resume_task(self) -> bool:
        """恢复当前任务

        Returns:
            bool: 是否成功恢复
        """
        if self.task_status != TaskStatus.PAUSED:
            logger.warning("任务未处于暂停状态")
            return False

        self.pause_event.clear()
        self.task_status = TaskStatus.RUNNING

        if self.current_task_id:
            self.db_manager.add_execution_log(
                self.current_task_id, "INFO", "任务已恢复"
            )

        logger.info("任务已恢复")
        return True

    def _execute_task(self):
        """执行任务的主循环"""
        start_time = time.time()
        actions_completed = 0
        actions_failed = 0

        try:
            while not self.stop_event.is_set():
                # 检查暂停状态
                if self.pause_event.is_set():
                    time.sleep(0.1)
                    continue

                # 获取下一个操作
                try:
                    action = self.action_queue.get_nowait()
                except Empty:
                    # 队列为空，任务完成
                    self.task_status = TaskStatus.COMPLETED
                    break

                # 执行操作
                success = self._execute_action(action)
                if success:
                    actions_completed += 1
                    self.stats["actions_executed"] += 1
                else:
                    actions_failed += 1
                    self.stats["actions_failed"] += 1

                    # 如果是安全模式且操作失败，停止任务
                    if self.safe_mode:
                        logger.error("安全模式下操作失败，停止任务")
                        self.task_status = TaskStatus.FAILED
                        break

                # 操作间隔
                self._wait_with_random_delay()

                # 更新最后操作时间
                self.stats["last_action_time"] = time.time()

        except Exception as e:
            logger.error(f"任务执行异常: {e}")
            self.task_status = TaskStatus.FAILED
            actions_failed += 1

        # 计算执行时间
        execution_time = time.time() - start_time
        self.stats["total_execution_time"] += execution_time

        # 创建任务结果
        result = TaskResult(
            success=self.task_status == TaskStatus.COMPLETED,
            message=f"任务{self.task_status.value}",
            execution_time=execution_time,
            actions_completed=actions_completed,
            actions_failed=actions_failed,
        )

        # 更新数据库
        if self.current_task_id:
            self.db_manager.update_task_status(
                self.current_task_id, self.task_status.value
            )
            self.db_manager.add_execution_log(
                self.current_task_id,
                "INFO",
                f"任务完成: 成功{actions_completed}个操作，失败{actions_failed}个操作，耗时{execution_time:.1f}秒",
            )

        logger.info(f"任务执行完成: {result.message}")

    def _execute_action(self, action: AutomationAction) -> bool:
        """执行单个操作

        Args:
            action: 要执行的操作

        Returns:
            bool: 是否执行成功
        """
        logger.debug(f"执行操作: {action.action_type.value} - {action.description}")

        try:
            # 确保游戏窗口处于活动状态
            if not self.game_detector.is_game_active():
                if not self.game_detector.activate_game_window():
                    logger.warning("无法激活游戏窗口")

            # 根据操作类型执行相应操作
            if action.action_type == ActionType.CLICK:
                return self._execute_click(action)
            elif action.action_type == ActionType.DOUBLE_CLICK:
                return self._execute_double_click(action)
            elif action.action_type == ActionType.RIGHT_CLICK:
                return self._execute_right_click(action)
            elif action.action_type == ActionType.KEY_PRESS:
                return self._execute_key_press(action)
            elif action.action_type == ActionType.KEY_COMBINATION:
                return self._execute_key_combination(action)
            elif action.action_type == ActionType.WAIT:
                return self._execute_wait(action)
            elif action.action_type == ActionType.WAIT_FOR_TEMPLATE:
                return self._execute_wait_for_template(action)
            elif action.action_type == ActionType.SCROLL:
                return self._execute_scroll(action)
            elif action.action_type == ActionType.DRAG:
                return self._execute_drag(action)
            elif action.action_type == ActionType.TYPE_TEXT:
                return self._execute_type_text(action)
            else:
                logger.error(f"未知操作类型: {action.action_type}")
                return False

        except Exception as e:
            logger.error(f"执行操作失败 {action.action_type.value}: {e}")
            if self.current_task_id:
                self.db_manager.add_execution_log(
                    self.current_task_id,
                    "ERROR",
                    f"操作失败: {action.description}",
                    str(e),
                )
            return False

    def _execute_click(self, action: AutomationAction) -> bool:
        """执行点击操作"""
        params = action.params

        if "template" in params:
            # 基于模板的点击
            template_name = params["template"]
            region = params.get("region")

            result = self.game_detector.find_template(template_name, region=region)
            if not result.found:
                logger.warning(f"未找到模板 {template_name}，点击失败")
                return False

            x, y = result.location
        elif "x" in params and "y" in params:
            # 基于坐标的点击
            x, y = params["x"], params["y"]
        else:
            logger.error("点击操作缺少坐标或模板参数")
            return False

        # 添加随机偏移
        if self.random_delay:
            offset = random.randint(-3, 3)
            x += offset
            y += offset

        pyautogui.click(x, y)
        logger.debug(f"点击位置: ({x}, {y})")
        return True

    def _execute_double_click(self, action: AutomationAction) -> bool:
        """执行双击操作"""
        # 复用点击逻辑，但使用双击
        params = action.params

        if "template" in params:
            template_name = params["template"]
            region = params.get("region")

            result = self.game_detector.find_template(template_name, region=region)
            if not result.found:
                return False

            x, y = result.location
        elif "x" in params and "y" in params:
            x, y = params["x"], params["y"]
        else:
            return False

        pyautogui.doubleClick(x, y)
        logger.debug(f"双击位置: ({x}, {y})")
        return True

    def _execute_right_click(self, action: AutomationAction) -> bool:
        """执行右键点击操作"""
        params = action.params

        if "template" in params:
            template_name = params["template"]
            region = params.get("region")

            result = self.game_detector.find_template(template_name, region=region)
            if not result.found:
                return False

            x, y = result.location
        elif "x" in params and "y" in params:
            x, y = params["x"], params["y"]
        else:
            return False

        pyautogui.rightClick(x, y)
        logger.debug(f"右键点击位置: ({x}, {y})")
        return True

    def _execute_key_press(self, action: AutomationAction) -> bool:
        """执行按键操作"""
        key = action.params.get("key")
        if not key:
            logger.error("按键操作缺少key参数")
            return False

        pyautogui.press(key)
        logger.debug(f"按键: {key}")
        return True

    def _execute_key_combination(self, action: AutomationAction) -> bool:
        """执行组合键操作"""
        keys = action.params.get("keys")
        if not keys or not isinstance(keys, list):
            logger.error("组合键操作缺少keys参数或格式错误")
            return False

        pyautogui.hotkey(*keys)
        logger.debug(f"组合键: {'+'.join(keys)}")
        return True

    def _execute_wait(self, action: AutomationAction) -> bool:
        """执行等待操作"""
        duration = action.params.get("duration", 1.0)

        # 分段等待，以便响应停止信号
        wait_time = 0.0
        while wait_time < duration and not self.stop_event.is_set():
            sleep_time = min(0.1, duration - wait_time)
            time.sleep(sleep_time)
            wait_time += sleep_time

        logger.debug(f"等待: {duration}秒")
        return True

    def _execute_wait_for_template(self, action: AutomationAction) -> bool:
        """执行等待模板出现操作"""
        template_name = action.params.get("template")
        timeout = action.params.get("timeout", action.timeout)
        region = action.params.get("region")

        if not template_name:
            logger.error("等待模板操作缺少template参数")
            return False

        result = self.game_detector.wait_for_template(
            template_name, timeout=timeout, region=region
        )

        logger.debug(f"等待模板 {template_name}: {'成功' if result.found else '超时'}")
        return result.found

    def _execute_scroll(self, action: AutomationAction) -> bool:
        """执行滚动操作"""
        x = action.params.get("x", pyautogui.size().width // 2)
        y = action.params.get("y", pyautogui.size().height // 2)
        clicks = action.params.get("clicks", 3)

        pyautogui.scroll(clicks, x, y)
        logger.debug(f"滚动: 位置({x}, {y}), 滚动{clicks}次")
        return True

    def _execute_drag(self, action: AutomationAction) -> bool:
        """执行拖拽操作"""
        from_x = action.params.get("from_x")
        from_y = action.params.get("from_y")
        to_x = action.params.get("to_x")
        to_y = action.params.get("to_y")
        duration = action.params.get("duration", 1.0)

        if None in [from_x, from_y, to_x, to_y]:
            logger.error("拖拽操作缺少坐标参数")
            return False

        pyautogui.drag(to_x - from_x, to_y - from_y, duration, button="left")
        logger.debug(f"拖拽: 从({from_x}, {from_y})到({to_x}, {to_y})")
        return True

    def _execute_type_text(self, action: AutomationAction) -> bool:
        """执行文本输入操作"""
        text = action.params.get("text")
        interval = action.params.get("interval", 0.05)

        if not text:
            logger.error("文本输入操作缺少text参数")
            return False

        pyautogui.typewrite(text, interval=interval)
        logger.debug(f"输入文本: {text}")
        return True

    def _wait_with_random_delay(self):
        """带随机延迟的等待"""
        base_delay = self.click_delay

        if self.random_delay:
            # 添加随机延迟（±50%）
            random_factor = random.uniform(0.5, 1.5)
            delay = base_delay * random_factor
        else:
            delay = base_delay

        time.sleep(delay)

    def add_action(self, action: AutomationAction):
        """添加操作到队列

        Args:
            action: 要添加的操作
        """
        self.action_queue.put(action)
        logger.debug(f"添加操作到队列: {action.action_type.value}")

    def get_task_status(self) -> TaskStatus:
        """获取当前任务状态

        Returns:
            TaskStatus: 当前任务状态
        """
        return self.task_status

    def get_last_run_time(self) -> Optional[float]:
        """获取最后运行时间

        Returns:
            Optional[float]: 最后运行时间戳，如果从未运行则返回None
        """
        return self.last_run_time

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            Dict: 统计信息
        """
        return {
            "current_task_id": self.current_task_id,
            "task_status": self.task_status.value,
            "queue_size": self.action_queue.qsize(),
            "stats": self.stats.copy(),
            "config": {
                "click_delay": self.click_delay,
                "random_delay": self.random_delay,
                "safe_mode": self.safe_mode,
            },
        }

    def create_simple_actions(self) -> List[AutomationAction]:
        """创建一些简单的示例操作

        Returns:
            List[AutomationAction]: 操作列表
        """
        actions = [
            AutomationAction(
                action_type=ActionType.WAIT,
                params={"duration": 2.0},
                description="等待游戏加载",
            ),
            AutomationAction(
                action_type=ActionType.KEY_PRESS,
                params={"key": "space"},
                description="按空格键",
            ),
            AutomationAction(
                action_type=ActionType.WAIT,
                params={"duration": 1.0},
                description="短暂等待",
            ),
        ]

        return actions
