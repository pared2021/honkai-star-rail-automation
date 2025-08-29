import { DatabaseService } from './DatabaseService.js';
export class ApiService {
    constructor() {
        this.dbService = new DatabaseService();
    }
    async initialize() {
        try {
            await this.dbService.initialize();
            console.log('API服务初始化完成');
        }
        catch (error) {
            console.error('API服务初始化失败:', error);
            throw error;
        }
    }
    async createAccount(accountData) {
        try {
            const accountId = await this.dbService.createAccount(accountData);
            return {
                success: true,
                data: accountId.id,
                message: '账号创建成功'
            };
        }
        catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error)
            };
        }
    }
    async getAccounts() {
        try {
            const accounts = await this.dbService.getAccounts();
            return {
                success: true,
                data: accounts
            };
        }
        catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error)
            };
        }
    }
    async updateAccount(id, updates) {
        try {
            const result = await this.dbService.updateAccount(id, updates);
            return {
                success: true,
                data: result,
                message: '账号更新成功'
            };
        }
        catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error)
            };
        }
    }
    async deleteAccount(id) {
        try {
            const result = await this.dbService.deleteAccount(id);
            return {
                success: true,
                data: result,
                message: '账号删除成功'
            };
        }
        catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error)
            };
        }
    }
    async startTask(request) {
        try {
            const gameStatus = { isRunning: false, windowTitle: '', processId: 0 };
            if (!gameStatus.isRunning) {
                return {
                    success: false,
                    error: '游戏未运行，无法启动任务'
                };
            }
            const taskId = Math.random().toString(36).substr(2, 9);
            return {
                success: true,
                data: taskId,
                message: '任务启动成功'
            };
        }
        catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error)
            };
        }
    }
    async controlTask(request) {
        try {
            let result = false;
            switch (request.action) {
                case 'stop':
                    result = true;
                    break;
                case 'pause':
                case 'resume':
                    result = true;
                    break;
            }
            return {
                success: true,
                data: result,
                message: `任务${request.action}操作成功`
            };
        }
        catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error)
            };
        }
    }
    async getRunningTasks() {
        try {
            const tasks = [];
            return {
                success: true,
                data: tasks
            };
        }
        catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error)
            };
        }
    }
    async getTaskHistory(accountId) {
        try {
            const tasks = await this.dbService.getTasks(accountId);
            return {
                success: true,
                data: tasks
            };
        }
        catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error)
            };
        }
    }
    async createTaskConfig(config) {
        try {
            const configId = await this.dbService.createTaskConfig(config);
            return {
                success: true,
                data: configId.id,
                message: '任务配置创建成功'
            };
        }
        catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error)
            };
        }
    }
    async getTaskConfigs(taskType) {
        try {
            const configs = await this.dbService.getTaskConfigs(taskType);
            return {
                success: true,
                data: configs
            };
        }
        catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error)
            };
        }
    }
    async getGameStatus() {
        try {
            const status = { isRunning: false, windowTitle: '', processId: 0 };
            return {
                success: true,
                data: status
            };
        }
        catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error)
            };
        }
    }
    async getAccountStats(accountId, statType) {
        try {
            const stats = await this.dbService.getAccountStats(accountId, new Date(statType));
            return {
                success: true,
                data: stats
            };
        }
        catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error)
            };
        }
    }
    async getSystemStats() {
        const accounts = await this.dbService.getAccounts();
        const tasks = await this.dbService.getTasks();
        return {
            totalAccounts: accounts.length,
            activeTasks: tasks.filter(t => t.status === 'running').length,
            completedTasks: tasks.filter(t => t.status === 'completed').length,
            failedTasks: tasks.filter(t => t.status === 'failed').length,
            systemUptime: process.uptime(),
            memoryUsage: process.memoryUsage(),
            lastUpdated: new Date().toISOString()
        };
    }
    async shutdown() {
        try {
            await this.dbService.close();
            console.log('API服务已关闭');
        }
        catch (error) {
            console.error('API服务关闭失败:', error);
        }
    }
}
export default ApiService;
