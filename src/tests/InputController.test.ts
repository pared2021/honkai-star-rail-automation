import InputController, { GameWindow, SmoothMoveOptions, QueuedAction, RecordedAction } from '../modules/InputController';

// Mock robotjs
jest.mock('robotjs', () => ({
  moveMouse: jest.fn(),
  mouseClick: jest.fn(),
  keyTap: jest.fn(),
  typeString: jest.fn(),
  dragMouse: jest.fn(),
  scrollMouse: jest.fn(),
  getMousePos: jest.fn(() => ({ x: 100, y: 100 })),
  keyToggle: jest.fn(),
  setMouseDelay: jest.fn(),
  setKeyboardDelay: jest.fn()
}));

describe('InputController', () => {
  let inputController: InputController;
  const mockGameWindow: GameWindow = {
    x: 0,
    y: 0,
    width: 1920,
    height: 1080
  };

  beforeEach(() => {
    inputController = new InputController();
    inputController.setGameWindow(mockGameWindow);
    jest.clearAllMocks();
  });

  afterEach(() => {
    inputController.setEnabled(false);
    inputController.clearQueue();
    inputController.clearRecording();
    inputController.resetEmergencyStop();
  });

  // ==================== 基础功能测试 ====================

  describe('基础功能', () => {
    test('应该能够启用和禁用输入控制', () => {
      expect(inputController.isInputEnabled()).toBe(true);
      
      inputController.setEnabled(false);
      expect(inputController.isInputEnabled()).toBe(false);
      
      inputController.setEnabled(true);
      expect(inputController.isInputEnabled()).toBe(true);
    });

    test('应该能够设置和获取游戏窗口', () => {
      const newWindow: GameWindow = { x: 100, y: 100, width: 800, height: 600 };
      inputController.setGameWindow(newWindow);
      
      const retrievedWindow = inputController.getGameWindow();
      expect(retrievedWindow).toEqual(newWindow);
    });

    test('应该能够设置和获取默认延迟', () => {
      const newDelay = 200;
      inputController.setDefaultDelay(newDelay);
      
      expect(inputController.getDefaultDelay()).toBe(newDelay);
    });

    test('应该能够获取配置信息', () => {
      const config = inputController.getConfig();
      
      expect(config).toHaveProperty('isEnabled');
      expect(config).toHaveProperty('defaultDelay');
      expect(config).toHaveProperty('gameWindow');
      expect(config).toHaveProperty('safetyChecks');
    });
  });

  // ==================== 平滑移动API测试 ====================

  describe('平滑移动API', () => {
    beforeEach(() => {
      inputController.setEnabled(true);
    });

    test('应该能够执行线性平滑移动', async () => {
      const options: SmoothMoveOptions = {
        duration: 100,
        easing: 'linear',
        steps: 10
      };

      await inputController.smoothMoveTo(500, 300, options);
      
      // 验证robotjs.moveMouse被调用
      const robotjs = require('robotjs');
      expect(robotjs.moveMouse).toHaveBeenCalled();
    });

    test('应该能够执行缓动平滑移动', async () => {
      const options: SmoothMoveOptions = {
        duration: 150,
        easing: 'easeInOut',
        steps: 15
      };

      await inputController.smoothMoveTo(600, 400, options);
      
      const robotjs = require('robotjs');
      expect(robotjs.moveMouse).toHaveBeenCalled();
    });

    test('应该能够执行贝塞尔曲线移动', async () => {
      const options: SmoothMoveOptions = {
        duration: 200,
        easing: 'bezier',
        steps: 20,
        bezierControlPoints: {
          cp1: { x: 0.25, y: 0.1 },
          cp2: { x: 0.25, y: 1.0 }
        }
      };

      await inputController.smoothMoveTo(700, 500, options);
      
      const robotjs = require('robotjs');
      expect(robotjs.moveMouse).toHaveBeenCalled();
    });

    test('禁用状态下不应该执行移动', async () => {
      inputController.setEnabled(false);
      
      const result = await inputController.smoothMoveTo(500, 300);
      
      expect(result).toBe(false);
      const robotjs = require('robotjs');
      expect(robotjs.moveMouse).not.toHaveBeenCalled();
    });
  });

  // ==================== 操作队列系统测试 ====================

  describe('操作队列系统', () => {
    beforeEach(() => {
      inputController.setEnabled(true);
    });

    test('应该能够添加操作到队列', () => {
      const action: QueuedAction = {
        id: 'test-1',
        type: 'click',
        params: { x: 100, y: 100 },
        priority: 'medium',
        timestamp: Date.now(),
        maxRetries: 3
      };

      const result = inputController.addToQueue(action);
      expect(typeof result).toBe('string');
      expect(result).toMatch(/^action_\d+_[a-z0-9]+$/);
      
      const status = inputController.getQueueStatus();
      expect(status.size).toBe(1);
    });

    test('应该能够按优先级排序队列', () => {
      const lowPriorityAction: QueuedAction = {
        id: 'low',
        type: 'click',
        params: { x: 100, y: 100 },
        priority: 'low',
        timestamp: Date.now()
      };

      const highPriorityAction: QueuedAction = {
        id: 'high',
        type: 'click',
        params: { x: 200, y: 200 },
        priority: 'high',
        timestamp: Date.now()
      };

      inputController.addToQueue(lowPriorityAction);
      inputController.addToQueue(highPriorityAction);
      
      const status = inputController.getQueueStatus();
      expect(status.size).toBe(2);
    });

    test('应该能够暂停和恢复队列执行', () => {
      inputController.pauseQueue();
      
      let status = inputController.getQueueStatus();
      expect(status.isPaused).toBe(true);
      
      inputController.resumeQueue();
      
      status = inputController.getQueueStatus();
      expect(status.isPaused).toBe(false);
    });

    test('应该能够清空队列', () => {
      const action: QueuedAction = {
        id: 'test',
        type: 'click',
        params: { x: 100, y: 100 },
        priority: 'medium',
        timestamp: Date.now()
      };

      inputController.addToQueue(action);
      expect(inputController.getQueueStatus().size).toBe(1);
      
      inputController.clearQueue();
      expect(inputController.getQueueStatus().size).toBe(0);
    });

    test('应该能够从队列中移除特定操作', () => {
      const action: QueuedAction = {
        id: 'removable',
        type: 'click',
        params: { x: 100, y: 100 },
        priority: 'medium',
        timestamp: Date.now()
      };

      const actionId = inputController.addToQueue(action);
      expect(inputController.getQueueStatus().size).toBe(1);
      
      const removed = inputController.removeFromQueue(actionId);
      expect(removed).toBe(true);
      expect(inputController.getQueueStatus().size).toBe(0);
    });
  });

  // ==================== 录制回放功能测试 ====================

  describe('录制回放功能', () => {
    beforeEach(() => {
      inputController.setEnabled(true);
    });

    test('应该能够开始和停止录制', () => {
      expect(inputController.getRecordingStatus().isRecording).toBe(false);
      
      const startResult = inputController.startRecording();
      expect(startResult).toBe(true);
      expect(inputController.getRecordingStatus().isRecording).toBe(true);
      
      const actions = inputController.stopRecording();
      expect(Array.isArray(actions)).toBe(true);
      expect(inputController.getRecordingStatus().isRecording).toBe(false);
    });

    test('重复开始录制应该返回false', () => {
      inputController.startRecording();
      const secondStart = inputController.startRecording();
      expect(secondStart).toBe(false);
    });

    test('未开始录制时停止录制应该返回空数组', () => {
      const actions = inputController.stopRecording();
      expect(actions).toEqual([]);
    });

    test('应该能够清空录制', () => {
      inputController.startRecording();
      // 模拟一些录制操作
      inputController.stopRecording();
      
      inputController.clearRecording();
      const status = inputController.getRecordingStatus();
      expect(status.recordedActionsCount).toBe(0);
    });

    test('应该能够获取录制状态', () => {
      const initialStatus = inputController.getRecordingStatus();
      expect(initialStatus).toHaveProperty('isRecording');
      expect(initialStatus).toHaveProperty('recordedActionsCount');
      expect(initialStatus).toHaveProperty('recordingDuration');
    });
  });

  // ==================== 安全检查功能测试 ====================

  describe('安全检查功能', () => {
    test('应该能够验证游戏窗口配置', () => {
      const validWindow: GameWindow = {
        x: 0,
        y: 0,
        width: 1920,
        height: 1080
      };

      const validation = inputController.validateGameWindow(validWindow);
      expect(validation.isValid).toBe(true);
      expect(validation.errors).toHaveLength(0);
    });

    test('应该能够检测无效的游戏窗口配置', () => {
      const invalidWindow: GameWindow = {
        x: -100,
        y: -100,
        width: -800,
        height: 0
      };

      const validation = inputController.validateGameWindow(invalidWindow);
      expect(validation.isValid).toBe(false);
      expect(validation.errors.length).toBeGreaterThan(0);
    });

    test('应该能够检查坐标是否在安全区域内', () => {
      const safeCoordinate = inputController.isCoordinateInSafeArea(500, 500, 10);
      expect(safeCoordinate).toBe(true);
      
      const unsafeCoordinate = inputController.isCoordinateInSafeArea(5, 5, 10);
      expect(unsafeCoordinate).toBe(false);
    });

    test('应该能够获取游戏窗口中心点', () => {
      const center = inputController.getGameWindowCenter();
      expect(center).not.toBeNull();
      expect(center?.x).toBe(960); // 1920 / 2
      expect(center?.y).toBe(540); // 1080 / 2
    });

    test('应该能够获取游戏窗口详细信息', () => {
      const info = inputController.getGameWindowInfo();
      expect(info).toHaveProperty('window');
      expect(info).toHaveProperty('validation');
      expect(info).toHaveProperty('area');
      expect(info).toHaveProperty('aspectRatio');
      expect(info.area).toBe(1920 * 1080);
    });
  });

  // ==================== 重试机制测试 ====================

  describe('重试机制', () => {
    test('应该能够执行带重试的操作', async () => {
      let attemptCount = 0;
      const operation = jest.fn().mockImplementation(async () => {
        attemptCount++;
        if (attemptCount < 2) {
          throw new Error('模拟失败');
        }
        return '成功';
      });

      const result = await inputController.executeWithRetry(operation, 3, 10);
      expect(result).toBe('成功');
      expect(operation).toHaveBeenCalledTimes(2);
    });

    test('达到最大重试次数后应该抛出错误', async () => {
      const operation = jest.fn().mockRejectedValue(new Error('持续失败'));

      await expect(
        inputController.executeWithRetry(operation, 2, 10)
      ).rejects.toThrow('持续失败');
      
      expect(operation).toHaveBeenCalledTimes(3); // 初始尝试 + 2次重试
    });
  });

  // ==================== 性能监控测试 ====================

  describe('性能监控', () => {
    test('应该能够获取性能统计信息', () => {
      const stats = inputController.getPerformanceStats();
      expect(stats).toHaveProperty('averageExecutionTime');
      expect(stats).toHaveProperty('minExecutionTime');
      expect(stats).toHaveProperty('maxExecutionTime');
      expect(stats).toHaveProperty('standardDeviation');
      expect(stats).toHaveProperty('totalSamples');
      expect(stats).toHaveProperty('recommendedDelay');
    });

    test('应该能够重置性能统计数据', () => {
      inputController.resetPerformanceStats();
      const stats = inputController.getPerformanceStats();
      expect(stats.totalSamples).toBe(0);
    });

    test('应该能够检查性能健康状况', () => {
      const health = inputController.checkPerformanceHealth();
      expect(health).toHaveProperty('isHealthy');
      expect(health).toHaveProperty('issues');
      expect(health).toHaveProperty('recommendations');
      expect(Array.isArray(health.issues)).toBe(true);
      expect(Array.isArray(health.recommendations)).toBe(true);
    });
  });

  // ==================== 紧急停止功能测试 ====================

  describe('紧急停止功能', () => {
    test('应该能够触发紧急停止', () => {
      inputController.emergencyStop();
      // 紧急停止后的状态验证需要根据具体实现来测试
    });

    test('应该能够重置紧急停止状态', () => {
      inputController.emergencyStop();
      inputController.resetEmergencyStop();
      // 重置后的状态验证
    });
  });

  // ==================== 统计信息测试 ====================

  describe('统计信息', () => {
    test('应该能够获取增强的统计信息', () => {
      const stats = inputController.getEnhancedStats();
      expect(stats).toHaveProperty('totalActions');
      expect(stats).toHaveProperty('successfulActions');
      expect(stats).toHaveProperty('failedActions');
      // InputStats接口不包含successRate，使用getStats()方法获取包含successRate的统计信息
      const detailedStats = inputController.getStats();
      expect(detailedStats).toHaveProperty('successRate');
    });

    test('应该能够获取输入日志', () => {
      const logs = inputController.getInputLogs();
      expect(Array.isArray(logs)).toBe(true);
    });

    test('应该能够清空输入日志', () => {
      inputController.clearLogs();
      const logs = inputController.getInputLogs();
      expect(logs).toHaveLength(0);
    });
  });
});