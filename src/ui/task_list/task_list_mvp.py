"""任务列表MVP集成

该模块定义了任务列表的MVP集成类，将Model、View和Presenter组合在一起。
"""

from typing import Dict, List, Optional, Any
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QWidget

from src.ui.task_list.task_list_model import TaskListModel
from src.ui.task_list.task_list_view import TaskListView
from src.ui.task_list.task_list_presenter import TaskListPresenter
from src.models.task_models import Task, TaskStatus, TaskType, TaskPriority
from src.utils.logger import logger


class TaskListMVP(QObject):
    """任务列表MVP集成类
    
    将TaskListModel、TaskListView和TaskListPresenter组合在一起，
    提供完整的任务列表功能。
    """
    
    # 对外暴露的信号
    task_selected = pyqtSignal(str)  # 任务选择
    task_edit_requested = pyqtSignal(str)  # 编辑任务请求
    task_delete_requested = pyqtSignal(str)  # 删除任务请求
    task_start_requested = pyqtSignal(str)  # 启动任务请求
    task_stop_requested = pyqtSignal(str)  # 停止任务请求
    task_copy_requested = pyqtSignal(str)  # 复制任务请求
    execution_history_requested = pyqtSignal(str)  # 查看执行历史请求
    
    # 数据变化信号
    tasks_updated = pyqtSignal(list)  # 任务列表更新
    task_added = pyqtSignal(object)  # 任务添加
    task_updated = pyqtSignal(object)  # 任务更新
    task_removed = pyqtSignal(str)  # 任务删除
    task_status_changed = pyqtSignal(str, object)  # 任务状态变化
    task_progress_updated = pyqtSignal(str, int, str)  # 任务进度更新
    
    # 操作结果信号
    task_operation_result = pyqtSignal(str, bool, str)  # 任务操作结果
    refresh_completed = pyqtSignal(bool, str)  # 刷新完成
    
    # 错误信号
    error_occurred = pyqtSignal(str, str)  # 错误发生
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 创建MVP组件
        self.model = TaskListModel()
        self.view = TaskListView()
        self.presenter = TaskListPresenter(self.model, self.view)
        
        # 连接信号
        self._connect_signals()
        
        logger.info("任务列表MVP初始化完成")
    
    def _connect_signals(self):
        """连接信号"""
        # 连接Presenter信号到外部
        self.presenter.task_selected.connect(self.task_selected)
        self.presenter.task_edit_requested.connect(self.task_edit_requested)
        self.presenter.task_delete_requested.connect(self.task_delete_requested)
        self.presenter.task_start_requested.connect(self.task_start_requested)
        self.presenter.task_stop_requested.connect(self.task_stop_requested)
        self.presenter.task_copy_requested.connect(self.task_copy_requested)
        self.presenter.execution_history_requested.connect(self.execution_history_requested)
        
        # 数据变化信号
        self.presenter.tasks_updated.connect(self.tasks_updated)
        self.presenter.task_added.connect(self.task_added)
        self.presenter.task_updated.connect(self.task_updated)
        self.presenter.task_removed.connect(self.task_removed)
        self.presenter.task_status_changed.connect(self.task_status_changed)
        self.presenter.task_progress_updated.connect(self.task_progress_updated)
        
        # 操作结果信号
        self.presenter.task_operation_result.connect(self.task_operation_result)
        self.presenter.refresh_completed.connect(self.refresh_completed)
        
        # 错误信号
        self.presenter.error_occurred.connect(self.error_occurred)
    
    def get_widget(self) -> QWidget:
        """获取View组件"""
        return self.view
    
    def get_view(self) -> TaskListView:
        """获取View实例"""
        return self.view
    
    def get_model(self) -> TaskListModel:
        """获取Model实例"""
        return self.model
    
    def get_presenter(self) -> TaskListPresenter:
        """获取Presenter实例"""
        return self.presenter
    
    # 任务管理接口
    def refresh_tasks(self, user_id: str = "default_user"):
        """刷新任务列表"""
        self.presenter.refresh_tasks(user_id)
    
    def get_selected_task_id(self) -> Optional[str]:
        """获取选中的任务ID"""
        return self.presenter.get_selected_task_id()
    
    def get_selected_task(self) -> Optional[Task]:
        """获取选中的任务"""
        return self.presenter.get_selected_task()
    
    def select_task(self, task_id: str):
        """选择指定任务"""
        self.presenter.select_task(task_id)
    
    def clear_selection(self):
        """清除选择"""
        self.presenter.clear_selection()
    
    def get_all_tasks(self) -> List[Task]:
        """获取所有任务"""
        return self.presenter.get_all_tasks()
    
    def get_filtered_tasks(self) -> List[Task]:
        """获取过滤后的任务"""
        return self.presenter.get_filtered_tasks()
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """根据ID获取任务"""
        return self.presenter.get_task_by_id(task_id)
    
    # 过滤管理接口
    def get_current_filters(self) -> Dict[str, Any]:
        """获取当前过滤条件"""
        return self.presenter.get_current_filters()
    
    def set_filters(self, filters: Dict[str, Any]):
        """设置过滤条件"""
        self.presenter.set_filters(filters)
    
    def clear_filters(self):
        """清除过滤条件"""
        self.presenter.clear_filters()
    
    # 统计信息接口
    def get_statistics(self) -> Dict[str, int]:
        """获取统计信息"""
        return self.presenter.get_statistics()
    
    # 自动刷新接口
    def set_auto_refresh(self, enabled: bool, interval: int = 5000):
        """设置自动刷新"""
        self.presenter.set_auto_refresh(enabled, interval)
    
    # 操作控制接口
    def enable_operations(self, enabled: bool):
        """启用/禁用操作"""
        self.presenter.enable_operations(enabled)
    
    # 任务状态更新接口
    def update_task_status(self, task_id: str, status: TaskStatus):
        """更新任务状态"""
        self.presenter.update_task_status(task_id, status)
    
    def update_task_progress(self, task_id: str, progress: int, message: str = ""):
        """更新任务进度"""
        self.presenter.update_task_progress(task_id, progress, message)
    
    # 消息显示接口
    def show_message(self, title: str, message: str, msg_type: str = "info"):
        """显示消息"""
        self.presenter.show_message(title, message, msg_type)
    
    # 兼容性接口（为了与现有代码兼容）
    def display_tasks(self, tasks: List[Task]):
        """显示任务列表（兼容接口）"""
        self.view.display_tasks(tasks)
    
    def show_task_details(self, task: Optional[Task]):
        """显示任务详情（兼容接口）"""
        self.view.show_task_details(task)
    
    def update_statistics(self, statistics: Dict[str, int]):
        """更新统计信息（兼容接口）"""
        self.view.update_statistics(statistics)
    
    def set_loading_state(self, loading: bool):
        """设置加载状态（兼容接口）"""
        self.view.set_loading_state(loading)
    
    def show_error_dialog(self, title: str, message: str):
        """显示错误对话框（兼容接口）"""
        self.view.show_message(title, message, "error")
    
    def show_confirmation_dialog(self, title: str, message: str) -> bool:
        """显示确认对话框（兼容接口）"""
        return self.view.show_confirmation_dialog(title, message)
    
    def show_context_menu(self, position):
        """显示上下文菜单（兼容接口）"""
        self.view.show_context_menu(position)
    
    def show_execution_history(self, task_id: str):
        """显示执行历史（兼容接口）"""
        self.view.show_execution_history(task_id)
    
    def apply_filters(self, filters: Dict[str, Any]):
        """应用过滤条件（兼容接口）"""
        self.presenter.set_filters(filters)
    
    def get_task_progress(self, task_id: str) -> int:
        """获取任务进度（兼容接口）"""
        task = self.get_task_by_id(task_id)
        if task and hasattr(task, 'progress'):
            return task.progress
        return 0
    
    # 清理资源
    def cleanup(self):
        """清理资源"""
        try:
            self.presenter.cleanup()
            logger.info("任务列表MVP资源清理完成")
        except Exception as e:
            logger.error(f"清理任务列表MVP资源失败: {e}")
    
    def __del__(self):
        """析构函数"""
        self.cleanup()