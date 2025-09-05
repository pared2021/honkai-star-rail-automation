# -*- coding: utf-8 -*-
"""
任务执行历史MVP集成类
将TaskExecutionHistoryModel、TaskExecutionHistoryView和TaskExecutionHistoryPresenter组合在一起
"""

from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QObject, pyqtSignal
from loguru import logger

from src.adapters.task_manager_adapter import TaskManagerAdapter
from .task_execution_history_model import TaskExecutionHistoryModel
from .task_execution_history_view import TaskExecutionHistoryView
from .task_execution_history_presenter import TaskExecutionHistoryPresenter


class TaskExecutionHistoryMVP(QObject):
    """任务执行历史MVP集成类"""

    # 对外暴露的信号
    record_selected = pyqtSignal(dict)  # 记录选择
    export_requested = pyqtSignal(str, str)  # 导出请求
    cleanup_requested = pyqtSignal(int)  # 清理请求
    
    # 数据变化信号
    execution_records_updated = pyqtSignal(list)  # 执行记录更新
    execution_record_details_updated = pyqtSignal(dict)  # 执行记录详情更新
    filter_conditions_updated = pyqtSignal(dict)  # 过滤条件更新
    statistics_updated = pyqtSignal(dict)  # 统计信息更新
    
    # 操作结果信号
    data_loading_finished = pyqtSignal(bool, str)  # 数据加载完成
    export_finished = pyqtSignal(bool, str)  # 导出完成
    cleanup_finished = pyqtSignal(bool, str)  # 清理完成
    
    # 错误信号
    error_occurred = pyqtSignal(str)  # 错误发生

    def __init__(self, task_manager: TaskManagerAdapter, task_id: Optional[str] = None, parent=None):
        """初始化MVP集成类
        
        Args:
            task_manager: 任务管理器适配器
            task_id: 可选的任务ID，如果提供则只显示该任务的执行历史
            parent: 父组件
        """
        super().__init__(parent)
        
        # 创建MVP组件
        self._model = TaskExecutionHistoryModel(task_manager, task_id)
        self._view = TaskExecutionHistoryView(parent)
        self._presenter = TaskExecutionHistoryPresenter(self._model, self._view)
        
        # 连接信号
        self._connect_signals()
        
        logger.info(f"TaskExecutionHistoryMVP initialized with task_id: {task_id}")

    def _connect_signals(self):
        """连接MVP组件的信号"""
        # 连接Presenter的信号到MVP的信号
        self._presenter.record_selected.connect(self.record_selected)
        self._presenter.export_requested.connect(self.export_requested)
        self._presenter.cleanup_requested.connect(self.cleanup_requested)
        
        self._presenter.execution_records_updated.connect(self.execution_records_updated)
        self._presenter.execution_record_details_updated.connect(self.execution_record_details_updated)
        self._presenter.filter_conditions_updated.connect(self.filter_conditions_updated)
        self._presenter.statistics_updated.connect(self.statistics_updated)
        
        self._presenter.data_loading_finished.connect(self.data_loading_finished)
        self._presenter.export_finished.connect(self.export_finished)
        self._presenter.cleanup_finished.connect(self.cleanup_finished)
        
        self._presenter.error_occurred.connect(self.error_occurred)

    # 获取MVP组件实例
    def get_model(self) -> TaskExecutionHistoryModel:
        """获取Model实例"""
        return self._model

    def get_view(self) -> TaskExecutionHistoryView:
        """获取View实例"""
        return self._view

    def get_presenter(self) -> TaskExecutionHistoryPresenter:
        """获取Presenter实例"""
        return self._presenter

    # 数据管理
    def refresh_data(self):
        """刷新数据"""
        self._presenter.refresh_data()

    def get_selected_record(self) -> Optional[Dict[str, Any]]:
        """获取选中的执行记录"""
        return self._presenter.get_selected_record()

    def select_record_by_id(self, execution_id: str):
        """根据执行ID选择记录"""
        self._presenter.select_record_by_id(execution_id)

    def clear_selection(self):
        """清除选择"""
        self._presenter.clear_selection()

    def get_all_records(self) -> List[Dict[str, Any]]:
        """获取所有执行记录"""
        return self._presenter.get_all_records()

    def get_filtered_records(self) -> List[Dict[str, Any]]:
        """获取过滤后的执行记录"""
        return self._presenter.get_filtered_records()

    def get_record_by_execution_id(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """根据执行ID获取记录"""
        return self._model.get_record_by_execution_id(execution_id)

    # 过滤管理
    def get_filter_conditions(self) -> Dict[str, Any]:
        """获取过滤条件"""
        return self._presenter.get_filter_conditions()

    def set_filter_conditions(self, conditions: Dict[str, Any]):
        """设置过滤条件"""
        self._presenter.set_filter_conditions(conditions)

    def clear_filters(self):
        """清除过滤条件"""
        self._presenter.clear_filters()

    # 统计信息
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self._presenter.get_statistics()

    # 自动刷新
    def set_auto_refresh(self, enabled: bool, interval_ms: int = 30000):
        """设置自动刷新"""
        self._presenter.set_auto_refresh(enabled, interval_ms)

    # 操作控制
    def export_history(self, file_path: str, format_type: str = 'csv'):
        """导出执行历史"""
        self._presenter.export_history(file_path, format_type)

    def cleanup_old_records(self, days_before: int = 30):
        """清理旧记录"""
        self._presenter.cleanup_old_records(days_before)

    # 消息显示
    def show_message(self, title: str, message: str, is_error: bool = False):
        """显示消息"""
        self._presenter.show_message(title, message, is_error)

    # 资源清理
    def cleanup(self):
        """清理资源"""
        self._presenter.cleanup()
        logger.info("TaskExecutionHistoryMVP cleaned up")

    # 兼容性接口（用于与现有代码兼容）
    def load_execution_history(self):
        """加载执行历史（兼容性接口）"""
        self._presenter.load_execution_history()

    def apply_filters(self):
        """应用过滤条件（兼容性接口）"""
        self._presenter.apply_filters()

    def show_execution_details(self, record: Dict[str, Any]):
        """显示执行详情（兼容性接口）"""
        self._presenter.show_execution_details(record)

    def clear_execution_details(self):
        """清空执行详情（兼容性接口）"""
        self._presenter.clear_execution_details()

    # 对话框相关方法（兼容性接口）
    def exec(self) -> int:
        """执行对话框（兼容性接口）"""
        if hasattr(self._view, 'exec'):
            return self._view.exec()
        return 0

    def show(self):
        """显示对话框（兼容性接口）"""
        self._view.show()

    def hide(self):
        """隐藏对话框（兼容性接口）"""
        self._view.hide()

    def close(self) -> bool:
        """关闭对话框（兼容性接口）"""
        return self._view.close()

    def setWindowTitle(self, title: str):
        """设置窗口标题（兼容性接口）"""
        self._view.setWindowTitle(title)

    def resize(self, width: int, height: int):
        """调整窗口大小（兼容性接口）"""
        self._view.resize(width, height)

    def setModal(self, modal: bool):
        """设置模态（兼容性接口）"""
        if hasattr(self._view, 'setModal'):
            self._view.setModal(modal)

    # 属性访问（兼容性接口）
    @property
    def widget(self):
        """获取主要组件（兼容性接口）"""
        return self._view

    @property
    def dialog(self):
        """获取对话框组件（兼容性接口）"""
        return self._view

    @property
    def view(self):
        """获取视图组件"""
        return self._view

    @property
    def model(self):
        """获取模型组件"""
        return self._model

    @property
    def presenter(self):
        """获取展示器组件"""
        return self._presenter