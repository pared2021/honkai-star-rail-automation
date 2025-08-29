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

export class InputController {
  private isEnabled = true;
  private defaultDelay = 100; // 默认操作延迟
  private gameWindow: GameWindow | null = null;
  private inputLogs: InputLog[] = [];
  private maxLogEntries = 1000;
  private safetyChecks = true;
  private lastActionTime = 0;
  private minActionInterval = 10; // 最小操作间隔(ms)

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
   * 平滑移动鼠标
   */
  private async smoothMoveTo(from: MousePosition, to: MousePosition, duration: number = 500): Promise<void> {
    const steps = Math.max(10, Math.min(50, Math.floor(duration / 10))); // 动态计算步数
    const stepDelay = duration / steps;
    const deltaX = (to.x - from.x) / steps;
    const deltaY = (to.y - from.y) / steps;

    for (let i = 0; i <= steps; i++) {
      const x = Math.round(from.x + deltaX * i);
      const y = Math.round(from.y + deltaY * i);
      
      robot.moveMouse(x, y);
      await this.delay(stepDelay);
    }
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


}

export default InputController;