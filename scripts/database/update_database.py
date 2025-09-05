#!/usr/bin/env python3
"""
数据库更新脚本
"""

import sqlite3


def column_exists(cursor, table_name, column_name):
    """检查表中是否存在指定列"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return any(col[1] == column_name for col in columns)


def update_database():
    """更新数据库表结构"""
    try:
        conn = sqlite3.connect("data/app.db")
        cursor = conn.cursor()

        print("🔍 检查当前表结构...")

        # 检查并添加users表缺失的列
        if not column_exists(cursor, "users", "email"):
            cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
            print("✅ 添加users.email列")

        if not column_exists(cursor, "users", "updated_at"):
            cursor.execute("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP")
            cursor.execute(
                "UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL"
            )
            print("✅ 添加users.updated_at列")

        if not column_exists(cursor, "users", "preferences"):
            cursor.execute("ALTER TABLE users ADD COLUMN preferences TEXT DEFAULT '{}'")
            print("✅ 添加users.preferences列")

        # 检查并添加tasks表缺失的列
        if not column_exists(cursor, "tasks", "id"):
            cursor.execute("ALTER TABLE tasks ADD COLUMN id TEXT")
            cursor.execute('UPDATE tasks SET id = task_id WHERE id IS NULL OR id = ""')
            print("✅ 添加tasks.id列")

        if not column_exists(cursor, "tasks", "name"):
            cursor.execute("ALTER TABLE tasks ADD COLUMN name TEXT")
            cursor.execute(
                'UPDATE tasks SET name = task_name WHERE name IS NULL OR name = ""'
            )
            print("✅ 添加tasks.name列")

        if not column_exists(cursor, "tasks", "config"):
            cursor.execute("ALTER TABLE tasks ADD COLUMN config TEXT DEFAULT '{}'")
            print("✅ 添加tasks.config列")

        if not column_exists(cursor, "tasks", "started_at"):
            cursor.execute("ALTER TABLE tasks ADD COLUMN started_at TIMESTAMP")
            print("✅ 添加tasks.started_at列")

        if not column_exists(cursor, "tasks", "completed_at"):
            cursor.execute("ALTER TABLE tasks ADD COLUMN completed_at TIMESTAMP")
            print("✅ 添加tasks.completed_at列")

        if not column_exists(cursor, "tasks", "last_error"):
            cursor.execute("ALTER TABLE tasks ADD COLUMN last_error TEXT")
            print("✅ 添加tasks.last_error列")

        if not column_exists(cursor, "tasks", "execution_result"):
            cursor.execute("ALTER TABLE tasks ADD COLUMN execution_result TEXT")
            print("✅ 添加tasks.execution_result列")

        # 创建其他表（如果不存在）
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS task_executions (
                execution_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                status TEXT DEFAULT 'running',
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                actions_performed TEXT DEFAULT '[]',
                performance_metrics TEXT DEFAULT '{}',
                error_message TEXT,
                logs TEXT DEFAULT '[]',
                FOREIGN KEY (task_id) REFERENCES tasks(task_id)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS execution_actions (
                action_id TEXT PRIMARY KEY,
                execution_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                action_data TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                result TEXT,
                duration_ms INTEGER,
                FOREIGN KEY (execution_id) REFERENCES task_executions(execution_id)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS execution_screenshots (
                screenshot_id TEXT PRIMARY KEY,
                execution_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                FOREIGN KEY (execution_id) REFERENCES task_executions(execution_id)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS task_dependencies (
                dependency_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                depends_on_task_id TEXT NOT NULL,
                dependency_type TEXT DEFAULT 'sequential',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(task_id),
                FOREIGN KEY (depends_on_task_id) REFERENCES tasks(task_id)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS configs (
                config_id TEXT PRIMARY KEY,
                config_type TEXT NOT NULL,
                name TEXT NOT NULL,
                config_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """
        )

        # 创建索引
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_task_id ON tasks(task_id)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_id ON tasks(id)",
            "CREATE INDEX IF NOT EXISTS idx_task_executions_task_id ON task_executions(task_id)",
            "CREATE INDEX IF NOT EXISTS idx_task_executions_start_time ON task_executions(start_time DESC)",
            "CREATE INDEX IF NOT EXISTS idx_execution_actions_execution_id ON execution_actions(execution_id)",
            "CREATE INDEX IF NOT EXISTS idx_execution_screenshots_execution_id ON execution_screenshots(execution_id)",
            "CREATE INDEX IF NOT EXISTS idx_task_dependencies_task_id ON task_dependencies(task_id)",
            "CREATE INDEX IF NOT EXISTS idx_configs_type_active ON configs(config_type, is_active)",
        ]

        for index_sql in indexes:
            cursor.execute(index_sql)

        # 插入初始配置数据
        cursor.execute(
            """
            INSERT OR IGNORE INTO configs (config_id, config_type, name, config_data) VALUES 
            ('default_automation', 'automation', 'Default Automation Config', '{
              "screenshot_interval": 1000,
              "action_delay": 500,
              "max_wait_time": 10000,
              "confidence_threshold": 0.8
            }'),
            ('default_scheduler', 'scheduler', 'Default Scheduler Config', '{
              "max_concurrent_tasks": 3,
              "retry_delay": 5000,
              "health_check_interval": 30000
            }')
        """
        )

        conn.commit()

        print("✅ 数据库更新成功")

        # 验证更新后的表结构
        cursor.execute("PRAGMA table_info(tasks)")
        tasks_info = cursor.fetchall()
        print(f"📋 Tasks表列数: {len(tasks_info)}")

        # 检查id列是否存在
        id_column_exists = any(col[1] == "id" for col in tasks_info)
        print(f"🔍 ID列存在: {id_column_exists}")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ 数据库更新失败: {e}")
        return False


if __name__ == "__main__":
    update_database()
