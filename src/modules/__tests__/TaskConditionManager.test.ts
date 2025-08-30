import { TaskConditionManager, ConditionType, ConditionLogic, TimeCondition, ResourceCondition, GameStateCondition, CustomCondition, DependencyCondition, ConditionGroup } from '../TaskConditionManager';
import { GameDetector } from '../GameDetector';
import { Logger } from '../../utils/Logger';

// Mock dependencies
jest.mock('../../utils/Logger');
jest.mock('../GameDetector');

describe('TaskConditionManager', () => {
  let conditionManager: TaskConditionManager;
  let mockGameDetector: jest.Mocked<GameDetector>;
  let mockLogger: jest.Mocked<Logger>;

  beforeEach(() => {
    // Setup mocks
    mockLogger = {
      error: jest.fn(),
      info: jest.fn(),
      warn: jest.fn(),
      debug: jest.fn()
    } as any;
    
    (Logger.getInstance as jest.Mock).mockReturnValue(mockLogger);
    
    mockGameDetector = {
      isGameRunning: jest.fn().mockReturnValue(false),
      getCurrentScene: jest.fn()
    } as any;
    
    conditionManager = new TaskConditionManager(mockGameDetector);
  });

  afterEach(() => {
    jest.clearAllMocks();
    conditionManager.clearHistory();
  });

  describe('Time Conditions', () => {
    it('should pass when current time is within allowed range', async () => {
      const now = new Date();
      const currentHour = now.getHours();
      const startTime = `${(currentHour - 1).toString().padStart(2, '0')}:00`;
      const endTime = `${(currentHour + 1).toString().padStart(2, '0')}:00`;
      
      const timeCondition: TimeCondition = {
        type: ConditionType.TIME,
        startTime,
        endTime
      };

      const result = await conditionManager.checkConditions('test-task', [timeCondition]);
      expect(result.satisfied).toBe(true);
      expect(result.message).toBe('所有条件都满足');
    });

    it('should fail when current time is outside allowed range', async () => {
      const timeCondition: TimeCondition = {
        type: ConditionType.TIME,
        startTime: '02:00',
        endTime: '03:00'
      };

      const result = await conditionManager.checkConditions('test-task', [timeCondition]);
      expect(result.satisfied).toBe(false);
      expect(result.message).toContain('不在允许的执行时间范围内');
    });

    it('should respect day of week restrictions', async () => {
      const today = new Date().getDay();
      const otherDay = (today + 1) % 7;
      
      const timeCondition: TimeCondition = {
        type: ConditionType.TIME,
        daysOfWeek: [otherDay]
      };

      const result = await conditionManager.checkConditions('test-task', [timeCondition]);
      expect(result.satisfied).toBe(false);
      expect(result.message).toContain('不在允许的执行日期内');
    });

    it('should respect cooldown period', async () => {
      const timeCondition: TimeCondition = {
        type: ConditionType.TIME,
        cooldownMinutes: 60,
        lastExecuted: new Date(Date.now() - 30 * 60 * 1000) // 30 minutes ago
      };

      const result = await conditionManager.checkConditions('test-task', [timeCondition]);
      expect(result.satisfied).toBe(false);
      expect(result.message).toContain('冷却时间未结束');
    });
  });

  describe('Resource Conditions', () => {
    it('should pass when system resources are sufficient', async () => {
      // Mock system resources to be high
      jest.spyOn(conditionManager as any, 'getSystemResources').mockResolvedValue({
        cpuAvailable: 80,
        memoryAvailable: 70,
        networkLatency: 20,
        diskSpace: 5000
      });

      const resourceCondition: ResourceCondition = {
        type: ConditionType.RESOURCE,
        minCpuAvailable: 50,
        minMemoryAvailable: 60,
        maxNetworkLatency: 50
      };

      const result = await conditionManager.checkConditions('test-task', [resourceCondition]);
      expect(result.satisfied).toBe(true);
    });

    it('should fail when CPU is insufficient', async () => {
      jest.spyOn(conditionManager as any, 'getSystemResources').mockResolvedValue({
        cpuAvailable: 30,
        memoryAvailable: 70,
        networkLatency: 20,
        diskSpace: 5000
      });

      const resourceCondition: ResourceCondition = {
        type: ConditionType.RESOURCE,
        minCpuAvailable: 50
      };

      const result = await conditionManager.checkConditions('test-task', [resourceCondition]);
      expect(result.satisfied).toBe(false);
      expect(result.message).toContain('CPU可用率不足');
    });

    it('should fail when network latency is too high', async () => {
      jest.spyOn(conditionManager as any, 'getSystemResources').mockResolvedValue({
        cpuAvailable: 80,
        memoryAvailable: 70,
        networkLatency: 200,
        diskSpace: 5000
      });

      const resourceCondition: ResourceCondition = {
        type: ConditionType.RESOURCE,
        maxNetworkLatency: 100
      };

      const result = await conditionManager.checkConditions('test-task', [resourceCondition]);
      expect(result.satisfied).toBe(false);
      expect(result.message).toContain('网络延迟过高');
    });
  });

  describe('Game State Conditions', () => {
    it('should pass when game is running and condition requires it', async () => {
      mockGameDetector.isGameRunning.mockReturnValue(true);

      const gameStateCondition: GameStateCondition = {
        type: ConditionType.GAME_STATE,
        gameRunning: true
      };

      const result = await conditionManager.checkConditions('test-task', [gameStateCondition]);
      expect(result.satisfied).toBe(true);
    });

    it('should fail when game is not running but condition requires it', async () => {
      mockGameDetector.isGameRunning.mockReturnValue(false);

      const gameStateCondition: GameStateCondition = {
        type: ConditionType.GAME_STATE,
        gameRunning: true
      };

      const result = await conditionManager.checkConditions('test-task', [gameStateCondition]);
      expect(result.satisfied).toBe(false);
      expect(result.message).toBe('条件不满足: 游戏未运行');
    });

    it('should pass when game is not running and condition requires it not to run', async () => {
      mockGameDetector.isGameRunning.mockReturnValue(false);

      const gameStateCondition: GameStateCondition = {
        type: ConditionType.GAME_STATE,
        gameRunning: false
      };

      const result = await conditionManager.checkConditions('test-task', [gameStateCondition]);
      expect(result.satisfied).toBe(true);
    });
  });

  describe('Custom Conditions', () => {
    it('should pass when custom checker returns satisfied', async () => {
      const customCondition: CustomCondition = {
        type: ConditionType.CUSTOM,
        name: 'test-custom',
        checker: async () => ({ satisfied: true, message: 'Custom condition met' })
      };

      const result = await conditionManager.checkConditions('test-task', [customCondition]);
      expect(result.satisfied).toBe(true);
    });

    it('should fail when custom checker returns not satisfied', async () => {
      const customCondition: CustomCondition = {
        type: ConditionType.CUSTOM,
        name: 'test-custom',
        checker: async () => ({ satisfied: false, message: 'Custom condition not met' })
      };

      const result = await conditionManager.checkConditions('test-task', [customCondition]);
      expect(result.satisfied).toBe(false);
      expect(result.message).toContain('Custom condition not met');
    });

    it('should handle custom checker errors', async () => {
      const customCondition: CustomCondition = {
        type: ConditionType.CUSTOM,
        name: 'test-custom',
        checker: async () => { throw new Error('Custom checker error'); }
      };

      const result = await conditionManager.checkConditions('test-task', [customCondition]);
      expect(result.satisfied).toBe(false);
      expect(result.message).toContain('自定义条件检查失败');
    });
  });

  describe('Dependency Conditions', () => {
    it('should pass when all required dependencies are completed', async () => {
      conditionManager.markTaskCompleted('task1');
      conditionManager.markTaskCompleted('task2');

      const dependencyCondition: DependencyCondition = {
        type: ConditionType.DEPENDENCY,
        taskIds: ['task1', 'task2'],
        requireAll: true
      };

      const result = await conditionManager.checkConditions('test-task', [dependencyCondition]);
      expect(result.satisfied).toBe(true);
    });

    it('should fail when not all required dependencies are completed', async () => {
      conditionManager.markTaskCompleted('task1');

      const dependencyCondition: DependencyCondition = {
        type: ConditionType.DEPENDENCY,
        taskIds: ['task1', 'task2'],
        requireAll: true
      };

      const result = await conditionManager.checkConditions('test-task', [dependencyCondition]);
      expect(result.satisfied).toBe(false);
      expect(result.message).toContain('依赖条件不满足');
    });

    it('should pass when at least one dependency is completed (requireAll=false)', async () => {
      conditionManager.markTaskCompleted('task1');

      const dependencyCondition: DependencyCondition = {
        type: ConditionType.DEPENDENCY,
        taskIds: ['task1', 'task2'],
        requireAll: false
      };

      const result = await conditionManager.checkConditions('test-task', [dependencyCondition]);
      expect(result.satisfied).toBe(true);
    });
  });

  describe('Condition Groups', () => {
    it('should handle AND logic correctly', async () => {
      mockGameDetector.isGameRunning.mockReturnValue(true);
      
      const conditionGroup: ConditionGroup = {
        logic: ConditionLogic.AND,
        conditions: [
          {
            type: ConditionType.GAME_STATE,
            gameRunning: true
          },
          {
            type: ConditionType.CUSTOM,
            name: 'test',
            checker: async () => ({ satisfied: true, message: 'OK' })
          }
        ]
      };

      const result = await conditionManager.checkConditions('test-task', conditionGroup);
      expect(result.satisfied).toBe(true);
      expect(result.message).toBe('所有条件都满足');
    });

    it('should handle OR logic correctly', async () => {
      mockGameDetector.isGameRunning.mockReturnValue(false);
      
      const conditionGroup: ConditionGroup = {
        logic: ConditionLogic.OR,
        conditions: [
          {
            type: ConditionType.GAME_STATE,
            gameRunning: true // This will fail
          },
          {
            type: ConditionType.CUSTOM,
            name: 'test',
            checker: async () => ({ satisfied: true, message: 'OK' }) // This will pass
          }
        ]
      };

      const result = await conditionManager.checkConditions('test-task', conditionGroup);
      expect(result.satisfied).toBe(true);
      expect(result.message).toBe('至少一个条件满足');
    });

    it('should handle NOT logic correctly', async () => {
      mockGameDetector.isGameRunning.mockReturnValue(false);
      
      const conditionGroup: ConditionGroup = {
        logic: ConditionLogic.NOT,
        conditions: [
          {
            type: ConditionType.GAME_STATE,
            gameRunning: true // This will fail, so NOT logic should pass
          }
        ]
      };

      const result = await conditionManager.checkConditions('test-task', conditionGroup);
      expect(result.satisfied).toBe(true);
      expect(result.message).toBe('条件不满足（符合NOT逻辑）');
    });
  });

  describe('Task Management', () => {
    it('should mark tasks as completed', () => {
      conditionManager.markTaskCompleted('task1');
      
      // Verify through dependency condition
      const dependencyCondition: DependencyCondition = {
        type: ConditionType.DEPENDENCY,
        taskIds: ['task1'],
        requireAll: true
      };

      return conditionManager.checkConditions('test-task', [dependencyCondition])
        .then(result => {
          expect(result.satisfied).toBe(true);
        });
    });

    it('should clear history correctly', async () => {
      conditionManager.markTaskCompleted('task1');
      conditionManager.clearHistory();
      
      const dependencyCondition: DependencyCondition = {
        type: ConditionType.DEPENDENCY,
        taskIds: ['task1'],
        requireAll: true
      };

      const result = await conditionManager.checkConditions('test-task', [dependencyCondition]);
      expect(result.satisfied).toBe(false);
    });
  });

  describe('Error Handling', () => {
    it('should handle unknown condition types', async () => {
      const unknownCondition = {
        type: 'unknown' as any
      };

      const result = await conditionManager.checkConditions('test-task', [unknownCondition]);
      expect(result.satisfied).toBe(false);
      expect(result.message).toContain('未知的条件类型');
    });

    it('should handle condition check errors gracefully', async () => {
      // Mock getSystemResources to throw an error
      jest.spyOn(conditionManager as any, 'getSystemResources').mockRejectedValue(new Error('System error'));

      const resourceCondition: ResourceCondition = {
        type: ConditionType.RESOURCE,
        minCpuAvailable: 50
      };

      const result = await conditionManager.checkConditions('test-task', [resourceCondition]);
      expect(result.satisfied).toBe(false);
      expect(result.message).toContain('条件检查出错');
    });
  });
});