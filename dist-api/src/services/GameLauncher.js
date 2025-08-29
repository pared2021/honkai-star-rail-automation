import { spawn } from 'child_process';
import { existsSync } from 'fs';
import { dirname } from 'path';
export class GameLauncher {
    constructor(gameMonitor) {
        this.launchProcess = null;
        this.launchTimeout = null;
        this.gameMonitor = gameMonitor;
    }
    async launchGame(config) {
        const startTime = new Date();
        try {
            const validationResult = this.validateLaunchConfig(config);
            if (!validationResult.isValid) {
                return {
                    success: false,
                    errorMessage: validationResult.errorMessage,
                    launchTime: startTime,
                    totalWaitTime: 0
                };
            }
            const currentStatus = await this.gameMonitor.getGameStatus();
            if (currentStatus.isGameRunning) {
                return {
                    success: false,
                    errorMessage: '游戏已经在运行中',
                    launchTime: startTime,
                    totalWaitTime: 0
                };
            }
            if (config.launchDelay > 0) {
                console.log(`等待启动延迟: ${config.launchDelay}秒`);
                await this.sleep(config.launchDelay * 1000);
            }
            const launchResult = await this.startGameProcess(config);
            if (!launchResult.success) {
                return {
                    success: false,
                    errorMessage: launchResult.errorMessage,
                    launchTime: startTime,
                    totalWaitTime: Date.now() - startTime.getTime()
                };
            }
            let readyTime;
            if (config.waitForGameReady) {
                const waitResult = await this.waitForGameReady(config.maxWaitTime);
                if (waitResult.success) {
                    readyTime = waitResult.readyTime;
                }
                else {
                    console.warn('游戏启动超时，但进程已启动:', waitResult.errorMessage);
                }
            }
            const totalWaitTime = Date.now() - startTime.getTime();
            return {
                success: true,
                processId: launchResult.processId,
                launchTime: startTime,
                readyTime,
                totalWaitTime
            };
        }
        catch (error) {
            console.error('启动游戏失败:', error);
            return {
                success: false,
                errorMessage: error instanceof Error ? error.message : '未知错误',
                launchTime: startTime,
                totalWaitTime: Date.now() - startTime.getTime()
            };
        }
    }
    validateLaunchConfig(config) {
        if (!config.gamePath) {
            return { isValid: false, errorMessage: '游戏路径不能为空' };
        }
        if (!existsSync(config.gamePath)) {
            return { isValid: false, errorMessage: `游戏文件不存在: ${config.gamePath}` };
        }
        if (config.launcherPath && !existsSync(config.launcherPath)) {
            return { isValid: false, errorMessage: `启动器文件不存在: ${config.launcherPath}` };
        }
        if (config.workingDirectory && !existsSync(config.workingDirectory)) {
            return { isValid: false, errorMessage: `工作目录不存在: ${config.workingDirectory}` };
        }
        if (config.maxWaitTime < 0 || config.maxWaitTime > 300) {
            return { isValid: false, errorMessage: '最大等待时间必须在0-300秒之间' };
        }
        return { isValid: true };
    }
    async startGameProcess(config) {
        return new Promise((resolve) => {
            try {
                const executablePath = config.launcherPath || config.gamePath;
                const args = config.launchArguments ? config.launchArguments.split(' ').filter(arg => arg.trim()) : [];
                const workingDir = config.workingDirectory || dirname(executablePath);
                console.log(`启动游戏: ${executablePath}`);
                console.log(`参数: ${args.join(' ')}`);
                console.log(`工作目录: ${workingDir}`);
                this.launchProcess = spawn(executablePath, args, {
                    cwd: workingDir,
                    detached: true,
                    stdio: 'ignore'
                });
                this.launchProcess.on('spawn', () => {
                    console.log(`游戏进程已启动，PID: ${this.launchProcess?.pid}`);
                    resolve({
                        success: true,
                        processId: this.launchProcess?.pid
                    });
                });
                this.launchProcess.on('error', (error) => {
                    console.error('游戏进程启动失败:', error);
                    resolve({
                        success: false,
                        errorMessage: `进程启动失败: ${error.message}`
                    });
                });
                this.launchProcess.on('exit', (code, signal) => {
                    if (code !== 0 && code !== null) {
                        console.error(`游戏进程异常退出，代码: ${code}, 信号: ${signal}`);
                        resolve({
                            success: false,
                            errorMessage: `进程异常退出，代码: ${code}`
                        });
                    }
                });
                setTimeout(() => {
                    if (this.launchProcess && !this.launchProcess.pid) {
                        this.launchProcess.kill();
                        resolve({
                            success: false,
                            errorMessage: '进程启动超时'
                        });
                    }
                }, 30000);
            }
            catch (error) {
                console.error('启动游戏进程异常:', error);
                resolve({
                    success: false,
                    errorMessage: error instanceof Error ? error.message : '未知错误'
                });
            }
        });
    }
    async waitForGameReady(maxWaitTime) {
        const startTime = Date.now();
        const maxWaitMs = maxWaitTime * 1000;
        const checkInterval = 2000;
        return new Promise((resolve) => {
            const checkReady = async () => {
                try {
                    const currentTime = Date.now();
                    const elapsedTime = currentTime - startTime;
                    if (elapsedTime >= maxWaitMs) {
                        resolve({
                            success: false,
                            errorMessage: `等待游戏就绪超时 (${maxWaitTime}秒)`
                        });
                        return;
                    }
                    const status = await this.gameMonitor.getGameStatus();
                    if (status.isGameRunning && status.isGameResponding && status.gameWindow) {
                        resolve({
                            success: true,
                            readyTime: new Date()
                        });
                        return;
                    }
                    setTimeout(checkReady, checkInterval);
                }
                catch (error) {
                    console.error('检查游戏就绪状态失败:', error);
                    resolve({
                        success: false,
                        errorMessage: '检查游戏状态失败'
                    });
                }
            };
            checkReady();
        });
    }
    async terminateGame() {
        try {
            const status = await this.gameMonitor.getGameStatus();
            if (!status.isGameRunning || !status.gameProcess) {
                console.log('游戏未在运行');
                return true;
            }
            if (this.launchProcess && this.launchProcess.pid === status.gameProcess.processId) {
                this.launchProcess.kill('SIGTERM');
                await this.sleep(5000);
                const newStatus = await this.gameMonitor.getGameStatus();
                if (!newStatus.isGameRunning) {
                    console.log('游戏已优雅关闭');
                    return true;
                }
            }
            console.log('尝试强制关闭游戏进程');
            const result = await this.forceKillGameProcess(status.gameProcess.processId);
            if (result) {
                console.log('游戏进程已强制关闭');
            }
            else {
                console.error('无法关闭游戏进程');
            }
            return result;
        }
        catch (error) {
            console.error('终止游戏失败:', error);
            return false;
        }
    }
    async forceKillGameProcess(processId) {
        try {
            process.kill(processId, 'SIGKILL');
            return true;
        }
        catch (error) {
            console.error('强制终止进程失败:', error);
            return false;
        }
    }
    async restartGame(config) {
        console.log('正在重启游戏...');
        const terminateSuccess = await this.terminateGame();
        if (!terminateSuccess) {
            return {
                success: false,
                errorMessage: '无法终止当前游戏进程',
                launchTime: new Date(),
                totalWaitTime: 0
            };
        }
        await this.sleep(3000);
        return await this.launchGame(config);
    }
    async canLaunchGame(gamePath) {
        const config = {
            gamePath,
            launchDelay: 0,
            waitForGameReady: true,
            maxWaitTime: 60,
            autoLaunch: false
        };
        const validationResult = this.validateLaunchConfig(config);
        if (!validationResult.isValid) {
            return {
                canLaunch: false,
                reason: validationResult.errorMessage || '配置验证失败',
                suggestions: ['请检查游戏路径是否正确', '确保游戏文件存在']
            };
        }
        const status = await this.gameMonitor.getGameStatus();
        if (status.isGameRunning) {
            return {
                canLaunch: false,
                reason: '游戏已在运行中',
                suggestions: ['请先关闭当前游戏', '或使用重启功能']
            };
        }
        const hasEnoughResources = await this.checkSystemResources();
        if (!hasEnoughResources) {
            return {
                canLaunch: false,
                reason: '系统资源不足',
                suggestions: ['关闭其他应用程序释放内存', '检查磁盘空间']
            };
        }
        return {
            canLaunch: true,
            reason: '可以启动游戏',
            suggestions: []
        };
    }
    async checkSystemResources() {
        try {
            return true;
        }
        catch (error) {
            console.error('检查系统资源失败:', error);
            return false;
        }
    }
    getRecommendedLaunchConfig(gamePath) {
        const gameDir = dirname(gamePath);
        return {
            gamePath,
            workingDirectory: gameDir,
            launchDelay: 2,
            waitForGameReady: true,
            maxWaitTime: 60,
            autoLaunch: false
        };
    }
    async detectGameInstallation() {
        const possiblePaths = [
            'C:\\Program Files (x86)\\Steam\\steamapps\\common\\Honkai Star Rail\\Game\\StarRail.exe',
            'D:\\Steam\\steamapps\\common\\Honkai Star Rail\\Game\\StarRail.exe',
            'E:\\Steam\\steamapps\\common\\Honkai Star Rail\\Game\\StarRail.exe',
            'C:\\Program Files\\Epic Games\\HonkaiStarRail\\Game\\StarRail.exe',
            'C:\\Program Files\\miHoYo\\Honkai Star Rail\\Game\\StarRail.exe',
            'D:\\miHoYo\\Honkai Star Rail\\Game\\StarRail.exe',
            'E:\\miHoYo\\Honkai Star Rail\\Game\\StarRail.exe',
            'C:\\Games\\Honkai Star Rail\\Game\\StarRail.exe',
            'D:\\Games\\Honkai Star Rail\\Game\\StarRail.exe',
            'E:\\Games\\Honkai Star Rail\\Game\\StarRail.exe'
        ];
        const foundPaths = [];
        for (const path of possiblePaths) {
            if (existsSync(path)) {
                foundPaths.push(path);
            }
        }
        return foundPaths;
    }
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    dispose() {
        if (this.launchTimeout) {
            clearTimeout(this.launchTimeout);
            this.launchTimeout = null;
        }
        if (this.launchProcess) {
            this.launchProcess.removeAllListeners();
            this.launchProcess = null;
        }
    }
}
