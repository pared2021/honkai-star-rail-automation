// 优化版游戏检测模块
import { GameStatus } from '../types';
import { isBrowser } from '../utils/browserCompat';
import nodeWindowManager from 'node-window-manager';
import activeWin from 'active-win';
import psList from 'ps-list';
import { EventEmitter } from 'events';
import { GameDetectorConfig, GameProcessInfo, GameWindowInfo, GameDetectorEvent } from './GameDetector';

// 安全获取模块
const windowManager = nodeWindowManager?.windowManager;

/**
 * 性能优化的游戏检测器
 * 主要优化点：
 * 1. 智能检测间隔调整
 * 2. 进程和窗口缓存
 * 3. 增量检测策略
 * 4. 性能监控和统计
 */
export class GameDetectorOptimized extends EventEmitter {
  private isDetecting = false;
  private detectionInterval?: NodeJS.Timeout;
  private config: GameDetectorConfig;
  private currentGameStatus: GameStatus = { isRunning: false, isActive: false };
  private previousGameStatus: GameStatus = { isRunning: false, isActive: false };
  private currentProcessInfo: GameProcessInfo | null = null;
  private currentWindowInfo: GameWindowInfo | null = null;
  private lastDetectionTime: Date = new Date();
  private detectionErrors: string[] = [];

  // 性能优化相关属性
  private processCache: Map<number, GameProcessInfo> = new Map();
  private windowCache: Map<number, GameWindowInfo> = new Map();
  private lastProcessScan: number = 0;
  private lastWindowScan: number = 0;
  private processCacheTimeout = 5000; // 进程缓存5秒
  private windowCacheTimeout = 2000; // 窗口缓存2秒
  
  // 智能检测间隔
  private baseInterval = 1000;
  private currentInterval = 1000;
  private fastInterval = 500; // 游戏运行时快速检测
  private slowInterval = 3000; // 游戏未运行时慢速检测
  private adaptiveMode = true;
  
  // 性能统计
  private performanceStats = {
    totalDetections: 0,
    averageDetectionTime: 0,
    cacheHitRate: 0,
    errorRate: 0,
    lastOptimizationTime: Date.now()
  };
  
  // 检测策略
  private detectionStrategy: 'full' | 'incremental' | 'cached' = 'incremental';
  private consecutiveFailures = 0;
  private maxConsecutiveFailures = 3;

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
    
    this.baseInterval = this.config.detectionInterval;
    this.currentInterval = this.baseInterval;
    
    // 设置最大监听器数量
    this.setMaxListeners(20);
    
    // 定期清理缓存
    setInterval(() => this.cleanupCaches(), 10000);
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
      const logMessage = `[${timestamp}] [GameDetectorOptimized] [${level.toUpperCase()}] ${message}`;
      
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

    this.log('info', `开始优化游戏检测，基础间隔: ${intervalMs}ms`);
    this.isDetecting = true;
    this.detectionErrors = [];
    this.baseInterval = intervalMs;
    this.currentInterval = intervalMs;
    this.resetPerformanceStats();
    
    // 立即执行一次检测
    this.detectGameStatus().catch(error => {
      this.log('error', '初始检测失败', error);
    });
    
    this.scheduleNextDetection();
    this.emit('detectionStarted');
  }

  /**
   * 调度下一次检测
   */
  private scheduleNextDetection(): void {
    if (!this.isDetecting) return;
    
    // 根据当前状态调整检测间隔
    if (this.adaptiveMode) {
      this.adjustDetectionInterval();
    }
    
    this.detectionInterval = setTimeout(async () => {
      try {
        await this.detectGameStatus();
        this.scheduleNextDetection();
      } catch (error) {
        this.log('error', '定时检测失败', error);
        this.emit('error', error);
        this.scheduleNextDetection();
      }
    }, this.currentInterval);
  }

  /**
   * 智能调整检测间隔
   */
  private adjustDetectionInterval(): void {
    const wasRunning = this.previousGameStatus.isRunning;
    const isRunning = this.currentGameStatus.isRunning;
    
    if (isRunning) {
      // 游戏运行时使用快速检测
      this.currentInterval = this.fastInterval;
    } else if (wasRunning && !isRunning) {
      // 游戏刚关闭，短时间内快速检测以确认状态
      this.currentInterval = this.fastInterval;
      setTimeout(() => {
        if (!this.currentGameStatus.isRunning) {
          this.currentInterval = this.slowInterval;
        }
      }, 5000);
    } else {
      // 游戏未运行时使用慢速检测
      this.currentInterval = this.slowInterval;
    }
    
    // 根据连续失败次数调整间隔
    if (this.consecutiveFailures > 0) {
      this.currentInterval = Math.min(
        this.currentInterval * (1 + this.consecutiveFailures * 0.5),
        10000
      );
    }
  }

  /**
   * 停止检测游戏状态
   */
  public stopDetection(): void {
    if (!this.isDetecting) {
      this.log('warn', '检测未在运行，忽略停止请求');
      return;
    }
    
    this.log('info', '停止优化游戏检测');
    
    if (this.detectionInterval) {
      clearTimeout(this.detectionInterval);
      this.detectionInterval = undefined;
    }
    
    this.isDetecting = false;
    this.logPerformanceStats();
    this.emit('detectionStopped');
  }

  /**
   * 检测游戏状态（优化版）
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

    const startTime = Date.now();
    this.lastDetectionTime = new Date();
    this.previousGameStatus = { ...this.currentGameStatus };
    this.performanceStats.totalDetections++;

    try {
      // 选择检测策略
      const strategy = this.selectDetectionStrategy();
      this.log('debug', `使用检测策略: ${strategy}`);
      
      let gameProcess: GameProcessInfo | null = null;
      let gameWindow: unknown | null = null;
      
      // 根据策略执行检测
      switch (strategy) {
        case 'cached':
          gameProcess = await this.getCachedGameProcess();
          gameWindow = await this.getCachedGameWindow();
          break;
        case 'incremental':
          gameProcess = await this.detectGameProcessIncremental();
          if (gameProcess) {
            gameWindow = await this.getGameWindow();
          }
          break;
        case 'full':
        default:
          gameProcess = await this.detectGameProcess();
          if (gameProcess) {
            gameWindow = await this.getGameWindow();
          }
          break;
      }
      
      // 处理检测结果
      if (!gameProcess) {
        this.currentProcessInfo = null;
        this.currentWindowInfo = null;
        this.currentGameStatus = { isRunning: false, isActive: false };
        this.consecutiveFailures = 0;
      } else {
        this.currentProcessInfo = gameProcess;
        
        if (!gameWindow) {
          this.currentWindowInfo = null;
          this.currentGameStatus = { isRunning: true, isActive: false, windowInfo: undefined };
        } else {
          // 获取窗口信息
          let windowInfo = null;
          try {
            const windowRect = this.getGameWindowRect(gameWindow);
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
          }
          
          const isActive = await this.isGameWindowActive();
          this.currentGameStatus = {
            isRunning: true,
            isActive: isActive,
            windowInfo,
            currentScene: 'unknown'
          };
        }
        
        this.consecutiveFailures = 0;
      }
      
      const elapsed = Date.now() - startTime;
      this.updatePerformanceStats(elapsed);
      
      this.log('debug', `优化检测完成，耗时: ${elapsed}ms, 策略: ${strategy}, 进程: ${!!gameProcess}, 窗口: ${!!gameWindow}`);
      this.checkAndEmitStatusChanges();
      
      return this.currentGameStatus;
    } catch (error) {
      this.consecutiveFailures++;
      this.log('error', '游戏状态检测失败', error);
      this.detectionErrors.push(`${new Date().toISOString()}: ${error}`);
      
      // 保留最多10个错误记录
      if (this.detectionErrors.length > 10) {
        this.detectionErrors = this.detectionErrors.slice(-10);
      }
      
      this.currentGameStatus = { isRunning: false, isActive: false };
      this.checkAndEmitStatusChanges();
      
      // 异步发射错误事件，避免阻塞
      process.nextTick(() => {
        this.emit('error', error);
      });
      
      const elapsed = Date.now() - startTime;
      this.updatePerformanceStats(elapsed, true);
      
      return this.currentGameStatus;
    }
  }

  /**
   * 选择检测策略
   */
  private selectDetectionStrategy(): 'full' | 'incremental' | 'cached' {
    // 如果连续失败次数过多，使用完整检测
    if (this.consecutiveFailures >= this.maxConsecutiveFailures) {
      return 'full';
    }
    
    // 如果有有效缓存，优先使用缓存
    if (this.hasFreshCache()) {
      return 'cached';
    }
    
    // 默认使用增量检测
    return 'incremental';
  }

  /**
   * 检查是否有新鲜的缓存
   */
  private hasFreshCache(): boolean {
    const now = Date.now();
    const hasProcessCache = (now - this.lastProcessScan) < this.processCacheTimeout && this.processCache.size > 0;
    const hasWindowCache = (now - this.lastWindowScan) < this.windowCacheTimeout && this.windowCache.size > 0;
    return hasProcessCache || hasWindowCache;
  }

  /**
   * 获取缓存的游戏进程
   */
  private async getCachedGameProcess(): Promise<GameProcessInfo | null> {
    const now = Date.now();
    if ((now - this.lastProcessScan) < this.processCacheTimeout) {
      for (const [pid, processInfo] of this.processCache) {
        // 验证进程是否仍然存在
        try {
          const processes = await psList();
          const exists = processes.some(p => p.pid === pid);
          if (exists) {
            this.performanceStats.cacheHitRate++;
            return processInfo;
          } else {
            this.processCache.delete(pid);
          }
        } catch (error) {
          this.log('warn', '验证缓存进程失败', error);
        }
      }
    }
    return null;
  }

  /**
   * 获取缓存的游戏窗口
   */
  private async getCachedGameWindow(): Promise<unknown | null> {
    const now = Date.now();
    if ((now - this.lastWindowScan) < this.windowCacheTimeout && this.windowCache.size > 0) {
      // 简单返回第一个缓存的窗口（实际应用中可能需要更复杂的逻辑）
      this.performanceStats.cacheHitRate++;
      return Array.from(this.windowCache.values())[0];
    }
    return null;
  }

  /**
   * 增量检测游戏进程
   */
  private async detectGameProcessIncremental(): Promise<GameProcessInfo | null> {
    // 如果当前有进程信息，先验证是否仍然存在
    if (this.currentProcessInfo) {
      try {
        const processes = await psList();
        const exists = processes.some(p => p.pid === this.currentProcessInfo!.pid);
        if (exists) {
          return this.currentProcessInfo;
        }
      } catch (error) {
        this.log('warn', '验证当前进程失败', error);
      }
    }
    
    // 如果当前进程不存在，执行完整检测
    return this.detectGameProcess();
  }

  /**
   * 检测游戏进程（继承原有逻辑）
   */
  private async detectGameProcess(): Promise<GameProcessInfo | null> {
    if (isBrowser || !psList) {
      return null;
    }

    try {
      const processes = await psList();
      this.lastProcessScan = Date.now();
      
      // 检查进程列表是否有效
      if (!processes || !Array.isArray(processes)) {
        this.log('warn', '进程列表无效或为空');
        return null;
      }
      
      // 清理旧缓存
      this.processCache.clear();
      
      // 优化：按优先级排序进程名
      const prioritizedProcessNames = [...this.config.gameProcessNames].sort((a, b) => {
        const priority = ['StarRail.exe', 'HonkaiStarRail.exe', '崩坏星穹铁道.exe'];
        const aIndex = priority.indexOf(a);
        const bIndex = priority.indexOf(b);
        if (aIndex !== -1 && bIndex !== -1) return aIndex - bIndex;
        if (aIndex !== -1) return -1;
        if (bIndex !== -1) return 1;
        return 0;
      });
      
      // 查找匹配的游戏进程
      for (const processName of prioritizedProcessNames) {
        const gameProcess = processes.find(p => {
          if (!p.name) return false;
          
          const name = p.name.toLowerCase();
          const targetName = processName.toLowerCase();
          
          return name === targetName || 
                 name.includes(targetName) ||
                 name.replace('.exe', '') === targetName.replace('.exe', '') ||
                 name.replace(/[\s\-_]/g, '') === targetName.replace(/[\s\-_]/g, '') ||
                 this.fuzzyMatchProcessName(name, targetName);
        });
        
        if (gameProcess) {
          const processInfo: GameProcessInfo = {
            pid: gameProcess.pid,
            name: gameProcess.name,
            cpu: gameProcess.cpu || 0,
            memory: gameProcess.memory || 0,
            ppid: gameProcess.ppid
          };
          
          // 缓存进程信息
          this.processCache.set(gameProcess.pid, processInfo);
          
          this.log('debug', `找到游戏进程: ${gameProcess.name} (PID: ${gameProcess.pid})`);
          return processInfo;
        }
      }
      
      return null;
    } catch (error) {
      this.log('error', '检测游戏进程失败', error);
      throw error;
    }
  }

  /**
   * 模糊匹配进程名
   */
  private fuzzyMatchProcessName(processName: string, targetName: string): boolean {
    const cleanProcess = processName.replace(/\.(exe|app|bin)$/i, '').toLowerCase();
    const cleanTarget = targetName.replace(/\.(exe|app|bin)$/i, '').toLowerCase();
    
    const keywords = ['starrail', 'honkai', '崩坏', '星穹', '铁道'];
    return keywords.some(keyword => 
      cleanProcess.includes(keyword) && cleanTarget.includes(keyword)
    );
  }

  /**
   * 获取游戏窗口（继承原有逻辑，添加缓存）
   */
  private async getGameWindow(): Promise<unknown | null> {
    try {
      if (!windowManager) {
        this.log('warn', 'windowManager 未初始化');
        return null;
      }
      
      const windows = windowManager.getWindows();
      if (!windows || windows.length === 0) {
        return null;
      }
      
      this.lastWindowScan = Date.now();
      this.windowCache.clear();
      
      const prioritizedTitles = [...this.config.gameWindowTitles].sort((a, b) => {
        const priority = ['崩坏：星穹铁道', 'Honkai: Star Rail', 'StarRail'];
        const aIndex = priority.indexOf(a);
        const bIndex = priority.indexOf(b);
        if (aIndex !== -1 && bIndex !== -1) return aIndex - bIndex;
        if (aIndex !== -1) return -1;
        if (bIndex !== -1) return 1;
        return 0;
      });
      
      for (const windowTitle of prioritizedTitles) {
        const gameWindow = windows.find(w => {
          try {
            if (!w || typeof w.getTitle !== 'function') return false;
            const title = w.getTitle();
            if (!title) return false;
            return this.isGameWindowTitle(title, windowTitle);
          } catch (error) {
            return false;
          }
        });
        
        if (gameWindow) {
          try {
            if (typeof gameWindow.isVisible === 'function' && gameWindow.isVisible()) {
              // 缓存窗口信息
              const windowInfo = this.getGameWindowInfo(gameWindow);
              this.windowCache.set(windowInfo.id, windowInfo);
              
              return gameWindow;
            }
          } catch (error) {
            this.log('debug', '检查窗口可见性失败', error);
          }
        }
      }
      
      return null;
    } catch (error) {
      this.log('error', '获取游戏窗口失败', error);
      return null;
    }
  }

  // 继承其他必要方法（为了简洁，这里省略了一些方法的实现）
  private isGameWindowTitle(windowTitle: string, targetTitle: string): boolean {
    if (!windowTitle || !targetTitle) return false;
    
    const title = windowTitle.toLowerCase().trim();
    const target = targetTitle.toLowerCase().trim();
    
    if (title === target) return true;
    if (title.includes(target) || target.includes(title)) return true;
    
    const cleanTitle = title.replace(/[\s\-_：:]/g, '');
    const cleanTarget = target.replace(/[\s\-_：:]/g, '');
    if (cleanTitle.includes(cleanTarget) || cleanTarget.includes(cleanTitle)) return true;
    
    const keywords = ['starrail', 'honkai', '崩坏', '星穹', '铁道'];
    const titleHasKeyword = keywords.some(keyword => title.includes(keyword));
    const targetHasKeyword = keywords.some(keyword => target.includes(keyword));
    
    return titleHasKeyword && targetHasKeyword;
  }

  private getGameWindowInfo(window: unknown): GameWindowInfo {
    const win = window as Record<string, unknown>;
    
    try {
      let bounds = { x: 0, y: 0, width: 0, height: 0 };
      if (typeof win.getBounds === 'function') {
        try {
          bounds = win.getBounds();
        } catch (error) {
          this.log('warn', '获取窗口边界失败', error);
        }
      }
      
      let title = '';
      if (typeof win.getTitle === 'function') {
        try {
          title = win.getTitle() || '';
        } catch (error) {
          this.log('warn', '获取窗口标题失败', error);
        }
      }
      
      let isVisible = false;
      if (typeof win.isVisible === 'function') {
        try {
          isVisible = win.isVisible();
        } catch (error) {
          this.log('warn', '获取窗口可见性失败', error);
        }
      }
      
      return {
        id: Number(win.id) || 0,
        title: String(title),
        bounds: {
          x: Number(bounds.x) || 0,
          y: Number(bounds.y) || 0,
          width: Number(bounds.width) || 0,
          height: Number(bounds.height) || 0
        },
        isVisible: Boolean(isVisible),
        isMinimized: !Boolean(isVisible)
      };
    } catch (error) {
      this.log('error', '获取游戏窗口信息失败', error);
      return {
        id: 0,
        title: '',
        bounds: { x: 0, y: 0, width: 0, height: 0 },
        isVisible: false,
        isMinimized: true
      };
    }
  }

  private async isGameWindowActive(): Promise<boolean> {
    try {
      if (!activeWin) {
        return false;
      }
      
      const activeWindow = await activeWin();
      if (!activeWindow || !activeWindow.title) {
        return false;
      }
      
      const isGameActive = this.config.gameWindowTitles.some(title => {
        return this.isGameWindowTitle(activeWindow.title, title);
      });
      
      if (isGameActive && this.currentProcessInfo && activeWindow.owner?.processId) {
        return activeWindow.owner.processId === this.currentProcessInfo.pid;
      }
      
      return isGameActive;
    } catch (error) {
      this.log('error', '检测活动窗口失败', error);
      return false;
    }
  }

  private getGameWindowRect(window: unknown): { x: number; y: number; width: number; height: number } {
    try {
      const windowObj = window as Record<string, unknown>;
      
      if (!windowObj || typeof windowObj.getBounds !== 'function') {
        return { x: 0, y: 0, width: 0, height: 0 };
      }
      
      const bounds = windowObj.getBounds();
      if (!bounds || typeof bounds !== 'object') {
        return { x: 0, y: 0, width: 0, height: 0 };
      }
      
      return {
        x: Number(bounds.x) || 0,
        y: Number(bounds.y) || 0,
        width: Math.max(Number(bounds.width) || 0, 0),
        height: Math.max(Number(bounds.height) || 0, 0)
      };
    } catch (error) {
      this.log('error', '获取窗口位置失败', error);
      return { x: 0, y: 0, width: 0, height: 0 };
    }
  }

  private checkAndEmitStatusChanges(): void {
    const current = this.currentGameStatus;
    const previous = this.previousGameStatus;
    
    if (!previous.isRunning && current.isRunning) {
      this.log('info', '游戏已启动');
      this.emit('gameStarted', {
        processId: this.currentProcessInfo?.pid || 0,
        windowTitle: current.windowInfo?.title || '',
        windowInfo: current.windowInfo,
        timestamp: new Date().toISOString()
      });
    }
    
    if (previous.isRunning && !current.isRunning) {
      this.log('info', '游戏已停止');
      this.emit('gameStopped', {
        lastProcessId: this.currentProcessInfo?.pid || 0,
        timestamp: new Date().toISOString()
      });
      
      this.currentProcessInfo = null;
      this.currentWindowInfo = null;
    }
    
    if (current.isRunning && !previous.isActive && current.isActive) {
      this.log('info', '游戏窗口已激活');
      this.emit('gameActivated', {
        windowTitle: current.windowInfo?.title || '',
        windowInfo: current.windowInfo,
        timestamp: new Date().toISOString()
      });
    }
    
    if (current.isRunning && previous.isActive && !current.isActive) {
      this.log('info', '游戏窗口已失活');
      this.emit('gameDeactivated', {
        windowTitle: current.windowInfo?.title || '',
        timestamp: new Date().toISOString()
      });
    }
  }

  /**
   * 清理缓存
   */
  private cleanupCaches(): void {
    const now = Date.now();
    
    // 清理过期的进程缓存
    if ((now - this.lastProcessScan) > this.processCacheTimeout) {
      this.processCache.clear();
    }
    
    // 清理过期的窗口缓存
    if ((now - this.lastWindowScan) > this.windowCacheTimeout) {
      this.windowCache.clear();
    }
  }

  /**
   * 重置性能统计
   */
  private resetPerformanceStats(): void {
    this.performanceStats = {
      totalDetections: 0,
      averageDetectionTime: 0,
      cacheHitRate: 0,
      errorRate: 0,
      lastOptimizationTime: Date.now()
    };
  }

  /**
   * 更新性能统计
   */
  private updatePerformanceStats(detectionTime: number, isError: boolean = false): void {
    const stats = this.performanceStats;
    
    // 更新平均检测时间
    stats.averageDetectionTime = (
      (stats.averageDetectionTime * (stats.totalDetections - 1) + detectionTime) / 
      stats.totalDetections
    );
    
    // 更新错误率
    if (isError) {
      stats.errorRate = (stats.errorRate * (stats.totalDetections - 1) + 1) / stats.totalDetections;
    } else {
      stats.errorRate = (stats.errorRate * (stats.totalDetections - 1)) / stats.totalDetections;
    }
    
    // 计算缓存命中率
    if (stats.totalDetections > 0) {
      stats.cacheHitRate = stats.cacheHitRate / stats.totalDetections;
    }
  }

  /**
   * 记录性能统计
   */
  private logPerformanceStats(): void {
    const stats = this.performanceStats;
    this.log('info', '性能统计', {
      totalDetections: stats.totalDetections,
      averageDetectionTime: `${stats.averageDetectionTime.toFixed(2)}ms`,
      cacheHitRate: `${(stats.cacheHitRate * 100).toFixed(2)}%`,
      errorRate: `${(stats.errorRate * 100).toFixed(2)}%`,
      runTime: `${((Date.now() - stats.lastOptimizationTime) / 1000).toFixed(2)}s`
    });
  }

  /**
   * 获取当前游戏状态
   */
  public async getCurrentStatus(): Promise<GameStatus> {
    return this.detectGameStatus();
  }

  /**
   * 获取性能统计
   */
  public getPerformanceStats() {
    return { ...this.performanceStats };
  }

  /**
   * 设置自适应模式
   */
  public setAdaptiveMode(enabled: boolean): void {
    this.adaptiveMode = enabled;
    this.log('info', `自适应检测模式: ${enabled ? '启用' : '禁用'}`);
  }

  /**
   * 设置检测策略
   */
  public setDetectionStrategy(strategy: 'full' | 'incremental' | 'cached'): void {
    this.detectionStrategy = strategy;
    this.log('info', `检测策略设置为: ${strategy}`);
  }

  /**
   * 获取检测统计信息
   */
  public getDetectionStats() {
    return {
      isRunning: this.currentGameStatus.isRunning,
      lastDetectionTime: this.lastDetectionTime,
      errorCount: this.detectionErrors.length,
      currentProcess: this.currentProcessInfo,
      currentWindow: this.currentWindowInfo,
      currentInterval: this.currentInterval,
      cacheSize: {
        processes: this.processCache.size,
        windows: this.windowCache.size
      },
      performance: this.getPerformanceStats()
    };
  }
}