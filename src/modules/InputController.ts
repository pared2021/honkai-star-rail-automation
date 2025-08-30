import { isBrowser } from '../utils/browserCompat.js';
import robot from 'robotjs';

// 输入控制模块 - 鼠标键盘操作
export interface ClickOptions {
  button?: 'left' | 'right' | 'middle';
  double?: boolean;
  delay?: number;
}

export interface KeyOptions {
  modifiers?: string[];
  delay?: number;
}

export interface MousePosition {
  x: number;
  y: number;
}

export interface GameWindow {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface InputLog {
  timestamp: number;
  action: string;
  coordinates?: MousePosition;
  key?: string;
  success: boolean;
  error?: string;
}

// 新增接口定义
export interface SmoothMoveOptions {
  duration?: number;
  easing?: 'linear' | 'easeInOut' | 'easeIn' | 'easeOut' | 'bezier';
  steps?: number;
  bezierControlPoints?: { cp1: MousePosition; cp2: MousePosition };
}

export interface QueuedAction {
  id: string;
  type: 'click' | 'move' | 'key' | 'type' | 'drag' | 'scroll' | 'smoothMove';
  params: any;
  priority: 'high' | 'medium' | 'low';
  timestamp: number;
  retries?: number;
  maxRetries?: number;
}

export interface RecordedAction {
  timestamp: number;
  type: string;
  params: any;
  duration?: number;
}

export interface InputStats {
  totalActions: number;
  successfulActions: number;
  failedActions: number;
  averageResponseTime: number;
  queueSize: number;
  recordingActive: boolean;
}

export class InputController {
  private isEnabled = true;
  private defaultDelay = 100; // 默认操作延迟
  private gameWindow: GameWindow | null = null;
  private inputLogs: InputLog[] = [];
  private maxLogEntries = 1000;
  private safetyChecks = true;
  private lastActionTime = 0;
  private minActionInterval = 10; // 最小操作间隔(ms)
  
  // 操作队列相关
  private actionQueue: QueuedAction[] = [];
  private isQueueExecuting = false;
  private queuePaused = false;
  private queueExecutionPromise: Promise<void> | null = null;
  
  // 录制回放相关
  private isRecording = false;
  private recordedActions: RecordedAction[] = [];
  private recordingStartTime = 0;
  
  // 统计信息
  private stats: InputStats = {
    totalActions: 0,
    successfulActions: 0,
    failedActions: 0,
    averageResponseTime: 0,
    queueSize: 0,
    recordingActive: false
  };
  
  // 性能监控
  private actionTimes: number[] = [];
  private emergencyStopFlag = false;

  constructor() {
    // 浏览器环境中直接返回
    if (isBrowser || !robot) {
      return;
    }

    // 设置robotjs的延迟和速度
    robot.setMouseDelay(2);
    robot.setKeyboardDelay(10);
    
    // 初始化日志清理定时器（测试环境中不启动）
    if (process.env.NODE_ENV !== 'test') {
      setInterval(() => this.cleanupLogs(), 60000); // 每分钟清理一次日志
    }
  }

  /**
   * 启用/禁用输入控制
   */
  public setEnabled(enabled: boolean): void {
    this.isEnabled = enabled;
  }

  /**
   * 检查是否启用
   */
  public isInputEnabled(): boolean {
    return this.isEnabled;
  }

  /**
   * 点击指定位置
   */
  public async click(x: number, y: number, options: ClickOptions = {}): Promise<boolean> {
    if (!this.isEnabled) {
      this.logAction('click', { x, y }, false, '输入控制已禁用');
      return false;
    }

    if (!this.performSafetyCheck()) {
      this.logAction('click', { x, y }, false, '安全检查失败');
      return false;
    }

    try {
      const {
        button = 'left',
        double = false,
        delay = this.defaultDelay
      } = options;

      // 转换坐标（如果设置了游戏窗口）
      const screenCoords = this.gameToScreenCoords(x, y);
      
      // 移动鼠标到目标位置
      robot.moveMouse(screenCoords.x, screenCoords.y);
      
      // 等待一小段时间确保鼠标移动完成
      await this.delay(50);
      
      // 执行点击
      if (double) {
        robot.mouseClick(button, true);
      } else {
        robot.mouseClick(button, false);
      }
      
      this.logAction('click', screenCoords, true, `${button}${double ? ' double' : ''} click`);
      await this.delay(delay);
      return true;
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      this.logAction('click', { x, y }, false, errorMsg);
      console.error('鼠标点击失败:', error);
      return false;
    }
  }

  /**
   * 移动鼠标到指定位置
   */
  public async moveMouse(x: number, y: number): Promise<boolean> {
    if (!this.isEnabled) {
      this.logAction('moveMouse', { x, y }, false, '输入控制已禁用');
      return false;
    }

    if (!this.performSafetyCheck()) {
      this.logAction('moveMouse', { x, y }, false, '安全检查失败');
      return false;
    }

    try {
      // 转换坐标（如果设置了游戏窗口）
      const screenCoords = this.gameToScreenCoords(x, y);
      
      robot.moveMouse(screenCoords.x, screenCoords.y);
      
      this.logAction('moveMouse', screenCoords, true, `move to (${screenCoords.x}, ${screenCoords.y})`);
      await this.delay(50);
      return true;
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      this.logAction('moveMouse', { x, y }, false, errorMsg);
      console.error('鼠标移动失败:', error);
      return false;
    }
  }

  /**
   * 按下指定按键
   */
  public async pressKey(key: string, options: KeyOptions = {}): Promise<boolean> {
    if (!this.isEnabled) {
      this.logAction('pressKey', undefined, false, '输入控制已禁用');
      return false;
    }

    if (!this.performSafetyCheck()) {
      this.logAction('pressKey', undefined, false, '安全检查失败');
      return false;
    }

    try {
      const {
        modifiers = [],
        delay = this.defaultDelay
      } = options;

      // 验证按键名称
      if (!this.isValidKey(key)) {
        throw new Error(`无效的按键名称: ${key}`);
      }

      // 执行按键
      if (modifiers.length > 0) {
        robot.keyTap(key, modifiers);
      } else {
        robot.keyTap(key);
      }
      
      const keyDesc = modifiers.length > 0 ? `${modifiers.join('+')}+${key}` : key;
      this.logAction('pressKey', undefined, true, keyDesc);
      await this.delay(delay);
      return true;
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      this.logAction('pressKey', undefined, false, errorMsg);
      console.error('键盘按键失败:', error);
      return false;
    }
  }

  /**
   * 输入文本
   */
  public async typeText(text: string, delay: number = 50): Promise<void> {
    if (!this.isEnabled) {
      this.logAction('typeText', undefined, false, '输入控制已禁用');
      return;
    }

    if (!this.performSafetyCheck()) {
      this.logAction('typeText', undefined, false, '安全检查失败');
      return;
    }

    try {
      // 验证文本长度
      if (text.length > 1000) {
        throw new Error('文本长度超过限制(1000字符)');
      }

      // 输入文本
      robot.typeString(text);
      
      this.logAction('typeText', undefined, true, `typed: "${text.substring(0, 50)}${text.length > 50 ? '...' : ''}"`);
      await this.delay(delay * text.length);
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      this.logAction('typeText', undefined, false, errorMsg);
      console.error('文本输入失败:', error);
      throw error;
    }
  }

  /**
   * 鼠标拖拽
   */
  public async drag(fromX: number, fromY: number, toX: number, toY: number): Promise<void> {
    if (!this.isEnabled) {
      this.logAction('drag', { x: fromX, y: fromY }, false, '输入控制已禁用');
      return;
    }

    if (!this.performSafetyCheck()) {
      this.logAction('drag', { x: fromX, y: fromY }, false, '安全检查失败');
      return;
    }

    try {
      // 转换坐标
      const fromCoords = this.gameToScreenCoords(fromX, fromY);
      const toCoords = this.gameToScreenCoords(toX, toY);
      
      // 移动到起始位置
      robot.moveMouse(fromCoords.x, fromCoords.y);
      await this.delay(50);
      
      // 按下鼠标
      robot.mouseToggle('down');
      await this.delay(100);
      
      // 拖拽到目标位置
      robot.moveMouse(toCoords.x, toCoords.y);
      await this.delay(100);
      
      // 释放鼠标
      robot.mouseToggle('up');
      
      this.logAction('drag', fromCoords, true, `drag from (${fromCoords.x}, ${fromCoords.y}) to (${toCoords.x}, ${toCoords.y})`);
      await this.delay(200);
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      this.logAction('drag', { x: fromX, y: fromY }, false, errorMsg);
      console.error('鼠标拖拽失败:', error);
      throw error;
    }
  }

  /**
   * 滚轮滚动
   */
  public async scroll(x: number, y: number, direction: 'up' | 'down', clicks: number = 3): Promise<void> {
    if (!this.isEnabled) {
      this.logAction('scroll', { x, y }, false, '输入控制已禁用');
      return;
    }

    if (!this.performSafetyCheck()) {
      this.logAction('scroll', { x, y }, false, '安全检查失败');
      return;
    }

    try {
      // 转换坐标
      const screenCoords = this.gameToScreenCoords(x, y);
      
      // 移动鼠标到滚动位置
      robot.moveMouse(screenCoords.x, screenCoords.y);
      await this.delay(50);
      
      // 执行滚动
      robot.scrollMouse(direction === 'up' ? clicks : -clicks, 0);
      
      this.logAction('scroll', screenCoords, true, `scroll ${direction} ${clicks} clicks at (${screenCoords.x}, ${screenCoords.y})`);
      await this.delay(100);
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      this.logAction('scroll', { x, y }, false, errorMsg);
      console.error('滚轮滚动失败:', error);
      throw error;
    }
  }

  /**
   * 获取当前鼠标位置
   */
  public getCurrentMousePosition(): MousePosition {
    try {
      const pos = robot.getMousePos();
      return { x: pos.x, y: pos.y };
    } catch (error) {
      console.error('获取鼠标位置失败:', error);
      return { x: 0, y: 0 };
    }
  }

  /**
   * 获取当前鼠标位置（游戏坐标）
   */
  public getCurrentMousePositionInGame(): MousePosition {
    try {
      const screenPos = this.getCurrentMousePosition();
      return this.screenToGameCoords(screenPos.x, screenPos.y);
    } catch (error) {
      console.error('获取游戏内鼠标位置失败:', error);
      return { x: 0, y: 0 };
    }
  }

  /**
   * 平滑移动鼠标到指定位置（公共API）
   */
  public async smoothMoveTo(x: number, y: number, options: SmoothMoveOptions = {}): Promise<boolean> {
    if (!this.isEnabled) {
      this.logAction('smoothMoveTo', { x, y }, false, '输入控制已禁用');
      return false;
    }

    if (!this.performSafetyCheck()) {
      this.logAction('smoothMoveTo', { x, y }, false, '安全检查失败');
      return false;
    }

    if (this.emergencyStopFlag) {
      this.logAction('smoothMoveTo', { x, y }, false, '紧急停止已激活');
      return false;
    }

    try {
      const startTime = Date.now();
      const from = this.getCurrentMousePosition();
      const to = this.gameToScreenCoords(x, y);
      
      // 边界检查
      if (!this.isCoordinateInGameWindow(x, y)) {
        const clampedCoords = this.clampToGameWindow(x, y);
        this.logAction('smoothMoveTo', { x, y }, false, `坐标超出游戏窗口边界，已调整为 (${clampedCoords.x}, ${clampedCoords.y})`);
        return await this.smoothMoveTo(clampedCoords.x, clampedCoords.y, options);
      }

      await this.performSmoothMove(from, to, options);
      
      const duration = Date.now() - startTime;
      this.updateStats(true, duration);
      this.logAction('smoothMoveTo', to, true, `smooth move to (${to.x}, ${to.y}) in ${duration}ms`);
      
      // 录制操作
      if (this.isRecording) {
        this.recordAction('smoothMoveTo', { x, y, options }, duration);
      }
      
      return true;
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      this.updateStats(false);
      this.logAction('smoothMoveTo', { x, y }, false, errorMsg);
      console.error('平滑移动失败:', error);
      return false;
    }
  }

  /**
   * 执行平滑移动的核心逻辑
   */
  private async performSmoothMove(from: MousePosition, to: MousePosition, options: SmoothMoveOptions): Promise<void> {
    const {
      duration = 500,
      easing = 'easeInOut',
      steps = Math.max(10, Math.min(50, Math.floor(duration / 10))),
      bezierControlPoints
    } = options;

    const stepDelay = duration / steps;
    
    for (let i = 0; i <= steps; i++) {
      if (this.emergencyStopFlag) {
        throw new Error('操作被紧急停止');
      }
      
      const progress = i / steps;
      let easedProgress: number;
      
      // 根据缓动类型计算位置
      switch (easing) {
        case 'linear':
          easedProgress = progress;
          break;
        case 'easeIn':
          easedProgress = progress * progress;
          break;
        case 'easeOut':
          easedProgress = 1 - (1 - progress) * (1 - progress);
          break;
        case 'easeInOut':
          easedProgress = progress < 0.5 
            ? 2 * progress * progress 
            : 1 - Math.pow(-2 * progress + 2, 2) / 2;
          break;
        case 'bezier':
          if (bezierControlPoints) {
            easedProgress = this.calculateBezierProgress(progress, from, to, bezierControlPoints);
          } else {
            easedProgress = progress; // 回退到线性
          }
          break;
        default:
          easedProgress = progress;
      }
      
      let x: number, y: number;
      
      if (easing === 'bezier' && bezierControlPoints) {
        const point = this.calculateBezierPoint(progress, from, to, bezierControlPoints);
        x = Math.round(point.x);
        y = Math.round(point.y);
      } else {
        x = Math.round(from.x + (to.x - from.x) * easedProgress);
        y = Math.round(from.y + (to.y - from.y) * easedProgress);
      }
      
      robot.moveMouse(x, y);
      await this.delay(stepDelay);
    }
  }

  /**
   * 计算贝塞尔曲线上的点
   */
  private calculateBezierPoint(t: number, p0: MousePosition, p3: MousePosition, controlPoints: { cp1: MousePosition; cp2: MousePosition }): MousePosition {
    const { cp1, cp2 } = controlPoints;
    const u = 1 - t;
    const tt = t * t;
    const uu = u * u;
    const uuu = uu * u;
    const ttt = tt * t;
    
    const x = uuu * p0.x + 3 * uu * t * cp1.x + 3 * u * tt * cp2.x + ttt * p3.x;
    const y = uuu * p0.y + 3 * uu * t * cp1.y + 3 * u * tt * cp2.y + ttt * p3.y;
    
    return { x, y };
  }

  /**
   * 计算贝塞尔曲线的进度（用于非贝塞尔缓动函数）
   */
  private calculateBezierProgress(t: number, from: MousePosition, to: MousePosition, controlPoints: { cp1: MousePosition; cp2: MousePosition }): number {
    // 这里简化处理，实际应该根据贝塞尔曲线的长度来计算
    return t;
  }

  /**
   * 延迟函数
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 设置默认延迟
   */
  public setDefaultDelay(delay: number): void {
    this.defaultDelay = delay;
  }

  /**
   * 获取默认延迟
   */
  public getDefaultDelay(): number {
    return this.defaultDelay;
  }

  /**
   * 设置游戏窗口信息
   */
  public setGameWindow(window: GameWindow): void {
    this.gameWindow = window;
  }

  /**
   * 获取游戏窗口信息
   */
  public getGameWindow(): GameWindow | null {
    return this.gameWindow;
  }

  /**
   * 设置安全检查开关
   */
  public setSafetyChecks(enabled: boolean): void {
    this.safetyChecks = enabled;
  }

  /**
   * 游戏坐标转屏幕坐标
   */
  private gameToScreenCoords(gameX: number, gameY: number): MousePosition {
    if (!this.gameWindow) {
      return { x: gameX, y: gameY };
    }
    
    return {
      x: this.gameWindow.x + gameX,
      y: this.gameWindow.y + gameY
    };
  }

  /**
   * 屏幕坐标转游戏坐标
   */
  private screenToGameCoords(screenX: number, screenY: number): MousePosition {
    if (!this.gameWindow) {
      return { x: screenX, y: screenY };
    }
    
    return {
      x: screenX - this.gameWindow.x,
      y: screenY - this.gameWindow.y
    };
  }

  /**
   * 执行安全检查
   */
  private performSafetyCheck(): boolean {
    if (!this.safetyChecks) {
      return true;
    }

    const now = Date.now();
    if (now - this.lastActionTime < this.minActionInterval) {
      return false;
    }

    this.lastActionTime = now;
    return true;
  }

  /**
   * 验证按键名称
   */
  private isValidKey(key: string): boolean {
    const validKeys = [
      'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
      'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
      '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
      'space', 'enter', 'escape', 'tab', 'backspace', 'delete',
      'up', 'down', 'left', 'right',
      'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
      'shift', 'control', 'alt', 'command'
    ];
    
    return validKeys.includes(key.toLowerCase());
  }

  /**
   * 记录操作日志
   */
  private logAction(action: string, coordinates?: MousePosition, success: boolean = true, details?: string): void {
    const log: InputLog = {
      timestamp: Date.now(),
      action,
      coordinates,
      success,
      ...(details && { error: success ? undefined : details })
    };

    if (details && success) {
      log.key = details;
    }

    this.inputLogs.push(log);
    
    // 限制日志数量
    if (this.inputLogs.length > this.maxLogEntries) {
      this.inputLogs = this.inputLogs.slice(-this.maxLogEntries);
    }
  }

  /**
   * 获取操作日志
   */
  public getInputLogs(limit?: number): InputLog[] {
    if (limit) {
      return this.inputLogs.slice(-limit);
    }
    return [...this.inputLogs];
  }

  /**
   * 清理日志
   */
  private cleanupLogs(): void {
    const oneHourAgo = Date.now() - 60 * 60 * 1000;
    this.inputLogs = this.inputLogs.filter(log => log.timestamp > oneHourAgo);
  }

  /**
   * 清空所有日志
   */
  public clearLogs(): void {
    this.inputLogs = [];
  }

  /**
   * 获取统计信息
   */
  public getStats(): { total: number; success: number; failed: number; successRate: number } {
    const total = this.inputLogs.length;
    const success = this.inputLogs.filter(log => log.success).length;
    const failed = total - success;
    const successRate = total > 0 ? (success / total) * 100 : 0;
    
    return { total, success, failed, successRate };
  }

  /**
   * 组合键操作
   */
  public async keyCombo(keys: string[], holdTime: number = 100): Promise<boolean> {
    if (!this.isEnabled) {
      this.logAction('keyCombo', undefined, false, '输入控制已禁用');
      return false;
    }

    if (!this.performSafetyCheck()) {
      this.logAction('keyCombo', undefined, false, '安全检查失败');
      return false;
    }

    try {
      // 验证所有按键
      for (const key of keys) {
        if (!this.isValidKey(key)) {
          this.logAction('keyCombo', undefined, false, `无效按键: ${key}`);
          return false;
        }
      }

      // 按下所有按键
      for (const key of keys) {
        robot.keyToggle(key, 'down');
        await this.delay(10);
      }

      // 保持按键
      await this.delay(holdTime);

      // 释放所有按键（逆序）
      for (let i = keys.length - 1; i >= 0; i--) {
        robot.keyToggle(keys[i], 'up');
        await this.delay(10);
      }

      this.logAction('keyCombo', undefined, true, `combo: ${keys.join('+')}`);
      await this.delay(this.defaultDelay);
      return true;
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      this.logAction('keyCombo', undefined, false, errorMsg);
      console.error('组合键操作失败:', error);
      return false;
    }
  }

  /**
   * 双击操作
   */
  public async doubleClick(x: number, y: number, button: 'left' | 'right' = 'left'): Promise<boolean> {
    if (!this.isEnabled) {
      this.logAction('doubleClick', { x, y }, false, '输入控制已禁用');
      return false;
    }

    if (!this.performSafetyCheck()) {
      this.logAction('doubleClick', { x, y }, false, '安全检查失败');
      return false;
    }

    try {
      const screenCoords = this.gameToScreenCoords(x, y);
      
      // 移动到目标位置
      robot.moveMouse(screenCoords.x, screenCoords.y);
      await this.delay(50);
      
      // 执行双击
      robot.mouseClick(button, true); // 双击
      
      this.logAction('doubleClick', screenCoords, true, `${button} double click`);
      await this.delay(this.defaultDelay);
      return true;
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      this.logAction('doubleClick', { x, y }, false, errorMsg);
      console.error('双击操作失败:', error);
      return false;
    }
  }

  /**
   * 右键点击
   */
  public async rightClick(x: number, y: number): Promise<boolean> {
    return this.click(x, y, { button: 'right' });
  }

  /**
   * 中键点击
   */
  public async middleClick(x: number, y: number): Promise<boolean> {
    return this.click(x, y, { button: 'middle' });
  }

  /**
   * 获取配置信息
   */
  public getConfig(): {
    isEnabled: boolean;
    defaultDelay: number;
    safetyChecks: boolean;
    minActionInterval: number;
    gameWindow: GameWindow | null;
  } {
    return {
      isEnabled: this.isEnabled,
      defaultDelay: this.defaultDelay,
      safetyChecks: this.safetyChecks,
      minActionInterval: this.minActionInterval,
      gameWindow: this.gameWindow
    };
  }

  // ==================== 新增功能方法 ====================

  /**
   * 检查坐标是否在游戏窗口内
   */
  private isCoordinateInGameWindow(x: number, y: number): boolean {
    if (!this.gameWindow) {
      return true; // 如果没有设置游戏窗口，则认为所有坐标都有效
    }
    
    return x >= this.gameWindow.x && 
           x <= this.gameWindow.x + this.gameWindow.width &&
           y >= this.gameWindow.y && 
           y <= this.gameWindow.y + this.gameWindow.height;
  }

  /**
   * 将坐标限制在游戏窗口内
   */
  private clampToGameWindow(x: number, y: number): { x: number; y: number } {
    if (!this.gameWindow) {
      return { x, y };
    }
    
    const clampedX = Math.max(
      this.gameWindow.x,
      Math.min(x, this.gameWindow.x + this.gameWindow.width)
    );
    
    const clampedY = Math.max(
      this.gameWindow.y,
      Math.min(y, this.gameWindow.y + this.gameWindow.height)
    );
    
    return { x: clampedX, y: clampedY };
  }

  /**
   * 验证游戏窗口配置的有效性
   */
  public validateGameWindow(window?: GameWindow): {
    isValid: boolean;
    errors: string[];
    warnings: string[];
  } {
    const targetWindow = window || this.gameWindow;
    const errors: string[] = [];
    const warnings: string[] = [];
    
    if (!targetWindow) {
      warnings.push('未设置游戏窗口，将使用全屏坐标');
      return { isValid: true, errors, warnings };
    }
    
    // 检查基本属性
    if (typeof targetWindow.x !== 'number' || isNaN(targetWindow.x)) {
      errors.push('游戏窗口X坐标无效');
    }
    
    if (typeof targetWindow.y !== 'number' || isNaN(targetWindow.y)) {
      errors.push('游戏窗口Y坐标无效');
    }
    
    if (typeof targetWindow.width !== 'number' || isNaN(targetWindow.width) || targetWindow.width <= 0) {
      errors.push('游戏窗口宽度无效');
    }
    
    if (typeof targetWindow.height !== 'number' || isNaN(targetWindow.height) || targetWindow.height <= 0) {
      errors.push('游戏窗口高度无效');
    }
    
    // 检查坐标范围
    if (targetWindow.x < 0) {
      warnings.push('游戏窗口X坐标为负数，可能超出屏幕范围');
    }
    
    if (targetWindow.y < 0) {
      warnings.push('游戏窗口Y坐标为负数，可能超出屏幕范围');
    }
    
    // 检查窗口大小合理性
    if (targetWindow.width > 0 && targetWindow.width < 100) {
      warnings.push('游戏窗口宽度过小，可能影响操作精度');
    }
    
    if (targetWindow.height > 0 && targetWindow.height < 100) {
      warnings.push('游戏窗口高度过小，可能影响操作精度');
    }
    
    if (targetWindow.width > 4000) {
      warnings.push('游戏窗口宽度过大，请确认是否正确');
    }
    
    if (targetWindow.height > 4000) {
      warnings.push('游戏窗口高度过大，请确认是否正确');
    }
    
    // 检查窗口是否在合理的屏幕范围内
    const maxX = targetWindow.x + targetWindow.width;
    const maxY = targetWindow.y + targetWindow.height;
    
    if (maxX > 8000) {
      warnings.push('游戏窗口右边界超出常见屏幕范围');
    }
    
    if (maxY > 8000) {
      warnings.push('游戏窗口下边界超出常见屏幕范围');
    }
    
    const isValid = errors.length === 0;
    
    if (!isValid) {
      console.error('游戏窗口验证失败:', errors);
    }
    
    if (warnings.length > 0) {
      console.warn('游戏窗口验证警告:', warnings);
    }
    
    return { isValid, errors, warnings };
  }

  /**
   * 获取游戏窗口的详细信息
   */
  public getGameWindowInfo(): {
    window: GameWindow | null;
    validation: ReturnType<typeof this.validateGameWindow>;
    area: number;
    aspectRatio: number;
  } {
    const validation = this.validateGameWindow();
    const area = this.gameWindow ? this.gameWindow.width * this.gameWindow.height : 0;
    const aspectRatio = this.gameWindow ? this.gameWindow.width / this.gameWindow.height : 0;
    
    return {
      window: this.gameWindow,
      validation,
      area,
      aspectRatio
    };
  }

  /**
   * 检查坐标是否在游戏窗口的安全区域内（带边距）
   */
  public isCoordinateInSafeArea(x: number, y: number, margin: number = 10): boolean {
    if (!this.gameWindow) {
      return true;
    }
    
    return x >= this.gameWindow.x + margin && 
           x <= this.gameWindow.x + this.gameWindow.width - margin &&
           y >= this.gameWindow.y + margin && 
           y <= this.gameWindow.y + this.gameWindow.height - margin;
  }

  /**
   * 获取游戏窗口的中心点坐标
   */
  public getGameWindowCenter(): { x: number; y: number } | null {
    if (!this.gameWindow) {
      return null;
    }
    
    return {
      x: this.gameWindow.x + this.gameWindow.width / 2,
      y: this.gameWindow.y + this.gameWindow.height / 2
    };
  }

  /**
   * 更新统计信息
   */
  private updateStats(success: boolean, duration?: number): void {
    this.stats.totalActions++;
    if (success) {
      this.stats.successfulActions++;
    } else {
      this.stats.failedActions++;
    }
    
    if (duration !== undefined) {
      this.actionTimes.push(duration);
      // 保持最近100次操作的时间记录
      if (this.actionTimes.length > 100) {
        this.actionTimes = this.actionTimes.slice(-100);
      }
      
      // 计算平均响应时间
      this.stats.averageResponseTime = this.actionTimes.reduce((a, b) => a + b, 0) / this.actionTimes.length;
    }
    
    this.stats.queueSize = this.actionQueue.length;
    this.stats.recordingActive = this.isRecording;
  }

  /**
   * 录制操作
   */
  private recordAction(type: string, params: any, duration?: number): void {
    if (!this.isRecording) {
      return;
    }
    
    const action: RecordedAction = {
      timestamp: Date.now() - this.recordingStartTime,
      type,
      params,
      duration
    };
    
    this.recordedActions.push(action);
  }

  /**
   * 紧急停止所有操作
   */
  public emergencyStop(): void {
    this.emergencyStopFlag = true;
    this.queuePaused = true;
    console.warn('InputController: 紧急停止已激活');
  }

  /**
   * 重置紧急停止状态
   */
  public resetEmergencyStop(): void {
    this.emergencyStopFlag = false;
    console.log('InputController: 紧急停止已重置');
  }

  /**
   * 获取增强的统计信息
   */
  public getEnhancedStats(): InputStats {
    return { ...this.stats };
  }

  // ==================== 操作队列系统 ====================

  /**
   * 添加操作到队列
   */
  public addToQueue(action: Omit<QueuedAction, 'id' | 'timestamp'>): string {
    const actionId = `action_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const queuedAction: QueuedAction = {
      ...action,
      id: actionId,
      timestamp: Date.now(),
      retries: 0,
      maxRetries: action.maxRetries || 3
    };
    
    // 根据优先级插入队列
    const priorityOrder = { high: 0, medium: 1, low: 2 };
    let insertIndex = this.actionQueue.length;
    
    for (let i = 0; i < this.actionQueue.length; i++) {
      if (priorityOrder[queuedAction.priority] < priorityOrder[this.actionQueue[i].priority]) {
        insertIndex = i;
        break;
      }
    }
    
    this.actionQueue.splice(insertIndex, 0, queuedAction);
    this.updateStats(true); // 更新队列大小
    
    console.log(`操作已添加到队列: ${actionId}, 优先级: ${action.priority}`);
    return actionId;
  }

  /**
   * 执行队列中的所有操作
   */
  public async executeQueue(): Promise<void> {
    if (this.isQueueExecuting) {
      console.warn('队列已在执行中');
      return;
    }
    
    if (this.actionQueue.length === 0) {
      console.log('队列为空，无需执行');
      return;
    }
    
    this.isQueueExecuting = true;
    this.queuePaused = false;
    
    console.log(`开始执行队列，共 ${this.actionQueue.length} 个操作`);
    
    try {
      while (this.actionQueue.length > 0 && !this.emergencyStopFlag) {
        if (this.queuePaused) {
          await this.delay(100); // 暂停时等待
          continue;
        }
        
        const action = this.actionQueue.shift()!;
        await this.executeQueuedAction(action);
      }
    } catch (error) {
      console.error('队列执行过程中发生错误:', error);
    } finally {
      this.isQueueExecuting = false;
      console.log('队列执行完成');
    }
  }

  /**
   * 暂停队列执行
   */
  public pauseQueue(): void {
    this.queuePaused = true;
    console.log('队列执行已暂停');
  }

  /**
   * 恢复队列执行
   */
  public resumeQueue(): void {
    this.queuePaused = false;
    console.log('队列执行已恢复');
  }

  /**
   * 清空队列
   */
  public clearQueue(): void {
    this.actionQueue = [];
    this.updateStats(true);
    console.log('队列已清空');
  }

  /**
   * 获取队列状态
   */
  public getQueueStatus(): {
    size: number;
    isExecuting: boolean;
    isPaused: boolean;
    actions: QueuedAction[];
  } {
    return {
      size: this.actionQueue.length,
      isExecuting: this.isQueueExecuting,
      isPaused: this.queuePaused,
      actions: [...this.actionQueue]
    };
  }

  /**
   * 移除队列中的特定操作
   */
  public removeFromQueue(actionId: string): boolean {
    const index = this.actionQueue.findIndex(action => action.id === actionId);
    if (index !== -1) {
      this.actionQueue.splice(index, 1);
      this.updateStats(true);
      console.log(`操作已从队列中移除: ${actionId}`);
      return true;
    }
    return false;
  }

  /**
   * 执行队列中的单个操作
   */
  private async executeQueuedAction(action: QueuedAction): Promise<void> {
    const startTime = Date.now();
    let success = false;
    
    try {
      console.log(`执行队列操作: ${action.type} (${action.id})`);
      
      switch (action.type) {
        case 'click':
          success = await this.click(action.params.x, action.params.y, action.params.options);
          break;
        case 'move':
          success = await this.moveMouse(action.params.x, action.params.y);
          break;
        case 'key':
          success = await this.pressKey(action.params.key, action.params.options);
          break;
        case 'type':
          await this.typeText(action.params.text, action.params.delay);
          success = true;
          break;
        case 'drag':
          await this.drag(action.params.fromX, action.params.fromY, action.params.toX, action.params.toY);
          success = true;
          break;
        case 'scroll':
          await this.scroll(action.params.x, action.params.y, action.params.direction, action.params.clicks);
          success = true;
          break;
        case 'smoothMove':
          success = await this.smoothMoveTo(action.params.x, action.params.y, action.params.options);
          break;
        default:
          console.warn(`未知的操作类型: ${action.type}`);
          success = false;
      }
      
      if (success) {
        const duration = Date.now() - startTime;
        this.updateStats(true, duration);
        console.log(`队列操作执行成功: ${action.id} (${duration}ms)`);
      } else {
        throw new Error(`操作执行失败: ${action.type}`);
      }
      
    } catch (error) {
      console.error(`队列操作执行失败: ${action.id}`, error);
      
      // 重试逻辑
      if (action.retries! < action.maxRetries!) {
        action.retries!++;
        console.log(`重试操作: ${action.id} (第 ${action.retries} 次重试)`);
        
        // 重新添加到队列前端
        this.actionQueue.unshift(action);
        
        // 重试前等待
        await this.delay(1000 * action.retries!);
      } else {
        console.error(`操作重试次数已达上限: ${action.id}`);
        this.updateStats(false);
      }
    }
   }

  // ==================== 操作录制和回放系统 ====================

  /**
   * 开始录制操作
   */
  public startRecording(): boolean {
    if (this.isRecording) {
      console.warn('录制已在进行中');
      return false;
    }
    
    this.isRecording = true;
    this.recordedActions = [];
    this.recordingStartTime = Date.now();
    this.updateStats(true);
    
    console.log('开始录制操作');
    return true;
  }

  /**
   * 停止录制操作
   */
  public stopRecording(): RecordedAction[] {
    if (!this.isRecording) {
      console.warn('当前没有进行录制');
      return [];
    }
    
    this.isRecording = false;
    this.updateStats(true);
    
    const actions = [...this.recordedActions];
    console.log(`录制停止，共录制 ${actions.length} 个操作`);
    
    return actions;
  }

  /**
   * 回放录制的操作
   */
  public async playback(actions?: RecordedAction[], speedMultiplier: number = 1.0): Promise<boolean> {
    const actionsToPlay = actions || this.recordedActions;
    
    if (actionsToPlay.length === 0) {
      console.warn('没有可回放的操作');
      return false;
    }
    
    if (!this.isEnabled) {
      console.warn('输入控制已禁用，无法回放');
      return false;
    }
    
    console.log(`开始回放 ${actionsToPlay.length} 个操作，速度倍数: ${speedMultiplier}`);
    
    try {
      let lastTimestamp = 0;
      
      for (const action of actionsToPlay) {
        if (this.emergencyStopFlag) {
          console.log('回放被紧急停止');
          return false;
        }
        
        // 计算延迟时间
        const delay = (action.timestamp - lastTimestamp) / speedMultiplier;
        if (delay > 0 && lastTimestamp > 0) {
          await this.delay(delay);
        }
        
        // 执行操作
        await this.executeRecordedAction(action);
        lastTimestamp = action.timestamp;
      }
      
      console.log('回放完成');
      return true;
    } catch (error) {
      console.error('回放过程中发生错误:', error);
      return false;
    }
  }

  /**
   * 保存录制到文件
   */
  public async saveRecording(filename: string, actions?: RecordedAction[]): Promise<boolean> {
    const actionsToSave = actions || this.recordedActions;
    
    if (actionsToSave.length === 0) {
      console.warn('没有可保存的录制操作');
      return false;
    }
    
    try {
      const fs = require('fs').promises;
      const path = require('path');
      
      // 确保录制目录存在
      const recordingsDir = path.join(process.cwd(), 'recordings');
      try {
        await fs.access(recordingsDir);
      } catch {
        await fs.mkdir(recordingsDir, { recursive: true });
      }
      
      const filepath = path.join(recordingsDir, `${filename}.json`);
      const recordingData = {
        version: '1.0',
        timestamp: Date.now(),
        totalActions: actionsToSave.length,
        duration: actionsToSave.length > 0 ? actionsToSave[actionsToSave.length - 1].timestamp : 0,
        actions: actionsToSave
      };
      
      await fs.writeFile(filepath, JSON.stringify(recordingData, null, 2), 'utf8');
      console.log(`录制已保存到: ${filepath}`);
      return true;
    } catch (error) {
      console.error('保存录制失败:', error);
      return false;
    }
  }

  /**
   * 从文件加载录制
   */
  public async loadRecording(filename: string): Promise<RecordedAction[]> {
    try {
      const fs = require('fs').promises;
      const path = require('path');
      
      const filepath = path.join(process.cwd(), 'recordings', `${filename}.json`);
      const fileContent = await fs.readFile(filepath, 'utf8');
      const recordingData = JSON.parse(fileContent);
      
      if (!recordingData.actions || !Array.isArray(recordingData.actions)) {
        throw new Error('无效的录制文件格式');
      }
      
      console.log(`录制已加载: ${filename}, 共 ${recordingData.actions.length} 个操作`);
      return recordingData.actions;
    } catch (error) {
      console.error('加载录制失败:', error);
      return [];
    }
  }

  /**
   * 获取录制状态
   */
  public getRecordingStatus(): {
    isRecording: boolean;
    recordedActionsCount: number;
    recordingDuration: number;
  } {
    return {
      isRecording: this.isRecording,
      recordedActionsCount: this.recordedActions.length,
      recordingDuration: this.isRecording ? Date.now() - this.recordingStartTime : 0
    };
  }

  /**
   * 清空当前录制
   */
  public clearRecording(): void {
    this.recordedActions = [];
    console.log('当前录制已清空');
  }

  /**
   * 执行录制的单个操作
   */
  private async executeRecordedAction(action: RecordedAction): Promise<void> {
    try {
      console.log(`回放操作: ${action.type}`);
      
      switch (action.type) {
        case 'click':
          await this.click(action.params.x, action.params.y, action.params.options);
          break;
        case 'move':
          await this.moveMouse(action.params.x, action.params.y);
          break;
        case 'key':
          await this.pressKey(action.params.key, action.params.options);
          break;
        case 'typeText':
          await this.typeText(action.params.text, action.params.delay);
          break;
        case 'drag':
          await this.drag(action.params.fromX, action.params.fromY, action.params.toX, action.params.toY);
          break;
        case 'scroll':
          await this.scroll(action.params.x, action.params.y, action.params.direction, action.params.clicks);
          break;
        case 'smoothMoveTo':
          await this.smoothMoveTo(action.params.x, action.params.y, action.params.options);
          break;
        case 'keyCombo':
          await this.keyCombo(action.params.keys, action.params.holdTime);
          break;
        case 'doubleClick':
          await this.doubleClick(action.params.x, action.params.y, action.params.button);
          break;
        default:
          console.warn(`未知的录制操作类型: ${action.type}`);
      }
    } catch (error) {
      console.error(`回放操作失败: ${action.type}`, error);
      throw error;
    }
   }

  // ==================== 动态延迟调整和重试机制 ====================

  /**
   * 带重试机制的操作执行
   */
  public async executeWithRetry<T>(
    operation: () => Promise<T>,
    maxRetries: number = 3,
    retryDelay: number = 1000,
    backoffMultiplier: number = 1.5
  ): Promise<T> {
    let lastError: Error | null = null;
    let currentDelay = retryDelay;
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        if (this.emergencyStopFlag) {
          throw new Error('操作被紧急停止');
        }
        
        const startTime = Date.now();
        const result = await operation();
        const executionTime = Date.now() - startTime;
        
        // 记录成功执行的时间，用于性能调整
        this.actionTimes.push(executionTime);
        if (this.actionTimes.length > 100) {
          this.actionTimes.shift(); // 保持最近100次的执行时间
        }
        
        // 更新统计信息
        this.updateStats(true);
        
        if (attempt > 0) {
          console.log(`操作在第 ${attempt + 1} 次尝试后成功执行`);
        }
        
        return result;
      } catch (error) {
        lastError = error as Error;
        this.updateStats(false);
        
        if (attempt < maxRetries) {
          console.warn(`操作执行失败，第 ${attempt + 1} 次尝试，${currentDelay}ms 后重试:`, error);
          await this.delay(currentDelay);
          currentDelay *= backoffMultiplier;
        } else {
          console.error(`操作执行失败，已达到最大重试次数 ${maxRetries}:`, error);
        }
      }
    }
    
    throw lastError || new Error('操作执行失败');
  }

  /**
   * 基于性能调整延迟时间
   */
  public adjustDelayBasedOnPerformance(): number {
    if (this.actionTimes.length < 5) {
      return this.defaultDelay; // 数据不足，使用默认延迟
    }
    
    // 计算平均执行时间
    const avgTime = this.actionTimes.reduce((sum, time) => sum + time, 0) / this.actionTimes.length;
    
    // 计算标准差
    const variance = this.actionTimes.reduce((sum, time) => sum + Math.pow(time - avgTime, 2), 0) / this.actionTimes.length;
    const stdDev = Math.sqrt(variance);
    
    // 基于性能调整延迟
    let adjustedDelay = this.defaultDelay;
    
    if (avgTime > 200) {
      // 如果平均执行时间较长，增加延迟
      adjustedDelay = Math.max(this.defaultDelay, avgTime * 0.5);
    } else if (avgTime < 50 && stdDev < 20) {
      // 如果执行时间短且稳定，可以减少延迟
      adjustedDelay = Math.max(10, this.defaultDelay * 0.8);
    }
    
    // 限制延迟范围
    adjustedDelay = Math.max(10, Math.min(adjustedDelay, 5000));
    
    console.log(`性能调整: 平均执行时间 ${avgTime.toFixed(2)}ms, 调整后延迟 ${adjustedDelay.toFixed(2)}ms`);
    
    return adjustedDelay;
  }

  /**
   * 智能延迟 - 根据系统负载和历史性能自动调整
   */
  public async smartDelay(baseDelay?: number): Promise<void> {
    const delay = baseDelay || this.adjustDelayBasedOnPerformance();
    
    // 检查系统负载（简单实现）
    const startTime = Date.now();
    await new Promise(resolve => setTimeout(resolve, 1));
    const actualDelay = Date.now() - startTime;
    
    if (actualDelay > 10) {
      // 系统负载较高，增加延迟
      const loadFactor = Math.min(actualDelay / 10, 3);
      const adjustedDelay = delay * loadFactor;
      console.log(`检测到系统负载较高，延迟调整为 ${adjustedDelay.toFixed(2)}ms`);
      await this.delay(adjustedDelay);
    } else {
      await this.delay(delay);
    }
  }

  /**
   * 获取性能统计信息
   */
  public getPerformanceStats(): {
    averageExecutionTime: number;
    minExecutionTime: number;
    maxExecutionTime: number;
    standardDeviation: number;
    totalSamples: number;
    recommendedDelay: number;
  } {
    if (this.actionTimes.length === 0) {
      return {
        averageExecutionTime: 0,
        minExecutionTime: 0,
        maxExecutionTime: 0,
        standardDeviation: 0,
        totalSamples: 0,
        recommendedDelay: this.defaultDelay
      };
    }
    
    const avgTime = this.actionTimes.reduce((sum, time) => sum + time, 0) / this.actionTimes.length;
    const minTime = Math.min(...this.actionTimes);
    const maxTime = Math.max(...this.actionTimes);
    
    const variance = this.actionTimes.reduce((sum, time) => sum + Math.pow(time - avgTime, 2), 0) / this.actionTimes.length;
    const stdDev = Math.sqrt(variance);
    
    return {
      averageExecutionTime: avgTime,
      minExecutionTime: minTime,
      maxExecutionTime: maxTime,
      standardDeviation: stdDev,
      totalSamples: this.actionTimes.length,
      recommendedDelay: this.adjustDelayBasedOnPerformance()
    };
  }

  /**
   * 重置性能统计数据
   */
  public resetPerformanceStats(): void {
    this.actionTimes = [];
    console.log('性能统计数据已重置');
  }

  /**
   * 设置性能监控阈值
   */
  public setPerformanceThresholds(thresholds: {
    maxExecutionTime?: number;
    maxStandardDeviation?: number;
    minSampleSize?: number;
  }): void {
    // 这里可以存储阈值配置，用于性能监控和告警
    console.log('性能监控阈值已设置:', thresholds);
  }

  /**
   * 检查性能是否正常
   */
  public checkPerformanceHealth(): {
    isHealthy: boolean;
    issues: string[];
    recommendations: string[];
  } {
    const stats = this.getPerformanceStats();
    const issues: string[] = [];
    const recommendations: string[] = [];
    
    if (stats.totalSamples < 10) {
      issues.push('性能数据样本不足');
      recommendations.push('继续执行操作以收集更多性能数据');
    }
    
    if (stats.averageExecutionTime > 500) {
      issues.push('平均执行时间过长');
      recommendations.push('考虑优化操作或增加延迟时间');
    }
    
    if (stats.standardDeviation > stats.averageExecutionTime * 0.5) {
      issues.push('执行时间波动较大');
      recommendations.push('检查系统负载或网络状况');
    }
    
    if (stats.maxExecutionTime > stats.averageExecutionTime * 3) {
      issues.push('存在异常缓慢的操作');
      recommendations.push('检查是否有阻塞操作或系统资源不足');
    }
    
    const isHealthy = issues.length === 0;
    
    return {
      isHealthy,
      issues,
      recommendations
    };
  }


}

export default InputController;