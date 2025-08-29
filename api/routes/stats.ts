// 统计数据API路由
import express, { Response } from 'express';
import { ExtendedRequest } from '../types/index.js';

const router = express.Router();

// 获取账号统计数据
router.get('/accounts/:accountId?', async (req: ExtendedRequest, res: Response) => {
  try {
    const { accountId } = req.params;
    const dbService = req.dbService;
    
    if (accountId) {
      // 获取特定账号的统计数据
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
    } else {
      // 获取所有账号的统计数据
      const accounts = await dbService.getAccounts();
      const statsPromises = accounts.map(account => 
        dbService.getAccountStats(account.id)
      );
      
      const allStats = await Promise.all(statsPromises);
      const validStats = allStats.filter(stats => stats !== null);
      
      res.json({
        success: true,
        data: validStats
      });
    }
  } catch (error) {
    console.error('获取账号统计数据失败:', error);
    res.status(500).json({
      success: false,
      message: '获取账号统计数据失败'
    });
  }
});

// 获取任务统计概览
router.get('/tasks/overview', async (req: ExtendedRequest, res: Response) => {
  try {
    const { accountId, startDate, endDate } = req.query;
    const dbService = req.dbService;
    
    // 获取任务列表
    let tasks = await dbService.getTasks(accountId as string);
    
    // 按日期范围过滤
    if (startDate || endDate) {
      tasks = tasks.filter(task => {
        const taskDate = new Date(task.createdAt);
        if (startDate && taskDate < new Date(startDate as string)) return false;
        if (endDate && taskDate > new Date(endDate as string)) return false;
        return true;
      });
    }
    
    // 统计数据
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
        .filter(t => t.endTime && t.startTime)
        .reduce((sum, t) => {
          const duration = new Date(t.endTime!).getTime() - new Date(t.startTime!).getTime();
          return sum + duration;
        }, 0),
      averageDuration: 0
    };
    
    // 计算平均耗时
    const completedTasks = tasks.filter(t => t.endTime && t.startTime);
    if (completedTasks.length > 0) {
      overview.averageDuration = overview.totalDuration / completedTasks.length;
    }
    
    res.json({
      success: true,
      data: overview
    });
  } catch (error) {
    console.error('获取任务统计概览失败:', error);
    res.status(500).json({
      success: false,
      message: '获取任务统计概览失败'
    });
  }
});

// 获取每日任务统计
router.get('/tasks/daily', async (req: ExtendedRequest, res: Response) => {
  try {
    const { accountId, days = 7 } = req.query;
    const dbService = req.dbService;
    
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - parseInt(days as string));
    
    let tasks = await dbService.getTasks(accountId as string);
    
    // 按日期范围过滤
    tasks = tasks.filter(task => {
      const taskDate = new Date(task.createdAt);
      return taskDate >= startDate && taskDate <= endDate;
    });
    
    // 按日期分组统计
    const dailyStats: { [date: string]: {
      date: string;
      total: number;
      completed: number;
      failed: number;
      byType: {
        daily: number;
        main: number;
        side: number;
        custom: number;
      };
    } } = {};
    
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
  } catch (error) {
    console.error('获取每日任务统计失败:', error);
    res.status(500).json({
      success: false,
      message: '获取每日任务统计失败'
    });
  }
});

// 更新账号统计数据
router.post('/accounts/:accountId', async (req: ExtendedRequest, res: Response) => {
  try {
    const { accountId } = req.params;
    const updates = req.body;
    const dbService = req.dbService;
    
    // 检查账号是否存在
    const account = await dbService.getAccountById(accountId);
    if (!account) {
      return res.status(404).json({
        success: false,
        message: '账号不存在'
      });
    }
    
    // 获取现有统计数据
    let stats = await dbService.getAccountStats(accountId);
    
    if (stats) {
      // 更新现有统计数据
      const success = await dbService.updateAccountStats(accountId, new Date().toISOString().split('T')[0], updates);
      if (success) {
        stats = await dbService.getAccountStats(accountId);
        res.json({
          success: true,
          data: stats,
          message: '统计数据更新成功'
        });
      } else {
        res.status(400).json({
          success: false,
          message: '统计数据更新失败'
        });
      }
    } else {
      // 创建新的统计数据
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
  } catch (error) {
    console.error('更新账号统计数据失败:', error);
    res.status(500).json({
      success: false,
      message: '更新账号统计数据失败'
    });
  }
});

// 获取系统整体统计
router.get('/system', async (req: ExtendedRequest, res: Response) => {
  try {
    const dbService = req.dbService;
    
    // 模拟系统统计数据
    const systemStats = {
      cpu: 45,
      memory: 60,
      disk: 30,
      network: 25
    };
    
    res.json({
      success: true,
      data: systemStats
    });
  } catch (error) {
    console.error('获取系统统计失败:', error);
    res.status(500).json({
      success: false,
      message: '获取系统统计失败'
    });
  }
});

// 获取任务日志统计
router.get('/tasks/logs/:accountId', async (req: ExtendedRequest, res: Response) => {
  try {
    const { accountId } = req.params;
    const { startDate } = req.query;
    const dbService = req.dbService;
    
    const results = dbService.executeQuery(`
      SELECT 
        DATE(createdAt) as date,
        COUNT(*) as count,
        AVG(duration) as avgDuration
      FROM task_logs 
      WHERE accountId = ? AND createdAt >= ?
      GROUP BY DATE(createdAt)
      ORDER BY date DESC
    `, [accountId, startDate]) as Array<{
      date: string;
      count: number;
      avgDuration: number;
    }>;
    
    res.json({
      success: true,
      data: results
    });
  } catch (error) {
    console.error('获取任务日志统计失败:', error);
    res.status(500).json({
      success: false,
      message: '获取任务日志统计失败'
    });
  }
});

// 获取任务类型统计
router.get('/tasks/types/:accountId', async (req: ExtendedRequest, res: Response) => {
  try {
    const { accountId } = req.params;
    const { startDate } = req.query;
    const dbService = req.dbService;
    
    const results = dbService.executeQuery(`
      SELECT 
        taskType,
        COUNT(*) as count,
        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successCount,
        AVG(duration) as avgDuration
      FROM task_logs 
      WHERE accountId = ? AND createdAt >= ?
      GROUP BY taskType
    `, [accountId, startDate]) as Array<{
      taskType: string;
      count: number;
      successCount: number;
      avgDuration: number;
    }>;
    
    res.json({
      success: true,
      data: results
    });
  } catch (error) {
    console.error('获取任务类型统计失败:', error);
    res.status(500).json({
      success: false,
      message: '获取任务类型统计失败'
    });
  }
});

// 获取账号任务汇总
router.get('/accounts/:accountId/summary', async (req: ExtendedRequest, res: Response) => {
  try {
    const { accountId } = req.params;
    const dbService = req.dbService;
    
    const result = dbService.executeQuerySingle(`
      SELECT 
        COUNT(*) as totalTasks,
        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completedTasks,
        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failedTasks,
        AVG(duration) as avgDuration,
        MAX(createdAt) as lastTaskTime
      FROM task_logs 
      WHERE accountId = ?
    `, [accountId]) as {
      totalTasks: number;
      completedTasks: number;
      failedTasks: number;
      avgDuration: number;
      lastTaskTime: string;
    };
    
    res.json({
      success: true,
      data: result
    });
  } catch (error) {
    console.error('获取账号任务汇总失败:', error);
    res.status(500).json({
      success: false,
      message: '获取账号任务汇总失败'
    });
  }
});

export { router as statsRoutes };