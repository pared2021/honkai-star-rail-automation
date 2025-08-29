import { FilterDetector } from './FilterDetector.js';
import { exec } from 'child_process';
import { promisify } from 'util';
const execAsync = promisify(exec);
export class GameMonitor {
    constructor() {
        this.monitorInterval = null;
        this.filterMonitorInterval = null;
        this.eventListeners = new Map();
        this.lastStatus = null;
        this.settings = null;
        this.knownThirdPartyTools = [
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
        ];
        this.filterDetector = new FilterDetector();
        this.initializeEventListeners();
    }
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
    setSettings(settings) {
        this.settings = settings;
    }
    startMonitoring(options) {
        if (this.monitorInterval) {
            this.stopMonitoring();
        }
        const interval = options?.interval || this.settings?.monitorSettings.checkInterval || 5;
        this.monitorInterval = setInterval(() => {
            this.performMonitorCheck();
        }, interval * 1000);
        this.filterMonitorInterval = this.filterDetector.startFilterMonitoring((report) => {
            this.emitEvent('third_party_detected', {
                message: '检测到滤镜工具变化',
                data: report
            });
        }, 30000);
        console.log(`游戏监控已启动，检查间隔: ${interval}秒`);
    }
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
    async performMonitorCheck() {
        try {
            const status = await this.getGameStatus();
            this.checkStatusChanges(status);
            this.lastStatus = status;
        }
        catch (error) {
            console.error('监控检查失败:', error);
        }
    }
    checkStatusChanges(currentStatus) {
        if (!this.lastStatus)
            return;
        if (currentStatus.isGameRunning !== this.lastStatus.isGameRunning) {
            const eventType = currentStatus.isGameRunning ? 'game_started' : 'game_stopped';
            this.emitEvent(eventType, {
                processInfo: currentStatus.gameProcess,
                timestamp: new Date()
            });
        }
        if (this.hasWindowChanged(currentStatus.gameWindow, this.lastStatus.gameWindow)) {
            this.emitEvent('window_changed', {
                oldWindow: this.lastStatus.gameWindow,
                newWindow: currentStatus.gameWindow,
                timestamp: new Date()
            });
        }
        const newTools = this.getNewlyDetectedTools(currentStatus.thirdPartyTools, this.lastStatus.thirdPartyTools);
        if (newTools.length > 0) {
            newTools.forEach(tool => {
                this.emitEvent('third_party_detected', {
                    tool,
                    timestamp: new Date()
                });
            });
        }
        if (currentStatus.hasInterference && !this.lastStatus.hasInterference) {
            this.emitEvent('interference_detected', {
                tools: currentStatus.thirdPartyTools.filter(t => t.isDetected && t.riskLevel === 'high'),
                timestamp: new Date()
            });
        }
    }
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
    getNewlyDetectedTools(current, previous) {
        return current.filter(currentTool => {
            const previousTool = previous.find(p => p.processName === currentTool.processName);
            return currentTool.isDetected && (!previousTool || !previousTool.isDetected);
        });
    }
    async getGameStatus() {
        const gameProcess = await this.getGameProcessInfo();
        const gameWindow = gameProcess ? await this.getGameWindowInfo() : null;
        const thirdPartyTools = await this.detectThirdPartyTools();
        const isGameRunning = gameProcess !== null;
        const isGameResponding = gameProcess ? await this.checkGameResponding(gameProcess.processId) : false;
        const hasInterference = thirdPartyTools.some(tool => tool.isDetected && tool.riskLevel === 'high');
        const warnings = [];
        if (isGameRunning && !isGameResponding) {
            warnings.push('游戏进程未响应');
        }
        if (hasInterference) {
            const highRiskTools = thirdPartyTools.filter(t => t.isDetected && t.riskLevel === 'high');
            warnings.push(`检测到高风险第三方工具: ${highRiskTools.map(t => t.name).join(', ')}`);
        }
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
    async getGameProcessInfo() {
        try {
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
    async getGameWindowInfo() {
        try {
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
    async detectThirdPartyTools() {
        return await this.filterDetector.detectAllFilterTools();
    }
    async generateFilterReport() {
        return await this.filterDetector.generateFilterReport();
    }
    async detectGameInjection(gameProcessId) {
        return await this.filterDetector.detectGameInjection(gameProcessId);
    }
    async detectDriverLevelFilters() {
        return await this.filterDetector.detectDriverLevelFilters();
    }
    async checkGameResponding(processId) {
        try {
            return true;
        }
        catch (error) {
            console.error('检查游戏响应状态失败:', error);
            return false;
        }
    }
    async getRunningProcesses() {
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
    async getActiveWindows() {
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
    addEventListener(eventType, callback) {
        const listeners = this.eventListeners.get(eventType) || [];
        listeners.push(callback);
        this.eventListeners.set(eventType, listeners);
    }
    removeEventListener(eventType, callback) {
        const listeners = this.eventListeners.get(eventType) || [];
        const index = listeners.indexOf(callback);
        if (index > -1) {
            listeners.splice(index, 1);
            this.eventListeners.set(eventType, listeners);
        }
    }
    emitEvent(eventType, data) {
        const listeners = this.eventListeners.get(eventType) || [];
        listeners.forEach(callback => {
            try {
                callback({
                    type: eventType,
                    data,
                    timestamp: new Date()
                });
            }
            catch (error) {
                console.error(`事件监听器执行失败 [${eventType}]:`, error);
            }
        });
    }
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
    dispose() {
        this.stopMonitoring();
        this.eventListeners.clear();
        this.lastStatus = null;
        this.settings = null;
    }
}
