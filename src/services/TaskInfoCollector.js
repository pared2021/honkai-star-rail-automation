/**
 * 任务信息收集器
 * 负责收集和管理主线、支线任务的详细信息
 */
export class TaskInfoCollector {
    constructor(dbService) {
        Object.defineProperty(this, "dbService", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "collectionQueue", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: new Map()
        });
        Object.defineProperty(this, "isCollecting", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: false
        });
        this.dbService = dbService;
    }
    /**
     * 开始收集任务信息
     */
    async startCollection() {
        if (this.isCollecting) {
            console.log('任务信息收集已在进行中');
            return;
        }
        this.isCollecting = true;
        console.log('开始收集任务信息...');
        try {
            // 收集主线任务
            await this.collectMainQuests();
            // 收集支线任务
            await this.collectSideQuests();
            // 收集日常任务
            await this.collectDailyQuests();
            // 收集活动任务
            await this.collectEventQuests();
            console.log('任务信息收集完成');
        }
        catch (error) {
            console.error('任务信息收集失败:', error);
            throw error;
        }
        finally {
            this.isCollecting = false;
        }
    }
    /**
     * 收集主线任务信息
     */
    async collectMainQuests() {
        console.log('正在收集主线任务信息...');
        const mainQuests = await this.getMainQuestData();
        for (const quest of mainQuests) {
            await this.processTaskInfo(quest);
        }
    }
    /**
     * 收集支线任务信息
     */
    async collectSideQuests() {
        console.log('正在收集支线任务信息...');
        const sideQuests = await this.getSideQuestData();
        for (const quest of sideQuests) {
            await this.processTaskInfo(quest);
        }
    }
    /**
     * 收集日常任务信息
     */
    async collectDailyQuests() {
        console.log('正在收集日常任务信息...');
        const dailyQuests = await this.getDailyQuestData();
        for (const quest of dailyQuests) {
            await this.processTaskInfo(quest);
        }
    }
    /**
     * 收集活动任务信息
     */
    async collectEventQuests() {
        console.log('正在收集活动任务信息...');
        const eventQuests = await this.getEventQuestData();
        for (const quest of eventQuests) {
            await this.processTaskInfo(quest);
        }
    }
    /**
     * 处理任务信息
     */
    async processTaskInfo(taskData) {
        try {
            const taskInfo = {
                taskName: taskData.name,
                taskType: taskData.type,
                name: taskData.name, // 别名映射
                type: taskData.type, // 别名映射
                description: taskData.description,
                prerequisites: taskData.requirements || [],
                rewards: taskData.rewards || [],
                difficulty: taskData.difficulty || 'easy',
                estimatedTime: taskData.estimatedTime || 0,
                location: taskData.location || '',
                npcName: taskData.npcName,
                chapter: taskData.chapter,
                questLine: taskData.questLine,
                isRepeatable: taskData.isRepeatable || false,
                collectTime: new Date()
            };
            // 检查是否已存在
            const existingTasks = await this.dbService.getTaskInfos();
            const existingTask = existingTasks.find(t => t.taskType === taskInfo.taskType &&
                t.taskName === taskInfo.taskName);
            if (existingTask) {
                // 更新现有任务信息
                await this.dbService.updateTaskInfo(existingTask.id, {
                    ...taskInfo,
                    lastUpdated: new Date()
                });
                console.log(`更新任务信息: ${taskInfo.taskName}`);
            }
            else {
                // 创建新任务信息
                await this.dbService.createTaskInfo(taskInfo);
                console.log(`收集新任务信息: ${taskInfo.taskName}`);
            }
        }
        catch (error) {
            console.error(`处理任务信息失败: ${taskData.name}`, error);
        }
    }
    /**
     * 获取主线任务数据
     */
    async getMainQuestData() {
        // 模拟从游戏数据或API获取主线任务信息
        return [
            {
                name: '开拓之旅',
                type: 'main',
                category: '主线剧情',
                description: '跟随开拓者的脚步，探索星穹铁道的奥秘',
                requirements: ['完成新手教程'],
                rewards: [
                    { type: 'exp', amount: 1000, name: '经验值' },
                    { type: 'credits', amount: 500, name: '信用点' }
                ],
                difficulty: 'easy',
                estimatedTime: 30,
                prerequisites: [],
                location: '空间站「黑塔」',
                npcName: '艾丝妲',
                isRepeatable: false,
                isDaily: false,
                isWeekly: false,
                version: '1.0',
                tags: ['新手', '剧情', '必做']
            },
            {
                name: '雅利洛-VI的冒险',
                type: 'main',
                category: '主线剧情',
                description: '前往雅利洛-VI星球，解决当地的危机',
                requirements: ['完成开拓之旅'],
                rewards: [
                    { type: 'exp', amount: 2000, name: '经验值' },
                    { type: 'credits', amount: 1000, name: '信用点' },
                    { type: 'items', amount: 1, name: '4星光锥' }
                ],
                difficulty: 'medium',
                estimatedTime: 120,
                prerequisites: ['开拓之旅'],
                location: '雅利洛-VI',
                npcName: '布洛妮娅',
                isRepeatable: false,
                isDaily: false,
                isWeekly: false,
                version: '1.0',
                tags: ['主线', '剧情', '重要']
            }
        ];
    }
    /**
     * 获取支线任务数据
     */
    async getSideQuestData() {
        return [
            {
                name: '研究员的委托',
                type: 'side',
                category: '支线任务',
                description: '帮助研究员收集实验材料',
                requirements: ['到达空间站'],
                rewards: [
                    { type: 'exp', amount: 500, name: '经验值' },
                    { type: 'credits', amount: 200, name: '信用点' },
                    { type: 'materials', amount: 3, name: '基础材料' }
                ],
                difficulty: 'easy',
                estimatedTime: 15,
                prerequisites: [],
                location: '空间站「黑塔」',
                npcName: '研究员A',
                isRepeatable: true,
                isDaily: false,
                isWeekly: false,
                version: '1.0',
                tags: ['支线', '材料', '可重复']
            },
            {
                name: '迷失的记忆',
                type: 'side',
                category: '支线任务',
                description: '帮助NPC找回失去的记忆碎片',
                requirements: ['完成开拓之旅'],
                rewards: [
                    { type: 'exp', amount: 800, name: '经验值' },
                    { type: 'credits', amount: 400, name: '信用点' },
                    { type: 'items', amount: 1, name: '记忆光锥' }
                ],
                difficulty: 'medium',
                estimatedTime: 45,
                prerequisites: ['开拓之旅'],
                location: '雅利洛-VI',
                npcName: '失忆者',
                isRepeatable: false,
                isDaily: false,
                isWeekly: false,
                version: '1.0',
                tags: ['支线', '剧情', '奖励丰富']
            }
        ];
    }
    /**
     * 获取日常任务数据
     */
    async getDailyQuestData() {
        return [
            {
                name: '每日训练',
                type: 'daily',
                category: '日常任务',
                description: '完成每日的战斗训练',
                requirements: ['角色等级≥10'],
                rewards: [
                    { type: 'exp', amount: 300, name: '经验值' },
                    { type: 'credits', amount: 100, name: '信用点' },
                    { type: 'materials', amount: 2, name: '训练材料' }
                ],
                difficulty: 'easy',
                estimatedTime: 10,
                prerequisites: [],
                location: '任意地点',
                npcName: null,
                isRepeatable: true,
                isDaily: true,
                isWeekly: false,
                version: '1.0',
                tags: ['日常', '战斗', '经验']
            },
            {
                name: '材料收集',
                type: 'daily',
                category: '日常任务',
                description: '收集指定的升级材料',
                requirements: ['解锁材料副本'],
                rewards: [
                    { type: 'exp', amount: 200, name: '经验值' },
                    { type: 'materials', amount: 5, name: '升级材料' }
                ],
                difficulty: 'easy',
                estimatedTime: 15,
                prerequisites: [],
                location: '材料副本',
                npcName: null,
                isRepeatable: true,
                isDaily: true,
                isWeekly: false,
                version: '1.0',
                tags: ['日常', '材料', '副本']
            }
        ];
    }
    /**
     * 获取活动任务数据
     */
    async getEventQuestData() {
        return [
            {
                name: '限时活动：星海探索',
                type: 'event',
                category: '限时活动',
                description: '参与限时活动，获得丰厚奖励',
                requirements: ['活动期间', '角色等级≥20'],
                rewards: [
                    { type: 'exp', amount: 1500, name: '经验值' },
                    { type: 'credits', amount: 800, name: '信用点' },
                    { type: 'items', amount: 1, name: '限定光锥' },
                    { type: 'stellar_jade', amount: 100, name: '活动代币' }
                ],
                difficulty: 'hard',
                estimatedTime: 60,
                prerequisites: [],
                location: '活动副本',
                npcName: '活动NPC',
                isRepeatable: true,
                isDaily: false,
                isWeekly: false,
                version: '1.1',
                tags: ['活动', '限时', '高奖励']
            }
        ];
    }
    /**
     * 获取收集状态
     */
    getCollectionStatus() {
        return {
            isCollecting: this.isCollecting,
            queueSize: this.collectionQueue.size
        };
    }
    /**
     * 停止收集
     */
    stopCollection() {
        this.isCollecting = false;
        this.collectionQueue.clear();
        console.log('任务信息收集已停止');
    }
    /**
     * 获取已收集的任务统计
     */
    async getCollectionStats() {
        const allTasks = await this.dbService.getTaskInfos();
        const stats = {
            total: allTasks.length,
            byType: {},
            byCategory: {},
            byStatus: {}
        };
        allTasks.forEach(task => {
            // 按类型统计
            stats.byType[task.taskType] = (stats.byType[task.taskType] || 0) + 1;
            // 按难度统计
            stats.byCategory[task.difficulty] = (stats.byCategory[task.difficulty] || 0) + 1;
            // 按是否可重复统计
            const status = task.isRepeatable ? 'repeatable' : 'one_time';
            stats.byStatus[status] = (stats.byStatus[status] || 0) + 1;
        });
        return stats;
    }
}
export default TaskInfoCollector;
