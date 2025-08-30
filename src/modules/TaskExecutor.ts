import { EventEmitter } from 'events';
import { Task, TaskType, TaskStatus, TaskPriority, ExtendedTask, TaskExecutionResult } from '../types';

// 简单的日志记录器实现
class Logger {
  private prefix: string;

  constructor(prefix: string) {
    this.prefix = prefix;
  }

  info(message: string): void {
    console.log(`[${this.prefix}] INFO: ${message}`);
  }

  error(message: string): void {
    console.error(`[${this.prefix}] ERROR: ${message}`);
  }

  warn(message: string): void {
    console.warn(`[${this.prefix}] WARN: ${message}`);
  }

  debug(message: string): void {
    console.debug(`[${this.prefix}] DEBUG: ${message}`);
  }
}

/**
 * 任务执行器 - 负责管理和执行各种游戏任务
 */
export class TaskExecutor extends EventEmitter {
  private tasks: Map<string, ExtendedTask> = new Map();
  private taskQueue: ExtendedTask[] = [];
  private runningTasks: Set<string> = new Set();
  private maxConcurrentTasks: number = 3;
  private isProcessing: boolean = false;
  private logger: Logger;
  private executionTimes: Map<TaskType, number[]> = new Map();

  constructor() {
    super();
    this.logger = new Logger('TaskExecutor');
    this.initializeExecutionTimes();
  }

  /**
   * 初始化任务执行时间统计
   */
  private initializeExecutionTimes(): void {
    const taskTypes: TaskType[] = [TaskType.DAILY, TaskType.MAIN, TaskType.SIDE, TaskType.CUSTOM, TaskType.EVENT];
    taskTypes.forEach(type => {
      this.executionTimes.set(type, []);
    });
  }

  /**
   * 添加任务到队列
   */
  public async addTask(task: Omit<Task, 'id' | 'createdAt' | 'updatedAt'>): Promise<string> {
    const taskId = this.generateTaskId();
    const now = new Date();
    
    const extendedTask: ExtendedTask = {
      ...task,
      id: taskId,
      createdAt: now,
      updatedAt: now,
      priority: (task as any).priority || 'normal',
      retryCount: 0,
      maxRetries: (task.config as any)?.maxRetries || 3,
      logs: [],
      timeout: 300000, // 5分钟默认超时
      startTime: undefined,
      endTime: undefined
    };

    this.tasks.set(taskId, extendedTask);
    this.taskQueue.push(extendedTask);
    this.sortTaskQueue();
    
    this.logger.info(`任务已添加到队列: ${taskId} (${task.taskType})`);
    this.emit('taskAdded', extendedTask);
    
    // 启动队列处理
    this.processQueue();
    
    return taskId;
  }

  /**
   * 处理任务队列
   */
  private async processQueue(): Promise<void> {
    if (this.isProcessing || this.runningTasks.size >= this.maxConcurrentTasks) {
      return;
    }

    this.isProcessing = true;

    try {
      while (this.taskQueue.length > 0 && this.runningTasks.size < this.maxConcurrentTasks) {
        const task = this.taskQueue.shift();
        if (task && task.status === 'pending') {
          this.executeTask(task);
        }
      }
    } finally {
      this.isProcessing = false;
    }
  }

  /**
   * 执行单个任务
   */
  public async executeTask(task: ExtendedTask): Promise<TaskExecutionResult> {
    this.runningTasks.add(task.id);
    task.status = 'running';
    task.startTime = new Date();
    task.updatedAt = new Date();
    
    this.logger.info(`开始执行任务: ${task.id} (${task.taskType})`);
    this.emit('taskStarted', task);

    try {
      let result: boolean = false;

      switch (task.taskType) {
        case TaskType.DAILY:
          result = await this.executeDailyCommission(task);
          break;
        case TaskType.MAIN:
          result = await this.executeMainQuest(task);
          break;
        case TaskType.SIDE:
          result = await this.executeSideQuest(task);
          break;
        case TaskType.CUSTOM:
          result = await this.executeCustomTask(task);
          break;
        case TaskType.EVENT:
          result = await this.executeEventTask(task);
          break;
        default:
          throw new Error(`未知的任务类型: ${task.taskType}`);
      }

      if (result) {
        task.status = 'completed';
        task.endTime = new Date();
        this.logger.info(`任务执行成功: ${task.id}`);
        this.emit('taskCompleted', task);
        this.recordExecutionTime(task);
        return {
          success: true,
          executionTime: task.endTime.getTime() - (task.startTime?.getTime() || 0),
          message: '任务执行成功'
        };
      } else {
        throw new Error('任务执行失败');
      }
    } catch (error) {
      await this.handleTaskError(task, error as Error);
      return {
        success: false,
        executionTime: task.endTime ? task.endTime.getTime() - (task.startTime?.getTime() || 0) : 0,
        message: `任务执行失败: ${(error as Error).message}`
      };
    } finally {
      this.runningTasks.delete(task.id);
      task.updatedAt = new Date();
      this.tasks.set(task.id, task);
      
      // 继续处理队列
      setTimeout(() => this.processQueue(), 100);
    }
  }

  /**
   * 处理任务错误
   */
  private async handleTaskError(task: ExtendedTask, error: Error): Promise<void> {
    task.retryCount = (task.retryCount || 0) + 1;
    const errorMessage = `任务执行失败: ${error.message}`;
    
    task.logs.push({
      timestamp: new Date(),
      level: 'error',
      message: errorMessage
    });

    this.logger.error(`${errorMessage} (重试次数: ${task.retryCount}/${task.maxRetries})`);

    if (task.retryCount < task.maxRetries) {
      task.status = 'pending';
      this.taskQueue.unshift(task); // 重新加入队列头部
      this.logger.info(`任务将重试: ${task.id}`);
    } else {
      task.status = 'failed';
      task.endTime = new Date();
      this.logger.error(`任务最终失败: ${task.id}`);
      this.emit('taskFailed', task, error);
    }
  }

  /**
   * 执行每日委托任务
   */
  private async executeDailyCommission(task: ExtendedTask): Promise<boolean> {
    this.addTaskLog(task, 'info', '开始执行每日委托任务');
    
    try {
      // 1. 初始化游戏环境
      await this.initializeGameEnvironment();
      
      // 2. 导航到委托界面
      await this.navigateToCommissionInterface(task);
      
      // 3. 接取委托
      await this.acceptCommissions(task);
      
      // 4. 执行委托
      await this.executeCommission(task);
      
      // 5. 提交完成的委托
      await this.submitCompletedCommissions(task);
      
      // 6. 领取奖励
      await this.claimCommissionRewards(task);
      
      this.addTaskLog(task, 'info', '每日委托任务执行完成');
      return true;
    } catch (error) {
      this.addTaskLog(task, 'error', `每日委托执行失败: ${(error as Error).message}`);
      throw error;
    }
  }

  /**
   * 执行主线任务
   */
  private async executeMainQuest(task: ExtendedTask): Promise<boolean> {
    this.addTaskLog(task, 'info', '开始执行主线任务');
    // 主线任务执行逻辑
    await this.sleep(2000); // 模拟执行时间
    this.addTaskLog(task, 'info', '主线任务执行完成');
    return true;
  }

  /**
   * 执行支线任务
   */
  private async executeSideQuest(task: ExtendedTask): Promise<boolean> {
    this.addTaskLog(task, 'info', '开始执行支线任务');
    // 支线任务执行逻辑
    await this.sleep(1500); // 模拟执行时间
    this.addTaskLog(task, 'info', '支线任务执行完成');
    return true;
  }

  /**
   * 执行自定义任务
   */
  private async executeCustomTask(task: ExtendedTask): Promise<boolean> {
    this.addTaskLog(task, 'info', '开始执行自定义任务');
    // 自定义任务执行逻辑
    await this.sleep(1000); // 模拟执行时间
    this.addTaskLog(task, 'info', '自定义任务执行完成');
    return true;
  }

  /**
   * 执行活动任务
   */
  private async executeEventTask(task: ExtendedTask): Promise<boolean> {
    this.addTaskLog(task, 'info', '开始执行活动任务');
    // 活动任务执行逻辑
    await this.sleep(3000); // 模拟执行时间
    this.addTaskLog(task, 'info', '活动任务执行完成');
    return true;
  }



  /**
   * 导航到委托界面
   */
  private async navigateToCommissionInterface(task: ExtendedTask): Promise<void> {
    this.addTaskLog(task, 'info', '导航到委托界面');
    await this.sleep(500);
  }

  /**
   * 接取委托
   */
  private async acceptCommissions(task: ExtendedTask): Promise<void> {
    this.addTaskLog(task, 'info', '接取委托');
    await this.sleep(800);
  }

  /**
   * 执行委托
   */
  private async executeCommission(task: ExtendedTask): Promise<void> {
    this.addTaskLog(task, 'info', '执行委托');
    await this.sleep(2000);
  }

  /**
   * 提交完成的委托
   */
  private async submitCompletedCommissions(task: ExtendedTask): Promise<void> {
    this.addTaskLog(task, 'info', '提交完成的委托');
    await this.sleep(600);
  }

  /**
   * 领取委托奖励
   */
  private async claimCommissionRewards(task: ExtendedTask): Promise<void> {
    this.addTaskLog(task, 'info', '领取委托奖励');
    await this.sleep(400);
  }

  /**
   * 添加任务日志
   */
  private addTaskLog(task: ExtendedTask, level: 'info' | 'warn' | 'error', message: string): void {
    task.logs.push({
      timestamp: new Date(),
      level,
      message
    });
  }

  /**
   * 记录任务执行时间
   */
  private recordExecutionTime(task: ExtendedTask): void {
    if (task.startTime && task.endTime) {
      const duration = task.endTime.getTime() - task.startTime.getTime();
      const times = this.executionTimes.get(task.taskType) || [];
      times.push(duration);
      
      // 只保留最近100次记录
      if (times.length > 100) {
        times.shift();
      }
      
      this.executionTimes.set(task.taskType, times);
    }
  }

  /**
   * 生成任务ID
   */
  private generateTaskId(): string {
    return `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 排序任务队列
   */
  private sortTaskQueue(): void {
    this.taskQueue.sort((a, b) => {
      const priorityOrder = { high: 3, normal: 2, low: 1 };
      return priorityOrder[b.priority] - priorityOrder[a.priority];
    });
  }

  /**
   * 睡眠函数
   */
  private async sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // 公共方法

  /**
   * 获取任务统计信息
   */
  public getStats(): {
    total: number;
    pending: number;
    running: number;
    completed: number;
    failed: number;
  } {
    let pending = 0, running = 0, completed = 0, failed = 0;
    
    for (const task of this.tasks.values()) {
      switch (task.status) {
        case 'pending': pending++; break;
        case 'running': running++; break;
        case 'completed': completed++; break;
        case 'failed': failed++; break;
      }
    }
    
    return {
      total: this.tasks.size,
      pending,
      running,
      completed,
      failed
    };
  }

  /**
   * 清理资源
   */
  public async cleanup(): Promise<void> {
    this.logger.info('开始清理TaskExecutor资源');
    
    // 停止所有运行中的任务
    this.runningTasks.clear();
    
    // 清空任务队列
    this.taskQueue.length = 0;
    
    // 清理任务记录
    this.tasks.clear();
    
    this.logger.info('TaskExecutor资源清理完成');
  }

  /**
   * 暂停任务
   */
  public pauseTask(taskId: string): boolean {
    const task = this.tasks.get(taskId);
    if (task && task.status === 'running') {
      task.status = 'paused';
      this.runningTasks.delete(taskId);
      this.logger.info(`任务已暂停: ${taskId}`);
      return true;
    }
    return false;
  }

  /**
   * 恢复任务
   */
  public resumeTask(taskId: string): boolean {
    const task = this.tasks.get(taskId);
    if (task && task.status === 'paused') {
      task.status = 'pending';
      this.taskQueue.unshift(task);
      this.processQueue();
      this.logger.info(`任务已恢复: ${taskId}`);
      return true;
    }
    return false;
  }

  /**
   * 取消任务
   */
  public cancelTask(taskId: string): boolean {
    const task = this.tasks.get(taskId);
    if (task && ['pending', 'running', 'paused'].includes(task.status)) {
      task.status = 'cancelled';
      task.endTime = new Date();
      this.runningTasks.delete(taskId);
      
      // 从队列中移除
      const queueIndex = this.taskQueue.findIndex(t => t.id === taskId);
      if (queueIndex !== -1) {
        this.taskQueue.splice(queueIndex, 1);
      }
      
      this.logger.info(`任务已取消: ${taskId}`);
      this.emit('taskCancelled', task);
      return true;
    }
    return false;
  }

  /**
   * 获取任务状态
   */
  public getTaskStatus(taskId: string): TaskStatus | undefined {
    return this.tasks.get(taskId)?.status;
  }

  /**
   * 获取任务日志
   */
  public getTaskLogs(taskId: string): Array<{ timestamp: Date; level: string; message: string }> {
    return this.tasks.get(taskId)?.logs || [];
  }

  /**
   * 清理已完成的任务
   */
  public cleanupCompletedTasks(): number {
    let cleanedCount = 0;
    const cutoffTime = new Date(Date.now() - 24 * 60 * 60 * 1000); // 24小时前
    
    for (const [taskId, task] of this.tasks.entries()) {
      if (['completed', 'failed', 'cancelled'].includes(task.status) && 
          task.endTime && task.endTime < cutoffTime) {
        this.tasks.delete(taskId);
        cleanedCount++;
      }
    }
    
    this.logger.info(`清理了 ${cleanedCount} 个已完成的任务`);
    return cleanedCount;
  }

  /**
   * 停止所有任务
   */
  public stopAllTasks(): void {
    for (const taskId of this.runningTasks) {
      this.cancelTask(taskId);
    }
    this.taskQueue.length = 0;
    this.logger.info('所有任务已停止');
  }

  /**
   * 获取正在运行的任务
   */
  public getRunningTasks(): ExtendedTask[] {
    const runningTasks: ExtendedTask[] = [];
    for (const [taskId, task] of this.tasks.entries()) {
      if (task.status === 'running') {
        runningTasks.push(task);
      }
    }
    return runningTasks;
  }

  /**
   * 获取游戏检测器
   */
  getGameDetector(): any {
    return {
      isGameRunning: async () => true,
      getCurrentScene: async () => 'main_menu'
    };
  }

  /**
   * 获取输入控制器
   */
  getInputController(): any {
    return {
      click: async (x: number, y: number) => {},
      keyPress: async (key: string) => {},
      type: async (text: string) => {}
    };
  }

  /**
   * 获取图像识别器
   */
  getImageRecognition(): any {
    return {
      findTemplate: async (template: string) => ({ x: 100, y: 100, confidence: 0.9 }),
      captureScreen: async () => Buffer.alloc(0)
    };
  }

  /**
   * 初始化游戏环境（公开方法）
   */
  async initializeGameEnvironment(): Promise<boolean> {
    return this.initializeGameEnvironmentPrivate();
  }

  /**
   * 初始化游戏环境（私有实现）
   */
  private async initializeGameEnvironmentPrivate(): Promise<boolean> {
    this.logger.info('正在初始化游戏环境...');
    
    try {
      // 模拟游戏环境初始化
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      this.logger.info('游戏环境初始化完成');
      return true;
    } catch (error) {
      this.logger.error(`游戏环境初始化失败: ${error}`);
      return false;
    }
  }

  /**
   * 根据ID获取任务
   */
  public getTaskById(taskId: string): ExtendedTask | undefined {
    return this.tasks.get(taskId);
  }

  /**
   * 停止指定任务
   */
  public stopTask(taskId: string): boolean {
    return this.cancelTask(taskId);
  }

  /**
   * 获取待处理的任务
   */
  public getPendingTasks(): ExtendedTask[] {
    const pendingTasks: ExtendedTask[] = [];
    for (const [taskId, task] of this.tasks.entries()) {
      if (task.status === 'pending') {
        pendingTasks.push(task);
      }
    }
    return pendingTasks;
  }

  /**
   * 获取暂停的任务
   */
  public getPausedTasks(): ExtendedTask[] {
    const pausedTasks: ExtendedTask[] = [];
    for (const [taskId, task] of this.tasks.entries()) {
      if (task.status === 'paused') {
        pausedTasks.push(task);
      }
    }
    return pausedTasks;
  }

  /**
   * 更新任务优先级
   */
  public updateTaskPriority(taskId: string, priority: TaskPriority): boolean {
    const task = this.tasks.get(taskId);
    if (task) {
      task.priority = priority;
      this.sortTaskQueue();
      return true;
    }
    return false;
  }

  /**
   * 获取最大并发任务数
   */
  public getMaxConcurrentTasks(): number {
    return this.maxConcurrentTasks;
  }

  /**
   * 设置最大并发任务数
   */
  public setMaxConcurrentTasks(max: number): void {
    this.maxConcurrentTasks = Math.max(1, max);
  }

  /**
   * 获取已完成的任务
   */
  public getCompletedTasks(): ExtendedTask[] {
    const completedTasks: ExtendedTask[] = [];
    for (const [taskId, task] of this.tasks.entries()) {
      if (task.status === 'completed') {
        completedTasks.push(task);
      }
    }
    return completedTasks;
  }

  /**
   * 清理已完成的任务（别名方法）
   */
  public clearCompletedTasks(): number {
    return this.cleanupCompletedTasks();
  }

  /**
   * 获取任务（兼容性方法）
   */
  public getTask(taskId: string): ExtendedTask | undefined {
    return this.getTaskById(taskId);
  }
}