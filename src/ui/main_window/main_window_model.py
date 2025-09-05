"""主窗口Model层

管理主窗口的数据状态和业务逻辑
"""

from typing import Optional, Dict, Any, List
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from datetime import datetime
import logging

from ...core.models.task import Task, TaskStatus
from ...services.ui_service_facade import IUIServiceFacade

logger = logging.getLogger(__name__)


class MainWindowModel(QObject):
    """主窗口Model层
    
    管理主窗口的数据状态和业务逻辑
    """
    
    # 数据变化信号
    automation_status_changed = pyqtSignal(bool)  # 自动化状态变化 (is_running)
    current_task_changed = pyqtSignal(str)  # 当前任务变化 (task_id)
    status_message_changed = pyqtSignal(str)  # 状态消息变化 (message)
    tab_changed = pyqtSignal(int)  # 标签页变化 (tab_index)
    window_state_changed = pyqtSignal(dict)  # 窗口状态变化 (state_dict)
    
    # 错误信号
    error_occurred = pyqtSignal(str, str)  # 错误发生 (operation, error_message)
    
    def __init__(self, ui_service: Optional[IUIServiceFacade] = None):
        super().__init__()
        
        # 依赖注入
        self.ui_service = ui_service
        
        # 状态数据
        self._is_automation_running = False
        self._current_task_id: Optional[str] = None
        self._status_message = "就绪"
        self._current_tab_index = 0
        self._window_state = {
            'geometry': None,
            'splitter_sizes': None,
            'tab_index': 0
        }
        
        # 状态历史
        self._status_history: List[Dict[str, Any]] = []
        self._max_history_size = 100
        
        # 定时器
        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._update_periodic_status)
        
        logger.debug("MainWindowModel 初始化完成")
    
    # 属性访问器
    @property
    def is_automation_running(self) -> bool:
        """获取自动化运行状态"""
        return self._is_automation_running
    
    @property
    def current_task_id(self) -> Optional[str]:
        """获取当前任务ID"""
        return self._current_task_id
    
    @property
    def status_message(self) -> str:
        """获取状态消息"""
        return self._status_message
    
    @property
    def current_tab_index(self) -> int:
        """获取当前标签页索引"""
        return self._current_tab_index
    
    @property
    def window_state(self) -> Dict[str, Any]:
        """获取窗口状态"""
        return self._window_state.copy()
    
    # 状态设置方法
    def set_automation_running(self, running: bool):
        """设置自动化运行状态
        
        Args:
            running: 是否运行中
        """
        if self._is_automation_running != running:
            self._is_automation_running = running
            self.automation_status_changed.emit(running)
            
            # 更新状态消息
            status_msg = "运行中" if running else "就绪"
            self.set_status_message(status_msg)
            
            # 记录状态历史
            self._add_status_history("automation_status", {
                'running': running,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"自动化状态变更: {'运行中' if running else '停止'}")
    
    def set_current_task(self, task_id: Optional[str]):
        """设置当前任务
        
        Args:
            task_id: 任务ID，None表示无任务
        """
        if self._current_task_id != task_id:
            old_task_id = self._current_task_id
            self._current_task_id = task_id
            self.current_task_changed.emit(task_id or "")
            
            # 记录状态历史
            self._add_status_history("current_task", {
                'old_task_id': old_task_id,
                'new_task_id': task_id,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"当前任务变更: {old_task_id} -> {task_id}")
    
    def set_status_message(self, message: str):
        """设置状态消息
        
        Args:
            message: 状态消息
        """
        if self._status_message != message:
            self._status_message = message
            self.status_message_changed.emit(message)
            
            # 记录状态历史
            self._add_status_history("status_message", {
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.debug(f"状态消息变更: {message}")
    
    def set_current_tab(self, tab_index: int):
        """设置当前标签页
        
        Args:
            tab_index: 标签页索引
        """
        if self._current_tab_index != tab_index:
            self._current_tab_index = tab_index
            self._window_state['tab_index'] = tab_index
            self.tab_changed.emit(tab_index)
            
            logger.debug(f"标签页变更: {tab_index}")
    
    def set_window_state(self, state: Dict[str, Any]):
        """设置窗口状态
        
        Args:
            state: 窗口状态字典
        """
        self._window_state.update(state)
        self.window_state_changed.emit(self._window_state.copy())
        
        logger.debug(f"窗口状态更新: {state}")
    
    # 业务逻辑方法
    def start_automation(self, task_name: str = "自动化任务") -> Optional[str]:
        """启动自动化
        
        Args:
            task_name: 任务名称
        
        Returns:
            创建的任务ID，失败返回None
        """
        try:
            if self._is_automation_running:
                logger.warning("自动化已在运行中")
                return None
            
            # 创建新任务
            if self.ui_service:
                task_id = self.ui_service.create_simple_task(task_name)
            else:
                # 生成临时任务ID
                import uuid
                task_id = str(uuid.uuid4())
            
            # 更新状态
            self.set_current_task(task_id)
            self.set_automation_running(True)
            
            logger.info(f"自动化启动成功: {task_id}")
            return task_id
            
        except Exception as e:
            error_msg = f"启动自动化失败: {e}"
            logger.error(error_msg)
            self.error_occurred.emit("start_automation", str(e))
            return None
    
    def stop_automation(self) -> bool:
        """停止自动化
        
        Returns:
            是否成功停止
        """
        try:
            if not self._is_automation_running:
                logger.warning("自动化未在运行")
                return True
            
            # 更新任务状态
            if self._current_task_id and self.ui_service:
                self.ui_service.toggle_task_status(self._current_task_id, "cancelled")
            
            # 更新状态
            task_id = self._current_task_id
            self.set_automation_running(False)
            self.set_current_task(None)
            
            logger.info(f"自动化停止成功: {task_id}")
            return True
            
        except Exception as e:
            error_msg = f"停止自动化失败: {e}"
            logger.error(error_msg)
            self.error_occurred.emit("stop_automation", str(e))
            return False
    
    def get_current_task(self) -> Optional[Task]:
        """获取当前任务对象
        
        Returns:
            当前任务对象，如果没有则返回None
        """
        if not self._current_task_id or not self.ui_service:
            return None
        
        try:
            # 通过服务门面获取任务摘要，然后转换为Task对象
            task_summary = self.ui_service.get_task_summary()
            # 这里需要根据实际的Task类结构来构造对象
            # 暂时返回None，具体实现需要根据Task类的构造函数调整
            return None
        except Exception as e:
            logger.error(f"获取当前任务失败: {e}")
            return None
    
    def update_task_status(self, task_id: str, status: TaskStatus):
        """更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
        """
        try:
            if self.ui_service:
                self.ui_service.toggle_task_status(task_id, status.value)
            
            # 如果是当前任务，更新相关状态
            if task_id == self._current_task_id:
                if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    self.set_automation_running(False)
                    self.set_current_task(None)
            
            logger.debug(f"任务状态更新: {task_id} -> {status.value}")
            
        except Exception as e:
            error_msg = f"更新任务状态失败: {e}"
            logger.error(error_msg)
            self.error_occurred.emit("update_task_status", str(e))
    
    # 状态历史管理
    def _add_status_history(self, event_type: str, data: Dict[str, Any]):
        """添加状态历史记录
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        history_entry = {
            'event_type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        self._status_history.append(history_entry)
        
        # 限制历史记录大小
        if len(self._status_history) > self._max_history_size:
            self._status_history = self._status_history[-self._max_history_size:]
    
    def get_status_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取状态历史
        
        Args:
            limit: 返回记录数量限制
        
        Returns:
            状态历史记录列表
        """
        return self._status_history[-limit:] if limit > 0 else self._status_history.copy()
    
    def clear_status_history(self):
        """清除状态历史"""
        self._status_history.clear()
        logger.debug("状态历史已清除")
    
    # 定时器控制
    def start_status_timer(self, interval: int = 1000):
        """启动状态定时器
        
        Args:
            interval: 更新间隔（毫秒）
        """
        self._status_timer.start(interval)
        logger.debug(f"状态定时器启动，间隔: {interval}ms")
    
    def stop_status_timer(self):
        """停止状态定时器"""
        self._status_timer.stop()
        logger.debug("状态定时器停止")
    
    def _update_periodic_status(self):
        """定期状态更新"""
        try:
            # 更新时间显示
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 如果自动化正在运行，可以在这里添加更多状态检查
            if self._is_automation_running:
                # 检查任务状态等
                pass
            
        except Exception as e:
            logger.error(f"定期状态更新失败: {e}")
    
    # 配置管理
    def save_window_config(self):
        """保存窗口配置"""
        try:
            if self.ui_service:
                config_data = {
                    'window_state': self._window_state,
                    'current_tab': self._current_tab_index
                }
                self.ui_service.update_ui_config('main_window', config_data)
                logger.debug("窗口配置已保存")
                
        except Exception as e:
            logger.error(f"保存窗口配置失败: {e}")
    
    def load_window_config(self) -> Dict[str, Any]:
        """加载窗口配置
        
        Returns:
            窗口配置字典
        """
        try:
            if self.ui_service:
                config_data = self.ui_service.get_ui_config('main_window', {})
                
                # 恢复窗口状态
                if 'window_state' in config_data:
                    self.set_window_state(config_data['window_state'])
                
                # 恢复标签页
                if 'current_tab' in config_data:
                    self.set_current_tab(config_data['current_tab'])
                
                logger.debug("窗口配置已加载")
                return config_data
                
        except Exception as e:
            logger.error(f"加载窗口配置失败: {e}")
        
        return {}
    
    # 统计信息
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        try:
            stats = {
                'automation_running': self._is_automation_running,
                'current_task_id': self._current_task_id,
                'status_message': self._status_message,
                'current_tab': self._current_tab_index,
                'history_count': len(self._status_history),
                'timer_active': self._status_timer.isActive()
            }
            
            # 如果有服务门面，获取任务统计
            if self.ui_service:
                try:
                    task_summary = self.ui_service.get_task_summary()
                    stats['task_summary'] = task_summary
                except Exception as e:
                    logger.warning(f"获取任务统计失败: {e}")
            
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    # 清理资源
    def cleanup(self):
        """清理资源"""
        try:
            # 停止定时器
            self.stop_status_timer()
            
            # 保存配置
            self.save_window_config()
            
            # 如果自动化正在运行，停止它
            if self._is_automation_running:
                self.stop_automation()
            
            logger.debug("MainWindowModel 资源清理完成")
            
        except Exception as e:
            logger.error(f"清理MainWindowModel资源失败: {e}")