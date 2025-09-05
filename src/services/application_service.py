"""应用服务层

提供UI层访问核心功能的统一接口，解耦UI层和核心层。
"""

from typing import Optional, Dict, Any, List
import logging
from abc import ABC, abstractmethod

from ..core.dependency_injection import Injectable, inject
from ..core.interfaces import (
    ITaskManager, IConfigManager, IDatabaseManager,
    ITaskScheduler, ITaskMonitor, IResourceManager
)
from ..core.models.task import Task, TaskStatus

logger = logging.getLogger(__name__)


class IApplicationService(ABC):
    """应用服务接口"""
    
    @abstractmethod
    def get_task_list(self) -> List[Task]:
        """获取任务列表"""
        pass
    
    @abstractmethod
    def create_task(self, task_data: Dict[str, Any]) -> Optional[str]:
        """创建任务"""
        pass
    
    @abstractmethod
    def update_task(self, task_id: str, task_data: Dict[str, Any]) -> bool:
        """更新任务"""
        pass
    
    @abstractmethod
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        pass
    
    @abstractmethod
    def start_task(self, task_id: str) -> bool:
        """启动任务"""
        pass
    
    @abstractmethod
    def stop_task(self, task_id: str) -> bool:
        """停止任务"""
        pass
    
    @abstractmethod
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置"""
        pass
    
    @abstractmethod
    def set_config(self, key: str, value: Any) -> bool:
        """设置配置"""
        pass
    
    @abstractmethod
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        pass


@inject
class ApplicationService(Injectable, IApplicationService):
    """应用服务实现
    
    封装核心管理器功能，为UI层提供统一的服务接口。
    """
    
    def __init__(self,
                 task_manager: ITaskManager,
                 config_manager: IConfigManager,
                 db_manager: IDatabaseManager,
                 scheduler: ITaskScheduler,
                 monitor: ITaskMonitor,
                 resource_manager: IResourceManager):
        super().__init__()
        self._task_manager = task_manager
        self._config_manager = config_manager
        self._db_manager = db_manager
        self._scheduler = scheduler
        self._monitor = monitor
        self._resource_manager = resource_manager
        
        logger.debug("ApplicationService 初始化完成")
    
    def get_task_list(self) -> List[Task]:
        """获取任务列表"""
        try:
            return self._task_manager.get_all_tasks()
        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            return []
    
    def create_task(self, task_data: Dict[str, Any]) -> Optional[str]:
        """创建任务"""
        try:
            task = Task.from_dict(task_data)
            return self._task_manager.add_task(task)
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            return None
    
    def update_task(self, task_id: str, task_data: Dict[str, Any]) -> bool:
        """更新任务"""
        try:
            task = self._task_manager.get_task(task_id)
            if not task:
                return False
            
            # 更新任务属性
            for key, value in task_data.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            
            return self._task_manager.update_task(task)
        except Exception as e:
            logger.error(f"更新任务失败: {e}")
            return False
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        try:
            return self._task_manager.remove_task(task_id)
        except Exception as e:
            logger.error(f"删除任务失败: {e}")
            return False
    
    def start_task(self, task_id: str) -> bool:
        """启动任务"""
        try:
            return self._task_manager.start_task(task_id)
        except Exception as e:
            logger.error(f"启动任务失败: {e}")
            return False
    
    def stop_task(self, task_id: str) -> bool:
        """停止任务"""
        try:
            return self._task_manager.stop_task(task_id)
        except Exception as e:
            logger.error(f"停止任务失败: {e}")
            return False
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置"""
        try:
            return self._config_manager.get(key, default)
        except Exception as e:
            logger.error(f"获取配置失败: {e}")
            return default
    
    def set_config(self, key: str, value: Any) -> bool:
        """设置配置"""
        try:
            self._config_manager.set(key, value)
            return True
        except Exception as e:
            logger.error(f"设置配置失败: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            return {
                'task_count': len(self.get_task_list()),
                'running_tasks': len([t for t in self.get_task_list() if t.status == TaskStatus.RUNNING]),
                'scheduler_status': self._scheduler.is_running() if hasattr(self._scheduler, 'is_running') else False,
                'monitor_status': self._monitor.is_monitoring() if hasattr(self._monitor, 'is_monitoring') else False,
                'resource_usage': self._resource_manager.get_system_resource_usage()
            }
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return {}
    
    def import_config(self, file_path: str) -> bool:
        """导入配置"""
        try:
            return self._config_manager.import_config(file_path)
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return False
    
    def export_config(self, file_path: str) -> bool:
        """导出配置"""
        try:
            return self._config_manager.export_config(file_path)
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """获取数据库信息"""
        try:
            return self._db_manager.get_database_info()
        except Exception as e:
            logger.error(f"获取数据库信息失败: {e}")
            return {}
    
    def backup_database(self, backup_path: str) -> bool:
        """备份数据库"""
        try:
            return self._db_manager.backup_database(backup_path)
        except Exception as e:
            logger.error(f"备份数据库失败: {e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """恢复数据库"""
        try:
            return self._db_manager.restore_database(backup_path)
        except Exception as e:
            logger.error(f"恢复数据库失败: {e}")
            return False