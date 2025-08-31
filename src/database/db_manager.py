# -*- coding: utf-8 -*-
"""
数据库管理器 - 负责SQLite数据库的创建、连接和管理
"""

import sqlite3
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from contextlib import contextmanager

from loguru import logger


class DatabaseManager:
    """数据库管理器类"""
    
    def __init__(self, db_path: Optional[Path] = None):
        """初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径，默认为项目根目录下的data/app.db
        """
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent
            data_dir = project_root / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "app.db"
        
        self.db_path = Path(db_path)
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """确保数据库文件存在"""
        if not self.db_path.exists():
            self.db_path.touch()
            logger.info(f"创建数据库文件: {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def run_migrations(self):
        """运行数据库迁移"""
        migrations_dir = Path(__file__).parent / "migrations"
        if not migrations_dir.exists():
            logger.info("迁移目录不存在，跳过迁移")
            return
            
        # 创建迁移记录表
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    migration_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 获取已应用的迁移
            cursor.execute("SELECT filename FROM schema_migrations")
            applied_migrations = {row[0] for row in cursor.fetchall()}
            
            # 执行未应用的迁移
            migration_files = sorted(migrations_dir.glob("*.sql"))
            for migration_file in migration_files:
                if migration_file.name not in applied_migrations:
                    logger.info(f"应用迁移: {migration_file.name}")
                    try:
                        with open(migration_file, 'r', encoding='utf-8') as f:
                            migration_sql = f.read()
                        
                        # 执行迁移SQL
                        cursor.executescript(migration_sql)
                        
                        # 记录迁移
                        migration_id = str(uuid.uuid4())
                        cursor.execute(
                            "INSERT INTO schema_migrations (migration_id, filename) VALUES (?, ?)",
                            (migration_id, migration_file.name)
                        )
                        
                        logger.info(f"迁移 {migration_file.name} 应用成功")
                    except Exception as e:
                        logger.error(f"迁移 {migration_file.name} 应用失败: {e}")
                        conn.rollback()
                        raise
            
            conn.commit()
    
    def initialize_database(self):
        """初始化数据库表结构"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建用户表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建任务表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    task_name TEXT NOT NULL,
                    description TEXT,
                    task_type TEXT NOT NULL,
                    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
                    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'paused', 'cancelled')),
                    max_duration INTEGER DEFAULT 300,
                    retry_count INTEGER DEFAULT 3,
                    retry_interval REAL DEFAULT 1.0,
                    safe_mode BOOLEAN DEFAULT 1,
                    scheduled_time TIMESTAMP,
                    repeat_interval INTEGER,
                    last_execution TIMESTAMP,
                    execution_count INTEGER DEFAULT 0,
                    progress REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # 创建任务配置表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_configs (
                    config_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    config_key TEXT NOT NULL,
                    config_value TEXT NOT NULL,
                    data_type TEXT DEFAULT 'string' CHECK (data_type IN ('string', 'integer', 'float', 'boolean', 'json')),
                    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
                )
            """)
            
            # 创建执行日志表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS execution_logs (
                    log_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    log_level TEXT DEFAULT 'INFO' CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    details TEXT,
                    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
                )
            """)
            
            # 创建用户配置表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_configs (
                    config_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    section TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    UNIQUE(user_id, section, key)
                )
            """)
            
            # 创建索引
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
                "CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
                "CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(task_type)",
                "CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_task_configs_task_id ON task_configs(task_id)",
                "CREATE INDEX IF NOT EXISTS idx_task_configs_key ON task_configs(config_key)",
                "CREATE INDEX IF NOT EXISTS idx_execution_logs_task_id ON execution_logs(task_id)",
                "CREATE INDEX IF NOT EXISTS idx_execution_logs_timestamp ON execution_logs(timestamp DESC)",
                "CREATE INDEX IF NOT EXISTS idx_execution_logs_level ON execution_logs(log_level)",
                "CREATE INDEX IF NOT EXISTS idx_user_configs_user_id ON user_configs(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_user_configs_section ON user_configs(section)"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            # 插入默认用户（如果不存在）
            cursor.execute(
                "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
                ('default_user', '默认用户')
            )
            
            # 插入默认配置（如果不存在）
            default_configs = [
                ('cfg_001', 'default_user', 'game', 'resolution', '1920x1080'),
                ('cfg_002', 'default_user', 'game', 'game_path', ''),
                ('cfg_003', 'default_user', 'automation', 'click_delay', '1.0'),
                ('cfg_004', 'default_user', 'automation', 'detection_threshold', '0.8'),
                ('cfg_005', 'default_user', 'security', 'random_delay', 'true'),
                ('cfg_006', 'default_user', 'security', 'safe_mode', 'true')
            ]
            
            for config in default_configs:
                cursor.execute(
                    "INSERT OR IGNORE INTO user_configs (config_id, user_id, section, key, value) VALUES (?, ?, ?, ?, ?)",
                    config
                )
            
            conn.commit()
            logger.info("数据库初始化完成")
            
        # 运行迁移
        self.run_migrations()
    
    def create_user(self, username: str) -> str:
        """创建新用户
        
        Args:
            username: 用户名
            
        Returns:
            str: 用户ID
        """
        user_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (user_id, username) VALUES (?, ?)",
                (user_id, username)
            )
            conn.commit()
            
        logger.info(f"创建用户: {username} (ID: {user_id})")
        return user_id
    
    def create_task(self, user_id: str, task_name: str, task_type: str, 
                   description: str = None, priority: str = 'medium',
                   max_duration: int = 300, retry_count: int = 3,
                   retry_interval: float = 1.0, safe_mode: bool = True,
                   scheduled_time: str = None, repeat_interval: int = None) -> str:
        """创建新任务
        
        Args:
            user_id: 用户ID
            task_name: 任务名称
            task_type: 任务类型
            description: 任务描述
            priority: 优先级
            max_duration: 最大执行时间（秒）
            retry_count: 重试次数
            retry_interval: 重试间隔（秒）
            safe_mode: 安全模式
            scheduled_time: 计划执行时间
            repeat_interval: 重复间隔（秒）
            
        Returns:
            str: 任务ID
        """
        task_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO tasks (task_id, user_id, task_name, description, task_type, 
                   priority, max_duration, retry_count, retry_interval, safe_mode, 
                   scheduled_time, repeat_interval) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (task_id, user_id, task_name, description, task_type, priority,
                 max_duration, retry_count, retry_interval, safe_mode,
                 scheduled_time, repeat_interval)
            )
            conn.commit()
            
        logger.info(f"创建任务: {task_name} (ID: {task_id})")
        return task_id
    
    def update_task_status(self, task_id: str, status: str):
        """更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE tasks SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE task_id = ?",
                (status, task_id)
            )
            conn.commit()
            
        logger.info(f"更新任务状态: {task_id} -> {status}")
    
    def update_task(self, task_id: str, **kwargs):
        """更新任务信息
        
        Args:
            task_id: 任务ID
            **kwargs: 要更新的字段
        """
        if not kwargs:
            return
            
        # 构建更新语句
        set_clauses = []
        values = []
        
        for key, value in kwargs.items():
            if key in ['task_name', 'description', 'task_type', 'priority', 'status',
                      'max_duration', 'retry_count', 'retry_interval', 'safe_mode',
                      'scheduled_time', 'repeat_interval', 'last_execution', 
                      'execution_count', 'progress']:
                set_clauses.append(f"{key} = ?")
                values.append(value)
        
        if not set_clauses:
            return
            
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        values.append(task_id)
        
        sql = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE task_id = ?"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, values)
            conn.commit()
            
        logger.info(f"更新任务: {task_id}")
    
    def get_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Dict]: 任务信息
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM tasks WHERE task_id = ?",
                (task_id,)
            )
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def delete_task(self, task_id: str):
        """删除任务
        
        Args:
            task_id: 任务ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 删除相关的配置和日志
            cursor.execute("DELETE FROM task_configs WHERE task_id = ?", (task_id,))
            cursor.execute("DELETE FROM execution_logs WHERE task_id = ?", (task_id,))
            
            # 删除任务
            cursor.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
            
            conn.commit()
            
        logger.info(f"删除任务: {task_id}")

    def get_task_config(self, task_id: str) -> Dict[str, Any]:
        """获取任务配置
        
        Args:
            task_id: 任务ID
            
        Returns:
            Dict[str, Any]: 任务配置字典
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT config_key, config_value, data_type FROM task_configs WHERE task_id = ?",
                (task_id,)
            )
            
            config = {}
            for row in cursor.fetchall():
                key, value, data_type = row
                # 根据数据类型转换值
                if data_type == 'integer':
                    config[key] = int(value)
                elif data_type == 'float':
                    config[key] = float(value)
                elif data_type == 'boolean':
                    config[key] = value.lower() in ('true', '1', 'yes')
                elif data_type == 'json':
                    import json
                    config[key] = json.loads(value)
                else:
                    config[key] = value
            
            return config

    def add_execution_log(self, task_id: str, level: str, message: str, details: str = None):
        """添加执行日志
        
        Args:
            task_id: 任务ID
            level: 日志级别
            message: 日志消息
            details: 详细信息
        """
        log_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO execution_logs (log_id, task_id, log_level, message, details) VALUES (?, ?, ?, ?, ?)",
                (log_id, task_id, level, message, details)
            )
            conn.commit()
    
    def get_tasks_by_user(self, user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取用户的任务列表
        
        Args:
            user_id: 用户ID
            status: 任务状态过滤（可选）
            
        Returns:
            List[Dict]: 任务列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if status:
                cursor.execute(
                    "SELECT * FROM tasks WHERE user_id = ? AND status = ? ORDER BY created_at DESC",
                    (user_id, status)
                )
            else:
                cursor.execute(
                    "SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,)
                )
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_task_logs(self, task_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取任务执行日志
        
        Args:
            task_id: 任务ID
            limit: 返回记录数限制
            
        Returns:
            List[Dict]: 日志列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM execution_logs WHERE task_id = ? ORDER BY timestamp DESC LIMIT ?",
                (task_id, limit)
            )
            
            return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_old_logs(self, days: int = 30):
        """清理旧日志
        
        Args:
            days: 保留天数
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM execution_logs WHERE timestamp < datetime('now', '-{} days')".format(days)
            )
            deleted_count = cursor.rowcount
            conn.commit()
            
        logger.info(f"清理了 {deleted_count} 条旧日志记录")
    
    def get_database_stats(self) -> Dict[str, int]:
        """获取数据库统计信息
        
        Returns:
            Dict: 统计信息
        """
        stats = {}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 统计各表记录数
            tables = ['users', 'tasks', 'task_configs', 'execution_logs', 'user_configs']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]
            
            # 统计数据库文件大小
            stats['db_size_bytes'] = self.db_path.stat().st_size
            
        return stats
    
    # 任务动作管理方法
    def create_task_action(self, task_id: str, action_type: str, action_order: int,
                          target_element: str = None, coordinates: str = None,
                          key_code: str = None, wait_duration: float = None,
                          screenshot_path: str = None, custom_script: str = None,
                          parameters: str = None) -> str:
        """创建任务动作
        
        Args:
            task_id: 任务ID
            action_type: 动作类型
            action_order: 动作顺序
            target_element: 目标元素
            coordinates: 坐标信息（JSON格式）
            key_code: 按键代码
            wait_duration: 等待时长
            screenshot_path: 截图路径
            custom_script: 自定义脚本
            parameters: 其他参数（JSON格式）
            
        Returns:
            str: 动作ID
        """
        action_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO task_actions (action_id, task_id, action_type, action_order,
                   target_element, coordinates, key_code, wait_duration, screenshot_path,
                   custom_script, parameters) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (action_id, task_id, action_type, action_order, target_element,
                 coordinates, key_code, wait_duration, screenshot_path,
                 custom_script, parameters)
            )
            conn.commit()
            
        logger.info(f"创建任务动作: {action_type} (ID: {action_id})")
        return action_id
    
    def get_task_actions(self, task_id: str) -> List[Dict[str, Any]]:
        """获取任务的所有动作
        
        Args:
            task_id: 任务ID
            
        Returns:
            List[Dict]: 动作列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM task_actions WHERE task_id = ? AND is_enabled = 1 ORDER BY action_order",
                (task_id,)
            )
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_task_action(self, action_id: str, **kwargs):
        """更新任务动作
        
        Args:
            action_id: 动作ID
            **kwargs: 要更新的字段
        """
        if not kwargs:
            return
            
        set_clauses = []
        values = []
        
        for key, value in kwargs.items():
            if key in ['action_type', 'action_order', 'target_element', 'coordinates',
                      'key_code', 'wait_duration', 'screenshot_path', 'custom_script',
                      'parameters', 'is_enabled']:
                set_clauses.append(f"{key} = ?")
                values.append(value)
        
        if not set_clauses:
            return
            
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        values.append(action_id)
        
        sql = f"UPDATE task_actions SET {', '.join(set_clauses)} WHERE action_id = ?"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, values)
            conn.commit()
            
        logger.info(f"更新任务动作: {action_id}")
    
    def delete_task_action(self, action_id: str):
        """删除任务动作
        
        Args:
            action_id: 动作ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM task_actions WHERE action_id = ?", (action_id,))
            conn.commit()
            
        logger.info(f"删除任务动作: {action_id}")
    
    # 任务执行记录管理方法
    def create_task_execution(self, task_id: str) -> str:
        """创建任务执行记录
        
        Args:
            task_id: 任务ID
            
        Returns:
            str: 执行记录ID
        """
        execution_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO task_executions (execution_id, task_id) VALUES (?, ?)",
                (execution_id, task_id)
            )
            conn.commit()
            
        logger.info(f"创建任务执行记录: {execution_id}")
        return execution_id
    
    def update_task_execution(self, execution_id: str, **kwargs):
        """更新任务执行记录
        
        Args:
            execution_id: 执行记录ID
            **kwargs: 要更新的字段
        """
        if not kwargs:
            return
            
        set_clauses = []
        values = []
        
        for key, value in kwargs.items():
            if key in ['execution_status', 'end_time', 'duration_seconds',
                      'success_count', 'failure_count', 'current_action_index',
                      'progress_percentage', 'error_message', 'execution_log']:
                set_clauses.append(f"{key} = ?")
                values.append(value)
        
        if not set_clauses:
            return
            
        values.append(execution_id)
        sql = f"UPDATE task_executions SET {', '.join(set_clauses)} WHERE execution_id = ?"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, values)
            conn.commit()
            
        logger.info(f"更新任务执行记录: {execution_id}")
    
    def get_task_executions(self, task_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取任务执行记录
        
        Args:
            task_id: 任务ID
            limit: 返回记录数限制
            
        Returns:
            List[Dict]: 执行记录列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM task_executions WHERE task_id = ? ORDER BY start_time DESC LIMIT ?",
                (task_id, limit)
            )
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_execution_by_id(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取执行记录
        
        Args:
            execution_id: 执行记录ID
            
        Returns:
            Optional[Dict]: 执行记录信息
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM task_executions WHERE execution_id = ?",
                (execution_id,)
            )
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # 任务模板管理方法
    def create_task_template(self, template_name: str, template_type: str,
                           description: str, template_config: str,
                           is_public: bool = False, created_by: str = 'default_user') -> str:
        """创建任务模板
        
        Args:
            template_name: 模板名称
            template_type: 模板类型
            description: 模板描述
            template_config: 模板配置（JSON格式）
            is_public: 是否公开
            created_by: 创建者
            
        Returns:
            str: 模板ID
        """
        template_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO task_templates (template_id, template_name, template_type,
                   description, template_config, is_public, created_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (template_id, template_name, template_type, description,
                 template_config, is_public, created_by)
            )
            conn.commit()
            
        logger.info(f"创建任务模板: {template_name} (ID: {template_id})")
        return template_id
    
    def get_task_templates(self, template_type: str = None, is_public: bool = None) -> List[Dict[str, Any]]:
        """获取任务模板列表
        
        Args:
            template_type: 模板类型过滤
            is_public: 是否公开过滤
            
        Returns:
            List[Dict]: 模板列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            conditions = []
            params = []
            
            if template_type:
                conditions.append("template_type = ?")
                params.append(template_type)
            
            if is_public is not None:
                conditions.append("is_public = ?")
                params.append(is_public)
            
            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            sql = f"SELECT * FROM task_templates{where_clause} ORDER BY usage_count DESC, created_at DESC"
            
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]