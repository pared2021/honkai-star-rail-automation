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
from models.task_models import Task, TaskConfig, TaskStatus, TaskType, TaskPriority
from core.task_manager import TaskManager
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
        
        # 初始化仓储和统一的TaskManager
        self.repository = SQLiteTaskRepository(db_manager.get_db_path())
        self.task_manager = TaskManager(self.repository)
        
        # 启动异步服务
        self._start_services()
        
        logger.info("TaskManager适配器初始化完成")
    
    def _start_services(self):
        """启动异步服务"""
        try:
            # 启动同步适配器
            if not self.sync_adapter.is_running():
                self.sync_adapter.start()
            
            # 启动TaskManager
            self.sync_adapter.run_async_blocking(self.task_manager.start())
            
            logger.info("异步服务启动完成")
        except Exception as e:
            logger.error(f"启动异步服务失败: {e}")
            raise
    
    def close(self):
        """关闭适配器"""
        try:
            # 停止TaskManager
            self.sync_adapter.run_async_blocking(self.task_manager.stop())
            
            # 关闭并发执行系统
            self.task_manager.shutdown_concurrent_execution()
            
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
                self.task_manager.create_task_async(
                    user_id=user_id,
                    task_type=task_config.task_type.value,
                    config=self._task_config_to_dict(task_config),
                    priority=task_config.priority.value,
                    description=task_config.description
                )
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
        
        result = await self.task_manager.create_task_async(
            user_id=user_id,
            task_type=task_config.task_type.value,
            config=self._task_config_to_dict(task_config),
            priority=task_config.priority.value,
            description=task_config.description
        )
        return result.get('task_id')
    
    def get_task_sync(self, task_id: str) -> Optional[Task]:
        """
        同步获取任务（兼容旧接口）
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Task]: 任务对象
        """
        try:
            task_data = self.sync_adapter.run_async_blocking(
                self.task_manager.get_task_async(task_id, "default")
            )
            task = self._dict_to_task(task_data) if task_data else None
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
        task_data = await self.task_manager.get_task_async(task_id, "default")
        return self._dict_to_task(task_data) if task_data else None
    
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
                self.task_manager.update_task_async(task_id, "default", **task_updates)
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
                self.task_manager.delete_task_async(task_id, "default")
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
            task_data_list = self.sync_adapter.run_async_blocking(
                self.task_manager.list_tasks_async("default")
            )
            tasks = [self._dict_to_task(task_data) for task_data in task_data_list]
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
            task_data_list = self.sync_adapter.run_async_blocking(
                self.task_manager.list_tasks_async("default", status=status.value)
            )
            tasks = [self._dict_to_task(task_data) for task_data in task_data_list]
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
            task_data_list = self.sync_adapter.run_async_blocking(
                self.task_manager.list_tasks_async("default", task_type=task_type.value)
            )
            tasks = [self._dict_to_task(task_data) for task_data in task_data_list]
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
            task_data_list = self.sync_adapter.run_async_blocking(
                self.task_manager.search_tasks_async("default", query)
            )
            tasks = [self._dict_to_task(task_data) for task_data in task_data_list]
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
                self.task_manager.execute_task_async(task_id, "default")
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
            # 使用并发任务取消功能
            self.task_manager.cancel_concurrent_task(task_id)
            
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
            # 更新任务状态为暂停
            self.sync_adapter.run_async_blocking(
                self.task_manager.update_task_async(task_id, "default", status="paused")
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
            # 更新任务状态为运行中并重新执行
            self.sync_adapter.run_async_blocking(
                self.task_manager.update_task_async(task_id, "default", status="running")
            )
            self.sync_adapter.run_async_blocking(
                self.task_manager.execute_task_async(task_id, "default")
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
            # 获取并发执行状态作为统计信息
            stats = self.task_manager.get_concurrent_execution_status()
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
    
    def _task_config_to_dict(self, task_config: TaskConfig) -> Dict[str, Any]:
        """将TaskConfig对象转换为字典
        
        Args:
            task_config: TaskConfig对象
            
        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            'name': task_config.name,
            'description': task_config.description,
            'task_type': task_config.task_type.value,
            'priority': task_config.priority.value,
            'max_retry_count': task_config.max_retry_count,
            'timeout_seconds': task_config.timeout_seconds,
            'actions': task_config.actions,
            'custom_params': task_config.custom_params,
            'schedule_enabled': task_config.schedule_enabled,
            'schedule_time': task_config.schedule_time,
            'repeat_interval': task_config.repeat_interval
        }
    
    def _dict_to_task(self, task_data: Dict[str, Any]) -> Task:
        """将字典转换为Task对象
        
        Args:
            task_data: 任务数据字典
            
        Returns:
            Task: 任务对象
        """
        # 创建TaskConfig
        config = TaskConfig(
            name=task_data.get('config', {}).get('name', ''),
            description=task_data.get('description', ''),
            task_type=TaskType(task_data.get('task_type', 'custom')),
            priority=TaskPriority(task_data.get('priority', 'medium')),
            max_retry_count=task_data.get('config', {}).get('max_retry_count', 3),
            timeout_seconds=task_data.get('config', {}).get('timeout_seconds', 300),
            actions=task_data.get('config', {}).get('actions', []),
            custom_params=task_data.get('config', {}).get('custom_params', {}),
            schedule_enabled=task_data.get('config', {}).get('schedule_enabled', False),
            schedule_time=task_data.get('scheduled_at'),
            repeat_interval=task_data.get('config', {}).get('repeat_interval')
        )
        
        # 创建Task对象
        task = Task(
            task_id=task_data.get('task_id', ''),
            config=config,
            user_id=task_data.get('user_id', 'default'),
            status=TaskStatus(task_data.get('status', 'pending')),
            created_at=task_data.get('created_at'),
            updated_at=task_data.get('updated_at'),
            started_at=task_data.get('started_at'),
            completed_at=task_data.get('completed_at'),
            retry_count=task_data.get('retry_count', 0),
            last_error=task_data.get('last_error'),
            result=task_data.get('result'),
            parent_task_id=task_data.get('parent_task_id')
        )
        
        return task
    
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