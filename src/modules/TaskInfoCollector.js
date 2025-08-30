import { TaskType } from '../types';
import { v4 as uuidv4 } from 'uuid';
import * as path from 'path';
export class TaskInfoCollector {
    constructor(imageRecognition, databaseService, config) {
        Object.defineProperty(this, "imageRecognition", {
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
        Object.defineProperty(this, "logger", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        // 任务界面UI元素模板
        Object.defineProperty(this, "taskUIElements", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: {
                [TaskType.MAIN]: [
                    { name: 'taskTitle', templatePath: 'templates/main_task_title.png', required: true },
                    { name: 'taskDescription', templatePath: 'templates/main_task_desc.png', required: true },
                    { name: 'taskRewards', templatePath: 'templates/main_task_rewards.png', required: false }
                ],
                [TaskType.SIDE]: [
                    { name: 'taskTitle', templatePath: 'templates/side_task_title.png', required: true },
                    { name: 'taskDescription', templatePath: 'templates/side_task_desc.png', required: true },
                    { name: 'taskRewards', templatePath: 'templates/side_task_rewards.png', required: false }
                ],
                [TaskType.DAILY]: [
                    { name: 'taskTitle', templatePath: 'templates/daily_task_title.png', required: true },
                    { name: 'taskDescription', templatePath: 'templates/daily_task_desc.png', required: false },
                    { name: 'taskRewards', templatePath: 'templates/daily_task_rewards.png', required: true }
                ],
                [TaskType.WEEKLY]: [
                    { name: 'taskTitle', templatePath: 'templates/weekly_task_title.png', required: true },
                    { name: 'taskDescription', templatePath: 'templates/weekly_task_desc.png', required: false },
                    { name: 'taskRewards', templatePath: 'templates/weekly_task_rewards.png', required: true }
                ],
                [TaskType.EVENT]: [
                    { name: 'taskTitle', templatePath: 'templates/event_task_title.png', required: true },
                    { name: 'taskDescription', templatePath: 'templates/event_task_desc.png', required: true },
                    { name: 'taskRewards', templatePath: 'templates/event_task_rewards.png', required: true }
                ],
                [TaskType.CUSTOM]: [
                    { name: 'taskTitle', templatePath: 'templates/custom_task_title.png', required: true },
                    { name: 'taskDescription', templatePath: 'templates/custom_task_desc.png', required: true },
                    { name: 'taskRewards', templatePath: 'templates/custom_task_rewards.png', required: false }
                ]
            }
        });
        this.imageRecognition = imageRecognition;
        this.databaseService = databaseService;
        this.config = config;
        this.logger = {
            info: (msg) => console.log(`[TaskInfoCollector] ${msg}`),
            error: (msg, error) => console.error(`[TaskInfoCollector] ${msg}`, error),
            debug: (msg) => console.debug(`[TaskInfoCollector] ${msg}`)
        };
    }
    /**
     * 自动收集当前屏幕上的任务信息
     */
    async collectTaskInfo() {
        try {
            this.logger.info('开始收集任务信息...');
            // 首先检测任务类型
            const taskType = await this.detectTaskType();
            if (!taskType) {
                return {
                    success: false,
                    error: '无法检测到任务类型',
                    confidence: 0
                };
            }
            this.logger.debug(`检测到任务类型: ${taskType}`);
            // 根据任务类型收集信息
            const taskInfo = await this.collectTaskInfoByType(taskType);
            if (!taskInfo) {
                return {
                    success: false,
                    error: '无法收集任务信息',
                    confidence: 0
                };
            }
            // 保存到数据库
            if (this.config.storage?.enableBackup) {
                await this.saveTaskInfo(taskInfo);
            }
            this.logger.info(`任务信息收集成功: ${taskInfo.name}`);
            return {
                success: true,
                taskInfo,
                confidence: taskInfo.confidence || 0.8
            };
        }
        catch (error) {
            this.logger.error('任务信息收集失败:', error);
            return {
                success: false,
                error: error instanceof Error ? error.message : '未知错误',
                confidence: 0
            };
        }
    }
    /**
     * 检测当前任务类型
     */
    async detectTaskType() {
        const taskTypes = Object.keys(this.taskUIElements);
        for (const taskType of taskTypes) {
            const elements = this.taskUIElements[taskType];
            let detectedCount = 0;
            let requiredCount = 0;
            for (const element of elements) {
                if (element.required) {
                    requiredCount++;
                }
                const templatePath = path.join(process.cwd(), 'assets', element.templatePath);
                const result = await this.imageRecognition.findImage(templatePath);
                if (result.found && result.confidence > this.config.quality.minConfidence) {
                    detectedCount++;
                    this.logger.debug(`检测到UI元素: ${element.name}, 置信度: ${result.confidence}`);
                }
            }
            // 如果检测到所有必需元素，认为是该任务类型
            if (detectedCount >= requiredCount && requiredCount > 0) {
                return taskType;
            }
        }
        return null;
    }
    /**
     * 根据任务类型收集具体信息
     */
    async collectTaskInfoByType(taskType) {
        try {
            const taskInfo = {
                id: uuidv4(),
                taskType: taskType,
                taskName: '',
                name: '',
                type: taskType,
                description: '',
                prerequisites: [],
                rewards: [],
                estimatedTime: 0,
                difficulty: 'easy',
                location: '',
                isRepeatable: false,
                collectTime: new Date(),
                lastUpdated: new Date(),
                confidence: 0,
                requirements: [],
                tags: []
            };
            // 收集任务名称
            const name = await this.extractTaskName(taskType);
            if (name) {
                taskInfo.name = name;
            }
            // 收集任务描述
            const description = await this.extractTaskDescription(taskType);
            if (description) {
                taskInfo.description = description;
            }
            // 收集任务奖励
            const rewards = await this.extractTaskRewards(taskType);
            if (rewards.length > 0) {
                taskInfo.rewards = rewards;
            }
            // 收集任务要求
            const requirements = await this.extractTaskRequirements(taskType);
            if (requirements.length > 0) {
                taskInfo.requirements = requirements;
            }
            // 估算任务难度和时间
            taskInfo.difficulty = this.estimateTaskDifficulty(taskInfo);
            taskInfo.estimatedTime = this.estimateTaskTime(taskInfo);
            // 计算整体置信度
            taskInfo.confidence = this.calculateOverallConfidence(taskInfo);
            return taskInfo;
        }
        catch (error) {
            this.logger.error('收集任务信息失败:', error);
            return null;
        }
    }
    /**
     * 提取任务名称
     */
    async extractTaskName(taskType) {
        try {
            // 根据任务类型确定名称区域
            const nameRegion = this.getTaskNameRegion(taskType);
            if (!nameRegion) {
                return '未知任务';
            }
            // 使用OCR识别文字
            const result = await this.imageRecognition.recognizeText(nameRegion);
            if (result.found && result.text) {
                return result.text.trim();
            }
            return '未知任务';
        }
        catch (error) {
            this.logger.error('提取任务名称失败:', error);
            return '未知任务';
        }
    }
    /**
     * 提取任务描述
     */
    async extractTaskDescription(taskType) {
        try {
            const descriptionRegion = this.getTaskDescriptionRegion(taskType);
            if (!descriptionRegion) {
                return '';
            }
            const result = await this.imageRecognition.recognizeText(descriptionRegion);
            if (result.found && result.text) {
                return result.text.trim();
            }
            return '';
        }
        catch (error) {
            this.logger.error('提取任务描述失败:', error);
            return '';
        }
    }
    /**
     * 提取任务奖励
     */
    async extractTaskRewards(taskType) {
        try {
            const rewardsRegion = this.getTaskRewardsRegion(taskType);
            if (!rewardsRegion) {
                return [];
            }
            const result = await this.imageRecognition.recognizeText(rewardsRegion);
            if (result.found && result.text) {
                // 简单解析奖励文本并转换为TaskReward对象
                const rewardLines = result.text.split('\n').filter(line => line.trim().length > 0);
                return rewardLines.map((line, index) => ({
                    type: 'exp', // 默认类型，实际应根据文本内容判断
                    name: line.trim(),
                    amount: 1, // 默认数量，实际应从文本中解析
                    rarity: 'common'
                }));
            }
            return [];
        }
        catch (error) {
            this.logger.error('提取任务奖励失败:', error);
            return [];
        }
    }
    /**
     * 提取任务要求
     */
    async extractTaskRequirements(taskType) {
        try {
            const requirementsRegion = this.getTaskRequirementsRegion(taskType);
            if (!requirementsRegion) {
                return [];
            }
            const result = await this.imageRecognition.recognizeText(requirementsRegion);
            if (result.found && result.text) {
                return result.text.split('\n').filter(line => line.trim().length > 0);
            }
            return [];
        }
        catch (error) {
            this.logger.error('提取任务要求失败:', error);
            return [];
        }
    }
    /**
     * 获取任务名称区域
     */
    getTaskNameRegion(taskType) {
        // 根据任务类型返回不同的名称区域坐标
        // 这些坐标需要根据实际游戏界面调整
        switch (taskType) {
            case TaskType.MAIN:
                return { x: 100, y: 50, width: 400, height: 60 };
            case TaskType.SIDE:
                return { x: 120, y: 80, width: 350, height: 50 };
            case TaskType.DAILY:
                return { x: 150, y: 100, width: 300, height: 40 };
            case TaskType.WEEKLY:
                return { x: 150, y: 100, width: 300, height: 40 };
            case TaskType.EVENT:
                return { x: 80, y: 60, width: 450, height: 70 };
            default:
                return null;
        }
    }
    /**
     * 获取任务描述区域
     */
    getTaskDescriptionRegion(taskType) {
        switch (taskType) {
            case TaskType.MAIN:
                return { x: 100, y: 120, width: 500, height: 150 };
            case TaskType.SIDE:
                return { x: 120, y: 140, width: 450, height: 120 };
            case TaskType.DAILY:
                return { x: 150, y: 150, width: 400, height: 80 };
            case TaskType.WEEKLY:
                return { x: 150, y: 150, width: 400, height: 80 };
            case TaskType.EVENT:
                return { x: 80, y: 140, width: 550, height: 180 };
            default:
                return null;
        }
    }
    /**
     * 获取任务奖励区域
     */
    getTaskRewardsRegion(taskType) {
        switch (taskType) {
            case TaskType.MAIN:
            case TaskType.SIDE:
            case TaskType.EVENT:
                return { x: 100, y: 300, width: 500, height: 100 };
            case TaskType.DAILY:
            case TaskType.WEEKLY:
                return { x: 150, y: 250, width: 400, height: 80 };
            default:
                return null;
        }
    }
    /**
     * 获取任务要求区域
     */
    getTaskRequirementsRegion(taskType) {
        switch (taskType) {
            case TaskType.MAIN:
            case TaskType.SIDE:
                return { x: 100, y: 280, width: 500, height: 80 };
            default:
                return null;
        }
    }
    /**
     * 估算任务难度
     */
    estimateTaskDifficulty(taskInfo) {
        let difficultyScore = 1;
        // 根据任务类型调整基础难度
        switch (taskInfo.type) {
            case TaskType.MAIN:
                difficultyScore = 3;
                break;
            case TaskType.SIDE:
                difficultyScore = 2;
                break;
            case TaskType.EVENT:
                difficultyScore = 4;
                break;
            default:
                difficultyScore = 1;
        }
        // 根据要求数量调整难度
        if (taskInfo.prerequisites.length > 3) {
            difficultyScore += 1;
        }
        // 根据描述长度调整难度
        if (taskInfo.description.length > 100) {
            difficultyScore += 1;
        }
        const finalScore = Math.min(difficultyScore, 5);
        // 将数字转换为字符串字面量
        if (finalScore <= 1)
            return 'easy';
        if (finalScore <= 2)
            return 'medium';
        if (finalScore <= 4)
            return 'hard';
        return 'extreme';
    }
    /**
     * 估算任务时间（分钟）
     */
    estimateTaskTime(taskInfo) {
        let baseTime = 5; // 基础5分钟
        // 根据任务类型调整时间
        switch (taskInfo.type) {
            case TaskType.MAIN:
                baseTime = 30;
                break;
            case TaskType.SIDE:
                baseTime = 15;
                break;
            case TaskType.EVENT:
                baseTime = 20;
                break;
            case TaskType.DAILY:
                baseTime = 5;
                break;
            case TaskType.WEEKLY:
                baseTime = 10;
                break;
        }
        // 根据难度调整时间
        const difficultyMultiplier = {
            'easy': 1,
            'medium': 1.5,
            'hard': 2,
            'extreme': 3
        };
        baseTime *= difficultyMultiplier[taskInfo.difficulty] || 1;
        return baseTime;
    }
    /**
     * 计算整体置信度
     */
    calculateOverallConfidence(taskInfo) {
        let confidence = 0.5; // 基础置信度
        // 有名称加分
        if (taskInfo.name && taskInfo.name !== '未知任务') {
            confidence += 0.2;
        }
        // 有描述加分
        if (taskInfo.description && taskInfo.description.length > 0) {
            confidence += 0.2;
        }
        // 有奖励信息加分
        if (taskInfo.rewards.length > 0) {
            confidence += 0.1;
        }
        return Math.min(confidence, 1.0);
    }
    /**
     * 保存任务信息到数据库
     */
    async saveTaskInfo(taskInfo) {
        try {
            await this.databaseService.addTaskInfo(taskInfo);
            this.logger.info(`任务信息已保存: ${taskInfo.id}`);
        }
        catch (error) {
            this.logger.error('保存任务信息失败:', error);
            throw error;
        }
    }
    /**
     * 更新配置
     */
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
        this.logger.info('任务信息收集配置已更新');
    }
    /**
     * 获取当前配置
     */
    getConfig() {
        return { ...this.config };
    }
}
