import { TaskScheduler, TaskPriority, ScheduledTask } from '../TaskScheduler';
import { TaskExecutor, TaskResult, TaskStatus } from '../TaskExecutor';
import { Logger } from '../../utils/Logger';

// Mock Logger
jest.mock('../../utils/Logger');

// Mock TaskExecutor for testing
class MockTaskExecutor extends TaskExecutor {
  private shouldSucceed: boolean;
  private mockExecutionTime: number;
  private executeCallback?: () => void;

  constructor(shouldSucceed: boolean = true, executionTime: number = 100) {
    super('mock-task');
    this.shouldSucceed = shouldSucceed;
    this.mockExecutionTime = executionTime;
  }

  getEstimatedTime(): number {
    return this.mockExecutionTime;
  }

  async canExecute(): Promise<boolean> {
    return true;
  }

  protected async executeTask(): Promise<TaskResult> {
    const startTime = Date.now();
    
    if (this.executeCallback) {
      this.executeCallback();
    }

    await new Promise(resolve => setTimeout(resolve, this.mockExecutionTime));
    
    const executionTime = Date.now() - startTime;

    if (this.shouldSucceed) {
      return {
        success: true,
        message: 'Task completed successfully',
        data: { result: 'success' },
        executionTime
      };
    } else {
      return {
        success: false,
        message: 'Task failed',
        executionTime,
        errors: ['Mock task failure']
      };
    }
  }

  setExecuteCallback(callback: () => void): void {
    this.executeCallback = callback;
  }
}

describe('TaskScheduler', () => {
  let scheduler: TaskScheduler;
  let mockLogger: jest.Mocked<Logger>;

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Mock Logger instance
    mockLogger = {
      info: jest.fn(),
      warn: jest.fn(),
      error: jest.fn(),
      debug: jest.fn()
    } as any;
    
    (Logger.getInstance as jest.Mock).mockReturnValue(mockLogger);

    // Create scheduler with test configuration
    scheduler = new TaskScheduler({
      maxConcurrentTasks: 2,
      defaultTimeout: 5000,
      defaultMaxRetries: 2,
      enablePriorityBoost: false, // Disable for predictable testing
      enableDeadlockDetection: false
    });
  });

  afterEach(async () => {
    if (scheduler.getStatus().isRunning) {
      await scheduler.stop();
    }
  });

  describe('基本功能', () => {
    test('应该能够启动和停止调度器', async () => {
      expect(scheduler.getStatus().isRunning).toBe(false);
      
      scheduler.start();
      expect(scheduler.getStatus().isRunning).toBe(true);
      
      await scheduler.stop();
      expect(scheduler.getStatus().isRunning).toBe(false);
    });

    test('应该能够添加任务到队列', () => {
      const executor = new MockTaskExecutor();
      
      scheduler.scheduleTask('test-task-1', executor, {
        priority: TaskPriority.HIGH
      });
      
      const status = scheduler.getStatus();
      expect(status.queuedTasks).toBe(1);
      
      const queuedTasks = scheduler.getQueuedTasks();
      expect(queuedTasks).toHaveLength(1);
      expect(queuedTasks[0].id).toBe('test-task-1');
      expect(queuedTasks[0].priority).toBe(TaskPriority.HIGH);
    });

    test('应该拒绝重复的任务ID', () => {
      const executor1 = new MockTaskExecutor();
      const executor2 = new MockTaskExecutor();
      
      scheduler.scheduleTask('duplicate-id', executor1);
      
      expect(() => {
        scheduler.scheduleTask('duplicate-id', executor2);
      }).toThrow('任务ID已存在: duplicate-id');
    });

    test('应该能够取消队列中的任务', () => {
      const executor = new MockTaskExecutor();
      
      scheduler.scheduleTask('cancel-test', executor);
      expect(scheduler.getStatus().queuedTasks).toBe(1);
      
      const cancelled = scheduler.cancelTask('cancel-test');
      expect(cancelled).toBe(true);
      expect(scheduler.getStatus().queuedTasks).toBe(0);
    });
  });

  describe('任务执行', () => {
    test('应该能够执行单个任务', async () => {
      const executor = new MockTaskExecutor(true, 50);
      let taskCompleted = false;
      
      scheduler.on('taskCompleted', () => {
        taskCompleted = true;
      });
      
      scheduler.scheduleTask('execute-test', executor);
      scheduler.start();
      
      // 等待任务完成
      await new Promise(resolve => {
        scheduler.on('taskCompleted', resolve);
      });
      
      expect(taskCompleted).toBe(true);
      expect(scheduler.getStatus().completedTasks).toBe(1);
      expect(scheduler.getStatus().runningTasks).toBe(0);
      expect(scheduler.getTaskStatus('execute-test')).toBe(TaskStatus.COMPLETED);
    });

    test('应该能够并发执行多个任务', async () => {
      const executor1 = new MockTaskExecutor(true, 100);
      const executor2 = new MockTaskExecutor(true, 100);
      let completedCount = 0;
      
      scheduler.on('taskCompleted', () => {
        completedCount++;
      });
      
      scheduler.scheduleTask('concurrent-1', executor1);
      scheduler.scheduleTask('concurrent-2', executor2);
      scheduler.start();
      
      // 等待两个任务都完成
      await new Promise(resolve => {
        const checkCompletion = () => {
          if (completedCount === 2) {
            resolve(undefined);
          } else {
            setTimeout(checkCompletion, 10);
          }
        };
        checkCompletion();
      });
      
      expect(completedCount).toBe(2);
      expect(scheduler.getStatus().completedTasks).toBe(2);
    });

    test('应该遵守最大并发限制', async () => {
      const executors = [
        new MockTaskExecutor(true, 200),
        new MockTaskExecutor(true, 200),
        new MockTaskExecutor(true, 200)
      ];
      
      let maxConcurrent = 0;
      let currentRunning = 0;
      
      executors.forEach(executor => {
        executor.setExecuteCallback(() => {
          currentRunning++;
          maxConcurrent = Math.max(maxConcurrent, currentRunning);
        });
      });
      
      scheduler.on('taskCompleted', () => {
        currentRunning--;
      });
      
      scheduler.scheduleTask('limit-1', executors[0]);
      scheduler.scheduleTask('limit-2', executors[1]);
      scheduler.scheduleTask('limit-3', executors[2]);
      scheduler.start();
      
      // 等待所有任务完成
      await new Promise(resolve => {
        let completedCount = 0;
        scheduler.on('taskCompleted', () => {
          completedCount++;
          if (completedCount === 3) {
            resolve(undefined);
          }
        });
      });
      
      // 最大并发数应该不超过配置的限制（2）
      expect(maxConcurrent).toBeLessThanOrEqual(2);
    });
  });

  describe('优先级调度', () => {
    test('应该按优先级顺序执行任务', async () => {
      const executionOrder: string[] = [];
      
      const lowPriorityExecutor = new MockTaskExecutor(true, 50);
      const highPriorityExecutor = new MockTaskExecutor(true, 50);
      const urgentPriorityExecutor = new MockTaskExecutor(true, 50);
      
      lowPriorityExecutor.setExecuteCallback(() => {
        executionOrder.push('low');
      });
      
      highPriorityExecutor.setExecuteCallback(() => {
        executionOrder.push('high');
      });
      
      urgentPriorityExecutor.setExecuteCallback(() => {
        executionOrder.push('urgent');
      });
      
      // 按相反的优先级顺序添加任务
      scheduler.scheduleTask('low-priority', lowPriorityExecutor, {
        priority: TaskPriority.LOW
      });
      
      scheduler.scheduleTask('high-priority', highPriorityExecutor, {
        priority: TaskPriority.HIGH
      });
      
      scheduler.scheduleTask('urgent-priority', urgentPriorityExecutor, {
        priority: TaskPriority.URGENT
      });
      
      scheduler.start();
      
      // 等待所有任务完成
      await new Promise(resolve => {
        let completedCount = 0;
        scheduler.on('taskCompleted', () => {
          completedCount++;
          if (completedCount === 3) {
            resolve(undefined);
          }
        });
      });
      
      // 应该按优先级顺序执行：urgent -> high -> low
      expect(executionOrder).toEqual(['urgent', 'high', 'low']);
    });
  });

  describe('依赖管理', () => {
    test('应该等待依赖任务完成后再执行', async () => {
      const executionOrder: string[] = [];
      
      const dependencyExecutor = new MockTaskExecutor(true, 100);
      const dependentExecutor = new MockTaskExecutor(true, 50);
      
      dependencyExecutor.setExecuteCallback(() => {
        executionOrder.push('dependency');
      });
      
      dependentExecutor.setExecuteCallback(() => {
        executionOrder.push('dependent');
      });
      
      // 先添加依赖任务的任务
      scheduler.scheduleTask('dependent-task', dependentExecutor, {
        dependencies: ['dependency-task']
      });
      
      // 后添加依赖任务
      scheduler.scheduleTask('dependency-task', dependencyExecutor);
      
      scheduler.start();
      
      // 等待所有任务完成
      await new Promise(resolve => {
        let completedCount = 0;
        scheduler.on('taskCompleted', () => {
          completedCount++;
          if (completedCount === 2) {
            resolve(undefined);
          }
        });
      });
      
      // 依赖任务应该先执行
      expect(executionOrder).toEqual(['dependency', 'dependent']);
    });

    test('应该在依赖任务失败时不执行依赖它的任务', async () => {
      const dependencyExecutor = new MockTaskExecutor(false, 50); // 失败的任务
      const dependentExecutor = new MockTaskExecutor(true, 50);
      
      let dependentExecuted = false;
      dependentExecutor.setExecuteCallback(() => {
        dependentExecuted = true;
      });
      
      scheduler.scheduleTask('failed-dependency', dependencyExecutor);
      scheduler.scheduleTask('dependent-on-failed', dependentExecutor, {
        dependencies: ['failed-dependency']
      });
      
      scheduler.start();
      
      // 等待依赖任务失败
      await new Promise(resolve => {
        scheduler.on('taskFailed', resolve);
      });
      
      // 等待一段时间确保依赖任务不会执行
      await new Promise(resolve => setTimeout(resolve, 200));
      
      expect(dependentExecuted).toBe(false);
      expect(scheduler.getStatus().failedTasks).toBe(1);
      expect(scheduler.getStatus().completedTasks).toBe(0);
    });
  });

  describe('错误处理和重试', () => {
    test('应该重试失败的任务', async () => {
      let attemptCount = 0;
      const executor = new MockTaskExecutor(false, 50);
      
      // 重写execute方法来计数执行次数
      const originalExecute = executor.execute.bind(executor);
      executor.execute = async () => {
        attemptCount++;
        return originalExecute();
      };
      
      scheduler.scheduleTask('retry-test', executor, {
        maxRetries: 2
      });
      
      scheduler.start();
      
      // 等待任务最终失败
      await new Promise(resolve => {
        scheduler.on('taskFailed', resolve);
      });
      
      // 应该执行3次（初始执行 + 2次重试）
      expect(attemptCount).toBe(3);
      expect(scheduler.getStatus().failedTasks).toBe(1);
    });

    test('应该在重试成功时标记任务为完成', async () => {
      let attemptCount = 0;
      const executor = new MockTaskExecutor(false, 50);
      
      // 重写execute方法，第二次尝试成功
      executor.execute = async () => {
        const startTime = Date.now();
        attemptCount++;
        await new Promise(resolve => setTimeout(resolve, 50));
        const executionTime = Date.now() - startTime;
        
        if (attemptCount === 1) {
          return {
            success: false,
            message: 'First attempt failed',
            executionTime,
            errors: ['Mock failure']
          };
        } else {
          return {
            success: true,
            message: 'Retry succeeded',
            data: { result: 'success' },
            executionTime
          };
        }
      };
      
      scheduler.scheduleTask('retry-success', executor, {
        maxRetries: 2
      });
      
      scheduler.start();
      
      // 等待任务完成
      await new Promise(resolve => {
        scheduler.on('taskCompleted', resolve);
      });
      
      expect(attemptCount).toBe(2);
      expect(scheduler.getStatus().completedTasks).toBe(1);
      expect(scheduler.getStatus().failedTasks).toBe(0);
    });
  });

  describe('调度时间', () => {
    test('应该等待调度时间到达后再执行任务', async () => {
      const executor = new MockTaskExecutor(true, 50);
      const futureTime = new Date(Date.now() + 200);
      
      let taskStarted = false;
      scheduler.on('taskStarted', () => {
        taskStarted = true;
      });
      
      scheduler.scheduleTask('scheduled-task', executor, {
        scheduledTime: futureTime
      });
      
      scheduler.start();
      
      // 立即检查任务是否开始（应该没有）
      await new Promise(resolve => setTimeout(resolve, 50));
      expect(taskStarted).toBe(false);
      
      // 等待调度时间过后
      await new Promise(resolve => setTimeout(resolve, 200));
      
      // 等待任务开始
      await new Promise(resolve => {
        if (taskStarted) {
          resolve(undefined);
        } else {
          scheduler.on('taskStarted', resolve);
        }
      });
      
      expect(taskStarted).toBe(true);
    });
  });

  describe('状态管理', () => {
    test('应该正确跟踪调度器状态', async () => {
      const executor1 = new MockTaskExecutor(true, 100);
      const executor2 = new MockTaskExecutor(false, 50);
      
      // 初始状态
      let status = scheduler.getStatus();
      expect(status.queuedTasks).toBe(0);
      expect(status.runningTasks).toBe(0);
      expect(status.completedTasks).toBe(0);
      expect(status.failedTasks).toBe(0);
      
      // 添加任务
      scheduler.scheduleTask('status-test-1', executor1);
      scheduler.scheduleTask('status-test-2', executor2, {
        maxRetries: 0 // 不重试，直接失败
      });
      
      status = scheduler.getStatus();
      expect(status.queuedTasks).toBe(2);
      
      scheduler.start();
      
      // 等待任务完成和失败
      await new Promise(resolve => {
        let events = 0;
        const checkEvents = () => {
          events++;
          if (events === 2) { // 一个完成，一个失败
            // 等待一小段时间确保状态更新
            setTimeout(() => {
              resolve(undefined);
            }, 100);
          }
        };
        
        scheduler.on('taskCompleted', checkEvents);
        scheduler.on('taskFailed', checkEvents);
      });
      
      status = scheduler.getStatus();
      expect(status.queuedTasks).toBe(0);
      expect(status.runningTasks).toBe(0);
      expect(status.completedTasks).toBe(1);
      expect(status.failedTasks).toBe(1);
    });

    test('应该能够清理历史记录', () => {
      const executor = new MockTaskExecutor();
      
      scheduler.scheduleTask('history-test', executor);
      
      // 模拟一些历史数据
      scheduler['completedTasks'].set('completed-1', {
        success: true,
        message: 'Test completed',
        executionTime: 100
      });
      
      scheduler['failedTasks'].set('failed-1', new Error('Test error'));
      
      scheduler['status'].completedTasks = 1;
      scheduler['status'].failedTasks = 1;
      scheduler['status'].totalExecutionTime = 1000;
      
      scheduler.clearHistory();
      
      const status = scheduler.getStatus();
      expect(status.completedTasks).toBe(0);
      expect(status.failedTasks).toBe(0);
      expect(status.totalExecutionTime).toBe(0);
      expect(status.averageExecutionTime).toBe(0);
    });
  });
});