import { DatabaseService } from './DatabaseService.js';
import { TaskInfoCollector } from './TaskInfoCollector.js';
import { StrategyAnalyzer } from './StrategyAnalyzer.js';
export class AutomationManager {
    constructor(dbService, accountId = 'default') {
        this.isRunning = false;
        this.scheduledTasks = new Map();
        this.db = dbService || new DatabaseService();
        this.accountId = accountId;
        this.taskInfoCollector = new TaskInfoCollector(this.db);
        this.strategyAnalyzer = new StrategyAnalyzer(this.db);
        this.status = {
            isRunning: false,
            currentTasks: [],
            totalTasksCompleted: 0,
            successRate: 0,
            errors: []
        };
    }
    async startAutomation(config) {
        if (this.isRunning) {
            throw new Error('自动化管理已在运行中');
        }
        try {
            const automationConfig = config || await this.getDefaultConfig();
            this.isRunning = true;
            this.status.isRunning = true;
            this.status.errors = [];
            console.log('启动自动化管理系统...');
            if (automationConfig.autoCollectInfo) {
                await this.scheduleTaskInfoCollection(automationConfig);
            }
            if (automationConfig.autoAnalyzeStrategy) {
                await this.scheduleStrategyAnalysis(automationConfig);
            }
            if (automationConfig.enableSmartScheduling) {
                await this.scheduleSmartTaskExecution(automationConfig);
            }
            this.status.lastExecutionTime = new Date();
            this.status.nextScheduledTime = new Date(Date.now() + automationConfig.intervalMinutes * 60 * 1000);
        }
        catch (error) {
            this.isRunning = false;
            this.status.isRunning = false;
            this.status.errors.push(`启动自动化失败: ${error.message}`);
            throw error;
        }
    }
    async stopAutomation() {
        if (!this.isRunning) {
            return;
        }
        console.log('停止自动化管理系统...');
        for (const [taskId, timeout] of this.scheduledTasks) {
            clearTimeout(timeout);
        }
        this.scheduledTasks.clear();
        this.isRunning = false;
        this.status.isRunning = false;
        this.status.currentTasks = [];
    }
    async scheduleTaskInfoCollection(config) {
        const collectInfo = async () => {
            try {
                this.status.currentTasks.push('任务信息收集');
                await this.taskInfoCollector.startCollection();
                let attempts = 0;
                const maxAttempts = 30;
                while (attempts < maxAttempts) {
                    const status = await this.taskInfoCollector.getCollectionStatus();
                    if (!status.isCollecting) {
                        break;
                    }
                    await new Promise(resolve => setTimeout(resolve, 10000));
                    attempts++;
                }
                this.status.currentTasks = this.status.currentTasks.filter(task => task !== '任务信息收集');
                this.status.totalTasksCompleted++;
            }
            catch (error) {
                this.status.errors.push(`任务信息收集失败: ${error.message}`);
                this.status.currentTasks = this.status.currentTasks.filter(task => task !== '任务信息收集');
            }
        };
        await collectInfo();
        const timeout = setInterval(collectInfo, config.intervalMinutes * 60 * 1000);
        this.scheduledTasks.set('taskInfoCollection', timeout);
    }
    async scheduleStrategyAnalysis(config) {
        const analyzeStrategies = async () => {
            try {
                this.status.currentTasks.push('攻略分析');
                const taskInfos = await this.db.getTaskInfos();
                for (const taskInfo of taskInfos) {
                    const existingStrategies = await this.db.getStrategies({ taskInfoId: taskInfo.id });
                    if (existingStrategies.length < 3 || this.shouldReanalyze(existingStrategies)) {
                        await this.strategyAnalyzer.startAnalysis(taskInfo.id);
                        let attempts = 0;
                        const maxAttempts = 20;
                        while (attempts < maxAttempts) {
                            const status = await this.strategyAnalyzer.getAnalysisStatus();
                            if (!status.isAnalyzing) {
                                break;
                            }
                            await new Promise(resolve => setTimeout(resolve, 5000));
                            attempts++;
                        }
                    }
                }
                this.status.currentTasks = this.status.currentTasks.filter(task => task !== '攻略分析');
                this.status.totalTasksCompleted++;
            }
            catch (error) {
                this.status.errors.push(`攻略分析失败: ${error.message}`);
                this.status.currentTasks = this.status.currentTasks.filter(task => task !== '攻略分析');
            }
        };
        const timeout = setTimeout(async () => {
            await analyzeStrategies();
            const interval = setInterval(analyzeStrategies, config.intervalMinutes * 60 * 1000 * 2);
            this.scheduledTasks.set('strategyAnalysisInterval', interval);
        }, 60000);
        this.scheduledTasks.set('strategyAnalysis', timeout);
    }
    async scheduleSmartTaskExecution(config) {
        const executeSmartTasks = async () => {
            try {
                this.status.currentTasks.push('智能任务执行');
                const taskInfos = await this.db.getTaskInfos();
                const prioritizedTasks = this.prioritizeTasks(taskInfos, config.prioritySettings);
                for (const taskInfo of prioritizedTasks) {
                    if (this.status.currentTasks.length >= config.resourceManagement.maxConcurrentTasks) {
                        break;
                    }
                    const strategies = await this.db.getStrategies(taskInfo.id);
                    const bestStrategy = strategies.length > 0 ? strategies[0] : null;
                    if (bestStrategy && bestStrategy.successRate >= config.minSuccessRate) {
                        await this.executeTaskWithStrategy(taskInfo, bestStrategy, config);
                    }
                }
                this.status.currentTasks = this.status.currentTasks.filter(task => task !== '智能任务执行');
                this.status.totalTasksCompleted++;
            }
            catch (error) {
                this.status.errors.push(`智能任务执行失败: ${error.message}`);
                this.status.currentTasks = this.status.currentTasks.filter(task => task !== '智能任务执行');
            }
        };
        const timeout = setTimeout(async () => {
            await executeSmartTasks();
            const interval = setInterval(executeSmartTasks, config.intervalMinutes * 60 * 1000);
            this.scheduledTasks.set('smartTaskExecutionInterval', interval);
        }, 120000);
        this.scheduledTasks.set('smartTaskExecution', timeout);
    }
    shouldReanalyze(strategies) {
        if (strategies.length === 0)
            return true;
        const latestStrategy = strategies.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())[0];
        const daysSinceLastAnalysis = (Date.now() - new Date(latestStrategy.createdAt).getTime()) / (1000 * 60 * 60 * 24);
        return daysSinceLastAnalysis > 7 || latestStrategy.successRate < 0.8;
    }
    prioritizeTasks(taskInfos, prioritySettings) {
        return taskInfos.sort((a, b) => {
            const priorityA = prioritySettings[a.type] || 0;
            const priorityB = prioritySettings[b.type] || 0;
            if (priorityA !== priorityB) {
                return priorityB - priorityA;
            }
            return a.difficulty - b.difficulty;
        });
    }
    async executeTaskWithStrategy(taskInfo, strategy, config) {
        console.log(`执行任务: ${taskInfo.taskName}，使用攻略: ${strategy.name}`);
        await new Promise(resolve => setTimeout(resolve, strategy.estimatedTime * 1000));
        const success = Math.random() < strategy.successRate;
        if (success) {
            console.log(`任务 ${taskInfo.taskName} 执行成功`);
            if (config.notificationSettings.onTaskComplete) {
                this.sendNotification(`任务 ${taskInfo.taskName} 执行成功`);
            }
        }
        else {
            console.log(`任务 ${taskInfo.taskName} 执行失败`);
            this.status.errors.push(`任务 ${taskInfo.taskName} 执行失败`);
            if (config.notificationSettings.onError) {
                this.sendNotification(`任务 ${taskInfo.taskName} 执行失败`);
            }
        }
        this.updateSuccessRate(success);
    }
    sendNotification(message) {
        console.log(`[通知] ${message}`);
    }
    updateSuccessRate(success) {
        const totalTasks = this.status.totalTasksCompleted;
        const currentSuccessRate = this.status.successRate;
        if (success) {
            this.status.successRate = (currentSuccessRate * totalTasks + 1) / (totalTasks + 1);
        }
        else {
            this.status.successRate = (currentSuccessRate * totalTasks) / (totalTasks + 1);
        }
    }
    async getDefaultConfig() {
        return {
            id: Date.now(),
            accountId: this.accountId,
            level: 'medium',
            taskType: 'daily',
            autoCollectInfo: true,
            autoAnalyzeStrategy: true,
            autoSelectBestStrategy: true,
            autoExecuteTasks: false,
            minSuccessRate: 0.8,
            maxRetryCount: 3,
            intervalMinutes: 30,
            enableSmartScheduling: true,
            prioritySettings: {
                main: 3,
                side: 1,
                daily: 2,
                event: 4
            },
            resourceManagement: {
                maxConcurrentTasks: 3,
                energyThreshold: 20,
                autoRestoreEnergy: true
            },
            taskPriority: {
                main: 'high',
                side: 'low',
                daily: 'medium',
                event: 'high'
            },
            enableErrorRecovery: true,
            pauseOnError: false,
            notificationSettings: {
                onTaskComplete: true,
                onError: true,
                onOptimalStrategyFound: false
            },
            createdAt: new Date(),
            updatedAt: new Date()
        };
    }
    getAutomationStatus() {
        return { ...this.status };
    }
    async updateAutomationConfig(config) {
        const currentConfig = await this.db.getAutomationConfig(this.accountId) || await this.getDefaultConfig();
        const updatedConfig = { ...currentConfig, ...config };
        await this.db.updateAutomationConfig(this.accountId, config);
        if (this.isRunning) {
            await this.stopAutomation();
            await this.startAutomation(updatedConfig);
        }
    }
    async getAutomationConfig() {
        return await this.db.getAutomationConfig(this.accountId) || await this.getDefaultConfig();
    }
    async triggerTaskInfoCollection() {
        if (this.status.currentTasks.includes('任务信息收集')) {
            throw new Error('任务信息收集正在进行中');
        }
        await this.taskInfoCollector.startCollection();
    }
    async triggerStrategyAnalysis(taskId) {
        if (this.status.currentTasks.includes('攻略分析')) {
            throw new Error('攻略分析正在进行中');
        }
        if (taskId) {
            await this.strategyAnalyzer.startAnalysis(taskId.toString());
        }
        else {
            const taskInfos = await this.db.getTaskInfos();
            for (const taskInfo of taskInfos) {
                await this.strategyAnalyzer.startAnalysis(taskInfo.id);
            }
        }
    }
    clearErrors() {
        this.status.errors = [];
    }
    getStatistics() {
        return {
            totalTasksCompleted: this.status.totalTasksCompleted,
            successRate: this.status.successRate,
            averageExecutionTime: 0,
            errorCount: this.status.errors.length
        };
    }
}
