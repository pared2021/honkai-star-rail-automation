// 数据库服务模块
import sqlite3 from 'sqlite3';
import { TaskType } from '../types/index.js';
import { v4 as uuidv4 } from 'uuid';
import * as fs from 'fs';
import * as path from 'path';
export class DatabaseService {
    constructor(dbPath = './data/game.db') {
        Object.defineProperty(this, "db", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: null
        });
        Object.defineProperty(this, "dbPath", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        this.dbPath = dbPath;
    }
    // 初始化数据库连接
    async initialize() {
        return new Promise((resolve, reject) => {
            try {
                // 确保数据库目录存在
                const dbDir = path.dirname(this.dbPath);
                if (!fs.existsSync(dbDir)) {
                    fs.mkdirSync(dbDir, { recursive: true });
                }
                // 创建数据库连接
                this.db = new sqlite3.Database(this.dbPath, (err) => {
                    if (err) {
                        console.error('数据库连接失败:', err);
                        reject(err);
                        return;
                    }
                    // 启用外键约束
                    this.db.run('PRAGMA foreign_keys = ON', (err) => {
                        if (err) {
                            console.error('启用外键约束失败:', err);
                            reject(err);
                            return;
                        }
                        // 创建数据表
                        this.createTables()
                            .then(() => {
                            console.log('数据库初始化成功');
                            resolve();
                        })
                            .catch(reject);
                    });
                });
            }
            catch (error) {
                console.error('数据库初始化失败:', error);
                reject(error);
            }
        });
    }
    /**
     * 创建数据表
     */
    async createTables() {
        if (!this.db) {
            throw new Error('数据库未初始化');
        }
        return new Promise((resolve, reject) => {
            const tables = [
                // 创建账号表
                `CREATE TABLE IF NOT EXISTS accounts (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL UNIQUE,
          gameAccount TEXT NOT NULL,
          isActive BOOLEAN DEFAULT 1,
          createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
          lastLoginAt DATETIME
        )`,
                // 创建任务表
                `CREATE TABLE IF NOT EXISTS tasks (
          id TEXT PRIMARY KEY,
          accountId TEXT NOT NULL,
          type TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'pending',
          config TEXT,
          createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
          startedAt DATETIME,
          completedAt DATETIME,
          error TEXT,
          FOREIGN KEY (accountId) REFERENCES accounts(id) ON DELETE CASCADE
        )`,
                // 创建任务配置表
                `CREATE TABLE IF NOT EXISTS task_configs (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          taskType TEXT NOT NULL,
          config TEXT NOT NULL,
          isDefault BOOLEAN DEFAULT 0,
          createdAt DATETIME DEFAULT CURRENT_TIMESTAMP
        )`,
                // 创建任务日志表
                `CREATE TABLE IF NOT EXISTS task_logs (
          id TEXT PRIMARY KEY,
          taskId TEXT NOT NULL,
          level TEXT NOT NULL,
          message TEXT NOT NULL,
          timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (taskId) REFERENCES tasks(id) ON DELETE CASCADE
        )`,
                // 创建账号统计表
                `CREATE TABLE IF NOT EXISTS account_stats (
          id TEXT PRIMARY KEY,
          accountId TEXT NOT NULL UNIQUE,
          totalTasks INTEGER DEFAULT 0,
          completedTasks INTEGER DEFAULT 0,
          failedTasks INTEGER DEFAULT 0,
          totalPlayTime INTEGER DEFAULT 0,
          lastActiveAt DATETIME,
          createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (accountId) REFERENCES accounts(id) ON DELETE CASCADE
        )`,
                // 创建任务信息表
                `CREATE TABLE IF NOT EXISTS task_infos (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          type TEXT NOT NULL,
          category TEXT NOT NULL,
          description TEXT,
          requirements TEXT,
          rewards TEXT,
          difficulty INTEGER DEFAULT 1,
          estimatedTime INTEGER DEFAULT 0,
          prerequisites TEXT,
          location TEXT,
          npcName TEXT,
          isRepeatable INTEGER DEFAULT 0,
          isDaily INTEGER DEFAULT 0,
          isWeekly INTEGER DEFAULT 0,
          version TEXT,
          tags TEXT,
          collectionStatus TEXT DEFAULT 'pending',
          lastUpdated TEXT DEFAULT CURRENT_TIMESTAMP,
          createdAt TEXT DEFAULT CURRENT_TIMESTAMP
        )`,
                // 创建攻略表
                `CREATE TABLE IF NOT EXISTS strategies (
          id TEXT PRIMARY KEY,
          taskInfoId TEXT NOT NULL,
          name TEXT NOT NULL,
          description TEXT,
          steps TEXT NOT NULL,
          estimatedTime INTEGER DEFAULT 0,
          successRate REAL DEFAULT 0,
          difficulty INTEGER DEFAULT 1,
          requirements TEXT,
          notes TEXT,
          author TEXT,
          version TEXT,
          isVerified INTEGER DEFAULT 0,
          evaluations TEXT,
          createdAt TEXT DEFAULT CURRENT_TIMESTAMP,
          updatedAt TEXT DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (taskInfoId) REFERENCES task_infos (id) ON DELETE CASCADE
        )`,
                // 创建攻略步骤表
                `CREATE TABLE IF NOT EXISTS strategy_steps (
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
        )`,
                // 创建攻略评估表
                `CREATE TABLE IF NOT EXISTS strategy_evaluations (
          id TEXT PRIMARY KEY,
          strategyId TEXT NOT NULL,
          executionTime INTEGER NOT NULL,
          successRate REAL NOT NULL,
          errorCount INTEGER DEFAULT 0,
          notes TEXT,
          factors TEXT,
          timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (strategyId) REFERENCES strategies (id) ON DELETE CASCADE
        )`,
                // 创建用户反馈表
                `CREATE TABLE IF NOT EXISTS strategy_feedbacks (
          id TEXT PRIMARY KEY,
          strategyId TEXT NOT NULL,
          userId TEXT NOT NULL,
          rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
          category TEXT,
          tags TEXT,
          comment TEXT,
          likeCount INTEGER DEFAULT 0,
          officialReply TEXT,
          createdAt TEXT DEFAULT CURRENT_TIMESTAMP,
          updatedAt TEXT DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (strategyId) REFERENCES strategies (id) ON DELETE CASCADE
        )`,
                // 创建反馈点赞表
                `CREATE TABLE IF NOT EXISTS feedback_likes (
          id TEXT PRIMARY KEY,
          feedbackId TEXT NOT NULL,
          userId TEXT NOT NULL,
          createdAt TEXT DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (feedbackId) REFERENCES strategy_feedbacks (id) ON DELETE CASCADE,
          UNIQUE(feedbackId, userId)
        )`,
                // 创建自动化配置表
                `CREATE TABLE IF NOT EXISTS automation_configs (
          id TEXT PRIMARY KEY,
          accountId TEXT NOT NULL,
          taskTypes TEXT NOT NULL,
          automationLevel TEXT DEFAULT 'medium',
          enableSmartRetry INTEGER DEFAULT 1,
          maxRetryAttempts INTEGER DEFAULT 3,
          retryDelay INTEGER DEFAULT 5000,
          enableAdaptiveDelay INTEGER DEFAULT 1,
          enableErrorRecovery INTEGER DEFAULT 1,
          notificationSettings TEXT,
          customSettings TEXT,
          isActive INTEGER DEFAULT 1,
          createdAt TEXT DEFAULT CURRENT_TIMESTAMP,
          updatedAt TEXT DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (accountId) REFERENCES accounts (id) ON DELETE CASCADE
        )`,
                // 创建调度配置表
                `CREATE TABLE IF NOT EXISTS schedule_configs (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          accountId TEXT,
          taskType TEXT NOT NULL,
          scheduleType TEXT NOT NULL DEFAULT 'interval',
          intervalMinutes INTEGER,
          cronExpression TEXT,
          startTime TEXT,
          endTime TEXT,
          enabled INTEGER DEFAULT 1,
          maxExecutions INTEGER,
          currentExecutions INTEGER DEFAULT 0,
          lastExecutedAt TEXT,
          nextExecutionAt TEXT,
          config TEXT,
          createdAt TEXT DEFAULT CURRENT_TIMESTAMP,
          updatedAt TEXT DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (accountId) REFERENCES accounts (id) ON DELETE CASCADE
        )`,
                // 创建系统配置表
                `CREATE TABLE IF NOT EXISTS system_configs (
          id TEXT PRIMARY KEY,
          configKey TEXT NOT NULL UNIQUE,
          configValue TEXT NOT NULL,
          configType TEXT DEFAULT 'string',
          description TEXT,
          category TEXT DEFAULT 'general',
          isEditable INTEGER DEFAULT 1,
          createdAt TEXT DEFAULT CURRENT_TIMESTAMP,
          updatedAt TEXT DEFAULT CURRENT_TIMESTAMP
        )`
            ];
            let completed = 0;
            const total = tables.length;
            tables.forEach((sql, index) => {
                this.db.run(sql, (err) => {
                    if (err) {
                        console.error(`创建表失败 (${index}):`, err);
                        reject(err);
                        return;
                    }
                    completed++;
                    if (completed === total) {
                        console.log('数据表创建完成');
                        this.createIndexes().then(() => {
                            console.log('数据库索引创建完成');
                            resolve();
                        }).catch((indexErr) => {
                            console.error('创建索引失败:', indexErr);
                            reject(indexErr);
                        });
                    }
                });
            });
        });
    }
    /**
     * 创建数据库索引以优化查询性能
     */
    async createIndexes() {
        if (!this.db)
            throw new Error('数据库未初始化');
        const indexes = [
            // 攻略表索引
            'CREATE INDEX IF NOT EXISTS idx_strategies_task_info_id ON strategies(taskInfoId)',
            'CREATE INDEX IF NOT EXISTS idx_strategies_success_rate ON strategies(successRate DESC)',
            'CREATE INDEX IF NOT EXISTS idx_strategies_author ON strategies(author)',
            'CREATE INDEX IF NOT EXISTS idx_strategies_difficulty ON strategies(difficulty)',
            'CREATE INDEX IF NOT EXISTS idx_strategies_verified ON strategies(isVerified)',
            'CREATE INDEX IF NOT EXISTS idx_strategies_created_at ON strategies(createdAt DESC)',
            // 任务信息表索引
            'CREATE INDEX IF NOT EXISTS idx_task_infos_type ON task_infos(type)',
            'CREATE INDEX IF NOT EXISTS idx_task_infos_category ON task_infos(category)',
            'CREATE INDEX IF NOT EXISTS idx_task_infos_difficulty ON task_infos(difficulty)',
            'CREATE INDEX IF NOT EXISTS idx_task_infos_collection_status ON task_infos(collectionStatus)',
            // 攻略步骤表索引
            'CREATE INDEX IF NOT EXISTS idx_strategy_steps_strategy_id ON strategy_steps(strategyId)',
            'CREATE INDEX IF NOT EXISTS idx_strategy_steps_step_number ON strategy_steps(stepNumber)',
            'CREATE INDEX IF NOT EXISTS idx_strategy_steps_strategy_step ON strategy_steps(strategyId, stepNumber)',
            'CREATE UNIQUE INDEX IF NOT EXISTS idx_strategy_steps_unique ON strategy_steps(strategyId, stepNumber)',
            // 攻略评估表索引
            'CREATE INDEX IF NOT EXISTS idx_strategy_evaluations_strategy_id ON strategy_evaluations(strategyId)',
            'CREATE INDEX IF NOT EXISTS idx_strategy_evaluations_timestamp ON strategy_evaluations(timestamp DESC)',
            // 任务表索引
            'CREATE INDEX IF NOT EXISTS idx_tasks_account_id ON tasks(accountId)',
            'CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(type)',
            'CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)',
            'CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(createdAt DESC)',
            // 账号表索引
            'CREATE INDEX IF NOT EXISTS idx_accounts_active ON accounts(isActive)',
            'CREATE INDEX IF NOT EXISTS idx_accounts_game_account ON accounts(gameAccount)',
            // 自动化配置表索引
            'CREATE INDEX IF NOT EXISTS idx_automation_configs_account_id ON automation_configs(accountId)',
            'CREATE INDEX IF NOT EXISTS idx_automation_configs_active ON automation_configs(isActive)',
            // 复合索引用于常见查询
            'CREATE INDEX IF NOT EXISTS idx_strategies_task_success ON strategies(taskInfoId, successRate DESC)',
            'CREATE INDEX IF NOT EXISTS idx_strategies_author_verified ON strategies(author, isVerified)',
            'CREATE INDEX IF NOT EXISTS idx_task_infos_type_difficulty ON task_infos(type, difficulty)',
            'CREATE INDEX IF NOT EXISTS idx_strategy_feedbacks_strategy_id ON strategy_feedbacks(strategyId)',
            'CREATE INDEX IF NOT EXISTS idx_strategy_feedbacks_rating ON strategy_feedbacks(rating)',
            'CREATE INDEX IF NOT EXISTS idx_feedback_likes_feedback_id ON feedback_likes(feedbackId)',
            'CREATE INDEX IF NOT EXISTS idx_feedback_likes_user_id ON feedback_likes(userId)'
        ];
        return new Promise((resolve, reject) => {
            let completed = 0;
            const total = indexes.length;
            indexes.forEach((sql, index) => {
                this.db.run(sql, (err) => {
                    if (err) {
                        console.error(`创建索引失败 (${index}):`, err);
                        reject(err);
                        return;
                    }
                    completed++;
                    if (completed === total) {
                        resolve();
                    }
                });
            });
        });
    }
    /**
     * 账号相关操作
     */
    async createAccount(account) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const id = uuidv4();
        const createdAt = new Date();
        const newAccount = {
            ...account,
            id,
            createdAt
        };
        const stmt = this.db.prepare(`
      INSERT INTO accounts (id, name, gameAccount, isActive, createdAt)
      VALUES (?, ?, ?, ?, ?)
    `);
        stmt.run(id, account.name, account.gameAccount, account.isActive ? 1 : 0, createdAt.toISOString());
        return newAccount;
    }
    async getAccounts() {
        if (!this.db)
            throw new Error('数据库未初始化');
        const stmt = this.db.prepare('SELECT * FROM accounts ORDER BY createdAt DESC');
        const rows = stmt.all();
        return rows.map((row) => ({
            id: row.id,
            name: row.name,
            gameAccount: row.gameAccount,
            isActive: Boolean(row.isActive),
            createdAt: new Date(row.createdAt),
            lastLoginAt: row.lastLoginAt ? new Date(row.lastLoginAt) : undefined
        }));
    }
    async getAccountById(id) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const stmt = this.db.prepare('SELECT * FROM accounts WHERE id = ?');
        const row = stmt.get(id);
        if (!row)
            return null;
        return {
            id: row.id,
            name: row.name,
            gameAccount: row.gameAccount,
            isActive: Boolean(row.isActive),
            createdAt: new Date(row.createdAt),
            lastLoginAt: row.lastLoginAt ? new Date(row.lastLoginAt) : undefined
        };
    }
    updateAccount(id, updates) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const fields = [];
        const values = [];
        if (updates.configName !== undefined) {
            fields.push('name = ?');
            values.push(updates.configName);
        }
        if (updates.gameAccount !== undefined) {
            fields.push('gameAccount = ?');
            values.push(updates.gameAccount);
        }
        if (updates.isActive !== undefined) {
            fields.push('isActive = ?');
            values.push(updates.isActive ? 1 : 0);
        }
        if (updates.lastLoginAt !== undefined) {
            fields.push('lastLoginAt = ?');
            values.push(updates.lastLoginAt.toISOString());
        }
        if (fields.length === 0)
            return Promise.resolve(false);
        values.push(id);
        return new Promise((resolve, reject) => {
            const stmt = this.db.prepare(`UPDATE accounts SET ${fields.join(', ')} WHERE id = ?`);
            stmt.run(values, function (err) {
                if (err) {
                    reject(err);
                }
                else {
                    resolve(this.changes > 0);
                }
            });
            stmt.finalize();
        });
    }
    deleteAccount(id) {
        if (!this.db)
            throw new Error('数据库未初始化');
        return new Promise((resolve, reject) => {
            const stmt = this.db.prepare('DELETE FROM accounts WHERE id = ?');
            stmt.run([id], function (err) {
                if (err) {
                    reject(err);
                }
                else {
                    resolve(this.changes > 0);
                }
            });
            stmt.finalize();
        });
    }
    /**
     * 任务相关操作
     */
    async createTask(task) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const id = uuidv4();
        const createdAt = new Date();
        const newTask = {
            ...task,
            id,
            createdAt
        };
        const stmt = this.db.prepare(`
      INSERT INTO tasks (id, accountId, taskType, status, config, createdAt, startTime, endTime)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `);
        stmt.run(id, task.accountId, task.taskType, task.status, task.config ? JSON.stringify(task.config) : null, createdAt.toISOString(), task.startTime?.toISOString() || null, task.endTime?.toISOString() || null);
        return newTask;
    }
    async getTasks(accountId) {
        if (!this.db)
            throw new Error('数据库未初始化');
        let query = 'SELECT * FROM tasks';
        const params = [];
        if (accountId) {
            query += ' WHERE accountId = ?';
            params.push(accountId);
        }
        query += ' ORDER BY createdAt DESC';
        const stmt = this.db.prepare(query);
        const rows = stmt.all(...params);
        return rows.map((row) => ({
            id: row.id,
            accountId: row.accountId,
            taskType: row.taskType,
            status: row.status,
            config: row.config ? JSON.parse(row.config) : undefined,
            createdAt: new Date(row.createdAt),
            startTime: row.startTime ? new Date(row.startTime) : undefined,
            endTime: row.endTime ? new Date(row.endTime) : undefined
        }));
    }
    async getTaskById(id) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const stmt = this.db.prepare('SELECT * FROM tasks WHERE id = ?');
        const row = stmt.get(id);
        if (!row)
            return null;
        return {
            id: row.id,
            accountId: row.accountId,
            taskType: row.taskType,
            status: row.status,
            config: row.config ? JSON.parse(row.config) : undefined,
            createdAt: new Date(row.createdAt),
            startTime: row.startTime ? new Date(row.startTime) : undefined,
            endTime: row.endTime ? new Date(row.endTime) : undefined
        };
    }
    async updateTask(id, updates) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const fields = [];
        const values = [];
        if (updates.status !== undefined) {
            fields.push('status = ?');
            values.push(updates.status);
        }
        if (updates.config !== undefined) {
            fields.push('config = ?');
            values.push(JSON.stringify(updates.config || {}));
        }
        if (updates.startTime !== undefined) {
            fields.push('startTime = ?');
            values.push(updates.startTime?.toISOString() || null);
        }
        if (updates.endTime !== undefined) {
            fields.push('endTime = ?');
            values.push(updates.endTime?.toISOString() || null);
        }
        if (fields.length === 0)
            return false;
        values.push(id);
        const stmt = this.db.prepare(`UPDATE tasks SET ${fields.join(', ')} WHERE id = ?`);
        const result = stmt.run(...values);
        return result.changes > 0;
    }
    async deleteTask(id) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const stmt = this.db.prepare('DELETE FROM tasks WHERE id = ?');
        const result = stmt.run(id);
        return result.changes > 0;
    }
    /**
     * 任务配置相关操作
     */
    async createTaskConfig(config) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const id = uuidv4();
        const createdAt = new Date();
        const newConfig = {
            ...config,
            id,
            createdAt
        };
        const stmt = this.db.prepare(`
      INSERT INTO task_configs (id, name, taskType, config, isDefault, createdAt)
      VALUES (?, ?, ?, ?, ?, ?)
    `);
        stmt.run(id, config.configName, config.taskType, JSON.stringify(config.configData), config.isDefault ? 1 : 0, createdAt.toISOString());
        return newConfig;
    }
    async getTaskConfigs(taskType) {
        if (!this.db)
            throw new Error('数据库未初始化');
        let query = 'SELECT * FROM task_configs';
        const params = [];
        if (taskType) {
            query += ' WHERE taskType = ?';
            params.push(taskType);
        }
        query += ' ORDER BY isDefault DESC, createdAt DESC';
        const stmt = this.db.prepare(query);
        const rows = stmt.all(...params);
        return rows.map((row) => ({
            id: row.id,
            configName: row.name,
            taskType: row.taskType,
            configData: JSON.parse(row.config),
            isDefault: Boolean(row.isDefault),
            createdAt: new Date(row.createdAt)
        }));
    }
    async updateTaskConfig(id, updates) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const fields = [];
        const values = [];
        if (updates.configName !== undefined) {
            fields.push('name = ?');
            values.push(updates.configName);
        }
        if (updates.configData !== undefined) {
            fields.push('config = ?');
            values.push(JSON.stringify(updates.configData || {}));
        }
        if (updates.isDefault !== undefined) {
            fields.push('isDefault = ?');
            values.push(updates.isDefault ? 1 : 0);
        }
        if (fields.length === 0)
            return false;
        values.push(id);
        const stmt = this.db.prepare(`UPDATE task_configs SET ${fields.join(', ')} WHERE id = ?`);
        const result = stmt.run(...values);
        return result.changes > 0;
    }
    async deleteTaskConfig(id) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const stmt = this.db.prepare('DELETE FROM task_configs WHERE id = ?');
        const result = stmt.run(id);
        return result.changes > 0;
    }
    /**
     * 任务日志相关操作
     */
    async createTaskLog(log) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const id = uuidv4();
        const timestamp = new Date();
        const newLog = {
            ...log,
            id,
            timestamp
        };
        const stmt = this.db.prepare(`
      INSERT INTO task_logs (id, taskId, level, message, timestamp)
      VALUES (?, ?, ?, ?, ?)
    `);
        stmt.run(id, log.taskId, log.level, log.message, timestamp.toISOString());
        return newLog;
    }
    async getTaskLogs(taskId) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const stmt = this.db.prepare('SELECT * FROM task_logs WHERE taskId = ? ORDER BY timestamp ASC');
        const rows = stmt.all(taskId);
        return rows.map((row) => ({
            id: row.id,
            taskId: row.taskId,
            level: row.level,
            message: row.message,
            timestamp: new Date(row.timestamp)
        }));
    }
    async deleteTaskLogs(taskId) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const stmt = this.db.prepare('DELETE FROM task_logs WHERE taskId = ?');
        const result = stmt.run(taskId);
        return result.changes > 0;
    }
    /**
     * 统计数据相关操作
     */
    async createAccountStats(stats) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const id = uuidv4();
        const newStats = {
            ...stats,
            id
        };
        const stmt = this.db.prepare(`
      INSERT OR REPLACE INTO account_stats (id, accountId, date, tasksCompleted, tasksFailed, totalRuntime)
      VALUES (?, ?, ?, ?, ?, ?)
    `);
        stmt.run(id, stats.accountId, stats.date, stats.tasksCompleted, stats.tasksFailed, stats.totalRuntime);
        return newStats;
    }
    async getAccountStats(accountId, startDate, endDate) {
        if (!this.db)
            throw new Error('数据库未初始化');
        let query = 'SELECT * FROM account_stats WHERE accountId = ?';
        const params = [accountId];
        if (startDate) {
            query += ' AND date >= ?';
            params.push(startDate.toISOString().split('T')[0]);
        }
        if (endDate) {
            query += ' AND date <= ?';
            params.push(endDate.toISOString().split('T')[0]);
        }
        query += ' ORDER BY date DESC';
        const stmt = this.db.prepare(query);
        const rows = stmt.all(...params);
        return rows.map((row) => ({
            id: row.id,
            accountId: row.accountId,
            date: row.date,
            tasksCompleted: row.tasksCompleted,
            tasksFailed: row.tasksFailed,
            totalRuntime: row.totalRuntime,
            loginCount: row.loginCount || 0,
            totalPlayTime: row.totalPlayTime || 0,
            createdAt: row.createdAt || new Date().toISOString(),
            updatedAt: row.updatedAt || new Date().toISOString()
        }));
    }
    updateAccountStats(accountId, date, updates) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const fields = [];
        const values = [];
        if (updates.tasksCompleted !== undefined) {
            fields.push('tasksCompleted = ?');
            values.push(updates.tasksCompleted);
        }
        if (updates.tasksFailed !== undefined) {
            fields.push('tasksFailed = ?');
            values.push(updates.tasksFailed);
        }
        if (updates.totalRuntime !== undefined) {
            fields.push('totalRuntime = ?');
            values.push(updates.totalRuntime);
        }
        if (updates.loginCount !== undefined) {
            fields.push('loginCount = ?');
            values.push(updates.loginCount);
        }
        if (updates.totalPlayTime !== undefined) {
            fields.push('totalPlayTime = ?');
            values.push(updates.totalPlayTime);
        }
        if (updates.lastLogin !== undefined) {
            fields.push('lastLogin = ?');
            values.push(updates.lastLogin);
        }
        if (fields.length === 0)
            return Promise.resolve(false);
        values.push(accountId, date);
        const sql = `UPDATE account_stats SET ${fields.join(', ')}, updatedAt = datetime('now') WHERE accountId = ? AND date = ?`;
        return new Promise((resolve, reject) => {
            const stmt = this.db.prepare(sql);
            stmt.run(values, function (err) {
                if (err) {
                    reject(err);
                }
                else {
                    resolve(this.changes > 0);
                }
            });
            stmt.finalize();
        });
    }
    /**
     * 任务信息相关操作
     */
    async createTaskInfo(taskInfo) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const id = uuidv4();
        const now = new Date().toISOString();
        const newTaskInfo = {
            ...taskInfo,
            id,
            lastUpdated: new Date(now)
        };
        const stmt = this.db.prepare(`
      INSERT INTO task_infos (
        id, name, type, category, description, requirements, rewards,
        difficulty, estimatedTime, prerequisites, location, npcName,
        isRepeatable, isDaily, isWeekly, version, tags, collectionStatus,
        lastUpdated, createdAt
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
        stmt.run(id, taskInfo.taskName, taskInfo.taskType, taskInfo.description, taskInfo.description || null, JSON.stringify([]), JSON.stringify([]), taskInfo.difficulty || 1, taskInfo.estimatedTime || 0, JSON.stringify([]), taskInfo.location || null, taskInfo.npcName || null, taskInfo.isRepeatable ? 1 : 0, 0, 0, '1.0', JSON.stringify([]), 'collected', now, now);
        return newTaskInfo;
    }
    async updateTaskInfo(id, updates) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const fields = [];
        const values = [];
        Object.entries(updates).forEach(([key, value]) => {
            if (key !== 'id' && key !== 'createdAt' && value !== undefined) {
                if (key === 'requirements' || key === 'rewards' || key === 'prerequisites' || key === 'tags') {
                    fields.push(`${key} = ?`);
                    values.push(JSON.stringify(value));
                }
                else if (key === 'isRepeatable' || key === 'isDaily' || key === 'isWeekly') {
                    fields.push(`${key} = ?`);
                    values.push(value ? 1 : 0);
                }
                else {
                    fields.push(`${key} = ?`);
                    values.push(value);
                }
            }
        });
        if (fields.length === 0)
            return false;
        fields.push('lastUpdated = ?');
        values.push(new Date().toISOString());
        values.push(id);
        const stmt = this.db.prepare(`UPDATE task_infos SET ${fields.join(', ')} WHERE id = ?`);
        const result = stmt.run(...values);
        return result.changes > 0;
    }
    /**
     * 攻略相关操作
     */
    async createStrategy(strategy) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const id = uuidv4();
        const now = new Date().toISOString();
        const newStrategy = {
            ...strategy,
            id,
            createdAt: new Date(now),
            lastUpdated: new Date(now)
        };
        const stmt = this.db.prepare(`
      INSERT INTO strategies (
        id, taskInfoId, name, description, steps, estimatedTime,
        successRate, difficulty, requirements, notes, author, version,
        isVerified, evaluations, createdAt, updatedAt
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
        stmt.run(id, strategy.taskInfoId, strategy.strategyName, strategy.description || null, JSON.stringify(strategy.steps), strategy.estimatedTime || 0, strategy.successRate || 0, strategy.difficulty || 1, JSON.stringify(strategy.requirements || []), JSON.stringify(strategy.tips || []), strategy.author || null, strategy.version || null, strategy.isVerified ? 1 : 0, JSON.stringify([]), now, now);
        return newStrategy;
    }
    async getStrategies(options) {
        if (!this.db)
            throw new Error('数据库未初始化');
        let query = 'SELECT * FROM strategies';
        const params = [];
        const conditions = [];
        // 构建WHERE条件
        if (options?.taskInfoId) {
            conditions.push('taskInfoId = ?');
            params.push(options.taskInfoId);
        }
        if (options?.author) {
            conditions.push('author = ?');
            params.push(options.author);
        }
        if (options?.difficulty !== undefined) {
            conditions.push('difficulty = ?');
            params.push(options.difficulty);
        }
        if (options?.isVerified !== undefined) {
            conditions.push('isVerified = ?');
            params.push(options.isVerified ? 1 : 0);
        }
        if (options?.minSuccessRate !== undefined) {
            conditions.push('successRate >= ?');
            params.push(options.minSuccessRate);
        }
        if (conditions.length > 0) {
            query += ' WHERE ' + conditions.join(' AND ');
        }
        // 构建ORDER BY
        const sortBy = options?.sortBy || 'successRate';
        const sortOrder = options?.sortOrder || 'DESC';
        query += ` ORDER BY ${sortBy} ${sortOrder}`;
        // 如果按成功率排序，添加创建时间作为次要排序
        if (sortBy === 'successRate') {
            query += ', createdAt DESC';
        }
        // 添加分页
        if (options?.limit) {
            query += ' LIMIT ?';
            params.push(options.limit.toString());
            if (options?.offset) {
                query += ' OFFSET ?';
                params.push(options.offset);
            }
        }
        const stmt = this.db.prepare(query);
        const rows = stmt.all(...params);
        return rows.map((row) => ({
            id: row.id,
            taskInfoId: row.taskInfoId,
            strategyName: row.name,
            description: row.description,
            steps: row.steps ? JSON.parse(row.steps) : [],
            estimatedTime: row.estimatedTime,
            successRate: row.successRate,
            difficulty: row.difficulty,
            requirements: row.requirements ? JSON.parse(row.requirements) : [],
            tips: row.notes ? [row.notes] : [],
            author: row.author,
            version: row.version,
            isVerified: Boolean(row.isVerified),
            createdAt: new Date(row.createdAt),
            lastUpdated: new Date(row.updatedAt)
        }));
    }
    /**
     * 根据ID获取单个攻略
     */
    async getStrategy(id) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const stmt = this.db.prepare('SELECT * FROM strategies WHERE id = ?');
        const row = stmt.get(id);
        if (!row)
            return null;
        return {
            id: row.id,
            taskInfoId: row.taskInfoId,
            strategyName: row.name,
            description: row.description,
            steps: row.steps ? JSON.parse(row.steps) : [],
            estimatedTime: row.estimatedTime,
            successRate: row.successRate,
            difficulty: row.difficulty,
            requirements: row.requirements ? JSON.parse(row.requirements) : [],
            tips: row.notes ? [row.notes] : [],
            author: row.author,
            version: row.version,
            isVerified: Boolean(row.isVerified),
            createdAt: new Date(row.createdAt),
            lastUpdated: new Date(row.updatedAt)
        };
    }
    async updateStrategy(id, updates) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const fields = [];
        const values = [];
        Object.entries(updates).forEach(([key, value]) => {
            if (key !== 'id' && key !== 'createdAt' && value !== undefined) {
                if (key === 'steps' || key === 'requirements' || key === 'evaluations') {
                    fields.push(`${key} = ?`);
                    values.push(JSON.stringify(value));
                }
                else if (key === 'isVerified') {
                    fields.push(`${key} = ?`);
                    values.push(value ? 1 : 0);
                }
                else {
                    fields.push(`${key} = ?`);
                    values.push(value);
                }
            }
        });
        if (fields.length === 0)
            return false;
        fields.push('updatedAt = ?');
        values.push(new Date().toISOString());
        values.push(id);
        const stmt = this.db.prepare(`UPDATE strategies SET ${fields.join(', ')} WHERE id = ?`);
        const result = stmt.run(...values);
        return result.changes > 0;
    }
    async addStrategy(strategy) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const id = Date.now().toString();
        const now = new Date().toISOString();
        const newStrategy = {
            ...strategy,
            id,
            createdAt: new Date(now),
            lastUpdated: new Date(now)
        };
        const stmt = this.db.prepare(`
      INSERT INTO strategies (
        id, taskInfoId, name, description, steps, estimatedTime,
        successRate, difficulty, requirements, notes, author, version,
        isVerified, evaluations, createdAt, updatedAt
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
        stmt.run(id, strategy.taskInfoId, strategy.strategyName || '', strategy.description || '', JSON.stringify(strategy.steps || []), strategy.estimatedTime || 0, strategy.successRate || 0, strategy.difficulty || 1, JSON.stringify(strategy.requirements || []), JSON.stringify(strategy.tips || []), strategy.author || '', strategy.version || '1.0', strategy.isVerified ? 1 : 0, JSON.stringify([]), now, now);
        return newStrategy;
    }
    async cloneStrategy(id, newName) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const original = await this.getStrategy(id);
        if (!original)
            throw new Error('策略不存在');
        return this.addStrategy({
            ...original,
            strategyName: newName,
            isVerified: false,
            successRate: 0
        });
    }
    async getStrategySteps(strategyId) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const strategy = await this.getStrategy(strategyId);
        if (!strategy)
            return [];
        return strategy.steps || [];
    }
    /**
     * 批量创建攻略
     */
    async batchCreateStrategies(strategies) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const createdStrategies = [];
        const now = new Date().toISOString();
        // 开始事务
        this.db.run('BEGIN TRANSACTION');
        try {
            const stmt = this.db.prepare(`
        INSERT INTO strategies (
          id, taskInfoId, name, description, steps, estimatedTime,
          successRate, difficulty, requirements, notes, author, version,
          isVerified, evaluations, createdAt, updatedAt
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `);
            for (const strategy of strategies) {
                const id = uuidv4();
                const newStrategy = {
                    ...strategy,
                    id,
                    createdAt: new Date(now),
                    lastUpdated: new Date(now)
                };
                stmt.run(id, strategy.taskInfoId, strategy.strategyName, strategy.description || null, JSON.stringify(strategy.steps), strategy.estimatedTime || 0, strategy.successRate || 0, strategy.difficulty || 1, JSON.stringify(strategy.requirements || []), JSON.stringify(strategy.tips || []), strategy.author || null, strategy.author || null, strategy.isVerified ? 1 : 0, JSON.stringify([]), now, now);
                createdStrategies.push(newStrategy);
            }
            // 提交事务
            this.db.run('COMMIT');
            console.log(`批量创建 ${createdStrategies.length} 个攻略成功`);
            return createdStrategies;
        }
        catch (error) {
            // 回滚事务
            this.db.run('ROLLBACK');
            console.error('批量创建攻略失败:', error);
            throw error;
        }
    }
    /**
     * 按来源删除攻略
     */
    async deleteStrategiesBySource(source) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const stmt = this.db.prepare('DELETE FROM strategies WHERE author = ?');
        const result = stmt.run(source);
        const deletedCount = result.changes;
        console.log(`删除来源为 ${source} 的 ${deletedCount} 个攻略`);
        return deletedCount;
    }
    /**
     * 删除单个攻略
     */
    async deleteStrategy(id) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const stmt = this.db.prepare('DELETE FROM strategies WHERE id = ?');
        const result = stmt.run(id);
        return result.changes > 0;
    }
    /**
     * 获取攻略统计信息
     */
    async getStrategyStats() {
        if (!this.db)
            throw new Error('数据库未初始化');
        // 获取总数和验证数量
        const totalStmt = this.db.prepare('SELECT COUNT(*) as total, SUM(CASE WHEN isVerified = 1 THEN 1 ELSE 0 END) as verified FROM strategies');
        const totalResult = totalStmt.get();
        // 按难度统计
        const difficultyStmt = this.db.prepare('SELECT difficulty, COUNT(*) as count FROM strategies GROUP BY difficulty');
        const difficultyResults = difficultyStmt.all();
        const byDifficulty = {};
        difficultyResults.forEach(row => {
            byDifficulty[row.difficulty] = row.count;
        });
        // 按作者统计
        const authorStmt = this.db.prepare('SELECT author, COUNT(*) as count FROM strategies WHERE author IS NOT NULL GROUP BY author ORDER BY count DESC LIMIT 10');
        const authorResults = authorStmt.all();
        const byAuthor = {};
        authorResults.forEach(row => {
            byAuthor[row.author] = row.count;
        });
        // 平均成功率和执行时间
        const avgStmt = this.db.prepare('SELECT AVG(successRate) as avgSuccessRate, AVG(estimatedTime) as avgEstimatedTime FROM strategies');
        const avgResult = avgStmt.get();
        return {
            total: totalResult.total || 0,
            verified: totalResult.verified || 0,
            byDifficulty,
            byAuthor,
            avgSuccessRate: avgResult.avgSuccessRate || 0,
            avgEstimatedTime: avgResult.avgEstimatedTime || 0
        };
    }
    /**
     * 获取指定来源的攻略
     */
    async getStrategiesBySource(source) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const stmt = this.db.prepare('SELECT * FROM strategies WHERE author = ? ORDER BY successRate DESC, createdAt DESC');
        const rows = stmt.all(source);
        return rows.map((row) => ({
            id: row.id,
            taskInfoId: row.taskInfoId,
            strategyName: row.name,
            description: row.description,
            steps: row.steps ? JSON.parse(row.steps) : [],
            estimatedTime: row.estimatedTime,
            successRate: row.successRate,
            difficulty: row.difficulty,
            requirements: row.requirements ? JSON.parse(row.requirements) : [],
            tips: row.notes ? [row.notes] : [],
            author: row.author,
            version: '1.0',
            isVerified: Boolean(row.isVerified),
            createdAt: new Date(row.createdAt),
            lastUpdated: new Date(row.updatedAt)
        }));
    }
    /**
     * 批量导入任务信息
     */
    async batchCreateTaskInfos(taskInfos) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const createdTaskInfos = [];
        const now = new Date().toISOString();
        // 开始事务
        this.db.run('BEGIN TRANSACTION');
        try {
            const stmt = this.db.prepare(`
        INSERT OR REPLACE INTO task_infos (
          id, name, type, category, description, requirements, rewards,
          difficulty, estimatedTime, prerequisites, location, npcName,
          isRepeatable, isDaily, isWeekly, version, tags, collectionStatus,
          lastUpdated, createdAt
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `);
            for (const taskInfo of taskInfos) {
                const id = uuidv4();
                const newTaskInfo = {
                    ...taskInfo,
                    id,
                    lastUpdated: new Date(now),
                    collectTime: new Date(now)
                };
                stmt.run(id, taskInfo.taskName, taskInfo.taskType, taskInfo.taskType, taskInfo.description || null, JSON.stringify(taskInfo.prerequisites || []), JSON.stringify(taskInfo.rewards || []), taskInfo.difficulty || 1, taskInfo.estimatedTime || 0, JSON.stringify([]), null, null, 1, 0, 0, null, JSON.stringify([]), 'completed', now, now);
                createdTaskInfos.push(newTaskInfo);
            }
            // 提交事务
            this.db.run('COMMIT');
            console.log(`批量创建 ${createdTaskInfos.length} 个任务信息成功`);
            return createdTaskInfos;
        }
        catch (error) {
            // 回滚事务
            this.db.run('ROLLBACK');
            console.error('批量创建任务信息失败:', error);
            throw error;
        }
    }
    /**
     * 攻略评估相关操作
     */
    async createStrategyEvaluation(evaluation) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const id = uuidv4();
        const timestamp = new Date().toISOString();
        const newEvaluation = {
            ...evaluation,
            id,
            executedAt: new Date(timestamp)
        };
        const stmt = this.db.prepare(`
      INSERT INTO strategy_evaluations (
        id, strategyId, executionTime, successRate, errorCount,
        notes, factors, timestamp
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `);
        stmt.run(id, evaluation.strategyId, evaluation.executionTime, evaluation.success ? 1 : 0, evaluation.completionRate, evaluation.efficiency, evaluation.feedback || null, evaluation.errorMessage || null, timestamp);
        return newEvaluation;
    }
    async getStrategyEvaluations(strategyId, options) {
        if (!this.db)
            throw new Error('数据库未初始化');
        let query = 'SELECT * FROM strategy_evaluations WHERE strategyId = ? ORDER BY timestamp DESC';
        const params = [strategyId];
        if (options?.limit) {
            query += ' LIMIT ?';
            params.push(options.limit.toString());
            if (options?.offset) {
                query += ' OFFSET ?';
                params.push(options.offset.toString());
            }
        }
        const stmt = this.db.prepare(query);
        const rows = stmt.all(...params);
        return rows.map((row) => ({
            id: row.id,
            strategyId: row.strategyId,
            accountId: row.accountId || '',
            executionTime: row.executionTime,
            success: Boolean(row.success),
            errorMessage: row.errorMessage,
            completionRate: row.completionRate,
            efficiency: row.efficiency,
            feedback: row.feedback,
            executedAt: new Date(row.timestamp)
        }));
    }
    /**
     * 自动化配置相关操作
     */
    async createAutomationConfig(config) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const id = Date.now(); // 使用数字ID
        const now = new Date().toISOString();
        const newConfig = {
            ...config,
            id,
            createdAt: new Date(now),
            updatedAt: new Date(now)
        };
        const stmt = this.db.prepare(`
      INSERT INTO automation_configs (
        id, accountId, taskTypes, automationLevel, enableSmartRetry,
        maxRetryAttempts, retryDelay, enableAdaptiveDelay, enableErrorRecovery,
        notificationSettings, customSettings, isActive, createdAt, updatedAt
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
        stmt.run(id, config.accountId, JSON.stringify(config.taskPriority), config.level, config.enableSmartScheduling ? 1 : 0, config.maxRetryCount, config.errorRecovery.enableErrorRecovery ? 1 : 0, config.errorRecovery.pauseOnError ? 1 : 0, JSON.stringify(config.notificationSettings), JSON.stringify({}), 1, now, now);
        return newConfig;
    }
    async getAutomationConfig(accountId) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const stmt = this.db.prepare('SELECT * FROM automation_configs WHERE accountId = ? AND isActive = 1 ORDER BY updatedAt DESC LIMIT 1');
        const row = stmt.get(accountId);
        if (!row)
            return null;
        return {
            id: row.id,
            accountId: row.accountId,
            level: row.automationLevel,
            taskType: TaskType.DAILY,
            autoCollectInfo: true,
            autoAnalyzeStrategy: true,
            autoSelectBestStrategy: true,
            autoExecuteTasks: false,
            minSuccessRate: 0.8,
            maxRetryCount: row.maxRetryAttempts,
            intervalMinutes: 30,
            enableSmartScheduling: Boolean(row.enableSmartRetry),
            prioritySettings: {
                main: 3,
                side: 2,
                daily: 1,
                event: 4
            },
            resourceManagement: {
                maxConcurrentTasks: 3,
                energyThreshold: 20,
                autoRestoreEnergy: true
            },
            taskPriority: JSON.parse(row.taskTypes),
            errorRecovery: {
                enableErrorRecovery: Boolean(row.enableErrorRecovery),
                pauseOnError: Boolean(row.pauseOnError),
                autoRetryOnTransientErrors: false,
                maxAutoRetryAttempts: 3,
                retryDelaySeconds: 30,
                escalationRules: [],
                errorLearning: {
                    enabled: false,
                    trackErrorPatterns: false,
                    suggestPrevention: false
                }
            },
            automationMode: {
                level: 'manual_confirmation',
                manualConfirmation: {
                    confirmBeforeEachTask: true,
                    confirmBeforeEachStep: false,
                    showDetailedPreview: true,
                    allowBatchConfirmation: false,
                    requireExplicitApproval: true
                }
            },
            smartPriorityAdjustment: {
                enabled: false,
                basedOnHistoricalData: false,
                basedOnCurrentLoad: false,
                basedOnResourceAvailability: false,
                adjustmentFrequency: 'daily',
                learningEnabled: false,
                adaptationRate: 0.1
            },
            notificationSettings: {
                onTaskComplete: true,
                onError: true,
                onOptimalStrategyFound: false,
                onConfirmationRequired: false,
                onAutomationModeChange: false,
                onPriorityAdjustment: false,
                channels: {
                    inApp: true,
                    email: false
                }
            },
            createdAt: new Date(row.createdAt),
            updatedAt: new Date(row.updatedAt)
        };
    }
    async updateAutomationConfig(id, updates) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const fields = [];
        const values = [];
        Object.entries(updates).forEach(([key, value]) => {
            if (key !== 'id' && key !== 'createdAt' && value !== undefined) {
                if (key === 'taskPriority') {
                    fields.push('taskTypes = ?');
                    values.push(JSON.stringify(value));
                }
                else if (key === 'level') {
                    fields.push('automationLevel = ?');
                    values.push(value);
                }
                else if (key === 'enableSmartScheduling') {
                    fields.push('enableSmartRetry = ?');
                    values.push(value ? 1 : 0);
                }
                else if (key === 'maxRetryCount') {
                    fields.push('maxRetryAttempts = ?');
                    values.push(value);
                }
                else if (key === 'pauseOnError') {
                    fields.push('enableAdaptiveDelay = ?');
                    values.push(value ? 1 : 0);
                }
                else if (key === 'notificationSettings') {
                    fields.push(`${key} = ?`);
                    values.push(JSON.stringify(value));
                }
                else if (key === 'enableErrorRecovery') {
                    fields.push(`${key} = ?`);
                    values.push(value ? 1 : 0);
                }
                else {
                    fields.push(`${key} = ?`);
                    values.push(value);
                }
            }
        });
        if (fields.length === 0)
            return false;
        fields.push('updatedAt = ?');
        values.push(new Date().toISOString());
        values.push(id);
        const stmt = this.db.prepare(`UPDATE automation_configs SET ${fields.join(', ')} WHERE id = ?`);
        const result = stmt.run(...values);
        return result.changes > 0;
    }
    /**
     * 用户反馈相关操作
     */
    async createStrategyFeedback(feedback) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const id = uuidv4();
        const now = new Date().toISOString();
        const stmt = this.db.prepare(`
      INSERT INTO strategy_feedbacks (
        id, strategyId, userId, rating, category, tags, comment, createdAt, updatedAt
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
        stmt.run(id, feedback.strategyId, feedback.userId, feedback.rating, feedback.category || null, feedback.tags ? JSON.stringify(feedback.tags) : null, feedback.comment || null, feedback.createdAt, now);
        return {
            id,
            ...feedback,
            likeCount: 0,
            officialReply: null,
            updatedAt: now
        };
    }
    async getStrategyFeedbacks(strategyId, options) {
        if (!this.db)
            throw new Error('数据库未初始化');
        let query = `
      SELECT sf.*, 
             (SELECT COUNT(*) FROM feedback_likes fl WHERE fl.feedbackId = sf.id) as likeCount
      FROM strategy_feedbacks sf 
      WHERE sf.strategyId = ?
    `;
        const params = [strategyId];
        if (options?.category) {
            query += ' AND sf.category = ?';
            params.push(options.category);
        }
        // 排序
        const sortBy = options?.sortBy || 'createdAt';
        if (sortBy === 'rating') {
            query += ' ORDER BY sf.rating DESC, sf.createdAt DESC';
        }
        else if (sortBy === 'likes') {
            query += ' ORDER BY likeCount DESC, sf.createdAt DESC';
        }
        else {
            query += ' ORDER BY sf.createdAt DESC';
        }
        if (options?.limit) {
            query += ' LIMIT ?';
            params.push(options.limit);
        }
        const stmt = this.db.prepare(query);
        const rows = stmt.all(...params);
        return rows.map(row => ({
            id: row.id,
            strategyId: row.strategyId,
            userId: row.userId,
            rating: row.rating,
            category: row.category,
            tags: row.tags ? JSON.parse(row.tags) : [],
            comment: row.comment,
            likeCount: row.likeCount || 0,
            officialReply: row.officialReply,
            createdAt: row.createdAt,
            updatedAt: row.updatedAt
        }));
    }
    async getFeedbackStatistics(strategyId) {
        if (!this.db)
            throw new Error('数据库未初始化');
        // 获取总反馈数和平均评分
        const totalStmt = this.db.prepare(`
      SELECT COUNT(*) as total, AVG(rating) as avgRating 
      FROM strategy_feedbacks 
      WHERE strategyId = ?
    `);
        const totalResult = totalStmt.get(strategyId);
        // 获取评分分布
        const ratingStmt = this.db.prepare(`
      SELECT rating, COUNT(*) as count 
      FROM strategy_feedbacks 
      WHERE strategyId = ? 
      GROUP BY rating
    `);
        const ratingRows = ratingStmt.all(strategyId);
        // 获取分类统计
        const categoryStmt = this.db.prepare(`
      SELECT category, COUNT(*) as count 
      FROM strategy_feedbacks 
      WHERE strategyId = ? AND category IS NOT NULL 
      GROUP BY category
    `);
        const categoryRows = categoryStmt.all(strategyId);
        const ratingDistribution = {};
        for (let i = 1; i <= 5; i++) {
            ratingDistribution[i] = 0;
        }
        ratingRows.forEach(row => {
            ratingDistribution[row.rating] = row.count;
        });
        const categoryStats = {};
        categoryRows.forEach(row => {
            categoryStats[row.category] = row.count;
        });
        return {
            totalFeedbacks: totalResult.total || 0,
            averageRating: totalResult.avgRating || 0,
            ratingDistribution,
            categoryStats
        };
    }
    async updateFeedbackLike(feedbackId, userId, isLike) {
        if (!this.db)
            throw new Error('数据库未初始化');
        if (isLike) {
            // 添加点赞
            const insertStmt = this.db.prepare(`
        INSERT OR IGNORE INTO feedback_likes (id, feedbackId, userId, createdAt) 
        VALUES (?, ?, ?, ?)
      `);
            insertStmt.run(uuidv4(), feedbackId, userId, new Date().toISOString());
        }
        else {
            // 取消点赞
            const deleteStmt = this.db.prepare(`
        DELETE FROM feedback_likes 
        WHERE feedbackId = ? AND userId = ?
      `);
            deleteStmt.run(feedbackId, userId);
        }
        // 获取更新后的点赞数
        const countStmt = this.db.prepare(`
      SELECT COUNT(*) as count 
      FROM feedback_likes 
      WHERE feedbackId = ?
    `);
        const result = countStmt.get(feedbackId);
        return { likeCount: result.count || 0 };
    }
    /**
     * 任务信息相关操作
     */
    async addTaskInfo(taskInfo) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const id = `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const now = new Date().toISOString();
        const stmt = this.db.prepare(`
      INSERT INTO task_infos (
        id, name, type, description, location, npcName, prerequisites, rewards, 
        estimatedTime, difficulty, isRepeatable, tags, createdAt, updatedAt
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
        stmt.run(id, taskInfo.name, taskInfo.type, taskInfo.description, taskInfo.location, taskInfo.npcName, JSON.stringify(taskInfo.prerequisites || []), JSON.stringify(taskInfo.rewards || []), taskInfo.estimatedTime, taskInfo.difficulty, taskInfo.isRepeatable ? 1 : 0, JSON.stringify(taskInfo.tags || []), now, now);
        return id;
    }
    async getTaskInfos(options) {
        if (!this.db)
            throw new Error('数据库未初始化');
        let query = 'SELECT * FROM task_infos WHERE 1=1';
        const params = [];
        if (options?.type) {
            query += ' AND type = ?';
            params.push(options.type);
        }
        if (options?.status) {
            query += ' AND collectionStatus = ?';
            params.push(options.status);
        }
        query += ' ORDER BY collectionTimestamp DESC';
        if (options?.limit) {
            query += ' LIMIT ?';
            params.push(options.limit);
            if (options?.offset) {
                query += ' OFFSET ?';
                params.push(options.offset);
            }
        }
        const stmt = this.db.prepare(query);
        const rows = stmt.all(...params);
        return rows.map(row => ({
            id: row.id,
            name: row.name,
            taskName: row.name,
            type: row.type,
            taskType: row.type,
            description: row.description,
            location: row.location || null,
            npcName: row.npcName || null,
            prerequisites: JSON.parse(row.prerequisites || '[]'),
            rewards: JSON.parse(row.rewards || '[]'),
            estimatedTime: row.estimatedTime,
            difficulty: row.difficulty,
            isRepeatable: Boolean(row.isRepeatable),
            tags: JSON.parse(row.tags || '[]'),
            collectTime: new Date(row.collectionTimestamp || row.createdAt),
            lastUpdated: new Date(row.updatedAt || row.createdAt)
        }));
    }
    async getTaskInfoById(id) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const stmt = this.db.prepare('SELECT * FROM task_infos WHERE id = ?');
        const row = stmt.get(id);
        if (!row)
            return null;
        return {
            id: row.id,
            name: row.name,
            taskName: row.name,
            type: row.type,
            taskType: row.type,
            description: row.description,
            location: row.location || null,
            npcName: row.npcName || null,
            prerequisites: JSON.parse(row.prerequisites || '[]'),
            rewards: JSON.parse(row.rewards || '[]'),
            estimatedTime: row.estimatedTime,
            difficulty: row.difficulty,
            isRepeatable: Boolean(row.isRepeatable),
            tags: JSON.parse(row.tags || '[]'),
            collectTime: new Date(row.collectionTimestamp || row.createdAt),
            lastUpdated: new Date(row.updatedAt || row.createdAt)
        };
    }
    async updateTaskInfoData(id, updates) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const fields = [];
        const values = [];
        Object.entries(updates).forEach(([key, value]) => {
            if (key !== 'id' && value !== undefined) {
                if (['prerequisites', 'rewards', 'tags'].includes(key)) {
                    fields.push(`${key} = ?`);
                    values.push(JSON.stringify(value));
                }
                else if (key === 'name') {
                    fields.push('name = ?');
                    values.push(value);
                }
                else if (key === 'type') {
                    fields.push('type = ?');
                    values.push(value);
                }
                else if (key === 'isRepeatable') {
                    fields.push(`${key} = ?`);
                    values.push(value ? 1 : 0);
                }
                else {
                    fields.push(`${key} = ?`);
                    values.push(value);
                }
            }
        });
        if (fields.length === 0)
            return false;
        fields.push('updatedAt = ?');
        values.push(new Date().toISOString());
        values.push(id);
        const stmt = this.db.prepare(`UPDATE task_infos SET ${fields.join(', ')} WHERE id = ?`);
        const result = stmt.run(...values);
        return result.changes > 0;
    }
    async deleteTaskInfo(id) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const stmt = this.db.prepare('DELETE FROM task_infos WHERE id = ?');
        const result = stmt.run(id);
        return result.changes > 0;
    }
    async searchTaskInfos(searchTerm, options) {
        if (!this.db)
            throw new Error('数据库未初始化');
        let query = `
      SELECT * FROM task_infos 
      WHERE (name LIKE ? OR description LIKE ?)
    `;
        const params = [`%${searchTerm}%`, `%${searchTerm}%`];
        if (options?.type) {
            query += ' AND type = ?';
            params.push(options.type);
        }
        query += ' ORDER BY difficulty DESC, createdAt DESC';
        if (options?.limit) {
            query += ' LIMIT ?';
            params.push(options.limit.toString());
        }
        const stmt = this.db.prepare(query);
        const rows = stmt.all(...params);
        return rows.map(row => ({
            id: row.id,
            name: row.name,
            taskName: row.name,
            type: row.type,
            taskType: row.type,
            description: row.description,
            location: row.location || null,
            npcName: row.npcName || null,
            prerequisites: JSON.parse(row.prerequisites || '[]'),
            rewards: JSON.parse(row.rewards || '[]'),
            estimatedTime: row.estimatedTime,
            difficulty: row.difficulty,
            isRepeatable: Boolean(row.isRepeatable),
            tags: JSON.parse(row.tags || '[]'),
            collectTime: new Date(row.collectionTimestamp || row.createdAt),
            lastUpdated: new Date(row.updatedAt || row.createdAt)
        }));
    }
    /**
     * 执行自定义SQL查询 - 返回多行结果
     */
    executeQuery(sql, params = []) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const stmt = this.db.prepare(sql);
        return stmt.all(...params);
    }
    /**
     * 执行自定义SQL查询 - 返回单行结果
     */
    executeQuerySingle(sql, params = []) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const stmt = this.db.prepare(sql);
        return stmt.get(...params);
    }
    /**
     * 调度配置相关方法
     */
    async addScheduleConfig(config) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const id = uuidv4();
        const stmt = this.db.prepare(`
      INSERT INTO schedule_configs (
        id, name, accountId, taskType, scheduleType, intervalMinutes, 
        cronExpression, startTime, endTime, enabled, maxExecutions, 
        config, createdAt, updatedAt
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
        const now = new Date().toISOString();
        stmt.run(id, config.name, config.accountId, config.taskType, config.scheduleType || 'interval', config.intervalMinutes, config.cronExpression, config.startTime, config.endTime, config.enabled ? 1 : 0, config.maxExecutions, JSON.stringify(config.config || {}), now, now);
        return { ...config, id, createdAt: new Date(now), updatedAt: new Date(now) };
    }
    async updateScheduleConfig(id, updates) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const fields = [];
        const values = [];
        Object.entries(updates).forEach(([key, value]) => {
            if (key !== 'id' && value !== undefined) {
                if (key === 'config') {
                    fields.push(`${key} = ?`);
                    values.push(JSON.stringify(value));
                }
                else if (key === 'enabled') {
                    fields.push(`${key} = ?`);
                    values.push(value ? 1 : 0);
                }
                else {
                    fields.push(`${key} = ?`);
                    values.push(value);
                }
            }
        });
        if (fields.length === 0)
            return null;
        fields.push('updatedAt = ?');
        values.push(new Date().toISOString());
        values.push(id);
        const stmt = this.db.prepare(`UPDATE schedule_configs SET ${fields.join(', ')} WHERE id = ?`);
        const result = stmt.run(...values);
        if (result.changes > 0) {
            const getStmt = this.db.prepare('SELECT * FROM schedule_configs WHERE id = ?');
            const row = getStmt.get(id);
            return {
                ...row,
                enabled: Boolean(row.enabled),
                config: JSON.parse(row.config || '{}'),
                createdAt: new Date(row.createdAt),
                updatedAt: new Date(row.updatedAt)
            };
        }
        return null;
    }
    async deleteScheduleConfig(id) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const stmt = this.db.prepare('DELETE FROM schedule_configs WHERE id = ?');
        const result = stmt.run(id);
        return result.changes > 0;
    }
    async toggleScheduleConfig(id, enabled) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const stmt = this.db.prepare('UPDATE schedule_configs SET enabled = ?, updatedAt = ? WHERE id = ?');
        const result = stmt.run(enabled ? 1 : 0, new Date().toISOString(), id);
        if (result.changes > 0) {
            const getStmt = this.db.prepare('SELECT * FROM schedule_configs WHERE id = ?');
            const row = getStmt.get(id);
            return {
                ...row,
                enabled: Boolean(row.enabled),
                config: JSON.parse(row.config || '{}'),
                createdAt: new Date(row.createdAt),
                updatedAt: new Date(row.updatedAt)
            };
        }
        return null;
    }
    /**
     * 系统配置相关方法
     */
    async getSystemConfig() {
        if (!this.db)
            throw new Error('数据库未初始化');
        const stmt = this.db.prepare('SELECT * FROM system_configs');
        const rows = stmt.all();
        const config = {};
        rows.forEach(row => {
            let value = row.configValue;
            if (row.configType === 'number') {
                value = Number(value);
            }
            else if (row.configType === 'boolean') {
                value = value === 'true';
            }
            else if (row.configType === 'json') {
                value = JSON.parse(value);
            }
            config[row.configKey] = value;
        });
        return config;
    }
    async updateSystemConfig(updates) {
        if (!this.db)
            throw new Error('数据库未初始化');
        const now = new Date().toISOString();
        for (const [key, value] of Object.entries(updates)) {
            if (key === 'updatedAt')
                continue;
            let configType = 'string';
            let configValue = String(value);
            if (typeof value === 'number') {
                configType = 'number';
            }
            else if (typeof value === 'boolean') {
                configType = 'boolean';
            }
            else if (typeof value === 'object') {
                configType = 'json';
                configValue = JSON.stringify(value);
            }
            const stmt = this.db.prepare(`
        INSERT OR REPLACE INTO system_configs 
        (id, configKey, configValue, configType, updatedAt) 
        VALUES (?, ?, ?, ?, ?)
      `);
            stmt.run(uuidv4(), key, configValue, configType, now);
        }
        return this.getSystemConfig();
    }
    async getScheduleConfigs(filters) {
        if (!this.db)
            throw new Error('数据库未初始化');
        let query = 'SELECT * FROM schedule_configs';
        const params = [];
        const conditions = [];
        if (filters) {
            if (filters.accountId) {
                conditions.push('accountId = ?');
                params.push(filters.accountId);
            }
            if (filters.taskType) {
                conditions.push('taskType = ?');
                params.push(filters.taskType);
            }
            if (filters.enabled !== undefined) {
                conditions.push('enabled = ?');
                params.push(filters.enabled ? 1 : 0);
            }
        }
        if (conditions.length > 0) {
            query += ' WHERE ' + conditions.join(' AND ');
        }
        query += ' ORDER BY createdAt DESC';
        const stmt = this.db.prepare(query);
        const rows = stmt.all(...params);
        return rows.map(row => ({
            ...row,
            enabled: Boolean(row.enabled),
            config: JSON.parse(row.config || '{}'),
            createdAt: new Date(row.createdAt),
            updatedAt: new Date(row.updatedAt)
        }));
    }
    async getStrategySuccessRate(strategyId, timeRange) {
        if (!this.db)
            throw new Error('数据库未初始化');
        let query = `
      SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful
      FROM strategy_evaluations 
      WHERE strategyId = ?
    `;
        const params = [strategyId];
        if (timeRange) {
            const now = new Date();
            let startDate;
            switch (timeRange) {
                case '24h':
                    startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000);
                    break;
                case '7d':
                    startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                    break;
                case '30d':
                    startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                    break;
                default:
                    startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000);
            }
            query += ' AND executedAt >= ?';
            params.push(startDate.toISOString());
        }
        const stmt = this.db.prepare(query);
        const result = stmt.get(...params);
        if (!result || result.total === 0) {
            return 0;
        }
        return (result.successful / result.total) * 100;
    }
    /**
     * 关闭数据库连接
     */
    async close() {
        if (this.db) {
            this.db.close();
            this.db = null;
            console.log('数据库连接已关闭');
        }
    }
}
export default DatabaseService;
