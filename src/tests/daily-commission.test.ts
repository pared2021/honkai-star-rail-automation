import TaskExecutor, { TaskPriority } from '../modules/TaskExecutor.js';
import { GameDetector } from '../modules/GameDetector';
import { ImageRecognition } from '../modules/ImageRecognition';
import { InputController } from '../modules/InputController';
import { TaskType } from '../types';

/**
 * 每日委托功能测试
 * 这是一个基础的端到端测试，用于验证每日委托自动化功能
 */
describe('每日委托自动化测试', () => {
  let taskExecutor: TaskExecutor;
  let gameDetector: GameDetector;
  let imageRecognition: ImageRecognition;
  let inputController: InputController;

  beforeEach(async () => {
    // 初始化所有必要的模块
    gameDetector = new GameDetector();
    imageRecognition = new ImageRecognition();
    inputController = new InputController();
    taskExecutor = new TaskExecutor(3); // maxConcurrentTasks = 3
  });

  afterEach(async () => {
    // 清理资源
    await taskExecutor.cleanup();
  });

  describe('基础功能测试', () => {
    test('应该能够创建每日委托任务', () => {
      const task = {
        id: 'test-daily-task',
        accountId: 'test-account',
        taskType: TaskType.DAILY,
        status: 'pending' as const,
        config: {
          type: 'daily',
          autoAccept: true,
          autoSubmit: true,
          maxRetries: 3
        },
        createdAt: new Date(),
        updatedAt: new Date()
      };
      const taskId = taskExecutor.addTask(task, TaskPriority.NORMAL);

      expect(taskId).toBeDefined();
      expect(typeof taskId).toBe('string');

      const task = taskExecutor.getTaskById(taskId);
      expect(task).toBeDefined();
      expect(task?.status).toBe('pending');
    });

    test('应该能够获取任务状态', () => {
      const taskId = taskExecutor.addTask({
        taskType: 'daily',
        priority: 'high'
      });

      const task = taskExecutor.getTaskById(taskId);
      expect(task).toBeDefined();
      expect(task?.status).toBe('pending');
      expect(task?.taskType).toBe('daily');
    });

    test('应该能够取消任务', () => {
      const task = {
        id: 'test-cancel-task',
        taskType: TaskType.DAILY,
        accountId: 'test-account',
        status: 'pending' as const,
        config: {
          type: 'daily',
          autoAccept: true,
          autoSubmit: true,
          maxRetries: 3
        },
        createdAt: new Date(),
        updatedAt: new Date()
      };
      const taskId = taskExecutor.addTask(task, TaskPriority.NORMAL);

      const cancelled = taskExecutor.cancelTask(taskId);
      expect(cancelled).toBe(true);

      const task = taskExecutor.getTask(taskId);
      expect(task?.status).toBe('cancelled');
    });
  });

  describe('错误处理测试', () => {
    test('应该能够处理游戏未运行的情况', async () => {
      // 模拟游戏未运行
      jest.spyOn(gameDetector, 'isGameRunning').mockResolvedValue(false);

      const task = {
        id: 'test-game-not-running',
        taskType: TaskType.DAILY,
        accountId: 'test-account',
        status: 'pending' as const,
        config: {
          type: 'daily',
          autoAccept: true,
          autoSubmit: true,
          maxRetries: 1
        },
        createdAt: new Date(),
        updatedAt: new Date()
      };
      const taskId = taskExecutor.addTask(task, TaskPriority.NORMAL);

      // 等待任务执行完成
      await new Promise(resolve => {
        taskExecutor.on('taskCompleted', (completedTaskId) => {
          if (completedTaskId === taskId) {
            resolve(void 0);
          }
        });
        taskExecutor.on('taskFailed', (failedTaskId) => {
          if (failedTaskId === taskId) {
            resolve(void 0);
          }
        });
      });

      const task = taskExecutor.getTask(taskId);
      expect(task?.status).toBe('failed');
    });

    test('应该能够处理图像识别失败', async () => {
      // 模拟游戏运行但图像识别失败
      jest.spyOn(gameDetector, 'isGameRunning').mockResolvedValue(true);
      jest.spyOn(imageRecognition, 'findImage').mockResolvedValue({
        found: false,
        location: null,
        confidence: 0
      });

      const task = {
        id: 'test-image-recognition-fail',
        taskType: TaskType.DAILY,
        accountId: 'test-account',
        status: 'pending' as const,
        config: {
          type: 'daily',
          autoAccept: true,
          autoSubmit: true,
          maxRetries: 1
        },
        createdAt: new Date(),
        updatedAt: new Date()
      };
      const taskId = taskExecutor.addTask(task, TaskPriority.NORMAL);

      // 等待任务执行完成
      await new Promise(resolve => {
        const timeout = setTimeout(() => resolve(void 0), 10000); // 10秒超时
        
        taskExecutor.on('taskCompleted', (completedTaskId) => {
          if (completedTaskId === taskId) {
            clearTimeout(timeout);
            resolve(void 0);
          }
        });
        taskExecutor.on('taskFailed', (failedTaskId) => {
          if (failedTaskId === taskId) {
            clearTimeout(timeout);
            resolve(void 0);
          }
        });
      });

      const task = taskExecutor.getTask(taskId);
      expect(task?.status).toBe('failed');
      expect(task?.retryCount).toBeGreaterThan(0);
    });
  });

  describe('系统健康检查测试', () => {
    test('应该能够检查系统健康状态', async () => {
      jest.spyOn(gameDetector, 'isGameRunning').mockResolvedValue(true);
      
      const isHealthy = await taskExecutor.checkSystemHealth();
      expect(typeof isHealthy).toBe('boolean');
    });

    test('应该能够执行紧急停止', async () => {
      const task = {
        id: 'emergency-test-task',
        taskType: TaskType.DAILY,
        accountId: 'test-account',
        status: 'pending' as const,
        config: {
          type: 'daily',
          autoAccept: true,
          autoSubmit: true,
          maxRetries: 3
        },
        createdAt: new Date(),
        updatedAt: new Date()
      };
      const taskId = taskExecutor.addTask(task, TaskPriority.HIGH);

      await taskExecutor.emergencyStop();
      
      const retrievedTask = taskExecutor.getTaskById(taskId);
      expect(retrievedTask?.status).toBe('cancelled');
    });
  });

  describe('统计信息测试', () => {
    test('应该能够获取任务统计信息', () => {
      // 创建多个任务
      const taskIds = [];
      for (let i = 0; i < 3; i++) {
        const task = {
          id: `test-stats-task-${i}`,
          taskType: TaskType.DAILY,
          accountId: 'test-account',
          status: 'pending' as const,
          config: {
            type: 'daily',
            autoAccept: true,
            autoSubmit: true,
            maxRetries: 3
          },
          createdAt: new Date(),
          updatedAt: new Date()
        };
        const taskId = taskExecutor.addTask(task, TaskPriority.NORMAL);
        taskIds.push(taskId);
      }

      const stats = taskExecutor.getStats();
      expect(stats).toBeDefined();
      expect(typeof stats.totalTasks).toBe('number');
      expect(typeof stats.completedTasks).toBe('number');
      expect(typeof stats.failedTasks).toBe('number');
    });

    test('应该能够获取不同状态的任务列表', () => {
      const task1 = {
        id: 'test-pending-task-1',
        taskType: TaskType.DAILY,
        accountId: 'test-account-1',
        status: 'pending' as const,
        config: {
          type: 'daily',
          autoAccept: true,
          autoSubmit: true,
          maxRetries: 3
        },
        createdAt: new Date(),
        updatedAt: new Date()
      };
      const taskId1 = taskExecutor.addTask(task1, TaskPriority.NORMAL);

      const task2 = {
        id: 'test-pending-task-2',
        taskType: TaskType.DAILY,
        accountId: 'test-account-2',
        status: 'pending' as const,
        config: {
          type: 'daily',
          autoAccept: true,
          autoSubmit: true,
          maxRetries: 3
        },
        createdAt: new Date(),
        updatedAt: new Date()
      };
      const taskId2 = taskExecutor.addTask(task2, TaskPriority.LOW);
      
      taskExecutor.cancelTask(taskId2);

      const pendingTasks = taskExecutor.getPendingTasks();
      const cancelledTasks = taskExecutor.getCompletedTasks(); // 包含已取消的任务

      expect(pendingTasks.length).toBeGreaterThan(0);
      expect(pendingTasks.some(task => task.id === taskId1)).toBe(true);
    });
  });
});

/**
 * 集成测试 - 需要真实的游戏环境
 * 这些测试需要游戏实际运行，通常在开发环境中手动执行
 */
describe('每日委托集成测试 (需要游戏运行)', () => {
  let taskExecutor: TaskExecutor;

  beforeAll(async () => {
    // 检查游戏是否运行
    const gameDetector = new GameDetector();
    const isGameRunning = await gameDetector.isGameRunning();
    
    if (!isGameRunning) {
      console.log('跳过集成测试：游戏未运行');
      return;
    }

    const imageRecognition = new ImageRecognition();
    const inputController = new InputController();
    taskExecutor = new TaskExecutor(3);
  });

  afterAll(async () => {
    if (taskExecutor) {
      await taskExecutor.cleanup();
    }
  });

  test('完整的每日委托流程测试', async () => {
    if (!taskExecutor) {
      console.log('跳过测试：游戏未运行');
      return;
    }

    const task = {
      id: 'integration-test-task',
      taskType: TaskType.DAILY,
      accountId: 'integration-test-account',
      status: 'pending' as const,
      config: {
        type: 'daily',
        autoAccept: true,
        autoSubmit: true,
        maxRetries: 3
      },
      createdAt: new Date(),
      updatedAt: new Date()
    };
    const taskId = taskExecutor.addTask(task, TaskPriority.NORMAL);

    // 等待任务完成或超时
    const startTime = Date.now();
    const maxWaitTime = 600000; // 10分钟

    while (Date.now() - startTime < maxWaitTime) {
      const task = taskExecutor.getTaskById(taskId);
      
      if (task?.status === 'completed') {
        expect(task.result?.success).toBe(true);
        expect(task.result?.data?.steps).toBeDefined();
        break;
      } else if (task?.status === 'failed') {
        console.log('任务失败原因:', task.result?.errors);
        expect(task.status).not.toBe('failed');
        break;
      }

      await new Promise(resolve => setTimeout(resolve, 5000)); // 每5秒检查一次
    }

    const finalTask = taskExecutor.getTaskById(taskId);
    expect(['completed', 'failed']).toContain(finalTask?.status);

    // 如果任务成功，验证结果
    if (finalTask?.status === 'completed') {
      expect(finalTask.result?.success).toBe(true);
      expect(finalTask.result?.data?.rewards).toBeDefined();
    }

    // 清理
    await taskExecutor.cleanup();
  }, 700000); // 测试超时时间设为11分钟
});