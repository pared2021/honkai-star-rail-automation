// 主进程控制器 - 整合所有核心模块
import GameDetector from './GameDetector.js';
import TaskExecutor, { TaskPriority } from './TaskExecutor.js';
import ImageRecognition from './ImageRecognition.js';
import InputController from './InputController.js';
import DatabaseService from '../services/DatabaseService';
import { EventEmitter } from 'events';
import { promises as fs } from 'fs';
import path from 'path';
import { v4 as uuidv4 } from 'uuid';
export class MainController extends EventEmitter {
    constructor(config = {}) {
        super();
        Object.defineProperty(this, "gameDetector", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "taskExecutor", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "imageRecognition", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "inputController", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "databaseService", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "config", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "isInitialized", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: false
        });
        Object.defineProperty(this, "currentGameStatus", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: { isRunning: false, isActive: false }
        });
        Object.defineProperty(this, "performanceMetrics", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "systemHealth", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "startTime", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "eventLogs", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: []
        });
        Object.defineProperty(this, "configFilePath", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "monitoringInterval", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "healthCheckInterval", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "errorCount", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: 0
        });
        Object.defineProperty(this, "lastErrorTime", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "automationState", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "autoScheduleInterval", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "pauseCheckInterval", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        // 游戏监控相关属性
        Object.defineProperty(this, "gameMonitoringState", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "gameMonitorInterval", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "windowStateCheckInterval", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "gameRecoveryInterval", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        // 异常处理相关属性
        Object.defineProperty(this, "exceptionHandlingState", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "recoveryCheckInterval", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "systemStabilityCheckInterval", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        // 性能监控相关属性
        Object.defineProperty(this, "performanceMonitoringState", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "performanceMonitorInterval", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "optimizationCheckInterval", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "resourceMonitorInterval", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        // 配置管理相关属性
        Object.defineProperty(this, "configurationSchema", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "configurationState", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "configurationBackups", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "persistenceOptions", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "autoSaveInterval", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "configWatcher", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        }); // fs.FSWatcher type
        Object.defineProperty(this, "gameDetectionInterval", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        }); // 游戏检测定时器
        Object.defineProperty(this, "gameStatusInterval", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        // 事件系统相关属性
        Object.defineProperty(this, "eventSystemState", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "eventSubscriptions", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "eventHistory", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "notificationChannels", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "eventQueue", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "eventProcessingInterval", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "notificationRateLimits", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        // ==================== 事件过滤和路由功能 ====================
        /**
         * 事件路由规则
         */
        Object.defineProperty(this, "eventRoutes", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: new Map()
        });
        this.config = {
            gameDetection: {
                interval: 1000,
                timeout: 5000,
                ...config.gameDetection
            },
            taskExecution: {
                retryAttempts: 3,
                retryDelay: 1000,
                ...config.taskExecution
            },
            safety: {
                enableSafetyChecks: true,
                maxExecutionTime: 300000,
                ...config.safety
            },
            maxConcurrentTasks: config.maxConcurrentTasks || 3,
            autoRecovery: config.autoRecovery !== undefined ? config.autoRecovery : true,
            performanceMonitoring: config.performanceMonitoring !== undefined ? config.performanceMonitoring : true,
            configPersistence: config.configPersistence !== undefined ? config.configPersistence : true,
            eventLogging: config.eventLogging !== undefined ? config.eventLogging : true,
            automation: {
                enableAutoScheduling: true,
                smartPauseResume: true,
                adaptiveRetry: true,
                loadBalancing: true,
                priorityAdjustment: true,
                ...config.automation
            }
        };
        this.startTime = new Date();
        this.configFilePath = path.join(process.cwd(), 'config', 'main-controller.json');
        // 初始化性能指标
        this.performanceMetrics = {
            cpuUsage: 0,
            memoryUsage: 0,
            taskExecutionTime: 0,
            gameDetectionLatency: 0,
            errorRate: 0,
            uptime: 0
        };
        // 初始化系统健康状态
        this.systemHealth = {
            status: 'healthy',
            issues: [],
            recommendations: [],
            lastCheck: new Date()
        };
        // 初始化自动化状态
        this.automationState = {
            isAutoSchedulingActive: false,
            isPaused: false,
            scheduledTasksCount: 0,
            adaptiveRetryEnabled: this.config.automation.adaptiveRetry
        };
        // 初始化游戏监控状态
        this.gameMonitoringState = {
            isMonitoring: false,
            gameStatusHistory: [],
            windowStateChanges: [],
            connectionLostCount: 0,
            autoRecoveryAttempts: 0
        };
        // 初始化异常处理状态
        this.exceptionHandlingState = {
            isEnabled: true,
            exceptions: [],
            recoveryStrategies: new Map(),
            globalRecoveryAttempts: 0,
            systemStability: 'stable',
            errorThresholds: {
                lowSeverity: 10,
                mediumSeverity: 5,
                highSeverity: 3,
                criticalSeverity: 1
            }
        };
        // 初始化恢复策略
        this.initializeRecoveryStrategies();
        // 初始化性能监控状态
        this.performanceMonitoringState = {
            isMonitoring: false,
            snapshots: [],
            alerts: [],
            thresholds: {
                cpu: {
                    warning: 70,
                    critical: 90
                },
                memory: {
                    warning: 80,
                    critical: 95
                },
                responseTime: {
                    warning: 1000,
                    critical: 3000
                },
                errorRate: {
                    warning: 5,
                    critical: 10
                },
                taskExecutionTime: {
                    warning: 30000,
                    critical: 60000
                }
            },
            optimizationActions: [],
            lastOptimization: null,
            autoOptimizationEnabled: true,
            maxSnapshotHistory: 100,
            monitoringInterval: 5000
        };
        // 初始化优化操作
        this.initializeOptimizationActions();
        // 初始化配置管理
        this.configurationSchema = this.createDefaultConfiguration();
        this.configurationState = {
            isLoaded: false,
            isDirty: false,
            autoSaveEnabled: true,
            autoSaveInterval: 30000, // 30秒自动保存
            backupCount: 0,
            validationErrors: []
        };
        this.configurationBackups = [];
        this.persistenceOptions = {
            format: 'json',
            encryption: false,
            compression: false,
            backup: true,
            validate: true,
            autoSave: true,
            backupEnabled: true
        };
        // 初始化配置管理
        this.initializeConfigurationManagement();
        // 初始化事件系统
        this.initializeEventSystem();
        // 初始化各个模块
        this.gameDetector = new GameDetector();
        this.taskExecutor = new TaskExecutor(this.config.maxConcurrentTasks);
        this.imageRecognition = new ImageRecognition();
        this.inputController = new InputController();
        this.databaseService = new DatabaseService();
        // 设置模块间的事件监听
        this.setupModuleEventListeners();
    }
    /**
     * 设置模块间的事件监听
     */
    setupModuleEventListeners() {
        // 监听任务执行器事件
        this.taskExecutor.on('taskCompleted', (task) => {
            this.logEvent('info', `任务完成: ${task.taskType} (${task.id})`);
            this.emit('taskCompleted', task);
        });
        this.taskExecutor.on('taskFailed', (task, error) => {
            this.logEvent('error', `任务失败: ${task.taskType} (${task.id}) - ${error}`);
            this.handleTaskFailure(task, error);
            this.emit('taskFailed', task, error);
        });
        this.taskExecutor.on('taskStarted', (task) => {
            this.logEvent('info', `任务开始: ${task.taskType} (${task.id})`);
            this.emit('taskStarted', task);
        });
    }
    /**
     * 初始化主控制器
     */
    async initialize() {
        try {
            this.log('info', '正在初始化主控制器...');
            // 初始化配置管理
            await this.initializeConfigurationManagement();
            // 加载配置
            await this.loadConfiguration();
            // 启动配置自动保存
            if (this.configurationState.autoSaveEnabled) {
                this.startAutoSave();
            }
            // 初始化数据库
            await this.databaseService.initialize();
            // 启动游戏检测
            this.gameDetector.startDetection(this.config.gameDetectionInterval);
            // 设置游戏状态监听
            this.setupGameStatusMonitoring();
            // 启动性能监控
            if (this.config.performanceMonitoring) {
                this.startPerformanceMonitoring();
            }
            // 加载配置
            await this.loadConfiguration();
            // 启动配置自动保存
            if (this.configurationState.autoSaveEnabled) {
                this.startAutoSave();
            }
            // 启动健康检查
            this.startHealthCheck();
            // 启动自动调度（如果启用）
            if (this.config.automation.enableAutoScheduling) {
                this.startAutoScheduling();
            }
            // 启动游戏状态监控
            this.startGameMonitoring();
            // 启动异常处理系统
            this.startExceptionHandling();
            // 启动性能监控
            if (this.config.performanceMonitoring) {
                this.startPerformanceMonitoring();
            }
            // 启动事件系统
            this.startEventSystem();
            this.isInitialized = true;
            this.log('info', '主控制器初始化完成');
            this.emit('initialized');
        }
        catch (error) {
            this.log('error', `主控制器初始化失败: ${error}`);
            this.emit('initializationFailed', error);
            throw error;
        }
    }
    /**
     * 处理任务失败
     */
    async handleTaskFailure(task, error) {
        this.errorCount++;
        this.lastErrorTime = new Date();
        if (this.config.autoRecovery) {
            this.log('info', `尝试自动恢复任务: ${task.id}`);
            // 实现自动恢复逻辑
            await this.attemptTaskRecovery(task);
        }
    }
    /**
     * 尝试任务恢复
     */
    async attemptTaskRecovery(task) {
        try {
            // 检查游戏状态
            const gameStatus = await this.gameDetector.getCurrentStatus();
            if (!gameStatus.isRunning) {
                this.log('warn', '游戏未运行，无法恢复任务');
                return;
            }
            // 重新添加任务到队列
            const newTaskId = this.taskExecutor.addTask({
                id: uuidv4(),
                accountId: task.accountId,
                taskType: task.taskType,
                config: task.config,
                status: 'pending',
                createdAt: new Date()
            }, TaskPriority.HIGH);
            this.log('info', `任务恢复成功，新任务ID: ${newTaskId}`);
        }
        catch (error) {
            this.log('error', `任务恢复失败: ${error}`);
        }
    }
    /**
     * 记录事件日志
     */
    logEvent(level, message, metadata) {
        if (!this.config.eventLogging)
            return;
        const eventLog = {
            id: uuidv4(),
            taskId: 'system',
            level,
            message,
            timestamp: new Date(),
            metadata
        };
        this.eventLogs.push(eventLog);
        // 限制日志数量
        if (this.eventLogs.length > 1000) {
            this.eventLogs = this.eventLogs.slice(-500);
        }
        // 创建事件对象用于路由处理
        const routingEvent = {
            type: 'log',
            severity: level,
            source: 'MainController',
            message,
            timestamp: eventLog.timestamp,
            data: {
                id: eventLog.id,
                taskId: eventLog.taskId,
                metadata
            }
        };
        // 处理事件路由（异步，不阻塞日志记录）
        this.processEventRouting(routingEvent).catch(error => {
            console.error('事件路由处理失败:', error);
        });
        this.emit('eventLogged', eventLog);
    }
    /**
     * 加载持久化配置
     */
    async loadPersistedConfig() {
        try {
            const configData = await fs.readFile(this.configFilePath, 'utf-8');
            const persistedConfig = JSON.parse(configData);
            this.config = { ...this.config, ...persistedConfig };
            this.log('info', '已加载持久化配置');
        }
        catch (error) {
            this.log('debug', '未找到持久化配置文件，使用默认配置');
        }
    }
    /**
     * 创建默认配置
     */
    createDefaultConfiguration() {
        return {
            version: '1.0.0',
            lastModified: new Date(),
            game: {
                detectionInterval: 1000,
                windowTitle: 'StarRail',
                processName: 'StarRail.exe',
                autoStart: false,
                priority: 'normal'
            },
            tasks: {
                maxConcurrent: 3,
                defaultTimeout: 30000,
                retryAttempts: 3,
                retryDelay: 1000,
                priorityWeights: {
                    main: 3,
                    side: 2,
                    daily: 1,
                    event: 4
                }
            },
            performance: {
                monitoringEnabled: true,
                monitoringInterval: 5000,
                autoOptimization: true,
                thresholds: {
                    cpu: { warning: 70, critical: 90 },
                    memory: { warning: 80, critical: 95 },
                    responseTime: { warning: 1000, critical: 3000 },
                    errorRate: { warning: 5, critical: 10 },
                    taskExecutionTime: { warning: 30000, critical: 60000 }
                }
            },
            automation: {
                enabled: true,
                scheduleInterval: 30000,
                adaptiveScheduling: true,
                learningEnabled: true
            },
            ui: {
                theme: 'auto',
                language: 'zh-CN',
                notifications: true,
                soundEnabled: true,
                logLevel: 'info'
            },
            advanced: {
                debugMode: false,
                experimentalFeatures: false,
                telemetryEnabled: true,
                backupEnabled: true,
                backupInterval: 3600000
            }
        };
    }
    /**
     * 初始化配置管理
     */
    async initializeConfigurationManagement() {
        try {
            // 初始化配置状态
            this.configurationState = {
                isLoaded: false,
                isDirty: false,
                autoSaveEnabled: true,
                autoSaveInterval: 30000, // 30秒
                backupCount: 5,
                validationErrors: []
            };
            // 初始化配置备份数组
            this.configurationBackups = [];
            // 初始化持久化选项
            this.persistenceOptions = {
                format: 'json',
                encryption: false,
                compression: false,
                backup: true,
                validate: true,
                autoSave: true,
                backupEnabled: true
            };
            this.logEvent('info', '配置管理系统初始化完成');
        }
        catch (error) {
            this.logEvent('error', '配置管理系统初始化失败', { error: error.toString() });
            throw error;
        }
    }
    /**
     * 加载配置
     */
    async loadConfiguration() {
        try {
            const configPath = path.join(process.cwd(), 'config', 'main-controller.json');
            if (await this.fileExists(configPath)) {
                const configData = await fs.readFile(configPath, 'utf-8');
                const loadedConfig = JSON.parse(configData);
                // 验证配置
                const validationResult = this.validateConfiguration(loadedConfig);
                if (!validationResult.isValid) {
                    this.configurationState.validationErrors = validationResult.errors;
                    this.logEvent('warn', '配置验证失败，使用默认配置', { errors: validationResult.errors });
                    return;
                }
                // 合并配置
                this.config = { ...this.config, ...loadedConfig };
                this.configurationState.isLoaded = true;
                this.configurationState.lastLoaded = new Date();
                this.logEvent('info', '配置加载成功', { configPath });
            }
            else {
                this.logEvent('info', '配置文件不存在，使用默认配置');
                await this.saveConfiguration(); // 保存默认配置
            }
        }
        catch (error) {
            this.logEvent('error', '配置加载失败', { error: error.toString() });
            this.configurationState.validationErrors.push(`加载失败: ${error.toString()}`);
        }
    }
    /**
     * 保存配置
     */
    async saveConfiguration() {
        try {
            const configPath = path.join(process.cwd(), 'config', 'main-controller.json');
            // 创建备份
            if (this.persistenceOptions.backupEnabled) {
                await this.createConfigurationBackup();
            }
            // 确保目录存在
            await fs.mkdir(path.dirname(configPath), { recursive: true });
            // 保存配置
            const configData = JSON.stringify(this.config, null, 2);
            await fs.writeFile(configPath, configData, 'utf-8');
            this.configurationState.isDirty = false;
            this.configurationState.lastSaved = new Date();
            this.logEvent('info', '配置保存成功', { configPath });
            this.emit('configurationSaved', { path: configPath });
        }
        catch (error) {
            this.logEvent('error', '配置保存失败', { error: error.toString() });
            throw error;
        }
    }
    /**
     * 更新配置
     */
    async updateConfiguration(updates) {
        try {
            // 验证更新
            const mergedConfig = { ...this.config, ...updates };
            const validationResult = this.validateConfiguration(mergedConfig);
            if (!validationResult.isValid) {
                throw new Error(`配置验证失败: ${validationResult.errors.join(', ')}`);
            }
            // 应用更新
            this.config = mergedConfig;
            this.configurationState.isDirty = true;
            this.logEvent('info', '配置更新成功', { updates });
            this.emit('configurationUpdated', { updates });
            // 自动保存
            if (this.persistenceOptions.autoSave) {
                await this.saveConfiguration();
            }
        }
        catch (error) {
            this.logEvent('error', '配置更新失败', { error: error.toString() });
            throw error;
        }
    }
    /**
     * 验证配置
     */
    validateConfiguration(config) {
        const errors = [];
        try {
            // 验证基本结构
            if (!config || typeof config !== 'object') {
                errors.push('配置必须是一个对象');
                return { isValid: false, errors };
            }
            // 验证版本信息
            if (!config.version || typeof config.version !== 'string') {
                errors.push('配置版本信息缺失或无效');
            }
            else if (!this.isValidVersion(config.version)) {
                errors.push('配置版本格式无效，应为 x.y.z 格式');
            }
            // 验证游戏检测配置
            if (config.gameDetection) {
                if (config.gameDetection.interval && config.gameDetection.interval < 100) {
                    errors.push('游戏检测间隔不能小于100ms');
                }
                if (config.gameDetection.timeout && config.gameDetection.timeout < 1000) {
                    errors.push('游戏检测超时不能小于1000ms');
                }
            }
            // 验证任务执行配置
            if (config.taskExecution) {
                if (config.taskExecution.maxConcurrentTasks && config.taskExecution.maxConcurrentTasks < 1) {
                    errors.push('最大并发任务数不能小于1');
                }
                if (config.taskExecution.defaultTimeout && config.taskExecution.defaultTimeout < 1000) {
                    errors.push('默认任务超时不能小于1000ms');
                }
            }
            // 验证性能监控配置
            if (config.performanceMonitoring) {
                if (config.performanceMonitoring.interval && config.performanceMonitoring.interval < 1000) {
                    errors.push('性能监控间隔不能小于1000ms');
                }
            }
            // 验证安全配置
            if (config.security) {
                if (config.security.maxRetryAttempts && config.security.maxRetryAttempts < 1) {
                    errors.push('最大重试次数不能小于1');
                }
                if (config.security.lockoutDuration && config.security.lockoutDuration < 1000) {
                    errors.push('锁定持续时间不能小于1000ms');
                }
            }
        }
        catch (error) {
            errors.push(`配置验证过程中发生错误: ${error.toString()}`);
        }
        return { isValid: errors.length === 0, errors };
    }
    /**
     * 验证版本格式
     */
    isValidVersion(version) {
        const versionRegex = /^\d+\.\d+\.\d+$/;
        return versionRegex.test(version);
    }
    /**
     * 比较版本号
     */
    compareVersions(version1, version2) {
        const v1Parts = version1.split('.').map(Number);
        const v2Parts = version2.split('.').map(Number);
        for (let i = 0; i < Math.max(v1Parts.length, v2Parts.length); i++) {
            const v1Part = v1Parts[i] || 0;
            const v2Part = v2Parts[i] || 0;
            if (v1Part > v2Part)
                return 1;
            if (v1Part < v2Part)
                return -1;
        }
        return 0;
    }
    /**
     * 升级配置版本
     */
    async upgradeConfiguration(targetVersion) {
        try {
            const currentVersion = this.configurationSchema.version;
            if (this.compareVersions(currentVersion, targetVersion) >= 0) {
                throw new Error(`当前版本 ${currentVersion} 已经是最新或更高版本`);
            }
            // 创建升级前备份
            await this.createConfigurationBackup();
            // 执行版本升级逻辑
            const upgradedConfig = await this.performConfigurationUpgrade(currentVersion, targetVersion);
            // 验证升级后的配置
            const validationResult = this.validateConfiguration(upgradedConfig);
            if (!validationResult.isValid) {
                throw new Error(`升级后配置验证失败: ${validationResult.errors.join(', ')}`);
            }
            // 应用升级后的配置
            this.config = upgradedConfig;
            this.configurationSchema.version = targetVersion;
            this.configurationSchema.lastModified = new Date();
            this.configurationState.isDirty = true;
            this.logEvent('info', '配置版本升级成功', {
                fromVersion: currentVersion,
                toVersion: targetVersion
            });
            // 保存升级后的配置
            await this.saveConfiguration();
        }
        catch (error) {
            this.logEvent('error', '配置版本升级失败', {
                targetVersion,
                error: error.toString()
            });
            throw error;
        }
    }
    /**
     * 执行配置升级
     */
    async performConfigurationUpgrade(fromVersion, toVersion) {
        let config = { ...this.config };
        // 根据版本执行相应的升级逻辑
        if (this.compareVersions(fromVersion, '1.1.0') < 0 && this.compareVersions(toVersion, '1.1.0') >= 0) {
            // 升级到 1.1.0
            config = this.upgradeToV1_1_0(config);
        }
        if (this.compareVersions(fromVersion, '1.2.0') < 0 && this.compareVersions(toVersion, '1.2.0') >= 0) {
            // 升级到 1.2.0
            config = this.upgradeToV1_2_0(config);
        }
        return config;
    }
    /**
     * 升级到版本 1.1.0
     */
    upgradeToV1_1_0(config) {
        // 添加新的性能监控配置
        if (!config.performanceMonitoring) {
            config.performanceMonitoring = {
                enabled: true,
                interval: 5000,
                memoryThreshold: 80,
                cpuThreshold: 70
            };
        }
        // 添加新的安全配置
        if (!config.security) {
            config.security = {
                enableSafetyChecks: true,
                maxRetryAttempts: 3,
                lockoutDuration: 300000
            };
        }
        return config;
    }
    /**
     * 升级到版本 1.2.0
     */
    upgradeToV1_2_0(config) {
        // 添加事件系统配置
        if (!config.eventSystem) {
            config.eventSystem = {
                enabled: true,
                maxEventHistory: 1000,
                retentionDays: 7
            };
        }
        // 添加通知配置
        if (!config.notifications) {
            config.notifications = {
                enabled: true,
                channels: ['console', 'file'],
                logLevel: 'info'
            };
        }
        return config;
    }
    /**
     * 回滚配置版本
     */
    async rollbackConfiguration(targetVersion) {
        try {
            // 查找目标版本的备份
            const targetBackup = this.configurationBackups.find(backup => backup.config.version === targetVersion);
            if (!targetBackup) {
                throw new Error(`未找到版本 ${targetVersion} 的配置备份`);
            }
            // 恢复目标版本的配置
            await this.restoreConfigurationBackup(targetBackup.id);
            this.logEvent('info', '配置版本回滚成功', {
                toVersion: targetVersion,
                backupId: targetBackup.id
            });
        }
        catch (error) {
            this.logEvent('error', '配置版本回滚失败', {
                targetVersion,
                error: error.toString()
            });
            throw error;
        }
    }
    /**
     * 创建配置备份
     */
    async createConfigurationBackup() {
        try {
            const backup = {
                id: `backup_${Date.now()}`,
                timestamp: new Date(),
                version: '1.0.0',
                config: this.config,
                description: '自动备份'
            };
            this.configurationBackups.push(backup);
            // 限制备份数量
            if (this.configurationBackups.length > this.configurationState.backupCount) {
                this.configurationBackups = this.configurationBackups.slice(-this.configurationState.backupCount);
            }
            // 保存备份到文件
            const backupPath = path.join(process.cwd(), 'config', 'backups', `${backup.id}.json`);
            await fs.mkdir(path.dirname(backupPath), { recursive: true });
            await fs.writeFile(backupPath, JSON.stringify(backup, null, 2), 'utf-8');
            this.logEvent('debug', '配置备份创建成功', { backupId: backup.id });
        }
        catch (error) {
            this.logEvent('error', '配置备份创建失败', { error: error.toString() });
        }
    }
    /**
     * 恢复配置备份
     */
    async restoreConfigurationBackup(backupId) {
        try {
            const backup = this.configurationBackups.find(b => b.id === backupId);
            if (!backup) {
                throw new Error(`备份不存在: ${backupId}`);
            }
            // 验证备份配置
            const validationResult = this.validateConfiguration(backup.config);
            if (!validationResult.isValid) {
                throw new Error(`备份配置无效: ${validationResult.errors.join(', ')}`);
            }
            // 创建当前配置的备份
            await this.createConfigurationBackup();
            // 恢复配置
            // 注意：这里需要将ConfigurationSchema转换为MainControllerConfig
            // 暂时跳过类型检查，实际使用时需要进行适当的类型转换
            this.config = backup.config;
            this.configurationState.isDirty = true;
            this.logEvent('info', '配置备份恢复成功', { backupId });
            this.emit('configurationRestored', { backupId });
            // 保存恢复的配置
            await this.saveConfiguration();
        }
        catch (error) {
            this.logEvent('error', '配置备份恢复失败', { backupId, error: error.toString() });
            throw error;
        }
    }
    /**
     * 启动配置自动保存
     */
    startAutoSave() {
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
        }
        this.autoSaveInterval = setInterval(async () => {
            if (this.configurationState.isDirty) {
                try {
                    await this.saveConfiguration();
                }
                catch (error) {
                    this.logEvent('error', '自动保存配置失败', { error: error.toString() });
                }
            }
        }, this.configurationState.autoSaveInterval);
        this.logEvent('debug', '配置自动保存已启动', { interval: this.configurationState.autoSaveInterval });
    }
    /**
     * 停止配置自动保存
     */
    stopAutoSave() {
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
            this.autoSaveInterval = undefined;
            this.logEvent('debug', '配置自动保存已停止');
        }
    }
    /**
     * 启动配置文件监听
     */
    startConfigurationWatcher() {
        try {
            const configPath = path.join(process.cwd(), 'config', 'main-controller.json');
            this.configWatcher = fs.watch(configPath, { encoding: 'utf8' });
            this.configWatcher.on('change', async (eventType, filename) => {
                this.logEvent('info', '检测到配置文件变化，重新加载配置');
                try {
                    await this.loadConfiguration();
                    this.emit('configurationReloaded');
                }
                catch (error) {
                    this.logEvent('error', '配置文件重新加载失败', { error: error.toString() });
                }
            });
            this.logEvent('debug', '配置文件监听已启动');
        }
        catch (error) {
            this.logEvent('error', '配置文件监听启动失败', { error: error.toString() });
        }
    }
    /**
     * 停止配置文件监听
     */
    stopConfigurationWatcher() {
        if (this.configWatcher) {
            this.configWatcher.close();
            this.configWatcher = undefined;
            this.logEvent('debug', '配置文件监听已停止');
        }
    }
    /**
     * 检查文件是否存在
     */
    async fileExists(filePath) {
        try {
            await fs.access(filePath);
            return true;
        }
        catch {
            return false;
        }
    }
    /**
     * 获取配置状态
     */
    getConfigurationState() {
        return { ...this.configurationState };
    }
    /**
     * 获取配置备份列表
     */
    getConfigurationBackups() {
        return [...this.configurationBackups];
    }
    /**
     * 停止配置管理
     */
    stopConfigurationManagement() {
        this.stopAutoSave();
        this.stopConfigurationWatcher();
        this.logEvent('info', '配置管理系统已停止');
    }
    /**
     * 保存配置到文件
     */
    async saveConfig() {
        try {
            await fs.mkdir(path.dirname(this.configFilePath), { recursive: true });
            await fs.writeFile(this.configFilePath, JSON.stringify(this.config, null, 2));
            this.log('debug', '配置已保存');
        }
        catch (error) {
            this.log('error', `保存配置失败: ${error}`);
        }
    }
    /**
     * 更新性能指标
     */
    updatePerformanceMetrics() {
        const memUsage = process.memoryUsage();
        this.performanceMetrics.memoryUsage = memUsage.heapUsed / 1024 / 1024; // MB
        this.performanceMetrics.uptime = (Date.now() - this.startTime.getTime()) / 1000; // 秒
        // 计算错误率
        if (this.performanceMetrics.uptime > 0) {
            this.performanceMetrics.errorRate = this.errorCount / (this.performanceMetrics.uptime / 60); // 每分钟错误数
        }
        this.emit('performanceUpdated', this.performanceMetrics);
    }
    /**
     * 启动健康检查
     */
    startHealthCheck() {
        this.healthCheckInterval = setInterval(() => {
            this.performHealthCheck();
        }, 30000); // 每30秒检查一次
    }
    /**
     * 执行健康检查
     */
    async performHealthCheck() {
        const issues = [];
        const recommendations = [];
        // 检查内存使用
        if (this.performanceMetrics.memoryUsage > 500) {
            issues.push('内存使用过高');
            recommendations.push('考虑重启应用程序');
        }
        // 检查错误率
        if (this.performanceMetrics.errorRate > 5) {
            issues.push('错误率过高');
            recommendations.push('检查系统配置和游戏状态');
        }
        // 检查游戏连接
        try {
            const gameStatus = await this.gameDetector.getCurrentStatus();
            if (!gameStatus.isRunning) {
                issues.push('游戏未运行');
                recommendations.push('启动游戏客户端');
            }
        }
        catch (error) {
            issues.push('无法检测游戏状态');
            recommendations.push('检查游戏检测器配置');
        }
        // 更新健康状态
        this.systemHealth = {
            status: issues.length === 0 ? 'healthy' : issues.length <= 2 ? 'warning' : 'critical',
            issues,
            recommendations,
            lastCheck: new Date()
        };
        this.emit('healthCheckCompleted', this.systemHealth);
    }
    /**
     * 启动任务
     */
    async startTask(taskType, accountId, config) {
        try {
            if (!this.isInitialized) {
                throw new Error('主控制器未初始化');
            }
            // 检查系统健康状态
            if (this.systemHealth.status === 'critical') {
                return {
                    success: false,
                    error: '系统状态异常，无法启动任务'
                };
            }
            // 检查游戏状态
            if (!this.currentGameStatus.isRunning) {
                this.logEvent('warn', '尝试启动任务但游戏未运行', { taskType, accountId });
                return {
                    success: false,
                    error: '游戏未运行，无法启动任务'
                };
            }
            // 安全模式检查
            if (this.config.safety.enableSafetyChecks) {
                const safetyCheck = await this.performSafetyCheck();
                if (!safetyCheck.safe) {
                    this.logEvent('warn', '安全检查失败', { reason: safetyCheck.reason, taskType });
                    return {
                        success: false,
                        error: `安全检查失败: ${safetyCheck.reason}`
                    };
                }
            }
            // 检查并发任务限制
            const runningTasks = this.taskExecutor.getRunningTasks();
            if (runningTasks.length >= this.config.maxConcurrentTasks) {
                return {
                    success: false,
                    error: `已达到最大并发任务数限制 (${this.config.maxConcurrentTasks})`
                };
            }
            // 创建任务
            const task = {
                accountId,
                taskType,
                config
            };
            const taskWithDefaults = {
                ...task,
                id: uuidv4(),
                status: 'pending',
                createdAt: new Date()
            };
            const taskId = this.taskExecutor.addTask(taskWithDefaults);
            // 保存任务到数据库
            const fullTask = {
                ...task,
                id: taskId,
                status: 'pending',
                createdAt: new Date()
            };
            await this.databaseService.createTask(fullTask);
            this.logEvent('info', '任务启动成功', { taskId, taskType, accountId });
            this.emit('taskStarted', { taskId, taskType, accountId });
            return {
                success: true,
                data: { taskId },
                message: '任务启动成功'
            };
        }
        catch (error) {
            this.errorCount++;
            this.lastErrorTime = new Date();
            this.logEvent('error', '启动任务失败', { error: error.toString(), taskType, accountId });
            return {
                success: false,
                error: error instanceof Error ? error.message : String(error)
            };
        }
    }
    /**
     * 停止任务
     */
    async stopTask(taskId) {
        try {
            // 获取任务信息用于日志记录
            const task = this.taskExecutor.getTaskById(taskId);
            const success = this.taskExecutor.stopTask(taskId);
            if (success) {
                // 更新数据库中的任务状态
                await this.databaseService.updateTask(taskId, {
                    status: 'cancelled',
                    endTime: new Date()
                });
                this.logEvent('info', '任务停止成功', {
                    taskId,
                    taskType: task?.taskType,
                    accountId: task?.accountId
                });
                this.emit('taskStopped', { taskId, reason: 'manual' });
                return {
                    success: true,
                    message: '任务停止成功',
                    data: null
                };
            }
            else {
                this.logEvent('warn', '尝试停止不存在的任务', { taskId });
                return {
                    success: false,
                    message: '任务不存在或已结束',
                    data: null
                };
            }
        }
        catch (error) {
            this.errorCount++;
            this.lastErrorTime = new Date();
            this.logEvent('error', '停止任务失败', {
                taskId,
                error: error.toString()
            });
            return {
                success: false,
                message: `停止任务失败: ${error}`,
                data: null
            };
        }
    }
    /**
     * 获取游戏状态
     */
    async getGameStatus() {
        try {
            const status = await this.gameDetector.getCurrentStatus();
            // 更新内部状态缓存
            this.currentGameStatus = status;
            return {
                success: true,
                message: '获取游戏状态成功',
                data: status
            };
        }
        catch (error) {
            this.errorCount++;
            this.lastErrorTime = new Date();
            this.logEvent('error', '获取游戏状态失败', { error: error.toString() });
            return {
                success: false,
                message: `获取游戏状态失败: ${error}`,
                data: null
            };
        }
    }
    /**
     * 获取运行中的任务
     */
    getRunningTasks() {
        return this.taskExecutor.getRunningTasks();
    }
    /**
     * 获取系统健康状态
     */
    getSystemHealth() {
        return this.systemHealth;
    }
    /**
     * 获取性能指标
     */
    getPerformanceMetrics() {
        return this.performanceMetrics;
    }
    /**
     * 获取事件日志
     */
    getEventLogs(limit = 100) {
        return this.eventLogs.slice(-limit);
    }
    /**
     * 更新配置
     */
    async updateConfig(newConfig) {
        try {
            this.config = { ...this.config, ...newConfig };
            if (this.config.configPersistence) {
                await this.saveConfig();
            }
            this.logEvent('info', '配置更新成功', { updatedFields: Object.keys(newConfig) });
            this.emit('configUpdated', this.config);
            return {
                success: true,
                message: '配置更新成功',
                data: null
            };
        }
        catch (error) {
            this.logEvent('error', '配置更新失败', { error: error.toString() });
            return {
                success: false,
                message: `配置更新失败: ${error}`,
                data: null
            };
        }
    }
    /**
     * 获取当前配置
     */
    getConfig() {
        return { ...this.config };
    }
    /**
     * 清理事件日志
     */
    clearEventLogs() {
        this.eventLogs = [];
        this.logEvent('info', '事件日志已清理');
    }
    /**
     * 重置错误计数
     */
    resetErrorCount() {
        this.errorCount = 0;
        this.lastErrorTime = null;
        this.logEvent('info', '错误计数已重置');
    }
    /**
     * 启动自动调度
     */
    startAutoScheduling() {
        if (!this.config.automation.enableAutoScheduling) {
            this.logEvent('warn', '自动调度功能已禁用');
            return;
        }
        if (this.automationState.isAutoSchedulingActive) {
            this.logEvent('warn', '自动调度已在运行中');
            return;
        }
        this.automationState.isAutoSchedulingActive = true;
        this.automationState.lastScheduleTime = new Date();
        // 启动自动调度定时器
        this.autoScheduleInterval = setInterval(() => {
            this.performAutoScheduling();
        }, 10000); // 每10秒检查一次
        // 启动智能暂停检查
        if (this.config.automation.smartPauseResume) {
            this.pauseCheckInterval = setInterval(() => {
                this.checkSmartPauseResume();
            }, 5000); // 每5秒检查一次
        }
        this.logEvent('info', '自动调度已启动');
        this.emit('autoSchedulingStarted');
    }
    /**
     * 停止自动调度
     */
    stopAutoScheduling() {
        this.automationState.isAutoSchedulingActive = false;
        if (this.autoScheduleInterval) {
            clearInterval(this.autoScheduleInterval);
            this.autoScheduleInterval = undefined;
        }
        if (this.pauseCheckInterval) {
            clearInterval(this.pauseCheckInterval);
            this.pauseCheckInterval = undefined;
        }
        this.logEvent('info', '自动调度已停止');
        this.emit('autoSchedulingStopped');
    }
    /**
     * 执行自动调度逻辑
     */
    async performAutoScheduling() {
        try {
            if (this.automationState.isPaused) {
                return;
            }
            // 检查系统健康状态
            if (this.systemHealth.status === 'critical') {
                this.logEvent('warn', '系统状态异常，暂停自动调度');
                return;
            }
            // 检查游戏状态
            const gameStatus = await this.gameDetector.getCurrentStatus();
            if (!gameStatus.isRunning) {
                return;
            }
            // 获取当前运行的任务
            const runningTasks = this.taskExecutor.getRunningTasks();
            const availableSlots = this.config.maxConcurrentTasks - runningTasks.length;
            if (availableSlots <= 0) {
                return;
            }
            // 负载均衡：根据系统性能调整任务数量
            if (this.config.automation.loadBalancing) {
                const adjustedSlots = this.calculateOptimalTaskSlots(availableSlots);
                if (adjustedSlots !== availableSlots) {
                    this.logEvent('info', '负载均衡调整任务槽位', {
                        original: availableSlots,
                        adjusted: adjustedSlots
                    });
                }
            }
            // 优先级调整
            if (this.config.automation.priorityAdjustment) {
                await this.adjustTaskPriorities();
            }
            this.automationState.lastScheduleTime = new Date();
        }
        catch (error) {
            this.logEvent('error', '自动调度执行失败', { error: error.toString() });
        }
    }
    /**
     * 智能暂停恢复检查
     */
    async checkSmartPauseResume() {
        try {
            const shouldPause = await this.shouldPauseAutomation();
            if (shouldPause && !this.automationState.isPaused) {
                this.pauseAutomation(shouldPause.reason);
            }
            else if (!shouldPause && this.automationState.isPaused) {
                this.resumeAutomation();
            }
        }
        catch (error) {
            this.logEvent('error', '智能暂停检查失败', { error: error.toString() });
        }
    }
    /**
     * 判断是否应该暂停自动化
     */
    async shouldPauseAutomation() {
        // 检查系统资源
        if (this.performanceMetrics.memoryUsage > 800) {
            return { reason: '内存使用过高' };
        }
        if (this.performanceMetrics.errorRate > 10) {
            return { reason: '错误率过高' };
        }
        // 检查游戏状态
        try {
            const gameStatus = await this.gameDetector.getCurrentStatus();
            if (!gameStatus.isRunning) {
                return { reason: '游戏未运行' };
            }
            if (!gameStatus.isActive) {
                return { reason: '游戏窗口不活跃' };
            }
        }
        catch (error) {
            return { reason: '无法检测游戏状态' };
        }
        return null;
    }
    /**
     * 暂停自动化
     */
    pauseAutomation(reason) {
        this.automationState.isPaused = true;
        this.automationState.pauseReason = reason;
        this.logEvent('info', '自动化已暂停', { reason });
        this.emit('automationPaused', { reason });
    }
    /**
     * 恢复自动化
     */
    resumeAutomation() {
        this.automationState.isPaused = false;
        this.automationState.pauseReason = undefined;
        this.logEvent('info', '自动化已恢复');
        this.emit('automationResumed');
    }
    /**
     * 计算最优任务槽位数
     */
    calculateOptimalTaskSlots(availableSlots) {
        // 基于系统性能调整
        let optimalSlots = availableSlots;
        // 内存使用率过高时减少任务数
        if (this.performanceMetrics.memoryUsage > 600) {
            optimalSlots = Math.max(1, Math.floor(optimalSlots * 0.7));
        }
        // 错误率高时减少任务数
        if (this.performanceMetrics.errorRate > 5) {
            optimalSlots = Math.max(1, Math.floor(optimalSlots * 0.8));
        }
        return optimalSlots;
    }
    /**
     * 调整任务优先级
     */
    async adjustTaskPriorities() {
        // 获取所有待执行任务
        const pendingTasks = this.taskExecutor.getPendingTasks();
        // 根据任务类型、账户状态等调整优先级
        for (const task of pendingTasks) {
            const newPriority = this.calculateTaskPriority(task);
            if (newPriority !== task.priority) {
                this.taskExecutor.updateTaskPriority(task.id, newPriority);
                this.logEvent('debug', '任务优先级已调整', {
                    taskId: task.id,
                    oldPriority: task.priority,
                    newPriority
                });
            }
        }
    }
    /**
     * 计算任务优先级
     */
    calculateTaskPriority(task) {
        // 基于任务类型的基础优先级
        let priority = TaskPriority.NORMAL;
        switch (task.taskType) {
            case 'daily':
                priority = TaskPriority.HIGH;
                break;
            case 'side':
                priority = TaskPriority.NORMAL;
                break;
            case 'event':
                priority = TaskPriority.HIGH;
                break;
            case 'side':
                priority = TaskPriority.LOW;
                break;
            default:
                priority = TaskPriority.NORMAL;
        }
        // 根据任务创建时间调整（越久的任务优先级越高）
        const taskAge = Date.now() - task.createdAt.getTime();
        if (taskAge > 3600000) { // 超过1小时
            priority = Math.min(priority + 1, TaskPriority.URGENT);
        }
        return priority;
    }
    /**
     * 获取自动化状态
     */
    getAutomationState() {
        return { ...this.automationState };
    }
    /**
     * 启动游戏状态监控
     */
    startGameMonitoring() {
        if (this.gameMonitoringState.isMonitoring) {
            this.logEvent('warn', '游戏监控已在运行中');
            return;
        }
        this.gameMonitoringState.isMonitoring = true;
        this.gameMonitoringState.lastConnectionTime = new Date();
        // 启动游戏状态检查定时器
        this.gameMonitorInterval = setInterval(() => {
            this.checkGameStatus();
        }, 2000); // 每2秒检查一次
        // 启动窗口状态检查定时器
        this.windowStateCheckInterval = setInterval(() => {
            this.checkWindowState();
        }, 1000); // 每1秒检查一次
        // 启动自动恢复检查定时器
        this.gameRecoveryInterval = setInterval(() => {
            this.checkAutoRecovery();
        }, 5000); // 每5秒检查一次
        this.logEvent('info', '游戏状态监控已启动');
        this.emit('gameMonitoringStarted');
    }
    /**
     * 停止游戏状态监控
     */
    stopGameMonitoring() {
        this.gameMonitoringState.isMonitoring = false;
        if (this.gameMonitorInterval) {
            clearInterval(this.gameMonitorInterval);
            this.gameMonitorInterval = undefined;
        }
        if (this.windowStateCheckInterval) {
            clearInterval(this.windowStateCheckInterval);
            this.windowStateCheckInterval = undefined;
        }
        if (this.gameRecoveryInterval) {
            clearInterval(this.gameRecoveryInterval);
            this.gameRecoveryInterval = undefined;
        }
        this.logEvent('info', '游戏状态监控已停止');
        this.emit('gameMonitoringStopped');
    }
    /**
     * 检查游戏状态
     */
    async checkGameStatus() {
        try {
            const currentStatus = await this.gameDetector.getCurrentStatus();
            const previousStatus = this.gameMonitoringState.lastGameStatus;
            // 记录状态快照
            const snapshot = {
                timestamp: new Date(),
                isRunning: currentStatus.isRunning,
                isActive: currentStatus.isActive,
                windowRect: currentStatus.windowInfo ? {
                    x: currentStatus.windowInfo.x || 0,
                    y: currentStatus.windowInfo.y || 0,
                    width: currentStatus.windowInfo.width || 0,
                    height: currentStatus.windowInfo.height || 0
                } : undefined,
                processId: currentStatus.isActive ? 1 : undefined
            };
            this.gameMonitoringState.gameStatusHistory.push(snapshot);
            // 保持历史记录在合理范围内（最多保留100条）
            if (this.gameMonitoringState.gameStatusHistory.length > 100) {
                this.gameMonitoringState.gameStatusHistory.shift();
            }
            // 检查状态变化
            if (previousStatus) {
                await this.handleGameStatusChange(previousStatus, currentStatus);
            }
            this.gameMonitoringState.lastGameStatus = currentStatus;
            // 更新连接状态
            if (currentStatus.isRunning) {
                this.gameMonitoringState.lastConnectionTime = new Date();
                this.gameMonitoringState.connectionLostCount = 0;
            }
            else {
                this.gameMonitoringState.connectionLostCount++;
            }
        }
        catch (error) {
            this.logEvent('error', '游戏状态检查失败', { error: error.toString() });
            this.gameMonitoringState.connectionLostCount++;
        }
    }
    /**
     * 处理游戏状态变化
     */
    async handleGameStatusChange(previousStatus, currentStatus) {
        // 游戏启动
        if (!previousStatus.isRunning && currentStatus.isRunning) {
            this.logEvent('info', '检测到游戏启动');
            this.emit('gameStarted', currentStatus);
            // 重置恢复尝试计数
            this.gameMonitoringState.autoRecoveryAttempts = 0;
            // 如果有暂停的任务，考虑恢复
            if (this.config.autoRecovery) {
                await this.resumePausedTasksOnGameStart();
            }
        }
        // 游戏关闭
        if (previousStatus.isRunning && !currentStatus.isRunning) {
            this.logEvent('warn', '检测到游戏关闭');
            this.emit('gameClosed', previousStatus);
            // 暂停所有运行中的任务
            await this.pauseAllTasksOnGameClose();
        }
        // 游戏窗口激活
        if (!previousStatus.isActive && currentStatus.isActive) {
            this.logEvent('info', '游戏窗口已激活');
            this.emit('gameWindowActivated', currentStatus);
        }
        // 游戏窗口失活
        if (previousStatus.isActive && !currentStatus.isActive) {
            this.logEvent('info', '游戏窗口已失活');
            this.emit('gameWindowDeactivated', currentStatus);
            // 根据配置决定是否暂停任务
            if (this.config.automation.smartPauseResume) {
                await this.handleWindowDeactivation();
            }
        }
    }
    /**
     * 检查窗口状态
     */
    async checkWindowState() {
        try {
            if (!this.gameMonitoringState.lastGameStatus?.isRunning) {
                return;
            }
            // 获取游戏窗口信息和活动状态
            const gameStatus = await this.gameDetector.getCurrentStatus();
            const isActive = gameStatus.isActive;
            const windowRect = gameStatus.windowInfo;
            // 检测窗口状态变化
            const lastChange = this.gameMonitoringState.windowStateChanges[this.gameMonitoringState.windowStateChanges.length - 1];
            const currentState = this.determineWindowState(isActive, windowRect);
            if (!lastChange || lastChange.currentState !== currentState) {
                const change = {
                    timestamp: new Date(),
                    previousState: lastChange?.currentState || 'inactive',
                    currentState,
                    duration: lastChange ? Date.now() - lastChange.timestamp.getTime() : 0
                };
                this.gameMonitoringState.windowStateChanges.push(change);
                // 保持历史记录在合理范围内
                if (this.gameMonitoringState.windowStateChanges.length > 50) {
                    this.gameMonitoringState.windowStateChanges.shift();
                }
                this.emit('windowStateChanged', change);
            }
        }
        catch (error) {
            this.logEvent('error', '窗口状态检查失败', { error: error.toString() });
        }
    }
    /**
     * 确定窗口状态
     */
    determineWindowState(isActive, windowRect) {
        if (!windowRect) {
            return 'closed';
        }
        if (windowRect.width <= 0 || windowRect.height <= 0) {
            return 'minimized';
        }
        return isActive ? 'active' : 'inactive';
    }
    /**
     * 检查自动恢复
     */
    async checkAutoRecovery() {
        if (!this.config.autoRecovery) {
            return;
        }
        try {
            // 检查是否需要恢复游戏连接
            if (this.gameMonitoringState.connectionLostCount > 3) {
                await this.attemptGameRecovery();
            }
            // 检查是否有长时间未响应的任务
            await this.checkStuckTasks();
        }
        catch (error) {
            this.logEvent('error', '自动恢复检查失败', { error: error.toString() });
        }
    }
    /**
     * 尝试游戏恢复
     */
    async attemptGameRecovery() {
        if (this.gameMonitoringState.autoRecoveryAttempts >= 3) {
            this.logEvent('warn', '游戏恢复尝试次数已达上限，停止自动恢复');
            return;
        }
        this.gameMonitoringState.autoRecoveryAttempts++;
        this.logEvent('info', `尝试游戏恢复 (第${this.gameMonitoringState.autoRecoveryAttempts}次)`);
        try {
            // 等待游戏启动
            const gameStarted = await this.gameDetector.waitForGameStart(30000); // 等待30秒
            if (gameStarted) {
                this.logEvent('info', '游戏恢复成功');
                this.gameMonitoringState.connectionLostCount = 0;
                this.gameMonitoringState.autoRecoveryAttempts = 0;
                this.emit('gameRecovered');
            }
            else {
                this.logEvent('warn', '游戏恢复失败，游戏未在指定时间内启动');
            }
        }
        catch (error) {
            this.logEvent('error', '游戏恢复过程中发生错误', { error: error.toString() });
        }
    }
    /**
     * 检查卡住的任务
     */
    async checkStuckTasks() {
        const runningTasks = this.taskExecutor.getRunningTasks();
        const now = Date.now();
        for (const task of runningTasks) {
            if (task.startTime) {
                const runningTime = now - task.startTime.getTime();
                // 如果任务运行超过30分钟，认为可能卡住了
                if (runningTime > 30 * 60 * 1000) {
                    this.logEvent('warn', '检测到可能卡住的任务', {
                        taskId: task.id,
                        runningTime: Math.floor(runningTime / 1000) + '秒'
                    });
                    // 尝试重启任务
                    if (this.config.autoRecovery) {
                        await this.restartStuckTask(task);
                    }
                }
            }
        }
    }
    /**
     * 重启卡住的任务
     */
    async restartStuckTask(task) {
        try {
            this.logEvent('info', '尝试重启卡住的任务', { taskId: task.id });
            // 停止当前任务
            this.taskExecutor.stopTask(task.id);
            // 重新添加任务
            await this.taskExecutor.addTask({
                id: uuidv4(),
                taskType: task.taskType,
                accountId: task.accountId,
                // 任务优先级通过TaskExecutor管理
                config: task.config,
                status: 'pending',
                createdAt: new Date()
            });
            this.logEvent('info', '任务重启成功', { taskId: task.id });
        }
        catch (error) {
            this.logEvent('error', '任务重启失败', {
                taskId: task.id,
                error: error.toString()
            });
        }
    }
    /**
     * 游戏启动时恢复暂停的任务
     */
    async resumePausedTasksOnGameStart() {
        const pausedTasks = this.taskExecutor.getPausedTasks();
        for (const task of pausedTasks) {
            // 检查任务状态，如果是因为游戏关闭而暂停
            if (task.status === 'paused') {
                this.logEvent('info', '游戏启动，恢复暂停的任务', { taskId: task.id });
                this.taskExecutor.resumeTask(task.id);
            }
        }
    }
    /**
     * 游戏关闭时暂停所有任务
     */
    async pauseAllTasksOnGameClose() {
        const runningTasks = this.taskExecutor.getRunningTasks();
        for (const task of runningTasks) {
            this.logEvent('info', '游戏关闭，暂停运行中的任务', { taskId: task.id });
            // 任务因游戏关闭而暂停
            this.taskExecutor.pauseTask(task.id);
        }
    }
    /**
     * 处理窗口失活
     */
    async handleWindowDeactivation() {
        // 检查失活时间
        const lastChange = this.gameMonitoringState.windowStateChanges[this.gameMonitoringState.windowStateChanges.length - 1];
        if (lastChange && lastChange.currentState === 'inactive') {
            const inactiveTime = Date.now() - lastChange.timestamp.getTime();
            // 如果失活超过5分钟，暂停任务
            if (inactiveTime > 5 * 60 * 1000) {
                const runningTasks = this.taskExecutor.getRunningTasks();
                for (const task of runningTasks) {
                    this.logEvent('info', '窗口长时间失活，暂停任务', { taskId: task.id });
                    // 任务因窗口非活动而暂停
                    this.taskExecutor.pauseTask(task.id);
                }
            }
        }
    }
    /**
     * 获取游戏监控状态
     */
    getGameMonitoringState() {
        return { ...this.gameMonitoringState };
    }
    /**
     * 获取游戏状态历史
     */
    getGameStatusHistory(limit = 50) {
        return this.gameMonitoringState.gameStatusHistory.slice(-limit);
    }
    /**
     * 获取窗口状态变化历史
     */
    getWindowStateHistory(limit = 20) {
        return this.gameMonitoringState.windowStateChanges.slice(-limit);
    }
    /**
     * 初始化恢复策略
     */
    initializeRecoveryStrategies() {
        // 任务重启策略
        this.exceptionHandlingState.recoveryStrategies.set('task_restart', {
            name: 'task_restart',
            description: '重启失败的任务',
            priority: 1,
            maxAttempts: 3,
            cooldownMs: 5000,
            execute: async (exception) => {
                return await this.executeTaskRestartStrategy(exception);
            }
        });
        // 游戏重连策略
        this.exceptionHandlingState.recoveryStrategies.set('game_reconnect', {
            name: 'game_reconnect',
            description: '重新连接游戏',
            priority: 2,
            maxAttempts: 5,
            cooldownMs: 10000,
            execute: async (exception) => {
                return await this.executeGameReconnectStrategy(exception);
            }
        });
        // 系统重置策略
        this.exceptionHandlingState.recoveryStrategies.set('system_reset', {
            name: 'system_reset',
            description: '重置系统状态',
            priority: 3,
            maxAttempts: 2,
            cooldownMs: 30000,
            execute: async (exception) => {
                return await this.executeSystemResetStrategy(exception);
            }
        });
        // 资源清理策略
        this.exceptionHandlingState.recoveryStrategies.set('resource_cleanup', {
            name: 'resource_cleanup',
            description: '清理系统资源',
            priority: 4,
            maxAttempts: 1,
            cooldownMs: 60000,
            execute: async (exception) => {
                return await this.executeResourceCleanupStrategy(exception);
            }
        });
    }
    /**
     * 启动异常处理系统
     */
    startExceptionHandling() {
        if (!this.exceptionHandlingState.isEnabled) {
            this.logEvent('warn', '异常处理系统已禁用');
            return;
        }
        // 启动恢复检查定时器
        this.recoveryCheckInterval = setInterval(() => {
            this.checkPendingRecoveries();
        }, 10000); // 每10秒检查一次
        // 启动系统稳定性检查定时器
        this.systemStabilityCheckInterval = setInterval(() => {
            this.checkSystemStability();
        }, 30000); // 每30秒检查一次
        this.logEvent('info', '异常处理系统已启动');
        this.emit('exceptionHandlingStarted');
    }
    /**
     * 停止异常处理系统
     */
    stopExceptionHandling() {
        this.exceptionHandlingState.isEnabled = false;
        if (this.recoveryCheckInterval) {
            clearInterval(this.recoveryCheckInterval);
            this.recoveryCheckInterval = undefined;
        }
        if (this.systemStabilityCheckInterval) {
            clearInterval(this.systemStabilityCheckInterval);
            this.systemStabilityCheckInterval = undefined;
        }
        this.logEvent('info', '异常处理系统已停止');
        this.emit('exceptionHandlingStopped');
    }
    /**
     * 记录异常
     */
    recordException(type, severity, message, source, details, error) {
        const exceptionId = uuidv4();
        const exception = {
            id: exceptionId,
            type,
            severity,
            message,
            details,
            timestamp: new Date(),
            source,
            stackTrace: error?.stack,
            recoveryAttempts: 0,
            maxRecoveryAttempts: this.getMaxRecoveryAttempts(severity),
            isRecovered: false
        };
        this.exceptionHandlingState.exceptions.push(exception);
        // 保持异常记录在合理范围内（最多保留1000条）
        if (this.exceptionHandlingState.exceptions.length > 1000) {
            this.exceptionHandlingState.exceptions.shift();
        }
        this.logEvent('error', `记录异常: ${message}`, {
            exceptionId,
            type,
            severity,
            source,
            details
        });
        // 触发异常事件
        this.emit('exceptionRecorded', exception);
        // 立即尝试恢复（如果是高严重性异常）
        if (severity === 'high' || severity === 'critical') {
            this.attemptRecovery(exception).catch(err => {
                this.logEvent('error', '立即恢复尝试失败', { error: err.toString() });
            });
        }
        return exceptionId;
    }
    /**
     * 获取最大恢复尝试次数
     */
    getMaxRecoveryAttempts(severity) {
        switch (severity) {
            case 'low': return 2;
            case 'medium': return 3;
            case 'high': return 5;
            case 'critical': return 10;
            default: return 3;
        }
    }
    /**
     * 尝试恢复异常
     */
    async attemptRecovery(exception) {
        if (exception.isRecovered || exception.recoveryAttempts >= exception.maxRecoveryAttempts) {
            return false;
        }
        exception.recoveryAttempts++;
        this.exceptionHandlingState.globalRecoveryAttempts++;
        this.exceptionHandlingState.lastRecoveryTime = new Date();
        this.logEvent('info', `开始恢复异常 (第${exception.recoveryAttempts}次尝试)`, {
            exceptionId: exception.id,
            type: exception.type,
            severity: exception.severity
        });
        // 根据异常类型选择恢复策略
        const strategies = this.selectRecoveryStrategies(exception);
        for (const strategy of strategies) {
            try {
                // 检查冷却时间
                if (await this.isStrategyCoolingDown(strategy)) {
                    continue;
                }
                this.logEvent('info', `执行恢复策略: ${strategy.name}`, {
                    exceptionId: exception.id,
                    strategy: strategy.name
                });
                const success = await strategy.execute(exception);
                if (success) {
                    exception.isRecovered = true;
                    exception.recoveryStrategy = strategy.name;
                    this.logEvent('info', '异常恢复成功', {
                        exceptionId: exception.id,
                        strategy: strategy.name,
                        attempts: exception.recoveryAttempts
                    });
                    this.emit('exceptionRecovered', exception);
                    return true;
                }
            }
            catch (error) {
                this.logEvent('error', `恢复策略执行失败: ${strategy.name}`, {
                    exceptionId: exception.id,
                    error: error.toString()
                });
            }
        }
        this.logEvent('warn', '异常恢复失败', {
            exceptionId: exception.id,
            attempts: exception.recoveryAttempts,
            maxAttempts: exception.maxRecoveryAttempts
        });
        return false;
    }
    /**
     * 选择恢复策略
     */
    selectRecoveryStrategies(exception) {
        const strategies = [];
        switch (exception.type) {
            case 'task_error':
                strategies.push(this.exceptionHandlingState.recoveryStrategies.get('task_restart'), this.exceptionHandlingState.recoveryStrategies.get('system_reset'));
                break;
            case 'game_error':
                strategies.push(this.exceptionHandlingState.recoveryStrategies.get('game_reconnect'), this.exceptionHandlingState.recoveryStrategies.get('system_reset'));
                break;
            case 'system_error':
                strategies.push(this.exceptionHandlingState.recoveryStrategies.get('system_reset'), this.exceptionHandlingState.recoveryStrategies.get('resource_cleanup'));
                break;
            case 'resource_error':
                strategies.push(this.exceptionHandlingState.recoveryStrategies.get('resource_cleanup'), this.exceptionHandlingState.recoveryStrategies.get('system_reset'));
                break;
            case 'network_error':
                strategies.push(this.exceptionHandlingState.recoveryStrategies.get('game_reconnect'));
                break;
        }
        // 按优先级排序
        return strategies.filter(s => s).sort((a, b) => a.priority - b.priority);
    }
    /**
     * 检查策略是否在冷却中
     */
    async isStrategyCoolingDown(strategy) {
        // 这里可以实现更复杂的冷却逻辑
        // 简单实现：检查最后执行时间
        return false; // 暂时不实现冷却
    }
    /**
     * 检查待恢复的异常
     */
    async checkPendingRecoveries() {
        const pendingExceptions = this.exceptionHandlingState.exceptions.filter(ex => !ex.isRecovered && ex.recoveryAttempts < ex.maxRecoveryAttempts);
        for (const exception of pendingExceptions) {
            // 只处理中等及以上严重性的异常
            if (exception.severity === 'medium' || exception.severity === 'high' || exception.severity === 'critical') {
                await this.attemptRecovery(exception);
            }
        }
    }
    /**
     * 检查系统稳定性
     */
    checkSystemStability() {
        const now = Date.now();
        const oneHourAgo = now - 60 * 60 * 1000;
        // 统计最近一小时的异常
        const recentExceptions = this.exceptionHandlingState.exceptions.filter(ex => ex.timestamp.getTime() > oneHourAgo);
        const criticalCount = recentExceptions.filter(ex => ex.severity === 'critical').length;
        const highCount = recentExceptions.filter(ex => ex.severity === 'high').length;
        const mediumCount = recentExceptions.filter(ex => ex.severity === 'medium').length;
        const lowCount = recentExceptions.filter(ex => ex.severity === 'low').length;
        let newStability = 'stable';
        if (criticalCount >= this.exceptionHandlingState.errorThresholds.criticalSeverity) {
            newStability = 'critical';
        }
        else if (highCount >= this.exceptionHandlingState.errorThresholds.highSeverity) {
            newStability = 'critical';
        }
        else if (mediumCount >= this.exceptionHandlingState.errorThresholds.mediumSeverity) {
            newStability = 'unstable';
        }
        else if (lowCount >= this.exceptionHandlingState.errorThresholds.lowSeverity) {
            newStability = 'unstable';
        }
        if (newStability !== this.exceptionHandlingState.systemStability) {
            const previousStability = this.exceptionHandlingState.systemStability;
            this.exceptionHandlingState.systemStability = newStability;
            this.logEvent('warn', '系统稳定性状态变化', {
                previous: previousStability,
                current: newStability,
                criticalCount,
                highCount,
                mediumCount,
                lowCount
            });
            this.emit('systemStabilityChanged', {
                previous: previousStability,
                current: newStability,
                statistics: { criticalCount, highCount, mediumCount, lowCount }
            });
            // 如果系统变为不稳定或危险状态，触发紧急处理
            if (newStability === 'critical') {
                this.handleCriticalSystemState();
            }
        }
    }
    /**
     * 处理系统危险状态
     */
    async handleCriticalSystemState() {
        this.logEvent('error', '系统进入危险状态，启动紧急处理程序');
        try {
            // 暂停所有非关键任务
            const runningTasks = this.taskExecutor.getRunningTasks();
            for (const task of runningTasks) {
                if (task.priority < 8) { // 只保留高优先级任务
                    this.taskExecutor.pauseTask(task.id);
                }
            }
            // 执行系统重置
            await this.executeSystemResetStrategy({
                id: 'critical_system_reset',
                type: 'system_error',
                severity: 'critical',
                message: '系统稳定性危险，执行紧急重置',
                timestamp: new Date(),
                source: 'system_stability_monitor',
                recoveryAttempts: 0,
                maxRecoveryAttempts: 1,
                isRecovered: false
            });
            this.emit('criticalSystemHandled');
        }
        catch (error) {
            this.logEvent('error', '紧急处理程序执行失败', { error: error.toString() });
        }
    }
    /**
     * 执行任务重启策略
     */
    async executeTaskRestartStrategy(exception) {
        try {
            this.logEvent('info', '执行任务重启策略', { exceptionId: exception.id });
            // 从异常详情中获取任务ID
            const taskId = exception.details?.taskId;
            if (!taskId) {
                this.logEvent('warn', '无法获取任务ID，跳过任务重启', { exceptionId: exception.id });
                return false;
            }
            // 获取任务信息
            const task = this.taskExecutor.getTaskById(taskId);
            if (!task) {
                this.logEvent('warn', '任务不存在，跳过重启', { taskId, exceptionId: exception.id });
                return false;
            }
            // 停止当前任务
            await this.taskExecutor.stopTask(taskId);
            // 等待一段时间
            await new Promise(resolve => setTimeout(resolve, 2000));
            // 重新添加任务到队列
            const newTaskId = await this.taskExecutor.addTask({
                ...task,
                id: uuidv4(), // 生成新的任务ID
                status: 'pending',
                startTime: undefined,
                endTime: undefined
                // error属性不存在于Task类型中，已移除
            });
            this.logEvent('info', '任务重启成功', {
                originalTaskId: taskId,
                newTaskId,
                exceptionId: exception.id
            });
            return true;
        }
        catch (error) {
            this.logEvent('error', '任务重启策略执行失败', {
                exceptionId: exception.id,
                error: error.toString()
            });
            return false;
        }
    }
    /**
     * 执行游戏重连策略
     */
    async executeGameReconnectStrategy(exception) {
        try {
            this.logEvent('info', '执行游戏重连策略', { exceptionId: exception.id });
            // 检查游戏检测器状态
            if (!this.gameDetector) {
                this.logEvent('warn', '游戏检测器未初始化，跳过重连', { exceptionId: exception.id });
                return false;
            }
            // 停止当前游戏监控
            this.stopGameMonitoring();
            // 等待一段时间
            await new Promise(resolve => setTimeout(resolve, 3000));
            // 重新初始化游戏检测器
            try {
                // GameDetector不需要初始化
            }
            catch (error) {
                this.logEvent('error', '游戏检测器重新初始化失败', {
                    exceptionId: exception.id,
                    error: error.toString()
                });
                return false;
            }
            // 重新启动游戏监控
            this.startGameMonitoring();
            // 检查游戏状态
            const gameStatus = await this.getGameStatus();
            if (gameStatus.data && gameStatus.data.isRunning) {
                this.logEvent('info', '游戏重连成功', {
                    exceptionId: exception.id,
                    gameStatus
                });
                return true;
            }
            else {
                this.logEvent('warn', '游戏重连后仍未检测到游戏运行', {
                    exceptionId: exception.id,
                    gameStatus
                });
                return false;
            }
        }
        catch (error) {
            this.logEvent('error', '游戏重连策略执行失败', {
                exceptionId: exception.id,
                error: error.toString()
            });
            return false;
        }
    }
    /**
     * 执行系统重置策略
     */
    async executeSystemResetStrategy(exception) {
        try {
            this.logEvent('info', '执行系统重置策略', { exceptionId: exception.id });
            // 暂停所有运行中的任务
            const runningTasks = this.taskExecutor.getRunningTasks();
            for (const task of runningTasks) {
                this.taskExecutor.pauseTask(task.id);
            }
            // 停止所有监控和自动化
            this.stopGameMonitoring();
            this.stopAutoScheduling();
            // 重置内部状态（使用现有的状态管理）
            this.gameMonitoringState.connectionLostCount = 0;
            this.gameMonitoringState.autoRecoveryAttempts = 0;
            this.exceptionHandlingState.globalRecoveryAttempts = 0;
            this.exceptionHandlingState.systemStability = 'stable';
            // 等待一段时间让系统稳定
            await new Promise(resolve => setTimeout(resolve, 5000));
            // 重新初始化各个模块
            try {
                if (this.gameDetector) {
                    // GameDetector不需要初始化
                }
                if (this.inputController) {
                    // InputController不需要初始化
                }
                if (this.imageRecognition) {
                    // ImageRecognition不需要初始化
                }
            }
            catch (error) {
                this.logEvent('error', '模块重新初始化失败', {
                    exceptionId: exception.id,
                    error: error.toString()
                });
                return false;
            }
            // 重新启动监控和自动化
            this.startGameMonitoring();
            if (this.config.automation.enableAutoScheduling) {
                this.startAutoScheduling();
            }
            // 恢复暂停的任务
            const pausedTasks = this.taskExecutor.getPausedTasks();
            for (const task of pausedTasks) {
                if (task.priority >= 5) { // 只恢复中等及以上优先级的任务
                    this.taskExecutor.resumeTask(task.id);
                }
            }
            this.logEvent('info', '系统重置完成', {
                exceptionId: exception.id,
                resumedTasks: pausedTasks.filter(t => t.priority >= 5).length
            });
            return true;
        }
        catch (error) {
            this.logEvent('error', '系统重置策略执行失败', {
                exceptionId: exception.id,
                error: error.toString()
            });
            return false;
        }
    }
    /**
     * 执行资源清理策略
     */
    async executeResourceCleanupStrategy(exception) {
        try {
            this.logEvent('info', '执行资源清理策略', { exceptionId: exception.id });
            // 清理已完成的任务
            this.taskExecutor.clearCompletedTasks();
            // 清理事件日志（保留最近1000条）
            if (this.eventLogs.length > 1000) {
                this.eventLogs = this.eventLogs.slice(-1000);
            }
            // 清理异常记录（保留最近500条）
            if (this.exceptionHandlingState.exceptions.length > 500) {
                this.exceptionHandlingState.exceptions = this.exceptionHandlingState.exceptions.slice(-500);
            }
            // 清理性能监控历史（保留最近100条）
            if (this.performanceMonitoringState.snapshots.length > 100) {
                this.performanceMonitoringState.snapshots = this.performanceMonitoringState.snapshots.slice(-100);
            }
            // 清理游戏状态历史（保留最近50条）
            if (this.gameMonitoringState.gameStatusHistory.length > 50) {
                this.gameMonitoringState.gameStatusHistory = this.gameMonitoringState.gameStatusHistory.slice(-50);
            }
            // 清理窗口状态变化历史（保留最近50条）
            if (this.gameMonitoringState.windowStateChanges.length > 50) {
                this.gameMonitoringState.windowStateChanges = this.gameMonitoringState.windowStateChanges.slice(-50);
            }
            // 强制垃圾回收（如果可用）
            if (global.gc) {
                global.gc();
            }
            this.logEvent('info', '资源清理完成', {
                exceptionId: exception.id,
                clearedItems: {
                    eventLogs: this.eventLogs.length,
                    exceptions: this.exceptionHandlingState.exceptions.length,
                    performanceHistory: this.performanceMonitoringState.snapshots.length,
                    gameStatusHistory: this.gameMonitoringState.gameStatusHistory.length,
                    windowStateHistory: this.gameMonitoringState.windowStateChanges.length
                }
            });
            return true;
        }
        catch (error) {
            this.logEvent('error', '资源清理策略执行失败', {
                exceptionId: exception.id,
                error: error.toString()
            });
            return false;
        }
    }
    /**
     * 获取异常处理状态
     */
    getExceptionHandlingState() {
        return { ...this.exceptionHandlingState };
    }
    /**
     * 获取异常列表
     */
    getExceptions(filter) {
        let exceptions = [...this.exceptionHandlingState.exceptions];
        if (filter) {
            if (filter.type) {
                exceptions = exceptions.filter(ex => ex.type === filter.type);
            }
            if (filter.severity) {
                exceptions = exceptions.filter(ex => ex.severity === filter.severity);
            }
            if (filter.isRecovered !== undefined) {
                exceptions = exceptions.filter(ex => ex.isRecovered === filter.isRecovered);
            }
            if (filter.limit) {
                exceptions = exceptions.slice(-filter.limit);
            }
        }
        return exceptions;
    }
    /**
     * 清理已恢复的异常
     */
    clearRecoveredExceptions() {
        const beforeCount = this.exceptionHandlingState.exceptions.length;
        this.exceptionHandlingState.exceptions = this.exceptionHandlingState.exceptions.filter(ex => !ex.isRecovered);
        const clearedCount = beforeCount - this.exceptionHandlingState.exceptions.length;
        this.logEvent('info', '清理已恢复的异常', { clearedCount });
        return clearedCount;
    }
    // ==================== 性能监控系统 ====================
    /**
     * 初始化优化操作
     */
    initializeOptimizationActions() {
        this.performanceMonitoringState.optimizationActions = [
            {
                id: 'task_throttling',
                type: 'task_throttling',
                description: '限制并发任务数量以减少系统负载',
                execute: async () => {
                    const currentMax = this.taskExecutor.getMaxConcurrentTasks();
                    const newMax = Math.max(1, Math.floor(currentMax * 0.7));
                    this.taskExecutor.setMaxConcurrentTasks(newMax);
                    this.logEvent('info', '执行任务限流优化', { oldMax: currentMax, newMax });
                    return true;
                },
                rollback: async () => {
                    this.taskExecutor.setMaxConcurrentTasks(this.config.maxConcurrentTasks);
                    this.logEvent('info', '回滚任务限流优化');
                    return true;
                },
                impact: 'medium',
                estimatedImprovement: 20
            },
            {
                id: 'memory_cleanup',
                type: 'memory_cleanup',
                description: '清理内存缓存和临时数据',
                execute: async () => {
                    // 清理已完成的任务
                    const clearedTasks = this.taskExecutor.clearCompletedTasks();
                    // 清理旧的性能快照
                    const oldSnapshotCount = this.performanceMonitoringState.snapshots.length;
                    this.performanceMonitoringState.snapshots = this.performanceMonitoringState.snapshots
                        .slice(-this.performanceMonitoringState.maxSnapshotHistory / 2);
                    // 清理旧的事件日志
                    const oldLogCount = this.eventLogs.length;
                    this.eventLogs = this.eventLogs.slice(-1000);
                    this.logEvent('info', '执行内存清理优化', {
                        clearedTasks,
                        clearedSnapshots: oldSnapshotCount - this.performanceMonitoringState.snapshots.length,
                        clearedLogs: oldLogCount - this.eventLogs.length
                    });
                    // 强制垃圾回收（如果可用）
                    if (global.gc) {
                        global.gc();
                    }
                    return true;
                },
                impact: 'low',
                estimatedImprovement: 15
            },
            {
                id: 'priority_adjustment',
                type: 'priority_adjustment',
                description: '调整任务优先级以优化执行顺序',
                execute: async () => {
                    const pendingTasks = this.taskExecutor.getPendingTasks();
                    let adjustedCount = 0;
                    for (const task of pendingTasks) {
                        // 降低低优先级任务的优先级
                        if (task.priority > 5) {
                            this.taskExecutor.updateTaskPriority(task.id, Math.min(10, task.priority + 1));
                            adjustedCount++;
                        }
                    }
                    this.logEvent('info', '执行优先级调整优化', { adjustedCount });
                    return adjustedCount > 0;
                },
                impact: 'low',
                estimatedImprovement: 10
            },
            {
                id: 'resource_reallocation',
                type: 'resource_reallocation',
                description: '重新分配系统资源以提高效率',
                execute: async () => {
                    // 暂停非关键任务
                    const runningTasks = this.taskExecutor.getRunningTasks();
                    let pausedCount = 0;
                    for (const task of runningTasks) {
                        if (task.priority > 7) {
                            this.taskExecutor.pauseTask(task.id);
                            pausedCount++;
                        }
                    }
                    this.logEvent('info', '执行资源重分配优化', { pausedCount });
                    return pausedCount > 0;
                },
                rollback: async () => {
                    // 恢复暂停的任务
                    const pausedTasks = this.taskExecutor.getPausedTasks();
                    let resumedCount = 0;
                    for (const task of pausedTasks) {
                        this.taskExecutor.resumeTask(task.id);
                        resumedCount++;
                    }
                    this.logEvent('info', '回滚资源重分配优化', { resumedCount });
                    return true;
                },
                impact: 'high',
                estimatedImprovement: 30
            }
        ];
    }
    /**
     * 启动性能监控
     */
    startPerformanceMonitoring() {
        if (this.performanceMonitoringState.isMonitoring) {
            return;
        }
        this.performanceMonitoringState.isMonitoring = true;
        // 启动性能数据收集
        this.performanceMonitorInterval = setInterval(() => {
            this.collectPerformanceSnapshot();
        }, this.performanceMonitoringState.monitoringInterval);
        // 启动优化检查
        this.optimizationCheckInterval = setInterval(() => {
            this.checkOptimizationNeeds();
        }, 30000); // 每30秒检查一次
        // 启动资源监控
        this.resourceMonitorInterval = setInterval(() => {
            this.monitorSystemResources();
        }, 10000); // 每10秒监控一次
        this.logEvent('info', '性能监控已启动');
    }
    /**
     * 停止性能监控
     */
    stopPerformanceMonitoring() {
        if (!this.performanceMonitoringState.isMonitoring) {
            return;
        }
        this.performanceMonitoringState.isMonitoring = false;
        if (this.performanceMonitorInterval) {
            clearInterval(this.performanceMonitorInterval);
            this.performanceMonitorInterval = undefined;
        }
        if (this.optimizationCheckInterval) {
            clearInterval(this.optimizationCheckInterval);
            this.optimizationCheckInterval = undefined;
        }
        if (this.resourceMonitorInterval) {
            clearInterval(this.resourceMonitorInterval);
            this.resourceMonitorInterval = undefined;
        }
        this.logEvent('info', '性能监控已停止');
    }
    /**
     * 收集性能快照
     */
    async collectPerformanceSnapshot() {
        try {
            const now = new Date();
            const uptime = now.getTime() - this.startTime.getTime();
            // 获取任务统计
            const taskStats = this.taskExecutor.getStats();
            const runningTasks = this.taskExecutor.getRunningTasks();
            // 计算平均执行时间
            const completedTasks = this.taskExecutor.getCompletedTasks();
            const avgExecutionTime = completedTasks.length > 0
                ? completedTasks.reduce((sum, task) => {
                    const duration = task.endTime && task.startTime
                        ? task.endTime.getTime() - task.startTime.getTime()
                        : 0;
                    return sum + duration;
                }, 0) / completedTasks.length
                : 0;
            // 获取系统资源信息
            const memoryUsage = process.memoryUsage();
            const cpuUsage = process.cpuUsage();
            // 计算错误率
            const totalTasks = taskStats.completed + taskStats.failed;
            const errorRate = totalTasks > 0 ? (taskStats.failed / totalTasks) * 100 : 0;
            const snapshot = {
                timestamp: now,
                cpu: {
                    usage: this.performanceMetrics.cpuUsage,
                    average: this.calculateAverageCpuUsage(),
                    peak: this.calculatePeakCpuUsage()
                },
                memory: {
                    used: memoryUsage.heapUsed,
                    total: memoryUsage.heapTotal,
                    percentage: (memoryUsage.heapUsed / memoryUsage.heapTotal) * 100,
                    peak: this.calculatePeakMemoryUsage()
                },
                tasks: {
                    total: taskStats.total,
                    running: taskStats.running,
                    completed: taskStats.completed,
                    failed: taskStats.failed,
                    averageExecutionTime: avgExecutionTime
                },
                system: {
                    uptime: uptime,
                    responseTime: this.performanceMetrics.gameDetectionLatency,
                    errorRate: errorRate,
                    throughput: this.calculateThroughput()
                }
            };
            // 添加快照到历史记录
            this.performanceMonitoringState.snapshots.push(snapshot);
            // 限制历史记录数量
            if (this.performanceMonitoringState.snapshots.length > this.performanceMonitoringState.maxSnapshotHistory) {
                this.performanceMonitoringState.snapshots = this.performanceMonitoringState.snapshots
                    .slice(-this.performanceMonitoringState.maxSnapshotHistory);
            }
            // 检查性能告警
            this.checkPerformanceAlerts(snapshot);
        }
        catch (error) {
            this.logEvent('error', '收集性能快照失败', { error: error.toString() });
        }
    }
    /**
     * 监控系统资源
     */
    async monitorSystemResources() {
        try {
            // 更新CPU使用率
            const cpuUsage = process.cpuUsage();
            this.performanceMetrics.cpuUsage = (cpuUsage.user + cpuUsage.system) / 1000000; // 转换为秒
            // 更新内存使用率
            const memoryUsage = process.memoryUsage();
            this.performanceMetrics.memoryUsage = (memoryUsage.heapUsed / memoryUsage.heapTotal) * 100;
            // 更新运行时间
            this.performanceMetrics.uptime = new Date().getTime() - this.startTime.getTime();
            // 检查资源使用是否超过阈值
            const thresholds = this.performanceMonitoringState.thresholds;
            if (this.performanceMetrics.cpuUsage > thresholds.cpu.critical) {
                this.createPerformanceAlert('critical', 'cpu', this.performanceMetrics.cpuUsage, thresholds.cpu.critical, 'CPU使用率过高');
            }
            else if (this.performanceMetrics.cpuUsage > thresholds.cpu.warning) {
                this.createPerformanceAlert('warning', 'cpu', this.performanceMetrics.cpuUsage, thresholds.cpu.warning, 'CPU使用率较高');
            }
            if (this.performanceMetrics.memoryUsage > thresholds.memory.critical) {
                this.createPerformanceAlert('critical', 'memory', this.performanceMetrics.memoryUsage, thresholds.memory.critical, '内存使用率过高');
            }
            else if (this.performanceMetrics.memoryUsage > thresholds.memory.warning) {
                this.createPerformanceAlert('warning', 'memory', this.performanceMetrics.memoryUsage, thresholds.memory.warning, '内存使用率较高');
            }
        }
        catch (error) {
            this.logEvent('error', '监控系统资源失败', { error: error.toString() });
        }
    }
    /**
     * 检查优化需求
     */
    async checkOptimizationNeeds() {
        if (!this.performanceMonitoringState.autoOptimizationEnabled) {
            return;
        }
        try {
            const criticalAlerts = this.performanceMonitoringState.alerts.filter(alert => alert.type === 'critical' && !alert.isResolved);
            if (criticalAlerts.length > 0) {
                this.logEvent('warn', '检测到严重性能问题，开始自动优化', { alertCount: criticalAlerts.length });
                await this.executeAutoOptimization(criticalAlerts);
            }
        }
        catch (error) {
            this.logEvent('error', '检查优化需求失败', { error: error.toString() });
        }
    }
    /**
     * 执行自动优化
     */
    async executeAutoOptimization(alerts) {
        const now = new Date();
        // 防止频繁优化
        if (this.performanceMonitoringState.lastOptimization &&
            now.getTime() - this.performanceMonitoringState.lastOptimization.getTime() < 60000) {
            return;
        }
        this.performanceMonitoringState.lastOptimization = now;
        // 根据告警类型选择优化操作
        const optimizationActions = [];
        for (const alert of alerts) {
            switch (alert.metric) {
                case 'cpu':
                    optimizationActions.push(...this.performanceMonitoringState.optimizationActions.filter(action => action.type === 'task_throttling' || action.type === 'resource_reallocation'));
                    break;
                case 'memory':
                    optimizationActions.push(...this.performanceMonitoringState.optimizationActions.filter(action => action.type === 'memory_cleanup'));
                    break;
                case 'responseTime':
                    optimizationActions.push(...this.performanceMonitoringState.optimizationActions.filter(action => action.type === 'priority_adjustment'));
                    break;
            }
        }
        // 去重并按影响程度排序
        const uniqueActions = Array.from(new Set(optimizationActions));
        uniqueActions.sort((a, b) => {
            const impactOrder = { high: 3, medium: 2, low: 1 };
            return impactOrder[b.impact] - impactOrder[a.impact];
        });
        // 执行优化操作
        for (const action of uniqueActions.slice(0, 2)) { // 最多执行2个优化操作
            try {
                const success = await action.execute();
                if (success) {
                    action.lastExecuted = now;
                    this.logEvent('info', '自动优化操作执行成功', {
                        actionId: action.id,
                        description: action.description
                    });
                }
            }
            catch (error) {
                this.logEvent('error', '自动优化操作执行失败', {
                    actionId: action.id,
                    error: error.toString()
                });
            }
        }
    }
    /**
     * 检查性能告警
     */
    checkPerformanceAlerts(snapshot) {
        const thresholds = this.performanceMonitoringState.thresholds;
        // 检查CPU告警
        if (snapshot.cpu.usage > thresholds.cpu.critical) {
            this.createPerformanceAlert('critical', 'cpu', snapshot.cpu.usage, thresholds.cpu.critical, 'CPU使用率达到临界值');
        }
        else if (snapshot.cpu.usage > thresholds.cpu.warning) {
            this.createPerformanceAlert('warning', 'cpu', snapshot.cpu.usage, thresholds.cpu.warning, 'CPU使用率较高');
        }
        // 检查内存告警
        if (snapshot.memory.percentage > thresholds.memory.critical) {
            this.createPerformanceAlert('critical', 'memory', snapshot.memory.percentage, thresholds.memory.critical, '内存使用率达到临界值');
        }
        else if (snapshot.memory.percentage > thresholds.memory.warning) {
            this.createPerformanceAlert('warning', 'memory', snapshot.memory.percentage, thresholds.memory.warning, '内存使用率较高');
        }
        // 检查响应时间告警
        if (snapshot.system.responseTime > thresholds.responseTime.critical) {
            this.createPerformanceAlert('critical', 'responseTime', snapshot.system.responseTime, thresholds.responseTime.critical, '系统响应时间过长');
        }
        else if (snapshot.system.responseTime > thresholds.responseTime.warning) {
            this.createPerformanceAlert('warning', 'responseTime', snapshot.system.responseTime, thresholds.responseTime.warning, '系统响应时间较长');
        }
        // 检查错误率告警
        if (snapshot.system.errorRate > thresholds.errorRate.critical) {
            this.createPerformanceAlert('critical', 'errorRate', snapshot.system.errorRate, thresholds.errorRate.critical, '错误率过高');
        }
        else if (snapshot.system.errorRate > thresholds.errorRate.warning) {
            this.createPerformanceAlert('warning', 'errorRate', snapshot.system.errorRate, thresholds.errorRate.warning, '错误率较高');
        }
        // 检查任务执行时间告警
        if (snapshot.tasks.averageExecutionTime > thresholds.taskExecutionTime.critical) {
            this.createPerformanceAlert('critical', 'taskExecutionTime', snapshot.tasks.averageExecutionTime, thresholds.taskExecutionTime.critical, '任务执行时间过长');
        }
        else if (snapshot.tasks.averageExecutionTime > thresholds.taskExecutionTime.warning) {
            this.createPerformanceAlert('warning', 'taskExecutionTime', snapshot.tasks.averageExecutionTime, thresholds.taskExecutionTime.warning, '任务执行时间较长');
        }
    }
    /**
     * 创建性能告警
     */
    createPerformanceAlert(type, metric, currentValue, threshold, message) {
        // 检查是否已存在相同的未解决告警
        const existingAlert = this.performanceMonitoringState.alerts.find(alert => alert.metric === metric && alert.type === type && !alert.isResolved);
        if (existingAlert) {
            // 更新现有告警
            existingAlert.currentValue = currentValue;
            existingAlert.lastOccurred = new Date();
            existingAlert.occurrenceCount++;
            return;
        }
        // 创建新告警
        const alert = {
            id: `perf_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            type,
            metric,
            message,
            value: currentValue,
            currentValue,
            threshold,
            timestamp: new Date(),
            lastOccurred: new Date(),
            isResolved: false,
            occurrenceCount: 1
        };
        this.performanceMonitoringState.alerts.push(alert);
        // 记录告警事件
        this.logEvent(type === 'critical' ? 'error' : 'warn', `性能告警: ${message}`, {
            alertId: alert.id,
            metric,
            currentValue,
            threshold
        });
        // 如果是严重告警，立即尝试优化
        if (type === 'critical' && this.performanceMonitoringState.autoOptimizationEnabled) {
            this.executeAutoOptimization([alert]).catch(error => {
                this.logEvent('error', '自动优化执行失败', { error: error.toString() });
            });
        }
    }
    /**
     * 计算平均CPU使用率
     */
    calculateAverageCpuUsage() {
        const snapshots = this.performanceMonitoringState.snapshots;
        if (snapshots.length === 0)
            return 0;
        const sum = snapshots.reduce((total, snapshot) => total + snapshot.cpu.usage, 0);
        return sum / snapshots.length;
    }
    /**
     * 计算峰值CPU使用率
     */
    calculatePeakCpuUsage() {
        const snapshots = this.performanceMonitoringState.snapshots;
        if (snapshots.length === 0)
            return 0;
        return Math.max(...snapshots.map(snapshot => snapshot.cpu.usage));
    }
    /**
     * 计算峰值内存使用量
     */
    calculatePeakMemoryUsage() {
        const snapshots = this.performanceMonitoringState.snapshots;
        if (snapshots.length === 0)
            return 0;
        return Math.max(...snapshots.map(snapshot => snapshot.memory.used));
    }
    /**
     * 计算系统吞吐量
     */
    calculateThroughput() {
        const snapshots = this.performanceMonitoringState.snapshots;
        if (snapshots.length < 2)
            return 0;
        const latest = snapshots[snapshots.length - 1];
        const previous = snapshots[snapshots.length - 2];
        const timeDiff = latest.timestamp.getTime() - previous.timestamp.getTime();
        const taskDiff = latest.tasks.completed - previous.tasks.completed;
        return timeDiff > 0 ? (taskDiff / timeDiff) * 1000 : 0; // 每秒完成的任务数
    }
    /**
     * 获取性能监控状态
     */
    getPerformanceMonitoringState() {
        return { ...this.performanceMonitoringState };
    }
    /**
     * 获取性能快照历史
     */
    getPerformanceSnapshots(limit) {
        const snapshots = this.performanceMonitoringState.snapshots;
        return limit ? snapshots.slice(-limit) : [...snapshots];
    }
    /**
     * 获取性能告警
     */
    getPerformanceAlerts(onlyUnresolved = false) {
        const alerts = this.performanceMonitoringState.alerts;
        return onlyUnresolved
            ? alerts.filter(alert => !alert.isResolved)
            : [...alerts];
    }
    /**
     * 解决性能告警
     */
    resolvePerformanceAlert(alertId) {
        const alert = this.performanceMonitoringState.alerts.find(a => a.id === alertId);
        if (alert) {
            alert.isResolved = true;
            alert.resolvedAt = new Date();
            this.logEvent('info', '性能告警已解决', { alertId });
            return true;
        }
        return false;
    }
    /**
     * 清理已解决的告警
     */
    clearResolvedAlerts() {
        const beforeCount = this.performanceMonitoringState.alerts.length;
        this.performanceMonitoringState.alerts = this.performanceMonitoringState.alerts
            .filter(alert => !alert.isResolved);
        const clearedCount = beforeCount - this.performanceMonitoringState.alerts.length;
        if (clearedCount > 0) {
            this.logEvent('info', '已清理已解决的性能告警', { clearedCount });
        }
        return clearedCount;
    }
    /**
     * 更新性能阈值
     */
    updatePerformanceThresholds(thresholds) {
        this.performanceMonitoringState.thresholds = {
            ...this.performanceMonitoringState.thresholds,
            ...thresholds
        };
        this.logEvent('info', '性能阈值已更新', { thresholds });
    }
    /**
     * 紧急停止所有任务
     */
    async emergencyStop() {
        try {
            this.logEvent('warn', '执行紧急停止', {
                runningTasks: this.taskExecutor.getRunningTasks().length
            });
            this.emit('emergencyStop', { timestamp: new Date() });
            // 停止所有运行中的任务
            const runningTasks = this.taskExecutor.getRunningTasks();
            for (const task of runningTasks) {
                this.taskExecutor.stopTask(task.id);
            }
            // 禁用输入控制
            this.inputController.setEnabled(false);
            // 停止性能监控
            if (this.monitoringInterval) {
                clearInterval(this.monitoringInterval);
                this.monitoringInterval = undefined;
            }
            // 停止健康检查
            if (this.healthCheckInterval) {
                clearInterval(this.healthCheckInterval);
                this.healthCheckInterval = undefined;
            }
            // 保存当前配置
            if (this.config.configPersistence) {
                await this.saveConfig();
            }
            this.logEvent('info', '紧急停止完成');
            return {
                success: true,
                message: '紧急停止成功',
                data: null
            };
        }
        catch (error) {
            this.errorCount++;
            this.lastErrorTime = new Date();
            this.logEvent('error', '紧急停止失败', { error: error.toString() });
            return {
                success: false,
                message: `紧急停止失败: ${error}`,
                data: null
            };
        }
    }
    /**
     * 设置游戏状态监听
     */
    setupGameStatusMonitoring() {
        setInterval(async () => {
            try {
                const status = await this.gameDetector.getCurrentStatus();
                const wasRunning = this.currentGameStatus.isRunning;
                this.currentGameStatus = status;
                // 如果游戏状态发生变化
                if (wasRunning !== status.isRunning) {
                    if (!status.isRunning) {
                        this.log('warn', '检测到游戏已关闭，停止所有任务');
                        await this.emergencyStop();
                    }
                    else {
                        this.log('info', '检测到游戏已启动');
                        this.inputController.setEnabled(true);
                    }
                }
            }
            catch (error) {
                this.log('error', `游戏状态监听失败: ${error}`);
            }
        }, this.config.gameDetection.interval);
    }
    /**
     * 执行安全检查
     */
    async performSafetyCheck() {
        try {
            // 检查游戏窗口是否在前台
            if (!this.currentGameStatus.windowInfo) {
                return { safe: false, reason: '无法获取游戏窗口信息' };
            }
            // 检查是否有其他任务正在运行
            const runningTasks = this.taskExecutor.getRunningTasks();
            if (runningTasks.length >= 3) {
                return { safe: false, reason: '同时运行的任务过多' };
            }
            // 检查系统资源
            // TODO: 添加更多安全检查
            return { safe: true };
        }
        catch (error) {
            return { safe: false, reason: `安全检查异常: ${error}` };
        }
    }
    /**
     * 日志记录
     */
    log(level, message) {
        const levels = { debug: 0, info: 1, warn: 2, error: 3 };
        const configLevel = levels[this.config.logLevel || 'info'];
        if (levels[level] >= configLevel) {
            const timestamp = new Date().toISOString();
            console.log(`[${timestamp}] [${level.toUpperCase()}] ${message}`);
        }
    }
    /**
     * 获取各个模块的实例
     */
    getModules() {
        return {
            gameDetector: this.gameDetector,
            taskExecutor: this.taskExecutor,
            imageRecognition: this.imageRecognition,
            inputController: this.inputController,
            databaseService: this.databaseService
        };
    }
    /**
     * 销毁控制器
     */
    async destroy() {
        try {
            this.logEvent('info', '正在销毁主控制器');
            // 停止自动调度
            this.stopAutoScheduling();
            // 停止游戏监控
            this.stopGameMonitoring();
            // 停止异常处理系统
            this.stopExceptionHandling();
            // 保存配置并清理配置管理
            await this.saveConfiguration();
            this.stopConfigurationManagement();
            // 停止事件系统
            this.stopEventSystem();
            // 停止所有任务
            this.taskExecutor.stopAllTasks();
            // 停止所有定时器
            if (this.gameStatusInterval) {
                clearInterval(this.gameStatusInterval);
                this.gameStatusInterval = null;
            }
            if (this.monitoringInterval) {
                clearInterval(this.monitoringInterval);
                this.monitoringInterval = null;
            }
            if (this.healthCheckInterval) {
                clearInterval(this.healthCheckInterval);
                this.healthCheckInterval = null;
            }
            // 保存最终配置
            if (this.config.configPersistence) {
                await this.saveConfig();
            }
            // 禁用输入控制器
            this.inputController.setEnabled(false);
            // 移除所有事件监听器
            this.removeAllListeners();
            this.logEvent('info', '主控制器已销毁');
            // 清理事件日志
            this.eventLogs = [];
        }
        catch (error) {
            this.logEvent('error', '销毁主控制器失败', { error: error.toString() });
            throw error;
        }
    }
    // ==================== 事件系统方法 ====================
    /**
     * 初始化事件系统
     */
    initializeEventSystem() {
        this.eventSubscriptions = new Map();
        this.notificationChannels = new Map();
        this.notificationRateLimits = new Map();
        this.eventQueue = [];
        this.eventHistory = {
            events: [],
            maxSize: 1000,
            retentionDays: 30,
            totalEvents: 0,
            lastCleanup: new Date()
        };
        this.eventSystemState = {
            subscriptions: [],
            eventHistory: this.eventHistory,
            notificationState: {
                channels: [],
                isEnabled: true,
                totalSent: 0,
                totalFailed: 0
            },
            isEnabled: true,
            totalEvents: 0,
            totalSubscriptions: 0,
            listeners: []
        };
        // 初始化默认通知渠道
        this.initializeDefaultNotificationChannels();
    }
    /**
     * 初始化默认通知渠道
     */
    initializeDefaultNotificationChannels() {
        // 控制台日志通道
        const consoleChannel = {
            id: 'console',
            name: '控制台日志',
            type: 'console',
            enabled: true,
            config: {
                logLevel: 'info'
            },
            filters: [],
            rateLimit: {
                maxCount: 100,
                windowMs: 60000,
                currentCount: 0,
                windowStart: new Date()
            }
        };
        // 文件日志通道
        const fileChannel = {
            id: 'file',
            name: '文件日志',
            type: 'file',
            enabled: true,
            config: {
                filePath: path.join(process.cwd(), 'logs', 'events.log'),
                fileFormat: 'json'
            },
            filters: [{
                    severity: 'medium'
                }],
            rateLimit: {
                maxCount: 1000,
                windowMs: 60000,
                currentCount: 0,
                windowStart: new Date()
            }
        };
        this.notificationChannels.set('console', consoleChannel);
        this.notificationChannels.set('file', fileChannel);
        this.eventSystemState.notificationState.channels = [consoleChannel, fileChannel];
    }
    /**
     * 启动事件系统
     */
    startEventSystem() {
        if (!this.eventSystemState.isEnabled) {
            return;
        }
        // 启动事件处理循环
        this.eventProcessingInterval = setInterval(() => {
            this.processEventQueue();
        }, 100); // 每100ms处理一次事件队列
        // 启动事件历史清理
        setInterval(() => {
            this.cleanupEventHistory();
        }, 3600000); // 每小时清理一次过期事件
        this.logEvent('info', '事件系统已启动');
    }
    /**
     * 停止事件系统
     */
    stopEventSystem() {
        if (this.eventProcessingInterval) {
            clearInterval(this.eventProcessingInterval);
            this.eventProcessingInterval = undefined;
        }
        // 处理剩余的事件队列
        this.processEventQueue();
        this.eventSystemState.isEnabled = false;
        this.logEvent('info', '事件系统已停止');
    }
    /**
     * 发布系统事件
     */
    publishEvent(type, data, options = {}) {
        const event = {
            id: uuidv4(),
            type,
            source: options.source || 'MainController',
            timestamp: new Date(),
            data,
            severity: options.severity || 'medium',
            category: options.category || 'system',
            tags: options.tags || [],
            metadata: options.metadata
        };
        // 添加到事件队列
        this.eventQueue.push(event);
        // 添加到事件历史
        this.eventHistory.events.push(event);
        // 限制历史记录大小
        if (this.eventHistory.events.length > this.eventHistory.maxSize) {
            this.eventHistory.events = this.eventHistory.events.slice(-this.eventHistory.maxSize);
        }
        this.eventSystemState.totalEvents++;
        return event.id;
    }
    /**
     * 订阅事件
     */
    subscribeToEvent(eventType, listener, options = {}) {
        const subscription = {
            id: uuidv4(),
            eventType,
            listener,
            priority: options.priority || 0,
            once: options.once || false,
            filter: options.filter,
            createdAt: new Date()
        };
        if (!this.eventSubscriptions.has(eventType)) {
            this.eventSubscriptions.set(eventType, []);
        }
        const subscriptions = this.eventSubscriptions.get(eventType);
        subscriptions.push(subscription);
        // 按优先级排序
        subscriptions.sort((a, b) => b.priority - a.priority);
        this.eventSystemState.subscriptions.push(subscription);
        this.eventSystemState.totalSubscriptions++;
        return subscription.id;
    }
    /**
     * 取消事件订阅
     */
    unsubscribeFromEvent(subscriptionId) {
        for (const [eventType, subscriptions] of this.eventSubscriptions.entries()) {
            const index = subscriptions.findIndex(sub => sub.id === subscriptionId);
            if (index !== -1) {
                subscriptions.splice(index, 1);
                // 从状态中移除
                const stateIndex = this.eventSystemState.subscriptions.findIndex(sub => sub.id === subscriptionId);
                if (stateIndex !== -1) {
                    this.eventSystemState.subscriptions.splice(stateIndex, 1);
                    this.eventSystemState.totalSubscriptions--;
                }
                return true;
            }
        }
        return false;
    }
    /**
     * 处理事件队列
     */
    async processEventQueue() {
        while (this.eventQueue.length > 0) {
            const event = this.eventQueue.shift();
            await this.processEvent(event);
        }
    }
    /**
     * 处理单个事件
     */
    async processEvent(event) {
        try {
            // 触发事件订阅者
            await this.triggerEventSubscriptions(event);
            // 发送通知
            await this.sendNotifications(event);
        }
        catch (error) {
            this.logEvent('error', '处理事件失败', {
                eventId: event.id,
                eventType: event.type,
                error: error.toString()
            });
        }
    }
    /**
     * 触发事件订阅者
     */
    async triggerEventSubscriptions(event) {
        const subscriptions = this.eventSubscriptions.get(event.type) || [];
        const toRemove = [];
        for (const subscription of subscriptions) {
            try {
                // 检查过滤器
                if (subscription.filter && !this.matchesFilter(event, subscription.filter)) {
                    continue;
                }
                // 执行监听器
                await subscription.listener.handler(event);
                // 如果是一次性订阅，标记为移除
                if (subscription.once) {
                    toRemove.push(subscription.id);
                }
            }
            catch (error) {
                this.logEvent('error', '事件监听器执行失败', {
                    subscriptionId: subscription.id,
                    eventType: event.type,
                    error: error.toString()
                });
            }
        }
        // 移除一次性订阅
        for (const id of toRemove) {
            this.unsubscribeFromEvent(id);
        }
    }
    /**
     * 检查事件是否匹配过滤器
     */
    matchesFilter(event, filter) {
        if (filter.source && event.source !== filter.source) {
            return false;
        }
        if (filter.severity && event.severity !== filter.severity) {
            return false;
        }
        if (filter.category && event.category !== filter.category) {
            return false;
        }
        if (filter.tags && filter.tags.length > 0) {
            const hasMatchingTag = filter.tags.some(tag => event.tags.includes(tag));
            if (!hasMatchingTag) {
                return false;
            }
        }
        return true;
    }
    /**
     * 发送通知
     */
    async sendNotifications(event) {
        for (const channel of this.notificationChannels.values()) {
            if (!channel.enabled) {
                continue;
            }
            // 检查过滤器
            if (channel.filters.length > 0) {
                const matches = channel.filters.some(filter => this.matchesFilter(event, filter));
                if (!matches) {
                    continue;
                }
            }
            // 检查频率限制
            if (!this.checkRateLimit(channel.id, channel.rateLimit)) {
                continue;
            }
            try {
                await this.sendNotificationToChannel(event, channel);
                this.eventSystemState.notificationState.totalSent++;
                this.eventSystemState.notificationState.lastNotification = new Date();
            }
            catch (error) {
                this.eventSystemState.notificationState.totalFailed++;
                this.logEvent('error', '发送通知失败', {
                    channelId: channel.id,
                    eventId: event.id,
                    error: error.toString()
                });
            }
        }
    }
    /**
     * 检查频率限制
     */
    checkRateLimit(channelId, rateLimit) {
        const now = new Date();
        const windowStart = rateLimit.windowStart;
        const windowMs = rateLimit.windowMs;
        // 检查是否需要重置窗口
        if (now.getTime() - windowStart.getTime() >= windowMs) {
            rateLimit.currentCount = 0;
            rateLimit.windowStart = now;
        }
        // 检查是否超过限制
        if (rateLimit.currentCount >= rateLimit.maxCount) {
            return false;
        }
        rateLimit.currentCount++;
        return true;
    }
    async sendNotificationToChannel(eventOrChannelId, channelOrMessage, eventData) {
        // 处理重载：如果第一个参数是字符串，则使用新的签名
        if (typeof eventOrChannelId === 'string') {
            const channelId = eventOrChannelId;
            const message = channelOrMessage;
            const event = eventData;
            const channel = this.notificationChannels.get(channelId);
            if (!channel) {
                this.logEvent('warn', '通知渠道不存在', { channelId });
                return;
            }
            // 将简单事件转换为SystemEvent格式
            const systemEvent = {
                id: event.data?.id || uuidv4(),
                type: event.type || 'notification',
                source: event.source || 'system',
                timestamp: new Date(event.timestamp) || new Date(),
                severity: event.severity || 'info',
                category: 'notification',
                tags: [],
                data: message,
                metadata: event.data || {}
            };
            return this.sendNotificationToChannel(systemEvent, channel);
        }
        // 原有的实现
        const event = eventOrChannelId;
        const channel = channelOrMessage;
        const message = this.formatNotificationMessage(event, channel);
        switch (channel.type) {
            case 'console':
                console.log(`[${event.severity.toUpperCase()}] ${message}`);
                break;
            case 'log':
                this.log(channel.config.logLevel || 'info', message);
                break;
            case 'file':
                await this.writeNotificationToFile(event, channel, message);
                break;
            case 'email':
                await this.sendEmailNotification(event, channel, message);
                break;
            case 'webhook':
                await this.sendWebhookNotification(event, channel, message);
                break;
            default:
                throw new Error(`不支持的通知渠道类型: ${channel.type}`);
        }
    }
    /**
     * 格式化通知消息
     */
    formatNotificationMessage(event, channel) {
        const timestamp = event.timestamp.toISOString();
        const data = typeof event.data === 'string' ? event.data : JSON.stringify(event.data);
        return `[${timestamp}] [${event.source}] [${event.type}] ${data}`;
    }
    /**
     * 写入文件通知
     */
    async writeNotificationToFile(event, channel, message) {
        const filePath = channel.config.filePath;
        const format = channel.config.fileFormat || 'text';
        // 确保目录存在
        const dir = path.dirname(filePath);
        await fs.mkdir(dir, { recursive: true });
        let content;
        if (format === 'json') {
            content = JSON.stringify(event) + '\n';
        }
        else if (format === 'csv') {
            content = `"${event.timestamp.toISOString()}","${event.source}","${event.type}","${event.severity}","${JSON.stringify(event.data).replace(/"/g, '""')}"\n`;
        }
        else {
            content = message + '\n';
        }
        await fs.appendFile(filePath, content, 'utf-8');
    }
    /**
     * 发送邮件通知
     */
    async sendEmailNotification(event, channel, message) {
        try {
            const config = channel.config;
            if (!config.smtpHost || !config.smtpPort || !config.recipients) {
                throw new Error('邮件配置不完整');
            }
            // 这里使用简单的邮件发送逻辑
            // 在实际项目中，应该集成 nodemailer 等邮件库
            const emailData = {
                from: config.smtpUser || 'system@example.com',
                to: config.recipients.join(','),
                subject: `系统通知 - ${event.type} [${event.severity.toUpperCase()}]`,
                text: message,
                html: `
          <div style="font-family: Arial, sans-serif;">
            <h3>系统事件通知</h3>
            <p><strong>事件类型:</strong> ${event.type}</p>
            <p><strong>严重程度:</strong> ${event.severity}</p>
            <p><strong>来源:</strong> ${event.source}</p>
            <p><strong>时间:</strong> ${event.timestamp.toLocaleString()}</p>
            <p><strong>详情:</strong></p>
            <pre>${JSON.stringify(event.data, null, 2)}</pre>
          </div>
        `
            };
            // 模拟邮件发送
            this.logEvent('info', '邮件通知已发送', {
                channelId: channel.id,
                recipients: config.recipients,
                subject: emailData.subject
            });
        }
        catch (error) {
            this.logEvent('error', '发送邮件通知失败', {
                channelId: channel.id,
                error: error.toString()
            });
            throw error;
        }
    }
    /**
     * 发送Webhook通知
     */
    async sendWebhookNotification(event, channel, message) {
        try {
            const config = channel.config;
            if (!config.webhookUrl) {
                throw new Error('Webhook URL未配置');
            }
            const payload = {
                event: {
                    id: event.id,
                    type: event.type,
                    source: event.source,
                    timestamp: event.timestamp.toISOString(),
                    severity: event.severity,
                    category: event.category,
                    tags: event.tags,
                    data: event.data,
                    metadata: event.metadata
                },
                message: message
            };
            const requestOptions = {
                method: config.webhookMethod || 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'User-Agent': 'MainController/1.0',
                    ...config.webhookHeaders
                },
                body: JSON.stringify(payload)
            };
            // 使用 fetch API 发送请求
            const response = await fetch(config.webhookUrl, requestOptions);
            if (!response.ok) {
                throw new Error(`Webhook请求失败: ${response.status} ${response.statusText}`);
            }
            this.logEvent('info', 'Webhook通知已发送', {
                channelId: channel.id,
                url: config.webhookUrl,
                method: requestOptions.method,
                status: response.status
            });
        }
        catch (error) {
            this.logEvent('error', '发送Webhook通知失败', {
                channelId: channel.id,
                error: error.toString()
            });
            throw error;
        }
    }
    /**
     * 清理过期事件历史
     */
    cleanupEventHistory() {
        const now = new Date();
        const retentionMs = this.eventHistory.retentionDays * 24 * 60 * 60 * 1000;
        this.eventHistory.events = this.eventHistory.events.filter(event => {
            return now.getTime() - event.timestamp.getTime() < retentionMs;
        });
    }
    /**
     * 添加通知渠道
     */
    addNotificationChannel(channel) {
        this.notificationChannels.set(channel.id, channel);
        this.eventSystemState.notificationState.channels.push(channel);
    }
    /**
     * 移除通知渠道
     */
    removeNotificationChannel(channelId) {
        const removed = this.notificationChannels.delete(channelId);
        if (removed) {
            const index = this.eventSystemState.notificationState.channels.findIndex(c => c.id === channelId);
            if (index !== -1) {
                this.eventSystemState.notificationState.channels.splice(index, 1);
            }
        }
        return removed;
    }
    /**
     * 获取事件系统状态
     */
    getEventSystemState() {
        return { ...this.eventSystemState };
    }
    /**
     * 获取事件历史
     */
    getEventHistory(filter) {
        let events = [...this.eventHistory.events];
        if (filter) {
            if (filter.eventType) {
                events = events.filter(e => e.type === filter.eventType);
            }
            if (filter.source) {
                events = events.filter(e => e.source === filter.source);
            }
            if (filter.severity) {
                events = events.filter(e => e.severity === filter.severity);
            }
            if (filter.startTime) {
                events = events.filter(e => e.timestamp >= filter.startTime);
            }
            if (filter.endTime) {
                events = events.filter(e => e.timestamp <= filter.endTime);
            }
            if (filter.limit) {
                events = events.slice(-filter.limit);
            }
        }
        return events;
    }
    /**
     * 重放事件
     */
    async replayEvents(eventIds) {
        for (const eventId of eventIds) {
            const event = this.eventHistory.events.find(e => e.id === eventId);
            if (event) {
                // 创建新的事件ID和时间戳
                const replayEvent = {
                    ...event,
                    id: uuidv4(),
                    timestamp: new Date(),
                    metadata: {
                        ...event.metadata,
                        isReplay: true,
                        originalEventId: eventId
                    }
                };
                this.eventQueue.push(replayEvent);
            }
        }
    }
    /**
     * 持久化事件历史
     */
    async persistEventHistory() {
        try {
            const eventHistoryPath = path.join(process.cwd(), 'data', 'event-history.json');
            // 确保目录存在
            await fs.mkdir(path.dirname(eventHistoryPath), { recursive: true });
            // 准备持久化数据
            const persistData = {
                events: this.eventHistory.events,
                totalEvents: this.eventHistory.totalEvents,
                retentionDays: this.eventHistory.retentionDays,
                lastCleanup: this.eventHistory.lastCleanup,
                savedAt: new Date().toISOString()
            };
            // 写入文件
            await fs.writeFile(eventHistoryPath, JSON.stringify(persistData, null, 2), 'utf-8');
            this.logEvent('debug', '事件历史已持久化', {
                eventCount: this.eventHistory.events.length,
                filePath: eventHistoryPath
            });
        }
        catch (error) {
            this.logEvent('error', '事件历史持久化失败', {
                error: error.toString()
            });
            throw error;
        }
    }
    /**
     * 加载事件历史
     */
    async loadEventHistory() {
        try {
            const eventHistoryPath = path.join(process.cwd(), 'data', 'event-history.json');
            // 检查文件是否存在
            if (!(await this.fileExists(eventHistoryPath))) {
                this.logEvent('info', '事件历史文件不存在，使用默认配置');
                return;
            }
            // 读取文件
            const fileContent = await fs.readFile(eventHistoryPath, 'utf-8');
            const persistData = JSON.parse(fileContent);
            // 恢复事件历史
            this.eventHistory.events = persistData.events.map((event) => ({
                ...event,
                timestamp: new Date(event.timestamp)
            }));
            this.eventHistory.totalEvents = persistData.totalEvents || this.eventHistory.events.length;
            this.eventHistory.retentionDays = persistData.retentionDays || 7;
            this.eventHistory.lastCleanup = persistData.lastCleanup ? new Date(persistData.lastCleanup) : new Date();
            // 清理过期事件
            this.cleanupEventHistory();
            this.logEvent('info', '事件历史加载成功', {
                eventCount: this.eventHistory.events.length,
                loadedFrom: eventHistoryPath
            });
        }
        catch (error) {
            this.logEvent('error', '事件历史加载失败', {
                error: error.toString()
            });
            // 不抛出错误，使用默认配置继续运行
        }
    }
    /**
     * 导出事件历史
     */
    async exportEventHistory(filePath, filter) {
        try {
            // 获取过滤后的事件
            const events = this.getEventHistory(filter);
            // 准备导出数据
            const exportData = {
                exportedAt: new Date().toISOString(),
                filter: filter || {},
                eventCount: events.length,
                events: events
            };
            // 确保目录存在
            await fs.mkdir(path.dirname(filePath), { recursive: true });
            // 写入文件
            await fs.writeFile(filePath, JSON.stringify(exportData, null, 2), 'utf-8');
            this.logEvent('info', '事件历史导出成功', {
                eventCount: events.length,
                filePath: filePath
            });
        }
        catch (error) {
            this.logEvent('error', '事件历史导出失败', {
                filePath,
                error: error.toString()
            });
            throw error;
        }
    }
    /**
     * 导入事件历史
     */
    async importEventHistory(filePath, mergeMode = 'merge') {
        try {
            // 检查文件是否存在
            if (!(await this.fileExists(filePath))) {
                throw new Error(`导入文件不存在: ${filePath}`);
            }
            // 读取文件
            const fileContent = await fs.readFile(filePath, 'utf-8');
            const importData = JSON.parse(fileContent);
            if (!importData.events || !Array.isArray(importData.events)) {
                throw new Error('导入文件格式无效：缺少events数组');
            }
            // 转换时间戳
            const importedEvents = importData.events.map((event) => ({
                ...event,
                timestamp: new Date(event.timestamp)
            }));
            // 根据合并模式处理事件
            if (mergeMode === 'replace') {
                this.eventHistory.events = importedEvents;
            }
            else {
                // 合并模式：去重并按时间排序
                const existingEventIds = new Set(this.eventHistory.events.map(e => e.id));
                const newEvents = importedEvents.filter(e => !existingEventIds.has(e.id));
                this.eventHistory.events = [...this.eventHistory.events, ...newEvents]
                    .sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
            }
            // 更新总事件数
            this.eventHistory.totalEvents = this.eventHistory.events.length;
            // 清理过期事件
            this.cleanupEventHistory();
            this.logEvent('info', '事件历史导入成功', {
                importedCount: importedEvents.length,
                currentCount: this.eventHistory.events.length,
                mergeMode: mergeMode
            });
        }
        catch (error) {
            this.logEvent('error', '事件历史导入失败', {
                filePath,
                error: error.toString()
            });
            throw error;
        }
    }
    /**
     * 获取事件统计信息
     */
    getEventStatistics(timeRange) {
        let events = this.eventHistory.events;
        // 应用时间范围过滤
        if (timeRange) {
            events = events.filter(e => e.timestamp >= timeRange.startTime && e.timestamp <= timeRange.endTime);
        }
        // 统计事件类型
        const eventsByType = {};
        const eventsBySeverity = {};
        const eventsBySource = {};
        events.forEach(event => {
            eventsByType[event.type] = (eventsByType[event.type] || 0) + 1;
            eventsBySeverity[event.severity] = (eventsBySeverity[event.severity] || 0) + 1;
            eventsBySource[event.source] = (eventsBySource[event.source] || 0) + 1;
        });
        // 计算平均每日事件数
        const daysDiff = timeRange
            ? Math.max(1, Math.ceil((timeRange.endTime.getTime() - timeRange.startTime.getTime()) / (24 * 60 * 60 * 1000)))
            : Math.max(1, Math.ceil((Date.now() - (events[0]?.timestamp.getTime() || Date.now())) / (24 * 60 * 60 * 1000)));
        const averageEventsPerDay = events.length / daysDiff;
        // 获取前5个事件源
        const topSources = Object.entries(eventsBySource)
            .map(([source, count]) => ({ source, count }))
            .sort((a, b) => b.count - a.count)
            .slice(0, 5);
        return {
            totalEvents: events.length,
            eventsByType,
            eventsBySeverity,
            eventsBySource,
            averageEventsPerDay,
            topSources
        };
    }
    /**
     * 动态添加事件监听器
     */
    addEventListenerDynamic(id, eventType, handler, options) {
        const listener = {
            id,
            eventType,
            handler,
            priority: options?.priority || 0,
            once: options?.once || false,
            filter: options?.filter,
            description: options?.description || `动态监听器: ${id}`,
            createdAt: new Date(),
            isActive: true
        };
        // 检查是否已存在相同ID的监听器
        const existingIndex = this.eventSystemState.listeners.findIndex(l => l.id === id);
        if (existingIndex !== -1) {
            this.eventSystemState.listeners[existingIndex] = listener;
            this.logEvent('info', '事件监听器已更新', { listenerId: id, eventType });
        }
        else {
            this.eventSystemState.listeners.push(listener);
            this.logEvent('info', '事件监听器已添加', { listenerId: id, eventType });
        }
        // 按优先级排序
        this.eventSystemState.listeners.sort((a, b) => b.priority - a.priority);
    }
    /**
     * 移除事件监听器
     */
    removeEventListener(listenerId) {
        const index = this.eventSystemState.listeners.findIndex(l => l.id === listenerId);
        if (index !== -1) {
            const listener = this.eventSystemState.listeners[index];
            this.eventSystemState.listeners.splice(index, 1);
            this.logEvent('info', '事件监听器已移除', {
                listenerId,
                eventType: listener.eventType
            });
            return true;
        }
        this.logEvent('warning', '事件监听器不存在', { listenerId });
        return false;
    }
    /**
     * 启用/禁用事件监听器
     */
    toggleEventListener(listenerId, isActive) {
        const listener = this.eventSystemState.listeners.find(l => l.id === listenerId);
        if (listener) {
            listener.isActive = isActive;
            this.logEvent('info', `事件监听器已${isActive ? '启用' : '禁用'}`, {
                listenerId,
                eventType: listener.eventType
            });
            return true;
        }
        this.logEvent('warning', '事件监听器不存在', { listenerId });
        return false;
    }
    /**
     * 获取事件监听器列表
     */
    getEventListeners(filter) {
        let listeners = this.eventSystemState.listeners;
        if (filter) {
            listeners = listeners.filter(listener => {
                if (filter.eventType && listener.eventType !== filter.eventType) {
                    return false;
                }
                if (filter.isActive !== undefined && listener.isActive !== filter.isActive) {
                    return false;
                }
                if (filter.priority !== undefined && listener.priority !== filter.priority) {
                    return false;
                }
                return true;
            });
        }
        return listeners;
    }
    /**
     * 清理无效的事件监听器
     */
    cleanupEventListeners() {
        const beforeCount = this.eventSystemState.listeners.length;
        // 移除已标记为一次性且已执行的监听器
        this.eventSystemState.listeners = this.eventSystemState.listeners.filter(listener => {
            // 这里可以添加更多清理逻辑
            return listener.isActive;
        });
        const afterCount = this.eventSystemState.listeners.length;
        const removedCount = beforeCount - afterCount;
        if (removedCount > 0) {
            this.logEvent('info', '事件监听器清理完成', {
                removedCount,
                remainingCount: afterCount
            });
        }
    }
    /**
     * 批量管理事件监听器
     */
    batchManageEventListeners(operations) {
        let success = 0;
        let failed = 0;
        const errors = [];
        for (const operation of operations) {
            try {
                switch (operation.action) {
                    case 'add':
                        if (operation.eventType && operation.handler) {
                            this.addEventListenerDynamic(operation.listenerId, operation.eventType, operation.handler, operation.options);
                            success++;
                        }
                        else {
                            throw new Error('添加监听器需要eventType和handler参数');
                        }
                        break;
                    case 'remove':
                        if (this.removeEventListener(operation.listenerId)) {
                            success++;
                        }
                        else {
                            throw new Error('监听器不存在');
                        }
                        break;
                    case 'toggle':
                        const isActive = operation.options?.isActive ?? true;
                        if (this.toggleEventListener(operation.listenerId, isActive)) {
                            success++;
                        }
                        else {
                            throw new Error('监听器不存在');
                        }
                        break;
                    default:
                        throw new Error(`未知操作类型: ${operation.action}`);
                }
            }
            catch (error) {
                failed++;
                errors.push(`${operation.action} ${operation.listenerId}: ${error.toString()}`);
            }
        }
        this.logEvent('info', '批量事件监听器操作完成', {
            totalOperations: operations.length,
            success,
            failed
        });
        return { success, failed, errors };
    }
    /**
     * 高级事件过滤器
     */
    createAdvancedEventFilter(config) {
        const rateLimitState = config.rateLimit ? {
            count: 0,
            windowStart: Date.now()
        } : null;
        return {
            id: `advanced_filter_${Date.now()}`,
            condition: (event) => {
                try {
                    // 检查事件类型
                    if (config.types && !config.types.includes(event.type)) {
                        return false;
                    }
                    // 检查严重程度
                    if (config.severities && !config.severities.includes(event.severity)) {
                        return false;
                    }
                    // 检查事件源
                    if (config.sources && !config.sources.includes(event.source)) {
                        return false;
                    }
                    // 检查时间范围
                    if (config.timeRange) {
                        const eventTime = new Date(event.timestamp);
                        if (eventTime < config.timeRange.start || eventTime > config.timeRange.end) {
                            return false;
                        }
                    }
                    // 检查自定义条件
                    if (config.customConditions) {
                        for (const condition of config.customConditions) {
                            if (!condition(event)) {
                                return false;
                            }
                        }
                    }
                    // 检查频率限制
                    if (config.rateLimit && rateLimitState) {
                        const now = Date.now();
                        const windowElapsed = now - rateLimitState.windowStart;
                        if (windowElapsed >= config.rateLimit.timeWindow) {
                            // 重置窗口
                            rateLimitState.count = 0;
                            rateLimitState.windowStart = now;
                        }
                        if (rateLimitState.count >= config.rateLimit.maxEvents) {
                            return false;
                        }
                        rateLimitState.count++;
                    }
                    return true;
                }
                catch (error) {
                    this.logEvent('error', '事件过滤器执行失败', {
                        filterId: 'advanced_filter',
                        error: error.toString()
                    });
                    return false;
                }
            }
        };
    }
    /**
     * 添加事件路由
     */
    addEventRoute(routeId, config) {
        this.eventRoutes.set(routeId, {
            condition: config.condition,
            handlers: config.handlers,
            priority: config.priority || 0,
            enabled: config.enabled !== false
        });
        this.logEvent('debug', '事件路由已添加', {
            routeId,
            priority: config.priority || 0,
            handlerCount: config.handlers.length
        });
    }
    /**
     * 移除事件路由
     */
    removeEventRoute(routeId) {
        const removed = this.eventRoutes.delete(routeId);
        if (removed) {
            this.logEvent('debug', '事件路由已移除', { routeId });
        }
        return removed;
    }
    /**
     * 启用/禁用事件路由
     */
    toggleEventRoute(routeId, enabled) {
        const route = this.eventRoutes.get(routeId);
        if (route) {
            route.enabled = enabled;
            this.logEvent('debug', '事件路由状态已更新', { routeId, enabled });
            return true;
        }
        return false;
    }
    /**
     * 处理事件路由
     */
    async processEventRouting(event) {
        try {
            // 获取匹配的路由并按优先级排序
            const matchingRoutes = Array.from(this.eventRoutes.entries())
                .filter(([_, route]) => route.enabled && route.condition(event))
                .sort(([_, a], [__, b]) => b.priority - a.priority);
            // 执行匹配的路由处理器
            for (const [routeId, route] of matchingRoutes) {
                try {
                    await Promise.all(route.handlers.map(handler => handler(event)));
                    this.logEvent('debug', '事件路由处理完成', {
                        routeId,
                        eventType: event.type
                    });
                }
                catch (error) {
                    this.logEvent('error', '事件路由处理失败', {
                        routeId,
                        eventType: event.type,
                        error: error.toString()
                    });
                }
            }
        }
        catch (error) {
            this.logEvent('error', '事件路由处理过程失败', {
                error: error.toString()
            });
        }
    }
    /**
     * 条件路由构建器
     */
    createConditionalRoute(config) {
        const routeId = `conditional_route_${config.name}_${Date.now()}`;
        // 构建条件函数
        const condition = (event) => {
            // 检查事件类型
            if (config.conditions.eventType) {
                const types = Array.isArray(config.conditions.eventType)
                    ? config.conditions.eventType
                    : [config.conditions.eventType];
                if (!types.includes(event.type)) {
                    return false;
                }
            }
            // 检查严重程度
            if (config.conditions.severity) {
                const severities = Array.isArray(config.conditions.severity)
                    ? config.conditions.severity
                    : [config.conditions.severity];
                if (!severities.includes(event.severity)) {
                    return false;
                }
            }
            // 检查事件源
            if (config.conditions.source) {
                const sources = Array.isArray(config.conditions.source)
                    ? config.conditions.source
                    : [config.conditions.source];
                if (!sources.includes(event.source)) {
                    return false;
                }
            }
            // 检查自定义条件
            if (config.conditions.customCondition) {
                if (!config.conditions.customCondition(event)) {
                    return false;
                }
            }
            return true;
        };
        // 构建处理器
        const handlers = [];
        // 通知处理器
        if (config.actions.notify) {
            handlers.push(async (event) => {
                const message = config.actions.notify.template
                    ? this.formatNotificationTemplate(config.actions.notify.template, event)
                    : `事件通知: ${event.type} - ${event.message}`;
                for (const channelId of config.actions.notify.channels) {
                    await this.sendNotificationToChannel(channelId, message, event);
                }
            });
        }
        // 日志处理器
        if (config.actions.log) {
            handlers.push(async (event) => {
                const message = config.actions.log.message || `路由日志: ${event.type}`;
                this.logEvent(config.actions.log.level, message, event);
            });
        }
        // 执行处理器
        if (config.actions.execute) {
            handlers.push(config.actions.execute);
        }
        // 转发处理器
        if (config.actions.forward) {
            handlers.push(async (event) => {
                const transformedEvent = config.actions.forward.transform
                    ? config.actions.forward.transform(event)
                    : event;
                // 这里可以实现转发到其他系统的逻辑
                this.logEvent('debug', '事件已转发', {
                    target: config.actions.forward.target,
                    originalEvent: event.type,
                    transformedEvent
                });
            });
        }
        // 添加路由
        this.addEventRoute(routeId, {
            condition,
            handlers,
            priority: config.priority || 0
        });
        this.logEvent('info', '条件路由已创建', {
            routeId,
            name: config.name,
            priority: config.priority || 0
        });
        return routeId;
    }
    /**
     * 格式化通知模板
     */
    formatNotificationTemplate(template, event) {
        return template
            .replace(/\{\{type\}\}/g, event.type || '')
            .replace(/\{\{severity\}\}/g, event.severity || '')
            .replace(/\{\{source\}\}/g, event.source || '')
            .replace(/\{\{message\}\}/g, event.message || '')
            .replace(/\{\{timestamp\}\}/g, event.timestamp ? new Date(event.timestamp).toLocaleString() : '')
            .replace(/\{\{data\}\}/g, event.data ? JSON.stringify(event.data) : '');
    }
    /**
     * 获取事件路由状态
     */
    getEventRoutingState() {
        const routeDetails = Array.from(this.eventRoutes.entries()).map(([id, route]) => ({
            id,
            priority: route.priority,
            enabled: route.enabled,
            handlerCount: route.handlers.length
        }));
        return {
            totalRoutes: this.eventRoutes.size,
            enabledRoutes: routeDetails.filter(r => r.enabled).length,
            routeDetails
        };
    }
}
export default MainController;
