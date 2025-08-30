import { DatabaseService } from './DatabaseService.js';
import { TaskInfoCollector } from './TaskInfoCollector.js';
import { StrategyAnalyzer } from './StrategyAnalyzer.js';
import { TaskType } from '../types/index.js';
export class AutomationManager {
    constructor(dbService, accountId = 'default') {
        Object.defineProperty(this, "db", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "taskInfoCollector", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "strategyAnalyzer", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "accountId", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "isRunning", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: false
        });
        Object.defineProperty(this, "scheduledTasks", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: new Map()
        });
        Object.defineProperty(this, "status", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        // 新增：确认系统相关
        Object.defineProperty(this, "pendingConfirmations", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: new Map()
        });
        Object.defineProperty(this, "confirmationCallbacks", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: new Map()
        });
        // 新增：智能优先级调整
        Object.defineProperty(this, "priorityRules", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: []
        });
        Object.defineProperty(this, "priorityHistory", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: []
        });
        Object.defineProperty(this, "currentPriorities", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: new Map()
        });
        // 新增：自动化模式状态
        Object.defineProperty(this, "currentAutomationLevel", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: 'manual_confirmation'
        });
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
        // 初始化确认系统
        this.pendingConfirmations = new Map();
        this.confirmationCallbacks = new Map();
        // 初始化智能优先级调整
        this.priorityRules = [];
        this.priorityHistory = [];
        this.currentPriorities = new Map();
        // 初始化自动化级别
        this.currentAutomationLevel = 'manual_confirmation';
    }
    // 启动自动化管理
    async startAutomation(config) {
        if (this.isRunning) {
            throw new Error('自动化管理已在运行中');
        }
        try {
            // 获取或使用默认配置
            const automationConfig = config || await this.getDefaultConfig();
            this.isRunning = true;
            this.status.isRunning = true;
            this.status.errors = [];
            console.log('启动自动化管理系统...');
            // 启动任务信息收集
            if (automationConfig.autoCollectInfo) {
                await this.scheduleTaskInfoCollection(automationConfig);
            }
            // 启动攻略分析
            if (automationConfig.autoAnalyzeStrategy) {
                await this.scheduleStrategyAnalysis(automationConfig);
            }
            // 启动智能任务调度
            if (automationConfig.enableSmartScheduling) {
                await this.scheduleSmartTaskExecution(automationConfig);
            }
            this.status.lastExecutionTime = new Date();
            this.status.nextScheduledTime = new Date(Date.now() + automationConfig.intervalMinutes * 60 * 1000);
        }
        catch (error) {
            this.isRunning = false;
            this.status.isRunning = false;
            this.status.errors.push({
                id: Date.now().toString(),
                error: `启动自动化失败: ${error.message}`,
                timestamp: new Date(),
                resolved: false,
                recoveryAttempts: 0
            });
            throw error;
        }
    }
    // 停止自动化管理
    async stopAutomation() {
        if (!this.isRunning) {
            return;
        }
        console.log('停止自动化管理系统...');
        // 清除所有定时任务
        for (const [taskId, timeout] of this.scheduledTasks) {
            clearTimeout(timeout);
        }
        this.scheduledTasks.clear();
        this.isRunning = false;
        this.status.isRunning = false;
        this.status.currentTasks = [];
    }
    // 调度任务信息收集
    async scheduleTaskInfoCollection(config) {
        const collectInfo = async () => {
            try {
                this.status.currentTasks.push('任务信息收集');
                await this.taskInfoCollector.startCollection();
                // 等待收集完成
                let attempts = 0;
                const maxAttempts = 30; // 最多等待5分钟
                while (attempts < maxAttempts) {
                    const status = await this.taskInfoCollector.getCollectionStatus();
                    if (!status.isCollecting) {
                        break;
                    }
                    await new Promise(resolve => setTimeout(resolve, 10000)); // 等待10秒
                    attempts++;
                }
                this.status.currentTasks = this.status.currentTasks.filter(task => task !== '任务信息收集');
                this.status.totalTasksCompleted++;
            }
            catch (error) {
                this.status.errors.push({
                    id: Date.now().toString(),
                    error: `任务信息收集失败: ${error.message}`,
                    timestamp: new Date(),
                    resolved: false,
                    recoveryAttempts: 0
                });
                this.status.currentTasks = this.status.currentTasks.filter(task => task !== '任务信息收集');
            }
        };
        // 立即执行一次
        await collectInfo();
        // 设置定时执行
        const timeout = setInterval(collectInfo, config.intervalMinutes * 60 * 1000);
        this.scheduledTasks.set('taskInfoCollection', timeout);
    }
    // 调度攻略分析
    async scheduleStrategyAnalysis(config) {
        const analyzeStrategies = async () => {
            try {
                this.status.currentTasks.push('攻略分析');
                // 获取需要分析的任务
                const taskInfos = await this.db.getTaskInfos();
                for (const taskInfo of taskInfos) {
                    // 检查是否需要重新分析攻略
                    const existingStrategies = await this.db.getStrategies({ taskInfoId: taskInfo.id });
                    if (existingStrategies.length < 3 || this.shouldReanalyze(existingStrategies)) {
                        await this.strategyAnalyzer.startAnalysis(taskInfo.id);
                        // 等待分析完成
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
                this.status.errors.push({
                    id: Date.now().toString(),
                    error: `攻略分析失败: ${error.message}`,
                    timestamp: new Date(),
                    resolved: false,
                    recoveryAttempts: 0
                });
                this.status.currentTasks = this.status.currentTasks.filter(task => task !== '攻略分析');
            }
        };
        // 延迟执行，等待任务信息收集完成
        const timeout = setTimeout(async () => {
            await analyzeStrategies();
            // 设置定时执行
            const interval = setInterval(analyzeStrategies, config.intervalMinutes * 60 * 1000 * 2); // 攻略分析频率较低
            this.scheduledTasks.set('strategyAnalysisInterval', interval);
        }, 60000); // 1分钟后开始
        this.scheduledTasks.set('strategyAnalysis', timeout);
    }
    // 智能任务调度执行
    async scheduleSmartTaskExecution(config) {
        const executeSmartTasks = async () => {
            try {
                this.status.currentTasks.push('智能任务执行');
                // 获取最优攻略
                const taskInfos = await this.db.getTaskInfos();
                const prioritizedTasks = this.prioritizeTasks(taskInfos, config.prioritySettings);
                for (const taskInfo of prioritizedTasks) {
                    // 检查资源限制
                    if (this.status.currentTasks.length >= config.resourceManagement.maxConcurrentTasks) {
                        break;
                    }
                    // 获取最优攻略
                    const strategies = await this.db.getStrategies(taskInfo.id);
                    const bestStrategy = strategies.length > 0 ? strategies[0] : null;
                    if (bestStrategy && bestStrategy.successRate >= config.minSuccessRate) {
                        // 模拟执行任务（实际项目中这里会调用游戏自动化接口）
                        await this.executeTaskWithStrategy(taskInfo, bestStrategy, config);
                    }
                }
                this.status.currentTasks = this.status.currentTasks.filter(task => task !== '智能任务执行');
                this.status.totalTasksCompleted++;
            }
            catch (error) {
                this.status.errors.push({
                    id: Date.now().toString(),
                    error: `智能任务执行失败: ${error.message}`,
                    timestamp: new Date(),
                    resolved: false,
                    recoveryAttempts: 0
                });
                this.status.currentTasks = this.status.currentTasks.filter(task => task !== '智能任务执行');
            }
        };
        // 延迟执行，等待攻略分析完成
        const timeout = setTimeout(async () => {
            await executeSmartTasks();
            // 设置定时执行
            const interval = setInterval(executeSmartTasks, config.intervalMinutes * 60 * 1000);
            this.scheduledTasks.set('smartTaskExecutionInterval', interval);
        }, 120000); // 2分钟后开始
        this.scheduledTasks.set('smartTaskExecution', timeout);
    }
    // 判断是否需要重新分析攻略
    shouldReanalyze(strategies) {
        if (strategies.length === 0)
            return true;
        // 检查最新攻略的时间
        const latestStrategy = strategies.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())[0];
        const daysSinceLastAnalysis = (Date.now() - new Date(latestStrategy.createdAt).getTime()) / (1000 * 60 * 60 * 24);
        // 如果超过7天或者成功率低于80%，重新分析
        return daysSinceLastAnalysis > 7 || latestStrategy.successRate < 0.8;
    }
    // 任务优先级排序
    prioritizeTasks(taskInfos, prioritySettings) {
        return taskInfos.sort((a, b) => {
            const priorityA = prioritySettings[a.type] || 0;
            const priorityB = prioritySettings[b.type] || 0;
            if (priorityA !== priorityB) {
                return priorityB - priorityA; // 高优先级在前
            }
            // 相同优先级按难度排序（简单的在前）
            return a.difficulty - b.difficulty;
        });
    }
    // 执行任务（模拟）
    async executeTaskWithStrategy(taskInfo, strategy, config) {
        console.log(`执行任务: ${taskInfo.taskName}，使用攻略: ${strategy.name}`);
        // 模拟任务执行时间
        await new Promise(resolve => setTimeout(resolve, strategy.estimatedTime * 1000));
        // 模拟成功率
        const success = Math.random() < strategy.successRate;
        if (success) {
            console.log(`任务 ${taskInfo.taskName} 执行成功`);
            // 发送通知
            if (config.notificationSettings.onTaskComplete) {
                this.sendNotification(`任务 ${taskInfo.taskName} 执行成功`);
            }
        }
        else {
            console.log(`任务 ${taskInfo.taskName} 执行失败`);
            this.status.errors.push({
                id: Date.now().toString(),
                taskId: taskInfo.id,
                error: `任务 ${taskInfo.taskName} 执行失败`,
                timestamp: new Date(),
                resolved: false,
                recoveryAttempts: 0
            });
            // 发送错误通知
            if (config.notificationSettings.onError) {
                this.sendNotification(`任务 ${taskInfo.taskName} 执行失败`);
            }
        }
        // 更新成功率统计
        this.updateSuccessRate(success);
    }
    // 发送通知（模拟）
    sendNotification(message) {
        console.log(`[通知] ${message}`);
        // 实际项目中可以集成邮件、微信、钉钉等通知方式
    }
    // 更新成功率统计
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
    // 获取默认配置
    async getDefaultConfig() {
        // 返回默认配置
        return {
            id: Date.now(),
            accountId: this.accountId,
            level: 'medium',
            taskType: TaskType.DAILY,
            autoCollectInfo: true,
            autoAnalyzeStrategy: true,
            autoSelectBestStrategy: true,
            autoExecuteTasks: false,
            minSuccessRate: 0.8,
            maxRetryCount: 3,
            intervalMinutes: 30,
            enableSmartScheduling: true,
            // 新增：自动化模式配置
            automationMode: {
                level: 'manual_confirmation',
                manualConfirmation: {
                    confirmBeforeEachTask: true,
                    confirmBeforeEachStep: false,
                    showDetailedPreview: true,
                    allowBatchConfirmation: true,
                    requireExplicitApproval: true
                }
            },
            // 新增：智能优先级调整
            smartPriorityAdjustment: {
                enabled: false,
                basedOnHistoricalData: true,
                basedOnCurrentLoad: true,
                basedOnResourceAvailability: true,
                adjustmentFrequency: 'hourly',
                learningEnabled: false,
                adaptationRate: 0.1
            },
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
            // 增强的错误恢复配置
            errorRecovery: {
                enableErrorRecovery: true,
                pauseOnError: false,
                autoRetryOnTransientErrors: true,
                maxAutoRetryAttempts: 3,
                retryDelaySeconds: 30,
                escalationRules: [
                    {
                        errorType: 'network_timeout',
                        action: 'retry',
                        maxAttempts: 3,
                        fallbackStrategy: 'pause'
                    },
                    {
                        errorType: 'resource_unavailable',
                        action: 'pause',
                        maxAttempts: 1
                    }
                ],
                errorLearning: {
                    enabled: true,
                    trackErrorPatterns: true,
                    suggestPrevention: true
                }
            },
            // 增强的通知设置
            notificationSettings: {
                onTaskComplete: true,
                onError: true,
                onOptimalStrategyFound: false,
                onConfirmationRequired: true,
                onAutomationModeChange: true,
                onPriorityAdjustment: false,
                channels: {
                    inApp: true,
                    email: false
                }
            },
            createdAt: new Date(),
            updatedAt: new Date()
        };
    }
    // 获取自动化状态
    getAutomationStatus() {
        return { ...this.status };
    }
    // 更新自动化配置
    async updateAutomationConfig(config) {
        const currentConfig = await this.db.getAutomationConfig(this.accountId) || await this.getDefaultConfig();
        const updatedConfig = { ...currentConfig, ...config };
        await this.db.updateAutomationConfig(this.accountId, config);
        // 如果正在运行，重启自动化以应用新配置
        if (this.isRunning) {
            await this.stopAutomation();
            await this.startAutomation(updatedConfig);
        }
    }
    // 获取自动化配置
    async getAutomationConfig() {
        return await this.db.getAutomationConfig(this.accountId) || await this.getDefaultConfig();
    }
    // 手动触发任务信息收集
    async triggerTaskInfoCollection() {
        if (this.status.currentTasks.includes('任务信息收集')) {
            throw new Error('任务信息收集正在进行中');
        }
        await this.taskInfoCollector.startCollection();
    }
    // 手动触发攻略分析
    async triggerStrategyAnalysis(taskId) {
        if (this.status.currentTasks.includes('攻略分析')) {
            throw new Error('攻略分析正在进行中');
        }
        if (taskId) {
            await this.strategyAnalyzer.startAnalysis(taskId.toString());
        }
        else {
            // 分析所有任务
            const taskInfos = await this.db.getTaskInfos();
            for (const taskInfo of taskInfos) {
                await this.strategyAnalyzer.startAnalysis(taskInfo.id);
            }
        }
    }
    // 清理错误日志
    clearErrors() {
        this.status.errors = [];
    }
    // 获取统计信息
    getStatistics() {
        return {
            totalTasksCompleted: this.status.totalTasksCompleted,
            successRate: this.status.successRate,
            averageExecutionTime: 0, // 可以根据实际需求计算
            errorCount: this.status.errors.length
        };
    }
    // ==================== 确认系统相关方法 ====================
    // 创建确认请求
    async createConfirmationRequest(type, title, description, details, priority = 'medium', timeoutSeconds) {
        const requestId = `conf_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const request = {
            id: requestId,
            type,
            title,
            description,
            details,
            options: {
                approve: {
                    label: '确认执行',
                    action: 'approve',
                    consequences: ['任务将按计划执行']
                },
                reject: {
                    label: '拒绝执行',
                    action: 'reject',
                    alternatives: ['跳过此任务', '修改配置后重试']
                }
            },
            priority,
            timeoutSeconds,
            defaultAction: 'reject',
            createdAt: new Date(),
            expiresAt: timeoutSeconds ? new Date(Date.now() + timeoutSeconds * 1000) : undefined,
            status: 'pending'
        };
        this.pendingConfirmations.set(requestId, request);
        // 发送确认通知
        const config = await this.getAutomationConfig();
        if (config.notificationSettings.onConfirmationRequired) {
            this.sendNotification(`需要确认: ${title}`);
        }
        // 设置超时处理
        if (timeoutSeconds) {
            setTimeout(() => {
                this.handleConfirmationTimeout(requestId);
            }, timeoutSeconds * 1000);
        }
        return requestId;
    }
    // 响应确认请求
    async respondToConfirmation(response) {
        const request = this.pendingConfirmations.get(response.requestId);
        if (!request) {
            throw new Error(`确认请求 ${response.requestId} 不存在`);
        }
        if (request.status !== 'pending') {
            throw new Error(`确认请求 ${response.requestId} 已处理`);
        }
        // 更新请求状态
        request.status = response.action === 'approve' ? 'approved' :
            response.action === 'reject' ? 'rejected' :
                response.action === 'modify' ? 'modified' : 'cancelled';
        // 执行回调
        const callback = this.confirmationCallbacks.get(response.requestId);
        if (callback) {
            callback(response);
            this.confirmationCallbacks.delete(response.requestId);
        }
        // 清理已处理的请求
        this.pendingConfirmations.delete(response.requestId);
    }
    // 获取待处理的确认请求
    getPendingConfirmations() {
        return Array.from(this.pendingConfirmations.values())
            .filter(req => req.status === 'pending')
            .sort((a, b) => {
            const priorityOrder = { urgent: 4, high: 3, medium: 2, low: 1 };
            return priorityOrder[b.priority] - priorityOrder[a.priority];
        });
    }
    // 等待确认响应
    async waitForConfirmation(requestId) {
        return new Promise((resolve, reject) => {
            const request = this.pendingConfirmations.get(requestId);
            if (!request) {
                reject(new Error(`确认请求 ${requestId} 不存在`));
                return;
            }
            this.confirmationCallbacks.set(requestId, (response) => {
                resolve(response);
            });
            // 设置超时
            if (request.timeoutSeconds) {
                setTimeout(() => {
                    if (this.confirmationCallbacks.has(requestId)) {
                        this.confirmationCallbacks.delete(requestId);
                        reject(new Error(`确认请求 ${requestId} 超时`));
                    }
                }, request.timeoutSeconds * 1000);
            }
        });
    }
    // 处理确认超时
    handleConfirmationTimeout(requestId) {
        const request = this.pendingConfirmations.get(requestId);
        if (!request || request.status !== 'pending') {
            return;
        }
        // 执行默认操作
        const response = {
            requestId,
            action: request.defaultAction === 'approve' ? 'approve' : 'reject',
            reason: '超时自动处理',
            respondedAt: new Date(),
            respondedBy: 'system_timeout'
        };
        request.status = 'expired';
        this.respondToConfirmation(response);
    }
    // ==================== 智能优先级调整相关方法 ====================
    // 添加优先级调整规则
    async addPriorityRule(rule) {
        const ruleId = `rule_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const newRule = {
            ...rule,
            id: ruleId,
            createdAt: new Date(),
            triggerCount: 0
        };
        this.priorityRules.push(newRule);
        return ruleId;
    }
    // 移除优先级调整规则
    removePriorityRule(ruleId) {
        const index = this.priorityRules.findIndex(rule => rule.id === ruleId);
        if (index !== -1) {
            this.priorityRules.splice(index, 1);
            return true;
        }
        return false;
    }
    // 获取优先级调整规则
    getPriorityRules() {
        return [...this.priorityRules];
    }
    // 执行智能优先级调整
    async executeSmartPriorityAdjustment() {
        const config = await this.getAutomationConfig();
        if (!config.smartPriorityAdjustment.enabled) {
            return;
        }
        const now = new Date();
        const triggeredRules = [];
        for (const rule of this.priorityRules) {
            if (!rule.enabled)
                continue;
            if (await this.shouldTriggerRule(rule, now)) {
                triggeredRules.push(rule);
            }
        }
        // 应用触发的规则
        for (const rule of triggeredRules) {
            await this.applyPriorityRule(rule);
        }
    }
    // 判断是否应该触发规则
    async shouldTriggerRule(rule, now) {
        const { condition } = rule;
        switch (condition.type) {
            case 'time_based':
                return this.checkTimeBasedCondition(condition.parameters, now);
            case 'resource_based':
                return await this.checkResourceBasedCondition(condition.parameters);
            case 'performance_based':
                return await this.checkPerformanceBasedCondition(condition.parameters);
            case 'user_defined':
                return await this.checkUserDefinedCondition(condition.parameters);
            default:
                return false;
        }
    }
    // 检查基于时间的条件
    checkTimeBasedCondition(params, now) {
        if (!params.timeWindow)
            return false;
        const { start, end, daysOfWeek } = params.timeWindow;
        const currentTime = now.getHours() * 60 + now.getMinutes();
        const currentDay = now.getDay();
        // 检查时间窗口
        const [startHour, startMin] = start.split(':').map(Number);
        const [endHour, endMin] = end.split(':').map(Number);
        const startTime = startHour * 60 + startMin;
        const endTime = endHour * 60 + endMin;
        const inTimeWindow = currentTime >= startTime && currentTime <= endTime;
        // 检查星期
        const inDayWindow = !daysOfWeek || daysOfWeek.includes(currentDay);
        return inTimeWindow && inDayWindow;
    }
    // 检查基于资源的条件
    async checkResourceBasedCondition(params) {
        // 模拟资源检查
        const currentResources = {
            cpuUsage: Math.random() * 100,
            memoryUsage: Math.random() * 100,
            networkLatency: Math.random() * 1000
        };
        const { resourceThresholds } = params;
        if (!resourceThresholds)
            return false;
        return ((!resourceThresholds.cpuUsage || currentResources.cpuUsage > resourceThresholds.cpuUsage) &&
            (!resourceThresholds.memoryUsage || currentResources.memoryUsage > resourceThresholds.memoryUsage) &&
            (!resourceThresholds.networkLatency || currentResources.networkLatency > resourceThresholds.networkLatency));
    }
    // 检查基于性能的条件
    async checkPerformanceBasedCondition(params) {
        const { performanceMetrics } = params;
        if (!performanceMetrics)
            return false;
        const currentMetrics = {
            successRate: this.status.successRate,
            averageExecutionTime: 0, // 需要实际计算
            errorRate: this.status.errors.length / Math.max(this.status.totalTasksCompleted, 1)
        };
        return ((!performanceMetrics.successRate || currentMetrics.successRate < performanceMetrics.successRate) &&
            (!performanceMetrics.averageExecutionTime || currentMetrics.averageExecutionTime > performanceMetrics.averageExecutionTime) &&
            (!performanceMetrics.errorRate || currentMetrics.errorRate > performanceMetrics.errorRate));
    }
    // 检查用户自定义条件
    async checkUserDefinedCondition(params) {
        // 简化实现，实际项目中可以使用表达式解析器
        return false;
    }
    // 应用优先级规则
    async applyPriorityRule(rule) {
        const { adjustment } = rule;
        for (const taskType of adjustment.taskTypes) {
            const currentPriority = this.currentPriorities.get(taskType) || 0;
            let newPriority;
            switch (adjustment.action) {
                case 'increase':
                    newPriority = Math.min(10, currentPriority + adjustment.priorityChange);
                    break;
                case 'decrease':
                    newPriority = Math.max(0, currentPriority - adjustment.priorityChange);
                    break;
                case 'set_absolute':
                    newPriority = adjustment.absoluteValue || 0;
                    break;
                default:
                    continue;
            }
            // 记录优先级变更历史
            const historyEntry = {
                id: `hist_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                ruleId: rule.id,
                taskType,
                oldPriority: currentPriority,
                newPriority,
                reason: `规则触发: ${rule.name}`,
                triggeredBy: 'rule',
                timestamp: new Date(),
                impact: {
                    affectedTasks: 0 // 需要实际计算
                }
            };
            this.priorityHistory.push(historyEntry);
            this.currentPriorities.set(taskType, newPriority);
            // 更新规则触发统计
            rule.triggerCount++;
            rule.lastTriggered = new Date();
        }
        // 发送通知
        const config = await this.getAutomationConfig();
        if (config.notificationSettings.onPriorityAdjustment) {
            this.sendNotification(`优先级已调整: ${rule.name}`);
        }
    }
    // 获取优先级调整历史
    getPriorityHistory(limit = 50) {
        return this.priorityHistory
            .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
            .slice(0, limit);
    }
    // 获取当前优先级设置
    getCurrentPriorities() {
        return new Map(this.currentPriorities);
    }
    // 手动调整任务优先级
    async manualAdjustPriority(taskType, newPriority, reason) {
        const oldPriority = this.currentPriorities.get(taskType) || 0;
        const historyEntry = {
            id: `hist_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            ruleId: 'manual',
            taskType,
            oldPriority,
            newPriority,
            reason,
            triggeredBy: 'manual',
            timestamp: new Date(),
            impact: {
                affectedTasks: 0 // 需要实际计算
            }
        };
        this.priorityHistory.push(historyEntry);
        this.currentPriorities.set(taskType, newPriority);
    }
    // ==================== 自动化模式管理 ====================
    // 设置自动化级别
    async setAutomationLevel(level) {
        const oldLevel = this.currentAutomationLevel;
        this.currentAutomationLevel = level;
        // 更新配置
        const config = await this.getAutomationConfig();
        config.automationMode.level = level;
        await this.updateAutomationConfig({ automationMode: config.automationMode });
        // 发送通知
        if (config.notificationSettings.onAutomationModeChange) {
            this.sendNotification(`自动化级别已从 ${oldLevel} 更改为 ${level}`);
        }
    }
    // 获取当前自动化级别
    getCurrentAutomationLevel() {
        return this.currentAutomationLevel;
    }
    // 检查是否需要确认
    async shouldRequireConfirmation(action, context) {
        const config = await this.getAutomationConfig();
        const { automationMode } = config;
        switch (automationMode.level) {
            case 'fully_automatic':
                return false;
            case 'semi_automatic': {
                if (!automationMode.semiAutomatic)
                    return true;
                const semiConfig = automationMode.semiAutomatic;
                switch (action) {
                    case 'task_execution':
                        return semiConfig.requireConfirmationFor.taskExecution;
                    case 'strategy_changes':
                        return semiConfig.requireConfirmationFor.strategyChanges;
                    case 'error_recovery':
                        return semiConfig.requireConfirmationFor.errorRecovery;
                    case 'resource_intensive':
                        return semiConfig.requireConfirmationFor.resourceIntensiveTasks;
                    case 'new_task_types':
                        return semiConfig.requireConfirmationFor.newTaskTypes;
                    default:
                        return true;
                }
            }
            case 'manual_confirmation':
                return true;
            default:
                return true;
        }
    }
    // ==================== 异常处理和错误恢复 ====================
    // 处理任务执行错误
    async handleTaskError(taskId, error, context) {
        const config = await this.getAutomationConfig();
        const errorConfig = config.errorRecovery;
        // 记录错误
        const errorRecord = {
            id: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            taskId,
            error: error.message,
            stack: error.stack,
            context,
            timestamp: new Date(),
            recoveryAttempts: 0,
            resolved: false
        };
        this.status.errors.push(errorRecord);
        // 发送错误通知
        if (config.notificationSettings.onError) {
            this.sendNotification(`任务执行错误: ${error.message}`);
        }
        // 尝试自动恢复
        if (errorConfig.autoRetryOnTransientErrors) {
            return await this.attemptErrorRecovery(errorRecord, errorConfig);
        }
        return false;
    }
    // 尝试错误恢复
    async attemptErrorRecovery(errorRecord, errorConfig) {
        const { autoRetry } = errorConfig;
        if (errorRecord.recoveryAttempts >= autoRetry.maxAttempts) {
            // 超过最大重试次数，检查是否需要人工干预
            if (await this.shouldRequireConfirmation('error_recovery', errorRecord)) {
                const requestId = await this.createConfirmationRequest('error_recovery', '错误恢复确认', `任务 ${errorRecord.taskId} 执行失败，是否继续尝试恢复？`, { errorDetails: errorRecord.error, taskId: errorRecord.taskId, affectedTasks: [errorRecord.taskId] }, 'high', 300 // 5分钟超时
                );
                try {
                    const response = await this.waitForConfirmation(requestId);
                    if (response.action !== 'approve') {
                        return false;
                    }
                }
                catch (timeoutError) {
                    return false;
                }
            }
            else {
                return false;
            }
        }
        // 执行恢复策略
        for (const strategy of autoRetry.strategies) {
            if (await this.executeRecoveryStrategy(strategy, errorRecord)) {
                errorRecord.resolved = true;
                errorRecord.recoveryAttempts++;
                return true;
            }
        }
        errorRecord.recoveryAttempts++;
        // 等待重试间隔
        if (autoRetry.retryInterval > 0) {
            await new Promise(resolve => setTimeout(resolve, autoRetry.retryInterval * 1000));
        }
        return false;
    }
    // 执行恢复策略
    async executeRecoveryStrategy(strategy, errorRecord) {
        try {
            switch (strategy) {
                case 'restart_task': {
                    return await this.restartTask(errorRecord.taskId);
                }
                case 'reset_environment': {
                    return await this.resetEnvironment();
                }
                case 'switch_strategy': {
                    return await this.switchToAlternativeStrategy(errorRecord.taskId);
                }
                case 'reduce_complexity': {
                    return await this.reduceTaskComplexity(errorRecord.taskId);
                }
                case 'wait_and_retry': {
                    await new Promise(resolve => setTimeout(resolve, 5000)); // 等待5秒
                    return await this.retryTask(errorRecord.taskId);
                }
                default:
                    return false;
            }
        }
        catch (recoveryError) {
            console.error(`恢复策略 ${strategy} 执行失败:`, recoveryError);
            return false;
        }
    }
    // 重启任务
    async restartTask(taskId) {
        try {
            // 模拟重启任务逻辑
            console.log(`重启任务: ${taskId}`);
            return true;
        }
        catch (error) {
            return false;
        }
    }
    // 重置环境
    async resetEnvironment() {
        try {
            // 模拟重置环境逻辑
            console.log('重置执行环境');
            return true;
        }
        catch (error) {
            return false;
        }
    }
    // 切换到备用策略
    async switchToAlternativeStrategy(taskId) {
        try {
            // 模拟切换策略逻辑
            console.log(`为任务 ${taskId} 切换到备用策略`);
            return true;
        }
        catch (error) {
            return false;
        }
    }
    // 降低任务复杂度
    async reduceTaskComplexity(taskId) {
        try {
            // 模拟降低复杂度逻辑
            console.log(`降低任务 ${taskId} 的复杂度`);
            return true;
        }
        catch (error) {
            return false;
        }
    }
    // 重试任务
    async retryTask(taskId) {
        try {
            // 模拟重试任务逻辑
            console.log(`重试任务: ${taskId}`);
            return true;
        }
        catch (error) {
            return false;
        }
    }
    // 获取错误统计
    getErrorStatistics() {
        const totalErrors = this.status.errors.length;
        const resolvedErrors = this.status.errors.filter(e => e.resolved).length;
        const pendingErrors = totalErrors - resolvedErrors;
        const errorRate = totalErrors / Math.max(this.status.totalTasksCompleted, 1);
        // 统计常见错误
        const errorCounts = new Map();
        this.status.errors.forEach(error => {
            const errorType = error.error.split(':')[0]; // 取错误消息的第一部分作为错误类型
            errorCounts.set(errorType, (errorCounts.get(errorType) || 0) + 1);
        });
        const commonErrors = Array.from(errorCounts.entries())
            .map(([error, count]) => ({ error, count }))
            .sort((a, b) => b.count - a.count)
            .slice(0, 5);
        return {
            totalErrors,
            resolvedErrors,
            pendingErrors,
            errorRate,
            commonErrors
        };
    }
    // 清理已解决的错误记录
    cleanupResolvedErrors() {
        const config = this.getDefaultConfig();
        const maxAge = 7 * 24 * 60 * 60 * 1000; // 7天
        const cutoffTime = new Date(Date.now() - maxAge);
        this.status.errors = this.status.errors.filter(error => {
            return !error.resolved || error.timestamp > cutoffTime;
        });
    }
    // 检查系统健康状态
    async checkSystemHealth() {
        const issues = [];
        const recommendations = [];
        const errorStats = this.getErrorStatistics();
        const config = await this.getAutomationConfig();
        // 检查错误率
        if (errorStats.errorRate > 0.3) {
            issues.push(`错误率过高: ${(errorStats.errorRate * 100).toFixed(1)}%`);
            recommendations.push('检查任务配置和执行环境');
        }
        // 检查待处理错误数量
        if (errorStats.pendingErrors > 10) {
            issues.push(`待处理错误过多: ${errorStats.pendingErrors} 个`);
            recommendations.push('手动处理积压的错误');
        }
        // 检查自动化配置
        if (!config.errorRecovery.autoRetryOnTransientErrors) {
            issues.push('自动重试功能未启用');
            recommendations.push('启用自动重试以提高系统稳定性');
        }
        // 确定系统状态
        let status;
        if (issues.length === 0) {
            status = 'healthy';
        }
        else if (errorStats.errorRate > 0.5 || errorStats.pendingErrors > 20) {
            status = 'critical';
        }
        else {
            status = 'warning';
        }
        return { status, issues, recommendations };
    }
}
