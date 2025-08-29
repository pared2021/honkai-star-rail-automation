import express from 'express';
const router = express.Router();
router.get('/accounts/:accountId?', async (req, res) => {
    try {
        const { accountId } = req.params;
        const dbService = req.dbService;
        if (accountId) {
            const stats = await dbService.getAccountStats(accountId);
            if (!stats) {
                return res.status(404).json({
                    success: false,
                    message: '账号统计数据不存在'
                });
            }
            res.json({
                success: true,
                data: stats
            });
        }
        else {
            const accounts = await dbService.getAccounts();
            const statsPromises = accounts.map(account => dbService.getAccountStats(account.id));
            const allStats = await Promise.all(statsPromises);
            const validStats = allStats.filter(stats => stats !== null);
            res.json({
                success: true,
                data: validStats
            });
        }
    }
    catch (error) {
        console.error('获取账号统计数据失败:', error);
        res.status(500).json({
            success: false,
            message: '获取账号统计数据失败'
        });
    }
});
router.get('/tasks/overview', async (req, res) => {
    try {
        const { accountId, startDate, endDate } = req.query;
        const dbService = req.dbService;
        let tasks = await dbService.getTasks(accountId);
        if (startDate || endDate) {
            tasks = tasks.filter(task => {
                const taskDate = new Date(task.createdAt);
                if (startDate && taskDate < new Date(startDate))
                    return false;
                if (endDate && taskDate > new Date(endDate))
                    return false;
                return true;
            });
        }
        const overview = {
            total: tasks.length,
            completed: tasks.filter(t => t.status === 'completed').length,
            failed: tasks.filter(t => t.status === 'failed').length,
            running: tasks.filter(t => t.status === 'running').length,
            paused: tasks.filter(t => t.status === 'paused').length,
            byType: {
                daily: tasks.filter(t => t.taskType === 'daily').length,
                main: tasks.filter(t => t.taskType === 'main').length,
                side: tasks.filter(t => t.taskType === 'side').length,
                custom: tasks.filter(t => t.taskType === 'custom').length
            },
            totalDuration: tasks
                .filter(t => t.completedAt && t.startedAt)
                .reduce((sum, t) => {
                const duration = new Date(t.completedAt).getTime() - new Date(t.startedAt).getTime();
                return sum + duration;
            }, 0),
            averageDuration: 0
        };
        const completedTasks = tasks.filter(t => t.completedAt && t.startedAt);
        if (completedTasks.length > 0) {
            overview.averageDuration = overview.totalDuration / completedTasks.length;
        }
        res.json({
            success: true,
            data: overview
        });
    }
    catch (error) {
        console.error('获取任务统计概览失败:', error);
        res.status(500).json({
            success: false,
            message: '获取任务统计概览失败'
        });
    }
});
router.get('/tasks/daily', async (req, res) => {
    try {
        const { accountId, days = 7 } = req.query;
        const dbService = req.dbService;
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(endDate.getDate() - parseInt(days));
        let tasks = await dbService.getTasks(accountId);
        tasks = tasks.filter(task => {
            const taskDate = new Date(task.createdAt);
            return taskDate >= startDate && taskDate <= endDate;
        });
        const dailyStats = {};
        for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
            const dateStr = d.toISOString().split('T')[0];
            const dayTasks = tasks.filter(task => {
                const taskDate = new Date(task.createdAt).toISOString().split('T')[0];
                return taskDate === dateStr;
            });
            dailyStats[dateStr] = {
                date: dateStr,
                total: dayTasks.length,
                completed: dayTasks.filter(t => t.status === 'completed').length,
                failed: dayTasks.filter(t => t.status === 'failed').length,
                byType: {
                    daily: dayTasks.filter(t => t.taskType === 'daily').length,
                    main: dayTasks.filter(t => t.taskType === 'main').length,
                    side: dayTasks.filter(t => t.taskType === 'side').length,
                    custom: dayTasks.filter(t => t.taskType === 'custom').length
                }
            };
        }
        res.json({
            success: true,
            data: Object.values(dailyStats)
        });
    }
    catch (error) {
        console.error('获取每日任务统计失败:', error);
        res.status(500).json({
            success: false,
            message: '获取每日任务统计失败'
        });
    }
});
router.post('/accounts/:accountId', async (req, res) => {
    try {
        const { accountId } = req.params;
        const updates = req.body;
        const dbService = req.dbService;
        const account = await dbService.getAccountById(accountId);
        if (!account) {
            return res.status(404).json({
                success: false,
                message: '账号不存在'
            });
        }
        let stats = await dbService.getAccountStats(accountId);
        if (stats) {
            const success = await dbService.updateAccountStats(accountId, new Date().toISOString().split('T')[0], updates);
            if (success) {
                stats = await dbService.getAccountStats(accountId);
                res.json({
                    success: true,
                    data: stats,
                    message: '统计数据更新成功'
                });
            }
            else {
                res.status(400).json({
                    success: false,
                    message: '统计数据更新失败'
                });
            }
        }
        else {
            const newStats = await dbService.createAccountStats({
                accountId,
                date: new Date().toISOString().split('T')[0],
                ...updates
            });
            stats = [newStats];
            res.status(201).json({
                success: true,
                data: stats,
                message: '统计数据创建成功'
            });
        }
    }
    catch (error) {
        console.error('更新账号统计数据失败:', error);
        res.status(500).json({
            success: false,
            message: '更新账号统计数据失败'
        });
    }
});
router.get('/system', async (req, res) => {
    try {
        const { apiService } = req;
        const systemStats = await apiService.getSystemStats();
        res.json({
            success: true,
            data: systemStats
        });
    }
    catch (error) {
        console.error('获取系统统计失败:', error);
        res.status(500).json({
            success: false,
            message: '获取系统统计失败'
        });
    }
});
router.get('/tasks/logs/:accountId', async (req, res) => {
    try {
        const { accountId } = req.params;
        const { startDate } = req.query;
        const dbService = req.dbService;
        const db = dbService.db;
        const stmt = db.prepare(`
      SELECT 
        DATE(createdAt) as date,
        COUNT(*) as count,
        AVG(duration) as avgDuration
      FROM task_logs 
      WHERE accountId = ? AND createdAt >= ?
      GROUP BY DATE(createdAt)
      ORDER BY date DESC
    `);
        const results = stmt.all(accountId, startDate);
        res.json({
            success: true,
            data: results
        });
    }
    catch (error) {
        console.error('获取任务日志统计失败:', error);
        res.status(500).json({
            success: false,
            message: '获取任务日志统计失败'
        });
    }
});
router.get('/tasks/types/:accountId', async (req, res) => {
    try {
        const { accountId } = req.params;
        const { startDate } = req.query;
        const dbService = req.dbService;
        const db = dbService.db;
        const stmt = db.prepare(`
      SELECT 
        taskType,
        COUNT(*) as count,
        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successCount,
        AVG(duration) as avgDuration
      FROM task_logs 
      WHERE accountId = ? AND createdAt >= ?
      GROUP BY taskType
    `);
        const results = stmt.all(accountId, startDate);
        res.json({
            success: true,
            data: results
        });
    }
    catch (error) {
        console.error('获取任务类型统计失败:', error);
        res.status(500).json({
            success: false,
            message: '获取任务类型统计失败'
        });
    }
});
router.get('/accounts/:accountId/summary', async (req, res) => {
    try {
        const { accountId } = req.params;
        const dbService = req.dbService;
        const db = dbService.db;
        const stmt = db.prepare(`
      SELECT 
        COUNT(*) as totalTasks,
        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completedTasks,
        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failedTasks,
        AVG(duration) as avgDuration,
        MAX(createdAt) as lastTaskTime
      FROM task_logs 
      WHERE accountId = ?
    `);
        const result = stmt.get(accountId);
        res.json({
            success: true,
            data: result
        });
    }
    catch (error) {
        console.error('获取账号任务汇总失败:', error);
        res.status(500).json({
            success: false,
            message: '获取账号任务汇总失败'
        });
    }
});
export { router as statsRoutes };
