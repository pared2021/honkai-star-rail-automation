# -*- coding: utf-8 -*-
"""
SQLite任务数据访问层实现
实现TaskRepository接口的SQLite具体实现
"""

import json
import sqlite3
import aiosqlite
import asyncio
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from pathlib import Path

from loguru import logger
import os
import sys

# 添加父目录到Python路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from models.unified_models import Task, TaskConfig
from core.enums import TaskStatus, TaskType, TaskPriority
from database.db_manager import DatabaseManager
from .task_repository import (
    TaskRepository, RepositoryError, TaskNotFoundError, 
    DuplicateTaskError, DatabaseConnectionError, QueryExecutionError, ValidationError
)


class SQLiteTaskRepository(TaskRepository):
    """SQLite任务数据访问层实现"""
    
    def __init__(self, db_path: str = "tasks.db", connection_pool_size: int = 5):
        """
        初始化SQLite任务仓库
        
        Args:
            db_path: 数据库文件路径
            connection_pool_size: 连接池大小
        """
        self.db_path = db_path
        self.connection_pool_size = connection_pool_size
        self._connection_pool = []
        self._pool_lock = asyncio.Lock()
        self._init_lock = asyncio.Lock()  # 初始化锁
        self._initialized = False
        
        # 确保数据库目录存在（除非是内存数据库）
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self) -> bool:
        """初始化数据库和连接池"""
        async with self._init_lock:
            if self._initialized:
                return True
                
            try:
                # 先初始化连接池
                await self._initialize_connection_pool()
                
                # 然后创建数据库表
                await self._create_tables()
                
                self._initialized = True
                logger.info(f"SQLite任务仓库初始化成功: {self.db_path}")
                return True
                
            except Exception as e:
                logger.error(f"SQLite任务仓库初始化失败: {e}")
                raise DatabaseConnectionError(f"Failed to initialize database: {e}", e)
    
    async def _create_tables(self):
        """创建数据库表"""
        create_tasks_table = """
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            task_type TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL,
            config_json TEXT NOT NULL,
            execution_count INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0,
            failure_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_executed_at TEXT,
            last_error TEXT,
            execution_log_json TEXT,
            tags_json TEXT,
            version TEXT DEFAULT '1.0'
        )
        """
        
        create_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_task_type ON tasks(task_type)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_updated_at ON tasks(updated_at)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON tasks(user_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_user_type ON tasks(user_id, task_type)"
        ]
        
        # 对于内存数据库，需要使用连接池中的连接来创建表
        # 这样确保表在所有连接中都可见
        conn = await self._get_connection()
        try:
            # 启用WAL模式（对内存数据库可能不适用，但不会出错）
            await conn.execute("PRAGMA journal_mode=WAL")
            await conn.execute("PRAGMA synchronous=NORMAL")
            await conn.execute("PRAGMA cache_size=10000")
            await conn.execute("PRAGMA temp_store=memory")
            
            # 创建表
            await conn.execute(create_tasks_table)
            
            # 创建索引
            for index_sql in create_indexes:
                await conn.execute(index_sql)
            
            await conn.commit()
        finally:
            await self._return_connection(conn)
    
    async def _initialize_connection_pool(self):
        """初始化连接池"""
        async with self._pool_lock:
            for _ in range(self.connection_pool_size):
                conn = await aiosqlite.connect(self.db_path)
                conn.row_factory = aiosqlite.Row
                await conn.execute("PRAGMA journal_mode=WAL")
                await conn.execute("PRAGMA synchronous=NORMAL")
                self._connection_pool.append(conn)
    
    async def _get_connection(self):
        """从连接池获取连接"""
        async with self._pool_lock:
            if self._connection_pool:
                return self._connection_pool.pop()
            else:
                # 连接池为空，创建新连接
                conn = await aiosqlite.connect(self.db_path)
                conn.row_factory = aiosqlite.Row
                await conn.execute("PRAGMA journal_mode=WAL")
                await conn.execute("PRAGMA synchronous=NORMAL")
                return conn
    
    async def _return_connection(self, conn):
        """将连接返回到连接池"""
        async with self._pool_lock:
            if len(self._connection_pool) < self.connection_pool_size:
                self._connection_pool.append(conn)
            else:
                await conn.close()
    
    async def create_task(self, task: Task) -> str:
        """创建任务"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # 验证任务数据
            task.validate()
            
            # 检查任务是否已存在（直接查询数据库，避免递归调用）
            conn = await self._get_connection()
            try:
                cursor = await conn.execute(
                    "SELECT task_id FROM tasks WHERE task_id = ?",
                    (task.task_id,)
                )
                existing = await cursor.fetchone()
                if existing:
                    raise DuplicateTaskError(task.task_id)
            finally:
                await self._return_connection(conn)
            
            conn = await self._get_connection()
            try:
                insert_sql = """
                INSERT INTO tasks (
                    task_id, user_id, name, description, task_type, priority, status,
                    config_json, execution_count, success_count, failure_count,
                    created_at, updated_at, last_executed_at, last_error,
                    execution_log_json, tags_json, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                await conn.execute(insert_sql, (
                    task.task_id,
                    task.user_id,
                    task.config.name,
                    task.config.description,
                    task.config.task_type.value,
                    task.config.priority.value,
                    task.status.value,
                    task.config.to_json(),
                    task.execution_count,
                    task.success_count,
                    task.failure_count,
                    task.created_at.isoformat() if task.created_at else None,
                    task.updated_at.isoformat() if task.updated_at else None,
                    task.last_executed_at.isoformat() if task.last_executed_at else None,
                    task.last_error,
                    json.dumps(task.execution_log, ensure_ascii=False),
                    json.dumps(task.config.tags, ensure_ascii=False),
                    task.config.version
                ))
                
                await conn.commit()
                logger.info(f"任务创建成功: {task.task_id}")
                return task.task_id
                
            finally:
                await self._return_connection(conn)
                
        except Exception as e:
            if isinstance(e, (DuplicateTaskError, ValidationError)):
                raise
            logger.error(f"创建任务失败: {e}")
            raise QueryExecutionError("INSERT INTO tasks", str(e), e)
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """根据ID获取任务"""
        if not self._initialized:
            await self.initialize()
        
        try:
            conn = await self._get_connection()
            try:
                cursor = await conn.execute(
                    "SELECT * FROM tasks WHERE task_id = ?",
                    (task_id,)
                )
                row = await cursor.fetchone()
                
                if row:
                    return self._row_to_task(row)
                return None
                
            finally:
                await self._return_connection(conn)
                
        except Exception as e:
            logger.error(f"获取任务失败: {e}")
            raise QueryExecutionError("SELECT FROM tasks", str(e), e)
    
    async def update_task(self, task: Task) -> bool:
        """更新任务"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # 验证任务数据
            task.validate()
            
            # 更新时间戳
            task.updated_at = datetime.now()
            
            conn = await self._get_connection()
            try:
                update_sql = """
                UPDATE tasks SET
                    user_id = ?, name = ?, description = ?, task_type = ?, priority = ?,
                    status = ?, config_json = ?, execution_count = ?, success_count = ?,
                    failure_count = ?, updated_at = ?, last_executed_at = ?,
                    last_error = ?, execution_log_json = ?, tags_json = ?, version = ?
                WHERE task_id = ?
                """
                
                cursor = await conn.execute(update_sql, (
                    task.user_id,
                    task.config.name,
                    task.config.description,
                    task.config.task_type.value,
                    task.config.priority.value,
                    task.status.value,
                    task.config.to_json(),
                    task.execution_count,
                    task.success_count,
                    task.failure_count,
                    task.updated_at.isoformat(),
                    task.last_executed_at.isoformat() if task.last_executed_at else None,
                    task.last_error,
                    json.dumps(task.execution_log, ensure_ascii=False),
                    json.dumps(task.config.tags, ensure_ascii=False),
                    task.config.version,
                    task.task_id
                ))
                
                await conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"任务更新成功: {task.task_id}")
                    return True
                else:
                    logger.warning(f"任务不存在，无法更新: {task.task_id}")
                    return False
                    
            finally:
                await self._return_connection(conn)
                
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            logger.error(f"更新任务失败: {e}")
            raise QueryExecutionError("UPDATE tasks", str(e), e)
    
    async def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        if not self._initialized:
            await self.initialize()
        
        try:
            conn = await self._get_connection()
            try:
                cursor = await conn.execute(
                    "DELETE FROM tasks WHERE task_id = ?",
                    (task_id,)
                )
                await conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"任务删除成功: {task_id}")
                    return True
                else:
                    logger.warning(f"任务不存在，无法删除: {task_id}")
                    return False
                    
            finally:
                await self._return_connection(conn)
                
        except Exception as e:
            logger.error(f"删除任务失败: {e}")
            raise QueryExecutionError("DELETE FROM tasks", str(e), e)
    
    async def list_tasks(
        self,
        user_id: Optional[str] = None,
        status: Optional[Union[TaskStatus, List[TaskStatus]]] = None,
        task_type: Optional[Union[TaskType, List[TaskType]]] = None,
        priority: Optional[Union[TaskPriority, List[TaskPriority]]] = None,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        order_by: str = "created_at",
        order_desc: bool = True
    ) -> List[Task]:
        """查询任务列表"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # 构建查询条件
            where_conditions = []
            params = []
            
            if user_id:
                where_conditions.append("user_id = ?")
                params.append(user_id)
            
            if status:
                if isinstance(status, TaskStatus):
                    where_conditions.append("status = ?")
                    params.append(status.value)
                elif isinstance(status, list):
                    placeholders = ",".join(["?"] * len(status))
                    where_conditions.append(f"status IN ({placeholders})")
                    params.extend([s.value for s in status])
            
            if task_type:
                if isinstance(task_type, TaskType):
                    where_conditions.append("task_type = ?")
                    params.append(task_type.value)
                elif isinstance(task_type, list):
                    placeholders = ",".join(["?"] * len(task_type))
                    where_conditions.append(f"task_type IN ({placeholders})")
                    params.extend([t.value for t in task_type])
            
            if priority:
                if isinstance(priority, TaskPriority):
                    where_conditions.append("priority = ?")
                    params.append(priority.value)
                elif isinstance(priority, list):
                    placeholders = ",".join(["?"] * len(priority))
                    where_conditions.append(f"priority IN ({placeholders})")
                    params.extend([p.value for p in priority])
            
            # 构建SQL查询
            sql = "SELECT * FROM tasks"
            if where_conditions:
                sql += " WHERE " + " AND ".join(where_conditions)
            
            # 排序
            order_direction = "DESC" if order_desc else "ASC"
            sql += f" ORDER BY {order_by} {order_direction}"
            
            # 分页
            if limit:
                sql += f" LIMIT {limit} OFFSET {offset}"
            
            conn = await self._get_connection()
            try:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()
                
                tasks = []
                for row in rows:
                    task = self._row_to_task(row)
                    
                    # 标签过滤（在内存中进行，因为SQLite的JSON查询较复杂）
                    if tags:
                        task_tags = task.config.tags
                        if not any(tag in task_tags for tag in tags):
                            continue
                    
                    tasks.append(task)
                
                return tasks
                
            finally:
                await self._return_connection(conn)
                
        except Exception as e:
            logger.error(f"查询任务列表失败: {e}")
            raise QueryExecutionError("SELECT FROM tasks", str(e), e)
    
    async def count_tasks(
        self,
        user_id: Optional[str] = None,
        status: Optional[Union[TaskStatus, List[TaskStatus]]] = None,
        task_type: Optional[Union[TaskType, List[TaskType]]] = None,
        priority: Optional[Union[TaskPriority, List[TaskPriority]]] = None,
        tags: Optional[List[str]] = None
    ) -> int:
        """统计任务数量"""
        # 简化实现：获取所有匹配的任务然后计数
        # 在生产环境中，应该使用COUNT查询优化性能
        tasks = await self.list_tasks(
            user_id=user_id,
            status=status,
            task_type=task_type,
            priority=priority,
            tags=tags
        )
        return len(tasks)
    
    async def get_tasks_by_schedule(
        self,
        current_time: datetime,
        user_id: Optional[str] = None
    ) -> List[Task]:
        """获取需要调度的任务"""
        # 获取启用了调度的任务
        all_tasks = await self.list_tasks(user_id=user_id)
        
        scheduled_tasks = []
        for task in all_tasks:
            if (task.config.schedule_config.enabled and 
                task.status in [TaskStatus.PENDING, TaskStatus.COMPLETED]):
                
                # 检查是否到了调度时间
                if self._should_schedule_task(task, current_time):
                    scheduled_tasks.append(task)
        
        return scheduled_tasks
    
    def _should_schedule_task(self, task: Task, current_time: datetime) -> bool:
        """检查任务是否应该被调度"""
        schedule_config = task.config.schedule_config
        
        # 检查调度时间
        if schedule_config.schedule_time:
            try:
                hour, minute = map(int, schedule_config.schedule_time.split(':'))
                if current_time.hour != hour or current_time.minute != minute:
                    return False
            except ValueError:
                return False
        
        # 检查调度日期
        if schedule_config.schedule_days:
            weekday_names = [
                'monday', 'tuesday', 'wednesday', 'thursday',
                'friday', 'saturday', 'sunday'
            ]
            current_weekday = weekday_names[current_time.weekday()]
            if current_weekday not in schedule_config.schedule_days:
                return False
        
        # 检查重复间隔
        if schedule_config.repeat_interval > 0 and task.last_executed_at:
            time_since_last = current_time - task.last_executed_at
            if time_since_last.total_seconds() < schedule_config.repeat_interval:
                return False
        
        # 检查最大执行次数
        if (schedule_config.max_executions > 0 and 
            task.execution_count >= schedule_config.max_executions):
            return False
        
        return True
    
    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        error_message: Optional[str] = None
    ) -> bool:
        """更新任务状态"""
        task = await self.get_task(task_id)
        if not task:
            return False
        
        task.update_status(status, error_message)
        return await self.update_task(task)
    
    async def record_task_execution(
        self,
        task_id: str,
        success: bool,
        message: Optional[str] = None
    ) -> bool:
        """记录任务执行结果"""
        task = await self.get_task(task_id)
        if not task:
            return False
        
        task.record_execution(success, message)
        return await self.update_task(task)
    
    async def get_task_statistics(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取任务统计信息"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # 构建查询条件
            where_conditions = []
            params = []
            
            if user_id:
                where_conditions.append("user_id = ?")
                params.append(user_id)
            
            if start_date:
                where_conditions.append("created_at >= ?")
                params.append(start_date.isoformat())
            
            if end_date:
                where_conditions.append("created_at <= ?")
                params.append(end_date.isoformat())
            
            where_clause = ""
            if where_conditions:
                where_clause = " WHERE " + " AND ".join(where_conditions)
            
            conn = await self._get_connection()
            try:
                # 基本统计
                stats_sql = f"""
                SELECT 
                    COUNT(*) as total_tasks,
                    SUM(execution_count) as total_executions,
                    SUM(success_count) as total_successes,
                    SUM(failure_count) as total_failures,
                    AVG(execution_count) as avg_executions_per_task
                FROM tasks{where_clause}
                """
                
                cursor = await conn.execute(stats_sql, params)
                basic_stats = await cursor.fetchone()
                
                # 按状态统计
                status_sql = f"""
                SELECT status, COUNT(*) as count
                FROM tasks{where_clause}
                GROUP BY status
                """
                
                cursor = await conn.execute(status_sql, params)
                status_stats = await cursor.fetchall()
                
                # 按类型统计
                type_sql = f"""
                SELECT task_type, COUNT(*) as count
                FROM tasks{where_clause}
                GROUP BY task_type
                """
                
                cursor = await conn.execute(type_sql, params)
                type_stats = await cursor.fetchall()
                
                # 按优先级统计
                priority_sql = f"""
                SELECT priority, COUNT(*) as count
                FROM tasks{where_clause}
                GROUP BY priority
                """
                
                cursor = await conn.execute(priority_sql, params)
                priority_stats = await cursor.fetchall()
                
                return {
                    'basic': dict(basic_stats) if basic_stats else {},
                    'by_status': {row['status']: row['count'] for row in status_stats},
                    'by_type': {row['task_type']: row['count'] for row in type_stats},
                    'by_priority': {row['priority']: row['count'] for row in priority_stats}
                }
                
            finally:
                await self._return_connection(conn)
                
        except Exception as e:
            logger.error(f"获取任务统计失败: {e}")
            raise QueryExecutionError("Statistics query", str(e), e)
    
    async def search_tasks(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Task]:
        """搜索任务"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # 构建搜索条件
            where_conditions = [
                "(name LIKE ? OR description LIKE ?)"
            ]
            params = [f"%{query}%", f"%{query}%"]
            
            if user_id:
                where_conditions.append("user_id = ?")
                params.append(user_id)
            
            sql = f"""
            SELECT * FROM tasks 
            WHERE {' AND '.join(where_conditions)}
            ORDER BY updated_at DESC
            """
            
            if limit:
                sql += f" LIMIT {limit} OFFSET {offset}"
            
            conn = await self._get_connection()
            try:
                cursor = await conn.execute(sql, params)
                rows = await cursor.fetchall()
                
                return [self._row_to_task(row) for row in rows]
                
            finally:
                await self._return_connection(conn)
                
        except Exception as e:
            logger.error(f"搜索任务失败: {e}")
            raise QueryExecutionError("Search tasks", str(e), e)
    
    async def backup_tasks(
        self,
        user_id: Optional[str] = None,
        backup_path: Optional[str] = None
    ) -> str:
        """备份任务数据"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"tasks_backup_{timestamp}.json"
        
        tasks = await self.list_tasks(user_id=user_id)
        
        backup_data = {
            'backup_time': datetime.now().isoformat(),
            'user_id': user_id,
            'task_count': len(tasks),
            'tasks': [task.to_dict() for task in tasks]
        }
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"任务备份完成: {backup_path}, 任务数量: {len(tasks)}")
        return backup_path
    
    async def restore_tasks(
        self,
        backup_path: str,
        user_id: Optional[str] = None
    ) -> int:
        """恢复任务数据"""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            tasks_data = backup_data.get('tasks', [])
            restored_count = 0
            
            for task_data in tasks_data:
                try:
                    task = Task.from_dict(task_data)
                    
                    # 如果指定了用户ID，则覆盖备份中的用户ID
                    if user_id:
                        task.user_id = user_id
                    
                    # 检查任务是否已存在
                    existing_task = await self.get_task(task.task_id)
                    if existing_task:
                        logger.warning(f"任务已存在，跳过恢复: {task.task_id}")
                        continue
                    
                    await self.create_task(task)
                    restored_count += 1
                    
                except Exception as e:
                    logger.error(f"恢复任务失败: {e}")
                    continue
            
            logger.info(f"任务恢复完成: {restored_count}/{len(tasks_data)}")
            return restored_count
            
        except Exception as e:
            logger.error(f"恢复任务数据失败: {e}")
            raise RepositoryError(f"Failed to restore tasks: {e}", "RESTORE_ERROR", e)
    
    async def cleanup_old_tasks(
        self,
        days: int = 30,
        status_filter: Optional[List[TaskStatus]] = None
    ) -> int:
        """清理旧任务"""
        if not self._initialized:
            await self.initialize()
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 构建删除条件
            where_conditions = ["created_at < ?"]
            params = [cutoff_date.isoformat()]
            
            if status_filter:
                placeholders = ",".join(["?"] * len(status_filter))
                where_conditions.append(f"status IN ({placeholders})")
                params.extend([s.value for s in status_filter])
            
            delete_sql = f"""
            DELETE FROM tasks 
            WHERE {' AND '.join(where_conditions)}
            """
            
            conn = await self._get_connection()
            try:
                cursor = await conn.execute(delete_sql, params)
                await conn.commit()
                
                deleted_count = cursor.rowcount
                logger.info(f"清理旧任务完成: {deleted_count} 个任务被删除")
                return deleted_count
                
            finally:
                await self._return_connection(conn)
                
        except Exception as e:
            logger.error(f"清理旧任务失败: {e}")
            raise QueryExecutionError("DELETE old tasks", str(e), e)
    
    async def close(self) -> bool:
        """关闭数据访问层"""
        try:
            async with self._pool_lock:
                for conn in self._connection_pool:
                    await conn.close()
                self._connection_pool.clear()
            
            self._initialized = False
            logger.info("SQLite任务仓库已关闭")
            return True
            
        except Exception as e:
            logger.error(f"关闭SQLite任务仓库失败: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if not self._initialized:
                return {
                    'status': 'unhealthy',
                    'message': 'Repository not initialized',
                    'details': {}
                }
            
            # 测试数据库连接
            conn = await self._get_connection()
            try:
                await conn.execute("SELECT 1")
                
                # 获取基本统计信息
                cursor = await conn.execute("SELECT COUNT(*) as count FROM tasks")
                result = await cursor.fetchone()
                task_count = result['count'] if result else 0
                
                return {
                    'status': 'healthy',
                    'message': 'Repository is working properly',
                    'details': {
                        'db_path': self.db_path,
                        'connection_pool_size': len(self._connection_pool),
                        'task_count': task_count,
                        'initialized': self._initialized
                    }
                }
                
            finally:
                await self._return_connection(conn)
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Health check failed: {e}',
                'details': {
                    'error': str(e),
                    'db_path': self.db_path,
                    'initialized': self._initialized
                }
            }
    
    def _row_to_task(self, row) -> Task:
        """将数据库行转换为Task对象"""
        try:
            # 解析配置JSON
            config_data = json.loads(row['config_json'])
            config = TaskConfig.from_dict(config_data)
            
            # 解析执行日志
            execution_log = []
            if row['execution_log_json']:
                execution_log = json.loads(row['execution_log_json'])
            
            # 创建Task对象
            task = Task(
                task_id=row['task_id'],
                user_id=row['user_id'],
                config=config,
                status=TaskStatus(row['status']),
                execution_count=row['execution_count'],
                success_count=row['success_count'],
                failure_count=row['failure_count'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
                last_executed_at=datetime.fromisoformat(row['last_executed_at']) if row['last_executed_at'] else None,
                last_error=row['last_error'],
                execution_log=execution_log
            )
            
            return task
            
        except Exception as e:
            logger.error(f"转换数据库行为Task对象失败: {e}")
            raise RepositoryError(f"Failed to convert row to Task: {e}", "CONVERSION_ERROR", e)