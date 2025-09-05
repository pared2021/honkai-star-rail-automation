"""主窗口Presenter层

负责协调Model和View，处理用户交互和业务逻辑
"""

from typing import Optional, Dict, Any
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from datetime import datetime
import logging

from .main_window_model import MainWindowModel
from .main_window_view import MainWindowView
from ...services.ui_service_facade import IUIServiceFacade
from ...core.models.task import TaskStatus

logger = logging.getLogger(__name__)


class MainWindowPresenter(QObject):
    """主窗口Presenter层
    
    负责协调Model和View，处理用户交互和业务逻辑
    """
    
    # 业务信号
    automation_started = pyqtSignal(str)  # 自动化启动 (task_id)
    automation_stopped = pyqtSignal(str)  # 自动化停止 (task_id)
    task_status_changed = pyqtSignal(str, str)  # 任务状态变化 (task_id, status)
    
    # 外部请求信号
    config_import_requested = pyqtSignal()  # 配置导入请求
    config_export_requested = pyqtSignal()  # 配置导出请求
    database_management_requested = pyqtSignal()  # 数据库管理请求
    log_management_requested = pyqtSignal()  # 日志管理请求
    settings_requested = pyqtSignal()  # 设置请求
    
    def __init__(self, model: MainWindowModel, view: MainWindowView,
                 ui_service: Optional[IUIServiceFacade] = None):
        super().__init__()
        
        # 依赖注入
        self.model = model
        self.view = view
        self.ui_service = ui_service
        
        # 状态管理
        self._is_initialized = False
        self._auto_save_enabled = True
        
        # 定时器
        self._time_update_timer = QTimer()
        self._time_update_timer.timeout.connect(self._update_time_display)
        
        # 连接信号
        self._connect_view_signals()
        self._connect_model_signals()
        
        # 初始化数据
        self._initialize_data()
        
        logger.debug("MainWindowPresenter 初始化完成")
    
    def _connect_view_signals(self):
        """连接View信号到Presenter"""
        # 自动化控制信号
        self.view.start_automation_requested.connect(self._on_start_automation_requested)
        self.view.stop_automation_requested.connect(self._on_stop_automation_requested)
        
        # 标签页切换信号
        self.view.tab_changed.connect(self._on_tab_changed)
        
        # 窗口状态变化信号
        self.view.window_state_changed.connect(self._on_window_state_changed)
        
        # 菜单动作信号
        self.view.import_config_requested.connect(self._on_import_config_requested)
        self.view.export_config_requested.connect(self._on_export_config_requested)
        self.view.show_execution_history_requested.connect(self._on_show_execution_history_requested)
        self.view.database_management_requested.connect(self._on_database_management_requested)
        self.view.log_management_requested.connect(self._on_log_management_requested)
        self.view.settings_requested.connect(self._on_settings_requested)
        self.view.about_requested.connect(self._on_about_requested)
        
        # 设置变更信号
        self.view.game_settings_changed.connect(self._on_game_settings_changed)
        self.view.automation_settings_changed.connect(self._on_automation_settings_changed)
        
        # 日志操作信号
        self.view.log_exported.connect(self._on_log_exported)
        self.view.log_cleared.connect(self._on_log_cleared)
    
    def _connect_model_signals(self):
        """连接Model信号到Presenter"""
        # 数据变化信号
        self.model.automation_status_changed.connect(self._on_automation_status_changed)
        self.model.current_task_changed.connect(self._on_current_task_changed)
        self.model.status_message_changed.connect(self._on_status_message_changed)
        self.model.tab_changed.connect(self._on_model_tab_changed)
        self.model.window_state_changed.connect(self._on_model_window_state_changed)
        
        # 错误信号
        self.model.error_occurred.connect(self._on_model_error)
    
    def _initialize_data(self):
        """初始化数据"""
        try:
            # 加载窗口配置
            self.model.load_window_config()
            
            # 启动状态定时器
            self.model.start_status_timer(1000)
            
            # 启动时间更新定时器
            self._time_update_timer.start(1000)
            
            # 同步初始状态到View
            self._sync_model_to_view()
            
            self._is_initialized = True
            logger.info("主窗口数据初始化完成")
            
        except Exception as e:
            logger.error(f"初始化主窗口数据失败: {e}")
            self.view.show_error_message("初始化错误", f"初始化失败: {e}")
    
    def _sync_model_to_view(self):
        """同步Model数据到View"""
        try:
            # 同步自动化状态
            self.view.update_automation_status(self.model.is_automation_running)
            
            # 同步状态消息
            self.view.update_status_message(self.model.status_message)
            
            # 同步当前任务
            self.view.update_current_task(self.model.current_task_id or "")
            
            # 同步标签页
            self.view.set_current_tab(self.model.current_tab_index)
            
            # 同步窗口状态
            window_state = self.model.window_state
            if window_state:
                self.view.restore_window_state(window_state)
            
            logger.debug("Model数据已同步到View")
            
        except Exception as e:
            logger.error(f"同步Model数据到View失败: {e}")
    
    def _sync_view_to_model(self):
        """同步View数据到Model"""
        try:
            # 同步标签页
            current_tab = self.view.get_current_tab()
            self.model.set_current_tab(current_tab)
            
            # 同步窗口状态
            window_state = self.view.get_window_state()
            self.model.set_window_state(window_state)
            
            logger.debug("View数据已同步到Model")
            
        except Exception as e:
            logger.error(f"同步View数据到Model失败: {e}")
    
    # View信号处理方法
    def _on_start_automation_requested(self):
        """处理开始自动化请求"""
        try:
            if self.model.is_automation_running:
                self.view.show_message("提示", "自动化已在运行中")
                return
            
            # 启动自动化
            task_id = self.model.start_automation()
            if task_id:
                self.automation_started.emit(task_id)
                self.view.show_message("成功", f"自动化启动成功，任务ID: {task_id}")
                logger.info(f"自动化启动成功: {task_id}")
            else:
                self.view.show_error_message("错误", "启动自动化失败")
                
        except Exception as e:
            logger.error(f"处理开始自动化请求失败: {e}")
            self.view.show_error_message("错误", f"启动自动化失败: {e}")
    
    def _on_stop_automation_requested(self):
        """处理停止自动化请求"""
        try:
            if not self.model.is_automation_running:
                self.view.show_message("提示", "自动化未在运行")
                return
            
            # 确认停止
            if self.view.show_confirmation_dialog("确认", "确定要停止自动化吗？"):
                task_id = self.model.current_task_id
                if self.model.stop_automation():
                    if task_id:
                        self.automation_stopped.emit(task_id)
                    self.view.show_message("成功", "自动化已停止")
                    logger.info(f"自动化停止成功: {task_id}")
                else:
                    self.view.show_error_message("错误", "停止自动化失败")
                    
        except Exception as e:
            logger.error(f"处理停止自动化请求失败: {e}")
            self.view.show_error_message("错误", f"停止自动化失败: {e}")
    
    def _on_tab_changed(self, tab_index: int):
        """处理标签页切换"""
        try:
            self.model.set_current_tab(tab_index)
            
            # 自动保存配置
            if self._auto_save_enabled:
                self.model.save_window_config()
                
        except Exception as e:
            logger.error(f"处理标签页切换失败: {e}")
    
    def _on_window_state_changed(self, state: Dict[str, Any]):
        """处理窗口状态变化"""
        try:
            self.model.set_window_state(state)
            
            # 自动保存配置
            if self._auto_save_enabled:
                self.model.save_window_config()
                
        except Exception as e:
            logger.error(f"处理窗口状态变化失败: {e}")
    
    def _on_import_config_requested(self):
        """处理导入配置请求"""
        self.config_import_requested.emit()
    
    def _on_export_config_requested(self):
        """处理导出配置请求"""
        self.config_export_requested.emit()
    
    def _on_show_execution_history_requested(self):
        """处理显示执行历史请求"""
        try:
            self.view.show_execution_history_dialog()
        except Exception as e:
            logger.error(f"显示执行历史失败: {e}")
            self.view.show_error_message("错误", f"无法显示执行历史: {e}")
    
    def _on_database_management_requested(self):
        """处理数据库管理请求"""
        self.database_management_requested.emit()
    
    def _on_log_management_requested(self):
        """处理日志管理请求"""
        self.log_management_requested.emit()
    
    def _on_settings_requested(self):
        """处理设置请求"""
        self.settings_requested.emit()
    
    def _on_about_requested(self):
        """处理关于请求"""
        try:
            self.view.show_about_dialog()
        except Exception as e:
            logger.error(f"显示关于对话框失败: {e}")
    
    def _on_game_settings_changed(self, settings: Dict[str, Any]):
        """处理游戏设置变更"""
        try:
            if self.config_manager:
                self.config_manager.set_config('game_settings', settings)
                logger.info("游戏设置已更新")
            
        except Exception as e:
            logger.error(f"处理游戏设置变更失败: {e}")
            self.view.show_error_message("错误", f"保存游戏设置失败: {e}")
    
    def _on_automation_settings_changed(self, settings: Dict[str, Any]):
        """处理自动化设置变更"""
        try:
            if self.config_manager:
                self.config_manager.set_config('automation_settings', settings)
                logger.info("自动化设置已更新")
            
        except Exception as e:
            logger.error(f"处理自动化设置变更失败: {e}")
            self.view.show_error_message("错误", f"保存自动化设置失败: {e}")
    
    def _on_log_exported(self, file_path: str):
        """处理日志导出"""
        try:
            self.view.show_message("成功", f"日志已导出到: {file_path}")
            logger.info(f"日志导出成功: {file_path}")
            
        except Exception as e:
            logger.error(f"处理日志导出失败: {e}")
    
    def _on_log_cleared(self):
        """处理日志清空"""
        try:
            self.view.show_message("成功", "日志已清空")
            logger.info("日志清空成功")
            
        except Exception as e:
            logger.error(f"处理日志清空失败: {e}")
    
    # Model信号处理方法
    def _on_automation_status_changed(self, is_running: bool):
        """处理自动化状态变化"""
        try:
            self.view.update_automation_status(is_running)
            
            # 更新状态消息
            status_msg = "运行中" if is_running else "就绪"
            self.view.update_status_message(status_msg)
            
        except Exception as e:
            logger.error(f"处理自动化状态变化失败: {e}")
    
    def _on_current_task_changed(self, task_id: str):
        """处理当前任务变化"""
        try:
            self.view.update_current_task(task_id)
            
        except Exception as e:
            logger.error(f"处理当前任务变化失败: {e}")
    
    def _on_status_message_changed(self, message: str):
        """处理状态消息变化"""
        try:
            self.view.update_status_message(message)
            
        except Exception as e:
            logger.error(f"处理状态消息变化失败: {e}")
    
    def _on_model_tab_changed(self, tab_index: int):
        """处理Model标签页变化"""
        try:
            self.view.set_current_tab(tab_index)
            
        except Exception as e:
            logger.error(f"处理Model标签页变化失败: {e}")
    
    def _on_model_window_state_changed(self, state: Dict[str, Any]):
        """处理Model窗口状态变化"""
        try:
            self.view.restore_window_state(state)
            
        except Exception as e:
            logger.error(f"处理Model窗口状态变化失败: {e}")
    
    def _on_model_error(self, operation: str, error_message: str):
        """处理Model错误"""
        try:
            self.view.show_error_message("操作错误", f"{operation}: {error_message}")
            logger.error(f"Model操作错误 - {operation}: {error_message}")
            
        except Exception as e:
            logger.error(f"处理Model错误失败: {e}")
    
    # 定时器处理
    def _update_time_display(self):
        """更新时间显示"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.view.update_time_display(current_time)
            
        except Exception as e:
            logger.error(f"更新时间显示失败: {e}")
    
    # 公共接口
    def start_automation(self, task_name: str = "自动化任务") -> Optional[str]:
        """启动自动化
        
        Args:
            task_name: 任务名称
        
        Returns:
            创建的任务ID，失败返回None
        """
        return self.model.start_automation(task_name)
    
    def stop_automation(self) -> bool:
        """停止自动化
        
        Returns:
            是否成功停止
        """
        return self.model.stop_automation()
    
    def is_automation_running(self) -> bool:
        """获取自动化运行状态
        
        Returns:
            是否运行中
        """
        return self.model.is_automation_running
    
    def get_current_task_id(self) -> Optional[str]:
        """获取当前任务ID
        
        Returns:
            当前任务ID
        """
        return self.model.current_task_id
    
    def update_task_status(self, task_id: str, status: TaskStatus):
        """更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
        """
        self.model.update_task_status(task_id, status)
        self.task_status_changed.emit(task_id, status.value)
    
    def update_status_message(self, message: str):
        """更新状态消息
        
        Args:
            message: 状态消息
        """
        self.model.set_status_message(message)
    
    def set_current_tab(self, tab_index: int):
        """设置当前标签页
        
        Args:
            tab_index: 标签页索引
        """
        self.model.set_current_tab(tab_index)
    
    def get_current_tab(self) -> int:
        """获取当前标签页索引
        
        Returns:
            当前标签页索引
        """
        return self.model.current_tab_index
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        return self.model.get_statistics()
    
    def get_status_history(self, limit: int = 50) -> list:
        """获取状态历史
        
        Args:
            limit: 返回记录数量限制
        
        Returns:
            状态历史记录列表
        """
        return self.model.get_status_history(limit)
    
    def set_auto_save_enabled(self, enabled: bool):
        """设置自动保存启用状态
        
        Args:
            enabled: 是否启用自动保存
        """
        self._auto_save_enabled = enabled
        logger.debug(f"自动保存设置: {'启用' if enabled else '禁用'}")
    
    def save_config(self):
        """保存配置"""
        try:
            # 同步View数据到Model
            self._sync_view_to_model()
            
            # 保存窗口配置
            self.model.save_window_config()
            
            logger.info("配置保存成功")
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            self.view.show_error_message("错误", f"保存配置失败: {e}")
    
    def load_config(self):
        """加载配置"""
        try:
            # 加载窗口配置
            self.model.load_window_config()
            
            # 同步到View
            self._sync_model_to_view()
            
            logger.info("配置加载成功")
            
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            self.view.show_error_message("错误", f"加载配置失败: {e}")
    
    # 外部任务操作处理
    def handle_task_started(self, task_id: str):
        """处理外部任务启动
        
        Args:
            task_id: 任务ID
        """
        try:
            self.model.set_current_task(task_id)
            self.model.set_automation_running(True)
            self.model.update_task_status(task_id, TaskStatus.RUNNING)
            
            logger.info(f"外部任务启动: {task_id}")
            
        except Exception as e:
            logger.error(f"处理外部任务启动失败: {e}")
    
    def handle_task_stopped(self, task_id: str):
        """处理外部任务停止
        
        Args:
            task_id: 任务ID
        """
        try:
            if self.model.current_task_id == task_id:
                self.model.set_automation_running(False)
                self.model.set_current_task(None)
            
            self.model.update_task_status(task_id, TaskStatus.COMPLETED)
            
            logger.info(f"外部任务停止: {task_id}")
            
        except Exception as e:
            logger.error(f"处理外部任务停止失败: {e}")
    
    def handle_task_failed(self, task_id: str, error_message: str):
        """处理外部任务失败
        
        Args:
            task_id: 任务ID
            error_message: 错误消息
        """
        try:
            if self.model.current_task_id == task_id:
                self.model.set_automation_running(False)
                self.model.set_current_task(None)
            
            self.model.update_task_status(task_id, TaskStatus.FAILED)
            self.model.set_status_message(f"任务失败: {error_message}")
            
            logger.error(f"外部任务失败: {task_id} - {error_message}")
            
        except Exception as e:
            logger.error(f"处理外部任务失败失败: {e}")
    
    # 清理资源
    def cleanup(self):
        """清理资源"""
        try:
            # 停止定时器
            self._time_update_timer.stop()
            
            # 保存配置
            if self._auto_save_enabled:
                self.save_config()
            
            # 清理Model
            self.model.cleanup()
            
            # 清理View
            self.view.cleanup()
            
            logger.debug("MainWindowPresenter 资源清理完成")
            
        except Exception as e:
            logger.error(f"清理MainWindowPresenter资源失败: {e}")