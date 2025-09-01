"""任务列表视图接口定义

定义任务列表视图的抽象接口，用于MVP模式中的View层。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from PyQt6.QtCore import pyqtSignal, QObject

from ...models.task import Task, TaskStatus, TaskType, TaskPriority


class TaskListView(ABC):
    """任务列表视图接口
    
    定义任务列表视图的所有界面操作方法，用于MVP模式中的View层。
    实现类需要继承此接口并实现所有抽象方法。
    """
    
    # 视图信号定义
    @property
    @abstractmethod
    def task_selected(self) -> pyqtSignal:
        """任务选择信号
        
        Args:
            task_id (str): 选中的任务ID
        """
        pass
    
    @property
    @abstractmethod
    def task_edit_requested(self) -> pyqtSignal:
        """任务编辑请求信号
        
        Args:
            task_id (str): 要编辑的任务ID
        """
        pass
    
    @property
    @abstractmethod
    def task_delete_requested(self) -> pyqtSignal:
        """任务删除请求信号
        
        Args:
            task_id (str): 要删除的任务ID
        """
        pass
    
    @property
    @abstractmethod
    def task_start_requested(self) -> pyqtSignal:
        """任务启动请求信号
        
        Args:
            task_id (str): 要启动的任务ID
        """
        pass
    
    @property
    @abstractmethod
    def task_stop_requested(self) -> pyqtSignal:
        """任务停止请求信号
        
        Args:
            task_id (str): 要停止的任务ID
        """
        pass
    
    @property
    @abstractmethod
    def task_copy_requested(self) -> pyqtSignal:
        """任务复制请求信号
        
        Args:
            task_id (str): 要复制的任务ID
        """
        pass
    
    @property
    @abstractmethod
    def filter_changed(self) -> pyqtSignal:
        """过滤条件变化信号
        
        Args:
            filters (dict): 过滤条件字典
        """
        pass
    
    @property
    @abstractmethod
    def refresh_requested(self) -> pyqtSignal:
        """刷新请求信号"""
        pass
    
    # 数据显示方法
    @abstractmethod
    def display_tasks(self, tasks: List[Task]) -> None:
        """显示任务列表
        
        Args:
            tasks: 要显示的任务列表
        """
        pass
    
    @abstractmethod
    def update_task_status(self, task_id: str, status: TaskStatus) -> None:
        """更新任务状态显示
        
        Args:
            task_id: 任务ID
            status: 新状态
        """
        pass
    
    @abstractmethod
    def update_task_progress(self, task_id: str, progress: int, message: str = "") -> None:
        """更新任务进度显示
        
        Args:
            task_id: 任务ID
            progress: 进度百分比 (0-100)
            message: 进度消息
        """
        pass
    
    @abstractmethod
    def show_task_details(self, task: Optional[Task]) -> None:
        """显示任务详情
        
        Args:
            task: 要显示的任务，None表示清空详情
        """
        pass
    
    @abstractmethod
    def update_statistics(self, stats: Dict[str, Any]) -> None:
        """更新统计信息显示
        
        Args:
            stats: 统计信息字典，包含总数、各状态数量等
        """
        pass
    
    # 选择和交互方法
    @abstractmethod
    def select_task(self, task_id: str) -> None:
        """选择指定任务
        
        Args:
            task_id: 要选择的任务ID
        """
        pass
    
    @abstractmethod
    def get_selected_task_id(self) -> Optional[str]:
        """获取当前选中的任务ID
        
        Returns:
            选中的任务ID，如果没有选中则返回None
        """
        pass
    
    @abstractmethod
    def clear_selection(self) -> None:
        """清除选择"""
        pass
    
    # 过滤和搜索方法
    @abstractmethod
    def set_filter_options(self, 
                          status_options: List[TaskStatus],
                          type_options: List[TaskType],
                          priority_options: List[TaskPriority]) -> None:
        """设置过滤选项
        
        Args:
            status_options: 状态选项列表
            type_options: 类型选项列表
            priority_options: 优先级选项列表
        """
        pass
    
    @abstractmethod
    def get_current_filters(self) -> Dict[str, Any]:
        """获取当前过滤条件
        
        Returns:
            过滤条件字典
        """
        pass
    
    @abstractmethod
    def clear_filters(self) -> None:
        """清除所有过滤条件"""
        pass
    
    # 界面状态控制方法
    @abstractmethod
    def set_loading_state(self, loading: bool) -> None:
        """设置加载状态
        
        Args:
            loading: 是否正在加载
        """
        pass
    
    @abstractmethod
    def enable_actions(self, enabled: bool) -> None:
        """启用/禁用操作按钮
        
        Args:
            enabled: 是否启用
        """
        pass
    
    @abstractmethod
    def update_button_states(self, has_selection: bool, selected_task: Optional[Task] = None) -> None:
        """更新按钮状态
        
        Args:
            has_selection: 是否有选中的任务
            selected_task: 选中的任务对象
        """
        pass
    
    # 消息和通知方法
    @abstractmethod
    def show_message(self, message: str, message_type: str = "info") -> None:
        """显示消息
        
        Args:
            message: 消息内容
            message_type: 消息类型 ("info", "warning", "error", "success")
        """
        pass
    
    @abstractmethod
    def show_confirmation_dialog(self, title: str, message: str) -> bool:
        """显示确认对话框
        
        Args:
            title: 对话框标题
            message: 确认消息
            
        Returns:
            用户是否确认
        """
        pass
    
    @abstractmethod
    def show_error_dialog(self, title: str, error_message: str) -> None:
        """显示错误对话框
        
        Args:
            title: 对话框标题
            error_message: 错误消息
        """
        pass
    
    # 自动刷新控制
    @abstractmethod
    def set_auto_refresh(self, enabled: bool, interval: int = 5000) -> None:
        """设置自动刷新
        
        Args:
            enabled: 是否启用自动刷新
            interval: 刷新间隔（毫秒）
        """
        pass
    
    # 上下文菜单
    @abstractmethod
    def show_context_menu(self, position, task_id: str) -> None:
        """显示上下文菜单
        
        Args:
            position: 菜单显示位置
            task_id: 相关任务ID
        """
        pass
    
    # 执行历史
    @abstractmethod
    def show_execution_history(self, task_id: str) -> None:
        """显示任务执行历史
        
        Args:
            task_id: 任务ID
        """
        pass