-- 崩坏星穹铁道自动化助手 - 初始数据库架构
-- 创建时间: 2025-01-02
-- 版本: 1.0.0

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    preferences TEXT DEFAULT '{}'
);

-- 任务表
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    task_type TEXT NOT NULL,
    description TEXT DEFAULT '',
    priority INTEGER DEFAULT 2,
    status TEXT DEFAULT 'pending',
    config TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    last_error TEXT,
    execution_result TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 任务执行记录表
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
);

-- 执行动作表
CREATE TABLE IF NOT EXISTS execution_actions (
    action_id TEXT PRIMARY KEY,
    execution_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    action_data TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    result TEXT,
    duration_ms INTEGER,
    FOREIGN KEY (execution_id) REFERENCES task_executions(execution_id)
);

-- 执行截图表
CREATE TABLE IF NOT EXISTS execution_screenshots (
    screenshot_id TEXT PRIMARY KEY,
    execution_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    FOREIGN KEY (execution_id) REFERENCES task_executions(execution_id)
);

-- 任务依赖表
CREATE TABLE IF NOT EXISTS task_dependencies (
    dependency_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    depends_on_task_id TEXT NOT NULL,
    dependency_type TEXT DEFAULT 'sequential',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (depends_on_task_id) REFERENCES tasks(task_id)
);

-- 配置表
CREATE TABLE IF NOT EXISTS configs (
    config_id TEXT PRIMARY KEY,
    config_type TEXT NOT NULL,
    name TEXT NOT NULL,
    config_data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(task_type);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority DESC);

CREATE INDEX IF NOT EXISTS idx_task_executions_task_id ON task_executions(task_id);
CREATE INDEX IF NOT EXISTS idx_task_executions_start_time ON task_executions(start_time DESC);
CREATE INDEX IF NOT EXISTS idx_task_executions_status ON task_executions(status);

CREATE INDEX IF NOT EXISTS idx_execution_actions_execution_id ON execution_actions(execution_id);
CREATE INDEX IF NOT EXISTS idx_execution_actions_timestamp ON execution_actions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_execution_actions_type ON execution_actions(action_type);

CREATE INDEX IF NOT EXISTS idx_execution_screenshots_execution_id ON execution_screenshots(execution_id);
CREATE INDEX IF NOT EXISTS idx_execution_screenshots_timestamp ON execution_screenshots(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_task_dependencies_task_id ON task_dependencies(task_id);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_depends_on ON task_dependencies(depends_on_task_id);

CREATE INDEX IF NOT EXISTS idx_configs_type_active ON configs(config_type, is_active);
CREATE INDEX IF NOT EXISTS idx_configs_name ON configs(name);

-- 插入初始数据
INSERT OR IGNORE INTO users (user_id, username, email) VALUES 
('default_user', 'Default User', 'default@example.com');

-- 插入默认配置
INSERT OR IGNORE INTO configs (config_id, config_type, name, config_data) VALUES 
('default_automation', 'automation', 'Default Automation Config', '{
  "screenshot_interval": 1000,
  "action_delay": 500,
  "max_wait_time": 10000,
  "confidence_threshold": 0.8,
  "retry_attempts": 3,
  "timeout_seconds": 300
}'),
('default_game', 'game', 'Default Game Config', '{
  "window_title": "崩坏：星穹铁道",
  "process_name": "StarRail.exe",
  "resolution": [1920, 1080],
  "fullscreen": true
}'),
('default_task', 'task', 'Default Task Config', '{
  "max_concurrent_tasks": 3,
  "default_priority": 2,
  "auto_retry": true,
  "max_retries": 3,
  "retry_delay": 5000
}'),
('default_logging', 'logging', 'Default Logging Config', '{
  "level": "INFO",
  "file_rotation": "daily",
  "max_file_size": "10MB",
  "backup_count": 7,
  "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
}');

-- 创建触发器用于自动更新 updated_at 字段
CREATE TRIGGER IF NOT EXISTS update_users_updated_at
    AFTER UPDATE ON users
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE user_id = NEW.user_id;
END;

CREATE TRIGGER IF NOT EXISTS update_tasks_updated_at
    AFTER UPDATE ON tasks
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE tasks SET updated_at = CURRENT_TIMESTAMP WHERE task_id = NEW.task_id;
END;

CREATE TRIGGER IF NOT EXISTS update_configs_updated_at
    AFTER UPDATE ON configs
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE configs SET updated_at = CURRENT_TIMESTAMP WHERE config_id = NEW.config_id;
END;

-- 创建视图用于常用查询
CREATE VIEW IF NOT EXISTS task_summary AS
SELECT 
    t.task_id,
    t.name,
    t.task_type,
    t.status,
    t.priority,
    t.created_at,
    t.updated_at,
    COUNT(te.execution_id) as execution_count,
    MAX(te.start_time) as last_execution_time
FROM tasks t
LEFT JOIN task_executions te ON t.task_id = te.task_id
GROUP BY t.task_id;

CREATE VIEW IF NOT EXISTS execution_summary AS
SELECT 
    te.execution_id,
    te.task_id,
    t.name as task_name,
    te.status,
    te.start_time,
    te.end_time,
    CASE 
        WHEN te.end_time IS NOT NULL THEN 
            ROUND((julianday(te.end_time) - julianday(te.start_time)) * 86400, 2)
        ELSE NULL
    END as duration_seconds,
    COUNT(ea.action_id) as action_count,
    COUNT(es.screenshot_id) as screenshot_count
FROM task_executions te
JOIN tasks t ON te.task_id = t.task_id
LEFT JOIN execution_actions ea ON te.execution_id = ea.execution_id
LEFT JOIN execution_screenshots es ON te.execution_id = es.execution_id
GROUP BY te.execution_id;