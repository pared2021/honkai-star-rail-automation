"""任务列表展示器

实现MVP模式中的Presenter层，处理任务列表的业务逻辑和数据绑定。
"""

import logging
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QTimer, pyqtSlot

from ..application.task_application_service import TaskApplicationService
from ..core.sync_adapter import SyncAdapter
from ..models.task_models import Task, TaskConfig, TaskPriority, TaskStatus, TaskType
from ..ui.mvp.base_model import BaseModel
from ..ui.mvp.base_presenter import BasePresenter
from ..ui.mvp.base_view import BaseView

logger = logging.getLogger(__name__)


class TaskListModel(BaseModel):
    """任务列表数据模型"""

    def __init__(
        self, task_service: TaskApplicationService, user_id: str = "default_user"
    ):
        super().__init__()
        self.task_service = task_service
        self.user_id = user_id
        self.tasks: List[Task] = []
        self.filters: Dict[str, Any] = {}
        self.selected_task_id: Optional[str] = None

    async def load_data(self) -> bool:
        """加载任务数据"""
        try:
            tasks = await self.task_service.get_recent_tasks(
                user_id=self.user_id, limit=1000
            )
            self.set_data("tasks", tasks)
            return True
        except Exception as e:
            logger.error(f"加载任务数据失败: {e}")
            return False

    def get_tasks(self) -> List[Task]:
        """获取任务列表"""
        return self.get_data("tasks", [])

    def set_filters(self, filters: Dict[str, Any]):
        """设置过滤条件"""
        self.set_data("filters", filters)

    def get_filters(self) -> Dict[str, Any]:
        """获取过滤条件"""
        return self.get_data("filters", {})

    def set_selected_task(self, task_id: Optional[str]):
        """设置选中的任务"""
        self.set_data("selected_task_id", task_id)

    def get_selected_task(self) -> Optional[str]:
        """获取选中的任务ID"""
        return self.get_data("selected_task_id")


class TaskListView(BaseView):
    """任务列表视图接口

    定义任务列表视图的所有界面操作方法。
    """

    def setup_ui(self):
        """设置用户界面"""
        # 子类实现具体的UI设置
        pass

    def connect_signals(self):
        """连接信号槽"""
        # 子类实现具体的信号连接
        pass

    def _update_field_display(self, field_name: str, value: Any):
        """更新特定字段的显示"""
        if field_name == "tasks":
            self.display_tasks(value)
        elif field_name == "selected_task_id":
            if value:
                self.select_task(value)
            else:
                self.clear_selection()
        elif field_name == "filters":
            self.apply_filters(value)

    # 抽象方法，由具体实现类定义
    def display_tasks(self, tasks: List[Task]):
        """显示任务列表"""
        raise NotImplementedError

    def select_task(self, task_id: str):
        """选择任务"""
        raise NotImplementedError

    def clear_selection(self):
        """清除选择"""
        raise NotImplementedError

    def apply_filters(self, filters: Dict[str, Any]):
        """应用过滤条件"""
        raise NotImplementedError

    def set_loading_state(self, loading: bool):
        """设置加载状态"""
        self.set_loading(loading)

    def show_error_dialog(self, title: str, message: str):
        """显示错误对话框"""
        self.show_error(message, title)


class TaskListPresenter(BasePresenter):
    """任务列表展示器

    MVP模式中的Presenter层，负责：
    1. 处理视图事件和用户交互
    2. 调用应用服务层执行业务逻辑
    3. 更新视图显示状态
    4. 管理数据流和状态同步
    """

    def __init__(
        self,
        view: TaskListView,
        task_service: TaskApplicationService,
        user_id: str = "default_user",
    ):
        """初始化展示器

        Args:
            view: 任务列表视图
            task_service: 任务应用服务
            user_id: 用户ID
        """
        model = TaskListModel(task_service, user_id)
        super().__init__(model, view)

        self.task_service = task_service
        self.user_id = user_id

        # 自动刷新定时器
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._auto_refresh)

        logger.info(f"TaskListPresenter 初始化完成，用户ID: {user_id}")

    def _register_action_handlers(self):
        """注册动作处理器"""
        self.register_action_handler("task_selected", self._on_task_selected)
        self.register_action_handler(
            "task_edit_requested", self._on_task_edit_requested
        )
        self.register_action_handler(
            "task_delete_requested", self._on_task_delete_requested
        )
        self.register_action_handler(
            "task_start_requested", self._on_task_start_requested
        )
        self.register_action_handler(
            "task_stop_requested", self._on_task_stop_requested
        )
        self.register_action_handler(
            "task_copy_requested", self._on_task_copy_requested
        )
        self.register_action_handler("filter_changed", self._on_filter_changed)
        self.register_action_handler("refresh_requested", self.refresh_tasks)

    def _on_view_initialized(self):
        """视图初始化完成后的处理"""
        self._initialize_filter_options()

    def _initialize_filter_options(self):
        """初始化过滤选项"""
        try:
            # 设置过滤选项
            status_options = list(TaskStatus)
            type_options = list(TaskType)
            priority_options = list(TaskPriority)

            if hasattr(self._view, "set_filter_options"):
                self._view.set_filter_options(
                    status_options, type_options, priority_options
                )

            logger.debug("过滤选项初始化完成")

        except Exception as e:
            logger.error(f"初始化过滤选项失败: {e}")

    @pyqtSlot()
    def refresh_tasks(self):
        """刷新任务列表"""
        try:
            logger.debug("开始刷新任务列表")

            # 使用基类的异步加载机制
            self._load_initial_data()

        except Exception as e:
            logger.error(f"刷新任务列表异常: {e}")
            self._view.show_error(f"刷新任务列表失败：{str(e)}")

    def set_auto_refresh(self, enabled: bool, interval: int = 5000):
        """设置自动刷新

        Args:
            enabled: 是否启用自动刷新
            interval: 刷新间隔（毫秒）
        """
        if enabled:
            self.refresh_timer.start(interval)
            logger.info(f"自动刷新已启用，间隔: {interval}ms")
        else:
            self.refresh_timer.stop()
            logger.info("自动刷新已禁用")

    def _auto_refresh(self):
        """自动刷新回调"""
        self.refresh_tasks()

    def _on_task_selected(self, task_id: str):
        """处理任务选择"""
        try:
            self._model.set_selected_task(task_id)

            # 获取并显示任务详情
            tasks = self._model.get_tasks()
            task = next((t for t in tasks if t.id == task_id), None)

            if hasattr(self._view, "show_task_details"):
                self._view.show_task_details(task)

            if hasattr(self._view, "update_button_states"):
                self._view.update_button_states(True, task)

            logger.debug(f"任务已选择: {task_id}")

        except Exception as e:
            logger.error(f"选择任务失败: {e}")

    def _on_task_edit_requested(self, task_id: str):
        """处理任务编辑请求"""
        logger.debug(f"请求编辑任务: {task_id}")
        # 具体实现由子类或外部处理

    def _on_task_delete_requested(self, task_id: str):
        """处理任务删除请求"""
        try:
            logger.debug(f"请求删除任务: {task_id}")

            async def delete_task_callback():
                return await self.task_service.delete_task(task_id)

            def on_success(result):
                logger.info(f"任务删除成功: {task_id}")
                self.refresh_tasks()

            def on_error(error: Exception):
                logger.error(f"删除任务失败: {error}")
                self._view.show_error(f"删除任务失败：{str(error)}")

            # 异步执行删除
            self._sync_adapter.run_async(
                delete_task_callback(), callback=on_success, error_callback=on_error
            )

        except Exception as e:
            logger.error(f"删除任务异常: {e}")
            self._view.show_error(f"删除任务失败：{str(e)}")

    def _on_task_start_requested(self, task_id: str):
        """处理任务启动请求"""
        try:
            logger.debug(f"请求启动任务: {task_id}")

            async def start_task_callback():
                return await self.task_service.start_task(task_id)

            def on_success(result):
                logger.info(f"任务启动成功: {task_id}")
                self.refresh_tasks()

            def on_error(error: Exception):
                logger.error(f"启动任务失败: {error}")
                self._view.show_error(f"启动任务失败：{str(error)}")

            # 异步执行启动
            self._sync_adapter.run_async(
                start_task_callback(), callback=on_success, error_callback=on_error
            )

        except Exception as e:
            logger.error(f"启动任务异常: {e}")
            self._view.show_error(f"启动任务失败：{str(e)}")

    def _on_task_stop_requested(self, task_id: str):
        """处理任务停止请求"""
        try:
            logger.debug(f"请求停止任务: {task_id}")

            async def stop_task_callback():
                return await self.task_service.stop_task(task_id)

            def on_success(result):
                logger.info(f"任务停止成功: {task_id}")
                self.refresh_tasks()

            def on_error(error: Exception):
                logger.error(f"停止任务失败: {error}")
                self._view.show_error(f"停止任务失败：{str(error)}")

            # 异步执行停止
            self._sync_adapter.run_async(
                stop_task_callback(), callback=on_success, error_callback=on_error
            )

        except Exception as e:
            logger.error(f"停止任务异常: {e}")
            self._view.show_error(f"停止任务失败：{str(e)}")

    def _on_task_copy_requested(self, task_id: str):
        """处理任务复制请求"""
        logger.debug(f"请求复制任务: {task_id}")
        # 具体实现由子类或外部处理

    def _on_filter_changed(self, filters: Dict[str, Any]):
        """处理过滤条件变化"""
        try:
            logger.debug(f"过滤条件变化: {filters}")
            self._model.set_filters(filters)
            self._apply_current_filters()

        except Exception as e:
            logger.error(f"应用过滤条件失败: {e}")

    def _apply_current_filters(self):
        """应用当前过滤条件"""
        try:
            tasks = self._model.get_tasks()
            filters = self._model.get_filters()

            # 应用过滤逻辑
            filtered_tasks = self._filter_tasks(tasks, filters)

            # 更新视图显示
            self._view.display_tasks(filtered_tasks)

            # 更新统计信息
            self._update_statistics(filtered_tasks)

        except Exception as e:
            logger.error(f"应用过滤条件失败: {e}")

    def _filter_tasks(self, tasks: List[Task], filters: Dict[str, Any]) -> List[Task]:
        """过滤任务列表"""
        if not filters:
            return tasks

        filtered = tasks

        # 状态过滤
        if "status" in filters and filters["status"]:
            filtered = [t for t in filtered if t.status == filters["status"]]

        # 类型过滤
        if "type" in filters and filters["type"]:
            filtered = [t for t in filtered if t.type == filters["type"]]

        # 优先级过滤
        if "priority" in filters and filters["priority"]:
            filtered = [t for t in filtered if t.priority == filters["priority"]]

        # 关键词搜索
        if "keyword" in filters and filters["keyword"]:
            keyword = filters["keyword"].lower()
            filtered = [
                t
                for t in filtered
                if keyword in t.name.lower() or keyword in t.description.lower()
            ]

        return filtered

    def _update_statistics(self, tasks: List[Task]):
        """更新统计信息"""
        try:
            stats = {
                "total": len(tasks),
                "pending": len([t for t in tasks if t.status == TaskStatus.PENDING]),
                "running": len([t for t in tasks if t.status == TaskStatus.RUNNING]),
                "completed": len(
                    [t for t in tasks if t.status == TaskStatus.COMPLETED]
                ),
                "failed": len([t for t in tasks if t.status == TaskStatus.FAILED]),
            }

            if hasattr(self._view, "update_statistics"):
                self._view.update_statistics(stats)

        except Exception as e:
            logger.error(f"更新统计信息失败: {e}")
