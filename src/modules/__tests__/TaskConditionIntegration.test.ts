import { DailyCommissionTask } from '../DailyCommissionTask';
import { TaskConditionManager } from '../TaskConditionManager';
import { SceneDetector } from '../SceneDetector';
import { InputController } from '../InputController';
import { ImageRecognition } from '../ImageRecognition';
import { GameDetector } from '../GameDetector';
import { Logger } from '../../utils/Logger';

// Mock dependencies
jest.mock('../../utils/Logger');
jest.mock('../SceneDetector');
jest.mock('../InputController');
jest.mock('../ImageRecognition');
jest.mock('../GameDetector');

describe('TaskConditionManager Integration with DailyCommissionTask', () => {
  let dailyCommissionTask: DailyCommissionTask;
  let conditionManager: TaskConditionManager;
  let mockSceneDetector: jest.Mocked<SceneDetector>;
  let mockInputController: jest.Mocked<InputController>;
  let mockImageRecognition: jest.Mocked<ImageRecognition>;
  let mockGameDetector: jest.Mocked<GameDetector>;
  let mockLogger: jest.Mocked<Logger>;

  beforeEach(() => {
    // Mock getCurrentTime method for DailyCommissionTask
    jest.spyOn(DailyCommissionTask.prototype, 'getCurrentTime').mockReturnValue(1672531200000);
    // Setup mocks
    mockLogger = {
      info: jest.fn(),
      error: jest.fn(),
      warn: jest.fn(),
      debug: jest.fn()
    } as any;
    (Logger.getInstance as jest.Mock).mockReturnValue(mockLogger);

    mockSceneDetector = {
      detectCurrentScene: jest.fn(),
      waitForScene: jest.fn()
    } as any;

    mockInputController = {
      pressKey: jest.fn(),
      click: jest.fn()
    } as any;

    mockImageRecognition = {
      findImage: jest.fn()
    } as any;

    mockGameDetector = {
      isGameRunning: jest.fn(),
      isGameActive: jest.fn()
    } as any;

    // Create condition manager
    conditionManager = new TaskConditionManager(mockGameDetector);

    // Create task with condition manager
    dailyCommissionTask = new DailyCommissionTask(
      mockSceneDetector,
      mockInputController,
      mockImageRecognition,
      mockGameDetector,
      {},
      conditionManager
    );
  });

  describe('Condition Checking Integration', () => {
    it('should pass when all conditions are satisfied', async () => {
      // Setup: Game is running, good time, good resources
      mockGameDetector.isGameRunning.mockReturnValue(true);
      mockGameDetector.isGameActive.mockReturnValue(true);
      
      // Mock current time to be in allowed range (e.g., 10 AM)
      const mockDate = new Date('2024-01-01T10:00:00');
      jest.spyOn(global, 'Date').mockImplementation(() => mockDate as any);
      
      // Mock system resources (simulated as good)
      jest.spyOn(Math, 'random').mockReturnValue(0.8); // High CPU available
      
      const canExecute = await dailyCommissionTask.canExecute();
      expect(canExecute).toBe(true);
    });

    it('should fail when game is not running', async () => {
      // Setup: Game is not running
      mockGameDetector.isGameRunning.mockReturnValue(false);
      mockGameDetector.isGameActive.mockReturnValue(false);
      
      const canExecute = await dailyCommissionTask.canExecute();
      expect(canExecute).toBe(false);
    });

    it('should fail when time is outside allowed range', async () => {
      // Setup: Game is running but time is not allowed (e.g., 3 AM)
      mockGameDetector.isGameRunning.mockReturnValue(true);
      mockGameDetector.isGameActive.mockReturnValue(true);
      
      // Clear the existing getCurrentTime mock from beforeEach and set new one
      jest.restoreAllMocks();
      const mockTime3AM = new Date('2024-01-15T03:00:00.000Z').getTime(); // 1705287600000
      const getCurrentTimeSpy = jest.spyOn(DailyCommissionTask.prototype, 'getCurrentTime')
        .mockReturnValue(mockTime3AM);
      
      // Mock good system resources directly
      const originalGetSystemResources = conditionManager['getSystemResources'];
      conditionManager['getSystemResources'] = jest.fn().mockResolvedValue({
        cpuAvailable: 80, // Above required 20%
        memoryAvailable: 70, // Above required 30%
        networkLatency: 50,
        diskSpace: 5000
      });
      
      // Setup mocks for task execution (in case condition check passes unexpectedly)
      mockSceneDetector.detectCurrentScene.mockResolvedValue({
        scene: 'MAIN_MENU' as any,
        confidence: 0.9,
        timestamp: 1672531200000,
        matchedTemplates: [],
        detectionTime: 100
      });
      mockSceneDetector.waitForScene.mockResolvedValue(true);
      mockImageRecognition.findImage.mockResolvedValue({
        found: true,
        location: { x: 200, y: 200 },
        confidence: 0.9
      });
      
      try {
        // canExecute only checks game state, not time conditions
        const canExecute = await dailyCommissionTask.canExecute();
        expect(canExecute).toBe(true); // Game state check passes
        
        // Test if getCurrentTime mock is working
        expect(dailyCommissionTask.getCurrentTime()).toBe(mockTime3AM);
        
        // Directly test checkConditions to see what it returns
        // Access conditions from the task's config
        const taskConditions = (dailyCommissionTask as any).config.conditions;
        const conditionResult = await conditionManager.checkConditions('DailyCommission', taskConditions);
        
        // Log the actual result for debugging
        console.log('Condition result:', JSON.stringify(conditionResult, null, 2));
        
        // The time condition should fail at 3:00 AM (outside 06:00-23:59)
        expect(conditionResult.satisfied).toBe(false);
        expect(conditionResult.message).toContain('时间');
        
        // Now test the full execute flow
        const result = await dailyCommissionTask.execute();
        expect(result.success).toBe(false);
        expect(result.message).toContain('任务条件不满足');
      } finally {
         // Cleanup
         getCurrentTimeSpy.mockRestore();
         conditionManager['getSystemResources'] = originalGetSystemResources;
       }
     });

    it('should fail when system resources are insufficient', async () => {
      // Setup: Game is running, good time, but poor resources
      mockGameDetector.isGameRunning.mockReturnValue(true);
      mockGameDetector.isGameActive.mockReturnValue(true);
      
      const mockDate = new Date('2024-01-01T10:00:00');
      const dateSpy = jest.spyOn(global, 'Date').mockImplementation(() => mockDate as any);
      
      // Mock poor system resources - need very high random values to get below thresholds
      // cpuAvailable = 100 - random * 50, need < 20, so random > 1.6 (impossible)
      // memoryAvailable = 100 - random * 40, need < 30, so random > 1.75 (impossible)
      // Let's mock the getSystemResources method directly instead
      const originalGetSystemResources = conditionManager['getSystemResources'];
      conditionManager['getSystemResources'] = jest.fn().mockResolvedValue({
        cpuAvailable: 15, // Below required 20%
        memoryAvailable: 25, // Below required 30%
        networkLatency: 50,
        diskSpace: 5000
      });
      
      // Setup mocks for task execution (in case condition check passes unexpectedly)
      mockSceneDetector.detectCurrentScene.mockResolvedValue({
        scene: 'MAIN_MENU' as any,
        confidence: 0.9,
        timestamp: 1672531200000,
        matchedTemplates: [],
        detectionTime: 100
      });
      mockSceneDetector.waitForScene.mockResolvedValue(true);
      mockImageRecognition.findImage.mockResolvedValue({
        found: true,
        location: { x: 200, y: 200 },
        confidence: 0.9
      });
      
      try {
        // canExecute only checks game state, not resource conditions
        const canExecute = await dailyCommissionTask.canExecute();
        expect(canExecute).toBe(true); // Game state check passes
        
        // But execute should fail due to resource condition check in TaskExecutor
        const result = await dailyCommissionTask.execute();
        expect(result.success).toBe(false);
        expect(result.message).toContain('任务条件不满足:');
        expect(result.message).toContain('CPU可用率不足');
      } finally {
        // Restore mocks
        dateSpy.mockRestore();
        conditionManager['getSystemResources'] = originalGetSystemResources;
      }
    });
  });

  describe('Task Execution with Conditions', () => {
    beforeEach(() => {
      // Setup successful conditions by default
      mockGameDetector.isGameRunning.mockReturnValue(true);
      mockGameDetector.isGameActive.mockReturnValue(true);
      
      const mockDate = new Date('2024-01-01T10:00:00');
      jest.spyOn(global, 'Date').mockImplementation(() => mockDate as any);
      jest.spyOn(Math, 'random').mockReturnValue(0.8);
      
      // Mock successful task execution
      mockSceneDetector.detectCurrentScene.mockResolvedValue({
        scene: 'MAIN_MENU' as any,
        confidence: 0.9,
        timestamp: 1672531200000,
        matchedTemplates: [],
        detectionTime: 100
      });
      mockSceneDetector.waitForScene.mockResolvedValue(true);
      mockImageRecognition.findImage.mockResolvedValue({
        found: true,
        location: { x: 200, y: 200 },
        confidence: 0.9
      });
    });

    it('should execute task successfully when all conditions pass', async () => {
      const result = await dailyCommissionTask.execute();
      
      expect(result.success).toBe(true);
      expect(result.message).toContain('每日委托任务执行完成');
      expect(mockLogger.info).toHaveBeenCalledWith(
        expect.stringContaining('条件检查通过')
      );
    });

    it('should log condition check results', async () => {
      await dailyCommissionTask.execute();
      
      // Verify that condition checking was logged
      expect(mockLogger.info).toHaveBeenCalledWith(
        expect.stringContaining('条件检查通过')
      );
    });
  });

  describe('Condition Manager Integration', () => {
    it('should use condition manager when provided', () => {
      expect(dailyCommissionTask['conditionManager']).toBe(conditionManager);
    });

    it('should work without condition manager', () => {
      const taskWithoutConditions = new DailyCommissionTask(
        mockSceneDetector,
        mockInputController,
        mockImageRecognition,
        mockGameDetector
      );
      
      expect(taskWithoutConditions['conditionManager']).toBeUndefined();
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  afterAll(() => {
    jest.restoreAllMocks();
  });
});