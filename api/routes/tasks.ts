// 任务管理API路由
import express, { Response } from 'express';
import { 
  TaskType,
  StartTaskRequest, 
  TaskControlRequest, 
  StartExecutionRequest,
  UpdateExecutionStepRequest,
  OptimizeStrategyRequest,
  SubmitFeedbackRequest,
  TriggerAnalysisRequest,
  ExtendedRequest
} from '../types/index.js';
import PerformanceDataCollector from '../../src/services/PerformanceDataCollector.js';
import IntelligentEvaluator from '../../src/services/IntelligentEvaluator.js';
import ExecutionTracker from '../../src/services/ExecutionTracker.js';
import { DatabaseService } from '../../src/services/DatabaseService.js';

const router = express.Router();

// 初始化服务实例（在路由处理器中动态创建）
function createServices(dbService: DatabaseService) {
  const performanceCollector = new PerformanceDataCollector(dbService);
  const intelligentEvaluator = new IntelligentEvaluator(performanceCollector, dbService);
  const executionTracker = new ExecutionTracker(performanceCollector, intelligentEvaluator, dbService);
  return { performanceCollector, executionTracker, intelligentEvaluator };
}

// 获取任务列表
router.get('/', async (req: ExtendedRequest, res: Response) => {
  try {
    const { accountId, status } = req.query;
    const dbService = req.dbService;
    const { performanceCollector, executionTracker, intelligentEvaluator } = createServices(dbService);
    
    let tasks = await dbService.getTasks(accountId as string);
    
    // 按状态过滤
    if (status) {
      tasks = tasks.filter(task => task.status === status);
    }
    
    res.json({
      success: true,
      data: tasks
    });
  } catch (error) {
    console.error('获取任务列表失败:', error);
    res.status(500).json({
      success: false,
      message: '获取任务列表失败'
    });
  }
});

// 获取运行中的任务
router.get('/running', async (req: ExtendedRequest, res: Response) => {
  try {
    const dbService = req.dbService;
    const { performanceCollector, executionTracker, intelligentEvaluator } = createServices(dbService);
    const runningTasks = await dbService.getTasks(); // 获取所有任务，后续可以过滤运行中的任务
    
    res.json({
      success: true,
      data: runningTasks
    });
  } catch (error) {
    console.error('获取运行中任务失败:', error);
    res.status(500).json({
      success: false,
      message: '获取运行中任务失败'
    });
  }
});

// 根据ID获取任务
router.get('/:id', async (req: ExtendedRequest, res: Response) => {
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
  } catch (error) {
    console.error('获取任务失败:', error);
    res.status(500).json({
      success: false,
      message: '获取任务失败'
    });
  }
});

// 启动新任务
router.post('/start', async (req: ExtendedRequest, res: Response) => {
  try {
    const dbService = req.dbService;
    const { performanceCollector, executionTracker, intelligentEvaluator } = createServices(dbService);
    const taskRequest: StartTaskRequest = req.body;
    
    // 验证必填字段
    if (!taskRequest.accountId || !taskRequest.taskType) {
      return res.status(400).json({
        success: false,
        message: '账号ID和任务类型为必填项'
      });
    }
    
    // 创建任务对象
    const task = {
      accountId: req.user?.id || 'default',
      name: `Task ${taskRequest.taskType}`,
      description: `Auto-generated task for ${taskRequest.taskType}`,
      type: taskRequest.taskType,
      status: 'pending' as const,
      difficulty: 'medium' as const,
      estimatedTime: 30,
      rewards: [],
      requirements: [],
      isAvailable: true,
      isCompleted: false,
      completionCount: 0,
      config: taskRequest.config || {},
      taskType: taskRequest.taskType as TaskType,
      updatedAt: new Date()
    };
    await dbService.createTask(task);
    
    res.status(201).json({
      success: true,
      data: task,
      message: '任务启动成功'
    });
  } catch (error) {
    console.error('启动任务失败:', error);
    res.status(500).json({
      success: false,
      message: error instanceof Error ? error.message : '启动任务失败'
    });
  }
});

// 控制任务（暂停/恢复/停止）
router.post('/:id/control', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const { action }: TaskControlRequest = req.body;
    
    if (!action || !['pause', 'resume', 'stop'].includes(action)) {
      return res.status(400).json({
        success: false,
        message: '无效的操作类型'
      });
    }
    
    const dbService = req.dbService;
    const { performanceCollector, executionTracker, intelligentEvaluator } = createServices(dbService);
    // 模拟任务控制操作
    const success = true; // 这里应该实现实际的任务控制逻辑
    
    if (success) {
      res.json({
        success: true,
        message: `任务${action === 'pause' ? '暂停' : action === 'resume' ? '恢复' : '停止'}成功`
      });
    } else {
      res.status(400).json({
        success: false,
        message: '任务控制失败'
      });
    }
  } catch (error) {
    console.error('控制任务失败:', error);
    res.status(500).json({
      success: false,
      message: '控制任务失败'
    });
  }
});

// 获取任务日志
router.get('/:id/logs', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const { level } = req.query;
    const dbService = req.dbService;
    
    let logs = await dbService.getTaskLogs(id);
    
    // 按日志级别过滤
    if (level) {
      logs = logs.filter(log => log.level === level);
    }
    
    res.json({
      success: true,
      data: logs
    });
  } catch (error) {
    console.error('获取任务日志失败:', error);
    res.status(500).json({
      success: false,
      message: '获取任务日志失败'
    });
  }
});

// 删除任务
router.delete('/:id', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const dbService = req.dbService;
    
    const success = await dbService.deleteTask(id);
    
    if (success) {
      res.json({
        success: true,
        message: '任务删除成功'
      });
    } else {
      res.status(404).json({
        success: false,
        message: '任务不存在'
      });
    }
  } catch (error) {
    console.error('删除任务失败:', error);
    res.status(500).json({
      success: false,
      message: '删除任务失败'
    });
  }
});

// ==================== 执行追踪相关接口 ====================

// 开始执行追踪
router.post('/executions/start', async (req: ExtendedRequest, res: Response) => {
  try {
    const { strategyId, accountId, options }: StartExecutionRequest = req.body;
    
    if (!strategyId || !accountId) {
      return res.status(400).json({
        success: false,
        message: '攻略ID和账户ID为必填项'
      });
    }
    
    // 获取策略信息
    const dbService = req.dbService;
    const strategy = await dbService.getStrategy(strategyId);
    
    if (!strategy) {
      return res.status(404).json({
        success: false,
        message: '攻略不存在'
      });
    }
    
    const { performanceCollector, executionTracker, intelligentEvaluator } = createServices(dbService);
    const executionId = await executionTracker.startExecution(strategyId, accountId, strategy);
    
    res.json({
      success: true,
      data: { executionId },
      message: '执行追踪已启动'
    });
  } catch (error) {
    console.error('启动执行追踪失败:', error);
    res.status(500).json({
      success: false,
      message: '启动执行追踪失败'
    });
  }
});

// 更新执行步骤
router.put('/executions/:id/step', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const stepData: UpdateExecutionStepRequest = req.body;
    
    if (!stepData.stepIndex || stepData.success === undefined) {
      return res.status(400).json({
        success: false,
        message: '步骤索引和执行结果为必填项'
      });
    }
    
    const dbService = req.dbService;
    const { performanceCollector, executionTracker, intelligentEvaluator } = createServices(dbService);
    await performanceCollector.recordStepComplete(id, stepData.stepId, stepData.success || false, stepData.error);
    
    res.json({
      success: true,
      message: '执行步骤已更新'
    });
  } catch (error) {
    console.error('更新执行步骤失败:', error);
    res.status(500).json({
      success: false,
      message: '更新执行步骤失败'
    });
  }
});

// 获取执行数据
router.get('/executions/:id', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const dbService = req.dbService;
    const { performanceCollector, executionTracker, intelligentEvaluator } = createServices(dbService);
    const executionData = await executionTracker.getExecutionStats();
    
    if (!executionData) {
      return res.status(404).json({
        success: false,
        message: '执行数据不存在'
      });
    }
    
    res.json({
      success: true,
      data: executionData
    });
  } catch (error) {
    console.error('获取执行数据失败:', error);
    res.status(500).json({
      success: false,
      message: '获取执行数据失败'
    });
  }
});

// ==================== 性能分析相关接口 ====================

// 获取攻略性能分析
router.get('/strategies/:id/performance', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const { timeRange, includeDetails } = req.query;
    
    const dbService = req.dbService;
    const { performanceCollector, executionTracker, intelligentEvaluator } = createServices(dbService);
    const analysis = await performanceCollector.getExecutionStats(id);
    
    res.json({
      success: true,
      data: analysis
    });
  } catch (error) {
    console.error('获取性能分析失败:', error);
    res.status(500).json({
      success: false,
      message: '获取性能分析失败'
    });
  }
});

// 触发攻略优化分析
router.post('/strategies/:id/optimize', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const { analysisType, options }: OptimizeStrategyRequest = req.body;
    
    const dbService = req.dbService;
    const { performanceCollector, executionTracker, intelligentEvaluator } = createServices(dbService);
    const evaluation = await intelligentEvaluator.evaluateStrategy(id);
    const recommendations = evaluation.optimizationSuggestions;
    
    res.json({
      success: true,
      data: recommendations,
      message: '优化建议生成成功'
    });
  } catch (error) {
    console.error('生成优化建议失败:', error);
    res.status(500).json({
      success: false,
      message: '生成优化建议失败'
    });
  }
});

// ==================== 用户反馈相关接口 ====================

// 提交用户反馈
router.post('/feedback', async (req: ExtendedRequest, res: Response) => {
  try {
    const feedbackData: SubmitFeedbackRequest = req.body;
    
    if (!feedbackData.strategyId || !feedbackData.rating) {
      return res.status(400).json({
        success: false,
        message: '攻略ID和评分为必填项'
      });
    }
    
    const dbService = req.dbService;
    const feedback = await dbService.createStrategyFeedback({
      ...feedbackData,
      userId: req.user?.id || 'anonymous',
      createdAt: new Date().toISOString()
    });
    
    // 触发智能评估更新
    const { performanceCollector, executionTracker, intelligentEvaluator } = createServices(dbService);
    await intelligentEvaluator.evaluateStrategy(feedbackData.strategyId);
    
    res.json({
      success: true,
      data: feedback,
      message: '反馈提交成功'
    });
  } catch (error) {
    console.error('提交反馈失败:', error);
    res.status(500).json({
      success: false,
      message: '提交反馈失败'
    });
  }
});

// 获取反馈列表
router.get('/feedback/:strategyId', async (req: ExtendedRequest, res: Response) => {
  try {
    const { strategyId } = req.params;
    const { limit, offset } = req.query;
    
    const dbService = req.dbService;
    const feedbacks = await dbService.getStrategyFeedbacks(strategyId, {
      limit: limit ? parseInt(limit as string) : 20
    });
    
    res.json({
      success: true,
      data: feedbacks
    });
  } catch (error) {
    console.error('获取反馈列表失败:', error);
    res.status(500).json({
      success: false,
      message: '获取反馈列表失败'
    });
  }
});

// ==================== 智能评估相关接口 ====================

// 获取智能评估结果
router.get('/evaluations/:strategyId', async (req: ExtendedRequest, res: Response) => {
  try {
    const { strategyId } = req.params;
    const dbService = req.dbService;
    const { performanceCollector, executionTracker, intelligentEvaluator } = createServices(dbService);
    const evaluation = await intelligentEvaluator.evaluateStrategy(strategyId);
    
    res.json({
      success: true,
      data: evaluation
    });
  } catch (error) {
    console.error('获取智能评估结果失败:', error);
    res.status(500).json({
      success: false,
      message: '获取智能评估结果失败'
    });
  }
});

// 触发实时分析
router.post('/evaluations/analyze', async (req: ExtendedRequest, res: Response) => {
  try {
    const { strategyIds, analysisType }: TriggerAnalysisRequest = req.body;
    
    if (!strategyIds || !Array.isArray(strategyIds)) {
      return res.status(400).json({
        success: false,
        message: '攻略ID列表为必填项'
      });
    }
    
    const dbService = req.dbService;
    const { performanceCollector, executionTracker, intelligentEvaluator } = createServices(dbService);
    const results = await Promise.all(
      strategyIds.map(id => intelligentEvaluator.evaluateStrategy(id))
    );
    
    res.json({
      success: true,
      data: results,
      message: '实时分析完成'
    });
  } catch (error) {
    console.error('触发实时分析失败:', error);
    res.status(500).json({
      success: false,
      message: '触发实时分析失败'
    });
  }
});

// 获取性能仪表板数据
router.get('/performance/dashboard/:strategyId', async (req: ExtendedRequest, res: Response) => {
  try {
    const { strategyId } = req.params;
    const { timeRange } = req.query;
    
    const dbService = req.dbService;
    const { performanceCollector, executionTracker, intelligentEvaluator } = createServices(dbService);
    const activeSessions = performanceCollector.getActiveSessions();
    const latestData = performanceCollector.getLatestData();
    const performanceHistory = performanceCollector.getPerformanceHistory(60); // 最近1小时
    
    const dashboardData = {
      activeSessions: activeSessions.filter(s => s.strategyId === strategyId),
      currentPerformance: latestData,
      performanceHistory,
      executionStats: await performanceCollector.getExecutionStats(strategyId)
    };
    
    res.json({
      success: true,
      data: dashboardData
    });
  } catch (error) {
    console.error('获取性能仪表板数据失败:', error);
    res.status(500).json({
      success: false,
      message: '获取性能仪表板数据失败'
    });
  }
});

// ==================== 性能数据收集相关接口 ====================

// 启动性能数据收集
router.post('/performance/start', async (req: ExtendedRequest, res: Response) => {
  try {
    const { strategyId, sessionConfig } = req.body;
    
    if (!strategyId) {
      return res.status(400).json({
        success: false,
        message: '攻略ID为必填项'
      });
    }
    
    const dbService = req.dbService;
    const { performanceCollector, executionTracker, intelligentEvaluator } = createServices(dbService);
    performanceCollector.startCollection();
    
    // 获取策略信息
    const strategy = await dbService.getStrategy(strategyId);
    if (!strategy) {
      return res.status(404).json({ success: false, message: '策略不存在' });
    }
    
    const sessionId = await performanceCollector.startExecutionSession(strategyId, req.body.accountId || 'default', strategy);
    
    res.json({
      success: true,
      data: { sessionId },
      message: '性能数据收集已启动'
    });
  } catch (error) {
    console.error('启动性能数据收集失败:', error);
    res.status(500).json({
      success: false,
      message: '启动性能数据收集失败'
    });
  }
});

// 停止性能数据收集
router.post('/performance/stop', async (req: ExtendedRequest, res: Response) => {
  try {
    const { sessionId } = req.body;
    
    const dbService = req.dbService;
    const { performanceCollector, executionTracker, intelligentEvaluator } = createServices(dbService);
    if (sessionId) {
      await performanceCollector.endExecutionSession(sessionId, 'completed');
    }
    
    performanceCollector.stopCollection();
    
    res.json({
      success: true,
      message: '性能数据收集已停止'
    });
  } catch (error) {
    console.error('停止性能数据收集失败:', error);
    res.status(500).json({
      success: false,
      message: '停止性能数据收集失败'
    });
  }
});

// 获取实时性能数据
router.get('/performance/realtime/:sessionId', async (req: ExtendedRequest, res: Response) => {
  try {
    const { sessionId } = req.params;
    const dbService = req.dbService;
    const { performanceCollector, executionTracker, intelligentEvaluator } = createServices(dbService);
    // 获取实时数据
    const data = performanceCollector.getLatestData();
    
    res.json({
      success: true,
      data
    });
  } catch (error) {
    console.error('获取实时性能数据失败:', error);
    res.status(500).json({
      success: false,
      message: '获取实时性能数据失败'
    });
  }
});

// 获取性能历史数据
router.get('/performance/history/:strategyId', async (req: ExtendedRequest, res: Response) => {
  try {
    const { strategyId } = req.params;
    const { timeRange, limit } = req.query;
    
    const dbService = req.dbService;
    const { performanceCollector, executionTracker, intelligentEvaluator } = createServices(dbService);
    // 获取性能历史数据
    const minutes = timeRange === '1h' ? 60 : timeRange === '6h' ? 360 : timeRange === '24h' ? 1440 : 60;
    const data = performanceCollector.getPerformanceHistory(minutes);
    
    res.json({
      success: true,
      data
    });
  } catch (error) {
    console.error('获取性能历史数据失败:', error);
    res.status(500).json({
      success: false,
      message: '获取性能历史数据失败'
    });
  }
});

// ==================== 任务信息管理相关接口 ====================

// 获取任务信息列表
router.get('/task-info', async (req: ExtendedRequest, res: Response) => {
  try {
    const { accountId, taskType, status, limit, offset } = req.query;
    const dbService = req.dbService;
    
    const taskInfos = await dbService.getTaskInfos({
      status: status as string,
      limit: limit ? parseInt(limit as string) : 50,
      offset: offset ? parseInt(offset as string) : 0
    });
    
    res.json({
      success: true,
      data: taskInfos
    });
  } catch (error) {
    console.error('获取任务信息列表失败:', error);
    res.status(500).json({
      success: false,
      message: '获取任务信息列表失败'
    });
  }
});

// 根据ID获取任务信息
router.get('/task-info/:id', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const dbService = req.dbService;
    
    const taskInfo = await dbService.getTaskInfoById(id);
    
    if (!taskInfo) {
      return res.status(404).json({
        success: false,
        message: '任务信息不存在'
      });
    }
    
    res.json({
      success: true,
      data: taskInfo
    });
  } catch (error) {
    console.error('获取任务信息失败:', error);
    res.status(500).json({
      success: false,
      message: '获取任务信息失败'
    });
  }
});

// 创建任务信息
router.post('/task-info', async (req: ExtendedRequest, res: Response) => {
  try {
    const taskInfoData = req.body;
    
    // 验证必填字段
    if (!taskInfoData.name || !taskInfoData.type) {
      return res.status(400).json({
        success: false,
        message: '任务名称和类型为必填项'
      });
    }
    
    const dbService = req.dbService;
    const taskInfo = await dbService.addTaskInfo({
      ...taskInfoData,
      createdAt: new Date(),
      updatedAt: new Date()
    });
    
    res.status(201).json({
      success: true,
      data: taskInfo,
      message: '任务信息创建成功'
    });
  } catch (error) {
    console.error('创建任务信息失败:', error);
    res.status(500).json({
      success: false,
      message: '创建任务信息失败'
    });
  }
});

// 更新任务信息
router.put('/task-info/:id', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const updateData = req.body;
    
    const dbService = req.dbService;
    
    // 检查任务信息是否存在
    const existingTaskInfo = await dbService.getTaskInfoById(id);
    if (!existingTaskInfo) {
      return res.status(404).json({
        success: false,
        message: '任务信息不存在'
      });
    }
    
    const updatedTaskInfo = await dbService.updateTaskInfo(id, {
      ...updateData,
      updatedAt: new Date()
    });
    
    res.json({
      success: true,
      data: updatedTaskInfo,
      message: '任务信息更新成功'
    });
  } catch (error) {
    console.error('更新任务信息失败:', error);
    res.status(500).json({
      success: false,
      message: '更新任务信息失败'
    });
  }
});

// 删除任务信息
router.delete('/task-info/:id', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const dbService = req.dbService;
    
    const success = await dbService.deleteTaskInfo(id);
    
    if (success) {
      res.json({
        success: true,
        message: '任务信息删除成功'
      });
    } else {
      res.status(404).json({
        success: false,
        message: '任务信息不存在'
      });
    }
  } catch (error) {
    console.error('删除任务信息失败:', error);
    res.status(500).json({
      success: false,
      message: '删除任务信息失败'
    });
  }
});

// 搜索任务信息
router.get('/task-info/search', async (req: ExtendedRequest, res: Response) => {
  try {
    const { query, filters } = req.query;
    
    if (!query) {
      return res.status(400).json({
        success: false,
        message: '搜索关键词为必填项'
      });
    }
    
    const dbService = req.dbService;
    const searchResults = await dbService.searchTaskInfos(query as string, filters ? JSON.parse(filters as string) : {});
    
    res.json({
      success: true,
      data: searchResults
    });
  } catch (error) {
    console.error('搜索任务信息失败:', error);
    res.status(500).json({
      success: false,
      message: '搜索任务信息失败'
    });
  }
});

// ==================== 攻略管理相关接口 ====================

// 获取攻略列表
router.get('/strategies', async (req: ExtendedRequest, res: Response) => {
  try {
    const { taskType, difficulty, status, limit, offset } = req.query;
    const dbService = req.dbService;
    
    const strategies = await dbService.getStrategies({
      difficulty: parseInt(difficulty as string) || 1,
      limit: limit ? parseInt(limit as string) : 50,
      offset: offset ? parseInt(offset as string) : 0
    });
    
    res.json({
      success: true,
      data: strategies
    });
  } catch (error) {
    console.error('获取攻略列表失败:', error);
    res.status(500).json({
      success: false,
      message: '获取攻略列表失败'
    });
  }
});

// 根据ID获取攻略详情
router.get('/strategies/:id', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const dbService = req.dbService;
    
    const strategy = await dbService.getStrategy(id);
    
    if (!strategy) {
      return res.status(404).json({
        success: false,
        message: '攻略不存在'
      });
    }
    
    res.json({
      success: true,
      data: strategy
    });
  } catch (error) {
    console.error('获取攻略详情失败:', error);
    res.status(500).json({
      success: false,
      message: '获取攻略详情失败'
    });
  }
});

// 创建攻略
router.post('/strategies', async (req: ExtendedRequest, res: Response) => {
  try {
    const strategyData = req.body;
    
    // 验证必填字段
    if (!strategyData.name || !strategyData.taskType || !strategyData.steps) {
      return res.status(400).json({
        success: false,
        message: '攻略名称、任务类型和步骤为必填项'
      });
    }
    
    const dbService = req.dbService;
    const strategy = await dbService.addStrategy({
      ...strategyData,
      createdAt: new Date(),
      updatedAt: new Date()
    });
    
    res.status(201).json({
      success: true,
      data: strategy,
      message: '攻略创建成功'
    });
  } catch (error) {
    console.error('创建攻略失败:', error);
    res.status(500).json({
      success: false,
      message: '创建攻略失败'
    });
  }
});

// 更新攻略
router.put('/strategies/:id', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const updateData = req.body;
    
    const dbService = req.dbService;
    
    // 检查攻略是否存在
    const existingStrategy = await dbService.getStrategy(id);
    if (!existingStrategy) {
      return res.status(404).json({
        success: false,
        message: '攻略不存在'
      });
    }
    
    const updatedStrategy = await dbService.updateStrategy(id, {
      ...updateData,
      updatedAt: new Date()
    });
    
    res.json({
      success: true,
      data: updatedStrategy,
      message: '攻略更新成功'
    });
  } catch (error) {
    console.error('更新攻略失败:', error);
    res.status(500).json({
      success: false,
      message: '更新攻略失败'
    });
  }
});

// 删除攻略
router.delete('/strategies/:id', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const dbService = req.dbService;
    
    const success = await dbService.deleteStrategy(id);
    
    if (success) {
      res.json({
        success: true,
        message: '攻略删除成功'
      });
    } else {
      res.status(404).json({
        success: false,
        message: '攻略不存在'
      });
    }
  } catch (error) {
    console.error('删除攻略失败:', error);
    res.status(500).json({
      success: false,
      message: '删除攻略失败'
    });
  }
});

// 复制攻略
router.post('/strategies/:id/clone', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const { name } = req.body;
    
    const dbService = req.dbService;
    
    const originalStrategy = await dbService.getStrategy(id);
    if (!originalStrategy) {
      return res.status(404).json({
        success: false,
        message: '原攻略不存在'
      });
    }
    
    const clonedStrategy = await dbService.cloneStrategy(id, name || `${(originalStrategy as any).name || (originalStrategy as any).strategyName || 'Unknown Strategy'} (副本)`);
    
    res.status(201).json({
      success: true,
      data: clonedStrategy,
      message: '攻略复制成功'
    });
  } catch (error) {
    console.error('复制攻略失败:', error);
    res.status(500).json({
      success: false,
      message: '复制攻略失败'
    });
  }
});

// 获取攻略步骤
router.get('/strategies/:id/steps', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const dbService = req.dbService;
    
    const steps = await dbService.getStrategySteps(id);
    
    res.json({
      success: true,
      data: steps
    });
  } catch (error) {
    console.error('获取攻略步骤失败:', error);
    res.status(500).json({
      success: false,
      message: '获取攻略步骤失败'
    });
  }
});

// 更新攻略步骤
router.put('/strategies/:id/steps', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const { steps } = req.body;
    
    if (!Array.isArray(steps)) {
      return res.status(400).json({
        success: false,
        message: '步骤数据格式错误'
      });
    }
    
    const dbService = req.dbService;
    const updatedSteps = await dbService.updateStrategy(id, { steps });
    
    res.json({
      success: true,
      data: updatedSteps,
      message: '攻略步骤更新成功'
    });
  } catch (error) {
    console.error('更新攻略步骤失败:', error);
    res.status(500).json({
      success: false,
      message: '更新攻略步骤失败'
    });
  }
});

// ==================== 攻略评估相关接口 ====================

// 评估攻略性能
router.post('/strategies/:id/evaluate', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const { evaluationConfig } = req.body;
    
    const dbService = req.dbService;
    const strategyAnalyzer = req.strategyAnalyzer;
    
    // 检查攻略是否存在
    const strategy = await dbService.getStrategy(id);
    if (!strategy) {
      return res.status(404).json({
        success: false,
        message: '攻略不存在'
      });
    }
    
    // 执行攻略评估
    const evaluation = await strategyAnalyzer.evaluateStrategy(strategy, evaluationConfig);
    
    res.json({
      success: true,
      data: evaluation,
      message: '攻略评估完成'
    });
  } catch (error) {
    console.error('攻略评估失败:', error);
    res.status(500).json({
      success: false,
      message: '攻略评估失败'
    });
  }
});

// 批量评估攻略
router.post('/strategies/batch-evaluate', async (req: ExtendedRequest, res: Response) => {
  try {
    const { strategyIds, evaluationConfig } = req.body;
    
    if (!Array.isArray(strategyIds) || strategyIds.length === 0) {
      return res.status(400).json({
        success: false,
        message: '攻略ID列表不能为空'
      });
    }
    
    const dbService = req.dbService;
    const strategyAnalyzer = req.strategyAnalyzer;
    
    const evaluations = [];
    
    for (const strategyId of strategyIds) {
      try {
        const strategy = await dbService.getStrategy(strategyId);
        if (strategy) {
          const evaluation = await strategyAnalyzer.evaluateStrategy(strategy, evaluationConfig);
          evaluations.push({
            strategyId,
            evaluation,
            success: true
          });
        } else {
          evaluations.push({
            strategyId,
            error: '攻略不存在',
            success: false
          });
        }
      } catch (error) {
        evaluations.push({
          strategyId,
          error: error.message,
          success: false
        });
      }
    }
    
    res.json({
      success: true,
      data: evaluations,
      message: '批量评估完成'
    });
  } catch (error) {
    console.error('批量评估失败:', error);
    res.status(500).json({
      success: false,
      message: '批量评估失败'
    });
  }
});

// 获取攻略评估历史
router.get('/strategies/:id/evaluations', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const { limit, offset } = req.query;
    
    const dbService = req.dbService;
    
    const evaluations = await dbService.getStrategyEvaluations(id, {
      limit: limit ? parseInt(limit as string) : 20,
      offset: offset ? parseInt(offset as string) : 0
    });
    
    res.json({
      success: true,
      data: evaluations
    });
  } catch (error) {
    console.error('获取评估历史失败:', error);
    res.status(500).json({
      success: false,
      message: '获取评估历史失败'
    });
  }
});

// 比较攻略性能
router.post('/strategies/compare', async (req: ExtendedRequest, res: Response) => {
  try {
    const { strategyIds, comparisonMetrics } = req.body;
    
    if (!Array.isArray(strategyIds) || strategyIds.length < 2) {
      return res.status(400).json({
        success: false,
        message: '至少需要两个攻略进行比较'
      });
    }
    
    const dbService = req.dbService;
    const strategyAnalyzer = req.strategyAnalyzer;
    
    const strategies = [];
    for (const id of strategyIds) {
      const strategy = await dbService.getStrategy(id);
      if (strategy) {
        strategies.push(strategy);
      }
    }
    
    if (strategies.length < 2) {
      return res.status(400).json({
        success: false,
        message: '找不到足够的有效攻略进行比较'
      });
    }
    
    const comparison = await strategyAnalyzer.compareStrategies(strategies, comparisonMetrics);
    
    res.json({
      success: true,
      data: comparison,
      message: '攻略比较完成'
    });
  } catch (error) {
    console.error('攻略比较失败:', error);
    res.status(500).json({
      success: false,
      message: '攻略比较失败'
    });
  }
});

// 获取攻略优化建议
router.get('/strategies/:id/recommendations', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    
    const dbService = req.dbService;
    const strategyAnalyzer = req.strategyAnalyzer;
    
    const strategy = await dbService.getStrategy(id);
    if (!strategy) {
      return res.status(404).json({
        success: false,
        message: '攻略不存在'
      });
    }
    
    const recommendations = await strategyAnalyzer.generateRecommendations(strategy);
    
    res.json({
      success: true,
      data: recommendations,
      message: '优化建议生成完成'
    });
  } catch (error) {
    console.error('生成优化建议失败:', error);
    res.status(500).json({
      success: false,
      message: '生成优化建议失败'
    });
  }
});

// 获取攻略成功率统计
router.get('/strategies/:id/success-rate', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const { timeRange } = req.query;
    
    const dbService = req.dbService;
    
    const successRate = await dbService.getStrategySuccessRate(id, timeRange as string);
    
    res.json({
      success: true,
      data: successRate
    });
  } catch (error) {
    console.error('获取成功率统计失败:', error);
    res.status(500).json({
      success: false,
      message: '获取成功率统计失败'
    });
  }
});

// ==================== 自动化配置相关接口 ====================

// 获取自动化配置
router.get('/automation/config', async (req: ExtendedRequest, res: Response) => {
  try {
    const { accountId } = req.query;
    const dbService = req.dbService;
    
    const config = await dbService.getAutomationConfig(accountId as string);
    
    res.json({
      success: true,
      data: config
    });
  } catch (error) {
    console.error('获取自动化配置失败:', error);
    res.status(500).json({
      success: false,
      message: '获取自动化配置失败'
    });
  }
});

// 更新自动化配置
router.put('/automation/config', async (req: ExtendedRequest, res: Response) => {
  try {
    const configData = req.body;
    
    // 验证必填字段
    if (!configData.accountId) {
      return res.status(400).json({
        success: false,
        message: '账户ID为必填项'
      });
    }
    
    const dbService = req.dbService;
    const config = await dbService.updateAutomationConfig(configData.accountId, {
      ...configData,
      updatedAt: new Date()
    });
    
    res.json({
      success: true,
      data: config,
      message: '自动化配置更新成功'
    });
  } catch (error) {
    console.error('更新自动化配置失败:', error);
    res.status(500).json({
      success: false,
      message: '更新自动化配置失败'
    });
  }
});

// 获取调度配置
router.get('/automation/schedule', async (req: ExtendedRequest, res: Response) => {
  try {
    const { accountId, taskType } = req.query;
    const dbService = req.dbService;
    
    const schedules = await dbService.getScheduleConfigs({
      accountId: accountId as string,
      taskType: taskType as string
    });
    
    res.json({
      success: true,
      data: schedules
    });
  } catch (error) {
    console.error('获取调度配置失败:', error);
    res.status(500).json({
      success: false,
      message: '获取调度配置失败'
    });
  }
});

// 创建调度配置
router.post('/automation/schedule', async (req: ExtendedRequest, res: Response) => {
  try {
    const scheduleData = req.body;
    
    // 验证必填字段
    if (!scheduleData.accountId || !scheduleData.taskType || !scheduleData.cronExpression) {
      return res.status(400).json({
        success: false,
        message: '账户ID、任务类型和调度表达式为必填项'
      });
    }
    
    const dbService = req.dbService;
    const schedule = await dbService.addScheduleConfig({
      ...scheduleData,
      createdAt: new Date(),
      updatedAt: new Date()
    });
    
    res.status(201).json({
      success: true,
      data: schedule,
      message: '调度配置创建成功'
    });
  } catch (error) {
    console.error('创建调度配置失败:', error);
    res.status(500).json({
      success: false,
      message: '创建调度配置失败'
    });
  }
});

// 更新调度配置
router.put('/automation/schedule/:id', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const updateData = req.body;
    
    const dbService = req.dbService;
    
    const updatedSchedule = await dbService.updateScheduleConfig(id, {
      ...updateData,
      updatedAt: new Date()
    });
    
    res.json({
      success: true,
      data: updatedSchedule,
      message: '调度配置更新成功'
    });
  } catch (error) {
    console.error('更新调度配置失败:', error);
    res.status(500).json({
      success: false,
      message: '更新调度配置失败'
    });
  }
});

// 删除调度配置
router.delete('/automation/schedule/:id', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const dbService = req.dbService;
    
    const success = await dbService.deleteScheduleConfig(id);
    
    if (success) {
      res.json({
        success: true,
        message: '调度配置删除成功'
      });
    } else {
      res.status(404).json({
        success: false,
        message: '调度配置不存在'
      });
    }
  } catch (error) {
    console.error('删除调度配置失败:', error);
    res.status(500).json({
      success: false,
      message: '删除调度配置失败'
    });
  }
});

// 启用/禁用调度
router.patch('/automation/schedule/:id/toggle', async (req: ExtendedRequest, res: Response) => {
  try {
    const { id } = req.params;
    const { enabled } = req.body;
    
    const dbService = req.dbService;
    
    const schedule = await dbService.toggleScheduleConfig(id, enabled);
    
    res.json({
      success: true,
      data: schedule,
      message: `调度配置已${enabled ? '启用' : '禁用'}`
    });
  } catch (error) {
    console.error('切换调度状态失败:', error);
    res.status(500).json({
      success: false,
      message: '切换调度状态失败'
    });
  }
});

// 获取系统配置
router.get('/automation/system-config', async (req: ExtendedRequest, res: Response) => {
  try {
    const dbService = req.dbService;
    
    const systemConfig = await dbService.getSystemConfig();
    
    res.json({
      success: true,
      data: systemConfig
    });
  } catch (error) {
    console.error('获取系统配置失败:', error);
    res.status(500).json({
      success: false,
      message: '获取系统配置失败'
    });
  }
});

// 更新系统配置
router.put('/automation/system-config', async (req: ExtendedRequest, res: Response) => {
  try {
    const configData = req.body;
    
    const dbService = req.dbService;
    const systemConfig = await dbService.updateSystemConfig({
      ...configData,
      updatedAt: new Date()
    });
    
    res.json({
      success: true,
      data: systemConfig,
      message: '系统配置更新成功'
    });
  } catch (error) {
    console.error('更新系统配置失败:', error);
    res.status(500).json({
      success: false,
      message: '更新系统配置失败'
    });
  }
});

// 获取自动化状态
router.get('/automation/status', async (req: ExtendedRequest, res: Response) => {
  try {
    const { accountId } = req.query;
    const automationManager = req.automationManager;
    
    const status = await automationManager.getAutomationStatus(accountId as string);
    
    res.json({
      success: true,
      data: status
    });
  } catch (error) {
    console.error('获取自动化状态失败:', error);
    res.status(500).json({
      success: false,
      message: '获取自动化状态失败'
    });
  }
});

// 启动/停止自动化
router.post('/automation/toggle', async (req: ExtendedRequest, res: Response) => {
  try {
    const { accountId, action } = req.body;
    
    if (!accountId || !['start', 'stop'].includes(action)) {
      return res.status(400).json({
        success: false,
        message: '账户ID和操作类型为必填项'
      });
    }
    
    const automationManager = req.automationManager;
    
    let result;
    if (action === 'start') {
      result = await automationManager.startAutomation(accountId);
    } else {
      result = await automationManager.stopAutomation(accountId);
    }
    
    res.json({
      success: true,
      data: result,
      message: `自动化已${action === 'start' ? '启动' : '停止'}`
    });
  } catch (error) {
    console.error('切换自动化状态失败:', error);
    res.status(500).json({
      success: false,
      message: '切换自动化状态失败'
    });
  }
});

export default router;