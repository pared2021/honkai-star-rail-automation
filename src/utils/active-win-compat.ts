// active-win 浏览器兼容性模块

// 模拟 active-win 功能
const mockActiveWin = () => Promise.resolve(null);

// 提供默认导出和命名导出
export default mockActiveWin;
export { mockActiveWin };