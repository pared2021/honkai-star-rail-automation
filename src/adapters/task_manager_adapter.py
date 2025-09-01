# -*- coding: utf-8 -*-
"""
任务管理器适配器 - 将旧的TaskManager接口适配到新的TaskService架构
"""

import asyncio
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from loguru import logger

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from models.unified_models import Task, TaskConfig, TaskStatus, TaskType, TaskPriority
from services.task_service import TaskService
from adapters.sync_adapter import get_global_sync_adapter, async_to_sync
from repositories.sqlite_task_repository import SQLiteTaskRepository
from database.db_manager import DatabaseManager


class TaskManagerAdapter:
    """
    任务管理器适配器
    
    将旧的TaskManager接口适配到新的TaskService架构，
    保持向后兼容性的同时使用新的统一数据模型。
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化适配器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager
        self.sync_adapter = get_global_sync_adapter()
        
        # 初始化仓储和服务
        self.repository = SQLiteTaskRepository(db_manager.get_db_path())
        self.task_service = TaskService(self.repository)
        
        # 启动异步服务
        self._start_services()
        
        logger.info("TaskManager适配器初始化完成")
    
    def _start_services(self):
        """启动异步服务"""
        try:
            # 启动同步适配器
            if not self.sync_adapter.is_running():
                self.sync_adapter.start()
            
            # 启动任务服务
            self.sync_adapter.run_async_blocking(self.task_service.start())
            
            logger.info("异步服务启动完成")
        except Exception as e:
            logger.error(f"启动异步服务失败: {e}")
            raise
    
    def close(self):
        """关闭适配器"""
        try:
            # 停止任务服务
            self.sync_adapter.run_async_blocking(self.task_service.stop())
            
            # 停止同步适配器
            self.sync_adapter.stop()
            
            logger.info("TaskManager适配器已关闭")
        except Exception as e:
            logger.error(f"关闭适配器失败: {e}")
    
    # ==================== 任务创建和管理 ====================
    
    def create_task_sync(self, config: Union[TaskConfig, Dict[str, Any]], user_id: str = "default") -> str:
        """
        同步创建任务（兼容旧接口）
        
        Args:
            config: 任务配置（支持TaskConfig对象或字典）
            user_id: 用户ID
            
        Returns:
            str: 任务ID
        """
        try:
            # 转换配置格式
            if isinstance(config, dict):
                task_config = self._convert_dict_to_task_config(config)
            else:
                task_config = config
            
            # 异步创建任务
            task_id = self.sync_adapter.run_async_blocking(
                self.task_service.create_task(task_config, user_id)
            )
            
            logger.info(f"任务创建成功: {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            raise
    
    async def create_task(self, config: Union[TaskConfig, Dict[str, Any]], user_id: str = "default") -> str:
        """
        异步创建任务
        
        Args:
            config: 任务配置
            user_id: 用户ID
            
        Returns:
            str: 任务ID
        """
        if isinstance(config, dict):
            task_config = self._convert_dict_to_task_config(config)
        else:
            task_config = config
        
        return await self.task_service.create_task(task_config, user_id)
    
    def get_task_sync(self, task_id: str) -> Optional[Task]:
        """
        同步获取任务（兼容旧接口）
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Task]: 任务对象
        """
        try:
            task = self.sync_adapter.run_async_blocking(
                self.task_service.get_task(task_id)
            )
            return task
        except Exception as e:
            logger.error(f"获取任务失败: {e}")
            return None
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        同步获取任务（保持兼容性）
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Task]: 任务对象
        """
        return self.get_task_sync(task_id)
    
    async def get_task_async(self, task_id: str) -> Optional[Task]:
        """
        异步获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Task]: 任务对象
        """
        return await self.task_service.get_task(task_id)
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新任务（兼容旧接口）
        
        Args:
            task_id: 任务ID
            updates: 更新数据
            
        Returns:
            bool: 是否成功
        """
        try:
            # 转换更新数据格式
            task_updates = self._convert_dict_to_task_updates(updates)
            
            # 异步更新任务
            self.sync_adapter.run_async_blocking(
                self.task_service.update_task(task_id, task_updates)
            )
            
            logger.info(f"任务更新成功: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新任务失败: {e}")
            return False
    
    def delete_task(self, task_id: str) -> bool:
        """
        删除任务（兼容旧接口）
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功
        """
        try:
            self.sync_adapter.run_async_blocking(
                self.task_service.delete_task(task_id)
            )
            
            logger.info(f"任务删除成功: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除任务失败: {e}")
            return False
    
    # ==================== 任务查询 ====================
    
    def get_all_tasks(self) -> List[Task]:
        """
        获取所有任务（兼容旧接口）
        
        Returns:
            List[Task]: 任务列表
        """
        try:
            tasks = self.sync_adapter.run_async_blocking(
                self.task_service.list_tasks()
            )
            return tasks
        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            return []
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """
        根据状态获取任务
        
        Args:
            status: 任务状态
            
        Returns:
            List[Task]: 任务列表
        """
        try:
            tasks = self.sync_adapter.run_async_blocking(
                self.task_service.list_tasks(status=status)
            )
            return tasks
        except Exception as e:
            logger.error(f"根据状态获取任务失败: {e}")
            return []
    
    def get_tasks_by_type(self, task_type: TaskType) -> List[Task]:
        """
        根据类型获取任务
        
        Args:
            task_type: 任务类型
            
        Returns:
            List[Task]: 任务列表
        """
        try:
            tasks = self.sync_adapter.run_async_blocking(
                self.task_service.list_tasks(task_type=task_type)
            )
            return tasks
        except Exception as e:
            logger.error(f"根据类型获取任务失败: {e}")
            return []
    
    def search_tasks(self, query: str) -> List[Task]:
        """
        搜索任务
        
        Args:
            query: 搜索关键词
            
        Returns:
            List[Task]: 任务列表
        """
        try:
            tasks = self.sync_adapter.run_async_blocking(
                self.task_service.search_tasks(query)
            )
            return tasks
        except Exception as e:
            logger.error(f"搜索任务失败: {e}")
            return []
    
    # ==================== 任务执行管理 ====================
    
    def start_task(self, task_id: str) -> bool:
        """
        启动任务执行
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功
        """
        try:
            self.sync_adapter.run_async_blocking(
                self.task_service.start_task_execution(task_id)
            )
            
            logger.info(f"任务启动成功: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"启动任务失败: {e}")
            return False
    
    def stop_task(self, task_id: str) -> bool:
        """
        停止任务执行
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功
        """
        try:
            self.sync_adapter.run_async_blocking(
                self.task_service.stop_task_execution(task_id)
            )
            
            logger.info(f"任务停止成功: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"停止任务失败: {e}")
            return False
    
    def pause_task(self, task_id: str) -> bool:
        """
        暂停任务执行
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功
        """
        try:
            self.sync_adapter.run_async_blocking(
                self.task_service.pause_task_execution(task_id)
            )
            
            logger.info(f"任务暂停成功: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"暂停任务失败: {e}")
            return False
    
    def resume_task(self, task_id: str) -> bool:
        """
        恢复任务执行
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功
        """
        try:
            self.sync_adapter.run_async_blocking(
                self.task_service.resume_task_execution(task_id)
            )
            
            logger.info(f"任务恢复成功: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"恢复任务失败: {e}")
            return False
    
    # ==================== 统计和监控 ====================
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """
        获取任务统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            stats = self.sync_adapter.run_async_blocking(
                self.task_service.get_task_statistics()
            )
            return stats
        except Exception as e:
            logger.error(f"获取任务统计失败: {e}")
            return {}
    
    def get_running_tasks(self) -> List[Task]:
        """
        获取正在运行的任务
        
        Returns:
            List[Task]: 运行中的任务列表
        """
        return self.get_tasks_by_status(TaskStatus.RUNNING)
    
    def get_pending_tasks(self) -> List[Task]:
        """
        获取待执行的任务
        
        Returns:
            List[Task]: 待执行的任务列表
        """
        return self.get_tasks_by_status(TaskStatus.PENDING)
    
    # ==================== 数据转换方法 ====================
    
    def _convert_dict_to_task_config(self, config_dict: Dict[str, Any]) -> TaskConfig:
        """
        将字典转换为TaskConfig对象
        
        Args:
            config_dict: 配置字典
            
        Returns:
            TaskConfig: 任务配置对象
        """
        # 提取基本字段
        name = config_dict.get('name', '')
        description = config_dict.get('description', '')
        
        # 转换枚举类型
        task_type = config_dict.get('task_type', TaskType.CUSTOM)
        if isinstance(task_type, str):
            task_type = TaskType(task_type)
        
        priority = config_dict.get('priority', TaskPriority.MEDIUM)
        if isinstance(priority, str):
            priority = TaskPriority(priority)
        
        # 提取其他配置
        max_retry_count = config_dict.get('max_retry_count', config_dict.get('retry_count', 3))
        timeout_seconds = config_dict.get('timeout_seconds', config_dict.get('max_duration', 300))
        actions = config_dict.get('actions', [])
        custom_params = config_dict.get('custom_params', {})
        
        # 调度配置
        schedule_enabled = config_dict.get('schedule_enabled', False)
        schedule_time = config_dict.get('schedule_time')
        repeat_interval = config_dict.get('repeat_interval')
        
        return TaskConfig(
            name=name,
            description=description,
            task_type=task_type,
            priority=priority,
            max_retry_count=max_retry_count,
            timeout_seconds=timeout_seconds,
            actions=actions,
            custom_params=custom_params,
            schedule_enabled=schedule_enabled,
            schedule_time=schedule_time,
            repeat_interval=repeat_interval
        )
    
    def _convert_dict_to_task_updates(self, updates_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        将更新字典转换为标准格式
        
        Args:
            updates_dict: 更新字典
            
        Returns:
            Dict[str, Any]: 标准化的更新字典
        """
        # 转换枚举类型
        if 'task_type' in updates_dict and isinstance(updates_dict['task_type'], str):
            updates_dict['task_type'] = TaskType(updates_dict['task_type'])
        
        if 'priority' in updates_dict and isinstance(updates_dict['priority'], str):
            updates_dict['priority'] = TaskPriority(updates_dict['priority'])
        
        if 'status' in updates_dict and isinstance(updates_dict['status'], str):
            updates_dict['status'] = TaskStatus(updates_dict['status'])
        
        return updates_dict
    
    # ==================== 兼容性方法 ====================
    
    def execute_in_transaction(self, operations: List[callable]) -> bool:
        """
        在事务中执行多个操作（兼容旧接口）
        
        Args:
            operations: 操作列表
            
        Returns:
            bool: 是否成功
        """
        try:
            # 简单实现：顺序执行所有操作
            for operation in operations:
                operation()
            return True
        except Exception as e:
            logger.error(f"事务执行失败: {e}")
            return False
    
    def validate_task_config(self, config: Union[TaskConfig, Dict[str, Any]]) -> tuple[bool, str]:
        """
        验证任务配置（兼容旧接口）
        
        Args:
            config: 任务配置
            
        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        try:
            if isinstance(config, dict):
                task_config = self._convert_dict_to_task_config(config)
            else:
                task_config = config
            
            # 基本验证
            if not task_config.name.strip():
                return False, "任务名称不能为空"
            
            if task_config.timeout_seconds <= 0:
                return False, "超时时间必须大于0"
            
            if task_config.max_retry_count < 0:
                return False, "重试次数不能为负数"
            
            return True, ""
            
        except Exception as e:
            return False, f"配置验证失败: {e}"