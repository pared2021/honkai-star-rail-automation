"""自动化设置界面控制器模块.

处理自动化设置界面的业务逻辑和交互。
"""

from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from typing import Dict, Any, Optional
from .automation_settings_model import AutomationSettingsModel
from .automation_settings_view import AutomationSettingsView


class AutomationSettingsPresenter(QObject):
    """自动化设置界面控制器."""
    
    # 信号定义
    automation_started = pyqtSignal()
    automation_paused = pyqtSignal()
    automation_stopped = pyqtSignal()
    automation_resumed = pyqtSignal()
    settings_updated = pyqtSignal(dict)
    
    def __init__(self, model: AutomationSettingsModel = None, 
                 view: AutomationSettingsView = None, parent=None):
        super().__init__(parent)
        
        # 初始化模型和视图
        self.model = model or AutomationSettingsModel()
        self.view = view or AutomationSettingsView()
        
        # 运行时计时器
        self.runtime_timer = QTimer()
        self.runtime_timer.timeout.connect(self.update_runtime)
        self.start_time = None
        
        # 连接信号
        self.connect_signals()
        
        # 初始化界面
        self.initialize_view()
        
    def connect_signals(self):
        """连接信号和槽."""
        # 模型信号
        self.model.settings_changed.connect(self.on_model_settings_changed)
        self.model.status_changed.connect(self.on_model_status_changed)
        
        # 视图信号
        self.view.settings_changed.connect(self.on_view_settings_changed)
        
        # 控制组件信号
        control_widget = self.view.get_control_widget()
        control_widget.start_automation.connect(self.on_start_automation)
        control_widget.pause_automation.connect(self.on_pause_automation)
        control_widget.stop_automation.connect(self.on_stop_automation)
        control_widget.resume_automation.connect(self.on_resume_automation)
        
    def initialize_view(self):
        """初始化视图."""
        # 设置初始设置值
        settings = self.model.get_settings()
        self.view.set_settings(settings.to_dict())
        
        # 设置初始状态
        status = self.model.get_status()
        control_widget = self.view.get_control_widget()
        control_widget.update_status(
            status.status, 
            status.runtime, 
            status.completed_tasks
        )
        control_widget.update_progress(
            status.overall_progress,
            status.current_task_progress,
            status.current_task
        )
        
    def on_view_settings_changed(self, settings: Dict[str, Any]):
        """处理视图设置变更."""
        # 验证设置
        if self.validate_settings(settings):
            self.model.update_settings(settings)
        else:
            # 恢复原设置
            current_settings = self.model.get_settings()
            self.view.set_settings(current_settings.to_dict())
            
    def on_model_settings_changed(self, settings: Dict[str, Any]):
        """处理模型设置变更."""
        self.settings_updated.emit(settings)
        
    def on_model_status_changed(self, status: Dict[str, Any]):
        """处理模型状态变更."""
        control_widget = self.view.get_control_widget()
        control_widget.update_status(
            status['status'],
            status['runtime'],
            status['completed_tasks']
        )
        control_widget.update_progress(
            status['overall_progress'],
            status['current_task_progress'],
            status['current_task']
        )
        
    def on_start_automation(self):
        """处理开始自动化."""
        from datetime import datetime
        
        # 验证设置
        if not self.model.validate_settings():
            return
            
        # 启动自动化
        self.model.start_automation()
        self.start_time = datetime.now()
        
        # 启动运行时计时器
        self.runtime_timer.start(1000)  # 每秒更新一次
        
        # 发送信号
        self.automation_started.emit()
        
    def on_pause_automation(self):
        """处理暂停自动化."""
        self.model.pause_automation()
        self.runtime_timer.stop()
        self.automation_paused.emit()
        
    def on_resume_automation(self):
        """处理恢复自动化."""
        self.model.resume_automation()
        self.runtime_timer.start(1000)
        self.automation_resumed.emit()
        
    def on_stop_automation(self):
        """处理停止自动化."""
        self.model.stop_automation()
        self.runtime_timer.stop()
        self.start_time = None
        self.automation_stopped.emit()
        
    def update_runtime(self):
        """更新运行时间."""
        if self.start_time:
            from datetime import datetime
            
            elapsed = datetime.now() - self.start_time
            hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            runtime = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            self.model.update_runtime(runtime)
            
    def update_progress(self, overall_progress: int = None,
                       current_task_progress: int = None,
                       current_task: str = None,
                       completed_tasks: int = None):
        """更新进度."""
        self.model.update_progress(
            overall_progress=overall_progress,
            current_task_progress=current_task_progress,
            current_task=current_task,
            completed_tasks=completed_tasks
        )
        
    def add_error(self, error_message: str):
        """添加错误."""
        self.model.add_error(error_message)
        
    def get_current_settings(self) -> Dict[str, Any]:
        """获取当前设置."""
        return self.model.get_settings().to_dict()
        
    def get_current_status(self) -> Dict[str, Any]:
        """获取当前状态."""
        return self.model.get_status().to_dict()
        
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息."""
        return self.model.get_statistics()
        
    def reset_settings(self):
        """重置设置."""
        self.model.reset_settings()
        settings = self.model.get_settings()
        self.view.set_settings(settings.to_dict())
        
    def validate_settings(self, settings: Dict[str, Any]) -> bool:
        """验证设置."""
        try:
            retry_count = settings.get('retry_count', 0)
            if retry_count < 0 or retry_count > 10:
                return False
                
            operation_delay = settings.get('operation_delay', 0)
            if operation_delay < 1 or operation_delay > 60:
                return False
                
            return True
        except Exception:
            return False
            
    def is_automation_running(self) -> bool:
        """检查自动化是否正在运行."""
        status = self.model.get_status()
        return status.status in ["running", "paused"]
        
    def get_view(self) -> AutomationSettingsView:
        """获取视图."""
        return self.view
        
    def get_model(self) -> AutomationSettingsModel:
        """获取模型."""
        return self.model
        
    def cleanup(self):
        """清理资源."""
        if self.runtime_timer.isActive():
            self.runtime_timer.stop()
            
        # 如果自动化正在运行，停止它
        if self.is_automation_running():
            self.on_stop_automation()
