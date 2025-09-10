"""日志查看器展示器模块.

实现日志查看器界面的展示器逻辑。
"""

from typing import Dict, List, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from datetime import datetime
import logging
import os

from .log_viewer_model import LogViewerModel, LogEntry, LogFilter
from .log_viewer_view import LogViewerView


class LogViewerPresenter(QObject):
    """日志查看器展示器."""
    
    # 信号定义
    log_exported = pyqtSignal(str)  # 日志导出完成
    log_loaded = pyqtSignal(str)  # 日志加载完成
    error_occurred = pyqtSignal(str)  # 错误发生
    status_changed = pyqtSignal(str)  # 状态变化
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = LogViewerModel()
        self.view = LogViewerView()
        
        # 自动刷新定时器
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._auto_refresh)
        
        # 连接信号
        self._connect_signals()
        
        # 初始化视图
        self._init_view()
        
    def _connect_signals(self):
        """连接信号槽."""
        # 模型信号
        self.model.logs_changed.connect(self.view.update_logs)
        self.model.log_added.connect(self.view.add_log)
        self.model.filter_applied.connect(self.view.update_filtered_logs)
        self.model.statistics_updated.connect(self.view.update_statistics)
        self.model.export_completed.connect(self._on_export_completed)
        self.model.error_occurred.connect(self._on_model_error)
        
        # 视图信号
        self.view.filter_changed.connect(self._on_filter_changed)
        self.view.log_selected.connect(self._on_log_selected)
        self.view.export_requested.connect(self._on_export_requested)
        self.view.clear_requested.connect(self._on_clear_requested)
        self.view.refresh_requested.connect(self._on_refresh_requested)
        self.view.save_requested.connect(self._on_save_requested)
        self.view.load_requested.connect(self._on_load_requested)
        self.view.auto_refresh_toggled.connect(self._on_auto_refresh_toggled)
        self.view.max_logs_changed.connect(self._on_max_logs_changed)
        
    def _init_view(self):
        """初始化视图."""
        # 设置初始状态
        self.view.set_status("就绪")
        
        # 加载日志文件列表
        self._update_log_files()
        
        # 更新统计信息
        self.model.update_statistics()
        
    def get_view(self) -> LogViewerView:
        """获取视图组件."""
        return self.view
        
    def add_log(self, log_data: Dict[str, Any]):
        """添加日志."""
        try:
            self.model.add_log(log_data)
            self.status_changed.emit(f"已添加日志: {log_data.get('message', '')[:50]}...")
        except Exception as e:
            self.error_occurred.emit(f"添加日志失败: {str(e)}")
            
    def add_logs(self, logs_data: List[Dict[str, Any]]):
        """批量添加日志."""
        try:
            self.model.add_logs(logs_data)
            self.status_changed.emit(f"已添加 {len(logs_data)} 条日志")
        except Exception as e:
            self.error_occurred.emit(f"批量添加日志失败: {str(e)}")
            
    def set_logs(self, logs_data: List[Dict[str, Any]]):
        """设置日志列表."""
        try:
            self.model.set_logs(logs_data)
            self.status_changed.emit(f"已设置 {len(logs_data)} 条日志")
        except Exception as e:
            self.error_occurred.emit(f"设置日志列表失败: {str(e)}")
            
    def clear_logs(self):
        """清空日志."""
        try:
            self.model.clear_logs()
            self.status_changed.emit("已清空日志")
        except Exception as e:
            self.error_occurred.emit(f"清空日志失败: {str(e)}")
            
    def get_logs(self) -> List[Dict[str, Any]]:
        """获取当前显示的日志."""
        return self.model.get_logs()
        
    def get_all_logs(self) -> List[Dict[str, Any]]:
        """获取所有日志."""
        return self.model.get_all_logs()
        
    def apply_filter(self, filter_data: Dict[str, Any]):
        """应用过滤器."""
        try:
            self.model.apply_filter(filter_data)
            filtered_count = len(self.model.filtered_logs)
            total_count = len(self.model.logs)
            self.status_changed.emit(f"过滤结果: {filtered_count}/{total_count} 条日志")
        except Exception as e:
            self.error_occurred.emit(f"应用过滤器失败: {str(e)}")
            
    def export_logs(self, format_type: str = 'json', filtered_only: bool = True):
        """导出日志."""
        try:
            self.model.export_logs(format_type, filtered_only)
            self.status_changed.emit(f"正在导出日志 ({format_type} 格式)...")
        except Exception as e:
            self.error_occurred.emit(f"导出日志失败: {str(e)}")
            
    def save_logs(self, filename: Optional[str] = None):
        """保存日志到文件."""
        try:
            self.model.save_logs(filename)
            self.status_changed.emit("正在保存日志...")
        except Exception as e:
            self.error_occurred.emit(f"保存日志失败: {str(e)}")
            
    def load_logs(self, filename: str):
        """从文件加载日志."""
        try:
            self.model.load_logs(filename)
            self.status_changed.emit(f"正在加载日志: {filename}")
        except Exception as e:
            self.error_occurred.emit(f"加载日志失败: {str(e)}")
            
    def collect_log(self, log_data: Dict[str, Any]):
        """收集日志（外部接口）."""
        try:
            self.model.collect_log(log_data)
        except Exception as e:
            self.error_occurred.emit(f"收集日志失败: {str(e)}")
            
    def set_max_logs(self, max_logs: int):
        """设置最大日志数量."""
        try:
            self.model.set_max_logs(max_logs)
            self.status_changed.emit(f"已设置最大日志数量: {max_logs}")
        except Exception as e:
            self.error_occurred.emit(f"设置最大日志数量失败: {str(e)}")
            
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息."""
        return self.model.get_statistics()
        
    def _on_filter_changed(self, filter_data: Dict[str, Any]):
        """处理过滤器变化."""
        self.apply_filter(filter_data)
        
    def _on_log_selected(self, log_data: Dict[str, Any]):
        """处理日志选择."""
        # 在详情面板显示日志详情
        self.view.show_log_details(log_data)
        
    def _on_export_requested(self, export_config: Dict[str, Any]):
        """处理导出请求."""
        format_type = export_config.get('format', 'json')
        filtered_only = export_config.get('filtered_only', True)
        
        # 选择保存路径
        if format_type == 'json':
            file_filter = "JSON文件 (*.json)"
            default_ext = ".json"
        elif format_type == 'txt':
            file_filter = "文本文件 (*.txt)"
            default_ext = ".txt"
        elif format_type == 'csv':
            file_filter = "CSV文件 (*.csv)"
            default_ext = ".csv"
        else:
            file_filter = "所有文件 (*.*)"
            default_ext = ""
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_filename = f"logs_export_{timestamp}{default_ext}"
        
        filename, _ = QFileDialog.getSaveFileName(
            self.view,
            "导出日志",
            default_filename,
            file_filter
        )
        
        if filename:
            try:
                # 获取要导出的日志
                logs_to_export = self.model.filtered_logs if filtered_only else self.model.logs
                
                # 直接导出到指定文件
                if format_type == 'json':
                    import json
                    log_data = [log.to_dict() for log in logs_to_export]
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(log_data, f, ensure_ascii=False, indent=2)
                elif format_type == 'txt':
                    with open(filename, 'w', encoding='utf-8') as f:
                        for log in logs_to_export:
                            timestamp_str = log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else ''
                            f.write(f"[{timestamp_str}] [{log.level}] [{log.source}] {log.message}\n")
                elif format_type == 'csv':
                    import csv
                    import json
                    with open(filename, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(['时间', '级别', '来源', '消息', '详情'])
                        for log in logs_to_export:
                            timestamp_str = log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else ''
                            details_str = json.dumps(log.details, ensure_ascii=False) if log.details else ''
                            writer.writerow([timestamp_str, log.level, log.source, log.message, details_str])
                            
                self.log_exported.emit(filename)
                self.status_changed.emit(f"日志已导出到: {filename}")
                
                # 显示成功消息
                QMessageBox.information(
                    self.view,
                    "导出成功",
                    f"日志已成功导出到:\n{filename}"
                )
                
            except Exception as e:
                self.error_occurred.emit(f"导出日志失败: {str(e)}")
                QMessageBox.critical(
                    self.view,
                    "导出失败",
                    f"导出日志时发生错误:\n{str(e)}"
                )
                
    def _on_clear_requested(self):
        """处理清空请求."""
        reply = QMessageBox.question(
            self.view,
            "确认清空",
            "确定要清空所有日志吗？此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.clear_logs()
            
    def _on_refresh_requested(self):
        """处理刷新请求."""
        # 重新应用当前过滤器
        current_filter = self.model.current_filter.to_dict()
        self.apply_filter(current_filter)
        
        # 更新统计信息
        self.model.update_statistics()
        
        # 更新日志文件列表
        self._update_log_files()
        
        self.status_changed.emit("已刷新")
        
    def _on_save_requested(self):
        """处理保存请求."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_filename = f"logs_{timestamp}.json"
        
        filename, _ = QFileDialog.getSaveFileName(
            self.view,
            "保存日志",
            default_filename,
            "JSON文件 (*.json)"
        )
        
        if filename:
            self.save_logs(os.path.basename(filename))
            
    def _on_load_requested(self):
        """处理加载请求."""
        log_files = self.model.get_log_files()
        
        if not log_files:
            QMessageBox.information(
                self.view,
                "无日志文件",
                "没有找到可加载的日志文件。"
            )
            return
            
        # 显示文件选择对话框
        filename, _ = QFileDialog.getOpenFileName(
            self.view,
            "加载日志",
            "logs",
            "JSON文件 (*.json)"
        )
        
        if filename:
            self.load_logs(os.path.basename(filename))
            
    def _on_auto_refresh_toggled(self, enabled: bool):
        """处理自动刷新切换."""
        if enabled:
            self.refresh_timer.start(5000)  # 5秒刷新一次
            self.status_changed.emit("已启用自动刷新")
        else:
            self.refresh_timer.stop()
            self.status_changed.emit("已禁用自动刷新")
            
    def _on_max_logs_changed(self, max_logs: int):
        """处理最大日志数量变化."""
        self.set_max_logs(max_logs)
        
    def _auto_refresh(self):
        """自动刷新."""
        self._on_refresh_requested()
        
    def _on_export_completed(self, filepath: str):
        """处理导出完成."""
        self.log_exported.emit(filepath)
        self.status_changed.emit(f"导出完成: {filepath}")
        
    def _on_model_error(self, error_message: str):
        """处理模型错误."""
        self.error_occurred.emit(error_message)
        self.view.set_status(f"错误: {error_message}")
        
        # 显示错误对话框
        QMessageBox.critical(
            self.view,
            "错误",
            error_message
        )
        
    def _update_log_files(self):
        """更新日志文件列表."""
        try:
            log_files = self.model.get_log_files()
            self.view.update_log_files(log_files)
        except Exception as e:
            self.error_occurred.emit(f"更新日志文件列表失败: {str(e)}")
            
    def show_view(self):
        """显示视图."""
        self.view.show()
        
    def hide_view(self):
        """隐藏视图."""
        self.view.hide()
        
    def cleanup(self):
        """清理资源."""
        try:
            # 停止定时器
            self.refresh_timer.stop()
            
            # 清理模型
            self.model.cleanup()
            
            self.status_changed.emit("已清理资源")
            
        except Exception as e:
            self.error_occurred.emit(f"清理资源失败: {str(e)}")
            
    def get_current_filter(self) -> Dict[str, Any]:
        """获取当前过滤器."""
        return self.model.current_filter.to_dict()
        
    def set_filter(self, filter_data: Dict[str, Any]):
        """设置过滤器."""
        self.view.set_filter(filter_data)
        
    def get_log_count(self) -> int:
        """获取日志总数."""
        return len(self.model.logs)
        
    def get_filtered_log_count(self) -> int:
        """获取过滤后的日志数."""
        return len(self.model.filtered_logs)
        
    def is_auto_refresh_enabled(self) -> bool:
        """检查是否启用自动刷新."""
        return self.refresh_timer.isActive()
        
    def set_auto_refresh(self, enabled: bool):
        """设置自动刷新."""
        self.view.set_auto_refresh(enabled)
