"""数据库简化测试"""

import os
import sqlite3
import tempfile
from unittest.mock import Mock

import pytest


@pytest.fixture
def temp_db_path():
    """创建临时数据库文件路径"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        temp_path = temp_file.name

    yield temp_path

    # 清理临时文件
    if os.path.exists(temp_path):
        os.unlink(temp_path)


class TestDatabase:
    """数据库简化测试类"""

    def test_sqlite_connection(self, temp_db_path):
        """测试SQLite连接"""
        conn = sqlite3.connect(temp_db_path)
        assert conn is not None

        # 测试基本查询
        cursor = conn.cursor()
        cursor.execute("SELECT sqlite_version()")
        version = cursor.fetchone()
        assert version is not None

        conn.close()

    def test_create_table(self, temp_db_path):
        """测试创建表"""
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # 创建测试表
        cursor.execute(
            """
            CREATE TABLE test_users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                email TEXT UNIQUE
            )
        """
        )

        # 验证表是否创建成功
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='test_users'"
        )
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == "test_users"

        conn.close()

    def test_insert_and_select(self, temp_db_path):
        """测试插入和查询数据"""
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # 创建表
        cursor.execute(
            """
            CREATE TABLE test_data (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                value INTEGER
            )
        """
        )

        # 插入数据
        test_data = [("项目A", 100), ("项目B", 200), ("项目C", 300)]
        cursor.executemany(
            "INSERT INTO test_data (name, value) VALUES (?, ?)", test_data
        )
        conn.commit()

        # 查询数据
        cursor.execute("SELECT name, value FROM test_data ORDER BY value")
        results = cursor.fetchall()

        assert len(results) == 3
        assert results[0] == ("项目A", 100)
        assert results[1] == ("项目B", 200)
        assert results[2] == ("项目C", 300)

        conn.close()

    def test_update_and_delete(self, temp_db_path):
        """测试更新和删除数据"""
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # 创建表并插入数据
        cursor.execute(
            """
            CREATE TABLE test_items (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT DEFAULT 'active'
            )
        """
        )

        cursor.execute("INSERT INTO test_items (name) VALUES (?)", ("测试项目",))
        conn.commit()

        # 更新数据
        cursor.execute(
            "UPDATE test_items SET status = ? WHERE name = ?", ("inactive", "测试项目")
        )
        conn.commit()

        # 验证更新
        cursor.execute("SELECT status FROM test_items WHERE name = ?", ("测试项目",))
        result = cursor.fetchone()
        assert result[0] == "inactive"

        # 删除数据
        cursor.execute("DELETE FROM test_items WHERE name = ?", ("测试项目",))
        conn.commit()

        # 验证删除
        cursor.execute("SELECT COUNT(*) FROM test_items WHERE name = ?", ("测试项目",))
        count = cursor.fetchone()[0]
        assert count == 0

        conn.close()

    def test_transaction_rollback(self, temp_db_path):
        """测试事务回滚"""
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # 创建表
        cursor.execute(
            """
            CREATE TABLE test_transactions (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            )
        """
        )

        # 插入初始数据
        cursor.execute("INSERT INTO test_transactions (name) VALUES (?)", ("初始数据",))
        conn.commit()

        try:
            # 开始事务
            cursor.execute(
                "INSERT INTO test_transactions (name) VALUES (?)", ("事务数据1",)
            )
            cursor.execute(
                "INSERT INTO test_transactions (name) VALUES (?)", ("事务数据2",)
            )
            # 故意插入重复数据引发错误
            cursor.execute(
                "INSERT INTO test_transactions (name) VALUES (?)", ("初始数据",)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            # 回滚事务
            conn.rollback()

        # 验证只有初始数据存在
        cursor.execute("SELECT COUNT(*) FROM test_transactions")
        count = cursor.fetchone()[0]
        assert count == 1

        cursor.execute("SELECT name FROM test_transactions")
        result = cursor.fetchone()
        assert result[0] == "初始数据"

        conn.close()

    def test_mock_database_manager(self):
        """测试模拟数据库管理器"""
        # 创建模拟的数据库管理器
        mock_db = Mock()
        mock_db.connect.return_value = Mock()
        mock_db.execute_query.return_value = [(1, "测试用户", "test@example.com")]
        mock_db.insert_data.return_value = True

        # 测试连接
        connection = mock_db.connect()
        assert connection is not None

        # 测试查询
        results = mock_db.execute_query("SELECT * FROM users")
        assert len(results) == 1
        assert results[0][1] == "测试用户"

        # 测试插入
        success = mock_db.insert_data(
            "users", {"name": "新用户", "email": "new@example.com"}
        )
        assert success is True
