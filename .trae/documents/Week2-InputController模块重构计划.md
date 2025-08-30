# Week 2: InputController模块重构开发计划

## 项目背景

根据实施路线图第一阶段的安排，Week 1的GameDetector模块重构已成功完成，现在进入Week 2的InputController模块实现阶段。本阶段的目标是移除所有TODO代码，实现真实的输入控制功能，确保程序能够准确、安全地与游戏进行交互。

## 当前状态分析

### 已实现功能
经过代码审查，InputController.ts模块已经具备了相当完整的基础实现：

✅ **基础鼠标操作**
- 鼠标点击（左键、右键、中键）
- 鼠标移动
- 双击操作
- 鼠标拖拽

✅ **键盘操作**
- 单键按下
- 组合键操作
- 文本输入

✅ **高级功能**
- 滚轮滚动
- 坐标转换（游戏坐标↔屏幕坐标）
- 操作日志记录
- 安全检查机制
- 统计信息收集

### 需要改进的方面

❌ **缺失的核心功能**
- 平滑鼠标移动的完整实现
- 批量操作队列执行
- 操作录制和回放功能
- 更精确的延迟控制

❌ **安全性增强**
- 游戏窗口边界检查
- 操作频率限制
- 异常恢复机制

❌ **测试覆盖**
- 单元测试缺失
- 集成测试不完整

## Week 2 详细任务规划

### 阶段1：代码审查和清理 (Day 1-2)

#### 任务1.1：TODO代码清理
**目标**：移除所有TODO注释，确保代码完整性

**具体任务**：
```bash
# 搜索并清理所有TODO注释
grep -r "TODO" src/modules/InputController.ts
grep -r "FIXME" src/modules/InputController.ts
grep -r "XXX" src/modules/InputController.ts
```

**验收标准**：
- 代码中无任何TODO、FIXME、XXX注释
- 所有注释掉的代码块已清理或实现
- 代码通过ESLint检查

#### 任务1.2：依赖项验证
**目标**：确保所有依赖项正确导入和使用

**具体任务**：
- 验证robotjs库的正确导入和初始化
- 检查browserCompat兼容性处理
- 确认所有接口定义的完整性

**验收标准**：
- 所有依赖项正常工作
- 浏览器环境兼容性正常
- TypeScript类型检查通过

### 阶段2：核心功能完善 (Day 3-5)

#### 任务2.1：平滑鼠标移动实现
**目标**：实现更自然的鼠标移动轨迹

**具体实现**：
```typescript
/**
 * 平滑移动鼠标到目标位置
 * @param toX 目标X坐标
 * @param toY 目标Y坐标
 * @param duration 移动持续时间(ms)
 * @param curve 移动曲线类型
 */
public async smoothMoveTo(toX: number, toY: number, duration: number = 500, curve: 'linear' | 'ease' | 'bezier' = 'ease'): Promise<boolean>

/**
 * 贝塞尔曲线移动
 */
private calculateBezierPath(start: MousePosition, end: MousePosition, steps: number): MousePosition[]

/**
 * 缓动函数
 */
private easeInOutQuad(t: number): number
```

**验收标准**：
- 鼠标移动轨迹自然，避免直线移动
- 支持多种移动曲线
- 移动速度可配置
- 移动过程可中断

#### 任务2.2：操作队列系统
**目标**：实现批量操作的队列执行

**具体实现**：
```typescript
interface QueuedAction {
  type: 'click' | 'key' | 'move' | 'drag' | 'scroll';
  params: any[];
  delay?: number;
  id?: string;
}

/**
 * 添加操作到队列
 */
public addToQueue(action: QueuedAction): string

/**
 * 执行队列中的所有操作
 */
public async executeQueue(): Promise<boolean[]>

/**
 * 清空操作队列
 */
public clearQueue(): void

/**
 * 获取队列状态
 */
public getQueueStatus(): { pending: number; executing: boolean }
```

**验收标准**：
- 支持多种操作类型的队列化
- 队列执行可暂停/恢复
- 支持操作优先级
- 执行失败时的错误处理

#### 任务2.3：操作录制和回放
**目标**：实现用户操作的录制和自动回放

**具体实现**：
```typescript
interface RecordedAction {
  timestamp: number;
  action: QueuedAction;
  relativeTime: number;
}

/**
 * 开始录制操作
 */
public startRecording(): void

/**
 * 停止录制
 */
public stopRecording(): RecordedAction[]

/**
 * 回放录制的操作
 */
public async playback(actions: RecordedAction[], speed: number = 1.0): Promise<boolean>

/**
 * 保存/加载录制文件
 */
public saveRecording(actions: RecordedAction[], filename: string): Promise<void>
public loadRecording(filename: string): Promise<RecordedAction[]>
```

**验收标准**：
- 准确录制用户操作时序
- 支持变速回放
- 录制文件可保存和加载
- 回放过程可中断

### 阶段3：安全性和稳定性增强 (Day 6-8)

#### 任务3.1：游戏窗口边界检查
**目标**：确保所有操作都在游戏窗口范围内

**具体实现**：
```typescript
/**
 * 检查坐标是否在游戏窗口内
 */
private isCoordinateInGameWindow(x: number, y: number): boolean

/**
 * 自动修正超出边界的坐标
 */
private clampToGameWindow(x: number, y: number): MousePosition

/**
 * 验证游戏窗口是否有效
 */
public validateGameWindow(): boolean
```

**验收标准**：
- 所有鼠标操作自动限制在游戏窗口内
- 超出边界的操作被安全拒绝或修正
- 游戏窗口失效时自动停止操作

#### 任务3.2：操作频率限制
**目标**：防止过于频繁的操作影响游戏稳定性

**具体实现**：
```typescript
/**
 * 动态调整操作频率
 */
public setDynamicDelay(enabled: boolean): void

/**
 * 检测操作频率
 */
private checkOperationFrequency(): boolean

/**
 * 自适应延迟调整
 */
private adjustDelayBasedOnPerformance(): void
```

**验收标准**：
- 操作频率自动适应系统性能
- 高频操作时自动增加延迟
- 支持手动设置频率限制

#### 任务3.3：异常恢复机制
**目标**：在操作失败时能够自动恢复

**具体实现**：
```typescript
/**
 * 操作重试机制
 */
public async executeWithRetry<T>(operation: () => Promise<T>, maxRetries: number = 3): Promise<T>

/**
 * 检测并恢复鼠标状态
 */
public async recoverMouseState(): Promise<boolean>

/**
 * 紧急停止所有操作
 */
public emergencyStop(): void
```

**验收标准**：
- 操作失败时自动重试
- 鼠标卡死时能够恢复
- 紧急情况下能够立即停止

### 阶段4：测试和验证 (Day 9-10)

#### 任务4.1：单元测试编写
**目标**：为所有核心功能编写单元测试

**测试覆盖范围**：
```typescript
// InputController.test.ts
describe('InputController', () => {
  describe('基础操作', () => {
    test('鼠标点击功能');
    test('键盘按键功能');
    test('坐标转换功能');
  });
  
  describe('高级功能', () => {
    test('平滑移动功能');
    test('操作队列功能');
    test('录制回放功能');
  });
  
  describe('安全检查', () => {
    test('边界检查功能');
    test('频率限制功能');
    test('异常恢复功能');
  });
});
```

**验收标准**：
- 测试覆盖率 > 90%
- 所有核心功能有对应测试
- 边界情况和异常情况有测试覆盖
- 测试运行稳定，无随机失败

#### 任务4.2：集成测试
**目标**：验证InputController与其他模块的集成

**测试场景**：
- 与GameDetector的集成测试
- 与ImageRecognition的协作测试
- 真实游戏环境下的功能测试

**验收标准**：
- 模块间协作正常
- 真实环境下功能稳定
- 性能指标达到要求

#### 任务4.3：性能测试
**目标**：验证操作性能和资源使用

**测试指标**：
- 操作响应时间 < 100ms
- 内存使用稳定
- CPU占用 < 5%
- 连续操作1小时无异常

**验收标准**：
- 所有性能指标达标
- 长时间运行稳定
- 资源使用合理

## 技术要求

### 开发环境
- **Node.js**: v18+
- **TypeScript**: v5+
- **robotjs**: v0.6+
- **Jest**: v29+ (测试框架)

### 代码质量标准
- **ESLint**: 无警告和错误
- **TypeScript**: 严格模式，无类型错误
- **测试覆盖率**: > 90%
- **文档**: 所有公共方法有JSDoc注释

### 性能要求
- **操作延迟**: < 100ms
- **内存使用**: < 50MB
- **CPU占用**: < 5%
- **稳定性**: 连续运行4小时无崩溃

## 验收标准

### 功能验收
- [ ] 所有TODO代码已清理
- [ ] 基础鼠标操作准确率 > 99%
- [ ] 键盘操作响应正常
- [ ] 平滑移动轨迹自然
- [ ] 操作队列执行稳定
- [ ] 录制回放功能正常
- [ ] 安全检查机制有效
- [ ] 异常恢复机制可靠

### 质量验收
- [ ] 单元测试覆盖率 > 90%
- [ ] 集成测试通过
- [ ] 性能测试达标
- [ ] 代码审查通过
- [ ] 文档完整准确

### 用户体验验收
- [ ] 操作响应及时
- [ ] 错误提示清晰
- [ ] 配置简单易用
- [ ] 日志信息详细

## 风险管理

### 技术风险
1. **robotjs兼容性问题**
   - 风险：不同系统版本的兼容性
   - 缓解：多环境测试，备用方案

2. **操作精度问题**
   - 风险：高DPI屏幕下的坐标偏移
   - 缓解：DPI感知，坐标校准

3. **性能问题**
   - 风险：频繁操作导致系统卡顿
   - 缓解：智能延迟，资源监控

### 进度风险
1. **功能复杂度超预期**
   - 缓解：分阶段实现，优先核心功能

2. **测试时间不足**
   - 缓解：并行开发和测试，自动化测试

## 成功指标

### 技术指标
- 操作成功率 > 99%
- 响应时间 < 100ms
- 内存使用 < 50MB
- 测试覆盖率 > 90%

### 用户指标
- 配置时间 < 5分钟
- 学习成本 < 30分钟
- 错误恢复时间 < 10秒

### 业务指标
- 相比手动操作效率提升 > 80%
- 操作准确性 > 手动操作
- 用户满意度 > 4.0/5.0

## 后续计划

Week 2完成后，将进入Week 3的ImageRecognition模块实现阶段。InputController模块将为后续的图像识别和任务执行提供稳定可靠的输入控制基础。

### 与其他模块的集成点
- **GameDetector**: 获取游戏窗口信息
- **ImageRecognition**: 提供点击目标坐标
- **TaskExecutor**: 执行具体的操作序列

### 持续改进计划
- 根据用户反馈优化操作体验
- 基于使用数据调整默认参数
- 扩展支持更多输入设备
- 增加AI辅助的操作优化

---

**项目负责人**: 开发团队  
**计划制定时间**: 2024年1月  
**预计完成时间**: Week 2结束  
**文档版本**: v1.0