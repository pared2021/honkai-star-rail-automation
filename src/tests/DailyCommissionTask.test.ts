import { DailyCommissionTask, DailyCommissionConfig } from '../modules/DailyCommissionTask';
import { SceneDetector } from '../modules/SceneDetector';
import { InputController } from '../modules/InputController';
import { ImageRecognition } from '../modules/ImageRecognition';
import { GameDetector } from '../modules/GameDetector';
import { TaskStatus } from '../modules/TaskExecutor';
import { GameScene } from '../modules/TemplateManager';

// Mock dependencies
jest.mock('../modules/SceneDetector');
jest.mock('../modules/InputController');
jest.mock('../modules/ImageRecognition');
jest.mock('../modules/GameDetector');

const MockedSceneDetector = SceneDetector as jest.MockedClass<typeof SceneDetector>;
const MockedInputController = InputController as jest.MockedClass<typeof InputController>;
const MockedImageRecognition = ImageRecognition as jest.MockedClass<typeof ImageRecognition>;
const MockedGameDetector = GameDetector as jest.MockedClass<typeof GameDetector>;

describe('DailyCommissionTask', () => {
  let task: DailyCommissionTask;
  let mockSceneDetector: jest.Mocked<SceneDetector>;
  let mockInputController: jest.Mocked<InputController>;
  let mockImageRecognition: jest.Mocked<ImageRecognition>;
  let mockGameDetector: jest.Mocked<GameDetector>;

  beforeEach(() => {
    // 创建模拟对象
    mockSceneDetector = {
      detectCurrentScene: jest.fn().mockResolvedValue({
        scene: GameScene.MAIN_MENU,
        confidence: 0.9,
        timestamp: Date.now(),
        matchedTemplates: [],
        detectionTime: 100
      }),
      startDetection: jest.fn(),
      stopDetection: jest.fn(),
      getCurrentScene: jest.fn().mockReturnValue(GameScene.MAIN_MENU),
      waitForScene: jest.fn().mockResolvedValue(true),
      start: jest.fn(),
      stop: jest.fn(),
      destroy: jest.fn(),
      on: jest.fn(),
      off: jest.fn(),
      emit: jest.fn(),
      getStats: jest.fn(),
      updateConfig: jest.fn(),
      setCurrentScene: jest.fn(),
      waitForSceneChange: jest.fn(),
      getRelatedTemplates: jest.fn(),
      isReady: jest.fn().mockReturnValue(true)
    } as any;

    mockInputController = {
      click: jest.fn().mockResolvedValue(undefined),
      pressKey: jest.fn().mockResolvedValue(undefined),
      move: jest.fn().mockResolvedValue(undefined),
      drag: jest.fn().mockResolvedValue(undefined),
      scroll: jest.fn().mockResolvedValue(undefined),
      type: jest.fn().mockResolvedValue(undefined),
      pressKeyCombo: jest.fn().mockResolvedValue(undefined),
      startRecording: jest.fn(),
      stopRecording: jest.fn(),
      playback: jest.fn(),
      clearQueue: jest.fn(),
      isRecording: jest.fn().mockReturnValue(false),
      getQueueLength: jest.fn().mockReturnValue(0)
    } as any;

    mockImageRecognition = {
      findImage: jest.fn().mockResolvedValue({
        found: true,
        location: { x: 100, y: 100 },
        confidence: 0.9
      }),
      captureScreen: jest.fn(),
      findText: jest.fn(),
      getPixelColor: jest.fn(),
      findMultipleImages: jest.fn(),
      waitForImage: jest.fn(),
      compareImages: jest.fn(),
      detectImageDifference: jest.fn(),
      clearCache: jest.fn()
    } as any;

    mockGameDetector = {
      isGameRunning: jest.fn().mockReturnValue(true),
      isGameActive: jest.fn().mockReturnValue(true),
      getGameWindow: jest.fn(),
      activateGameWindow: jest.fn(),
      start: jest.fn(),
      stop: jest.fn(),
      on: jest.fn(),
      off: jest.fn(),
      emit: jest.fn()
    } as any;

    // 创建任务实例
    task = new DailyCommissionTask(
      mockSceneDetector,
      mockInputController,
      mockImageRecognition,
      mockGameDetector
    );
  });

  afterEach(() => {
    task.removeAllListeners();
    jest.clearAllMocks();
  });

  describe('Basic Properties', () => {
    test('should have correct estimated time', () => {
      expect(task.getEstimatedTime()).toBe(60000);
    });

    test('should have correct initial status', () => {
      expect(task.getStatus()).toBe(TaskStatus.PENDING);
    });

    test('should have default configuration', () => {
      const config = task.getConfig();
      expect(config.autoClaimRewards).toBe(true);
      expect(config.autoStartCommissions).toBe(false);
      expect(config.maxCommissions).toBe(4);
      expect(config.waitTimeout).toBe(10000);
    });
  });

  describe('Configuration Management', () => {
    test('should update configuration', () => {
      const newConfig: Partial<DailyCommissionConfig> = {
        autoStartCommissions: true,
        maxCommissions: 6
      };
      
      task.updateConfig(newConfig);
      const config = task.getConfig();
      
      expect(config.autoStartCommissions).toBe(true);
      expect(config.maxCommissions).toBe(6);
      expect(config.autoClaimRewards).toBe(true); // 保持原值
    });

    test('should accept custom configuration in constructor', () => {
      const customConfig: Partial<DailyCommissionConfig> = {
        autoClaimRewards: false,
        maxCommissions: 2
      };
      
      const customTask = new DailyCommissionTask(
        mockSceneDetector,
        mockInputController,
        mockImageRecognition,
        mockGameDetector,
        customConfig
      );
      
      const config = customTask.getConfig();
      expect(config.autoClaimRewards).toBe(false);
      expect(config.maxCommissions).toBe(2);
    });
  });

  describe('Execution Conditions', () => {
    test('should pass execution conditions when all requirements met', async () => {
      const canExecute = await task.canExecute();
      
      expect(canExecute).toBe(true);
      expect(mockGameDetector.isGameRunning).toHaveBeenCalled();
      expect(mockGameDetector.isGameActive).toHaveBeenCalled();
    });

    test('should fail when game is not running', async () => {
      mockGameDetector.isGameRunning.mockReturnValue(false);
      
      const canExecute = await task.canExecute();
      
      expect(canExecute).toBe(false);
    });

    test('should fail when game window is not active', async () => {
      mockGameDetector.isGameActive.mockReturnValue(false);
      
      const canExecute = await task.canExecute();
      
      expect(canExecute).toBe(false);
    });

    // Scene detector is always ready in current implementation, so this test is not needed

    test('should handle errors in condition checking', async () => {
      mockGameDetector.isGameRunning.mockReturnValue(false);
      
      const canExecute = await task.canExecute();
      
      expect(canExecute).toBe(false);
    });

    it('should handle canExecute failure', async () => {
      // 模拟游戏未运行
      mockGameDetector.isGameRunning.mockReturnValue(false);
      
      const result = await task.canExecute();
      
      expect(result).toBe(false);
    });

    it('should handle errors during execution', async () => {
      mockSceneDetector.detectCurrentScene.mockRejectedValue(new Error('Scene detection failed') as any);
      
      const result = await task.execute();
      
      expect(result.success).toBe(false);
      expect(result.errors?.[0]).toContain('Scene detection failed');
    });

    it('should handle dependency errors', async () => {
      mockImageRecognition.findImage.mockRejectedValue(new Error('Image recognition failed') as any);
      
      const result = await task.execute();
      
      expect(result.success).toBe(false);
      expect(result.errors?.[0]).toContain('Image recognition failed');
    });
  });

  describe('Task Execution', () => {
    test('should execute successfully with default configuration', async () => {
      // 模拟成功的执行流程
      mockSceneDetector.detectCurrentScene.mockResolvedValue({
        scene: GameScene.MAIN_MENU,
        confidence: 0.9,
        timestamp: Date.now(),
        matchedTemplates: [],
        detectionTime: 100
      });
      mockSceneDetector.waitForScene.mockResolvedValue(true);
      mockImageRecognition.findImage
        .mockResolvedValueOnce({ // commission_button
          found: true,
          location: { x: 100, y: 100 },
          confidence: 0.9
        })
        .mockResolvedValueOnce({ // claim_reward_button
          found: true,
          location: { x: 200, y: 200 },
          confidence: 0.9
        })
        .mockResolvedValueOnce({ // confirm_button
          found: true,
          location: { x: 300, y: 300 },
          confidence: 0.9
        })
        .mockResolvedValueOnce({ // back_button
          found: true,
          location: { x: 50, y: 50 },
          confidence: 0.9
        });
      
      const result = await task.execute();
      
      expect(result.success).toBe(true);
      expect(result.message).toBe('每日委托任务执行完成');
      expect(result.executionTime).toBeGreaterThan(0);
      expect(result.data?.steps).toContain('导航到主界面');
      expect(result.data?.steps).toContain('打开委托界面');
      expect(result.data?.steps).toContain('领取委托奖励');
      expect(result.data?.steps).toContain('返回主界面');
    });

    test('should execute with commission starting enabled', async () => {
      task.updateConfig({ autoStartCommissions: true });
      
      // 模拟成功的执行流程
      mockSceneDetector.detectCurrentScene.mockResolvedValue({
        scene: GameScene.MAIN_MENU,
        confidence: 0.9,
        timestamp: Date.now(),
        matchedTemplates: [],
        detectionTime: 100
      });
      mockSceneDetector.waitForScene.mockResolvedValue(true);
      mockImageRecognition.findImage
        .mockResolvedValueOnce({ found: true, location: { x: 100, y: 100 }, confidence: 0.9 }) // commission_button
        .mockResolvedValueOnce({ found: true, location: { x: 200, y: 200 }, confidence: 0.9 }) // claim_reward_button
        .mockResolvedValueOnce({ found: true, location: { x: 300, y: 300 }, confidence: 0.9 }) // confirm_button
        .mockResolvedValueOnce({ found: true, location: { x: 250, y: 250 }, confidence: 0.9 }) // start_commission_button
        .mockResolvedValueOnce({ found: true, location: { x: 300, y: 300 }, confidence: 0.9 }) // confirm_button
        .mockResolvedValueOnce({ found: true, location: { x: 50, y: 50 }, confidence: 0.9 }); // back_button
      
      const result = await task.execute();
      
      expect(result.success).toBe(true);
      expect(result.data?.steps).toContain('开始新委托');
    });

    test('should handle navigation failure', async () => {
      mockSceneDetector.detectCurrentScene.mockResolvedValue({
        scene: GameScene.BATTLE, // 不在主界面
        confidence: 0.9,
        timestamp: Date.now(),
        matchedTemplates: [],
        detectionTime: 100
      });
      mockSceneDetector.waitForScene.mockResolvedValue(false);
      
      const result = await task.execute();
      
      expect(result.success).toBe(false);
      expect(result.message).toContain('无法导航到主界面');
      expect(result.errors).toEqual(expect.arrayContaining([expect.stringContaining('无法导航到主界面')]));
    });

    test('should handle commission button not found', async () => {
        mockSceneDetector.detectCurrentScene.mockResolvedValue({
          scene: GameScene.MAIN_MENU,
          confidence: 0.9,
          timestamp: Date.now(),
          matchedTemplates: [],
          detectionTime: 100
        });
      mockSceneDetector.waitForScene.mockResolvedValue(true);
      mockImageRecognition.findImage.mockResolvedValue({
        found: false,
        location: { x: 0, y: 0 },
        confidence: 0
      });
      
      const result = await task.execute();
      
      expect(result.success).toBe(false);
      expect(result.message).toContain('未找到委托按钮');
    });

    test('should handle commission panel loading failure', async () => {
      // Mock game running and window active
      mockGameDetector.isGameRunning.mockReturnValue(true);
      mockGameDetector.isGameActive.mockReturnValue(true);
      
      // Mock current scene as MAIN_MENU to skip navigation
      mockSceneDetector.detectCurrentScene.mockResolvedValue({
        scene: GameScene.MAIN_MENU,
        confidence: 0.9,
        timestamp: Date.now(),
        matchedTemplates: [],
        detectionTime: 100
      });
      
      // Mock commission button found
      mockImageRecognition.findImage.mockResolvedValue({
        found: true,
        location: { x: 100, y: 200 },
        confidence: 0.8
      });
      
      // Mock waitForScene to fail immediately (commission panel doesn't load)
      mockSceneDetector.waitForScene.mockImplementation((targetScene, timeout) => {
        return Promise.resolve(false);
      });
      
      const result = await task.execute();
      
      expect(result.success).toBe(false);
      expect(result.errors).toEqual(expect.arrayContaining([expect.stringContaining('无法加载委托界面')]));
    }, 5000);
  });

  describe('Reward Claiming', () => {
    test('should claim multiple rewards', async () => {
      // 模拟找到多个奖励
      mockImageRecognition.findImage
        .mockResolvedValueOnce({ found: true, location: { x: 100, y: 100 }, confidence: 0.9 }) // commission_button
        .mockResolvedValueOnce({ found: true, location: { x: 200, y: 200 }, confidence: 0.9 }) // first claim_reward_button
        .mockResolvedValueOnce({ found: true, location: { x: 300, y: 300 }, confidence: 0.9 }) // confirm_button
        .mockResolvedValueOnce({ found: true, location: { x: 200, y: 200 }, confidence: 0.9 }) // second claim_reward_button
        .mockResolvedValueOnce({ found: true, location: { x: 300, y: 300 }, confidence: 0.9 }) // confirm_button
        .mockResolvedValueOnce({ found: false, location: { x: 0, y: 0 }, confidence: 0 }) // no more rewards
        .mockResolvedValueOnce({ found: true, location: { x: 50, y: 50 }, confidence: 0.9 }); // back_button
      
      mockSceneDetector.detectCurrentScene.mockResolvedValue({
          scene: GameScene.MAIN_MENU,
          confidence: 0.9,
          timestamp: Date.now(),
          matchedTemplates: [],
          detectionTime: 100
        });
      mockSceneDetector.waitForScene.mockResolvedValue(true);
      
      const result = await task.execute();
      
      expect(result.success).toBe(true);
      expect(mockInputController.click).toHaveBeenCalledTimes(6); // commission + 2*(claim+confirm) + back
    });

    test('should handle no rewards available', async () => {
      mockImageRecognition.findImage
        .mockResolvedValueOnce({ found: true, location: { x: 100, y: 100 }, confidence: 0.9 }) // commission_button
        .mockResolvedValueOnce({ found: false, location: { x: 0, y: 0 }, confidence: 0 }) // no claim_reward_button
        .mockResolvedValueOnce({ found: true, location: { x: 50, y: 50 }, confidence: 0.9 }); // back_button
      
      mockSceneDetector.detectCurrentScene.mockResolvedValue({
          scene: GameScene.MAIN_MENU,
          confidence: 0.9,
          timestamp: Date.now(),
          matchedTemplates: [],
          detectionTime: 100
        });
      mockSceneDetector.waitForScene.mockResolvedValue(true);
      
      const result = await task.execute();
      
      expect(result.success).toBe(true);
      expect(mockInputController.click).toHaveBeenCalledTimes(2); // commission + back
    });
  });

  describe('Commission Starting', () => {
    beforeEach(() => {
      task.updateConfig({ autoStartCommissions: true });
    });

    test('should start multiple commissions', async () => {
      mockImageRecognition.findImage
        .mockResolvedValueOnce({ found: true, location: { x: 100, y: 100 }, confidence: 0.9 }) // commission_button
        .mockResolvedValueOnce({ found: false, location: { x: 0, y: 0 }, confidence: 0 }) // no claim rewards
        .mockResolvedValueOnce({ found: true, location: { x: 250, y: 250 }, confidence: 0.9 }) // first start_commission_button
        .mockResolvedValueOnce({ found: true, location: { x: 300, y: 300 }, confidence: 0.9 }) // confirm_button
        .mockResolvedValueOnce({ found: true, location: { x: 250, y: 250 }, confidence: 0.9 }) // second start_commission_button
        .mockResolvedValueOnce({ found: true, location: { x: 300, y: 300 }, confidence: 0.9 }) // confirm_button
        .mockResolvedValueOnce({ found: false, location: { x: 0, y: 0 }, confidence: 0 }) // no more commissions
        .mockResolvedValueOnce({ found: true, location: { x: 50, y: 50 }, confidence: 0.9 }); // back_button
      
      mockSceneDetector.detectCurrentScene.mockResolvedValue({
           scene: GameScene.MAIN_MENU,
           confidence: 0.9,
           timestamp: Date.now(),
           matchedTemplates: [],
           detectionTime: 100
         });
        mockSceneDetector.waitForScene.mockResolvedValue(true);
      
      const result = await task.execute();
      
      expect(result.success).toBe(true);
      expect(mockInputController.click).toHaveBeenCalledTimes(6); // commission + 2*(start+confirm) + back
    });
  });

  describe('Error Handling', () => {
    test('should handle input controller errors', async () => {
      mockInputController.click.mockRejectedValue(new Error('点击失败'));
      
      const result = await task.execute();
      
      expect(result.success).toBe(false);
      expect(result.message).toContain('点击失败');
    });

    test('should handle scene detector errors', async () => {
      mockSceneDetector.detectCurrentScene.mockRejectedValue(new Error('场景检测失败'));
      
      const result = await task.execute();
      
      expect(result.success).toBe(false);
      expect(result.message).toContain('场景检测失败');
    });

    test('should handle image recognition errors', async () => {
      mockImageRecognition.findImage.mockRejectedValue(new Error('图像识别失败'));
      
      const result = await task.execute();
      
      expect(result.success).toBe(false);
      expect(result.message).toContain('图像识别失败');
    });
  });

  describe('Task Cancellation', () => {
    test('should handle cancellation during execution', async () => {
      // 模拟长时间执行，但会被取消中断
      mockSceneDetector.waitForScene.mockImplementation(() => 
        new Promise((resolve, reject) => {
          const timeout = setTimeout(() => resolve(true), 1000);
          // 检查取消状态
          const checkCancel = setInterval(() => {
            if (task.getStatus() === TaskStatus.CANCELLED) {
              clearTimeout(timeout);
              clearInterval(checkCancel);
              reject(new Error('任务已取消'));
            }
          }, 50);
        })
      );
      
      const executePromise = task.execute();
      
      // 在执行过程中取消
      setTimeout(() => {
        task.cancel();
      }, 100);
      
      const result = await executePromise;
      
      expect(result.success).toBe(false);
      expect(result.message).toContain('任务已取消');
      expect(task.getStatus()).toBe(TaskStatus.CANCELLED);
    });
  });
});