# -*- coding: utf-8 -*-
"""
主窗口Model

管理主窗口的数据状态，包括应用程序状态、任务统计等。
"""

from datetime import datetime
import logging
from typing import Any, Dict, List

from ...application.automation_application_service import AutomationApplicationService
from ...application.task_application_service import TaskApplicationService
from ...core.config_manager import ConfigManager
from ...core.enums import TaskStatus, TaskType
from ..mvp.base_model import BaseModel

logger = logging.getLogger(__name__)


class MainWindowModel(BaseModel):
    """主窗口数据模型

    管理主窗口相关的所有数据状态
    """

    def __init__(
        self,
        task_service: TaskApplicationService,
        automation_service: AutomationApplicationService,
        config_manager: ConfigManager,
    ):
        super().__init__()

        self._task_service = task_service
        self._automation_service = automation_service
        self._config_manager = config_manager

        # 初始化数据字段
        self._initialize_fields()

        # 设置验证器
        self._setup_validators()

        logger.debug("主窗口Model初始化完成")

    def _initialize_fields(self):
        """初始化数据字段"""
        self._data.update(
            {
                # 应用状态
                "app_status": "idle",  # idle, running, paused, error
                "automation_enabled": False,
                "last_update_time": None,
                # 任务统计
                "total_tasks": 0,
                "pending_tasks": 0,
                "running_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0,
                # 任务类型统计
                "daily_mission_count": 0,
                "weekly_mission_count": 0,
                "event_mission_count": 0,
                "custom_task_count": 0,
                # 系统信息
                "game_detected": False,
                "game_window_title": "",
                "automation_running": False,
                "last_automation_time": None,
                # 配置信息
                "auto_start_enabled": False,
                "notification_enabled": True,
                "log_level": "INFO",
                # 最近任务
                "recent_tasks": [],
                # 错误信息
                "last_error": None,
                "error_count": 0,
            }
        )

    def _setup_validators(self):
        """设置验证器"""
        # 应用状态验证
        self.add_validator(
            "app_status", lambda x: x in ["idle", "running", "paused", "error"]
        )

        # 日志级别验证
        self.add_validator(
            "log_level", lambda x: x in ["DEBUG", "INFO", "WARNING", "ERROR"]
        )

        # 数值验证
        for field in [
            "total_tasks",
            "pending_tasks",
            "running_tasks",
            "completed_tasks",
            "failed_tasks",
            "error_count",
        ]:
            self.add_validator(field, lambda x: isinstance(x, int) and x >= 0)

    async def load_data(self) -> bool:
        """加载数据

        Returns:
            是否加载成功
        """
        try:
            logger.info("开始加载主窗口数据")

            # 加载任务统计
            await self._load_task_statistics()

            # 加载系统状态
            await self._load_system_status()

            # 加载配置信息
            await self._load_configuration()

            # 加载最近任务
            await self._load_recent_tasks()

            # 更新最后更新时间
            self.set_data("last_update_time", datetime.now(), validate=False)

            logger.info("主窗口数据加载完成")
            return True

        except Exception as e:
            logger.error(f"加载主窗口数据失败: {e}")
            self.set_data("last_error", str(e), validate=False)
            return False

    async def save_data(self) -> bool:
        """保存数据

        Returns:
            是否保存成功
        """
        try:
            logger.info("开始保存主窗口数据")

            # 保存配置信息
            await self._save_configuration()

            logger.info("主窗口数据保存完成")
            return True

        except Exception as e:
            logger.error(f"保存主窗口数据失败: {e}")
            self.set_data("last_error", str(e), validate=False)
            return False

    async def _load_task_statistics(self):
        """加载任务统计"""
        try:
            # 获取所有任务
            all_tasks = await self._task_service.get_all_tasks()

            # 统计总数
            self.set_data("total_tasks", len(all_tasks), validate=False)

            # 按状态统计
            status_counts = {}
            for task in all_tasks:
                status = task.status
                status_counts[status] = status_counts.get(status, 0) + 1

            self.set_data(
                "pending_tasks",
                status_counts.get(TaskStatus.PENDING, 0),
                validate=False,
            )
            self.set_data(
                "running_tasks",
                status_counts.get(TaskStatus.RUNNING, 0),
                validate=False,
            )
            self.set_data(
                "completed_tasks",
                status_counts.get(TaskStatus.COMPLETED, 0),
                validate=False,
            )
            self.set_data(
                "failed_tasks", status_counts.get(TaskStatus.FAILED, 0), validate=False
            )

            # 按类型统计
            type_counts = {}
            for task in all_tasks:
                task_type = task.task_type
                type_counts[task_type] = type_counts.get(task_type, 0) + 1

            self.set_data(
                "daily_mission_count",
                type_counts.get(TaskType.DAILY_MISSION, 0),
                validate=False,
            )
            self.set_data(
                "weekly_mission_count",
                type_counts.get(TaskType.WEEKLY_MISSION, 0),
                validate=False,
            )
            self.set_data(
                "event_mission_count",
                type_counts.get(TaskType.DAILY_MISSIONS, 0),
                validate=False,
            )
            self.set_data(
                "custom_task_count", type_counts.get(TaskType.CUSTOM, 0), validate=False
            )

            logger.debug("任务统计加载完成")

        except Exception as e:
            logger.error(f"加载任务统计失败: {e}")
            raise

    async def _load_system_status(self):
        """加载系统状态"""
        try:
            # 检查游戏检测状态
            game_detected = await self._automation_service.is_game_detected()
            self.set_data("game_detected", game_detected, validate=False)

            if game_detected:
                game_info = await self._automation_service.get_game_info()
                self.set_data(
                    "game_window_title",
                    game_info.get("window_title", ""),
                    validate=False,
                )

            # 检查自动化状态
            automation_running = await self._automation_service.is_automation_running()
            self.set_data("automation_running", automation_running, validate=False)

            if automation_running:
                last_run_time = await self._automation_service.get_last_run_time()
                self.set_data("last_automation_time", last_run_time, validate=False)

            # 设置应用状态
            if automation_running:
                self.set_data("app_status", "running", validate=False)
            elif game_detected:
                self.set_data("app_status", "idle", validate=False)
            else:
                self.set_data("app_status", "paused", validate=False)

            logger.debug("系统状态加载完成")

        except Exception as e:
            logger.error(f"加载系统状态失败: {e}")
            raise

    async def _load_configuration(self):
        """加载配置信息"""
        try:
            # 加载自动化配置
            automation_config = self._config_manager.get_automation_config()
            self.set_data(
                "automation_enabled",
                automation_config.get("enabled", False),
                validate=False,
            )
            self.set_data(
                "auto_start_enabled",
                automation_config.get("auto_start", False),
                validate=False,
            )

            # 加载UI配置
            ui_config = self._config_manager.get_ui_config()
            self.set_data(
                "notification_enabled",
                ui_config.get("notifications", True),
                validate=False,
            )

            # 加载日志配置
            log_config = self._config_manager.get_log_config()
            self.set_data("log_level", log_config.get("level", "INFO"), validate=False)

            logger.debug("配置信息加载完成")

        except Exception as e:
            logger.error(f"加载配置信息失败: {e}")
            raise

    async def _load_recent_tasks(self):
        """加载最近任务"""
        try:
            # 获取最近10个任务
            recent_tasks = await self._task_service.get_recent_tasks(limit=10)

            # 转换为显示格式
            task_list = []
            for task in recent_tasks:
                task_info = {
                    "id": task.id,
                    "name": task.name,
                    "type": task.task_type.value,
                    "status": task.status.value,
                    "created_time": task.created_at,
                    "updated_time": task.updated_at,
                }
                task_list.append(task_info)

            self.set_data("recent_tasks", task_list, validate=False)

            logger.debug(f"加载了 {len(task_list)} 个最近任务")

        except Exception as e:
            logger.error(f"加载最近任务失败: {e}")
            raise

    async def _save_configuration(self):
        """保存配置信息"""
        try:
            # 保存自动化配置
            automation_config = {
                "enabled": self.get_data("automation_enabled", False),
                "auto_start": self.get_data("auto_start_enabled", False),
            }
            self._config_manager.update_automation_config(automation_config)

            # 保存UI配置
            ui_config = {"notifications": self.get_data("notification_enabled", True)}
            self._config_manager.update_ui_config(ui_config)

            # 保存日志配置
            log_config = {"level": self.get_data("log_level", "INFO")}
            self._config_manager.update_log_config(log_config)

            logger.debug("配置信息保存完成")

        except Exception as e:
            logger.error(f"保存配置信息失败: {e}")
            raise

    async def refresh_data(self):
        """刷新数据"""
        logger.info("刷新主窗口数据")
        return await self.load_data()

    def get_task_summary(self) -> Dict[str, Any]:
        """获取任务摘要

        Returns:
            任务摘要信息
        """
        return {
            "total": self.get_data("total_tasks", 0),
            "pending": self.get_data("pending_tasks", 0),
            "running": self.get_data("running_tasks", 0),
            "completed": self.get_data("completed_tasks", 0),
            "failed": self.get_data("failed_tasks", 0),
        }

    def get_type_summary(self) -> Dict[str, Any]:
        """获取类型摘要

        Returns:
            任务类型摘要信息
        """
        return {
            "daily_mission": self.get_data("daily_mission_count", 0),
            "weekly_mission": self.get_data("weekly_mission_count", 0),
            "event_mission": self.get_data("event_mission_count", 0),
            "custom_task": self.get_data("custom_task_count", 0),
        }

    def get_system_summary(self) -> Dict[str, Any]:
        """获取系统摘要

        Returns:
            系统状态摘要信息
        """
        return {
            "app_status": self.get_data("app_status", "idle"),
            "game_detected": self.get_data("game_detected", False),
            "automation_running": self.get_data("automation_running", False),
            "automation_enabled": self.get_data("automation_enabled", False),
        }
