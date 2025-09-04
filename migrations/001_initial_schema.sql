-- 崩坏星穹铁道自动化助手 - 初始数据库架构
-- 创建时间: 2025-01-22

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
    id TEXT PRIMARY KEY,  -- 添加id列作为主键
    task_id TEXT UNIQUE NOT NULL,  -- 保持task_id作为业务标识
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
CREATE INDEX IF NOT EXISTS idx_tasks_task_id ON tasks(task_id);
CREATE INDEX IF NOT EXISTS idx_task_executions_task_id ON task_executions(task_id);
CREATE INDEX IF NOT EXISTS idx_task_executions_start_time ON task_executions(start_time DESC);
CREATE INDEX IF NOT EXISTS idx_execution_actions_execution_id ON execution_actions(execution_id);
CREATE INDEX IF NOT EXISTS idx_execution_screenshots_execution_id ON execution_screenshots(execution_id);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_task_id ON task_dependencies(task_id);
CREATE INDEX IF NOT EXISTS idx_configs_type_active ON configs(config_type, is_active);

-- 插入初始数据
INSERT OR IGNORE INTO users (user_id, username, email) VALUES 
('default_user', 'Default User', 'default@example.com');

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
}');