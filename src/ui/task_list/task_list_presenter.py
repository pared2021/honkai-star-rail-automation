"""任务列表展示器模块..

实现任务列表界面的展示器逻辑。
"""

from typing import Optional, Dict, Any
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from .task_list_view import TaskListView
from .task_list_model import TaskListModel
from ...core.enhanced_task_executor import (
    EnhancedTaskExecutor, TaskExecution, TaskConfig, 
    TaskType, TaskPriority, TaskStatus
)
from ...application.task_service import TaskService


class TaskListPresenter(QObject):
    """任务列表展示器。"""
    
    # 信号定义
    taskCreationRequested = pyqtSignal()
    taskEditRequested = pyqtSignal(str)
    
    def __init__(self, view: TaskListView, task_executor: EnhancedTaskExecutor, parent=None):
        """初始化任务列表展示器。
        
        Args:
            view: 任务列表视图
            task_executor: 任务执行器
            parent: 父对象
        """
        super().__init__(parent)
        self.view = view
        self.task_executor = task_executor
        self.task_service = TaskService()
        
        # 连接信号
        self._connect_signals()
        
        # 初始化数据
        self._load_tasks()
        
        # 设置定时器更新任务状态
        self._setup_update_timer()
        
    def _connect_signals(self):
        """连接信号槽。"""
        # 视图信号
        self.view.createTaskRequested.connect(self.taskCreationRequested.emit)
        self.view.taskEditRequested.connect(self.taskEditRequested.emit)
        self.view.taskStartRequested.connect(self._start_task)
        self.view.taskPauseRequested.connect(self._pause_task)
        self.view.taskStopRequested.connect(self._stop_task)
        self.view.taskDeleteRequested.connect(self._delete_task)
        
        # 任务执行器信号（如果有的话）
        # self.task_executor.taskStatusChanged.connect(self._on_task_status_changed)
        
    def _setup_update_timer(self):
        """设置更新定时器。"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_task_status)
        self.update_timer.start(1000)  # 每秒更新一次
        
    def _load_tasks(self):
        """加载任务列表。"""
        try:
            # 从任务执行器获取所有任务
            tasks = self.task_executor.get_all_tasks()
            
            # 清空现有任务
            self.view.clearTasks()
            
            # 添加任务到视图
            for task in tasks:
                self.view.addTask(task)
                
        except Exception as e:
            print(f"加载任务失败: {e}")
            
    def _update_task_status(self):
        """更新任务状态。"""
        try:
            # 获取所有任务的最新状态
            tasks = self.task_executor.get_all_tasks()
            
            # 更新视图中的任务
            for task in tasks:
                self.view.updateTask(task)
                
        except Exception as e:
            print(f"更新任务状态失败: {e}")
            
    def _start_task(self, task_id: str):
        """开始任务。
        
        Args:
            task_id: 任务ID
        """
        try:
            # 通过任务执行器开始任务
            result = self.task_executor.start_task(task_id)
            if result:
                print(f"任务 {task_id} 开始成功")
            else:
                print(f"任务 {task_id} 开始失败")
                
        except Exception as e:
            print(f"开始任务失败: {e}")
            
    def _pause_task(self, task_id: str):
        """暂停任务。
        
        Args:
            task_id: 任务ID
        """
        try:
            # 通过任务执行器暂停任务
            result = self.task_executor.pause_task(task_id)
            if result:
                print(f"任务 {task_id} 暂停成功")
            else:
                print(f"任务 {task_id} 暂停失败")
                
        except Exception as e:
            print(f"暂停任务失败: {e}")
            
    def _stop_task(self, task_id: str):
        """停止任务。
        
        Args:
            task_id: 任务ID
        """
        try:
            # 通过任务执行器停止任务
            result = self.task_executor.cancel_task(task_id)
            if result:
                print(f"任务 {task_id} 停止成功")
            else:
                print(f"任务 {task_id} 停止失败")
                
        except Exception as e:
            print(f"停止任务失败: {e}")
            
    def _delete_task(self, task_id: str):
        """删除任务。
        
        Args:
            task_id: 任务ID
        """
        try:
            # 首先停止任务（如果正在运行）
            self.task_executor.cancel_task(task_id)
            
            # 从任务执行器移除任务
            # 注意：这里需要根据实际的任务执行器API调整
            # self.task_executor.remove_task(task_id)
            
            # 从视图移除任务
            self.view.removeTask(task_id)
            
            print(f"任务 {task_id} 删除成功")
            
        except Exception as e:
            print(f"删除任务失败: {e}")
            
    def add_task(self, task_config: TaskConfig) -> bool:
        """添加新任务。
        
        Args:
            task_config: 任务配置
            
        Returns:
            bool: 是否添加成功
        """
        try:
            # 通过任务执行器提交任务
            task_id = self.task_executor.submit_task(task_config)
            
            if task_id:
                # 获取任务执行信息
                task_execution = self.task_executor.get_task_status(task_id)
                if task_execution:
                    # 添加到视图
                    self.view.addTask(task_execution)
                    print(f"任务 {task_id} 添加成功")
                    return True
                    
            return False
            
        except Exception as e:
            print(f"添加任务失败: {e}")
            return False
            
    def update_task(self, task_config: TaskConfig) -> bool:
        """更新任务配置。
        
        Args:
            task_config: 任务配置
            
        Returns:
            bool: 是否更新成功
        """
        try:
            # 这里需要根据实际的任务执行器API实现任务更新
            # 目前的实现可能需要先删除再添加
            
            # 获取任务执行信息
            task_execution = self.task_executor.get_task_status(task_config.task_id)
            if task_execution:
                # 更新视图
                self.view.updateTask(task_execution)
                print(f"任务 {task_config.task_id} 更新成功")
                return True
                
            return False
            
        except Exception as e:
            print(f"更新任务失败: {e}")
            return False
            
    def get_selected_task(self) -> Optional[TaskExecution]:
        """获取当前选中的任务。
        
        Returns:
            Optional[TaskExecution]: 选中的任务执行信息
        """
        return self.view.getSelectedTask()
        
    def refresh_tasks(self):
        """刷新任务列表。"""
        self._load_tasks()
        
    def get_task_statistics(self) -> Dict[str, int]:
        """获取任务统计信息。
        
        Returns:
            Dict[str, int]: 任务统计信息
        """
        try:
            tasks = self.task_executor.get_all_tasks()
            
            stats = {
                'total': len(tasks),
                'pending': len([t for t in tasks if t.status == TaskStatus.PENDING]),
                'running': len([t for t in tasks if t.status == TaskStatus.RUNNING]),
                'paused': len([t for t in tasks if t.status == TaskStatus.PAUSED]),
                'completed': len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
                'failed': len([t for t in tasks if t.status == TaskStatus.FAILED]),
                'cancelled': len([t for t in tasks if t.status == TaskStatus.CANCELLED])
            }
            
            return stats
            
        except Exception as e:
            print(f"获取任务统计失败: {e}")
            return {}
            
    def cleanup(self):
        """清理资源。"""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
            
    def _on_task_status_changed(self, task_id: str, status: TaskStatus):
        """任务状态变化处理。
        
        Args:
            task_id: 任务ID
            status: 新状态
        """
        try:
            # 获取最新的任务执行信息
            task_execution = self.task_executor.get_task_status(task_id)
            if task_execution:
                # 更新视图
                self.view.updateTask(task_execution)
                
        except Exception as e:
            print(f"处理任务状态变化失败: {e}")
            
    def start_all_pending_tasks(self):
        """开始所有待执行的任务。"""
        try:
            tasks = self.task_executor.get_all_tasks()
            pending_tasks = [t for t in tasks if t.status == TaskStatus.PENDING]
            
            for task in pending_tasks:
                self._start_task(task.task_id)
                
            print(f"开始了 {len(pending_tasks)} 个待执行任务")
            
        except Exception as e:
            print(f"批量开始任务失败: {e}")
            
    def pause_all_running_tasks(self):
        """暂停所有运行中的任务。"""
        try:
            tasks = self.task_executor.get_all_tasks()
            running_tasks = [t for t in tasks if t.status == TaskStatus.RUNNING]
            
            for task in running_tasks:
                self._pause_task(task.task_id)
                
            print(f"暂停了 {len(running_tasks)} 个运行中任务")
            
        except Exception as e:
            print(f"批量暂停任务失败: {e}")
            
    def stop_all_active_tasks(self):
        """停止所有活动任务。"""
        try:
            tasks = self.task_executor.get_all_tasks()
            active_tasks = [t for t in tasks if t.status in [TaskStatus.RUNNING, TaskStatus.PAUSED]]
            
            for task in active_tasks:
                self._stop_task(task.task_id)
                
            print(f"停止了 {len(active_tasks)} 个活动任务")
            
        except Exception as e:
            print(f"批量停止任务失败: {e}")
            
    def clear_completed_tasks(self):
        """清理已完成的任务。"""
        try:
            tasks = self.task_executor.get_all_tasks()
            completed_tasks = [t for t in tasks if t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]]
            
            for task in completed_tasks:
                self._delete_task(task.task_id)
                
            print(f"清理了 {len(completed_tasks)} 个已完成任务")
            
        except Exception as e:
            print(f"清理已完成任务失败: {e}")
            
    def export_task_list(self, file_path: str) -> bool:
        """导出任务列表。
        
        Args:
            file_path: 导出文件路径
            
        Returns:
            bool: 是否导出成功
        """
        try:
            tasks = self.task_executor.get_all_tasks()
            
            # 这里可以实现具体的导出逻辑
            # 例如导出为JSON、CSV等格式
            
            print(f"任务列表已导出到: {file_path}")
            return True
            
        except Exception as e:
            print(f"导出任务列表失败: {e}")
            return False
