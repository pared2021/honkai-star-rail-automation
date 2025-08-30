// 游戏检测模块
import { GameStatus } from '../types';
import { isBrowser } from '../utils/browserCompat';
import nodeWindowManager from 'node-window-manager';
import activeWin from 'active-win';
import psList from 'ps-list';
// 安全获取模块
const windowManager = nodeWindowManager?.windowManager;
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


  // 实时监控相关属性
  private realTimeMonitoringEnabled = false;
  private monitoringInterval: NodeJS.Timeout | null = null;
  private lastGameState = {
    isRunning: false,
    isActive: false,
    windowPosition: null as any,
    processInfo: null as any
  };
  private stateChangeCallbacks: Array<(state: any) => void> = [];

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
      
      // 优化：按优先级排序进程名，常见的放在前面
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
          
          // 多种匹配策略
          return name === targetName || 
                 name.includes(targetName) ||
                 name.replace('.exe', '') === targetName.replace('.exe', '') ||
                 name.replace(/[\s\-_]/g, '') === targetName.replace(/[\s\-_]/g, '') ||
                 this.fuzzyMatchProcessName(name, targetName);
        });
        
        if (gameProcess) {
          this.log('debug', `找到游戏进程: ${gameProcess.name} (PID: ${gameProcess.pid})`);
          const processInfo: GameProcessInfo = {
            pid: gameProcess.pid,
            name: gameProcess.name,
            cpu: gameProcess.cpu || 0,
            memory: gameProcess.memory || 0,
            ppid: gameProcess.ppid
          };
          return processInfo;
        }
      }
      
      this.log('debug', `未找到游戏进程，搜索的进程名: ${this.config.gameProcessNames.join(', ')}`);
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
    // 移除常见的后缀和前缀
    const cleanProcess = processName.replace(/\.(exe|app|bin)$/i, '').toLowerCase();
    const cleanTarget = targetName.replace(/\.(exe|app|bin)$/i, '').toLowerCase();
    
    // 检查是否包含关键词
    const keywords = ['starrail', 'honkai', '崩坏', '星穹', '铁道'];
    return keywords.some(keyword => 
      cleanProcess.includes(keyword) && cleanTarget.includes(keyword)
    );
  }

  /**
   * 获取游戏窗口
   */
  private async getGameWindow(): Promise<unknown | null> {
    try {
      if (!windowManager) {
        this.log('warn', 'windowManager 未初始化');
        return null;
      }
      
      const windows = windowManager.getWindows();
      if (!windows || windows.length === 0) {
        this.log('debug', '未检测到任何窗口');
        return null;
      }
      
      // 优化：按优先级排序窗口标题
      const prioritizedTitles = [...this.config.gameWindowTitles].sort((a, b) => {
        const priority = ['崩坏：星穹铁道', 'Honkai: Star Rail', 'StarRail'];
        const aIndex = priority.indexOf(a);
        const bIndex = priority.indexOf(b);
        if (aIndex !== -1 && bIndex !== -1) return aIndex - bIndex;
        if (aIndex !== -1) return -1;
        if (bIndex !== -1) return 1;
        return 0;
      });
      
      // 查找匹配的游戏窗口
      for (const windowTitle of prioritizedTitles) {
        const gameWindow = windows.find(w => {
          try {
            if (!w || typeof w.getTitle !== 'function') return false;
            
            const title = w.getTitle();
            if (!title) return false;
            
            return this.isGameWindowTitle(title, windowTitle);
          } catch (error) {
            // 某些窗口可能无法获取标题
            this.log('debug', '获取窗口标题失败', error);
            return false;
          }
        });
        
        if (gameWindow) {
          try {
            // 检查窗口是否可见
            if (typeof gameWindow.isVisible === 'function' && gameWindow.isVisible()) {
              const title = gameWindow.getTitle ? gameWindow.getTitle() : 'Unknown';
              const id = gameWindow.id || 'Unknown';
              this.log('debug', `找到游戏窗口: ${title} (ID: ${id})`);
              return gameWindow;
            } else {
              this.log('debug', '找到游戏窗口但不可见，继续搜索');
            }
          } catch (error) {
            this.log('debug', '检查窗口可见性失败', error);
          }
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
   * 检查窗口标题是否匹配游戏窗口
   */
  private isGameWindowTitle(windowTitle: string, targetTitle: string): boolean {
    if (!windowTitle || !targetTitle) return false;
    
    const title = windowTitle.toLowerCase().trim();
    const target = targetTitle.toLowerCase().trim();
    
    // 精确匹配
    if (title === target) return true;
    
    // 包含匹配
    if (title.includes(target) || target.includes(title)) return true;
    
    // 忽略空格和特殊字符的匹配
    const cleanTitle = title.replace(/[\s\-_：:]/g, '');
    const cleanTarget = target.replace(/[\s\-_：:]/g, '');
    if (cleanTitle.includes(cleanTarget) || cleanTarget.includes(cleanTitle)) return true;
    
    // 关键词匹配
    const keywords = ['starrail', 'honkai', '崩坏', '星穹', '铁道'];
    const titleHasKeyword = keywords.some(keyword => title.includes(keyword));
    const targetHasKeyword = keywords.some(keyword => target.includes(keyword));
    
    return titleHasKeyword && targetHasKeyword;
  }

  /**
   * 获取游戏窗口信息
   */
  private getGameWindowInfo(window: unknown): GameWindowInfo {
    const win = window as Record<string, unknown>;
    
    try {
      // 安全获取窗口边界
      let bounds = { x: 0, y: 0, width: 0, height: 0 };
      if (typeof win.getBounds === 'function') {
        try {
          bounds = win.getBounds();
        } catch (error) {
          this.log('warn', '获取窗口边界失败', error);
        }
      }
      
      // 安全获取窗口标题
      let title = '';
      if (typeof win.getTitle === 'function') {
        try {
          title = win.getTitle() || '';
        } catch (error) {
          this.log('warn', '获取窗口标题失败', error);
        }
      }
      
      // 安全获取可见性状态
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

  /**
   * 检测游戏窗口是否处于活动状态
   */
  private async isGameWindowActive(): Promise<boolean> {
    try {
      if (!activeWin) {
        this.log('warn', 'activeWin 模块未可用');
        return false;
      }
      
      const activeWindow = await activeWin();
      
      if (!activeWindow || !activeWindow.title) {
        this.log('debug', '未检测到活动窗口或窗口无标题');
        return false;
      }
      
      // 检查活动窗口是否为游戏窗口
      const isGameActive = this.config.gameWindowTitles.some(title => {
        return this.isGameWindowTitle(activeWindow.title, title);
      });
      
      if (isGameActive) {
        this.log('debug', `游戏窗口处于活动状态: ${activeWindow.title} (PID: ${activeWindow.owner?.processId || 'Unknown'})`);
        
        // 额外验证：检查进程ID是否匹配
        if (this.currentProcessInfo && activeWindow.owner?.processId) {
          const pidMatch = activeWindow.owner.processId === this.currentProcessInfo.pid;
          if (!pidMatch) {
            this.log('debug', `窗口标题匹配但进程ID不匹配: 活动窗口PID=${activeWindow.owner.processId}, 游戏进程PID=${this.currentProcessInfo.pid}`);
          }
          return pidMatch;
        }
      } else {
        this.log('debug', `当前活动窗口不是游戏窗口: ${activeWindow.title}`);
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
      
      if (!windowObj || typeof windowObj.getBounds !== 'function') {
        this.log('warn', '窗口对象无效或不支持getBounds方法');
        return { x: 0, y: 0, width: 0, height: 0 };
      }
      
      const bounds = windowObj.getBounds();
      
      if (!bounds || typeof bounds !== 'object') {
        this.log('warn', '获取到的窗口边界信息无效');
        return { x: 0, y: 0, width: 0, height: 0 };
      }
      
      // 验证和规范化边界值
      const rect = {
        x: Number(bounds.x) || 0,
        y: Number(bounds.y) || 0,
        width: Math.max(Number(bounds.width) || 0, 0),
        height: Math.max(Number(bounds.height) || 0, 0)
      };
      
      // 检查边界值的合理性
      if (rect.width > 10000 || rect.height > 10000) {
        this.log('warn', '窗口尺寸异常大，可能存在问题', rect);
      }
      
      if (rect.x < -10000 || rect.x > 10000 || rect.y < -10000 || rect.y > 10000) {
        this.log('warn', '窗口位置异常，可能存在问题', rect);
      }
      
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
   * 获取游戏窗口句柄
   */
  public async getGameWindowHandle(): Promise<string | null> {
    try {
      const window = await this.getGameWindow();
      if (!window) {
        this.log('debug', '未找到游戏窗口，无法获取句柄');
        return null;
      }

      const windowObj = window as Record<string, unknown>;
      
      // 尝试获取窗口句柄（不同平台可能有不同的属性名）
      const handle = windowObj.handle || windowObj.id || windowObj.hwnd || windowObj.windowId;
      
      if (handle) {
        const handleStr = String(handle);
        this.log('debug', `获取到游戏窗口句柄: ${handleStr}`);
        return handleStr;
      } else {
        this.log('warn', '无法从窗口对象获取句柄');
        return null;
      }
    } catch (error) {
      this.log('error', '获取游戏窗口句柄失败', error);
      return null;
    }
  }

  /**
   * 获取游戏窗口详细位置信息
   */
  public async getGameWindowPosition(): Promise<{
    handle: string | null;
    bounds: { x: number; y: number; width: number; height: number };
    isVisible: boolean;
    isActive: boolean;
  } | null> {
    try {
      const window = await this.getGameWindow();
      if (!window) {
        this.log('debug', '未找到游戏窗口，无法获取位置信息');
        return null;
      }

      const handle = await this.getGameWindowHandle();
      const bounds = this.getGameWindowRect(window);
      const windowInfo = this.getGameWindowInfo(window);
      const isActive = await this.isGameWindowActive();

      const position = {
        handle,
        bounds,
        isVisible: windowInfo.isVisible,
        isActive
      };

      this.log('debug', '获取游戏窗口位置信息', position);
      return position;
    } catch (error) {
      this.log('error', '获取游戏窗口位置信息失败', error);
      return null;
    }
  }

  /**
   * 检查游戏窗口是否在指定区域内
   */
  public async isGameWindowInRegion(region: { x: number; y: number; width: number; height: number }): Promise<boolean> {
    try {
      const position = await this.getGameWindowPosition();
      if (!position) {
        return false;
      }

      const { bounds } = position;
      
      // 检查窗口是否与指定区域有重叠
      const overlap = (
        bounds.x < region.x + region.width &&
        bounds.x + bounds.width > region.x &&
        bounds.y < region.y + region.height &&
        bounds.y + bounds.height > region.y
      );

      this.log('debug', `游戏窗口区域检查: 窗口(${bounds.x},${bounds.y},${bounds.width},${bounds.height}) 区域(${region.x},${region.y},${region.width},${region.height}) 重叠:${overlap}`);
      return overlap;
    } catch (error) {
      this.log('error', '检查游戏窗口区域失败', error);
      return false;
    }
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

  /**
   * 启用实时监控
   */
  public enableRealTimeMonitoring(interval: number = 2000): void {
    if (this.realTimeMonitoringEnabled) {
      this.log('warn', '实时监控已经启用');
      return;
    }

    this.realTimeMonitoringEnabled = true;
    this.monitoringInterval = setInterval(async () => {
      await this.performRealTimeCheck();
    }, interval);

    this.log('info', `实时监控已启用，检查间隔: ${interval}ms`);
  }

  /**
   * 禁用实时监控
   */
  public disableRealTimeMonitoring(): void {
    if (!this.realTimeMonitoringEnabled) {
      this.log('warn', '实时监控未启用');
      return;
    }

    this.realTimeMonitoringEnabled = false;
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }

    this.log('info', '实时监控已禁用');
  }

  /**
   * 执行实时检查
   */
  private async performRealTimeCheck(): Promise<void> {
    try {
      const currentState = {
        isRunning: false,
        isActive: false,
        windowPosition: null as any,
        processInfo: null as any
      };

      // 检查游戏进程
      const processInfo = await this.detectGameProcess();
      currentState.processInfo = processInfo;
      currentState.isRunning = !!processInfo;

      // 检查游戏窗口状态
      if (processInfo) {
        currentState.isActive = await this.isGameWindowActive();
        currentState.windowPosition = await this.getGameWindowPosition();
      }

      // 检查状态变化
      this.checkStateChanges(currentState);

      // 更新最后状态
      this.lastGameState = currentState;

    } catch (error) {
      this.log('error', '实时监控检查失败', error);
    }
  }

  /**
   * 检查状态变化并触发事件
   */
  private checkStateChanges(currentState: any): void {
    // 游戏启动检测
    if (!this.lastGameState.isRunning && currentState.isRunning) {
      this.log('info', '检测到游戏启动');
      this.emit('gameStarted', currentState.processInfo);
      this.notifyStateChange('gameStarted', currentState);
    }

    // 游戏关闭检测
    if (this.lastGameState.isRunning && !currentState.isRunning) {
      this.log('info', '检测到游戏关闭');
      this.emit('gameStopped');
      this.notifyStateChange('gameStopped', currentState);
    }

    // 游戏激活状态变化
    if (this.lastGameState.isActive !== currentState.isActive) {
      if (currentState.isActive) {
        this.log('info', '游戏窗口变为活动状态');
        this.emit('gameActivated');
        this.notifyStateChange('gameActivated', currentState);
      } else {
        this.log('info', '游戏窗口失去活动状态');
        this.emit('gameDeactivated');
        this.notifyStateChange('gameDeactivated', currentState);
      }
    }

    // 窗口位置变化检测
    if (this.hasWindowPositionChanged(this.lastGameState.windowPosition, currentState.windowPosition)) {
      this.log('debug', '游戏窗口位置发生变化');
      this.emit('windowPositionChanged', currentState.windowPosition);
      this.notifyStateChange('windowPositionChanged', currentState);
    }
  }

  /**
   * 检查窗口位置是否发生变化
   */
  private hasWindowPositionChanged(oldPos: any, newPos: any): boolean {
    if (!oldPos && !newPos) return false;
    if (!oldPos || !newPos) return true;

    const oldBounds = oldPos.bounds;
    const newBounds = newPos.bounds;

    return (
      oldBounds.x !== newBounds.x ||
      oldBounds.y !== newBounds.y ||
      oldBounds.width !== newBounds.width ||
      oldBounds.height !== newBounds.height
    );
  }

  /**
   * 添加状态变化回调
   */
  public onStateChange(callback: (state: any) => void): void {
    this.stateChangeCallbacks.push(callback);
  }

  /**
   * 移除状态变化回调
   */
  public removeStateChangeCallback(callback: (state: any) => void): void {
    const index = this.stateChangeCallbacks.indexOf(callback);
    if (index > -1) {
      this.stateChangeCallbacks.splice(index, 1);
    }
  }

  /**
   * 通知状态变化
   */
  private notifyStateChange(eventType: string, state: any): void {
    this.stateChangeCallbacks.forEach(callback => {
      try {
        callback({ eventType, state, timestamp: new Date() });
      } catch (error) {
        this.log('error', '状态变化回调执行失败', error);
      }
    });
  }

  /**
   * 获取当前游戏状态
   */
  public getCurrentGameState(): any {
    return { ...this.lastGameState };
  }

  /**
   * 检查实时监控是否启用
   */
  public isRealTimeMonitoringEnabled(): boolean {
    return this.realTimeMonitoringEnabled;
  }
}

export default GameDetector;