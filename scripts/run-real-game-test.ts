#!/usr/bin/env ts-node

/**
 * 真实游戏环境测试运行脚本
 * 使用方法: npm run test:real-game 或 ts-node scripts/run-real-game-test.ts
 */

import { RealGameIntegrationTest } from '../tests/integration/real-game-test';

async function main() {
  console.log('🎮 真实游戏环境集成测试');
  console.log('请确保游戏已启动并可见');
  console.log('');
  
  // 等待用户确认
  console.log('按 Enter 键开始测试，或按 Ctrl+C 取消...');
  await waitForEnter();
  
  try {
    const test = new RealGameIntegrationTest();
    await test.runAllTests();
    
    console.log('\n📊 测试日志已保存，可以查看详细信息');
    
    // 可选：将测试结果保存到文件
    const fs = require('fs');
    const path = require('path');
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const logFile = path.join(__dirname, '..', 'logs', `real-game-test-${timestamp}.log`);
    
    // 确保logs目录存在
    const logsDir = path.dirname(logFile);
    if (!fs.existsSync(logsDir)) {
      fs.mkdirSync(logsDir, { recursive: true });
    }
    
    const testLogs = test.getTestLogs();
    const eventLogs = test.getEventLogs();
    
    const logContent = [
      '=== 真实游戏环境集成测试日志 ===',
      `测试时间: ${new Date().toISOString()}`,
      '',
      '=== 测试日志 ===',
      ...testLogs,
      '',
      '=== 事件日志 ===',
      ...eventLogs,
      '',
      '=== 测试结束 ==='
    ].join('\n');
    
    fs.writeFileSync(logFile, logContent, 'utf8');
    console.log(`📝 详细日志已保存到: ${logFile}`);
    
  } catch (error) {
    console.error('❌ 测试执行失败:', error);
    process.exit(1);
  }
}

/**
 * 等待用户按Enter键
 */
function waitForEnter(): Promise<void> {
  return new Promise((resolve) => {
    process.stdin.setRawMode(true);
    process.stdin.resume();
    process.stdin.on('data', (key) => {
      // Enter键 (\r) 或 Ctrl+C (\u0003)
      if (key.toString() === '\r' || key.toString() === '\n') {
        process.stdin.setRawMode(false);
        process.stdin.pause();
        resolve();
      } else if (key.toString() === '\u0003') {
        console.log('\n测试已取消');
        process.exit(0);
      }
    });
  });
}

// 运行主函数
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error('脚本执行失败:', error);
    process.exit(1);
  });
}

export { main };