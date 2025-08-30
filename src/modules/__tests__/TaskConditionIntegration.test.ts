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
      
      const mockDate = new Date('2024-01-01T03:00:00');
      jest.spyOn(global, 'Date').mockImplementation(() => mockDate as any);
      
      // Should fail during execution due to time condition
      try {
        await dailyCommissionTask.execute();
        fail('Expected task to fail due to time condition');
      } catch (error) {
        expect(error.message).toContain('任务条件不满足');
      }
    });

    it('should fail when system resources are insufficient', async () => {
      // Setup: Game is running, good time, but poor resources
      mockGameDetector.isGameRunning.mockReturnValue(true);
      mockGameDetector.isGameActive.mockReturnValue(true);
      
      const mockDate = new Date('2024-01-01T10:00:00');
      jest.spyOn(global, 'Date').mockImplementation(() => mockDate as any);
      
      // Mock poor system resources
      jest.spyOn(Math, 'random').mockReturnValue(0.1); // Low CPU available
      
      try {
        await dailyCommissionTask.execute();
        fail('Expected task to fail due to resource condition');
      } catch (error) {
        expect(error.message).toContain('任务条件不满足');
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
        location: { x: 100, y: 100 }
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
    jest.restoreAllMocks();
  });
});