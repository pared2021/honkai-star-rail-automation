# -*- coding: utf-8 -*-
"""
任务管理器 - 负责任务的创建、查询、更新和删除操作
"""

import json
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from loguru import logger
from ..database.db_manager import DatabaseManager
from ..models.task_model import Task, TaskStatus, TaskType, TaskPriority
from ..automation.automation_controller import ActionType, AutomationAction


@dataclass
class TaskConfig:
    """任务配置数据结构"""
    # 基本信息
    task_name: str
    task_type: TaskType
    description: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    
    # 执行配置
    max_retry_count: int = 3
    timeout_seconds: int = 300
    auto_restart: bool = False
    
    # 调度配置
    schedule_enabled: bool = False
    schedule_time: Optional[str] = None  # "HH:MM" 格式
    schedule_days: List[str] = None  # ["monday", "tuesday", ...]
    
    # 操作序列
    actions: List[Dict[str, Any]] = None
    
    # 其他配置
    tags: List[str] = None
    custom_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.actions is None:
            self.actions = []
        if self.tags is None:
            self.tags = []
        if self.custom_params is None:
            self.custom_params = {}
        if self.schedule_days is None:
            self.schedule_days = []


# Task类已从models.task_model导入


class TaskManager:
    """任务管理器类"""
    
    def __init__(self, db_manager: DatabaseManager, default_user_id: str = "default_user"):
        """初始化任务管理器
        
        Args:
            db_manager: 数据库管理器
            default_user_id: 默认用户ID
        """
        self.db_manager = db_manager
        self.default_user_id = default_user_id
        logger.info("任务管理器初始化完成")
    
    def create_task(self, config: TaskConfig, user_id: Optional[str] = None) -> str:
        """创建新任务
        
        Args:
            config: 任务配置
            user_id: 用户ID，如果为None则使用默认用户
            
        Returns:
            str: 任务ID
        """
        if user_id is None:
            user_id = self.default_user_id
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 创建任务对象
        task = Task(
            task_id=task_id,
            user_id=user_id,
            config=config,
            status=TaskStatus.CREATED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 保存到数据库
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 插入任务基本信息
            cursor.execute(
                "INSERT INTO tasks (task_id, user_id, task_name, task_type, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (task_id, user_id, config.task_name, config.task_type.value, TaskStatus.CREATED.value, 
                 task.created_at.isoformat(), task.updated_at.isoformat())
            )
            
            # 插入任务配置
            config_data = asdict(config)
            config_data['task_type'] = config.task_type.value
            config_data['priority'] = config.priority.value
            
            cursor.execute(
                "INSERT INTO task_configs (config_id, task_id, config_key, config_value) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), task_id, "full_config", json.dumps(config_data, ensure_ascii=False))
            )
            
            conn.commit()
        
        logger.info(f"创建任务成功: {config.task_name} (ID: {task_id})")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务详情
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Task]: 任务对象，如果不存在则返回None
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取任务基本信息
            cursor.execute(
                "SELECT * FROM tasks WHERE task_id = ?",
                (task_id,)
            )
            task_row = cursor.fetchone()
            
            if not task_row:
                return None
            
            # 获取任务配置
            cursor.execute(
                "SELECT config_value FROM task_configs WHERE task_id = ? AND config_key = ?",
                (task_id, "full_config")
            )
            config_row = cursor.fetchone()
            
            if not config_row:
                logger.warning(f"任务 {task_id} 缺少配置信息")
                return None
            
            # 解析配置
            config_data = json.loads(config_row[0])
            config_data['task_type'] = TaskType(config_data['task_type'])
            config_data['priority'] = TaskPriority(config_data['priority'])
            config = TaskConfig(**config_data)
            
            # 创建任务对象
            task = Task(
                task_id=task_row['task_id'],
                user_id=task_row['user_id'],
                config=config,
                status=TaskStatus(task_row['status']),
                created_at=datetime.fromisoformat(task_row['created_at']) if task_row['created_at'] else None,
                updated_at=datetime.fromisoformat(task_row['updated_at']) if task_row['updated_at'] else None,
                last_executed_at=datetime.fromisoformat(task_row['last_executed_at']) if task_row.get('last_executed_at') else None,
                execution_count=task_row.get('execution_count', 0),
                success_count=task_row.get('success_count', 0),
                failure_count=task_row.get('failure_count', 0)
            )
            
            return task
    
    def update_task(self, task_id: str, config: Optional[TaskConfig] = None, 
                   status: Optional[TaskStatus] = None) -> bool:
        """更新任务
        
        Args:
            task_id: 任务ID
            config: 新的任务配置（可选）
            status: 新的任务状态（可选）
            
        Returns:
            bool: 是否更新成功
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查任务是否存在
            cursor.execute("SELECT 1 FROM tasks WHERE task_id = ?", (task_id,))
            if not cursor.fetchone():
                logger.warning(f"任务 {task_id} 不存在")
                return False
            
            # 更新任务基本信息
            update_fields = []
            update_values = []
            
            if config is not None:
                update_fields.extend(["task_name = ?", "task_type = ?"])
                update_values.extend([config.task_name, config.task_type.value])
            
            if status is not None:
                update_fields.append("status = ?")
                update_values.append(status.value)
            
            if update_fields:
                update_fields.append("updated_at = ?")
                update_values.append(datetime.now().isoformat())
                update_values.append(task_id)
                
                cursor.execute(
                    f"UPDATE tasks SET {', '.join(update_fields)} WHERE task_id = ?",
                    update_values
                )
            
            # 更新任务配置
            if config is not None:
                config_data = asdict(config)
                config_data['task_type'] = config.task_type.value
                config_data['priority'] = config.priority.value
                
                cursor.execute(
                    "UPDATE task_configs SET config_value = ? WHERE task_id = ? AND config_key = ?",
                    (json.dumps(config_data, ensure_ascii=False), task_id, "full_config")
                )
            
            conn.commit()
        
        logger.info(f"更新任务成功: {task_id}")
        return True
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否删除成功
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查任务是否存在
            cursor.execute("SELECT 1 FROM tasks WHERE task_id = ?", (task_id,))
            if not cursor.fetchone():
                logger.warning(f"任务 {task_id} 不存在")
                return False
            
            # 删除相关数据
            cursor.execute("DELETE FROM execution_logs WHERE task_id = ?", (task_id,))
            cursor.execute("DELETE FROM task_configs WHERE task_id = ?", (task_id,))
            cursor.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
            
            conn.commit()
        
        logger.info(f"删除任务成功: {task_id}")
        return True
    
    def list_tasks(self, user_id: Optional[str] = None, status: Optional[TaskStatus] = None,
                  task_type: Optional[TaskType] = None, limit: int = 100) -> List[Task]:
        """获取任务列表
        
        Args:
            user_id: 用户ID过滤（可选）
            status: 状态过滤（可选）
            task_type: 类型过滤（可选）
            limit: 返回数量限制
            
        Returns:
            List[Task]: 任务列表
        """
        if user_id is None:
            user_id = self.default_user_id
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 构建查询条件
            where_conditions = ["user_id = ?"]
            query_params = [user_id]
            
            if status is not None:
                where_conditions.append("status = ?")
                query_params.append(status.value)
            
            if task_type is not None:
                where_conditions.append("task_type = ?")
                query_params.append(task_type.value)
            
            query_params.append(limit)
            
            # 执行查询
            cursor.execute(
                f"SELECT task_id FROM tasks WHERE {' AND '.join(where_conditions)} ORDER BY created_at DESC LIMIT ?",
                query_params
            )
            
            task_ids = [row[0] for row in cursor.fetchall()]
        
        # 获取完整任务信息
        tasks = []
        for task_id in task_ids:
            task = self.get_task(task_id)
            if task:
                tasks.append(task)
        
        return tasks
    
    def get_task_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """获取任务统计信息
        
        Args:
            user_id: 用户ID（可选）
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        if user_id is None:
            user_id = self.default_user_id
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 总任务数
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ?", (user_id,))
            total_tasks = cursor.fetchone()[0]
            
            # 按状态统计
            cursor.execute(
                "SELECT status, COUNT(*) FROM tasks WHERE user_id = ? GROUP BY status",
                (user_id,)
            )
            status_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 按类型统计
            cursor.execute(
                "SELECT task_type, COUNT(*) FROM tasks WHERE user_id = ? GROUP BY task_type",
                (user_id,)
            )
            type_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 最近执行统计
            cursor.execute(
                "SELECT COUNT(*) FROM tasks WHERE user_id = ? AND last_executed_at > datetime('now', '-7 days')",
                (user_id,)
            )
            recent_executions = cursor.fetchone()[0]
        
        return {
            'total_tasks': total_tasks,
            'status_distribution': status_stats,
            'type_distribution': type_stats,
            'recent_executions': recent_executions,
            'user_id': user_id
        }