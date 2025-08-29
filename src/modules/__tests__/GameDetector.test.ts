import { GameDetector } from '../GameDetector';
import { windowManager } from 'node-window-manager';

// Mock the dependencies
jest.mock('node-window-manager');
jest.mock('active-win', () => jest.fn());
jest.mock('ps-list', () => jest.fn());

const mockWindowManager = windowManager as jest.Mocked<typeof windowManager>;
const mockActiveWin = require('active-win') as jest.MockedFunction<() => Promise<any>>;
const mockPsList = require('ps-list') as jest.MockedFunction<() => Promise<any[]>>;

describe('GameDetector', () => {
  let gameDetector: GameDetector;

  beforeEach(() => {
    gameDetector = new GameDetector();
    jest.clearAllMocks();
  });

  afterEach(() => {
    gameDetector.stopDetection();
  });

  describe('constructor', () => {
    it('should initialize with default configuration', () => {
      const detector = new GameDetector();
      const config = detector.getConfig();
      
      expect(config.gameProcessNames).toEqual([
        'StarRail.exe', 
        'HonkaiStarRail.exe', 
        '崩坏星穹铁道.exe',
        'starrail.exe',
        'honkai_star_rail.exe'
      ]);
      expect(config.gameWindowTitles).toEqual([
        '崩坏：星穹铁道', 
        'Honkai: Star Rail', 
        'StarRail',
        'Honkai Star Rail',
        '崩坏星穹铁道'
      ]);
      expect(config.detectionInterval).toBe(1000);
      expect(config.enableLogging).toBe(true);
      expect(config.logLevel).toBe('info');
    });
  });

  // detectGameProcess is private, tested through getCurrentStatus

  // getGameWindow is private, tested through getCurrentStatus

  // isGameWindowActive is private, tested through getCurrentStatus

  describe('getCurrentStatus', () => {
    it('should detect running game with window info', async () => {
      const mockProcess = {
        name: 'StarRail.exe',
        pid: 1234,
        ppid: 5678,
        cpu: 10.5,
        memory: 1024000
      };

      const mockWindow = {
         getTitle: jest.fn(() => '崩坏：星穹铁道'),
         getBounds: jest.fn(() => ({ x: 0, y: 0, width: 1920, height: 1080 })),
         isVisible: jest.fn(() => true)
       } as any;

      mockPsList.mockResolvedValue([mockProcess]);
      mockWindowManager.getWindows.mockReturnValue([mockWindow]);
      mockActiveWin.mockResolvedValue({
        title: '崩坏：星穹铁道',
        id: 123,
        bounds: { x: 0, y: 0, width: 1920, height: 1080 },
        owner: { name: 'StarRail.exe', processId: 1234, bundleId: '', path: '' },
        memoryUsage: 1024000
      });

      const result = await gameDetector.getCurrentStatus();
      
      expect(result.isRunning).toBe(true);
      expect(result.windowInfo).toEqual({
        title: '崩坏：星穹铁道',
        width: 1920,
        height: 1080,
        x: 0,
        y: 0
      });
      expect(result.currentScene).toBe('unknown');
    });

    it('should detect game not running', async () => {
      mockPsList.mockResolvedValue([]);

      const result = await gameDetector.getCurrentStatus();
      
      expect(result.isRunning).toBe(false);
    });
  });

  describe('startDetection and stopDetection', () => {
    it('should start and stop detection', () => {
      expect(gameDetector.isDetectionRunning()).toBe(false);
      
      gameDetector.startDetection();
      expect(gameDetector.isDetectionRunning()).toBe(true);
      
      gameDetector.stopDetection();
      expect(gameDetector.isDetectionRunning()).toBe(false);
    });

    it('should not start detection multiple times', () => {
      gameDetector.startDetection();
      const firstInterval = (gameDetector as any).detectionInterval;
      
      gameDetector.startDetection();
      const secondInterval = (gameDetector as any).detectionInterval;
      
      expect(firstInterval).toBe(secondInterval);
      
      gameDetector.stopDetection();
    });
  });

  describe('configuration management', () => {
    it('should update configuration', () => {
      const newConfig = {
        gameProcessNames: ['NewGame.exe'],
        gameWindowTitles: ['New Game Title'],
        detectionInterval: 5000
      };

      gameDetector.updateConfig(newConfig);
      const config = gameDetector.getConfig();
      
      expect(config.gameProcessNames).toEqual(['NewGame.exe']);
      expect(config.gameWindowTitles).toEqual(['New Game Title']);
      expect(config.detectionInterval).toBe(5000);
    });
  });

  describe('waitForGameStart', () => {
    it('should resolve when game starts', async () => {
      const mockProcess = {
        name: 'StarRail.exe',
        pid: 1234,
        ppid: 5678,
        cpu: 10.5,
        memory: 1024000
      };

      // First call returns empty, second call returns process
      mockPsList
        .mockResolvedValueOnce([])
        .mockResolvedValueOnce([mockProcess]);

      const startTime = Date.now();
      await gameDetector.waitForGameStart(5000);
      const endTime = Date.now();

      expect(endTime - startTime).toBeLessThan(5000);
      expect(mockPsList).toHaveBeenCalledTimes(2);
    });

    it('should timeout when game does not start', async () => {
      mockPsList.mockResolvedValue([]);

      const startTime = Date.now();
      const result = await gameDetector.waitForGameStart(1000);
      const endTime = Date.now();

      expect(result).toBe(false);
      expect(endTime - startTime).toBeGreaterThanOrEqual(1000);
    });
  });
});