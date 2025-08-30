// node-window-manager 浏览器兼容性模块
// 模拟 windowManager 对象
const windowManager = {
    getWindows: () => []
};
// 模拟 node-window-manager 功能
const mockWindowManager = {
    windowManager
};
// 提供默认导出和命名导出
export default mockWindowManager;
export { windowManager, mockWindowManager };
