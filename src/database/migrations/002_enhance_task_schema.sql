-- 增强任务管理数据库表结构
-- 添加任务动作和执行跟踪表

-- 创建任务动作表
CREATE TABLE IF NOT EXISTS task_actions (
    action_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    action_type TEXT NOT NULL CHECK (action_type IN ('click', 'key_press', 'wait', 'screenshot', 'custom')),
    action_order INTEGER NOT NULL,
    target_element TEXT,
    coordinates TEXT, -- JSON格式存储坐标信息 {"x": 100, "y": 200}
    key_code TEXT,
    wait_duration REAL,
    screenshot_path TEXT,
    custom_script TEXT,
    parameters TEXT, -- JSON格式存储其他参数
    is_enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
);

-- 创建任务执行记录表
CREATE TABLE IF NOT EXISTS task_executions (
    execution_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    execution_status TEXT DEFAULT 'running' CHECK (execution_status IN ('running', 'completed', 'failed', 'cancelled')),
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds REAL,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    current_action_index INTEGER DEFAULT 0,
    progress_percentage REAL DEFAULT 0.0,
    error_message TEXT,
    execution_log TEXT, -- JSON格式存储详细执行日志
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
);

-- 创建模板表（用于任务模板功能）
CREATE TABLE IF NOT EXISTS task_templates (
    template_id TEXT PRIMARY KEY,
    template_name TEXT NOT NULL,
    template_type TEXT NOT NULL,
    description TEXT,
    template_config TEXT NOT NULL, -- JSON格式存储模板配置
    is_public BOOLEAN DEFAULT 0,
    usage_count INTEGER DEFAULT 0,
    created_by TEXT DEFAULT 'default_user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- 创建模板匹配记录表
CREATE TABLE IF NOT EXISTS template_matches (
    match_id TEXT PRIMARY KEY,
    template_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    match_score REAL DEFAULT 0.0,
    match_details TEXT, -- JSON格式存储匹配详情
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES task_templates(template_id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
);

-- 创建配置历史表（用于配置版本管理）
CREATE TABLE IF NOT EXISTS config_history (
    history_id TEXT PRIMARY KEY,
    config_type TEXT NOT NULL, -- 'task', 'user', 'system'
    config_id TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    change_reason TEXT,
    changed_by TEXT DEFAULT 'default_user',
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (changed_by) REFERENCES users(user_id)
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_task_actions_task_id ON task_actions(task_id);
CREATE INDEX IF NOT EXISTS idx_task_actions_order ON task_actions(task_id, action_order);
CREATE INDEX IF NOT EXISTS idx_task_actions_type ON task_actions(action_type);

CREATE INDEX IF NOT EXISTS idx_task_executions_task_id ON task_executions(task_id);
CREATE INDEX IF NOT EXISTS idx_task_executions_status ON task_executions(execution_status);
CREATE INDEX IF NOT EXISTS idx_task_executions_start_time ON task_executions(start_time DESC);

CREATE INDEX IF NOT EXISTS idx_task_templates_type ON task_templates(template_type);
CREATE INDEX IF NOT EXISTS idx_task_templates_public ON task_templates(is_public);
CREATE INDEX IF NOT EXISTS idx_task_templates_usage ON task_templates(usage_count DESC);

CREATE INDEX IF NOT EXISTS idx_template_matches_template ON template_matches(template_id);
CREATE INDEX IF NOT EXISTS idx_template_matches_task ON template_matches(task_id);
CREATE INDEX IF NOT EXISTS idx_template_matches_score ON template_matches(match_score DESC);

CREATE INDEX IF NOT EXISTS idx_config_history_type ON config_history(config_type);
CREATE INDEX IF NOT EXISTS idx_config_history_config_id ON config_history(config_id);
CREATE INDEX IF NOT EXISTS idx_config_history_changed_at ON config_history(changed_at DESC);

-- 插入一些默认的任务模板
INSERT OR IGNORE INTO task_templates (template_id, template_name, template_type, description, template_config, is_public, created_by) VALUES
('tpl_001', '每日签到', 'daily_mission', '自动完成每日签到任务', '{"task_type": "daily_mission", "priority": "medium", "actions": [{"type": "click", "target": "sign_in_button", "coordinates": {"x": 500, "y": 300}}]}', 1, 'default_user'),
('tpl_002', '材料刷取', 'material_farming', '自动刷取指定材料', '{"task_type": "material_farming", "priority": "high", "actions": [{"type": "click", "target": "material_stage"}, {"type": "wait", "duration": 3}, {"type": "click", "target": "start_battle"}]}', 1, 'default_user'),
('tpl_003', '基础点击序列', 'custom_sequence', '简单的点击操作序列', '{"task_type": "custom_sequence", "priority": "low", "actions": [{"type": "click", "coordinates": {"x": 100, "y": 100}}, {"type": "wait", "duration": 1}, {"type": "click", "coordinates": {"x": 200, "y": 200}}]}', 1, 'default_user');

-- 插入一些默认配置历史记录
INSERT OR IGNORE INTO config_history (history_id, config_type, config_id, old_value, new_value, change_reason, changed_by) VALUES
('hist_001', 'system', 'database_version', '1.0', '1.1', '增强任务管理数据库表结构', 'default_user');