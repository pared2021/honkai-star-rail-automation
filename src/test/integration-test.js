/**
 * 集成测试 - 验证TaskExecutor与核心模块的集成
 */
import { TaskExecutor } from '../modules/TaskExecutor.js';
import { GameDetector } from '../modules/GameDetector.js';
import { InputController } from '../modules/InputController.js';
import { ImageRecognition } from '../modules/ImageRecognition.js';
import { TaskType } from '../types/index.js';
/**
 * 测试TaskExecutor与核心模块的集成
 */
async function testModuleIntegration() {
    console.log('开始集成测试...');
    try {
        // 创建TaskExecutor实例
        const taskExecutor = new TaskExecutor();
        // 测试核心模块实例获取
        console.log('\n1. 测试核心模块实例获取:');
        const gameDetector = taskExecutor.getGameDetector();
        const inputController = taskExecutor.getInputController();
        const imageRecognition = taskExecutor.getImageRecognition();
        console.log('- GameDetector实例:', gameDetector instanceof GameDetector);
        console.log('- InputController实例:', inputController instanceof InputController);
        console.log('- ImageRecognition实例:', imageRecognition instanceof ImageRecognition);
        // 测试游戏环境初始化
        console.log('\n2. 测试游戏环境初始化:');
        const initResult = await taskExecutor.initializeGameEnvironment();
        console.log('- 初始化结果:', initResult);
        if (initResult) {
            // 测试游戏检测功能
            console.log('\n3. 测试游戏检测功能:');
            const isGameRunning = await gameDetector.isGameRunning();
            console.log('- 游戏运行状态:', isGameRunning);
            if (isGameRunning) {
                const gameInfo = await gameDetector.getGameProcessInfo();
                console.log('- 游戏进程信息:', gameInfo);
                // 测试图像识别功能
                console.log('\n4. 测试图像识别功能:');
                try {
                    const screenshot = await imageRecognition.captureGameWindow();
                    console.log('- 截图成功:', screenshot !== null);
                    if (screenshot) {
                        const stats = await imageRecognition.getImageStats();
                        console.log('- 图像统计:', stats);
                    }
                }
                catch (error) {
                    console.log('- 截图失败:', error.message);
                }
                // 测试输入控制功能
                console.log('\n5. 测试输入控制功能:');
                const isInputEnabled = inputController.isInputEnabled();
                console.log('- 输入控制状态:', isInputEnabled);
                if (isInputEnabled) {
                    const mousePos = inputController.getCurrentMousePosition();
                    console.log('- 当前鼠标位置:', mousePos);
                }
            }
        }
        // 测试日常任务执行
        console.log('\n6. 测试日常任务执行:');
        const dailyTask = {
            id: 'test-daily-001',
            type: 'daily',
            name: '测试日常委托',
            description: '测试日常委托任务执行',
            priority: 1,
            timeout: 30000,
            retryCount: 0,
            maxRetries: 1,
            status: 'pending',
            createdAt: new Date(),
            dependencies: [],
            accountId: 'test-account',
            taskType: TaskType.DAILY,
            config: {
                useDefaultFlow: true
            },
            logs: []
        };
        try {
            const result = await taskExecutor.executeTask(dailyTask);
            console.log('- 任务执行结果:', result);
        }
        catch (error) {
            console.log('- 任务执行失败:', error.message);
        }
        // 获取执行统计
        console.log('\n7. 获取执行统计:');
        const stats = taskExecutor.getStats();
        console.log('- 执行统计:', stats);
        // 清理资源
        console.log('\n8. 清理资源:');
        await taskExecutor.cleanup();
        console.log('- 资源清理完成');
        console.log('\n集成测试完成!');
    }
    catch (error) {
        console.error('集成测试失败:', error);
    }
}
/**
 * 测试模块配置
 */
async function testModuleConfiguration() {
    console.log('\n开始模块配置测试...');
    try {
        const taskExecutor = new TaskExecutor();
        const gameDetector = taskExecutor.getGameDetector();
        const inputController = taskExecutor.getInputController();
        const imageRecognition = taskExecutor.getImageRecognition();
        // 测试GameDetector配置
        console.log('\n1. 测试GameDetector配置:');
        const gameConfig = gameDetector.getConfig();
        console.log('- 当前配置:', gameConfig);
        // 测试InputController配置
        console.log('\n2. 测试InputController配置:');
        const inputConfig = inputController.getConfig();
        console.log('- 当前配置:', inputConfig);
        // 设置默认延迟
        inputController.setDefaultDelay(100);
        console.log('- 设置默认延迟:', inputController.getDefaultDelay());
        // 测试ImageRecognition配置
        console.log('\n3. 测试ImageRecognition配置:');
        const imageConfig = imageRecognition.getConfig();
        console.log('- 当前配置:', imageConfig);
        // 获取缓存统计
        const cacheStats = imageRecognition.getCacheStats();
        console.log('- 缓存统计:', cacheStats);
        console.log('\n模块配置测试完成!');
    }
    catch (error) {
        console.error('模块配置测试失败:', error);
    }
}
/**
 * 主测试函数
 */
async function runTests() {
    console.log('='.repeat(50));
    console.log('TaskExecutor 集成测试');
    console.log('='.repeat(50));
    await testModuleIntegration();
    await testModuleConfiguration();
    console.log('\n所有测试完成!');
}
// 如果直接运行此文件，则执行测试
if (import.meta.url === `file://${process.argv[1]}`) {
    runTests().catch(console.error);
}
export { testModuleIntegration, testModuleConfiguration, runTests };
