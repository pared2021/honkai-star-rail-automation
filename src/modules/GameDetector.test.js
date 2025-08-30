import { GameDetector } from './GameDetector';
import { EventEmitter } from 'events';
// Mock dependencies
jest.mock('node-window-manager', () => ({
    windowManager: {
        getWindows: jest.fn(),
        getActiveWindow: jest.fn()
    }
}));
jest.mock('active-win', () => jest.fn());
jest.mock('ps-list', () => jest.fn());
describe('GameDetector', () => {
    let gameDetector;
    let mockWindowManager;
    let mockActiveWin;
    let mockPsList;
    beforeEach(() => {
        // Reset mocks
        jest.clearAllMocks();
        // Setup mocks
        mockWindowManager = require('node-window-manager').windowManager;
        mockActiveWin = require('active-win');
        mockPsList = require('ps-list');
        // Create new instance
        gameDetector = new GameDetector({
            gameProcessNames: ['StarRail.exe', 'HonkaiStarRail.exe'],
            gameWindowTitles: ['崩坏：星穹铁道', 'Honkai: Star Rail'],
            detectionInterval: 1000
        });
    });
    afterEach(async () => {
        gameDetector.stopDetection();
        gameDetector.disableRealTimeMonitoring();
    });
    describe('Configuration', () => {
        test('should initialize with default config', () => {
            const detector = new GameDetector();
            expect(detector).toBeInstanceOf(EventEmitter);
        });
        test('should initialize with custom config', () => {
            const config = {
                gameProcessNames: ['test.exe'],
                gameWindowTitles: ['Test Game'],
                detectionInterval: 2000
            };
            const detector = new GameDetector(config);
            expect(detector).toBeInstanceOf(EventEmitter);
        });
        test('should update configuration', () => {
            const newConfig = {
                gameProcessNames: ['newgame.exe'],
                detectionInterval: 3000
            };
            gameDetector.updateConfig(newConfig);
            expect(gameDetector.getConfig().detectionInterval).toBe(3000);
        });
    });
    describe('Process Detection', () => {
        test('should detect game status when running', async () => {
            const mockProcess = {
                pid: 1234,
                name: 'StarRail.exe',
                cpu: 10.5,
                memory: 1024000
            };
            mockPsList.mockResolvedValue([mockProcess]);
            const result = await gameDetector.getCurrentStatus();
            expect(result).toBeTruthy();
            expect(result.isRunning).toBe(true);
        });
        test('should return not running when no game process found', async () => {
            mockPsList.mockResolvedValue([]);
            const result = await gameDetector.getCurrentStatus();
            expect(result.isRunning).toBe(false);
        });
        test('should handle process detection errors', async () => {
            mockPsList.mockRejectedValue(new Error('Process list error'));
            const result = await gameDetector.getCurrentStatus();
            expect(result.isRunning).toBe(false);
        });
    });
    describe('Window Detection', () => {
        test('should detect game window when available', async () => {
            const mockWindow = {
                id: 12345,
                getTitle: () => '崩坏：星穹铁道',
                getBounds: () => ({ x: 100, y: 100, width: 1920, height: 1080 }),
                isVisible: () => true
            };
            mockWindowManager.getWindows.mockReturnValue([mockWindow]);
            const result = await gameDetector.getCurrentStatus();
            expect(result).toBeTruthy();
            expect(result.windowInfo).toBeTruthy();
            expect(result.windowInfo?.title).toBe('崩坏：星穹铁道');
        });
        test('should return null window info when no game window found', async () => {
            mockWindowManager.getWindows.mockReturnValue([]);
            const result = await gameDetector.getCurrentStatus();
            expect(result.windowInfo).toBeNull();
        });
        test('should handle window detection errors gracefully', async () => {
            mockWindowManager.getWindows.mockImplementation(() => {
                throw new Error('Window manager error');
            });
            const result = await gameDetector.getCurrentStatus();
            expect(result.windowInfo).toBeNull();
        });
    });
    describe('Window Handle and Position', () => {
        test('should get window handle', async () => {
            const mockWindow = {
                id: 12345,
                handle: 'HWND_12345',
                getTitle: () => '崩坏：星穹铁道',
                getBounds: () => ({ x: 100, y: 100, width: 1920, height: 1080 }),
                isVisible: () => true
            };
            mockWindowManager.getWindows.mockReturnValue([mockWindow]);
            const handle = await gameDetector.getGameWindowHandle();
            expect(handle).toBe('HWND_12345');
        });
        test('should get window position info', async () => {
            const mockWindow = {
                id: 12345,
                handle: 'HWND_12345',
                getTitle: () => '崩坏：星穹铁道',
                getBounds: () => ({ x: 100, y: 100, width: 1920, height: 1080 }),
                isVisible: () => true
            };
            mockWindowManager.getWindows.mockReturnValue([mockWindow]);
            mockActiveWin.mockResolvedValue({
                title: '崩坏：星穹铁道',
                owner: { processId: 1234 }
            });
            const position = await gameDetector.getGameWindowPosition();
            expect(position).toEqual({
                handle: 'HWND_12345',
                bounds: { x: 100, y: 100, width: 1920, height: 1080 },
                isVisible: true,
                isActive: true
            });
        });
        test('should check if window is in region', async () => {
            const mockWindow = {
                id: 12345,
                getTitle: () => '崩坏：星穹铁道',
                getBounds: () => ({ x: 100, y: 100, width: 800, height: 600 }),
                isVisible: () => true
            };
            mockWindowManager.getWindows.mockReturnValue([mockWindow]);
            const region = { x: 50, y: 50, width: 200, height: 200 };
            const isInRegion = await gameDetector.isGameWindowInRegion(region);
            expect(isInRegion).toBe(true);
        });
    });
    describe('Real-time Monitoring', () => {
        test('should enable real-time monitoring', () => {
            gameDetector.startDetection();
            gameDetector.enableRealTimeMonitoring(1000);
            gameDetector.stopDetection();
            gameDetector.disableRealTimeMonitoring();
            expect(gameDetector.isRealTimeMonitoringEnabled()).toBe(false);
        });
        test('should disable real-time monitoring', () => {
            gameDetector.enableRealTimeMonitoring(500);
            gameDetector.disableRealTimeMonitoring();
            expect(gameDetector.isRealTimeMonitoringEnabled()).toBe(false);
        });
        test('should handle state change callbacks', () => {
            const callback = jest.fn();
            gameDetector.onStateChange(callback);
            // Simulate state change
            gameDetector.startDetection();
            gameDetector.stopDetection();
            expect(callback).toBeDefined();
        });
        test('should remove state change callbacks', () => {
            const callback = jest.fn();
            gameDetector.onStateChange(callback);
            gameDetector.removeStateChangeCallback(callback);
            // Simulate state change
            gameDetector['notifyStateChange']('gameStarted', { isRunning: true });
            expect(callback).not.toHaveBeenCalled();
        });
    });
    describe('Status and Control', () => {
        test('should start and stop detection', async () => {
            gameDetector.startDetection();
            expect(gameDetector.isDetectionRunning()).toBe(true);
            gameDetector.stopDetection();
            expect(gameDetector.isDetectionRunning()).toBe(false);
        });
        test('should get current game state', () => {
            const state = gameDetector.getCurrentGameState();
            expect(state).toEqual({
                isRunning: false,
                isActive: false,
                windowPosition: null,
                processInfo: null
            });
        });
        test('should reset detector state', () => {
            gameDetector.reset();
            expect(gameDetector.getCurrentProcessInfo()).toBeNull();
            expect(gameDetector.getCurrentWindowInfo()).toBeNull();
        });
        test('should clear detection errors', () => {
            gameDetector.clearDetectionErrors();
            expect(gameDetector.getDetectionErrors()).toEqual([]);
        });
    });
    describe('Game Status Checks', () => {
        test('should check if game is running', () => {
            expect(gameDetector.isGameRunning()).toBe(false);
        });
        test('should check if game is active', () => {
            expect(gameDetector.isGameActive()).toBe(false);
        });
        test('should wait for game start with timeout', async () => {
            const mockProcess = {
                pid: 1234,
                name: 'StarRail.exe',
                cpu: 0,
                memory: 0
            };
            // Mock process detection after a delay
            setTimeout(() => {
                mockPsList.mockResolvedValue([mockProcess]);
            }, 100);
            const result = await gameDetector.waitForGameStart(200);
            expect(result).toBe(false); // Should timeout before process is found
        });
    });
});
