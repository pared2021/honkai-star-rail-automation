"""数据库管理器模块。.

提供数据库的管理和操作功能。
"""

import sqlite3
import threading
from typing import Any, Dict, List, Optional


class DatabaseManager:
    """数据库管理器类。.

    提供数据库连接管理、事务处理和基本的CRUD操作。
    """

    def __init__(self, db_path: Optional[str] = None):
        """初始化数据库管理器。.

        Args:
            db_path: 数据库文件路径，如果为None则使用内存数据库
        """
        self.db_path = db_path or ":memory:"
        self._local = threading.local()
        self._lock = threading.Lock()
        self._initialized = False

    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接。.

        Returns:
            数据库连接对象
        """
        if not hasattr(self._local, "connection"):
            self._local.connection = sqlite3.connect(
                self.db_path, check_same_thread=False
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection  # type: ignore

    def execute_query(
        self, query: str, params: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """执行查询语句。.

        Args:
            query: SQL查询语句
            params: 查询参数

        Returns:
            查询结果列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            cursor.close()

    def execute_update(
        self, query: str, params: Optional[tuple] = None
    ) -> int:
        """执行更新语句。.

        Args:
            query: SQL更新语句
            params: 更新参数

        Returns:
            受影响的行数
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            conn.commit()
            return cursor.rowcount
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()

    def begin_transaction(self):
        """开始事务。."""
        conn = self.get_connection()
        conn.execute("BEGIN")

    def commit_transaction(self):
        """提交事务。."""
        conn = self.get_connection()
        conn.commit()

    def rollback_transaction(self):
        """回滚事务。."""
        conn = self.get_connection()
        conn.rollback()

    def close(self):
        """关闭数据库连接。."""
        if hasattr(self._local, "connection"):
            self._local.connection.close()
            delattr(self._local, "connection")

    def initialize_schema(self):
        """初始化数据库架构。."""
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return  # type: ignore

            # 创建基本表结构
            self.execute_update(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    state TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            self.execute_update(
                """
                CREATE TABLE IF NOT EXISTS task_executions (
                    execution_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    result TEXT,
                    worker_id TEXT,
                    FOREIGN KEY (task_id) REFERENCES tasks (id)
                )
            """
            )

            self._initialized = True

    def __enter__(self):
        """上下文管理器入口。."""
        self.begin_transaction()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口。."""
        if exc_type is None:
            self.commit_transaction()
        else:
            self.rollback_transaction()
