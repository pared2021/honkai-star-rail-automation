import fs from 'fs';
import path from 'path';
export class StrategyDataInitializer {
    constructor(db) {
        this.db = db;
        this.dataPath = path.join(process.cwd(), 'data', 'preset-strategies.json');
    }
    async needsInitialization() {
        try {
            const existingStrategies = await this.db.getStrategies();
            const presetStrategies = existingStrategies.filter(s => s.author === 'preset');
            return presetStrategies.length === 0;
        }
        catch (error) {
            console.error('检查初始化状态失败:', error);
            return true;
        }
    }
    async loadPresetData() {
        try {
            if (!fs.existsSync(this.dataPath)) {
                console.warn(`预置攻略数据文件不存在: ${this.dataPath}`);
                return [];
            }
            const fileContent = fs.readFileSync(this.dataPath, 'utf-8');
            const data = JSON.parse(fileContent);
            console.log(`成功加载 ${data.length} 个预置任务的攻略数据`);
            return data;
        }
        catch (error) {
            console.error('加载预置攻略数据失败:', error);
            return [];
        }
    }
    async initializePresetData() {
        try {
            console.log('开始初始化预置攻略数据...');
            const presetData = await this.loadPresetData();
            if (presetData.length === 0) {
                console.log('没有找到预置攻略数据，跳过初始化');
                return;
            }
            let importedCount = 0;
            let errorCount = 0;
            for (const taskData of presetData) {
                try {
                    const allTaskInfos = await this.db.getTaskInfos();
                    let taskInfo = allTaskInfos.find(t => t.id === taskData.taskId);
                    let taskInfoId = taskData.taskId;
                    if (!taskInfo) {
                        const newTaskInfo = {
                            id: taskData.taskId,
                            taskName: taskData.taskName,
                            taskType: taskData.taskType,
                            name: taskData.taskName,
                            type: taskData.taskType,
                            description: `预置任务: ${taskData.taskName}`,
                            prerequisites: [],
                            rewards: [],
                            difficulty: 'medium',
                            estimatedTime: 30,
                            location: '',
                            npcName: '',
                            chapter: '',
                            questLine: '',
                            isRepeatable: false,
                            collectTime: new Date(),
                            lastUpdated: new Date()
                        };
                        const createdTaskInfo = await this.db.createTaskInfo(newTaskInfo);
                        taskInfo = createdTaskInfo;
                        taskInfoId = createdTaskInfo.id;
                        console.log(`创建预置任务信息: ${taskData.taskName}`);
                    }
                    if (taskData.strategies && taskData.strategies.length > 0) {
                        const strategiesToCreate = taskData.strategies.map((strategyData) => ({
                            taskInfoId: taskInfoId,
                            strategyName: strategyData.name,
                            description: strategyData.description,
                            steps: strategyData.steps.map((step, index) => ({
                                id: `${strategyData.name}-step-${index + 1}`,
                                strategyId: '',
                                stepOrder: index + 1,
                                stepType: 'custom',
                                description: step.description || step,
                                action: {
                                    type: 'custom',
                                    parameters: step.action || {}
                                },
                                timeout: step.timeout || 30,
                                retryCount: step.retryCount || 3,
                                isOptional: step.isOptional || false
                            })),
                            estimatedTime: strategyData.estimatedTime,
                            successRate: strategyData.successRate,
                            difficulty: strategyData.difficulty,
                            requirements: strategyData.requirements,
                            tips: strategyData.tips,
                            author: 'preset',
                            version: '1.0.0',
                            isVerified: true
                        }));
                        const createdStrategies = await this.db.batchCreateStrategies(strategiesToCreate);
                        importedCount += createdStrategies.length;
                        console.log(`导入任务 ${taskData.taskName} 的 ${taskData.strategies.length} 个攻略`);
                    }
                }
                catch (error) {
                    console.error(`导入任务 ${taskData.taskName} 的攻略失败:`, error);
                    errorCount++;
                }
            }
            console.log(`预置攻略数据初始化完成: 成功导入 ${importedCount} 个攻略，失败 ${errorCount} 个`);
        }
        catch (error) {
            console.error('初始化预置攻略数据失败:', error);
            throw error;
        }
    }
    async updatePresetData() {
        try {
            console.log('开始更新预置攻略数据...');
            await this.db.deleteStrategiesBySource('preset');
            await this.initializePresetData();
            console.log('预置攻略数据更新完成');
        }
        catch (error) {
            console.error('更新预置攻略数据失败:', error);
            throw error;
        }
    }
    async getPresetDataStats() {
        try {
            const strategies = await this.db.getStrategies();
            const taskInfos = await this.db.getTaskInfos();
            const presetStrategies = strategies.filter(s => s.author === 'preset');
            const presetTaskInfos = taskInfos.filter(t => t.taskType && ['main', 'side', 'daily', 'event'].includes(t.taskType));
            const taskIds = new Set(presetStrategies.map(s => s.taskInfoId));
            const taskTypes = {};
            const difficultyDistribution = {};
            for (const taskId of taskIds) {
                const allTaskInfos = await this.db.getTaskInfos();
                const taskInfo = allTaskInfos.find(t => t.id === taskId);
                if (taskInfo) {
                    taskTypes[taskInfo.taskType] = (taskTypes[taskInfo.taskType] || 0) + 1;
                }
            }
            for (const strategy of presetStrategies) {
                difficultyDistribution[strategy.difficulty] =
                    (difficultyDistribution[strategy.difficulty] || 0) + 1;
            }
            return {
                totalTasks: taskIds.size,
                totalStrategies: presetStrategies.length,
                taskTypes,
                difficultyDistribution
            };
        }
        catch (error) {
            console.error('获取预置攻略统计信息失败:', error);
            return {
                totalTasks: 0,
                totalStrategies: 0,
                taskTypes: {},
                difficultyDistribution: {}
            };
        }
    }
    async validatePresetData() {
        const errors = [];
        const warnings = [];
        try {
            const presetData = await this.loadPresetData();
            if (presetData.length === 0) {
                warnings.push('没有找到预置攻略数据文件');
                return { isValid: true, errors, warnings };
            }
            for (const taskData of presetData) {
                if (!taskData.taskId || !taskData.taskName) {
                    errors.push(`任务缺少必要字段: ${JSON.stringify(taskData)}`);
                    continue;
                }
                if (!['main', 'side', 'daily'].includes(taskData.taskType)) {
                    errors.push(`任务 ${taskData.taskName} 的类型无效: ${taskData.taskType}`);
                }
                for (const strategy of taskData.strategies) {
                    if (!strategy.id || !strategy.name || !strategy.steps || strategy.steps.length === 0) {
                        errors.push(`任务 ${taskData.taskName} 的攻略缺少必要字段: ${strategy.name}`);
                    }
                    if (strategy.successRate < 0 || strategy.successRate > 1) {
                        warnings.push(`任务 ${taskData.taskName} 的攻略 ${strategy.name} 成功率超出范围: ${strategy.successRate}`);
                    }
                    if (strategy.averageTime <= 0) {
                        warnings.push(`任务 ${taskData.taskName} 的攻略 ${strategy.name} 平均时间无效: ${strategy.averageTime}`);
                    }
                }
            }
            return {
                isValid: errors.length === 0,
                errors,
                warnings
            };
        }
        catch (error) {
            errors.push(`验证预置攻略数据时发生错误: ${error}`);
            return { isValid: false, errors, warnings };
        }
    }
}
