-- 添加攻略步骤表
-- 这个表用于存储攻略的详细步骤信息，支持更精细的步骤管理

CREATE TABLE IF NOT EXISTS strategy_steps (
  id TEXT PRIMARY KEY,
  strategyId TEXT NOT NULL,
  stepNumber INTEGER NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  action TEXT NOT NULL,
  parameters TEXT,
  expectedResult TEXT,
  timeout INTEGER DEFAULT 30000,
  retryCount INTEGER DEFAULT 0,
  isOptional INTEGER DEFAULT 0,
  conditions TEXT,
  notes TEXT,
  createdAt TEXT DEFAULT CURRENT_TIMESTAMP,
  updatedAt TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (strategyId) REFERENCES strategies (id) ON DELETE CASCADE
);

-- 为strategy_steps表创建索引
CREATE INDEX IF NOT EXISTS idx_strategy_steps_strategy_id ON strategy_steps(strategyId);
CREATE INDEX IF NOT EXISTS idx_strategy_steps_step_number ON strategy_steps(stepNumber);
CREATE INDEX IF NOT EXISTS idx_strategy_steps_strategy_step ON strategy_steps(strategyId, stepNumber);

-- 确保每个攻略的步骤编号唯一
CREATE UNIQUE INDEX IF NOT EXISTS idx_strategy_steps_unique ON strategy_steps(strategyId, stepNumber);