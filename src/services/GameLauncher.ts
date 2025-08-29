import { spawn, ChildProcess } from 'child_process';
import { existsSync } from 'fs';
import { dirname, resolve } from 'path';
import { 
  GameLaunchConfig, 
  GameLaunchResult, 
  GameProcessInfo,
  GameWindowInfo,
  AutoLaunchConditions 
} from '../types/index.js';
import { GameMonitor } from './GameMonitor.js';

/**
 * 游戏启动器服务
 * 负责游戏的自动启动、启动验证和启动管理
 */
export class GameLauncher {
  private gameMonitor: GameMonitor;
  private launchProcess: ChildProcess | null = null;
  private launchTimeout: NodeJS.Timeout | null = null;

  constructor(gameMonitor: GameMonitor) {
    this.gameMonitor = gameMonitor;
  }

  /**
   * 启动游戏
   */
  public async launchGame(config: GameLaunchConfig): Promise<GameLaunchResult> {
    const startTime = new Date();
    
    try {
      // 验证配置
      const validationResult = this.validateLaunchConfig(config);
      if (!validationResult.isValid) {
        return {
          success: false,
          errorMessage: validationResult.errorMessage,
          launchTime: startTime,
          totalWaitTime: 0
        };
      }

      // 检查游戏是否已经在运行
      const currentStatus = await this.gameMonitor.getGameStatus();
      if (currentStatus.isGameRunning) {
        return {
          success: false,
          errorMessage: '游戏已经在运行中',
          launchTime: startTime,
          totalWaitTime: 0
        };
      }

      // 应用启动延迟
      if (config.launchDelay > 0) {
        console.log(`等待启动延迟: ${config.launchDelay}秒`);
        await this.sleep(config.launchDelay * 1000);
      }

      // 启动游戏进程
      const launchResult = await this.startGameProcess(config);
      if (!launchResult.success) {
        return {
          success: false,
          errorMessage: launchResult.errorMessage,
          launchTime: startTime,
          totalWaitTime: Date.now() - startTime.getTime()
        };
      }

      // 等待游戏准备就绪
      let readyTime: Date | undefined;
      if (config.waitForGameReady) {
        const waitResult = await this.waitForGameReady(config.maxWaitTime);
        if (waitResult.success) {
          readyTime = waitResult.readyTime;
        } else {
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

    } catch (error) {
      console.error('启动游戏失败:', error);
      return {
        success: false,
        errorMessage: error instanceof Error ? error.message : '未知错误',
        launchTime: startTime,
        totalWaitTime: Date.now() - startTime.getTime()
      };
    }
  }

  /**
   * 验证启动配置
   */
  private validateLaunchConfig(config: GameLaunchConfig): { isValid: boolean; errorMessage?: string } {
    // 检查游戏路径
    if (!config.gamePath) {
      return { isValid: false, errorMessage: '游戏路径不能为空' };
    }

    if (!existsSync(config.gamePath)) {
      return { isValid: false, errorMessage: `游戏文件不存在: ${config.gamePath}` };
    }

    // 检查启动器路径（如果指定）
    if (config.launcherPath && !existsSync(config.launcherPath)) {
      return { isValid: false, errorMessage: `启动器文件不存在: ${config.launcherPath}` };
    }

    // 检查工作目录（如果指定）
    if (config.workingDirectory && !existsSync(config.workingDirectory)) {
      return { isValid: false, errorMessage: `工作目录不存在: ${config.workingDirectory}` };
    }

    // 检查最大等待时间
    if (config.maxWaitTime < 0 || config.maxWaitTime > 300) {
      return { isValid: false, errorMessage: '最大等待时间必须在0-300秒之间' };
    }

    return { isValid: true };
  }

  /**
   * 启动游戏进程
   */
  private async startGameProcess(config: GameLaunchConfig): Promise<{ success: boolean; processId?: number; errorMessage?: string }> {
    return new Promise((resolve) => {
      try {
        // 确定要执行的程序和参数
        const executablePath = config.launcherPath || config.gamePath;
        const args = config.launchArguments ? config.launchArguments.split(' ').filter(arg => arg.trim()) : [];
        const workingDir = config.workingDirectory || dirname(executablePath);

        console.log(`启动游戏: ${executablePath}`);
        console.log(`参数: ${args.join(' ')}`);
        console.log(`工作目录: ${workingDir}`);

        // 启动进程
        this.launchProcess = spawn(executablePath, args, {
          cwd: workingDir,
          detached: true,
          stdio: 'ignore'
        });

        // 处理启动成功
        this.launchProcess.on('spawn', () => {
          console.log(`游戏进程已启动，PID: ${this.launchProcess?.pid}`);
          resolve({
            success: true,
            processId: this.launchProcess?.pid
          });
        });

        // 处理启动失败
        this.launchProcess.on('error', (error) => {
          console.error('游戏进程启动失败:', error);
          resolve({
            success: false,
            errorMessage: `进程启动失败: ${error.message}`
          });
        });

        // 处理进程意外退出
        this.launchProcess.on('exit', (code, signal) => {
          if (code !== 0 && code !== null) {
            console.error(`游戏进程异常退出，代码: ${code}, 信号: ${signal}`);
            resolve({
              success: false,
              errorMessage: `进程异常退出，代码: ${code}`
            });
          }
        });

        // 设置启动超时
        setTimeout(() => {
          if (this.launchProcess && !this.launchProcess.pid) {
            this.launchProcess.kill();
            resolve({
              success: false,
              errorMessage: '进程启动超时'
            });
          }
        }, 30000); // 30秒超时

      } catch (error) {
        console.error('启动游戏进程异常:', error);
        resolve({
          success: false,
          errorMessage: error instanceof Error ? error.message : '未知错误'
        });
      }
    });
  }

  /**
   * 等待游戏准备就绪
   */
  private async waitForGameReady(maxWaitTime: number): Promise<{ success: boolean; readyTime?: Date; errorMessage?: string }> {
    const startTime = Date.now();
    const maxWaitMs = maxWaitTime * 1000;
    const checkInterval = 2000; // 每2秒检查一次

    return new Promise((resolve) => {
      const checkReady = async () => {
        try {
          const currentTime = Date.now();
          const elapsedTime = currentTime - startTime;

          // 检查是否超时
          if (elapsedTime >= maxWaitMs) {
            resolve({
              success: false,
              errorMessage: `等待游戏就绪超时 (${maxWaitTime}秒)`
            });
            return;
          }

          // 检查游戏状态
          const status = await this.gameMonitor.getGameStatus();
          
          if (status.isGameRunning && status.isGameResponding && status.gameWindow) {
            // 游戏已就绪
            resolve({
              success: true,
              readyTime: new Date()
            });
            return;
          }

          // 继续等待
          setTimeout(checkReady, checkInterval);

        } catch (error) {
          console.error('检查游戏就绪状态失败:', error);
          resolve({
            success: false,
            errorMessage: '检查游戏状态失败'
          });
        }
      };

      // 开始检查
      checkReady();
    });
  }

  /**
   * 强制终止游戏
   */
  public async terminateGame(): Promise<boolean> {
    try {
      const status = await this.gameMonitor.getGameStatus();
      
      if (!status.isGameRunning || !status.gameProcess) {
        console.log('游戏未在运行');
        return true;
      }

      // 尝试优雅关闭
      if (this.launchProcess && this.launchProcess.pid === status.gameProcess.processId) {
        this.launchProcess.kill('SIGTERM');
        
        // 等待进程关闭
        await this.sleep(5000);
        
        // 检查是否已关闭
        const newStatus = await this.gameMonitor.getGameStatus();
        if (!newStatus.isGameRunning) {
          console.log('游戏已优雅关闭');
          return true;
        }
      }

      // 强制关闭
      console.log('尝试强制关闭游戏进程');
      const result = await this.forceKillGameProcess(status.gameProcess.processId);
      
      if (result) {
        console.log('游戏进程已强制关闭');
      } else {
        console.error('无法关闭游戏进程');
      }
      
      return result;

    } catch (error) {
      console.error('终止游戏失败:', error);
      return false;
    }
  }

  /**
   * 强制杀死游戏进程
   */
  private async forceKillGameProcess(processId: number): Promise<boolean> {
    try {
      // 在实际实现中，这里会调用系统API来强制终止进程
      // 这里提供一个模拟实现
      process.kill(processId, 'SIGKILL');
      return true;
    } catch (error) {
      console.error('强制终止进程失败:', error);
      return false;
    }
  }

  /**
   * 重启游戏
   */
  public async restartGame(config: GameLaunchConfig): Promise<GameLaunchResult> {
    console.log('正在重启游戏...');
    
    // 先终止当前游戏
    const terminateSuccess = await this.terminateGame();
    if (!terminateSuccess) {
      return {
        success: false,
        errorMessage: '无法终止当前游戏进程',
        launchTime: new Date(),
        totalWaitTime: 0
      };
    }

    // 等待一段时间确保进程完全关闭
    await this.sleep(3000);

    // 重新启动游戏
    return await this.launchGame(config);
  }

  /**
   * 检查游戏是否可以启动
   */
  public async canLaunchGame(gamePath: string): Promise<{ canLaunch: boolean; reason: string; suggestions: string[] }> {
    const config: GameLaunchConfig = {
      gamePath,
      launchDelay: 0,
      waitForGameReady: true,
      maxWaitTime: 60,
      autoLaunch: false
    };

    // 验证配置
    const validationResult = this.validateLaunchConfig(config);
    if (!validationResult.isValid) {
      return {
        canLaunch: false,
        reason: validationResult.errorMessage || '配置验证失败',
        suggestions: ['请检查游戏路径是否正确', '确保游戏文件存在']
      };
    }

    // 检查游戏是否已在运行
    const status = await this.gameMonitor.getGameStatus();
    if (status.isGameRunning) {
      return {
        canLaunch: false,
        reason: '游戏已在运行中',
        suggestions: ['请先关闭当前游戏', '或使用重启功能']
      };
    }

    // 检查系统资源（可选）
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

  /**
   * 检查系统资源
   */
  private async checkSystemResources(): Promise<boolean> {
    try {
      // 在实际实现中，这里会检查内存、CPU等系统资源
      // 这里提供一个模拟实现
      return true;
    } catch (error) {
      console.error('检查系统资源失败:', error);
      return false;
    }
  }

  /**
   * 获取推荐的启动配置
   */
  public getRecommendedLaunchConfig(gamePath: string): Partial<GameLaunchConfig> {
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

  /**
   * 检测游戏安装路径
   */
  public async detectGameInstallation(): Promise<string[]> {
    const possiblePaths = [
      // Steam 默认路径
      'C:\\Program Files (x86)\\Steam\\steamapps\\common\\Honkai Star Rail\\Game\\StarRail.exe',
      'D:\\Steam\\steamapps\\common\\Honkai Star Rail\\Game\\StarRail.exe',
      'E:\\Steam\\steamapps\\common\\Honkai Star Rail\\Game\\StarRail.exe',
      
      // Epic Games 默认路径
      'C:\\Program Files\\Epic Games\\HonkaiStarRail\\Game\\StarRail.exe',
      
      // miHoYo 官方启动器路径
      'C:\\Program Files\\miHoYo\\Honkai Star Rail\\Game\\StarRail.exe',
      'D:\\miHoYo\\Honkai Star Rail\\Game\\StarRail.exe',
      'E:\\miHoYo\\Honkai Star Rail\\Game\\StarRail.exe',
      
      // 其他常见路径
      'C:\\Games\\Honkai Star Rail\\Game\\StarRail.exe',
      'D:\\Games\\Honkai Star Rail\\Game\\StarRail.exe',
      'E:\\Games\\Honkai Star Rail\\Game\\StarRail.exe'
    ];

    const foundPaths: string[] = [];
    
    for (const path of possiblePaths) {
      if (existsSync(path)) {
        foundPaths.push(path);
      }
    }

    return foundPaths;
  }

  /**
   * 睡眠函数
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 清理资源
   */
  public dispose(): void {
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