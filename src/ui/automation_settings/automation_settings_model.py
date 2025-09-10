"""自动化设置数据模型模块..

定义自动化设置界面的数据模型。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal
import json
import os


@dataclass
class AutomationSettings:
    """自动化设置数据类."""
    retry_count: int = 3
    operation_delay: int = 2
    auto_save: bool = True
    max_runtime: int = 3600  # 最大运行时间(秒)
    enable_logging: bool = True
    log_level: str = "INFO"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            'retry_count': self.retry_count,
            'operation_delay': self.operation_delay,
            'auto_save': self.auto_save,
            'max_runtime': self.max_runtime,
            'enable_logging': self.enable_logging,
            'log_level': self.log_level
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AutomationSettings':
        """从字典创建实例."""
        return cls(
            retry_count=data.get('retry_count', 3),
            operation_delay=data.get('operation_delay', 2),
            auto_save=data.get('auto_save', True),
            max_runtime=data.get('max_runtime', 3600),
            enable_logging=data.get('enable_logging', True),
            log_level=data.get('log_level', 'INFO')
        )


@dataclass
class AutomationStatus:
    """自动化状态数据类."""
    status: str = "stopped"  # stopped, running, paused
    start_time: Optional[str] = None
    runtime: str = "00:00:00"
    completed_tasks: int = 0
    total_tasks: int = 0
    current_task: str = "无"
    overall_progress: int = 0
    current_task_progress: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            'status': self.status,
            'start_time': self.start_time,
            'runtime': self.runtime,
            'completed_tasks': self.completed_tasks,
            'total_tasks': self.total_tasks,
            'current_task': self.current_task,
            'overall_progress': self.overall_progress,
            'current_task_progress': self.current_task_progress,
            'error_count': self.error_count,
            'last_error': self.last_error
        }


class AutomationSettingsModel(QObject):
    """自动化设置数据模型."""
    
    # 信号定义
    settings_changed = pyqtSignal(dict)
    status_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = AutomationSettings()
        self.status = AutomationStatus()
        self.settings_file = "automation_settings.json"
        
        # 加载设置
        self.load_settings()
        
    def get_settings(self) -> AutomationSettings:
        """获取设置."""
        return self.settings
        
    def update_settings(self, settings_dict: Dict[str, Any]):
        """更新设置."""
        # 更新设置对象
        for key, value in settings_dict.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
                
        # 保存设置
        self.save_settings()
        
        # 发送信号
        self.settings_changed.emit(self.settings.to_dict())
        
    def get_status(self) -> AutomationStatus:
        """获取状态."""
        return self.status
        
    def update_status(self, **kwargs):
        """更新状态."""
        for key, value in kwargs.items():
            if hasattr(self.status, key):
                setattr(self.status, key, value)
                
        # 发送信号
        self.status_changed.emit(self.status.to_dict())
        
    def start_automation(self):
        """开始自动化."""
        from datetime import datetime
        
        self.status.status = "running"
        self.status.start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status.runtime = "00:00:00"
        self.status.completed_tasks = 0
        self.status.error_count = 0
        self.status.overall_progress = 0
        self.status.current_task_progress = 0
        
        self.status_changed.emit(self.status.to_dict())
        
    def pause_automation(self):
        """暂停自动化."""
        self.status.status = "paused"
        self.status_changed.emit(self.status.to_dict())
        
    def resume_automation(self):
        """恢复自动化."""
        self.status.status = "running"
        self.status_changed.emit(self.status.to_dict())
        
    def stop_automation(self):
        """停止自动化."""
        self.status.status = "stopped"
        self.status.start_time = None
        self.status.runtime = "00:00:00"
        self.status.current_task = "无"
        self.status.overall_progress = 0
        self.status.current_task_progress = 0
        
        self.status_changed.emit(self.status.to_dict())
        
    def update_progress(self, overall_progress: int = None, 
                      current_task_progress: int = None,
                      current_task: str = None,
                      completed_tasks: int = None):
        """更新进度."""
        if overall_progress is not None:
            self.status.overall_progress = overall_progress
        if current_task_progress is not None:
            self.status.current_task_progress = current_task_progress
        if current_task is not None:
            self.status.current_task = current_task
        if completed_tasks is not None:
            self.status.completed_tasks = completed_tasks
            
        self.status_changed.emit(self.status.to_dict())
        
    def update_runtime(self, runtime: str):
        """更新运行时间."""
        self.status.runtime = runtime
        self.status_changed.emit(self.status.to_dict())
        
    def add_error(self, error_message: str):
        """添加错误."""
        self.status.error_count += 1
        self.status.last_error = error_message
        self.status_changed.emit(self.status.to_dict())
        
    def save_settings(self):
        """保存设置到文件."""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存设置失败: {e}")
            
    def load_settings(self):
        """从文件加载设置."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.settings = AutomationSettings.from_dict(data)
        except Exception as e:
            print(f"加载设置失败: {e}")
            # 使用默认设置
            self.settings = AutomationSettings()
            
    def reset_settings(self):
        """重置为默认设置."""
        self.settings = AutomationSettings()
        self.save_settings()
        self.settings_changed.emit(self.settings.to_dict())
        
    def validate_settings(self) -> bool:
        """验证设置有效性."""
        if self.settings.retry_count < 0 or self.settings.retry_count > 10:
            return False
        if self.settings.operation_delay < 1 or self.settings.operation_delay > 60:
            return False
        if self.settings.max_runtime < 60 or self.settings.max_runtime > 86400:
            return False
        return True
        
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息."""
        return {
            'total_tasks': self.status.total_tasks,
            'completed_tasks': self.status.completed_tasks,
            'error_count': self.status.error_count,
            'success_rate': (self.status.completed_tasks / max(self.status.total_tasks, 1)) * 100,
            'runtime': self.status.runtime,
            'status': self.status.status
        }
