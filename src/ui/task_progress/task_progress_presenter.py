"""任务进度显示控制器模块.

处理任务进度显示界面的业务逻辑和交互。
"""

from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from typing import Dict, Any, Optional
from datetime import timedelta
from .task_progress_model import TaskProgressModel
from .task_progress_view import TaskProgressView


class TaskProgressPresenter(QObject):
    """任务进度显示控制器."""
    
    # 信号定义
    task_paused = pyqtSignal(str)  # task_id
    task_resumed = pyqtSignal(str)  # task_id
    task_cancelled = pyqtSignal(str)  # task_id
    progress_updated = pyqtSignal(str, dict)  # task_id, progress_data
    
    def __init__(self, model: TaskProgressModel = None, 
                 view: TaskProgressView = None, parent=None):
        super().__init__(parent)
        
        # 初始化模型和视图
        self.model = model or TaskProgressModel()
        self.view = view or TaskProgressView()
        
        # 连接信号
        self.connect_signals()
        
        # 初始化界面
        self.initialize_view()
        
    def connect_signals(self):
        """连接信号和槽."""
        # 模型信号
        self.model.progress_updated.connect(self.on_model_progress_updated)
        self.model.overall_progress_updated.connect(self.on_model_overall_progress_updated)
        self.model.task_started.connect(self.on_model_task_started)
        self.model.task_completed.connect(self.on_model_task_completed)
        self.model.task_failed.connect(self.on_model_task_failed)
        self.model.task_paused.connect(self.on_model_task_paused)
        self.model.task_resumed.connect(self.on_model_task_resumed)
        
        # 视图信号
        self.view.task_pause_requested.connect(self.on_view_pause_requested)
        self.view.task_resume_requested.connect(self.on_view_resume_requested)
        self.view.task_cancel_requested.connect(self.on_view_cancel_requested)
        self.view.refresh_requested.connect(self.on_view_refresh_requested)
        
    def initialize_view(self):
        """初始化视图."""
        # 更新整体进度
        overall_progress = self.model.get_overall_progress()
        self.view.update_overall_progress(overall_progress.to_dict())
        
        # 添加现有任务
        all_tasks = self.model.get_all_tasks()
        for task_id, task_progress in all_tasks.items():
            self.view.add_task_widget(task_id, task_progress.task_name)
            self.view.update_task_progress(task_id, task_progress.to_dict())
            
    def on_model_progress_updated(self, task_id: str, progress_data: Dict[str, Any]):
        """处理模型进度更新."""
        self.view.update_task_progress(task_id, progress_data)
        self.progress_updated.emit(task_id, progress_data)
        
    def on_model_overall_progress_updated(self, progress_data: Dict[str, Any]):
        """处理模型整体进度更新."""
        self.view.update_overall_progress(progress_data)
        
    def on_model_task_started(self, task_id: str):
        """处理模型任务开始."""
        task_progress = self.model.get_task_progress(task_id)
        if task_progress:
            # 确保视图中有对应的组件
            if task_id not in self.view.task_widgets:
                self.view.add_task_widget(task_id, task_progress.task_name)
                
    def on_model_task_completed(self, task_id: str):
        """处理模型任务完成."""
        pass  # 视图会通过progress_updated信号自动更新
        
    def on_model_task_failed(self, task_id: str, error_message: str):
        """处理模型任务失败."""
        pass  # 视图会通过progress_updated信号自动更新
        
    def on_model_task_paused(self, task_id: str):
        """处理模型任务暂停."""
        self.task_paused.emit(task_id)
        
    def on_model_task_resumed(self, task_id: str):
        """处理模型任务恢复."""
        self.task_resumed.emit(task_id)
        
    def on_view_pause_requested(self, task_id: str):
        """处理视图暂停请求."""
        self.model.pause_task(task_id)
        
    def on_view_resume_requested(self, task_id: str):
        """处理视图恢复请求."""
        self.model.resume_task(task_id)
        
    def on_view_cancel_requested(self, task_id: str):
        """处理视图取消请求."""
        self.model.fail_task(task_id, "用户取消")
        self.task_cancelled.emit(task_id)
        
    def on_view_refresh_requested(self):
        """处理视图刷新请求."""
        # 刷新所有任务的显示
        all_tasks = self.model.get_all_tasks()
        for task_id, task_progress in all_tasks.items():
            self.view.update_task_progress(task_id, task_progress.to_dict())
            
        # 刷新整体进度
        overall_progress = self.model.get_overall_progress()
        self.view.update_overall_progress(overall_progress.to_dict())
        
    # 公共接口方法
    def add_task(self, task_id: str, task_name: str, 
                 estimated_time: Optional[int] = None,
                 total_steps: int = 0):
        """添加任务."""
        task_progress = self.model.add_task(task_id, task_name, estimated_time, total_steps)
        self.view.add_task_widget(task_id, task_name)
        self.view.update_task_progress(task_id, task_progress.to_dict())
        
    def start_task(self, task_id: str):
        """开始任务."""
        self.model.start_task(task_id)
        
    def update_task_progress(self, task_id: str, progress_value: int,
                           current_step: str = "",
                           completed_steps: int = None):
        """更新任务进度."""
        self.model.update_task_progress(
            task_id, progress_value, current_step, completed_steps
        )
        
    def complete_task(self, task_id: str):
        """完成任务."""
        self.model.complete_task(task_id)
        
    def fail_task(self, task_id: str, error_message: str):
        """任务失败."""
        self.model.fail_task(task_id, error_message)
        
    def pause_task(self, task_id: str):
        """暂停任务."""
        self.model.pause_task(task_id)
        
    def resume_task(self, task_id: str):
        """恢复任务."""
        self.model.resume_task(task_id)
        
    def remove_task(self, task_id: str):
        """移除任务."""
        self.model.remove_task(task_id)
        self.view.remove_task_widget(task_id)
        
    def clear_completed_tasks(self):
        """清除已完成的任务."""
        all_tasks = self.model.get_all_tasks()
        completed_task_ids = [
            task_id for task_id, task_progress in all_tasks.items()
            if task_progress.status in ['completed', 'failed']
        ]
        
        for task_id in completed_task_ids:
            self.remove_task(task_id)
            
    def clear_all_tasks(self):
        """清除所有任务."""
        self.model.clear_all_tasks()
        self.view.clear_all_tasks()
        
    def get_task_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务进度."""
        task_progress = self.model.get_task_progress(task_id)
        return task_progress.to_dict() if task_progress else None
        
    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """获取所有任务."""
        all_tasks = self.model.get_all_tasks()
        return {task_id: task_progress.to_dict() 
                for task_id, task_progress in all_tasks.items()}
                
    def get_overall_progress(self) -> Dict[str, Any]:
        """获取整体进度."""
        return self.model.get_overall_progress().to_dict()
        
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息."""
        return self.model.get_statistics()
        
    def is_any_task_running(self) -> bool:
        """检查是否有任务正在运行."""
        all_tasks = self.model.get_all_tasks()
        return any(task.status == 'running' for task in all_tasks.values())
        
    def get_running_tasks(self) -> Dict[str, Dict[str, Any]]:
        """获取正在运行的任务."""
        all_tasks = self.model.get_all_tasks()
        return {
            task_id: task_progress.to_dict()
            for task_id, task_progress in all_tasks.items()
            if task_progress.status == 'running'
        }
        
    def get_pending_tasks(self) -> Dict[str, Dict[str, Any]]:
        """获取待处理的任务."""
        all_tasks = self.model.get_all_tasks()
        return {
            task_id: task_progress.to_dict()
            for task_id, task_progress in all_tasks.items()
            if task_progress.status == 'pending'
        }
        
    def get_completed_tasks(self) -> Dict[str, Dict[str, Any]]:
        """获取已完成的任务."""
        all_tasks = self.model.get_all_tasks()
        return {
            task_id: task_progress.to_dict()
            for task_id, task_progress in all_tasks.items()
            if task_progress.status == 'completed'
        }
        
    def get_failed_tasks(self) -> Dict[str, Dict[str, Any]]:
        """获取失败的任务."""
        all_tasks = self.model.get_all_tasks()
        return {
            task_id: task_progress.to_dict()
            for task_id, task_progress in all_tasks.items()
            if task_progress.status == 'failed'
        }
        
    def pause_all_running_tasks(self):
        """暂停所有正在运行的任务."""
        running_tasks = self.get_running_tasks()
        for task_id in running_tasks.keys():
            self.pause_task(task_id)
            
    def resume_all_paused_tasks(self):
        """恢复所有暂停的任务."""
        all_tasks = self.model.get_all_tasks()
        paused_tasks = [
            task_id for task_id, task_progress in all_tasks.items()
            if task_progress.status == 'paused'
        ]
        
        for task_id in paused_tasks:
            self.resume_task(task_id)
            
    def cancel_all_tasks(self):
        """取消所有任务."""
        all_tasks = self.model.get_all_tasks()
        active_tasks = [
            task_id for task_id, task_progress in all_tasks.items()
            if task_progress.status in ['running', 'paused', 'pending']
        ]
        
        for task_id in active_tasks:
            self.fail_task(task_id, "用户取消")
            
    def get_view(self) -> TaskProgressView:
        """获取视图."""
        return self.view
        
    def get_model(self) -> TaskProgressModel:
        """获取模型."""
        return self.model
        
    def cleanup(self):
        """清理资源."""
        self.view.cleanup()
        
        # 断开信号连接
        try:
            self.model.progress_updated.disconnect()
            self.model.overall_progress_updated.disconnect()
            self.model.task_started.disconnect()
            self.model.task_completed.disconnect()
            self.model.task_failed.disconnect()
            self.model.task_paused.disconnect()
            self.model.task_resumed.disconnect()
        except TypeError:
            pass  # 信号可能已经断开