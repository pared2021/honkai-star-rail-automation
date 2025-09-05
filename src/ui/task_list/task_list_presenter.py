"""任务列表Presenter层

该模块定义了任务列表的Presenter层，负责协调Model和View之间的交互。
"""

from typing import Dict, List, Optional, Any
from PyQt6.QtCore import QObject, pyqtSignal

from src.ui.task_list.task_list_model import TaskListModel
from src.ui.task_list.task_list_view import TaskListView
from src.models.task_models import Task, TaskStatus, TaskType, TaskPriority
from src.utils.logger import logger


class TaskListPresenter(QObject):
    """任务列表Presenter层
    
    负责协调TaskListModel和TaskListView，处理用户交互和业务逻辑。
    """
    
    # 业务信号
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
    
    def __init__(self, model: TaskListModel, view: TaskListView, parent=None):
        super().__init__(parent)
        
        self.model = model
        self.view = view
        
        # 连接信号
        self._connect_view_signals()
        self._connect_model_signals()
        
        # 初始化数据
        self._initialize_data()
        
        logger.info("任务列表Presenter初始化完成")
    
    def _connect_view_signals(self):
        """连接View信号"""
        # 用户交互信号
        self.view.task_selected.connect(self._on_task_selected)
        self.view.task_edit_requested.connect(self._on_task_edit_requested)
        self.view.task_delete_requested.connect(self._on_task_delete_requested)
        self.view.task_start_requested.connect(self._on_task_start_requested)
        self.view.task_stop_requested.connect(self._on_task_stop_requested)
        self.view.task_copy_requested.connect(self._on_task_copy_requested)
        self.view.refresh_requested.connect(self._on_refresh_requested)
        self.view.filter_changed.connect(self._on_filter_changed)
        self.view.execution_history_requested.connect(self._on_execution_history_requested)
    
    def _connect_model_signals(self):
        """连接Model信号"""
        # 数据变化信号
        self.model.tasks_updated.connect(self._on_tasks_updated)
        self.model.task_added.connect(self._on_task_added)
        self.model.task_updated.connect(self._on_task_updated)
        self.model.task_removed.connect(self._on_task_removed)
        self.model.task_status_changed.connect(self._on_task_status_changed)
        self.model.task_progress_updated.connect(self._on_task_progress_updated)
        
        # 过滤和统计信号
        self.model.filters_changed.connect(self._on_filters_changed)
        self.model.statistics_updated.connect(self._on_statistics_updated)
        
        # 操作结果信号
        self.model.task_operation_result.connect(self._on_task_operation_result)
        self.model.refresh_completed.connect(self._on_refresh_completed)
        
        # 错误信号
        self.model.error_occurred.connect(self._on_model_error)
    
    def _initialize_data(self):
        """初始化数据"""
        try:
            # 刷新任务列表
            self.refresh_tasks()
            
            # 启用自动刷新
            self.model.set_auto_refresh(True, 5000)
            
        except Exception as e:
            logger.error(f"初始化任务列表数据失败: {e}")
            self.error_occurred.emit("initialization", str(e))
    
    # View信号处理方法
    def _on_task_selected(self, task_id: str):
        """处理任务选择"""
        try:
            self.model.set_selected_task_id(task_id)
            self.task_selected.emit(task_id)
            logger.debug(f"任务已选择: {task_id}")
        except Exception as e:
            logger.error(f"处理任务选择失败: {e}")
            self.error_occurred.emit("task_selection", str(e))
    
    def _on_task_edit_requested(self, task_id: str):
        """处理编辑任务请求"""
        try:
            self.task_edit_requested.emit(task_id)
            logger.debug(f"编辑任务请求: {task_id}")
        except Exception as e:
            logger.error(f"处理编辑任务请求失败: {e}")
            self.error_occurred.emit("edit_request", str(e))
    
    def _on_task_delete_requested(self, task_id: str):
        """处理删除任务请求"""
        try:
            self.model.delete_task(task_id)
            self.task_delete_requested.emit(task_id)
            logger.debug(f"删除任务请求: {task_id}")
        except Exception as e:
            logger.error(f"处理删除任务请求失败: {e}")
            self.error_occurred.emit("delete_request", str(e))
    
    def _on_task_start_requested(self, task_id: str):
        """处理启动任务请求"""
        try:
            self.model.start_task(task_id)
            self.task_start_requested.emit(task_id)
            logger.debug(f"启动任务请求: {task_id}")
        except Exception as e:
            logger.error(f"处理启动任务请求失败: {e}")
            self.error_occurred.emit("start_request", str(e))
    
    def _on_task_stop_requested(self, task_id: str):
        """处理停止任务请求"""
        try:
            self.model.stop_task(task_id)
            self.task_stop_requested.emit(task_id)
            logger.debug(f"停止任务请求: {task_id}")
        except Exception as e:
            logger.error(f"处理停止任务请求失败: {e}")
            self.error_occurred.emit("stop_request", str(e))
    
    def _on_task_copy_requested(self, task_id: str):
        """处理复制任务请求"""
        try:
            self.model.copy_task(task_id)
            self.task_copy_requested.emit(task_id)
            logger.debug(f"复制任务请求: {task_id}")
        except Exception as e:
            logger.error(f"处理复制任务请求失败: {e}")
            self.error_occurred.emit("copy_request", str(e))
    
    def _on_refresh_requested(self):
        """处理刷新请求"""
        try:
            self.refresh_tasks()
            logger.debug("刷新任务列表请求")
        except Exception as e:
            logger.error(f"处理刷新请求失败: {e}")
            self.error_occurred.emit("refresh_request", str(e))
    
    def _on_filter_changed(self, filters: Dict[str, Any]):
        """处理过滤条件变化"""
        try:
            self.model.set_filters(filters)
            logger.debug(f"过滤条件变化: {filters}")
        except Exception as e:
            logger.error(f"处理过滤条件变化失败: {e}")
            self.error_occurred.emit("filter_change", str(e))
    
    def _on_execution_history_requested(self, task_id: str):
        """处理查看执行历史请求"""
        try:
            self.view.show_execution_history(task_id)
            self.execution_history_requested.emit(task_id)
            logger.debug(f"查看执行历史请求: {task_id}")
        except Exception as e:
            logger.error(f"处理查看执行历史请求失败: {e}")
            self.error_occurred.emit("history_request", str(e))
    
    # Model信号处理方法
    def _on_tasks_updated(self, tasks: List[Task]):
        """处理任务列表更新"""
        try:
            self.view.display_tasks(tasks)
            self.tasks_updated.emit(tasks)
            logger.debug(f"任务列表已更新，共 {len(tasks)} 个任务")
        except Exception as e:
            logger.error(f"处理任务列表更新失败: {e}")
            self.error_occurred.emit("tasks_update", str(e))
    
    def _on_task_added(self, task: Task):
        """处理任务添加"""
        try:
            self.task_added.emit(task)
            logger.debug(f"任务已添加: {task.task_id}")
        except Exception as e:
            logger.error(f"处理任务添加失败: {e}")
            self.error_occurred.emit("task_add", str(e))
    
    def _on_task_updated(self, task: Task):
        """处理任务更新"""
        try:
            self.task_updated.emit(task)
            logger.debug(f"任务已更新: {task.task_id}")
        except Exception as e:
            logger.error(f"处理任务更新失败: {e}")
            self.error_occurred.emit("task_update", str(e))
    
    def _on_task_removed(self, task_id: str):
        """处理任务删除"""
        try:
            self.task_removed.emit(task_id)
            logger.debug(f"任务已删除: {task_id}")
        except Exception as e:
            logger.error(f"处理任务删除失败: {e}")
            self.error_occurred.emit("task_remove", str(e))
    
    def _on_task_status_changed(self, task_id: str, status: TaskStatus):
        """处理任务状态变化"""
        try:
            self.view.update_task_status(task_id, status)
            self.task_status_changed.emit(task_id, status)
            logger.debug(f"任务状态已变化: {task_id} -> {status.value}")
        except Exception as e:
            logger.error(f"处理任务状态变化失败: {e}")
            self.error_occurred.emit("status_change", str(e))
    
    def _on_task_progress_updated(self, task_id: str, progress: int, message: str):
        """处理任务进度更新"""
        try:
            self.view.update_task_progress(task_id, progress, message)
            self.task_progress_updated.emit(task_id, progress, message)
            logger.debug(f"任务进度已更新: {task_id} -> {progress}%")
        except Exception as e:
            logger.error(f"处理任务进度更新失败: {e}")
            self.error_occurred.emit("progress_update", str(e))
    
    def _on_filters_changed(self, filters: Dict[str, Any]):
        """处理过滤条件变化"""
        try:
            # 过滤条件已在Model中处理，这里可以做额外的UI更新
            logger.debug(f"过滤条件已变化: {filters}")
        except Exception as e:
            logger.error(f"处理过滤条件变化失败: {e}")
            self.error_occurred.emit("filters_change", str(e))
    
    def _on_statistics_updated(self, statistics: Dict[str, int]):
        """处理统计信息更新"""
        try:
            self.view.update_statistics(statistics)
            logger.debug(f"统计信息已更新: {statistics}")
        except Exception as e:
            logger.error(f"处理统计信息更新失败: {e}")
            self.error_occurred.emit("statistics_update", str(e))
    
    def _on_task_operation_result(self, operation: str, success: bool, message: str):
        """处理任务操作结果"""
        try:
            if success:
                self.view.show_message("操作成功", message, "info")
            else:
                self.view.show_message("操作失败", message, "error")
            
            self.task_operation_result.emit(operation, success, message)
            logger.debug(f"任务操作结果: {operation} -> {'成功' if success else '失败'}: {message}")
        except Exception as e:
            logger.error(f"处理任务操作结果失败: {e}")
            self.error_occurred.emit("operation_result", str(e))
    
    def _on_refresh_completed(self, success: bool, message: str):
        """处理刷新完成"""
        try:
            self.view.set_loading_state(False)
            
            if not success:
                self.view.show_message("刷新失败", message, "error")
            
            self.refresh_completed.emit(success, message)
            logger.debug(f"刷新完成: {'成功' if success else '失败'}: {message}")
        except Exception as e:
            logger.error(f"处理刷新完成失败: {e}")
            self.error_occurred.emit("refresh_complete", str(e))
    
    def _on_model_error(self, error_type: str, message: str):
        """处理Model错误"""
        try:
            self.view.show_message("错误", f"{error_type}: {message}", "error")
            self.error_occurred.emit(error_type, message)
            logger.error(f"Model错误: {error_type} - {message}")
        except Exception as e:
            logger.error(f"处理Model错误失败: {e}")
    
    # 公共接口方法
    def refresh_tasks(self, user_id: str = "default_user"):
        """刷新任务列表"""
        try:
            self.view.set_loading_state(True)
            self.model.refresh_tasks(user_id)
            logger.info("开始刷新任务列表")
        except Exception as e:
            logger.error(f"刷新任务列表失败: {e}")
            self.view.set_loading_state(False)
            self.error_occurred.emit("refresh", str(e))
    
    def get_selected_task_id(self) -> Optional[str]:
        """获取选中的任务ID"""
        return self.model.get_selected_task_id()
    
    def get_selected_task(self) -> Optional[Task]:
        """获取选中的任务"""
        return self.model.get_selected_task()
    
    def select_task(self, task_id: str):
        """选择指定任务"""
        try:
            self.view.select_task(task_id)
            self.model.set_selected_task_id(task_id)
            logger.debug(f"选择任务: {task_id}")
        except Exception as e:
            logger.error(f"选择任务失败: {e}")
            self.error_occurred.emit("select_task", str(e))
    
    def clear_selection(self):
        """清除选择"""
        try:
            self.view.clear_selection()
            self.model.set_selected_task_id(None)
            logger.debug("清除任务选择")
        except Exception as e:
            logger.error(f"清除选择失败: {e}")
            self.error_occurred.emit("clear_selection", str(e))
    
    def get_current_filters(self) -> Dict[str, Any]:
        """获取当前过滤条件"""
        return self.model.get_filters()
    
    def set_filters(self, filters: Dict[str, Any]):
        """设置过滤条件"""
        try:
            self.view.apply_filters(filters)
            self.model.set_filters(filters)
            logger.debug(f"设置过滤条件: {filters}")
        except Exception as e:
            logger.error(f"设置过滤条件失败: {e}")
            self.error_occurred.emit("set_filters", str(e))
    
    def clear_filters(self):
        """清除过滤条件"""
        try:
            self.view.clear_filters()
            self.model.clear_filters()
            logger.debug("清除过滤条件")
        except Exception as e:
            logger.error(f"清除过滤条件失败: {e}")
            self.error_occurred.emit("clear_filters", str(e))
    
    def get_statistics(self) -> Dict[str, int]:
        """获取统计信息"""
        return self.model.get_statistics()
    
    def set_auto_refresh(self, enabled: bool, interval: int = 5000):
        """设置自动刷新"""
        try:
            self.model.set_auto_refresh(enabled, interval)
            logger.info(f"自动刷新{'启用' if enabled else '禁用'}，间隔: {interval}ms")
        except Exception as e:
            logger.error(f"设置自动刷新失败: {e}")
            self.error_occurred.emit("auto_refresh", str(e))
    
    def enable_operations(self, enabled: bool):
        """启用/禁用操作"""
        try:
            self.view.enable_operations(enabled)
            logger.debug(f"操作{'启用' if enabled else '禁用'}")
        except Exception as e:
            logger.error(f"启用/禁用操作失败: {e}")
            self.error_occurred.emit("enable_operations", str(e))
    
    def update_task_status(self, task_id: str, status: TaskStatus):
        """更新任务状态"""
        try:
            self.model.update_task_status(task_id, status)
            logger.debug(f"更新任务状态: {task_id} -> {status.value}")
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
            self.error_occurred.emit("update_status", str(e))
    
    def update_task_progress(self, task_id: str, progress: int, message: str = ""):
        """更新任务进度"""
        try:
            self.model.update_task_progress(task_id, progress, message)
            logger.debug(f"更新任务进度: {task_id} -> {progress}%")
        except Exception as e:
            logger.error(f"更新任务进度失败: {e}")
            self.error_occurred.emit("update_progress", str(e))
    
    def get_all_tasks(self) -> List[Task]:
        """获取所有任务"""
        return self.model.get_all_tasks()
    
    def get_filtered_tasks(self) -> List[Task]:
        """获取过滤后的任务"""
        return self.model.get_filtered_tasks()
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """根据ID获取任务"""
        return self.model.get_task_by_id(task_id)
    
    def show_message(self, title: str, message: str, msg_type: str = "info"):
        """显示消息"""
        self.view.show_message(title, message, msg_type)
    
    # 清理资源
    def cleanup(self):
        """清理资源"""
        try:
            self.model.cleanup()
            logger.info("任务列表Presenter资源清理完成")
        except Exception as e:
            logger.error(f"清理任务列表Presenter资源失败: {e}")