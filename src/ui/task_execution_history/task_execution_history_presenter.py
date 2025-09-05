# -*- coding: utf-8 -*-
"""
任务执行历史Presenter层
负责协调Model和View，处理用户交互和业务逻辑
"""

from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QObject, pyqtSignal
from loguru import logger

from .task_execution_history_model import TaskExecutionHistoryModel
from .task_execution_history_view import TaskExecutionHistoryView


class TaskExecutionHistoryPresenter(QObject):
    """任务执行历史Presenter"""

    # 业务信号 - 对外暴露
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

    def __init__(self, model: TaskExecutionHistoryModel, view: TaskExecutionHistoryView):
        """初始化Presenter
        
        Args:
            model: 任务执行历史Model
            view: 任务执行历史View
        """
        super().__init__()
        self.model = model
        self.view = view
        
        self._connect_view_signals()
        self._connect_model_signals()
        
        # 初始化数据
        self._initialize_data()
        
        logger.info("TaskExecutionHistoryPresenter initialized")

    def _connect_view_signals(self):
        """连接View信号"""
        # 用户交互信号
        self.view.filter_changed.connect(self._handle_filter_changed)
        self.view.record_selected.connect(self._handle_record_selected)
        self.view.refresh_requested.connect(self._handle_refresh_requested)
        self.view.export_requested.connect(self._handle_export_requested)
        self.view.cleanup_requested.connect(self._handle_cleanup_requested)

    def _connect_model_signals(self):
        """连接Model信号"""
        # 数据变化信号
        self.model.execution_records_updated.connect(self._handle_execution_records_updated)
        self.model.execution_record_selected.connect(self._handle_execution_record_selected)
        self.model.execution_record_details_updated.connect(self._handle_execution_record_details_updated)
        self.model.filter_conditions_updated.connect(self._handle_filter_conditions_updated)
        self.model.statistics_updated.connect(self._handle_statistics_updated)
        
        # 操作结果信号
        self.model.data_loading_finished.connect(self._handle_data_loading_finished)
        self.model.export_finished.connect(self._handle_export_finished)
        self.model.cleanup_finished.connect(self._handle_cleanup_finished)
        
        # 错误信号
        self.model.error_occurred.connect(self._handle_model_error)

    def _initialize_data(self):
        """初始化数据"""
        # 刷新执行历史数据
        self.refresh_data()
        
        # 设置自动刷新
        self.set_auto_refresh(True)

    # View事件处理方法
    def _handle_filter_changed(self, conditions: Dict[str, Any]):
        """处理过滤条件变化"""
        logger.debug(f"Filter conditions changed: {conditions}")
        self.model.set_filter_conditions(conditions)

    def _handle_record_selected(self, selection_info: Dict[str, Any]):
        """处理记录选择"""
        execution_id = selection_info.get('execution_id')
        if execution_id:
            record = self.model.get_record_by_execution_id(execution_id)
            self.model.select_record(record)
            logger.debug(f"Record selected: {execution_id}")
        else:
            self.model.select_record(None)
            logger.debug("Record selection cleared")

    def _handle_refresh_requested(self):
        """处理刷新请求"""
        logger.info("Refresh requested by user")
        self.refresh_data()

    def _handle_export_requested(self, file_path: str, format_type: str):
        """处理导出请求"""
        logger.info(f"Export requested: {file_path}, format: {format_type}")
        self.model.export_history(file_path, format_type)
        self.export_requested.emit(file_path, format_type)

    def _handle_cleanup_requested(self, days_before: int):
        """处理清理请求"""
        logger.info(f"Cleanup requested: {days_before} days before")
        self.model.cleanup_old_records(days_before)
        self.cleanup_requested.emit(days_before)

    # Model事件处理方法
    def _handle_execution_records_updated(self, records: List[Dict[str, Any]]):
        """处理执行记录更新"""
        self.view.display_execution_records(records)
        self.execution_records_updated.emit(records)
        logger.debug(f"Execution records updated: {len(records)} records")

    def _handle_execution_record_selected(self, record: Dict[str, Any]):
        """处理执行记录选择"""
        if record:
            self.view.display_execution_details(record)
            self.record_selected.emit(record)
        else:
            self.view.clear_execution_details()
            self.record_selected.emit({})

    def _handle_execution_record_details_updated(self, record: Dict[str, Any]):
        """处理执行记录详情更新"""
        self.view.display_execution_details(record)
        self.execution_record_details_updated.emit(record)

    def _handle_filter_conditions_updated(self, conditions: Dict[str, Any]):
        """处理过滤条件更新"""
        # 可以在这里更新View的过滤条件显示
        self.filter_conditions_updated.emit(conditions)
        logger.debug(f"Filter conditions updated: {conditions}")

    def _handle_statistics_updated(self, statistics: Dict[str, Any]):
        """处理统计信息更新"""
        self.view.update_statistics(statistics)
        self.statistics_updated.emit(statistics)
        logger.debug(f"Statistics updated: {statistics}")

    def _handle_data_loading_finished(self, success: bool, message: str):
        """处理数据加载完成"""
        self.view.set_loading_state(False)
        
        if not success:
            self.view.show_message("错误", message, is_error=True)
        
        self.data_loading_finished.emit(success, message)
        logger.info(f"Data loading finished: success={success}, message={message}")

    def _handle_export_finished(self, success: bool, message: str):
        """处理导出完成"""
        self.view.show_message(
            "导出结果" if success else "导出错误", 
            message, 
            is_error=not success
        )
        self.export_finished.emit(success, message)
        logger.info(f"Export finished: success={success}, message={message}")

    def _handle_cleanup_finished(self, success: bool, message: str):
        """处理清理完成"""
        self.view.show_message(
            "清理结果" if success else "清理错误", 
            message, 
            is_error=not success
        )
        self.cleanup_finished.emit(success, message)
        logger.info(f"Cleanup finished: success={success}, message={message}")

    def _handle_model_error(self, error_message: str):
        """处理Model错误"""
        self.view.show_message("错误", error_message, is_error=True)
        self.error_occurred.emit(error_message)
        logger.error(f"Model error: {error_message}")

    # 公共接口方法
    def refresh_data(self):
        """刷新数据"""
        self.view.set_loading_state(True)
        self.model.refresh_data()

    def get_selected_record(self) -> Optional[Dict[str, Any]]:
        """获取选中的执行记录"""
        return self.model.get_selected_record()

    def select_record_by_id(self, execution_id: str):
        """根据执行ID选择记录"""
        record = self.model.get_record_by_execution_id(execution_id)
        self.model.select_record(record)

    def clear_selection(self):
        """清除选择"""
        self.model.select_record(None)

    def get_filter_conditions(self) -> Dict[str, Any]:
        """获取过滤条件"""
        return self.model.get_filter_conditions()

    def set_filter_conditions(self, conditions: Dict[str, Any]):
        """设置过滤条件"""
        self.model.set_filter_conditions(conditions)
        self.view.set_filter_conditions(conditions)

    def clear_filters(self):
        """清除过滤条件"""
        default_conditions = {
            'status': '全部',
            'start_date': None,
            'end_date': None,
            'search_text': '',
            'show_failed_only': False
        }
        self.set_filter_conditions(default_conditions)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.model.get_statistics()

    def set_auto_refresh(self, enabled: bool, interval_ms: int = 30000):
        """设置自动刷新"""
        self.model.set_auto_refresh(enabled, interval_ms)

    def get_all_records(self) -> List[Dict[str, Any]]:
        """获取所有执行记录"""
        return self.model.get_execution_records()

    def get_filtered_records(self) -> List[Dict[str, Any]]:
        """获取过滤后的执行记录"""
        return self.model.get_filtered_records()

    def export_history(self, file_path: str, format_type: str = 'csv'):
        """导出执行历史"""
        self.model.export_history(file_path, format_type)

    def cleanup_old_records(self, days_before: int = 30):
        """清理旧记录"""
        self.model.cleanup_old_records(days_before)

    def show_message(self, title: str, message: str, is_error: bool = False):
        """显示消息"""
        self.view.show_message(title, message, is_error)

    def cleanup(self):
        """清理资源"""
        self.model.cleanup()
        logger.info("TaskExecutionHistoryPresenter cleaned up")

    # 兼容性接口（用于与现有代码兼容）
    def load_execution_history(self):
        """加载执行历史（兼容性接口）"""
        self.refresh_data()

    def apply_filters(self):
        """应用过滤条件（兼容性接口）"""
        conditions = self.view.get_filter_conditions()
        self.model.set_filter_conditions(conditions)

    def show_execution_details(self, record: Dict[str, Any]):
        """显示执行详情（兼容性接口）"""
        self.view.display_execution_details(record)

    def clear_execution_details(self):
        """清空执行详情（兼容性接口）"""
        self.view.clear_execution_details()