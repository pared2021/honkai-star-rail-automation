"""任务列表展示器

实现MVP模式中的Presenter层，处理任务列表的业务逻辑和数据绑定。
"""

import logging
from typing import List, Optional, Dict, Any
from PyQt6.QtCore import QObject, QTimer, pyqtSlot

from .task_list_view import TaskListView
from ...application.task_application_service import TaskApplicationService
from ...adapters.sync_adapter import SyncAdapter
from ...models.task_models import Task, TaskStatus, TaskType, TaskPriority
from ...core.task_manager import TaskConfig

logger = logging.getLogger(__name__)


class TaskListPresenter(QObject):
    """任务列表展示器
    
    MVP模式中的Presenter层，负责：
    1. 处理视图事件和用户交互
    2. 调用应用服务层执行业务逻辑
    3. 更新视图显示状态
    4. 管理数据流和状态同步
    """
    
    def __init__(self, 
                 view: TaskListView,
                 task_service: TaskApplicationService,
                 sync_adapter: SyncAdapter,
                 user_id: str = "default_user"):
        """初始化展示器
        
        Args:
            view: 任务列表视图接口
            task_service: 任务应用服务
            sync_adapter: 同步适配器
            user_id: 用户ID
        """
        super().__init__()
        
        self.view = view
        self.task_service = task_service
        self.sync_adapter = sync_adapter
        self.user_id = user_id
        
        # 当前数据状态
        self.current_tasks: List[Task] = []
        self.current_filters: Dict[str, Any] = {}
        self.selected_task_id: Optional[str] = None
        
        # 自动刷新定时器
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._auto_refresh)
        
        # 连接视图信号
        self._connect_view_signals()
        
        # 初始化过滤选项
        self._initialize_filter_options()
        
        logger.info(f"TaskListPresenter 初始化完成，用户ID: {user_id}")
    
    def _connect_view_signals(self):
        """连接视图信号"""
        try:
            # 任务操作信号
            self.view.task_selected.connect(self._on_task_selected)
            self.view.task_edit_requested.connect(self._on_task_edit_requested)
            self.view.task_delete_requested.connect(self._on_task_delete_requested)
            self.view.task_start_requested.connect(self._on_task_start_requested)
            self.view.task_stop_requested.connect(self._on_task_stop_requested)
            self.view.task_copy_requested.connect(self._on_task_copy_requested)
            
            # 过滤和刷新信号
            self.view.filter_changed.connect(self._on_filter_changed)
            self.view.refresh_requested.connect(self.refresh_tasks)
            
            logger.debug("视图信号连接完成")
            
        except Exception as e:
            logger.error(f"连接视图信号失败: {e}")
    
    def _initialize_filter_options(self):
        """初始化过滤选项"""
        try:
            # 设置过滤选项
            status_options = list(TaskStatus)
            type_options = list(TaskType)
            priority_options = list(TaskPriority)
            
            self.view.set_filter_options(status_options, type_options, priority_options)
            
            logger.debug("过滤选项初始化完成")
            
        except Exception as e:
            logger.error(f"初始化过滤选项失败: {e}")
    
    # 公共方法
    def initialize(self):
        """初始化展示器，加载初始数据"""
        try:
            logger.info("开始初始化任务列表展示器")
            
            # 设置加载状态
            self.view.set_loading_state(True)
            
            # 加载任务列表
            self.refresh_tasks()
            
            logger.info("任务列表展示器初始化完成")
            
        except Exception as e:
            logger.error(f"初始化展示器失败: {e}")
            self.view.show_error_dialog("初始化失败", f"初始化任务列表失败：{str(e)}")
        finally:
            self.view.set_loading_state(False)
    
    @pyqtSlot()
    def refresh_tasks(self):
        """刷新任务列表"""
        try:
            logger.debug("开始刷新任务列表")
            
            # 使用同步适配器获取任务列表
            async def get_tasks_callback():
                return await self.task_service.get_recent_tasks(user_id=self.user_id, limit=1000)
            
            def on_success(tasks: List[Task]):
                self.current_tasks = tasks
                self._apply_current_filters()
                self._update_statistics()
                logger.debug(f"任务列表刷新完成，共 {len(tasks)} 个任务")
            
            def on_error(error: Exception):
                logger.error(f"刷新任务列表失败: {error}")
                self.view.show_error_dialog("刷新失败", f"刷新任务列表失败：{str(error)}")
            
            # 异步执行
            self.sync_adapter.execute_async(
                get_tasks_callback,
                on_success,
                on_error
            )
            
        except Exception as e:
            logger.error(f"刷新任务列表异常: {e}")
            self.view.show_error_dialog("刷新失败", f"刷新任务列表失败：{str(e)}")
    
    def set_auto_refresh(self, enabled: bool, interval: int = 5000):
        """设置自动刷新
        
        Args:
            enabled: 是否启用自动刷新
            interval: 刷新间隔（毫秒）
        """
        if enabled:
            self.refresh_timer.start(interval)
            logger.info(f"自动刷新已启用，间隔: {interval}ms")
        else:
            self.refresh_timer.stop()
            logger.info("自动刷新已禁用")
        
        # 同步到视图
        self.view.set_auto_refresh(enabled, interval)
    
    def select_task(self, task_id: str):
        """选择指定任务
        
        Args:
            task_id: 要选择的任务ID
        """
        try:
            self.selected_task_id = task_id
            self.view.select_task(task_id)
            
            # 获取并显示任务详情
            task = self._find_task_by_id(task_id)
            self.view.show_task_details(task)
            
            # 更新按钮状态
            self.view.update_button_states(True, task)
            
            logger.debug(f"任务已选择: {task_id}")
            
        except Exception as e:
            logger.error(f"选择任务失败: {e}")
    
    def update_task_status(self, task_id: str, status: TaskStatus):
        """更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
        """
        try:
            # 更新本地缓存
            for task in self.current_tasks:
                if task.task_id == task_id:
                    task.status = status
                    break
            
            # 更新视图
            self.view.update_task_status(task_id, status)
            
            # 如果是当前选中的任务，更新详情
            if self.selected_task_id == task_id:
                task = self._find_task_by_id(task_id)
                self.view.show_task_details(task)
            
            # 更新统计信息
            self._update_statistics()
            
            logger.debug(f"任务状态已更新: {task_id} -> {status.value}")
            
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
    
    def update_task_progress(self, task_id: str, progress: int, message: str = ""):
        """更新任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度百分比 (0-100)
            message: 进度消息
        """
        try:
            # 更新视图
            self.view.update_task_progress(task_id, progress, message)
            
            logger.debug(f"任务进度已更新: {task_id} -> {progress}%")
            
        except Exception as e:
            logger.error(f"更新任务进度失败: {e}")
    
    # 私有方法
    def _apply_current_filters(self):
        """应用当前过滤条件"""
        try:
            filtered_tasks = self.current_tasks
            
            # 应用过滤条件
            if self.current_filters:
                filtered_tasks = self._filter_tasks(self.current_tasks, self.current_filters)
            
            # 更新视图显示
            self.view.display_tasks(filtered_tasks)
            
            logger.debug(f"过滤后显示 {len(filtered_tasks)} 个任务")
            
        except Exception as e:
            logger.error(f"应用过滤条件失败: {e}")
    
    def _filter_tasks(self, tasks: List[Task], filters: Dict[str, Any]) -> List[Task]:
        """过滤任务列表
        
        Args:
            tasks: 原始任务列表
            filters: 过滤条件
            
        Returns:
            过滤后的任务列表
        """
        filtered_tasks = []
        
        for task in tasks:
            # 状态过滤
            if filters.get('status') and task.status != filters['status']:
                continue
            
            # 类型过滤
            if filters.get('type') and task.task_type != filters['type']:
                continue
            
            # 优先级过滤
            if filters.get('priority') and task.priority != filters['priority']:
                continue
            
            # 文本搜索
            search_text = filters.get('search_text', '').lower()
            if search_text:
                task_text = f"{task.name} {task.description or ''}".lower()
                if search_text not in task_text:
                    continue
            
            filtered_tasks.append(task)
        
        return filtered_tasks
    
    def _update_statistics(self):
        """更新统计信息"""
        try:
            total_count = len(self.current_tasks)
            running_count = len([t for t in self.current_tasks if t.status == TaskStatus.RUNNING])
            completed_count = len([t for t in self.current_tasks if t.status == TaskStatus.COMPLETED])
            failed_count = len([t for t in self.current_tasks if t.status == TaskStatus.FAILED])
            pending_count = len([t for t in self.current_tasks if t.status == TaskStatus.PENDING])
            
            stats = {
                'total': total_count,
                'running': running_count,
                'completed': completed_count,
                'failed': failed_count,
                'pending': pending_count
            }
            
            self.view.update_statistics(stats)
            
        except Exception as e:
            logger.error(f"更新统计信息失败: {e}")
    
    def _find_task_by_id(self, task_id: str) -> Optional[Task]:
        """根据ID查找任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            找到的任务对象，如果不存在返回None
        """
        for task in self.current_tasks:
            if task.task_id == task_id:
                return task
        return None
    
    @pyqtSlot()
    def _auto_refresh(self):
        """自动刷新处理"""
        self.refresh_tasks()
    
    # 视图事件处理器
    @pyqtSlot(str)
    def _on_task_selected(self, task_id: str):
        """任务选择事件处理"""
        self.select_task(task_id)
    
    @pyqtSlot(str)
    def _on_task_edit_requested(self, task_id: str):
        """任务编辑请求处理"""
        try:
            # 这里可以发射信号给主窗口或直接打开编辑对话框
            logger.info(f"请求编辑任务: {task_id}")
            self.view.show_message(f"编辑任务功能待实现: {task_id}", "info")
            
        except Exception as e:
            logger.error(f"处理任务编辑请求失败: {e}")
            self.view.show_error_dialog("编辑失败", f"处理任务编辑请求失败：{str(e)}")
    
    @pyqtSlot(str)
    def _on_task_delete_requested(self, task_id: str):
        """任务删除请求处理"""
        try:
            # 显示确认对话框
            if not self.view.show_confirmation_dialog(
                "确认删除", 
                "确定要删除选中的任务吗？此操作不可撤销。"
            ):
                return
            
            # 使用同步适配器删除任务
            def delete_task_callback():
                return self.task_service.delete_task(task_id)
            
            def on_success(result):
                self.view.show_message("任务删除成功", "success")
                self.refresh_tasks()  # 刷新列表
                logger.info(f"任务删除成功: {task_id}")
            
            def on_error(error: Exception):
                logger.error(f"删除任务失败: {error}")
                self.view.show_error_dialog("删除失败", f"删除任务失败：{str(error)}")
            
            # 异步执行
            self.sync_adapter.execute_async(
                delete_task_callback,
                on_success,
                on_error
            )
            
        except Exception as e:
            logger.error(f"处理任务删除请求失败: {e}")
            self.view.show_error_dialog("删除失败", f"处理任务删除请求失败：{str(e)}")
    
    @pyqtSlot(str)
    def _on_task_start_requested(self, task_id: str):
        """任务启动请求处理"""
        try:
            # 使用同步适配器启动任务
            def start_task_callback():
                return self.task_service.start_task(task_id)
            
            def on_success(result):
                self.view.show_message("任务启动成功", "success")
                self.refresh_tasks()  # 刷新列表
                logger.info(f"任务启动成功: {task_id}")
            
            def on_error(error: Exception):
                logger.error(f"启动任务失败: {error}")
                self.view.show_error_dialog("启动失败", f"启动任务失败：{str(error)}")
            
            # 异步执行
            self.sync_adapter.execute_async(
                start_task_callback,
                on_success,
                on_error
            )
            
        except Exception as e:
            logger.error(f"处理任务启动请求失败: {e}")
            self.view.show_error_dialog("启动失败", f"处理任务启动请求失败：{str(e)}")
    
    @pyqtSlot(str)
    def _on_task_stop_requested(self, task_id: str):
        """任务停止请求处理"""
        try:
            # 使用同步适配器停止任务
            def stop_task_callback():
                return self.task_service.stop_task(task_id)
            
            def on_success(result):
                self.view.show_message("任务停止成功", "success")
                self.refresh_tasks()  # 刷新列表
                logger.info(f"任务停止成功: {task_id}")
            
            def on_error(error: Exception):
                logger.error(f"停止任务失败: {error}")
                self.view.show_error_dialog("停止失败", f"停止任务失败：{str(error)}")
            
            # 异步执行
            self.sync_adapter.execute_async(
                stop_task_callback,
                on_success,
                on_error
            )
            
        except Exception as e:
            logger.error(f"处理任务停止请求失败: {e}")
            self.view.show_error_dialog("停止失败", f"处理任务停止请求失败：{str(e)}")
    
    @pyqtSlot(str)
    def _on_task_copy_requested(self, task_id: str):
        """任务复制请求处理"""
        try:
            # 获取原任务
            original_task = self._find_task_by_id(task_id)
            if not original_task:
                self.view.show_error_dialog("复制失败", "找不到要复制的任务")
                return
            
            # 创建新的任务配置
            new_config = TaskConfig(
                task_name=f"{original_task.name} (副本)",
                description=original_task.description,
                task_type=original_task.task_type,
                priority=original_task.priority,
                **original_task.config  # 复制其他配置项
            )
            
            # 使用同步适配器创建新任务
            def copy_task_callback():
                return self.task_service.create_task(self.user_id, new_config)
            
            def on_success(new_task_id: str):
                self.view.show_message(f"任务复制成功！新任务ID: {new_task_id}", "success")
                self.refresh_tasks()  # 刷新列表
                logger.info(f"任务复制成功: {task_id} -> {new_task_id}")
            
            def on_error(error: Exception):
                logger.error(f"复制任务失败: {error}")
                self.view.show_error_dialog("复制失败", f"复制任务失败：{str(error)}")
            
            # 异步执行
            self.sync_adapter.execute_async(
                copy_task_callback,
                on_success,
                on_error
            )
            
        except Exception as e:
            logger.error(f"处理任务复制请求失败: {e}")
            self.view.show_error_dialog("复制失败", f"处理任务复制请求失败：{str(e)}")
    
    @pyqtSlot(dict)
    def _on_filter_changed(self, filters: Dict[str, Any]):
        """过滤条件变化处理"""
        try:
            self.current_filters = filters
            self._apply_current_filters()
            
            logger.debug(f"过滤条件已更新: {filters}")
            
        except Exception as e:
            logger.error(f"处理过滤条件变化失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        try:
            # 停止定时器
            if self.refresh_timer.isActive():
                self.refresh_timer.stop()
            
            logger.info("TaskListPresenter 资源清理完成")
            
        except Exception as e:
            logger.error(f"清理资源失败: {e}")