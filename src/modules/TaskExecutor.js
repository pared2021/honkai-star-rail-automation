import { EventEmitter } from 'events';
import GameDetector from './GameDetector.js';
import InputController from './InputController.js';
import ImageRecognition from './ImageRecognition.js';
// 任务优先级枚举
export var TaskPriority;
(function (TaskPriority) {
    TaskPriority[TaskPriority["LOW"] = 1] = "LOW";
    TaskPriority[TaskPriority["NORMAL"] = 2] = "NORMAL";
    TaskPriority[TaskPriority["HIGH"] = 3] = "HIGH";
    TaskPriority[TaskPriority["URGENT"] = 4] = "URGENT";
})(TaskPriority || (TaskPriority = {}));
/**
 * 任务执行器类
 * 负责管理和执行各种类型的任务
 */
export class TaskExecutor extends EventEmitter {
    constructor(maxConcurrentTasks = 3) {
        super();
        Object.defineProperty(this, "tasks", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: new Map()
        });
        Object.defineProperty(this, "runningTasks", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: new Set()
        });
        Object.defineProperty(this, "taskQueue", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: []
        });
        Object.defineProperty(this, "isProcessing", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: false
        });
        Object.defineProperty(this, "maxConcurrentTasks", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: 3
        });
        Object.defineProperty(this, "taskLogs", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: new Map()
        });
        Object.defineProperty(this, "stats", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: {
                totalTasks: 0,
                completedTasks: 0,
                failedTasks: 0,
                totalExecutionTime: 0,
                averageExecutionTime: 0,
                total: 0,
                running: 0,
                completed: 0,
                failed: 0
            }
        });
        // 核心模块实例
        Object.defineProperty(this, "gameDetector", {
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
        Object.defineProperty(this, "imageRecognition", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        this.maxConcurrentTasks = maxConcurrentTasks;
        // 初始化核心模块
        this.gameDetector = new GameDetector();
        this.inputController = new InputController();
        this.imageRecognition = new ImageRecognition();
        // 设置模块间的关联
        this.setupModuleIntegration();
    }
    /**
     * 设置模块间的集成
     */
    setupModuleIntegration() {
        // 当检测到游戏时，更新输入控制器的游戏窗口信息
        this.gameDetector.on('gameDetected', (gameInfo) => {
            this.inputController.setGameWindow(gameInfo.windowInfo);
            this.imageRecognition.setGameWindowBounds(gameInfo.windowInfo);
        });
        // 当游戏窗口变化时，更新相关模块
        this.gameDetector.on('windowChanged', (windowInfo) => {
            this.inputController.setGameWindow(windowInfo);
            this.imageRecognition.setGameWindowBounds(windowInfo);
        });
    }
    /**
     * 添加任务到执行队列
     */
    addTask(task, priority = TaskPriority.NORMAL) {
        const extendedTask = {
            ...task,
            priority,
            retryCount: 0,
            maxRetries: 3,
            timeout: 300000, // 5分钟超时
            dependencies: []
        };
        this.tasks.set(task.id, extendedTask);
        this.taskQueue.push(extendedTask);
        this.stats.totalTasks++;
        // 按优先级排序
        this.taskQueue.sort((a, b) => b.priority - a.priority);
        this.logTask(task.id, 'info', `任务已添加到队列，优先级: ${TaskPriority[priority]}`);
        this.emit('taskAdded', extendedTask);
        // 开始处理队列
        this.processQueue();
        return task.id;
    }
    /**
     * 处理任务队列
     */
    async processQueue() {
        if (this.isProcessing || this.taskQueue.length === 0) {
            return;
        }
        this.isProcessing = true;
        while (this.taskQueue.length > 0 && this.runningTasks.size < this.maxConcurrentTasks) {
            const task = this.taskQueue.shift();
            if (!task)
                break;
            // 检查依赖任务是否完成
            if (this.hasPendingDependencies(task)) {
                this.taskQueue.push(task); // 重新加入队列末尾
                continue;
            }
            this.runningTasks.add(task.id);
            this.executeTaskWithTimeout(task).catch(error => {
                this.logTask(task.id, 'error', `任务执行异常: ${error.message}`);
            });
        }
        this.isProcessing = false;
    }
    /**
     * 检查任务是否有未完成的依赖
     */
    hasPendingDependencies(task) {
        return task.dependencies.some(depId => {
            const depTask = this.tasks.get(depId);
            return depTask && depTask.status !== 'completed';
        });
    }
    /**
     * 带超时的任务执行
     */
    async executeTaskWithTimeout(task) {
        const timeoutPromise = new Promise((_, reject) => {
            setTimeout(() => reject(new Error('任务执行超时')), task.timeout);
        });
        try {
            await Promise.race([
                this.executeTask(task),
                timeoutPromise
            ]);
        }
        catch (error) {
            await this.handleTaskFailure(task, error);
        }
        finally {
            this.runningTasks.delete(task.id);
            this.processQueue(); // 继续处理队列
        }
    }
    /**
     * 执行单个任务
     */
    async executeTask(task) {
        this.logTask(task.id, 'info', `开始执行任务: ${task.taskType}`);
        // 更新任务状态
        task.status = 'running';
        task.startTime = new Date();
        this.emit('taskStarted', task);
        try {
            let result;
            // 根据任务类型执行不同的逻辑
            switch (task.taskType) {
                case 'daily':
                    result = await this.executeDailyTask(task);
                    break;
                case 'main':
                    result = await this.executeMainTask(task);
                    break;
                case 'side':
                    result = await this.executeSideTask(task);
                    break;
                case 'custom':
                    result = await this.executeCustomTask(task);
                    break;
                case 'event':
                    result = await this.executeEventTask(task);
                    break;
                default:
                    throw new Error(`不支持的任务类型: ${task.taskType}`);
            }
            // 任务执行成功
            task.status = 'completed';
            task.endTime = new Date();
            task.result = result;
            this.stats.completedTasks++;
            this.updateAverageExecutionTime();
            this.logTask(task.id, 'info', '任务执行完成');
            this.emit('taskCompleted', task, result);
        }
        catch (error) {
            throw error; // 重新抛出错误，由 executeTaskWithTimeout 处理
        }
    }
    /**
     * 处理任务失败
     */
    async handleTaskFailure(task, error) {
        task.retryCount++;
        this.logTask(task.id, 'error', `任务执行失败 (重试 ${task.retryCount}/${task.maxRetries}): ${error.message}`);
        if (task.retryCount < task.maxRetries) {
            // 重新加入队列进行重试
            task.status = 'pending';
            this.taskQueue.unshift(task); // 加入队列前端，优先重试
            this.logTask(task.id, 'info', `任务将在 ${task.retryCount * 1000}ms 后重试`);
            // 延迟重试
            setTimeout(() => {
                this.processQueue();
            }, task.retryCount * 1000);
        }
        else {
            // 重试次数用尽，标记为失败
            task.status = 'failed';
            task.endTime = new Date();
            task.result = {
                success: false,
                errors: [error.message]
            };
            this.stats.failedTasks++;
            this.logTask(task.id, 'error', '任务最终执行失败');
            this.emit('taskFailed', task, error);
        }
    }
    /**
     * 执行日常任务
     */
    async executeDailyTask(task) {
        this.logTask(task.id, 'info', '开始执行日常任务');
        const startTime = Date.now();
        const steps = [];
        try {
            // 1. 检查游戏是否运行
            steps.push('检查游戏状态');
            this.logTask(task.id, 'info', '检查游戏是否运行...');
            const isGameRunning = await this.gameDetector.isGameRunning();
            if (!isGameRunning) {
                throw new Error('游戏未运行，请先启动游戏');
            }
            // 2. 等待游戏窗口激活
            steps.push('激活游戏窗口');
            this.logTask(task.id, 'info', '等待游戏窗口激活...');
            await this.gameDetector.waitForGameActivation(5000);
            // 3. 截图检查游戏界面
            steps.push('检查游戏界面');
            this.logTask(task.id, 'info', '检查当前游戏界面...');
            const screenshot = await this.imageRecognition.captureGameWindow();
            if (!screenshot) {
                throw new Error('无法获取游戏截图');
            }
            // 4. 执行具体的日常任务步骤
            if (task.config && 'steps' in task.config && Array.isArray(task.config.steps)) {
                for (const step of task.config.steps) {
                    await this.executeTaskStep(task.id, step, steps);
                }
            }
            else {
                // 默认日常委托流程
                await this.executeDefaultDailyQuest(task.id, steps);
            }
            const duration = Date.now() - startTime;
            this.stats.completedTasks++;
            this.stats.totalExecutionTime += duration;
            return {
                success: true,
                data: {
                    steps,
                    duration,
                    rewards: (task.config && 'expectedRewards' in task.config && Array.isArray(task.config.expectedRewards)) ? task.config.expectedRewards : []
                }
            };
        }
        catch (error) {
            throw new Error(`日常任务执行失败: ${error instanceof Error ? error.message : String(error)}`);
        }
    }
    /**
     * 执行默认的日常委托流程
     */
    async executeDefaultDailyQuest(taskId, steps) {
        // 1. 寻找并点击委托按钮
        steps.push('寻找委托入口');
        this.logTask(taskId, 'info', '寻找委托入口...');
        // 尝试寻找委托按钮（这里需要实际的模板图片）
        const commissionButton = await this.imageRecognition.findImage('templates/commission_button.png');
        if (commissionButton.found && commissionButton.location) {
            await this.inputController.click(commissionButton.location.x, commissionButton.location.y);
            await this.delay(2000);
        }
        else {
            // 如果找不到委托按钮，尝试使用快捷键
            this.logTask(taskId, 'info', '使用快捷键打开委托界面...');
            await this.inputController.pressKey('f4'); // 假设F4是委托快捷键
            await this.delay(2000);
        }
        // 2. 接取所有可用委托
        steps.push('接取委托任务');
        this.logTask(taskId, 'info', '接取所有可用委托...');
        // 寻找"接取全部"按钮
        const acceptAllButton = await this.imageRecognition.findImage('templates/accept_all_button.png');
        if (acceptAllButton.found && acceptAllButton.location) {
            await this.inputController.click(acceptAllButton.location.x, acceptAllButton.location.y);
            await this.delay(1000);
        }
        // 3. 执行委托任务
        steps.push('执行委托任务');
        this.logTask(taskId, 'info', '开始执行委托任务...');
        // 寻找"立即完成"或"开始"按钮
        const startButton = await this.imageRecognition.findImage('templates/start_commission.png');
        if (startButton.found && startButton.location) {
            await this.inputController.click(startButton.location.x, startButton.location.y);
            await this.delay(3000); // 等待任务执行
        }
        // 4. 领取奖励
        steps.push('领取奖励');
        this.logTask(taskId, 'info', '领取委托奖励...');
        // 寻找"领取奖励"按钮
        const claimButton = await this.imageRecognition.findImage('templates/claim_reward.png');
        if (claimButton.found && claimButton.location) {
            await this.inputController.click(claimButton.location.x, claimButton.location.y);
            await this.delay(1000);
        }
        // 5. 关闭委托界面
        steps.push('关闭界面');
        await this.inputController.pressKey('Escape');
        await this.delay(500);
    }
    /**
     * 执行任务步骤
     */
    async executeTaskStep(taskId, step, steps) {
        steps.push(`执行步骤: ${step.name}`);
        this.logTask(taskId, 'info', `执行步骤: ${step.name}`);
        switch (step.action) {
            case 'click':
                if (step.template) {
                    // 基于图像识别的点击
                    const result = await this.imageRecognition.findImage(step.template);
                    if (result.found && result.location) {
                        await this.inputController.click(result.location.x, result.location.y);
                    }
                    else {
                        throw new Error(`找不到模板图像: ${step.template}`);
                    }
                }
                else if (step.coordinates) {
                    // 基于坐标的点击
                    await this.inputController.click(step.coordinates.x, step.coordinates.y);
                }
                break;
            case 'key':
                if (step.key) {
                    await this.inputController.pressKey(step.key);
                }
                break;
            case 'wait':
                await this.delay(step.duration || 1000);
                break;
            case 'waitForImage':
                if (step.template) {
                    await this.imageRecognition.waitForImage(step.template, step.timeout || 10000);
                }
                break;
            default:
                this.logTask(taskId, 'warn', `未知的步骤类型: ${step.action}`);
                await this.delay(step.duration || 1000);
        }
        // 步骤间延迟
        if (step.delay) {
            await this.delay(step.delay);
        }
    }
    /**
     * 执行主线任务
     */
    async executeMainTask(task) {
        this.logTask(task.id, 'info', '开始执行主线任务');
        const startTime = Date.now();
        const steps = [];
        try {
            // 检查任务前置条件
            steps.push('检查任务前置条件');
            await this.delay(500);
            // 执行主线任务步骤
            if (task.config && 'steps' in task.config && Array.isArray(task.config.steps)) {
                for (const step of task.config.steps) {
                    steps.push(`执行步骤: ${step.name}`);
                    this.logTask(task.id, 'info', `执行步骤: ${step.name}`);
                    await this.delay(step.duration || 2000);
                }
            }
            else {
                // 默认主线任务流程
                steps.push('进入任务场景');
                await this.delay(1500);
                steps.push('执行任务目标');
                await this.delay(3000);
                steps.push('完成任务对话');
                await this.delay(1000);
            }
            const duration = Date.now() - startTime;
            this.stats.completedTasks++;
            this.stats.totalExecutionTime += duration;
            return {
                success: true,
                data: {
                    steps,
                    duration,
                    experience: (task.config && 'expectedExperience' in task.config && typeof task.config.expectedExperience === 'number') ? task.config.expectedExperience : 0
                }
            };
        }
        catch (error) {
            throw new Error(`主线任务执行失败: ${error instanceof Error ? error.message : String(error)}`);
        }
    }
    /**
     * 执行支线任务
     */
    async executeSideTask(task) {
        this.logTask(task.id, 'info', '开始执行支线任务');
        const startTime = Date.now();
        const steps = [];
        try {
            // 检查支线任务可用性
            steps.push('检查支线任务可用性');
            await this.delay(500);
            // 执行支线任务步骤
            if (task.config && 'steps' in task.config && Array.isArray(task.config.steps)) {
                for (const step of task.config.steps) {
                    steps.push(`执行步骤: ${step.name}`);
                    this.logTask(task.id, 'info', `执行步骤: ${step.name}`);
                    await this.delay(step.duration || 1500);
                }
            }
            else {
                // 默认支线任务流程
                steps.push('接受支线任务');
                await this.delay(1000);
                steps.push('收集任务物品');
                await this.delay(2000);
                steps.push('提交任务');
                await this.delay(1000);
            }
            const duration = Date.now() - startTime;
            this.stats.completedTasks++;
            this.stats.totalExecutionTime += duration;
            return {
                success: true,
                data: {
                    steps,
                    duration,
                    rewards: (task.config && 'expectedRewards' in task.config && Array.isArray(task.config.expectedRewards)) ? task.config.expectedRewards : []
                }
            };
        }
        catch (error) {
            throw new Error(`支线任务执行失败: ${error instanceof Error ? error.message : String(error)}`);
        }
    }
    /**
     * 执行自定义任务
     */
    async executeCustomTask(task) {
        this.logTask(task.id, 'info', '开始执行自定义任务');
        const startTime = Date.now();
        const steps = [];
        try {
            // 执行自定义任务步骤
            if (task.config && 'steps' in task.config && Array.isArray(task.config.steps)) {
                for (const step of task.config.steps) {
                    steps.push(`执行步骤: ${step.name}`);
                    this.logTask(task.id, 'info', `执行步骤: ${step.name}`);
                    // 根据步骤类型执行不同操作
                    switch (step.type) {
                        case 'click':
                            await this.delay(500);
                            break;
                        case 'wait':
                            await this.delay(step.duration || 1000);
                            break;
                        case 'input':
                            await this.delay(300);
                            break;
                        default:
                            await this.delay(1000);
                    }
                }
            }
            else {
                throw new Error('自定义任务必须提供执行步骤');
            }
            const duration = Date.now() - startTime;
            this.stats.completedTasks++;
            this.stats.totalExecutionTime += duration;
            return {
                success: true,
                data: {
                    steps,
                    duration,
                    customData: (task.config && 'customData' in task.config && task.config.customData) ? task.config.customData : {}
                }
            };
        }
        catch (error) {
            throw new Error(`自定义任务执行失败: ${error instanceof Error ? error.message : String(error)}`);
        }
    }
    /**
     * 执行活动任务
     */
    async executeEventTask(task) {
        this.logTask(task.id, 'info', '开始执行活动任务');
        const startTime = Date.now();
        const steps = [];
        try {
            // 检查活动是否可用
            steps.push('检查活动可用性');
            await this.delay(500);
            // 执行活动任务步骤
            if (task.config && 'steps' in task.config && Array.isArray(task.config.steps)) {
                for (const step of task.config.steps) {
                    steps.push(`执行步骤: ${step.name}`);
                    this.logTask(task.id, 'info', `执行步骤: ${step.name}`);
                    await this.delay(step.duration || 1000);
                }
            }
            else {
                // 默认活动任务流程
                steps.push('进入活动界面');
                await this.delay(1000);
                steps.push('参与活动');
                await this.delay(2500);
                steps.push('领取活动奖励');
                await this.delay(1000);
            }
            const duration = Date.now() - startTime;
            this.stats.completedTasks++;
            this.stats.totalExecutionTime += duration;
            return {
                success: true,
                data: {
                    steps,
                    duration,
                    eventRewards: (task.config && 'expectedRewards' in task.config && Array.isArray(task.config.expectedRewards)) ? task.config.expectedRewards : []
                }
            };
        }
        catch (error) {
            throw new Error(`活动任务执行失败: ${error instanceof Error ? error.message : String(error)}`);
        }
    }
    /**
     * 记录任务日志
     */
    logTask(taskId, level, message, data) {
        const log = {
            id: `log_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            taskId,
            level,
            message,
            timestamp: new Date(),
            metadata: data ? { ...data } : undefined
        };
        if (!this.taskLogs.has(taskId)) {
            this.taskLogs.set(taskId, []);
        }
        this.taskLogs.get(taskId).push(log);
        // 控制台输出
        const timestamp = log.timestamp.toISOString();
        const levelStr = level.toUpperCase().padEnd(5);
        console.log(`[${timestamp}] [${levelStr}] Task ${taskId}: ${message}`);
        if (data) {
            console.log(`[${timestamp}] [${levelStr}] Task ${taskId} Data:`, data);
        }
        // 限制日志数量，避免内存泄漏
        const logs = this.taskLogs.get(taskId);
        if (logs.length > 100) {
            this.taskLogs.set(taskId, logs.slice(-80)); // 保留最新的80条日志
        }
        // 发出日志事件
        this.emit('taskLog', log);
    }
    /**
     * 更新平均执行时间
     */
    updateAverageExecutionTime() {
        if (this.stats.completedTasks > 0) {
            this.stats.averageExecutionTime = this.stats.totalExecutionTime / this.stats.completedTasks;
        }
    }
    /**
     * 延迟函数
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    /**
     * 获取任务统计信息
     */
    getStats() {
        this.stats.total = this.tasks.size;
        this.stats.running = this.runningTasks.size;
        this.stats.completed = Array.from(this.tasks.values()).filter(task => task.status === 'completed').length;
        this.stats.failed = Array.from(this.tasks.values()).filter(task => task.status === 'failed').length;
        return { ...this.stats };
    }
    /**
     * 获取游戏检测器实例
     */
    getGameDetector() {
        return this.gameDetector;
    }
    /**
     * 获取输入控制器实例
     */
    getInputController() {
        return this.inputController;
    }
    /**
     * 获取图像识别实例
     */
    getImageRecognition() {
        return this.imageRecognition;
    }
    /**
     * 初始化游戏环境
     */
    async initializeGameEnvironment() {
        try {
            // 启动游戏检测
            await this.gameDetector.startDetection();
            // 等待游戏启动
            const isGameRunning = await this.gameDetector.isGameRunning();
            if (!isGameRunning) {
                console.log('等待游戏启动...');
                return false;
            }
            // 获取游戏窗口信息
            const gameInfo = await this.gameDetector.getGameProcessInfo();
            if (gameInfo && gameInfo.windowInfo) {
                // 设置输入控制器和图像识别的游戏窗口
                // 转换GameWindowInfo为GameWindow格式
                const gameWindow = {
                    x: gameInfo.windowInfo.bounds.x,
                    y: gameInfo.windowInfo.bounds.y,
                    width: gameInfo.windowInfo.bounds.width,
                    height: gameInfo.windowInfo.bounds.height
                };
                this.inputController.setGameWindow(gameWindow);
                this.imageRecognition.setGameWindowBounds(gameWindow);
                console.log('游戏环境初始化成功');
                return true;
            }
            return false;
        }
        catch (error) {
            console.error('游戏环境初始化失败:', error);
            return false;
        }
    }
    /**
     * 获取任务状态
     */
    getTaskStatus(taskId) {
        return this.tasks.get(taskId)?.status;
    }
    /**
     * 根据ID获取任务
     */
    getTaskById(taskId) {
        return this.tasks.get(taskId);
    }
    /**
     * 获取任务日志
     */
    getTaskLogs(taskId) {
        return this.taskLogs.get(taskId) || [];
    }
    /**
     * 获取正在运行的任务
     */
    getRunningTasks() {
        return Array.from(this.runningTasks)
            .map(taskId => this.tasks.get(taskId))
            .filter((task) => task !== undefined);
    }
    /**
     * 更新任务优先级
     */
    updateTaskPriority(taskId, priority) {
        const task = this.tasks.get(taskId);
        if (task) {
            task.priority = priority;
            // 重新排序队列
            this.taskQueue.sort((a, b) => b.priority - a.priority);
            this.logTask(taskId, 'info', `任务优先级已更新为: ${TaskPriority[priority]}`);
            return true;
        }
        return false;
    }
    /**
     * 获取暂停的任务
     */
    getPausedTasks() {
        return Array.from(this.tasks.values()).filter(task => task.status === 'paused');
    }
    /**
     * 获取已完成的任务
     */
    getCompletedTasks() {
        return Array.from(this.tasks.values()).filter(task => task.status === 'completed');
    }
    /**
     * 获取最大并发任务数
     */
    getMaxConcurrentTasks() {
        return this.maxConcurrentTasks;
    }
    /**
     * 设置最大并发任务数
     */
    setMaxConcurrentTasks(max) {
        this.maxConcurrentTasks = max;
        this.logTask('system', 'info', `最大并发任务数已更新为: ${max}`);
    }
    /**
     * 清理已完成的任务
     */
    clearCompletedTasks() {
        const completedTasks = this.getCompletedTasks();
        let clearedCount = 0;
        for (const task of completedTasks) {
            this.tasks.delete(task.id);
            this.taskLogs.delete(task.id);
            clearedCount++;
        }
        this.logTask('system', 'info', `已清理 ${clearedCount} 个已完成任务`);
        return clearedCount;
    }
    /**
     * 获取待处理的任务
     */
    getPendingTasks() {
        return Array.from(this.tasks.values()).filter(task => task.status === 'pending');
    }
    /**
     * 停止指定任务
     */
    stopTask(taskId) {
        const task = this.tasks.get(taskId);
        if (!task) {
            return false;
        }
        // 如果任务正在运行，从运行集合中移除
        if (this.runningTasks.has(taskId)) {
            this.runningTasks.delete(taskId);
        }
        // 从队列中移除
        this.taskQueue = this.taskQueue.filter(t => t.id !== taskId);
        // 更新任务状态
        task.status = 'cancelled';
        task.endTime = new Date();
        this.logTask(taskId, 'info', '任务已停止');
        return true;
    }
    /**
     * 暂停任务
     */
    pauseTask(taskId) {
        const task = this.tasks.get(taskId);
        if (task && task.status === 'running') {
            task.status = 'paused';
            this.logTask(taskId, 'info', '任务已暂停');
            this.emit('taskPaused', task);
            return true;
        }
        return false;
    }
    /**
     * 恢复任务
     */
    resumeTask(taskId) {
        const task = this.tasks.get(taskId);
        if (task && task.status === 'paused') {
            task.status = 'pending';
            this.taskQueue.unshift(task);
            this.logTask(taskId, 'info', '任务已恢复');
            this.emit('taskResumed', task);
            this.processQueue();
            return true;
        }
        return false;
    }
    /**
     * 取消任务
     */
    cancelTask(taskId) {
        const task = this.tasks.get(taskId);
        if (task && ['pending', 'running', 'paused'].includes(task.status)) {
            task.status = 'cancelled';
            task.endTime = new Date();
            // 从队列中移除
            this.taskQueue = this.taskQueue.filter(t => t.id !== taskId);
            this.runningTasks.delete(taskId);
            this.logTask(taskId, 'info', '任务已取消');
            this.emit('taskCancelled', task);
            return true;
        }
        return false;
    }
    /**
     * 停止所有任务
     */
    stopAllTasks() {
        // 停止所有运行中的任务
        for (const taskId of this.runningTasks) {
            this.cancelTask(taskId);
        }
        // 清空任务队列
        this.taskQueue = [];
        // 停止处理
        this.isProcessing = false;
        this.logTask('system', 'info', '所有任务已停止');
        this.emit('allTasksStopped');
    }
    /**
     * 停止所有检测和清理资源
     */
    async cleanup() {
        try {
            // 停止游戏检测
            await this.gameDetector.stopDetection();
            // 清理图像识别缓存
            this.imageRecognition.clearCache();
            // 清理输入控制器日志
            this.inputController.clearLogs();
            // 清理已完成的任务
            const completedTasks = Array.from(this.tasks.values())
                .filter(task => ['completed', 'failed', 'cancelled'].includes(task.status));
            completedTasks.forEach(task => {
                this.tasks.delete(task.id);
                this.taskLogs.delete(task.id);
            });
            this.logTask('system', 'info', `清理了 ${completedTasks.length} 个已完成的任务`);
            console.log('资源清理完成');
        }
        catch (error) {
            console.error('资源清理失败:', error);
        }
    }
}
export default TaskExecutor;
