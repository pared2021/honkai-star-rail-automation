import { FilterDetector } from './FilterDetector.js';
import { exec } from 'child_process';
import { promisify } from 'util';
const execAsync = promisify(exec);
/**
 * 游戏监控服务
 * 负责监控游戏进程状态、窗口信息、检测第三方工具干扰
 */
export class GameMonitor {
    /**
     * 初始化监控器
     */
    constructor() {
        Object.defineProperty(this, "monitorInterval", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: null
        });
        Object.defineProperty(this, "filterMonitorInterval", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: null
        });
        Object.defineProperty(this, "eventListeners", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: new Map()
        });
        Object.defineProperty(this, "lastStatus", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: null
        });
        Object.defineProperty(this, "settings", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: null
        });
        Object.defineProperty(this, "filterDetector", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        // 已知的第三方工具列表
        Object.defineProperty(this, "knownThirdPartyTools", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: [
                {
                    name: '游戏加加',
                    processName: 'GamePP.exe',
                    type: 'overlay',
                    isDetected: false,
                    description: '游戏性能监控和录制工具',
                    riskLevel: 'medium'
                },
                {
                    name: 'MSI Afterburner',
                    processName: 'MSIAfterburner.exe',
                    type: 'overlay',
                    isDetected: false,
                    description: 'GPU监控和超频工具',
                    riskLevel: 'low'
                },
                {
                    name: 'NVIDIA GeForce Experience',
                    processName: 'NVIDIA Share.exe',
                    type: 'overlay',
                    isDetected: false,
                    description: 'NVIDIA游戏录制和优化工具',
                    riskLevel: 'low'
                },
                {
                    name: 'Steam Overlay',
                    processName: 'GameOverlayUI.exe',
                    type: 'overlay',
                    isDetected: false,
                    description: 'Steam游戏内覆盖层',
                    riskLevel: 'low'
                },
                {
                    name: 'Discord Overlay',
                    processName: 'Discord.exe',
                    type: 'overlay',
                    isDetected: false,
                    description: 'Discord游戏内覆盖层',
                    riskLevel: 'low'
                },
                {
                    name: 'OBS Studio',
                    processName: 'obs64.exe',
                    type: 'recorder',
                    isDetected: false,
                    description: '直播和录制软件',
                    riskLevel: 'medium'
                },
                {
                    name: 'Bandicam',
                    processName: 'bdcam.exe',
                    type: 'recorder',
                    isDetected: false,
                    description: '屏幕录制软件',
                    riskLevel: 'medium'
                },
                {
                    name: 'Cheat Engine',
                    processName: 'cheatengine-x86_64.exe',
                    type: 'injection',
                    isDetected: false,
                    description: '内存修改工具',
                    riskLevel: 'high'
                },
                {
                    name: 'Process Hacker',
                    processName: 'ProcessHacker.exe',
                    type: 'injection',
                    isDetected: false,
                    description: '进程管理和调试工具',
                    riskLevel: 'high'
                },
                {
                    name: 'ReShade',
                    processName: 'ReShade.exe',
                    type: 'filter',
                    isDetected: false,
                    description: '游戏画面增强工具',
                    riskLevel: 'medium'
                }
            ]
        });
        this.filterDetector = new FilterDetector();
        this.initializeEventListeners();
    }
    /**
     * 初始化事件监听器
     */
    initializeEventListeners() {
        const eventTypes = [
            'game_started',
            'game_stopped',
            'game_crashed',
            'window_changed',
            'resolution_changed',
            'third_party_detected',
            'interference_detected',
            'game_not_responding'
        ];
        eventTypes.forEach(type => {
            this.eventListeners.set(type, []);
        });
    }
    /**
     * 设置监控配置
     */
    setSettings(settings) {
        this.settings = settings;
    }
    /**
     * 开始监控
     */
    startMonitoring(options) {
        if (this.monitorInterval) {
            this.stopMonitoring();
        }
        const interval = options?.interval || this.settings?.monitorSettings.checkInterval || 5;
        this.monitorInterval = setInterval(() => {
            this.performMonitorCheck();
        }, interval * 1000);
        // 启动滤镜监控（较低频率）
        this.filterMonitorInterval = this.filterDetector.startFilterMonitoring((report) => {
            this.emitEvent('third_party_detected', {
                message: '检测到滤镜工具变化',
                data: report
            });
        }, 30000 // 30秒检查一次
        );
        console.log(`游戏监控已启动，检查间隔: ${interval}秒`);
    }
    /**
     * 停止监控
     */
    stopMonitoring() {
        if (this.monitorInterval) {
            clearInterval(this.monitorInterval);
            this.monitorInterval = null;
            console.log('游戏监控已停止');
        }
        if (this.filterMonitorInterval) {
            this.filterDetector.stopFilterMonitoring(this.filterMonitorInterval);
            this.filterMonitorInterval = null;
        }
    }
    /**
     * 执行监控检查
     */
    async performMonitorCheck() {
        try {
            const status = await this.getGameStatus();
            // 检查状态变化
            this.checkStatusChanges(status);
            // 更新最后状态
            this.lastStatus = status;
        }
        catch (error) {
            console.error('监控检查失败:', error);
        }
    }
    /**
     * 检查状态变化并触发事件
     */
    checkStatusChanges(currentStatus) {
        if (!this.lastStatus)
            return;
        // 检查游戏启动/停止
        if (currentStatus.isGameRunning !== this.lastStatus.isGameRunning) {
            const eventType = currentStatus.isGameRunning ? 'game_started' : 'game_stopped';
            this.emitEvent(eventType, {
                processInfo: currentStatus.gameProcess,
                timestamp: new Date()
            });
        }
        // 检查窗口变化
        if (this.hasWindowChanged(currentStatus.gameWindow, this.lastStatus.gameWindow)) {
            this.emitEvent('window_changed', {
                oldWindow: this.lastStatus.gameWindow,
                newWindow: currentStatus.gameWindow,
                timestamp: new Date()
            });
        }
        // 检查第三方工具
        const newTools = this.getNewlyDetectedTools(currentStatus.thirdPartyTools, this.lastStatus.thirdPartyTools);
        if (newTools.length > 0) {
            newTools.forEach(tool => {
                this.emitEvent('third_party_detected', {
                    tool,
                    timestamp: new Date()
                });
            });
        }
        // 检查干扰
        if (currentStatus.hasInterference && !this.lastStatus.hasInterference) {
            this.emitEvent('interference_detected', {
                tools: currentStatus.thirdPartyTools.filter(t => t.isDetected && t.riskLevel === 'high'),
                timestamp: new Date()
            });
        }
    }
    /**
     * 检查窗口是否发生变化
     */
    hasWindowChanged(current, previous) {
        if (!current && !previous)
            return false;
        if (!current || !previous)
            return true;
        return (current.width !== previous.width ||
            current.height !== previous.height ||
            current.x !== previous.x ||
            current.y !== previous.y ||
            current.isFullscreen !== previous.isFullscreen);
    }
    /**
     * 获取新检测到的第三方工具
     */
    getNewlyDetectedTools(current, previous) {
        return current.filter(currentTool => {
            const previousTool = previous.find(p => p.processName === currentTool.processName);
            return currentTool.isDetected && (!previousTool || !previousTool.isDetected);
        });
    }
    /**
     * 获取当前游戏状态
     */
    async getGameStatus() {
        const gameProcess = await this.getGameProcessInfo();
        const gameWindow = gameProcess ? await this.getGameWindowInfo() : null;
        const thirdPartyTools = await this.detectThirdPartyTools();
        const isGameRunning = gameProcess !== null;
        const isGameResponding = gameProcess ? await this.checkGameResponding(gameProcess.processId) : false;
        const hasInterference = thirdPartyTools.some(tool => tool.isDetected && tool.riskLevel === 'high');
        const warnings = [];
        // 生成警告信息
        if (isGameRunning && !isGameResponding) {
            warnings.push('游戏进程未响应');
        }
        if (hasInterference) {
            const highRiskTools = thirdPartyTools.filter(t => t.isDetected && t.riskLevel === 'high');
            warnings.push(`检测到高风险第三方工具: ${highRiskTools.map(t => t.name).join(', ')}`);
        }
        // 检查分辨率
        if (gameWindow && this.settings?.displaySettings.expectedResolution) {
            const expected = this.settings.displaySettings.expectedResolution;
            if (gameWindow.width !== expected.width || gameWindow.height !== expected.height) {
                warnings.push(`游戏分辨率不匹配，期望: ${expected.width}x${expected.height}，实际: ${gameWindow.width}x${gameWindow.height}`);
            }
        }
        return {
            isRunning: this.monitorInterval !== null,
            isMonitoring: this.monitorInterval !== null,
            processInfo: gameProcess,
            windowInfo: gameWindow,
            thirdPartyTools,
            lastCheck: new Date(),
            errors: warnings,
            gameProcess,
            gameWindow,
            isGameRunning,
            isGameResponding,
            hasInterference,
            lastCheckTime: new Date(),
            warnings
        };
    }
    /**
     * 获取游戏进程信息
     */
    async getGameProcessInfo() {
        try {
            // 在实际实现中，这里会调用系统API来获取进程信息
            // 这里提供一个模拟实现
            const processes = await this.getRunningProcesses();
            const gameProcess = processes.find(p => p.processName.toLowerCase().includes('starrail') ||
                p.processName.toLowerCase().includes('honkai') ||
                p.windowTitle.includes('崩坏：星穹铁道') ||
                p.windowTitle.includes('Honkai: Star Rail'));
            return gameProcess || null;
        }
        catch (error) {
            console.error('获取游戏进程信息失败:', error);
            return null;
        }
    }
    /**
     * 获取游戏窗口信息
     */
    async getGameWindowInfo() {
        try {
            // 在实际实现中，这里会调用系统API来获取窗口信息
            // 这里提供一个模拟实现
            const windows = await this.getActiveWindows();
            const gameWindow = windows.find(w => w.title.includes('崩坏：星穹铁道') ||
                w.title.includes('Honkai: Star Rail'));
            return gameWindow || null;
        }
        catch (error) {
            console.error('获取游戏窗口信息失败:', error);
            return null;
        }
    }
    /**
     * 检测第三方工具
     */
    async detectThirdPartyTools() {
        // 使用FilterDetector进行更全面的检测
        return await this.filterDetector.detectAllFilterTools();
    }
    /**
     * 生成滤镜检测报告
     */
    async generateFilterReport() {
        return await this.filterDetector.generateFilterReport();
    }
    /**
     * 检测游戏进程是否被注入
     */
    async detectGameInjection(gameProcessId) {
        return await this.filterDetector.detectGameInjection(gameProcessId);
    }
    /**
     * 检测驱动级滤镜
     */
    async detectDriverLevelFilters() {
        return await this.filterDetector.detectDriverLevelFilters();
    }
    /**
     * 检查游戏是否响应
     */
    async checkGameResponding(processId) {
        try {
            // 在实际实现中，这里会检查进程是否响应
            // 这里提供一个模拟实现
            return true;
        }
        catch (error) {
            console.error('检查游戏响应状态失败:', error);
            return false;
        }
    }
    /**
     * 获取运行中的进程列表（模拟实现）
     */
    async getRunningProcesses() {
        // 在实际实现中，这里会调用系统API
        // 这里返回模拟数据
        return [
            {
                processId: 12345,
                processName: 'StarRail.exe',
                windowTitle: '崩坏：星穹铁道',
                isRunning: true,
                startTime: new Date(),
                memoryUsage: 2048,
                cpuUsage: 15.5
            }
        ];
    }
    /**
     * 获取活动窗口列表（模拟实现）
     */
    async getActiveWindows() {
        // 在实际实现中，这里会调用系统API
        // 这里返回模拟数据
        return [
            {
                title: '崩坏：星穹铁道',
                className: 'UnityWndClass',
                width: 1920,
                height: 1080,
                x: 0,
                y: 0,
                isVisible: true,
                isMinimized: false,
                isMaximized: false,
                isFullscreen: true
            }
        ];
    }
    /**
     * 添加事件监听器
     */
    addEventListener(eventType, callback) {
        const listeners = this.eventListeners.get(eventType) || [];
        listeners.push(callback);
        this.eventListeners.set(eventType, listeners);
    }
    /**
     * 移除事件监听器
     */
    removeEventListener(eventType, callback) {
        const listeners = this.eventListeners.get(eventType) || [];
        const index = listeners.indexOf(callback);
        if (index > -1) {
            listeners.splice(index, 1);
            this.eventListeners.set(eventType, listeners);
        }
    }
    /**
     * 触发事件
     */
    emitEvent(eventType, data) {
        const listeners = this.eventListeners.get(eventType) || [];
        listeners.forEach(callback => {
            try {
                callback({
                    id: `${eventType}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                    type: eventType,
                    data,
                    timestamp: new Date(),
                    severity: this.getEventSeverity(eventType),
                    message: this.getEventMessage(eventType, data)
                });
            }
            catch (error) {
                console.error(`事件监听器执行失败 [${eventType}]:`, error);
            }
        });
    }
    /**
     * 获取监控状态
     */
    getStatus() {
        return {
            isRunning: this.monitorInterval !== null,
            isMonitoring: this.monitorInterval !== null,
            processInfo: null,
            windowInfo: null,
            thirdPartyTools: [],
            lastCheck: new Date(),
            errors: []
        };
    }
    /**
     * 获取监控统计信息
     */
    getMonitorStats() {
        return {
            totalChecks: 0,
            successfulChecks: 0,
            failedChecks: 0,
            averageResponseTime: 0,
            uptime: 0,
            lastError: null
        };
    }
    /**
     * 获取事件严重程度
     */
    getEventSeverity(eventType) {
        switch (eventType) {
            case 'game_crashed':
            case 'game_not_responding':
                return 'error';
            case 'third_party_detected':
            case 'interference_detected':
                return 'warning';
            default:
                return 'info';
        }
    }
    /**
     * 获取事件消息
     */
    getEventMessage(eventType, data) {
        switch (eventType) {
            case 'game_started':
                return '游戏已启动';
            case 'game_stopped':
                return '游戏已停止';
            case 'game_crashed':
                return '游戏崩溃';
            case 'window_changed':
                return '游戏窗口发生变化';
            case 'resolution_changed':
                return '游戏分辨率发生变化';
            case 'third_party_detected':
                return `检测到第三方工具: ${data?.message || '未知工具'}`;
            case 'interference_detected':
                return '检测到干扰';
            case 'game_not_responding':
                return '游戏无响应';
            default:
                return `游戏事件: ${eventType}`;
        }
    }
    /**
     * 清理资源
     */
    dispose() {
        this.stopMonitoring();
        this.eventListeners.clear();
        this.lastStatus = null;
        this.settings = null;
    }
}
