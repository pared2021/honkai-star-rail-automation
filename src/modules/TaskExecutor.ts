import { EventEmitter } from 'events';
import { Logger } from '../utils/Logger';

/**
 * 任务执行结果
 */
export interface TaskResult {
  success: boolean;
  message: string;
  data?: any;
  executionTime: number;
  errors?: string[];
}

/**
 * 任务状态
 */
export enum TaskStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

/**
 * 任务执行器配置
 */
export interface TaskExecutorConfig {
  maxRetries: number;
  retryDelay: number;
  timeout: number;
  enableLogging: boolean;
}

/**
 * 任务执行器基类
 * 提供任务执行的通用框架和生命周期管理
 */
export abstract class TaskExecutor extends EventEmitter {
  protected logger: Logger;
  protected config: TaskExecutorConfig;
  protected status: TaskStatus = TaskStatus.PENDING;
  protected startTime: number = 0;
  protected endTime: number = 0;
  protected retryCount: number = 0;
  protected cancelled: boolean = false;

  constructor(
    protected taskName: string,
    config: Partial<TaskExecutorConfig> = {}
  ) {
    super();
    this.logger = Logger.getInstance();
    this.config = {
      maxRetries: 3,
      retryDelay: 1000,
      timeout: 30000,
      enableLogging: true,
      ...config
    };
  }

  /**
   * 执行任务
   */
  async execute(): Promise<TaskResult> {
    if (this.status === TaskStatus.RUNNING) {
      throw new Error('任务已在运行中');
    }

    this.status = TaskStatus.RUNNING;
    this.startTime = Date.now();
    this.retryCount = 0;
    this.cancelled = false;

    this.emit('started', { taskName: this.taskName });
    this.log('任务开始执行');

    try {
      // 检查任务是否可以执行
      const canExecute = await this.canExecute();
      if (!canExecute) {
        throw new Error('任务执行条件不满足');
      }

      // 执行任务主逻辑
      const result = await this.executeWithRetry();
      
      this.status = TaskStatus.COMPLETED;
      this.endTime = Date.now();
      
      this.emit('completed', { taskName: this.taskName, result });
      this.log(`任务执行完成，耗时: ${this.getExecutionTime()}ms`);
      
      return result;
    } catch (error) {
      this.status = this.cancelled ? TaskStatus.CANCELLED : TaskStatus.FAILED;
      this.endTime = Date.now();
      
      const errorMessage = error instanceof Error ? error.message : String(error);
      const result: TaskResult = {
        success: false,
        message: errorMessage,
        executionTime: this.getExecutionTime(),
        errors: [errorMessage]
      };
      
      this.emit('failed', { taskName: this.taskName, error: errorMessage });
      this.log(`任务执行失败: ${errorMessage}`);
      
      return result;
    }
  }

  /**
   * 取消任务执行
   */
  cancel(): void {
    this.cancelled = true;
    this.status = TaskStatus.CANCELLED;
    this.emit('cancelled', { taskName: this.taskName });
    this.log('任务已取消');
  }

  /**
   * 获取任务状态
   */
  getStatus(): TaskStatus {
    return this.status;
  }

  /**
   * 获取执行时间
   */
  getExecutionTime(): number {
    if (this.startTime === 0) return 0;
    const endTime = this.endTime || Date.now();
    return endTime - this.startTime;
  }

  /**
   * 获取预估执行时间（毫秒）
   */
  abstract getEstimatedTime(): number;

  /**
   * 检查任务是否可以执行
   */
  abstract canExecute(): Promise<boolean>;

  /**
   * 执行任务的具体逻辑
   */
  protected abstract executeTask(): Promise<TaskResult>;

  /**
   * 带重试的任务执行
   */
  private async executeWithRetry(): Promise<TaskResult> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= this.config.maxRetries; attempt++) {
      if (this.cancelled) {
        throw new Error('任务已取消');
      }

      try {
        this.retryCount = attempt;
        if (attempt > 0) {
          this.log(`第 ${attempt} 次重试`);
          await this.delay(this.config.retryDelay);
        }

        // 设置超时
        const timeoutPromise = new Promise<never>((_, reject) => {
          setTimeout(() => reject(new Error('任务执行超时')), this.config.timeout);
        });

        const result = await Promise.race([
          this.executeTask(),
          timeoutPromise
        ]);

        if (result.success) {
          return result;
        } else {
          lastError = new Error(result.message);
        }
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));
        this.log(`执行失败: ${lastError.message}`);
      }
    }

    throw lastError || new Error('任务执行失败');
  }

  /**
   * 延迟函数
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 日志记录
   */
  protected log(message: string): void {
    if (this.config.enableLogging) {
      this.logger.info(message);
    }
  }

  /**
   * 错误日志记录
   */
  protected logError(message: string, error?: any): void {
    if (this.config.enableLogging) {
      this.logger.error(message, error);
    }
  }

  /**
   * 调试日志记录
   */
  protected logDebug(message: string): void {
    if (this.config.enableLogging) {
      this.logger.debug(message);
    }
  }
}

/**
 * 任务执行器管理器
 * 负责管理多个任务执行器的调度和监控
 */
export class TaskExecutorManager extends EventEmitter {
  private logger: Logger;
  private executors: Map<string, TaskExecutor> = new Map();
  private executionQueue: TaskExecutor[] = [];
  private isProcessing: boolean = false;
  private maxConcurrent: number = 1;

  constructor(maxConcurrent: number = 1) {
    super();
    this.logger = Logger.getInstance();
    this.maxConcurrent = maxConcurrent;
  }

  /**
   * 注册任务执行器
   */
  registerExecutor(id: string, executor: TaskExecutor): void {
    this.executors.set(id, executor);
    this.logger.info(`注册任务执行器: ${id}`);
  }

  /**
   * 执行任务
   */
  async executeTask(id: string): Promise<TaskResult> {
    const executor = this.executors.get(id);
    if (!executor) {
      throw new Error(`未找到任务执行器: ${id}`);
    }

    return executor.execute();
  }

  /**
   * 添加任务到队列
   */
  queueTask(id: string): void {
    const executor = this.executors.get(id);
    if (!executor) {
      throw new Error(`未找到任务执行器: ${id}`);
    }

    this.executionQueue.push(executor);
    this.processQueue();
  }

  /**
   * 取消任务
   */
  cancelTask(id: string): void {
    const executor = this.executors.get(id);
    if (executor) {
      executor.cancel();
    }
  }

  /**
   * 获取所有任务状态
   */
  getAllTaskStatus(): Record<string, TaskStatus> {
    const status: Record<string, TaskStatus> = {};
    for (const [id, executor] of this.executors) {
      status[id] = executor.getStatus();
    }
    return status;
  }

  /**
   * 处理任务队列
   */
  private async processQueue(): Promise<void> {
    if (this.isProcessing || this.executionQueue.length === 0) {
      return;
    }

    this.isProcessing = true;

    try {
      while (this.executionQueue.length > 0) {
        const executor = this.executionQueue.shift()!;
        await executor.execute();
      }
    } catch (error) {
      this.logger.error('队列处理失败', error);
    } finally {
      this.isProcessing = false;
    }
  }
}