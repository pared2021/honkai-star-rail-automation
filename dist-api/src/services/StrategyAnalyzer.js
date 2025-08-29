export class StrategyAnalyzer {
    constructor(dbService) {
        this.analysisQueue = new Map();
        this.isAnalyzing = false;
        this.dbService = dbService;
    }
    async startAnalysis(taskId, maxIterations = 5) {
        console.log(`开始分析任务 ${taskId} 的攻略...`);
        this.isAnalyzing = true;
        try {
            const taskInfos = await this.dbService.getTaskInfos({ type: 'main' });
            if (taskInfos.length === 0) {
                throw new Error(`未找到任务信息: ${taskId}`);
            }
            const taskInfo = taskInfos[0];
            const existingStrategies = await this.dbService.getStrategies({ taskInfoId: taskInfo.id });
            const newStrategies = [];
            for (let i = 0; i < maxIterations; i++) {
                console.log(`生成攻略方案 ${i + 1}/${maxIterations}...`);
                const strategy = await this.generateStrategy(taskInfo, existingStrategies.concat(newStrategies));
                const savedStrategy = await this.dbService.createStrategy(strategy);
                newStrategies.push(savedStrategy);
                await this.dbService.createStrategy(strategy);
            }
            const allStrategies = existingStrategies.concat(newStrategies);
            const evaluations = await this.evaluateStrategies(allStrategies, taskInfo);
            const bestStrategy = this.findBestStrategy(allStrategies, evaluations);
            const analysisResult = {
                taskInfoId: taskInfo.id,
                recommendedStrategy: bestStrategy,
                alternativeStrategies: allStrategies.filter(s => s.id !== bestStrategy.id),
                analysisScore: evaluations.find(e => e.strategyId === bestStrategy.id)?.efficiency || 0,
                confidenceLevel: 0.8,
                analysisTime: new Date(),
                factors: this.getAnalysisFactors()
            };
            console.log(`攻略分析完成，最优方案得分: ${analysisResult.analysisScore}`);
            return analysisResult;
        }
        catch (error) {
            console.error('攻略分析失败:', error);
            throw error;
        }
        finally {
            this.isAnalyzing = false;
        }
    }
    async generateStrategy(taskInfo, existingStrategies) {
        const existingPatterns = this.analyzeExistingPatterns(existingStrategies);
        let steps;
        switch (taskInfo.taskType) {
            case 'main':
                steps = await this.generateMainQuestSteps(taskInfo, existingPatterns);
                break;
            case 'side':
                steps = await this.generateSideQuestSteps(taskInfo, existingPatterns);
                break;
            case 'daily':
                steps = await this.generateDailyQuestSteps(taskInfo, existingPatterns);
                break;
            case 'daily':
                steps = await this.generateEventQuestSteps(taskInfo, existingPatterns);
                break;
            default:
                steps = await this.generateGenericSteps(taskInfo, existingPatterns);
        }
        const strategy = {
            taskInfoId: taskInfo.id,
            strategyName: `${taskInfo.taskName} - 攻略方案 ${existingStrategies.length + 1}`,
            description: this.generateStrategyDescription(taskInfo, steps),
            steps,
            estimatedTime: this.calculateEstimatedTime(steps),
            difficulty: 'medium',
            successRate: this.estimateSuccessRate(steps, taskInfo),
            requirements: this.extractRequirements(steps),
            tips: this.generateTips(taskInfo, steps),
            author: 'System',
            version: '1.0',
            isVerified: false
        };
        return strategy;
    }
    async generateMainQuestSteps(taskInfo, patterns) {
        const steps = [
            {
                id: `step_${Date.now()}_1`,
                strategyId: '',
                stepOrder: 1,
                stepType: 'navigation',
                action: {
                    type: 'click',
                    target: { text: taskInfo.location || '任务地点' },
                    parameters: { method: 'auto' }
                },
                description: `前往${taskInfo.location || '任务地点'}`,
                timeout: 30,
                retryCount: 3,
                isOptional: false,
                conditions: [
                    {
                        type: 'custom',
                        operator: 'equals',
                        value: '到达指定地点'
                    }
                ]
            },
            {
                id: `step_${Date.now()}_2`,
                strategyId: '',
                stepOrder: 2,
                stepType: 'interaction',
                action: {
                    type: 'click',
                    target: { text: taskInfo.npcName || '任务NPC' },
                    parameters: { interaction: 'talk' }
                },
                description: `与${taskInfo.npcName || '任务NPC'}对话`,
                timeout: 15,
                retryCount: 3,
                isOptional: false,
                conditions: [
                    {
                        type: 'custom',
                        operator: 'contains',
                        value: '对话包含任务关键词'
                    }
                ]
            },
            {
                id: `step_${Date.now()}_3`,
                strategyId: '',
                stepOrder: 3,
                stepType: 'battle',
                action: {
                    type: 'click',
                    target: { text: '敌人' },
                    parameters: { strategy: 'balanced' }
                },
                description: '完成战斗任务',
                timeout: 60,
                retryCount: 3,
                isOptional: false,
                conditions: [
                    {
                        type: 'custom',
                        operator: 'equals',
                        value: '战斗胜利'
                    }
                ]
            },
            {
                id: `step_${Date.now()}_4`,
                strategyId: '',
                stepOrder: 4,
                stepType: 'interaction',
                action: {
                    type: 'click',
                    target: { text: taskInfo.npcName || '任务NPC' },
                    parameters: { interaction: 'complete' }
                },
                description: '完成任务并领取奖励',
                timeout: 10,
                retryCount: 3,
                isOptional: false,
                conditions: [
                    {
                        type: 'custom',
                        operator: 'equals',
                        value: '任务完成'
                    }
                ]
            }
        ];
        return steps;
    }
    async generateSideQuestSteps(taskInfo, patterns) {
        const steps = [
            {
                id: `step_${Date.now()}_1`,
                strategyId: '',
                stepOrder: 1,
                stepType: 'navigation',
                action: {
                    type: 'click',
                    target: { text: taskInfo.location || '任务地点' },
                    parameters: { method: 'efficient' }
                },
                description: `快速前往${taskInfo.location || '任务地点'}`,
                timeout: 20,
                retryCount: 3,
                isOptional: false,
                conditions: []
            },
            {
                id: `step_${Date.now()}_2`,
                strategyId: '',
                stepOrder: 2,
                stepType: 'custom',
                action: {
                    type: 'click',
                    target: { text: '任务物品' },
                    parameters: { quantity: 1 }
                },
                description: '收集任务所需物品',
                timeout: 30,
                retryCount: 3,
                isOptional: false,
                conditions: [
                    {
                        type: 'custom',
                        operator: 'contains',
                        value: '背包包含任务物品'
                    }
                ]
            },
            {
                id: `step_${Date.now()}_3`,
                strategyId: '',
                stepOrder: 3,
                stepType: 'interaction',
                action: {
                    type: 'click',
                    target: { text: taskInfo.npcName || '任务NPC' },
                    parameters: { interaction: 'submit' }
                },
                description: '提交任务物品',
                timeout: 10,
                retryCount: 3,
                isOptional: false,
                conditions: []
            }
        ];
        return steps;
    }
    async generateDailyQuestSteps(taskInfo, patterns) {
        const steps = [
            {
                id: `step_${Date.now()}_1`,
                strategyId: '',
                stepOrder: 1,
                stepType: 'navigation',
                action: {
                    type: 'click',
                    target: { text: '副本入口' },
                    parameters: { method: 'teleport' }
                },
                description: '传送到副本入口',
                timeout: 5,
                retryCount: 3,
                isOptional: false,
                conditions: []
            },
            {
                id: `step_${Date.now()}_2`,
                strategyId: '',
                stepOrder: 2,
                stepType: 'interaction',
                action: {
                    type: 'click',
                    target: { text: '日常副本' },
                    parameters: { difficulty: 'normal' }
                },
                description: '进入日常副本',
                timeout: 10,
                retryCount: 3,
                isOptional: false,
                conditions: []
            },
            {
                id: `step_${Date.now()}_3`,
                strategyId: '',
                stepOrder: 3,
                stepType: 'battle',
                action: {
                    type: 'click',
                    target: { text: '副本怪物' },
                    parameters: { mode: 'speed' }
                },
                description: '自动战斗完成副本',
                timeout: 120,
                retryCount: 3,
                isOptional: false,
                conditions: [
                    {
                        type: 'custom',
                        operator: 'equals',
                        value: '副本完成'
                    }
                ]
            },
            {
                id: `step_${Date.now()}_4`,
                strategyId: '',
                stepOrder: 4,
                stepType: 'interaction',
                action: {
                    type: 'click',
                    target: { text: '副本奖励' },
                    parameters: {}
                },
                description: '收集副本奖励',
                timeout: 5,
                retryCount: 3,
                isOptional: false,
                conditions: []
            }
        ];
        return steps;
    }
    async generateEventQuestSteps(taskInfo, patterns) {
        const steps = [
            {
                id: `step_${Date.now()}_1`,
                strategyId: '',
                stepOrder: 1,
                stepType: 'interaction',
                action: {
                    type: 'click',
                    target: { text: '活动界面' },
                    parameters: { method: 'menu' }
                },
                description: '打开活动界面',
                timeout: 10,
                retryCount: 3,
                isOptional: false,
                conditions: []
            },
            {
                id: `step_${Date.now()}_2`,
                strategyId: '',
                stepOrder: 2,
                stepType: 'interaction',
                action: {
                    type: 'click',
                    target: { text: taskInfo.taskName },
                    parameters: {}
                },
                description: `选择活动：${taskInfo.taskName}`,
                timeout: 5,
                retryCount: 3,
                isOptional: false,
                conditions: []
            },
            {
                id: `step_${Date.now()}_3`,
                strategyId: '',
                stepOrder: 3,
                stepType: 'interaction',
                action: {
                    type: 'click',
                    target: { text: '活动内容' },
                    parameters: { mode: 'optimal' }
                },
                description: '参与活动内容',
                timeout: 180,
                retryCount: 3,
                isOptional: false,
                conditions: [
                    {
                        type: 'custom',
                        operator: 'equals',
                        value: '活动进度100%'
                    }
                ]
            }
        ];
        return steps;
    }
    async generateGenericSteps(taskInfo, patterns) {
        return [
            {
                id: `step_${Date.now()}_1`,
                strategyId: '',
                stepOrder: 1,
                stepType: 'custom',
                action: {
                    type: 'text_recognition',
                    target: { text: '任务要求' },
                    parameters: {}
                },
                description: '分析任务要求',
                timeout: 10,
                retryCount: 3,
                isOptional: false,
                conditions: []
            },
            {
                id: `step_${Date.now()}_2`,
                strategyId: '',
                stepOrder: 2,
                stepType: 'interaction',
                action: {
                    type: 'click',
                    target: { x: 100, y: 100 },
                    parameters: { method: 'auto' }
                },
                description: '执行任务内容',
                timeout: (taskInfo.estimatedTime || 60) * 60,
                retryCount: 3,
                isOptional: false,
                conditions: []
            }
        ];
    }
    async evaluateStrategies(strategies, taskInfo) {
        const evaluations = [];
        for (const strategy of strategies) {
            const evaluation = await this.evaluateStrategy(strategy, taskInfo);
            evaluations.push({ ...evaluation, id: `eval_${Date.now()}_${Math.random()}` });
            await this.dbService.createStrategyEvaluation(evaluation);
        }
        return evaluations;
    }
    async evaluateStrategy(strategy, taskInfo) {
        const timeScore = this.calculateTimeScore(strategy, taskInfo);
        const difficultyScore = this.calculateDifficultyScore(strategy);
        const successScore = this.calculateSuccessScore(strategy);
        const reliabilityScore = this.calculateReliabilityScore(strategy);
        const resourceScore = this.calculateResourceScore(strategy);
        const overallScore = (timeScore * 0.25 +
            difficultyScore * 0.2 +
            successScore * 0.3 +
            reliabilityScore * 0.15 +
            resourceScore * 0.1);
        const evaluation = {
            strategyId: strategy.id,
            accountId: 'system',
            executionTime: this.calculateEstimatedTime(strategy.steps),
            success: true,
            completionRate: 1.0,
            efficiency: overallScore,
            feedback: this.generateFeedback(strategy, {
                timeScore,
                difficultyScore,
                successScore,
                reliabilityScore,
                resourceScore,
                overallScore
            }),
            executedAt: new Date()
        };
        return evaluation;
    }
    calculateTimeScore(strategy, taskInfo) {
        const estimatedTime = strategy.estimatedTime;
        const baseTime = taskInfo.estimatedTime || 60;
        if (estimatedTime <= baseTime * 0.8)
            return 100;
        if (estimatedTime <= baseTime)
            return 85;
        if (estimatedTime <= baseTime * 1.2)
            return 70;
        if (estimatedTime <= baseTime * 1.5)
            return 50;
        return 30;
    }
    calculateDifficultyScore(strategy) {
        const difficulty = strategy.difficulty;
        const difficultyLevel = typeof difficulty === 'string' ?
            ({ 'easy': 1, 'medium': 3, 'hard': 5 }[difficulty] || 3) : difficulty;
        if (difficultyLevel <= 2)
            return 100;
        if (difficultyLevel <= 3)
            return 80;
        if (difficultyLevel <= 4)
            return 60;
        return 40;
    }
    calculateSuccessScore(strategy) {
        return strategy.successRate;
    }
    calculateReliabilityScore(strategy) {
        const stepCount = strategy.steps.length;
        const complexSteps = strategy.steps.filter(step => step.conditions && step.conditions.length > 0).length;
        const baseScore = Math.max(100 - stepCount * 5, 50);
        const complexityPenalty = complexSteps * 3;
        return Math.max(baseScore - complexityPenalty, 30);
    }
    calculateResourceScore(strategy) {
        const resourceCount = strategy.requirements?.length || 0;
        if (resourceCount === 0)
            return 100;
        if (resourceCount <= 2)
            return 85;
        if (resourceCount <= 4)
            return 70;
        return 50;
    }
    findBestStrategy(strategies, evaluations) {
        let bestStrategy = strategies[0];
        let bestScore = 0;
        for (const strategy of strategies) {
            const evaluation = evaluations.find(e => e.strategyId === strategy.id);
            if (evaluation && evaluation.efficiency > bestScore) {
                bestScore = evaluation.efficiency;
                bestStrategy = strategy;
            }
        }
        return bestStrategy;
    }
    getAnalysisFactors() {
        return [
            {
                name: '时间效率',
                weight: 0.25,
                description: '完成任务所需的时间',
                score: 0
            },
            {
                name: '难度等级',
                weight: 0.2,
                description: '攻略的执行难度',
                score: 0
            },
            {
                name: '成功率',
                weight: 0.3,
                description: '攻略的成功概率',
                score: 0
            },
            {
                name: '可靠性',
                weight: 0.15,
                description: '攻略的稳定性和一致性',
                score: 0
            },
            {
                name: '资源消耗',
                weight: 0.1,
                description: '执行攻略所需的资源',
                score: 0
            }
        ];
    }
    generateRecommendations(bestStrategy, evaluations) {
        const recommendations = [];
        const bestEvaluation = evaluations.find(e => e.strategyId === bestStrategy.id);
        if (!bestEvaluation)
            return recommendations;
        if (bestEvaluation.efficiency < 80) {
            recommendations.push('建议优化时间效率，减少不必要的等待时间');
        }
        if (bestEvaluation.completionRate < 0.9) {
            recommendations.push('建议增加容错机制，提高成功率');
        }
        if (!bestEvaluation.success) {
            recommendations.push('建议简化攻略步骤，提高可靠性');
        }
        if (bestStrategy.estimatedTime > 300) {
            recommendations.push('任务时间较长，建议分阶段执行');
        }
        return recommendations;
    }
    analyzeExistingPatterns(strategies) {
        return {
            commonSteps: this.findCommonSteps(strategies),
            averageTime: this.calculateAverageTime(strategies),
            successPatterns: this.findSuccessPatterns(strategies)
        };
    }
    findCommonSteps(strategies) {
        return [];
    }
    calculateAverageTime(strategies) {
        if (strategies.length === 0)
            return 0;
        const totalTime = strategies.reduce((sum, s) => sum + s.estimatedTime, 0);
        return totalTime / strategies.length;
    }
    findSuccessPatterns(strategies) {
        return [];
    }
    generateStrategyDescription(taskInfo, steps) {
        return `针对${taskInfo.taskName}的优化攻略，包含${steps.length}个步骤，预计用时${this.calculateEstimatedTime(steps)}分钟`;
    }
    calculateEstimatedTime(steps) {
        return steps.reduce((total, step) => total + (step.timeout || 30), 0);
    }
    calculateDifficulty(steps) {
        const complexSteps = steps.filter(step => step.conditions && step.conditions.length > 0).length;
        return Math.min(Math.ceil(complexSteps / 2) + 1, 5);
    }
    estimateSuccessRate(steps, taskInfo) {
        const baseRate = 95;
        const stepPenalty = steps.length * 2;
        const difficultyMap = { 'easy': 1, 'medium': 2, 'hard': 3, 'extreme': 4 };
        const difficultyPenalty = (difficultyMap[taskInfo.difficulty] || 1) * 5;
        return Math.max(baseRate - stepPenalty - difficultyPenalty, 60);
    }
    extractRequirements(steps) {
        const requirements = new Set();
        steps.forEach(step => {
            if (step.stepType === 'battle') {
                requirements.add('战斗能力');
            }
            if (step.stepType === 'navigation') {
                requirements.add('传送点解锁');
            }
            if (step.action.type === 'image_recognition') {
                requirements.add('图像识别功能');
            }
        });
        return Array.from(requirements);
    }
    generateTips(taskInfo, steps) {
        const tips = [];
        if (taskInfo.difficulty === 'hard' || taskInfo.difficulty === 'extreme') {
            tips.push('建议提升角色等级后再尝试');
        }
        if (steps.some(step => step.stepType === 'battle')) {
            tips.push('注意角色血量，及时使用治疗道具');
        }
        if (taskInfo.isRepeatable) {
            tips.push('此任务可重复完成，建议加入日常任务列表');
        }
        return tips;
    }
    generateStrategyTags(taskInfo, steps) {
        const tags = [taskInfo.taskType];
        if (taskInfo.difficulty) {
            tags.push(taskInfo.difficulty);
        }
        if (steps.some(step => step.stepType === 'battle')) {
            tags.push('战斗');
        }
        if (steps.some(step => step.stepType === 'navigation')) {
            tags.push('移动');
        }
        return tags;
    }
    generateFeedback(strategy, scores) {
        const feedback = [];
        if (scores.overallScore >= 90) {
            feedback.push('优秀的攻略方案');
        }
        else if (scores.overallScore >= 75) {
            feedback.push('良好的攻略方案');
        }
        else {
            feedback.push('需要改进的攻略方案');
        }
        if (scores.timeScore < 70) {
            feedback.push('时间效率有待提升');
        }
        if (scores.successScore < 80) {
            feedback.push('成功率需要改善');
        }
        return feedback.join('，');
    }
    generateTestResults(strategy) {
        return {
            executionTime: strategy.estimatedTime,
            successCount: Math.floor(strategy.successRate / 10),
            failureCount: Math.floor((100 - strategy.successRate) / 10),
            averageScore: strategy.successRate
        };
    }
    generateStrategyRecommendations(strategy) {
        const recommendations = [];
        if (strategy.steps.length > 5) {
            recommendations.push('考虑合并相似步骤以简化流程');
        }
        if (strategy.estimatedTime > 180) {
            recommendations.push('添加中间检查点以提高容错性');
        }
        if (strategy.successRate < 85) {
            recommendations.push('增加备选方案以提高成功率');
        }
        return recommendations;
    }
    getAnalysisStatus() {
        return {
            isAnalyzing: this.isAnalyzing,
            queueSize: this.analysisQueue.size
        };
    }
    stopAnalysis() {
        this.isAnalyzing = false;
        this.analysisQueue.clear();
        console.log('攻略分析已停止');
    }
}
export default StrategyAnalyzer;
