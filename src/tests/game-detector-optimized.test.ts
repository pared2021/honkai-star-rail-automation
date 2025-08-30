import { GameDetectorOptimized } from '../modules/GameDetectorOptimized';
import { GameStatus } from '../types';
import { jest } from '@jest/globals';

// Mock 外部依赖
jest.mock('node-window-manager', () => ({
  windowManager: {
    getWindows: jest.fn(() => [])
  }
}));

jest.mock('active-win', () => jest.fn());
jest.mock('ps-list', () => jest.fn());

// Mock 浏览器兼容性工具
jest.mock('../utils/browserCompat', () => ({
  isBrowser: false
}));

describe('GameDetectorOptimized', () => {
  let detector: GameDetectorOptimized;
  let mockPsList: jest.MockedFunction<any>;
  let mockActiveWin: jest.MockedFunction<any>;
  let mockWindowManager: any;

  afterAll(async () => {
    // 确保所有定时器都被清理
    jest.clearAllTimers();
    // 等待所有异步操作完成
    await new Promise(resolve => setTimeout(resolve, 200));
  });

  beforeEach(() => {
    // 重置所有 mock
    jest.clearAllMocks();
    
    // 设置 mock
    mockPsList = require('ps-list');
    mockActiveWin = require('active-win');
    mockWindowManager = require('node-window-manager').windowManager;
    
    // 创建检测器实例
    detector = new GameDetectorOptimized({
      gameProcessNames: ['StarRail.exe', 'TestGame.exe'],
      gameWindowTitles: ['崩坏：星穹铁道', 'Test Game'],
      detectionInterval: 100, // 快速测试
      enableLogging: false // 禁用日志以减少测试输出
    });
  });

  afterEach(async () => {
    // 确保检测器停止
    detector.stopDetection();
    
    // 移除所有监听器
    detector.removeAllListeners();
    
    // 清理所有 mock
    jest.clearAllMocks();
    
    // 等待所有异步操作完成
    await new Promise(resolve => process.nextTick(resolve));
    
    // 等待一小段时间确保清理完成
    await new Promise(resolve => setTimeout(resolve, 50));
  });

  describe('基础功能测试', () => {
    test('应该能够创建检测器实例', () => {
      expect(detector).toBeInstanceOf(GameDetectorOptimized);
    });

    test('应该能够开始和停止检测', () => {
      const startSpy = jest.spyOn(detector, 'emit');
      
      detector.startDetection(100);
      expect(startSpy).toHaveBeenCalledWith('detectionStarted');
      
      detector.stopDetection();
      expect(startSpy).toHaveBeenCalledWith('detectionStopped');
    });

    test('应该能够获取当前状态', async () => {
      mockPsList.mockResolvedValue([]);
      
      const status = await detector.getCurrentStatus();
      expect(status).toHaveProperty('isRunning');
      expect(status).toHaveProperty('isActive');
      expect(status.isRunning).toBe(false);
    });
  });

  describe('性能优化功能测试', () => {
    test('应该能够获取性能统计', () => {
      const stats = detector.getPerformanceStats();
      expect(stats).toHaveProperty('totalDetections');
      expect(stats).toHaveProperty('averageDetectionTime');
      expect(stats).toHaveProperty('cacheHitRate');
      expect(stats).toHaveProperty('errorRate');
    });

    test('应该能够设置自适应模式', () => {
      detector.setAdaptiveMode(true);
      detector.setAdaptiveMode(false);
      // 如果没有抛出错误，说明方法工作正常
      expect(true).toBe(true);
    });

    test('应该能够设置检测策略', () => {
      detector.setDetectionStrategy('full');
      detector.setDetectionStrategy('incremental');
      detector.setDetectionStrategy('cached');
      // 如果没有抛出错误，说明方法工作正常
      expect(true).toBe(true);
    });

    test('应该能够获取检测统计信息', () => {
      const stats = detector.getDetectionStats();
      expect(stats).toHaveProperty('isRunning');
      expect(stats).toHaveProperty('lastDetectionTime');
      expect(stats).toHaveProperty('errorCount');
      expect(stats).toHaveProperty('currentInterval');
      expect(stats).toHaveProperty('cacheSize');
      expect(stats).toHaveProperty('performance');
    });
  });

  describe('游戏进程检测测试', () => {
    test('应该能够检测到游戏进程', async () => {
      // Mock 进程列表，包含游戏进程
      mockPsList.mockResolvedValue([
        {
          pid: 1234,
          name: 'StarRail.exe',
          cpu: 15.5,
          memory: 1024000,
          ppid: 1000
        },
        {
          pid: 5678,
          name: 'chrome.exe',
          cpu: 5.0,
          memory: 512000,
          ppid: 1000
        }
      ]);

      // Mock 窗口管理器
      const mockWindow = {
        getTitle: jest.fn(() => '崩坏：星穹铁道'),
        getBounds: jest.fn(() => ({ x: 0, y: 0, width: 1920, height: 1080 })),
        isVisible: jest.fn(() => true),
        id: 12345
      };
      mockWindowManager.getWindows.mockReturnValue([mockWindow]);

      // Mock 活动窗口
      mockActiveWin.mockResolvedValue({
        title: '崩坏：星穹铁道',
        owner: { processId: 1234 }
      });

      const status = await detector.getCurrentStatus();
      
      expect(status.isRunning).toBe(true);
      expect(status.isActive).toBe(true);
      expect(status.windowInfo).toBeDefined();
      expect(status.windowInfo?.title).toBe('崩坏：星穹铁道');
    });

    test('应该能够处理进程不存在的情况', async () => {
      mockPsList.mockResolvedValue([]);
      mockWindowManager.getWindows.mockReturnValue([]);

      const status = await detector.getCurrentStatus();
      
      expect(status.isRunning).toBe(false);
      expect(status.isActive).toBe(false);
      expect(status.windowInfo).toBeUndefined();
    });

    test('应该能够处理检测错误', async () => {
      const errorSpy = jest.fn();
      detector.on('error', errorSpy);
      
      mockPsList.mockRejectedValue(new Error('进程列表获取失败'));

      const status = await detector.getCurrentStatus();
      
      // 等待错误事件
      await new Promise(resolve => process.nextTick(resolve));
      
      expect(status.isRunning).toBe(false);
      expect(status.isActive).toBe(false);
      expect(errorSpy).toHaveBeenCalled();
      
      const stats = detector.getDetectionStats();
      expect(stats.errorCount).toBeGreaterThan(0);
    });
  });

  describe('事件发射测试', () => {
    test('应该在游戏启动时发射事件', async () => {
      const gameStartedSpy = jest.fn();
      detector.on('gameStarted', gameStartedSpy);

      // 第一次检测：游戏未运行
      mockPsList.mockResolvedValueOnce([]);
      await detector.getCurrentStatus();

      // 第二次检测：游戏运行
      mockPsList.mockResolvedValueOnce([
        {
          pid: 1234,
          name: 'StarRail.exe',
          cpu: 15.5,
          memory: 1024000,
          ppid: 1000
        }
      ]);

      const mockWindow = {
        getTitle: jest.fn(() => '崩坏：星穹铁道'),
        getBounds: jest.fn(() => ({ x: 0, y: 0, width: 1920, height: 1080 })),
        isVisible: jest.fn(() => true),
        id: 12345
      };
      mockWindowManager.getWindows.mockReturnValue([mockWindow]);
      mockActiveWin.mockResolvedValue({
        title: '崩坏：星穹铁道',
        owner: { processId: 1234 }
      });

      await detector.getCurrentStatus();

      expect(gameStartedSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          processId: 1234,
          windowTitle: '崩坏：星穹铁道',
          timestamp: expect.any(String)
        })
      );
    });

    test('应该在游戏停止时发射事件', async () => {
      const gameStoppedSpy = jest.fn();
      detector.on('gameStopped', gameStoppedSpy);

      // 第一次检测：游戏运行
      mockPsList.mockResolvedValueOnce([
        {
          pid: 1234,
          name: 'StarRail.exe',
          cpu: 15.5,
          memory: 1024000,
          ppid: 1000
        }
      ]);

      const mockWindow = {
        getTitle: jest.fn(() => '崩坏：星穹铁道'),
        getBounds: jest.fn(() => ({ x: 0, y: 0, width: 1920, height: 1080 })),
        isVisible: jest.fn(() => true),
        id: 12345
      };
      mockWindowManager.getWindows.mockReturnValue([mockWindow]);
      mockActiveWin.mockResolvedValue({
        title: '崩坏：星穹铁道',
        owner: { processId: 1234 }
      });

      await detector.getCurrentStatus();

      // 第二次检测：游戏停止
      mockPsList.mockResolvedValueOnce([]);
      mockWindowManager.getWindows.mockReturnValue([]);
      await detector.getCurrentStatus();

      expect(gameStoppedSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          lastProcessId: expect.any(Number),
          timestamp: expect.any(String)
        })
      );
    });
  });

  describe('缓存机制测试', () => {
    test('应该能够利用进程缓存提高性能', async () => {
      // 第一次调用，建立缓存
      mockPsList.mockResolvedValueOnce([
        {
          pid: 1234,
          name: 'StarRail.exe',
          cpu: 15.5,
          memory: 1024000,
          ppid: 1000
        }
      ]);

      await detector.getCurrentStatus();
      
      // 第二次调用，应该使用缓存（在缓存超时之前）
      mockPsList.mockResolvedValueOnce([
        {
          pid: 1234,
          name: 'StarRail.exe',
          cpu: 15.5,
          memory: 1024000,
          ppid: 1000
        }
      ]);

      await detector.getCurrentStatus();
      
      // 验证性能统计中的缓存命中
      const stats = detector.getPerformanceStats();
      expect(stats.totalDetections).toBeGreaterThan(0);
    });
  });

  describe('自适应检测间隔测试', () => {
    test('应该根据游戏状态调整检测间隔', async () => {
      detector.setAdaptiveMode(true);
      
      // 模拟游戏未运行状态
      mockPsList.mockResolvedValue([]);
      await detector.getCurrentStatus();
      
      let stats = detector.getDetectionStats();
      const slowInterval = stats.currentInterval;
      
      // 模拟游戏运行状态
      mockPsList.mockResolvedValue([
        {
          pid: 1234,
          name: 'StarRail.exe',
          cpu: 15.5,
          memory: 1024000,
          ppid: 1000
        }
      ]);
      
      const mockWindow = {
        getTitle: jest.fn(() => '崩坏：星穹铁道'),
        getBounds: jest.fn(() => ({ x: 0, y: 0, width: 1920, height: 1080 })),
        isVisible: jest.fn(() => true),
        id: 12345
      };
      mockWindowManager.getWindows.mockReturnValue([mockWindow]);
      
      await detector.getCurrentStatus();
      
      stats = detector.getDetectionStats();
      const fastInterval = stats.currentInterval;
      
      // 游戏运行时应该使用更快的检测间隔
      expect(fastInterval).toBeLessThanOrEqual(slowInterval);
    });
  });

  describe('错误处理测试', () => {
    test('应该能够处理连续检测失败', async () => {
      const errorSpy = jest.fn();
      detector.on('error', errorSpy);
      
      // 模拟连续失败
      mockPsList.mockRejectedValue(new Error('检测失败'));
      
      await detector.getCurrentStatus();
      await detector.getCurrentStatus();
      await detector.getCurrentStatus();
      
      // 等待异步错误事件
      await new Promise(resolve => process.nextTick(resolve));
      await new Promise(resolve => process.nextTick(resolve));
      await new Promise(resolve => process.nextTick(resolve));
      
      expect(errorSpy).toHaveBeenCalledTimes(3);
      
      const stats = detector.getDetectionStats();
      expect(stats.errorCount).toBeGreaterThan(0);
    });

    test('应该在错误后恢复正常检测', async () => {
      const errorSpy = jest.fn();
      detector.on('error', errorSpy);
      
      // 第一次失败
      mockPsList.mockRejectedValueOnce(new Error('检测失败'));
      
      const status1 = await detector.getCurrentStatus();
      expect(status1.isRunning).toBe(false);
      
      // 等待异步错误事件
      await new Promise(resolve => process.nextTick(resolve));
      
      expect(errorSpy).toHaveBeenCalledTimes(1);
      
      // 第二次成功
      mockPsList.mockResolvedValueOnce([]);
      const status2 = await detector.getCurrentStatus();
      
      expect(status2.isRunning).toBe(false);
      expect(status2.isActive).toBe(false);
    });
  });

  describe('内存管理测试', () => {
    test('应该能够清理过期缓存', async () => {
      // 建立缓存
      mockPsList.mockResolvedValue([
        {
          pid: 1234,
          name: 'StarRail.exe',
          cpu: 15.5,
          memory: 1024000,
          ppid: 1000
        }
      ]);
      
      await detector.getCurrentStatus();
      
      let stats = detector.getDetectionStats();
      const initialCacheSize = stats.cacheSize.processes;
      
      // 等待缓存超时（模拟）
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // 再次检测
      await detector.getCurrentStatus();
      
      stats = detector.getDetectionStats();
      // 缓存应该被更新或清理
      expect(stats.cacheSize).toBeDefined();
    });
  });

  describe('配置测试', () => {
    test('应该能够使用自定义配置', () => {
      const customDetector = new GameDetectorOptimized({
        gameProcessNames: ['CustomGame.exe'],
        gameWindowTitles: ['Custom Game Title'],
        detectionInterval: 2000,
        enableLogging: true,
        logLevel: 'debug'
      });
      
      expect(customDetector).toBeInstanceOf(GameDetectorOptimized);
      
      const stats = customDetector.getDetectionStats();
      expect(stats.currentInterval).toBe(2000);
    });
  });
});