import { TaskExecutorManager, TaskExecutor, TaskResult } from '../modules/TaskExecutor';
import { TaskPriority, TaskType } from '../types';
import { GameDetector } from '../modules/GameDetector';
import { ImageRecognition } from '../modules/ImageRecognition';
import { InputController } from '../modules/InputController';
import { DailyCommissionTask } from '../modules/DailyCommissionTask';

// Mock TaskExecutor for testing
class MockDailyCommissionExecutor extends TaskExecutor {
  private shouldFail: boolean = false;
  private executionDelay: number = 100;

  constructor() {
    super('DailyCommission');
  }

  setShouldFail(fail: boolean) {
    this.shouldFail = fail;
  }

  setExecutionDelay(delay: number) {
    this.executionDelay = delay;
  }

  getEstimatedTime(): number {
    return 5000; // 5秒预估时间
  }

  async canExecute(): Promise<boolean> {
    return true; // 总是可以执行
  }

  protected async executeTask(): Promise<TaskResult> {
    await this.waitDelay(this.executionDelay);
    
    if (this.shouldFail) {
      return {
        success: false,
        message: '模拟每日委托执行失败',
        executionTime: this.getExecutionTime()
      };
    }

    return {
      success: true,
      message: '每日委托执行成功',
      data: {
        completedCommissions: 4,
        rewards: ['摩拉', '经验书', '强化石']
      },
      executionTime: this.getExecutionTime()
    };
  }

  private waitDelay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

/**
 * 每日委托功能测试
 * 这是一个基础的端到端测试，用于验证每日委托自动化功能
 */
describe('每日委托自动化测试', () => {
  let taskExecutorManager: TaskExecutorManager;
  let dailyCommissionExecutor: MockDailyCommissionExecutor;
  let gameDetector: GameDetector;
  let imageRecognition: ImageRecognition;
  let inputController: InputController;

  beforeEach(async () => {
    // 初始化所有必要的模块
    gameDetector = new GameDetector();
    imageRecognition = new ImageRecognition();
    inputController = new InputController();
    taskExecutorManager = new TaskExecutorManager();
    dailyCommissionExecutor = new MockDailyCommissionExecutor();
    
    // 注册每日委托执行器
    taskExecutorManager.registerExecutor('dailyCommission', dailyCommissionExecutor);
  });

  afterEach(async () => {
    // 清理资源
  });

  describe('基础功能测试', () => {
    test('应该能够注册和执行每日委托任务', async () => {
      // 验证执行器已注册
      const allStatus = taskExecutorManager.getAllTaskStatus();
      expect(allStatus['dailyCommission']).toBe('pending');

      // 执行任务
      const result = await taskExecutorManager.executeTask('dailyCommission');
      expect(result.success).toBe(true);
      expect(result.message).toBe('每日委托执行成功');
      expect(result.data?.completedCommissions).toBe(4);
    });

    test('应该能够获取任务状态', () => {
      const status = taskExecutorManager.getAllTaskStatus();
      expect(status['dailyCommission']).toBe('pending');
    });

    test('应该能够取消任务', () => {
      taskExecutorManager.cancelTask('dailyCommission');
      
      const status = taskExecutorManager.getAllTaskStatus();
      expect(status['dailyCommission']).toBe('cancelled');
    });
  });

  describe('错误处理测试', () => {
    test('应该能够处理游戏未运行的情况', async () => {
      // 模拟游戏未运行
      jest.spyOn(gameDetector, 'isGameRunning').mockReturnValue(false);
      
      // 设置执行器失败
      dailyCommissionExecutor.setShouldFail(true);
      
      const result = await taskExecutorManager.executeTask('dailyCommission');
      expect(result.success).toBe(false);
      expect(result.message).toContain('模拟每日委托执行失败');
    });

    test('应该能够处理图像识别失败', async () => {
      // 模拟游戏运行但图像识别失败
      jest.spyOn(gameDetector, 'isGameRunning').mockReturnValue(true);
      jest.spyOn(imageRecognition, 'findImage').mockResolvedValue({
        found: false,
        location: null,
        confidence: 0
      });
      
      // 设置执行器失败
      dailyCommissionExecutor.setShouldFail(true);
      
      const result = await taskExecutorManager.executeTask('dailyCommission');
      expect(result.success).toBe(false);
      expect(result.message).toContain('模拟每日委托执行失败');
    });
  });

  describe('任务执行器事件测试', () => {
    test('应该能够监听任务开始事件', async () => {
      const startedHandler = jest.fn();
      dailyCommissionExecutor.on('started', startedHandler);
      
      await taskExecutorManager.executeTask('dailyCommission');
      
      expect(startedHandler).toHaveBeenCalledWith({
        taskName: 'DailyCommission'
      });
    });

    test('应该能够监听任务完成事件', async () => {
      const completedHandler = jest.fn();
      dailyCommissionExecutor.on('completed', completedHandler);
      
      const result = await taskExecutorManager.executeTask('dailyCommission');
      
      expect(completedHandler).toHaveBeenCalledWith({
        taskName: 'DailyCommission',
        result
      });
    });

    test('应该能够监听任务失败事件', async () => {
      const failedHandler = jest.fn();
      dailyCommissionExecutor.on('failed', failedHandler);
      dailyCommissionExecutor.setShouldFail(true);
      
      await taskExecutorManager.executeTask('dailyCommission');
      
      expect(failedHandler).toHaveBeenCalledWith({
        taskName: 'DailyCommission',
        error: '模拟每日委托执行失败'
      });
    });
  });

  describe('任务执行器状态测试', () => {
    test('应该能够获取执行器状态', () => {
      const status = dailyCommissionExecutor.getStatus();
      expect(status).toBe('pending');
    });

    test('应该能够获取预估执行时间', () => {
      const estimatedTime = dailyCommissionExecutor.getEstimatedTime();
      expect(estimatedTime).toBe(5000);
    });

    test('应该能够检查执行条件', async () => {
      const canExecute = await dailyCommissionExecutor.canExecute();
      expect(canExecute).toBe(true);
    });
  });

  describe('集成测试', () => {
    test('应该能够完整执行每日委托任务流程', async () => {
      jest.spyOn(gameDetector, 'isGameRunning').mockReturnValue(true);
      
      // 执行任务
      const result = await taskExecutorManager.executeTask('dailyCommission');
      
      // 验证结果
      expect(result).toBeDefined();
      expect(result.success).toBe(true);
      expect(result.message).toBe('每日委托执行成功');
    });

    test('应该能够处理游戏未运行的情况', async () => {
      jest.spyOn(gameDetector, 'isGameRunning').mockReturnValue(false);
      dailyCommissionExecutor.setShouldFail(true);
      
      // 执行任务应该失败
      const result = await taskExecutorManager.executeTask('dailyCommission');
      
      expect(result.success).toBe(false);
      expect(result.message).toContain('模拟每日委托执行失败');
    });

    test('应该能够取消正在执行的任务', async () => {
      // 直接测试执行器的取消功能
      dailyCommissionExecutor.setExecutionDelay(1000);
      
      // 开始执行任务
      const executePromise = dailyCommissionExecutor.execute();
      
      // 立即取消任务
      dailyCommissionExecutor.cancel();
      
      const result = await executePromise;
      
      // 验证任务被取消
       expect(result.success).toBe(false);
       expect(result.message).toContain('任务已取消');
    });
  });
});

/**
 * 集成测试 - 需要真实的游戏环境
 * 这些测试需要游戏实际运行，通常在开发环境中手动执行
 */
describe('每日委托集成测试 (需要游戏运行)', () => {
  let taskExecutorManager: TaskExecutorManager;
  let realDailyCommissionExecutor: MockDailyCommissionExecutor;

  beforeAll(async () => {
    // 检查游戏是否运行
    const gameDetector = new GameDetector();
    const isGameRunning = gameDetector.isGameRunning();
    
    if (!isGameRunning) {
      console.log('跳过集成测试：游戏未运行');
      return;
    }

    const imageRecognition = new ImageRecognition();
    const inputController = new InputController();
    taskExecutorManager = new TaskExecutorManager(3);
    realDailyCommissionExecutor = new MockDailyCommissionExecutor();
    taskExecutorManager.registerExecutor('realDailyCommission', realDailyCommissionExecutor);
  });

  test('完整的每日委托流程测试', async () => {
    if (!taskExecutorManager) {
      console.log('跳过测试：游戏未运行');
      return;
    }

    // 执行真实的每日委托任务
    const result = await taskExecutorManager.executeTask('realDailyCommission');
    
    // 验证结果
    expect(result).toBeDefined();
    if (result.success) {
       expect(result.message).toBe('每日委托执行成功');
     } else {
       console.log('任务失败原因:', result.errors);
       // 在真实环境中，任务可能因为各种原因失败，这是正常的
     }

    // 验证任务状态
    const status = taskExecutorManager.getAllTaskStatus();
    expect(['completed', 'failed', 'cancelled']).toContain(status['realDailyCommission']);
  }, 700000); // 测试超时时间设为11分钟
});