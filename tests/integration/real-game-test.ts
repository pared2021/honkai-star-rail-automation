/**
 * 真实游戏环境集成测试脚本
 * 用于验证GameDetector模块在实际游戏运行时的检测准确性
 * 注意：此测试需要真实的游戏进程运行
 */

import { GameDetector, GameDetectorConfig } from '../../src/modules/GameDetector';
import { GameStatus } from '../../src/types';

class RealGameIntegrationTest {
  private detector: GameDetector;
  private testResults: { [key: string]: boolean } = {};
  private testLogs: string[] = [];
  private eventLogs: string[] = [];

  constructor() {
    // 配置GameDetector用于真实测试
    const config: Partial<GameDetectorConfig> = {
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
      detectionInterval: 500, // 更频繁的检测用于测试
      enableLogging: true,
      logLevel: 'debug'
    };

    this.detector = new GameDetector(config);
    this.setupEventListeners();
  }

  /**
   * 设置事件监听器
   */
  private setupEventListeners(): void {
    this.detector.on('gameStarted', (status: GameStatus) => {
      this.eventLogs.push(`[${new Date().toISOString()}] 游戏启动事件: ${JSON.stringify(status)}`);
    });

    this.detector.on('gameStopped', (status: GameStatus) => {
      this.eventLogs.push(`[${new Date().toISOString()}] 游戏停止事件: ${JSON.stringify(status)}`);
    });

    this.detector.on('gameActivated', (status: GameStatus) => {
      this.eventLogs.push(`[${new Date().toISOString()}] 游戏激活事件: ${JSON.stringify(status)}`);
    });

    this.detector.on('gameDeactivated', (status: GameStatus) => {
      this.eventLogs.push(`[${new Date().toISOString()}] 游戏失活事件: ${JSON.stringify(status)}`);
    });

    this.detector.on('windowChanged', (status: GameStatus) => {
      this.eventLogs.push(`[${new Date().toISOString()}] 窗口变化事件: ${JSON.stringify(status)}`);
    });

    this.detector.on('error', (error: any) => {
      this.eventLogs.push(`[${new Date().toISOString()}] 错误事件: ${error}`);
    });
  }

  /**
   * 记录测试日志
   */
  private log(message: string): void {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}`;
    this.testLogs.push(logMessage);
    console.log(logMessage);
  }

  /**
   * 测试1: 检测游戏进程是否正确识别
   */
  async testProcessDetection(): Promise<boolean> {
    this.log('开始测试: 游戏进程检测');
    
    try {
      const status = await this.detector.getCurrentStatus();
      const processInfo = this.detector.getCurrentProcessInfo();
      
      if (status.isRunning && processInfo) {
        this.log(`✓ 成功检测到游戏进程: ${processInfo.name} (PID: ${processInfo.pid})`);
        this.log(`  - CPU使用率: ${processInfo.cpu || 'N/A'}%`);
        this.log(`  - 内存使用: ${processInfo.memory || 'N/A'}MB`);
        return true;
      } else {
        this.log('✗ 未检测到游戏进程，请确保游戏正在运行');
        return false;
      }
    } catch (error) {
      this.log(`✗ 进程检测测试失败: ${error}`);
      return false;
    }
  }

  /**
   * 测试2: 窗口信息获取是否准确
   */
  async testWindowInfoAccuracy(): Promise<boolean> {
    this.log('开始测试: 窗口信息获取准确性');
    
    try {
      const status = await this.detector.getCurrentStatus();
      const windowInfo = this.detector.getCurrentWindowInfo();
      
      if (status.isRunning && windowInfo && status.windowInfo) {
        this.log(`✓ 成功获取窗口信息:`);
        this.log(`  - 窗口标题: ${windowInfo.title}`);
        this.log(`  - 窗口ID: ${windowInfo.id}`);
        this.log(`  - 窗口位置: (${windowInfo.bounds.x}, ${windowInfo.bounds.y})`);
        this.log(`  - 窗口大小: ${windowInfo.bounds.width}x${windowInfo.bounds.height}`);
        this.log(`  - 是否可见: ${windowInfo.isVisible}`);
        this.log(`  - 是否最小化: ${windowInfo.isMinimized}`);
        
        // 验证窗口信息的一致性
        const consistent = (
          status.windowInfo.title === windowInfo.title &&
          status.windowInfo.width === windowInfo.bounds.width &&
          status.windowInfo.height === windowInfo.bounds.height &&
          status.windowInfo.x === windowInfo.bounds.x &&
          status.windowInfo.y === windowInfo.bounds.y
        );
        
        if (consistent) {
          this.log('✓ 窗口信息一致性验证通过');
          return true;
        } else {
          this.log('✗ 窗口信息一致性验证失败');
          return false;
        }
      } else {
        this.log('✗ 未获取到窗口信息，请确保游戏窗口可见');
        return false;
      }
    } catch (error) {
      this.log(`✗ 窗口信息测试失败: ${error}`);
      return false;
    }
  }

  /**
   * 测试3: 游戏状态实时监控
   */
  async testRealtimeMonitoring(): Promise<boolean> {
    this.log('开始测试: 游戏状态实时监控');
    
    try {
      // 清除之前的事件日志
      this.eventLogs = [];
      
      // 启动实时监控
      this.detector.startDetection(500);
      this.log('✓ 实时监控已启动，检测间隔: 500ms');
      
      // 监控10秒
      await new Promise(resolve => setTimeout(resolve, 10000));
      
      // 停止监控
      this.detector.stopDetection();
      this.log('✓ 实时监控已停止');
      
      // 检查监控结果
      const stats = this.detector.getDetectionStats();
      this.log(`监控统计信息:`);
      this.log(`  - 检测运行状态: ${stats.isRunning}`);
      this.log(`  - 最后检测时间: ${stats.lastDetectionTime.toISOString()}`);
      this.log(`  - 错误计数: ${stats.errorCount}`);
      this.log(`  - 事件日志数量: ${this.eventLogs.length}`);
      
      if (this.eventLogs.length > 0) {
        this.log('✓ 实时监控产生了事件，监控功能正常');
        this.eventLogs.forEach(log => this.log(`  事件: ${log}`));
        return true;
      } else {
        this.log('⚠ 实时监控期间未产生事件，可能游戏状态未发生变化');
        return true; // 这不算失败，只是状态稳定
      }
    } catch (error) {
      this.log(`✗ 实时监控测试失败: ${error}`);
      return false;
    }
  }

  /**
   * 测试4: 配置更新功能
   */
  async testConfigUpdates(): Promise<boolean> {
    this.log('开始测试: 配置更新功能');
    
    try {
      // 获取原始配置
      const originalConfig = this.detector.getConfig();
      this.log(`原始配置: 检测间隔=${originalConfig.detectionInterval}ms, 日志级别=${originalConfig.logLevel}`);
      
      // 更新配置
      const newConfig = {
        detectionInterval: 2000,
        logLevel: 'warn' as const
      };
      
      this.detector.updateConfig(newConfig);
      this.log('✓ 配置已更新');
      
      // 验证配置更新
      const updatedConfig = this.detector.getConfig();
      const configUpdated = (
        updatedConfig.detectionInterval === newConfig.detectionInterval &&
        updatedConfig.logLevel === newConfig.logLevel
      );
      
      if (configUpdated) {
        this.log(`✓ 配置更新验证通过: 检测间隔=${updatedConfig.detectionInterval}ms, 日志级别=${updatedConfig.logLevel}`);
        
        // 恢复原始配置
        this.detector.updateConfig({
          detectionInterval: originalConfig.detectionInterval,
          logLevel: originalConfig.logLevel
        });
        this.log('✓ 原始配置已恢复');
        
        return true;
      } else {
        this.log('✗ 配置更新验证失败');
        return false;
      }
    } catch (error) {
      this.log(`✗ 配置更新测试失败: ${error}`);
      return false;
    }
  }

  /**
   * 测试5: 游戏启动等待功能
   */
  async testGameStartWaiting(): Promise<boolean> {
    this.log('开始测试: 游戏启动等待功能');
    
    try {
      // 检查当前游戏状态
      const currentStatus = await this.detector.getCurrentStatus();
      
      if (currentStatus.isRunning) {
        this.log('✓ 游戏当前正在运行，等待功能可用');
        
        // 测试等待功能（短超时，因为游戏已经在运行）
        const waitResult = await this.detector.waitForGameStart(5000);
        
        if (waitResult) {
          this.log('✓ 游戏启动等待功能正常');
          return true;
        } else {
          this.log('✗ 游戏启动等待功能异常');
          return false;
        }
      } else {
        this.log('⚠ 游戏当前未运行，无法测试等待功能');
        this.log('  提示: 请启动游戏后重新运行此测试');
        return false;
      }
    } catch (error) {
      this.log(`✗ 游戏启动等待测试失败: ${error}`);
      return false;
    }
  }

  /**
   * 运行所有测试
   */
  async runAllTests(): Promise<void> {
    this.log('='.repeat(60));
    this.log('开始真实游戏环境集成测试');
    this.log('='.repeat(60));
    
    // 运行各项测试
    this.testResults['processDetection'] = await this.testProcessDetection();
    await new Promise(resolve => setTimeout(resolve, 1000)); // 测试间隔
    
    this.testResults['windowInfoAccuracy'] = await this.testWindowInfoAccuracy();
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    this.testResults['realtimeMonitoring'] = await this.testRealtimeMonitoring();
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    this.testResults['configUpdates'] = await this.testConfigUpdates();
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    this.testResults['gameStartWaiting'] = await this.testGameStartWaiting();
    
    // 输出测试结果
    this.printTestResults();
  }

  /**
   * 打印测试结果
   */
  private printTestResults(): void {
    this.log('='.repeat(60));
    this.log('测试结果汇总');
    this.log('='.repeat(60));
    
    const testNames = {
      'processDetection': '游戏进程检测',
      'windowInfoAccuracy': '窗口信息获取准确性',
      'realtimeMonitoring': '游戏状态实时监控',
      'configUpdates': '配置更新功能',
      'gameStartWaiting': '游戏启动等待功能'
    };
    
    let passedCount = 0;
    let totalCount = 0;
    
    for (const [testKey, testName] of Object.entries(testNames)) {
      const result = this.testResults[testKey];
      const status = result ? '✓ 通过' : '✗ 失败';
      this.log(`${testName}: ${status}`);
      
      if (result) passedCount++;
      totalCount++;
    }
    
    this.log('='.repeat(60));
    this.log(`总体结果: ${passedCount}/${totalCount} 项测试通过`);
    
    if (passedCount === totalCount) {
      this.log('🎉 所有测试通过！GameDetector模块在真实环境中运行正常');
    } else {
      this.log('⚠ 部分测试失败，请检查游戏运行状态和环境配置');
    }
    
    // 输出检测错误（如果有）
    const errors = this.detector.getDetectionErrors();
    if (errors.length > 0) {
      this.log('\n检测错误历史:');
      errors.forEach(error => this.log(`  ${error}`));
    }
    
    this.log('='.repeat(60));
  }

  /**
   * 获取测试日志
   */
  getTestLogs(): string[] {
    return [...this.testLogs];
  }

  /**
   * 获取事件日志
   */
  getEventLogs(): string[] {
    return [...this.eventLogs];
  }
}

// 导出测试类
export { RealGameIntegrationTest };

// 如果直接运行此文件，则执行测试
if (import.meta.url.endsWith(process.argv[1]?.replace(/\\/g, '/'))) {
  const test = new RealGameIntegrationTest();
  test.runAllTests().catch(console.error);
}