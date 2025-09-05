"""任务列表Model层

该模块定义了任务列表的Model层，负责管理任务数据状态和业务逻辑。
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from src.models.task_models import Task, TaskStatus, TaskType, TaskPriority
from ...services.ui_service_facade import IUIServiceFacade
from src.utils.logger import logger


class TaskListModel(QObject):
    """任务列表Model层
    
    负责管理任务数据状态和业务逻辑，包括任务列表、过滤条件、统计信息等。
    """
    
    # 数据变化信号
    tasks_updated = pyqtSignal(list)  # 任务列表更新
    task_added = pyqtSignal(object)  # 任务添加
    task_updated = pyqtSignal(object)  # 任务更新
    task_removed = pyqtSignal(str)  # 任务删除，传递任务ID
    task_status_changed = pyqtSignal(str, object)  # 任务状态变化，传递任务ID和新状态
    task_progress_updated = pyqtSignal(str, int, str)  # 任务进度更新，传递任务ID、进度和消息
    
    # 过滤和统计信号
    filters_changed = pyqtSignal(dict)  # 过滤条件变化
    statistics_updated = pyqtSignal(dict)  # 统计信息更新
    
    # 操作结果信号
    task_operation_result = pyqtSignal(str, bool, str)  # 任务操作结果，传递操作类型、成功状态、消息
    refresh_completed = pyqtSignal(bool, str)  # 刷新完成
    
    # 错误信号
    error_occurred = pyqtSignal(str, str)  # 错误发生，传递错误类型和消息
    
    def __init__(self, ui_service: Optional[IUIServiceFacade] = None, parent=None):
        super().__init__(parent)
        
        # 依赖注入
        self.ui_service = ui_service
        
        # 数据状态
        self._all_tasks: List[Task] = []
        self._filtered_tasks: List[Task] = []
        self._selected_task_id: Optional[str] = None
        
        # 过滤条件
        self._filters = {
            'status': None,
            'type': None,
            'priority': None,
            'search_text': ''
        }
        
        # 统计信息
        self._statistics = {
            'total': 0,
            'running': 0,
            'completed': 0,
            'failed': 0,
            'pending': 0
        }
        
        # 自动刷新设置
        self._auto_refresh_enabled = True
        self._auto_refresh_interval = 5000  # 5秒
        
        # 自动刷新定时器
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._auto_refresh)
        
        logger.info("任务列表Model初始化完成")
    
    # 数据访问方法
    def get_all_tasks(self) -> List[Task]:
        """获取所有任务"""
        return self._all_tasks.copy()
    
    def get_filtered_tasks(self) -> List[Task]:
        """获取过滤后的任务"""
        return self._filtered_tasks.copy()
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """根据ID获取任务"""
        for task in self._all_tasks:
            if task.task_id == task_id:
                return task
        return None
    
    def get_selected_task_id(self) -> Optional[str]:
        """获取选中的任务ID"""
        return self._selected_task_id
    
    def get_selected_task(self) -> Optional[Task]:
        """获取选中的任务"""
        if self._selected_task_id:
            return self.get_task_by_id(self._selected_task_id)
        return None
    
    def get_filters(self) -> Dict[str, Any]:
        """获取当前过滤条件"""
        return self._filters.copy()
    
    def get_statistics(self) -> Dict[str, int]:
        """获取统计信息"""
        return self._statistics.copy()
    
    # 数据设置方法
    def set_tasks(self, tasks: List[Task]):
        """设置任务列表"""
        try:
            self._all_tasks = tasks.copy()
            self._apply_filters()
            self._update_statistics()
            self.tasks_updated.emit(self._filtered_tasks)
            logger.debug(f"任务列表已更新，共 {len(tasks)} 个任务")
        except Exception as e:
            logger.error(f"设置任务列表失败: {e}")
            self.error_occurred.emit("data_update", str(e))
    
    def set_selected_task_id(self, task_id: Optional[str]):
        """设置选中的任务ID"""
        if self._selected_task_id != task_id:
            self._selected_task_id = task_id
            logger.debug(f"选中任务: {task_id}")
    
    def set_filters(self, filters: Dict[str, Any]):
        """设置过滤条件"""
        try:
            self._filters.update(filters)
            self._apply_filters()
            self.filters_changed.emit(self._filters)
            logger.debug(f"过滤条件已更新: {filters}")
        except Exception as e:
            logger.error(f"设置过滤条件失败: {e}")
            self.error_occurred.emit("filter_update", str(e))
    
    def clear_filters(self):
        """清除所有过滤条件"""
        self._filters = {
            'status': None,
            'type': None,
            'priority': None,
            'search_text': ''
        }
        self._apply_filters()
        self.filters_changed.emit(self._filters)
        logger.debug("过滤条件已清除")
    
    # 过滤逻辑
    def _apply_filters(self):
        """应用过滤条件"""
        try:
            filtered_tasks = []
            
            for task in self._all_tasks:
                # 状态过滤
                if self._filters['status'] and task.status != self._filters['status']:
                    continue
                
                # 类型过滤
                if self._filters['type'] and task.task_type != self._filters['type']:
                    continue
                
                # 优先级过滤
                if self._filters['priority'] and task.priority != self._filters['priority']:
                    continue
                
                # 文本搜索
                search_text = self._filters['search_text'].lower()
                if search_text:
                    task_text = f"{task.name} {task.description or ''}".lower()
                    if search_text not in task_text:
                        continue
                
                filtered_tasks.append(task)
            
            self._filtered_tasks = filtered_tasks
            self._update_statistics()
            self.tasks_updated.emit(self._filtered_tasks)
            
        except Exception as e:
            logger.error(f"应用过滤条件失败: {e}")
            self.error_occurred.emit("filter_apply", str(e))
    
    def _update_statistics(self):
        """更新统计信息"""
        try:
            # 基于过滤后的任务计算统计
            total = len(self._filtered_tasks)
            running = len([t for t in self._filtered_tasks if t.status == TaskStatus.RUNNING])
            completed = len([t for t in self._filtered_tasks if t.status == TaskStatus.COMPLETED])
            failed = len([t for t in self._filtered_tasks if t.status == TaskStatus.FAILED])
            pending = len([t for t in self._filtered_tasks if t.status == TaskStatus.PENDING])
            
            self._statistics = {
                'total': total,
                'running': running,
                'completed': completed,
                'failed': failed,
                'pending': pending
            }
            
            self.statistics_updated.emit(self._statistics)
            
        except Exception as e:
            logger.error(f"更新统计信息失败: {e}")
            self.error_occurred.emit("statistics_update", str(e))
    
    # 任务操作方法
    def refresh_tasks(self, user_id: str = "default_user"):
        """刷新任务列表"""
        if not self.ui_service:
            self.error_occurred.emit("refresh", "UI服务未初始化")
            return
        
        try:
            tasks = self.ui_service.get_all_tasks(user_id=user_id)
            self.set_tasks(tasks)
            self.refresh_completed.emit(True, "任务列表刷新成功")
            logger.info(f"任务列表刷新成功，共 {len(tasks)} 个任务")
        except Exception as e:
            logger.error(f"刷新任务列表失败: {e}")
            self.refresh_completed.emit(False, str(e))
            self.error_occurred.emit("refresh", str(e))
    
    def start_task(self, task_id: str):
        """启动任务"""
        if not self.ui_service:
            self.error_occurred.emit("start_task", "UI服务未初始化")
            return
        
        try:
            self.ui_service.start_task(task_id)
            self.task_operation_result.emit("start", True, "任务启动成功")
            logger.info(f"任务启动成功: {task_id}")
            
            # 刷新任务状态
            self.refresh_tasks()
            
        except Exception as e:
            logger.error(f"启动任务失败: {e}")
            self.task_operation_result.emit("start", False, str(e))
            self.error_occurred.emit("start_task", str(e))
    
    def stop_task(self, task_id: str):
        """停止任务"""
        if not self.ui_service:
            self.error_occurred.emit("stop_task", "UI服务未初始化")
            return
        
        try:
            self.ui_service.stop_task(task_id)
            self.task_operation_result.emit("stop", True, "任务停止成功")
            logger.info(f"任务停止成功: {task_id}")
            
            # 刷新任务状态
            self.refresh_tasks()
            
        except Exception as e:
            logger.error(f"停止任务失败: {e}")
            self.task_operation_result.emit("stop", False, str(e))
            self.error_occurred.emit("stop_task", str(e))
    
    def delete_task(self, task_id: str):
        """删除任务"""
        if not self.ui_service:
            self.error_occurred.emit("delete_task", "UI服务未初始化")
            return
        
        try:
            self.ui_service.delete_task(task_id)
            self.task_operation_result.emit("delete", True, "任务删除成功")
            logger.info(f"任务删除成功: {task_id}")
            
            # 从本地列表中移除任务
            self._all_tasks = [t for t in self._all_tasks if t.task_id != task_id]
            self._apply_filters()
            self.task_removed.emit(task_id)
            
            # 如果删除的是选中任务，清除选择
            if self._selected_task_id == task_id:
                self._selected_task_id = None
            
        except Exception as e:
            logger.error(f"删除任务失败: {e}")
            self.task_operation_result.emit("delete", False, str(e))
            self.error_occurred.emit("delete_task", str(e))
    
    def copy_task(self, task_id: str, user_id: str = "default_user"):
        """复制任务"""
        if not self.ui_service:
            self.error_occurred.emit("copy_task", "UI服务未初始化")
            return
        
        try:
            # 获取原任务
            original_task = self.get_task_by_id(task_id)
            if not original_task:
                self.error_occurred.emit("copy_task", "找不到要复制的任务")
                return
            
            # 创建复制配置
            config = original_task.config.copy() if original_task.config else {}
            config["task_name"] = f"{original_task.name} (副本)"
            config["description"] = original_task.description
            config["task_type"] = original_task.task_type
            config["priority"] = original_task.priority
            
            # 创建新任务
            new_task_id = self.ui_service.create_task(user_id=user_id, config=config)
            self.task_operation_result.emit("copy", True, f"任务复制成功！新任务ID: {new_task_id}")
            logger.info(f"任务复制成功: {task_id} -> {new_task_id}")
            
            # 刷新任务列表
            self.refresh_tasks(user_id)
            
        except Exception as e:
            logger.error(f"复制任务失败: {e}")
            self.task_operation_result.emit("copy", False, str(e))
            self.error_occurred.emit("copy_task", str(e))
    
    def get_task_details(self, task_id: str) -> Optional[Task]:
        """获取任务详情"""
        if not self.ui_service:
            return None
        
        try:
            return self.ui_service.get_task(task_id)
        except Exception as e:
            logger.error(f"获取任务详情失败: {e}")
            self.error_occurred.emit("get_task_details", str(e))
            return None
    
    # 任务状态和进度更新
    def update_task_status(self, task_id: str, status: TaskStatus):
        """更新任务状态"""
        try:
            # 更新本地任务状态
            for task in self._all_tasks:
                if task.task_id == task_id:
                    task.status = status
                    break
            
            # 重新应用过滤
            self._apply_filters()
            
            # 发射状态变化信号
            self.task_status_changed.emit(task_id, status)
            
            logger.debug(f"任务状态已更新: {task_id} -> {status.value}")
            
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
            self.error_occurred.emit("update_status", str(e))
    
    def update_task_progress(self, task_id: str, progress: int, message: str = ""):
        """更新任务进度"""
        try:
            self.task_progress_updated.emit(task_id, progress, message)
            logger.debug(f"任务进度已更新: {task_id} -> {progress}% ({message})")
        except Exception as e:
            logger.error(f"更新任务进度失败: {e}")
            self.error_occurred.emit("update_progress", str(e))
    
    # 自动刷新控制
    def set_auto_refresh(self, enabled: bool, interval: int = 5000):
        """设置自动刷新"""
        self._auto_refresh_enabled = enabled
        self._auto_refresh_interval = interval
        
        if enabled:
            self._refresh_timer.start(interval)
        else:
            self._refresh_timer.stop()
        
        logger.info(f"自动刷新{'启用' if enabled else '禁用'}，间隔: {interval}ms")
    
    def _auto_refresh(self):
        """自动刷新任务列表"""
        if self._auto_refresh_enabled:
            self.refresh_tasks()
    
    # 清理资源
    def cleanup(self):
        """清理资源"""
        try:
            self._refresh_timer.stop()
            self._all_tasks.clear()
            self._filtered_tasks.clear()
            self._selected_task_id = None
            logger.info("任务列表Model资源清理完成")
        except Exception as e:
            logger.error(f"清理任务列表Model资源失败: {e}")