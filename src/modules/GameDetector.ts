// 游戏检测模块
import { GameStatus } from '../types';
import { isBrowser } from '../utils/browserCompat.js';
import nodeWindowManager from 'node-window-manager';
import activeWin from 'active-win';
import psList from 'ps-list';
// import { exec } from 'child_process';
// import { promisify } from 'util';

// 安全获取模块
const windowManager = nodeWindowManager?.windowManager;
// const execAsync = promisify(exec); // 暂时注释掉未使用的变量
import { EventEmitter } from 'events';

export interface GameDetectorConfig {
  gameProcessNames: string[];
  gameWindowTitles: string[];
  detectionInterval: number;
  enableLogging: boolean;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
}

export interface GameProcessInfo {
  pid: number;
  name: string;
  cpu?: number;
  memory?: number;
  ppid?: number;
}

export interface GameWindowInfo {
  id: number;
  title: string;
  bounds: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  isVisible: boolean;
  isMinimized: boolean;
}

export type GameDetectorEvent = 'gameStarted' | 'gameStopped' | 'gameActivated' | 'gameDeactivated' | 'windowChanged' | 'error';

export class GameDetector extends EventEmitter {
  private isDetecting = false;
  private detectionInterval?: NodeJS.Timeout;
  private config: GameDetectorConfig;
  private currentGameStatus: GameStatus = { isRunning: false, isActive: false };
  private previousGameStatus: GameStatus = { isRunning: false, isActive: false };
  private currentProcessInfo: GameProcessInfo | null = null;
  private currentWindowInfo: GameWindowInfo | null = null;
  private lastDetectionTime: Date = new Date();
  private detectionErrors: string[] = [];

  constructor(config?: Partial<GameDetectorConfig>) {
    super();
    this.config = {
      gameProcessNames: [
        'StarRail.exe', 
        'HonkaiStarRail.exe', 
        '崩坏星穹铁道.exe',
        'starrail.exe',
        'honkai_star_rail.exe'
      ],
      gameWindowTitles: [
        '崩坏：星穹铁道', 
        'Honkai: Star Rail', 
        'StarRail',
        'Honkai Star Rail',
        '崩坏星穹铁道'
      ],
      detectionInterval: 1000,
      enableLogging: true,
      logLevel: 'info',
      ...config
    };
    
    // 设置最大监听器数量
    this.setMaxListeners(20);
  }

  /**
   * 日志记录方法
   */
  private log(level: 'debug' | 'info' | 'warn' | 'error', message: string, data?: unknown): void {
    if (!this.config.enableLogging) return;
    
    const levels = { debug: 0, info: 1, warn: 2, error: 3 };
    const configLevel = levels[this.config.logLevel];
    const messageLevel = levels[level];
    
    if (messageLevel >= configLevel) {
      const timestamp = new Date().toISOString();
      const logMessage = `[${timestamp}] [GameDetector] [${level.toUpperCase()}] ${message}`;
      
      if (data) {
        console[level === 'debug' ? 'log' : level](logMessage, data);
      } else {
        console[level === 'debug' ? 'log' : level](logMessage);
      }
    }
  }

  /**
   * 开始检测游戏状态
   */
  public startDetection(intervalMs: number = 1000): void {
    if (this.isDetecting) {
      this.log('warn', '检测已在运行中，忽略重复启动请求');
      return;
    }

    this.log('info', `开始游戏检测，检测间隔: ${intervalMs}ms`);
    this.isDetecting = true;
    this.detectionErrors = [];
    
    // 立即执行一次检测
    this.detectGameStatus().catch(error => {
      this.log('error', '初始检测失败', error);
    });
    
    this.detectionInterval = setInterval(async () => {
      try {
        await this.detectGameStatus();
      } catch (error) {
        this.log('error', '定时检测失败', error);
        this.emit('error', error);
      }
    }, intervalMs);
    
    this.emit('detectionStarted');
  }

  /**
   * 停止检测游戏状态
   */
  public stopDetection(): void {
    if (!this.isDetecting) {
      this.log('warn', '检测未在运行，忽略停止请求');
      return;
    }
    
    this.log('info', '停止游戏检测');
    
    if (this.detectionInterval) {
      clearInterval(this.detectionInterval);
      this.detectionInterval = undefined;
    }
    
    this.isDetecting = false;
    this.emit('detectionStopped');
  }

  /**
   * 检测游戏状态
   */
  private async detectGameStatus(): Promise<GameStatus> {
    // 浏览器环境返回模拟数据
    if (isBrowser) {
      return {
        isRunning: false,
        isActive: false,
        windowInfo: undefined,
        currentScene: undefined
      };
    }

    try {
      const startTime = Date.now();
      this.lastDetectionTime = new Date();
      this.previousGameStatus = { ...this.currentGameStatus };
      
      // 1. 检测游戏进程
      const gameProcess = await this.detectGameProcess();
      if (!gameProcess) {
        this.currentProcessInfo = null;
        this.currentWindowInfo = null;
        this.currentGameStatus = { isRunning: false, isActive: false };
        this.checkAndEmitStatusChanges();
        return this.currentGameStatus;
      }
      
      this.currentProcessInfo = gameProcess;
      this.log('debug', '检测到游戏进程', { pid: gameProcess.pid, name: gameProcess.name });

      // 2. 检测游戏窗口
      const gameWindow = await this.getGameWindow();
      if (!gameWindow) {
        this.currentWindowInfo = null;
        this.currentGameStatus = { isRunning: true, isActive: false, windowInfo: undefined };
        this.checkAndEmitStatusChanges();
        return this.currentGameStatus;
      }

      // 3. 获取窗口信息
      let windowRect;
      let windowInfo = null;
      try {
        windowRect = this.getGameWindowRect(gameWindow);
        this.currentWindowInfo = this.getGameWindowInfo(gameWindow);
        windowInfo = {
          title: this.currentWindowInfo.title,
          width: windowRect.width,
          height: windowRect.height,
          x: windowRect.x,
          y: windowRect.y
        };
      } catch (error) {
        this.log('warn', '获取窗口信息失败', error);
        windowRect = { x: 0, y: 0, width: 0, height: 0 };
      }
      
      const isActive = await this.isGameWindowActive();

      this.currentGameStatus = {
         isRunning: true,
         isActive: isActive,
         windowInfo,
         currentScene: 'unknown'
       };
       
      const elapsed = Date.now() - startTime;
      this.log('debug', `游戏状态检测完成，耗时: ${elapsed}ms, 进程: ${!!gameProcess}, 窗口: ${!!gameWindow}, 活动: ${isActive}`);
      this.checkAndEmitStatusChanges();
      return this.currentGameStatus;
    } catch (error) {
      this.log('error', '游戏状态检测失败', error);
      this.detectionErrors.push(`${new Date().toISOString()}: ${error}`);
      
      // 保留最多10个错误记录
      if (this.detectionErrors.length > 10) {
        this.detectionErrors = this.detectionErrors.slice(-10);
      }
      
      this.currentGameStatus = { isRunning: false, isActive: false };
      this.checkAndEmitStatusChanges();
      this.emit('error', error);
      return this.currentGameStatus;
    }
  }

  /**
   * 检查并发射状态变化事件
   */
  private checkAndEmitStatusChanges(): void {
    const current = this.currentGameStatus;
    const previous = this.previousGameStatus;
    
    // 游戏启动事件
    if (!previous.isRunning && current.isRunning) {
      this.log('info', '游戏已启动');
      this.emit('gameStarted', {
        processId: this.currentProcessInfo?.pid || 0,
        windowTitle: current.windowInfo?.title || '',
        windowInfo: current.windowInfo,
        timestamp: new Date().toISOString()
      });
    }
    
    // 游戏停止事件
    if (previous.isRunning && !current.isRunning) {
      this.log('info', '游戏已停止');
      this.emit('gameStopped', {
        lastProcessId: this.currentProcessInfo?.pid || 0,
        timestamp: new Date().toISOString()
      });
      
      // 清理状态
      this.currentProcessInfo = null;
      this.currentWindowInfo = null;
    }
    
    // 游戏激活事件
    if (current.isRunning && !previous.isActive && current.isActive) {
      this.log('info', '游戏窗口已激活');
      this.emit('gameActivated', {
        windowTitle: current.windowInfo?.title || '',
        windowInfo: current.windowInfo,
        timestamp: new Date().toISOString()
      });
    }
    
    // 游戏失活事件
    if (current.isRunning && previous.isActive && !current.isActive) {
      this.log('info', '游戏窗口已失活');
      this.emit('gameDeactivated', {
        windowTitle: current.windowInfo?.title || '',
        timestamp: new Date().toISOString()
      });
    }
    
    // 窗口变化事件
    if (current.isRunning && previous.isRunning) {
      const currentTitle = current.windowInfo?.title || '';
      const previousTitle = previous.windowInfo?.title || '';
      
      if (currentTitle !== previousTitle && currentTitle && previousTitle) {
        this.log('info', '游戏窗口标题已变化', {
          from: previousTitle,
          to: currentTitle
        });
        this.emit('windowChanged', {
          previousTitle,
          currentTitle,
          windowInfo: current.windowInfo,
          timestamp: new Date().toISOString()
        });
      }
      
      // 窗口大小或位置变化
      if (current.windowInfo && previous.windowInfo) {
        const sizeChanged = current.windowInfo.width !== previous.windowInfo.width ||
                           current.windowInfo.height !== previous.windowInfo.height;
        const positionChanged = current.windowInfo.x !== previous.windowInfo.x ||
                               current.windowInfo.y !== previous.windowInfo.y;
        
        if (sizeChanged || positionChanged) {
          this.emit('windowResized', {
            windowInfo: current.windowInfo,
            previousInfo: previous.windowInfo,
            sizeChanged,
            positionChanged,
            timestamp: new Date().toISOString()
          });
        }
      }
    }
  }

  /**
   * 获取当前游戏状态
   */
  public async getCurrentStatus(): Promise<GameStatus> {
    return this.detectGameStatus();
  }

  /**
   * 检测游戏进程
   */
  private async detectGameProcess(): Promise<GameProcessInfo | null> {
    // 浏览器环境返回null
    if (isBrowser || !psList) {
      return null;
    }

    try {
      const processes = await psList();
      
      // 查找匹配的游戏进程
      for (const processName of this.config.gameProcessNames) {
        const gameProcess = processes.find(p => {
          const name = p.name.toLowerCase();
          const targetName = processName.toLowerCase();
          
          // 精确匹配或包含匹配
          return name === targetName || 
                 name.includes(targetName) ||
                 name.replace('.exe', '') === targetName.replace('.exe', '');
        });
        
        if (gameProcess) {
          this.log('debug', `找到游戏进程: ${gameProcess.name} (PID: ${gameProcess.pid})`);
          const processInfo: GameProcessInfo = {
            pid: gameProcess.pid,
            name: gameProcess.name,
            cpu: gameProcess.cpu,
            memory: gameProcess.memory,
            ppid: gameProcess.ppid
          };
          return processInfo;
        }
      }
      
      this.log('debug', `未找到游戏进程，搜索的进程名: ${this.config.gameProcessNames.join(', ')}`);
      return null;
    } catch (error) {
      this.log('error', '检测游戏进程失败', error);
      throw error; // 重新抛出错误以便上层捕获
    }
  }

  /**
   * 获取游戏窗口
   */
  private async getGameWindow(): Promise<unknown | null> {
    try {
      const windows = windowManager.getWindows();
      
      // 查找匹配的游戏窗口
      for (const windowTitle of this.config.gameWindowTitles) {
        const gameWindow = windows.find(w => {
          try {
            const title = w.getTitle().toLowerCase();
            const targetTitle = windowTitle.toLowerCase();
            
            // 精确匹配或包含匹配
            return title === targetTitle || 
                   title.includes(targetTitle) ||
                   title.replace(/\s+/g, '').includes(targetTitle.replace(/\s+/g, ''));
          } catch {
            // 某些窗口可能无法获取标题
            return false;
          }
        });
        
        if (gameWindow && gameWindow.isVisible()) {
          this.log('debug', `找到游戏窗口: ${gameWindow.getTitle()} (ID: ${gameWindow.id})`);
          return gameWindow;
        }
      }
      
      this.log('debug', `未找到游戏窗口，搜索的窗口标题: ${this.config.gameWindowTitles.join(', ')}`);
      return null;
    } catch (error) {
      this.log('error', '获取游戏窗口失败', error);
      return null;
    }
  }

  /**
   * 获取游戏窗口信息
   */
  private getGameWindowInfo(window: unknown): GameWindowInfo {
    const win = window as Record<string, unknown>;
    const bounds = (win.getBounds as Function)();
    return {
      id: Number(win.id) || 0,
      title: String((win.getTitle as Function)() || ''),
      bounds: {
        x: bounds.x,
        y: bounds.y,
        width: bounds.width,
        height: bounds.height
      },
      isVisible: Boolean((win.isVisible as Function)()),
      isMinimized: !Boolean((win.isVisible as Function)())
    };
  }

  /**
   * 检测游戏窗口是否处于活动状态
   */
  private async isGameWindowActive(): Promise<boolean> {
    try {
      const activeWindow = await activeWin();
      
      if (!activeWindow) {
        this.log('debug', '未检测到活动窗口');
        return false;
      }
      
      // 检查活动窗口是否为游戏窗口
      const isGameActive = this.config.gameWindowTitles.some(title => {
        const activeTitle = activeWindow.title.toLowerCase();
        const gameTitle = title.toLowerCase();
        return activeTitle === gameTitle || 
               activeTitle.includes(gameTitle) ||
               activeTitle.replace(/\s+/g, '').includes(gameTitle.replace(/\s+/g, ''));
      });
      
      if (isGameActive) {
        this.log('debug', `游戏窗口处于活动状态: ${activeWindow.title}`);
      }
      
      return isGameActive;
      
    } catch (error) {
      this.log('error', '检测活动窗口失败', error);
      return false;
    }
  }

  /**
   * 获取游戏窗口位置信息
   */
  private getGameWindowRect(window: unknown): { x: number; y: number; width: number; height: number } {
    try {
      const windowObj = window as Record<string, unknown>;
      const getBounds = windowObj.getBounds as () => { x: number; y: number; width: number; height: number };
      const bounds = getBounds();
      const rect = {
        x: bounds.x,
        y: bounds.y,
        width: bounds.width,
        height: bounds.height
      };
      this.log('debug', '获取窗口位置信息', rect);
      return rect;
    } catch (error) {
      this.log('error', '获取窗口位置失败', error);
      return { x: 0, y: 0, width: 0, height: 0 };
    }
  }



  /**
   * 等待游戏启动
   */
  public async waitForGameStart(timeoutMs: number = 30000): Promise<boolean> {
    const startTime = Date.now();
    let lastLogTime = startTime;
    
    this.log('info', `开始等待游戏启动，超时时间: ${timeoutMs}ms`);
    
    while (Date.now() - startTime < timeoutMs) {
      // 手动检测一次状态
      const status = await this.detectGameStatus();
      
      if (status.isRunning) {
        const elapsed = Date.now() - startTime;
        this.log('info', `游戏已启动，等待时间: ${elapsed}ms`);
        
        // 发射游戏启动事件
        this.emit('gameStarted', {
          processId: this.currentProcessInfo?.pid || 0,
          windowTitle: status.windowInfo?.title || '',
          windowInfo: status.windowInfo,
          timestamp: new Date().toISOString(),
          startupTime: elapsed
        });
        
        return true;
      }
      
      // 每5秒输出一次等待日志
      const now = Date.now();
      if (now - lastLogTime >= 5000) {
        const elapsed = now - startTime;
        const remaining = timeoutMs - elapsed;
        this.log('info', `等待游戏启动中... 已等待: ${Math.round(elapsed/1000)}s, 剩余: ${Math.round(remaining/1000)}s`);
        lastLogTime = now;
      }
      
      // 等待1秒后重试
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    const elapsed = Date.now() - startTime;
    this.log('warn', `等待游戏启动超时，总等待时间: ${elapsed}ms`);
    return false;
  }

  /**
   * 检测指定窗口是否为游戏窗口
   */
  private isGameWindow(windowTitle: string): boolean {
    if (!windowTitle) {
      return false;
    }
    
    const title = windowTitle.toLowerCase().trim();
    
    return this.config.gameWindowTitles.some(gameTitle => {
      const targetTitle = gameTitle.toLowerCase().trim();
      
      // 完全匹配
      if (title === targetTitle) {
        return true;
      }
      
      // 包含匹配
      if (title.includes(targetTitle)) {
        return true;
      }
      
      // 忽略空格的匹配
      const titleNoSpaces = title.replace(/\s+/g, '');
      const targetTitleNoSpaces = targetTitle.replace(/\s+/g, '');
      if (titleNoSpaces.includes(targetTitleNoSpaces)) {
        return true;
      }
      
      return false;
    });
  }

  /**
   * 获取检测配置
   */
  public getConfig(): GameDetectorConfig {
    return { ...this.config };
  }

  /**
   * 更新检测配置
   */
  public updateConfig(config: Partial<GameDetectorConfig>): void {
    const oldConfig = { ...this.config };
    this.config = { ...this.config, ...config };
    
    // 记录配置变更
    const changes: string[] = [];
    if (JSON.stringify(oldConfig.gameProcessNames) !== JSON.stringify(this.config.gameProcessNames)) {
      changes.push(`进程名: ${oldConfig.gameProcessNames.join(',')} -> ${this.config.gameProcessNames.join(',')}`);
    }
    if (JSON.stringify(oldConfig.gameWindowTitles) !== JSON.stringify(this.config.gameWindowTitles)) {
      changes.push(`窗口标题: ${oldConfig.gameWindowTitles.join(',')} -> ${this.config.gameWindowTitles.join(',')}`);
    }
    if (oldConfig.detectionInterval !== this.config.detectionInterval) {
      changes.push(`检测间隔: ${oldConfig.detectionInterval}ms -> ${this.config.detectionInterval}ms`);
    }
    
    if (changes.length > 0) {
      this.log('info', `游戏检测器配置已更新: ${changes.join('; ')}`);
      
      // 如果检测正在运行且间隔发生变化，重启检测
      if (this.isDetecting && oldConfig.detectionInterval !== this.config.detectionInterval) {
        this.log('info', '检测间隔已变更，重启检测器');
        this.stopDetection();
        setTimeout(() => this.startDetection(), 100);
      }
    }
  }

  /**
   * 获取检测状态
   */
  public isDetectionRunning(): boolean {
    return this.isDetecting;
  }

  /**
   * 获取当前进程信息
   */
  public getCurrentProcessInfo(): GameProcessInfo | null {
    return this.currentProcessInfo;
  }

  /**
   * 获取当前窗口信息
   */
  public getCurrentWindowInfo(): GameWindowInfo | null {
    return this.currentWindowInfo;
  }

  /**
   * 获取游戏进程信息（包含窗口信息）
   */
  public async getGameProcessInfo(): Promise<{ processInfo: GameProcessInfo | null; windowInfo: GameWindowInfo | null } | null> {
    if (!this.currentProcessInfo || !this.currentWindowInfo) {
      return null;
    }
    
    return {
      processInfo: this.currentProcessInfo,
      windowInfo: this.currentWindowInfo
    };
  }

  /**
   * 获取最后检测时间
   */
  public getLastDetectionTime(): Date {
    return this.lastDetectionTime;
  }

  /**
   * 获取检测错误历史
   */
  public getDetectionErrors(): string[] {
    return [...this.detectionErrors];
  }

  /**
   * 清除检测错误历史
   */
  public clearDetectionErrors(): void {
    this.detectionErrors = [];
    this.log('info', '检测错误历史已清除');
  }

  /**
   * 获取检测统计信息
   */
  public getDetectionStats(): {
    isRunning: boolean;
    lastDetectionTime: Date;
    errorCount: number;
    currentProcess: GameProcessInfo | null;
    currentWindow: GameWindowInfo | null;
  } {
    return {
      isRunning: this.isDetecting,
      lastDetectionTime: this.lastDetectionTime,
      errorCount: this.detectionErrors.length,
      currentProcess: this.currentProcessInfo,
      currentWindow: this.currentWindowInfo
    };
  }

  /**
   * 强制刷新游戏状态
   */
  public async forceRefresh(): Promise<GameStatus> {
    this.log('info', '强制刷新游戏状态');
    return await this.detectGameStatus();
  }

  /**
   * 重置检测器状态
   */
  public reset(): void {
    this.log('info', '重置检测器状态');
    
    // 停止检测
    this.stopDetection();
    
    // 清理状态
    this.currentProcessInfo = null;
    this.currentWindowInfo = null;
    this.previousGameStatus = { isRunning: false, isActive: false };
    this.currentGameStatus = { isRunning: false, isActive: false };
    
    // 清理错误
    this.detectionErrors = [];
    
    this.lastDetectionTime = new Date();
  }

  /**
   * 检查游戏是否正在运行
   */
  public isGameRunning(): boolean {
    return this.currentGameStatus.isRunning;
  }

  /**
   * 检查游戏窗口是否激活
   */
  public isGameActive(): boolean {
    return this.currentGameStatus.isActive;
  }

  /**
   * 等待游戏停止
   */
  public async waitForGameStop(timeout: number = 30000): Promise<boolean> {
    const startTime = Date.now();
    let lastLogTime = startTime;
    
    this.log('info', `开始等待游戏停止，超时时间: ${timeout}ms`);
    
    while (Date.now() - startTime < timeout) {
      // 手动检测一次状态
      await this.detectGameStatus();
      
      if (!this.currentGameStatus.isRunning) {
        this.log('info', '游戏停止检测成功');
        return true;
      }
      
      // 每5秒输出一次等待日志
      const now = Date.now();
      if (now - lastLogTime >= 5000) {
        const elapsed = now - startTime;
        const remaining = timeout - elapsed;
        this.log('info', `等待游戏停止中... 已等待: ${Math.round(elapsed/1000)}s, 剩余: ${Math.round(remaining/1000)}s`);
        lastLogTime = now;
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    this.log('warn', '等待游戏停止超时');
    return false;
  }

  /**
   * 等待游戏窗口激活
   */
  public async waitForGameActivation(timeout: number = 10000): Promise<boolean> {
    const startTime = Date.now();
    
    this.log('info', `开始等待游戏窗口激活，超时时间: ${timeout}ms`);
    
    while (Date.now() - startTime < timeout) {
      await this.detectGameStatus();
      
      if (this.currentGameStatus.isRunning && this.currentGameStatus.isActive) {
        this.log('info', '游戏窗口激活检测成功');
        return true;
      }
      
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    this.log('warn', '等待游戏窗口激活超时');
    return false;
  }
}

export default GameDetector;