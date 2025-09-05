"""日志查看器Presenter层

该模块定义了日志查看器的表示层，负责协调Model和View，处理用户交互和业务逻辑。
"""

from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal

from src.utils.logger import logger


class LogViewerPresenter(QObject):
    """日志查看器表示层"""
    
    # 业务信号
    log_line_added = pyqtSignal(str)  # 新增日志行
    statistics_updated = pyqtSignal(dict)  # 统计信息更新
    current_file_changed = pyqtSignal(str)  # 当前文件变化
    file_list_updated = pyqtSignal(list)  # 文件列表更新
    monitoring_status_changed = pyqtSignal(bool, str)  # 监控状态变化
    
    # 操作结果信号
    export_result = pyqtSignal(bool, str)  # 导出结果
    clear_result = pyqtSignal(bool, str)  # 清空结果
    file_load_result = pyqtSignal(bool, str)  # 文件加载结果
    
    def __init__(self, model, view, parent=None):
        super().__init__(parent)
        
        self.model = model
        self.view = view
        
        self._connect_view_signals()
        self._connect_model_signals()
        
        # 初始化数据
        self._initialize_data()
        
        logger.info("日志查看器Presenter初始化完成")
    
    def _connect_view_signals(self):
        """连接View信号"""
        # 过滤器信号
        self.view.level_filter_changed.connect(self._on_level_filter_changed)
        self.view.search_filter_changed.connect(self._on_search_filter_changed)
        
        # 控制信号
        self.view.realtime_monitoring_toggled.connect(self._on_realtime_monitoring_toggled)
        self.view.auto_scroll_toggled.connect(self._on_auto_scroll_toggled)
        
        # 设置信号
        self.view.max_lines_changed.connect(self._on_max_lines_changed)
        self.view.font_size_changed.connect(self._on_font_size_changed)
        self.view.theme_changed.connect(self._on_theme_changed)
        
        # 操作请求信号
        self.view.clear_logs_requested.connect(self._on_clear_logs_requested)
        self.view.export_logs_requested.connect(self._on_export_logs_requested)
        self.view.open_file_requested.connect(self._on_open_file_requested)
        self.view.refresh_requested.connect(self._on_refresh_requested)
        self.view.file_selected.connect(self._on_file_selected)
    
    def _connect_model_signals(self):
        """连接Model信号"""
        # 数据变化信号
        self.model.new_log_line.connect(self._on_new_log_line)
        self.model.file_changed.connect(self._on_file_changed)
        self.model.statistics_updated.connect(self._on_statistics_updated)
        self.model.settings_changed.connect(self._on_settings_changed)
        
        # 状态信号
        self.model.export_result.connect(self._on_export_result)
        self.model.clear_result.connect(self._on_clear_result)
        self.model.file_load_result.connect(self._on_file_load_result)
        self.model.monitoring_status.connect(self._on_monitoring_status)
        
        # 错误信号
        self.model.error_occurred.connect(self._on_model_error)
    
    def _initialize_data(self):
        """初始化数据"""
        try:
            # 设置初始值
            self.view.set_level_filter(self.model.get_level_filter())
            self.view.set_search_filter(self.model.get_search_filter())
            self.view.set_max_lines(self.model.get_max_lines())
            self.view.set_font_size(self.model.get_font_size())
            self.view.set_theme(self.model.get_theme())
            self.view.set_auto_scroll(self.model.get_auto_scroll())
            self.view.set_realtime_monitoring(self.model.get_realtime_monitoring())
            
            # 更新文件列表
            self._refresh_file_list()
            
            # 开始监控（如果启用）
            if self.model.get_realtime_monitoring():
                self.model.start_monitoring()
            
        except Exception as e:
            logger.error(f"初始化数据失败: {e}")
            self.view.show_message("错误", f"初始化失败: {e}", "error")
    
    # View信号处理
    def _on_level_filter_changed(self, level: str):
        """处理级别过滤变化"""
        try:
            self.model.set_level_filter(level)
            self._refresh_display()
        except Exception as e:
            logger.error(f"设置级别过滤失败: {e}")
    
    def _on_search_filter_changed(self, text: str):
        """处理搜索过滤变化"""
        try:
            self.model.set_search_filter(text)
            self._refresh_display()
        except Exception as e:
            logger.error(f"设置搜索过滤失败: {e}")
    
    def _on_realtime_monitoring_toggled(self, enabled: bool):
        """处理实时监控切换"""
        try:
            self.model.set_realtime_monitoring(enabled)
            if enabled:
                self.model.start_monitoring()
            else:
                self.model.stop_monitoring()
        except Exception as e:
            logger.error(f"切换实时监控失败: {e}")
    
    def _on_auto_scroll_toggled(self, enabled: bool):
        """处理自动滚动切换"""
        try:
            self.model.set_auto_scroll(enabled)
        except Exception as e:
            logger.error(f"设置自动滚动失败: {e}")
    
    def _on_max_lines_changed(self, max_lines: int):
        """处理最大行数变化"""
        try:
            self.model.set_max_lines(max_lines)
        except Exception as e:
            logger.error(f"设置最大行数失败: {e}")
    
    def _on_font_size_changed(self, size: int):
        """处理字体大小变化"""
        try:
            self.model.set_font_size(size)
            self.view.update_font_size(size)
        except Exception as e:
            logger.error(f"设置字体大小失败: {e}")
    
    def _on_theme_changed(self, theme: str):
        """处理主题变化"""
        try:
            self.model.set_theme(theme)
            self.view.update_theme(theme)
        except Exception as e:
            logger.error(f"设置主题失败: {e}")
    
    def _on_clear_logs_requested(self):
        """处理清空日志请求"""
        try:
            self.view.set_loading_state(True)
            self.model.clear_logs()
        except Exception as e:
            logger.error(f"清空日志失败: {e}")
            self.view.set_loading_state(False)
            self.view.show_message("错误", f"清空日志失败: {e}", "error")
    
    def _on_export_logs_requested(self, file_path: str):
        """处理导出日志请求"""
        try:
            self.view.set_loading_state(True)
            self.model.export_logs(file_path)
        except Exception as e:
            logger.error(f"导出日志失败: {e}")
            self.view.set_loading_state(False)
            self.view.show_message("错误", f"导出日志失败: {e}", "error")
    
    def _on_open_file_requested(self, file_path: str):
        """处理打开文件请求"""
        try:
            self.view.set_loading_state(True)
            self.model.load_log_file(file_path)
        except Exception as e:
            logger.error(f"打开文件失败: {e}")
            self.view.set_loading_state(False)
            self.view.show_message("错误", f"打开文件失败: {e}", "error")
    
    def _on_refresh_requested(self):
        """处理刷新请求"""
        try:
            self._refresh_file_list()
            self._refresh_display()
        except Exception as e:
            logger.error(f"刷新失败: {e}")
            self.view.show_message("错误", f"刷新失败: {e}", "error")
    
    def _on_file_selected(self, file_path: str):
        """处理文件选择"""
        try:
            self.view.set_loading_state(True)
            self.model.load_log_file(file_path)
        except Exception as e:
            logger.error(f"选择文件失败: {e}")
            self.view.set_loading_state(False)
            self.view.show_message("错误", f"选择文件失败: {e}", "error")
    
    # Model信号处理
    def _on_new_log_line(self, line: str):
        """处理新增日志行"""
        try:
            # 检查是否应该显示这行
            if self.model.should_show_line(line):
                self.view.append_log_line(line)
                self.log_line_added.emit(line)
        except Exception as e:
            logger.error(f"处理新增日志行失败: {e}")
    
    def _on_file_changed(self, file_path: str):
        """处理文件变化"""
        try:
            self.view.update_current_file(file_path)
            self.current_file_changed.emit(file_path)
        except Exception as e:
            logger.error(f"处理文件变化失败: {e}")
    
    def _on_statistics_updated(self, stats: Dict[str, Any]):
        """处理统计信息更新"""
        try:
            self.view.update_statistics(stats)
            self.statistics_updated.emit(stats)
        except Exception as e:
            logger.error(f"处理统计信息更新失败: {e}")
    
    def _on_settings_changed(self, setting: str, value: Any):
        """处理设置变化"""
        try:
            # 根据设置类型更新View
            if setting == "level_filter":
                self.view.set_level_filter(value)
            elif setting == "search_filter":
                self.view.set_search_filter(value)
            elif setting == "max_lines":
                self.view.set_max_lines(value)
            elif setting == "font_size":
                self.view.set_font_size(value)
                self.view.update_font_size(value)
            elif setting == "theme":
                self.view.set_theme(value)
                self.view.update_theme(value)
            elif setting == "auto_scroll":
                self.view.set_auto_scroll(value)
            elif setting == "realtime_monitoring":
                self.view.set_realtime_monitoring(value)
        except Exception as e:
            logger.error(f"处理设置变化失败: {e}")
    
    def _on_export_result(self, success: bool, message: str):
        """处理导出结果"""
        try:
            self.view.set_loading_state(False)
            
            if success:
                self.view.show_message("成功", message, "info")
            else:
                self.view.show_message("错误", message, "error")
            
            self.export_result.emit(success, message)
        except Exception as e:
            logger.error(f"处理导出结果失败: {e}")
    
    def _on_clear_result(self, success: bool, message: str):
        """处理清空结果"""
        try:
            self.view.set_loading_state(False)
            
            if success:
                self.view.clear_log_display()
                self.view.show_message("成功", message, "info")
            else:
                self.view.show_message("错误", message, "error")
            
            self.clear_result.emit(success, message)
        except Exception as e:
            logger.error(f"处理清空结果失败: {e}")
    
    def _on_file_load_result(self, success: bool, message: str):
        """处理文件加载结果"""
        try:
            self.view.set_loading_state(False)
            
            if success:
                # 刷新显示
                self._refresh_display()
            else:
                self.view.show_message("错误", message, "error")
            
            self.file_load_result.emit(success, message)
        except Exception as e:
            logger.error(f"处理文件加载结果失败: {e}")
    
    def _on_monitoring_status(self, is_monitoring: bool, status_text: str):
        """处理监控状态"""
        try:
            self.view.update_monitoring_status(is_monitoring, status_text)
            self.monitoring_status_changed.emit(is_monitoring, status_text)
        except Exception as e:
            logger.error(f"处理监控状态失败: {e}")
    
    def _on_model_error(self, error_msg: str):
        """处理Model错误"""
        try:
            self.view.set_loading_state(False)
            self.view.show_message("错误", error_msg, "error")
            logger.error(f"Model错误: {error_msg}")
        except Exception as e:
            logger.error(f"处理Model错误失败: {e}")
    
    # 辅助方法
    def _refresh_display(self):
        """刷新显示"""
        try:
            # 获取过滤后的日志
            filtered_logs = self.model.get_filtered_logs()
            self.view.set_log_content(filtered_logs)
        except Exception as e:
            logger.error(f"刷新显示失败: {e}")
    
    def _refresh_file_list(self):
        """刷新文件列表"""
        try:
            files = self.model.get_log_files()
            self.view.update_file_list(files)
            self.file_list_updated.emit(files)
        except Exception as e:
            logger.error(f"刷新文件列表失败: {e}")
    
    # 公共接口
    def load_log_file(self, file_path: str):
        """加载日志文件"""
        try:
            self.view.set_loading_state(True)
            self.model.load_log_file(file_path)
        except Exception as e:
            logger.error(f"加载日志文件失败: {e}")
            self.view.set_loading_state(False)
            self.view.show_message("错误", f"加载日志文件失败: {e}", "error")
    
    def start_monitoring(self):
        """开始监控"""
        try:
            self.model.start_monitoring()
        except Exception as e:
            logger.error(f"开始监控失败: {e}")
            self.view.show_message("错误", f"开始监控失败: {e}", "error")
    
    def stop_monitoring(self):
        """停止监控"""
        try:
            self.model.stop_monitoring()
        except Exception as e:
            logger.error(f"停止监控失败: {e}")
    
    def add_log_message(self, message: str, level: str = "INFO"):
        """手动添加日志消息"""
        try:
            self.model.add_log_message(message, level)
        except Exception as e:
            logger.error(f"添加日志消息失败: {e}")
    
    def get_current_logs(self) -> str:
        """获取当前日志内容"""
        try:
            return self.view.get_log_content()
        except Exception as e:
            logger.error(f"获取当前日志失败: {e}")
            return ""
    
    def clear_filters(self):
        """清除所有过滤条件"""
        try:
            self.model.set_level_filter("全部")
            self.model.set_search_filter("")
            self._refresh_display()
        except Exception as e:
            logger.error(f"清除过滤条件失败: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            return self.model.get_statistics()
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def set_enabled(self, enabled: bool):
        """设置启用状态"""
        try:
            self.view.set_enabled_state(enabled)
        except Exception as e:
            logger.error(f"设置启用状态失败: {e}")
    
    def show(self):
        """显示组件"""
        try:
            self.view.show()
        except Exception as e:
            logger.error(f"显示组件失败: {e}")
    
    def hide(self):
        """隐藏组件"""
        try:
            self.view.hide()
        except Exception as e:
            logger.error(f"隐藏组件失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        try:
            # 停止监控
            self.model.stop_monitoring()
            
            # 清理Model和View
            self.model.cleanup()
            self.view.cleanup()
            
            logger.info("日志查看器Presenter清理完成")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")