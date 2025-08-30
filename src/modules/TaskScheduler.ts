import { EventEmitter } from 'events';
import { Logger } from '../utils/Logger';
import { TaskExecutor, TaskResult, TaskStatus } from './TaskExecutor';

/**
 * 任务优先级枚举
 */
export enum TaskPriority {
  LOW = 1,
  NORMAL = 2,
  HIGH = 3,
  URGENT = 4,
  CRITICAL = 5
}

/**
 * 调度任务接口
 */
export interface ScheduledTask {
  id: string;
  executor: TaskExecutor;
  priority: TaskPriority;
  scheduledTime: Date;
  dependencies: string[];
  maxRetries: number;
  retryCount: number;
  timeout: number;
  metadata: Record<string, any>;
}

/**
 * 任务调度器配置
 */
export interface TaskSchedulerConfig {
  maxConcurrentTasks: number;
  defaultTimeout: number;
  defaultMaxRetries: number;
  enablePriorityBoost: boolean;
  priorityBoostInterval: number;
  enableDeadlockDetection: boolean;
  deadlockTimeout: number;
}

/**
 * 任务调度器状态
 */
export interface SchedulerStatus {
  isRunning: boolean;
  queuedTasks: number;
  runningTasks: number;
  completedTasks: number;
  failedTasks: number;
  totalExecutionTime: number;
  averageExecutionTime: number;
}

/**
 * 高级任务调度器
 * 支持优先级调度、依赖管理、并发控制等功能
 */
export class TaskScheduler extends EventEmitter {
  private logger: Logger;
  private config: TaskSchedulerConfig;
  private taskQueue: ScheduledTask[] = [];
  private runningTasks: Map<string, ScheduledTask> = new Map();
  private completedTasks: Map<string, TaskResult> = new Map();
  private failedTasks: Map<string, Error> = new Map();
  private isRunning: boolean = false;
  private processingInterval: NodeJS.Timeout | null = null;
  private priorityBoostInterval: NodeJS.Timeout | null = null;
  private status: SchedulerStatus;

  constructor(config: Partial<TaskSchedulerConfig> = {}) {
    super();
    this.logger = Logger.getInstance();
    this.config = {
      maxConcurrentTasks: 3,
      defaultTimeout: 300000, // 5分钟
      defaultMaxRetries: 3,
      enablePriorityBoost: true,
      priorityBoostInterval: 60000, // 1分钟
      enableDeadlockDetection: true,
      deadlockTimeout: 600000, // 10分钟
      ...config
    };
    
    this.status = {
      isRunning: false,
      queuedTasks: 0,
      runningTasks: 0,
      completedTasks: 0,
      failedTasks: 0,
      totalExecutionTime: 0,
      averageExecutionTime: 0
    };
  }

  /**
   * 启动任务调度器
   */
  start(): void {
    if (this.isRunning) {
      this.logger.warn('任务调度器已在运行中');
      return;
    }

    this.isRunning = true;
    this.status.isRunning = true;
    this.logger.info('任务调度器已启动');

    // 开始处理任务队列
    this.processingInterval = setInterval(() => {
      this.processQueue();
    }, 1000);

    // 启用优先级提升
    if (this.config.enablePriorityBoost) {
      this.priorityBoostInterval = setInterval(() => {
        this.boostWaitingTasksPriority();
      }, this.config.priorityBoostInterval);
    }

    this.emit('started');
  }

  /**
   * 停止任务调度器
   */
  async stop(): Promise<void> {
    if (!this.isRunning) {
      return;
    }

    this.logger.info('正在停止任务调度器...');
    this.isRunning = false;
    this.status.isRunning = false;

    // 清除定时器
    if (this.processingInterval) {
      clearInterval(this.processingInterval);
      this.processingInterval = null;
    }

    if (this.priorityBoostInterval) {
      clearInterval(this.priorityBoostInterval);
      this.priorityBoostInterval = null;
    }

    // 等待正在运行的任务完成或取消它们
    const runningTaskIds = Array.from(this.runningTasks.keys());
    for (const taskId of runningTaskIds) {
      const task = this.runningTasks.get(taskId);
      if (task) {
        task.executor.cancel();
      }
    }

    // 等待所有任务完成
    let attempts = 0;
    while (this.runningTasks.size > 0 && attempts < 30) {
      await new Promise(resolve => setTimeout(resolve, 1000));
      attempts++;
    }

    this.logger.info('任务调度器已停止');
    this.emit('stopped');
  }

  /**
   * 添加任务到调度队列
   */
  scheduleTask(
    id: string,
    executor: TaskExecutor,
    options: {
      priority?: TaskPriority;
      scheduledTime?: Date;
      dependencies?: string[];
      maxRetries?: number;
      timeout?: number;
      metadata?: Record<string, any>;
    } = {}
  ): void {
    const task: ScheduledTask = {
      id,
      executor,
      priority: options.priority || TaskPriority.NORMAL,
      scheduledTime: options.scheduledTime || new Date(),
      dependencies: options.dependencies || [],
      maxRetries: options.maxRetries || this.config.defaultMaxRetries,
      retryCount: 0,
      timeout: options.timeout || this.config.defaultTimeout,
      metadata: options.metadata || {}
    };

    // 检查任务ID是否已存在
    if (this.taskQueue.some(t => t.id === id) || this.runningTasks.has(id)) {
      throw new Error(`任务ID已存在: ${id}`);
    }

    this.taskQueue.push(task);
    this.sortTaskQueue();
    this.updateStatus();

    this.logger.info(`任务已添加到调度队列: ${id}, 优先级: ${task.priority}`);
    this.emit('taskScheduled', { taskId: id, task });
  }

  /**
   * 取消任务
   */
  cancelTask(taskId: string): boolean {
    // 检查队列中的任务
    const queueIndex = this.taskQueue.findIndex(t => t.id === taskId);
    if (queueIndex !== -1) {
      const task = this.taskQueue.splice(queueIndex, 1)[0];
      this.logger.info(`队列中的任务已取消: ${taskId}`);
      this.emit('taskCancelled', { taskId, task });
      this.updateStatus();
      return true;
    }

    // 检查正在运行的任务
    const runningTask = this.runningTasks.get(taskId);
    if (runningTask) {
      runningTask.executor.cancel();
      this.logger.info(`正在运行的任务已取消: ${taskId}`);
      this.emit('taskCancelled', { taskId, task: runningTask });
      return true;
    }

    return false;
  }

  /**
   * 获取调度器状态
   */
  getStatus(): SchedulerStatus {
    return { ...this.status };
  }

  /**
   * 获取任务状态
   */
  getTaskStatus(taskId: string): TaskStatus | null {
    // 检查正在运行的任务
    const runningTask = this.runningTasks.get(taskId);
    if (runningTask) {
      return runningTask.executor.getStatus();
    }

    // 检查队列中的任务
    const queuedTask = this.taskQueue.find(t => t.id === taskId);
    if (queuedTask) {
      return TaskStatus.PENDING;
    }

    // 检查已完成的任务
    if (this.completedTasks.has(taskId)) {
      return TaskStatus.COMPLETED;
    }

    // 检查失败的任务
    if (this.failedTasks.has(taskId)) {
      return TaskStatus.FAILED;
    }

    return null;
  }

  /**
   * 获取队列中的所有任务
   */
  getQueuedTasks(): ScheduledTask[] {
    return [...this.taskQueue];
  }

  /**
   * 获取正在运行的任务
   */
  getRunningTasks(): ScheduledTask[] {
    return Array.from(this.runningTasks.values());
  }

  /**
   * 处理任务队列
   */
  private async processQueue(): Promise<void> {
    if (!this.isRunning) {
      return;
    }

    // 检查是否有可执行的任务
    while (this.runningTasks.size < this.config.maxConcurrentTasks && this.taskQueue.length > 0) {
      const task = this.getNextExecutableTask();
      if (!task) {
        break;
      }

      // 从队列中移除任务
      const index = this.taskQueue.indexOf(task);
      this.taskQueue.splice(index, 1);

      // 开始执行任务
      this.executeTask(task);
    }

    this.updateStatus();
  }

  /**
   * 获取下一个可执行的任务
   */
  private getNextExecutableTask(): ScheduledTask | null {
    const now = new Date();

    for (const task of this.taskQueue) {
      // 检查调度时间
      if (task.scheduledTime > now) {
        continue;
      }

      // 检查依赖关系
      if (!this.areDependenciesSatisfied(task)) {
        continue;
      }

      return task;
    }

    return null;
  }

  /**
   * 检查任务依赖是否满足
   */
  private areDependenciesSatisfied(task: ScheduledTask): boolean {
    for (const depId of task.dependencies) {
      // 依赖任务必须已完成
      if (!this.completedTasks.has(depId)) {
        return false;
      }

      // 依赖任务必须成功完成
      const depResult = this.completedTasks.get(depId);
      if (!depResult || !depResult.success) {
        return false;
      }
    }

    return true;
  }

  /**
   * 执行任务
   */
  private async executeTask(task: ScheduledTask): Promise<void> {
    this.runningTasks.set(task.id, task);
    this.logger.info(`开始执行任务: ${task.id}`);
    this.emit('taskStarted', { taskId: task.id, task });

    const startTime = Date.now();

    try {
      // 设置超时
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => {
          reject(new Error(`任务执行超时: ${task.id}`));
        }, task.timeout);
      });

      const result = await Promise.race([
        task.executor.execute(),
        timeoutPromise
      ]);

      const executionTime = Date.now() - startTime;
      this.status.totalExecutionTime += executionTime;

      if (result.success) {
        this.completedTasks.set(task.id, result);
        this.status.completedTasks++;
        this.logger.info(`任务执行成功: ${task.id}, 耗时: ${executionTime}ms`);
        this.emit('taskCompleted', { taskId: task.id, task, result });
      } else {
        await this.handleTaskFailure(task, new Error(result.message));
      }
    } catch (error) {
      await this.handleTaskFailure(task, error as Error);
    } finally {
      this.runningTasks.delete(task.id);
      this.updateStatus();
    }
  }

  /**
   * 处理任务失败
   */
  private async handleTaskFailure(task: ScheduledTask, error: Error): Promise<void> {
    this.logger.error(`任务执行失败: ${task.id}, 错误: ${error.message}`);

    if (task.retryCount < task.maxRetries) {
      // 增加重试次数
      task.retryCount++;
      // 重新调度任务
      task.scheduledTime = new Date(Date.now() + 1000); // 1秒后重试
      this.taskQueue.push(task);
      this.sortTaskQueue();
      this.logger.info(`任务将重试: ${task.id}, 第${task.retryCount}次重试`);
      this.emit('taskRetry', { taskId: task.id, task, retryCount: task.retryCount });
    } else {
      // 任务最终失败
      this.failedTasks.set(task.id, error);
      this.status.failedTasks++;
      this.logger.error(`任务最终失败: ${task.id}, 已重试${task.retryCount}次`);
      this.emit('taskFailed', { taskId: task.id, task, error });
    }
  }

  /**
   * 对任务队列进行排序
   */
  private sortTaskQueue(): void {
    this.taskQueue.sort((a, b) => {
      // 首先按优先级排序（高优先级在前）
      if (a.priority !== b.priority) {
        return b.priority - a.priority;
      }

      // 然后按调度时间排序（早的在前）
      return a.scheduledTime.getTime() - b.scheduledTime.getTime();
    });
  }

  /**
   * 提升等待任务的优先级
   */
  private boostWaitingTasksPriority(): void {
    const now = Date.now();
    const boostThreshold = this.config.priorityBoostInterval;

    for (const task of this.taskQueue) {
      const waitTime = now - task.scheduledTime.getTime();
      if (waitTime > boostThreshold && task.priority < TaskPriority.CRITICAL) {
        task.priority = Math.min(task.priority + 1, TaskPriority.CRITICAL) as TaskPriority;
        this.logger.debug(`任务优先级已提升: ${task.id}, 新优先级: ${task.priority}`);
      }
    }

    this.sortTaskQueue();
  }

  /**
   * 更新调度器状态
   */
  private updateStatus(): void {
    this.status.queuedTasks = this.taskQueue.length;
    this.status.runningTasks = this.runningTasks.size;
    
    if (this.status.completedTasks > 0) {
      this.status.averageExecutionTime = this.status.totalExecutionTime / this.status.completedTasks;
    }
  }

  /**
   * 清理已完成和失败的任务记录
   */
  clearHistory(): void {
    this.completedTasks.clear();
    this.failedTasks.clear();
    this.status.completedTasks = 0;
    this.status.failedTasks = 0;
    this.status.totalExecutionTime = 0;
    this.status.averageExecutionTime = 0;
    this.logger.info('任务历史记录已清理');
  }
}