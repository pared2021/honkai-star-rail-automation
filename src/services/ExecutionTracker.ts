import { EventEmitter } from 'events';
import PerformanceDataCollector, { StrategyExecutionSession, ExecutionMetrics } from './PerformanceDataCollector.js';
import IntelligentEvaluator from './IntelligentEvaluator.js';
import DatabaseService from './DatabaseService.js';
import { Strategy, StrategyStep } from '../types/index.js';

/**
 * 执行状态
 */
export type ExecutionStatus = 
  | 'idle'           // 空闲
  | 'preparing'      // 准备中
  | 'running'        // 执行中
  | 'paused'         // 暂停
  | 'completed'      // 完成
  | 'failed'         // 失败
  | 'cancelled';     // 取消

/**
 * 步骤执行状态
 */
export interface StepExecutionStatus {
  stepId: string;
  stepIndex: number;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  startTime?: Date;
  endTime?: Date;
  duration?: number;
  attempts: number;
  maxAttempts: number;
  errorMessage?: string;
  progress: number; // 0-100
  subTasks?: SubTaskStatus[];
}

/**
 * 子任务状态
 */
export interface SubTaskStatus {
  id: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
}

/**
 * 执行进度信息
 */
export interface ExecutionProgress {
  sessionId: string;
  strategyId: string;
  accountId: string;
  status: ExecutionStatus;
  currentStepIndex: number;
  totalSteps: number;
  completedSteps: number;
  failedSteps: number;
  skippedSteps: number;
  overallProgress: number; // 0-100
  estimatedTimeRemaining: number; // 毫秒
  elapsedTime: number; // 毫秒
  startTime: Date;
  lastUpdateTime: Date;
  steps: StepExecutionStatus[];
  currentActivity: string;
  performanceMetrics: {
    averageStepDuration: number;
    successRate: number;
    errorRate: number;
    retryRate: number;
  };
}

/**
 * 执行控制命令
 */
export interface ExecutionCommand {
  type: 'start' | 'pause' | 'resume' | 'stop' | 'skip_step' | 'retry_step';
  sessionId?: string;
  stepId?: string;
  parameters?: any;
}

/**
 * 执行事件
 */
export interface ExecutionEvent {
  type: 'session_started' | 'session_ended' | 'step_started' | 'step_completed' | 'step_failed' | 'progress_updated' | 'error_occurred';
  sessionId: string;
  timestamp: Date;
  data: any;
}

/**
 * 攻略执行追踪器
 * 负责监控和管理攻略执行过程
 */
class ExecutionTracker extends EventEmitter {
  private dataCollector: PerformanceDataCollector;
  private evaluator: IntelligentEvaluator;
  private dbService: DatabaseService;
  
  private activeExecutions: Map<string, ExecutionProgress> = new Map();
  private executionHistory: ExecutionEvent[] = [];
  private maxHistorySize = 1000;
  
  private updateInterval?: NodeJS.Timeout;
  private isTracking = false;

  constructor(
    dataCollector: PerformanceDataCollector,
    evaluator: IntelligentEvaluator,
    dbService: DatabaseService
  ) {
    super();
    this.dataCollector = dataCollector;
    this.evaluator = evaluator;
    this.dbService = dbService;
    
    // 监听数据收集器事件
    this.setupDataCollectorListeners();
  }

  /**
   * 开始追踪
   */
  public startTracking(): void {
    if (this.isTracking) return;
    
    this.isTracking = true;
    console.log('开始执行追踪...');
    
    // 每秒更新一次进度
    this.updateInterval = setInterval(() => {
      this.updateAllProgress();
    }, 1000);
    
    this.emit('trackingStarted');
  }

  /**
   * 停止追踪
   */
  public stopTracking(): void {
    if (!this.isTracking) return;
    
    this.isTracking = false;
    
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = undefined;
    }
    
    console.log('执行追踪已停止');
    this.emit('trackingStopped');
  }

  /**
   * 开始执行攻略
   */
  public async startExecution(
    strategyId: string,
    accountId: string,
    strategy: Strategy
  ): Promise<string> {
    console.log(`开始执行攻略: ${strategy.strategyName}`);
    
    // 启动数据收集会话
    const sessionId = await this.dataCollector.startExecutionSession(
      strategyId,
      accountId,
      strategy
    );
    
    // 初始化执行进度
    const progress: ExecutionProgress = {
      sessionId,
      strategyId,
      accountId,
      status: 'preparing',
      currentStepIndex: -1,
      totalSteps: strategy.steps.length,
      completedSteps: 0,
      failedSteps: 0,
      skippedSteps: 0,
      overallProgress: 0,
      estimatedTimeRemaining: 0,
      elapsedTime: 0,
      startTime: new Date(),
      lastUpdateTime: new Date(),
      steps: strategy.steps.map((step, index) => ({
        stepId: step.id,
        stepIndex: index,
        status: 'pending',
        attempts: 0,
        maxAttempts: step.retryCount || 3,
        progress: 0,
        subTasks: this.generateSubTasks(step)
      })),
      currentActivity: '准备执行攻略...',
      performanceMetrics: {
        averageStepDuration: 0,
        successRate: 0,
        errorRate: 0,
        retryRate: 0
      }
    };
    
    this.activeExecutions.set(sessionId, progress);
    
    // 记录事件
    this.recordEvent({
      type: 'session_started',
      sessionId,
      timestamp: new Date(),
      data: { strategyId, accountId, totalSteps: strategy.steps.length }
    });
    
    // 开始执行
    setTimeout(() => {
      this.executeStrategy(sessionId, strategy);
    }, 1000);
    
    return sessionId;
  }

  /**
   * 执行攻略
   */
  private async executeStrategy(sessionId: string, strategy: Strategy): Promise<void> {
    const progress = this.activeExecutions.get(sessionId);
    if (!progress) return;
    
    progress.status = 'running';
    progress.currentActivity = '开始执行攻略步骤...';
    this.updateProgress(sessionId);
    
    try {
      for (let i = 0; i < strategy.steps.length; i++) {
        const step = strategy.steps[i];
        
        // 重新获取最新的progress状态
        const currentProgress = this.activeExecutions.get(sessionId);
        if (!currentProgress) break;
        
        // 检查是否被暂停或取消
        if (currentProgress.status === 'paused') {
          await this.waitForResume(sessionId);
        }
        
        if (currentProgress.status === 'cancelled') {
          break;
        }
        
        // 执行步骤
        const success = await this.executeStep(sessionId, step, i);
        
        if (!success && !step.isOptional) {
          // 必需步骤失败，终止执行
          progress.status = 'failed';
          progress.currentActivity = `步骤执行失败: ${step.description}`;
          break;
        }
      }
      
      // 完成执行
      if (progress.status === 'running') {
        progress.status = 'completed';
        progress.currentActivity = '攻略执行完成';
        progress.overallProgress = 100;
      }
      
    } catch (error) {
      console.error('攻略执行出错:', error);
      progress.status = 'failed';
      progress.currentActivity = `执行出错: ${error}`;
    }
    
    // 结束数据收集会话
    await this.dataCollector.endExecutionSession(
      sessionId,
      progress.status === 'completed' ? 'completed' : 'failed'
    );
    
    // 记录结束事件
    this.recordEvent({
      type: 'session_ended',
      sessionId,
      timestamp: new Date(),
      data: { 
        status: progress.status,
        completedSteps: progress.completedSteps,
        failedSteps: progress.failedSteps,
        totalDuration: progress.elapsedTime
      }
    });
    
    this.updateProgress(sessionId);
    
    // 从活动执行中移除
    setTimeout(() => {
      this.activeExecutions.delete(sessionId);
    }, 30000); // 30秒后清理
  }

  /**
   * 执行单个步骤
   */
  private async executeStep(
    sessionId: string,
    step: StrategyStep,
    stepIndex: number
  ): Promise<boolean> {
    const progress = this.activeExecutions.get(sessionId);
    if (!progress) return false;
    
    const stepStatus = progress.steps[stepIndex];
    progress.currentStepIndex = stepIndex;
    progress.currentActivity = `执行步骤: ${step.description}`;
    
    // 开始执行步骤
    stepStatus.status = 'running';
    stepStatus.startTime = new Date();
    stepStatus.attempts++;
    
    // 记录步骤开始
    const metricId = await this.dataCollector.recordStepStart(
      sessionId,
      step,
      stepIndex
    );
    
    this.recordEvent({
      type: 'step_started',
      sessionId,
      timestamp: new Date(),
      data: { stepId: step.id, stepIndex, description: step.description }
    });
    
    this.updateProgress(sessionId);
    
    try {
      // 模拟步骤执行
      const success = await this.simulateStepExecution(step, stepStatus);
      
      stepStatus.endTime = new Date();
      stepStatus.duration = stepStatus.endTime.getTime() - stepStatus.startTime!.getTime();
      
      if (success) {
        stepStatus.status = 'completed';
        stepStatus.progress = 100;
        progress.completedSteps++;
        
        // 记录步骤完成
        await this.dataCollector.recordStepComplete(sessionId, metricId, true);
        
        this.recordEvent({
          type: 'step_completed',
          sessionId,
          timestamp: new Date(),
          data: { stepId: step.id, duration: stepStatus.duration }
        });
        
      } else {
        stepStatus.status = 'failed';
        progress.failedSteps++;
        
        const errorMessage = `步骤执行失败: ${step.description}`;
        stepStatus.errorMessage = errorMessage;
        
        // 记录步骤失败
        await this.dataCollector.recordStepComplete(sessionId, metricId, false, errorMessage);
        
        this.recordEvent({
          type: 'step_failed',
          sessionId,
          timestamp: new Date(),
          data: { stepId: step.id, error: errorMessage, attempts: stepStatus.attempts }
        });
        
        // 重试逻辑
        if (stepStatus.attempts < stepStatus.maxAttempts) {
          console.log(`步骤失败，准备重试 (${stepStatus.attempts}/${stepStatus.maxAttempts})`);
          await new Promise(resolve => setTimeout(resolve, 2000)); // 等待2秒后重试
          return this.executeStep(sessionId, step, stepIndex);
        }
      }
      
      this.updateProgress(sessionId);
      return success;
      
    } catch (error) {
      console.error('步骤执行异常:', error);
      
      stepStatus.status = 'failed';
      stepStatus.endTime = new Date();
      stepStatus.errorMessage = `执行异常: ${error}`;
      progress.failedSteps++;
      
      await this.dataCollector.recordStepComplete(sessionId, metricId, false, stepStatus.errorMessage);
      
      this.recordEvent({
        type: 'error_occurred',
        sessionId,
        timestamp: new Date(),
        data: { stepId: step.id, error: error.toString() }
      });
      
      this.updateProgress(sessionId);
      return false;
    }
  }

  /**
   * 模拟步骤执行
   */
  private async simulateStepExecution(
    step: StrategyStep,
    stepStatus: StepExecutionStatus
  ): Promise<boolean> {
    const duration = (step.timeout || 10000) * (0.5 + Math.random() * 0.5); // 随机执行时间
    const progressInterval = duration / 20; // 20次进度更新
    
    // 更新子任务进度
    if (stepStatus.subTasks) {
      for (const subTask of stepStatus.subTasks) {
        subTask.status = 'running';
        
        // 模拟子任务执行
        for (let i = 0; i <= 100; i += 10) {
          subTask.progress = i;
          if (i === 100) {
            subTask.status = 'completed';
          }
          await new Promise(resolve => setTimeout(resolve, progressInterval / 10));
        }
      }
    }
    
    // 更新步骤进度
    for (let i = 0; i <= 100; i += 5) {
      stepStatus.progress = i;
      await new Promise(resolve => setTimeout(resolve, progressInterval));
    }
    
    // 模拟成功率（基于步骤类型）
    const successRate = this.getStepSuccessRate(step);
    return Math.random() < successRate;
  }

  /**
   * 获取步骤成功率
   */
  private getStepSuccessRate(step: StrategyStep): number {
    switch (step.stepType) {
      case 'navigation':
        return 0.95;
      case 'interaction':
        return 0.85;
      case 'battle':
        return 0.75;
      case 'wait':
        return 0.98;
      default:
        return 0.80;
    }
  }

  /**
   * 生成子任务
   */
  private generateSubTasks(step: StrategyStep): SubTaskStatus[] {
    const subTasks: SubTaskStatus[] = [];
    
    switch (step.stepType) {
      case 'navigation':
        subTasks.push(
          { id: '1', description: '检测当前位置', status: 'pending', progress: 0 },
          { id: '2', description: '计算路径', status: 'pending', progress: 0 },
          { id: '3', description: '执行移动', status: 'pending', progress: 0 }
        );
        break;
      case 'interaction':
        subTasks.push(
          { id: '1', description: '查找目标元素', status: 'pending', progress: 0 },
          { id: '2', description: '执行交互', status: 'pending', progress: 0 },
          { id: '3', description: '验证结果', status: 'pending', progress: 0 }
        );
        break;
      case 'battle':
        subTasks.push(
          { id: '1', description: '进入战斗', status: 'pending', progress: 0 },
          { id: '2', description: '执行战斗策略', status: 'pending', progress: 0 },
          { id: '3', description: '结束战斗', status: 'pending', progress: 0 }
        );
        break;
    }
    
    return subTasks;
  }

  /**
   * 更新所有执行进度
   */
  private updateAllProgress(): void {
    for (const sessionId of this.activeExecutions.keys()) {
      this.updateProgress(sessionId);
    }
  }

  /**
   * 更新执行进度
   */
  private updateProgress(sessionId: string): void {
    const progress = this.activeExecutions.get(sessionId);
    if (!progress) return;
    
    // 更新总体进度
    progress.overallProgress = (progress.completedSteps / progress.totalSteps) * 100;
    
    // 更新已用时间
    progress.elapsedTime = Date.now() - progress.startTime.getTime();
    
    // 估算剩余时间
    if (progress.completedSteps > 0) {
      const averageStepTime = progress.elapsedTime / progress.completedSteps;
      const remainingSteps = progress.totalSteps - progress.completedSteps;
      progress.estimatedTimeRemaining = averageStepTime * remainingSteps;
    }
    
    // 更新性能指标
    const completedSteps = progress.steps.filter(s => s.status === 'completed');
    if (completedSteps.length > 0) {
      const totalDuration = completedSteps.reduce((sum, s) => sum + (s.duration || 0), 0);
      progress.performanceMetrics.averageStepDuration = totalDuration / completedSteps.length;
      progress.performanceMetrics.successRate = (progress.completedSteps / (progress.completedSteps + progress.failedSteps)) * 100;
      progress.performanceMetrics.errorRate = (progress.failedSteps / progress.totalSteps) * 100;
      
      const totalAttempts = progress.steps.reduce((sum, s) => sum + s.attempts, 0);
      progress.performanceMetrics.retryRate = ((totalAttempts - progress.totalSteps) / progress.totalSteps) * 100;
    }
    
    progress.lastUpdateTime = new Date();
    
    // 发送进度更新事件
    this.emit('progressUpdated', progress);
  }

  /**
   * 执行控制命令
   */
  public async executeCommand(command: ExecutionCommand): Promise<boolean> {
    const { type, sessionId } = command;
    
    if (!sessionId) {
      console.error('缺少会话ID');
      return false;
    }
    
    const progress = this.activeExecutions.get(sessionId);
    if (!progress) {
      console.error(`未找到执行会话: ${sessionId}`);
      return false;
    }
    
    switch (type) {
      case 'pause':
        if (progress.status === 'running') {
          progress.status = 'paused';
          progress.currentActivity = '执行已暂停';
          console.log(`暂停执行: ${sessionId}`);
          return true;
        }
        break;
        
      case 'resume':
        if (progress.status === 'paused') {
          progress.status = 'running';
          progress.currentActivity = '恢复执行中...';
          console.log(`恢复执行: ${sessionId}`);
          return true;
        }
        break;
        
      case 'stop':
        progress.status = 'cancelled';
        progress.currentActivity = '执行已取消';
        console.log(`停止执行: ${sessionId}`);
        return true;
        
      case 'skip_step':
        if (command.stepId && progress.status === 'running') {
          const stepIndex = progress.steps.findIndex(s => s.stepId === command.stepId);
          if (stepIndex >= 0) {
            progress.steps[stepIndex].status = 'skipped';
            progress.skippedSteps++;
            console.log(`跳过步骤: ${command.stepId}`);
            return true;
          }
        }
        break;
    }
    
    return false;
  }

  /**
   * 等待恢复执行
   */
  private async waitForResume(sessionId: string): Promise<void> {
    const progress = this.activeExecutions.get(sessionId);
    if (!progress) return;
    
    while (progress.status === 'paused') {
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }

  /**
   * 记录事件
   */
  private recordEvent(event: ExecutionEvent): void {
    this.executionHistory.push(event);
    
    // 限制历史记录大小
    if (this.executionHistory.length > this.maxHistorySize) {
      this.executionHistory.shift();
    }
    
    this.emit('eventRecorded', event);
  }

  /**
   * 设置数据收集器监听器
   */
  private setupDataCollectorListeners(): void {
    this.dataCollector.on('sessionStarted', (session) => {
      console.log('数据收集会话开始:', session.id);
    });
    
    this.dataCollector.on('sessionEnded', (session) => {
      console.log('数据收集会话结束:', session.id);
    });
    
    this.dataCollector.on('stepStarted', ({ sessionId, metric }) => {
      console.log(`步骤开始: ${metric.stepId}`);
    });
    
    this.dataCollector.on('stepCompleted', ({ sessionId, metric }) => {
      console.log(`步骤完成: ${metric.stepId}, 成功: ${metric.success}`);
    });
  }

  // 公共接口方法
  
  /**
   * 获取所有活动执行
   */
  public getActiveExecutions(): ExecutionProgress[] {
    return Array.from(this.activeExecutions.values());
  }

  /**
   * 获取执行进度
   */
  public getExecutionProgress(sessionId: string): ExecutionProgress | undefined {
    return this.activeExecutions.get(sessionId);
  }

  /**
   * 获取执行历史事件
   */
  public getExecutionHistory(sessionId?: string): ExecutionEvent[] {
    if (sessionId) {
      return this.executionHistory.filter(event => event.sessionId === sessionId);
    }
    return [...this.executionHistory];
  }

  /**
   * 获取执行统计
   */
  public getExecutionStats(): {
    totalExecutions: number;
    activeExecutions: number;
    completedExecutions: number;
    failedExecutions: number;
    averageExecutionTime: number;
  } {
    const activeCount = this.activeExecutions.size;
    const historyEvents = this.executionHistory.filter(e => e.type === 'session_ended');
    
    const completedCount = historyEvents.filter(e => e.data.status === 'completed').length;
    const failedCount = historyEvents.filter(e => e.data.status === 'failed').length;
    
    const totalDurations = historyEvents
      .filter(e => e.data.totalDuration)
      .map(e => e.data.totalDuration);
    
    const averageTime = totalDurations.length > 0 ?
      totalDurations.reduce((sum, duration) => sum + duration, 0) / totalDurations.length : 0;
    
    return {
      totalExecutions: historyEvents.length,
      activeExecutions: activeCount,
      completedExecutions: completedCount,
      failedExecutions: failedCount,
      averageExecutionTime: averageTime
    };
  }

  /**
   * 清理历史数据
   */
  public clearHistory(): void {
    this.executionHistory = [];
    console.log('执行历史已清理');
  }
}

export default ExecutionTracker;