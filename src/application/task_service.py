"""任务服务模块.

提供任务相关的业务逻辑和服务实现。
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from loguru import logger

from ..core.task_manager import TaskManager


class TaskService:
    """任务服务类.
    
    提供任务相关的业务逻辑和服务实现。
    """
    
    def __init__(self, task_manager: TaskManager):
        """初始化任务服务.
        
        Args:
            task_manager: 任务管理器实例
        """
        self.task_manager = task_manager
        logger.info("任务服务初始化完成")
    
    def create_task(self, name: str, description: str = "", 
                   priority: str = "medium", task_type: str = "general",
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """创建新任务.
        
        Args:
            name: 任务名称
            description: 任务描述
            priority: 任务优先级
            task_type: 任务类型
            metadata: 任务元数据
            
        Returns:
            str: 任务ID
        """
        try:
            task_id = self.task_manager.create_task(
                name=name,
                description=description,
                priority=priority,
                metadata=metadata or {}
            )
            logger.info(f"创建任务成功: {name} (ID: {task_id})")
            return task_id
        except Exception as e:
            logger.error(f"创建任务失败: {str(e)}")
            raise
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取指定任务.
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Dict[str, Any]]: 任务信息
        """
        try:
            return self.task_manager.get_task(task_id)
        except Exception as e:
            logger.error(f"获取任务失败: {str(e)}")
            return None
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务.
        
        Returns:
            List[Dict[str, Any]]: 任务列表
        """
        try:
            return self.task_manager.get_all_tasks()
        except Exception as e:
            logger.error(f"获取任务列表失败: {str(e)}")
            return []
    
    def update_task(self, task_id: str, **kwargs) -> bool:
        """更新任务信息.
        
        Args:
            task_id: 任务ID
            **kwargs: 更新的字段
            
        Returns:
            bool: 更新是否成功
        """
        try:
            self.task_manager.update_task(task_id, **kwargs)
            logger.info(f"更新任务成功: {task_id}")
            return True
        except Exception as e:
            logger.error(f"更新任务失败: {str(e)}")
            return False
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务.
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            self.task_manager.delete_task(task_id)
            logger.info(f"删除任务成功: {task_id}")
            return True
        except Exception as e:
            logger.error(f"删除任务失败: {str(e)}")
            return False
    
    def start_task(self, task_id: str) -> bool:
        """启动任务.
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 启动是否成功
        """
        try:
            self.task_manager.start_task(task_id)
            logger.info(f"启动任务成功: {task_id}")
            return True
        except Exception as e:
            logger.error(f"启动任务失败: {str(e)}")
            return False
    
    def pause_task(self, task_id: str) -> bool:
        """暂停任务.
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 暂停是否成功
        """
        try:
            self.task_manager.pause_task(task_id)
            logger.info(f"暂停任务成功: {task_id}")
            return True
        except Exception as e:
            logger.error(f"暂停任务失败: {str(e)}")
            return False
    
    def stop_task(self, task_id: str) -> bool:
        """停止任务.
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 停止是否成功
        """
        try:
            self.task_manager.stop_task(task_id)
            logger.info(f"停止任务成功: {task_id}")
            return True
        except Exception as e:
            logger.error(f"停止任务失败: {str(e)}")
            return False
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """获取任务统计信息.
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            tasks = self.get_all_tasks()
            
            stats = {
                'total': len(tasks),
                'pending': 0,
                'running': 0,
                'completed': 0,
                'failed': 0,
                'paused': 0
            }
            
            for task in tasks:
                status = task.get('status', 'pending')
                if status in stats:
                    stats[status] += 1
            
            return stats
        except Exception as e:
            logger.error(f"获取任务统计失败: {str(e)}")
            return {}
    
    def get_tasks_by_status(self, status: str) -> List[Dict[str, Any]]:
        """根据状态获取任务.
        
        Args:
            status: 任务状态
            
        Returns:
            List[Dict[str, Any]]: 任务列表
        """
        try:
            all_tasks = self.get_all_tasks()
            return [task for task in all_tasks if task.get('status') == status]
        except Exception as e:
            logger.error(f"根据状态获取任务失败: {str(e)}")
            return []
    
    def get_tasks_by_priority(self, priority: str) -> List[Dict[str, Any]]:
        """根据优先级获取任务.
        
        Args:
            priority: 任务优先级
            
        Returns:
            List[Dict[str, Any]]: 任务列表
        """
        try:
            all_tasks = self.get_all_tasks()
            return [task for task in all_tasks if task.get('priority') == priority]
        except Exception as e:
            logger.error(f"根据优先级获取任务失败: {str(e)}")
            return []
