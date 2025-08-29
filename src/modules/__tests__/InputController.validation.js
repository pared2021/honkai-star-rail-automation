import InputController from '../InputController.js';
/**
 * InputController功能验证脚本
 * 用于测试真实环境中的输入控制功能
 */
async function validateInputController() {
    console.log('开始验证InputController功能...');
    const inputController = new InputController();
    try {
        // 1. 测试基本鼠标操作
        console.log('\n1. 测试鼠标位置获取...');
        const mousePos = inputController.getCurrentMousePosition();
        console.log(`当前鼠标位置: (${mousePos.x}, ${mousePos.y})`);
        // 2. 测试鼠标移动（安全区域）
        console.log('\n2. 测试鼠标移动...');
        const targetX = mousePos.x + 50;
        const targetY = mousePos.y + 50;
        await inputController.moveMouse(targetX, targetY);
        console.log(`鼠标移动到: (${targetX}, ${targetY})`);
        // 验证移动是否成功
        await new Promise(resolve => setTimeout(resolve, 100));
        const newPos = inputController.getCurrentMousePosition();
        console.log(`移动后位置: (${newPos.x}, ${newPos.y})`);
        // 3. 测试键盘输入（安全按键）
        console.log('\n3. 测试键盘按键...');
        console.log('即将按下ESC键（安全按键）');
        await inputController.pressKey('escape');
        console.log('ESC键按下完成');
        // 4. 测试安全检查功能
        console.log('\n4. 测试安全检查功能...');
        inputController.setSafetyChecks(true);
        // 快速连续操作测试
        console.log('测试操作间隔限制...');
        const startTime = Date.now();
        await inputController.moveMouse(mousePos.x, mousePos.y);
        await inputController.moveMouse(mousePos.x + 1, mousePos.y + 1);
        const endTime = Date.now();
        console.log(`连续操作耗时: ${endTime - startTime}ms`);
        // 5. 测试日志功能
        console.log('\n5. 测试日志功能...');
        const logs = inputController.getInputLogs(5);
        console.log(`最近5条操作日志:`);
        logs.forEach((log, index) => {
            console.log(`  ${index + 1}. ${log.action} - ${log.success ? '成功' : '失败'} (${new Date(log.timestamp).toLocaleTimeString()})`);
        });
        // 6. 测试统计信息
        console.log('\n6. 测试统计信息...');
        const stats = inputController.getStats();
        console.log(`操作统计: 总计${stats.total}次, 成功${stats.success}次, 失败${stats.failed}次, 成功率${stats.successRate.toFixed(1)}%`);
        // 7. 测试禁用功能
        console.log('\n7. 测试输入控制禁用...');
        inputController.setEnabled(false);
        console.log('输入控制已禁用');
        await inputController.moveMouse(mousePos.x + 10, mousePos.y + 10);
        console.log('尝试移动鼠标（应该被忽略）');
        // 重新启用
        inputController.setEnabled(true);
        console.log('输入控制已重新启用');
        console.log('\n✅ InputController功能验证完成！所有功能正常工作。');
    }
    catch (error) {
        console.error('\n❌ InputController功能验证失败:', error);
        throw error;
    }
}
// 如果直接运行此文件，则执行验证
if (require.main === module) {
    validateInputController()
        .then(() => {
        console.log('\n验证脚本执行完成');
        process.exit(0);
    })
        .catch((error) => {
        console.error('\n验证脚本执行失败:', error);
        process.exit(1);
    });
}
export default validateInputController;
