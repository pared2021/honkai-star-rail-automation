/**
 * Jest测试环境设置文件
 * 用于配置全局测试环境和模拟
 */
// 模拟Electron相关模块
jest.mock('electron', () => ({
    app: {
        getPath: jest.fn(() => '/mock/path'),
        quit: jest.fn(),
        on: jest.fn()
    },
    BrowserWindow: jest.fn().mockImplementation(() => ({
        loadFile: jest.fn(),
        on: jest.fn(),
        webContents: {
            on: jest.fn()
        }
    })),
    ipcMain: {
        on: jest.fn(),
        handle: jest.fn()
    },
    ipcRenderer: {
        invoke: jest.fn(),
        on: jest.fn()
    }
}));
// 模拟node-window-manager
jest.mock('node-window-manager', () => ({
    windowManager: {
        getWindows: jest.fn(() => []),
        getActiveWindow: jest.fn(() => null)
    }
}));
// 模拟active-win
jest.mock('active-win', () => jest.fn(() => Promise.resolve(null)));
// 模拟ps-list
jest.mock('ps-list', () => jest.fn(() => Promise.resolve([])));
// 模拟sharp图像处理库
jest.mock('sharp', () => {
    const mockSharp = jest.fn(() => ({
        resize: jest.fn().mockReturnThis(),
        png: jest.fn().mockReturnThis(),
        toBuffer: jest.fn(() => Promise.resolve(Buffer.from('mock-image-data')))
    }));
    return mockSharp;
});
// 模拟文件系统操作
jest.mock('fs', () => ({
    ...jest.requireActual('fs'),
    readFileSync: jest.fn(() => Buffer.from('mock-file-data')),
    writeFileSync: jest.fn(),
    existsSync: jest.fn(() => true),
    mkdirSync: jest.fn()
}));
// 模拟路径操作
jest.mock('path', () => ({
    ...jest.requireActual('path'),
    join: jest.fn((...args) => args.join('/')),
    resolve: jest.fn((...args) => '/' + args.join('/'))
}));
// 设置全局超时
jest.setTimeout(30000);
// 全局测试前设置
beforeAll(() => {
    // 禁用console.log以减少测试输出噪音
    jest.spyOn(console, 'log').mockImplementation(() => { });
    jest.spyOn(console, 'info').mockImplementation(() => { });
    jest.spyOn(console, 'debug').mockImplementation(() => { });
    // 保留错误和警告输出
    jest.spyOn(console, 'error').mockImplementation((message) => {
        if (process.env.NODE_ENV === 'test' && process.env.VERBOSE_TESTS) {
            console.error(message);
        }
    });
    jest.spyOn(console, 'warn').mockImplementation((message) => {
        if (process.env.NODE_ENV === 'test' && process.env.VERBOSE_TESTS) {
            console.warn(message);
        }
    });
});
// 全局测试后清理
afterAll(() => {
    // 恢复所有模拟
    jest.restoreAllMocks();
});
// 每个测试前的设置
beforeEach(() => {
    // 清除所有模拟调用记录
    jest.clearAllMocks();
});
// 导出测试工具函数
export const testUtils = {
    /**
     * 创建模拟的游戏窗口信息
     */
    createMockGameWindow: () => ({
        id: 12345,
        title: '崩坏：星穹铁道',
        processId: 67890,
        bounds: {
            x: 100,
            y: 100,
            width: 1920,
            height: 1080
        }
    }),
    /**
     * 创建模拟的图像识别结果
     */
    createMockImageResult: (found = true, confidence = 0.9) => ({
        found,
        location: found ? { x: 500, y: 300 } : null,
        confidence
    }),
    /**
     * 等待指定时间
     */
    delay: (ms) => new Promise(resolve => setTimeout(resolve, ms)),
    /**
     * 等待条件满足
     */
    waitFor: async (condition, timeout = 5000) => {
        const start = Date.now();
        while (!condition() && Date.now() - start < timeout) {
            await testUtils.delay(100);
        }
        return condition();
    }
};
