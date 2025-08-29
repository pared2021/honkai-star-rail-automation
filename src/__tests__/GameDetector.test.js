import { GameDetector } from '../modules/GameDetector';
import { windowManager } from 'node-window-manager';
import activeWin from 'active-win';
import psList from 'ps-list';
// Mock modules
jest.mock('node-window-manager');
jest.mock('active-win', () => jest.fn());
jest.mock('ps-list', () => jest.fn());
const mockWindowManager = windowManager;
const mockActiveWin = activeWin;
const mockPsList = psList;
describe('GameDetector', () => {
    let gameDetector;
    let mockLogger;
    beforeEach(() => {
        // Reset all mocks
        jest.clearAllMocks();
        // Create mock logger
        mockLogger = jest.fn();
        // Create GameDetector instance
        gameDetector = new GameDetector({
            gameProcessNames: ['StarRail.exe', 'YuanShen.exe'],
            gameWindowTitles: ['崩坏：星穹铁道', 'Honkai: Star Rail'],
            detectionInterval: 1000,
            enableLogging: true
        });
        // Replace logger with mock
        gameDetector.log = mockLogger;
    });
    afterEach(() => {
        gameDetector.stopDetection();
    });
    describe('Configuration', () => {
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
        it('should update configuration', () => {
            const newConfig = {
                gameProcessNames: ['NewGame.exe'],
                gameWindowTitles: ['New Game'],
                detectionInterval: 2000,
                enableLogging: false,
                logLevel: 'info'
            };
            gameDetector.updateConfig(newConfig);
            const config = gameDetector.getConfig();
            expect(config).toEqual(newConfig);
        });
    });
    describe('Process Detection', () => {
        it('should detect game process when running', async () => {
            const mockProcesses = [
                { name: 'StarRail.exe', pid: 1234, ppid: 1000, cmd: 'StarRail.exe' },
                { name: 'chrome.exe', pid: 5678, ppid: 1000, cmd: 'chrome.exe' }
            ];
            mockPsList.mockResolvedValue(mockProcesses);
            const processInfo = await gameDetector.detectGameProcess();
            expect(processInfo).toEqual({
                name: 'StarRail.exe',
                pid: 1234,
                ppid: 1000,
                cpu: undefined,
                memory: undefined
            });
            // detectGameProcess方法不直接记录日志，日志在detectGameStatus中记录
        });
        it('should return null when no game process found', async () => {
            const mockProcesses = [
                { name: 'chrome.exe', pid: 5678, ppid: 1000, cmd: 'chrome.exe' },
                { name: 'notepad.exe', pid: 9012, ppid: 1000, cmd: 'notepad.exe' }
            ];
            mockPsList.mockResolvedValue(mockProcesses);
            const processInfo = await gameDetector.detectGameProcess();
            expect(processInfo).toBeNull();
            expect(mockLogger).toHaveBeenCalledWith('debug', '未找到游戏进程');
        });
        it('should handle process detection errors', async () => {
            const error = new Error('Process list failed');
            mockPsList.mockRejectedValue(error);
            await expect(gameDetector.detectGameProcess()).rejects.toThrow('Process list failed');
            expect(mockLogger).toHaveBeenCalledWith('error', '检测游戏进程失败', error);
        });
    });
    describe('Window Detection', () => {
        it('should detect game window when available', async () => {
            const mockWindows = [
                {
                    id: 123456,
                    getTitle: () => '崩坏：星穹铁道',
                    getBounds: () => ({ x: 100, y: 100, width: 1920, height: 1080 }),
                    isVisible: () => true,
                    isMinimized: () => false,
                    processId: 1234
                },
                {
                    id: 789012,
                    getTitle: () => 'Chrome',
                    getBounds: () => ({ x: 200, y: 200, width: 800, height: 600 }),
                    isVisible: () => true,
                    isMinimized: () => false,
                    processId: 5678
                }
            ];
            mockWindowManager.getWindows.mockReturnValue(mockWindows);
            const windowInfo = await gameDetector.getGameWindow();
            expect(windowInfo).toEqual({
                id: 123456,
                processId: 1234,
                getTitle: expect.any(Function),
                getBounds: expect.any(Function),
                isVisible: expect.any(Function),
                isMinimized: expect.any(Function)
            });
            // getGameWindow方法不记录找到窗口的日志，只记录未找到的情况
        });
        it('should return null when no game window found', async () => {
            const mockWindows = [
                {
                    id: 789012,
                    getTitle: () => 'Chrome',
                    getBounds: () => ({ x: 200, y: 200, width: 800, height: 600 }),
                    isVisible: () => true,
                    isMinimized: () => false,
                    processId: 5678
                }
            ];
            mockWindowManager.getWindows.mockReturnValue(mockWindows);
            const windowInfo = await gameDetector.getGameWindow();
            expect(windowInfo).toBeNull();
            expect(mockLogger).toHaveBeenCalledWith('debug', '未找到游戏窗口');
        });
        it('should handle window detection errors', async () => {
            const error = new Error('Window manager failed');
            mockWindowManager.getWindows.mockImplementation(() => {
                throw error;
            });
            const windowInfo = await gameDetector.getGameWindow();
            expect(windowInfo).toBeNull();
            expect(mockLogger).toHaveBeenCalledWith('error', '获取游戏窗口失败', error);
        });
    });
    describe('Active Window Detection', () => {
        it('should detect when game window is active', async () => {
            mockActiveWin.mockResolvedValue({
                title: '崩坏：星穹铁道',
                id: 123456,
                bounds: { x: 100, y: 100, width: 1920, height: 1080 },
                owner: { name: 'StarRail.exe', processId: 1234, path: '' },
                memoryUsage: 0,
                platform: 'windows'
            });
            const isActive = await gameDetector.isGameWindowActive();
            expect(isActive).toBe(true);
            expect(mockLogger).toHaveBeenCalledWith('debug', '活动窗口检测结果: true', { title: '崩坏：星穹铁道' });
        });
        it('should return false when non-game window is active', async () => {
            mockActiveWin.mockResolvedValue({
                title: 'Chrome',
                id: 789012,
                bounds: { x: 200, y: 200, width: 800, height: 600 },
                owner: { name: 'chrome.exe', processId: 5678, path: '' },
                memoryUsage: 0,
                platform: 'windows'
            });
            const isActive = await gameDetector.isGameWindowActive();
            expect(isActive).toBe(false);
            expect(mockLogger).toHaveBeenCalledWith('debug', '活动窗口检测结果: false', { title: 'Chrome' });
        });
        it('should return false when no active window', async () => {
            mockActiveWin.mockResolvedValue(undefined);
            const isActive = await gameDetector.isGameWindowActive();
            expect(isActive).toBe(false);
            expect(mockLogger).toHaveBeenCalledWith('debug', '未检测到活动窗口');
        });
        it('should handle active window detection errors', async () => {
            const error = new Error('Active window detection failed');
            mockActiveWin.mockRejectedValue(error);
            const isActive = await gameDetector.isGameWindowActive();
            expect(isActive).toBe(false);
            expect(mockLogger).toHaveBeenCalledWith('error', '检测活动窗口失败', error);
        });
    });
    describe('Game Status Detection', () => {
        it('should detect game as running when process and window exist', async () => {
            // Mock process detection
            const mockProcesses = [
                { name: 'StarRail.exe', pid: 1234, ppid: 1000, cpu: 0, memory: 0 }
            ];
            mockPsList.mockResolvedValue(mockProcesses);
            // Mock window detection
            const mockWindows = [
                {
                    id: 123456,
                    getTitle: () => '崩坏：星穹铁道',
                    getBounds: () => ({ x: 100, y: 100, width: 1920, height: 1080 }),
                    isVisible: () => true,
                    isMinimized: () => false,
                    processId: 1234
                }
            ];
            mockWindowManager.getWindows.mockReturnValue(mockWindows);
            // Mock active window
            mockActiveWin.mockResolvedValue({
                title: '崩坏：星穹铁道',
                id: 123456,
                bounds: { x: 100, y: 100, width: 1920, height: 1080 },
                owner: { name: 'StarRail.exe', processId: 1234, path: '' },
                memoryUsage: 0,
                platform: 'windows'
            });
            await gameDetector.detectGameStatus();
            const status = await gameDetector.getCurrentStatus();
            expect(status.isRunning).toBe(true);
            expect(status.isActive).toBe(true);
            // processInfo is not part of GameStatus interface, it's internal to GameDetector
            // We can verify the game is detected as running instead
            expect(status.isRunning).toBe(true);
            expect(status.windowInfo).toEqual({
                title: '崩坏：星穹铁道',
                width: 1920,
                height: 1080,
                x: 100,
                y: 100
            });
        });
        it('should detect game as not running when no process found', async () => {
            mockPsList.mockResolvedValue([]);
            mockWindowManager.getWindows.mockReturnValue([]);
            mockActiveWin.mockResolvedValue(undefined);
            await gameDetector.detectGameStatus();
            const status = await gameDetector.getCurrentStatus();
            expect(status.isRunning).toBe(false);
            expect(status.isActive).toBe(false);
            expect(status.isRunning).toBe(false);
            expect(status.windowInfo).toBeUndefined();
        });
    });
    describe('Event Emission', () => {
        it('should emit gameStarted event when game starts', (done) => {
            gameDetector.on('gameStarted', (gameStatus) => {
                expect(gameStatus.isRunning).toBe(true);
                expect(gameStatus.isActive).toBe(false);
                done();
            });
            // Simulate game start
            const mockProcesses = [
                { name: 'StarRail.exe', pid: 1234, ppid: 1000, cpu: 0, memory: 0 }
            ];
            mockPsList.mockResolvedValue(mockProcesses);
            mockWindowManager.getWindows.mockReturnValue([]);
            mockActiveWin.mockResolvedValue(undefined);
            gameDetector.detectGameStatus();
        });
        it('should emit gameStopped event when game stops', (done) => {
            // First simulate game running
            const mockProcesses = [
                { name: 'StarRail.exe', pid: 1234, ppid: 1000, cpu: 0, memory: 0 }
            ];
            mockPsList.mockResolvedValue(mockProcesses);
            mockWindowManager.getWindows.mockReturnValue([]);
            mockActiveWin.mockResolvedValue(undefined);
            // First detection to set game as running
            gameDetector.detectGameStatus().then(() => {
                gameDetector.on('gameStopped', () => {
                    done();
                });
                // Now simulate game stop
                mockPsList.mockResolvedValue([]);
                mockWindowManager.getWindows.mockReturnValue([]);
                mockActiveWin.mockResolvedValue(undefined);
                return gameDetector.detectGameStatus();
            }).catch(done);
        });
    });
    describe('Wait for Game Start', () => {
        it('should resolve when game starts within timeout', async () => {
            // Mock game detection to succeed on second call
            let callCount = 0;
            mockPsList.mockImplementation(() => {
                callCount++;
                if (callCount >= 2) {
                    return Promise.resolve([
                        { name: 'StarRail.exe', pid: 1234, ppid: 1000, cpu: 0, memory: 0 }
                    ]);
                }
                return Promise.resolve([]);
            });
            mockWindowManager.getWindows.mockReturnValue([]);
            const result = await gameDetector.waitForGameStart(5000);
            expect(result).toBe(true);
            expect(mockLogger).toHaveBeenCalledWith('info', '游戏启动检测成功，尝试次数:', expect.any(Number));
        });
        it('should reject when timeout is reached', async () => {
            mockPsList.mockResolvedValue([]);
            mockWindowManager.getWindows.mockReturnValue([]);
            const result = await gameDetector.waitForGameStart(1000);
            expect(result).toBe(false);
            expect(mockLogger).toHaveBeenCalledWith('warn', '等待游戏启动超时');
        });
    });
    describe('Error Handling', () => {
        it('should track detection errors', async () => {
            const error = new Error('Detection failed');
            mockPsList.mockRejectedValue(error);
            try {
                await gameDetector.detectGameStatus();
            }
            catch (e) {
                // 错误被正确抛出
            }
            const errors = gameDetector.getDetectionErrors();
            expect(errors).toHaveLength(1);
            expect(errors[0]).toContain('Detection failed');
        });
        it('should clear detection errors', async () => {
            const error = new Error('Detection failed');
            mockPsList.mockRejectedValue(error);
            try {
                await gameDetector.detectGameStatus();
            }
            catch (e) {
                // 错误被正确抛出
            }
            expect(gameDetector.getDetectionErrors()).toHaveLength(1);
            gameDetector.clearDetectionErrors();
            expect(gameDetector.getDetectionErrors()).toHaveLength(0);
        });
    });
    describe('Detection Statistics', () => {
        it('should track detection statistics', async () => {
            mockPsList.mockResolvedValue([]);
            mockWindowManager.getWindows.mockReturnValue([]);
            mockActiveWin.mockResolvedValue(undefined);
            await gameDetector.detectGameStatus();
            await gameDetector.detectGameStatus();
            const stats = gameDetector.getDetectionStats();
            expect(stats.isRunning).toBe(false);
            expect(stats.errorCount).toBe(0);
            expect(stats.currentProcess).toBeNull();
            expect(stats.currentWindow).toBeNull();
            expect(stats.lastDetectionTime).toBeInstanceOf(Date);
        });
    });
});
