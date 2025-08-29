import express from 'express';
import { TaskInfoCollector } from '../../src/services/TaskInfoCollector.js';
import { StrategyAnalyzer } from '../../src/services/StrategyAnalyzer.js';
import { AutomationManager } from '../../src/services/AutomationManager.js';
import { StrategyDataInitializer } from '../../src/services/StrategyDataInitializer.js';
const router = express.Router();
router.get('/', async (req, res) => {
    try {
        const { accountId, status } = req.query;
        const dbService = req.dbService;
        let tasks = await dbService.getTasks(accountId);
        if (status) {
            tasks = tasks.filter(task => task.status === status);
        }
        res.json({
            success: true,
            data: tasks
        });
    }
    catch (error) {
        console.error('获取任务列表失败:', error);
        res.status(500).json({
            success: false,
            message: '获取任务列表失败'
        });
    }
});
router.get('/running', async (req, res) => {
    try {
        const apiService = req.apiService;
        const runningTasks = await apiService.getRunningTasks();
        res.json({
            success: true,
            data: runningTasks
        });
    }
    catch (error) {
        console.error('获取运行中任务失败:', error);
        res.status(500).json({
            success: false,
            message: '获取运行中任务失败'
        });
    }
});
router.get('/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const dbService = req.dbService;
        const task = await dbService.getTaskById(id);
        if (!task) {
            return res.status(404).json({
                success: false,
                message: '任务不存在'
            });
        }
        res.json({
            success: true,
            data: task
        });
    }
    catch (error) {
        console.error('获取任务失败:', error);
        res.status(500).json({
            success: false,
            message: '获取任务失败'
        });
    }
});
router.post('/start', async (req, res) => {
    try {
        const taskRequest = req.body;
        if (!taskRequest.accountId || !taskRequest.taskType) {
            return res.status(400).json({
                success: false,
                message: '账号ID和任务类型为必填项'
            });
        }
        const apiService = req.apiService;
        const task = await apiService.startTask(taskRequest);
        res.status(201).json({
            success: true,
            data: task,
            message: '任务启动成功'
        });
    }
    catch (error) {
        console.error('启动任务失败:', error);
        res.status(500).json({
            success: false,
            message: error instanceof Error ? error.message : '启动任务失败'
        });
    }
});
router.post('/:id/control', async (req, res) => {
    try {
        const { id } = req.params;
        const { action } = req.body;
        if (!action || !['pause', 'resume', 'stop'].includes(action)) {
            return res.status(400).json({
                success: false,
                message: '无效的操作类型'
            });
        }
        const apiService = req.apiService;
        const success = await apiService.controlTask({ taskId: id, action });
        if (success) {
            res.json({
                success: true,
                message: `任务${action === 'pause' ? '暂停' : action === 'resume' ? '恢复' : '停止'}成功`
            });
        }
        else {
            res.status(400).json({
                success: false,
                message: '任务控制失败'
            });
        }
    }
    catch (error) {
        console.error('控制任务失败:', error);
        res.status(500).json({
            success: false,
            message: '控制任务失败'
        });
    }
});
router.get('/:id/logs', async (req, res) => {
    try {
        const { id } = req.params;
        const { level } = req.query;
        const dbService = req.dbService;
        let logs = await dbService.getTaskLogs(id);
        if (level) {
            logs = logs.filter(log => log.level === level);
        }
        res.json({
            success: true,
            data: logs
        });
    }
    catch (error) {
        console.error('获取任务日志失败:', error);
        res.status(500).json({
            success: false,
            message: '获取任务日志失败'
        });
    }
});
router.delete('/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const dbService = req.dbService;
        const existingTask = await dbService.getTaskById(id);
        if (!existingTask) {
            return res.status(404).json({
                success: false,
                message: '任务不存在'
            });
        }
        if (existingTask.status === 'running') {
            return res.status(400).json({
                success: false,
                message: '无法删除正在运行的任务'
            });
        }
        const success = await dbService.deleteTask(id);
        if (success) {
            await dbService.deleteTaskLogs(id);
            res.json({
                success: true,
                message: '任务删除成功'
            });
        }
        else {
            res.status(400).json({
                success: false,
                message: '任务删除失败'
            });
        }
    }
    catch (error) {
        console.error('删除任务失败:', error);
        res.status(500).json({
            success: false,
            message: '删除任务失败'
        });
    }
});
router.get('/configs/:taskType?', async (req, res) => {
    try {
        const { taskType } = req.params;
        const dbService = req.dbService;
        const configs = await dbService.getTaskConfigs(taskType);
        res.json({
            success: true,
            data: configs
        });
    }
    catch (error) {
        console.error('获取任务配置失败:', error);
        res.status(500).json({
            success: false,
            message: '获取任务配置失败'
        });
    }
});
router.post('/configs', async (req, res) => {
    try {
        const { name, taskType, config, isDefault = false } = req.body;
        if (!name || !taskType || !config) {
            return res.status(400).json({
                success: false,
                message: '配置名称、任务类型和配置内容为必填项'
            });
        }
        const dbService = req.dbService;
        const taskConfig = await dbService.createTaskConfig({
            configName: name,
            configData: config,
            isDefault,
            taskType: 'main'
        });
        res.status(201).json({
            success: true,
            data: taskConfig,
            message: '任务配置创建成功'
        });
    }
    catch (error) {
        console.error('创建任务配置失败:', error);
        res.status(500).json({
            success: false,
            message: '创建任务配置失败'
        });
    }
});
router.get('/info', async (req, res) => {
    try {
        const { taskType, category, collectionStatus } = req.query;
        const dbService = req.dbService;
        const filters = {};
        if (taskType)
            filters.type = taskType;
        if (category)
            filters.category = category;
        if (collectionStatus)
            filters.collectionStatus = collectionStatus;
        const taskInfos = await dbService.getTaskInfos(filters);
        res.json({
            success: true,
            data: taskInfos
        });
    }
    catch (error) {
        console.error('获取任务信息失败:', error);
        res.status(500).json({
            success: false,
            message: '获取任务信息失败'
        });
    }
});
router.post('/info/collect', async (req, res) => {
    try {
        const { taskTypes = ['main', 'side', 'daily', 'event'] } = req.body;
        const dbService = req.dbService;
        const collector = new TaskInfoCollector(dbService);
        await collector.startCollection();
        res.json({
            success: true,
            message: '任务信息收集已启动'
        });
    }
    catch (error) {
        console.error('启动任务信息收集失败:', error);
        res.status(500).json({
            success: false,
            message: '启动任务信息收集失败'
        });
    }
});
router.get('/info/collect/status', async (req, res) => {
    try {
        const dbService = req.dbService;
        const collector = new TaskInfoCollector(dbService);
        const status = await collector.getCollectionStatus();
        res.json({
            success: true,
            data: status
        });
    }
    catch (error) {
        console.error('获取收集状态失败:', error);
        res.status(500).json({
            success: false,
            message: '获取收集状态失败'
        });
    }
});
router.get('/strategies', async (req, res) => {
    try {
        const { taskId } = req.query;
        const dbService = req.dbService;
        const strategies = await dbService.getStrategies({ taskInfoId: taskId });
        res.json({
            success: true,
            data: strategies
        });
    }
    catch (error) {
        console.error('获取攻略列表失败:', error);
        res.status(500).json({
            success: false,
            message: '获取攻略列表失败'
        });
    }
});
router.post('/strategies/analyze', async (req, res) => {
    try {
        const { taskId, iterations = 5 } = req.body;
        if (!taskId) {
            return res.status(400).json({
                success: false,
                message: '任务ID为必填项'
            });
        }
        const dbService = req.dbService;
        const analyzer = new StrategyAnalyzer(dbService);
        const result = await analyzer.startAnalysis(taskId, iterations);
        res.json({
            success: true,
            data: result,
            message: '攻略分析完成'
        });
    }
    catch (error) {
        console.error('攻略分析失败:', error);
        res.status(500).json({
            success: false,
            message: '攻略分析失败'
        });
    }
});
router.get('/strategies/:taskId/best', async (req, res) => {
    try {
        const { taskId } = req.params;
        const dbService = req.dbService;
        const strategies = await dbService.getStrategies({ taskInfoId: taskId });
        const bestStrategy = strategies.length > 0 ? strategies[0] : null;
        if (!bestStrategy) {
            return res.status(404).json({
                success: false,
                message: '未找到最优攻略'
            });
        }
        res.json({
            success: true,
            data: bestStrategy
        });
    }
    catch (error) {
        console.error('获取最优攻略失败:', error);
        res.status(500).json({
            success: false,
            message: '获取最优攻略失败'
        });
    }
});
router.get('/strategies/:strategyId/evaluations', async (req, res) => {
    try {
        const { strategyId } = req.params;
        const dbService = req.dbService;
        const evaluations = await dbService.getStrategyEvaluations(strategyId);
        res.json({
            success: true,
            data: evaluations
        });
    }
    catch (error) {
        console.error('获取攻略评估失败:', error);
        res.status(500).json({
            success: false,
            message: '获取攻略评估失败'
        });
    }
});
router.get('/automation/config', async (req, res) => {
    try {
        const { accountId = 'default' } = req.query;
        const dbService = req.dbService;
        const config = await dbService.getAutomationConfig(accountId);
        res.json({
            success: true,
            data: config
        });
    }
    catch (error) {
        console.error('获取自动化配置失败:', error);
        res.status(500).json({
            success: false,
            message: '获取自动化配置失败'
        });
    }
});
router.put('/automation/config', async (req, res) => {
    try {
        const config = req.body;
        const { accountId = 'default' } = req.body;
        const dbService = req.dbService;
        await dbService.updateAutomationConfig(accountId, config);
        res.json({
            success: true,
            message: '自动化配置更新成功'
        });
    }
    catch (error) {
        console.error('更新自动化配置失败:', error);
        res.status(500).json({
            success: false,
            message: '更新自动化配置失败'
        });
    }
});
router.post('/automation/start', async (req, res) => {
    try {
        const { config, accountId = 'default' } = req.body;
        const dbService = req.dbService;
        const automationManager = new AutomationManager(dbService, accountId);
        await automationManager.startAutomation(config);
        res.json({
            success: true,
            message: '自动化管理启动成功'
        });
    }
    catch (error) {
        console.error('启动自动化管理失败:', error);
        res.status(500).json({
            success: false,
            message: error instanceof Error ? error.message : '启动自动化管理失败'
        });
    }
});
router.post('/automation/stop', async (req, res) => {
    try {
        const dbService = req.dbService;
        const automationManager = new AutomationManager(dbService);
        await automationManager.stopAutomation();
        res.json({
            success: true,
            message: '自动化管理停止成功'
        });
    }
    catch (error) {
        console.error('停止自动化管理失败:', error);
        res.status(500).json({
            success: false,
            message: '停止自动化管理失败'
        });
    }
});
router.get('/automation/status', async (req, res) => {
    try {
        const dbService = req.dbService;
        const automationManager = new AutomationManager(dbService);
        const status = automationManager.getAutomationStatus();
        res.json({
            success: true,
            data: status
        });
    }
    catch (error) {
        console.error('获取自动化状态失败:', error);
        res.status(500).json({
            success: false,
            message: '获取自动化状态失败'
        });
    }
});
router.post('/automation/trigger/collect', async (req, res) => {
    try {
        const dbService = req.dbService;
        const automationManager = new AutomationManager(dbService);
        await automationManager.triggerTaskInfoCollection();
        res.json({
            success: true,
            message: '任务信息收集已触发'
        });
    }
    catch (error) {
        console.error('触发任务信息收集失败:', error);
        res.status(500).json({
            success: false,
            message: error instanceof Error ? error.message : '触发任务信息收集失败'
        });
    }
});
router.post('/automation/trigger/analyze', async (req, res) => {
    try {
        const { taskId } = req.body;
        const dbService = req.dbService;
        const automationManager = new AutomationManager(dbService);
        await automationManager.triggerStrategyAnalysis(taskId);
        res.json({
            success: true,
            message: '攻略分析已触发'
        });
    }
    catch (error) {
        console.error('触发攻略分析失败:', error);
        res.status(500).json({
            success: false,
            message: error instanceof Error ? error.message : '触发攻略分析失败'
        });
    }
});
router.get('/automation/statistics', async (req, res) => {
    try {
        const dbService = req.dbService;
        const automationManager = new AutomationManager(dbService);
        const statistics = automationManager.getStatistics();
        res.json({
            success: true,
            data: statistics
        });
    }
    catch (error) {
        console.error('获取自动化统计信息失败:', error);
        res.status(500).json({
            success: false,
            message: '获取自动化统计信息失败'
        });
    }
});
router.post('/automation/clear-errors', async (req, res) => {
    try {
        const dbService = req.dbService;
        const automationManager = new AutomationManager(dbService);
        automationManager.clearErrors();
        res.json({
            success: true,
            message: '错误日志已清理'
        });
    }
    catch (error) {
        console.error('清理错误日志失败:', error);
        res.status(500).json({
            success: false,
            message: '清理错误日志失败'
        });
    }
});
router.get('/strategies/preset', async (req, res) => {
    try {
        const { source } = req.query;
        const dbService = req.dbService;
        const strategies = await dbService.getStrategiesBySource(source || 'preset');
        res.json({
            success: true,
            data: strategies
        });
    }
    catch (error) {
        console.error('获取预置攻略失败:', error);
        res.status(500).json({
            success: false,
            message: '获取预置攻略失败'
        });
    }
});
router.get('/strategies/stats', async (req, res) => {
    try {
        const dbService = req.dbService;
        const stats = await dbService.getStrategyStats();
        res.json({
            success: true,
            data: stats
        });
    }
    catch (error) {
        console.error('获取攻略统计信息失败:', error);
        res.status(500).json({
            success: false,
            message: '获取攻略统计信息失败'
        });
    }
});
router.get('/strategies/preset/stats', async (req, res) => {
    try {
        const dbService = req.dbService;
        const initializer = new StrategyDataInitializer(dbService);
        const stats = await initializer.getPresetDataStats();
        res.json({
            success: true,
            data: stats
        });
    }
    catch (error) {
        console.error('获取预置攻略统计信息失败:', error);
        res.status(500).json({
            success: false,
            message: '获取预置攻略统计信息失败'
        });
    }
});
router.post('/strategies/preset/reinitialize', async (req, res) => {
    try {
        const dbService = req.dbService;
        const initializer = new StrategyDataInitializer(dbService);
        const result = await initializer.initializePresetData();
        res.json({
            success: true,
            data: result,
            message: '预置攻略数据重新初始化成功'
        });
    }
    catch (error) {
        console.error('重新初始化预置攻略数据失败:', error);
        res.status(500).json({
            success: false,
            message: '重新初始化预置攻略数据失败'
        });
    }
});
router.delete('/strategies/preset/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const dbService = req.dbService;
        const strategies = await dbService.getStrategiesBySource('preset');
        const strategy = strategies.find(s => s.id === id);
        if (!strategy) {
            return res.status(404).json({
                success: false,
                message: '预置攻略不存在'
            });
        }
        const success = await dbService.deleteStrategy(id);
        if (success) {
            res.json({
                success: true,
                message: '预置攻略删除成功'
            });
        }
        else {
            res.status(400).json({
                success: false,
                message: '预置攻略删除失败'
            });
        }
    }
    catch (error) {
        console.error('删除预置攻略失败:', error);
        res.status(500).json({
            success: false,
            message: '删除预置攻略失败'
        });
    }
});
router.put('/strategies/preset/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const { name, taskType, description, steps } = req.body;
        const dbService = req.dbService;
        if (!name || !taskType || !steps) {
            return res.status(400).json({
                success: false,
                message: '攻略名称、任务类型和攻略步骤为必填项'
            });
        }
        const strategies = await dbService.getStrategiesBySource('preset');
        const strategy = strategies.find(s => s.id === id);
        if (!strategy) {
            return res.status(404).json({
                success: false,
                message: '预置攻略不存在'
            });
        }
        const updatedStrategy = await dbService.updateStrategy(id, {
            strategyName: name,
            description,
            steps
        });
        res.json({
            success: true,
            data: updatedStrategy,
            message: '预置攻略更新成功'
        });
    }
    catch (error) {
        console.error('更新预置攻略失败:', error);
        res.status(500).json({
            success: false,
            message: '更新预置攻略失败'
        });
    }
});
export { router as taskRoutes };
