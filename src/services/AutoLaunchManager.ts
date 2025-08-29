// 自动启动管理器
import { GameLauncher } from './GameLauncher.js';
import { GameMonitor } from './GameMonitor.js';
import { GameSettings, GameLaunchConfig } from '../types/index.js';

export interface AutoLaunchSettings {
  enabled: boolean;
  gamePath: string;
  launchDelay: number;
  startMonitoring: boolean;
  monitoringDelay: number;
  retryAttempts: number;
  retryDelay: number;
}

export interface AutoLaunchResult {
  success: boolean;
  launched: boolean;
  monitoringStarted: boolean;
  message: string;
  error?: string;
}

export class AutoLaunchManager {
  private gameLauncher: GameLauncher;
  private gameMonitor: GameMonitor;
  private isInitialized: boolean = false;
  private launchAttempts: number = 0;

  constructor() {
    this.gameMonitor = new GameMonitor();
    this.gameLauncher = new GameLauncher(this.gameMonitor);
  }

  /**
   * 初始化自动启动管理器
   */
  public async initialize(): Promise<void> {
    if (this.isInitialized) {
      return;
    }

    try {
      // 等待服务初始化
      await this.delay(1000);
      this.isInitialized = true;
      console.log('AutoLaunchManager initialized successfully');
    } catch (error) {
      console.error('Failed to initialize AutoLaunchManager:', error);
      throw error;
    }
  }

  /**
   * 执行自动启动逻辑
   */
  public async executeAutoLaunch(settings: AutoLaunchSettings): Promise<AutoLaunchResult> {
    const result: AutoLaunchResult = {
      success: false,
      launched: false,
      monitoringStarted: false,
      message: ''
    };

    try {
      // 检查是否启用自动启动
      if (!settings.enabled) {
        result.message = '自动启动已禁用';
        result.success = true;
        return result;
      }

      // 验证游戏路径
      if (!settings.gamePath) {
        result.message = '游戏路径未配置';
        result.error = 'Game path not configured';
        return result;
      }

      // 检查游戏是否已经在运行
      const gameStatus = await this.gameMonitor.getGameStatus();
      if (gameStatus.isRunning) {
        result.message = '游戏已在运行，跳过启动';
        result.success = true;
        
        // 如果需要启动监控
        if (settings.startMonitoring && !this.gameMonitor.getStatus().isMonitoring) {
          await this.startMonitoring(settings.monitoringDelay);
          result.monitoringStarted = true;
        }
        
        return result;
      }

      // 等待启动延迟
      if (settings.launchDelay > 0) {
        console.log(`Waiting ${settings.launchDelay} seconds before launching game...`);
        await this.delay(settings.launchDelay * 1000);
      }

      // 尝试启动游戏
      const launchResult = await this.attemptGameLaunch(settings);
      result.launched = launchResult.success;
      
      if (launchResult.success) {
        result.message = '游戏启动成功';
        result.success = true;
        
        // 如果需要启动监控
        if (settings.startMonitoring) {
          await this.startMonitoring(settings.monitoringDelay);
          result.monitoringStarted = true;
        }
      } else {
        result.message = `游戏启动失败: ${launchResult.message}`;
        result.error = launchResult.error;
      }

      return result;
    } catch (error) {
      result.message = '自动启动过程中发生错误';
      result.error = error instanceof Error ? error.message : String(error);
      console.error('Auto launch failed:', error);
      return result;
    }
  }

  /**
   * 尝试启动游戏（支持重试）
   */
  private async attemptGameLaunch(settings: AutoLaunchSettings): Promise<{ success: boolean; message: string; error?: string }> {
    const maxAttempts = Math.max(1, settings.retryAttempts || 1);
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      this.launchAttempts = attempt;
      
      try {
        console.log(`Game launch attempt ${attempt}/${maxAttempts}`);
        
        // 构建启动配置
        const launchConfig: GameLaunchConfig = {
          gamePath: settings.gamePath,
          launchDelay: 0, // 已经在外层处理了延迟
          waitForGameReady: true,
          maxWaitTime: 60,
          autoLaunch: true,
          terminateOnExit: false
        };

        // 尝试启动游戏
        const result = await this.gameLauncher.launchGame(launchConfig);
        
        if (result.success) {
          return {
            success: true,
            message: `游戏在第 ${attempt} 次尝试中启动成功`
          };
        } else {
          console.warn(`Launch attempt ${attempt} failed:`, result.message);
          
          // 如果不是最后一次尝试，等待重试延迟
          if (attempt < maxAttempts && settings.retryDelay > 0) {
            console.log(`Waiting ${settings.retryDelay} seconds before retry...`);
            await this.delay(settings.retryDelay * 1000);
          }
        }
      } catch (error) {
        console.error(`Launch attempt ${attempt} error:`, error);
        
        // 如果不是最后一次尝试，等待重试延迟
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

  /**
   * 启动游戏监控
   */
  private async startMonitoring(delay: number = 5): Promise<void> {
    try {
      if (delay > 0) {
        console.log(`Waiting ${delay} seconds before starting monitoring...`);
        await this.delay(delay * 1000);
      }

      await this.gameMonitor.startMonitoring();
      console.log('Game monitoring started successfully');
    } catch (error) {
      console.error('Failed to start game monitoring:', error);
      throw error;
    }
  }

  /**
   * 从游戏设置创建自动启动设置
   */
  public static createAutoLaunchSettings(gameSettings: GameSettings): AutoLaunchSettings {
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

  /**
   * 检查自动启动条件
   */
  public async checkAutoLaunchConditions(settings: AutoLaunchSettings): Promise<{
    canLaunch: boolean;
    reason?: string;
    suggestions?: string[];
  }> {
    try {
      // 检查基本条件
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

      // 检查游戏是否可以启动
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
    } catch (error) {
      return {
        canLaunch: false,
        reason: '检查启动条件时发生错误',
        suggestions: ['请检查游戏路径和系统状态']
      };
    }
  }

  /**
   * 获取自动启动状态
   */
  public getAutoLaunchStatus(): {
    isInitialized: boolean;
    launchAttempts: number;
    gameRunning: boolean;
    monitoringActive: boolean;
  } {
    return {
      isInitialized: this.isInitialized,
      launchAttempts: this.launchAttempts,
      gameRunning: false, // 需要异步检查，这里返回默认值
      monitoringActive: this.gameMonitor.getStatus().isMonitoring
    };
  }

  /**
   * 停止自动启动相关服务
   */
  public async shutdown(): Promise<void> {
    try {
      if (this.gameMonitor.getStatus().isMonitoring) {
        await this.gameMonitor.stopMonitoring();
      }
      
      this.isInitialized = false;
      console.log('AutoLaunchManager shutdown completed');
    } catch (error) {
      console.error('Error during AutoLaunchManager shutdown:', error);
    }
  }

  /**
   * 延迟工具函数
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 获取推荐的自动启动设置
   */
  public static getRecommendedSettings(): Partial<AutoLaunchSettings> {
    return {
      enabled: false, // 默认禁用，让用户主动启用
      launchDelay: 3, // 3秒启动延迟
      startMonitoring: true,
      monitoringDelay: 5, // 5秒监控延迟
      retryAttempts: 2, // 重试2次
      retryDelay: 10 // 10秒重试延迟
    };
  }
}