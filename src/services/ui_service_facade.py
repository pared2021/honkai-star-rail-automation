"""UI服务门面

为UI层提供简化的服务接口，隐藏复杂的业务逻辑。
"""

from typing import Optional, Dict, Any, List, Tuple
import logging
from abc import ABC, abstractmethod

from ..core.dependency_injection import Injectable, inject
from .application_service import IApplicationService
from ..core.models.task import Task, TaskStatus

logger = logging.getLogger(__name__)


class IUIServiceFacade(ABC):
    """UI服务门面接口"""
    
    @abstractmethod
    def get_task_summary(self) -> Dict[str, Any]:
        """获取任务摘要信息"""
        pass
    
    @abstractmethod
    def create_simple_task(self, name: str, description: str = "") -> Tuple[bool, str]:
        """创建简单任务"""
        pass
    
    @abstractmethod
    def toggle_task_status(self, task_id: str) -> Tuple[bool, str]:
        """切换任务状态（启动/停止）"""
        pass
    
    @abstractmethod
    def get_ui_config(self) -> Dict[str, Any]:
        """获取UI相关配置"""
        pass
    
    @abstractmethod
    def update_ui_config(self, config: Dict[str, Any]) -> bool:
        """更新UI配置"""
        pass
    
    @abstractmethod
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据"""
        pass


@inject
class UIServiceFacade(Injectable, IUIServiceFacade):
    """UI服务门面实现
    
    为UI层提供简化的服务接口，封装复杂的业务逻辑。
    """
    
    def __init__(self, app_service: IApplicationService):
        super().__init__()
        self._app_service = app_service
        
        logger.debug("UIServiceFacade 初始化完成")
    
    def get_task_summary(self) -> Dict[str, Any]:
        """获取任务摘要信息"""
        try:
            tasks = self._app_service.get_task_list()
            
            summary = {
                'total_count': len(tasks),
                'running_count': 0,
                'completed_count': 0,
                'failed_count': 0,
                'pending_count': 0,
                'recent_tasks': []
            }
            
            for task in tasks:
                if task.status == TaskStatus.RUNNING:
                    summary['running_count'] += 1
                elif task.status == TaskStatus.COMPLETED:
                    summary['completed_count'] += 1
                elif task.status == TaskStatus.FAILED:
                    summary['failed_count'] += 1
                elif task.status == TaskStatus.PENDING:
                    summary['pending_count'] += 1
            
            # 获取最近的5个任务
            recent_tasks = sorted(tasks, key=lambda t: t.created_at, reverse=True)[:5]
            summary['recent_tasks'] = [
                {
                    'id': task.id,
                    'name': task.name,
                    'status': task.status.value,
                    'created_at': task.created_at.isoformat() if task.created_at else None
                }
                for task in recent_tasks
            ]
            
            return summary
            
        except Exception as e:
            logger.error(f"获取任务摘要失败: {e}")
            return {
                'total_count': 0,
                'running_count': 0,
                'completed_count': 0,
                'failed_count': 0,
                'pending_count': 0,
                'recent_tasks': []
            }
    
    def create_simple_task(self, name: str, description: str = "") -> Tuple[bool, str]:
        """创建简单任务
        
        Returns:
            Tuple[bool, str]: (是否成功, 任务ID或错误信息)
        """
        try:
            if not name.strip():
                return False, "任务名称不能为空"
            
            task_data = {
                'name': name.strip(),
                'description': description.strip(),
                'status': TaskStatus.PENDING.value,
                'priority': 'medium'
            }
            
            task_id = self._app_service.create_task(task_data)
            if task_id:
                return True, task_id
            else:
                return False, "创建任务失败"
                
        except Exception as e:
            logger.error(f"创建简单任务失败: {e}")
            return False, f"创建任务失败: {str(e)}"
    
    def toggle_task_status(self, task_id: str) -> Tuple[bool, str]:
        """切换任务状态（启动/停止）
        
        Returns:
            Tuple[bool, str]: (是否成功, 状态信息)
        """
        try:
            tasks = self._app_service.get_task_list()
            task = next((t for t in tasks if t.id == task_id), None)
            
            if not task:
                return False, "任务不存在"
            
            if task.status == TaskStatus.RUNNING:
                success = self._app_service.stop_task(task_id)
                return success, "任务已停止" if success else "停止任务失败"
            elif task.status in [TaskStatus.PENDING, TaskStatus.PAUSED]:
                success = self._app_service.start_task(task_id)
                return success, "任务已启动" if success else "启动任务失败"
            else:
                return False, f"任务状态为 {task.status.value}，无法切换"
                
        except Exception as e:
            logger.error(f"切换任务状态失败: {e}")
            return False, f"操作失败: {str(e)}"
    
    def get_ui_config(self) -> Dict[str, Any]:
        """获取UI相关配置"""
        try:
            return {
                'theme': self._app_service.get_config('ui.theme', 'light'),
                'language': self._app_service.get_config('ui.language', 'zh_CN'),
                'auto_refresh': self._app_service.get_config('ui.auto_refresh', True),
                'refresh_interval': self._app_service.get_config('ui.refresh_interval', 5000),
                'show_notifications': self._app_service.get_config('ui.show_notifications', True),
                'window_state': self._app_service.get_config('ui.window_state', {}),
                'recent_files': self._app_service.get_config('ui.recent_files', []),
                'toolbar_visible': self._app_service.get_config('ui.toolbar_visible', True),
                'statusbar_visible': self._app_service.get_config('ui.statusbar_visible', True)
            }
        except Exception as e:
            logger.error(f"获取UI配置失败: {e}")
            return {}
    
    def update_ui_config(self, config: Dict[str, Any]) -> bool:
        """更新UI配置"""
        try:
            success = True
            for key, value in config.items():
                ui_key = f'ui.{key}'
                if not self._app_service.set_config(ui_key, value):
                    success = False
                    logger.warning(f"设置UI配置失败: {ui_key}")
            
            return success
            
        except Exception as e:
            logger.error(f"更新UI配置失败: {e}")
            return False
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据"""
        try:
            task_summary = self.get_task_summary()
            system_status = self._app_service.get_system_status()
            
            return {
                'task_summary': task_summary,
                'system_status': system_status,
                'timestamp': self._get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"获取仪表板数据失败: {e}")
            return {
                'task_summary': {},
                'system_status': {},
                'timestamp': self._get_current_timestamp()
            }
    
    def handle_config_import(self, file_path: str) -> Tuple[bool, str]:
        """处理配置导入
        
        Returns:
            Tuple[bool, str]: (是否成功, 结果信息)
        """
        try:
            success = self._app_service.import_config(file_path)
            return success, "配置导入成功" if success else "配置导入失败"
        except Exception as e:
            logger.error(f"处理配置导入失败: {e}")
            return False, f"导入失败: {str(e)}"
    
    def handle_config_export(self, file_path: str) -> Tuple[bool, str]:
        """处理配置导出
        
        Returns:
            Tuple[bool, str]: (是否成功, 结果信息)
        """
        try:
            success = self._app_service.export_config(file_path)
            return success, "配置导出成功" if success else "配置导出失败"
        except Exception as e:
            logger.error(f"处理配置导出失败: {e}")
            return False, f"导出失败: {str(e)}"
    
    def get_database_summary(self) -> Dict[str, Any]:
        """获取数据库摘要信息"""
        try:
            db_info = self._app_service.get_database_info()
            return {
                'connection_status': db_info.get('connected', False),
                'database_size': db_info.get('size', 0),
                'table_count': db_info.get('table_count', 0),
                'last_backup': db_info.get('last_backup', None)
            }
        except Exception as e:
            logger.error(f"获取数据库摘要失败: {e}")
            return {
                'connection_status': False,
                'database_size': 0,
                'table_count': 0,
                'last_backup': None
            }
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()