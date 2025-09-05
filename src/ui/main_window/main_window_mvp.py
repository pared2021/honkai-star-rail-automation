"""主窗口MVP组合类

将MainWindowModel、MainWindowView和MainWindowPresenter组合成一个完整的主窗口组件
"""

from typing import Optional, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMainWindow
import logging

from .main_window_model import MainWindowModel
from .main_window_view import MainWindowView
from .main_window_presenter import MainWindowPresenter
from ...services.ui_service_facade import IUIServiceFacade
from ...core.models.task import TaskStatus

logger = logging.getLogger(__name__)


class MainWindowMVP(QObject):
    """主窗口MVP组合类
    
    将Model、View和Presenter组合成一个完整的主窗口组件
    """
    
    # 业务信号 - 转发自Presenter
    automation_started = pyqtSignal(str)  # 自动化启动 (task_id)
    automation_stopped = pyqtSignal(str)  # 自动化停止 (task_id)
    task_status_changed = pyqtSignal(str, str)  # 任务状态变化 (task_id, status)
    
    # 外部请求信号 - 转发自Presenter
    config_import_requested = pyqtSignal()  # 配置导入请求
    config_export_requested = pyqtSignal()  # 配置导出请求
    database_management_requested = pyqtSignal()  # 数据库管理请求
    log_management_requested = pyqtSignal()  # 日志管理请求
    settings_requested = pyqtSignal()  # 设置请求
    
    # 窗口状态信号
    window_closing = pyqtSignal()  # 窗口关闭
    
    def __init__(self, 
                 ui_service: Optional[IUIServiceFacade] = None,
                 parent: Optional[QObject] = None):
        super().__init__(parent)
        
        # 依赖注入
        self.ui_service = ui_service
        
        # 初始化MVP组件
        self.model = MainWindowModel(ui_service=ui_service)
        self.view = MainWindowView(ui_service=ui_service)
        self.presenter = MainWindowPresenter(
            model=self.model,
            view=self.view,
            ui_service=ui_service
        )
        
        # 连接业务信号
        self._connect_business_signals()
        
        # 连接窗口信号
        self._connect_window_signals()
        
        logger.debug("MainWindowMVP 初始化完成")
    
    def _connect_business_signals(self):
        """连接业务信号"""
        # 转发Presenter的业务信号
        self.presenter.automation_started.connect(self.automation_started)
        self.presenter.automation_stopped.connect(self.automation_stopped)
        self.presenter.task_status_changed.connect(self.task_status_changed)
        
        # 转发Presenter的外部请求信号
        self.presenter.config_import_requested.connect(self.config_import_requested)
        self.presenter.config_export_requested.connect(self.config_export_requested)
        self.presenter.database_management_requested.connect(self.database_management_requested)
        self.presenter.log_management_requested.connect(self.log_management_requested)
        self.presenter.settings_requested.connect(self.settings_requested)
    
    def _connect_window_signals(self):
        """连接窗口信号"""
        # 监听窗口关闭事件
        if hasattr(self.view, 'closeEvent'):
            # 重写closeEvent以发出信号
            original_close_event = self.view.closeEvent
            
            def close_event_wrapper(event):
                self.window_closing.emit()
                original_close_event(event)
            
            self.view.closeEvent = close_event_wrapper
    
    # 公共接口 - 窗口操作
    def show(self):
        """显示主窗口"""
        self.view.show()
    
    def hide(self):
        """隐藏主窗口"""
        self.view.hide()
    
    def close(self) -> bool:
        """关闭主窗口
        
        Returns:
            是否成功关闭
        """
        return self.view.close()
    
    def is_visible(self) -> bool:
        """获取窗口可见状态
        
        Returns:
            是否可见
        """
        return self.view.isVisible()
    
    def set_window_title(self, title: str):
        """设置窗口标题
        
        Args:
            title: 窗口标题
        """
        self.view.setWindowTitle(title)
    
    def get_window_title(self) -> str:
        """获取窗口标题
        
        Returns:
            窗口标题
        """
        return self.view.windowTitle()
    
    # 公共接口 - 自动化控制
    def start_automation(self, task_name: str = "自动化任务") -> Optional[str]:
        """启动自动化
        
        Args:
            task_name: 任务名称
        
        Returns:
            创建的任务ID，失败返回None
        """
        return self.presenter.start_automation(task_name)
    
    def stop_automation(self) -> bool:
        """停止自动化
        
        Returns:
            是否成功停止
        """
        return self.presenter.stop_automation()
    
    def is_automation_running(self) -> bool:
        """获取自动化运行状态
        
        Returns:
            是否运行中
        """
        return self.presenter.is_automation_running()
    
    def get_current_task_id(self) -> Optional[str]:
        """获取当前任务ID
        
        Returns:
            当前任务ID
        """
        return self.presenter.get_current_task_id()
    
    def update_task_status(self, task_id: str, status: TaskStatus):
        """更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
        """
        self.presenter.update_task_status(task_id, status)
    
    def update_status_message(self, message: str):
        """更新状态消息
        
        Args:
            message: 状态消息
        """
        self.presenter.update_status_message(message)
    
    # 公共接口 - 标签页管理
    def set_current_tab(self, tab_index: int):
        """设置当前标签页
        
        Args:
            tab_index: 标签页索引
        """
        self.presenter.set_current_tab(tab_index)
    
    def get_current_tab(self) -> int:
        """获取当前标签页索引
        
        Returns:
            当前标签页索引
        """
        return self.presenter.get_current_tab()
    
    # 公共接口 - 内部组件访问
    def get_task_list_mvp(self):
        """获取任务列表MVP组件
        
        Returns:
            TaskListMVP实例
        """
        return self.view.get_task_list_mvp()
    
    def get_task_creation_mvp(self):
        """获取任务创建MVP组件
        
        Returns:
            TaskCreationMVP实例
        """
        return self.view.get_task_creation_mvp()
    
    def get_game_settings_mvp(self):
        """获取游戏设置MVP组件
        
        Returns:
            GameSettingsMVP实例
        """
        return self.view.get_game_settings_mvp()
    
    def get_automation_settings_mvp(self):
        """获取自动化设置MVP组件
        
        Returns:
            AutomationSettingsMVP实例
        """
        return self.view.get_automation_settings_mvp()
    
    def get_log_viewer_mvp(self):
        """获取日志查看MVP组件
        
        Returns:
            LogViewerMVP实例
        """
        return self.view.get_log_viewer_mvp()
    
    # 公共接口 - 配置管理
    def save_config(self):
        """保存配置"""
        self.presenter.save_config()
    
    def load_config(self):
        """加载配置"""
        self.presenter.load_config()
    
    def set_auto_save_enabled(self, enabled: bool):
        """设置自动保存启用状态
        
        Args:
            enabled: 是否启用自动保存
        """
        self.presenter.set_auto_save_enabled(enabled)
    
    # 公共接口 - 统计信息
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        return self.presenter.get_statistics()
    
    def get_status_history(self, limit: int = 50) -> list:
        """获取状态历史
        
        Args:
            limit: 返回记录数量限制
        
        Returns:
            状态历史记录列表
        """
        return self.presenter.get_status_history(limit)
    
    # 公共接口 - 外部任务操作处理
    def handle_task_started(self, task_id: str):
        """处理外部任务启动
        
        Args:
            task_id: 任务ID
        """
        self.presenter.handle_task_started(task_id)
    
    def handle_task_stopped(self, task_id: str):
        """处理外部任务停止
        
        Args:
            task_id: 任务ID
        """
        self.presenter.handle_task_stopped(task_id)
    
    def handle_task_failed(self, task_id: str, error_message: str):
        """处理外部任务失败
        
        Args:
            task_id: 任务ID
            error_message: 错误消息
        """
        self.presenter.handle_task_failed(task_id, error_message)
    
    def handle_task_progress_updated(self, task_id: str, progress: int, message: str = ""):
        """处理外部任务进度更新
        
        Args:
            task_id: 任务ID
            progress: 进度百分比 (0-100)
            message: 进度消息
        """
        try:
            # 更新任务列表中的进度
            task_list_mvp = self.get_task_list_mvp()
            if task_list_mvp:
                task_list_mvp.update_task_progress(task_id, progress)
            
            # 更新状态消息
            if message:
                self.update_status_message(f"任务进度: {progress}% - {message}")
            else:
                self.update_status_message(f"任务进度: {progress}%")
            
            logger.debug(f"任务进度更新: {task_id} - {progress}%")
            
        except Exception as e:
            logger.error(f"处理任务进度更新失败: {e}")
    
    def handle_task_message_updated(self, task_id: str, message: str):
        """处理外部任务消息更新
        
        Args:
            task_id: 任务ID
            message: 任务消息
        """
        try:
            # 更新状态消息
            self.update_status_message(f"任务消息: {message}")
            
            logger.debug(f"任务消息更新: {task_id} - {message}")
            
        except Exception as e:
            logger.error(f"处理任务消息更新失败: {e}")
    
    def handle_task_completed(self, task_id: str, result: Dict[str, Any]):
        """处理外部任务完成
        
        Args:
            task_id: 任务ID
            result: 任务结果
        """
        try:
            # 更新任务状态
            self.update_task_status(task_id, TaskStatus.COMPLETED)
            
            # 如果是当前任务，停止自动化
            if self.get_current_task_id() == task_id:
                self.model.set_automation_running(False)
                self.model.set_current_task(None)
            
            # 更新状态消息
            self.update_status_message(f"任务完成: {task_id}")
            
            # 刷新任务列表
            task_list_mvp = self.get_task_list_mvp()
            if task_list_mvp:
                task_list_mvp.refresh_tasks()
            
            logger.info(f"任务完成: {task_id}")
            
        except Exception as e:
            logger.error(f"处理任务完成失败: {e}")
    
    # 公共接口 - 显示对话框
    def show_message(self, title: str, message: str):
        """显示消息对话框
        
        Args:
            title: 对话框标题
            message: 消息内容
        """
        self.view.show_message(title, message)
    
    def show_error_message(self, title: str, message: str):
        """显示错误消息对话框
        
        Args:
            title: 对话框标题
            message: 错误消息
        """
        self.view.show_error_message(title, message)
    
    def show_confirmation_dialog(self, title: str, message: str) -> bool:
        """显示确认对话框
        
        Args:
            title: 对话框标题
            message: 确认消息
        
        Returns:
            用户是否确认
        """
        return self.view.show_confirmation_dialog(title, message)
    
    def show_execution_history_dialog(self):
        """显示执行历史对话框"""
        self.view.show_execution_history_dialog()
    
    def show_about_dialog(self):
        """显示关于对话框"""
        self.view.show_about_dialog()
    
    # 公共接口 - 状态控制
    def set_loading_state(self, loading: bool, message: str = ""):
        """设置加载状态
        
        Args:
            loading: 是否加载中
            message: 加载消息
        """
        self.view.set_loading_state(loading, message)
    
    def set_enabled(self, enabled: bool):
        """设置启用状态
        
        Args:
            enabled: 是否启用
        """
        self.view.setEnabled(enabled)
    
    def is_enabled(self) -> bool:
        """获取启用状态
        
        Returns:
            是否启用
        """
        return self.view.isEnabled()
    
    # 公共接口 - 窗口状态
    def get_window_state(self) -> Dict[str, Any]:
        """获取窗口状态
        
        Returns:
            窗口状态字典
        """
        return self.view.get_window_state()
    
    def restore_window_state(self, state: Dict[str, Any]):
        """恢复窗口状态
        
        Args:
            state: 窗口状态字典
        """
        self.view.restore_window_state(state)
    
    # 清理资源
    def cleanup(self):
        """清理资源"""
        try:
            # 清理Presenter
            self.presenter.cleanup()
            
            logger.debug("MainWindowMVP 资源清理完成")
            
        except Exception as e:
            logger.error(f"清理MainWindowMVP资源失败: {e}")
    
    # 属性访问
    @property
    def main_window(self) -> QMainWindow:
        """获取主窗口实例
        
        Returns:
            QMainWindow实例
        """
        return self.view