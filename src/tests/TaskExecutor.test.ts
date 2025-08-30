import { TaskExecutor, TaskResult, TaskStatus, TaskExecutorManager } from '../modules/TaskExecutor';
import { EventEmitter } from 'events';

// 模拟具体的任务执行器实现
class MockTaskExecutor extends TaskExecutor {
  private shouldFail: boolean = false;
  private executionDelay: number = 100;
  private canExecuteResult: boolean = true;

  constructor(taskName: string = 'MockTask') {
    super(taskName, {
      maxRetries: 2,
      retryDelay: 50,
      timeout: 1000,
      enableLogging: false
    });
  }

  getEstimatedTime(): number {
    return 1000;
  }

  async canExecute(): Promise<boolean> {
    return this.canExecuteResult;
  }

  protected async executeTask(): Promise<TaskResult> {
    await this.waitDelay(this.executionDelay);
    
    if (this.shouldFail) {
      throw new Error('模拟任务执行失败');
    }

    return {
      success: true,
      message: '任务执行成功',
      executionTime: this.executionDelay,
      data: { mockData: 'test' }
    };
  }

  // 测试辅助方法
  setShouldFail(shouldFail: boolean): void {
    this.shouldFail = shouldFail;
  }

  setExecutionDelay(delay: number): void {
    this.executionDelay = delay;
  }

  setCanExecuteResult(result: boolean): void {
    this.canExecuteResult = result;
  }

  private waitDelay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

describe('TaskExecutor', () => {
  let mockExecutor: MockTaskExecutor;

  beforeEach(() => {
    mockExecutor = new MockTaskExecutor();
  });

  afterEach(() => {
    mockExecutor.removeAllListeners();
  });

  describe('Basic Functionality', () => {
    test('should execute task successfully', async () => {
      const result = await mockExecutor.execute();
      
      expect(result.success).toBe(true);
      expect(result.message).toBe('任务执行成功');
      expect(result.executionTime).toBeGreaterThan(0);
      expect(result.data).toEqual({ mockData: 'test' });
      expect(mockExecutor.getStatus()).toBe(TaskStatus.COMPLETED);
    });

    test('should fail when canExecute returns false', async () => {
      mockExecutor.setCanExecuteResult(false);
      
      const result = await mockExecutor.execute();
      
      expect(result.success).toBe(false);
      expect(result.message).toBe('任务执行条件不满足');
      expect(mockExecutor.getStatus()).toBe(TaskStatus.FAILED);
    });

    test('should handle task execution failure', async () => {
      mockExecutor.setShouldFail(true);
      
      const result = await mockExecutor.execute();
      
      expect(result.success).toBe(false);
      expect(result.message).toBe('模拟任务执行失败');
      expect(result.errors).toContain('模拟任务执行失败');
      expect(mockExecutor.getStatus()).toBe(TaskStatus.FAILED);
    });

    test('should prevent multiple concurrent executions', async () => {
      const promise1 = mockExecutor.execute();
      
      await expect(mockExecutor.execute()).rejects.toThrow('任务已在运行中');
      
      await promise1; // 等待第一个执行完成
    });

    test('should track execution time correctly', async () => {
      const startTime = Date.now();
      await mockExecutor.execute();
      const endTime = Date.now();
      
      const executionTime = mockExecutor.getExecutionTime();
      expect(executionTime).toBeGreaterThan(0);
      expect(executionTime).toBeLessThanOrEqual(endTime - startTime);
    });
  });

  describe('Retry Mechanism', () => {
    test('should retry on failure and eventually succeed', async () => {
      let attemptCount = 0;
      const originalExecuteTask = mockExecutor['executeTask'];
      
      mockExecutor['executeTask'] = async (): Promise<TaskResult> => {
        attemptCount++;
        if (attemptCount < 2) {
          throw new Error('临时失败');
        }
        return originalExecuteTask.call(mockExecutor);
      };
      
      const result = await mockExecutor.execute();
      
      expect(result.success).toBe(true);
      expect(attemptCount).toBe(2);
    });

    test('should fail after max retries', async () => {
      mockExecutor.setShouldFail(true);
      
      const result = await mockExecutor.execute();
      
      expect(result.success).toBe(false);
      expect(result.message).toBe('模拟任务执行失败');
    });
  });

  describe('Timeout Handling', () => {
    test('should timeout on long running task', async () => {
      mockExecutor.setExecutionDelay(2000); // 超过1秒超时限制
      
      const result = await mockExecutor.execute();
      
      expect(result.success).toBe(false);
      expect(result.message).toBe('任务执行超时');
    });
  });

  describe('Cancellation', () => {
    test('should cancel running task', async () => {
      mockExecutor.setExecutionDelay(1000);
      
      const executePromise = mockExecutor.execute();
      
      // 在任务执行过程中取消
      setTimeout(() => {
        mockExecutor.cancel();
      }, 50);
      
      const result = await executePromise;
      
      expect(result.success).toBe(false);
      expect(result.message).toBe('任务已取消');
      expect(mockExecutor.getStatus()).toBe(TaskStatus.CANCELLED);
    });
  });

  describe('Event Emission', () => {
    test('should emit started event', async () => {
      const startedHandler = jest.fn();
      mockExecutor.on('started', startedHandler);
      
      await mockExecutor.execute();
      
      expect(startedHandler).toHaveBeenCalledWith({ taskName: 'MockTask' });
    });

    test('should emit completed event on success', async () => {
      const completedHandler = jest.fn();
      mockExecutor.on('completed', completedHandler);
      
      const result = await mockExecutor.execute();
      
      expect(completedHandler).toHaveBeenCalledWith({
        taskName: 'MockTask',
        result
      });
    });

    test('should emit failed event on failure', async () => {
      const failedHandler = jest.fn();
      mockExecutor.on('failed', failedHandler);
      
      mockExecutor.setShouldFail(true);
      await mockExecutor.execute();
      
      expect(failedHandler).toHaveBeenCalledWith({
        taskName: 'MockTask',
        error: '模拟任务执行失败'
      });
    });

    test('should emit cancelled event on cancellation', () => {
      const cancelledHandler = jest.fn();
      mockExecutor.on('cancelled', cancelledHandler);
      
      mockExecutor.cancel();
      
      expect(cancelledHandler).toHaveBeenCalledWith({ taskName: 'MockTask' });
    });
  });

  describe('Status Management', () => {
    test('should have correct initial status', () => {
      expect(mockExecutor.getStatus()).toBe(TaskStatus.PENDING);
    });

    test('should update status during execution', async () => {
      const statusChanges: TaskStatus[] = [];
      
      mockExecutor.on('started', () => {
        statusChanges.push(mockExecutor.getStatus());
      });
      
      mockExecutor.on('completed', () => {
        statusChanges.push(mockExecutor.getStatus());
      });
      
      await mockExecutor.execute();
      
      expect(statusChanges).toEqual([TaskStatus.RUNNING, TaskStatus.COMPLETED]);
    });
  });
});

describe('TaskExecutorManager', () => {
  let manager: TaskExecutorManager;
  let mockExecutor1: MockTaskExecutor;
  let mockExecutor2: MockTaskExecutor;

  beforeEach(() => {
    manager = new TaskExecutorManager();
    mockExecutor1 = new MockTaskExecutor('Task1');
    mockExecutor2 = new MockTaskExecutor('Task2');
  });

  afterEach(() => {
    manager.removeAllListeners();
    mockExecutor1.removeAllListeners();
    mockExecutor2.removeAllListeners();
  });

  describe('Executor Registration', () => {
    test('should register executors', () => {
      manager.registerExecutor('task1', mockExecutor1);
      manager.registerExecutor('task2', mockExecutor2);
      
      const status = manager.getAllTaskStatus();
      expect(status).toHaveProperty('task1', TaskStatus.PENDING);
      expect(status).toHaveProperty('task2', TaskStatus.PENDING);
    });
  });

  describe('Task Execution', () => {
    beforeEach(() => {
      manager.registerExecutor('task1', mockExecutor1);
      manager.registerExecutor('task2', mockExecutor2);
    });

    test('should execute registered task', async () => {
      const result = await manager.executeTask('task1');
      
      expect(result.success).toBe(true);
      expect(mockExecutor1.getStatus()).toBe(TaskStatus.COMPLETED);
    });

    test('should throw error for unregistered task', async () => {
      await expect(manager.executeTask('nonexistent'))
        .rejects.toThrow('未找到任务执行器: nonexistent');
    });
  });

  describe('Task Cancellation', () => {
    beforeEach(() => {
      manager.registerExecutor('task1', mockExecutor1);
    });

    test('should cancel registered task', () => {
      manager.cancelTask('task1');
      
      expect(mockExecutor1.getStatus()).toBe(TaskStatus.CANCELLED);
    });

    test('should handle cancellation of unregistered task', () => {
      // 应该不抛出错误
      expect(() => manager.cancelTask('nonexistent')).not.toThrow();
    });
  });

  describe('Queue Management', () => {
    beforeEach(() => {
      manager.registerExecutor('task1', mockExecutor1);
      manager.registerExecutor('task2', mockExecutor2);
    });

    test('should queue and execute tasks', async () => {
      manager.queueTask('task1');
      
      // 等待任务执行完成
      await new Promise(resolve => setTimeout(resolve, 200));
      
      expect(mockExecutor1.getStatus()).toBe(TaskStatus.COMPLETED);
    });

    test('should throw error when queueing unregistered task', () => {
      expect(() => manager.queueTask('nonexistent'))
        .toThrow('未找到任务执行器: nonexistent');
    });
  });

  describe('Status Monitoring', () => {
    beforeEach(() => {
      manager.registerExecutor('task1', mockExecutor1);
      manager.registerExecutor('task2', mockExecutor2);
    });

    test('should return all task statuses', async () => {
      await manager.executeTask('task1');
      mockExecutor2.setShouldFail(true);
      await manager.executeTask('task2');
      
      const statuses = manager.getAllTaskStatus();
      
      expect(statuses.task1).toBe(TaskStatus.COMPLETED);
      expect(statuses.task2).toBe(TaskStatus.FAILED);
    });
  });
});