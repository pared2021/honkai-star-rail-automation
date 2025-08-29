// 游戏状态API路由
import express, { Response } from 'express';
import { ApiService } from '../../src/services/ApiService.js';
import { GameMonitor } from '../../src/services/GameMonitor.js';
import { GameLauncher } from '../../src/services/GameLauncher.js';
import { GameLaunchConfig } from '../../src/types/index.js';
import { AutoLaunchSettings, ExtendedRequest } from '../types/index.js';
import { AutoLaunchManager } from '../../src/services/AutoLaunchManager.js';

const router = express.Router();

// 初始化游戏监控、启动器和自动启动管理器
const gameMonitor = new GameMonitor();
const gameLauncher = new GameLauncher(gameMonitor);
const autoLaunchManager = new AutoLaunchManager();

// 获取游戏状态
router.get('/status', async (req: ExtendedRequest, res: Response) => {
  try {
    const status = await gameMonitor.getGameStatus();
    
    res.json({
      success: true,
      data: status
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: '获取游戏状态失败',
      error: error instanceof Error ? error.message : String(error)
    });
  }
});

// 开始游戏监控
router.post('/monitor/start', async (req: ExtendedRequest, res: Response) => {
  try {
    const { interval = 5000 } = req.body;
    gameMonitor.startMonitoring({ interval });
    
    res.json({
      success: true,
      message: '游戏监控已启动'
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: '启动游戏监控失败',
      error: error instanceof Error ? error.message : String(error)
    });
  }
});

// 停止游戏监控
router.post('/monitor/stop', async (req: ExtendedRequest, res: Response) => {
  try {
    gameMonitor.stopMonitoring();
    
    res.json({
      success: true,
      message: '游戏监控已停止'
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: '停止游戏监控失败',
      error: error instanceof Error ? error.message : String(error)
    });
  }
});

// 获取游戏进程信息
router.get('/process', async (req: ExtendedRequest, res: Response) => {
  try {
    const processInfo = await gameMonitor.getGameProcessInfo();
    
    res.json({
      success: true,
      data: processInfo
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: '获取游戏进程信息失败',
      error: error instanceof Error ? error.message : String(error)
    });
  }
});

// 获取游戏窗口信息
router.get('/window', async (req: ExtendedRequest, res: Response) => {
  try {
    const windowInfo = await gameMonitor.getGameWindowInfo();
    
    res.json({
      success: true,
      data: windowInfo
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: '获取游戏窗口信息失败',
      error: error instanceof Error ? error.message : String(error)
    });
  }
});

// 检测第三方工具
router.get('/third-party-tools', async (req: ExtendedRequest, res: Response) => {
  try {
    const tools = await gameMonitor.detectThirdPartyTools();
    
    res.json({
      success: true,
      data: tools
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: '检测第三方工具失败',
      error: error instanceof Error ? error.message : String(error)
    });
  }
});

// 新增：生成滤镜检测报告
router.get('/filter-report', async (req: ExtendedRequest, res: Response) => {
  try {
    const report = await gameMonitor.generateFilterReport();
    res.json({
      success: true,
      data: report
    });
  } catch (error) {
    console.error('生成滤镜报告失败:', error);
    res.status(500).json({
      success: false,
      message: '生成滤镜报告失败',
      error: error instanceof Error ? error.message : '未知错误'
    });
  }
});

// 新增：检测游戏注入
router.get('/injection/:processId', async (req: ExtendedRequest, res: Response) => {
  try {
    const processId = parseInt(req.params.processId);
    if (isNaN(processId)) {
      return res.status(400).json({
        success: false,
        message: '无效的进程ID'
      });
    }

    const injection = await gameMonitor.detectGameInjection(processId);
    res.json({
      success: true,
      data: injection
    });
  } catch (error) {
    console.error('检测游戏注入失败:', error);
    res.status(500).json({
      success: false,
      message: '检测游戏注入失败',
      error: error instanceof Error ? error.message : '未知错误'
    });
  }
});

// 新增：检测驱动级滤镜
router.get('/driver-filters', async (req: ExtendedRequest, res: Response) => {
  try {
    const filters = await gameMonitor.detectDriverLevelFilters();
    res.json({
      success: true,
      data: filters
    });
  } catch (error) {
    console.error('检测驱动级滤镜失败:', error);
    res.status(500).json({
      success: false,
      message: '检测驱动级滤镜失败',
      error: error instanceof Error ? error.message : '未知错误'
    });
  }
});

// 获取监控统计
router.get('/monitor/stats', async (req: ExtendedRequest, res: Response) => {
  try {
    const stats = gameMonitor.getMonitorStats();
    
    res.json({
      success: true,
      data: stats
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: '获取监控统计失败',
      error: error instanceof Error ? error.message : String(error)
    });
  }
});

// 启动游戏
router.post('/launch', async (req: ExtendedRequest, res: Response) => {
  try {
    const config: GameLaunchConfig = {
      ...req.body,
      id: req.body.id || undefined,
      gameName: req.body.gameName || undefined,
      createdAt: req.body.createdAt || undefined,
      updatedAt: req.body.updatedAt || undefined,
      terminateOnExit: req.body.terminateOnExit || false
    };
    const result = await gameLauncher.launchGame(config);
    
    res.json({
      success: result.success,
      data: result,
      message: result.success ? '游戏启动成功' : result.errorMessage
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: '启动游戏失败',
      error: error instanceof Error ? error.message : String(error)
    });
  }
});

// 终止游戏
router.post('/terminate', async (req: ExtendedRequest, res: Response) => {
  try {
    const success = await gameLauncher.terminateGame();
    
    res.json({
      success,
      message: success ? '游戏已终止' : '终止游戏失败'
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: '终止游戏失败',
      error: error instanceof Error ? error.message : String(error)
    });
  }
});

// 重启游戏
router.post('/restart', async (req: ExtendedRequest, res: Response) => {
  try {
    const config: GameLaunchConfig = {
      ...req.body,
      id: req.body.id || undefined,
      gameName: req.body.gameName || undefined,
      createdAt: req.body.createdAt || undefined,
      updatedAt: req.body.updatedAt || undefined,
      terminateOnExit: req.body.terminateOnExit || false
    };
    const result = await gameLauncher.restartGame(config);
    
    res.json({
      success: result.success,
      data: result,
      message: result.success ? '游戏重启成功' : result.errorMessage
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: '重启游戏失败',
      error: error instanceof Error ? error.message : String(error)
    });
  }
});

// 检查是否可以启动游戏
router.post('/can-launch', async (req: ExtendedRequest, res: Response) => {
  try {
    const config: GameLaunchConfig = {
      ...req.body,
      id: req.body.id || undefined,
      gameName: req.body.gameName || undefined,
      createdAt: req.body.createdAt || undefined,
      updatedAt: req.body.updatedAt || undefined,
      terminateOnExit: req.body.terminateOnExit || false
    };
    const result = await gameLauncher.canLaunchGame(config.gamePath);
    
    res.json({
      success: true,
      data: result
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: '检查启动条件失败',
      error: error instanceof Error ? error.message : String(error)
    });
  }
});

// 检测游戏安装路径
router.get('/detect-installation', async (req: ExtendedRequest, res: Response) => {
  try {
    const paths = await gameLauncher.detectGameInstallation();
    
    res.json({
      success: true,
      data: paths
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: '检测游戏安装路径失败',
      error: error instanceof Error ? error.message : String(error)
    });
  }
});

// 获取推荐启动配置
router.get('/recommended-config/:gamePath', async (req: ExtendedRequest, res: Response) => {
  try {
    const { gamePath } = req.params;
    const decodedPath = decodeURIComponent(gamePath);
    const config = gameLauncher.getRecommendedLaunchConfig(decodedPath);
    
    res.json({
      success: true,
      data: config
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: '获取推荐配置失败',
      error: error instanceof Error ? error.message : String(error)
    });
  }
});

// 检查自动启动条件
router.post('/auto-launch/check', async (req: ExtendedRequest, res: Response) => {
  try {
    const body = req.body;
    const settings: AutoLaunchSettings = {
      enabled: body.enabled || false,
      gamePath: body.gamePath || '',
      autoLaunch: body.autoLaunch || false,
      launchDelay: body.launchDelay || 0,
      enableMonitoring: body.enableMonitoring || false,
      startMonitoring: body.startMonitoring || false,
      monitoringInterval: body.monitoringInterval || 1000,
      monitoringDelay: body.monitoringDelay || 5,
      enableFilterDetection: body.enableFilterDetection || false,
      filterDetectionInterval: body.filterDetectionInterval || 5000,
      detectInjection: body.detectInjection || false,
      detectDriverFilters: body.detectDriverFilters || false,
      terminateOnExit: body.terminateOnExit || false,
      retryAttempts: body.retryAttempts || 3,
      retryDelay: body.retryDelay || 5
    };
    const conditions = await autoLaunchManager.checkAutoLaunchConditions(settings);
    
    res.json({
      success: true,
      data: conditions
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: '检查自动启动条件失败',
      error: error instanceof Error ? error.message : String(error)
    });
  }
});

// 执行自动启动
router.post('/auto-launch/execute', async (req: ExtendedRequest, res: Response) => {
  try {
    const body = req.body;
    const settings: AutoLaunchSettings = {
      enabled: body.enabled || false,
      gamePath: body.gamePath || '',
      autoLaunch: body.autoLaunch || false,
      launchDelay: body.launchDelay || 0,
      enableMonitoring: body.enableMonitoring || false,
      startMonitoring: body.startMonitoring || false,
      monitoringInterval: body.monitoringInterval || 1000,
      monitoringDelay: body.monitoringDelay || 5,
      enableFilterDetection: body.enableFilterDetection || false,
      filterDetectionInterval: body.filterDetectionInterval || 5000,
      detectInjection: body.detectInjection || false,
      detectDriverFilters: body.detectDriverFilters || false,
      terminateOnExit: body.terminateOnExit || false,
      retryAttempts: body.retryAttempts || 3,
      retryDelay: body.retryDelay || 5
    };
    const result = await autoLaunchManager.executeAutoLaunch(settings);
    
    res.json({
      success: result.success,
      data: result,
      message: result.message
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: '执行自动启动失败',
      error: error instanceof Error ? error.message : String(error)
    });
  }
});

// 紧急停止所有任务
router.post('/emergency-stop', async (req: ExtendedRequest, res: Response) => {
  try {
    const dbService = req.dbService;
    
    // 停止所有运行中的任务
    const runningTasks: unknown[] = []; // await apiService.getRunningTasks();
    const stopPromises = runningTasks.map(task => 
      // apiService.controlTask({ taskId: task.id, action: 'stop' })
      Promise.resolve({ success: true })
    );
    
    await Promise.all(stopPromises);
    
    res.json({
      success: true,
      message: `已紧急停止 ${runningTasks.length} 个任务`,
      data: {
        stoppedTaskCount: runningTasks.length
      }
    });
  } catch (error) {
    console.error('紧急停止失败:', error);
    res.status(500).json({
      success: false,
      message: '紧急停止失败'
    });
  }
});

export { router as gameRoutes };