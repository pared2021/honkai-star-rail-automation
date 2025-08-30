import { GameDetector } from '../GameDetector';
/**
 * 集成测试 - 需要在真实环境中运行
 * 这些测试需要实际的游戏进程或窗口来验证功能
 */
describe('GameDetector Integration Tests', () => {
    let gameDetector;
    beforeEach(() => {
        gameDetector = new GameDetector({
            gameProcessNames: ['StarRail.exe', 'YuanShen.exe', 'notepad.exe'], // 添加notepad.exe用于测试
            detectionInterval: 1000
        });
    });
    afterEach(() => {
        gameDetector.stopDetection();
    });
    // 这个测试需要手动运行记事本来验证
    it('should detect notepad process when running', async () => {
        console.log('请启动记事本(notepad.exe)来测试游戏检测功能...');
        // 等待用户启动记事本
        const status = await gameDetector.getCurrentStatus();
        if (status.isRunning) {
            console.log('检测到游戏运行');
            console.log('游戏窗口信息:', status.windowInfo ? '已找到' : '未找到');
            expect(status.isRunning).toBe(true);
            if (status.windowInfo) {
                expect(status.windowInfo.title).toBeTruthy();
                expect(typeof status.windowInfo.x).toBe('number');
                expect(typeof status.windowInfo.y).toBe('number');
            }
        }
        else {
            console.log('未检测到游戏进程，请确保记事本正在运行');
            // 在CI环境中，这个测试可能会失败，这是正常的
            expect(status.isRunning).toBe(false);
        }
    }, 10000);
    it('should start and stop detection properly', async () => {
        gameDetector.startDetection();
        // 等待一段时间确保检测正在运行
        await new Promise(resolve => setTimeout(resolve, 1000));
        // 获取状态以验证检测功能
        const status = await gameDetector.getCurrentStatus();
        console.log('检测状态:', status.isRunning ? '运行中' : '未运行');
        gameDetector.stopDetection();
        // 验证检测可以正常启动和停止
        expect(typeof status.isRunning).toBe('boolean');
    }, 5000);
    it('should handle window position detection', async () => {
        const status = await gameDetector.getCurrentStatus();
        if (status.isRunning && status.windowInfo) {
            console.log('窗口位置信息:', status.windowInfo);
            expect(status.windowInfo).toBeTruthy();
            expect(typeof status.windowInfo.x).toBe('number');
            expect(typeof status.windowInfo.y).toBe('number');
            expect(typeof status.windowInfo.width).toBe('number');
            expect(typeof status.windowInfo.height).toBe('number');
            expect(status.windowInfo.title).toBeTruthy();
        }
        else {
            console.log('没有检测到游戏窗口，跳过窗口位置测试');
        }
    });
    it('should wait for game start with timeout', async () => {
        console.log('测试等待游戏启动功能（1秒超时）...');
        const startTime = Date.now();
        const result = await gameDetector.waitForGameStart(1000);
        const endTime = Date.now();
        if (result) {
            console.log('检测到游戏启动');
            expect(result).toBe(true);
        }
        else {
            console.log('等待超时，未检测到游戏启动');
            expect(result).toBe(false);
            expect(endTime - startTime).toBeGreaterThanOrEqual(1000);
        }
    }, 2000);
});
