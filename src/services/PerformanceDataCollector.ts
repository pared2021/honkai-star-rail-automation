import { EventEmitter } from 'events';
import { v4 as uuidv4 } from 'uuid';
import DatabaseService from './DatabaseService.js';
import { Strategy, StrategyStep } from '../types/index.js';

/**
 * 性能数据收集器
 * 负责实时收集攻略执行过程中的性能数据
 */
export interface ExecutionMetrics {
  id: string;
  strategyId: string;
  stepId: string;
  stepIndex: number;
  startTime: Date;
  endTime?: Date;
  duration?: number;
  success: boolean;
  errorMessage?: string;
  memoryUsage?: number;
  cpuUsage?: number;
  gameState?: any;
  screenCapture?: string;
  userInput?: any;
}

export interface StrategyExecutionSession {
  id: string;
  strategyId: string;
  accountId: string;
  startTime: Date;
  endTime?: Date;
  totalDuration?: number;
  status: 'running' | 'completed' | 'failed' | 'paused';
  completedSteps: number;
  totalSteps: number;
  successRate: number;
  metrics: ExecutionMetrics[];
  gameVersion?: string;
  deviceInfo?: any;
}

export interface RealTimePerformanceData {
  timestamp: Date;
  fps: number;
  memoryUsage: number;
  cpuUsage: number;
  networkLatency: number;
  gameState: string;
  activeWindows: string[];
}

class PerformanceDataCollector extends EventEmitter {
  private dbService: DatabaseService;
  private activeSessions: Map<string, StrategyExecutionSession> = new Map();
  private isCollecting = false;
  private collectionInterval?: NodeJS.Timeout;
  private performanceHistory: RealTimePerformanceData[] = [];
  private maxHistorySize = 1000;

  constructor(dbService: DatabaseService) {
    super();
    this.dbService = dbService;
  }

  /**
   * 开始数据收集
   */
  public startCollection(): void {
    if (this.isCollecting) return;
    
    this.isCollecting = true;
    console.log('开始性能数据收集...');
    
    // 每秒收集一次性能数据
    this.collectionInterval = setInterval(() => {
      this.collectRealTimeData();
    }, 1000);
    
    this.emit('collectionStarted');
  }

  /**
   * 停止数据收集
   */
  public stopCollection(): void {
    if (!this.isCollecting) return;
    
    this.isCollecting = false;
    
    if (this.collectionInterval) {
      clearInterval(this.collectionInterval);
      this.collectionInterval = undefined;
    }
    
    console.log('性能数据收集已停止');
    this.emit('collectionStopped');
  }

  /**
   * 开始攻略执行会话
   */
  public async startExecutionSession(
    strategyId: string, 
    accountId: string,
    strategy: Strategy
  ): Promise<string> {
    const sessionId = uuidv4();
    
    const session: StrategyExecutionSession = {
      id: sessionId,
      strategyId,
      accountId,
      startTime: new Date(),
      status: 'running',
      completedSteps: 0,
      totalSteps: strategy.steps.length,
      successRate: 0,
      metrics: [],
      gameVersion: await this.getGameVersion(),
      deviceInfo: await this.getDeviceInfo()
    };
    
    this.activeSessions.set(sessionId, session);
    
    // 保存到数据库
    await this.saveExecutionSession(session);
    
    console.log(`开始攻略执行会话: ${sessionId}`);
    this.emit('sessionStarted', session);
    
    return sessionId;
  }

  /**
   * 记录步骤开始执行
   */
  public async recordStepStart(
    sessionId: string, 
    step: StrategyStep, 
    stepIndex: number
  ): Promise<string> {
    const session = this.activeSessions.get(sessionId);
    if (!session) {
      throw new Error(`未找到执行会话: ${sessionId}`);
    }
    
    const metricId = uuidv4();
    const metric: ExecutionMetrics = {
      id: metricId,
      strategyId: session.strategyId,
      stepId: step.id,
      stepIndex,
      startTime: new Date(),
      success: false,
      memoryUsage: await this.getMemoryUsage(),
      cpuUsage: await this.getCpuUsage(),
      gameState: await this.captureGameState(),
      userInput: step.action
    };
    
    session.metrics.push(metric);
    
    console.log(`步骤开始执行: ${step.description}`);
    this.emit('stepStarted', { sessionId, metric });
    
    return metricId;
  }

  /**
   * 记录步骤执行完成
   */
  public async recordStepComplete(
    sessionId: string, 
    metricId: string, 
    success: boolean, 
    errorMessage?: string
  ): Promise<void> {
    const session = this.activeSessions.get(sessionId);
    if (!session) {
      throw new Error(`未找到执行会话: ${sessionId}`);
    }
    
    const metric = session.metrics.find(m => m.id === metricId);
    if (!metric) {
      throw new Error(`未找到执行指标: ${metricId}`);
    }
    
    metric.endTime = new Date();
    metric.duration = metric.endTime.getTime() - metric.startTime.getTime();
    metric.success = success;
    metric.errorMessage = errorMessage;
    metric.screenCapture = await this.captureScreen();
    
    if (success) {
      session.completedSteps++;
    }
    
    // 更新会话成功率
    session.successRate = session.completedSteps / session.totalSteps;
    
    // 保存指标数据
    await this.saveExecutionMetric(metric);
    
    console.log(`步骤执行完成: ${success ? '成功' : '失败'}`);
    this.emit('stepCompleted', { sessionId, metric });
  }

  /**
   * 结束攻略执行会话
   */
  public async endExecutionSession(
    sessionId: string, 
    status: 'completed' | 'failed' | 'paused'
  ): Promise<StrategyExecutionSession> {
    const session = this.activeSessions.get(sessionId);
    if (!session) {
      throw new Error(`未找到执行会话: ${sessionId}`);
    }
    
    session.endTime = new Date();
    session.totalDuration = session.endTime.getTime() - session.startTime.getTime();
    session.status = status;
    
    // 更新数据库
    await this.updateExecutionSession(session);
    
    // 从活动会话中移除
    this.activeSessions.delete(sessionId);
    
    console.log(`攻略执行会话结束: ${sessionId}, 状态: ${status}`);
    this.emit('sessionEnded', session);
    
    return session;
  }

  /**
   * 收集实时性能数据
   */
  private async collectRealTimeData(): Promise<void> {
    try {
      const data: RealTimePerformanceData = {
        timestamp: new Date(),
        fps: await this.getFPS(),
        memoryUsage: await this.getMemoryUsage(),
        cpuUsage: await this.getCpuUsage(),
        networkLatency: await this.getNetworkLatency(),
        gameState: await this.getGameState(),
        activeWindows: await this.getActiveWindows()
      };
      
      this.performanceHistory.push(data);
      
      // 限制历史数据大小
      if (this.performanceHistory.length > this.maxHistorySize) {
        this.performanceHistory.shift();
      }
      
      this.emit('performanceData', data);
    } catch (error) {
      console.error('收集性能数据失败:', error);
    }
  }

  /**
   * 获取性能历史数据
   */
  public getPerformanceHistory(minutes: number = 10): RealTimePerformanceData[] {
    const cutoffTime = new Date(Date.now() - minutes * 60 * 1000);
    return this.performanceHistory.filter(data => data.timestamp >= cutoffTime);
  }

  /**
   * 获取活动会话
   */
  public getActiveSessions(): StrategyExecutionSession[] {
    return Array.from(this.activeSessions.values());
  }

  /**
   * 获取最新的性能数据
   */
  public getLatestData(): RealTimePerformanceData | null {
    return this.performanceHistory.length > 0 
      ? this.performanceHistory[this.performanceHistory.length - 1] 
      : null;
  }

  /**
   * 获取会话详情
   */
  public getSession(sessionId: string): StrategyExecutionSession | undefined {
    return this.activeSessions.get(sessionId);
  }

  // 系统信息收集方法
  private async getGameVersion(): Promise<string> {
    // TODO: 实现游戏版本检测
    return '1.0.0';
  }

  private async getDeviceInfo(): Promise<any> {
    // TODO: 实现设备信息收集
    return {
      os: process.platform,
      arch: process.arch,
      nodeVersion: process.version
    };
  }

  private async getFPS(): Promise<number> {
    // TODO: 实现FPS检测
    return Math.floor(Math.random() * 60) + 30;
  }

  private async getMemoryUsage(): Promise<number> {
    const usage = process.memoryUsage();
    return Math.round(usage.heapUsed / 1024 / 1024); // MB
  }

  private async getCpuUsage(): Promise<number> {
    // TODO: 实现CPU使用率检测
    return Math.floor(Math.random() * 50) + 10;
  }

  private async getNetworkLatency(): Promise<number> {
    // TODO: 实现网络延迟检测
    return Math.floor(Math.random() * 100) + 20;
  }

  private async getGameState(): Promise<string> {
    // TODO: 实现游戏状态检测
    const states = ['menu', 'battle', 'dialog', 'loading', 'exploration'];
    return states[Math.floor(Math.random() * states.length)];
  }

  private async getActiveWindows(): Promise<string[]> {
    // TODO: 实现活动窗口检测
    return ['Game Window', 'Assistant'];
  }

  private async captureGameState(): Promise<any> {
    // TODO: 实现游戏状态捕获
    return {
      scene: 'battle',
      playerLevel: 50,
      currentHP: 100,
      currentMP: 80
    };
  }

  private async captureScreen(): Promise<string> {
    // TODO: 实现屏幕截图
    return 'base64_screenshot_data';
  }

  // 数据库操作方法
  private async saveExecutionSession(session: StrategyExecutionSession): Promise<void> {
    // TODO: 实现会话数据保存
    console.log('保存执行会话:', session.id);
  }

  private async updateExecutionSession(session: StrategyExecutionSession): Promise<void> {
    // TODO: 实现会话数据更新
    console.log('更新执行会话:', session.id);
  }

  private async saveExecutionMetric(metric: ExecutionMetrics): Promise<void> {
    // TODO: 实现指标数据保存
    console.log('保存执行指标:', metric.id);
  }

  /**
   * 获取攻略执行统计数据
   */
  public async getExecutionStats(strategyId: string): Promise<{
    totalExecutions: number;
    successRate: number;
    averageDuration: number;
    commonErrors: string[];
    performanceTrends: any[];
  }> {
    console.debug('Getting execution stats for strategy:', strategyId);
    // TODO: 实现统计数据计算
    return {
      totalExecutions: 0,
      successRate: 0,
      averageDuration: 0,
      commonErrors: [],
      performanceTrends: []
    };
  }

  /**
   * 清理历史数据
   */
  public async cleanupOldData(daysToKeep: number = 30): Promise<void> {
    const cutoffDate = new Date(Date.now() - daysToKeep * 24 * 60 * 60 * 1000);
    // TODO: 实现历史数据清理
    console.log(`清理 ${cutoffDate} 之前的数据`);
  }
}

export default PerformanceDataCollector;