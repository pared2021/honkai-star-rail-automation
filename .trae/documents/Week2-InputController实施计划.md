# Week 2: InputController模块实施计划

## 当前状态评估

### ✅ 已完成功能
经过代码审查，InputController.ts模块已经具备了相当完整的基础实现：

**基础操作功能**：
- ✅ 鼠标点击（左键、右键、中键、双击）
- ✅ 鼠标移动和拖拽
- ✅ 键盘按键和组合键
- ✅ 文本输入
- ✅ 滚轮滚动

**高级功能**：
- ✅ 坐标转换（游戏坐标↔屏幕坐标）
- ✅ 操作日志记录和统计
- ✅ 安全检查机制
- ✅ 配置管理
- ✅ 基础的平滑移动（私有方法）

**安全特性**：
- ✅ 操作频率限制
- ✅ 输入控制开关
- ✅ 按键名称验证
- ✅ 日志自动清理

### ❌ 需要增强的功能

**缺失的高级功能**：
- ❌ 公共的平滑移动API
- ❌ 操作队列系统
- ❌ 操作录制和回放
- ❌ 贝塞尔曲线移动
- ❌ 批量操作执行

**安全性增强**：
- ❌ 游戏窗口边界检查
- ❌ 动态延迟调整
- ❌ 操作重试机制
- ❌ 紧急停止功能

**测试覆盖**：
- ❌ 单元测试
- ❌ 集成测试
- ❌ 性能测试

## 详细实施计划

### 阶段1：功能增强 (Day 1-4)

#### 任务1.1：公共平滑移动API实现
**目标**：将私有的smoothMoveTo方法扩展为公共API

**具体实现**：
```typescript
/**
 * 平滑移动鼠标到目标位置（公共API）
 */
public async smoothMoveTo(toX: number, toY: number, duration: number = 500, curve: 'linear' | 'ease' | 'bezier' = 'ease'): Promise<boolean> {
  if (!this.isEnabled) {
    this.logAction('smoothMoveTo', { x: toX, y: toY }, false, '输入控制已禁用');
    return false;
  }

  if (!this.performSafetyCheck()) {
    this.logAction('smoothMoveTo', { x: toX, y: toY }, false, '安全检查失败');
    return false;
  }

  try {
    const from = this.getCurrentMousePosition();
    const to = this.gameToScreenCoords(toX, toY);
    
    switch (curve) {
      case 'linear':
        await this.smoothMoveLinear(from, to, duration);
        break;
      case 'ease':
        await this.smoothMoveEase(from, to, duration);
        break;
      case 'bezier':
        await this.smoothMoveBezier(from, to, duration);
        break;
    }
    
    this.logAction('smoothMoveTo', to, true, `smooth move to (${to.x}, ${to.y}) with ${curve} curve`);
    return true;
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    this.logAction('smoothMoveTo', { x: toX, y: toY }, false, errorMsg);
    console.error('平滑移动失败:', error);
    return false;
  }
}

/**
 * 贝塞尔曲线移动
 */
private async smoothMoveBezier(from: MousePosition, to: MousePosition, duration: number): Promise<void> {
  const path = this.calculateBezierPath(from, to, Math.floor(duration / 10));
  const stepDelay = duration / path.length;
  
  for (const point of path) {
    robot.moveMouse(point.x, point.y);
    await this.delay(stepDelay);
  }
}

/**
 * 计算贝塞尔曲线路径
 */
private calculateBezierPath(start: MousePosition, end: MousePosition, steps: number): MousePosition[] {
  const path: MousePosition[] = [];
  const controlPoint1 = {
    x: start.x + (end.x - start.x) * 0.25 + (Math.random() - 0.5) * 50,
    y: start.y + (end.y - start.y) * 0.25 + (Math.random() - 0.5) * 50
  };
  const controlPoint2 = {
    x: start.x + (end.x - start.x) * 0.75 + (Math.random() - 0.5) * 50,
    y: start.y + (end.y - start.y) * 0.75 + (Math.random() - 0.5) * 50
  };
  
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const point = this.calculateBezierPoint(start, controlPoint1, controlPoint2, end, t);
    path.push(point);
  }
  
  return path;
}
```

**验收标准**：
- [ ] 支持线性、缓动、贝塞尔三种移动曲线
- [ ] 移动轨迹自然，避免机械感
- [ ] 移动时间可精确控制
- [ ] 移动过程可被安全检查中断

#### 任务1.2：操作队列系统实现
**目标**：实现批量操作的队列化执行

**具体实现**：
```typescript
interface QueuedAction {
  id: string;
  type: 'click' | 'key' | 'move' | 'drag' | 'scroll' | 'type' | 'smoothMove';
  params: any[];
  delay?: number;
  priority?: number;
  retries?: number;
}

interface QueueStatus {
  pending: number;
  executing: boolean;
  paused: boolean;
  currentAction?: QueuedAction;
}

// 添加队列相关属性
private actionQueue: QueuedAction[] = [];
private queueExecuting: boolean = false;
private queuePaused: boolean = false;
private currentActionId: string | null = null;
private queueBatchSize: number = 10;

/**
 * 添加操作到队列
 */
public addToQueue(action: Omit<QueuedAction, 'id'>): string {
  const id = `action_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  const queuedAction: QueuedAction = {
    id,
    priority: 0,
    retries: 3,
    ...action
  };
  
  this.actionQueue.push(queuedAction);
  
  // 按优先级排序
  this.actionQueue.sort((a, b) => (b.priority || 0) - (a.priority || 0));
  
  this.logAction('addToQueue', undefined, true, `Added action ${id} to queue`);
  return id;
}

/**
 * 执行队列中的所有操作
 */
public async executeQueue(): Promise<{ success: number; failed: number; results: boolean[] }> {
  if (this.queueExecuting) {
    throw new Error('队列正在执行中');
  }
  
  this.queueExecuting = true;
  const results: boolean[] = [];
  let success = 0;
  let failed = 0;
  
  try {
    while (this.actionQueue.length > 0 && !this.queuePaused) {
      const batch = this.actionQueue.splice(0, this.queueBatchSize);
      
      for (const action of batch) {
        if (this.queuePaused) {
          // 将未执行的操作放回队列
          this.actionQueue.unshift(...batch.slice(batch.indexOf(action)));
          break;
        }
        
        this.currentActionId = action.id;
        const result = await this.executeAction(action);
        results.push(result);
        
        if (result) {
          success++;
        } else {
          failed++;
          // 重试逻辑
          if (action.retries && action.retries > 0) {
            action.retries--;
            this.actionQueue.unshift(action); // 重新加入队列头部
          }
        }
        
        if (action.delay) {
          await this.delay(action.delay);
        }
      }
    }
    
    return { success, failed, results };
  } finally {
    this.queueExecuting = false;
    this.currentActionId = null;
  }
}

/**
 * 执行单个操作
 */
private async executeAction(action: QueuedAction): Promise<boolean> {
  try {
    switch (action.type) {
      case 'click':
        return await this.click(...action.params);
      case 'key':
        return await this.pressKey(...action.params);
      case 'move':
        return await this.moveMouse(...action.params);
      case 'drag':
        await this.drag(...action.params);
        return true;
      case 'scroll':
        await this.scroll(...action.params);
        return true;
      case 'type':
        await this.typeText(...action.params);
        return true;
      case 'smoothMove':
        return await this.smoothMoveTo(...action.params);
      default:
        throw new Error(`未知的操作类型: ${action.type}`);
    }
  } catch (error) {
    console.error(`执行操作 ${action.id} 失败:`, error);
    return false;
  }
}

/**
 * 暂停队列执行
 */
public pauseQueue(): void {
  this.queuePaused = true;
  this.logAction('pauseQueue', undefined, true, 'Queue execution paused');
}

/**
 * 恢复队列执行
 */
public resumeQueue(): void {
  this.queuePaused = false;
  this.logAction('resumeQueue', undefined, true, 'Queue execution resumed');
}

/**
 * 清空操作队列
 */
public clearQueue(): void {
  this.actionQueue = [];
  this.logAction('clearQueue', undefined, true, 'Queue cleared');
}

/**
 * 获取队列状态
 */
public getQueueStatus(): QueueStatus {
  return {
    pending: this.actionQueue.length,
    executing: this.queueExecuting,
    paused: this.queuePaused,
    currentAction: this.currentActionId ? 
      this.actionQueue.find(a => a.id === this.currentActionId) : undefined
  };
}
```

**验收标准**：
- [ ] 支持多种操作类型的队列化
- [ ] 支持操作优先级排序
- [ ] 支持批量执行和暂停/恢复
- [ ] 支持操作重试机制
- [ ] 队列状态可实时查询

#### 任务1.3：操作录制和回放系统
**目标**：实现用户操作的录制和自动回放

**具体实现**：
```typescript
interface RecordedAction {
  timestamp: number;
  action: QueuedAction;
  relativeTime: number;
  windowState?: GameWindow;
  mousePosition?: MousePosition;
}

interface RecordingSession {
  id: string;
  name: string;
  startTime: number;
  endTime?: number;
  actions: RecordedAction[];
  metadata?: {
    gameWindow?: GameWindow;
    totalDuration?: number;
    actionCount?: number;
  };
}

// 添加录制相关属性
private recording: boolean = false;
private recordedActions: RecordedAction[] = [];
private recordingStartTime: number = 0;
private recordingSession: RecordingSession | null = null;

/**
 * 开始录制操作
 */
public startRecording(sessionName: string = `Recording_${Date.now()}`): string {
  if (this.recording) {
    throw new Error('已经在录制中');
  }
  
  const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  
  this.recording = true;
  this.recordedActions = [];
  this.recordingStartTime = Date.now();
  this.recordingSession = {
    id: sessionId,
    name: sessionName,
    startTime: this.recordingStartTime,
    actions: [],
    metadata: {
      gameWindow: this.gameWindow ? { ...this.gameWindow } : undefined
    }
  };
  
  this.logAction('startRecording', undefined, true, `Started recording session: ${sessionName}`);
  return sessionId;
}

/**
 * 停止录制并返回录制会话
 */
public stopRecording(): RecordingSession {
  if (!this.recording || !this.recordingSession) {
    throw new Error('当前没有在录制');
  }
  
  this.recording = false;
  const endTime = Date.now();
  
  this.recordingSession.endTime = endTime;
  this.recordingSession.actions = [...this.recordedActions];
  this.recordingSession.metadata = {
    ...this.recordingSession.metadata,
    totalDuration: endTime - this.recordingStartTime,
    actionCount: this.recordedActions.length
  };
  
  const session = { ...this.recordingSession };
  this.recordingSession = null;
  this.recordedActions = [];
  
  this.logAction('stopRecording', undefined, true, `Stopped recording session: ${session.name}`);
  return session;
}

/**
 * 录制操作（在每个操作方法中调用）
 */
private recordAction(type: QueuedAction['type'], params: any[], success: boolean): void {
  if (!this.recording) return;
  
  const now = Date.now();
  const recordedAction: RecordedAction = {
    timestamp: now,
    relativeTime: now - this.recordingStartTime,
    action: {
      id: `recorded_${now}_${Math.random().toString(36).substr(2, 9)}`,
      type,
      params,
      delay: this.defaultDelay
    },
    windowState: this.gameWindow ? { ...this.gameWindow } : undefined,
    mousePosition: this.getCurrentMousePosition()
  };
  
  this.recordedActions.push(recordedAction);
}

/**
 * 回放录制的操作
 */
public async playback(session: RecordingSession, options: {
  speed?: number;
  skipErrors?: boolean;
  restoreWindow?: boolean;
} = {}): Promise<{ success: number; failed: number; skipped: number }> {
  const { speed = 1.0, skipErrors = true, restoreWindow = true } = options;
  
  if (this.queueExecuting) {
    throw new Error('队列正在执行中，无法开始回放');
  }
  
  // 恢复窗口状态
  if (restoreWindow && session.metadata?.gameWindow) {
    this.setGameWindow(session.metadata.gameWindow);
  }
  
  let success = 0;
  let failed = 0;
  let skipped = 0;
  
  this.logAction('startPlayback', undefined, true, `Starting playback of session: ${session.name}`);
  
  try {
    for (let i = 0; i < session.actions.length; i++) {
      const recordedAction = session.actions[i];
      const nextAction = session.actions[i + 1];
      
      // 执行操作
      const result = await this.executeAction(recordedAction.action);
      
      if (result) {
        success++;
      } else {
        failed++;
        if (!skipErrors) {
          throw new Error(`回放操作失败: ${recordedAction.action.type}`);
        }
      }
      
      // 计算延迟时间
      if (nextAction) {
        const originalDelay = nextAction.relativeTime - recordedAction.relativeTime;
        const adjustedDelay = Math.max(10, originalDelay / speed);
        await this.delay(adjustedDelay);
      }
    }
    
    this.logAction('finishPlayback', undefined, true, `Playback completed: ${success} success, ${failed} failed`);
    return { success, failed, skipped };
  } catch (error) {
    this.logAction('playbackError', undefined, false, error instanceof Error ? error.message : String(error));
    throw error;
  }
}

/**
 * 保存录制会话到文件
 */
public async saveRecording(session: RecordingSession, filename: string): Promise<void> {
  try {
    const fs = await import('fs/promises');
    const path = await import('path');
    
    const recordingsDir = path.join(process.cwd(), 'recordings');
    await fs.mkdir(recordingsDir, { recursive: true });
    
    const filepath = path.join(recordingsDir, `${filename}.json`);
    await fs.writeFile(filepath, JSON.stringify(session, null, 2), 'utf-8');
    
    this.logAction('saveRecording', undefined, true, `Saved recording to: ${filepath}`);
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    this.logAction('saveRecording', undefined, false, errorMsg);
    throw error;
  }
}

/**
 * 从文件加载录制会话
 */
public async loadRecording(filename: string): Promise<RecordingSession> {
  try {
    const fs = await import('fs/promises');
    const path = await import('path');
    
    const filepath = path.join(process.cwd(), 'recordings', `${filename}.json`);
    const content = await fs.readFile(filepath, 'utf-8');
    const session: RecordingSession = JSON.parse(content);
    
    this.logAction('loadRecording', undefined, true, `Loaded recording from: ${filepath}`);
    return session;
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    this.logAction('loadRecording', undefined, false, errorMsg);
    throw error;
  }
}
```

**验收标准**：
- [ ] 准确录制操作时序和参数
- [ ] 支持变速回放（0.1x - 5.0x）
- [ ] 录制会话可保存和加载
- [ ] 回放过程可中断和错误处理
- [ ] 支持窗口状态恢复

### 阶段2：安全性增强 (Day 5-6)

#### 任务2.1：游戏窗口边界检查
**目标**：确保所有操作都在游戏窗口范围内

**具体实现**：
```typescript
/**
 * 检查坐标是否在游戏窗口内
 */
private isCoordinateInGameWindow(x: number, y: number): boolean {
  if (!this.gameWindow) {
    return true; // 没有设置游戏窗口时不进行检查
  }
  
  const screenCoords = this.gameToScreenCoords(x, y);
  
  return screenCoords.x >= this.gameWindow.x &&
         screenCoords.x <= this.gameWindow.x + this.gameWindow.width &&
         screenCoords.y >= this.gameWindow.y &&
         screenCoords.y <= this.gameWindow.y + this.gameWindow.height;
}

/**
 * 自动修正超出边界的坐标
 */
private clampToGameWindow(x: number, y: number): MousePosition {
  if (!this.gameWindow) {
    return { x, y };
  }
  
  const clampedX = Math.max(0, Math.min(x, this.gameWindow.width));
  const clampedY = Math.max(0, Math.min(y, this.gameWindow.height));
  
  return { x: clampedX, y: clampedY };
}

/**
 * 验证游戏窗口是否有效
 */
public validateGameWindow(): boolean {
  if (!this.gameWindow) {
    return false;
  }
  
  // 检查窗口尺寸是否合理
  if (this.gameWindow.width <= 0 || this.gameWindow.height <= 0) {
    return false;
  }
  
  // 检查窗口位置是否在屏幕范围内
  const screenSize = robot.getScreenSize();
  if (this.gameWindow.x < 0 || this.gameWindow.y < 0 ||
      this.gameWindow.x + this.gameWindow.width > screenSize.width ||
      this.gameWindow.y + this.gameWindow.height > screenSize.height) {
    return false;
  }
  
  return true;
}

/**
 * 增强的安全检查
 */
private performSafetyCheck(x?: number, y?: number): boolean {
  if (!this.safetyChecks) {
    return true;
  }

  // 原有的频率检查
  const now = Date.now();
  if (now - this.lastActionTime < this.minActionInterval) {
    return false;
  }

  // 游戏窗口有效性检查
  if (!this.validateGameWindow()) {
    console.warn('游戏窗口无效，操作被阻止');
    return false;
  }

  // 坐标边界检查
  if (x !== undefined && y !== undefined) {
    if (!this.isCoordinateInGameWindow(x, y)) {
      console.warn(`坐标 (${x}, ${y}) 超出游戏窗口边界，操作被阻止`);
      return false;
    }
  }

  this.lastActionTime = now;
  return true;
}
```

#### 任务2.2：动态延迟和重试机制
**目标**：智能调整操作延迟和失败重试

**具体实现**：
```typescript
// 添加性能监控属性
private performanceMetrics = {
  averageResponseTime: 100,
  systemLoad: 0,
  recentFailures: 0,
  adaptiveDelay: 100
};

/**
 * 动态调整延迟
 */
private adjustDelayBasedOnPerformance(): number {
  const baseDelay = this.defaultDelay;
  let adjustedDelay = baseDelay;
  
  // 根据系统负载调整
  if (this.performanceMetrics.systemLoad > 0.8) {
    adjustedDelay *= 1.5;
  } else if (this.performanceMetrics.systemLoad < 0.3) {
    adjustedDelay *= 0.8;
  }
  
  // 根据最近失败次数调整
  if (this.performanceMetrics.recentFailures > 3) {
    adjustedDelay *= (1 + this.performanceMetrics.recentFailures * 0.2);
  }
  
  // 限制延迟范围
  adjustedDelay = Math.max(50, Math.min(adjustedDelay, 2000));
  
  this.performanceMetrics.adaptiveDelay = adjustedDelay;
  return adjustedDelay;
}

/**
 * 带重试的操作执行
 */
public async executeWithRetry<T>(
  operation: () => Promise<T>,
  maxRetries: number = 3,
  retryDelay: number = 1000
): Promise<T> {
  let lastError: Error | null = null;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const result = await operation();
      
      // 成功时重置失败计数
      this.performanceMetrics.recentFailures = Math.max(0, this.performanceMetrics.recentFailures - 1);
      
      return result;
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      this.performanceMetrics.recentFailures++;
      
      this.logAction('retryAttempt', undefined, false, `Attempt ${attempt}/${maxRetries} failed: ${lastError.message}`);
      
      if (attempt < maxRetries) {
        const adaptiveDelay = this.adjustDelayBasedOnPerformance();
        await this.delay(retryDelay + adaptiveDelay);
      }
    }
  }
  
  throw lastError || new Error('操作失败，已达到最大重试次数');
}

/**
 * 紧急停止所有操作
 */
public emergencyStop(): void {
  this.isEnabled = false;
  this.queuePaused = true;
  this.recording = false;
  
  // 清空队列
  this.actionQueue = [];
  
  // 释放所有按下的按键（如果有的话）
  try {
    // 这里可以添加释放按键的逻辑
    robot.keyToggle('shift', 'up');
    robot.keyToggle('control', 'up');
    robot.keyToggle('alt', 'up');
  } catch (error) {
    // 忽略释放按键时的错误
  }
  
  this.logAction('emergencyStop', undefined, true, 'Emergency stop activated');
  console.warn('紧急停止已激活，所有操作已停止');
}

/**
 * 恢复正常操作
 */
public resumeNormalOperation(): void {
  this.isEnabled = true;
  this.queuePaused = false;
  this.performanceMetrics.recentFailures = 0;
  
  this.logAction('resumeOperation', undefined, true, 'Normal operation resumed');
}
```

**验收标准**：
- [ ] 所有操作自动限制在游戏窗口内
- [ ] 延迟根据系统性能自动调整
- [ ] 操作失败时自动重试
- [ ] 紧急情况下能立即停止所有操作

### 阶段3：测试和验证 (Day 7-10)

#### 任务3.1：单元测试编写
**目标**：为所有核心功能编写单元测试

**测试文件结构**：
```
src/tests/
├── InputController.test.ts
├── InputController.queue.test.ts
├── InputController.recording.test.ts
└── InputController.safety.test.ts
```

**主要测试用例**：
```typescript
// InputController.test.ts
describe('InputController 基础功能', () => {
  let controller: InputController;
  
  beforeEach(() => {
    controller = new InputController();
    controller.setGameWindow({ x: 100, y: 100, width: 800, height: 600 });
  });
  
  describe('鼠标操作', () => {
    test('应该能够点击指定位置', async () => {
      const result = await controller.click(400, 300);
      expect(result).toBe(true);
    });
    
    test('应该能够移动鼠标', async () => {
      const result = await controller.moveMouse(200, 150);
      expect(result).toBe(true);
    });
    
    test('应该能够执行拖拽操作', async () => {
      await expect(controller.drag(100, 100, 200, 200)).resolves.not.toThrow();
    });
    
    test('应该能够平滑移动鼠标', async () => {
      const result = await controller.smoothMoveTo(300, 250, 500, 'bezier');
      expect(result).toBe(true);
    });
  });
  
  describe('键盘操作', () => {
    test('应该能够按下单个按键', async () => {
      const result = await controller.pressKey('space');
      expect(result).toBe(true);
    });
    
    test('应该能够执行组合键', async () => {
      const result = await controller.keyCombo(['control', 'c']);
      expect(result).toBe(true);
    });
    
    test('应该能够输入文本', async () => {
      await expect(controller.typeText('Hello World')).resolves.not.toThrow();
    });
  });
  
  describe('坐标转换', () => {
    test('应该正确转换游戏坐标到屏幕坐标', () => {
      const screenCoords = controller['gameToScreenCoords'](100, 50);
      expect(screenCoords).toEqual({ x: 200, y: 150 });
    });
    
    test('应该正确转换屏幕坐标到游戏坐标', () => {
      const gameCoords = controller['screenToGameCoords'](200, 150);
      expect(gameCoords).toEqual({ x: 100, y: 50 });
    });
  });
});

// InputController.queue.test.ts
describe('InputController 队列功能', () => {
  let controller: InputController;
  
  beforeEach(() => {
    controller = new InputController();
  });
  
  test('应该能够添加操作到队列', () => {
    const actionId = controller.addToQueue({
      type: 'click',
      params: [100, 100],
      priority: 1
    });
    
    expect(actionId).toBeDefined();
    expect(controller.getQueueStatus().pending).toBe(1);
  });
  
  test('应该能够执行队列中的操作', async () => {
    controller.addToQueue({ type: 'click', params: [100, 100] });
    controller.addToQueue({ type: 'key', params: ['space'] });
    
    const result = await controller.executeQueue();
    expect(result.success).toBeGreaterThan(0);
    expect(controller.getQueueStatus().pending).toBe(0);
  });
  
  test('应该能够暂停和恢复队列执行', () => {
    controller.pauseQueue();
    expect(controller.getQueueStatus().paused).toBe(true);
    
    controller.resumeQueue();
    expect(controller.getQueueStatus().paused).toBe(false);
  });
});

// InputController.recording.test.ts
describe('InputController 录制功能', () => {
  let controller: InputController;
  
  beforeEach(() => {
    controller = new InputController();
  });
  
  test('应该能够开始和停止录制', () => {
    const sessionId = controller.startRecording('Test Session');
    expect(sessionId).toBeDefined();
    
    const session = controller.stopRecording();
    expect(session.name).toBe('Test Session');
    expect(session.actions).toBeDefined();
  });
  
  test('应该能够录制操作', async () => {
    controller.startRecording('Action Recording');
    
    await controller.click(100, 100);
    await controller.pressKey('space');
    
    const session = controller.stopRecording();
    expect(session.actions.length).toBeGreaterThan(0);
  });
  
  test('应该能够回放录制的操作', async () => {
    controller.startRecording('Playback Test');
    await controller.click(100, 100);
    const session = controller.stopRecording();
    
    const result = await controller.playback(session);
    expect(result.success).toBeGreaterThan(0);
  });
});

// InputController.safety.test.ts
describe('InputController 安全功能', () => {
  let controller: InputController;
  
  beforeEach(() => {
    controller = new InputController();
    controller.setGameWindow({ x: 100, y: 100, width: 800, height: 600 });
  });
  
  test('应该阻止超出窗口边界的操作', async () => {
    const result = await controller.click(1000, 1000); // 超出边界
    expect(result).toBe(false);
  });
  
  test('应该在禁用时阻止操作', async () => {
    controller.setEnabled(false);
    const result = await controller.click(100, 100);
    expect(result).toBe(false);
  });
  
  test('应该能够执行紧急停止', () => {
    controller.addToQueue({ type: 'click', params: [100, 100] });
    controller.emergencyStop();
    
    expect(controller.isInputEnabled()).toBe(false);
    expect(controller.getQueueStatus().pending).toBe(0);
  });
  
  test('应该能够验证游戏窗口', () => {
    expect(controller.validateGameWindow()).toBe(true);
    
    controller.setGameWindow({ x: -100, y: -100, width: 800, height: 600 });
    expect(controller.validateGameWindow()).toBe(false);
  });
});
```

**验收标准**：
- [ ] 测试覆盖率 > 90%
- [ ] 所有核心功能有对应测试
- [ ] 边界情况和异常情况有测试覆盖
- [ ] 测试运行稳定，无随机失败

#### 任务3.2：集成测试和性能测试
**目标**：验证模块集成和性能指标

**集成测试**：
```typescript
// integration/InputController.integration.test.ts
describe('InputController 集成测试', () => {
  test('应该与GameDetector正确集成', async () => {
    const gameDetector = new GameDetector();
    const inputController = new InputController();
    
    // 模拟游戏检测
    const gameWindow = await gameDetector.getGameWindow();
    if (gameWindow) {
      inputController.setGameWindow(gameWindow);
      expect(inputController.validateGameWindow()).toBe(true);
    }
  });
  
  test('应该能够处理长时间连续操作', async () => {
    const controller = new InputController();
    const startTime = Date.now();
    
    // 连续执行100个操作
    for (let i = 0; i < 100; i++) {
      await controller.click(100 + i % 10, 100 + i % 10);
    }
    
    const duration = Date.now() - startTime;
    expect(duration).toBeLessThan(30000); // 30秒内完成
    
    const stats = controller.getStats();
    expect(stats.successRate).toBeGreaterThan(95); // 95%以上成功率
  });
});
```

**性能测试**：
```typescript
// performance/InputController.performance.test.ts
describe('InputController 性能测试', () => {
  test('单次操作响应时间应小于100ms', async () => {
    const controller = new InputController();
    
    const startTime = Date.now();
    await controller.click(100, 100);
    const duration = Date.now() - startTime;
    
    expect(duration).toBeLessThan(100);
  });
  
  test('内存使用应保持稳定', async () => {
    const controller = new InputController();
    const initialMemory = process.memoryUsage().heapUsed;
    
    // 执行大量操作
    for (let i = 0; i < 1000; i++) {
      await controller.click(100, 100);
    }
    
    const finalMemory = process.memoryUsage().heapUsed;
    const memoryIncrease = finalMemory - initialMemory;
    
    expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024); // 50MB以内
  });
  
  test('队列执行性能', async () => {
    const controller = new InputController();
    
    // 添加100个操作到队列
    for (let i = 0; i < 100; i++) {
      controller.addToQueue({
        type: 'click',
        params: [100 + i % 10, 100 + i % 10],
        delay: 10
      });
    }
    
    const startTime = Date.now();
    const result = await controller.executeQueue();
    const duration = Date.now() - startTime;
    
    expect(result.success).toBe(100);
    expect(duration).toBeLessThan(5000); // 5秒内完成
  });
});
```

**验收标准**：
- [ ] 单次操作响应时间 < 100ms
- [ ] 内存使用增长 < 50MB/1000次操作
- [ ] 连续操作4小时无崩溃
- [ ] 队列执行效率 > 20操作/秒

## 最终验收标准

### 功能完整性
- [ ] 所有基础操作功能正常
- [ ] 平滑移动支持多种曲线
- [ ] 操作队列系统完整可用
- [ ] 录制回放功能稳定
- [ ] 安全检查机制有效

### 代码质量
- [ ] 无TODO、FIXME注释
- [ ] ESLint检查通过
- [ ] TypeScript严格模式通过
- [ ] 测试覆盖率 > 90%
- [ ] 所有公共方法有JSDoc注释

### 性能指标
- [ ] 操作响应时间 < 100ms
- [ ] 内存使用 < 50MB
- [ ] CPU占用 < 5%
- [ ] 连续运行4小时稳定

### 用户体验
- [ ] API接口简洁易用
- [ ] 错误信息清晰明确
- [ ] 配置选项丰富合理
- [ ] 日志信息详细有用

## 风险管理

### 技术风险
1. **robotjs兼容性**：在不同系统版本上测试
2. **性能问题**：实施性能监控和优化
3. **内存泄漏**：定期内存使用检查

### 进度风险
1. **功能复杂度**：分阶段实现，优先核心功能
2. **测试时间**：并行开发和测试

## 后续计划

Week 2完成后，InputController模块将为Week 3的ImageRecognition模块和Week 4的任务执行提供稳定的输入控制基础。

---

**项目负责人**: 开发团队  
**计划制定时间**: 2024年1月  
**预计完成时间**: Week 2结束  
**文档版本**: v1.0