import { GameLauncher } from './GameLauncher';
import { GameMonitor } from './GameMonitor';
export class AutoLaunchManager {
    constructor() {
        this.isInitialized = false;
        this.launchAttempts = 0;
        this.gameMonitor = new GameMonitor();
        this.gameLauncher = new GameLauncher(this.gameMonitor);
    }
    async initialize() {
        if (this.isInitialized) {
            return;
        }
        try {
            await this.delay(1000);
            this.isInitialized = true;
            console.log('AutoLaunchManager initialized successfully');
        }
        catch (error) {
            console.error('Failed to initialize AutoLaunchManager:', error);
            throw error;
        }
    }
    async executeAutoLaunch(settings) {
        const result = {
            success: false,
            launched: false,
            monitoringStarted: false,
            message: ''
        };
        try {
            if (!settings.enabled) {
                result.message = '自动启动已禁用';
                result.success = true;
                return result;
            }
            if (!settings.gamePath) {
                result.message = '游戏路径未配置';
                result.error = 'Game path not configured';
                return result;
            }
            const gameStatus = await this.gameMonitor.getGameStatus();
            if (gameStatus.isRunning) {
                result.message = '游戏已在运行，跳过启动';
                result.success = true;
                if (settings.startMonitoring && !this.gameMonitor.getStatus().isMonitoring) {
                    await this.startMonitoring(settings.monitoringDelay);
                    result.monitoringStarted = true;
                }
                return result;
            }
            if (settings.launchDelay > 0) {
                console.log(`Waiting ${settings.launchDelay} seconds before launching game...`);
                await this.delay(settings.launchDelay * 1000);
            }
            const launchResult = await this.attemptGameLaunch(settings);
            result.launched = launchResult.success;
            if (launchResult.success) {
                result.message = '游戏启动成功';
                result.success = true;
                if (settings.startMonitoring) {
                    await this.startMonitoring(settings.monitoringDelay);
                    result.monitoringStarted = true;
                }
            }
            else {
                result.message = `游戏启动失败: ${launchResult.message}`;
                result.error = launchResult.error;
            }
            return result;
        }
        catch (error) {
            result.message = '自动启动过程中发生错误';
            result.error = error instanceof Error ? error.message : String(error);
            console.error('Auto launch failed:', error);
            return result;
        }
    }
    async attemptGameLaunch(settings) {
        const maxAttempts = Math.max(1, settings.retryAttempts || 1);
        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            this.launchAttempts = attempt;
            try {
                console.log(`Game launch attempt ${attempt}/${maxAttempts}`);
                const launchConfig = {
                    gamePath: settings.gamePath,
                    launchDelay: 0,
                    waitForGameReady: true,
                    maxWaitTime: 60,
                    autoLaunch: true,
                    terminateOnExit: false
                };
                const result = await this.gameLauncher.launchGame(launchConfig);
                if (result.success) {
                    return {
                        success: true,
                        message: `游戏在第 ${attempt} 次尝试中启动成功`
                    };
                }
                else {
                    console.warn(`Launch attempt ${attempt} failed:`, result.message);
                    if (attempt < maxAttempts && settings.retryDelay > 0) {
                        console.log(`Waiting ${settings.retryDelay} seconds before retry...`);
                        await this.delay(settings.retryDelay * 1000);
                    }
                }
            }
            catch (error) {
                console.error(`Launch attempt ${attempt} error:`, error);
                if (attempt < maxAttempts && settings.retryDelay > 0) {
                    await this.delay(settings.retryDelay * 1000);
                }
            }
        }
        return {
            success: false,
            message: `游戏启动失败，已尝试 ${maxAttempts} 次`,
            error: 'All launch attempts failed'
        };
    }
    async startMonitoring(delay = 5) {
        try {
            if (delay > 0) {
                console.log(`Waiting ${delay} seconds before starting monitoring...`);
                await this.delay(delay * 1000);
            }
            await this.gameMonitor.startMonitoring();
            console.log('Game monitoring started successfully');
        }
        catch (error) {
            console.error('Failed to start game monitoring:', error);
            throw error;
        }
    }
    static createAutoLaunchSettings(gameSettings) {
        return {
            enabled: gameSettings.autoLaunch,
            gamePath: gameSettings.gamePath,
            launchDelay: gameSettings.launchDelay || 2,
            startMonitoring: gameSettings.enableMonitoring || true,
            monitoringDelay: 5,
            retryAttempts: 3,
            retryDelay: 10
        };
    }
    async checkAutoLaunchConditions(settings) {
        try {
            if (!settings.enabled) {
                return {
                    canLaunch: false,
                    reason: '自动启动已禁用'
                };
            }
            if (!settings.gamePath) {
                return {
                    canLaunch: false,
                    reason: '游戏路径未配置',
                    suggestions: ['请在设置中配置游戏安装路径']
                };
            }
            const canLaunchResult = await this.gameLauncher.canLaunchGame(settings.gamePath);
            if (!canLaunchResult.canLaunch) {
                return {
                    canLaunch: false,
                    reason: canLaunchResult.reason || '游戏无法启动',
                    suggestions: canLaunchResult.suggestions || []
                };
            }
            return {
                canLaunch: true
            };
        }
        catch (error) {
            return {
                canLaunch: false,
                reason: '检查启动条件时发生错误',
                suggestions: ['请检查游戏路径和系统状态']
            };
        }
    }
    getAutoLaunchStatus() {
        return {
            isInitialized: this.isInitialized,
            launchAttempts: this.launchAttempts,
            gameRunning: false,
            monitoringActive: this.gameMonitor.getStatus().isMonitoring
        };
    }
    async shutdown() {
        try {
            if (this.gameMonitor.getStatus().isMonitoring) {
                await this.gameMonitor.stopMonitoring();
            }
            this.isInitialized = false;
            console.log('AutoLaunchManager shutdown completed');
        }
        catch (error) {
            console.error('Error during AutoLaunchManager shutdown:', error);
        }
    }
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    static getRecommendedSettings() {
        return {
            enabled: false,
            launchDelay: 3,
            startMonitoring: true,
            monitoringDelay: 5,
            retryAttempts: 2,
            retryDelay: 10
        };
    }
}
