"""任务进度显示数据模型模块.

定义任务进度显示界面的数据模型。
"""

from PyQt5.QtCore import QObject, pyqtSignal
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime


@dataclass
class TaskProgress:
    """任务进度数据类."""
    task_id: str
    task_name: str
    status: str  # pending, running, completed, failed, paused
    progress: int = 0  # 0-100
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    estimated_time: Optional[int] = None  # 预估时间（秒）
    elapsed_time: int = 0  # 已用时间（秒）
    remaining_time: Optional[int] = None  # 剩余时间（秒）
    current_step: str = ""
    total_steps: int = 0
    completed_steps: int = 0
    error_message: str = ""
    sub_tasks: List['TaskProgress'] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            'task_id': self.task_id,
            'task_name': self.task_name,
            'status': self.status,
            'progress': self.progress,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'estimated_time': self.estimated_time,
            'elapsed_time': self.elapsed_time,
            'remaining_time': self.remaining_time,
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'completed_steps': self.completed_steps,
            'error_message': self.error_message,
            'sub_tasks': [sub.to_dict() for sub in self.sub_tasks]
        }


@dataclass
class OverallProgress:
    """整体进度数据类."""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    running_tasks: int = 0
    pending_tasks: int = 0
    overall_progress: int = 0  # 0-100
    estimated_total_time: Optional[int] = None
    elapsed_total_time: int = 0
    remaining_total_time: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            'total_tasks': self.total_tasks,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'running_tasks': self.running_tasks,
            'pending_tasks': self.pending_tasks,
            'overall_progress': self.overall_progress,
            'estimated_total_time': self.estimated_total_time,
            'elapsed_total_time': self.elapsed_total_time,
            'remaining_total_time': self.remaining_total_time
        }


class TaskProgressModel(QObject):
    """任务进度数据模型."""
    
    # 信号定义
    progress_updated = pyqtSignal(str, dict)  # task_id, progress_data
    overall_progress_updated = pyqtSignal(dict)  # overall_progress_data
    task_started = pyqtSignal(str)  # task_id
    task_completed = pyqtSignal(str)  # task_id
    task_failed = pyqtSignal(str, str)  # task_id, error_message
    task_paused = pyqtSignal(str)  # task_id
    task_resumed = pyqtSignal(str)  # task_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 任务进度数据
        self.task_progresses: Dict[str, TaskProgress] = {}
        self.overall_progress = OverallProgress()
        
    def add_task(self, task_id: str, task_name: str, 
                 estimated_time: Optional[int] = None,
                 total_steps: int = 0) -> TaskProgress:
        """添加任务."""
        progress = TaskProgress(
            task_id=task_id,
            task_name=task_name,
            status="pending",
            estimated_time=estimated_time,
            total_steps=total_steps
        )
        
        self.task_progresses[task_id] = progress
        self.update_overall_progress()
        
        return progress
        
    def start_task(self, task_id: str):
        """开始任务."""
        if task_id in self.task_progresses:
            progress = self.task_progresses[task_id]
            progress.status = "running"
            progress.start_time = datetime.now()
            
            self.update_overall_progress()
            self.progress_updated.emit(task_id, progress.to_dict())
            self.task_started.emit(task_id)
            
    def update_task_progress(self, task_id: str, progress_value: int,
                           current_step: str = "",
                           completed_steps: int = None):
        """更新任务进度."""
        if task_id in self.task_progresses:
            progress = self.task_progresses[task_id]
            progress.progress = max(0, min(100, progress_value))
            
            if current_step:
                progress.current_step = current_step
                
            if completed_steps is not None:
                progress.completed_steps = completed_steps
                
            # 计算剩余时间
            if progress.start_time and progress.estimated_time:
                elapsed = (datetime.now() - progress.start_time).total_seconds()
                progress.elapsed_time = int(elapsed)
                
                if progress.progress > 0:
                    total_estimated = (elapsed / progress.progress) * 100
                    progress.remaining_time = max(0, int(total_estimated - elapsed))
                    
            self.update_overall_progress()
            self.progress_updated.emit(task_id, progress.to_dict())
            
    def complete_task(self, task_id: str):
        """完成任务."""
        if task_id in self.task_progresses:
            progress = self.task_progresses[task_id]
            progress.status = "completed"
            progress.progress = 100
            progress.end_time = datetime.now()
            progress.remaining_time = 0
            
            if progress.start_time:
                elapsed = (progress.end_time - progress.start_time).total_seconds()
                progress.elapsed_time = int(elapsed)
                
            self.update_overall_progress()
            self.progress_updated.emit(task_id, progress.to_dict())
            self.task_completed.emit(task_id)
            
    def fail_task(self, task_id: str, error_message: str):
        """任务失败."""
        if task_id in self.task_progresses:
            progress = self.task_progresses[task_id]
            progress.status = "failed"
            progress.end_time = datetime.now()
            progress.error_message = error_message
            progress.remaining_time = 0
            
            if progress.start_time:
                elapsed = (progress.end_time - progress.start_time).total_seconds()
                progress.elapsed_time = int(elapsed)
                
            self.update_overall_progress()
            self.progress_updated.emit(task_id, progress.to_dict())
            self.task_failed.emit(task_id, error_message)
            
    def pause_task(self, task_id: str):
        """暂停任务."""
        if task_id in self.task_progresses:
            progress = self.task_progresses[task_id]
            if progress.status == "running":
                progress.status = "paused"
                
                if progress.start_time:
                    elapsed = (datetime.now() - progress.start_time).total_seconds()
                    progress.elapsed_time = int(elapsed)
                    
                self.update_overall_progress()
                self.progress_updated.emit(task_id, progress.to_dict())
                self.task_paused.emit(task_id)
                
    def resume_task(self, task_id: str):
        """恢复任务."""
        if task_id in self.task_progresses:
            progress = self.task_progresses[task_id]
            if progress.status == "paused":
                progress.status = "running"
                
                # 重新计算开始时间
                if progress.start_time and progress.elapsed_time:
                    progress.start_time = datetime.now() - timedelta(seconds=progress.elapsed_time)
                    
                self.update_overall_progress()
                self.progress_updated.emit(task_id, progress.to_dict())
                self.task_resumed.emit(task_id)
                
    def remove_task(self, task_id: str):
        """移除任务."""
        if task_id in self.task_progresses:
            del self.task_progresses[task_id]
            self.update_overall_progress()
            
    def get_task_progress(self, task_id: str) -> Optional[TaskProgress]:
        """获取任务进度."""
        return self.task_progresses.get(task_id)
        
    def get_all_tasks(self) -> Dict[str, TaskProgress]:
        """获取所有任务."""
        return self.task_progresses.copy()
        
    def get_overall_progress(self) -> OverallProgress:
        """获取整体进度."""
        return self.overall_progress
        
    def update_overall_progress(self):
        """更新整体进度."""
        total_tasks = len(self.task_progresses)
        completed_tasks = sum(1 for p in self.task_progresses.values() if p.status == "completed")
        failed_tasks = sum(1 for p in self.task_progresses.values() if p.status == "failed")
        running_tasks = sum(1 for p in self.task_progresses.values() if p.status == "running")
        pending_tasks = sum(1 for p in self.task_progresses.values() if p.status == "pending")
        
        # 计算整体进度
        if total_tasks > 0:
            total_progress = sum(p.progress for p in self.task_progresses.values())
            overall_progress = int(total_progress / total_tasks)
        else:
            overall_progress = 0
            
        # 计算时间
        estimated_total_time = sum(
            p.estimated_time for p in self.task_progresses.values() 
            if p.estimated_time is not None
        )
        
        elapsed_total_time = sum(p.elapsed_time for p in self.task_progresses.values())
        
        remaining_total_time = sum(
            p.remaining_time for p in self.task_progresses.values() 
            if p.remaining_time is not None
        )
        
        self.overall_progress = OverallProgress(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            running_tasks=running_tasks,
            pending_tasks=pending_tasks,
            overall_progress=overall_progress,
            estimated_total_time=estimated_total_time if estimated_total_time > 0 else None,
            elapsed_total_time=elapsed_total_time,
            remaining_total_time=remaining_total_time if remaining_total_time > 0 else None
        )
        
        self.overall_progress_updated.emit(self.overall_progress.to_dict())
        
    def clear_all_tasks(self):
        """清除所有任务."""
        self.task_progresses.clear()
        self.update_overall_progress()
        
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息."""
        return {
            'total_tasks': len(self.task_progresses),
            'completed_tasks': sum(1 for p in self.task_progresses.values() if p.status == "completed"),
            'failed_tasks': sum(1 for p in self.task_progresses.values() if p.status == "failed"),
            'running_tasks': sum(1 for p in self.task_progresses.values() if p.status == "running"),
            'pending_tasks': sum(1 for p in self.task_progresses.values() if p.status == "pending"),
            'average_progress': self.overall_progress.overall_progress,
            'total_elapsed_time': self.overall_progress.elapsed_total_time,
            'estimated_remaining_time': self.overall_progress.remaining_total_time
        }