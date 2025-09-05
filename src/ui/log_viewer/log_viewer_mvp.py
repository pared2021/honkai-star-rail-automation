"""日志查看器MVP组合

该模块将日志查看器的Model、View和Presenter组合成一个完整的组件。
"""

from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal

from .log_viewer_model import LogViewerModel
from .log_viewer_view import LogViewerView
from .log_viewer_presenter import LogViewerPresenter
from src.utils.logger import logger


class LogViewerMVP(QObject):
    """日志查看器MVP组合类"""
    
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
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化MVP组件
        self.model = LogViewerModel()
        self.view = LogViewerView()
        self.presenter = LogViewerPresenter(self.model, self.view)
        
        # 连接业务信号
        self._connect_business_signals()
        
        logger.info("日志查看器MVP组合初始化完成")
    
    def _connect_business_signals(self):
        """连接业务信号"""
        # 连接Presenter的业务信号到MVP的信号
        self.presenter.log_line_added.connect(self.log_line_added.emit)
        self.presenter.statistics_updated.connect(self.statistics_updated.emit)
        self.presenter.current_file_changed.connect(self.current_file_changed.emit)
        self.presenter.file_list_updated.connect(self.file_list_updated.emit)
        self.presenter.monitoring_status_changed.connect(self.monitoring_status_changed.emit)
        
        # 连接操作结果信号
        self.presenter.export_result.connect(self.export_result.emit)
        self.presenter.clear_result.connect(self.clear_result.emit)
        self.presenter.file_load_result.connect(self.file_load_result.emit)
    
    # 显示控制
    def show(self):
        """显示组件"""
        try:
            self.presenter.show()
        except Exception as e:
            logger.error(f"显示日志查看器失败: {e}")
    
    def hide(self):
        """隐藏组件"""
        try:
            self.presenter.hide()
        except Exception as e:
            logger.error(f"隐藏日志查看器失败: {e}")
    
    def set_enabled(self, enabled: bool):
        """设置启用状态"""
        try:
            self.presenter.set_enabled(enabled)
        except Exception as e:
            logger.error(f"设置日志查看器启用状态失败: {e}")
    
    # 日志文件操作
    def load_log_file(self, file_path: str):
        """加载日志文件"""
        try:
            self.presenter.load_log_file(file_path)
        except Exception as e:
            logger.error(f"加载日志文件失败: {e}")
    
    def get_current_file(self) -> str:
        """获取当前日志文件路径"""
        try:
            return self.model.get_current_file()
        except Exception as e:
            logger.error(f"获取当前文件失败: {e}")
            return ""
    
    def get_log_files(self) -> list:
        """获取日志文件列表"""
        try:
            return self.model.get_log_files()
        except Exception as e:
            logger.error(f"获取日志文件列表失败: {e}")
            return []
    
    # 监控控制
    def start_monitoring(self):
        """开始监控"""
        try:
            self.presenter.start_monitoring()
        except Exception as e:
            logger.error(f"开始监控失败: {e}")
    
    def stop_monitoring(self):
        """停止监控"""
        try:
            self.presenter.stop_monitoring()
        except Exception as e:
            logger.error(f"停止监控失败: {e}")
    
    def is_monitoring(self) -> bool:
        """是否正在监控"""
        try:
            return self.model.is_monitoring()
        except Exception as e:
            logger.error(f"检查监控状态失败: {e}")
            return False
    
    # 日志操作
    def add_log_message(self, message: str, level: str = "INFO"):
        """手动添加日志消息"""
        try:
            self.presenter.add_log_message(message, level)
        except Exception as e:
            logger.error(f"添加日志消息失败: {e}")
    
    def get_current_logs(self) -> str:
        """获取当前日志内容"""
        try:
            return self.presenter.get_current_logs()
        except Exception as e:
            logger.error(f"获取当前日志失败: {e}")
            return ""
    
    def clear_logs(self):
        """清空日志"""
        try:
            self.model.clear_logs()
        except Exception as e:
            logger.error(f"清空日志失败: {e}")
    
    def export_logs(self, file_path: str):
        """导出日志"""
        try:
            self.model.export_logs(file_path)
        except Exception as e:
            logger.error(f"导出日志失败: {e}")
    
    # 过滤设置
    def set_level_filter(self, level: str):
        """设置级别过滤"""
        try:
            self.model.set_level_filter(level)
        except Exception as e:
            logger.error(f"设置级别过滤失败: {e}")
    
    def get_level_filter(self) -> str:
        """获取级别过滤"""
        try:
            return self.model.get_level_filter()
        except Exception as e:
            logger.error(f"获取级别过滤失败: {e}")
            return "全部"
    
    def set_search_filter(self, text: str):
        """设置搜索过滤"""
        try:
            self.model.set_search_filter(text)
        except Exception as e:
            logger.error(f"设置搜索过滤失败: {e}")
    
    def get_search_filter(self) -> str:
        """获取搜索过滤"""
        try:
            return self.model.get_search_filter()
        except Exception as e:
            logger.error(f"获取搜索过滤失败: {e}")
            return ""
    
    def clear_filters(self):
        """清除所有过滤条件"""
        try:
            self.presenter.clear_filters()
        except Exception as e:
            logger.error(f"清除过滤条件失败: {e}")
    
    # 显示设置
    def set_max_lines(self, max_lines: int):
        """设置最大行数"""
        try:
            self.model.set_max_lines(max_lines)
        except Exception as e:
            logger.error(f"设置最大行数失败: {e}")
    
    def get_max_lines(self) -> int:
        """获取最大行数"""
        try:
            return self.model.get_max_lines()
        except Exception as e:
            logger.error(f"获取最大行数失败: {e}")
            return 10000
    
    def set_font_size(self, size: int):
        """设置字体大小"""
        try:
            self.model.set_font_size(size)
        except Exception as e:
            logger.error(f"设置字体大小失败: {e}")
    
    def get_font_size(self) -> int:
        """获取字体大小"""
        try:
            return self.model.get_font_size()
        except Exception as e:
            logger.error(f"获取字体大小失败: {e}")
            return 9
    
    def set_theme(self, theme: str):
        """设置主题"""
        try:
            self.model.set_theme(theme)
        except Exception as e:
            logger.error(f"设置主题失败: {e}")
    
    def get_theme(self) -> str:
        """获取主题"""
        try:
            return self.model.get_theme()
        except Exception as e:
            logger.error(f"获取主题失败: {e}")
            return "默认"
    
    def set_auto_scroll(self, enabled: bool):
        """设置自动滚动"""
        try:
            self.model.set_auto_scroll(enabled)
        except Exception as e:
            logger.error(f"设置自动滚动失败: {e}")
    
    def get_auto_scroll(self) -> bool:
        """获取自动滚动状态"""
        try:
            return self.model.get_auto_scroll()
        except Exception as e:
            logger.error(f"获取自动滚动状态失败: {e}")
            return True
    
    def set_realtime_monitoring(self, enabled: bool):
        """设置实时监控"""
        try:
            self.model.set_realtime_monitoring(enabled)
        except Exception as e:
            logger.error(f"设置实时监控失败: {e}")
    
    def get_realtime_monitoring(self) -> bool:
        """获取实时监控状态"""
        try:
            return self.model.get_realtime_monitoring()
        except Exception as e:
            logger.error(f"获取实时监控状态失败: {e}")
            return True
    
    # 统计信息
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            return self.presenter.get_statistics()
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def get_log_count(self) -> int:
        """获取日志总行数"""
        try:
            stats = self.get_statistics()
            return stats.get('total_lines', 0)
        except Exception as e:
            logger.error(f"获取日志行数失败: {e}")
            return 0
    
    def get_error_count(self) -> int:
        """获取错误日志数量"""
        try:
            stats = self.get_statistics()
            return stats.get('error_count', 0)
        except Exception as e:
            logger.error(f"获取错误日志数量失败: {e}")
            return 0
    
    def get_warning_count(self) -> int:
        """获取警告日志数量"""
        try:
            stats = self.get_statistics()
            return stats.get('warning_count', 0)
        except Exception as e:
            logger.error(f"获取警告日志数量失败: {e}")
            return 0
    
    # 获取组件
    def get_widget(self):
        """获取View组件"""
        return self.view
    
    def get_model(self):
        """获取Model组件"""
        return self.model
    
    def get_view(self):
        """获取View组件"""
        return self.view
    
    def get_presenter(self):
        """获取Presenter组件"""
        return self.presenter
    
    # 配置管理
    def save_settings(self):
        """保存设置"""
        try:
            # 这里可以添加保存设置到配置文件的逻辑
            logger.info("日志查看器设置已保存")
        except Exception as e:
            logger.error(f"保存设置失败: {e}")
    
    def load_settings(self):
        """加载设置"""
        try:
            # 这里可以添加从配置文件加载设置的逻辑
            logger.info("日志查看器设置已加载")
        except Exception as e:
            logger.error(f"加载设置失败: {e}")
    
    def reset_settings(self):
        """重置设置为默认值"""
        try:
            self.set_level_filter("全部")
            self.set_search_filter("")
            self.set_max_lines(10000)
            self.set_font_size(9)
            self.set_theme("默认")
            self.set_auto_scroll(True)
            self.set_realtime_monitoring(True)
            
            logger.info("日志查看器设置已重置")
        except Exception as e:
            logger.error(f"重置设置失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        try:
            # 保存设置
            self.save_settings()
            
            # 清理Presenter（会自动清理Model和View）
            self.presenter.cleanup()
            
            logger.info("日志查看器MVP清理完成")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")