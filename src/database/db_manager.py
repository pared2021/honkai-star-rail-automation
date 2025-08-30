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
                    task_type TEXT NOT NULL,
                    status TEXT DEFAULT 'created' CHECK (status IN ('created', 'running', 'completed', 'failed', 'stopped')),
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
    
    def create_task(self, user_id: str, task_name: str, task_type: str) -> str:
        """创建新任务
        
        Args:
            user_id: 用户ID
            task_name: 任务名称
            task_type: 任务类型
            
        Returns:
            str: 任务ID
        """
        task_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tasks (task_id, user_id, task_name, task_type) VALUES (?, ?, ?, ?)",
                (task_id, user_id, task_name, task_type)
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